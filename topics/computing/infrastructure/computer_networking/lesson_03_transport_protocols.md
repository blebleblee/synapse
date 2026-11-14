# Lesson 3: Transport Protocols

## 1. First-Principles Intuition & Invariants

The network layer delivers packets on a best-effort basis. It makes no promises about whether a datagram arrives, in what order it arrives, or whether it arrives only once. This deliberate minimalism is what makes the Internet scale: routers can drop packets under congestion without bookkeeping, and the protocol stack remains stateless at every hop. The consequence is that any application requiring ordered, lossless, or rate-controlled delivery must recreate those guarantees at a higher layer. That layer is the transport.

Transport protocols occupy OSI Layer 4 and sit precisely at the boundary between the network's unreliable substrate and the application's demand for predictable byte-stream or message semantics. Two protocols dominate this space: the Transmission Control Protocol (TCP) and the User Datagram Protocol (UDP). They are not competitors in the conventional sense. They represent a fundamental design choice about where complexity belongs. TCP internalizes all the machinery needed to transform an unreliable channel into a reliable, ordered, flow-controlled byte stream. UDP exposes the raw channel almost unchanged, leaving every reliability concern to the application. Neither is universally superior; the right choice is determined entirely by the latency-versus-correctness trade-off that the application can tolerate.

Understanding why TCP exists requires understanding what happens when two processes attempt to communicate across a network without it. Suppose a sender transmits data as fast as the application produces it. If the receiver processes data slower than the sender transmits, intermediate router queues fill and begin dropping packets. Lost data means the receiver has gaps in the byte stream. Without ordering information, the receiver cannot even detect gaps unless it tracks sequence numbers, and without an acknowledgment mechanism, the sender has no way to know which data to retransmit. Without a rate-limiting protocol, every retransmission worsens the congestion that caused the loss in the first place, leading to the collapse scenario Jacobson documented in 1988 when the Internet experienced its first congestion collapse on the ARPANET. These are not edge cases; they are the default behavior of an unconstrained sender over a shared network. TCP's design is a direct engineering response to each of these failure modes, instantiated as formal mechanisms: sequence numbers, acknowledgments, flow control windows, and congestion control algorithms.

The core invariant of TCP is that every byte transmitted by the sender is accounted for. Each byte occupies a position in a 32-bit sequence number space, and the sender never transmits a byte further ahead than the receiver's ability to absorb it and the network's ability to carry it. This invariant is maintained jointly by two orthogonal window mechanisms: the receive window, which enforces the receiver's buffer capacity, and the congestion window, which enforces the sender's estimate of the network's capacity. The effective send window at any moment is the minimum of the two. Breaking this invariant in either direction causes harm: exceeding the receive window corrupts the receiver's buffer; exceeding the congestion window contributes to network congestion and packet loss.

UDP's invariant is the inverse: it provides none of these guarantees and makes no pretense of doing so. A UDP datagram is a self-contained message demultiplexed by source and destination port. The protocol adds nothing to IP except that port demultiplexing and an optional checksum. This simplicity is not laziness; it is the correct architecture for applications that need low latency above all else, such as DNS lookups, real-time media streams, or modern QUIC-based transports that implement their own reliability above UDP. When a DNS resolver sends a query and needs an answer within fifty milliseconds, the three-way handshake latency and the retransmission timeout of TCP are unacceptable overhead. The application is better served by sending the UDP query, waiting a short timeout, and retrying if necessary, because the application-level retry logic is simpler than what TCP would do and faster in the common case of no loss.

---

## 2. Core Architecture & Mechanics

### The TCP Segment and Connection State Machine

The TCP header encodes every mechanism the protocol requires. Its most consequential fields for reliability are the 32-bit sequence number, the 32-bit acknowledgment number, the 16-bit receive window, and the control flags (SYN, ACK, FIN, RST, PSH, URG). The sequence number identifies the position in the byte stream of the first data byte in the payload. The acknowledgment number carries the next byte the receiver expects, implicitly acknowledging all bytes below that value. This cumulative acknowledgment design means a single ACK can confirm receipt of a large burst of data, and duplicate ACKs of the same acknowledgment number signal that a specific segment was lost while later segments arrived.

Connection setup requires the three-way handshake because both endpoints must synchronize their initial sequence numbers. The client sends a SYN with its chosen ISN (Initial Sequence Number). The server responds with a SYN-ACK carrying both its own ISN and an acknowledgment of the client's SYN. The client completes the exchange with an ACK. Only after this exchange do both sides have enough state to deliver data. The choice of a random ISN matters for security: a predictable ISN allows an off-path attacker to inject forged segments by guessing the sequence number the receiver expects, the attack that broke early TCP implementations before RFC 1948 mandated randomization.

