# Lesson 3: TCP Transport Mechanisms

## 1. First-Principles Intuition & Invariants

The Transmission Control Protocol exists to solve a deceptively simple problem: how can two processes on different machines exchange an ordered, reliable stream of bytes over an unreliable packet network? The Internet Protocol beneath TCP offers no guarantees whatsoever. IP datagrams may arrive out of order, duplicated, corrupted, or not at all. Routers drop packets under congestion. Physical links introduce bit errors. Yet applications demand the illusion of a perfect bidirectional pipe, as though writing to a local file descriptor.

TCP achieves this illusion through continuous state synchronization between sender and receiver, treating the network as a stateless substrate over which it imposes a stateful session. Every byte transmitted carries a sequence number derived from an initial randomly chosen 32-bit value, enabling the receiver to detect gaps, duplicates, and reordering. The receiver responds with acknowledgment numbers that inform the sender which bytes have been successfully delivered, creating a feedback loop that drives retransmission of lost data. This acknowledgment mechanism forms the foundation of TCP's reliability contract.

The protocol operates as a distributed state machine with eleven distinct states governing connection establishment, data transfer, and teardown. Both endpoints maintain independent views of this state machine, synchronized through the exchange of segments carrying control flags—SYN for synchronization, ACK for acknowledgment, FIN for graceful closure, RST for abrupt termination. The three-way handshake that opens a connection exchanges initial sequence numbers and negotiates parameters like maximum segment size and window scaling, establishing the invariants that govern the subsequent data transfer phase.

Flow control and congestion control represent orthogonal but complementary mechanisms. Flow control prevents a fast sender from overwhelming a slow receiver by advertising a receive window that bounds the amount of unacknowledged data in flight. This window shrinks as the receiver's buffer fills and grows as the application consumes data, creating a sliding window protocol that adapts to receiver capacity in real time. The sender must respect this advertised window absolutely, never transmitting beyond the receiver's declared buffer space.

Congestion control, by contrast, addresses the shared resource problem inherent in packet-switched networks. Multiple flows compete for finite router buffer space and link bandwidth. Without coordination, senders transmitting at maximum rate would induce catastrophic congestion collapse, where the network carries packets that will ultimately be dropped, wasting capacity on futile work. TCP's congestion control algorithms infer network capacity through implicit signals—packet loss and increasing round-trip times—and adjust transmission rate accordingly. The congestion window maintained by the sender represents the protocol's estimate of safe in-flight data, growing cautiously during stable conditions and contracting aggressively upon detecting loss.

The interaction between flow control and congestion control determines the effective sending rate at any instant. The sender computes the minimum of the advertised receive window and its congestion window, then transmits only that amount of unacknowledged data. This dual constraint ensures neither the receiver nor the network becomes overwhelmed. Modern congestion control algorithms like CUBIC and BBR refine this fundamental mechanism, measuring bandwidth-delay product directly or inferring bottleneck capacity through careful observation of acknowledgment timing.

TCP's reliability guarantee rests on timeout-based retransmission. When the sender transmits a segment, it arms a retransmission timer calibrated to the observed round-trip time. If no acknowledgment arrives before the timer expires, the sender assumes packet loss and retransmits. The retransmission timeout calculation employs exponentially weighted moving averages of measured RTT and variance, balancing responsiveness against spurious retransmission caused by delay variation. Modern implementations also use fast retransmit, inferring loss when three duplicate acknowledgments arrive, signaling that subsequent data reached the receiver but an earlier segment did not.

The protocol distinguishes between the sending application's write operations and the actual transmission of segments. When an application writes data to a TCP socket, the kernel copies that data into a send buffer, returning immediately. The TCP state machine then parcels this byte stream into maximum-segment-sized chunks, respecting the path MTU to avoid IP fragmentation. Nagle's algorithm may coalesce small writes to improve efficiency, delaying transmission until a full segment accumulates or an acknowledgment arrives for prior data. The receiver's acknowledgment strategy similarly balances efficiency and latency, often delaying ACKs to piggyback them on return data or to acknowledge multiple segments at once.

Understanding TCP requires recognizing it as a closed-loop control system. The sender injects data into the network and observes acknowledgments returning, using this feedback to regulate transmission rate, detect packet loss, and measure path characteristics. The fundamental constraint is that the sender cannot directly observe the network interior—router queue depths, competing flows, or link utilization remain hidden. TCP must infer these conditions through endpoint measurements alone, making congestion control inherently heuristic. The algorithms that govern this inference represent decades of research into distributed resource allocation under partial observability.


## 2. Core Architecture & Mechanics

