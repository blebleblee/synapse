# Operational Verification Labs: 06 Dynamic Tracing And Kprobes

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with dynamic tracing and kprobes in a Linux environment. This will involve using tools such as `bpftool`, `strace`, `perf`, and `tcpdump` to inspect kernel state, benchmark performance, and analyze fault recovery mechanisms.

### Environment Setup
Ensure that the following tools are installed on your Linux system:
- `bpftool`: For eBPF program inspection and management.
- `strace`: For tracing system calls and signals.
- `perf`: For performance analysis and profiling.
- `tcpdump`: For network packet capture and analysis.
- `kubectl`: If you are working within a Kubernetes environment.
- `iproute2`: For network interface configuration and inspection.

Additionally, ensure that your kernel has eBPF support enabled. You can verify this by checking the kernel configuration:
```bash
grep CONFIG_BPF /boot/config-$(uname -r)
```
You should see output indicating that eBPF is enabled.

## Exercise 1: Live State & Internal Subsystem Inspection

### Inspecting Kernel Maps
Kernel maps are a fundamental part of eBPF programs. We will use `bpftool` to inspect these maps.

1. **List all eBPF maps:**
   ```bash
   sudo bpftool map list
   ```

2. **Inspect a specific map by its ID:**
   ```bash
   sudo bpftool map dump id <map_id>
   ```

### Inspecting Kernel Functions with Kprobes
Kprobes allow us to insert probes into kernel functions. We will use `bpftool` to attach a kprobe to a kernel function and inspect its behavior.

1. **Attach a kprobe to the `sys_open` function:**
   ```bash
   sudo bpftool prog loadall kprobe.o /sys/fs/bpf/kprobe type kprobe pinmaps /sys/fs/bpf/maps
   sudo bpftool prog attach pinned /sys/fs/bpf/kprobe kprobe func sys_open
   ```

2. **Inspect the attached kprobe:**
   ```bash
   sudo bpftool prog list
   ```

### Inspecting Process State with `strace`
`strace` is a powerful tool for tracing system calls and signals. We will use it to inspect the system calls made by a process.

1. **Run a simple program and trace its system calls:**
   ```bash
   strace ls
   ```

### Inspecting Network Traffic with `tcpdump`
`tcpdump` is used to capture and analyze network packets. We will use it to inspect network traffic on a specific interface.

1. **Capture packets on the `eth0` interface:**
   ```bash
   sudo tcpdump -i eth0
   ```

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmarking System Calls with `perf`
`perf` is a versatile tool for performance analysis. We will use it to benchmark system calls.

1. **Benchmark the `open` system call:**
   ```bash
   sudo perf stat -e 'syscalls:sys_enter_open' ls
   ```

### Generating Load with `stress-ng`
`stress-ng` is a tool for stress testing and benchmarking. We will use it to generate load on the system.

1. **Install `stress-ng`:**
   ```bash
   sudo apt-get install stress-ng
   ```

2. **Generate CPU load:**
   ```bash
   sudo stress-ng --cpu 4 --timeout 60s
   ```

3. **Generate I/O load:**
   ```bash
   sudo stress-ng --io 4 --timeout 60s
   ```

### Profiling Network Throughput with `iperf`
`iperf` is a tool for measuring network performance. We will use it to measure network throughput.

1. **Install `iperf`:**
   ```bash
   sudo apt-get install iperf
   ```

2. **Start the `iperf` server:**
   ```bash
   iperf -s
   ```

3. **Start the `iperf` client:**
   ```bash
   iperf -c <server_ip>
   ```

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Packet Drops with `tc`
`tc` (Traffic Control) is a tool for controlling traffic on network interfaces. We will use it to simulate packet drops.

1. **Simulate packet drops on the `eth0` interface:**
   ```bash
   sudo tc qdisc add dev eth0 root netem loss 10%
   ```

2. **Remove the packet drop simulation:**
   ```bash
   sudo tc qdisc del dev eth0 root
   ```

### Simulating Process Failures with `kill`
We will simulate process failures by sending signals to processes.

1. **Find the PID of a process:**
   ```bash
   pgrep sshd
   ```

2. **Send a SIGKILL signal to the process:**
   ```bash
   sudo kill -9 <pid>
   ```

3. **Inspect the system logs for recovery actions:**
   ```bash
   sudo journalctl -xe
   ```

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command      | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `bpftool`    | Inspect and manage eBPF programs and maps.                                  |
| `strace`     | Trace system calls and signals.                                             |
| `perf`       | Performance analysis and profiling.                                         |
| `tcpdump`    | Capture and analyze network packets.                                        |
| `stress-ng`  | Stress test and benchmark system resources.                                 |
| `iperf`      | Measure network performance.                                                |
| `tc`         | Control traffic on network interfaces.                                      |
| `kill`       | Send signals to processes.                                                  |
| `journalctl` | Inspect system logs.                                                        |

### Verification Checklist

- **Kernel Maps Inspection:**
  - List all eBPF maps.
  - Inspect a specific map by its ID.

- **Kprobes Inspection:**
  - Attach a kprobe to a kernel function.
  - Inspect the attached kprobe.

- **System Call Tracing:**
  - Trace system calls made by a process using `strace`.

- **Network Traffic Inspection:**
  - Capture and analyze network packets using `tcpdump`.

- **System Call Benchmarking:**
  - Benchmark system calls using `perf`.

- **Load Generation:**
  - Generate CPU and I/O load using `stress-ng`.

- **Network Throughput Profiling:**
  - Measure network throughput using `iperf`.

- **Packet Drop Simulation:**
  - Simulate packet drops on a network interface using `tc`.

- **Process Failure Simulation:**
  - Simulate process failures by sending signals.
  - Inspect system logs for recovery actions.

By completing these exercises, you will gain practical experience with dynamic tracing and kprobes, enabling you to diagnose and optimize system performance and reliability.
