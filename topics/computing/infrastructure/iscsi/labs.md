# Operational Verification Labs: iSCSI

## Objective & Environment Setup

iSCSI (Internet Small Computer System Interface) extends the SCSI block-level protocol over TCP/IP networks, enabling remote storage systems to present block devices to initiators as if they were locally attached disks. Unlike NFS or SMB, which operate at the filesystem layer, iSCSI delivers raw block devices that the initiator can partition, format, and mount according to local requirements. This architecture underpins modern SAN (Storage Area Network) deployments, virtualization platforms, and Kubernetes persistent volume backends.

The operational discipline required to maintain production iSCSI infrastructure extends beyond simple configuration. A practitioner must understand session-layer state machines, multipath failover mechanics, TCP congestion behavior under load, and the subtle interactions between the iSCSI protocol's SCSI Command Descriptor Block (CDB) encapsulation and underlying network transport. This lab sequence builds verification competency through live introspection, saturation profiling, and controlled fault injection using the native Linux Open-iSCSI initiator stack, kernel `dm-multipath` subsystem, and production-grade diagnostic tools.

The verification environment requires a Linux system running kernel 5.10 or later with the `iscsi_tcp` and `libiscsi` kernel modules loaded. You will interact with both initiator (client) and target (server) components, though primary focus remains on initiator-side diagnostics as this represents the operational failure domain most practitioners encounter. The target can be a hardware SAN, a software-defined storage appliance running TGT (SCSI Target Framework) or LIO (Linux-IO Target), or a simulated loopback target for isolated lab work.

Begin by installing the Open-iSCSI initiator tools and multipath-tools package. On Debian-derived systems, execute `apt-get install open-iscsi multipath-tools sg3-utils lsscsi`. On RHEL-derived systems, use `yum install iscsi-initiator-utils device-mapper-multipath sg3-utils lsscsi`. The `sg3-utils` package provides SCSI diagnostic commands like `sg_inq` and `sg_readcap` that query device parameters through the SCSI Generic (`sg`) interface. The `lsscsi` utility maps SCSI addresses to block device names, essential for correlating kernel messages with physical storage paths.

Verify that the iSCSI initiator service is installed but not yet started. Check the systemd unit status with `systemctl status iscsid.service` and `systemctl status iscsi.service`. The `iscsid` daemon manages session state and handles connection recovery, while the `iscsi.service` unit ensures automatic login to configured targets at boot. Before starting these services, inspect the initiator's IQN (iSCSI Qualified Name) in `/etc/iscsi/initiatorname.iscsi`. This globally unique identifier follows the format `iqn.YYYY-MM.reverse.domain:identifier` and serves as the initiator's identity during target authentication. If the file is missing or contains a default placeholder, generate a unique IQN with `echo "InitiatorName=$(iscsi-iname)" | tee /etc/iscsi/initiatorname.iscsi`.

The network path between initiator and target must support Jumbo Frames (MTU 9000) to minimize CPU overhead and maximize throughput for large block I/O workloads. Verify the MTU of the storage-facing interface with `ip link show dev eth1` (replace `eth1` with your storage NIC). If the MTU is 1500, increase it to 9000 with `ip link set dev eth1 mtu 9000`, then persist this change in your network configuration (e.g., `/etc/network/interfaces` or NetworkManager). Confirm end-to-end MTU with a ping test: `ping -M do -s 8972 -c 3 <target_ip>`. The payload size of 8972 bytes plus 28 bytes of IP and ICMP headers equals 9000 bytes. If fragmentation occurs, intermediate switches or the target NIC do not support Jumbo Frames.

For this lab, assume a target appliance at IP address `192.168.100.10` exposing an IQN of `iqn.2025-01.com.storage:san.array01`. This target presents two LUNs (Logical Unit Numbers): LUN 0 as a 100 GB block device and LUN 1 as a 50 GB device. The target supports multiple network paths: a primary path on `192.168.100.10` and a secondary path on `192.168.101.10`, both terminating at the same storage controller. This dual-path topology enables multipath failover verification in Exercise 3.

Start the iSCSI daemon with `systemctl start iscsid.service`. The daemon listens on the local IPC socket `/var/run/iscsid.socket` for administrative commands issued by the `iscsiadm` utility. Enable the daemon to start at boot with `systemctl enable iscsid.service`. Do not yet enable `iscsi.service`; automatic login will be configured after manual discovery and session validation.

The operational verification workflow follows a three-phase methodology. First, establish baseline visibility into session state, connection parameters, and device mappings through passive inspection commands. Second, apply controlled load via `fio` (Flexible I/O Tester) to profile throughput saturation, latency distribution, and queue depth scaling. Third, inject faults through network disruption, path failure, and target reboot to validate multipath failover, session recovery, and I/O error handling. Each phase builds diagnostic muscle memory, ensuring practitioners can distinguish transient network anomalies from storage-layer failures in production incidents.

## Exercise 1: Live State & Internal Subsystem Inspection

The first operational discipline is passive state inspection: reading kernel data structures, parsing session tables, and correlating iSCSI protocol state with underlying block device mappings without altering system behavior. This capability is foundational because production troubleshooting begins with observation, not intervention.

Begin by discovering available targets from the known storage appliance. Execute `iscsiadm --mode discovery --type sendtargets --portal 192.168.100.10`. The `sendtargets` discovery method queries the target's TCP port 3260 (the default iSCSI port) and retrieves a list of available IQNs and portal addresses. The output resembles:

```
192.168.100.10:3260,1 iqn.2025-01.com.storage:san.array01
192.168.101.10:3260,1 iqn.2025-01.com.storage:san.array01
```

