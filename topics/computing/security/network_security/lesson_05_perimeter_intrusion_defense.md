# Lesson 5: Perimeter Defense, Intrusion Detection, Prevention Systems

## 1. First-Principles Intuition & Invariants

The network perimeter represents the logical and physical boundary where an organization's controlled infrastructure terminates and the untrusted internet begins. This boundary is not a single point but a collection of enforcement planes where traffic undergoes progressive scrutiny before reaching internal hosts. Understanding perimeter defense requires decomposing network packets into layers of the OSI model and recognizing that each layer offers distinct opportunities for inspection, filtering, and policy enforcement.

At the lowest level of perimeter defense lies packet filtering, a stateless mechanism that examines individual packets in isolation. A packet filter evaluates each datagram against a rule set that specifies source and destination IP addresses, protocol numbers, and port values. The decision logic is purely deterministic: a packet either matches a rule and is permitted or denied, or it falls through to a default policy. This approach is computationally efficient because it requires no memory of prior packets, but it suffers from a fundamental weakness. Without connection state, a packet filter cannot distinguish between a legitimate SYN-ACK response to an internal client's connection request and a spoofed SYN-ACK from an attacker attempting to inject packets into a non-existent connection. The filter sees only a single frame and must decide based on header fields alone.

Stateful inspection evolved to address this limitation by maintaining a connection state table. When a firewall operating in stateful mode observes a TCP SYN packet originating from an internal host destined for an external server, it creates an entry in its state table recording the source IP, source port, destination IP, destination port, and the current TCP state (SYN_SENT). When the SYN-ACK returns, the firewall consults this table, verifies that the response corresponds to an established connection attempt, and permits the packet while updating the state to SYN_RECEIVED. This mechanism provides session awareness, allowing the firewall to enforce policies that reference connection context rather than just instantaneous header values. The state table becomes a shared memory structure that tracks the lifecycle of every active connection, and the firewall performs lookups on this table for every packet, trading computational overhead for security precision.

Application layer firewalls extend this inspection depth into the payload itself. Rather than stopping at transport layer headers, an application layer gateway (ALG) or next-generation firewall (NGFW) reassembles TCP streams, decodes application protocols, and applies policies based on HTTP methods, SQL query patterns, or TLS Server Name Indication (SNI) fields. This requires maintaining per-connection buffers to reconstruct fragmented or out-of-order segments, protocol parsers to interpret application semantics, and signature databases to detect malicious payloads. The computational cost escalates dramatically because the firewall must now perform deep packet inspection (DPI), effectively operating as a transparent proxy that terminates and re-originates connections on both sides.

Intrusion detection systems (IDS) and intrusion prevention systems (IPS) sit adjacent to or inline with firewalls, but their operational model differs fundamentally. Where a firewall enforces explicit policies (permit or deny based on rules), an IDS attempts to detect malicious activity by comparing observed traffic against known attack signatures or statistical baselines. Signature-based detection relies on pattern matching: the IDS maintains a database of byte sequences or protocol anomalies associated with known exploits, such as the NOP sled preceding shellcode in a buffer overflow or the specific SQL injection string used by a widespread worm. When a packet or reassembled stream matches a signature, the IDS generates an alert.

Anomaly-based detection inverts this logic by modeling normal behavior and flagging deviations. This approach typically involves training a statistical model on baseline traffic to learn expected distributions of packet sizes, protocol ratios, connection rates, and inter-arrival times. During operation, the IDS compares observed metrics against this baseline, triggering alerts when deviations exceed a threshold. The advantage is detecting zero-day attacks that lack signatures; the disadvantage is high false positive rates because legitimate traffic can exhibit statistical outliers. A software update rollout that suddenly quadruples HTTP request rates or a batch job that saturates a previously idle network link can both trigger anomaly alerts despite being benign.

The distinction between IDS and IPS is architectural placement and response capability. An IDS operates out-of-band, receiving a mirrored copy of network traffic from a SPAN port or network tap. It observes passively and can only generate alerts for human analysis or SIEM correlation. An IPS operates inline, positioned directly in the data path such that all traffic must traverse it. This placement grants the IPS the ability to drop malicious packets in real time, effectively blocking attacks before they reach their targets. The tradeoff is failure mode: an IDS failure affects only visibility, while an IPS failure can segment the network entirely if it crashes or becomes a bottleneck.

