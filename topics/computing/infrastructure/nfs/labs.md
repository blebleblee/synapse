# Operational Verification Labs: Nfs

## Objective & Environment Setup

The Network File System protocol represents one of the foundational distributed file-sharing mechanisms in modern infrastructure, enabling remote clients to mount and manipulate file hierarchies over TCP or UDP transports as if they were locally attached block devices. Unlike object stores or distributed databases that abstract storage behind HTTP REST APIs, NFS preserves POSIX semantics—file handles, directory operations, attribute caching, and lock coordination—across network boundaries. This preservation of familiar file system interfaces makes NFS ubiquitous in container orchestration persistent volumes, high-performance computing shared scratch spaces, and traditional enterprise network-attached storage architectures.

These operational verification laboratories ground NFS diagnostics in the concrete realities of kernel RPC state machines, network protocol analysis, client-side attribute cache coherency, and server-side export authorization. You will instrument live NFS mounts using kernel tracing infrastructure, dissect on-wire RPC exchanges with packet capture tools, benchmark throughput under concurrent workload saturation, and inject deliberate network partitions to observe client recovery behavior. The exercises synthesize knowledge from multiple infrastructure domains: Linux VFS layer interactions, TCP socket buffer tuning, RPC authentication mechanisms, and storage I/O profiling.

Your diagnostic environment requires a Linux system with kernel version 5.10 or newer to access modern NFS client implementations and eBPF tracing hooks. Install the foundational toolchain with your distribution's package manager. On Debian-based systems, execute `apt-get install nfs-common nfs-kernel-server iproute2 tcpdump strace perf-tools-unstable bpfcc-tools`. For Red Hat derivatives, use `dnf install nfs-utils iproute tcpdump strace perf bcc-tools`. Verify kernel support for NFSv4 by checking `/proc/fs/nfsd/versions`; you should observe version strings including `+4.2` indicating NFSv4.2 protocol availability. The NFS client kernel module loads automatically on first mount attempt, but you can preload it explicitly with `modprobe nfs` to inspect module parameters in `/sys/module/nfs/parameters/`.

Establish a minimal NFS server and client topology on two virtual machines or container network namespaces. On the server node, create an export directory `/srv/nfs/share` and populate `/etc/exports` with a single line: `/srv/nfs/share 192.168.100.0/24(rw,sync,no_subtree_check,no_root_squash)`. The `sync` option forces synchronous write semantics, making server-side durability guarantees visible in latency measurements, while `no_root_squash` disables UID zero mapping for simplified testing. Start the NFS server daemon with `systemctl start nfs-server` and verify listening sockets with `ss -tln | grep :2049`; you should observe the server bound to the NFS port on all interfaces. On the client node, mount the remote export with `mount -t nfs -o vers=4.2,rsize=1048576,wsize=1048576 192.168.100.10:/srv/nfs/share /mnt/nfs`. The explicit NFSv4.2 version and large read/write buffer sizes establish a baseline for high-throughput operations. Confirm the mount with `mount | grep nfs` and inspect mount options in `/proc/mounts` where the kernel rewrites your requested parameters into the actual negotiated values.

This topology allows you to observe both client-side kernel state and server-side RPC processing. The client VFS layer translates POSIX system calls into NFS RPC operations, which traverse the network as Sun RPC XDR-encoded messages, arrive at the server's `nfsd` kernel threads, and return results that populate client-side attribute caches and page cache buffers. Understanding this full round-trip flow requires instrumenting both endpoints simultaneously, correlating packet timestamps with kernel tracepoints, and measuring latencies at each stage of the distributed transaction.

## Exercise 1: Live State & Internal Subsystem Inspection

Begin your inspection of live NFS client state by examining the kernel's internal mount table representation. The pseudo-filesystem mounted at `/proc/mounts` exposes the authoritative view of active mounts as the kernel maintains them, not the user-space mount command's view. Execute `cat /proc/mounts | grep nfs` and observe the rewritten mount options. The kernel may have negotiated a lower `rsize` or `wsize` than you requested if server or network constraints imposed limits. Note the `timeo` and `retrans` parameters, which define the initial RPC timeout in deciseconds and the maximum retry count before marking the server unreachable. These parameters govern the client's resilience to transient network disruptions and server pauses.

