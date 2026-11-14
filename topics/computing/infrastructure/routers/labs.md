# Operational Verification Labs: Routers

## Objective & Environment Setup

Modern IP routers exist as distributed state machines that maintain forwarding information bases, enforce policy through packet filter chains, and participate in dynamic routing protocols to compute optimal paths across autonomous systems. Whether operating as a bare-metal Linux appliance running Bird or FRRouting, a virtualized router instance in OpenStack Neutron, or a Kubernetes network policy enforcement point through Calico or Cilium, the fundamental verification methodology remains anchored in kernel forwarding plane inspection, control plane protocol analysis, and data plane throughput characterization under load.

This laboratory curriculum assumes a practitioner role responsible for production router availability, performance, and correctness. The exercises progress from passive observation of live forwarding state through active stress testing and controlled fault injection. The verification techniques span from userspace control plane introspection through kernel subsystem telemetry and hardware packet processing counters. Each exercise delivers actionable diagnostic muscle memory that translates directly to incident response, capacity planning, and architectural validation in production networks.

The reference environment requires a Linux host with kernel 5.10 or later to access modern BPF capabilities and extended routing subsystem features. Install the diagnostic toolchain through your distribution's package manager. On Debian-derived systems, execute `apt-get install iproute2 ethtool tcpdump linux-tools-$(uname -r) bpftrace iputils-ping iperf3 bird2`. Red Hat derivatives use `dnf install iproute ethtool tcpdump perf bpftrace iputils iperf3 frr`. For Kubernetes-native routing verification, install `kubectl` from the upstream release binaries and deploy a test cluster with Calico or Cilium CNI to enable policy enforcement observation.

The laboratory topology consists of three network namespaces representing distinct routing domains. Create the baseline environment by executing the following sequence. The `ip netns add` commands instantiate isolated network stacks with independent routing tables and packet filter chains. The veth pairs establish point-to-point layer two links between namespaces, analogous to physical crossover cables. Assigning IP addresses and setting links operationally up brings the interfaces into the kernel's forwarding decision path.

```bash
# Create three network namespaces: client, router, server
ip netns add ns-client
ip netns add ns-router
ip netns add ns-server

# Create veth pairs: client<->router and router<->server
ip link add veth-c type veth peer name veth-cr
ip link add veth-rs type veth peer name veth-s

# Assign veth endpoints to namespaces
ip link set veth-cr netns ns-router
ip link set veth-c netns ns-client
ip link set veth-rs netns ns-router
ip link set veth-s netns ns-server

# Configure IP addressing on client namespace
ip netns exec ns-client ip addr add 10.0.1.2/24 dev veth-c
ip netns exec ns-client ip link set veth-c up
ip netns exec ns-client ip link set lo up

# Configure router namespace with two interfaces
ip netns exec ns-router ip addr add 10.0.1.1/24 dev veth-cr
ip netns exec ns-router ip addr add 10.0.2.1/24 dev veth-rs
ip netns exec ns-router ip link set veth-cr up
ip netns exec ns-router ip link set veth-rs up
ip netns exec ns-router ip link set lo up

# Enable IPv4 forwarding in router namespace
ip netns exec ns-router sysctl -w net.ipv4.ip_forward=1

# Configure server namespace
ip netns exec ns-server ip addr add 10.0.2.2/24 dev veth-s
ip netns exec ns-server ip link set veth-s up
ip netns exec ns-server ip link set lo up

# Install routes on client and server to reach remote subnets
ip netns exec ns-client ip route add 10.0.2.0/24 via 10.0.1.1
ip netns exec ns-server ip route add 10.0.1.0/24 via 10.0.2.1
```

This topology establishes the foundational environment for all subsequent exercises. The client namespace at `10.0.1.2` must traverse the router namespace to reach the server at `10.0.2.2`. The router performs longest-prefix-match lookups in its forwarding information base, decrements the IP TTL field, recalculates checksums, and performs layer two address resolution before transmitting packets toward the next hop. Verify end-to-end connectivity by executing `ip netns exec ns-client ping -c 3 10.0.2.2`. The round-trip time measurements should reflect sub-millisecond latency for this software-switched path through kernel namespaces.

