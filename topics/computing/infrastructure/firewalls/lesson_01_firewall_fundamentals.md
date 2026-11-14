# Lesson 1: Firewall Fundamentals, Access Control Lists, Packet Filtering

## 1. First-Principles Intuition & Invariants

Every network is, at its core, a trust problem. When two machines exchange packets, the receiver is implicitly trusting that the sender is who they claim to be, that the payload is what it appears to be, and that the intent behind the connection is benign. In a closed lab environment, that trust might be warranted. In production, it is suicidal. The firewall exists because trust must be earned through policy, not assumed through proximity.

The word "firewall" borrows from civil engineering: a physical barrier of fire-resistant material built into a structure to contain a blaze within a compartment. The network analogue performs the same function at the boundary between trust zones. It does not eliminate threats from within, nor does it guarantee correctness of the traffic it permits. What it enforces is a declared policy: a set of rules, evaluated against the properties of each packet or flow, that partition traffic into two classes — permitted and denied. The power of this model is not in what it blocks, but in the invariant it establishes: nothing crosses the boundary without explicit authorization, and nothing is implicitly trusted by virtue of arriving.

This is the **default-deny principle**, and it is the most important invariant in firewall design. A default-permit policy says "allow everything we have not explicitly forbidden," which is untenable in practice because the space of harmful traffic is unbounded and largely unpredictable. A default-deny policy inverts this: the space of permitted traffic is explicitly enumerated and bounded by the operator's intent. Everything outside that enumeration is dropped. This shifts the security posture from reactive to declarative: you do not need to predict every attack variant, only to describe the legitimate traffic your infrastructure requires. The residual risk narrows dramatically.

Before we can evaluate policy, however, we need to understand what properties of a packet are available for inspection. At the network layer (IP), a packet carries a source address, a destination address, a protocol identifier (TCP, UDP, ICMP, etc.), a Time-to-Live, and a set of fragmentation fields. At the transport layer (TCP/UDP), it carries source and destination ports, and in the case of TCP, a set of control flags: SYN, ACK, FIN, RST, PSH, URG. These fields are the vocabulary of packet filtering. An Access Control List (ACL) is simply a structured list of predicates over this vocabulary, where each predicate maps to a terminal action: permit or deny.

The fundamental evaluation invariant of an ACL is **first-match termination**. Rules are evaluated in order, and the first rule whose predicate matches the packet governs its fate. The list is not exhaustive by combination — the system does not compute the union of all matching rules. It stops at the first match. This has a profound architectural implication: rule ordering is semantically load-bearing. A broad permit rule placed before a narrow deny rule will shadow the deny rule entirely, and vice versa. Engineers who misunderstand first-match semantics consistently introduce security holes by placing general rules above specific ones. The correct mental model is that an ACL is a decision tree flattened into a linear sequence, and the sequence is the program.

The distinction between **stateless** and **stateful** packet filtering is not merely a performance optimization — it is a fundamental difference in what properties of traffic the firewall can reason about. A stateless filter evaluates each packet in complete isolation. It has no memory of prior packets, no concept of a connection, and no ability to correlate the current packet with past traffic. This is both its strength and its limitation. Because each packet is an independent evaluation, stateless filtering is fast, predictable, and horizontally scalable. It is also structurally incapable of reasoning about connection state, which matters enormously when you consider how TCP works.

TCP is a connection-oriented protocol whose semantics depend entirely on sequence. A SYN packet initiates a handshake. A SYN-ACK continues it. An ACK completes it. Subsequent packets carry the ACK flag because they are part of an established session. A stateless firewall that permits inbound TCP traffic on port 443 must permit all TCP packets on that port, including unsolicited ACK packets crafted to inject data into non-existent sessions, or RST packets designed to tear down legitimate connections. It cannot distinguish between a packet that belongs to an established session and a packet that is a blind TCP injection attempt, because distinguishing them requires memory.

