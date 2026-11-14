# Operational Verification Labs: Switches

## Objective & Environment Setup

Network switches form the foundational data plane of modern infrastructure, operating at Layer 2 (Data Link) and Layer 3 (Network) of the OSI model to forward Ethernet frames and IP packets across physical and virtual topologies. In production environments, switches range from physical Top-of-Rack (ToR) devices in data centers to software-defined virtual switches inside Linux kernel namespaces, Open vSwitch (OVS) bridges in OpenStack deployments, and CNI plugin datapaths in Kubernetes clusters. This lab guide equips systems engineers with the diagnostic methodology to verify switching state, measure forwarding performance, and analyze failure modes using authentic CLI tooling: `iproute2` for kernel networking state, `ethtool` for NIC-level statistics, `tcpdump` for packet capture, `perf` for CPU profiling, and `kubectl` for Kubernetes network policy verification.

The architecture of a network switch revolves around three core subsystems: the **forwarding plane**, which performs MAC address table lookups and frame replication at line rate; the **control plane**, which runs spanning tree protocols (STP/RSTP), VLAN tagging logic, and link aggregation (LACP); and the **management plane**, which exposes SNMP counters, syslog streams, and API endpoints for orchestration. Physical switches implement these planes in dedicated ASICs (Application-Specific Integrated Circuits) such as Broadcom Trident or Mellanox Spectrum, achieving sub-microsecond latency and terabit-scale throughput. Software switches like Linux Bridge and OVS execute the same logical operations but leverage general-purpose CPU cores, eBPF JIT compilation, and DPDK (Data Plane Development Kit) for hardware offload.

In this lab, we focus on Linux-based software switching because it exposes the full state machine through standard kernel interfaces, making it ideal for deep operational verification. Every exercise targets a specific failure domain: Exercise 1 dissects live forwarding tables and bridge port states to detect misconfigured VLANs or stale MAC entries; Exercise 2 measures packet forwarding rates under synthetic load to identify CPU bottlenecks or NIC queue saturation; Exercise 3 injects link failures and STP topology changes to validate convergence timers and failover correctness.

Before beginning the exercises, prepare a Linux host (physical server or virtual machine) with kernel version 5.10 or newer, which includes modern TC (Traffic Control) eBPF hooks and enhanced bridge statistics. Install the required diagnostic toolchain:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y iproute2 ethtool tcpdump linux-tools-common linux-tools-generic bridge-utils net-tools iperf3

# RHEL/CentOS/Fedora
sudo dnf install -y iproute ethtool tcpdump perf bridge-utils net-tools iperf3

# Verify kernel version and bridge module
uname -r
lsmod | grep bridge
```

For Kubernetes cluster environments, ensure `kubectl` is configured with admin credentials and CNI plugins (Calico, Cilium, or Flannel) are deployed. The exercises will reference both standalone Linux bridges and CNI-managed virtual switches to demonstrate cross-domain troubleshooting techniques.

Conceptually, a switch maintains a **MAC address table** (also called a CAM table in hardware switches or an FDB—Forwarding Database—in Linux) that maps each learned MAC address to an egress port. When a frame arrives, the switch extracts the source MAC and updates the FDB with a timestamp; it then looks up the destination MAC and forwards the frame to the corresponding port. If the destination is unknown, the switch floods the frame to all ports except the ingress port, emulating a hub. This flood-and-learn mechanism underpins Ethernet's plug-and-play simplicity but also creates the risk of broadcast storms if loops exist in the physical topology. Spanning Tree Protocol (STP) prevents loops by electing a root bridge and blocking redundant links, maintaining a loop-free tree structure.

In software-defined networking, OpenFlow controllers and eBPF programs replace or augment traditional control planes, injecting FDB entries and flow rules dynamically. For example, Kubernetes network policies compile into iptables rules or eBPF TC classifiers that enforce pod-to-pod segmentation at the virtual switch layer. Understanding the relationship between high-level policy abstractions and low-level forwarding state is critical for diagnosing connectivity failures that manifest as "pod cannot reach service" but originate from a missing FDB entry or a misconfigured VLAN tag.

The diagnostic workflow for switch verification follows a layered methodology: first, inspect the control plane state (bridge configuration, port membership, STP roles); second, examine the data plane statistics (packet counters, drop counters, queue depths); third, capture live traffic to correlate application-layer symptoms with L2/L3 anomalies; and finally, stress-test the forwarding pipeline under load to expose race conditions or resource exhaustion. This approach mirrors how production SREs troubleshoot network incidents: start with cheap, non-intrusive reads of `/sys` and `ip` commands, escalate to packet capture when state inspection is inconclusive, and reproduce failures in isolated test harnesses before patching live systems.

Each exercise provides the complete command syntax, expected output, and interpretive guidance. The exercises are designed to be repeatable: all configuration changes are scoped to ephemeral network namespaces or temporary bridge devices, ensuring the host system remains unaffected. After completing the labs, you will possess a mental model of switching internals, a CLI muscle memory for rapid diagnostics, and a reference implementation for automated health checks in production monitoring systems.

---

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise teaches the foundational skill of reading switch state from the Linux kernel's bridge subsystem. We will create a virtual bridge, attach VETH (Virtual Ethernet) pairs simulating connected devices, observe MAC address learning, and inspect STP port states. The goal is to build intuition for how the kernel's FDB evolves in response to traffic and how misconfigurations (wrong VLAN IDs, disabled ports) manifest in the state output.

### 1.1 Creating a Test Bridge with Virtual Ports

Begin by creating an isolated network namespace to prevent interference with the host's default networking stack. A network namespace is a kernel facility that partitions the global network state—interfaces, routing tables, iptables rules—into independent instances. Inside this namespace, we construct a Linux bridge named `br0` and attach four VETH pairs representing four simulated hosts.

```bash
# Create a dedicated network namespace
sudo ip netns add switch-lab