Each line specifies a portal address, a TPGT (Target Portal Group Tag, here `1`), and the target IQN. The presence of two portal addresses confirms that the target supports multipath access. The discovery data is cached in `/var/lib/iscsi/nodes/<target_iqn>/<portal_address>,<port>,<tpgt>/default`, which contains connection parameters, authentication credentials (if CHAP is configured), and session recovery timers.

Log in to the target via the primary portal with `iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --login`. The initiator daemon establishes a TCP connection, performs iSCSI Full Feature Phase negotiation, and transitions the session to the logged-in state. Upon successful login, the kernel's SCSI mid-layer enumerates attached LUNs and creates corresponding block devices in `/dev/`. Observe kernel messages in real time with `journalctl -kf` or `dmesg -w`. You should see:

```
scsi host3: iSCSI Initiator over TCP/IP
scsi 3:0:0:0: Direct-Access     VENDOR   MODEL            REV  PQ: 0 ANSI: 5
sd 3:0:0:0: [sdc] 209715200 512-byte logical blocks: (107 GB/100 GiB)
sd 3:0:0:0: [sdc] Write Protect is off
sd 3:0:0:0: [sdc] Cache data unavailable
sd 3:0:0:0: [sdc] Assuming drive cache: write through
sd 3:0:0:0: [sdc] Attached SCSI disk
```

The SCSI address `3:0:0:0` decodes as `host:channel:target:lun`. Here, host 3 corresponds to the iSCSI HBA (Host Bus Adapter) emulated by the kernel module, channel 0 is unused in iSCSI, target 0 represents the target IQN, and LUN 0 is the first logical unit. The block device name `sdc` is assigned dynamically; use `lsscsi` to establish a stable SCSI-to-device mapping:

```
lsscsi
```

Output:

```
[3:0:0:0]    disk    VENDOR   MODEL            REV   /dev/sdc
[3:0:0:1]    disk    VENDOR   MODEL            REV   /dev/sdd
```

LUN 1 appears as `/dev/sdd`. These device names are kernel-assigned and may change across reboots or if other SCSI devices are hotplugged. For stable device references, use UUIDs or WWIDs (World Wide Identifiers). Query the WWID with `scsi_id --whitelisted --device=/dev/sdc`. The WWID encodes vendor, model, and serial information, and remains constant regardless of device name changes.

Inspect active iSCSI sessions with `iscsiadm --mode session`. The output lists each active session by target IQN and portal:

```
tcp: [1] 192.168.100.10:3260,1 iqn.2025-01.com.storage:san.array01 (non-flash)
```

The bracketed number `[1]` is the session identifier (SID), used in subsequent `iscsiadm` commands to reference this specific session. The `(non-flash)` tag indicates the session was manually logged in rather than restored from flash (persistent boot configuration). To display detailed session parameters, execute `iscsiadm --mode session --sid 1 --print 1`. This dumps connection state including negotiated values for `MaxRecvDataSegmentLength`, `MaxBurstLength`, `FirstBurstLength`, and timeouts like `Nop-Out Interval` and `Nop-Out Timeout`. These parameters govern iSCSI PDU (Protocol Data Unit) segmentation and keepalive behavior.

Critical parameters include `node.session.timeo.replacement_timeout`, which defines how long the initiator waits for a lost connection to be re-established before failing I/O requests back to the application layer. The default is 120 seconds. Query this value with `iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --op show | grep replacement_timeout`. For latency-sensitive workloads, reduce this to 15–30 seconds to accelerate failover, but only if multipath is configured to handle path failures gracefully.

Examine the TCP connection state underlying the iSCSI session with `ss -tnp | grep :3260`. The output shows established TCP sessions between the initiator's ephemeral port and the target's port 3260:

```
ESTAB  0      0      192.168.100.50:47832  192.168.100.10:3260   users:(("iscsid",pid=1234,fd=8))
```

The `ss` command reports zero bytes in the send queue (`0` in the second column) and zero bytes in the receive queue (`0` in the third column), indicating no backlog. During I/O activity, these queues will fluctuate. Use `ss -tipm` to display TCP congestion control state, including the congestion window (`cwnd`), slow start threshold (`ssthresh`), and round-trip time (`rtt`). For a low-latency datacenter fabric, expect RTT below 1 ms and a large `cwnd` (hundreds of packets).

Correlate the iSCSI session with its kernel SCSI host by examining `/sys/class/iscsi_session/sessionX/`. Each session has a dedicated sysfs directory where `X` is the SID. Navigate with `cd /sys/class/iscsi_session/session1/device/` and execute `ls -l`. You will find symbolic links to the SCSI host, connection, and target portal. The `targetname` file contains the IQN: `cat targetname` yields `iqn.2025-01.com.storage:san.array01`. The session's current state is in `state`: `cat state` should return `LOGGED_IN`. During recovery, this transitions to `RECOVERY` or `FREE` (session terminated).

Inspect connection-level statistics with `cat /sys/class/iscsi_connection/connection1:0/stats/*`. The `connection1:0` naming format combines the session ID (`1`) and connection ID (`0`). Files in this directory expose counters for transmitted and received iSCSI PDUs, digest errors, and timeout events. Key counters include `txdata_octets` (bytes sent), `rxdata_octets` (bytes received), and `digest_err` (CRC failures). A non-zero `digest_err` count indicates network corruption or faulty hardware; investigate with `ethtool -S eth1` to check for NIC-level CRC errors and frame alignment issues.

