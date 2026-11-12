# Operational Verification Labs: Core

## Objective & Environment Setup

The operational verification lab for the **Core** domain within the **Infrastructure/Cloud Native** discipline is designed to provide hands-on experience in diagnosing, inspecting, and validating the behavior of core system components under real-world conditions. This lab targets practitioners and systems engineers who must understand how Linux/BSD systems behave at the kernel level, how distributed systems maintain consistency, and how to perform live diagnostics using native tools.

### Required CLI Tools

To execute the exercises in this lab, the following tools must be installed and available in the environment:

- `bpftool`: For inspecting eBPF programs and maps.
- `kubectl`: For interacting with Kubernetes clusters.
- `iproute2`: For network interface and routing inspection.
- `tcpdump`: For packet capture and network traffic analysis.
- `strace`: For tracing system calls made by processes.
- `perf`: For performance profiling and kernel-level event monitoring.
- `bpftrace`: For dynamic tracing of kernel and userspace events (optional but recommended).

Ensure that the system has root privileges or appropriate capabilities to access kernel memory and eBPF resources. The lab environment should be a Linux kernel version ≥ 5.4, with support for eBPF, and a container runtime such as containerd or Docker installed.

### Environment Configuration

Before beginning, ensure the following:

1. **Kernel Version**: Verify that the kernel supports eBPF and BTF (BPF Type Format).
   ```bash
   uname -r
   ```

2. **eBPF Support**: Confirm that eBPF is enabled.
   ```bash
   cat /proc/sys/net/core/bpf_jit_enable
   ```
   Output should be `1` for JIT compilation enabled.

3. **Kubernetes Cluster**: A running Kubernetes cluster with at least one worker node. Ensure `kubectl` is configured to communicate with the cluster.

4. **Network Interface**: Identify the primary network interface for packet capture and routing inspection.
   ```bash
   ip link show
   ```

5. **Container Runtime**: Ensure that containerd or Docker is installed and running.
   ```bash
   systemctl status containerd
   ```

With these prerequisites met, the lab can proceed with confidence in the availability of diagnostic tools and system state access.

---

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise focuses on inspecting the live state of the system’s core subsystems, including kernel memory, process state, network interfaces, and eBPF maps. These inspections are critical for understanding how the system behaves under normal operation and can be used to detect anomalies or misconfigurations.

### 1.1 Inspecting Kernel Memory and Page Tables

To examine the virtual memory layout and page table structures, we use `/proc` and `/sys` filesystems.

#### Inspect Kernel Memory Usage:
```bash
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable)"
```

#### Inspect Page Table Entries:
```bash
cat /proc/vmstat | grep -E "(pgpgin|pgpgout|pgfault|pgmajfault)"
```

#### Analyze Memory Allocation:
```bash
cat /proc/zoneinfo
```

This provides detailed information on memory zones and fragmentation.

### 1.2 Inspecting Running Processes and System Calls

Use `ps` and `strace` to inspect running processes and their system call behavior.

#### List all running processes:
```bash
ps aux --sort=-%cpu | head -10
```

#### Trace system calls for a specific process:
```bash
strace -p <PID> -e trace=openat,read,write -o trace.log
```

This will log all file-related system calls for a given process.

### 1.3 Inspecting Network Interfaces and Routing

Use `iproute2` to inspect network state.

#### Show network interfaces:
```bash
ip link show
```

#### Show routing table:
```bash
ip route show
```

#### Show active connections:
```bash
ss -tuln
```

### 1.4 Inspecting eBPF Maps and Programs

Use `bpftool` to inspect eBPF programs and maps, which are critical for tracing and monitoring kernel behavior.

#### List all loaded eBPF programs:
```bash
bpftool prog show
```

#### List all eBPF maps:
```bash
bpftool map show
```

#### Inspect a specific map:
```bash
bpftool map dump id <map_id>
```

#### Inspect program details:
```bash
bpftool prog dump xlated id <prog_id>
```

These commands provide visibility into how eBPF programs are structured and how data flows through them.

---

## Exercise 2: Benchmarking & Saturation Profiling

This exercise involves generating load on the system and profiling its behavior under saturation. The goal is to simulate real-world conditions and observe how the system handles resource contention.

### 2.1 CPU Saturation Benchmark