# Enter the namespace for all subsequent commands
sudo ip netns exec switch-lab bash

# Inside the namespace, create a bridge device
ip link add name br0 type bridge

# Configure bridge parameters: disable STP initially for clarity
ip link set br0 type bridge stp_state 0

# Bring the bridge interface up
ip link set br0 up

# Create four VETH pairs (each pair has two ends: vethX and vethX-peer)
for i in {1..4}; do
    ip link add veth${i} type veth peer name veth${i}-peer
    ip link set veth${i} master br0
    ip link set veth${i} up
    ip link set veth${i}-peer up
    # Assign a unique MAC address to each peer for easy identification
    ip link set veth${i}-peer address 02:00:00:00:00:0${i}
done

# Verify bridge membership
bridge link show
```

The `bridge link show` command outputs each port's membership, forwarding state, and per-port flags. At this stage, all ports are in the `forwarding` state because STP is disabled. In a production environment, you would verify that all expected physical NICs (e.g., `eno1`, `eno2`) appear as bridge members and that no ports are stuck in `blocking` or `disabled` states due to STP miscalculation.

### 1.2 Inspecting the Forwarding Database (FDB)

The FDB is the heart of switch operation. Initially, the FDB is empty because no traffic has traversed the bridge. We will generate ARP (Address Resolution Protocol) traffic to trigger MAC learning and then inspect the resulting FDB entries.

```bash
# Assign IP addresses to the peer interfaces (simulating connected hosts)
ip addr add 192.168.100.1/24 dev veth1-peer
ip addr add 192.168.100.2/24 dev veth2-peer
ip addr add 192.168.100.3/24 dev veth3-peer
ip addr add 192.168.100.4/24 dev veth4-peer

# Display the current FDB (should be mostly empty except for bridge's own MAC)
bridge fdb show dev br0

# Generate traffic: ping from veth1-peer to veth2-peer
# This triggers ARP requests and MAC learning
ping -c 3 -I veth1-peer 192.168.100.2

# Inspect the FDB again
bridge fdb show
```

After the ping, the FDB contains dynamically learned entries mapping the MAC addresses of `veth1-peer` and `veth2-peer` to their respective bridge ports. Each entry includes a timestamp (in kernel ticks) indicating when the MAC was last seen. Stale entries expire after a configurable aging timeout (default 300 seconds), which you can query via:

```bash
cat /sys/class/net/br0/bridge/ageing_time
```

In production switches, stale FDB entries cause intermittent connectivity failures: packets destined for an aged-out MAC are flooded to all ports, creating broadcast storms or triggering rate limiters. The diagnostic pattern is to compare the FDB against the expected topology (via LLDP neighbor discovery or network inventory databases) and identify missing or incorrect entries.

### 1.3 VLAN Configuration and Tagging

VLANs (Virtual LANs) partition a single physical switch into multiple logical broadcast domains, enforcing L2 isolation. Linux bridges support 802.1Q VLAN tagging, where each frame carries a 12-bit VLAN ID in the Ethernet header. We will configure two VLANs on the bridge and verify that traffic is properly segregated.

```bash
# Enable VLAN filtering on the bridge
ip link set br0 type bridge vlan_filtering 1