Log in to the secondary portal to establish a second session: `iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.101.10:3260 --login`. The kernel now presents duplicate SCSI devices for each LUN—one per path. Without multipath, the system sees four devices (`sdc`, `sdd`, `sde`, `sdf`) corresponding to two LUNs across two sessions. Using both paths simultaneously without multipath-tools risks data corruption because the filesystem or application is unaware that multiple device names refer to the same underlying LUN.

Enable device-mapper multipath to aggregate paths. Edit `/etc/multipath.conf` to define the storage array's device characteristics. A minimal configuration for the lab target:

```
defaults {
    user_friendly_names yes
    find_multipaths yes
    path_grouping_policy multibus
    failback immediate
}

devices {
    device {
        vendor "VENDOR"
        product "MODEL"
        path_selector "service-time 0"
        path_checker tur
        features "1 queue_if_no_path"
        hardware_handler "0"
        prio const
        rr_weight uniform
        no_path_retry 5
    }
}
```

The `path_grouping_policy multibus` directive places all paths in a single active priority group, distributing I/O across both paths via round-robin. The `path_selector "service-time 0"` algorithm routes I/O to the path with the lowest estimated service time, balancing load dynamically. The `path_checker tur` setting uses the SCSI Test Unit Ready command to verify path health. The `features "1 queue_if_no_path"` option queues I/O internally when all paths fail, preventing immediate I/O errors during transient outages. The `no_path_retry 5` parameter retries path recovery five times before marking the device as failed.

Restart the multipath daemon with `systemctl restart multipathd.service`. The daemon scans existing SCSI devices, identifies those with matching WWIDs across multiple paths, and creates aggregate multipath devices in `/dev/mapper/`. Query the multipath topology with `multipath -ll`. The output displays a tree structure:

```
mpatha (36001405abcdef1234567890abcdef12) dm-0 VENDOR,MODEL
size=100G features='1 queue_if_no_path' hwhandler='0' wp=rw
|-+- policy='service-time 0' prio=1 status=active
| `- 3:0:0:0 sdc 8:32 active ready running
`-+- policy='service-time 0' prio=1 status=enabled
  `- 4:0:0:0 sde 8:64 active ready running
```

The multipath device `mpatha` is an alias for `dm-0` (device-mapper device 0). The WWID `36001405...` uniquely identifies the LUN. Two paths are active: `sdc` via session 1 and `sde` via session 2. The `status=active` tag indicates the path is currently servicing I/O, while `status=enabled` means the path is healthy but not actively used in this I/O cycle (due to round-robin scheduling). Create a filesystem on the multipath device with `mkfs.ext4 /dev/mapper/mpatha` and mount it to `/mnt/iscsi`. All subsequent I/O flows through the device-mapper layer, which transparently distributes requests across both paths and handles failover.

Verify that I/O to the mounted filesystem generates traffic on both network paths. Open two terminal windows. In the first, start a continuous write test: `dd if=/dev/zero of=/mnt/iscsi/testfile bs=1M count=10000`. In the second, monitor per-interface transmit rates with `ip -s link show dev eth1 && ip -s link show dev eth2` in a loop or use `watch -n 1 'ip -s -h link'`. The `-h` flag displays human-readable byte counts. Both interfaces should show increasing TX (transmit) byte counters, confirming that the multipath layer is distributing I/O.

Inspect the device-mapper table for `mpatha` with `dmsetup table mpatha`. The output is a space-separated list of sector ranges and target specifications:

```
0 209715200 multipath 2 0 1 1 service-time 0 2 1 8:32 1 1 8:64 1
```

This cryptic line decodes as: starting at sector 0, covering 209715200 sectors (100 GiB), using the `multipath` target with two priority groups (`2 0`), each containing one path (`1 1`), mapped to major:minor pairs `8:32` (sdc) and `8:64` (sde). The `service-time 0` token specifies the path selection algorithm. Understanding this table is critical for debugging path failures, as `dmsetup` commands can manually suspend, resume, or reload target mappings during maintenance.

Query per-path I/O statistics with `dmsetup status mpatha`. The output includes each path's current state, I/O count, and failure count:

```
0 209715200 multipath 2 0 1 1 1 8:32 A 0 1 0 8:64 A 0
```

The `A` indicates an active path. If a path fails, it transitions to `F` (failed). The numeric fields following each path represent the number of I/O errors and path-specific metadata. This status output is the first diagnostic to check when applications report I/O timeouts or degraded performance, as it immediately reveals which paths are healthy and which have failed.

Capture iSCSI protocol exchanges with `tcpdump` to observe low-level PDU flow. Start a capture on the storage interface: `tcpdump -i eth1 -w /tmp/iscsi.pcap -s 96 port 3260`. The `-s 96` option captures only the first 96 bytes of each packet—sufficient to inspect iSCSI and TCP headers without saving bulk data payloads. Perform a small read operation: `dd if=/dev/mapper/mpatha of=/dev/null bs=4k count=10`. Stop the capture and analyze with `tcpdump -r /tmp/iscsi.pcap -nn -X | less`. Look for iSCSI PDU opcodes in the packet payload: `0x01` for SCSI Command, `0x21` for SCSI Response, `0x25` for SCSI Data-In. The hexdump shows the encapsulated SCSI CDB (Command Descriptor Block) bytes, such as `0x28` for READ(10) or `0x2A` for WRITE(10), followed by LBA (Logical Block Address) and transfer length fields.

For detailed SCSI command tracing, enable kernel tracing via debugfs. Mount debugfs if not already mounted: `mount -t debugfs none /sys/kernel/debug`. Enable SCSI command logging for the iSCSI host with `echo 1 > /sys/kernel/debug/tracing/events/scsi/scsi_dispatch_cmd_start/enable` and `echo 1 > /sys/kernel/debug/tracing/events/scsi/scsi_dispatch_cmd_done/enable`. Perform I/O and read the trace buffer: `cat /sys/kernel/debug/tracing/trace`. Each SCSI command is logged with its opcode, LBA, transfer length, and latency. This low-level trace is invaluable for diagnosing command-level timeouts or unexpected SCSI sense codes (error conditions returned by the target).

Finally, capture a snapshot of the entire iSCSI subsystem state for offline analysis. Collect session data with `iscsiadm --mode session --print 1 > /tmp/iscsi_session.txt`, multipath topology with `multipath -ll > /tmp/mpath_topology.txt`, SCSI device details with `lsscsi -v > /tmp/scsi_devices.txt`, and kernel messages with `journalctl -k --since "10 minutes ago" > /tmp/kernel_log.txt`. Archive these files together: `tar -czf iscsi_state_$(date +%F_%T).tar.gz /tmp/iscsi_*.txt /tmp/mpath_topology.txt /tmp/scsi_devices.txt /tmp/kernel_log.txt`. This artifact forms a comprehensive operational baseline, essential for correlating pre-failure state with post-failure symptoms in production incidents.

## Exercise 2: Benchmarking & Saturation Profiling

Performance characterization of iSCSI storage requires systematic load generation across multiple dimensions: block size, queue depth, read/write ratio, and access pattern (sequential vs. random). Unlike local NVMe, where latency is measured in microseconds and dominated by device physics, iSCSI latency is primarily network RTT plus target processing time. The practitioner must distinguish bottlenecks in the initiator's TCP stack, the network fabric, the target's controller, and the backing disk subsystem.

Install `fio` (Flexible I/O Tester), the industry-standard block I/O benchmark: `apt-get install fio` or `yum install fio`. Verify installation with `fio --version`, which should report version 3.30 or later for full NVMe and io_uring support (though io_uring is not applicable to iSCSI block devices, the tool's feature set remains relevant).

Begin with a sequential write saturation test to establish maximum throughput. Create a fio job file `/tmp/iscsi_seq_write.fio`:

```
[global]
ioengine=libaio
direct=1
bs=1m
iodepth=32
runtime=60
time_based
group_reporting

