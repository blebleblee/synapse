# Operational Verification Labs: Core

## Objective & Environment Setup

This lab guide is designed for systems engineers and SRE practitioners who must perform operational verification of core infrastructure components in Linux and BSD environments. The exercises are structured to validate the integrity, performance, and resilience of foundational subsystems such as kernel memory management, process scheduling, network stack behavior, and eBPF-based observability.

### Required CLI Tools

Before beginning, ensure the following tools are installed and available in your environment:

- `bpftool`: For inspecting eBPF programs and maps.
- `kubectl`: Kubernetes CLI for containerized environments.
- `iproute2`: Network configuration and inspection utilities.
- `tcpdump`: Packet capture and network analysis.
- `strace`: System call tracing for process behavior.
- `perf`: Performance profiling and kernel event monitoring.
- `vmstat`, `iostat`, `sar`: System resource monitoring.
- `lsof`, `ss`, `netstat`: Process and network connection inspection.
- `dmesg`, `journalctl`: Kernel log inspection.

### Environment Configuration

The lab assumes a Linux-based system running a kernel version ≥ 5.10 with support for eBPF and BTF (BPF Type Format). For containerized environments, ensure `kubectl` is configured with access to a Kubernetes cluster (e.g., minikube or a cloud provider).

To begin, verify that the kernel supports eBPF:

```bash
grep -i bpf /boot/config-$(uname -r)
```

Ensure that `CONFIG_BPF_SYSCALL=y` and `CONFIG_BPF_JIT=y` are set.

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise focuses on inspecting live system state using kernel interfaces, memory maps, and process metrics. The goal is to validate that subsystems are operating as expected under normal conditions.

### 1.1 Inspect Kernel Memory Maps and Page Tables

Use `bpftool` to inspect eBPF maps and their contents, which are critical for runtime observability.

```bash
bpftool map show
```

This command lists all eBPF maps currently loaded in the kernel. For example, a map named `stats_map` may be defined as:

```c
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);
    __type(value, struct stats);
} stats_map SEC(".maps");
```

To inspect the contents of this map:

```bash
bpftool map dump name stats_map
```

### 1.2 Inspect Virtual Memory and TLB State

Use `cat /proc/meminfo` to inspect memory usage and `cat /proc/vmstat` for virtual memory statistics:

```bash
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable)"
cat /proc/vmstat | grep -E "(pgpgin|pgpgout|pgfault|pgmajfault)"
```

To inspect the kernel's page table structure, use `perf` to trace page faults:

```bash
perf record -e page-faults -a sleep 10
perf script
```

### 1.3 Inspect Process and Thread State

Use `ps` and `top` to inspect running processes and their resource consumption:

```bash
ps aux --sort=-%cpu | head -10
top -b -n1 | head -20
```

Use `strace` to trace system calls for a specific process:

```bash
strace -p <PID> -e trace=openat,read,write -o trace.log
```

### 1.4 Inspect Network Stack and Interface Metrics

Use `ss` and `ip` to inspect active connections and network interfaces:

```bash
ss -tuln
ip addr show
ip route show
```

Use `tcpdump` to capture and analyze network traffic:

```bash
tcpdump -i any -n -c 10
```

### 1.5 Inspect Kernel Logs and System Events

Use `dmesg` and `journalctl` to inspect kernel messages and systemd logs:

```bash
dmesg | tail -20
journalctl -u <service> --since "1 hour ago"
```

## Exercise 2: Benchmarking & Saturation Profiling

This exercise involves generating synthetic load and measuring system performance under saturation. The goal is to validate that the system can handle expected workloads and identify bottlenecks.

### 2.1 CPU Saturation and Scheduling Profiling

Use `perf` to profile CPU usage and scheduling behavior:

```bash
perf record -e sched:sched_switch -a sleep 30
perf script
```

Use `stress-ng` to simulate CPU load:

```bash
stress-ng --cpu 4 --timeout 60s
```