Dive deeper into client-side RPC statistics by reading `/proc/self/mountstats`, which enumerates every mounted filesystem's internal counters. For your NFS mount, locate the section beginning with `device 192.168.100.10:/srv/nfs/share mounted on /mnt/nfs with fstype nfs4`. The subsequent lines expose RPC operation counts categorized by procedure type: `READ`, `WRITE`, `GETATTR`, `LOOKUP`, `ACCESS`, and dozens more. Each operation lists its invocation count, transmission count (including retries), major timeouts, and cumulative bytes sent and received. Write a small read workload with `dd if=/dev/zero of=/mnt/nfs/testfile bs=1M count=100` and immediately re-read `/proc/self/mountstats`. The `WRITE` operation count increments by the number of RPC calls required to satisfy your write request, which depends on the negotiated `wsize`. For a 1 MiB write buffer and 1 MiB `wsize`, you expect approximately 100 `WRITE` calls plus several `GETATTR` calls for metadata synchronization.

The disparity between operation counts and actual system calls reveals the kernel's client-side caching and request coalescing behavior. NFS clients aggressively cache file attributes in memory for a duration controlled by the `acdirmin`, `acdirmax`, `acregmin`, and `acregmax` mount options. During the attribute cache validity window, the client satisfies `stat()` and `getattr()` system calls directly from cache without issuing RPC operations. Demonstrate this by executing `stat /mnt/nfs/testfile` repeatedly within a few seconds. After the first invocation increments the `GETATTR` count in `mountstats`, subsequent `stat` calls produce zero additional RPC operations until the cache timeout expires. The default `acregmax` value of 60 seconds means file attributes remain cached for up to one minute, during which modifications by other clients become invisible to your view.

Move from high-level statistics to real-time RPC tracing using the kernel's built-in NFS client tracepoints. The `trace-cmd` utility provides a user-friendly interface to the kernel's `ftrace` infrastructure. Execute `trace-cmd record -e nfs:nfs_readdir_enter -e nfs:nfs_readdir_exit ls /mnt/nfs/` to capture directory enumeration events. The resulting `trace.dat` file contains timestamped entries for each tracepoint hit. Extract human-readable output with `trace-cmd report`, which displays the calling process, CPU, timestamp, and tracepoint-specific arguments. For `nfs_readdir_enter`, you observe the directory inode number and file handle. The paired `nfs_readdir_exit` tracepoint reveals the operation's return code and the number of directory entries fetched. By calculating the delta between enter and exit timestamps, you measure the server round-trip latency for directory operations, isolating network and server processing time from client-side VFS overhead.

Extend tracing to write operations by capturing `nfs:nfs_file_write` and `nfs:nfs_writeback_done` events during a file modification workload. The `nfs_file_write` tracepoint fires when the VFS layer issues a write request, while `nfs_writeback_done` triggers after the NFS client receives the server's acknowledgment and updates its internal state. The time gap between these events encompasses network transmission, server-side disk I/O if `sync` semantics are enabled, and the return path latency. Run `trace-cmd record -e nfs:nfs_file_write -e nfs:nfs_writeback_done dd if=/dev/zero of=/mnt/nfs/largefile bs=4M count=25` and analyze the trace output. Each 4 MiB write may split into multiple RPC operations depending on the effective `wsize`, and you can correlate the split writes by matching file offset values in the tracepoint arguments.

For server-side introspection, the `nfsdfs` pseudo-filesystem mounted at `/proc/fs/nfsd/` exposes internal server state. The `clients` subdirectory enumerates currently connected NFSv4 clients by their unique client identifiers. Enter a client directory and read the `info` file to see the client's IP address, connection time, and callback address. NFSv4's stateful model requires the server to track client sessions and delegations, unlike NFSv3's stateless design. The `states` file within each client directory lists open file handles, lock ranges, and delegation types. Create a file on the client with `touch /mnt/nfs/delegated` and immediately inspect the server's `states` file. You should observe an open state entry with a state ID, file handle, and possibly a read delegation if the server granted one to optimize subsequent reads without round-trips.

