# Lesson 4: CNI Operational Patterns and Troubleshooting

## 1. First-Principles Intuition & Invariants

The Container Network Interface specification is, at its core, a contract. It defines a narrow, well-understood boundary between two independent systems — the container runtime (or its orchestrator) and the networking plugin — connected by nothing more than a JSON configuration file, a set of environment variables, and the binary execution model of Unix processes. Understanding why that contract exists the way it does, and what invariants it enforces, is the foundation for every operational decision you will make in production.

Before CNI existed, every container runtime invented its own networking model. Docker had `libnetwork` with its bridge, overlay, and macvlan drivers baked in. rkt had its own network configuration format. The proliferation of runtimes made networking a liability rather than a capability: operators needed to learn a different mental model for each environment, and plugin authors needed to implement the same VXLAN encapsulation logic four times over. CNI emerged from the same philosophical impulse that produced Unix pipes — not to solve networking once, but to define the smallest possible interface through which networking solutions could be composed without coupling.

The fundamental invariant of that interface is statelessness from the runtime's perspective. The runtime does not maintain a long-running connection to the CNI plugin. It does not negotiate capabilities or exchange heartbeats. It executes a binary, passes a network configuration on stdin along with a small set of environment variables describing the container's identity and the operation requested (ADD, DEL, CHECK, or VERSION), and reads back a result on stdout. The plugin is entirely responsible for maintaining whatever persistent state it needs — in a local file, a distributed key-value store, or a kernel data structure — to honor future invocations. This design means that any failure in the plugin's state management immediately becomes a failure in network reachability, and no amount of container runtime heroics can compensate for it.

The second invariant is that CNI operates at a single point in the container lifecycle: the creation and deletion of the network namespace. By the time the runtime calls the CNI ADD, the kernel has already created a fresh `netns` for the container. CNI's job is to populate that namespace: attach interfaces, assign addresses, configure routes, and program any necessary forwarding state in the host kernel or an external data plane. When the container terminates, DEL reverses those operations. There is no concept of a CNI "steady state" — only the moment of attachment and the moment of detachment. This is architecturally elegant but operationally unforgiving, because there is no retry loop, no health check, and no reconciliation daemon built into the protocol itself. If ADD fails partway through a chained plugin execution, the container scheduler will typically fail the pod and reschedule it, but the partially configured state left behind — an orphaned IPAM lease, a half-programmed iptables rule — becomes your problem.