Network access control (NAC) enforces policies at the host admission layer, before a device is granted network connectivity. A NAC system performs authentication (verifying device identity via 802.1X, MAC address, or certificate), authorization (checking compliance with corporate policy such as antivirus status or patch level), and accounting (logging connection events). Once authenticated, the NAC assigns the device to a VLAN or applies access control lists (ACLs) that constrain its reachability. This creates a dynamic perimeter that adapts to device posture rather than relying solely on static network topology.

The demilitarized zone (DMZ) is a network segment that sits logically between the internal trusted network and the external untrusted internet. Public-facing services such as web servers, mail relays, and DNS resolvers reside in the DMZ, where they are accessible from the internet but isolated from internal hosts. A dual-firewall architecture enforces this isolation: an external firewall filters internet traffic bound for the DMZ, permitting only specific service ports (TCP 80/443 for HTTP/S, TCP 25 for SMTP, UDP 53 for DNS), while an internal firewall restricts DMZ hosts from initiating connections into the internal network. This segmentation limits the blast radius of a compromise; an attacker who gains control of a DMZ web server cannot directly pivot to internal databases or domain controllers.

Proxy systems introduce an intermediary that terminates and re-originates connections, providing a choke point for inspection and policy enforcement. A forward proxy mediates client requests to external servers, commonly used for content filtering, caching, and anonymization. A reverse proxy sits in front of backend servers, accepting client connections and forwarding requests to internal services while hiding the internal topology. In both cases, the proxy operates at the application layer, parsing protocols and making routing decisions based on HTTP headers, TLS SNI, or even request body content. This enables sophisticated policies such as URL whitelisting, malware scanning of downloaded files, or rate limiting per user session.

The core invariant across all perimeter defenses is the principle of layered security. No single mechanism is sufficient; packet filters cannot detect application layer exploits, stateful firewalls cannot prevent malware in encrypted streams, and IDS cannot block attacks they merely observe. Effective perimeter defense requires orchestrating multiple enforcement points, each operating at different protocol layers and with different inspection depths, such that an attacker must defeat multiple independent mechanisms to reach critical assets.

## 2. Core Architecture & Mechanics

### Packet Filtering Rule Evaluation

Packet filtering operates on a linear rule set where each rule specifies match criteria and an action. The firewall evaluates rules in order, and the first match determines the packet's fate. A typical rule contains five-tuple match fields (source IP, destination IP, protocol, source port, destination port) and an action (accept, drop, or reject).

```
Rule 1: src=192.168.1.0/24 dst=any proto=tcp dport=443 action=accept
Rule 2: src=192.168.1.0/24 dst=any proto=tcp dport=80  action=accept
Rule 3: src=192.168.1.0/24 dst=any proto=any dport=any action=drop
Rule 4: src=any dst=any proto=any dport=any action=drop
```

This rule set permits internal hosts (192.168.1.0/24) to initiate HTTPS and HTTP connections to any destination but drops all other traffic from that subnet. The final rule implements default-deny for all other sources. The ordering is critical: if Rule 3 preceded Rules 1 and 2, all internal traffic would be dropped before specific permits could be evaluated.

The evaluation mechanism involves hash table lookups or decision tree traversal. For small rule sets, linear scanning is acceptable, but production firewalls handling tens of thousands of rules employ optimized data structures. A common approach is tuple space search, where rules are organized into hash tables keyed by distinct combinations of field wildcards. A rule matching all five fields exactly hashes into one table, while a rule matching only destination port hashes into a separate table for port-only lookups. The firewall probes each table in order of decreasing specificity, terminating on the first match.

### Stateful Connection Tracking

Stateful firewalls maintain a connection tracking table, a hash map keyed by the five-tuple of active connections. Each entry contains the current TCP state (SYN_SENT, ESTABLISHED, FIN_WAIT, etc.), sequence numbers, and timestamps. The state machine transitions mirror the TCP state diagram:

```
State Machine Transitions:
CLIENT ---SYN---> FIREWALL ---SYN---> SERVER
  [Create entry: state=SYN_SENT, seq_init=X]

CLIENT <--SYN/ACK-- FIREWALL <--SYN/ACK-- SERVER
  [Update entry: state=SYN_RECEIVED, seq_reply=Y]

CLIENT ---ACK---> FIREWALL ---ACK---> SERVER
  [Update entry: state=ESTABLISHED]

CLIENT ---data---> FIREWALL ---data---> SERVER
  [Validate: seq in window, state=ESTABLISHED]

CLIENT ---FIN---> FIREWALL ---FIN---> SERVER
  [Update entry: state=FIN_WAIT]
```

For UDP, which lacks connection state, the firewall uses a timeout-based pseudo-state. When an internal host sends a UDP packet to an external server, the firewall creates an entry allowing return traffic from that server IP/port pair for a limited duration (typically 30 seconds). This permits request-response protocols like DNS while preventing unsolicited inbound UDP traffic.

The connection tracking table is sized to handle peak concurrent connections. A firewall serving 10,000 users with an average of 50 concurrent connections per user requires a table with 500,000 entries. Each entry consumes approximately 200 bytes (five-tuple, state, sequence numbers, timestamps, pointers), resulting in 100 MB of memory. Hash collisions are resolved via chaining, and entries are aged out based on inactivity timers to prevent exhaustion attacks where an adversary floods the firewall with SYN packets to fill the state table.

### Application Layer Gateway Operation

An application layer gateway (ALG) operates as a transparent proxy, terminating the client TCP connection, inspecting and potentially modifying the application payload, then re-originating a connection to the destination server. For HTTP, this involves:

1. **TCP Handshake Termination**: The firewall completes the three-way handshake with the client, allocating a socket and buffer for the connection.

2. **Stream Reassembly**: As the client sends data, the firewall buffers TCP segments, handling retransmissions and reordering to reconstruct the byte stream.

3. **Protocol Parsing**: The firewall parses HTTP headers, extracting method, URI, Host field, and any Content-Type or Content-Length headers. For TLS, it performs TLS interception (commonly called SSL inspection), presenting a firewall-generated certificate to the client and establishing a separate TLS session to the server.

4. **Policy Evaluation**: The firewall matches parsed fields against policies. For example, block all POST requests to URIs containing `/admin/`, or deny responses with `Content-Type: application/x-executable`.

5. **Forwarding Decision**: If the request is permitted, the firewall initiates a connection to the destination server and forwards the buffered data. If denied, it sends an HTTP 403 response to the client and closes the connection.

This architecture introduces significant latency because the firewall cannot forward data until it has parsed enough of the stream to make a policy decision. For large POST requests, the firewall may need to buffer the entire request body before forwarding, increasing memory consumption and stalling the client.

### Intrusion Detection Signature Matching

Signature-based IDS relies on pattern matching against a rule database. A signature specifies protocol filters, packet content patterns, and metadata. A Snort rule for detecting SQL injection might appear as:

```
alert tcp any any -> any 80 (msg:"SQL Injection Attempt"; 
  flow:to_server,established; 
  content:"UNION"; nocase; 
  content:"SELECT"; nocase; distance:0; 
  pcre:"/(\%27)|(\')|(\-\-)|(\%23)|(#)/i"; 
  classtype:web-application-attack; 
  sid:1000001; rev:1;)
```

This rule triggers on TCP packets destined for port 80 in an established connection, containing the case-insensitive strings "UNION" and "SELECT" in proximity, followed by a PCRE regex matching common SQL injection metacharacters.

The IDS processes packets through a multi-stage pipeline:

1. **Packet Capture**: Libpcap or AF_PACKET captures raw frames from the network interface.

2. **Protocol Decoding**: The IDS decodes Ethernet, IP, TCP/UDP headers, extracting five-tuple and payload offset.

3. **Stream Reassembly**: For TCP, the IDS maintains per-connection buffers to reconstruct streams, handling overlapping fragments and retransmissions.

4. **Signature Matching**: The IDS scans the reassembled stream using a multi-pattern matching algorithm such as Aho-Corasick, which constructs a finite automaton from all signature patterns and scans the input in a single pass.

5. **Alert Generation**: On a match, the IDS logs the event with timestamp, five-tuple, matched signature ID, and a copy of the triggering packet.