# Assign veth1 and veth2 to VLAN 10
bridge vlan add dev veth1 vid 10 pvid untagged
bridge vlan add dev veth2 vid 10 pvid untagged

# Assign veth3 and veth4 to VLAN 20
bridge vlan add dev veth3 vid 20 pvid untagged
bridge vlan add dev veth4 vid 20 pvid untagged

# Display VLAN membership
bridge vlan show
```

The `pvid` (Port VLAN ID) flag designates the VLAN for untagged ingress traffic, while `untagged` specifies that egress frames should be sent without the VLAN tag. This configuration is typical for access ports connecting end hosts. Trunk ports, which carry multiple VLANs to other switches, would omit the `untagged` flag.

Test VLAN isolation by attempting cross-VLAN communication:

```bash
# This ping should succeed (same VLAN)
ping -c 2 -I veth1-peer 192.168.100.2

# This ping should fail (different VLAN)
ping -c 2 -I veth1-peer 192.168.100.3
```

If the second ping succeeds despite VLAN separation, suspect a misconfigured trunk port or a bypassed bridge datapath (e.g., traffic routed at L3 instead of switched at L2). Use `tcpdump` to capture frames and verify the presence or absence of 802.1Q tags:

```bash
tcpdump -i veth1 -e -n -c 10
```

The `-e` flag prints Ethernet headers, revealing VLAN tags in the format `vlan 10`.

### 1.4 Spanning Tree Protocol (STP) State Verification

Re-enable STP to observe port state transitions. STP prevents loops by designating one bridge as the root and blocking redundant paths. In a simple single-bridge topology, all ports transition to `forwarding` immediately, but in multi-bridge scenarios, some ports enter `blocking` to break loops.

```bash
# Enable STP (default is RSTP—Rapid Spanning Tree Protocol)
ip link set br0 type bridge stp_state 1

# Query bridge STP parameters
bridge -d link show | grep state

# Display detailed STP information
cat /sys/class/net/br0/bridge/stp_state
cat /sys/class/net/br0/bridge/root_id
cat /sys/class/net/br0/bridge/root_port
cat /sys/class/net/br0/bridge/topology_change
```

Each port's STP state is one of: `disabled`, `listening`, `learning`, `forwarding`, or `blocking`. The `listening` and `learning` states are transient phases during convergence, each lasting 15 seconds (the default forward delay). The `root_id` file shows the root bridge's MAC address; if this doesn't match your expectations (e.g., a lower-priority bridge has been elected root), investigate bridge priority settings:

```bash
# Display bridge priority (default 32768)
cat /sys/class/net/br0/bridge/priority

# Lower the priority to force this bridge to become root (lower value wins)
echo 16384 > /sys/class/net/br0/bridge/priority
```

In production data centers, STP misconfigurations cause catastrophic outages. A common failure mode: an operator adds a cable between two switches without realizing it creates a loop, STP blocks the new link, but a subsequent STP topology change (triggered by a flapping port elsewhere) causes the entire network to enter the `listening` state, dropping all traffic for 30 seconds. The diagnostic fingerprint is a burst of `TCN` (Topology Change Notification) BPDUs (Bridge Protocol Data Units) in the logs, correlating with connectivity loss. To detect this, monitor the `topology_change` counter:

```bash
watch -n 1 cat /sys/class/net/br0/bridge/topology_change_detected
```

### 1.5 Port Statistics and Error Counters

Every bridge port maintains per-port counters for received/transmitted packets, bytes, drops, and errors. These counters are the first line of defense when diagnosing performance degradation or silent packet loss.

```bash
# Display detailed port statistics
ip -s -s link show br0
ip -s -s link show veth1