Use `stress-ng` to simulate CPU load and observe system behavior.

#### Install stress-ng:
```bash
apt install stress-ng
```

#### Generate CPU load:
```bash
stress-ng --cpu 4 --timeout 60s
```

#### Monitor CPU usage during load:
```bash
top -b -n 1 | grep "Cpu(s)"
```

### 2.2 Memory Saturation Benchmark

Use `stress-ng` to stress memory allocation.

#### Generate memory load:
```bash
stress-ng --vm 4 --vm-bytes 1G --timeout 60s
```

#### Monitor memory usage:
```bash
free -h
```

### 2.3 Network Throughput Profiling

Use `iperf3` to simulate network load and measure throughput.

#### Install iperf3:
```bash
apt install iperf3
```

#### Start iperf3 server:
```bash
iperf3 -s
```

#### Start iperf3 client:
```bash
iperf3 -c <server_ip> -t 60
```

#### Monitor network traffic:
```bash
tcpdump -i any -n port 5201
```

### 2.4 Kernel Performance Profiling with `perf`

Use `perf` to profile kernel-level events and identify bottlenecks.

#### Profile system-wide:
```bash
perf record -g -e syscalls:sys_enter_open,syscalls:sys_enter_read,syscalls:sys_enter_write -a
```

#### Analyze results:
```bash
perf report
```

This provides a call graph of system calls and helps identify hotspots in kernel execution.

---

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates system faults such as network partitions, process termination, or memory corruption, and then analyzes the system's recovery behavior.

### 3.1 Simulating Network Partition with `iptables`

Use `iptables` to simulate a network partition.

#### Block all traffic to a specific IP:
```bash
iptables -A OUTPUT -d <target_ip> -j DROP
```

#### Monitor traffic:
```bash
tcpdump -i any host <target_ip>
```

#### Restore traffic:
```bash
iptables -D OUTPUT -d <target_ip> -j DROP
```

### 3.2 Simulating Process Termination

Use `kill` to terminate a process and observe recovery behavior.

#### Identify a process:
```bash
ps aux | grep <process_name>
```

#### Terminate the process:
```bash
kill -TERM <PID>
```

#### Monitor process restart (if managed by systemd):
```bash
journalctl -u <service_name> -f
```

### 3.3 Simulating Memory Corruption with `dd`

Use `dd` to simulate memory pressure and observe system behavior.

#### Fill disk with zeros:
```bash
dd if=/dev/zero of=/tmp/fill bs=1M count=1000
```

#### Monitor disk usage:
```bash
df -h
```

#### Clean up:
```bash
rm /tmp/fill
```

### 3.4 Analyzing Recovery Logs

After simulating faults, analyze system logs to understand recovery behavior.

#### Check kernel logs:
```bash
dmesg | tail -50
```

#### Check systemd logs:
```bash
journalctl -u <service_name> --since "10 minutes ago"
```

#### Monitor system stability:
```bash
uptime
```

This exercise helps verify that the system can recover gracefully from faults and maintain operational integrity.

---

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Purpose |
|------|---------|---------|
| Check kernel version | `uname -r` | Verify eBPF support |
| Check memory usage | `cat /proc/meminfo` | Monitor memory health |
| List processes | `ps aux` | Identify running processes |
| Trace system calls | `strace -p <PID>` | Diagnose process behavior |
| Inspect network interfaces | `ip link show` | Verify network state |
| Inspect routing table | `ip route show` | Diagnose routing issues |
| List eBPF programs | `bpftool prog show` | Inspect kernel tracing |
| List eBPF maps | `bpftool map show` | Inspect data flow |
| Monitor CPU usage | `top` or `htop` | Identify CPU bottlenecks |
| Monitor memory usage | `free -h` | Monitor memory saturation |
| Profile system calls | `perf record -e syscalls:*` | Identify kernel hotspots |
| Simulate network partition | `iptables -A OUTPUT -d <IP> -j DROP` | Test network resilience |
| Monitor network traffic | `tcpdump` | Capture packet flow |
| Check system logs | `dmesg` or `journalctl` | Diagnose system behavior |

This checklist provides a structured approach to diagnosing and verifying the core operational state of a Linux/BSD system, ensuring that all subsystems are functioning as expected under both normal and faulted conditions.