The TCP header encodes the metadata necessary to maintain connection state and implement reliability. Following the IP header, the TCP header spans a minimum of twenty bytes, expandable to sixty bytes with options. The source and destination port numbers form a four-tuple with the IP addresses, uniquely identifying the connection. Sequence and acknowledgment numbers occupy thirty-two bits each, tracking the byte stream in both directions. Nine flag bits control connection state transitions: URG for urgent data, ACK indicating valid acknowledgment number, PSH requesting immediate data delivery, RST forcing connection reset, SYN and FIN for connection establishment and teardown. The window field advertises receive buffer space, while the checksum covers header and data to detect corruption.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |       |C|E|U|A|P|R|S|F|                               |
| Offset| Rsrvd |W|C|R|C|S|S|Y|I|            Window             |
|       |       |R|E|G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options                    |    Padding    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Connection establishment begins when a client sends a SYN segment with its initial sequence number. The server responds with SYN-ACK, carrying both its own initial sequence number and an acknowledgment of the client's sequence number plus one. The client completes the handshake with an ACK, acknowledging the server's sequence number. This three-way exchange synchronizes sequence numbers and transitions both endpoints from CLOSED through LISTEN and SYN-SENT or SYN-RECEIVED to ESTABLISHED state. The initial sequence numbers are randomized for security, preventing blind injection attacks that exploit predictable values.

```
Client                                Server
  |                                     |
  |  SYN seq=x                         |
  |------------------------------------>|
  |                                     |
  |         SYN-ACK seq=y, ack=x+1     |
  |<------------------------------------|
  |                                     |
  |  ACK seq=x+1, ack=y+1              |
  |------------------------------------>|
  |                                     |
  |         ESTABLISHED                 |
```

During data transfer, the sender maintains several key variables. Send.UNA tracks the oldest unacknowledged sequence number, representing data transmitted but not yet confirmed. Send.NXT holds the next sequence number to send. Send.WND stores the receiver's advertised window. The sender may transmit data in the range from Send.UNA to Send.UNA plus the minimum of the congestion window and Send.WND. As acknowledgments arrive, Send.UNA advances, opening the sliding window to permit transmission of additional data.

The receiver mirrors this structure with Recv.NXT indicating the next expected sequence number and Recv.WND representing available buffer space. When a segment arrives with sequence number equal to Recv.NXT, the receiver accepts it, advances Recv.NXT, and may send an acknowledgment. Out-of-order segments must be buffered, since TCP guarantees in-order delivery to the application. The receiver maintains a queue of these future segments, using their presence to generate duplicate acknowledgments that signal gaps to the sender.

Acknowledgments in TCP are cumulative, meaning an acknowledgment number N confirms receipt of all bytes through N minus one. If segments carrying bytes 0-99, 100-199, and 200-299 all arrive successfully, the receiver need only send a single ACK with acknowledgment number 300. This cumulative property simplifies receiver logic and provides robustness against ACK loss—if one acknowledgment is dropped, a subsequent ACK still conveys all prior progress. Selective acknowledgments, negotiated via options, supplement cumulative ACKs by explicitly identifying non-contiguous ranges of received data, enabling more efficient recovery from multiple packet losses.

The retransmission timer calculation employs Karn's algorithm and Jacobson's method for estimating smoothed round-trip time and variance. Each acknowledgment provides an RTT sample, which updates the smoothed RTT (SRTT) and RTT variance (RTTVAR) through exponential weighted moving averages:

```
RTTVAR = (1 - β) × RTTVAR + β × |SRTT - R|
SRTT = (1 - α) × SRTT + α × R
RTO = SRTT + max(G, 4 × RTTVAR)
```

Here R represents the measured round-trip time, α and β are smoothing factors (typically 1/8 and 1/4), and G is the clock granularity. The retransmission timeout RTO combines the smoothed estimate with a variance term scaled by four, providing a safety margin that accommodates delay variation while remaining responsive to changing conditions. When timeout occurs, TCP retransmits the earliest unacknowledged segment and doubles the RTO using exponential backoff, reducing load on a potentially congested network.

Fast retransmit triggers when the sender receives three duplicate acknowledgments, indicating that the receiver has received data beyond a missing segment. This scenario arises when a single packet drops but subsequent packets arrive successfully. Rather than waiting for the retransmission timer to expire, the sender immediately retransmits the implied missing segment. Fast recovery accompanies fast retransmit, adjusting the congestion window to maintain transmission throughput while recovering from loss. The sender temporarily inflates the congestion window by the number of duplicate ACKs received, permitting new data transmission to keep the pipe full during recovery.