Network-level observation complements kernel tracing by revealing the actual on-wire RPC protocol exchanges. Use `tcpdump` to capture NFS traffic between client and server. On the client machine, execute `tcpdump -i eth0 -w nfs_capture.pcap port 2049` to write raw packets to a file. In a second terminal, perform a simple operation like `cat /mnt/nfs/testfile > /dev/null` to generate read traffic. Stop the packet capture and analyze it with `tcpdump -r nfs_capture.pcap -vvv` for verbose output, or use Wireshark for graphical dissection. Each NFS RPC operation encapsulates within a TCP stream as a Sun RPC message with XDR encoding. You will observe the RPC call header containing program number 100003 (NFS), version 4, and procedure numbers corresponding to operations like `GETATTR` (9), `READ` (25), and `CLOSE` (4). The reply messages carry status codes and marshaled data structures including file attributes with `size`, `mtime`, and `change` values.

Filter the packet trace to isolate specific operations. For example, `tcpdump -r nfs_capture.pcap 'port 2049 and tcp[32:4] = 0x00000019'` extracts packets where byte offset 32 in the TCP payload contains the COMPOUND procedure number. NFSv4 bundles multiple operations into COMPOUND requests to reduce round-trips, so a single `open()` system call may translate into a COMPOUND containing PUTFH (to set the current file handle), OPEN, and GETATTR operations. By inspecting the XDR-encoded arguments, you verify that the client sent the expected file name, access mode flags, and attribute bitmask. The server's reply COMPOUND includes status codes for each sub-operation, returned file handles, and requested attributes.

Correlating packet captures with kernel tracepoints provides end-to-end visibility. Export the trace data with timestamps in a format matching `tcpdump` output by running `trace-cmd report -t -F 'secs.usecs'` to get seconds.microseconds precision. Align the packet timestamp for an NFS WRITE reply with the `nfs_writeback_done` tracepoint timestamp. The difference between the packet arrival time and the tracepoint firing time exposes the kernel's internal processing overhead for updating page cache state, invoking write completion callbacks, and potentially triggering further I/O operations.

Client-side performance often bottlenecks on attribute cache misses forcing excessive `GETATTR` calls. Profile attribute cache effectiveness by monitoring `mountstats` before and after a metadata-intensive workload. Execute `find /mnt/nfs -type f` to enumerate all files, then examine the `GETATTR` count delta. Each cache miss results in an RPC round-trip, so a large `GETATTR` count relative to the number of files suggests suboptimal cache tuning. Increase the attribute cache timeout by remounting with `-o remount,acregmax=300,acdirmax=300` to cache attributes for up to five minutes. Repeat the `find` operation and observe fewer `GETATTR` calls as the client reuses cached metadata. This tuning trades off consistency—other clients' modifications become visible only after the cache timeout—against reduced network traffic and lower latency.

## Exercise 2: Benchmarking & Saturation Profiling

Quantify NFS client throughput and latency under controlled synthetic workloads to establish performance baselines and identify bottlenecks. The `fio` (Flexible I/O Tester) tool provides a sophisticated framework for generating reproducible I/O patterns with precise control over concurrency, block sizes, and access patterns. Install `fio` with your package manager and verify its version supports NFS by checking the output of `fio --enghelp` for the `sync` I/O engine, which issues standard POSIX read and write system calls suitable for NFS testing.

Create a baseline sequential read benchmark job file named `nfs_seq_read.fio` containing the following specification:

```ini
[global]
ioengine=sync
direct=0
numjobs=1
time_based=1
runtime=60
group_reporting=1

[seq_read]
rw=read
bs=1M
directory=/mnt/nfs
size=1G
filename=seqread_test
```

This configuration instructs `fio` to perform sequential reads with 1 MiB block sizes for 60 seconds, using buffered I/O (`direct=0`) to engage the kernel's page cache. Execute the benchmark with `fio nfs_seq_read.fio` and observe the reported bandwidth, IOPS, and latency percentiles. The sequential read bandwidth should approach the physical network link capacity if the server has sufficient disk throughput and the client's CPU is not saturated. For a gigabit Ethernet link, expect approximately 100-115 MiB/s effective throughput after accounting for TCP/IP overhead. If observed bandwidth is significantly lower, inspect intermediate layers: check for packet loss with `ip -s link show eth0` and examine the `RX-ERR` counter, verify that the server's disk is not I/O-bound by running `iostat -x 1` on the server during the test, and confirm that no firewall or traffic shaping rules are throttling the connection.

