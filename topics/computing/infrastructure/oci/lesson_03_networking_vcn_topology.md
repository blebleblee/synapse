# Lesson 3: Virtual Cloud Networks, Routing Tables, Security Lists, DRG Transit

## 1. First-Principles Intuition & Invariants

Every cloud network is ultimately a lie told to a virtual machine. The lie is a useful one: a VM believes it owns a private Ethernet segment, maintains an ARP cache, issues DHCP requests, and routes packets through a default gateway sitting at a well-known IP. None of that hardware exists. What exists instead is a programmable packet-forwarding fabric that intercepts every frame the VM emits, rewrites it according to tables derived from your declarative intent, and delivers it somewhere else entirely. Understanding OCI's Virtual Cloud Network requires you to hold that duality in mind at all times: the abstraction is the product, but the mechanics underneath are the substrate that determines correctness, latency, and blast radius when things fail.

OCI's networking plane is built around a software-defined networking model that diverges in one critical way from competitors: Oracle does not use an overlay protocol like VXLAN or Geneve tunneling between hypervisors in the conventional sense visible to operators. Instead, OCI's physical network fabric is a purpose-built, lossless, low-latency RDMA-capable substrate, and the virtualization layer sits atop it as a forwarding decision engine. When you provision a VCN, you are creating a namespace in a distributed routing database. When you create a subnet, you are carving a CIDR prefix out of that namespace and binding it to a physical availability domain. The Virtual NIC attached to your instance does not exist as a software bridge in the Linux kernel of the hypervisor; it is a first-class object in OCI's network control plane, with its own MAC address, IP assignment, and policy bindings that the fabric enforces at line rate.

The foundational invariant of OCI networking is that every routing and security decision is stateful and enforced at the VNIC boundary. The fabric does not forward packets through a chain of software firewalls or virtual routers; it enforces rules at ingress and egress of the source VNIC and again at ingress and egress of the destination VNIC. This architecture means that adding instances to a subnet does not degrade security enforcement performance, because each VNIC carries its own enforcement context independently.

### CIDR Allocation and the Address Space Contract

When you create a VCN, you choose one or more IPv4 CIDR blocks. OCI supports up to five non-overlapping CIDR blocks per VCN, with the constraint that none may overlap with each other or with any CIDR block you plan to reach via Dynamic Routing Gateway. The practical implication is that your CIDR design is not merely an aesthetic choice; it is a formal contract with the routing plane. If you allocate `10.0.0.0/16` to a VCN and later try to peer it with another VCN using `10.0.128.0/17`, the control plane will reject the peering because the CIDR ranges overlap. This is not a bug. The distributed routing engine requires unambiguous prefix ownership to build its forwarding tables without introducing black holes or routing loops.

The subnet is the atomic unit of placement within a VCN. Each subnet receives a CIDR that must fall entirely within one of the VCN's CIDR blocks, and each subnet is bound to exactly one availability domain (regional subnets, introduced later in OCI's evolution, span all ADs in a region, but their addressing rules remain identical). The first IP in a subnet CIDR is the network address, the last is the broadcast address, and OCI reserves three additional addresses internally: the second IP is the default gateway (the implicit router), and two others are reserved for future use. A `/30` subnet therefore yields only two usable host addresses, making `/28` or larger a practical minimum for most workloads.

IPv6 is fully supported: a VCN may be assigned an Oracle-allocated `/56` IPv6 prefix, from which individual `/64` subnet prefixes are carved. IPv6 routing follows the same route table and gateway mechanics as IPv4, though the security list and NSG rules require explicit IPv6 CIDR entries. Many operators provision IPv6 from day one to avoid retrofitting address space into established security rule sets later.

### The Implicit Router as a First-Class Primitive