A **stateful firewall** solves this by maintaining a connection tracking table — a hash map keyed by the five-tuple (source IP, destination IP, source port, destination port, protocol) — where each entry records the current state of the connection (SYN_SENT, ESTABLISHED, TIME_WAIT, etc.) and sequence number windows. When a packet arrives, the firewall first consults the connection table. If an entry exists and the packet is consistent with the recorded state, it is permitted without traversing the full ACL. If no entry exists, the ACL is evaluated to determine whether to permit the new connection and create a tracking entry. This model allows the firewall to enforce a critical invariant: inbound TCP traffic is only permitted if it corresponds to a connection that was initiated from the inside (or explicitly permitted from the outside), and the packet is sequentially valid within that connection.

The tradeoff is resource consumption and state exhaustion. Every tracked connection occupies memory. Under SYN flood conditions, an attacker can exhaust the connection table by sending millions of SYN packets that never complete the handshake, causing the firewall to allocate state for each half-open connection until memory is depleted and legitimate connections are denied. This is why stateful firewalls implement SYN cookies and aggressive timeout policies alongside their tracking tables — the state machine must be hardened against adversarial input, not just designed for the happy path.

## 2. Core Architecture & Mechanics

To understand how a software firewall processes packets in a Linux infrastructure environment, it is necessary to trace the path a packet takes from the network interface through the kernel's networking stack. Linux uses `netfilter` as its in-kernel packet filtering framework, and `nftables` (or its predecessor `iptables`) as the userspace rule management interface. The processing pipeline is organized around **hooks** — fixed points in the network stack at which registered functions are called, with the ability to terminate further processing by returning a verdict.

The five canonical netfilter hooks in the IPv4 path are:

```
NF_INET_PRE_ROUTING   → after checksum validation, before routing decision
NF_INET_LOCAL_IN      → packets destined for the local host
NF_INET_FORWARD       → packets being routed through the host
NF_INET_LOCAL_OUT     → packets originating from the local host
NF_INET_POST_ROUTING  → after routing decision, before transmission
```

A packet destined for the local machine traverses PRE_ROUTING, then LOCAL_IN. A packet being forwarded traverses PRE_ROUTING, then FORWARD, then POST_ROUTING. A packet generated by a local process traverses LOCAL_OUT, then POST_ROUTING. This topology determines where rules must be placed to achieve a given effect, and conflating these hook points is a frequent source of misconfiguration: a rule placed in the INPUT chain will never see forwarded traffic, and a rule placed in the FORWARD chain will never see traffic destined for the firewall host itself.

`nftables` organizes rules into tables, chains, and rules, where chains are attached to netfilter hooks with a declared priority. Priority governs the order in which multiple chains attached to the same hook are evaluated — lower numeric priority runs first. This is the data structure behind policy:

```
                   ┌────────────────────────────────────────┐
                   │            nftables Ruleset             │
                   │                                         │
                   │  table inet filter {                    │
                   │    chain input {                        │
                   │      type filter hook input priority 0  │
                   │      policy drop                        │
                   │      ┌──────────────────────────────┐  │
                   │      │  Rule 1: ct state established │  │
                   │      │          accept               │  │
                   │      │  Rule 2: tcp dport 22 accept  │  │
                   │      │  Rule 3: tcp dport 443 accept │  │
                   │      │  Rule 4: (implicit policy)    │  │
                   │      │          drop                 │  │
                   │      └──────────────────────────────┘  │
                   │    }                                     │
                   │  }                                       │
                   └────────────────────────────────────────┘
```

The `policy drop` declaration at the chain level implements default-deny. If a packet reaches the end of the chain without matching any explicit rule, the chain policy governs its fate. This is architecturally cleaner than appending an explicit `drop all` rule at the end, because it makes the default action a property of the chain rather than a rule that could accidentally be reordered or deleted.