Contrast sequential performance with random read patterns by modifying the job file. Change `rw=read` to `rw=randread` and reduce the block size to `bs=4k` to simulate small random accesses typical of database or virtual machine disk workloads. Random reads stress the NFS client's ability to parallelize requests and the server's capacity to handle concurrent I/O operations. Run the modified benchmark and note the dramatic reduction in throughput compared to sequential reads. Each 4 KiB read now requires a separate RPC operation, and the round-trip latency dominates performance. The IOPS metric becomes more relevant than bandwidth; on a local network with sub-millisecond latencies, you might achieve 500-2000 IOPS depending on server disk speed and client parallelism.

Increase client-side parallelism by modifying `numjobs=1` to `numjobs=8` in the `fio` configuration. This change spawns eight concurrent `fio` worker threads, each issuing independent read operations. NFS clients benefit from parallelism because multiple outstanding RPCs can amortize network round-trip costs and leverage server-side concurrency. Re-run the random read benchmark with eight jobs and observe the IOPS increase. However, at some concurrency level, you will encounter diminishing returns or even performance degradation as the client or server becomes resource-constrained. Profile client-side CPU utilization during high-concurrency runs with `perf top` to identify hot kernel functions. Look for high percentages in NFS client code paths like `nfs_readpage`, `rpc_execute`, or TCP send/receive functions indicating client CPU saturation.

Write benchmarks expose different bottlenecks due to the interplay of client-side write buffering, server-side disk synchronization, and NFS consistency semantics. Create a sequential write job file named `nfs_seq_write.fio`:

```ini
[global]
ioengine=sync
direct=0
numjobs=1
time_based=1
runtime=60
group_reporting=1

[seq_write]
rw=write
bs=1M
directory=/mnt/nfs
size=1G
filename=seqwrite_test
end_fsync=1
```

The `end_fsync=1` directive forces `fio` to call `fsync()` after completing all writes, ensuring that reported performance includes the cost of flushing data to stable storage. Execute the benchmark and compare write bandwidth to read bandwidth from the previous test. Writes typically exhibit higher latency than reads because the NFS server must commit data to disk before acknowledging the operation when `sync` semantics are in effect. If your server export uses `async` instead of `sync`, the server may acknowledge writes immediately after caching them in memory, yielding much higher throughput at the cost of potential data loss on server crashes.

Measure write latency distribution by examining `fio`'s percentile output. The median (`50.00th percentile`) latency represents typical performance, while the `99.00th` and `99.99th` percentiles reveal tail latencies caused by disk seek time, TCP retransmissions, or server-side resource contention. High tail latencies indicate unpredictable performance, problematic for latency-sensitive applications. If the 99th percentile latency exceeds several milliseconds on a local network, investigate server-side disk I/O patterns with `blktrace` to capture block device request queues and identify sources of latency spikes.

Network saturation tests determine the maximum sustainable throughput before packet loss or congestion degrades performance. Increase the `numjobs` parameter progressively from 1 to 16 in the sequential write benchmark and plot the achieved bandwidth against concurrency. Initially, bandwidth scales linearly as additional jobs exploit available network capacity. Beyond a critical concurrency threshold, bandwidth plateaus or decreases as the network link saturates, TCP congestion control activates, or server-side locking contention emerges. Monitor real-time network utilization during the test with `iftop -i eth0` to visualize bandwidth consumption and identify the saturation point.

Concurrent mixed read-write workloads stress the NFS client's request scheduling and the server's ability to handle heterogeneous operations. Design a mixed I/O job file that combines random reads and writes:

```ini
[global]
ioengine=sync
direct=0
numjobs=4
time_based=1
runtime=60
group_reporting=1

[mixed_rw]
rw=randrw
rwmixread=70
bs=4k
directory=/mnt/nfs
size=1G
filename=mixed_test
```

The `rwmixread=70` setting generates a 70% read, 30% write ratio, simulating typical application access patterns. Four concurrent jobs contend for both client and server resources. Execute the benchmark and analyze the separate read and write IOPS, bandwidth, and latency statistics. Writes may exhibit higher latency variance due to server-side commit delays, while reads benefit from client-side page cache hits if the working set fits in memory. Observe the read cache hit rate by comparing the reported read IOPS against the `READ` operation count in `/proc/self/mountstats`. A large discrepancy indicates that many reads satisfied from local cache without generating RPC operations.

