# Operational Verification Labs: 03 High Performance Maps

## Objective & Environment Setup

The objective of this lab is to verify and validate the operational behavior of **High Performance Maps (HPMs)** within the Linux kernel using eBPF-based tracing and monitoring. HPMs are optimized data structures for high-throughput, low-latency key-value storage in kernel space, often used in eBPF programs for performance-critical applications such as packet filtering, traffic shaping, and system telemetry.

This lab assumes a Linux environment with eBPF support (kernel version 5.10 or higher), and the following tools installed:

- `bpftool`: Inspect and manage BPF maps and programs.
- `kubectl`: Kubernetes CLI for container orchestration (if testing in a Kubernetes environment).
- `iproute2`: Network configuration and inspection tools.
- `tcpdump`: Packet capture and inspection.
- `strace`: System call tracing.
- `perf`: Performance profiling.
- `bpftrace`: High-level BPF tracing language.

### Environment Configuration

Ensure the following kernel parameters are set for optimal eBPF performance:

```bash
# Enable BPF JIT compilation
echo 1 > /proc/sys/net/core/bpf_jit_enable

# Increase BPF map limits
echo 1048576 > /proc/sys/net/core/bpf_map_max_entries
```

Additionally, ensure that the following modules are loaded:

```bash
modprobe bpf
modprobe bpf_tracing
```

## Exercise 1: Live State & Internal Subsystem Inspection

In this exercise, we inspect the live state of BPF maps and their internal subsystems using `bpftool` and kernel memory inspection tools.

### 1.1 Inspect BPF Maps

First, list all BPF maps currently loaded in the system:

```bash
bpftool map show
```

This command outputs a table of all BPF maps, including their type, key size, value size, and maximum entries. For example:

```
1: hash  flags 0x0
        key 4B value 8B max_entries 1024
        memlock 4096B
```

To inspect a specific map by ID (e.g., ID `1`), run:

```bash
bpftool map dump id 1
```

This dumps the key-value pairs stored in the map. If the map is a hash table, it will show all entries.

### 1.2 Inspect BPF Programs and Attachments

List all BPF programs and their attachments:

```bash
bpftool prog show
```

To inspect a specific program (e.g., program ID `10`):

```bash
bpftool prog dump id 10
```

This shows the BPF bytecode and associated metadata.

### 1.3 Inspect Kernel Memory and Map Usage

Use `cat /proc/meminfo` to inspect memory usage, particularly the `BPF` memory sections:

```bash
grep -i bpf /proc/meminfo
```

To inspect the memory used by BPF maps, use:

```bash
bpftool map pin /sys/fs/bpf/my_map /tmp/my_map
```

Then, inspect the pinned map:

```bash
bpftool map show pinned /tmp/my_map
```

### 1.4 Monitor eBPF Events in Real-Time

Use `bpftrace` to trace BPF events in real-time:

```bash
bpftrace -e 'tracepoint:syscalls:sys_enter_open { printf("Opening file: %s\n", str(args->filename)); }'
```

This traces all `open()` system calls and prints the filename being opened.

## Exercise 2: Benchmarking & Saturation Profiling

In this exercise, we generate load and profile the performance of BPF maps under saturation.

### 2.1 Generate Load Using `perf` and `stress-ng`

First, install `stress-ng`:

```bash
apt install stress-ng
```

Then, simulate CPU and memory load to stress the system:

```bash
stress-ng --cpu 4 --timeout 60s
```

Monitor BPF map performance using `perf`:

```bash
perf stat -e bpf:map_lookup, bpf:map_update -I 1000
```

This command monitors BPF map lookup and update events every 1000 milliseconds.

### 2.2 Simulate High-Throughput Traffic with `iperf3`

Set up a server and client for network load testing:

```bash
# Server
iperf3 -s -p 5201

# Client
iperf3 -c <server-ip> -p 5201 -t 60 -u -b 100M
```

Use `tcpdump` to capture and analyze packet flow:

```bash
tcpdump -i any -n port 5201
```

### 2.3 Profile BPF Map Access Patterns

Use `perf` to profile BPF map access:

```bash
perf record -e bpf:map_lookup, bpf:map_update -g ./your_bpf_program
perf report
```

This records and reports the call graph of BPF map operations.

## Exercise 3: Fault Injection & Recovery Analysis

In this exercise, we simulate failure scenarios and analyze recovery behavior.

### 3.1 Simulate Memory Exhaustion

Use `stress-ng` to simulate memory exhaustion:

```bash
stress-ng --vm 4 --vm-bytes 1G --timeout 30s
```

Monitor BPF map behavior during memory pressure:

```bash
bpftool map show
```

If the system runs out of memory, BPF maps may fail to allocate new entries, and the kernel will log OOM events.

### 3.2 Simulate Packet Drop Using `tc` (Traffic Control)

Simulate packet loss using `tc`:

```bash
tc qdisc add dev lo root netem loss 10%
```

Then, run a packet capture:

```bash
tcpdump -i lo -n
```

Monitor BPF programs that rely on packet flow for correctness:

```bash
bpftool prog dump id <program_id>
```

### 3.3 Analyze Recovery Logs

Check kernel logs for BPF-related errors:

```bash
dmesg | grep -i bpf
```

If a BPF program crashes or fails due to a map error, it will be logged here.

## Diagnostic Cheat Sheet & Verification Checklist

| Task | CLI Command | Description |
|------|-------------|-------------|
| List all BPF maps | `bpftool map show` | Displays all loaded BPF maps |
| Dump map contents | `bpftool map dump id <map_id>` | Shows key-value pairs in a map |
| List BPF programs | `bpftool prog show` | Displays all loaded BPF programs |
| Dump program bytecode | `bpftool prog dump id <prog_id>` | Shows BPF bytecode |
| Pin a map to filesystem | `bpftool map pin id <map_id> /tmp/map_name` | Pins a map for persistence |
| Monitor BPF events | `perf stat -e bpf:*` | Monitors BPF-related system events |
| Profile BPF map access | `perf record -e bpf:* -g ./program` | Records BPF map access patterns |
| Simulate memory stress | `stress-ng --vm 4 --vm-bytes 1G` | Generates memory pressure |
| Simulate packet loss | `tc qdisc add dev lo root netem loss 10%` | Introduces packet loss |
| View kernel logs | `dmesg | grep -i bpf` | Inspects BPF-related kernel messages |

---

This lab provides a comprehensive operational verification framework for BPF maps in high-performance environments. By following these steps, practitioners can ensure that BPF-based systems are correctly configured, performant, and resilient under various load and failure conditions.
