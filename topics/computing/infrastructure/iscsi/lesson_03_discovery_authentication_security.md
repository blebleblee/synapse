# Lesson 3: Discovery, Authentication, Security

## 1. First-Principles Intuition & Invariants

Before an initiator can transfer a single byte of SCSI data, it must solve three problems in strict sequence: it must find the target, prove it is authorized to speak with that target, and establish a channel over which every subsequent PDU can be trusted. These three problems map directly to the iSCSI stack's discovery layer, authentication layer, and session security layer. They are not optional embellishments bolted onto a working protocol; they are the protocol's precondition for correctness. Understanding why each layer exists the way it does requires tracing the engineering pressures that shaped iSCSI's design when it was standardized in RFC 3720 (later revised in RFC 7143).

SCSI was born on a point-to-point electrical bus. The HBA knew exactly which targets existed because they were physically cabled to it and enumerated at bus scan time. The notion of "discovering" a target was meaningless in that world — the wire was the directory. When the SCSI command set was lifted off the parallel bus and carried over TCP/IP in iSCSI, the fabric became a routed IP network that might span data centers. The initiator no longer had any inherent knowledge of what targets existed, where they lived, or whether a given LUN was even intended for it. Discovery was not a convenience; it became a first-class architectural requirement.

Authentication entered the picture for an equally grounded reason. A SCSI bus is a closed, physically secured cable plant. An Ethernet network is not. Any host on the same broadcast domain — or, through routing, any host on the same IP network — can in principle send TCP segments to port 3260 and begin an iSCSI Login sequence. Without authentication, storage becomes entirely dependent on network segregation for its security boundary, which violates the principle of defense in depth. CHAP (Challenge Handshake Authentication Protocol) provides a shared-secret mechanism that makes the initiator prove its identity before the Login phase completes, and mutual CHAP extends this symmetrically so the initiator can also verify the target.

Integrity and confidentiality are distinct concerns from authentication, and iSCSI handles them through two independent mechanisms. Header and data digests based on CRC32C provide end-to-end integrity detection for every PDU field and every data payload traversing the connection. IPsec at the IP layer provides both confidentiality (through ESP encryption) and a second layer of authentication. The two mechanisms are not redundant; CRC32C guards against bit errors and undetected memory corruption within the storage network path, whereas IPsec guards against active interception and traffic injection between network-layer endpoints.

The fundamental invariant that governs all three layers is sequencing. Discovery must complete before Login can begin. Login — which includes authentication — must complete before the Full Feature Phase begins. Session security parameters such as digest negotiation are established during Login and cannot be renegotiated without tearing down and re-establishing the connection. This is not arbitrary rigidity; it reflects the state-machine design of iSCSI as defined in RFC 7143 Section 7, where the session automaton is a strict directed graph with no backward edges. Violating sequence causes an immediate connection reset with a reason code of `PROTOCOL_ERROR`. Every practitioner working with iSCSI must internalize this sequencing constraint because every configuration tool, every kernel driver, and every target daemon enforces it.

---

## 2. Core Architecture & Mechanics

### SendTargets: The Discovery Wire Protocol

iSCSI defines three discovery mechanisms: SendTargets, iSNS (Internet Storage Name Service), and Static configuration. Of the three, SendTargets is the most widely deployed because it requires no additional infrastructure and works with every conformant target implementation. It deserves a detailed mechanical analysis.

SendTargets operates by opening a discovery session — a special iSCSI session whose only purpose is to retrieve a list of targets from a known portal. The initiator connects to TCP port 3260 (or a configured alternative) and enters the Login phase with the SessionType operational parameter set to `Discovery`. After the Login phase completes, the initiator issues a single Text request PDU carrying the key-value pair `SendTargets=All`. The target responds with one or more Text response PDUs containing a flat, ordered sequence of key-value pairs. The critical ones are `TargetName`, which carries an iSCSI Qualified Name (IQN) or EUI-64 formatted name, and `TargetAddress`, which carries a `host:port,portal-group-tag` triple. Consider a minimal response body:

```
TargetName=iqn.2024-01.com.storagevendor:array01.lun0
TargetAddress=10.10.1.50:3260,1
TargetAddress=10.10.1.51:3260,1
TargetName=iqn.2024-01.com.storagevendor:array01.lun1
TargetAddress=10.10.1.50:3260,2
```

This response encodes two targets. The first target has two portal addresses sharing portal-group-tag 1, meaning both portals serve the same target portal group and an initiator may connect to either for multi-path purposes. The second target has one portal with a different portal-group-tag, indicating a distinct portal group. The initiator's discovery daemon — `iscsid` on Linux — parses this response, populates its persistent node database under `/var/lib/iscsi/nodes/`, and closes the discovery session. The actual storage sessions to discovered targets are established separately and independently.

The Linux open-iSCSI toolchain makes this fully observable:

```bash
# Perform a SendTargets discovery against a portal and persist the results
iscsiadm --mode discovery --type sendtargets --portal 10.10.1.50:3260

# Inspect the resulting node database entries
iscsiadm --mode node --op show

# Log in to a specific discovered target
iscsiadm --mode node \
  --targetname iqn.2024-01.com.storagevendor:array01.lun0 \
  --portal 10.10.1.50:3260 \
  --login

# Dump the full session parameters for a running session (session ID 1)
iscsiadm --mode session -r 1 --op show
```

The `iscsiadm` command is the administrative interface to the `iscsid` daemon, which maintains persistent session state and handles reconnection. The kernel driver (`iscsi_tcp` or an offload HBA driver) manages the actual TCP connection and PDU processing. This split architecture means that `iscsid` can be restarted without dropping kernel-managed sessions, though in practice a daemon restart does trigger session revalidation.

### iSNS Architecture

Where SendTargets is bilateral — one initiator queries one target — iSNS (defined in RFC 4171) introduces a centralized directory service. The iSNS server is a separate network entity that all initiators and targets register with. Its internal data model is built around three entity types: Network Entities (physical hosts), iSCSI Nodes (initiators or targets identified by IQN), and Portals (IP:port:interface-index tuples). These form a containment hierarchy: a Network Entity contains Nodes, and a Node contains Portals.

The key architectural feature of iSNS beyond simple directory lookup is the Discovery Domain. A Discovery Domain is an administrative group that restricts which initiators can discover which targets. Even if an initiator and target are both registered in the same iSNS server, they cannot discover each other unless they share a Discovery Domain membership. This provides a soft zoning equivalent at the storage naming layer, analogous to WWN zoning in Fibre Channel fabrics.

iSNS also implements State Change Notifications (SCN). When a target registers or deregisters, the iSNS server sends a notification to all registered initiators in the same Discovery Domain. This eliminates the need for initiators to poll for topology changes, enabling faster failover and more responsive multi-path reconvergence.

The following diagram shows the iSNS registration and query flow:

```
Initiator                    iSNS Server                    Target
    |                             |                             |
    |<-- DevAttrReg (Node Reg) -->|<-- DevAttrReg (Node Reg) --|
    |                             |                             |
    |-- DevGetNext (Query DD) --->|                             |
    |<-- DevAttrQryRsp ----------|                             |
    |   [TargetName, PortalAddr]  |                             |
    |                             |                             |
    |====== iSCSI Login ==========================================>|
    |          (now using discovered portal address)              |
```

Registering an initiator with an iSNS server using the `iscsiadm` toolchain:

```bash
# Configure the iSNS server address in iscsid.conf
echo "isns.address = 10.10.1.100" >> /etc/iscsi/iscsid.conf
echo "isns.port = 3205" >> /etc/iscsi/iscsid.conf

# Perform iSNS discovery
iscsiadm --mode discovery --type isns --portal 10.10.1.100:3205

# Verify registered nodes on the iSNS server (using isnsadm if available)
isnsadm --query node --attr iSCSI-Name
```

### CHAP Authentication: Phase Mechanics

