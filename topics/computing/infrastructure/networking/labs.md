# Operational Verification Labs: Networking Internals

## Objective & Environment Setup

### Objective
This operational lab verifies the core mechanisms of the Linux and BSD network stack. You will inspect socket buffers, trace packet traversal through kernel routing subsystems, profile interface queue drops, and diagnose path MTU and congestion window failures using standard networking diagnostic tools (`iproute2`, `ss`, `tcpdump`, `ethtool`, and `tc`).

### Required Tooling
Ensure standard networking diagnostic utilities are installed:
- `iproute2` (`ip`, `ss`, `bridge`)
- `tcpdump` / `tshark`
- `ethtool`
- `iperf3` / `curl`

---

## Exercise 1: Socket Buffer Inspection & Connection State Diagnostics

Inspect TCP socket buffer allocations, receive/send queues, and round-trip time estimates for active connections.

### 1.1 Detailed Socket Memory & Flow Inspection
Inspect socket send/receive buffer sizes, TCP congestion window (`cwnd`), and unacknowledged bytes using `ss`:

```bash
# Query active TCP streams with internal TCP info (-i), timer state (-o), and memory metrics (-m)
ss -tipm state established
```

Expected output includes metrics such as:
- `skmem`: Socket memory buffers (`rmem_alloc`, `rcv_buf`, `wmem_alloc`, `snd_buf`).
- `cwnd`: Congestion window size in MSS units.
- `rtt`: Smoothed round-trip time and variance (`rtt:24.5/1.2`).

### 1.2 Network Interface Queue & Ring Buffer Profiling
Examine hardware and software ring buffer capacities and frame drops:

```bash
# Query interface statistics and dropped packets
ip -s link show dev eth0

# Query Ethernet driver ring buffer descriptors (TX/RX queues)
ethtool -g eth0

# Inspect interface hardware drop and FIFO overrun counters
ethtool -S eth0 | grep -E "drop|error|miss"
```

---

## Exercise 2: Path MTU Discovery & Congestion Dynamics

Diagnose MTU mismatches, path fragmentation boundaries, and throughput bottlenecks under artificial congestion.

### 2.1 Path MTU Fragmentation Boundary Testing
Determine the exact Path MTU to a target endpoint without permitting packet fragmentation:

```bash
# Probe destination with Don't Fragment (DF) bit set across packet size boundaries
ping -c 2 -M do -s 1472 1.1.1.1
ping -c 2 -M do -s 1473 1.1.1.1
```

If packet size exceeds MTU, verify receipt of ICMP Type 3, Code 4 (`Fragmentation Needed and DF set`):
```bash
tcpdump -nn -i any "icmp and icmp[0] == 3"
```

### 2.2 TCP Buffer Saturation & Flow Control
Simulate bandwidth saturation using `iperf3` while monitoring TCP window scale factors and send queue backpressure:

```bash
# In terminal 1: Monitor socket buffer backpressure
watch -n 0.5 'ss -t -i "( sport = :5201 or dport = :5201 )"'

# In terminal 2: Execute high-throughput transfer
iperf3 -c 127.0.0.1 -t 10 -P 4
```

---

## Exercise 3: Queueing Discipline (tc) Fault Injection & Drop Verification

Inject controlled packet loss, latency jitter, and bandwidth limits to observe TCP rate-reduction and fast-retransmit behavior.

### 3.1 Network Delay & Packet Loss Injection
Add 100ms artificial round-trip latency and 5% packet loss using Linux `netem`:

```bash
# Attach netem queueing discipline to loopback or test veth interface
sudo tc qdisc add dev lo root netem delay 100ms loss 5%

# Verify active queueing discipline configuration
tc qdisc show dev lo
```

### 3.2 Capture Duplicate ACKs & Fast Retransmission
Capture and analyze TCP retransmission events provoked by the injected packet loss:

```bash
# Capture duplicate ACKs and fast-retransmit frames
tcpdump -nn -i lo -c 50 "tcp[tcpflags] & (tcp-ack) != 0"
```

### 3.3 Recovery & Queue Cleanup
Restore default interface queueing discipline:

```bash
# Remove injected netem qdisc
sudo tc qdisc del dev lo root
```

---

## Networking Diagnostic Cheat Sheet

| Subsystem | Command | Diagnostic Purpose |
| :--- | :--- | :--- |
| **Socket Info** | `ss -tipm state established` | Inspect `cwnd`, `rtt`, and socket buffer memory |
| **Interface Drops** | `ip -s link show dev <iface>` | Measure RX/TX byte counters and packet drops |
| **Ring Buffers** | `ethtool -g <iface>` | Query NIC RX/TX hardware ring capacities |
| **HW Counters** | `ethtool -S <iface>` | Inspect low-level driver and MAC overrun errors |
| **Packet Trace** | `tcpdump -nn -i <iface> -vvv` | Raw protocol dissection and flag inspection |
| **Route Cache** | `ip route show table cache` | Verify Path MTU cache entries and next-hops |
| **Fault Injection** | `tc qdisc add dev <iface> root netem` | Simulate latency, jitter, and packet loss |