# Alternative: use ethtool for NIC-level statistics (works for physical NICs)
ethtool -S veth1
```

Key counters to examine:

- **RX packets / TX packets**: Baseline throughput. A large discrepancy between RX and TX on a switch port suggests unidirectional traffic or a black-hole route.
- **RX dropped / TX dropped**: Frames discarded due to buffer overflow, policy enforcement (iptables, eBPF), or invalid VLAN tags. A non-zero drop counter warrants immediate investigation.
- **RX errors / TX errors**: Physical layer errors such as CRC failures, runt frames, or collisions. On virtual interfaces, errors usually indicate kernel bugs or memory corruption.
- **Multicast / Broadcast**: Excessive broadcast traffic can saturate switch CPU or trigger rate limiters. High multicast counts suggest misconfigured IGMP snooping.

For software switches, also inspect CPU softirq (software interrupt) statistics, since packet processing occurs in kernel context:

```bash
cat /proc/softirqs | grep NET
```

A skewed distribution of `NET_RX` across CPU cores indicates poor RSS (Receive Side Scaling) configuration, causing a single core to bottleneck.

### 1.6 Cleanup

Exit the namespace and delete it to restore the system to a clean state:

```bash
exit  # Exit the namespace shell
sudo ip netns del switch-lab
```

All virtual interfaces and bridge state are automatically deleted when the namespace is destroyed.

---

## Exercise 2: Benchmarking & Saturation Profiling

This exercise measures the forwarding performance of a Linux bridge under synthetic load, identifies CPU bottlenecks, and correlates packet loss with kernel subsystem saturation. We will use `iperf3` to generate sustained traffic, `perf` to profile CPU cycles, and `ss` (socket statistics) to inspect queue depths. The methodology applies equally to physical switches (via remote console) and virtualized switches (via hypervisor instrumentation).

### 2.1 Baseline Throughput Measurement

Reconstruct the bridge topology from Exercise 1, but this time optimize for performance by disabling unnecessary kernel features:

```bash
sudo ip netns add perf-lab
sudo ip netns exec perf-lab bash

# Create bridge with STP disabled and large MTU for efficiency
ip link add name br0 type bridge stp_state 0
ip link set br0 up
ip link set br0 mtu 9000  # Jumbo frames

# Create two VETH pairs for client-server traffic
ip link add veth1 type veth peer name veth1-peer
ip link add veth2 type veth peer name veth2-peer

ip link set veth1 master br0
ip link set veth2 master br0

ip link set veth1 up
ip link set veth2 up
ip link set veth1-peer up mtu 9000
ip link set veth2-peer up mtu 9000

# Assign IP addresses
ip addr add 10.0.0.1/24 dev veth1-peer
ip addr add 10.0.0.2/24 dev veth2-peer
```

Launch an `iperf3` server on `veth2-peer` and a client on `veth1-peer`:

```bash
# Terminal 1: Start iperf3 server
ip netns exec perf-lab iperf3 -s -B 10.0.0.2

# Terminal 2: Start iperf3 client with parallel streams
ip netns exec perf-lab iperf3 -c 10.0.0.2 -t 30 -P 4 -i 5
```

The `-P 4` flag spawns four parallel TCP streams, saturating the bridge's forwarding capacity. The `-i 5` interval provides per-5-second throughput samples, revealing short-term variability. Record the final aggregate throughput (typically reported in Gbits/sec).

On a modern server with 10GbE NICs and minimal CPU load, expect near-line-rate forwarding (9+ Gbps for TCP). Significantly lower throughput indicates a bottleneck. Common culprits:

- **CPU pinning**: Virtual interfaces not bound to NUMA-local CPUs, causing cross-socket memory traffic.
- **Interrupt coalescing**: NIC interrupt rate exceeds CPU capacity. Tune via `ethtool -C`.
- **Kernel lock contention**: Bridge FDB lookups under heavy multicast traffic serialize on a spinlock.

### 2.2 CPU Profiling with `perf`

While `iperf3` is running, profile the kernel's CPU usage to identify hot code paths:

```bash
# Terminal 3: Profile all CPUs for 10 seconds
sudo perf record -a -g -F 99 -- sleep 10

# Generate a report sorted by CPU overhead
sudo perf report --stdio | head -50
```

The `-a` flag profiles all CPUs, `-g` enables call-graph recording (stack traces), and `-F 99` sets the sampling frequency to 99 Hz (a prime number to avoid phase-locking with periodic timers). The output lists functions consuming the most CPU cycles. For bridge forwarding, expect to see:

- `br_handle_frame`: Entry point for ingress frames.
- `br_fdb_update`: MAC learning logic.
- `__dev_queue_xmit`: Egress frame transmission.
- `ip_rcv` / `ip_output`: If L3 processing is involved.

A large percentage in `spin_lock` or `_raw_spin_lock_irqsave` signals contention on the bridge's FDB lock. To mitigate, enable RCU (Read-Copy-Update) lookups:

```bash
echo 1 > /sys/class/net/br0/bridge/fdb_rcu
```

If `__alloc_pages` or `kmem_cache_alloc` dominates, the system is memory-starved, causing excessive page faults. Increase the socket buffer sizes:

```bash
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
```

### 2.3 Queue Depth and Backpressure Analysis

The Linux kernel maintains per-device TX (transmit) queues, which buffer outbound packets when the NIC cannot drain them immediately. Under sustained load, these queues fill up, and the kernel drops packets or applies backpressure to the sender. Inspect queue statistics:

```bash
# Display qdisc (queuing discipline) statistics for the bridge
tc -s qdisc show dev br0