```
Client                          Server
  |                               |
  |--------- SYN (seq=x) -------->|
  |                               |
  |<--- SYN-ACK (seq=y, ack=x+1)--|
  |                               |
  |--------- ACK (ack=y+1) ------>|
  |                               |
  |====== DATA TRANSFER ==========|
  |                               |
  |--------- FIN (seq=a) -------->|
  |<-------- ACK (ack=a+1) -------|
  |<-------- FIN (seq=b) ---------|
  |--------- ACK (ack=b+1) ------>|
  |                               |
  [TIME_WAIT: 2*MSL seconds]
```

The teardown is a four-way exchange because TCP connections are half-duplex at close: each side independently closes its direction of the stream with a FIN. The TIME_WAIT state on the initiating side lasts 2×MSL (Maximum Segment Lifetime, typically 60 seconds, so TIME_WAIT is 2 minutes) to absorb any delayed segments that might otherwise be misinterpreted by a future connection reusing the same four-tuple.

### Reliability: Sequence Numbers, Retransmission, and Selective Acknowledgment

The core of TCP reliability is Go-Back-N or, more precisely in modern implementations, Selective Repeat combined with Selective Acknowledgment (SACK). Without SACK, cumulative acknowledgments force the sender to retransmit all segments after a lost segment even if later segments arrived safely. With SACK, enabled via the TCP options field during the handshake, the receiver can report precisely which non-contiguous ranges of the byte stream it has buffered. The sender then retransmits only the missing segments rather than the entire window.

SACK blocks are encoded as (left edge, right edge) pairs in the TCP options field, up to four pairs per ACK segment. The kernel maintains a data structure mapping outstanding sequence number ranges to their transmission status so the retransmission logic can identify the exact bytes to resend. This reduces retransmission volume substantially on paths with burst loss, where multiple segments from one congestion window might be lost but segments outside the burst arrived correctly.

Retransmission timing is governed by the Retransmission Timeout (RTO). If a sent segment is not acknowledged within the RTO, TCP assumes it is lost and retransmits. The RTO is computed dynamically from Round Trip Time (RTT) samples using the algorithm from RFC 6298, which maintains a smoothed RTT estimate (SRTT) and a mean deviation (RTTVAR):

```
SRTT  = (1 - α) × SRTT + α × RTTsample     where α = 1/8
RTTVAR = (1 - β) × RTTVAR + β × |SRTT - RTTsample|   where β = 1/4
RTO   = SRTT + 4 × RTTVAR
```

The minimum RTO is 1 second per RFC, though Linux defaults to 200ms in practice. When the RTO fires, TCP retransmits and applies exponential backoff, doubling the RTO with each consecutive timeout up to a platform-defined maximum (typically 120 seconds on Linux). This backoff is not merely a politeness convention; it is essential for network stability. A sender that retransmits aggressively in response to loss caused by congestion compounds the very congestion that caused the loss.

Fast retransmit is the complement to timeout-based retransmission. When the sender receives three duplicate ACKs for the same acknowledgment number, it infers that the segment following the acknowledged data was lost but that later segments arrived (since the receiver is generating ACKs in response to those later arrivals). The sender immediately retransmits the missing segment without waiting for the RTO to expire. Three duplicates is the threshold because two duplicates can be generated by reordering, which is common on paths that use multipath or ECMP routing.

### Flow Control: The Receive Window

Flow control prevents the sender from overwhelming the receiver's buffer. Every ACK carries a 16-bit window field that tells the sender how many bytes of data it may transmit beyond the acknowledgment number. If the receiver's application is slow to consume data from the socket receive buffer, the kernel reduces the advertised window, throttling the sender without any explicit error. When the receiver advertises a window of zero, the sender must stop transmitting data entirely and begin probing the receiver with zero-window probes (single-byte segments) on a timer to detect when the window opens again.

The 16-bit window field caps the receive window at 65,535 bytes, which is catastrophically small for modern high-bandwidth-delay-product paths. A 1 Gbps link with a 100ms RTT has a bandwidth-delay product of 12.5 megabytes; a 65KB window allows only 0.5% of the pipe to be in flight at any time. The Window Scale option (RFC 7323), negotiated during the handshake, shifts the window field left by 0 to 14 bits, extending the effective maximum to 1 gigabyte. Modern operating systems negotiate window scaling automatically, and the socket buffer sizes are tuned by the kernel's autotuning logic based on observed bandwidth.