## Exercise 1: Live State & Internal Subsystem Inspection

The first operational discipline is non-invasive state inspection: reading the current forwarding table, examining neighbor cache entries, observing packet filter rule traversal counters, and correlating interface statistics with expected traffic patterns. These techniques form the foundation of rapid triage during production incidents, where determining whether a routing loop exists, a next-hop is unreachable, or packet loss occurs at a specific interface can isolate root cause within seconds.

Begin by inspecting the router's forwarding information base. Execute `ip netns exec ns-router ip route show table main`. The output displays the directly connected subnets `10.0.1.0/24` and `10.0.2.0/24` learned through interface configuration, along with the local routes for the router's own addresses. The kernel routing subsystem maintains these entries in a trie structure optimized for longest-prefix-match operations. Each route entry contains a next-hop gateway address, an egress interface identifier, a metric value influencing path selection when multiple routes exist to the same destination, and protocol metadata indicating the route source (kernel, static, dynamic routing daemon).

For dynamic routing scenarios, inspect protocol-specific state maintained by the routing daemon. If running Bird, query the routing table through `birdc show route`. For FRRouting, use `vtysh -c 'show ip route'`. These commands reveal routes learned through OSPF link-state advertisements, BGP path vector announcements, or static configuration, along with route preference values that determine which protocol's routes are installed into the kernel forwarding table when conflicts arise. The administrative distance hierarchy—where directly connected routes override static routes, which override OSPF, which override BGP—ensures deterministic path selection.

Examine the neighbor cache, which maps layer three IP addresses to layer two MAC addresses through ARP for IPv4 or Neighbor Discovery for IPv6. Execute `ip netns exec ns-router ip neigh show`. Each entry displays an IP address, the associated MAC address, the interface on which the neighbor is reachable, and a state field indicating whether the entry is reachable (recently confirmed), stale (not recently used but not yet expired), or failed (ARP resolution attempts exhausted). A failed neighbor entry for a next-hop gateway immediately explains packet loss, as the router cannot construct the Ethernet frame header without the destination MAC address. The kernel ARP cache implements a finite-state automaton with exponential backoff for retransmission and garbage collection timers to purge stale entries.

Interface statistics expose packet processing outcomes at the device driver level. Execute `ip -s -s link show` within the router namespace to display detailed counters for each interface. The output includes transmitted and received packet counts, byte counters, error tallies, and dropped packet counts. Pay particular attention to the RX errors, TX errors, RX dropped, and TX dropped fields. Receive errors typically indicate checksum failures, frame alignment issues, or buffer overflow conditions when the kernel cannot allocate socket buffers fast enough to accept incoming packets. Transmit errors reflect hardware-level failures or queue discipline drops when egress queuing depth exceeds configured limits. Dropped packets signal backpressure: the kernel discarded packets because the receiving application did not consume data from its socket buffer, or the traffic control subsystem enforced rate limits.

To correlate these statistics with specific traffic flows, observe the counters in real time while generating test traffic. In a separate terminal, execute `ip netns exec ns-client ping -f 10.0.2.2` to generate flood pings from client to server. Simultaneously, in the router namespace, execute `watch -n 0.5 'ip -s link show veth-cr'` to refresh interface statistics every 500 milliseconds. Watch the RX packets and RX bytes counters increment as ICMP echo requests arrive. The TX packets counter on the egress interface `veth-rs` should increment at the same rate, confirming the router is successfully forwarding the traffic stream. Any divergence between ingress and egress counters indicates packet loss within the routing path.

Packet filter rules, implemented through iptables or nftables, enforce security policy and perform connection tracking. Inspect the filter, nat, and mangle tables to understand the policy evaluation path. Execute `ip netns exec ns-router iptables -t filter -L -v -n` to list filter table rules with packet and byte counters. The `-v` flag displays verbose statistics showing how many packets traversed each rule, while `-n` prevents DNS lookups that would slow output rendering. If the router implements stateful firewalling, the conntrack subsystem maintains a hash table of active connections with state labels (NEW, ESTABLISHED, RELATED, INVALID). Query connection tracking state with `ip netns exec ns-router conntrack -L`. Each entry displays the protocol, source and destination addresses and ports, connection state, timeout remaining, and byte/packet counters per direction.

