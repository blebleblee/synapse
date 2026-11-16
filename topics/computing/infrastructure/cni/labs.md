# Operational Verification Labs: Cni

## Objective & Environment Setup

The Container Network Interface (CNI) establishes the contract between container orchestrators and network providers, delegating pod networking to modular plugins that configure network namespaces, allocate IP addresses, program routing tables, and enforce policy. Understanding CNI operational correctness requires moving beyond declarative Kubernetes manifests to examine the runtime state of network namespaces, bridge devices, iptables chains, and routing decisions that transform pod specifications into packet flows. This laboratory guide equips infrastructure practitioners with diagnostic procedures to verify CNI plugin behavior, trace packet paths through host and pod network stacks, measure forwarding latency and throughput saturation, and inject faults that expose configuration drift, resource exhaustion, and failure modes masked by high-level abstractions.

The verification environment assumes a Kubernetes cluster running a CNI plugin—Calico, Cilium, Flannel, or Weave—on Linux hosts with kernel 5.4 or later. The host requires root privileges to inspect network namespaces, manipulate iptables rules, and attach eBPF programs. Install the core diagnostic toolchain: `kubectl` for cluster state queries, `iproute2` for namespace and routing inspection, `ethtool` for NIC statistics, `tcpdump` for packet capture, `crictl` for low-level container runtime interaction, `ss` for socket state enumeration, `perf` for kernel tracing, `strace` for system call observation, and `bpftool` for eBPF map and program introspection. On Debian-based systems, provision these tools with `apt-get install -y iproute2 ethtool tcpdump linux-tools-generic bpftrace`. For Red Hat derivatives, substitute `yum install -y iproute ethtool tcpdump perf bpftrace`. Verify kernel support for eBPF and network namespaces by confirming `/sys/fs/bpf` is mounted and `/proc/self/ns/net` exists.

Configure a test workload comprising at least three pods distributed across two nodes to exercise inter-node routing, service load balancing, and network policy enforcement. Deploy a simple HTTP echo server using `kubectl create deployment echo --image=hashicorp/http-echo --replicas=3 -- -text="response"` and expose it via a ClusterIP service with `kubectl expose deployment echo --port=5678`. Label one pod with `role=client` to serve as the traffic source and another with `role=isolated` to test network policy deny rules. This topology provides the foundation for tracing packet flows from pod network namespaces through veth pairs, bridge devices or overlay tunnels, host routing tables, and across the physical fabric to remote nodes, then back through the reverse path to verify bidirectional connectivity and policy enforcement at every hop.

## Exercise 1: Live State & Internal Subsystem Inspection

Begin verification by mapping the relationship between Kubernetes pod abstractions and the underlying Linux networking primitives that implement CNI connectivity. Each pod receives a dedicated network namespace containing its own loopback interface, routing table, and network device. The CNI plugin creates a virtual Ethernet pair—one end residing in the pod namespace, the other anchored in the host namespace—and configures IP addresses, routes, and firewall rules to forward traffic between the pod and the cluster network. Inspect this mapping by selecting a running pod and extracting its container runtime identifier, network namespace path, and assigned IP address.

Start by listing all pods across namespaces with `kubectl get pods -A -o wide` to identify a target pod and its host node. Note the pod name, namespace, and IP address. SSH to the node hosting the pod and query the container runtime for the pod's pause container, which holds the network namespace shared by all containers in the pod. Use `crictl pods` to list pod sandboxes, then filter for the target pod with `crictl pods --name <pod-name>` to obtain the pod sandbox ID. Extract the container ID of the pause container with `crictl ps --pod <pod-sandbox-id>`, then inspect the container's process namespace with `crictl inspect <container-id> | jq -r '.info.pid'` to retrieve the process ID. The network namespace path resides at `/proc/<pid>/ns/net`. Verify the namespace exists with `ls -l /proc/<pid>/ns/net` and note the inode number, which uniquely identifies the namespace.