# Display per-port qdisc statistics
tc -s qdisc show dev veth1
```

The `qdisc` output includes `backlog` (current queue depth in bytes/packets), `dropped` (packets discarded due to queue overflow), and `overlimits` (rate limiter hits). A non-zero `dropped` counter indicates the TX queue size (default 1000 packets) is insufficient. Increase it:

```bash
ip link set veth1 txqueuelen 10000
```

For real-time traffic (VoIP, video), replace the default FIFO qdisc with a priority-based scheduler:

```bash
tc qdisc replace dev veth1 root pfifo_fast
```

### 2.4 Measuring Latency Under Load

Throughput alone is insufficient for diagnosing user-facing issues; latency (packet delay) and jitter (delay variation) matter equally. While `iperf3` saturates the bridge, measure ICMP round-trip time (RTT):

```bash
# Terminal 4: Ping during load
ip netns exec perf-lab ping -i 0.2 10.0.0.2 | ts %.s
```

The `ts` utility (from the `moreutils` package) timestamps each line. Under no load, expect RTT < 0.5ms. Under full load, RTT may spike to 5–50ms due to qdisc backlog. Persistent RTT > 100ms suggests packet reordering or TCP retransmissions, visible via:

```bash
ss -ti dst 10.0.0.2
```

The `-t` flag filters TCP sockets, `-i` shows internal TCP state. Look for `retrans` (retransmission count) and `rtt` (smoothed round-trip time). High retransmission rates (> 1%) indicate buffer overrun or silent packet corruption.

### 2.5 Saturation Testing with UDP Floods

TCP's congestion control masks true bridge capacity by throttling the sender. To stress-test the absolute forwarding limit, use UDP floods:

```bash
# Terminal 2: UDP flood with iperf3
ip netns exec perf-lab iperf3 -c 10.0.0.2 -u -b 10G -t 30

# Terminal 3: Monitor drop counters in real-time
watch -n 1 'ip -s link show veth2 | grep -A 4 "RX:"'
```

The `-u` flag switches to UDP, `-b 10G` requests 10 Gbps transmission rate (the sender will transmit at this rate regardless of losses). Compare the RX packet count on `veth2` with the TX count on `veth1`. Packet loss percentage is:

```
Loss% = 100 * (1 - RX_packets / TX_packets)
```

Non-zero loss under UDP flood is expected if the requested rate exceeds NIC capacity. However, loss at rates well below line rate indicates CPU or memory bottlenecks.

### 2.6 eBPF-Based Packet Tracing

For granular visibility into packet drops, attach an eBPF program to the TC (Traffic Control) egress hook of the bridge:

```bash
# Install bpftool if not present
sudo apt-get install -y linux-tools-common linux-tools-generic

# Load a sample eBPF program that counts packets
cat > tc_count.c <<'EOF'
#include <linux/bpf.h>
#include <linux/pkt_cls.h>

SEC("classifier")
int tc_count(struct __sk_buff *skb) {
    return TC_ACT_OK;  // Pass all packets
}

char _license[] SEC("license") = "GPL";
EOF

clang -O2 -target bpf -c tc_count.c -o tc_count.o

# Attach to br0 egress
tc qdisc add dev br0 clsact
tc filter add dev br0 egress bpf direct-action obj tc_count.o sec classifier

# Trace eBPF events
sudo bpftool prog tracelog
```

This minimal program passes all packets but increments an implicit counter accessible via `bpftool prog show`. For production diagnostics, extend the program to log drop reasons (e.g., invalid VLAN, exceeded rate limit) to a BPF map.

### 2.7 Cleanup

```bash
exit
sudo ip netns del perf-lab
```

---

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates real-world failure scenarios—link flaps, port storms, STP reconvergence—and validates automated recovery mechanisms. The skills developed here are critical for on-call engineers responding to live incidents.

### 3.1 Simulating Link Flapping

Link flapping (rapid up/down transitions) destabilizes STP and triggers FDB flushes. We will inject controlled flaps and measure convergence time.

```bash
sudo ip netns add fault-lab
sudo ip netns exec fault-lab bash