Congestion control algorithms orchestrate the growth and contraction of the congestion window (cwnd) through several phases. Slow start begins when a connection opens or after a retransmission timeout, setting cwnd to the initial window (typically ten maximum segments in modern systems). For each acknowledgment received, cwnd grows by one maximum segment, resulting in exponential growth—one segment acknowledged allows two to be sent, two acknowledged allow four, and so forth. This aggressive growth continues until cwnd reaches the slow-start threshold (ssthresh) or packet loss occurs.

Upon reaching ssthresh, TCP transitions to congestion avoidance, where cwnd grows linearly by one maximum segment per round-trip time. This additive increase phase probes for additional available bandwidth conservatively, incrementing cwnd by approximately MSS × MSS / cwnd for each acknowledgment. When packet loss is detected through duplicate ACKs, TCP halves ssthresh, sets cwnd to ssthresh plus three times the maximum segment size (accounting for the three duplicate ACKs), and enters fast recovery. After the lost segment is acknowledged, cwnd returns to ssthresh, resuming congestion avoidance.

CUBIC, the default algorithm in Linux, modifies this additive-increase multiplicative-decrease pattern for high-bandwidth-delay-product networks. CUBIC maintains a cubic function of time since the last congestion event, growing the window aggressively when far from the previous maximum and cautiously as it approaches that point. The window function takes the form:

```
W(t) = C × (t - K)³ + W_max
```

where W_max represents the window size at the last loss event, K is the time required to reach W_max, and C is a scaling constant. This cubic growth provides faster recovery to high throughput while remaining TCP-friendly. When the current window is well below W_max, CUBIC grows rapidly. As the window approaches W_max, growth slows, probing carefully for the true network capacity.

BBR (Bottleneck Bandwidth and Round-trip propagation time) represents a paradigm shift from loss-based to model-based congestion control. Rather than interpreting packet loss as the primary congestion signal, BBR continuously estimates the bottleneck bandwidth and minimum RTT, computing the bandwidth-delay product to determine the optimal in-flight data. BBR cycles through probe phases: startup to find bandwidth, drain to empty queues, probe bandwidth to detect capacity changes, and probe RTT to update minimum delay measurements. By targeting full link utilization without inducing persistent queueing, BBR achieves higher throughput and lower latency than loss-based algorithms, particularly over paths with non-negligible random loss.

Flow control operates through the receiver's advertised window, which appears in every TCP segment header. As the receiving application consumes data from the receive buffer, the receiver sends acknowledgments with an increased window value, permitting the sender to transmit additional data. If the receive buffer fills completely, the receiver advertises a zero window, forcing the sender to halt transmission. The sender then enters persist mode, periodically sending window probe segments to detect when the receiver's window reopens. These probes prevent deadlock if a window update is lost.

Window scaling addresses the limitation of the sixteen-bit window field, which caps the receive window at 65,535 bytes—insufficient for high-bandwidth-delay-product paths where the optimal in-flight data exceeds this value. The window scale option, negotiated during connection establishment, specifies a shift count applied to all subsequent window advertisements. With a scale factor of fourteen, the effective window can reach one gigabyte, accommodating modern high-speed long-distance links.

Connection termination follows a four-segment exchange, as TCP provides full-duplex communication requiring independent shutdown of each direction. When an application closes its end, TCP sends a FIN segment, transitioning to FIN-WAIT-1 state. Upon receiving an acknowledgment, it moves to FIN-WAIT-2, where it can still receive data from the peer. When the peer's FIN arrives, the endpoint acknowledges it and enters TIME-WAIT, remaining there for twice the maximum segment lifetime (typically one to two minutes). This TIME-WAIT period ensures that delayed segments from the old connection expire before the four-tuple is reused, preventing segment confusion across connection instances.

```
Client                                Server
  |                                     |
  |  FIN seq=x                         |
  |------------------------------------>|
  |                                     |
  |         ACK ack=x+1                |
  |<------------------------------------|
  |                                     |
  |         (Server may send more data) |
  |                                     |
  |         FIN seq=y                  |
  |<------------------------------------|
  |                                     |
  |  ACK ack=y+1                       |
  |------------------------------------>|
  |                                     |
  | TIME-WAIT (2×MSL)                  |
```

Abrupt termination via RST segments bypasses the graceful shutdown sequence, immediately destroying connection state. A RST may result from a segment arriving for a non-existent connection, a connection reset by the application, or detection of a half-open connection where one endpoint has restarted and lost state while the peer still considers the connection active.


## 3. High-Performance Optimization & Failure Modes