Enter the pod's network namespace using `nsenter` to execute commands within the isolated network environment. Run `nsenter -t <pid> -n ip addr show` to enumerate all network interfaces visible inside the pod. The output reveals the loopback interface `lo` with address `127.0.0.1`, and a virtual Ethernet interface typically named `eth0` with the pod's cluster IP address. Record the interface name and MAC address. Next, inspect the pod's routing table with `nsenter -t <pid> -n ip route show` to verify the default gateway points to the host-side veth peer, usually an address in the pod CIDR range. Confirm the routing decision by pinging the Kubernetes DNS service from within the pod namespace: `nsenter -t <pid> -n ping -c 3 10.96.0.10`. Successful replies indicate correct routing and DNS resolution.

Exit the pod namespace and examine the host-side veth peer. The peer interface name follows the pattern `veth<random>` or `cali<truncated-hash>` depending on the CNI plugin. List all veth devices on the host with `ip link show type veth` and correlate the peer index from the pod's `eth0` with the host-side interface using `ip link show | grep <peer-index>`. Once identified, inspect the veth device's statistics with `ip -s link show <veth-name>` to observe transmitted and received packet counts, errors, and drops. Zero errors and drops indicate healthy forwarding. If the CNI plugin uses a bridge (as in Flannel or Weave), verify the veth is enslaved to the bridge with `ip link show master <bridge-name>`. For Calico's direct routing, confirm the veth lacks a master and the host routing table contains a direct route to the pod IP via the veth device: `ip route show | grep <pod-ip>`.

Trace the packet path from the pod through the veth pair to the host routing decision. Initiate a test connection from the pod to an external endpoint, such as a ClusterIP service. Use `nsenter -t <pid> -n curl <service-ip>:<port>` while simultaneously capturing packets on both ends of the veth pair. On the pod side, run `nsenter -t <pid> -n tcpdump -i eth0 -nn` to observe outbound SYN packets. On the host side, run `tcpdump -i <veth-name> -nn` to confirm the packets traverse the veth. Compare MAC addresses, IP source and destination, and TCP sequence numbers to verify frame integrity across the namespace boundary. If the plugin employs VXLAN or other overlay encapsulation, inspect the outer IP header on the host's physical interface with `tcpdump -i <physical-nic> -nn udp port 4789` to observe the encapsulated frames.

Inspect iptables rules that enforce network policies and service load balancing. Kubernetes kube-proxy or the CNI plugin (in the case of Cilium or Calico with eBPF datapath) programs iptables chains in the `nat`, `filter`, and `mangle` tables. Dump the `nat` table's `KUBE-SERVICES` and `KUBE-SVC-*` chains with `iptables -t nat -L KUBE-SERVICES -n -v` to observe service IP to endpoint DNAT transformations. For a ClusterIP service, locate the chain matching the service IP and port, then trace through the probability-based load balancing chains (`KUBE-SEP-*`) to verify equal distribution across endpoints. Confirm source NAT (SNAT) for pod-to-external traffic in the `POSTROUTING` chain with `iptables -t nat -L POSTROUTING -n -v`. Count packet and byte counters to verify traffic is hitting the expected rules. If counters remain zero despite active traffic, suspect eBPF bypass or a misconfigured policy.

For CNI plugins leveraging eBPF (Cilium), query the active eBPF programs attached to network interfaces with `bpftool net show`. The output lists programs attached to `tc ingress` and `tc egress` hooks on the host veth devices and physical NICs. Inspect a specific program's metadata with `bpftool prog show id <prog-id>` and dump the JIT-compiled assembly with `bpftool prog dump xlated id <prog-id>`. While the raw bytecode is dense, confirm the program type (`sched_cls` for traffic control) and the map references. List all eBPF maps with `bpftool map list`, then examine the contents of endpoint and policy maps with `bpftool map dump id <map-id>`. These maps encode pod IP to endpoint ID mappings and network policy verdict caches. Cross-reference the pod IP from earlier steps to verify its presence in the endpoint map.

Validate DNS resolution within the pod namespace by querying the cluster DNS service directly. Enter the pod namespace and perform an `nslookup` or `dig` query: `nsenter -t <pid> -n nslookup kubernetes.default.svc.cluster.local`. The response should resolve to the cluster IP of the `kubernetes` service. Inspect `/etc/resolv.conf` inside the pod with `nsenter -t <pid> -n cat /etc/resolv.conf` to confirm the nameserver points to the Kubernetes DNS service IP (typically `10.96.0.10` or the cluster-configured DNS address). If resolution fails, verify the DNS pod is running with `kubectl get pods -n kube-system -l k8s-app=kube-dns`, inspect its logs for errors with `kubectl logs -n kube-system <dns-pod>`, and confirm the service endpoint exists with `kubectl get endpoints -n kube-system kube-dns`.