Saturate the NFS server by launching multiple client nodes executing concurrent benchmarks. Deploy the same `fio` job file on two or more client machines targeting the same server export. Start the benchmarks simultaneously and aggregate the total throughput. As client count increases, you eventually hit server-side limits: disk I/O bandwidth, CPU processing capacity for RPC decoding, or network interface saturation. Identify the bottleneck by monitoring server metrics. Use `nfsiostat` (part of `nfs-utils`) on the server to display per-export statistics including operations per second, bytes read/written, and average response time. Execute `nfsiostat -h 1` for human-readable output refreshed every second during the multi-client test. If operations per second plateau while server CPU remains low and disk utilization is moderate, the bottleneck likely resides in network bandwidth or NFS daemon concurrency limits.

Kernel-level profiling with `perf` exposes hot code paths in the NFS client and server stacks. On the client, start a system-wide profile during a high-throughput benchmark with `perf record -a -g sleep 30` to sample all CPUs for 30 seconds with call graph recording. After the benchmark completes, generate a flame graph or examine the hottest functions with `perf report`. Typical hot spots in the NFS client include `__tcp_transmit_skb` for TCP send operations, `nfs_write_end` for page cache management, and `rpc_execute` for RPC state machine transitions. High percentages in TCP stack functions suggest network processing is CPU-bound, potentially addressable by enabling NIC offload features like TCP segmentation offload (TSO) or checksum offload.

On the server, profile the `nfsd` kernel threads with `perf record -a -g -p $(pgrep nfsd | head -1) sleep 30` targeting a specific `nfsd` thread PID. Analyze the resulting profile to identify whether server CPU time concentrates in filesystem operations, RPC deserialization, or network receive paths. If the server spends significant time in the underlying filesystem's write path (e.g., `ext4_file_write_iter`), consider tuning the filesystem mount options or switching to a more performant filesystem for the NFS export backend. For example, mounting the export filesystem with `noatime` avoids updating access timestamps on every read, reducing metadata write overhead.

## Exercise 3: Fault Injection & Recovery Analysis

Distributed systems reveal their true resilience characteristics under failure conditions when network partitions interrupt communication, servers become unresponsive, or concurrent clients create conflicting state. Deliberately injecting faults into your NFS topology allows you to observe and measure the client's recovery mechanisms, quantify service disruption duration, and validate that applications built atop NFS handle transient failures gracefully.

Begin with a simple network partition between client and server. On the client machine, identify the network interface connecting to the NFS server with `ip route get 192.168.100.10` and note the `dev` interface name, such as `eth0`. Establish a baseline by running a continuous write loop: `while true; do dd if=/dev/zero of=/mnt/nfs/liveness bs=1M count=1 conv=fsync; sleep 1; done`. This loop writes a 1 MiB file every second, providing a clear indicator of NFS availability. In a separate terminal, monitor the write operation's success by watching the file's modification timestamp: `watch -n 1 stat /mnt/nfs/liveness`.

Inject a network partition by bringing down the client's network interface with `ip link set eth0 down`. The continuous write loop will block immediately on the next write attempt because the NFS client cannot reach the server. Observe the process state with `ps aux | grep dd`; the `dd` process enters an uninterruptible sleep state (`D` state) waiting for the RPC operation to complete or timeout. Examine the kernel's RPC timeout behavior by reading the client's mount options in `/proc/mounts`. The `timeo` parameter, typically expressed in deciseconds (e.g., `timeo=600` equals 60 seconds), governs the initial RPC timeout. After the timeout expires, the client retries the operation according to the `retrans` parameter, doubling the timeout interval for each retry up to a maximum.

After approximately two to three minutes (depending on your `timeo` and `retrans` settings), the NFS client exhausts its retry attempts and the write operation fails with an I/O error. The `dd` process exits, and the continuous loop attempts the next write, which also fails immediately. Restore network connectivity with `ip link set eth0 up` and observe the recovery. The NFS client re-establishes its TCP connection to the server, and subsequent write operations succeed immediately. This hard-mount behavior, where the client retries indefinitely until the server returns or a hard timeout expires, preserves application semantics at the cost of blocking I/O operations during outages.

Contrast hard-mount behavior with soft-mount semantics by remounting the NFS share with the `soft` option: `mount -o remount,soft,timeo=100,retrans=3 /mnt/nfs`. Soft mounts cause RPC operations to fail with an error after the retry limit expires instead of blocking indefinitely. Repeat the network partition experiment with the soft mount. After the client exhausts three retries at 10-second intervals (30 seconds total), the `dd` command receives an I/O error and exits. The continuous loop immediately attempts the next write, which also fails. Soft mounts provide bounded failure latency, allowing applications to detect server unavailability quickly and implement their own retry logic or failover strategies. However, soft mounts risk data corruption if applications do not properly handle I/O errors, making them unsuitable for critical data.