### Congestion Control: The Mechanics of cwnd

Congestion control is TCP's most architecturally significant mechanism and the one with the most profound implications for infrastructure engineering. The congestion window (`cwnd`) is a sender-side state variable, invisible to the receiver, that limits how many bytes may be in flight in the network simultaneously. The sender's effective window is `min(cwnd, rwnd)` where `rwnd` is the receiver's advertised window. Congestion control algorithms adjust `cwnd` based on signals from the network.

The original Jacobson/Karels algorithm, which all subsequent algorithms build upon, defines three phases. Slow Start begins with `cwnd` equal to the initial congestion window (IW), which RFC 6928 sets at ten segments (10 × MSS, approximately 14,600 bytes). For each ACK received, the sender increases `cwnd` by one MSS, doubling `cwnd` each RTT. This exponential growth continues until `cwnd` reaches the slow start threshold (`ssthresh`). When loss occurs, `ssthresh` is set to half of the current `cwnd`, and `cwnd` is reset to IW.

```
cwnd growth (cwnd in MSS units):

  |             /
  |            /                 Congestion
  |           /                  Avoidance
  |          /                 (linear, +1 MSS/RTT)
  |         /            ......./............
  |        /         ..../
  |       /      ..../
  |      /   ..../     <- ssthresh
  |     /..../
  |    /
  |   /  Slow Start
  |  /   (doubles each RTT)
  | /
  |/
  +------------------------------------------> time
```

Congestion Avoidance activates once `cwnd` exceeds `ssthresh`. The sender grows `cwnd` by one MSS per RTT rather than per ACK, producing linear growth. The combined shape is the sawtooth waveform that characterizes classic TCP: exponential growth, detection of loss, halving, then linear recovery. This sawtooth is not ideal; it means TCP probes for bandwidth by inducing loss, which forces queues to overflow before it backs off.

CUBIC, the default algorithm in Linux since kernel 2.6.19, replaces the linear Congestion Avoidance phase with a cubic function of time since the last congestion event. CUBIC's window growth is independent of RTT, which addresses a critical fairness problem in the original algorithm: on high-BDP paths, an RTT-dependent algorithm grows `cwnd` extremely slowly in Congestion Avoidance, starving long-distance flows in favor of local flows with short RTTs. CUBIC's time-based growth treats all flows equally regardless of their RTT.

BBR (Bottleneck Bandwidth and Round-trip propagation time), developed at Google and available in Linux since 4.9, represents a fundamentally different architecture. Classic algorithms infer congestion from packet loss, which means they deliberately fill queues to the point of overflow. BBR instead models the network path by continuously measuring the maximum bandwidth it has achieved and the minimum RTT it has observed. It computes the optimal `cwnd` and pacing rate directly from the bandwidth-delay product of the path, targeting a queue occupancy near zero. This eliminates the sawtooth and results in dramatically lower latency and higher throughput on paths with shallow buffers, though BBR can behave aggressively against loss-based algorithms sharing the same bottleneck link.

You can observe `cwnd` dynamics directly with `ss` and interpret them against live traffic with `tc`:

```bash
# Watch cwnd and RTT for all ESTABLISHED TCP connections every second
watch -n 1 'ss -tin state established | grep -E "cwnd|rtt"'

# Full socket diagnostics: cwnd, ssthresh, rtt, retransmits, send buffer
ss -tipm state established

# Display per-interface queue discipline and packet statistics
tc -s qdisc show dev eth0

# Show current congestion control algorithm
sysctl net.ipv4.tcp_congestion_control

# Inspect available congestion control modules
sysctl net.ipv4.tcp_available_congestion_control

# Change to BBR (requires fq or fq_codel as the qdisc)
sysctl -w net.ipv4.tcp_congestion_control=bbr
tc qdisc replace dev eth0 root fq
```

### UDP: The Minimal Transport

A UDP datagram adds exactly eight bytes of header to the IP payload: source port (16 bits), destination port (16 bits), length (16 bits), and checksum (16 bits). There is no connection state, no sequence number, no acknowledgment, and no retransmission. The kernel's UDP send path is a nearly direct call from `sendto()` through the socket layer to IP fragmentation and transmission. The receive path is equally direct: the kernel demultiplexes the datagram by destination port, copies it into the socket's receive buffer, and wakes any blocked `recvfrom()`. If the receive buffer is full when a datagram arrives, the kernel silently drops it. No RST, no error, no notification to the sender.