[seqwrite]
rw=write
filename=/dev/mapper/mpatha
numjobs=4
```

This job spawns four threads, each issuing asynchronous I/O (`libaio`) with a queue depth of 32 against the multipath device. The `direct=1` flag bypasses the page cache, ensuring I/O reaches the iSCSI layer. The 1 MB block size (`bs=1m`) maximizes per-I/O efficiency by amortizing protocol overhead across large transfers. Execute with `fio /tmp/iscsi_seq_write.fio`. The output reports aggregate bandwidth, IOPS (I/O Operations Per Second), and latency distribution:

```
  write: IOPS=950, BW=950MiB/s (996MB/s)(55.7GiB/60001msec)
    slat (usec): min=12, max=2340, avg=45.3, stdev=78.2
    clat (msec): min=8, max=234, avg=134.5, stdev=23.4
     lat (msec): min=8, max=234, avg=134.5, stdev=23.4
```

The `slat` (submission latency) measures time from fio submitting the I/O to the kernel until the kernel accepts it into the block layer—typically sub-millisecond. The `clat` (completion latency) spans from kernel acceptance until I/O completion, encompassing network RTT, target processing, and disk write time. The average completion latency of 134.5 ms is dominated by target-side disk seeks and write cache flushing. The bandwidth of 950 MiB/s approaches the 10 Gigabit Ethernet line rate (approximately 1.19 GB/s after protocol overhead), indicating the network is saturated.

Confirm network saturation by monitoring interface statistics during the test. In a separate terminal, run `watch -n 1 'ip -s -h link show dev eth1'`. The TX rate should stabilize near 1.2 GB/s. If bandwidth is significantly lower, suspect TCP congestion control, MTU mismatches, or packet loss. Check for dropped packets with `ip -s link show dev eth1 | grep drop`. Non-zero RX-DRP or TX-DRP counters indicate the NIC's ring buffers overflowed, causing packet loss and TCP retransmissions. Increase ring buffer sizes with `ethtool -G eth1 rx 4096 tx 4096` (if the NIC supports larger rings) and re-run the test.

Profile latency sensitivity by varying queue depth. Create a series of fio jobs with `iodepth` values of 1, 4, 16, 64, and 128. For each depth, record the average completion latency and IOPS. Plot latency vs. queue depth; you should observe a near-linear increase in latency as queue depth grows, reflecting queuing delay both in the kernel's block layer and the target's command queue. At low queue depths (1–4), latency is primarily network RTT plus target seek time. At high depths (64+), latency increases due to queuing at the target's SCSI command scheduler (typically CFQ or deadline).

Isolate network latency by measuring unloaded RTT with `ping -c 100 192.168.100.10` and computing the minimum RTT. For a datacenter fabric, expect 0.2–0.5 ms. Add this to the target's intrinsic disk latency (for spinning disks, 5–10 ms; for SSDs, 0.1–0.5 ms) to estimate the floor latency. If measured `clat` significantly exceeds this sum, investigate TCP retransmissions with `netstat -s | grep retrans` or use `ss -ti` to inspect per-connection retransmission counts.

Test random read IOPS, which stress the target's ability to handle concurrent small-block requests. Create `/tmp/iscsi_rand_read.fio`:

```
[global]
ioengine=libaio
direct=1
bs=4k
iodepth=64
runtime=60
time_based
group_reporting