Simulate server-side delays without full unavailability by introducing artificial latency on the server's network interface. On the server machine, use the `tc` (traffic control) utility to add 500 milliseconds of delay to outbound packets: `tc qdisc add dev eth0 root netem delay 500ms`. The client's write operations now experience dramatically increased latency, as each RPC round-trip incurs an additional second (500ms in each direction). Monitor the write loop's throughput; instead of completing one write per second, the loop may only achieve one write every two to three seconds due to the compounded RPC latency and client-side timeout adjustments. Examine the client's perception of latency by reading `/proc/self/mountstats` and observing the `rtt` (round-trip time) statistics for RPC operations. The average RTT increases proportionally to the injected delay.

Remove the artificial delay with `tc qdisc del dev eth0 root` and observe the client's adaptation. NFS clients maintain dynamic RPC timeout estimates based on recent RTT measurements, so after delay removal, the client gradually reduces its timeout intervals to match the restored low-latency network. This adaptive behavior prevents premature timeouts during transient congestion while quickly recovering to low-latency operations when conditions improve.

Introduce packet loss to simulate degraded network conditions. On the server, configure a 10% packet drop rate with `tc qdisc add dev eth0 root netem loss 10%`. The NFS client now experiences occasional RPC failures requiring retransmission. Monitor the TCP layer's response to packet loss by tracking retransmission statistics with `ss -ti` targeting the client's NFS connection. Execute `ss -ti '( dport = :2049 )'` repeatedly during a write workload and observe the `bytes_retrans` field incrementing as TCP retransmits lost segments. NFS performance degrades under packet loss because each lost RPC request or reply triggers a timeout and retry, multiplying the effective latency by the retry count.

Measure the impact of packet loss on application throughput by running a timed write benchmark. Execute `time dd if=/dev/zero of=/mnt/nfs/loss_test bs=1M count=100 conv=fsync` with and without the packet loss injection. Compare the completion times; a 10% loss rate may increase write duration by 50% or more due to the cascading effects of retransmissions and increased latency. Remove the packet loss with `tc qdisc del dev eth0 root` to restore normal operation.

Concurrent client scenarios expose NFS consistency models and locking behavior. Mount the same NFS export on two separate client machines. On client A, create a file with `echo "Client A" > /mnt/nfs/shared_file`. On client B, immediately read the file with `cat /mnt/nfs/shared_file`. NFSv4's close-to-open consistency semantics guarantee that once client A closes the file, client B's subsequent open will observe the updated content, provided client B's attribute cache has expired or been invalidated. However, if client B has recently accessed the file and its attribute cache remains valid, it may read stale cached data. Demonstrate this by rapidly alternating writes and reads between the two clients within the attribute cache timeout window.

Validate NFS file locking by implementing a critical section protected by an exclusive file lock. On client A, execute a script that acquires a lock, performs a long-running operation, and releases the lock:

```bash
#!/bin/bash
exec 200>/mnt/nfs/lockfile
flock -x 200
echo "Client A acquired lock"
sleep 30
echo "Client A releasing lock"
flock -u 200
```

While client A holds the lock, attempt to acquire the same lock on client B with an identical script. Client B's `flock` call blocks until client A releases the lock, demonstrating that NFS correctly coordinates locks across clients. The NFS lock manager (NLM) protocol, or NFSv4's integrated locking, ensures that only one client holds the exclusive lock at any time. Verify lock coordination by observing the time delta between client A's release message and client B's acquisition message; it should be nearly instantaneous on a low-latency network.

Introduce a server restart to observe client recovery from complete server unavailability. While client A runs the continuous write loop, execute `systemctl restart nfs-server` on the server machine. The NFS server process terminates, closing all client connections and losing any uncommitted data in server-side caches. Client A's write operations immediately begin failing as the TCP connection breaks. After the server restarts—typically within a few seconds—clients automatically re-establish connections and resume operations. However, NFSv4's stateful model requires clients to reclaim open file handles and locks during a grace period after server restart. Observe this grace period by monitoring the server's `nfsdfs` filesystem; the `/proc/fs/nfsd/` directory contains a `v4_end_grace` file indicating when the grace period expires.