For Kubernetes-native routing, the verification methodology shifts to examining pod network policies and the underlying CNI implementation's enforcement mechanisms. Deploy a test workload by creating a namespace and two pods. Execute `kubectl create namespace lab-routing` followed by:

```yaml
# client-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: client-pod
  namespace: lab-routing
  labels:
    app: client
spec:
  containers:
  - name: client
    image: nicolaka/netshoot:latest
    command: ["/bin/sleep", "3600"]
---
# server-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: server-pod
  namespace: lab-routing
  labels:
    app: server
spec:
  containers:
  - name: server
    image: nicolaka/netshoot:latest
    command: ["/bin/sleep", "3600"]
```

Apply these manifests with `kubectl apply -f client-pod.yaml -f server-pod.yaml`. Once both pods reach Running state, verify their IP addresses through `kubectl get pods -n lab-routing -o wide`. The CNI plugin assigned each pod an IP address from the cluster's pod CIDR range. These addresses are routable within the cluster through the overlay network or host-based routing tables configured by the CNI daemon.

Inspect the routing state on the Kubernetes node hosting the client pod. SSH to the node and execute `ip route show`. You will observe routes directing pod CIDR traffic to the CNI bridge or tunnel interface. For Calico, these appear as individual /32 host routes pointing to the cali-prefixed veth interface for each pod. For Cilium, routes direct traffic through the cilium_host or cilium_net interfaces with eBPF programs attached to perform encapsulation and policy enforcement. Use `ip link show` to identify these interfaces and `tc qdisc show` to observe any traffic control disciplines attached for bandwidth shaping.

To inspect Cilium's eBPF-based routing, execute `bpftool prog list` on a node running Cilium. The output displays loaded BPF programs with their type (sched_cls, xdp, cgroup_skb), attachment points, and program IDs. Identify programs attached to the pod veth interfaces with `bpftool net show`. Each program enforces network policy by evaluating packet headers against compiled policy maps and either allowing the packet to proceed or dropping it. Dump the BPF maps used for policy decisions with `bpftool map dump name cilium_policy_v4`. These maps encode allow/deny rules as key-value pairs where keys are tuples of source identity, destination identity, protocol, and port, and values are the verdict (allow or deny).

Network policy enforcement verification requires creating a restrictive policy and confirming that traffic flows change as expected. Apply the following NetworkPolicy to deny all ingress traffic to the server pod except from pods labeled `app: client`:

```yaml
# server-netpol.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: server-ingress-policy
  namespace: lab-routing
spec:
  podSelector:
    matchLabels:
      app: server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: client
    ports:
    - protocol: TCP
      port: 8080
```

Apply this policy with `kubectl apply -f server-netpol.yaml`. The CNI plugin translates this declarative policy into eBPF programs (Cilium) or iptables rules (Calico) that enforce the ingress restrictions. Verify enforcement by executing a shell in the client pod and attempting to reach the server. Run `kubectl exec -it client-pod -n lab-routing -- curl http://<server-pod-ip>:8080`. This should succeed if the server is listening on port 8080. Now deploy a third pod without the `app: client` label and attempt the same connection—it should fail, confirming policy enforcement.

Inspect Calico's iptables implementation of the policy by executing `iptables -t filter -L -v -n` on the node hosting the server pod. You will observe chains prefixed with `cali-` that match on source IP ranges corresponding to pod CIDRs and source labels. The policy rules appear as jump targets that either ACCEPT or DROP packets based on the source pod's identity. Packet counters in the iptables output confirm whether traffic is being evaluated against these rules and whether drops are occurring as expected.

## Exercise 2: Benchmarking & Saturation Profiling

Characterizing router performance requires measuring forwarding throughput, latency under load, and identifying bottlenecks in the packet processing pipeline. A production router must sustain line-rate forwarding without packet loss across the expected traffic matrix. Profiling involves saturating the forwarding plane to determine maximum achievable throughput, measuring latency distribution at various load levels, and correlating performance degradation with CPU utilization, memory bandwidth, or queue depth exhaustion.