The performance bottleneck is the pattern matching stage. A signature database with 50,000 rules and an IDS processing 10 Gbps of traffic must scan approximately 1.25 GB/s of payload data against all patterns. Hardware acceleration using FPGA-based content addressable memory (CAM) or ASIC regex engines is common in high-throughput deployments.

### Anomaly Detection Statistical Modeling

Anomaly-based IDS constructs a baseline profile during a training phase, then compares operational metrics against this profile. A simple approach models packet size distribution using a Gaussian mixture model. During training, the IDS observes packet sizes over a representative period and fits the distribution:

```
P(size) = Σ w_k * N(μ_k, σ_k²)
```

where each Gaussian component captures a mode in the distribution (e.g., TCP ACKs at 54 bytes, full MTU packets at 1500 bytes, HTTP responses at various sizes).

During operation, each packet size is evaluated against this model. If the log-likelihood falls below a threshold, indicating the size is unlikely under the learned distribution, an anomaly alert is generated. More sophisticated models incorporate temporal features such as inter-arrival times, connection rates, or entropy of destination IP addresses.

The challenge is adaptive attackers who carefully craft traffic to match the baseline. An exfiltration attack that slowly leaks data in packet sizes consistent with normal web browsing may evade anomaly detection. Conversely, legitimate network changes such as deploying a new application or a sudden spike in user activity can trigger floods of false positives.

### Network Access Control Enforcement

NAC systems integrate with the network infrastructure to enforce admission policies. A typical 802.1X deployment involves:

1. **Supplicant**: Client software (Windows, Linux, macOS built-in 802.1X client) that authenticates using EAP (Extensible Authentication Protocol).

2. **Authenticator**: Network switch or wireless access point that blocks traffic until the client is authenticated.

3. **Authentication Server**: RADIUS server that validates credentials against LDAP, Active Directory, or certificate store.

When a device connects to the network, the switch port enters an unauthorized state, permitting only EAPOL (EAP over LAN) frames. The client sends an EAP-Start, initiating an authentication exchange. The switch relays EAP packets between the client and RADIUS server. Upon successful authentication, the RADIUS server returns an Access-Accept message containing VLAN assignment and ACL attributes. The switch then moves the port to an authorized state, applying the specified VLAN tag and ACL to the client's traffic.

For clients failing authentication or lacking 802.1X support, the NAC system can assign them to a quarantine VLAN with restricted access, typically allowing only remediation resources such as antivirus update servers or help desk portals.

### DMZ and Dual-Firewall Topology

A standard DMZ architecture employs two firewalls creating three security zones:

```
[Internet] <---> [Firewall 1] <---> [DMZ] <---> [Firewall 2] <---> [Internal LAN]
```

Firewall 1 rules permit inbound traffic to DMZ services:

```
allow tcp any -> dmz_subnet port 80,443
allow tcp any -> dmz_subnet port 25 (mail relay)
allow udp any -> dmz_subnet port 53 (DNS)
deny all else
```

Firewall 2 rules restrict DMZ-to-internal communication:

```
allow tcp dmz_web_server -> internal_db_server port 3306 (MySQL)
deny tcp dmz_subnet -> internal_lan any
deny udp dmz_subnet -> internal_lan any
```

This configuration allows the web server in the DMZ to query the database server on a specific port, but prevents the web server from initiating arbitrary connections to internal hosts. If an attacker compromises the web server, they cannot use it as a pivot point to scan or exploit the internal network.

### Proxy System Internal Flow

A forward proxy intercepts client requests through explicit configuration (browser proxy settings) or transparent interception (iptables REDIRECT or policy-based routing). The flow for an HTTP request is:

1. **Client Connection**: Client connects to proxy IP:port (e.g., 192.168.1.100:3128).

2. **Request Parsing**: Proxy receives `GET http://example.com/index.html HTTP/1.1` and parses the URI.

3. **Policy Lookup**: Proxy checks URI against content filter database (URL categories, blacklists, malware URL feeds).

4. **DNS Resolution**: Proxy resolves `example.com` (client does not perform DNS, preventing DNS-based exfiltration).

5. **Server Connection**: Proxy establishes TCP connection to `example.com:80`.

6. **Request Forwarding**: Proxy sends `GET /index.html HTTP/1.1\r\nHost: example.com\r\n...` to the server.