Client-side caching and write-back behavior complicate fault recovery. The NFS client's page cache buffers dirty pages in memory before flushing them to the server, improving performance at the risk of data loss if the client crashes before writeback completes. Demonstrate dirty page accumulation by writing a large file without an explicit flush: `dd if=/dev/zero of=/mnt/nfs/cached_write bs=1M count=500`. Immediately after the `dd` command completes, examine the client's dirty page count with `grep Dirty /proc/meminfo`. The `Dirty:` field shows the amount of modified data awaiting writeback. Force an immediate flush with `sync` or `echo 3 > /proc/sys/vm/drop_caches` and observe the dirty count drop to zero as the client transmits buffered writes to the server.

Inject a client crash simulation by killing the client process after accumulating dirty pages but before writeback. Write a file without syncing: `dd if=/dev/zero of=/mnt/nfs/unsynced bs=1M count=100`. Check the dirty page count to confirm buffering, then abruptly reboot the client with `reboot -f` to bypass graceful shutdown. After the client restarts and remounts the NFS share, check the file size on the server. Depending on timing, the file may be smaller than expected or entirely absent if no data was flushed before the crash. This behavior underscores the importance of explicit synchronization—applications requiring durability guarantees must call `fsync()` or use `O_SYNC` open flags to force immediate writeback.

Network-level chaos injection with tools like `tc-netem` (network emulator) enables more complex failure scenarios. Install the `iproute2-tc` package if not already present, then apply a composite delay, loss, and reordering policy to the client's network interface:

```bash
tc qdisc add dev eth0 root netem delay 50ms 10ms distribution normal loss 2% reorder 5% 25%
```

This configuration adds a mean delay of 50ms with 10ms standard deviation following a normal distribution, drops 2% of packets, and reorders 5% of packets with 25% of those being reordered. The reordering component simulates network switches or routers delivering packets out of sequence, stressing TCP's handling of such conditions. Run a mixed read-write benchmark under these chaotic conditions and compare performance to the baseline. Latency percentiles widen significantly, and throughput drops as TCP and NFS retry mechanisms engage more frequently. Remove the netem rules with `tc qdisc del dev eth0 root` to restore normal operation.

Finally, validate that critical application data survives NFS failures by implementing a journaling or transaction log pattern atop NFS. Write a script that appends transaction records to a log file with `fsync` after each record, simulating a database or message queue:

```bash
#!/bin/bash
for i in {1..100}; do
  echo "Transaction $i at $(date +%s)" >> /mnt/nfs/transaction_log
  sync /mnt/nfs/transaction_log
  sleep 0.1
done
```

While the script runs, inject a brief network partition (5 seconds) by bringing down the interface, waiting, and bringing it back up. After the partition heals, verify that the transaction log is intact and contains all records up to the partition point. Some transactions initiated during the partition may have failed to commit, but no records should be corrupted or lost. This pattern, combined with application-level retry logic, enables building reliable systems atop NFS despite transient failures.

## Diagnostic Cheat Sheet & Verification Checklist

Rapidly diagnosing NFS issues in production environments requires a mental model of common failure modes and their diagnostic signatures. The following reference tables consolidate key commands, metrics, and interpretations for quick troubleshooting.

**Essential NFS Client Commands:**

| Command | Purpose | Key Output Fields |
|---------|---------|-------------------|
| `mount \| grep nfs` | List active NFS mounts | Mount point, server, options |
| `cat /proc/mounts \| grep nfs` | Show kernel's actual mount parameters | Negotiated rsize/wsize, timeouts |
| `cat /proc/self/mountstats` | Per-mount RPC statistics | Operation counts, retries, timeouts |
| `nfsstat -c` | Client-side RPC operation summary | Calls, retransmits, timeouts per operation |
| `ss -ti '( dport = :2049 )'` | TCP state for NFS connections | RTT, retransmits, congestion window |
| `trace-cmd record -e nfs:*` | Capture all NFS tracepoints | Operation timings, file handles |

**Essential NFS Server Commands:**