Establish a baseline throughput measurement using iperf3 to generate TCP traffic between the client and server namespaces. In the server namespace, launch an iperf3 server with `ip netns exec ns-server iperf3 -s -B 10.0.2.2`. This binds the server to the server's IP address and listens for incoming test connections. In the client namespace, initiate a throughput test with `ip netns exec ns-client iperf3 -c 10.0.2.2 -t 30 -P 4`. The `-t 30` flag runs the test for 30 seconds, and `-P 4` spawns four parallel TCP streams to better saturate the available bandwidth and avoid single-stream TCP congestion control limitations.

The iperf3 output displays achieved throughput in Gbits/sec, retransmission counts, and congestion window evolution. For software routers built on veth pairs in network namespaces, expect throughput in the range of 10-40 Gbits/sec depending on CPU core count and memory bandwidth. Hardware routers with dedicated forwarding ASICs or DPDK-based software routers bypass the kernel network stack and achieve significantly higher rates. Record the baseline throughput for comparison against subsequent tests where additional processing load or policy enforcement is introduced.

To measure forwarding latency, use ICMP echo requests with varying packet rates and sizes. Execute `ip netns exec ns-client ping -i 0.001 -c 10000 -s 1400 10.0.2.2` to send 10,000 pings with 1-millisecond intervals and 1400-byte payloads. The output provides minimum, average, maximum, and standard deviation of round-trip times. Latency measurements expose queueing delays in the router's traffic control subsystem and reveal jitter that impacts real-time applications like VoIP or videoconferencing. For production capacity planning, measure latency at 10%, 50%, 80%, and 100% of the router's maximum forwarding rate to construct a latency-vs-load profile.

Saturate the router by generating high packet-per-second loads that stress the forwarding decision logic rather than link bandwidth. Small packets maximize the per-packet processing overhead relative to data transfer time. Execute `ip netns exec ns-client ping -f -s 0 10.0.2.2` to generate flood pings with minimal payload. The `-f` flag sends packets as fast as the kernel can process them, limited only by CPU and socket buffer availability. Monitor the router's CPU utilization during this test with `ip netns exec ns-router top -b -n 1 | head -n 20`. Observe the `%si` (software interrupt) and `%id` (idle) columns. High software interrupt utilization indicates the kernel is spending most of its time in interrupt handlers processing packets from the veth interfaces.

For deeper CPU profiling, use `perf` to sample the kernel call stack during forwarding. Execute `ip netns exec ns-router perf record -a -g -F 99 sleep 10` while the flood ping is running. The `-a` flag profiles all CPUs, `-g` enables call graph recording, and `-F 99` samples at 99 Hz to minimize measurement perturbation. After the recording completes, generate a flame graph or examine the hottest functions with `perf report`. The top functions will include `ip_rcv` (IP receive processing), `ip_forward` (forwarding decision), `ip_output` (IP transmit processing), and `dev_queue_xmit` (device transmit queue enqueue). If a significant portion of CPU time is spent in `iptables` or `nf_conntrack` functions, packet filter overhead is the bottleneck.

Queue discipline saturation is another common bottleneck. The default pfifo_fast qdisc on Linux interfaces implements three priority bands with FIFO behavior within each band. Under high load, the queue fills and tail-drop occurs, discarding packets when the queue depth exceeds the configured limit. Inspect the current qdisc configuration with `ip netns exec ns-router tc qdisc show dev veth-cr`. Replace the default with a more sophisticated qdisc that exposes detailed statistics. Execute:

```bash
ip netns exec ns-router tc qdisc replace dev veth-cr root fq_codel
ip netns exec ns-router tc qdisc replace dev veth-rs root fq_codel
```

The `fq_codel` qdisc implements fair queueing combined with controlled delay active queue management. It maintains per-flow queues and uses the CoDel algorithm to detect and mitigate bufferbloat by dropping packets when queueing delay exceeds a threshold. Query qdisc statistics with `ip netns exec ns-router tc -s qdisc show dev veth-cr`. The output includes backlog (current queue depth in bytes and packets), drops, overlimits (instances where the queue depth exceeded the limit), and requeues. High drop counts during the flood ping test indicate that the ingress rate exceeded the router's forwarding capacity, causing queue exhaustion and packet loss.