CHAP in iSCSI is performed within the Login phase, specifically during the Security Negotiation stage. Login is subdivided into the Security Negotiation stage (parameter key `AuthMethod` and the actual CHAP exchange) and the Operational Negotiation stage (all other session parameters). Authentication must conclude before operational parameters are exchanged.

The CHAP exchange is a three-step challenge-response protocol. Consider unidirectional CHAP, where only the initiator is authenticated:

The target begins by sending a CHAP_A parameter (algorithm list, currently only `5` for HMAC-MD5 as defined in RFC 1994, though implementations commonly extend to SHA-256 by vendor agreement). The initiator selects an algorithm and the target responds with CHAP_I (an identifier byte) and CHAP_C (a randomly generated challenge value, encoded as a hex string prefixed with `0x`). The initiator computes the CHAP response as:

```
CHAP_R = MD5(CHAP_I || SharedSecret || CHAP_C)
```

where `||` denotes concatenation and the identifier byte CHAP_I is a single octet prepended to the secret before hashing. The initiator sends CHAP_N (its IQN as the authenticating name) and CHAP_R (the computed response). The target performs the same computation using the shared secret it holds for that initiator name, compares the result, and either completes the Login phase or returns a login response with status class `0x01` (Initiator Error) and detail `0x0201` (Authentication Failed).

Mutual CHAP reverses this symmetrically. The initiator selects CHAP_I and generates its own CHAP_C, sending them alongside CHAP_R. The target must then compute and return a CHAP response over the initiator's challenge using the target's own shared secret. This prevents a rogue target from accepting a valid CHAP response and then returning SCSI data from an unauthorized storage pool.

The `/etc/iscsi/iscsid.conf` configuration for mutual CHAP reflects these two independent secrets:

```bash
# /etc/iscsi/iscsid.conf - CHAP configuration block

# Initiator authenticates to target (outgoing CHAP)
node.session.auth.authmethod = CHAP
node.session.auth.username = iqn.2024-01.com.initiatorhost:host01
node.session.auth.password = Str0ng!nitiatorSecret42

# Target authenticates to initiator (incoming/mutual CHAP)
node.session.auth.username_in = iqn.2024-01.com.storagevendor:array01
node.session.auth.password_in = Str0ng!argetSecret99
```

A critical implementation constraint is that the two passwords must differ. RFC 7143 Section 11.1.5 explicitly prohibits using the same secret in both directions because a symmetric secret allows an attacker to replay the target's challenge back to the target, defeating the mutual authentication entirely.

You can inspect the negotiated authentication parameters on a live session:

```bash
# Show authentication state for all active sessions
iscsiadm --mode session --op show | grep -E "Auth|CHAP|username"

# Dump the full node configuration including CHAP for a specific target
iscsiadm --mode node \
  --targetname iqn.2024-01.com.storagevendor:array01.lun0 \
  --portal 10.10.1.50:3260 \
  --op show
```

### Header and Data Digests: CRC32C Mechanics

Digests are negotiated during the Operational Negotiation stage of Login through the `HeaderDigest` and `DataDigest` keys. Each accepts a comma-separated preference list of `CRC32C` and `None`. The rule is that the target's preference takes effect if both sides list a value in common, with the first match winning. A production configuration that mandates digests on both sides:

```bash
# /etc/iscsi/iscsid.conf - digest negotiation
node.conn[0].iscsi.HeaderDigest = CRC32C,None
node.conn[0].iscsi.DataDigest = CRC32C,None
```