Modern high-throughput TCP implementations demand careful attention to send and receive buffer sizing. The buffer size must accommodate the bandwidth-delay product of the path to achieve full link utilization. For a connection traversing a ten-gigabit link with one hundred millisecond RTT, the bandwidth-delay product reaches 125 megabytes. If the receive buffer is smaller, the advertised window will constrain throughput below the link capacity regardless of congestion control behavior. Linux exposes these parameters through socket options SO_RCVBUF and SO_SNDBUF, though automatic tuning mechanisms in modern kernels dynamically adjust buffer sizes based on measured path characteristics.

Examining TCP state on a live system reveals the protocol machinery in action. The ss utility (socket statistics) provides detailed per-connection information including state, send and receive queues, congestion window, slow-start threshold, and retransmission metrics:

```
ss -tin 'sport = :80'
```

This command filters for connections with source port 80, displaying extensive internal state. The output includes bytes_acked (cumulative acknowledged bytes), bytes_received, segs_out (segments sent), segs_in (segments received), data_segs_out (segments carrying data), and data_segs_in. The rtt and rttvar fields show the smoothed round-trip time and variance used for retransmission timeout calculation. The cwnd field exposes the current congestion window, while ssthresh reveals the slow-start threshold. Observing these values over time illuminates how the congestion control algorithm responds to network conditions.

For long-lived high-throughput connections, monitoring retransmission behavior identifies path quality issues. The retransmits and retrans field in ss output counts segment retransmissions. A non-zero retransmission rate may indicate congestion, physical link errors, or routing instability. Excessive retransmissions degrade throughput as the congestion window contracts and CPU cycles are wasted on redundant transmissions. Distinguishing between isolated losses and persistent congestion requires observing retransmission patterns over extended periods.

TCP timestamps, negotiated through options during connection establishment, enable more accurate round-trip time measurement and protect against sequence number wraparound in high-speed networks. Each segment carries a timestamp value, which the receiver echoes in acknowledgments. The sender compares the echoed timestamp to its current clock, obtaining an RTT sample for every acknowledged segment rather than requiring a segment-ACK pair without intervening retransmissions. The timestamp field also provides a 32-bit extension to sequence numbers, detecting old duplicates even when sequence numbers wrap.

Kernel tuning parameters govern TCP behavior at multiple layers. The net.ipv4.tcp_congestion_control sysctl selects the congestion control algorithm, with options including cubic, bbr, and reno. The net.ipv4.tcp_slow_start_after_idle parameter controls whether connections idle for more than one RTO should reset their congestion window, trading rapid startup against potential burst-induced congestion. The net.ipv4.tcp_rmem and net.ipv4.tcp_wmem vectors define minimum, default, and maximum receive and send buffer sizes for automatic tuning. The middle value sets the initial buffer size, while the maximum bounds how far automatic tuning will grow the buffer.

Modern servers handling thousands of concurrent connections encounter the TIME-WAIT state accumulation problem. Each closed connection consumes a socket structure in TIME-WAIT for up to two minutes, and the four-tuple cannot be reused during this period. On a busy server closing ten thousand connections per second, TIME-WAIT states could theoretically accumulate to over one million entries. The net.ipv4.tcp_tw_reuse parameter allows reusing TIME-WAIT sockets for outbound connections when timestamps indicate the new connection is unambiguous, mitigating state exhaustion. However, enabling this option requires careful consideration of NAT and timestamp behavior.

SYN flood attacks exploit the three-way handshake by sending a high rate of SYN segments with spoofed source addresses, causing the server to allocate connection state and send SYN-ACK segments that will never be acknowledged. The half-open connections accumulate, exhausting the server's connection table. SYN cookies provide a defense mechanism that avoids allocating state during the handshake. When a SYN arrives, the server encodes connection parameters into the initial sequence number using a cryptographic hash, sends the SYN-ACK, and discards all state. If the ACK returns, the server decodes the sequence number to reconstruct the connection parameters, only then allocating full state. This stateless approach allows handling arbitrary SYN rates, though at the cost of losing TCP options that don't fit in the cookie encoding.

Performance profiling of TCP-intensive applications requires understanding the kernel's TCP fast path and slow path. The fast path handles common-case segments—in-order data arriving on an established connection with no special flags or options—through highly optimized code that minimizes overhead. Segments requiring special processing—out-of-order data, retransmissions, connection state changes—traverse the slow path. Excessive slow-path processing indicates network issues or application behavior that defeats fast-path optimizations. Profiling tools can measure the ratio of fast-path to slow-path segment processing, identifying optimization opportunities.