# Create a three-bridge topology to simulate a loop
ip link add br1 type bridge stp_state 1
ip link add br2 type bridge stp_state 1
ip link add br3 type bridge stp_state 1

ip link set br1 up
ip link set br2 up
ip link set br3 up

# Create interconnects (three VETH pairs forming a triangle)
ip link add veth12-a type veth peer name veth12-b
ip link add veth23-a type veth peer name veth23-b
ip link add veth31-a type veth peer name veth31-b

ip link set veth12-a master br1
ip link set veth12-b master br2
ip link set veth23-a master br2
ip link set veth23-b master br3
ip link set veth31-a master br3
ip link set veth31-b master br1

for iface in veth12-a veth12-b veth23-a veth23-b veth31-a veth31-b; do
    ip link set $iface up
done
```

At this point, STP elects one bridge as root and blocks one port to break the loop. Identify the blocked port:

```bash
bridge -d link show | grep state
```

Now inject a link flap by bringing down and up a non-blocked port:

```bash
# Assume veth12-a is forwarding
ip link set veth12-a down
sleep 2
ip link set veth12-a up

# Monitor STP reconvergence time
date +%s%3N  # Millisecond timestamp
watch -n 0.5 'bridge -d link show | grep state'
```

Measure the duration until all ports return to `forwarding` or `blocking` (stable state). RSTP (Rapid Spanning Tree) should converge within 6 seconds (3 seconds for proposal/agreement handshake, 3 seconds for TCN propagation). If convergence exceeds 30 seconds, suspect classical STP (802.1D) is enabled instead of RSTP (802.1w). Verify:

```bash
cat /sys/class/net/br1/bridge/stp_state  # Should be 2 (RSTP)
```

### 3.2 Broadcast Storm Injection

A broadcast storm occurs when a loop exists without STP protection, causing frames to circulate indefinitely. We will disable STP temporarily and trigger a storm:

```bash
# Disable STP on all bridges (DANGEROUS: only in isolated namespace)
ip link set br1 type bridge stp_state 0
ip link set br2 type bridge stp_state 0
ip link set br3 type bridge stp_state 0

# Add a temporary host to generate broadcast traffic
ip link add veth-host type veth peer name veth-host-peer
ip link set veth-host master br1
ip link set veth-host up
ip link set veth-host-peer up
ip addr add 192.168.1.1/24 dev veth-host-peer

# Generate ARP broadcast (will loop infinitely)
ping -c 1 -b 192.168.1.255

# Observe exponential packet count growth
watch -n 1 'ip -s link show br1 | grep -A 2 "RX:"'
```

The RX packet count will skyrocket as frames loop. On physical switches, this saturates the management CPU, rendering the device unresponsive. To mitigate, enable storm control (rate limiting of broadcast/multicast):

```bash
# Re-enable STP to stop the storm
ip link set br1 type bridge stp_state 1
ip link set br2 type bridge stp_state 1
ip link set br3 type bridge stp_state 1

# Configure per-port broadcast rate limit (requires TC)
tc qdisc add dev veth12-a root tbf rate 1mbit burst 32kbit latency 400ms
```

The `tbf` (Token Bucket Filter) qdisc limits broadcast traffic to 1 Mbps, dropping excess frames.

### 3.3 FDB Poisoning Attack

An attacker on a switch port can inject frames with spoofed source MACs, polluting the FDB and redirecting traffic. We simulate this and demonstrate detection:

```bash
# Legitimate host
ip link add veth-victim type veth peer name veth-victim-peer
ip link set veth-victim master br1
ip link set veth-victim up
ip link set veth-victim-peer up address 02:00:00:00:00:AA
ip addr add 192.168.1.10/24 dev veth-victim-peer

# Attacker host
ip link add veth-attacker type veth peer name veth-attacker-peer
ip link set veth-attacker master br1
ip link set veth-attacker up
ip link set veth-attacker-peer up

# Attacker sends frames claiming to be the victim's MAC
ip netns exec fault-lab \
    python3 -c "
import socket, struct
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
s.bind(('veth-attacker-peer', 0))
# Ethernet frame: dst=broadcast, src=victim's MAC
frame = b'\xff\xff\xff\xff\xff\xff' + b'\x02\x00\x00\x00\x00\xAA' + b'\x08\x00' + (b'\x00' * 46)
for _ in range(100):
    s.send(frame)
