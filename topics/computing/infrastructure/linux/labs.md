# Operational Verification Labs: Core

## Objective & Environment Setup

The Operational Verification Labs for the Core domain are designed to provide hands-on experience in diagnosing and inspecting Linux kernel subsystems, system performance, and fault behavior using real-world CLI tools and diagnostic techniques. These labs are intended for practitioners and systems engineers who seek to understand how the Linux kernel operates under various conditions, and how to verify its behavior through live inspection, benchmarking, and fault injection.

### Required CLI Tools

Before beginning, ensure the following tools are installed and available in your environment:

- `bpftool`: For inspecting eBPF programs and maps.
- `kubectl`: For Kubernetes cluster interaction (if applicable).
- `iproute2`: For network interface and routing inspection.
- `tcpdump`: For packet capture and network traffic analysis.
- `strace`: For system call tracing.
- `perf`: For performance profiling and kernel event monitoring.
- `ltrace`: For library call tracing (optional but useful).
- `vmstat`, `iostat`, `sar`: For system resource monitoring.
- `sysctl`: For kernel parameter inspection and tuning.
- `dmesg`: For kernel log inspection.
- `ps`, `top`, `htop`: For process monitoring.
- `cat`, `grep`, `awk`, `sed`: For text processing.

### Environment Configuration

Ensure the following environment is set up:

- A Linux system running a recent kernel version (5.10+ recommended).
- Root or sudo access for system-level inspection.
- Network access for packet capture and network diagnostics.
- Optional: A Kubernetes cluster with `kubectl` configured.

### Lab Setup Script

```bash
#!/bin/bash

# Setup script for Core Operational Verification Labs
echo "Setting up Core Operational Verification Lab environment..."

# Install required tools
sudo apt update
sudo apt install -y iproute2 tcpdump strace perf sysstat ltrace

# Enable kernel debugging (if needed)
echo 'kernel.printk = 7 4 1 3' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Create a test directory for lab outputs
mkdir -p /tmp/lab_output
cd /tmp/lab_output

echo "Lab environment ready."
```

---

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise focuses on inspecting the live state of the Linux kernel and its subsystems using CLI tools. The goal is to observe kernel memory, process state, network interfaces, and system metrics in real time.

### 1.1 Inspecting Kernel Memory and Buffers

```bash
# View kernel memory usage and buffers
cat /proc/meminfo | grep -E "(MemTotal|MemFree|Buffers|Cached)"
```

```bash
# Inspect kernel page cache and slab usage
cat /proc/slabinfo | head -20
```

### 1.2 Process and Thread Inspection

```bash
# List all running processes with full command line
ps aux --forest
```

```bash
# Inspect process memory maps
cat /proc/<PID>/maps
```

```bash
# View process I/O statistics
cat /proc/<PID>/io
```

### 1.3 Network Interface and Routing Inspection

```bash
# View network interfaces and their status
ip addr show
```

```bash
# Inspect routing table
ip route show
```

```bash
# Monitor network traffic in real time
tcpdump -i any -n
```

### 1.4 Kernel Log Inspection

```bash
# View kernel messages in real time
dmesg -w
```

```bash
# Inspect kernel ring buffer with timestamps
dmesg --time
```

### 1.5 System Metrics and Performance

```bash
# Monitor CPU and memory usage in real time
vmstat 1 5
```

```bash
# Monitor I/O statistics
iostat -x 1 5
```

```bash
# Monitor system load and process activity
sar -u 1 5
```

---

## Exercise 2: Benchmarking & Saturation Profiling

This exercise involves generating load on the system and profiling performance to understand saturation points and bottlenecks.

### 2.1 CPU Saturation Benchmark

```bash
# Generate CPU load using stress-ng
stress-ng --cpu 4 --timeout 30s
```

```bash
# Monitor CPU usage during load
perf stat -I 1000 -e cpu-cycles,instructions,cache-misses,context-switches sleep 30
```

### 2.2 Memory Saturation Benchmark

```bash
# Allocate memory using stress-ng
stress-ng --vm 4 --vm-bytes 256M --timeout 30s
```