7. **Response Buffering**: Proxy receives response, scans for malware signatures or forbidden content types.

8. **Client Response**: Proxy forwards response to client, optionally caching the object.

For HTTPS, the proxy can operate in two modes:

- **CONNECT Tunneling**: Client sends `CONNECT example.com:443 HTTP/1.1`, and the proxy establishes a TCP tunnel without inspecting the TLS payload.

- **TLS Interception**: Proxy terminates the client TLS session using a dynamically generated certificate signed by a corporate CA installed on client machines, then establishes a separate TLS session to the server. This allows full inspection but requires client trust of the proxy CA.

Reverse proxies operate similarly but accept inbound connections from external clients and forward to internal servers. They provide load balancing by distributing requests across a pool of backend servers, request routing based on HTTP headers or URI paths, and caching to reduce backend load.

## 3. High-Performance Optimization & Failure Modes

### Optimizing Packet Filter Performance

Packet filtering performance scales with rule set size and traffic volume. For a firewall processing 10 Gbps of traffic with an average packet size of 500 bytes, it must evaluate 2.5 million packets per second. With a 10,000-rule policy, naive linear scanning requires 25 billion rule comparisons per second, far exceeding CPU capabilities.

The optimization is rule set compilation into a decision tree or finite automaton. Modern firewalls such as iptables with nftables or pf employ a directed acyclic graph (DAG) representation where each node represents a match condition on a specific field, and edges represent value ranges. A packet traverses the DAG by following edges corresponding to its header values, reaching a leaf node that specifies the action. This reduces worst-case complexity from O(N) to O(log N) or even O(1) with perfect hashing.

Another technique is caching recent decisions. A firewall maintains a hash table of recently seen five-tuples and their policy verdicts. Subsequent packets matching a cached entry bypass full rule evaluation, dramatically accelerating common flows. Cache size is tuned based on the diversity of traffic; environments with millions of unique flows per second (large web properties, CDNs) require large caches, while enterprise firewalls with predictable traffic patterns achieve high hit rates with smaller caches.

Hardware offload using TCAM (Ternary Content Addressable Memory) in switch ASICs enables line-rate filtering at 100 Gbps and beyond. TCAM stores rules in a parallel lookup structure where each rule entry can match exact values, wildcards, or ranges in a single clock cycle. However, TCAM capacity is limited (typically a few thousand to tens of thousands of entries) and power-hungry, so it is reserved for core routers and data center switches rather than general-purpose firewalls.

### Stateful Firewall Connection Table Exhaustion

The connection tracking table is vulnerable to state exhaustion attacks. An attacker floods the firewall with SYN packets from randomized source IPs, each creating a state table entry that consumes memory and waits for a SYN-ACK that will never arrive. The timeout for a SYN_SENT state is typically 60 seconds, so the attacker can fill a 1 million entry table by sending 16,667 SYN packets per second.

Mitigation strategies include SYN cookies, aggressive timeouts, and rate limiting. SYN cookies encode the initial sequence number in a way that allows the firewall to verify the SYN-ACK without storing state. The firewall computes a cryptographic hash of the client IP, port, server IP, port, and a timestamp, then uses this hash as the initial sequence number in the SYN-ACK. If the client responds with an ACK containing the incremented sequence number, the firewall recalculates the hash to verify legitimacy and only then creates a state table entry for the established connection. This trades cryptographic overhead for state table memory.

Aggressive timeouts reduce the duration state entries persist for incomplete connections. Dropping SYN_SENT states after 10 seconds instead of 60 limits the impact of a SYN flood. Rate limiting enforces per-source-IP connection rate thresholds, preventing a single attacker from monopolizing the state table. A firewall might permit at most 100 new connections per second from a given source IP, dropping excess SYN packets.

### Application Layer Gateway Latency and Buffering

Application layer inspection introduces latency because the firewall must buffer enough data to parse protocol semantics before making a forwarding decision. For HTTP, the firewall must buffer at least the headers (typically a few kilobytes) before it can extract the URI and apply URL filtering policies. For large POST requests, the firewall may need to buffer the entire body if the policy requires content scanning (e.g., malware signature matching on uploaded files).