This simplicity makes UDP the foundation for protocols that implement custom reliability semantics. QUIC, defined in RFC 9000, runs over UDP and implements its own stream multiplexing, connection migration, and loss recovery, with TLS 1.3 integrated at the protocol level rather than layered above. QUIC eliminates the head-of-line blocking inherent in TCP, where a single lost segment stalls all bytes behind it in the stream. QUIC's multiplexed streams allow independent loss recovery per stream, so a stalled stream does not delay others. DNS, NTP, and most real-time media protocols use UDP because the latency overhead of connection setup and retransmission is worse than occasional data loss for those applications.

The practical implication for infrastructure architects is that UDP requires explicit socket buffer sizing and monitoring because there is no backpressure mechanism. A slow consumer causes silent drops with no feedback to the producer.

```bash
# Inspect UDP receive buffer drops (RcvbufErrors) and send drops (SndbufErrors)
netstat -szu | grep -i "buffer\|error\|overflow"

# Or via /proc
cat /proc/net/udp

# Tune the system-wide maximum socket receive buffer (bytes)
sysctl -w net.core.rmem_max=67108864
sysctl -w net.core.wmem_max=67108864

# Per-socket buffer sizes (set before bind in application code, or via setsockopt)
# SO_RCVBUF, SO_SNDBUF, SO_RCVBUFFORCE (privileged)
```

---

## 3. High-Performance Optimization & Failure Modes

### Throughput Diagnosis with `ss`, `netstat`, and `tcpdump`

Diagnosing transport-layer performance problems requires separating the receiver bottleneck from the network bottleneck from the application bottleneck. The receiver bottleneck manifests as a shrinking `rwnd` in `ss` output: if the advertised window approaches zero while the application is slow to read, the socket receive buffer is filling. The network bottleneck manifests as growing RTT, frequent retransmissions, or a low `cwnd` relative to the bandwidth-delay product. The application bottleneck manifests as a large send queue (`Send-Q` in `ss`) despite an open window.

```bash
# Comprehensive connection diagnostics: note Send-Q and Recv-Q
ss -tnmp

# Correlate retransmits with specific connections
ss -ti | grep -A1 "retrans"

# Capture a session and analyze with tcpdump; write to pcap for Wireshark analysis
tcpdump -i eth0 -w /tmp/capture.pcap 'tcp port 8080 and host 10.0.1.5'

# Decode TCP flags and sequence numbers from a live capture
tcpdump -i eth0 -nn -S 'tcp port 443' | head -100

# Measure RTT and packet loss on a path
ping -c 100 -i 0.01 10.0.1.5 | tail -2

# Detailed path MTU and hop-by-hop latency
traceroute -n --sport=12345 10.0.1.5
mtr --report --report-cycles 100 10.0.1.5
```

When `ss -ti` reports a low `cwnd` with many retransmissions but normal RTT, the path is experiencing burst loss rather than congestion-induced queuing. This often indicates a misconfigured NIC ring buffer or a faulty cable causing occasional CRC errors that force retransmits. When `cwnd` is healthy but throughput is low, check the socket send buffer: if `Send-Q` is consistently empty, the application is not writing fast enough. If `Send-Q` is saturated, the kernel's send buffer is full, which means either `cwnd` is throttled or the write syscall rate cannot keep the buffer filled.

### Nagle's Algorithm and TCP_NODELAY

Nagle's algorithm, introduced in RFC 896, addresses the small-packet problem. Without it, an interactive application generates a stream of tiny segments, each carrying one or a few bytes of payload but forty bytes of TCP+IP header, wasting bandwidth and contributing to router queue overhead. Nagle's algorithm holds small segments in the send buffer until either the previous segment has been acknowledged or enough data has accumulated to fill a full MSS. This coalescing dramatically improves efficiency for chatty protocols.

The cost is latency. When a request-response protocol sends a small request, Nagle's algorithm holds the final byte of the request in the buffer waiting for an ACK. If the receiver delays ACKs (Delayed ACK, which waits up to 200ms hoping to coalesce ACKs with data), the interaction between Nagle and Delayed ACK can inject up to 200ms of latency per round trip. This interaction has silently degraded performance in thousands of production systems. The fix is to set `TCP_NODELAY` on the socket, which disables Nagle's algorithm:

```c
#include <netinet/tcp.h>
#include <sys/socket.h>

int sock = socket(AF_INET, SOCK_STREAM, 0);

int flag = 1;
if (setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag)) < 0) {
    perror("setsockopt TCP_NODELAY");
    return -1;
}
```

Any latency-sensitive TCP service, including database clients, gRPC, HTTP/1.1 keep-alive connections, and most RPC frameworks, must set `TCP_NODELAY`. The bandwidth overhead from sending more small packets is negligible compared to the latency saved on interactive paths.

### TIME_WAIT Exhaustion and Connection Reuse

Under high connection rates, the TIME_WAIT state can accumulate to tens of thousands of entries in the kernel's connection table. Each TIME_WAIT socket holds a four-tuple for 2×MSL to prevent sequence number collisions with future connections. On servers handling short-lived HTTP/1.0 connections, this is a frequent source of port exhaustion on the client side: the ephemeral port range (typically 32768–60999 on Linux) is consumed by TIME_WAIT sockets faster than they expire.

```bash
# Count sockets by TCP state
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn

# Inspect TIME_WAIT and CLOSE_WAIT counts specifically
ss -tan state time-wait | wc -l
ss -tan state close-wait | wc -l

# Enable TCP_TW_REUSE: allows reuse of TIME_WAIT sockets for new outgoing connections
# (safe with TCP timestamps enabled, which allow disambiguation)
sysctl -w net.ipv4.tcp_tw_reuse=1

# Ensure TCP timestamps are on (required for tw_reuse to be safe)
sysctl net.ipv4.tcp_timestamps

# Expand the ephemeral port range
sysctl -w net.ipv4.ip_local_port_range="10000 65535"
```

`net.ipv4.tcp_tw_recycle` was a faster but unsafe option removed in Linux 4.12 because it broke connections from clients behind NAT, where multiple clients share an IP and their timestamps are not monotonically ordered from the server's perspective. `tcp_tw_reuse` is the safe alternative, applicable only to outbound connections, and it relies on TCP timestamps to verify that the new connection's sequence numbers cannot collide with the old socket's delayed segments.

### Receive-Side Scaling and Interrupt Affinity

At network rates above 10 Gbps, single-queue NIC interrupt handling becomes the throughput bottleneck. All interrupts from a single receive queue land on one CPU, and that CPU becomes saturated processing softirqs while other CPUs sit idle. Receive-Side Scaling (RSS) enables the NIC hardware to hash the four-tuple (source IP, source port, destination IP, destination port) of each incoming packet and distribute packets across multiple hardware receive queues, each mapped to a separate CPU interrupt vector.

```bash
# Check how many RX queues the NIC is using
ethtool -l eth0

# Set the number of combined (TX+RX) queues (requires driver support)
ethtool -L eth0 combined 8

# View the IRQ-to-CPU mapping for NIC interrupts
cat /proc/interrupts | grep eth0

# Pin each NIC IRQ to a specific CPU core (example for IRQ 32)
echo 1 > /proc/irq/32/smp_affinity     # CPU 0 (bitmask)
echo 2 > /proc/irq/33/smp_affinity     # CPU 1
echo 4 > /proc/irq/34/smp_affinity     # CPU 2

# Or use the irqbalance daemon for automatic, power-aware affinity assignment
systemctl enable --now irqbalance

# Inspect NIC ring buffer sizes and check for drops
ethtool -g eth0
ethtool -S eth0 | grep -i "drop\|miss\|error"

# Increase the RX ring buffer to absorb bursts
ethtool -G eth0 rx 4096
```

Receive Buffer Steering (RFS) extends RSS by ensuring that the CPU that receives a packet is the same CPU that runs the application consuming that socket, maximizing L1/L2 cache reuse for socket buffer data. `Generic Receive Offload (GRO)` and `Large Receive Offload (LRO)` aggregate multiple small segments into a single larger buffer before the kernel processes them, reducing per-packet overhead at the cost of a small increase in latency. GRO is software-based and safe; LRO is hardware-based and can break when packets from multiple flows are incorrectly coalesced.

```bash
# View current offload settings
ethtool -k eth0 | grep -E "generic-receive-offload|large-receive-offload|tcp-segmentation-offload"

# Disable LRO if observing connection anomalies (GRO is usually safe to leave on)
ethtool -K eth0 lro off

# Confirm TCP Segmentation Offload (TSO) state; TSO lets the NIC segment large sends
ethtool -K eth0 | grep tcp-segmentation-offload
```

### Buffer Bloat and the AQM Response