"

# Inspect FDB: victim's MAC now points to attacker's port
bridge fdb show | grep 02:00:00:00:00:AA
```

The FDB now associates the victim's MAC with the attacker's port. Legitimate traffic to the victim is blackholed. Detection relies on monitoring FDB churn rate:

```bash
# Log FDB changes
bridge monitor fdb
```

A sudden spike in FDB updates (hundreds per second) indicates an attack or misconfigured device (e.g., a VM repeatedly changing its MAC).

### 3.4 Port Security and MAC Limiting

Prevent FDB poisoning by enforcing per-port MAC limits:

```bash
# Limit veth-attacker to 1 learned MAC
ip link set veth-attacker type bridge_slave learning_limit 1

# Attempt to learn multiple MACs (attack will fail)
# ... repeat the Python spoofing script ...

# Verify that additional MACs are rejected
bridge fdb show | grep veth-attacker
```

The port will learn only the first MAC; subsequent frames with different source MACs are dropped. Production switches implement this as "port security" with violations triggering SNMP traps or syslog alerts.

### 3.5 Failover and Link Aggregation (LACP)

Link Aggregation Control Protocol (LACP, 802.3ad) bonds multiple physical links into a single logical link for redundancy and increased throughput. We simulate a bond and trigger a failover:

```bash
# Create a bonded interface
ip link add bond0 type bond mode 802.3ad

# Attach two member links
ip link add veth-bond1 type veth peer name veth-bond1-peer
ip link add veth-bond2 type veth peer name veth-bond2-peer

ip link set veth-bond1 master bond0
ip link set veth-bond2 master bond0

ip link set bond0 up
ip link set veth-bond1 up
ip link set veth-bond2 up

# Verify bond status
cat /proc/net/bonding/bond0

# Fail one link
ip link set veth-bond1 down

# Observe failover (traffic should continue on veth-bond2)
cat /proc/net/bonding/bond0 | grep "MII Status"
```

LACP negotiates which links are active using LACPDU (Link Aggregation Control Protocol Data Units) frames. The kernel's bonding driver implements the protocol and performs failover automatically. Production networks require consistent LACP configuration on both ends (switch and server); mismatches cause the bond to flap between active-backup and load-balance modes.

### 3.6 Cleanup

```bash
exit
sudo ip netns del fault-lab
```

---

## Diagnostic Cheat Sheet & Verification Checklist

This section consolidates the essential commands and decision trees for rapid production troubleshooting.

### Quick Reference Commands

```bash
# Inspect bridge configuration
ip link show type bridge
bridge link show

# Display Forwarding Database (MAC table)
bridge fdb show [dev BRIDGE]

# Display VLAN membership
bridge vlan show

# Display STP state
bridge -d link show | grep state
cat /sys/class/net/BRIDGE/bridge/stp_state

# Display per-port statistics
ip -s -s link show INTERFACE
ethtool -S INTERFACE

# Monitor FDB changes in real-time
bridge monitor fdb

# Capture live traffic
tcpdump -i INTERFACE -e -n -v

# Profile CPU usage
perf top -a
perf record -a -g -- sleep 10 && perf report

# Inspect qdisc and queue backlog
tc -s qdisc show dev INTERFACE

# Display socket statistics (TCP state, retransmissions)
ss -tin

