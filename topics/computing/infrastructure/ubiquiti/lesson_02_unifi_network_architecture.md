# Lesson 2: UniFi Network Architecture

## 1. First-Principles Intuition & Invariants

Every production network, regardless of scale, faces the same fundamental tension: the need for a consistent, authoritative view of the entire topology while simultaneously forwarding packets at line rate across every individual link. These two concerns, management and forwarding, operate at different timescales, tolerate different failure modes, and demand different computational resources. A human operator configuring a VLAN policy thinks in seconds and minutes. A switching ASIC making a forwarding decision thinks in nanoseconds. Conflating these two concerns into a single monolithic device produces the closed, vertically integrated boxes that defined enterprise networking for decades. Separating them cleanly is the architectural insight that defines modern software-defined networking, and it is precisely what the UniFi ecosystem operationalizes for practitioners who lack the budget of a hyperscaler but need the operational hygiene of one.

The formal separation between the **control plane** and the **data plane** is worth establishing from first principles before touching a single CLI command. The data plane is the hardware and firmware path responsible for frame and packet forwarding: MAC address lookups in a CAM table, IP route resolution against an FIB, ACL enforcement at wire speed, and queue scheduling under congestion. This work is done by dedicated ASICs or FPGAs that operate independently of any management CPU. The control plane is the logical layer that *computes* the state these forwarding structures should contain: it runs spanning tree, processes OSPF LSAs, evaluates DHCP leases, and translates operator intent into concrete forwarding rules that are then pushed down into the data plane hardware. In traditional routers and switches these two planes share the same physical chassis and sometimes the same CPU, creating a single point of failure where a routing protocol storm can starve the forwarding path of CPU cycles or vice versa.

UniFi's architectural response to this problem is to externalize the control plane almost entirely. Each UniFi device, whether an AP, switch, or gateway, runs a lightweight agent whose primary job is to execute configuration it receives from a central controller and report telemetry back to it. The UniFi Network Application (historically called the UniFi Controller) is that central controller: a JVM-hosted process that maintains the authoritative configuration database, reconciles desired state against observed device state, and communicates changes outward. The devices themselves are not dumb pipes; they retain local forwarding intelligence and can survive a controller outage while continuing to forward traffic. But they cannot be meaningfully reconfigured, and they cannot participate in coordinated network-wide policies, without the controller present and reachable. This is the central invariant of the entire platform: **devices are configuration consumers, not configuration authorities**.

Understanding this invariant explains behaviors that would otherwise seem like bugs. When a UniFi AP loses its inform connection to the controller, it does not revert to some factory default; it continues operating on the last received configuration indefinitely. This is deliberate. The data plane never stops. What stops is the ability to push new state into it. This "frozen last-known-good" behavior is architecturally equivalent to what a Kubernetes node does when it loses contact with the API server: the kubelet continues running the last reconciled pod spec while attempting to reconnect, refusing to tear down running workloads based on a transient network partition. The analogy is not superficial. Both systems are implementing the same reconciliation loop pattern under the same failure assumptions.

The UniFi ecosystem spans several hardware families that share this controller-managed model but differ significantly in their internal architecture. UniFi APs handle 802.11 radio management, roaming coordination, and SSID-to-VLAN mapping. UniFi switches (the US and USW lines) handle Layer 2 forwarding, 802.1Q VLAN trunking, RSTP, and PoE budget management. UniFi Security Gateways and UniFi Dream Machines handle Layer 3 routing, stateful firewalling, NAT, and in some configurations IDS/IPS via Suricata. The Network Application orchestrates all of these device classes through a single pane of glass, with each class exposing a different capability surface to the controller's configuration model. What unifies them is not the hardware but the communication protocol and configuration schema they all speak.

## 2. Core Architecture & Mechanics

### The UniFi Controller: State Machine and Persistence Model