Setting `CRC32C,None` means "prefer CRC32C but accept None." To mandate it unconditionally (refusing connections that don't support it), set `CRC32C` alone. Be aware that this will cause Login to fail against targets that do not support CRC32C, so validate target capability before mandating.

The CRC32C checksum is computed over the iSCSI header (48 bytes for the basic header segment, plus any additional header segments) and appended as a 4-byte field immediately following the header. For data digests, the CRC32C covers the Data Segment and is appended after it, before the next PDU. The receiver recomputes the CRC32C upon receipt and drops any PDU where the received and computed values diverge, incrementing a connection error counter that the driver uses to trigger error recovery.

The kernel's software CRC32C implementation uses the Castagnoli polynomial (`0x1EDC6F41`). On processors with the SSE4.2 `crc32` instruction, the kernel automatically selects the hardware-accelerated path, reducing the CPU overhead to roughly one cycle per four bytes of payload — a negligible cost on modern hardware for block sizes of 4 KiB and above.

```c
/* Kernel-space CRC32C computation (from include/linux/crc32c.h) */
#include <linux/crc32c.h>

/*
 * crc32c(seed, data, length)
 * seed = 0xFFFFFFFF for iSCSI per RFC 7143 §6.4
 */
static u32 iscsi_crc32c(const void *data, size_t len)
{
    return crc32c(0xFFFFFFFF, data, len);
}
```

The seed value `0xFFFFFFFF` and the final XOR with `0xFFFFFFFF` (the standard CRC32C convention) are both specified in RFC 7143 and must be used exactly. Any deviation produces a CRC mismatch that will silently destroy sessions under load.

### IPsec Integration and Session Security Architecture

IPsec operates at Layer 3 and is therefore transparent to the iSCSI layer. From the iSCSI PDU's perspective, it simply flows over TCP, and that TCP connection happens to be carried in an ESP-encrypted IP datagram. This transparency is intentional: iSCSI does not negotiate IPsec parameters; that is handled entirely by IKEv2 and the kernel's Security Policy Database (SPD).

The practical consequence is that IPsec must be configured to match the specific source and destination IP addresses used by the iSCSI portals. A broad "encrypt all traffic between host A and host B" policy is the most maintainable approach in dedicated storage networks.

```bash
# Install strongSwan for IKEv2
apt-get install strongswan strongswan-pki

# /etc/ipsec.conf - iSCSI storage transport protection

config setup
    charondebug="ike 1, knl 1, cfg 0"

conn iscsi-storage
    type=transport
    authby=psk
    left=10.10.1.10          # Initiator IP
    right=10.10.1.50         # Target portal IP
    leftprotoport=tcp
    rightprotoport=tcp/3260
    esp=aes256gcm16-prfsha384-ecp384!
    ike=aes256gcm16-prfsha384-ecp384!
    keyingtries=%forever
    auto=start
```

```bash
# /etc/ipsec.secrets
10.10.1.10 10.10.1.50 : PSK "ProductionStoragePreSharedKey!2024"
```

```bash
# Start and verify the IPsec tunnel
systemctl start strongswan-starter
ipsec statusall | grep iscsi-storage

# Confirm ESP-encapsulated packets are flowing on the storage interface
tcpdump -nn -i eth1 esp
```

Transport mode (not tunnel mode) is the correct choice here because the initiator and target are IP peers, not gateways. Tunnel mode would double-encapsulate the IP header unnecessarily and complicate MTU calculations that are already tight due to iSCSI's header overhead.

The full session security parameter set that is established by the time the Full Feature Phase begins can be visualized as follows:

```
┌─────────────────────────────────────────────────────────┐
│                    iSCSI Session                        │
│                                                         │
│  Discovery Layer                                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SendTargets  │  iSNS  │  Static Node Config     │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│  Login Phase             ▼                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Stage 0: Security Negotiation                   │   │
│  │   AuthMethod=CHAP                                │   │
│  │   CHAP_A / CHAP_I / CHAP_C / CHAP_R (bidirect.) │   │
│  │  Stage 1: Operational Negotiation                │   │
│  │   HeaderDigest=CRC32C                            │   │
│  │   DataDigest=CRC32C                              │   │
│  │   MaxRecvDataSegmentLength=262144                │   │
│  │   ImmediateData=Yes                              │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│  Network Layer           ▼                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  IPsec ESP (AES-256-GCM) over TCP port 3260      │   │
│  │  IKEv2 with PSK or X.509 certificate auth        │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│  Full Feature Phase      ▼                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SCSI Command PDUs with CRC32C header + data     │   │
│  │  digests on every PDU for the session lifetime   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 3. High-Performance Optimization & Failure Modes

### Discovery Layer Failure Modes and Mitigations

The most operationally damaging discovery failure is a stale node database. When a target's portal address changes — due to a network reconfiguration, a controller failover, or an IP address reassignment — the initiator's `/var/lib/iscsi/nodes/` database retains the old portal. `iscsid` will attempt reconnection to the stale address indefinitely, with exponential backoff, while the actual target is now reachable at a new address. The mitigation is to either automate periodic SendTargets rediscovery or to use iSNS with State Change Notifications, which eliminates this problem entirely for topology changes that the iSNS server is aware of.

```bash
# Force a fresh SendTargets discovery, overwriting cached node records
iscsiadm --mode discovery --type sendtargets \
  --portal 10.10.1.50:3260 \
  --op update

# Remove all stale node entries for a target that has permanently moved
iscsiadm --mode node \
  --targetname iqn.2024-01.com.storagevendor:array01.lun0 \
  --op delete

# Inspect the discovery database for stale portals
iscsiadm --mode discoverydb --op show
```

A subtler issue occurs when the discovery session itself cannot complete Login due to network MTU fragmentation. iSCSI discovery sessions use the same Login PDU format as storage sessions, and Login PDUs can be large when the initiator IQN is long and the operational parameter list is verbose. If the network path MTU is below the PDU size and ICMP fragmentation-needed messages are blocked (a common misconfiguration in datacenter environments with ICMP filtering), the TCP connection silently stalls. The diagnostic is to check whether the discovery session completes with `tcpdump` on the initiator NIC and verify that no TCP retransmissions occur at the Login PDU boundary.

### CHAP Authentication Failures: Diagnosis and Common Causes

CHAP authentication failures surface as Login response PDUs with status class `0x01`, detail `0x0201`. The `iscsid` log captures this:

```bash
# Monitor iscsid authentication events in real time
journalctl -u iscsid -f | grep -E "CHAP|auth|Login"

# Check kernel-level iSCSI error logging
dmesg | grep -i iscsi | tail -30
```

The three most common root causes in production are: a secret that exceeds 256 bits (the RFC 7143 maximum for CHAP secrets when transmitted as hex-encoded binary), a character encoding mismatch where the secret contains multi-byte UTF-8 characters that one side interprets at the byte level while the other interprets at the codepoint level, and clock skew — CHAP itself is not time-sensitive, but if the IPsec IKEv2 layer is also active and the system clocks diverge by more than the IKEv2 clock skew tolerance (typically 300 seconds), IPsec rekey failures will drop the TCP connection during the CHAP exchange, producing what looks like an authentication failure but is actually a transport failure.

The debugging sequence for a suspected mutual CHAP failure must proceed in order: first verify the unidirectional (initiator-to-target) exchange succeeds by temporarily disabling `node.session.auth.username_in`, then re-enable and test mutual authentication. If unidirectional succeeds but mutual fails, the target-side secret or the target's IQN in `username_in` is incorrect.

### Digest Performance and Tuning

CRC32C digests add measurable CPU overhead on paths that do not have hardware CRC32C acceleration. On kernels before 4.14 and on ARM systems without the CRC32 optional instruction set, the software fallback consumes approximately 4–6 CPU cycles per byte. At 10 Gbps line rate, a single CPU core processing 1250 MB/s of digest computation is saturated. The solution on affected hardware is either to disable data digests (retaining only header digests, which are 48 bytes and negligible) or to offload iSCSI processing to an HBA that handles CRC32C in hardware.

```bash
# Check whether the kernel selected the hardware CRC32C implementation
grep crc32c /proc/crypto

# Expected output on SSE4.2-capable x86 (driver = "crc32c-intel"):
# name         : crc32c
# driver       : crc32c-intel
# module       : crc32c_intel
# priority     : 300

# If only the generic driver is present (priority 100), force-load the hardware module
modprobe crc32c_intel

# Measure throughput with and without data digest using fio against an iSCSI block device
fio --name=digest-test --filename=/dev/sdb --rw=read \
    --bs=128k --iodepth=32 --direct=1 --runtime=30 \
    --group_reporting --output-format=json
```

### IPsec and iSCSI MTU Interaction

The combination of IPsec transport mode and iSCSI over a standard 1500-byte Ethernet MTU is one of the most reliable sources of hard-to-diagnose throughput collapse in production. The overhead math is unforgiving: an ESP packet in transport mode with AES-256-GCM adds 8 bytes for the ESP header, 8 bytes for the IV, 16 bytes for the ICV (authentication tag), and up to 15 bytes of padding, for a worst-case addition of 47 bytes over the IP+TCP header that iSCSI already carries. Combined with the 48-byte iSCSI basic header segment and the 20-byte TCP header and 20-byte IP header, the effective payload per 1500-byte Ethernet frame drops to approximately 1365 bytes — a 9% overhead that compounds with connection count under multi-stream workloads.

The correct mitigation is to enable jumbo frames on the storage network (9000-byte MTU) and to set the iSCSI `MaxRecvDataSegmentLength` to reflect the available payload space after all encapsulation overhead:

```bash
# Set jumbo frames on the storage NIC
ip link set eth1 mtu 9000

# Verify end-to-end path MTU with ICMP (target IP 10.10.1.50)
ping -M do -s 8972 10.10.1.50

# Configure MaxRecvDataSegmentLength in iscsid.conf to avoid fragmentation
# 8192 is a conservative safe value for 9000-byte MTU with IPsec overhead
echo "node.conn[0].iscsi.MaxRecvDataSegmentLength = 8388608" \
  >> /etc/iscsi/iscsid.conf

# After changing iscsid.conf, restart the daemon and re-login
systemctl restart iscsid
iscsiadm --mode node \
  --targetname iqn.2024-01.com.storagevendor:array01.lun0 \
  --portal 10.10.1.50:3260 \
  --login
```

### Session Security Parameter Renegotiation and Its Absence

One of the most consequential constraints in iSCSI's security model is that session parameters, including `HeaderDigest`, `DataDigest`, and `AuthMethod`, cannot be changed after Login completes without terminating and re-establishing the session. There is no in-band mechanism analogous to TLS renegotiation. This means that a misconfigured session running with `HeaderDigest=None` cannot be upgraded to CRC32C without an I/O-impacting session teardown.

In practice, this means that security parameters must be enforced at two levels: in `iscsid.conf` on the initiator to control what the initiator proposes, and in the target daemon's configuration to mandate minimum acceptable parameters. If the target is configured to reject `None` for `HeaderDigest` and an initiator's configuration offers only `None`, the Login phase will fail cleanly before any data exposure occurs. The correct operational posture is to configure the target as the enforcement point and treat the initiator configuration as preference ordering.

```bash
# On a Linux target using targetcli / LIO, enforce CRC32C
targetcli
/iscsi/iqn.2024-01.com.storagevendor:array01/tpg1 set attribute \
  default_data_digest=crc32c
/iscsi/iqn.2024-01.com.storagevendor:array01/tpg1 set attribute \
  default_header_digest=crc32c
/iscsi/iqn.2024-01.com.storagevendor:array01/tpg1 set attribute \
  authentication=1
saveconfig
exit
```

The combination of enforced CRC32C digests, mandatory CHAP authentication (with mutual authentication on any network path that is not physically isolated), and IPsec ESP encryption constitutes a complete, defense-in-depth iSCSI security posture. No single layer is sufficient alone: CHAP without digests allows authenticated but corrupt data to propagate; digests without CHAP detect corruption but permit unauthorized sessions; IPsec without application-layer authentication delegates all access control to the IPsec SA, which does not map to iSCSI's per-target authorization model. Only the full stack addresses all three threat vectors — unauthorized access, data corruption, and traffic interception — within the constraints and sequencing invariants that RFC 7143 establishes.
