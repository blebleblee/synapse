# Lesson 4: Error Recovery, Performance Optimization

## 1. First-Principles Intuition & Invariants

Every storage protocol built atop a general-purpose transport inherits that transport's failure characteristics, and iSCSI is no exception. When SCSI was confined to a parallel copper bus, error recovery was straightforward: the host bus adapter issued a reset, the bus settled, and work resumed. The bus was private, deterministic, and physically short. iSCSI discards all of those properties. It routes SCSI commands through TCP/IP, a protocol designed for resilience across hostile, shared, variable-latency networks. The result is a profound mismatch in reliability assumptions that iSCSI must bridge through a carefully layered error-recovery architecture.

The fundamental invariant of SCSI semantics is *command ordering and completion*. An initiator issues a command expecting one of exactly three outcomes: the command completes successfully, it completes with a checked condition (an error the SCSI sense data describes), or it is aborted. What SCSI has never tolerated is ambiguity: a command whose fate is genuinely unknown. TCP can deliver this ambiguity freely. A connection can silently stall for minutes before the kernel's keepalive machinery declares it dead. During that window, commands are outstanding, R2T (Ready To Transfer) sequences may be partially delivered, and data-in PDUs may be in flight. Without a disciplined recovery framework, the initiator cannot distinguish between "the target is processing the command slowly" and "the command was lost."

RFC 3720 addresses this through a three-tier recovery hierarchy, each tier more disruptive than the last. Recovery within a connection handles the least severe class of fault: individual PDU loss or sequence-number discontinuity detectable without tearing down the session. Recovery at the connection level handles the case where a single TCP connection has failed but the iSCSI session it carried is still logically alive. Recovery at the session level handles total loss of all connections in a session, requiring the initiator to re-establish the session itself before any SCSI commands can proceed.

Understanding why these tiers exist requires understanding the iSCSI PDU numbering system. Every command PDU carries a **CmdSN** (command sequence number), a 32-bit counter scoped to the session and advanced monotonically by the initiator. Data-out PDUs carry a **DataSN** relative to their enclosing command. Status responses carry **StatSN**, advanced by the target per connection. R2T PDUs carry an **R2TSN**. These sequence numbers are not merely ordering hints; they are the substrate of exactly-once delivery semantics. If a data-out PDU is lost in the network and TCP's retransmit timer eventually fires, the retransmit happens transparently below iSCSI. But if the TCP *connection* itself is torn down and reconstructed, sequence numbers on the new connection start fresh, and iSCSI must use the preserved CmdSN and StatSN to re-synchronize state. This is the mechanical reason why the recovery tiers are distinct: each tier corresponds to a different level of sequence-number context that remains valid.

The first invariant of iSCSI error recovery is therefore: *sequence numbers belong to the session, not the connection*. A connection is a transport vehicle. The session is the logical entity that owns SCSI state. This distinction, seemingly academic, is what makes connection reinstatement possible at all. The second invariant is: *a target must never execute a command twice as a consequence of initiator retry*. The CmdSN ensures this: a target that has already processed a command and advanced its expected-command-sequence will recognize a retransmitted PDU as a duplicate and either discard it or respond with the cached status.

Performance optimization within iSCSI is inseparable from these recovery mechanics because the same parameters that govern burst sizes and outstanding I/O also govern how much state must be preserved and replayed during recovery. Setting `MaxOutstandingR2T` aggressively high accelerates write throughput on high-latency paths but increases the replay burden if a connection fails mid-transfer. `FirstBurstLength` and `MaxBurstLength` control how much unsolicited and solicited write data respectively can be in flight at any time, directly shaping both throughput and the size of the in-flight state that recovery must reconcile. These are not independent tuning knobs; they are coupled levers that trade off steady-state throughput against recovery complexity and re-establishment latency.

---

## 2. Core Architecture & Mechanics

### The Three-Tier Recovery Architecture

The iSCSI specification defines recovery levels 0, 1, and 2, numbered in order of increasing disruption. The kernel's iSCSI implementation (the `libiscsi` layer and the transport-class drivers such as `iscsi_tcp`) implements each tier with distinct code paths and state machine transitions.