Buffer bloat is the pathological interaction between large router buffers and loss-based congestion control. Classic TCP uses packet loss as the signal to back off. Router vendors, trying to minimize loss, deployed enormous FIFO buffers. The result is that queues fill to hundreds of milliseconds of depth before a packet is ever dropped. TCP sees no loss and continues growing `cwnd`. Latency inflates by hundreds of milliseconds while bandwidth stays at the apparent maximum. Real-time applications sharing the link with bulk transfers experience severe jitter.

The solution is Active Queue Management (AQM) at the queuing discipline layer. FQ-CoDel (Fair Queuing Controlled Delay, RFC 8290) implements a target queue delay of five milliseconds. When the minimum delay seen through a queue exceeds this target for more than 100ms, CoDel begins dropping packets. Fair Queuing distributes transmit slots across flows using a stochastic fair queue, preventing a single high-bandwidth flow from monopolizing the queue at the expense of latency-sensitive flows.

```bash
# Replace the default pfifo_fast qdisc with fq_codel on an interface
tc qdisc replace dev eth0 root fq_codel

# Or use fq (fair queuing with pacing, optimal for BBR) instead
tc qdisc replace dev eth0 root fq

# Inspect the qdisc statistics: dropped, overlimit, and delay metrics
tc -s qdisc show dev eth0

# For a WAN-facing interface, set a bandwidth limit and use cake (a modern fq_codel successor)
# cake implements RFC 8033 (PIE) and 802.11e EDCA traffic shaping
tc qdisc replace dev eth0 root cake bandwidth 100mbit
```

BBR paired with the `fq` queuing discipline produces the best throughput and latency characteristics on paths with any non-trivial RTT. The `fq` qdisc is mandatory for BBR because BBR computes a target pacing rate and relies on the qdisc to enforce per-flow pacing; without it, BBR's calculated rates cannot be transmitted smoothly and the latency model breaks down.

### Path MTU Discovery and Fragmentation

The Maximum Transmission Unit is the largest IP packet a link can carry without fragmentation. Ethernet links carry 1500-byte MTUs by default. Jumbo frames extend this to 9000 bytes on links where the entire path supports them. VXLAN and other overlay encapsulations add headers that reduce the effective MTU available to the guest packet (VXLAN adds 50 bytes, reducing the inner MTU to 1450 on a standard 1500-byte path). If the kernel sends a segment sized to the full outer MTU without accounting for overlay overhead, the resulting packet exceeds 1500 bytes, and the first router without jumbo frame support either fragments it or drops it with an ICMP Fragmentation Needed message.

Path MTU Discovery (PMTUD) works by setting the IP Don't Fragment (DF) bit and observing ICMP Type 3 Code 4 (Fragmentation Needed) messages from routers that cannot forward an oversized packet. The kernel reduces the PMTU for the destination and retransmits with a smaller segment. This mechanism fails silently when network operators block ICMP, which is surprisingly common in enterprise and cloud environments. The symptom is a connection that completes the TCP handshake (small SYN and SYN-ACK fit through) but hangs when large data segments are sent.

```bash
# Determine the effective path MTU to a destination
tracepath -n 8.8.8.8

# Send an ICMP probe of a specific size with DF set to test a path's MTU
ping -M do -s 1472 -c 3 10.0.1.5     # 1472 bytes payload + 28 bytes IP+ICMP = 1500

# Check the kernel's cached PMTU for a route
ip route get 10.0.1.5

# For VXLAN overlays, reduce the host interface MTU to avoid fragmentation
ip link set eth0 mtu 1500
ip link set vxlan0 mtu 1450

# Or configure TCP MSS clamping at the iptables level for all forwarded traffic
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --clamp-mss-to-pmtu
```

MSS clamping is a firewall-level workaround that modifies the MSS field in SYN and SYN-ACK segments passing through a router, ensuring that both endpoints negotiate a segment size that fits through the constrained path without fragmentation. It is the standard solution in cloud and overlay environments where end hosts cannot know the effective MTU of the entire forwarding path.

The combined picture of transport protocols for infrastructure engineers is one of layered knobs: congestion control algorithm and qdisc selection set the macroscopic behavior of a path under load, socket buffer sizes and offload configuration determine how efficiently the kernel handles individual connections, and MTU/PMTU settings determine whether large segments traverse the physical and virtual topology without silent failure. Each layer is independently tunable, and production performance problems almost always involve a mismatch between what the protocol assumes about the path and what the path actually provides.