Every VCN contains an implicit router. This is not a VM you manage, not an HA pair of appliances, and not a software process you can SSH into. It is a logical forwarding entity instantiated as part of the VCN's control plane state, and it owns the second IP address in every subnet CIDR. When a VM sends a packet to its default gateway, the fabric intercepts that packet, looks up the destination against the route table associated with the VM's subnet, and forwards accordingly. The implicit router is the execution engine for your route tables, and understanding its lookup semantics is the foundation of every routing architecture on OCI.

---

## 2. Core Architecture & Mechanics

### Route Table Mechanics and Longest-Prefix Match

A route table in OCI is a named ordered set of route rules. Each rule maps a destination CIDR to a next-hop target. The implicit router performs longest-prefix match (LPM) across all rules in the table associated with the originating subnet. OCI's forwarding plane uses the same LPM algorithm found in hardware FIBs: the most specific matching prefix wins, and ties at the same prefix length are broken by rule ordering within the table.

Route targets in OCI are typed objects, not bare IP addresses. This distinction matters enormously for operational clarity. A next-hop can be an Internet Gateway, a NAT Gateway, a Service Gateway, a Dynamic Routing Gateway, a Local Peering Gateway, or a private IP (the latter used for routing through an NVA or firewall instance). Specifying a typed target means the control plane can validate the target's existence, detect when it is deleted, and flag the broken route rule rather than silently blackholing traffic.

The following Terraform configuration represents a production-grade route table for a private application subnet that requires internet egress through NAT and access to Oracle services through the Service Gateway, while routing all inter-region and on-premises traffic through the DRG.

```hcl
resource "oci_core_route_table" "private_app_rt" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "private-app-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.nat_gw.id
  }

  route_rules {
    destination       = "all-iad-services-in-oracle-services-network"
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.svc_gw.id
  }

  route_rules {
    destination       = "10.0.0.0/8"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_drg.main_drg.id
  }

  route_rules {
    destination       = "172.16.0.0/12"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_drg.main_drg.id
  }
}
```

The `SERVICE_CIDR_BLOCK` destination type here is critical. It tells the routing engine to resolve the destination against OCI's internal service network label, rather than against a static CIDR that Oracle might change in the future. The Service Gateway itself is a managed NAT device that provides private connectivity to Oracle-managed services (Object Storage, Autonomous Database, Container Registry, Logging, and others) without the traffic ever leaving Oracle's physical network or traversing the internet.

### The Route Table Association Model

Each subnet is associated with exactly one route table. This is a hard constraint, not a soft default. When you change a subnet's route table association, the swap is atomic: the implicit router begins using the new table for all subsequent forwarding decisions immediately. There is no graceful drain, no connection migration. Any in-flight TCP sessions that were routing through a path that no longer exists in the new table will stall until TCP retransmit timers expire.