**Recovery Level 0: Within-Connection Recovery** operates entirely within an established TCP connection and does not require re-establishing any transport state. The fundamental mechanism is digest failure detection and sequence-number discontinuity. iSCSI PDU headers carry optional CRC-32C digests over both the header and data segments. When the initiator's receive path detects a digest mismatch, it records the error but does not immediately abort the command; instead, it issues a **NOP-Out** PDU to solicit an **ExpStatSN** echo from the target, using the response to determine which status PDUs the target believes have been acknowledged. If the initiator detects a gap in its received StatSN sequence, it issues a **SNACK (Selective Negative Acknowledgment) Request** PDU with Type=0 (data retransmit) or Type=1 (R2T/status retransmit), requesting the target resend specific PDUs identified by their sequence numbers. The target, if it has buffered the requested PDUs, retransmits them. If it has not, it responds with a Reject PDU bearing reason code "SNACK Reject," forcing the initiator to escalate to Level 1. Level 0 is entirely non-disruptive: SCSI commands remain active, the session remains connected, and the only observable overhead is the latency of the SNACK/retransmit exchange.

**Recovery Level 1: Connection Recovery** handles the failure of a single TCP connection carrying a subset of a session's commands. When the kernel's TCP layer reports a connection reset or the iSCSI session timer expires without a successful keepalive, the initiator driver transitions the connection to the `CLEANUP_WAIT` state and begins the reinstatement procedure. The critical property here is that the *session* remains alive. The initiator must re-establish a TCP connection to the same target portal (or an alternate portal in the same portal group), perform an iSCSI login with `SessionType=Normal` and a **TSIH (Target Session Identifying Handle)** matching the existing session. This signals to the target that the new TCP connection is reinstating a failed one, not creating a new session. The target verifies the TSIH and, if the session is still valid on its side, accepts the connection and synchronizes state by exchanging **ExpCmdSN** and **MaxCmdSN** in the login response.

After the new connection is established, the initiator must determine which commands were outstanding on the failed connection. It does this by examining its pending command queue, filtered by the connection's last acknowledged **ExpStatSN**. Any command whose CmdSN is greater than the highest acknowledged CmdSN is considered potentially lost and must be retried or explicitly cleaned up via task management. The initiator driver then issues those commands again on the new connection, relying on the target's duplicate-detection logic (CmdSN comparison against `ExpCmdSN`) to discard any that the target had already processed.

**Recovery Level 2: Session Recovery** is the last resort. It triggers when all TCP connections in a session have failed, or when a Level 1 recovery attempt fails because the target has already invalidated the TSIH. The initiator must perform a full session logout (if possible) or simply drop all state, then re-login with `TSIH=0` to create a fresh session. All commands that were outstanding in the old session are aborted from the initiator's perspective: the SCSI mid-layer is notified that each command has failed, and it is the SCSI error handler's responsibility to decide whether to retry, escalate to device reset, or surface the failure to the filesystem. Level 2 recovery is the most expensive: it incurs the full login handshake overhead and requires the SCSI error handler to serialize recovery, which on a loaded storage path can take several seconds and cause I/O queues to stall visibly.

### Task Management Functions

iSCSI task management functions (TMFs) are the SCSI protocol's mechanism for forcibly terminating in-flight commands, and their interaction with iSCSI's layered recovery is subtle. RFC 3720 maps the standard SCSI task management functions to iSCSI Task Management Request PDUs with function codes for Abort Task, Abort Task Set, Clear ACA, Clear Task Set, Logical Unit Reset, and Target Warm Reset.

The **Abort Task** function is the most granular: it targets a single command identified by its **Referenced Task Tag (RTT)** and **LUN**. When an initiator issues Abort Task, the target must check whether the referenced task is still active. If the command has already completed (but its status PDU was lost in transit), the target responds with "Task Does Not Exist" and the initiator infers the command completed at some point, then issues a SNACK to recover the lost status. If the command is genuinely active, the target terminates it and responds with Function Complete. The initiator must wait for this response before releasing the task tag and issuing any retry, ensuring no window where two instances of the same logical command could be active simultaneously.

**Logical Unit Reset** is substantially more disruptive. It clears the task set for the addressed LUN and resets the LU's ACA condition, but it also causes the target to discard all buffered status PDUs for outstanding commands to that LUN. The initiator must therefore treat all commands to that LUN as having unknown fate and either reissue them or abort them through the SCSI error handler. In a production environment, LU Reset is typically issued by the SCSI error handler after a command timeout that Abort Task failed to resolve.