Connection tracking in `nftables` is exposed through the `ct` expression, which queries the netfilter conntrack subsystem. `ct state established,related accept` is the idiomatic opening rule in a stateful default-deny input chain: it permits packets belonging to already-established connections or related sub-connections (such as ICMP error messages or FTP data channels) without evaluating the remainder of the ACL, reducing per-packet work for the dominant traffic class. The conntrack table itself lives in kernel memory, managed by `nf_conntrack`, and can be inspected at runtime with `conntrack -L`.

The internal representation of an nftables ruleset in the kernel is a bytecode VM (nf_tables uses its own expression-based VM, distinct from the classic iptables linear rule list). Each rule is compiled into a sequence of register operations and comparisons evaluated against a per-packet scratchpad. This is why nftables performs better than iptables at scale: sets and maps (hash tables and interval trees) replace linear list iteration, reducing ACL lookup complexity from O(N) to O(log N) for interval matches and O(1) for hash lookups on exact values.

For infrastructure engineers working on bare-metal hosts or VM hypervisors, the full stateful default-deny nftables configuration for a production server looks like this:

```nft
#!/usr/sbin/nft -f

flush ruleset

table inet filter {

    set allowed_tcp_dports {
        type inet_service
        elements = { 22, 80, 443 }
    }

    set trusted_mgmt_sources {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/24, 192.168.100.0/28 }
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Accept established/related traffic without full ACL traversal
        ct state established,related accept

        # Drop invalid conntrack entries (broken, out-of-window TCP, etc.)
        ct state invalid drop

        # Accept loopback traffic unconditionally
        iifname "lo" accept

        # Accept ICMP echo-request (ping) for reachability diagnostics
        ip protocol icmp icmp type echo-request limit rate 10/second accept

        # Restrict SSH to management subnets only
        tcp dport 22 ip saddr @trusted_mgmt_sources ct state new accept

        # Accept new connections on declared service ports
        tcp dport @allowed_tcp_dports ct state new accept

        # Log and drop everything else (rate-limited to avoid log flooding)
        limit rate 5/minute log prefix "nft-input-drop: " drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

This configuration encodes several production invariants simultaneously. The `ct state established,related accept` rule at the top exploits connection tracking to fast-path the dominant case (response packets), keeping rule evaluation cost proportional to new connection rate rather than total packet rate. The `ct state invalid drop` rule silently discards packets that the conntrack subsystem has flagged as anomalous — sequences outside the expected window, packets with inconsistent flags, or fragments that do not reassemble correctly. The rate-limited log-and-drop terminal rule provides forensic signal without exhausting disk I/O under flood conditions.

The forward chain with a default-drop policy is correct for a server that is not acting as a router. Any host that is forwarding packets between interfaces — a hypervisor, a Kubernetes node with pod-to-pod routing, or a software-defined gateway — must populate the FORWARD chain with rules governing inter-segment traffic, because packets transiting the host bypass INPUT and OUTPUT entirely.

## 3. High-Performance Optimization & Failure Modes

The most consequential performance optimization in firewall policy is **match locality**: structuring the ACL so that the rules matching the highest-volume traffic classes are evaluated first. For a typical web server, the overwhelming majority of packets belong to established connections. Placing `ct state established,related accept` as the first rule means that most packets hit the first rule and exit the chain immediately, with no further evaluation. The alternative — evaluating port and address matches against established traffic — multiplies CPU overhead proportional to connection throughput for no security benefit.

For infrastructure with large and dynamic ACLs, `nftables` **sets and maps** are the primary scaling mechanism. A linear list of individual ACCEPT rules for 10,000 IP addresses — a common pattern when naively migrating from `iptables` allow-lists — evaluates in O(N) per packet. The equivalent nftables set, implemented internally as a hash table or red-black tree depending on the element type, evaluates in O(1) or O(log N). The practical difference on a 10 Gbps interface is measurable in CPU cycles per packet, which translates directly to sustainable packet rates before the firewall becomes the bottleneck.

```nft
# Dynamically populated blocklist using an nftables set with a timeout
table inet filter {
    set blocklist {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
        gc-interval 10m
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Drop blocked sources before any other processing
        ip saddr @blocklist drop

        ct state established,related accept
        ct state invalid drop
        # ... remaining rules
    }
}
```

The `flags dynamic` annotation permits the kernel to insert entries into this set at runtime — from a userspace daemon via `nft` commands, or from within nftables rules themselves using the `update @set` expression. Combined with `timeout`, entries expire automatically without requiring external cleanup, which is essential for IP reputation lists that change continuously.

The most dangerous failure mode in firewall administration is **policy-replace atomicity**. Operators who reload firewall rules by flushing the existing ruleset and loading a new one introduce a window between the flush and the load where the host is unprotected. Under normal conditions this window is milliseconds; under load or with complex rulesets it can extend to seconds. The correct approach is an atomic replace: `nft -f /etc/nftables.conf` replaces the entire ruleset in a single kernel transaction when the script begins with `flush ruleset`, but `nft -f` applied to a file is atomic at the netlink message level — if any rule fails to load, the entire transaction is rolled back and the previous ruleset remains active.

Verify this behavior before trusting it in production:

```bash
# Validate syntax without applying changes
nft --check -f /etc/nftables.conf