The Network Application is a Java process built on top of MongoDB as its primary persistence layer and an embedded web server (historically Jetty, later migrated toward a more modular servlet container) for the management UI and API surface. MongoDB's document model maps naturally to the controller's configuration schema: each site, device, network, WLAN, user, and event is stored as a JSON document in a named collection. The schema is not rigidly normalized in the relational sense; device configuration documents embed nested subdocuments representing port overrides, radio settings, and VLAN assignments, trading strict normalization for read efficiency since the controller frequently needs to serialize the complete configuration for a single device in one operation.

The core collections that practitioners need to understand are as follows. The `device` collection holds the persistent configuration state for every adopted device, keyed by MAC address. The `site` collection holds site-level settings including network topology, WLAN definitions, and firewall rules. The `event` and `alarm` collections store time-series operational data. The `stat` collections hold aggregated counters pushed up from devices on a regular polling interval. When you modify a port's VLAN assignment in the UI, the controller writes the new configuration document to MongoDB and then marks that device as having a pending configuration delta. The provisioning pipeline picks up this delta and pushes it to the device during the next inform cycle.

The inform cycle is the heartbeat of the entire system. Every UniFi device periodically sends an HTTP POST to a URL of the form `http://<controller>:8080/inform`. The body of this POST is a binary payload encrypted with a device-specific key (AES-128-CBC with a key derived from the device's authentication credentials) containing a JSON object reporting the device's current status: uptime, firmware version, radio statistics, interface counters, connected clients, and a hash of its current configuration. The controller receives this inform, decrypts it, updates its local view of the device's operational state in the `device` collection, and responds with one of three possible responses: an empty acknowledgment meaning the device's state is consistent with desired configuration, a new configuration payload telling the device to apply changes, or a command such as a reboot or firmware upgrade instruction. The default inform interval is 30 seconds, though devices in an adoption-pending state poll more aggressively at roughly five-second intervals.

```mermaid
flowchart TD
    subgraph unifi_app ["UniFi Network Application"]
        REST["REST API\n(HTTPS / 8443)"]
        INFORM["Inform Loop Handler\n(HTTP 8080)"]
        SERIAL["Config Serializer"]
        BROWSER["Browser / unifi-os dashboard"]

        subgraph mongo ["MongoDB"]
            COLS["device · site · wlan\nnetwork · stat"]
        end

        REST -->|"incoming request"| INFORM
        INFORM -->|"persist state"| mongo
        INFORM -->|"diff & provision"| SERIAL
        BROWSER -->|"HTTPS 8443"| REST
    end

    subgraph unifi_device ["UniFi Device (AP / Switch / Gateway)"]
        MCAD["mcad\n(inform agent)"]
        UBNT["ubnt-util\n(config applier)"]
        SYSWRAP["syswrapper / hostapd / mca-ctrl\n(data plane config)"]

        subgraph fwd_hw ["Forwarding Hardware (ASIC / mac80211 / OpenWrt)"]
            HW[" "]
        end

        MCAD -->|"apply config"| UBNT
        UBNT -->|"program hardware"| SYSWRAP
        SYSWRAP --> fwd_hw
    end

    MCAD -->|"HTTP 8080 inform POST\n(AES-128-CBC payload)"| INFORM
    REST -->|"HTTPS 8443\n(UI / API)"| BROWSER
    SERIAL -->|"provisioned config\nHTTPS 8443"| MCAD
```

### Device-Side Agent Architecture

On the device itself, the inform loop is managed by a process called `mcad` (Management Controller Agent Daemon). `mcad` is responsible for assembling the status payload, encrypting it, posting it to the controller's inform URL, and handling the response. When the response contains a new configuration blob, `mcad` hands the decrypted JSON to a configuration application layer that translates the abstract controller configuration model into device-specific system calls, UCI commands (on OpenWrt-derived platforms), or proprietary UBNT configuration utilities.

This translation step is where the control plane abstraction becomes concrete. The controller's configuration model expresses intent at a high level: "SSID `corp-wifi` should be tagged to VLAN 10, should require WPA2-Enterprise authentication against RADIUS server 192.168.1.5, and should enforce a client isolation policy." The device-side applier takes this intent and writes it into `hostapd` configuration files for the wireless daemon, programs the kernel bridge configuration to enforce the VLAN tagging, and updates `ebtables` or `nftables` rules for client isolation. The controller never speaks directly to `hostapd`; it speaks to `mcad`, which speaks to the abstraction layer, which speaks to the actual system services. This layering means that Ubiquiti can ship radically different hardware, running different base operating systems, while presenting a uniform capability model upward to the controller.

Adoption is the initial handshake process that establishes the trust relationship between a factory-fresh device and a specific controller instance. A new device arrives with a default inform URL pointing to `http://unifi:8080/inform`, relying on DNS resolution of the name `unifi` to find the controller on the local network. When the controller receives an inform from an unadopted device, it places that device in a pending state visible in the UI. When the operator clicks "Adopt," the controller responds to the next inform with an adoption payload containing the controller's address, the site credentials, and an SSH-based device key. The device commits these credentials to non-volatile storage, switches its inform target to the specific controller URL, and re-encrypts subsequent payloads with the new controller-specific key. After this point, only that controller instance can provision the device without first performing a factory reset.

### Network Topology and VLAN Propagation

A production UniFi network is organized around the concept of *networks* defined in the controller, each of which corresponds to a 802.1Q VLAN with an associated IP subnet, DHCP scope, and firewall zone. The controller's switch configuration model uses a port *profile* abstraction: each switch port is assigned a profile that specifies its native (untagged) VLAN and the set of VLANs that should be carried as tagged frames. When this profile assignment changes, the controller serializes the new port configuration into the device's inform response and the switch programs its ASIC accordingly.

The propagation path from controller intent to data-plane forwarding state follows a strict sequence. First, the operator defines or modifies a network in the controller UI, which writes a new document to the `network` collection in MongoDB. Second, the controller's provisioning engine detects that one or more devices are affected by this change and flags them as requiring reprovisioning. Third, on the next inform cycle for each affected device, the controller includes the updated configuration in its response. Fourth, the device's configuration applier programs the hardware. The entire round-trip latency from UI save to active forwarding state is bounded by the inform interval, typically under 60 seconds in a healthy deployment.

```mermaid
sequenceDiagram
    participant Operator
    participant ControllerUI as Controller UI (HTTPS 8443)
    participant MongoDB
    participant ProvisionEngine as Provision Engine
    participant Device as UniFi Device (mcad)
    participant DataPlane as Forwarding Hardware

    Operator->>ControllerUI: Modify VLAN assignment on port 5
    ControllerUI->>MongoDB: Write updated device document
    MongoDB-->>ProvisionEngine: Change detected (watch/poll)
    ProvisionEngine->>MongoDB: Mark device pending provision

    loop Every 30s inform cycle
        Device->>ControllerUI: HTTP POST /inform (status payload)
        ControllerUI->>ProvisionEngine: Check for pending config
        ProvisionEngine->>ControllerUI: Return config delta
        ControllerUI-->>Device: Encrypted config response
        Device->>Device: mcad decrypts, applies config
        Device->>DataPlane: Program VLAN tables / ACLs
        DataPlane-->>Device: Acknowledge
        Device->>ControllerUI: Next inform confirms applied state
    end
```

### Configuration Persistence and the cfgversion Hash

Each device maintains a configuration version identifier, the `cfgversion` field in its inform payload, which is a hash of its currently applied configuration state. The controller compares the incoming `cfgversion` against the hash of the configuration it believes the device should have. If they match, no provisioning is needed and the response is a lightweight acknowledgment. If they diverge, the controller sends the full configuration document regardless of what changed. This is not a delta protocol; it is a full-state replacement on every mismatch. This design trades bandwidth efficiency for correctness: there is no accumulation of partially applied patches, no dependency ordering problem, and no reconciliation required between incremental updates. The device receives a complete authoritative configuration and applies it atomically.

This full-replacement model has direct implications for large switch deployments. A USW-48-Pro with 48 ports and multiple VLAN assignments produces a configuration document that is not trivially small. On slow or congested management networks, frequent reprovisioning of many devices simultaneously can cause visible inform latency. Practitioners who manage campus-scale deployments with hundreds of switches should be aware that mass VLAN policy changes will trigger a reprovisioning wave across the entire fleet, and they should schedule such changes during maintenance windows.

### UniFi OS and the Console Architecture

More recent Ubiquiti hardware, specifically the Dream Machine line (UDM, UDM-Pro, UDM-SE, UDR) and the CloudKey Gen2, runs UniFi OS, a container-orchestration layer built on top of a Linux base system. UniFi OS uses Docker to run the Network Application, the Protect NVR application, the Access controller, and other UniFi applications as isolated containers with shared access to a local MongoDB instance and a shared network namespace for inter-container communication.

From the perspective of a kernel or systems engineer, UniFi OS is a constrained container host with a curated set of base images managed entirely by Ubiquiti's update infrastructure. The operator interacts with the appliance through a local or cloud-brokered HTTPS portal rather than directly managing container lifecycle. The `/data` directory on the host is bind-mounted into the Network Application container at `/usr/lib/unifi/data`, providing the MongoDB data files, the keystore (for the HTTPS certificate), and the configuration state with persistence across container restarts and firmware upgrades. Understanding this mount structure is essential for backup and restore operations, since a complete backup of a UniFi installation requires capturing the MongoDB dump and the keystore file, not simply the Network Application JAR.

## 3. High-Performance Optimization & Failure Modes

### Controller Availability and the Split-Brain Problem

The most consequential failure mode in a UniFi deployment is controller unavailability. Because devices continue forwarding on their last provisioned state, a controller outage is operationally silent to end users for as long as the network configuration remains stable. The danger is not immediate packet loss; it is configuration drift and the loss of visibility. When the controller comes back online after an extended outage, it performs a reconciliation pass against all devices. If a device was factory-reset and re-adopted during the outage with a different configuration, or if manual SSH-based configuration changes were made directly to devices during the outage, the controller's next provisioning cycle will overwrite those changes. This is not a bug; it is the correct behavior of a system that considers the controller the authoritative configuration source. But it is a failure mode that administrators must anticipate and document clearly in their operational runbooks.

The correct mitigation for controller availability is to run the Network Application on infrastructure with appropriate redundancy. For small to medium deployments the CloudKey Gen2 Plus or a Dream Machine console provides adequate reliability. For environments where controller downtime is unacceptable, running the Network Application as a containerized service on a highly available Kubernetes cluster or a VM with automatic failover ensures that the management plane remains reachable even during host failures. The controller's data directory, which contains the MongoDB files, should be on persistent storage with regular automated snapshots. The controller does not natively support active-active clustering; it is a single-instance application, so the HA story is entirely about recovery time, not about simultaneous multi-instance operation.

### Scaling the Inform Loop

As a deployment grows beyond a few dozen devices, the inform loop becomes a performance consideration. Each inform is an HTTP request with a cryptographic payload, MongoDB reads and writes, and potentially a full configuration serialization. At 30-second intervals, a deployment of 500 devices generates roughly 17 inform transactions per second continuously. The controller's Java process is single-threaded in its core inform handling path in older versions, though more recent releases have improved concurrency. The MongoDB instance co-located with the controller on a CloudKey is the primary bottleneck: it is running on consumer-grade flash storage with limited IOPS, and under heavy inform load combined with statistics writes, it will exhibit IO wait that manifests as delayed inform responses and sluggish UI behavior.

For large deployments, the recommended architecture separates the MongoDB instance from the Network Application. Running MongoDB on a dedicated host with SSD-backed storage and adequate RAM to fit the working set in memory removes the storage bottleneck. The Network Application is configured to connect to this external MongoDB instance via its `system.properties` configuration file, which allows the two components to scale independently.

```properties
# /usr/lib/unifi/data/system.properties
# External MongoDB configuration
db.mongo.uri=mongodb://mongouser:mongopass@192.168.1.10:27017/ace
db.mongo.db=ace
db.mongo.db.stat=ace_stat
db.mongo.db.audit=ace_audit
```

Practitioners should also monitor the size of the `stat` and `event` collections over time. The controller accumulates per-client and per-device statistics on configurable retention windows, and these collections can grow to tens of gigabytes on busy networks over months of operation. MongoDB's performance degrades as collection size approaches available RAM, since it can no longer cache the working set of index pages. Setting aggressive data retention policies in the controller settings, limiting per-client statistics to 7 days and site statistics to 30 days rather than the defaults, is a critical operational hygiene step for any deployment older than a few months.

### VLAN and Trunk Misconfiguration Failure Patterns

The most common operational failure in UniFi switch and AP deployments is a VLAN trunk misconfiguration that silently drops traffic for a subset of clients. Consider a deployment where an AP is connected to a switch port, and the AP is broadcasting two SSIDs: one mapped to the native (management) VLAN and one mapped to a tagged guest VLAN. The AP uplink port on the switch must be configured as a trunk port carrying both VLANs. If the port profile assigns the native VLAN correctly but omits the guest VLAN from the tagged VLAN set, the AP will receive its management-plane frames (allowing the inform loop to function normally) but guest client traffic will be silently discarded at the switch egress. The AP will appear healthy in the controller UI, its inform loop will be functioning, but guest clients will be unable to reach the gateway.

Diagnosing this class of failure requires direct inspection of the switch's VLAN programming, which the controller exposes through its device detail panel showing per-port VLAN assignments. The authoritative diagnostic command is to SSH into the affected switch and inspect the hardware VLAN table directly:

```bash
# SSH into a UniFi switch running EdgeOS or the switch firmware
ssh admin@<switch-ip>

# Show the current VLAN database on a USW device
mca-cli
# Within mca-cli:
show vlan

# Alternatively, inspect the running configuration directly
cat /tmp/running.cfg | grep -A 5 "port 5"

# On newer switches with a Linux userspace, check bridge VLAN state
bridge vlan show

# Confirm trunk port VLAN membership
ip link show
cat /proc/net/vlan/config
```

The output of `bridge vlan show` on a correctly configured trunk port carrying VLANs 1, 10, and 20 should resemble the following, where `pvid` indicates the native untagged VLAN and the remaining entries are carried as tagged frames:

```text
port              vlan-id
eth0              1 PVID Egress Untagged
                  10
                  20
```

If VLAN 20 is absent from this output but should be present, the switch's data plane is not carrying that VLAN on this port regardless of what the controller UI displays. This divergence between controller-believed state and device-actual state indicates a provisioning failure: the device received a configuration that it was unable to apply, or the inform containing the corrective configuration has not yet been processed. Forcing a reprovision from the controller UI, or triggering it from the CLI, resolves most cases:

```bash
# Force reprovision from the device's SSH shell
# This command instructs the device to re-fetch and re-apply its configuration
mca-ctrl -t connect

# Alternatively, trigger a device provision from the controller REST API
# Replace SITE_ID, DEVICE_MAC, and your auth cookie appropriately
curl -k -X POST \
  --cookie "unifises=<session_cookie>" \
  "https://<controller>:8443/api/s/<site_id>/cmd/devmgr" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"force-provision","mac":"aa:bb:cc:dd:ee:ff"}'
```

### Firmware Upgrade Strategy and Atomic Rollback

Firmware upgrades on UniFi devices follow the same inform-based delivery mechanism as configuration changes. The controller stages a firmware binary and responds to the target device's next inform with an upgrade command containing a URL from which the device should download the firmware image. The device downloads the image, verifies its signature, writes it to the inactive partition (UniFi devices use a dual-partition A/B scheme on most platforms), updates the boot pointer to the new partition, and reboots. If the new firmware fails to establish a successful inform connection within a watchdog timeout, the bootloader rolls back to the previously active partition automatically.

This A/B partition model is the correct approach to managing firmware on embedded devices at scale, and it is worth making explicit in operational runbooks. A firmware upgrade that leaves the device unable to communicate is not a brick; it is a temporary failure that the device self-heals within a configurable timeout. The practical implication is that administrators should stagger firmware upgrades across a fleet rather than upgrading all devices simultaneously. If a firmware version has a critical bug that prevents inform connectivity on a specific hardware revision, a staggered rollout limits the blast radius to the first upgrade batch, and the automatic rollback ensures those devices return to service without manual intervention.

The controller's upgrade interface allows device-by-device or bulk upgrades, with the ability to target specific firmware versions from Ubiquiti's firmware manifest or from a locally hosted file. For air-gapped deployments that cannot reach Ubiquiti's CDN, hosting firmware images on an internal HTTP server and configuring the controller's firmware URL override is the correct pattern:

```bash
# Download a specific firmware image for offline use
# Check the Ubiquiti firmware manifest for the correct URL for your hardware
wget https://dl.ui.com/unifi/firmware/U7PG2/5.43.23+13534/BZ.qca956x.5.43.23+13534.200528.1719.bin \
  -O /var/www/html/firmware/U7PG2-5.43.23.bin

# The controller can be pointed to this internal URL per-device
# via the REST API device upgrade endpoint:
curl -k -X POST \
  --cookie "unifises=<session_cookie>" \
  "https://<controller>:8443/api/s/<site_id>/cmd/devmgr/upgrade-external" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://192.168.1.100/firmware/U7PG2-5.43.23.bin",
    "mac": "aa:bb:cc:dd:ee:ff"
  }'
```

### Wireless Roaming Architecture and Coordination

For Wi-Fi deployments with multiple APs serving mobile clients, roaming behavior is a critical performance dimension. UniFi implements 802.11r Fast BSS Transition and 802.11k neighbor reports natively, and these features are configured at the WLAN level in the controller. The controller's role in roaming is not to make per-client handoff decisions in real time; it is to pre-distribute the information that makes client-driven handoffs faster. By enabling 802.11k, each AP advertises its neighbor list to associated clients, allowing those clients to identify candidate APs for roaming without having to perform a full passive scan of all channels. By enabling 802.11r, the re-authentication handshake with the target AP is abbreviated because the Pairwise Master Key material is pre-distributed via the controller-managed PMK-R0 key holder.

The controller also coordinates the Band Steering and Minimum RSSI features, which are management-plane policies enforced through 802.11 association response handling. When Minimum RSSI is configured, an AP will respond to probe requests and association attempts from clients whose signal falls below the threshold with a disassociation frame, pushing the client to seek a closer AP. This policy is effective for preventing sticky-client behavior, but it must be tuned carefully: setting the threshold too aggressively in a sparse deployment leaves clients with no eligible AP and breaks connectivity. The correct threshold value depends on the specific RF environment and cell sizing, determined through a site survey rather than guessed from defaults.

The underlying lesson across all of these operational dimensions is that the UniFi architecture's strength, its centralized configuration authority and uniform inform-based delivery, is also the boundary condition for every failure mode. When the system works, configuration intent propagates reliably from operator action to forwarding hardware in under a minute, across every device in the deployment, with full audit visibility in the controller's event log. When the system fails, the failure is almost always a disconnect between what the controller believes is true and what the hardware has actually applied. Every diagnostic workflow begins at that seam: comparing controller-recorded device state against device-reported runtime state, and tracing the inform protocol path that connects them.