The sequence diagram below illustrates the Level 1 recovery flow through connection reinstatement and task management:

```
Initiator                           Target
    |                                   |
    |--- SCSI Write (CmdSN=42) -------->|
    |--- SCSI Read  (CmdSN=43) -------->|
    |                                   |
    | [TCP connection fails]            |
    |                                   |
    |--- TCP SYN (new connection) ----->|
    |<-- TCP SYN-ACK -------------------|
    |--- iSCSI Login (TSIH=0x1A3F) --->|
    |<-- Login Response (OK, StatSN=7) -|
    |                                   |
    | [Initiator checks: ExpStatSN=5,   |
    |  CmdSN 42-43 unacknowledged]      |
    |                                   |
    |--- TMF: Abort Task (RTT=42) ----->|
    |<-- TMF Response: Task Not Exist --|  (target finished cmd 42)
    |--- SNACK (StatSN=5, run=2) ------>|  (recover lost status PDUs)
    |<-- Data-In / R2T replay ----------|
    |<-- SCSI Response (CmdSN=42) ------|
    |                                   |
    |--- TMF: Abort Task (RTT=43) ----->|
    |<-- TMF Response: Function Complete|  (target aborted cmd 43)
    |--- SCSI Read (CmdSN=43, retry) -->|  (reissue on new connection)
    |<-- Data-In PDUs ------------------|
    |<-- SCSI Response (success) -------|
```

### Session and Connection Parameters: The Data Structures That Matter

The iSCSI operational parameters negotiated during login are stored per-session and per-connection in the kernel's iSCSI session structure. In the Linux kernel's `libiscsi` implementation (`drivers/scsi/libiscsi.c`), the `iscsi_session` structure carries the session-scoped parameters, while `iscsi_conn` carries the connection-scoped ones. Understanding which parameters live where is essential for understanding both performance tuning and recovery behavior.

`FirstBurstLength` is session-scoped. It defines the maximum amount of unsolicited write data, in bytes, that the initiator may send without receiving an R2T. The default is 65,536 bytes (64 KiB). Unsolicited data is included in the initial burst: the SCSI Command PDU carries an immediate data segment, and the initiator may optionally follow with unsolicited Data-Out PDUs until it has sent `FirstBurstLength` bytes. After that threshold, it must wait for explicit R2T PDUs from the target before sending more. The significance for recovery is that unsolicited data has no R2T sequence numbers: if the connection fails after the initiator has sent 48 KiB of unsolicited data toward a 128 KiB write, that 48 KiB has no recovery handle. The target does not issue SNACK for unsolicited data; the entire command must be reissued.

`MaxBurstLength` bounds the total write data the initiator may send in response to a single R2T (or across all R2Ts if `MaxOutstandingR2T` > 1). It is also session-scoped. Setting `MaxBurstLength` to 16,776,192 bytes (the RFC maximum) on a 10 GbE fabric with a target that has fast NVME backing will produce excellent throughput on large sequential writes, but each in-flight R2T-data sequence represents state the target must buffer. If a connection fails mid-burst, the initiator must reissue the entire command, retransmitting all data from offset zero. On high-bandwidth paths, this means recovery retransmits can consume significant target receive buffer capacity.

`MaxOutstandingR2T` is the most latency-sensitive parameter. It governs how many R2T/data sequences can be simultaneously in flight for a single SCSI command. With `MaxOutstandingR2T=1`, the initiator sends data only after receiving an explicit R2T, waits for the target to process it, receives the next R2T, and so on. This serializes write data transfer and is catastrophically inefficient on any path with meaningful RTT. With `MaxOutstandingR2T=4`, four independent data ranges can be in flight simultaneously, overlapping network round trips with target write operations. The tradeoff: each outstanding R2T-data sequence is a unit of potential replay work during recovery, and the target must track four simultaneous streams of data for the same command.

The `ErrorRecoveryLevel` parameter, negotiated at login, establishes which recovery tiers are mutually supported. Setting this to 0 disables SNACK and within-connection recovery; setting it to 1 enables connection recovery; setting it to 2 enables session recovery with the full reinstatement protocol. Almost all production deployments run at Level 2.