[randread]
rw=randread
filename=/dev/mapper/mpatha
numjobs=8
```

This job issues 4 KB random reads with eight threads and a queue depth of 64 per thread, generating high IOPS load. Execute with `fio /tmp/iscsi_rand_read.fio`. On a spinning-disk backend, expect IOPS in the range of 100–300 due to seek limitations. On an all-flash array, IOPS may reach 10,000–50,000. The key metric is latency consistency: examine the `clat` percentiles (`clat (msec): ... 99.00th=[28]`) to identify tail latency. The 99th percentile represents the worst 1% of I/Os, critical for latency-sensitive applications like databases.

Capture per-path IOPS distribution by enabling block layer tracing. Execute `echo 1 > /sys/block/dm-0/trace/enable` (replace `dm-0` with your multipath device). Run the fio test, then read the trace with `cat /sys/block/dm-0/trace/trace`. Each line logs a block I/O event with timestamps, SCSI addresses, and sector ranges. Parse this output with `awk` to count I/Os per underlying device (sdc vs. sde) and verify the multipath layer is balancing load. If one path handles disproportionately more I/Os, suspect an asymmetric target configuration (e.g., one portal preferred via ALUA—Asymmetric Logical Unit Access).

Profile CPU overhead by running `perf stat -p $(pgrep -x fio)` during a fio test. The output reports CPU cycles, instructions, and cache misses. High cache miss rates (L1-dcache-load-misses exceeding 5%) indicate excessive memory copying in the iSCSI or block layer. Investigate with `perf record -g -p $(pgrep -x fio)` and `perf report` to identify hot functions. Common bottlenecks include `memcpy` in the iSCSI data path, TCP checksum computation, and SCSI mid-layer command allocation.

Measure the impact of TCP congestion control algorithms. The default algorithm on modern kernels is `cubic`, optimized for high-bandwidth, high-latency WANs. For low-latency datacenters, switch to `bbr` (Bottleneck Bandwidth and RTT): `sysctl -w net.ipv4.tcp_congestion_control=bbr`. Re-run the sequential write test and compare bandwidth. BBR often improves throughput by 10–20% by avoiding buffer bloat and minimizing retransmissions. Verify the active algorithm per connection with `ss -ti | grep cubic` or `ss -ti | grep bbr`.

Stress the multipath failover logic by generating I/O while monitoring path state. Start a continuous write test: `fio --name=stress --rw=write --bs=1m --iodepth=32 --direct=1 --filename=/dev/mapper/mpatha --runtime=600 --time_based &`. In another terminal, watch multipath status: `watch -n 1 'multipath -ll'`. Observe that both paths remain active. Now, in Exercise 3, we will inject faults to trigger failover, but here we establish baseline behavior under load: both paths should show `status=active` or `status=enabled` without transitioning to `status=failed`.

Profile network throughput limits by comparing iSCSI performance against a raw TCP stream. Use `iperf3` to measure network capacity: `iperf3 -c 192.168.100.10 -t 60 -P 4`. The `-P 4` flag spawns four parallel TCP streams, simulating multiple iSCSI sessions. Compare the iperf3 bandwidth with fio's measured throughput. If iperf3 achieves 1.2 GB/s but fio only 800 MB/s, the bottleneck lies in iSCSI protocol overhead, TCP segmentation offload (TSO) settings, or target-side processing. Enable TSO on the NIC with `ethtool -K eth1 tso on` and re-test.

Capture system-wide I/O statistics with `iostat -xz 1` during the fio test. Focus on the multipath device's `%util` metric, which estimates device saturation. A value consistently at or near 100% indicates the storage backend is saturated. Cross-check with `await` (average wait time), which should correlate with fio's `clat`. If `%util` is low but `await` is high, suspect network issues rather than storage saturation.

Finally, document performance baselines in a structured format for future comparison. Create a table with columns: block size, queue depth, pattern (sequential/random), read/write ratio, IOPS, bandwidth, average latency, 99th percentile latency, and CPU utilization. Collect data across at least eight test cases (e.g., 4k randread, 4k randwrite, 1m seqread, 1m seqwrite, each at low and high queue depths). These baselines enable regression detection when infrastructure changes occur, such as firmware upgrades, network reconfigurations, or storage array expansions.

## Exercise 3: Fault Injection & Recovery Analysis

Production iSCSI environments must tolerate failures at multiple layers: network link loss, target controller failover, initiator daemon crashes, and transient congestion-induced packet drops. This exercise systematically injects faults while monitoring session recovery, multipath failover, and I/O error propagation to validate resilience.

Begin by establishing a steady-state I/O workload. Start a long-running fio job: `fio --name=resilience --rw=randrw --rwmixread=70 --bs=4k --iodepth=32 --direct=1 --filename=/dev/mapper/mpatha --runtime=3600 --time_based &`. This mixed read/write workload (70% reads) simulates database-like access patterns. Monitor application-visible I/O errors with `journalctl -kf | grep -E 'I/O error|failed|offline'` in a dedicated terminal.

Inject a network partition by disabling one interface. Identify which interface corresponds to the primary iSCSI session with `ip route get 192.168.100.10`. If the output shows `dev eth1`, then `eth1` carries the primary path. Disable it: `ip link set dev eth1 down`. Within seconds, observe kernel messages indicating connection loss:

```
connection1:0: detected conn error (1011)
session1: session recovery timed out after 15 secs
sd 3:0:0:0: rejecting I/O to offline device
```

The connection error code `1011` corresponds to `ISCSI_ERR_CONN_FAILED`. The session recovery timer (`node.session.timeo.replacement_timeout`, default 120 seconds) begins counting. During this window, the multipath layer redirects I/O to the surviving path on `eth2`. Verify with `multipath -ll`:

```
mpatha (36001405...) dm-0 VENDOR,MODEL
|-+- policy='service-time 0' prio=1 status=enabled
| `- 3:0:0:0 sdc 8:32 failed faulty offline
`-+- policy='service-time 0' prio=1 status=active
  `- 4:0:0:0 sde 8:64 active ready running
```