Conclude this exercise by constructing a complete connectivity matrix from pod to service to endpoint, verifying each hop with packet captures and routing table lookups. From the client pod, initiate a connection to the echo service ClusterIP. Simultaneously capture packets in the pod namespace, on the host veth, and on the physical NIC to trace the packet transformation from pod source IP through DNAT to endpoint pod IP, encapsulation if using overlay, and decapsulation at the destination node. Compare the captured sequence numbers, acknowledgment numbers, and payload to confirm end-to-end integrity. This multi-layer inspection establishes confidence that the CNI plugin correctly implements the Kubernetes networking model: every pod receives a unique IP, all pods can communicate without NAT (unless explicitly configured), and services abstract endpoint topology through transparent load balancing.

## Exercise 2: Benchmarking & Saturation Profiling

Quantifying CNI forwarding performance requires measuring latency and throughput at multiple points in the packet path, from pod application socket through the kernel network stack, veth pair, bridge or overlay, and physical NIC. Baseline measurements establish expected performance under steady-state load, while saturation profiling identifies bottlenecks—CPU scheduling delays, iptables rule traversal overhead, bridge forwarding limits, or NIC descriptor exhaustion—that manifest only under stress. This exercise employs `iperf3` for bulk throughput, `wrk` for HTTP request rate, and `perf` for CPU profiling to correlate packet forwarding with kernel function invocations.

Deploy an `iperf3` server pod on one node and a client pod on a different node to measure inter-node throughput. Create a DaemonSet to ensure one server instance per node: `kubectl create deployment iperf-server --image=networkstatic/iperf3 -- -s`. Label the server pod with `app=iperf-server` and create a headless service to expose the pod IP directly. Deploy a client pod with `kubectl run iperf-client --image=networkstatic/iperf3 --rm -it -- /bin/sh`, then initiate a TCP throughput test from the client to the server pod IP: `iperf3 -c <server-pod-ip> -t 30 -P 4`. The `-P 4` flag spawns four parallel streams to saturate the connection. Record the aggregate throughput in Gbps and observe the CPU utilization on both nodes with `top` or `htop`. Throughput below line rate (e.g., significantly less than 10 Gbps on a 10GbE link) or high `ksoftirqd` CPU usage indicates packet processing bottlenecks in the kernel.

While the `iperf3` test runs, profile the kernel's network stack with `perf`. On the server node, start a 30-second CPU profile scoped to network-related functions: `perf record -a -g -e cycles --call-graph dwarf -- sleep 30`. After the recording completes, generate a report with `perf report` and filter for `__netif_receive_skb`, `ip_rcv`, `tcp_v4_rcv`, and iptables-related functions like `ipt_do_table`. High sample counts in `ipt_do_table` relative to core TCP processing functions signal iptables rule traversal overhead. If the CNI plugin uses many rules (common with kube-proxy in iptables mode and hundreds of services), consider switching to IPVS mode or eBPF datapath to bypass iptables entirely. Compare the profile with a baseline captured during idle to isolate the incremental cost of packet forwarding.

Measure single-stream latency using `ping` and `hping3` to assess round-trip time and jitter. From the client pod, execute `ping -c 100 -i 0.2 <server-pod-ip>` to send 100 ICMP echo requests at five packets per second. Calculate the mean, minimum, maximum, and standard deviation of the RTT values. Baseline inter-node RTT on a local Ethernet network should range from 0.1 to 0.5 milliseconds. Elevated latency (above 1 ms) or high jitter (standard deviation exceeding 0.2 ms) suggests CPU scheduling delays, queue contention, or interrupt coalescing issues. Repeat the test with `hping3` to send TCP SYN packets: `hping3 -S -c 100 -i u200000 <server-pod-ip> -p 5678`. This bypasses ICMP processing and exercises the full TCP stack, providing a more realistic latency profile.