---

## 3. High-Performance Optimization & Failure Modes

### Tuning FirstBurstLength, MaxBurstLength, and MaxOutstandingR2T

The optimal values for these three parameters are not universal; they depend on the fabric RTT, the target's write buffer depth, the initiator's I/O pattern (sequential versus random), and the acceptable recovery overhead. The following analysis gives a practitioner the mechanistic reasoning to arrive at values empirically rather than copying cargo-cult defaults.

On a 25 GbE fabric with an average RTT of 100 microseconds between initiator and target, the bandwidth-delay product is approximately 312 KiB (25 Gbps × 100 µs / 8). This is the amount of data that can be "in the pipe" at any time. If `MaxBurstLength` is smaller than the BDP, the initiator will be forced to stall waiting for acknowledgment, underutilizing the link. For sequential write workloads, `MaxBurstLength` should be set to at least 2× the BDP, allowing the pipeline to remain full even under light congestion. For this fabric, 1 MiB (1,048,576 bytes) is a reasonable starting point.

`FirstBurstLength` should match the most common I/O request size for unsolicited-data eligibility. A database issuing 256 KiB sequential writes benefits from `FirstBurstLength=262144`, allowing the first quarter-megabyte to flow without R2T handshaking. A OLTP workload issuing 4 KiB random writes is better served by a smaller `FirstBurstLength` (the default 65,536 is likely fine) because the overhead of a single R2T exchange is negligible compared to the command processing time.

`MaxOutstandingR2T` should be tuned by measuring target write throughput as a function of R2T pipelining depth. The following procedure uses `fio` on the initiator and `iostat` on the target-side block device to characterize the optimal value:

```bash
# On the initiator: set the parameter via iscsiadm before login
iscsiadm -m node \
  -T iqn.2024-01.com.example:storage01 \
  -p 192.168.100.10:3260 \
  --op update \
  -n node.session.iscsi.MaxOutstandingR2T \
  -v 4

iscsiadm -m node \
  -T iqn.2024-01.com.example:storage01 \
  -p 192.168.100.10:3260 \
  --op update \
  -n node.session.iscsi.FirstBurstLength \
  -v 262144

iscsiadm -m node \
  -T iqn.2024-01.com.example:storage01 \
  -p 192.168.100.10:3260 \
  --op update \
  -n node.session.iscsi.MaxBurstLength \
  -v 16776192

# Log out and back in to apply negotiated parameters
iscsiadm -m node \
  -T iqn.2024-01.com.example:storage01 \
  -p 192.168.100.10:3260 \
  --logout

iscsiadm -m node \
  -T iqn.2024-01.com.example:storage01 \
  -p 192.168.100.10:3260 \
  --login

# Verify negotiated values after login
iscsiadm -m session -P 3 | grep -E 'MaxBurst|FirstBurst|MaxOutstanding'

# Run a sequential write benchmark at 1 MiB block size, queue depth 32
fio --name=iscsi_seq_write \
    --ioengine=libaio \
    --rw=write \
    --bs=1m \
    --iodepth=32 \
    --direct=1 \
    --filename=/dev/sdb \
    --runtime=60 \
    --time_based \
    --group_reporting
```

After each `MaxOutstandingR2T` value (1, 2, 4, 8, 16), record the throughput and latency from `fio`'s output. You will typically observe throughput increases up to the point where the target's receive buffer or its NVMe write commit path becomes the bottleneck, after which additional R2T parallelism yields no gain while increasing the recovery cost. For most NVMe-oF targets, the saturation point falls between 4 and 8 outstanding R2Ts for sequential 1 MiB writes.

To read back the actually negotiated parameters (the target may have constrained them below your requested values during login), read the kernel's sysfs representation:

```bash
# Find the session number
ls /sys/class/iscsi_session/

# Read negotiated parameters for session0
cat /sys/class/iscsi_session/session0/max_burst_len
cat /sys/class/iscsi_session/session0/first_burst_len
cat /sys/class/iscsi_session/session0/max_r2t
```

### TCP Socket Tuning for iSCSI Throughput