To isolate the specific processing stage causing saturation, use eBPF tracing to instrument packet flow through the kernel. Create a BPF program that increments counters at key points in the network stack: packet receive, routing decision, netfilter hooks, and packet transmit. Save the following as `trace_forward.bt`:

```c
// BPF tracing script for packet forwarding path
#include <linux/skbuff.h>

kprobe:ip_rcv
{
  @rcv_count = count();
}

kprobe:ip_forward
{
  @fwd_count = count();
}

kprobe:ip_output
{
  @out_count = count();
}

kprobe:dev_queue_xmit
{
  @xmit_count = count();
}

kprobe:kfree_skb
{
  @drop_count = count();
}

interval:s:1
{
  print(@rcv_count);
  print(@fwd_count);
  print(@out_count);
  print(@xmit_count);
  print(@drop_count);
  clear(@rcv_count);
  clear(@fwd_count);
  clear(@out_count);
  clear(@xmit_count);
  clear(@drop_count);
}
```

Run this script with `ip netns exec ns-router bpftrace trace_forward.bt` while generating test traffic. The output displays per-second counters for each instrumented function. If `@rcv_count` is high but `@fwd_count` is low, the bottleneck is in the routing decision logic. If `@fwd_count` matches `@rcv_count` but `@xmit_count` is lower, the bottleneck is in the transmit path or qdisc. A high `@drop_count` indicates packets are being freed (dropped) rather than forwarded, pinpointing the stage where loss occurs.

For Kubernetes routing performance, benchmark pod-to-pod throughput across nodes to measure the overhead of the CNI overlay network. Deploy iperf3 server and client pods on different nodes. Ensure the server pod listens on a NodePort or ClusterIP service accessible from the client. Execute `kubectl exec -it client-pod -n lab-routing -- iperf3 -c <server-service-ip> -t 30 -P 4`. Compare the achieved throughput against the native throughput between the physical nodes (measured by running iperf3 directly on the node operating systems). The overhead of VXLAN or Geneve encapsulation, eBPF processing, and connection tracking typically reduces throughput by 10-30% depending on the CNI implementation and packet size distribution.

Profile Cilium's eBPF forwarding overhead using `perf` to sample the BPF program execution. On a node running Cilium, execute `perf record -e bpf:bpf_prog_run -a -g sleep 10` while pod-to-pod traffic flows. After recording, run `perf report` to identify which BPF programs are consuming the most CPU cycles. The program names include function descriptors like `from-container` or `to-container`, indicating the direction of packet flow. High sample counts in the policy enforcement programs suggest that complex network policies are the bottleneck. Simplifying policies by reducing the number of ingress/egress rules or consolidating policies can recover performance.

## Exercise 3: Fault Injection & Recovery Analysis

Operational resilience testing requires deliberately injecting failures—link degradation, routing loops, transient congestion, control plane unavailability—and validating that the system detects the failure, reroutes traffic, and restores service within acceptable recovery time objectives. This discipline builds confidence that the router will behave correctly under adverse conditions and provides empirical data for runbook procedures and automated remediation workflows.

Begin with link failure simulation. In the baseline topology, simulate a link down event on the router's interface facing the server. Execute `ip netns exec ns-router ip link set veth-rs down`. This immediately removes all routes using `veth-rs` as their egress interface from the kernel forwarding table. Verify the route disappearance with `ip netns exec ns-router ip route show`. Attempt connectivity from client to server with `ip netns exec ns-client ping -c 3 10.0.2.2`. The ping will fail with "Network is unreachable" because the router has no valid route to `10.0.2.0/24` after the interface went down.

Observe how routing protocols respond to this failure. If running OSPF through Bird or FRRouting, the router will detect the link state change through the absence of OSPF Hello packets on the failed interface. It will flood a new Link State Advertisement (LSA) to all neighbors, announcing that the link is down. Other routers recompute their shortest path trees using Dijkstra's algorithm, excluding the failed link. Query the OSPF database to observe the LSA propagation timing. For Bird, execute `birdc show ospf state`. For FRRouting, use `vtysh -c 'show ip ospf database'`. Measure the time from link failure to route convergence by running a continuous ping from the client and noting the gap in ICMP responses during the convergence window.