| Command | Purpose | Key Output Fields |
|---------|---------|-------------------|
| `cat /proc/fs/nfsd/versions` | Supported NFS protocol versions | Active version numbers |
| `nfsstat -s` | Server-side RPC statistics | Calls received, replies sent, errors |
| `cat /proc/fs/nfsd/clients/*/info` | Connected client details | Client ID, IP address, connection time |
| `exportfs -v` | Current export list with options | Export path, client restrictions, flags |
| `nfsiostat 1` | Per-export I/O statistics | Ops/sec, KB/sec, avg latency |

**Common NFS Failure Signatures:**

**Symptom:** File I/O operations hang indefinitely; processes stuck in `D` state. **Diagnosis:** Check `ss -ti` for established TCP connection state. If connection is `ESTABLISHED` but no data flows, inspect `/proc/self/mountstats` for timeouts and retransmits incrementing. Verify server is responsive with `ping` and `telnet <server> 2049`. **Resolution:** If server is down, wait for hard-mount timeout or remount with `soft` option. If network is congested, increase `timeo` and `retrans` mount options.

**Symptom:** Poor write throughput; much lower than read throughput. **Diagnosis:** Check server export options in `/etc/exports` for `sync` vs `async`. Profile server-side disk I/O with `iostat -x 1` during writes; high `await` times indicate slow storage. **Resolution:** If server disk is bottleneck, consider caching layer or faster storage. If using `sync` semantics for data safety, ensure server has write-back cache with battery backup. Increase client-side `wsize` to reduce RPC overhead.

**Symptom:** Applications report stale data; changes made by one client not visible to others. **Diagnosis:** Examine attribute cache settings in `/proc/mounts`; long `acregmax` or `acdirmax` values delay cache invalidation. Check `mountstats` for low `GETATTR` counts suggesting excessive caching. **Resolution:** Reduce attribute cache timeouts with remount: `-o remount,acregmax=30,acdirmax=30`. For strict consistency, use NFSv4 delegations or open-to-close semantics by ensuring all clients close and reopen files after modifications.

**Symptom:** Lock acquisition fails or times out. **Diagnosis:** NFSv4 clients list locks in `/proc/fs/nfsd/clients/*/states` on the server. Check for stale locks from crashed clients. Verify lock manager is running with `systemctl status rpc-statd` (NFSv3) or ensure NFSv4 is in use. **Resolution:** For NFSv3, restart `rpc-statd` on both client and server. For NFSv4, unmount and remount the share to force lock reclaim during grace period.

**Symptom:** RPC operation count in `mountstats` vastly exceeds application-level I/O. **Diagnosis:** Small application buffer sizes or misaligned writes cause excessive RPC operations. Each write smaller than `wsize` generates a separate RPC. **Resolution:** Increase application buffer sizes to match or exceed `wsize`. Use memory-mapped I/O (`mmap`) for random access workloads to let the kernel batch operations.

**Verification Checklist for Production NFS Deployments:**

Prior to production cutover, systematically validate each layer of the NFS stack to avoid common misconfigurations. First, confirm NFSv4 operation by checking that no NFSv3 processes are running (`systemctl status rpc-bind nfs-lock`) and that mounts use `vers=4.2`. Verify security by ensuring exports do not use `no_root_squash` unless absolutely required; test that UID/GID mapping functions correctly by creating files as different users and inspecting ownership on the server.

Test client failover by simulating server restart during active I/O; confirm that applications handle transient I/O errors gracefully and that all data written before the restart persists. Measure recovery time from network partition by scripting partition injection and recording the duration until I/O resumes; tune `timeo` and `retrans` if recovery takes unacceptably long.

Benchmark both sequential and random I/O patterns under realistic concurrency; ensure throughput meets application requirements and identify any bottlenecks with `perf` profiling. Verify that server exports are protected by firewall rules limiting access to authorized clients; check with `iptables -L` or `nft list ruleset`.

Validate monitoring and alerting by confirming that your metrics system tracks key NFS statistics: client RPC retransmit rate, server RPC latency percentiles, and export-level I/O bandwidth. Establish baselines for normal operation and configure alerts for anomalies such as sustained high retransmit rates exceeding 1% or RPC latencies above 100ms.

Document the NFS deployment's consistency model and recovery characteristics so application developers understand the guarantees and failure modes. Specify attribute cache timeouts, whether mounts are hard or soft, and expected recovery time from common failure scenarios. This documentation enables developers to design applications that leverage NFS strengths while mitigating its weaknesses through appropriate retry logic, caching strategies, and error handling.