iSCSI performance is ultimately constrained by TCP socket buffers when the initiator is saturating the link. The kernel's autotuning (`tcp_rmem`, `tcp_wmem`) works well for general traffic but can throttle iSCSI at high block sizes. For an iSCSI-dedicated interface:

```bash
# Raise the TCP socket buffer limits for high-throughput iSCSI
# These values suit a 25 GbE fabric; scale linearly for higher speeds.
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"

# Disable Nagle on the iSCSI data path (the driver does this for dedicated
# iSCSI NICs, but confirm it is not re-enabled by a generic network script)
# Check via ss for the iSCSI TCP connections
ss -tnoi dst 192.168.100.10 | grep -i nagle

# Enable Jumbo Frames on the iSCSI storage NIC (MTU 9000)
ip link set ens5f0 mtu 9000

# Verify MTU end-to-end with a probe that sets the DF bit
ping -M do -s 8972 192.168.100.10
```

Jumbo frames deserve special attention because their benefit to iSCSI is not purely about raw throughput. Each TCP segment that spans an iSCSI PDU boundary forces the initiator driver to handle a header split across two socket buffers. At MTU 1500, a 512 KiB write burst generates roughly 341 segments; at MTU 9000, the same burst generates 57 segments. This reduces interrupt rate by 83%, cuts CPU time in the softirq path proportionally, and reduces the probability that a PDU's header and data segments are separated in the receive path in a way that forces a copy.

### Multi-Path I/O: Architecture and Failure Handling

Multi-path I/O for iSCSI operates at two distinct layers that must work together without conflict: the iSCSI session layer's own multi-connection support (multiple TCP connections within a single session, governed by `MaxConnections`) and the device-mapper multipath (`dm-multipath`) layer, which presents a single block device over multiple independent iSCSI sessions to independent target ports.

The two approaches are not equivalent. Multiple connections within a single iSCSI session share CmdSN space and the same TSIH; they provide connection-level redundancy and can aggregate bandwidth, but they all fail together if the target invalidates the session. `dm-multipath` with independent sessions to separate target portal groups (TPGs) provides true path independence: each path is a separate iSCSI session with its own TSIH, its own login exchange, and its own error-recovery state machine. If the target's port 0 goes offline, `dm-multipath` fails over to port 1's session within the failover timeout, and no SCSI error handler involvement is required at the application level.

A correct `multipath.conf` for iSCSI storage requires careful attention to the hardware handler and the path checker:

```
defaults {
    polling_interval      5
    path_selector         "round-robin 0"
    path_grouping_policy  multibus
    uid_attribute         ID_SERIAL
    rr_min_io             100
    flush_on_last_del     yes
    no_path_retry         fail
}

devices {
    device {
        vendor                  "LIO-ORG"
        product                 ".*"
        path_grouping_policy    multibus
        hardware_handler        "1 alua"
        path_checker            tur
        prio                    alua
        failback                immediate
        rr_weight               priorities
        no_path_retry           queue
        rr_min_io_rq            1
    }
}
```

The `path_checker tur` directive issues a SCSI **Test Unit Ready** command periodically to each path. This is preferred over `readsector0` for iSCSI targets because TUR does not perform an actual read I/O, reducing load on both the target and the fabric. The `hardware_handler "1 alua"` activates the ALUA (Asymmetric Logical Unit Access) handler, which reads the target's port group access state and preferentially routes I/O through **Active/Optimized** ports rather than **Active/Non-Optimized** ones, dramatically reducing write latency on active/passive arrays where non-optimized ports must proxy writes through an internal interconnect.

To inspect path state and verify ALUA port group status in production:

```bash
# View all multipath device paths and their status
multipath -ll

# Check ALUA access state for a specific LUN on each path
# sg_rtpg (from sg3_utils) sends REPORT TARGET PORT GROUPS
sg_rtpg --verbose /dev/sdb

# Trigger an immediate path failover test
# (removes path from dm-multipath's active set)
echo "offline" > /sys/block/sdb/device/state

# Watch dm-multipath react to the path failure
dmesg -w | grep -E 'multipath|dm-[0-9]'

# Restore the path
echo "running" > /sys/block/sdb/device/state
```

### Connection Reinstatement Under Load: The Stale Command Problem