Restore the link by executing `ip netns exec ns-router ip link set veth-rs up`. The directly connected route reappears in the routing table, and connectivity resumes. For routing protocols, the router floods a new LSA advertising the link's return to service, and neighbors recompute paths to include the restored link if it offers a better metric. Repeat this cycle while monitoring the routing daemon logs for diagnostic messages about neighbor state transitions, database synchronization, and route installation.

Inject packet loss to simulate a degraded link. Use the `tc` (traffic control) subsystem to apply a netem qdisc that probabilistically drops packets. Execute:

```bash
ip netns exec ns-router tc qdisc add dev veth-rs root netem loss 10%
```

This configuration drops 10% of packets egressing the `veth-rs` interface, simulating a lossy link. Generate TCP traffic with iperf3 and observe the throughput reduction and retransmission count increase. TCP's congestion control algorithm interprets packet loss as a congestion signal and reduces its sending rate by halving the congestion window. Measure the throughput degradation: a 10% random loss typically reduces TCP throughput by 50% or more due to the multiplicative decrease in the congestion window. Inspect TCP retransmission counters with `ip netns exec ns-client ss -ti` while the iperf3 test runs. The output includes fields like `retrans`, `lost`, and `sacked`, quantifying the retransmission overhead imposed by the lossy link.

Add latency to simulate long-distance or satellite links. Execute:

```bash
ip netns exec ns-router tc qdisc change dev veth-rs root netem delay 100ms loss 10%
```

This adds 100 milliseconds of fixed delay in addition to the 10% loss. The increased latency extends the TCP round-trip time, reducing the rate at which the congestion window can grow during slow start and limiting the achievable throughput even further. Verify the latency increase by running `ip netns exec ns-client ping 10.0.2.2` and observing that the round-trip time is approximately 200 milliseconds (100 ms in each direction).

Inject a routing loop to observe failure detection mechanisms. Modify the routing tables to create a circular forwarding dependency. In the router namespace, add a static route that loops traffic back toward the client. Execute:

```bash
ip netns exec ns-router ip route add 10.0.3.0/24 via 10.0.1.2
ip netns exec ns-client ip route add 10.0.3.0/24 via 10.0.1.1
```

Now generate traffic destined for `10.0.3.0/24`. Execute `ip netns exec ns-client ping -c 3 10.0.3.10`. The packet enters the router, which forwards it back to the client. The client forwards it back to the router, and the loop continues until the IP TTL field decrements to zero. At that point, the router drops the packet and sends an ICMP Time Exceeded message back to the source. Use `tcpdump` to observe the looping behavior. In one terminal, execute `ip netns exec ns-router tcpdump -i veth-cr -n icmp`. In another, run the ping. You will see the ICMP echo request traverse the interface multiple times with decreasing TTL values until the router drops it and generates the Time Exceeded response.

For BGP routing environments, simulate a route hijack by advertising a more specific prefix from a rogue peer. Configure a second router namespace to act as a BGP neighbor and announce a prefix that overlaps with an existing route. The router will prefer the more specific route due to longest-prefix-match rules, diverting traffic to the hijacker. Detect this through route monitoring: compare the current routing table against a known-good baseline and alert on unexpected route changes. Implement route filtering using prefix lists or route maps to reject invalid announcements. Query the BGP RIB with `vtysh -c 'show ip bgp'` to inspect all received routes and their selection status. The output includes AS path, next-hop, and local preference attributes that explain why a particular route was chosen.

In Kubernetes environments, test CNI plugin resilience by forcing a pod's network interface into a failure state. Identify the pod's veth interface on the host node by executing `ip link show` and correlating the interface index with the pod's container ID. Delete the veth interface with `ip link del <veth-name>`. The CNI plugin's reconciliation loop should detect the missing interface and recreate it, reassigning the pod's IP address. Monitor the pod status with `kubectl get pod <pod-name> -n lab-routing -w` to observe the brief disruption and recovery. Inspect the CNI daemon logs (Calico: `kubectl logs -n kube-system -l k8s-app=calico-node`, Cilium: `kubectl logs -n kube-system -l k8s-app=cilium`) for error messages about interface recreation and route reinstallation.