# Check kernel ring buffer for errors
dmesg | grep -i "bridge\|netdev\|link"
```

### Troubleshooting Decision Tree

**Symptom: Intermittent connectivity loss**
1. Check FDB aging: `bridge fdb show | grep dynamic`
2. Verify no stale entries: compare FDB against ARP table (`ip neigh show`)
3. Inspect STP topology changes: `cat /sys/class/net/br0/bridge/topology_change`
4. Capture BPDU frames: `tcpdump -i INTERFACE ether proto 0x0042`

**Symptom: High latency or packet loss**
1. Check drop counters: `ip -s link show | grep -i drop`
2. Inspect qdisc backlog: `tc -s qdisc show`
3. Profile CPU: `perf top` (look for `spin_lock`, `softirq`)
4. Verify NIC ring buffer size: `ethtool -g INTERFACE`

**Symptom: VLAN isolation failure**
1. Verify VLAN filtering enabled: `ip -d link show br0 | grep vlan_filtering`
2. Check port VLAN membership: `bridge vlan show`
3. Capture frames to verify 802.1Q tags: `tcpdump -e -i INTERFACE vlan`
4. Confirm no L3 routing bypassing the bridge: `ip route show`

**Symptom: STP not converging**
1. Verify RSTP enabled: `cat /sys/class/net/br0/bridge/stp_state` (expect `2`)
2. Check bridge priority: `cat /sys/class/net/br0/bridge/priority`
3. Inspect port roles: `bridge -d link show | grep -E "state|role"`
4. Capture BPDU frames to detect root conflicts: `tcpdump -i INTERFACE ether proto 0x0042 -v`

**Symptom: Bridge consuming excessive CPU**
1. Profile with `perf record -a -g`
2. Check for FDB lock contention: look for `_raw_spin_lock` in `perf report`
3. Enable RCU FDB lookups: `echo 1 > /sys/class/net/br0/bridge/fdb_rcu`
4. Offload to hardware: verify SR-IOV or hardware bridge offload support (`ethtool -k INTERFACE | grep hw-tc-offload`)

### Production Health Checks

Embed these checks in monitoring systems (Prometheus, Nagios):

```bash
#!/bin/bash
# bridge-health-check.sh

BRIDGE=$1

# Check bridge is up
ip link show $BRIDGE | grep -q "state UP" || exit 1

# Check no excessive drops (> 0.1%)
RX=$(ip -s link show $BRIDGE | awk '/RX:/{getline; print $1}')
RX_DROP=$(ip -s link show $BRIDGE | awk '/RX:/{getline; getline; print $2}')
LOSS=$(echo "scale=2; $RX_DROP * 100 / $RX" | bc)
(( $(echo "$LOSS > 0.1" | bc -l) )) && exit 1

# Check STP convergence (no ports in listening/learning)
bridge -d link show | grep -qE "state (listening|learning)" && exit 1

# Check FDB size within bounds (< 1000 entries)
FDB_SIZE=$(bridge fdb show | wc -l)
[ $FDB_SIZE -gt 1000 ] && exit 1

exit 0
```

Run via cron every minute: `* * * * * /usr/local/bin/bridge-health-check.sh br0 || logger -t bridge-health CRITICAL`

### Advanced: eBPF-Based Continuous Monitoring

For zero-overhead visibility, deploy an eBPF program that tracks per-port packet rates and drops, exporting metrics via BPF maps:

```c
// bridge_monitor.bpf.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <linux/if_ether.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key, __u32);    // ifindex
    __type(value, __u64);  // packet count
} port_stats SEC(".maps");

SEC("xdp")
int xdp_port_monitor(struct xdp_md *ctx) {
    __u32 ifindex = ctx->ingress_ifindex;
    __u64 *count = bpf_map_lookup_elem(&port_stats, &ifindex);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        __u64 init = 1;
        bpf_map_update_elem(&port_stats, &ifindex, &init, BPF_ANY);
    }
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

Compile and attach to all bridge ports:

```bash
clang -O2 -target bpf -c bridge_monitor.bpf.c -o bridge_monitor.bpf.o
for port in veth1 veth2 veth3 veth4; do
    ip link set dev $port xdp obj bridge_monitor.bpf.o sec xdp
done
```

Read metrics from userspace via `bpftool map dump` or a custom exporter using `libbpf`.

### Final Verification Checklist

Before declaring a switch "production-ready," validate:

- [ ] All expected ports are in `forwarding` state
- [ ] FDB entries match the physical topology (no stale MACs)
- [ ] VLAN isolation enforced (cross-VLAN ping fails)
- [ ] STP root bridge is the intended device
- [ ] Per-port drop counters are zero under normal load
- [ ] Throughput meets SLA (e.g., 9+ Gbps for 10GbE)
- [ ] Latency < 1ms under 50% load
- [ ] Failover completes within 6 seconds (RSTP)
- [ ] No BPDU storms (< 10 BPDUs/sec per port)
- [ ] Logging and SNMP traps operational

By mastering these exercises, you have internalized the operational model of network switches—from the abstract state machines of STP and VLAN filtering to the concrete implementation in Linux kernel data structures. The techniques demonstrated here generalize to physical switches accessed via console or API, requiring only syntactic translation (e.g., `show mac address-table` in Cisco IOS instead of `bridge fdb show`). Armed with this foundation, you can confidently diagnose production incidents, optimize forwarding pipelines, and design resilient network topologies.