The first path (`sdc`) transitions to `failed faulty offline`, while the second path (`sde`) becomes `active`. The fio job continues without I/O errors because the multipath layer transparently reroutes requests. Check fio's output for latency spikes: the `clat` distribution may show a temporary increase during failover as queued I/Os drain and the path selection algorithm converges.

Re-enable the interface: `ip link set dev eth1 up`. The iSCSI daemon detects the restored network and attempts to re-login to the target. Monitor with `journalctl -u iscsid.service -f`. After a few seconds, the session transitions back to `LOGGED_IN` and the path is reinstated. Verify with `multipath -ll`, which now shows both paths active again. The multipath daemon's `failback immediate` policy (configured in Exercise 1) causes I/O to immediately rebalance across both paths.

Inject a target-side fault by simulating a controller reboot. If you control the target, execute a reboot command remotely. If using a loopback target on the same host for lab purposes, restart the target daemon: `systemctl restart tgt.service` or `systemctl restart rtslib-fb-targetctl.service` (depending on whether you use TGT or LIO). All active iSCSI sessions terminate abruptly, and the initiator logs connection errors. Unlike the single-path failure, both paths fail simultaneously, exhausting the multipath layer's available paths.

During this dual-path failure, the multipath device's `queue_if_no_path` feature (configured in Exercise 1) queues I/O requests internally rather than failing them immediately. Verify by checking `dmsetup status mpatha`:

```
0 209715200 multipath 2 0 0 0 0 8:32 F 0 0 8:64 F 0
```

Both paths show `F` (failed). The fio job appears to hang as I/O requests queue in the device-mapper layer. This behavior is critical for filesystems like XFS, which rely on the block layer to queue I/Os during transient outages rather than propagating errors that trigger filesystem-level aborts.

After the target finishes rebooting and the iSCSI service starts, the initiator detects the restored portal and re-establishes sessions. The queued I/Os drain to the target, and the fio job resumes. Monitor the recovery duration by noting the timestamp of the last kernel error message before recovery and the first successful I/O completion afterward. Typical recovery takes 10–30 seconds depending on `replacement_timeout` and target boot time.

Inject packet loss to simulate transient congestion. Use `tc` (Traffic Control) to drop 5% of packets on the storage interface: `tc qdisc add dev eth1 root netem loss 5%`. This causes TCP retransmissions, increasing I/O latency. Observe the effect with `ss -ti | grep retrans`, which shows non-zero retransmit counts. The fio job continues but reports elevated `clat` values, potentially doubling average latency. Remove the packet loss: `tc qdisc del dev eth1 root`. Latency returns to baseline within seconds as TCP congestion control algorithms recover.

Test the initiator daemon's resilience by killing the `iscsid` process. Execute `systemctl stop iscsid.service`. Existing sessions persist because the kernel's iSCSI module maintains session state independently of the userspace daemon. However, session recovery and re-login logic requires the daemon. Verify that I/O continues uninterrupted by checking the fio job, which should show no errors. Now inject a path failure by disabling `eth1` again: `ip link set dev eth1 down`. Without the daemon, the session cannot recover, and after `replacement_timeout` expires, the path fails permanently. Re-enable `eth1` and restart the daemon: `systemctl start iscsid.service`. The daemon re-scans and re-logins to the target, restoring the path.

Simulate a SCSI command timeout by suspending the target's response processing. This is difficult to achieve without target-side instrumentation, but you can approximate it by introducing extreme latency with `tc qdisc add dev eth1 root netem delay 5000ms`. This adds a 5-second delay to all packets, exceeding the typical SCSI command timeout (`node.session.timeo.replacement_timeout` divided by the number of retry attempts). The kernel logs SCSI command timeouts:

```
sd 3:0:0:0: [sdc] tag#12 FAILED Result: hostbyte=DID_TIME_OUT driverbyte=DRIVER_OK
sd 3:0:0:0: [sdc] tag#12 CDB: Read(10) 28 00 00 12 34 56 00 00 08 00
```

The `DID_TIME_OUT` result code indicates the SCSI layer gave up waiting for the command to complete. The multipath layer retries the I/O on the alternate path. Remove the delay: `tc qdisc del dev eth1 root`.

Validate that the multipath `no_path_retry` parameter prevents indefinite I/O queueing. Edit `/etc/multipath.conf` to set `no_path_retry 0`, which disables queueing when no paths are available. Reload the configuration: `systemctl reload multipathd.service`. Disable both interfaces simultaneously: `ip link set dev eth1 down && ip link set dev eth2 down`. The fio job immediately reports I/O errors as the multipath layer returns `EIO` to the application. Re-enable the interfaces and restore `no_path_retry 5` to revert to the original behavior.

Inject a split-brain scenario by manually logging in to the target without using multipath. This simulates a misconfiguration where two initiators (or the same initiator via different sessions) access the same LUN without coordination. Create a second session manually: `iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --login --name node.session.nr_sessions`. The kernel creates a third session and maps the LUN to a new device name, say `/dev/sdf`. Now, write to `/dev/sdf` directly: `dd if=/dev/urandom of=/dev/sdf bs=1M count=100`. The target's LUN receives writes from both the multipath device (`/dev/mapper/mpatha`, which aggregates `sdc` and `sde`) and the standalone device `/dev/sdf`. This causes data corruption as the filesystem or application using `mpatha` is unaware of writes via `sdf`. Immediately log out of the rogue session: `iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --logout`. This exercise underscores the critical importance of centralized multipath management and avoiding manual session manipulation in production.