Test control plane failure by stopping the CNI daemon and observing that existing pods continue to forward traffic while new pods fail to obtain network configuration. For Calico, scale the calico-node daemonset to zero with `kubectl scale daemonset calico-node -n kube-system --replicas=0`. Existing pod-to-pod connectivity persists because the kernel routing tables and iptables rules remain in place. However, creating a new pod will fail with CNI plugin errors because no daemon is available to configure the pod's network namespace. Restore the control plane by scaling the daemonset back up with `kubectl scale daemonset calico-node -n kube-system --replicas=<original-count>`. The new pods will receive network configuration and become reachable.

Introduce connection tracking table exhaustion to simulate a state-table overflow scenario common in NAT gateways and stateful firewalls. The kernel's connection tracking subsystem maintains a hash table of active connections with a configurable maximum size. Query the current limit with `sysctl net.netfilter.nf_conntrack_max`. Reduce the limit to artificially constrain capacity: `ip netns exec ns-router sysctl -w net.netfilter.nf_conntrack_max=100`. Generate many concurrent connections by launching multiple `curl` or `nc` sessions from the client to the server. Once the connection tracking table fills, new connections will fail because the kernel cannot allocate conntrack entries. Monitor the table with `ip netns exec ns-router conntrack -L | wc -l` to observe the count approaching the limit. The kernel logs (accessible via `dmesg`) will display "nf_conntrack: table full, dropping packet" messages when the limit is exceeded. Production routers must size the conntrack table according to expected concurrent connection counts, typically millions of entries for high-traffic environments.

## Diagnostic Cheat Sheet & Verification Checklist

The following command reference provides rapid-access syntax for common router verification tasks. Each command includes a brief explanation of its output and the specific failure mode it diagnoses. Internalize this reference for use during incident response when decision latency is measured in seconds.

**Routing Table Inspection:**
- `ip route show table main`: Display the primary routing table with next-hop and interface information.
- `ip route get <destination-ip>`: Perform a route lookup for a specific destination, showing the selected route and egress interface.
- `ip route show table all`: Display all routing tables, including custom tables used by policy-based routing.

**Neighbor Cache Verification:**
- `ip neigh show`: Display ARP/ND cache entries with state (reachable, stale, failed).
- `ip neigh flush dev <interface>`: Clear neighbor cache for an interface, forcing fresh ARP/ND resolution.
- `ip -s neigh show`: Display neighbor cache statistics including probe counts and state transition history.

**Interface Statistics:**
- `ip -s -s link show`: Display detailed interface packet counters including errors, drops, and overruns.
- `ethtool -S <interface>`: Show driver-level hardware statistics including CRC errors, collision counts, and queue depth.
- `ethtool -g <interface>`: Display ring buffer sizes for RX and TX queues.

**Packet Filter Analysis:**
- `iptables -t filter -L -v -n`: List filter table rules with packet/byte counters.
- `iptables -t nat -L -v -n`: List NAT table rules for source/destination address translation.
- `conntrack -L`: Display connection tracking table entries with state and timeout values.
- `conntrack -S`: Show connection tracking statistics including table size and allocation failures.

**Traffic Control:**
- `tc qdisc show`: Display queueing disciplines configured on all interfaces.
- `tc -s qdisc show dev <interface>`: Show qdisc statistics including backlog, drops, and overlimits.
- `tc class show dev <interface>`: Display traffic classes for hierarchical qdiscs like HTB or HFSC.

**BPF Program Inspection:**
- `bpftool prog list`: Enumerate loaded BPF programs with type, ID, and attachment point.
- `bpftool net show`: Display BPF programs attached to network interfaces.
- `bpftool map dump name <map-name>`: Dump contents of a BPF map used for policy or routing decisions.
- `bpftool prog dump xlated id <prog-id>`: Disassemble a BPF program to inspect its logic.

**Performance Profiling:**
- `perf stat -e cycles,instructions,cache-misses -a sleep 10`: Measure CPU performance counters during a 10-second interval.
- `perf record -a -g -F 99 sleep 10`: Sample call stacks across all CPUs for 10 seconds.
- `perf report`: Analyze recorded samples, displaying hottest functions and call graphs.
- `bpftrace -e 'kprobe:ip_forward { @count = count(); }'`: Count calls to the IP forwarding function in real time.