Each gateway object (Internet Gateway, NAT Gateway, DRG, LPG) may also have a route table associated with it. This feature, called ingress routing, allows you to steer traffic entering a VCN through a firewall NVA before it reaches the target subnet. The ingress route table is evaluated by the implicit router when the gateway injects a packet into the VCN: the destination is matched against the ingress route table, and the packet is forwarded to the specified next-hop (typically a private IP on a firewall instance's VNIC) rather than directly to the target subnet.

The ingress routing architecture looks like this in a hub-and-spoke topology:

```
                    Internet
                       |
              [Internet Gateway]
                       |
              [IGW Ingress RT]        ← route: 0.0.0.0/0 → Firewall NVA VNIC IP
                       |
              [Firewall NVA VNIC]     ← North-South inspection
                       |
              [Firewall Egress RT]    ← route: 10.0.1.0/24 → implicit subnet route
                       |
              [Application Subnet]
                  10.0.1.0/24
```

The firewall NVA must have IP forwarding enabled on its VNIC (the `skip_source_dest_check` flag in OCI's VNIC configuration) or the fabric will drop packets whose destination IP does not match the VNIC's assigned address.

### Security Lists: Stateful and Stateless Enforcement

OCI provides two overlapping security mechanisms at the VNIC boundary: Security Lists and Network Security Groups. Both ultimately resolve to per-flow allow/deny decisions, but their scope and state semantics differ in ways that have direct performance consequences.

A Security List is a VCN-level resource associated with a subnet. Every VNIC in the subnet inherits the subnet's security list rules. A Network Security Group (NSG) is a VNIC-level resource: you add individual VNICs to an NSG and apply rules to the group. NSGs are the preferred model for production workloads because they provide fine-grained per-service rule sets without the combinatorial explosion that emerges when you try to express complex topologies through subnet-level lists.

The stateful vs. stateless distinction is the most operationally consequential choice in OCI security rule configuration. When you create a stateful ingress rule permitting TCP port 443 from `0.0.0.0/0`, the OCI connection tracking engine creates a flow entry for the five-tuple (source IP, source port, destination IP, destination port, protocol) when the first SYN arrives. Return traffic (the SYN-ACK and subsequent ACKs from the server back to the client) is automatically permitted because the connection tracker recognizes it as part of an established flow. You do not need a corresponding egress rule to permit the return path.

Stateless rules bypass the connection tracker entirely. A stateless ingress rule permitting TCP port 443 will allow the inbound SYN to pass. The SYN-ACK from the server, however, is an egress packet from the server's VNIC perspective, and without a corresponding stateless egress rule permitting TCP ephemeral ports (typically `1024-65535`) to the client's source range, the SYN-ACK will be dropped. This is the most common misconfiguration when operators migrate security rule sets from other platforms without understanding OCI's model. The asymmetry exists by design: stateless rules allow high-throughput packet processing for workloads like UDP streaming or IP-in-IP tunnels where connection tracking overhead is unacceptable.

The enforcement order when both a Security List and an NSG apply to the same VNIC is a union model: a packet is permitted if any rule in either the Security List or any NSG associated with the VNIC permits it, subject to the caveat that a stateless deny in one instrument does not block a stateful permit in another. OCI's security rule model is permit-only: there are no explicit deny rules. The implicit default deny is the absence of a matching permit rule. This simplifies the rule evaluation model at the cost of making exception-based allowlisting the only available posture, which is architecturally correct for zero-trust designs.

The following Terraform resource defines an NSG for a web tier that permits HTTPS from the internet and allows only the application tier to reach it on the backend port:

```hcl
resource "oci_core_network_security_group" "web_tier_nsg" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "web-tier-nsg"
}

resource "oci_core_network_security_group_security_rule" "allow_https_inbound" {
  network_security_group_id = oci_core_network_security_group.web_tier_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "allow_app_to_web_backend" {
  network_security_group_id = oci_core_network_security_group.web_tier_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.app_tier_nsg.id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 8080
      max = 8080
    }
  }
}

resource "oci_core_network_security_group_security_rule" "allow_all_egress" {
  network_security_group_id = oci_core_network_security_group.web_tier_nsg.id
  direction                 = "EGRESS"
  protocol                  = "all"
  destination               = "0.0.0.0/0"
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
}
```

The `source_type = "NETWORK_SECURITY_GROUP"` reference in the second rule is particularly powerful. The rule does not reference a CIDR; it references another NSG object. The fabric resolves this dynamically: as VNICs are added to or removed from the app tier NSG, the web tier rule automatically permits or revokes their access. This is the OCI equivalent of AWS Security Group references and eliminates the need to maintain static IP lists in security rules, which invariably drift from reality within weeks of initial provisioning.

### Service Gateway Mechanics

The Service Gateway deserves deeper examination because its behavior is frequently misunderstood. It is not a NAT device, and it does not translate source IP addresses. When a VM sends a packet to an Oracle service endpoint (say, `objectstorage.us-ashburn-1.oraclecloud.com`, which resolves to an IP in the Oracle Services Network range), and the subnet's route table has a `SERVICE_CIDR_BLOCK` rule pointing to the Service Gateway, the following sequence occurs:

The implicit router matches the destination against the service label, forwards the packet to the Service Gateway gateway object, which injects it into Oracle's internal backbone network. The source IP of the packet remains the VM's private VNIC IP. The Oracle service sees the request originating from the VM's private IP and can apply IAM resource principal policies against it without any NAT rewrite. This matters for security audit logs: Object Storage access logs will record the actual instance private IP, not a shared NAT pool address.

For this reason, the Service Gateway is the strictly correct path for all Oracle service API traffic from private subnets, not the NAT Gateway. Using the NAT Gateway for Oracle service traffic works (the packets reach the service via the public internet) but introduces unnecessary latency, routes traffic outside Oracle's network, and prevents IP-based policy enforcement on the Oracle service side.

### Dynamic Routing Gateway Architecture and Route Distribution

The Dynamic Routing Gateway is the edge routing device for a VCN. It is the attachment point for FastConnect virtual circuits, Site-to-Site VPN IPsec tunnels, Remote Peering Connections to other regions, and Local Peering Gateways for intra-region VCN peering. As of OCI's DRG v2 architecture (the current default), the DRG is not merely an attachment point but a full-featured route reflector with its own internal routing tables and import/export policy engine.

Understanding DRG v2 requires understanding its internal table model. Within a DRG, there are several distinct route table types. The VCN route table governs what routes the DRG exports to an attached VCN: when a VCN sends traffic with a destination that matches a route in the VCN route table, the DRG forwards it toward the appropriate attachment. The DRG route table governs what routes the DRG imports from each attachment type and how it redistributes them. Each attachment (VCN, IPsec tunnel, FastConnect virtual circuit, RPC) is associated with both an import route distribution and a DRG route table.

The route distribution mechanism uses a statement-based policy model. An import route distribution contains one or more statements, each specifying a match criteria (attachment type, attachment ID, or prefix list) and an action (accept). The DRG evaluates these statements when it receives route advertisements from an attachment and decides which routes to inject into which DRG route tables. This is architecturally identical to BGP route policy in physical routing hardware, and experienced network engineers will recognize the model immediately.

A transit routing scenario illustrates why this matters. Consider a hub-and-spoke architecture where multiple spoke VCNs (each in a separate compartment, owned by different business units) need to communicate with each other and with an on-premises network through a central hub VCN. The hub VCN contains the DRG and an NVA for East-West inspection. The spoke VCNs are attached to the same DRG.

```
On-Premises DC
   10.200.0.0/16
        |
  [FastConnect VC]
        |
   [DRG v2]
   /         \
[VCN Attach]  [VCN Attach]  [VCN Attach]
 Spoke A       Spoke B       Hub
 10.1.0.0/16   10.2.0.0/16  10.0.0.0/16
                              NVA: 10.0.0.5
```

For Spoke A to reach Spoke B through the hub NVA, three routing conditions must hold simultaneously. First, Spoke A's subnet route table must have a default route or a specific `10.2.0.0/16` route pointing to the DRG. Second, the DRG must have a route table entry directing `10.2.0.0/16` traffic arriving from the Spoke A VCN attachment toward the Hub VCN attachment (specifically to the NVA's private IP via the hub VCN's subnet routing). Third, the Hub VCN must have a route table directing `10.2.0.0/16` to the NVA, and the NVA must have a return route for `10.1.0.0/16` back through the DRG to Spoke A.

The import route distribution for the DRG route table that serves Spoke A's attachment needs to accept routes from the Hub VCN attachment and from the FastConnect attachment. It should not, by default, accept routes from Spoke B's attachment directly, because that would enable Spoke A to reach Spoke B without transiting the NVA. The route distribution policy enforces the topology invariant.

The following Terraform block configures a DRG import route distribution that accepts routes from FastConnect and Hub VCN attachments only, used by the DRG route table serving spoke VCN traffic:

```hcl
resource "oci_core_drg_route_distribution" "spoke_import_dist" {
  drg_id            = oci_core_drg.main_drg.id
  display_name      = "spoke-import-distribution"
  distribution_type = "IMPORT"
}

resource "oci_core_drg_route_distribution_statement" "accept_from_fastconnect" {
  drg_route_distribution_id = oci_core_drg_route_distribution.spoke_import_dist.id
  action                    = "ACCEPT"
  priority                  = 10

  match_criteria {
    match_type      = "DRG_ATTACHMENT_TYPE"
    attachment_type = "VIRTUAL_CIRCUIT"
  }
}

resource "oci_core_drg_route_distribution_statement" "accept_from_hub_vcn" {
  drg_route_distribution_id = oci_core_drg_route_distribution.spoke_import_dist.id
  action                    = "ACCEPT"
  priority                  = 20

  match_criteria {
    match_type        = "DRG_ATTACHMENT_ID"
    drg_attachment_id = oci_core_drg_attachment.hub_vcn_attachment.id
  }
}

resource "oci_core_drg_route_table" "spoke_drg_rt" {
  drg_id                           = oci_core_drg.main_drg.id
  display_name                     = "spoke-drg-route-table"
  import_drg_route_distribution_id = oci_core_drg_route_distribution.spoke_import_dist.id
  is_ecmp_enabled                  = false
}
```

The `priority` field within distribution statements is an integer where lower values are evaluated first. When multiple statements match, the first matching statement's action applies. Setting FastConnect routes at priority 10 and VCN attachment routes at priority 20 ensures that on-premises prefixes learned through FastConnect are not accidentally shadowed by more-specific routes leaked from a VCN.

### FastConnect Architecture

FastConnect is Oracle's dedicated physical connectivity product, equivalent to AWS Direct Connect or Azure ExpressRoute. A FastConnect connection is a physical cross-connect at a colocation facility where Oracle maintains a network presence, terminating on a FastConnect location port. This physical port is associated with a Virtual Circuit, which is an OSI Layer 2 construct carrying 802.1Q VLAN tags to multiplex multiple logical connections over the same physical port.

FastConnect supports two peering models. Private Peering attaches the virtual circuit to a DRG, extending a customer's private RFC 1918 address space into OCI. Public Peering attaches to Oracle's public endpoints, providing dedicated bandwidth to Oracle Cloud public IP ranges without transiting the internet. Most enterprise architectures use Private Peering exclusively and reach public Oracle services through the Service Gateway from within their VCNs.

The BGP session in FastConnect Private Peering runs between the customer edge router and Oracle's edge router. The customer advertises their on-premises prefixes over BGP; Oracle advertises the VCN CIDR blocks (and any other prefixes you configure the DRG to export). The BGP AS number on the Oracle side is `31898`. Customers must use a private ASN (64512-65535) or their own registered public ASN. BFD (Bidirectional Forwarding Detection) is supported and strongly recommended for sub-second failover detection.

FastConnect bandwidth tiers range from 1 Gbps to 10 Gbps per virtual circuit, with the total bandwidth shared across all virtual circuits on the same physical port. For redundancy, Oracle requires (and billing incentivizes) provisioning FastConnect circuits in pairs across two physically diverse colocation paths. The two circuits form an active/active or active/passive BGP pair against the same DRG, and the DRG's ECMP capability (enabled via `is_ecmp_enabled = true` on the DRG route table) can load-balance across both paths at the flow level.

---

## 3. High-Performance Optimization & Failure Modes

### Route Table Scaling Limits and Black Hole Detection

A single VCN route table supports up to 200 route rules. This limit is not arbitrary: it reflects the size of the forwarding table that can be maintained with bounded lookup latency at the fabric's forwarding layer. In practice, reaching 200 rules signals an architectural problem rather than a capacity constraint. If you are manually enumerating hundreds of destination CIDRs in a route table, you are almost certainly managing a topology that should be expressed through DRG route distribution policies and VCN peering rather than through static route aggregation.

The practical failure mode of an oversized route table is not a hard error but gradual operational brittleness. Each new VCN, on-premises range, or service endpoint requires a manual rule addition. When those rules fall out of sync with the actual topology (because someone deleted a peered VCN without cleaning up its route entry, or an on-premises subnet was renumbered), the stale rules become black holes. OCI does not currently provide native route table reachability analysis, so detecting these black holes requires deliberate tooling.

The OCI CLI provides direct route table introspection. The following command retrieves all route rules for a given route table and formats them as a readable table, which you can diff against a Terraform state file or a network documentation database:

```bash
oci network route-table get \
  --rt-id ocid1.routetable.oc1.iad.aaaaaaaa... \
  --query 'data."route-rules"[*].{destination:destination,"target-type":"network-entity-id"}' \
  --output table
```

For DRG route table inspection, the DRG route table learned routes endpoint exposes the full RIB (Routing Information Base) of a DRG route table, including routes learned dynamically through BGP on FastConnect and routes injected by VCN attachments:

```bash
oci network drg-route-table list-drg-route-rules \
  --drg-route-table-id ocid1.drgroutetable.oc1.iad.aaaaaaaa... \
  --route-type RIB \
  --all \
  --query 'data[*].{destination:destination,"next-hop-type":"next-hop-type","next-hop":destination}' \
  --output table
```

This distinction between the FIB (Forwarding Information Base, the active routes) and the RIB matters when debugging asymmetric routing: a route may be present in the RIB but not installed in the FIB due to a more-specific competing route from another attachment. The `--route-type FIB` flag narrows the query to active forwarding entries.

### Asymmetric Routing and Connection Tracking Failures

Asymmetric routing is the source of a large class of intermittent connectivity failures in multi-attachment DRG topologies. It occurs when the forward path for a TCP flow traverses a different sequence of network elements than the return path, invalidating the connection tracking state maintained at the VNIC boundary.

Consider a VM in Spoke A establishing a TCP connection to a VM in Spoke B, with both spokes attached to a shared DRG and transit routing through an NVA in the hub. The forward SYN travels: Spoke A VNIC → Spoke A subnet RT → DRG → Hub VCN RT → NVA → Hub VCN RT → DRG → Spoke B VCN RT → Spoke B VNIC. The stateful security rules on Spoke A's VNIC create a connection tracking entry for this five-tuple. The return SYN-ACK must traverse exactly the reverse path and arrive at Spoke A's VNIC for the connection tracker to recognize it as a return packet and permit it.

If the return routing is misconfigured such that the SYN-ACK takes a different path and arrives at Spoke A's VNIC from an unexpected source (say, it bypasses the NVA and arrives via a direct DRG route), the VNIC's connection tracker will not find a matching entry for a packet arriving from the NVA IP with that destination port, and the packet will be dropped. The TCP session stalls, the client retransmits the SYN, and the symptoms appear as intermittent timeouts rather than hard failures, making diagnosis extremely difficult without packet capture at the VNIC level.

OCI provides VNIC-level flow log capture through the VCN Flow Logs feature, which records five-tuple flow metadata (not packet payload) to OCI Logging. Enabling flow logs on a subnet and filtering for REJECT actions against a specific source IP is the fastest way to confirm asymmetric routing as the failure mechanism:

```bash
# Query VCN Flow Logs via Logging Query Language for REJECT events on a specific VNIC
oci logging-search search-logs \
  --search-query "search \"ocid1.compartment.oc1..aaaaaaaa\" | \
    source='vcn-flow-logs' | \
    logContent.data.action = 'REJECT' and \
    logContent.data.'source-port-range'.min = 443 | \
    summarize count() as reject_count by logContent.data.'source-address'" \
  --time-start "2024-01-15T00:00:00Z" \
  --time-end "2024-01-15T01:00:00Z"
```

### Security Rule Drift and NSG Lifecycle Management

Security rule sprawl is the security equivalent of route table black holes. In long-lived environments, NSG rules accumulate over time as services are added, migrated, and decommissioned. The decommissioning step, in practice, rarely includes a thorough cleanup of security rules because the people doing decommissioning are rarely the same people who originally wrote the rules, and the documentation linking compute instances to NSG memberships is typically stale.

The architectural mitigation is to treat NSG membership as infrastructure-as-code with the same lifecycle management as compute resources. When a compute instance is managed by Terraform and its NSG memberships are expressed in the same Terraform module, destroying the instance also destroys the NSG membership. The NSG rules themselves, however, should be reviewed periodically for rules whose `source_type` or `destination_type` references an NSG that no longer has any VNIC members. An NSG with zero members is not a security risk in itself (no traffic can match it) but is an operational liability because future additions to that NSG will inherit rules that may no longer reflect current intent.

The following OCI CLI command identifies NSGs within a compartment that have zero VNIC associations, which are candidates for decommissioning review:

```bash
oci network nsg list \
  --compartment-id ocid1.compartment.oc1..aaaaaaaa... \
  --all \
  --query 'data[?contains(@.`lifecycle-state`, `AVAILABLE`)].[id,"display-name"]' \
  --output table | while read nsg_ocid display_name; do
    vnic_count=$(oci network nsg list-vnics \
      --nsg-id "$nsg_ocid" \
      --all \
      --query 'length(data)' \
      --raw-output 2>/dev/null)
    if [ "$vnic_count" = "0" ]; then
      echo "EMPTY NSG: $display_name ($nsg_ocid)"
    fi
  done
```

### FastConnect Redundancy and BGP Failover Timing

FastConnect's failure mode taxonomy has two distinct layers. Physical layer failures (fiber cut, transceiver failure, cross-connect port failure) are detected by the optical layer and propagate to the BGP session through interface down events, triggering BFD timeout or BGP hold-timer expiry. BFD with a 300ms interval and a multiplier of 3 gives 900ms detection time, after which BGP withdraws the failed circuit's routes and the DRG reconverges to the surviving circuit. Without BFD, the BGP hold-timer (default 90 seconds in most configurations) governs failover time, which is unacceptable for production workloads.

Control-plane failures (BGP session reset due to software bugs, configuration errors, or route policy changes) may leave the physical layer intact while the logical session fails. This is why BFD is necessary but not sufficient: BGP hold-down timers must also be tuned. Oracle's FastConnect BGP supports a minimum hold time of 10 seconds with a keepalive interval of 3.33 seconds, which provides 10-second maximum detection time for control-plane failures independent of BFD.

The more subtle failure mode is a BGP route flap: a prefix is withdrawn and re-advertised rapidly due to instability on the customer edge router. Each flap triggers a DRG route table reconvergence event. If the flapping prefix is a default route or a highly aggregated summary, every flow in the VCN that traverses the DRG experiences a brief traffic disruption during each reconvergence. The mitigation is BGP route dampening on the customer edge, combined with specific-prefix advertising (advertising individual /24s rather than a single aggregate) so that instability in one prefix does not affect traffic flows using other prefixes.

For the highest-availability architectures, Oracle supports dual-port FastConnect where each physical cross-connect terminates on a different FastConnect location device (not just a different port on the same device). The two locations must be in physically diverse facilities with no shared optical path. Combined with ECMP load balancing on the DRG and BFD on both circuits, this configuration provides sub-second failover with zero single points of failure from the customer's on-premises router to the VCN's implicit router.

The complete production checklist for a resilient OCI network foundation, expressed as the operational invariants that every deployment should enforce, is not a matter of best-effort recommendations. It is the difference between a network that is correct under failure conditions and one that works only under nominal conditions. CIDR planning must preclude overlap before peering. Route tables must be managed as code with explicit lifecycle coupling to the resources they serve. Security rules must be stateful unless there is a measured performance justification for stateless. DRG route distributions must encode the topology's trust boundaries, not just its reachability requirements. And FastConnect must be provisioned in redundant pairs with BFD enabled before any production workload depends on the path.