```bash
# Monitor memory usage and swap activity
watch -n 1 'free -h && cat /proc/meminfo | grep -E "(MemTotal|MemFree|SwapTotal|SwapFree)"'
```

### 2.3 Network Throughput Benchmark

```bash
# Generate network traffic using iperf3
iperf3 -s &
iperf3 -c <server_ip> -t 30
```

```bash
# Capture network throughput using tcpdump
tcpdump -i any -n -s 0 -w /tmp/network_trace.pcap
```

### 2.4 Disk I/O Saturation

```bash
# Generate disk I/O load using fio
fio --name=test --ioengine=libaio --direct=1 --bs=4k --size=1G --numjobs=4 --runtime=30 --time_based --group_reporting
```

```bash
# Monitor disk I/O with iostat
iostat -x 1 10
```

---

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates system failures such as network partitions, memory exhaustion, or process termination, and analyzes the system's response and recovery behavior.

### 3.1 Simulating Network Partition

```bash
# Drop all packets to a specific IP using iptables
sudo iptables -A OUTPUT -d <target_ip> -j DROP
```

```bash
# Monitor network behavior with tcpdump
tcpdump -i any -n host <target_ip>
```

```bash
# Restore network access
sudo iptables -D OUTPUT -d <target_ip> -j DROP
```

### 3.2 Simulating Memory Exhaustion

```bash
# Allocate memory until system runs out
while true; do
  dd if=/dev/zero of=/tmp/fill bs=1M count=1000 2>/dev/null || break
done
```

```bash
# Monitor system behavior with dmesg
dmesg -w | grep -i "oom\|kill"
```

```bash
# Clean up memory allocation
rm -f /tmp/fill
```

### 3.3 Simulating Process Termination

```bash
# Start a long-running process
sleep 3600 &
PID=$!
```

```bash
# Kill the process and inspect logs
kill $PID
dmesg | grep -i "killed\|signal"
```

### 3.4 Simulating Kernel Panic (Advanced)

```bash
# Trigger a kernel panic (use with caution)
echo c > /proc/sysrq-trigger
```

```bash
# Monitor kernel logs for panic
dmesg -w | grep -i panic
```

---

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Description |
|------|---------|-------------|
| View memory usage | `cat /proc/meminfo` | Inspect total, free, and cached memory |
| View slab usage | `cat /proc/slabinfo` | Check kernel memory allocation |
| Monitor processes | `ps aux --forest` | View process tree and resource usage |
| Inspect process maps | `cat /proc/<PID>/maps` | View memory mapping of a process |
| View network interfaces | `ip addr show` | Inspect network interface configuration |
| View routing table | `ip route show` | Inspect routing decisions |
| Capture network traffic | `tcpdump -i any -n` | Capture live network packets |
| Monitor kernel logs | `dmesg -w` | View kernel messages in real time |
| Monitor CPU usage | `vmstat 1 5` | Monitor CPU and memory usage |
| Monitor I/O stats | `iostat -x 1 5` | Monitor disk I/O performance |
| Monitor system load | `sar -u 1 5` | Monitor system load and CPU usage |
| Generate CPU load | `stress-ng --cpu 4 --timeout 30s` | Simulate CPU load |
| Generate memory load | `stress-ng --vm 4 --vm-bytes 256M --timeout 30s` | Simulate memory pressure |
| Generate network load | `iperf3 -c <server_ip> -t 30` | Benchmark network throughput |
| Generate disk I/O load | `fio --name=test --ioengine=libaio --direct=1 --bs=4k --size=1G --numjobs=4 --runtime=30 --time_based` | Simulate disk I/O |
| Drop network traffic | `iptables -A OUTPUT -d <target_ip> -j DROP` | Simulate network partition |
| Monitor for OOM | `dmesg -w | grep -i "oom\|kill"` | Detect out-of-memory events |
| Trigger kernel panic | `echo c > /proc/sysrq-trigger` | Simulate system crash |

---

This Operational Verification Lab guide provides a comprehensive set of hands-on exercises for diagnosing and inspecting Linux systems using real-world tools and techniques. Each exercise is designed to build practical skills in system monitoring, performance profiling, and fault analysis, enabling practitioners to confidently operate and troubleshoot Linux infrastructure.