Zero-copy mechanisms reduce CPU overhead for high-throughput transfers by avoiding memory copies between kernel and user space. The sendfile system call on Linux transfers data directly from a file descriptor to a socket, bypassing user space entirely. The TCP_CORK socket option accumulates data across multiple write calls, sending larger segments and amortizing per-segment overhead. TCP segmentation offload (TSO) delegates segment construction to the network interface card, allowing the kernel to pass large buffers while the NIC handles MTU-sized fragmentation and checksum computation in hardware.

Receiver-side scaling (RSS) and accelerated receive flow steering (ARFS) distribute incoming TCP connections across multiple CPU cores, preventing a single CPU from becoming a bottleneck. Without these mechanisms, all interrupts for a network interface arrive on one core, limiting throughput to that core's packet processing capacity. RSS hashes incoming packet headers to select a receive queue and CPU core, distributing load. ARFS extends this by steering flows to the CPU where the application thread runs, improving cache locality and reducing inter-processor communication.

TCP head-of-line blocking represents a fundamental limitation arising from the protocol's in-order delivery guarantee. When a packet drops, all subsequent data must wait in the receive buffer until the lost segment is retransmitted and delivered, even if that data is independent and could be processed immediately. Applications requiring independent message streams often use multiple TCP connections or migrate to protocols like QUIC that provide multiple streams within a single connection, allowing one stream's packet loss to block only that stream while others proceed.

Path MTU discovery addresses the challenge of fragmentation in modern networks. Routers may drop large IP packets, returning ICMP fragmentation-needed messages, or silently discard them if the don't-fragment bit is set but the packet exceeds the link MTU. TCP performs path MTU discovery by setting the don't-fragment bit and starting with the interface MTU. When an ICMP fragmentation-needed message arrives, TCP reduces its effective MSS, avoiding fragmentation along the path. Black hole detection handles the case where ICMP messages are filtered, using retransmission timeout as a signal to probe smaller packet sizes.

Deployment of TCP in containerized environments introduces additional considerations. Container network namespaces isolate TCP state between containers, but conntrack tables and NAT mappings at the host level become shared resources. High connection rates from many containers can exhaust the conntrack table, causing new connections to fail. Monitoring nf_conntrack_count and nf_conntrack_max reveals this condition. Kernel parameters like net.netfilter.nf_conntrack_max and net.netfilter.nf_conntrack_buckets govern the conntrack table size and hash bucket count, tunable based on expected connection load.

Service mesh deployments proxy TCP connections, introducing additional hops and state management. Each connection from client to service becomes two connections—client to proxy and proxy to server. The end-to-end congestion control loop is broken, as each hop runs independent congestion control. If the proxy's send buffer fills because the downstream connection has limited capacity, the proxy advertises a reduced window to the upstream client, propagating backpressure. Understanding this multi-hop behavior is crucial for diagnosing throughput issues in service mesh architectures.

Kernel bypass techniques like DPDK and io_uring minimize per-packet overhead by batching operations and avoiding system call transitions. DPDK moves the entire network stack to user space, polling the NIC directly via memory-mapped I/O. Applications receive packets into user-space buffers without kernel involvement, achieving line-rate packet processing at the cost of dedicating CPU cores to polling. io_uring provides asynchronous I/O with shared ring buffers between kernel and user space, reducing system call overhead for socket operations while retaining kernel TCP implementation.

TCP connection splicing or TCP offload engines (TOE) move TCP protocol processing to hardware. The NIC maintains TCP state, performs segmentation and reassembly, and handles retransmissions, presenting a clean data stream to the host. While this offloads CPU, it complicates debugging and limits protocol evolution, as hardware cannot be easily updated with new congestion control algorithms or bug fixes. Most modern deployments favor software TCP implementations with hardware acceleration of specific functions like checksum computation and segmentation.

Observing TCP behavior at scale reveals population-level phenomena invisible in single-connection analysis. Connection duration distributions, flow size distributions, and congestion patterns across diverse paths inform infrastructure capacity planning and protocol tuning. Telemetry systems aggregate per-connection metrics—retransmission rates, handshake latencies, congestion window evolution—to detect degrading network paths, misconfigurations, or attack patterns. Automated systems can respond by rerouting traffic, adjusting kernel parameters, or triggering alerts for human investigation.

The reliability and ubiquity of TCP stem from its carefully balanced control loops—acknowledging data to prove delivery, inferring congestion from implicit signals, and adapting transmission rate to available capacity. Understanding these mechanisms at both the algorithmic level and the systems implementation level enables infrastructure engineers to diagnose performance issues, tune deployments for specific workloads, and reason about protocol behavior under failure conditions. TCP remains the foundation of reliable transport on the Internet precisely because its design accommodates heterogeneous paths, diverse application requirements, and evolving network conditions through adaptive closed-loop control.