Profile the overhead introduced by the veth pair by comparing throughput between pods on the same node (same-node) versus pods on different nodes (inter-node). Deploy two `iperf3` pods on the same node and measure throughput with `iperf3 -c <same-node-pod-ip> -t 30 -P 4`. Same-node traffic traverses only the veth pair and host bridge or routing table, bypassing the physical NIC and any overlay encapsulation. Compare this throughput with the inter-node result. A significant drop in inter-node throughput relative to same-node throughput implicates the overlay (VXLAN, IP-in-IP) or physical network. To isolate overlay overhead, disable encapsulation temporarily (if supported by the CNI plugin) and re-run the inter-node test, then calculate the encapsulation tax as the percentage difference.

Stress test the CNI plugin's handling of connection scale by launching a high-rate HTTP request workload. Deploy an Nginx pod as the target and use `wrk` from the client pod to generate concurrent connections: `wrk -t 4 -c 400 -d 30s --latency http://<nginx-pod-ip>:80/`. The `-c 400` flag opens 400 concurrent connections distributed across four threads. Monitor the request rate (requests per second) and latency distribution (50th, 99th percentile). Correlate client-side metrics with server-side socket state using `ss -s` on the server node to enumerate TCP states (ESTABLISHED, TIME_WAIT). Excessive TIME_WAIT sockets indicate rapid connection churn and potential ephemeral port exhaustion. Inspect the conntrack table size with `cat /proc/sys/net/netfilter/nf_conntrack_count` and compare against the maximum with `cat /proc/sys/net/netfilter/nf_conntrack_max`. Approaching the maximum triggers conntrack table drops, visible in `dmesg` as "nf_conntrack: table full" messages.

Benchmark service load balancing latency by measuring request distribution variance across endpoints. Create a service with three backend pods and instrument each pod to log request timestamps. Use `wrk` to send 10,000 requests to the service ClusterIP, then extract the pod logs and calculate the coefficient of variation in request count per pod. Ideal load balancing yields equal distribution (coefficient near zero), while high variance indicates imbalanced hashing or endpoint churn. If using kube-proxy in iptables mode, confirm the KUBE-SVC chain employs statistically correct probability branching with `iptables -t nat -L KUBE-SVC-<hash> -n -v` and verify each KUBE-SEP chain receives proportional packets.

Isolate NIC hardware bottlenecks by monitoring interrupt rates and queue depths during saturation. While running the `iperf3` throughput test, inspect the NIC's interrupt statistics with `cat /proc/interrupts | grep <nic-name>` before and after the test to calculate interrupts per second. High interrupt rates (exceeding 100,000 per second per core) without proportional throughput suggest interrupt processing overhead. Check the NIC's ring buffer utilization with `ethtool -S <nic-name> | grep -E 'rx_dropped|tx_dropped'`. Non-zero dropped counters indicate the NIC's hardware queues are full, implying the kernel cannot process packets fast enough. Increase the ring buffer size with `ethtool -G <nic-name> rx 4096 tx 4096` (if supported) and re-run the test. Compare CPU usage before and after the ring buffer increase to assess whether the bottleneck shifted from hardware to software.

Conclude the benchmarking exercise by constructing a performance budget that maps application requirements (e.g., 10 Gbps aggregate throughput, 1 ms p99 latency) to measured CNI forwarding characteristics. Document the baseline throughput, latency, and CPU utilization under nominal load, then identify the saturation point—the load level at which latency spikes or throughput plateaus—through incremental stress testing. This budget informs capacity planning and triggers for horizontal scaling, NIC upgrades, or CNI plugin migration to eBPF datapath for higher efficiency.

## Exercise 3: Fault Injection & Recovery Analysis

Resilient CNI operation demands graceful degradation under adverse conditions—network partitions, plugin crashes, configuration drift, and resource exhaustion. Fault injection exercises expose failure modes obscured by steady-state assumptions, testing the system's ability to detect, isolate, and recover from faults without manual intervention. This exercise introduces controlled failures at multiple layers: network namespace isolation, routing table corruption, iptables rule deletion, overlay tunnel disruption, and CNI plugin restart.