This buffering has memory and latency implications. A firewall handling 10,000 concurrent HTTP connections, each buffering an average of 64 KB, requires 640 MB of memory. If the firewall is CPU-bound and cannot keep up with the rate of incoming data, buffers overflow, forcing the firewall to drop packets and trigger TCP retransmissions, further degrading performance.

Optimization involves selective deep packet inspection. Rather than inspecting every connection, the firewall can use heuristics to identify high-risk flows (e.g., connections to recently registered domains, unusual User-Agent strings, suspicious HTTP methods) and apply DPI only to those flows, fast-pathing the majority of benign traffic. This requires accurate risk scoring to avoid bypassing malicious payloads while minimizing latency for legitimate users.

### IDS Signature Evasion Techniques

Attackers employ evasion techniques to bypass signature-based IDS. Fragmentation involves splitting attack payloads across multiple packets such that no single packet contains the signature pattern. An IDS that scans packets independently will miss the attack. The countermeasure is stream reassembly, where the IDS buffers and reconstructs TCP streams before applying signatures.

Encoding and obfuscation transform attack payloads to evade pattern matching. A SQL injection attack might URL-encode characters (`%27` instead of `'`), use Unicode escapes (`\u0027`), or insert SQL comments to break up keywords (`UN/*comment*/ION SELECT`). IDS signatures must include normalization rules that decode and canonicalize payloads before matching.

Protocol manipulation exploits ambiguities in protocol implementations. An attacker can craft a malformed HTTP request that the IDS interprets differently than the web server. For example, the IDS might parse `GET /normal HTTP/1.1\r\nHost: evil.com\r\n\r\nGET /admin HTTP/1.1\r\n` as a benign request to `/normal`, while the web server, using a more lenient parser, interprets it as a request to `/admin`. This is called an evasion via protocol inconsistency, and the defense requires the IDS to emulate the exact parsing behavior of the protected server.

### Anomaly Detection Baseline Drift

Anomaly detection models degrade over time as the network environment evolves. A baseline trained on Monday's traffic may not accurately represent Friday's traffic after deploying a new application or experiencing a surge in user activity. This baseline drift leads to increased false positives as legitimate new traffic is flagged as anomalous.

The solution is adaptive learning, where the model continuously updates its baseline using a sliding time window. Each day, the model incorporates the most recent 24 hours of data and discards the oldest day, gradually adapting to evolving traffic patterns. However, this introduces a vulnerability: an attacker who slowly ramps up malicious traffic over days can train the model to accept the attack as normal. A sophisticated adversary might exfiltrate data at 100 KB/day initially, incrementing by 10 KB/day each week until the exfiltration is imperceptible against the adapted baseline.

Hybrid approaches combine anomaly detection with signature-based detection. Anomalies trigger elevated scrutiny, where the IDS applies more aggressive signature matching or manual analyst review, rather than automatically blocking. This reduces false positives while preserving the ability to detect novel attacks.

### NAC Circumvention via MAC Spoofing

NAC systems that rely on MAC address authentication are vulnerable to spoofing. An attacker observes the MAC address of an authorized device (via ARP sniffing or passive monitoring), disconnects the legitimate device, then reconfigures their own device to use the spoofed MAC address. The switch port, seeing the authorized MAC, grants full network access.

The defense is 802.1X with certificate-based EAP methods such as EAP-TLS, where authentication is cryptographically bound to a private key stored on the device. An attacker cannot spoof a certificate without compromising the private key, which should be protected by a TPM or hardware security module. Additionally, port security features such as sticky MAC learning (where the switch binds a port to the first MAC address seen and rejects subsequent MACs until the port is administratively reset) limit the window for spoofing.

### DMZ Misconfiguration and Lateral Movement

A common DMZ misconfiguration is overly permissive rules on the internal firewall. If Firewall 2 permits DMZ hosts to initiate any connection to internal_lan, a compromised DMZ web server becomes a full pivot point. An attacker can scan the internal network, exploit vulnerabilities on internal hosts, and exfiltrate data.

The mitigation is principle of least privilege: internal firewall rules should permit only the minimum necessary connections. If the DMZ web server requires database access, permit only TCP connections from the web server IP to the database server IP on port 3306, with no other DMZ-to-internal traffic allowed. Additionally, deploy host-based firewalls on DMZ servers that drop all outbound connections except those explicitly required, preventing an attacker from using a compromised server to probe the internal network.