### 2.2 Memory Allocation and Garbage Collection Profiling

Use `perf` to profile memory allocations:

```bash
perf record -e mem-loads,mem-stores -a sleep 30
perf script
```

Use `stress-ng` to simulate memory pressure:

```bash
stress-ng --vm 4 --vm-bytes 256M --timeout 60s
```

### 2.3 Network Throughput and Latency Profiling

Use `iperf3` to measure network throughput:

```bash
iperf3 -s -p 5201
iperf3 -c <server-ip> -p 5201 -t 30
```

Use `ping` to measure latency:

```bash
ping -c 100 <target-host>
```

### 2.4 Disk I/O Saturation

Use `fio` to simulate disk I/O load:

```bash
fio --name=test --direct=1 --rw=randrw --bs=4k --size=1G --numjobs=4 --runtime=60 --time_based
```

Monitor I/O with `iostat`:

```bash
iostat -x 1 10
```

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates system-level failures and analyzes the system's response and recovery behavior. The goal is to validate that the system can tolerate and recover from faults gracefully.

### 3.1 Simulate Memory Pressure and OOM Handling

Use `stress-ng` to simulate memory exhaustion:

```bash
stress-ng --vm 8 --vm-bytes 512M --timeout 30s
```

Monitor for OOM killer activity:

```bash
dmesg | grep -i "killed\|oom"
```

### 3.2 Simulate Network Partition and Recovery

Use `iptables` to simulate a network partition:

```bash
iptables -A INPUT -p tcp --dport 80 -j DROP
iptables -A OUTPUT -p tcp --sport 80 -j DROP
```

To restore connectivity:

```bash
iptables -D INPUT -p tcp --dport 80 -j DROP
iptables -D OUTPUT -p tcp --sport 80 -j DROP
```

Use `tcpdump` to observe dropped packets:

```bash
tcpdump -i any -n port 80
```

### 3.3 Simulate CPU Overload and Process Termination

Use `stress-ng` to simulate CPU overload:

```bash
stress-ng --cpu 16 --timeout 30s
```

Monitor process behavior with `top` or `htop`:

```bash
top -b -n1 | grep -E "(PID|COMMAND)"
```

### 3.4 Simulate Kernel Panic and System Recovery

Use `echo 1 > /proc/sys/kernel/panic` to enable immediate panic on kernel oops:

```bash
echo 1 > /proc/sys/kernel/panic
```

Then simulate a kernel panic:

```bash
echo c > /proc/sysrq-trigger
```

Monitor recovery logs:

```bash
journalctl -b -1
```

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Purpose |
|------|---------|---------|
| Inspect eBPF maps | `bpftool map show` | Validate BPF map state |
| Inspect kernel memory | `cat /proc/meminfo` | Check memory usage |
| Inspect page faults | `perf record -e page-faults` | Analyze memory access patterns |
| Inspect processes | `ps aux`, `top` | Monitor CPU and memory usage |
| Trace system calls | `strace -p <PID>` | Analyze process behavior |
| Inspect network connections | `ss -tuln` | Check active connections |
| Capture network traffic | `tcpdump -i any -n` | Analyze packet flow |
| Inspect kernel logs | `dmesg`, `journalctl` | Monitor system events |
| Profile CPU usage | `perf record -e sched:sched_switch` | Analyze scheduling behavior |
| Simulate memory pressure | `stress-ng --vm` | Test memory limits |
| Simulate network partition | `iptables -A DROP` | Test network resilience |
| Simulate CPU overload | `stress-ng --cpu` | Test CPU saturation |
| Monitor disk I/O | `iostat -x` | Analyze disk performance |
| Trigger kernel panic | `echo c > /proc/sysrq-trigger` | Test crash recovery |

This lab guide provides a structured approach to operational verification of core infrastructure components. By following these steps, practitioners can validate system behavior under normal and faulted conditions, ensuring robustness and reliability in production environments.