Begin with network partition simulation by dropping packets between two nodes using iptables on the physical NIC. Identify two nodes hosting test pods and their physical network interface names with `ip link show`. On the source node, install a DROP rule targeting the destination node's IP: `iptables -I FORWARD -s <source-node-ip> -d <dest-node-ip> -j DROP`. Verify the rule with `iptables -L FORWARD -n -v` and confirm packet counters increment. From a pod on the source node, attempt to reach a pod on the destination node: `kubectl exec <source-pod> -- curl <dest-pod-ip>:5678`. The connection should timeout after the TCP retransmission limit. Observe the kubelet and CNI plugin logs on both nodes with `journalctl -u kubelet -f` and `kubectl logs -n kube-system <cni-plugin-pod>` to verify whether the plugin detects the partition and logs connectivity failures. Remove the DROP rule with `iptables -D FORWARD -s <source-node-ip> -d <dest-node-ip> -j DROP` and confirm connectivity recovery within the TCP keepalive interval.

Inject routing table corruption by deleting the default route in a pod's network namespace. Identify a target pod and enter its namespace with `nsenter` as in Exercise 1. Delete the default route with `nsenter -t <pid> -n ip route del default`. Attempt to reach an external IP from the pod: `nsenter -t <pid> -n ping 8.8.8.8`. The ping fails immediately with "Network is unreachable." Inspect the pod's routing table with `nsenter -t <pid> -n ip route show` to confirm the absence of a default gateway. This simulates the effect of a CNI plugin failure to configure routes during pod startup. Restore the route manually with `nsenter -t <pid> -n ip route add default via <gateway-ip>` and verify connectivity recovery. In production, the kubelet's liveness probe should detect the pod's network failure and restart the pod, triggering CNI plugin re-invocation to restore correct state.

Simulate CNI plugin crash by killing the plugin's daemonset pod on a node and observing the impact on existing and new pods. Identify the CNI plugin daemonset with `kubectl get daemonsets -n kube-system` (e.g., `calico-node`, `cilium`, `kube-flannel`). Delete the pod running on the target node with `kubectl delete pod -n kube-system <cni-plugin-pod>`. The daemonset controller immediately schedules a replacement pod, but there is a brief window where the plugin is unavailable. During this window, create a new pod on the affected node with `kubectl run test-pod --image=busybox --overrides='{"spec":{"nodeName":"<node-name>"}}' --command -- sleep 3600`. Inspect the pod's status with `kubectl describe pod test-pod`. If the CNI plugin is unavailable, the pod remains in `ContainerCreating` state with an event message indicating CNI plugin failure. Once the replacement plugin pod reaches `Running` state, the kubelet retries CNI invocation and the test pod transitions to `Running`. Verify the pod receives an IP address and connectivity works. This confirms the CNI plugin's stateless design—existing pods retain connectivity because their network namespaces persist across plugin restarts.

Introduce iptables rule corruption by flushing the NAT table's KUBE-SERVICES chain while services are active. On a node, execute `iptables -t nat -F KUBE-SERVICES` to delete all service DNAT rules. Attempt to reach a ClusterIP service from a pod: `kubectl exec <pod> -- curl <service-ip>:5678`. The connection fails or times out because the service IP no longer maps to endpoint pod IPs. Inspect the NAT table with `iptables -t nat -L KUBE-SERVICES -n -v` to confirm the chain is empty. Restore the rules by restarting kube-proxy on the node with `systemctl restart kubelet` (which triggers kube-proxy pod restart in static pod deployments) or by directly restarting the kube-proxy pod with `kubectl delete pod -n kube-system <kube-proxy-pod>`. After kube-proxy reinitializes, verify the KUBE-SERVICES chain repopulates with `iptables -t nat -L KUBE-SERVICES -n -v` and confirm service connectivity recovery.

Test overlay tunnel disruption by blocking VXLAN or IP-in-IP traffic between nodes. If using VXLAN (e.g., Flannel), install a DROP rule for UDP port 4789 on the source node: `iptables -I INPUT -p udp --dport 4789 -j DROP`. For IP-in-IP (e.g., Calico), block protocol 4 packets: `iptables -I INPUT -p ipencap -j DROP`. Verify inter-node pod connectivity fails while same-node connectivity remains intact. Capture packets on the physical NIC with `tcpdump -i <nic> -nn` to confirm overlay traffic is absent. Remove the DROP rule and observe automatic recovery as the overlay tunnel re-establishes. This fault injection validates that the CNI plugin's overlay encapsulation is mandatory for inter-node communication and that no fallback direct routing exists.