**Kubernetes Networking:**
- `kubectl get pods -A -o wide`: List all pods with their IP addresses and node assignments.
- `kubectl exec -it <pod-name> -n <namespace> -- ip route`: Inspect routing table inside a pod's network namespace.
- `kubectl exec -it <pod-name> -n <namespace> -- ss -tuln`: List listening sockets inside a pod.
- `kubectl get netpol -A`: List all network policies across namespaces.
- `kubectl describe netpol <policy-name> -n <namespace>`: Show detailed policy rules and selectors.

**Verification Checklist for Router Deployment:**
1. Confirm all expected routes are present in the routing table with correct next-hops and metrics.
2. Verify neighbor cache entries are in reachable state for all next-hop gateways.
3. Validate interface statistics show zero errors, drops, or overruns under normal load.
4. Confirm packet filter rules allow expected traffic and drop unauthorized flows, verified through rule counters.
5. Test end-to-end connectivity to all destination networks with ping and traceroute.
6. Measure baseline forwarding throughput and latency under controlled load conditions.
7. Verify routing protocol adjacencies are established with expected neighbors and LSA/route exchange is occurring.
8. Test link failure and recovery, confirming route convergence completes within acceptable time windows.
9. Validate connection tracking table has sufficient capacity for expected concurrent connection count.
10. Confirm queueing disciplines are configured appropriately for traffic shaping and congestion management requirements.

**Post-Incident Investigation Workflow:**
When investigating a routing-related production incident, follow this systematic approach to isolate root cause:

First, establish whether the failure is in the forwarding plane or control plane. Attempt connectivity to the affected destination with `ping`. If ping fails, check the routing table on the source host and all intermediate routers with `ip route get <destination>`. This identifies where the routing failure occurs. If the route exists but traffic still fails, the issue is in the forwarding plane—packet filters, interface state, or link degradation.

Second, examine interface statistics for packet loss indicators. Execute `ip -s -s link show` on each router in the path and identify interfaces with increasing error or drop counters. Correlate these counters with `tcpdump` captures on the same interfaces to determine whether packets are arriving but being dropped, or not arriving at all. A rising RX drop counter with corresponding tcpdump evidence of packet arrival indicates buffer exhaustion or packet filter drops. An interface with no RX packets in tcpdump but expected traffic flows indicates an upstream link failure or incorrect routing.

Third, inspect packet filter rules and connection tracking state. Execute `iptables -t filter -L -v -n` and identify rules with non-zero counters that should be zero, or rules with zero counters that should be incrementing. Check the connection tracking table for spurious entries or table exhaustion with `conntrack -L` and `conntrack -S`. High `insert_failed` or `drop` counts in conntrack statistics indicate state table overflow.

Fourth, analyze routing protocol state if dynamic routing is in use. Query the protocol's neighbor adjacencies, database contents, and route selection decisions. For OSPF, verify that all expected neighbors are in Full state with synchronized databases. For BGP, confirm that peers are Established and the expected routes are being received and selected for installation in the routing table. Route flapping, indicated by frequent neighbor state transitions in the protocol logs, suggests underlying link instability or misconfigured timers.

Fifth, profile performance if the symptom is degraded throughput or increased latency rather than complete connectivity failure. Use `perf` or BPF tracing to identify CPU bottlenecks in the forwarding path. Measure queueing delay with `tc -s qdisc show` and latency distribution with `ping` or specialized tools like `fping`. Compare observed performance against baseline measurements to quantify the degree of degradation.

This systematic methodology, combined with the command reference above, enables rapid root cause identification and remediation during production incidents. The key discipline is methodical isolation: partition the problem space by testing hypotheses in sequence, using diagnostic commands to confirm or refute each hypothesis, until the failure mechanism is unambiguously identified. Avoid the trap of speculative fixes that address symptoms rather than root causes. Each verification command produces objective evidence that either narrows the problem scope or redirects investigation toward a different failure mode. Mastery of this diagnostic discipline, built through deliberate practice in laboratory environments like these exercises, translates directly to reduced mean time to repair in production operations.