### Proxy Failure Modes and High Availability

A forward proxy is a single point of failure. If the proxy crashes or becomes overloaded, all client HTTP traffic is blocked. To mitigate this, proxies are deployed in high availability (HA) clusters with load balancing. A hardware or software load balancer distributes client connections across multiple proxy instances. If one proxy fails, the load balancer detects the failure via health checks (periodic HTTP requests to a status endpoint) and removes the failed instance from the pool.

Session persistence is critical for stateful proxies that cache authentication tokens or maintain per-client state. The load balancer must ensure subsequent requests from the same client are routed to the same proxy instance, typically using source IP hash or cookie-based affinity. Without session persistence, a client might authenticate with proxy A, receive a session token, then have their next request routed to proxy B, which rejects the token because it does not recognize it.

For TLS-intercepting proxies, certificate generation becomes a bottleneck. Each new HTTPS connection requires the proxy to dynamically generate a certificate for the target domain, sign it with the corporate CA key, and cache it for reuse. At high connection rates, the cryptographic overhead of RSA or ECDSA signing can saturate proxy CPUs. The optimization is certificate caching: the proxy generates a certificate for `example.com` once and reuses it for all subsequent connections to that domain. The cache is sized to hold certificates for the most frequently accessed domains, with LRU eviction for less common domains.

### IPS Inline Performance and Bypass Modes

An IPS operating inline must process every packet at line rate without introducing unacceptable latency. For a 10 Gbps link, the IPS has approximately 67 nanoseconds per 500-byte packet to perform signature matching, protocol decoding, and policy evaluation. Meeting this requirement demands highly optimized packet processing pipelines, often leveraging kernel bypass frameworks such as DPDK (Data Plane Development Kit) or hardware acceleration with FPGAs.

When the IPS cannot keep up with traffic volume, it faces a choice: drop packets (reducing throughput and triggering retransmissions) or fail open (bypassing inspection and allowing potentially malicious traffic). Production deployments often implement a fail-open mode with active monitoring, where the IPS bypasses inspection during overload but logs the bypass event and triggers alerts. This preserves connectivity at the cost of temporary security degradation, which is generally preferable to a total outage.

Advanced IPS architectures employ traffic steering, where a switch or router selectively mirrors high-risk flows to the IPS for inspection while fast-pathing low-risk flows. For example, all traffic to newly registered domains, uncommon ports, or flagged source IPs is mirrored to the IPS, while HTTPS to well-known CDNs or internal application traffic bypasses inspection. This reduces IPS load while maintaining coverage of high-risk threats.

### Practical Deployment: Integrating Firewall, IDS, and NAC

A production perimeter defense integrates multiple mechanisms into a cohesive architecture. A typical enterprise deployment might consist of:

- **Edge Router**: Routes traffic between the ISP and the organization, applies initial ACLs to drop obviously malicious traffic (bogon IP addresses, packets with invalid TTL, etc.).

- **External Firewall**: Stateful firewall enforcing policies for inbound and outbound traffic, maintaining connection state table, and performing basic DPI for known protocols.

- **IPS**: Inline between external firewall and DMZ switch, scanning all DMZ-bound traffic with signature and anomaly detection.

- **DMZ Switch**: Layer 2 switch with 802.1X NAC, VLAN segmentation, and port security.

- **Internal Firewall**: Stateful firewall restricting DMZ-to-internal traffic, permitting only specific application flows.

- **IDS**: Out-of-band on internal LAN, receiving mirrored traffic from internal switch, monitoring for insider threats and lateral movement.

- **Forward Proxy**: Mediates all internal-to-internet HTTP/S traffic, enforcing URL filtering, malware scanning, and data loss prevention policies.

This layered architecture ensures that an attacker must defeat multiple independent controls: the external firewall to reach the DMZ, the IPS to avoid detection, the NAC to pivot to internal hosts, the internal firewall to access critical assets, and the IDS to avoid alerting defenders during lateral movement. Each layer also provides telemetry for correlation in a SIEM, enabling detection of multi-stage attacks that no single control would flag in isolation.