# Apply atomically; rolls back on any error
nft -f /etc/nftables.conf

# Inspect the active ruleset as loaded in the kernel
nft list ruleset

# Verify conntrack table state
conntrack -L --proto tcp | grep ESTABLISHED | wc -l

# Inspect rule hit counters to verify traffic is matching expected rules
nft list ruleset | grep -A2 "packets"
```

A second failure mode is **asymmetric routing** in multi-homed or ECMP environments. The stateful conntrack subsystem assumes that both directions of a flow traverse the same host. If the SYN is tracked on ingress through interface A, but the SYN-ACK returns via interface B on a different host, the conntrack entry for the inbound ACK will not exist and the packet will be classified as `invalid` or `new` rather than `established`. In such environments, either connection tracking must be disabled for the forwarded path (reverting to stateless filtering), or the routing architecture must guarantee flow affinity — typically through consistent hashing on the five-tuple at the load balancer tier.

**Rule shadowing** is a silent correctness failure rather than a performance failure. Consider this fragment:

```nft
chain input {
    type filter hook input priority filter; policy drop;

    ip saddr 0.0.0.0/0 tcp dport 22 accept   # permits SSH from anywhere
    ip saddr @trusted_mgmt_sources tcp dport 22 accept  # never evaluated
}
```

The second rule is dead code. The first rule matches all SSH traffic regardless of source, so the more specific source restriction below it is unreachable. `nftables` does not warn about shadowed rules — it is the operator's responsibility to maintain ordering invariants. The discipline required is to always place more specific rules before more general ones, and to audit rule ordering as a first-class concern in code review for infrastructure changes.

For Kubernetes infrastructure, the firewall picture is more complex because `kube-proxy` and CNI plugins insert their own `iptables` or `nftables` rules, and direct manipulation of the host firewall can conflict with cluster networking. The `iptables` rules inserted by `kube-proxy` in `KUBE-SERVICES` and `KUBE-NODEPORTS` chains implement load balancing via DNAT and must remain intact for service routing to function. The correct pattern is to manage host-level firewall rules in chains that hook at a higher priority than `kube-proxy`'s chains (which typically run at priority 0), and to restrict rules to traffic that should never reach the cluster networking layer at all — DDoS mitigation, management access control, and inter-node traffic policies.

The terminal invariant to internalize is this: a firewall rule is a contract between the operator and the network. The operator declares the traffic their infrastructure requires. The firewall enforces that declaration deterministically. Every rule that cannot be justified by an operational requirement is an expansion of attack surface; every gap in the default-deny policy is a liability. The discipline of firewall engineering is not writing rules — it is knowing with certainty what every rule permits, why it was added, and what the network state would be if it were removed.