Exhaust IP address allocation by creating pods until the CNI plugin's IPAM (IP Address Management) pool is depleted. Query the plugin's IP pool configuration—for Calico, use `calicoctl get ippool -o yaml`; for Cilium, use `kubectl get ciliumnodes -o yaml` and inspect the `spec.ipam.podCIDRs` field. Calculate the total available IPs in the CIDR range (e.g., a /24 provides 254 usable addresses). Create a deployment scaled to exceed this limit: `kubectl create deployment ip-exhaust --image=busybox --replicas=300 -- sleep 3600`. Monitor pod scheduling with `kubectl get pods -o wide | grep ip-exhaust`. Pods beyond the IP pool capacity remain in `Pending` state with events indicating "Failed to allocate IP address." Inspect the CNI plugin logs to confirm IPAM exhaustion messages. Delete the deployment with `kubectl delete deployment ip-exhaust` and verify the IP pool replenishes as pods terminate and release their addresses.

Inject DNS resolution failure by deleting the kube-dns or coredns service endpoints. Backup the endpoints with `kubectl get endpoints -n kube-system kube-dns -o yaml > kube-dns-endpoints-backup.yaml`, then delete them with `kubectl delete endpoints -n kube-system kube-dns`. Attempt DNS resolution from a pod: `kubectl exec <pod> -- nslookup kubernetes.default.svc.cluster.local`. The query times out or returns NXDOMAIN. Inspect the DNS pod logs with `kubectl logs -n kube-system <coredns-pod>` to observe the absence of endpoint readiness checks. Restore the endpoints with `kubectl apply -f kube-dns-endpoints-backup.yaml` and verify resolution recovery. This test confirms the dependency of CNI-provided connectivity on auxiliary cluster services like DNS.

Conclude the fault injection exercise by documenting the recovery time objective (RTO) for each failure scenario—the elapsed time from fault introduction to full connectivity restoration. Measure RTO using timestamps from logs and `kubectl events` output. Assess whether the observed RTO meets application SLAs and identify opportunities for reducing recovery time through faster liveness probes, CNI plugin redundancy, or automated remediation scripts. This empirical failure analysis transforms abstract resilience claims into quantified operational confidence.

## Diagnostic Cheat Sheet & Verification Checklist

Consolidate the verification procedures into a rapid diagnostic protocol for routine CNI health checks and incident response. This checklist provides the essential commands and expected outputs to confirm correct CNI operation, detect common misconfigurations, and isolate failure domains during outages.

**Pod Network Namespace Inspection:**
- List all pods and nodes: `kubectl get pods -A -o wide`
- Get pod sandbox ID: `crictl pods --name <pod-name>`
- Get pause container PID: `crictl inspect <container-id> | jq -r '.info.pid'`
- Enter pod netns: `nsenter -t <pid> -n`
- List pod interfaces: `nsenter -t <pid> -n ip addr show`
- Show pod routes: `nsenter -t <pid> -n ip route show`
- Test pod connectivity: `nsenter -t <pid> -n ping <target-ip>`

**Host-Side veth and Bridge Verification:**
- List all veth pairs: `ip link show type veth`
- Show veth statistics: `ip -s link show <veth-name>`
- Find veth master bridge: `ip link show master <bridge-name>`
- Verify direct routes: `ip route show | grep <pod-ip>`
- Capture veth traffic: `tcpdump -i <veth-name> -nn`

**Iptables and Service Load Balancing:**
- Dump NAT table: `iptables -t nat -L -n -v`
- Inspect service chains: `iptables -t nat -L KUBE-SERVICES -n -v`
- Show endpoint chains: `iptables -t nat -L KUBE-SEP-<hash> -n -v`
- Check POSTROUTING SNAT: `iptables -t nat -L POSTROUTING -n -v`
- Monitor rule hit counts: `watch -n 1 'iptables -t nat -L -n -v | grep <service-ip>'`

**eBPF Program and Map Inspection (Cilium):**
- List attached programs: `bpftool net show`
- Show program details: `bpftool prog show id <prog-id>`
- Dump program bytecode: `bpftool prog dump xlated id <prog-id>`
- List all maps: `bpftool map list`
- Dump map contents: `bpftool map dump id <map-id>`
- Trace eBPF events: `bpftrace -e 'tracepoint:xdp:* { printf("%s\n", comm); }'`

