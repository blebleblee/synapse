# Operational Verification Labs: Core

## Objective & Environment Setup

The operational verification lab for the **Core** domain in **Infrastructure/Hyperconverged Infrastructure** is designed to provide hands-on experience in diagnosing and inspecting the fundamental subsystems of a Linux-based hyperconverged environment. This lab assumes a modern Linux kernel (5.10+) running on a bare-metal or virtualized system with access to root privileges, and a network interface capable of packet capture and traffic generation.

### Required CLI Tools

The following tools must be installed and available in the system's `$PATH`:

- `bpftool`: eBPF inspection and manipulation utility.
- `kubectl`: Kubernetes CLI for cluster state inspection.
- `iproute2`: Network configuration and inspection tools.
- `tcpdump`: Packet capture and network traffic analysis.
- `strace`: System call tracing for process behavior.
- `perf`: Performance profiling and kernel event tracing.
- `lsof`, `ss`, `vmstat`, `iostat`, `sar`, `dmesg`, `journalctl`: System diagnostics utilities.

### Environment Configuration

Ensure the following environment is configured:

1. **Kernel Version**: `uname -r` should return a kernel version >= 5.10.
2. **eBPF Support**: `bpftool` must be functional (`bpftool version`).
3. **Kubernetes Cluster**: A running cluster with `kubectl` configured (`kubectl cluster-info`).
4. **Network Interface**: A working interface (e.g., `eth0`) for packet capture and traffic generation.
5. **Root Access**: All commands require root privileges for full inspection and manipulation.

---

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise focuses on inspecting the live state of the system's core subsystems, including kernel memory, process state, network stack, and eBPF programs. The goal is to understand how these subsystems interact under normal operation.

### 1.1 Inspect Kernel Memory and Page Tables

```bash
# View kernel memory usage and slab allocations
cat /proc/meminfo | grep -E "(MemTotal|MemFree|Slab)"
cat /proc/slabinfo | head -20

# Inspect virtual memory mappings for a specific process
cat /proc/<PID>/maps

# View page table entries (requires kernel debug symbols)
cat /proc/kallsyms | grep -E "(pgd|pud|pmd|pte)"
```

### 1.2 Inspect Kernel Maps and eBPF Programs

```bash
# List all loaded eBPF programs
bpftool prog show

# List BPF maps
bpftool map show

# Inspect a specific BPF map (e.g., map ID 1)
bpftool map dump id 1

# View kernel ring buffer maps
bpftool map show type ringbuf
```

### 1.3 Inspect Running Processes and Scheduling

```bash
# View running processes with CPU and memory usage
ps aux --sort=-%cpu | head -10

# Inspect CFS scheduler state
cat /proc/schedstat

# View process scheduling latency
perf stat -e sched:sched_switch,syscalls:sys_enter_clone,syscalls:sys_enter_execve -I 1000
```

### 1.4 Inspect Network Stack and Interfaces

```bash
# View network interface statistics
ip -s link show eth0

# Inspect routing table
ip route show

# View active connections
ss -tuln

# Inspect network packet drops
cat /proc/net/dev
cat /proc/net/snmp
```

### 1.5 Inspect Kernel Logs and System Events

```bash
# View kernel ring buffer
dmesg | tail -50

# View systemd journal logs
journalctl -u <service-name> --since "1 hour ago"

# Inspect kernel events with perf
perf record -e kprobe:* -a
perf script
```

---

## Exercise 2: Benchmarking & Saturation Profiling

This exercise involves generating load on the system and profiling performance under saturation to detect bottlenecks and resource contention.

### 2.1 CPU Saturation and Benchmarking

```bash
# Run CPU-intensive workload using stress-ng
stress-ng --cpu 4 --timeout 60s

# Profile CPU usage with perf
perf top -p <PID>

# Benchmark CPU performance with sysbench
sysbench --test=cpu --cpu-max-prime=20000 run
```

### 2.2 Memory Saturation and Heap Profiling

```bash
# Allocate memory using stress-ng
stress-ng --vm 4 --vm-bytes 256M --timeout 60s

# Monitor memory usage with vmstat
vmstat 1 10

# Profile memory allocation with perf
perf record -e mem-loads,mem-stores -a
perf report
```

### 2.3 Network Throughput and Latency Profiling

```bash
# Generate network traffic using iperf3
iperf3 -s -p 5201 &  # server
iperf3 -c <server-ip> -p 5201 -t 60 -w 128K

# Capture network traffic with tcpdump
tcpdump -i eth0 -w capture.pcap port 5201

# Analyze packet latency with ping
ping -c 100 <target-ip>
```

### 2.4 Disk I/O Saturation

```bash
# Generate disk I/O load
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000

# Monitor I/O with iostat
iostat -x 1 10

# Profile disk I/O with perf
perf record -e block:block_rq_complete -a
perf script
```

---

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates system-level failures such as network partitions, memory corruption, or process termination, and analyzes the system's recovery behavior.

### 3.1 Simulate Network Partition

```bash
# Drop all packets to a specific IP
iptables -A OUTPUT -d <target-ip> -j DROP

# Restore traffic
iptables -D OUTPUT -d <target-ip> -j DROP
```

### 3.2 Simulate Memory Exhaustion

```bash
# Allocate large memory blocks to simulate OOM
stress-ng --vm 1 --vm-bytes 1G --timeout 30s

# Monitor OOM killer logs
dmesg | grep -i "killed\|oom"
```

### 3.3 Simulate Process Termination and Recovery

```bash
# Kill a process and monitor recovery
kill -9 <PID>

# Monitor process restarts with journalctl
journalctl -u <service-name> --since "1 minute ago"
```

### 3.4 Simulate Kernel Panic (Use with Caution)

```bash
# Trigger a kernel panic (only for testing)
echo c > /proc/sysrq-trigger
```

### 3.5 Analyze Recovery Logs

```bash
# Inspect system logs after fault injection
dmesg | tail -100

# View systemd recovery logs
journalctl --since "1 minute ago" | grep -i "restarted\|failed\|recovered"
```

---

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Purpose |
|------|---------|---------|
| View memory usage | `cat /proc/meminfo` | Assess memory allocation |
| Inspect slab allocations | `cat /proc/slabinfo` | Identify kernel memory fragmentation |
| View BPF programs | `bpftool prog show` | Inspect eBPF program state |
| View BPF maps | `bpftool map show` | Inspect BPF map contents |
| Monitor CPU usage | `perf top` | Identify CPU bottlenecks |
| Monitor network stats | `ip -s link show` | Analyze network throughput |
| Monitor disk I/O | `iostat -x` | Identify disk contention |
| Capture network traffic | `tcpdump` | Analyze packet flow |
| Monitor system logs | `dmesg`, `journalctl` | Diagnose kernel and service events |
| Stress CPU | `stress-ng --cpu 4` | Simulate CPU load |
| Stress memory | `stress-ng --vm 4` | Simulate memory pressure |
| Generate network load | `iperf3` | Benchmark network throughput |
| Monitor process state | `ps aux`, `ss` | Inspect process and connection state |
| Trigger OOM | `stress-ng --vm-bytes 1G` | Simulate memory exhaustion |
| Simulate network drop | `iptables -A OUTPUT -d <IP> -j DROP` | Simulate network partition |

This lab provides a comprehensive framework for diagnosing and verifying the operational integrity of core infrastructure components, enabling practitioners to build robust, resilient systems.