Capture diagnostic data during a fault injection cycle for post-mortem analysis. Before inducing a failure, start a packet capture: `tcpdump -i any -w /tmp/fault_inject.pcap port 3260 &`. Trigger the fault (e.g., disable `eth1`), allow recovery to complete, and stop the capture. Analyze with Wireshark or `tshark -r /tmp/fault_inject.pcap -Y iscsi`. Look for iSCSI Logout PDUs, connection close sequences, and the timing of re-login PDUs after recovery. This trace provides frame-by-frame visibility into protocol-level recovery mechanics.

Test the impact of MTU mismatches by reducing the initiator's MTU: `ip link set dev eth1 mtu 1500`. If the target and intermediate switches still use MTU 9000, fragmentation occurs. Generate large I/Os: `fio --name=mtu_test --rw=write --bs=128k --iodepth=1 --direct=1 --filename=/dev/mapper/mpatha --size=1G`. Monitor for ICMP fragmentation-needed messages with `tcpdump -i eth1 icmp` and check for retransmissions with `netstat -s | grep retrans`. Throughput degrades significantly due to fragmentation overhead. Restore the original MTU: `ip link set dev eth1 mtu 9000`.

Finally, validate CHAP authentication recovery. If CHAP is configured (username and password set in `/etc/iscsi/nodes/.../default`), change the CHAP secret on the target to a mismatched value. Log out and attempt to log back in: `iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --logout && iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --login`. The login fails with an authentication error. Kernel logs show `Login failed to authenticate with target`. Restore the correct CHAP secret and retry. This confirms that authentication failures are immediately visible and do not degrade into silent session establishment with no security.

## Diagnostic Cheat Sheet & Verification Checklist

This reference consolidates essential commands and verification steps for rapid operational response in production iSCSI environments.

### Session and Connection State

Inspect all active iSCSI sessions with target IQNs and portals:

```bash
iscsiadm --mode session
```

Display detailed parameters for a specific session (replace `1` with the session ID):

```bash
iscsiadm --mode session --sid 1 --print 1 | less
```

Query the current state of a session via sysfs:

```bash
cat /sys/class/iscsi_session/session1/state
```

Expected output for a healthy session: `LOGGED_IN`. During recovery: `RECOVERY`.

Check connection-level statistics for errors and digest failures:

```bash
cat /sys/class/iscsi_connection/connection1:0/stats/*
```

Examine TCP connection state for an iSCSI portal:

```bash
ss -tnp | grep :3260
ss -tipm | grep :3260
```

Key metrics: `cwnd` (congestion window), `rtt` (round-trip time), `retrans` (retransmission count).

### Multipath Topology and Path Health

Display multipath device topology with path states:

```bash
multipath -ll
```

Show device-mapper status with per-path I/O statistics:

```bash
dmsetup status mpatha
```

Path states: `A` (active), `E` (enabled), `F` (failed). Non-zero failure counts indicate recent path errors.

Verify that the multipath daemon is running and reload configuration:

```bash
systemctl status multipathd.service
systemctl reload multipathd.service
```

Manually fail a path for testing:

```bash
multipathd -k'fail path sdc'
```

Restore the path:

```bash
multipathd -k'reinstate path sdc'
```

### SCSI Device Mapping and Identification

List SCSI devices with addresses and block device names:

```bash
lsscsi -v
```

Query the WWID of a block device for stable identification:

```bash
scsi_id --whitelisted --device=/dev/sdc
```

Inspect SCSI device parameters (capacity, block size, vendor):

```bash
sg_inq /dev/sdc
sg_readcap -l /dev/sdc
```

### Network Path Verification

Verify MTU configuration on storage interfaces:

```bash
ip link show dev eth1
```

Test end-to-end MTU with ping (9000-byte MTU requires 8972-byte payload):

```bash
ping -M do -s 8972 -c 3 192.168.100.10
```

Monitor per-interface transmit and receive statistics:

```bash
ip -s -h link show dev eth1
watch -n 1 'ip -s -h link'
```

Check for packet drops and errors:

```bash
ethtool -S eth1 | grep -E 'drop|error|crc'
```

Measure network latency to the target:

```bash
ping -c 100 192.168.100.10 | tail -1
```

### TCP Congestion Control and Performance Tuning

Display the active TCP congestion control algorithm:

```bash
sysctl net.ipv4.tcp_congestion_control
```

Switch to BBR for low-latency datacenters:

```bash
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

Inspect per-connection congestion state:

```bash
ss -ti | grep -A 10 :3260
```

Enable TCP segmentation offload on the NIC:

```bash
ethtool -K eth1 tso on
```

Increase NIC ring buffer sizes to reduce packet drops:

```bash
ethtool -G eth1 rx 4096 tx 4096
```

### Performance Benchmarking

Run a sequential write throughput test:

```bash
fio --name=seqwrite --rw=write --bs=1m --iodepth=32 --direct=1 --filename=/dev/mapper/mpatha --runtime=60 --time_based --numjobs=4
```

Run a random read IOPS test:

```bash
fio --name=randread --rw=randread --bs=4k --iodepth=64 --direct=1 --filename=/dev/mapper/mpatha --runtime=60 --time_based --numjobs=8
```

Monitor real-time I/O statistics:

```bash
iostat -xz 1
```

Focus on `%util` (device saturation) and `await` (average wait time) for the multipath device.

Profile CPU overhead during I/O:

```bash
perf stat -p $(pgrep -x fio)
```

### Protocol and Kernel Tracing

Capture iSCSI PDU exchanges:

```bash
tcpdump -i eth1 -w /tmp/iscsi.pcap -s 96 port 3260
tcpdump -r /tmp/iscsi.pcap -nn -X | less
```

Enable SCSI command tracing:

```bash
echo 1 > /sys/kernel/debug/tracing/events/scsi/scsi_dispatch_cmd_start/enable
echo 1 > /sys/kernel/debug/tracing/events/scsi/scsi_dispatch_cmd_done/enable
cat /sys/kernel/debug/tracing/trace
```

Disable tracing after collection:

```bash
echo 0 > /sys/kernel/debug/tracing/events/scsi/scsi_dispatch_cmd_start/enable
echo 0 > /sys/kernel/debug/tracing/events/scsi/scsi_dispatch_cmd_done/enable
```

### Fault Injection and Recovery Testing

Disable a network interface to simulate path failure:

```bash
ip link set dev eth1 down
```

Re-enable the interface:

```bash
ip link set dev eth1 up
```

Inject packet loss to simulate congestion:

```bash
tc qdisc add dev eth1 root netem loss 5%
tc qdisc del dev eth1 root
```

Introduce network delay to trigger timeouts:

```bash
tc qdisc add dev eth1 root netem delay 5000ms
tc qdisc del dev eth1 root
```

Restart the iSCSI daemon to test session persistence:

```bash
systemctl restart iscsid.service
```

Monitor kernel messages during fault injection:

```bash
journalctl -kf | grep -E 'iscsi|multipath|scsi|I/O error'
```

### Configuration Validation

Verify the initiator IQN:

```bash
cat /etc/iscsi/initiatorname.iscsi
```

Check session recovery timeout:

```bash
iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --op show | grep replacement_timeout
```

Review multipath configuration:

```bash
cat /etc/multipath.conf
multipathd show config
```

Validate that automatic login is enabled for production targets:

```bash
iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --op show | grep node.startup
```

Expected: `node.startup = automatic`. Set with:

```bash
iscsiadm --mode node --targetname iqn.2025-01.com.storage:san.array01 --portal 192.168.100.10:3260 --op update --name node.startup --value automatic
```

### Comprehensive State Snapshot

Collect a full diagnostic snapshot for offline analysis:

```bash
iscsiadm --mode session --print 1 > /tmp/iscsi_session.txt
multipath -ll > /tmp/mpath_topology.txt
lsscsi -v > /tmp/scsi_devices.txt
dmsetup table > /tmp/dm_table.txt
dmsetup status > /tmp/dm_status.txt
journalctl -k --since "30 minutes ago" > /tmp/kernel_log.txt
ss -tipm > /tmp/tcp_state.txt
ethtool -S eth1 > /tmp/nic_stats_eth1.txt
ethtool -S eth2 > /tmp/nic_stats_eth2.txt
tar -czf iscsi_diagnostic_$(date +%F_%T).tar.gz /tmp/iscsi_*.txt /tmp/mpath_topology.txt /tmp/scsi_devices.txt /tmp/dm_*.txt /tmp/kernel_log.txt /tmp/tcp_state.txt /tmp/nic_stats_*.txt
```

### Verification Checklist

Before declaring an iSCSI deployment production-ready, validate the following:

1. **Initiator IQN uniqueness**: Confirm each initiator has a globally unique IQN. Duplicate IQNs cause authentication failures and session conflicts.
2. **Automatic login configuration**: Verify that `node.startup = automatic` is set for all production targets to ensure sessions re-establish after initiator reboot.
3. **Multipath configuration**: Confirm that all LUNs appear as multipath devices (`/dev/mapper/mpath*`) and no raw SCSI devices (`/dev/sd*`) are directly accessed.
4. **Path redundancy**: Validate that at least two independent network paths exist to each target portal, verified with `multipath -ll` showing multiple active paths per LUN.
5. **MTU consistency**: Ensure all storage interfaces, switches, and target ports use MTU 9000 (Jumbo Frames). Test with `ping -M do -s 8972`.
6. **TCP offload enablement**: Verify TSO, GSO, and checksum offload are enabled on storage NICs with `ethtool -k eth1 | grep -E 'tcp-segmentation-offload|generic-segmentation-offload|tx-checksumming'`.
7. **Session recovery timers**: Confirm `replacement_timeout` is set to a value appropriate for the application's RTO (Recovery Time Objective), typically 15–30 seconds for latency-sensitive workloads.
8. **Filesystem alignment**: Ensure partitions on multipath devices are aligned to 4 KB boundaries to avoid read-modify-write penalties. Check with `parted /dev/mapper/mpatha unit s print`.
9. **Performance baseline**: Document throughput, IOPS, and latency for sequential and random workloads at multiple queue depths. Store results for regression analysis.
10. **Failover validation**: Execute a controlled path failure test (disable one interface) under load and verify I/O continues without application-visible errors. Confirm recovery occurs within expected timeout.
11. **Monitoring integration**: Ensure iSCSI session state, multipath path health, and per-LUN I/O statistics are exported to the production monitoring system (e.g., Prometheus `node_exporter` with textfile collector).
12. **Firmware and driver versions**: Record iSCSI initiator kernel module version (`modinfo iscsi_tcp`), target firmware version, and NIC driver version (`ethtool -i eth1`). Validate against vendor compatibility matrices.

This checklist forms the operational contract between the infrastructure team and application owners, ensuring iSCSI storage meets availability and performance SLAs.