**DNS and Service Discovery:**
- Test DNS resolution: `kubectl exec <pod> -- nslookup kubernetes.default.svc.cluster.local`
- Inspect resolv.conf: `kubectl exec <pod> -- cat /etc/resolv.conf`
- Check DNS pod status: `kubectl get pods -n kube-system -l k8s-app=kube-dns`
- View DNS logs: `kubectl logs -n kube-system <coredns-pod>`
- Verify service endpoints: `kubectl get endpoints <service-name>`

**Performance and Throughput:**
- Measure inter-node throughput: `iperf3 -c <server-pod-ip> -t 30 -P 4`
- Test same-node throughput: `iperf3 -c <same-node-pod-ip> -t 30 -P 4`
- Measure RTT latency: `ping -c 100 -i 0.2 <target-ip>`
- Profile kernel network stack: `perf record -a -g -e cycles -- sleep 30 && perf report`
- Monitor NIC statistics: `ethtool -S <nic-name>`
- Check conntrack table: `cat /proc/sys/net/netfilter/nf_conntrack_count`

**Overlay and Encapsulation:**
- Capture VXLAN traffic: `tcpdump -i <nic> -nn udp port 4789`
- Capture IP-in-IP traffic: `tcpdump -i <nic> -nn proto 4`
- Verify overlay configuration: `ip -d link show <vxlan-device>`
- List FDB entries: `bridge fdb show dev <vxlan-device>`

**CNI Plugin and IPAM:**
- Check CNI plugin pods: `kubectl get pods -n kube-system -l <cni-label>`
- View plugin logs: `kubectl logs -n kube-system <cni-pod>`
- Inspect IP pool (Calico): `calicoctl get ippool -o yaml`
- Inspect IPAM (Cilium): `kubectl get ciliumnodes -o yaml`
- List allocated IPs: `kubectl get pods -A -o jsonpath='{.items[*].status.podIP}' | tr ' ' '\n' | sort | uniq -c`

**Fault Injection Commands:**
- Drop inter-node traffic: `iptables -I FORWARD -s <src-ip> -d <dst-ip> -j DROP`
- Delete pod default route: `nsenter -t <pid> -n ip route del default`
- Flush NAT rules: `iptables -t nat -F KUBE-SERVICES`
- Block VXLAN: `iptables -I INPUT -p udp --dport 4789 -j DROP`
- Block IP-in-IP: `iptables -I INPUT -p ipencap -j DROP`
- Delete CNI plugin pod: `kubectl delete pod -n kube-system <cni-pod>`

**Expected Outputs and Thresholds:**
- Pod `eth0` interface: Single IP address matching `kubectl get pod -o wide`, MTU typically 1450 (VXLAN) or 1480 (IP-in-IP)
- Host veth statistics: Zero RX/TX errors and drops under normal load
- Iptables KUBE-SERVICES: One chain per ClusterIP service, packet counters incrementing
- Same-node throughput: Near line rate (e.g., 9+ Gbps on 10GbE for large transfers)
- Inter-node RTT: 0.1–0.5 ms on local Ethernet, < 5 ms across availability zones
- Conntrack count: Below 80% of `nf_conntrack_max` to avoid table saturation
- CNI plugin pods: All pods `Running`, recent restarts indicate instability

**Common Failure Signatures:**
- Pod stuck in `ContainerCreating`: CNI plugin failure, inspect kubelet and plugin logs
- Intermittent connectivity: Conntrack table full, increase `nf_conntrack_max`
- DNS resolution fails: CoreDNS pods not ready, check service endpoints
- Service unreachable: Iptables rules missing or incorrect, verify kube-proxy operation
- High latency: CPU saturation in `ksoftirqd`, reduce iptables rule count or switch to eBPF
- Asymmetric routing: Overlay misconfiguration, verify tunnel endpoints and FDB entries

This operational verification framework transforms CNI from a black-box abstraction into a transparent, measurable subsystem. By mastering namespace inspection, packet tracing, performance profiling, and fault injection, infrastructure practitioners gain the empirical confidence to deploy, tune, and troubleshoot container networking at scale. The diagnostic discipline cultivated through these exercises—grounding high-level connectivity claims in verifiable packet flows, routing decisions, and kernel state—extends naturally to adjacent domains of distributed systems reliability, where first-principles inspection and quantified failure analysis replace assumption-driven operations.