The third invariant concerns identity. The runtime communicates the container's identity to the plugin through three environment variables: `CNI_CONTAINERID`, which is an opaque identifier the runtime generates; `CNI_NETNS`, the filesystem path to the network namespace (typically `/var/run/netns/<id>` or derived from `/proc/<pid>/ns/net`); and `CNI_IFNAME`, the interface name the plugin must create inside that namespace. The plugin has no access to Kubernetes pod metadata, namespace labels, or NetworkPolicy objects unless it reaches out to the Kubernetes API server itself. This means every CNI plugin that wants to enforce policy must solve the identity bootstrapping problem independently — either by trusting the `CNI_CONTAINERID`, by querying the API server with the pod's sandbox ID, or by relying on a local cache that was pre-populated by a background daemon. Understanding this identity gap explains the architectural split in production CNI implementations between the thin per-node binary (which executes the actual network attachment) and a persistent agent (like Calico's `felix`, Cilium's `cilium-agent`, or Flannel's `flanneld`) that maintains policy state and programs the data plane asynchronously.

## 2. Core Architecture & Mechanics

### Configuration Precedence and Plugin Selection Logic

The CNI runtime locates plugins and configurations through two independent directory paths. Configuration files live in a directory specified by `CNI_CONF_DIR`, defaulting to `/etc/cni/net.d/`. Plugin executables live in `CNI_PATH`, defaulting to `/opt/cni/bin/`. The runtime loads configuration files from the configuration directory, sorts them lexicographically by filename, and selects the **first** file. This is not a merge — it is a winner-take-all selection. The implication for operators is that file naming is a deployment invariant: naming your Calico configuration `10-calico.conflist` and accidentally leaving an old Flannel configuration named `05-flannel.conf` on a node means every new pod on that node gets Flannel, silently, until you trace the unexpected `10.244.x.x` addresses back to their source.

The file format comes in two varieties. A `.conf` file describes a single plugin invocation. A `.conflist` file describes a **chain** of plugins executed in order, where each plugin receives the previous plugin's result and can augment or transform it before passing it downstream. In practice, production deployments almost universally use `.conflist`, because separating the IPAM concern from the interface concern from the bandwidth shaping concern into composable plugins is the idiomatic CNI pattern. The conflist structure is worth examining closely because the semantics of chaining have operational implications that are not immediately obvious from the documentation.

```json
{
  "cniVersion": "1.0.0",
  "name": "production-net",
  "plugins": [
    {
      "type": "calico",
      "log_level": "info",
      "log_file_path": "/var/log/calico/cni/cni.log",
      "datastore_type": "kubernetes",
      "nodename": "__KUBERNETES_NODE_NAME__",
      "mtu": 1440,
      "ipam": {
        "type": "calico-ipam",
        "assign_ipv4": "true",
        "assign_ipv6": "false"
      },
      "policy": {
        "type": "k8s"
      },
      "kubernetes": {
        "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
      }
    },
    {
      "type": "bandwidth",
      "ingressRate": 10000000,
      "ingressBurst": 20000000,
      "egressRate": 10000000,
      "egressBurst": 20000000
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}
```

When containerd processes an ADD for a new pod using this conflist, it executes `calico` first, which creates the `eth0` veth pair, assigns the IPAM address, programs the routing, and writes its result into a JSON `PrevResult` structure. It then executes `bandwidth`, which receives the `PrevResult` on stdin and uses it to identify the correct interface before attaching tc-based traffic shaping to the host-side veth. Finally, `portmap` receives the final accumulated result and programs `iptables` DNAT rules for any `hostPort` entries the pod requested. If `bandwidth` fails — say, because the `tc` binary is missing from the node — the portmap plugin never runs, Calico has already assigned an IP, and the pod ends up with an address but no port forwarding and no tc qdiscs. The partial state is real and persistent.

Configuration merging within a single plugin's stanza follows standard JSON semantics — there is no deep-merge of overlapping keys. If your plugin configuration specifies a key at the top level and a Helm chart or DaemonSet init container overwrites that file, the last write wins entirely. This creates a hazard in GitOps workflows where multiple systems believe they own `/etc/cni/net.d/`: the DaemonSet that wrote the file on node startup, the configuration management tool that rendered it from a Helm chart, and potentially an operator that patches it in response to cluster events. Establishing a single authoritative writer for the CNI configuration directory is an operational requirement, not a convenience.

### Execution Model and Signal Paths

The sequence of events from pod scheduling to network reachability involves at least four independent processes: the kubelet, containerd (or CRI-O), the CNI binary, and any background daemon the CNI plugin depends on. Understanding the precise handoff points is essential for attributing failures correctly.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Node                             │
│                                                                     │
│  ┌──────────┐    gRPC/CRI     ┌───────────────────────────────┐    │
│  │  kubelet │ ─────────────► │       containerd (shim)        │    │
│  │          │ ◄───────────── │                                │    │
│  └──────────┘  PodSandboxID  │  1. Create netns               │    │
│                              │  2. exec CNI binary (ADD)      │    │
│                              │     stdin: conflist + args     │    │
│                              │     env: CNI_CONTAINERID       │    │
│                              │          CNI_NETNS             │    │
│                              │          CNI_IFNAME=eth0       │    │
│                              │          CNI_COMMAND=ADD       │    │
│                              │  3. Read stdout (Result JSON)  │    │
│                              └──────────┬────────────────────┘    │
│                                         │ fork/exec                │
│                                         ▼                          │
│                              ┌──────────────────────┐             │
│                              │   CNI Plugin Binary   │             │
│                              │  (e.g. /opt/cni/bin/  │             │
│                              │        calico)        │             │
│                              │                       │             │
│                              │  reads API server     │             │
│                              │  programs veth pair   │             │
│                              │  calls IPAM plugin    │             │
│                              │  writes routes        │             │
│                              └──────────┬────────────┘             │
│                                         │ Unix socket / local file │
│                                         ▼                          │
│                              ┌──────────────────────┐             │
│                              │  Background Daemon    │             │
│                              │  (felix / flanneld /  │             │
│                              │   cilium-agent)       │             │
│                              │                       │             │
│                              │  programs iptables    │             │
│                              │  programs routes      │             │
│                              │  syncs policy state   │             │
│                              └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

The critical insight this diagram conveys is that the CNI binary execution is **synchronous and blocking** from containerd's perspective. Containerd will not return the `RunPodSandbox` response to kubelet until the CNI ADD either succeeds or fails. The timeout for this operation is controlled by the runtime — containerd uses a 50-second deadline by default, configurable via the CNI configuration's `timeout` field. If your plugin takes longer than that to allocate an IP (because, say, the IPAM backend is an etcd cluster experiencing elevated latency), containerd will kill the plugin subprocess and report a timeout error to kubelet. Kubelet will then attempt to delete the sandbox, calling CNI DEL — but since ADD never completed, the DEL may find no state to clean up and return success, leaving a dangling netns on disk.

### IPAM Mechanics and State Management

IP Address Management deserves its own treatment because it is the most common source of persistent failure state in production CNI deployments. The `host-local` IPAM plugin maintains its state as a directory of empty files in `/var/lib/cni/networks/<network-name>/`, where each filename is an IP address and each file contains the `CNI_CONTAINERID` that holds that address. This is a local, node-scoped, file-system-based lock. It is fast, requires no external dependencies, and survives daemon restarts. It is also completely blind to the rest of the cluster: if two nodes are both configured with the subnet `10.1.0.0/24`, they will both independently assign `10.1.0.2` to their first pod, and you will have an IP collision with no detection mechanism at the CNI layer.

Production deployments address this with one of three strategies. The first is static per-node subnet assignment: each node is allocated a non-overlapping `/24` prefix (Flannel's model, where the `flanneld` daemon uses an etcd lock to claim a subnet from the cluster-wide pod CIDR and writes the assignment to the node's `flannel.1` interface and to `/run/flannel/subnet.env`). The second is dynamic cluster-wide IPAM: a distributed IPAM daemon manages a shared pool and leases addresses to nodes on demand (Calico's `calico-ipam` with IP pools, or the `whereabouts` plugin for secondary interfaces). The third is to offload the problem to the network fabric entirely, as AWS VPC CNI does by pre-allocating ENIs and secondary IPs from the VPC DHCP server and assigning them directly to pods.

The file for a leaked `host-local` allocation — left behind when a pod was forcibly deleted or the node was restarted mid-attachment — looks like this:

```
/var/lib/cni/networks/production-net/
├── 10.0.1.2    (contains: "abc123def456...containerid")
├── 10.0.1.3    (contains: "deadbeef...containerid")
├── 10.0.1.4    (contains: "orphan-container-id-no-longer-running")
└── lock
```

Detecting and clearing leaked allocations requires correlating these files against the running containers known to the runtime:

```bash
# List all IPs currently allocated by host-local for a given network
ls /var/lib/cni/networks/production-net/ | grep -v lock

# List all running container IDs known to containerd
crictl ps -q

# Cross-reference: find allocations with no corresponding running container
for ip_file in /var/lib/cni/networks/production-net/*; do
  [[ "$(basename $ip_file)" == "lock" ]] && continue
  container_id=$(cat "$ip_file")
  if ! crictl ps -q | grep -q "$container_id"; then
    echo "LEAKED: $ip_file -> $container_id"
  fi
done
```

Clearing a leaked allocation is a file deletion, but it must be done while holding the lock file to avoid a race with a concurrent CNI ADD invocation:

```bash
# Acquire the host-local lock, remove the leaked allocation, release
(
  flock -x 9
  rm -f /var/lib/cni/networks/production-net/10.0.1.4
) 9>/var/lib/cni/networks/production-net/lock
```

## 3. High-Performance Optimization & Failure Modes

### Failure Mode Taxonomy

Production CNI failures fall into five categories that are worth internalizing as a mental model before you need them at 3 AM. The categories are not arbitrary — they correspond to distinct remediation paths and diagnostic tools.

**Category 1: Configuration failures.** The wrong plugin is selected, a required field is missing, or the JSON is malformed. These fail immediately at ADD time, the error appears in the kubelet event log as a `FailedCreatePodSandBox` with the CNI error message embedded, and they affect every pod on the node simultaneously. Configuration failures are the easiest to diagnose because the error is deterministic and reproducible.

**Category 2: IPAM exhaustion.** The node's IP pool is full. This manifests as individual pod failures with an IPAM-specific error, while existing pods are unaffected. With `host-local`, the error is `no IP addresses available in range set`; with `calico-ipam`, it is similar but includes the IP pool name. IPAM exhaustion can be genuine (the pool is correctly sized but the node has scaled beyond it) or it can be phantom exhaustion caused by leaked allocations from crashed containers.

**Category 3: Dataplane programming failures.** The plugin successfully allocates an IP and creates the veth pair, but fails to program routes, iptables rules, or tunnel endpoints in the host kernel. These are the cruelest failures because the pod appears to come up, the container's `eth0` has an IP address, but packets simply drop. The pod is running from Kubernetes' perspective, the application process starts, and the readiness probe fails because no traffic can reach it.

**Category 4: Background daemon failures.** The CNI binary itself succeeds, but the asynchronous state maintained by `felix`, `flanneld`, or `cilium-agent` is stale or absent. Pod-to-pod traffic within a node works, but cross-node traffic fails. NetworkPolicy is not enforced. This category requires distinguishing between node-local and cross-node reachability as a first diagnostic step.

**Category 5: Race conditions and partial failures.** A node is running multiple pods simultaneously, the IPAM lock contention causes a timeout, or a pod is deleted during CNI ADD. These are intermittent and difficult to reproduce, but they almost always leave residue: a dangling netns, a leaked IPAM allocation, or an iptables rule pointing to a container ID that no longer exists.

### Diagnostic Workflow

The correct diagnostic workflow begins with establishing the precise failure boundary — not by reading log files, but by directly exercising the CNI plugin in isolation. Because CNI is just a binary with environment variables and stdin, you can invoke it manually against any network namespace, bypassing containerd entirely. This is the most powerful tool in the CNI operator's arsenal and the least used.

The first step in any CNI diagnosis is confirming which plugin is active on the failing node:

```bash
# Identify the active CNI configuration
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/$(ls /etc/cni/net.d/ | sort | head -1)

# Verify the plugin binary exists and is executable
ls -la /opt/cni/bin/

# Check the CNI version the plugin reports
CNI_COMMAND=VERSION CNI_PATH=/opt/cni/bin /opt/cni/bin/calico < /dev/null
```

For pod-level failures, the next step is extracting the network namespace of the failing pod and inspecting its state directly. If the pod is in `ContainerCreating`, the netns may already exist even though no interfaces have been configured:

```bash
# Get the pod's sandbox ID
crictl pods --name my-failing-pod -q

# Get the network namespace path for the sandbox
crictl inspectp <sandbox-id> | jq '.info.runtimeSpec.linux.namespaces[] | select(.type=="network") | .path'

# Inspect the interfaces inside the namespace
ip netns exec <netns-path> ip addr show
ip netns exec <netns-path> ip route show

# Check the veth pair from the host side
ip link show | grep -A1 "veth"
```

For cross-node traffic failures, the diagnostic hierarchy is: confirm same-node pod-to-pod connectivity first, then same-node pod-to-service, then cross-node pod-to-pod with no service involved, then cross-node pod-to-service. Each step isolates a different layer of the data plane:

```bash
# Same-node pod-to-pod: verify the bridge/veth topology is intact
# For a bridge-based CNI like Flannel or kindnet:
bridge link show
ip route show table main | grep 10.244

# Cross-node: verify the tunnel or routing fabric
# For Flannel VXLAN:
ip link show flannel.1
bridge fdb show dev flannel.1
ip route show | grep "via" | grep flannel

# For Calico BGP:
calicoctl node status
calicoctl get bgppeer
ip route show proto bird
```

Packet-level tracing without eBPF is fully achievable with `tcpdump`, the network's oldest truth-teller. The key insight is that for VXLAN-based overlays, you need to capture at two points: on the pod-side veth (inside or outside the namespace) and on the VXLAN tunnel interface. A packet that appears on the veth but not on the tunnel interface means the host routing or FDB programming is incorrect. A packet that appears on the tunnel interface but does not arrive at the remote node means the underlay is filtering UDP/4789:

```bash
# Capture on the host-side veth for a specific pod
# First find the veth peer index from inside the pod
crictl exec <container-id> ip link show eth0
# The link index tells you the peer index on the host
ip link show | grep "^<peer-index>:"

# Then capture:
tcpdump -i <host-veth-name> -n -v icmp

# Simultaneously capture on the VXLAN tunnel interface
tcpdump -i flannel.1 -n -v

# And on the physical NIC for the outer UDP encapsulation
tcpdump -i eth0 -n -v "udp port 4789"
```

### Calico-Specific Dataplane Diagnosis

Calico's production complexity warrants dedicated treatment because its architecture — a BGP-based routing daemon (`BIRD`) feeding routes into the kernel, with `felix` managing iptables and ipsets for NetworkPolicy — has failure modes that are distinct from simpler CNI implementations.

When Calico-managed pods cannot reach each other across nodes, the first checkpoint is whether `felix` has successfully programmed the routing and policy rules on the failing node. Felix writes its programming state to the kernel's iptables and to the Calico datastore:

```bash
# Check felix agent health
kubectl get pod -n kube-system -l k8s-app=calico-node -o wide
kubectl logs -n kube-system <calico-node-pod> -c calico-node | tail -50

# Verify felix's view of endpoints on this node
calicoctl get workloadendpoint --node=$(hostname) -o yaml

# Inspect the iptables chains Felix manages
iptables -L cali-FORWARD -n -v
iptables -L cali-to-wl-dispatch -n -v
iptables -L cali-from-wl-dispatch -n -v

# Check IP sets for NetworkPolicy
ipset list | grep cali

# Verify BGP route propagation from BIRD
# The BIRD socket is accessible via the calico-node container
kubectl exec -n kube-system <calico-node-pod> -- birdcl show protocols
kubectl exec -n kube-system <calico-node-pod> -- birdcl show route
```

A common Calico failure mode is IPIP or VXLAN tunnel misconfiguration when the node MTU is not properly accounted for. Calico's IPIP encapsulation adds a 20-byte IP header; VXLAN adds 50 bytes (8 VXLAN header, 14 Ethernet, 20 IP, 8 UDP). If the host NIC MTU is 1500 and the Calico MTU is also set to 1500, the outer-encapsulated packet will exceed the NIC's MTU and either be silently dropped or fragmented, depending on the kernel's forwarding configuration. The correct MTU for pods behind IPIP encapsulation on a 1500-byte underlay is 1480; for VXLAN it is 1450. Calico's `mtu` field in the conflist and the `MTU` setting in the `calico-config` ConfigMap must both be consistent, and the `calico-node` DaemonSet must have permission to set the host-side interface MTU.

```bash
# Verify effective MTU on the tunnel and pod interfaces
ip link show tunl0 | grep mtu
ip link show flannel.1 | grep mtu
ip netns exec <pod-netns> ip link show eth0 | grep mtu

# Detect MTU-induced fragmentation: look for ICMP "frag needed" messages
tcpdump -i eth0 -n "icmp and icmp[0] == 3 and icmp[1] == 4"

# Verify the Calico MTU configuration in the ConfigMap
kubectl get configmap -n kube-system calico-config -o jsonpath='{.data.veth_mtu}'
```

### Manual CNI Plugin Invocation for Isolated Testing

The most direct way to verify that a plugin is functioning correctly — independent of containerd, kubelet, and the Kubernetes control plane — is to invoke it manually. This technique is indispensable for validating a new CNI configuration before deploying it to a production node, and for reproducing failures in a controlled environment.

```bash
# Create a test network namespace
ip netns add cni-test

# Write a minimal CNI configuration
cat > /tmp/test-cni.conflist <<'EOF'
{
  "cniVersion": "1.0.0",
  "name": "test-net",
  "plugins": [
    {
      "type": "bridge",
      "bridge": "cni-test0",
      "isGateway": true,
      "ipMasq": true,
      "ipam": {
        "type": "host-local",
        "subnet": "10.99.0.0/24",
        "routes": [
          { "dst": "0.0.0.0/0" }
        ]
      }
    }
  ]
}
EOF

# Invoke the bridge plugin's ADD command manually
CNI_COMMAND=ADD \
CNI_CONTAINERID=test-container-001 \
CNI_NETNS=/var/run/netns/cni-test \
CNI_IFNAME=eth0 \
CNI_PATH=/opt/cni/bin \
/opt/cni/bin/bridge < /tmp/test-cni.conflist

# Verify the result inside the namespace
ip netns exec cni-test ip addr show
ip netns exec cni-test ip route show
ip netns exec cni-test ping -c3 8.8.8.8

# Clean up: invoke DEL
CNI_COMMAND=DEL \
CNI_CONTAINERID=test-container-001 \
CNI_NETNS=/var/run/netns/cni-test \
CNI_IFNAME=eth0 \
CNI_PATH=/opt/cni/bin \
/opt/cni/bin/bridge < /tmp/test-cni.conflist

ip netns del cni-test
```

This invocation pattern can be adapted to test Calico by providing a valid `calico-kubeconfig` and setting `KUBERNETES_NODE_NAME`, making it possible to verify the full plugin chain against a real cluster without scheduling any pods.

### Cross-Cluster Networking Constraints and Production Topology Decisions

Multi-cluster networking introduces constraints that do not exist within a single cluster, because the fundamental assumption of CNI — that all pods share a flat Layer 3 network — does not hold across cluster boundaries by default. Pod CIDRs from different clusters will frequently overlap (since most clusters use the standard `10.244.0.0/16` or `192.168.0.0/16` defaults), and even when they do not, there is no routing infrastructure that connects the two pod networks.

The industry has converged on three architectural patterns for cross-cluster pod networking, each with distinct operational characteristics. The first is **BGP route federation**: both clusters run a CNI with a BGP control plane (Calico or Cilium in BGP mode), and their route reflectors are peered either directly or through a transit network. This gives you native-speed cross-cluster routing with no encapsulation overhead, but it requires coordination between the networking teams managing each cluster's autonomous system, non-overlapping pod CIDRs enforced at provisioning time, and careful BGP policy to prevent route leakage. It is the highest-performance option and the most operationally complex.

The second pattern is **service mesh tunneling**: a data plane like Istio's `istio-remote` or Linkerd's service mirroring establishes mutual-TLS tunnels between clusters, exposing selected services across the boundary rather than the full pod network. This is operationally safer because the blast radius of a misconfiguration is bounded by the service mirror configuration, and pod CIDR overlap is irrelevant — traffic travels over the mesh's encrypted tunnels at the service level. The tradeoff is latency (additional TLS handshake and proxy hop) and the operational weight of running a service mesh.

The third pattern is **dedicated multi-cluster CNI infrastructure**: purpose-built tools like Submariner or Cilium's Cluster Mesh establish a separate control plane and tunnel fabric specifically for cross-cluster pod-to-pod and pod-to-service connectivity. Submariner, for example, deploys a gateway node per cluster that terminates IPsec or VXLAN tunnels, a broker component (backed by an etcd instance or a Kubernetes CRD) for exchanging endpoint and service information, and a route agent DaemonSet that programs routes on each node pointing inter-cluster traffic toward the gateway. Cilium Cluster Mesh exposes the etcd stores of each cluster to the others, allowing the `cilium-agent` on each node to maintain a global view of service endpoints and program service-aware routing without a centralized gateway.

```bash
# Submariner: verify the gateway and route agent status after deployment
kubectl get gateway -A
kubectl get submariners -A -o wide

# Check inter-cluster tunnel state from the gateway pod
kubectl exec -n submariner-operator \
  $(kubectl get pod -n submariner-operator -l app=submariner-gateway -o name) \
  -- subctl show connections

# Verify routes programmed on worker nodes by the route agent
ip route show table 100 | grep -E "10\.|192\.168\."

# Test cross-cluster pod connectivity
kubectl exec -it test-pod -- curl http://remote-service.remote-namespace.svc.clusterset.local
```

The most consequential production topology decision for a single cluster's CNI is the choice between an **overlay network** and a **native routing** data plane. An overlay (Flannel VXLAN, Calico VXLAN, Weave) encapsulates pod traffic in an outer UDP or IP-in-IP header, allowing the pod CIDR to be completely independent of the underlying network's routing topology. This is simpler to deploy — the underlay only needs to be able to route UDP between nodes — but it introduces encapsulation overhead (MTU reduction, CPU cost of kernel encap/decap, and an additional header-parsing step in every NIC that processes the traffic). On modern hardware with VXLAN offload support, this overhead is small but nonzero.

A native routing data plane (Calico BGP without encapsulation, AWS VPC CNI, Azure CNI, or GKE's native Pod IP routing) programs pod routes directly into the host routing table or the cloud provider's VPC route tables, so packets travel from pod to pod with no encapsulation. This delivers maximum throughput and minimum latency, but it requires that the underlay network either learns pod routes dynamically (via BGP) or has them programmed statically (via cloud provider APIs). It also means the pod CIDR must be routable from the underlay's perspective — which constrains the addressable pod density and can conflict with existing enterprise address plans.

The decision matrix reduces to two questions: does your underlay support (and can your team operate) a BGP control plane, and do your performance requirements justify the operational complexity of native routing? For cloud-native deployments on managed Kubernetes services, the answer is almost always to use the cloud provider's native CNI (EKS VPC CNI, GKE Dataplane V2, AKS Azure CNI) and accept its constraints on pod density and address space. For on-premises clusters where you own the network fabric, Calico with BGP peered to your ToR switches is the production-grade choice that the most demanding workloads in the industry have validated at scale. For teams that need simplicity and are willing to accept a 3–5% encapsulation overhead, Flannel VXLAN remains a reasonable and well-understood default.

### Observability Infrastructure for CNI

Persistent observability — not just break-glass diagnostics — requires that you have metrics flowing before an incident occurs. The minimum viable CNI observability stack consists of four components: a metrics endpoint from the CNI daemon, a scraping agent (Prometheus or its equivalent), node-level network counters from the kernel, and a correlated view that ties pod identity to network events.

Calico exports Prometheus metrics from `felix` on port 9091 and from `typha` (its fan-out proxy for API server watches) on port 9093. The metrics most worth alerting on in production are `felix_cluster_num_workload_endpoints` (a sharp drop indicates a mass policy programming failure), `felix_int_dataplane_failures` (any nonzero value indicates felix could not program the kernel), `felix_ipset_errors` (indicates iptables or ipset failures that will cause NetworkPolicy to silently stop enforcing), and `felix_route_table_list_errors` (indicates felix cannot read the routing table, usually due to a permissions or namespace issue).

```yaml
# Prometheus scrape configuration for Calico Felix metrics
# This assumes Prometheus is deployed via the kube-prometheus-stack
# with ServiceMonitor CRD support

apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: calico-felix
  namespace: monitoring
  labels:
    app: calico-felix
spec:
  selector:
    matchLabels:
      k8s-app: calico-node
  namespaceSelector:
    matchNames:
      - kube-system
  podMetricsEndpoints:
    - port: http-metrics
      path: /metrics
      interval: 15s
      scheme: http
```

Beyond plugin-specific metrics, the kernel's network interface counters provide a ground-truth view of what is actually flowing. The `/proc/net/dev` interface (or `ip -s link show`) shows per-interface byte and packet counts alongside error counters. `RX-ERR`, `TX-DRP`, and `TX-OVR` on the host-side veth or the tunnel interface are early indicators of capacity or configuration problems that do not surface in application-level metrics until they are severe enough to cause connection drops.

```bash
# Monitor interface error counters across all veth pairs
# This one-liner correlates interface names with error rates
watch -n5 'ip -s link show | awk "
  /^[0-9]+:/ { iface = \$2 }
  /RX:/ { getline; rx_err = \$3 }
  /TX:/ { getline; tx_drop = \$4; if (rx_err+tx_drop > 0) print iface, \"rx_err=\"rx_err, \"tx_drop=\"tx_drop }
"'

# Check conntrack table utilization (critical for large-scale CNI with iptables)
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# If conntrack utilization exceeds 80%, pods will start failing to establish
# new connections with ENOMEM; tune or switch to ipvs/eBPF proxy mode
sysctl -w net.netfilter.nf_conntrack_max=524288
```

Conntrack table exhaustion is one of the most common large-scale Kubernetes network failures and one of the least expected. The default `nf_conntrack_max` on most Linux distributions is sized for a general-purpose server, not a Kubernetes node running 110 pods each with dozens of active connections. At scale, with a kube-proxy running in iptables mode, every Service's ClusterIP requires conntrack entries for active sessions. A node running 110 pods, each connected to 10 services, with 50 concurrent connections per pod, requires 55,000 conntrack entries just for pod-to-service traffic, before accounting for host-process connections, NodePort traffic, and health check probes. Setting `nf_conntrack_max` to at least 524288 on nodes running more than 50 pods, and monitoring its utilization as a first-class infrastructure metric, is a production requirement that CNI documentation consistently underemphasizes and production postmortems consistently rediscover.
