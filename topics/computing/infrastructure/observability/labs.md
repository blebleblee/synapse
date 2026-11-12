# Operational Verification Labs: Core

## Objective & Environment Setup

This lab guide is designed for systems engineers and practitioners tasked with verifying the operational integrity of core infrastructure components in Linux and BSD environments. The exercises are structured to validate kernel subsystems, resource utilization, and fault resilience through live inspection, benchmarking, and controlled failure injection. The environment must be configured with the following tools:

- `bpftool`: eBPF inspection and management.
- `kubectl`: Kubernetes cluster interaction.
- `iproute2`: Network interface and routing inspection.
- `tcpdump`: Packet capture and analysis.
- `strace`: System call tracing.
- `perf`: Performance profiling.
- `sysctl`: Kernel parameter inspection and tuning.

All commands are executed in a Linux environment with root privileges. The lab assumes a standard Ubuntu 22.04 LTS or FreeBSD 13.2 system with default kernel configurations. For Kubernetes, a minimal cluster with at least one worker node is required.

### Environment Configuration

To begin, ensure the following kernel modules and settings are enabled:

```bash
# Load required kernel modules
modprobe bpf
modprobe ip6_tables

# Enable kernel parameters for eBPF
echo 1 > /proc/sys/net/core/bpf_jit_enable
echo 1 > /proc/sys/net/core/bpf_jit_harden

# Verify eBPF JIT is enabled
cat /proc/sys/net/core/bpf_jit_enable
```

For Kubernetes, ensure that `kubectl` is configured to access a running cluster:

```bash
kubectl cluster-info
kubectl get nodes
```

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise focuses on inspecting the live state of core kernel subsystems, including memory, process scheduling, and network state. The commands below provide a comprehensive view of the system's internal state.

### 1.1 Kernel Memory Map Inspection

```bash
# Inspect kernel memory allocation
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|Buffers|Cached)"
```

### 1.2 Process and Thread State

```bash
# List all running processes with CPU and memory usage
ps aux --sort=-%cpu | head -10

# Inspect process memory maps
cat /proc/1/maps | head -20

# Trace system calls for a specific process
strace -p 1 -c
```

### 1.3 Network Interface and Routing Tables

```bash
# Display network interfaces and their status
ip addr show

# Inspect routing table
ip route show

# Monitor network packet drops
cat /proc/net/dev
```

### 1.4 eBPF Program Inspection

```bash
# List all loaded eBPF programs
bpftool prog show

# Inspect BTF information for loaded programs
bpftool prog dump xlated id 1
```

### 1.5 Kernel Ring Buffer and Log Inspection

```bash
# View kernel log buffer
dmesg | tail -50

# Monitor kernel messages in real-time
journalctl -f
```

## Exercise 2: Benchmarking & Saturation Profiling

This exercise involves generating load on the system and profiling performance to understand saturation points and bottlenecks.

### 2.1 CPU and Memory Saturation

```bash
# Generate CPU load using stress-ng
stress-ng --cpu 4 --timeout 60s

# Generate memory load
stress-ng --vm 4 --vm-bytes 512M --timeout 60s
```

### 2.2 Network Throughput and Latency

```bash
# Generate network traffic using iperf3
iperf3 -s -D

# On another node, run client
iperf3 -c <server-ip> -t 60

# Monitor network performance
perf stat -I 1000 -e net.core.somaxconn,net.ipv4.tcp_max_syn_backlog
```

### 2.3 Disk I/O Profiling

```bash
# Generate disk I/O load
dd if=/dev/zero of=/tmp/testfile bs=1M count=1000

# Profile I/O using iostat
iostat -x 1 10
```

### 2.4 System Call Overhead Profiling

```bash
# Profile system calls using strace
strace -c -o /tmp/syscall_profile.txt ls /tmp

# Analyze the output
cat /tmp/syscall_profile.txt
```

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates system failures and evaluates the system's ability to recover and maintain service availability.

### 3.1 Simulating Memory Pressure

```bash
# Force memory pressure using oom-killer
echo 1 > /proc/sys/vm/oom_kill_allocating_task

# Monitor for OOM events
journalctl -k | grep -i oom
```

### 3.2 Network Partition Simulation

```bash
# Drop all packets to a specific IP
iptables -A OUTPUT -d <target-ip> -j DROP

# Monitor dropped packets
tcpdump -i any host <target-ip> -w /tmp/dropped.pcap
```

### 3.3 Process Termination and Recovery

```bash
# Kill a critical process
kill -9 1

# Monitor recovery logs
journalctl -u systemd --since "1 minute ago"
```

### 3.4 Kernel Panic Simulation (Use with Caution)

```bash
# Trigger a kernel panic (only for testing)
echo c > /proc/sysrq-trigger
```

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Purpose |
|------|---------|---------|
| Inspect memory usage | `cat /proc/meminfo` | Monitor memory allocation |
| List running processes | `ps aux` | Identify active processes |
| Trace system calls | `strace -p <pid>` | Analyze system call behavior |
| Inspect network interfaces | `ip addr show` | Verify network configuration |
| Monitor kernel logs | `dmesg \| tail` | Diagnose kernel-level issues |
| List eBPF programs | `bpftool prog show` | Validate BPF program state |
| Generate CPU load | `stress-ng --cpu 4` | Stress CPU subsystem |
| Generate memory load | `stress-ng --vm 4` | Stress memory subsystem |
| Monitor network throughput | `iperf3 -c <ip>` | Measure network performance |
| Profile disk I/O | `iostat -x 1 10` | Analyze disk performance |
| Monitor system calls | `strace -c ls /tmp` | Profile syscall overhead |

This guide provides a structured approach to operational verification of core infrastructure components. Each exercise is designed to be executed in sequence, with outputs used to validate system behavior under various conditions. The commands are fully executable and provide actionable insights into system health and performance.