The most dangerous failure mode in iSCSI production environments is not simple connection failure — it is *asymmetric partial failure* during a write burst. Consider this scenario: an initiator is writing a 64 MiB object to a target. `MaxBurstLength` is 8 MiB, and the initiator has received R2Ts for three 8 MiB ranges (offsets 0, 8, 16 MiB) simultaneously. It has completed sending the data for offset 0 and is 4 MiB into the range at offset 8. At this point, the TCP connection fails.

From the target's perspective, the write command is active, the data for offset 0 has been received and may already be committed to cache, the data for offset 8 is 4 MiB short of complete, and the data for offset 16 has not begun arriving. The target holds all three R2T grants as open.

From the initiator's perspective, the entire command must be treated as having unknown outcome. When it reinstates the connection and re-logs in with the existing TSIH, it must issue a Task Management Abort Task for the original command tag. If the target responds that the task does not exist, the target has completed the command and the initiator issues SNACK for the missing status PDU. If the target responds Function Complete, the command was aborted, and the initiator must reissue the write from byte zero, retransmitting all 64 MiB.

This scenario exposes a critical performance invariant: *the larger `MaxBurstLength` relative to the atomic commit unit of the target, the more data must be retransmitted on recovery*. For targets backed by block storage with write-back caches, there is an additional consistency risk: if the target committed the offset-0 range to its cache but not to persistent storage, and the system loses power before the cache is flushed, the application may believe the write failed (because the iSCSI recovery path returned an error), while the storage array holds a partial overwrite. Production deployments that require write ordering guarantees must configure the target to flush on each iSCSI write command completion (by honoring the FUA bit in the SCSI Write(16) CDB) or accept that `MaxBurstLength` tuning trades throughput for recovery determinism.

### Diagnosing Error Recovery Latency with iSCSI Session Statistics

The kernel exposes per-session error counters through sysfs that allow an operator to distinguish between transient within-connection errors (SNACK exchanges), connection-level recoveries (TCP resets followed by reinstatement), and session-level recoveries (full re-login). These counters are indispensable for capacity planning and SLA compliance analysis:

```bash
# Count of connection error recoveries for session0
cat /sys/class/iscsi_session/session0/conn_err_count

# Count of digest errors (triggers Level 0 recovery)
cat /sys/class/iscsi_connection/connection0:0/err_header_digest_count
cat /sys/class/iscsi_connection/connection0:0/err_data_digest_count

# EXP_STATSN on the current connection (use to track synchronization)
cat /sys/class/iscsi_connection/connection0:0/exp_statsn

# Display all iSCSI session statistics in one pass
for session in /sys/class/iscsi_session/session*; do
    echo "=== $(basename $session) ==="
    echo "  Target:      $(cat $session/targetname)"
    echo "  Conn Errors: $(cat $session/conn_err_count 2>/dev/null || echo N/A)"
    echo "  State:       $(cat $session/state)"
    for conn in $session/connection*; do
        echo "  Connection: $(basename $conn)"
        echo "    Header Digest Errors: $(cat $conn/err_header_digest_count 2>/dev/null || echo N/A)"
        echo "    Data Digest Errors:   $(cat $conn/err_data_digest_count 2>/dev/null || echo N/A)"
    done
done
```

A production iSCSI host should exhibit zero connection error recoveries during normal operation. Any non-zero `conn_err_count` that is growing indicates a fabric instability — typically an oversubscribed switch buffer causing TCP RSTs, a NIC driver bug in interrupt coalescing causing keepalive timeouts, or a target-side resource exhaustion causing connection tears. The correct response is to correlate the timestamp of recovery events (via `dmesg`) with network interface error counters (`ip -s link show`), switch port statistics, and target-side logs, then resolve the root cause before tuning `MaxBurstLength` or `MaxOutstandingR2T` further, since larger burst state amplifies the latency impact of each recovery event.

The relationship between these tuning parameters and the recovery architecture is ultimately a contract: the initiator and target negotiate, at login, the maximum in-flight state they are both prepared to manage. Setting that state too low wastes the fabric. Setting it too high makes recovery slow and resource-intensive. The practitioner's job is to find the equilibrium point where the fabric stays full, the target's buffers are not exhausted, and a single connection failure causes a recovery measured in tens of milliseconds rather than seconds.
