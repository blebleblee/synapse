# Operational Verification Labs: Core

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience in diagnosing and verifying the operational state of a Linux-based infrastructure. This includes inspecting kernel subsystems, benchmarking performance, and analyzing fault recovery mechanisms. The lab will equip you with practical skills using real Linux/BSD CLI tools, inspection utilities, and reproduction scripts.

### Environment Setup
Ensure you have the following tools installed on your Linux/BSD system:

- **bpftool**: For eBPF program inspection and debugging.
- **kubectl**: For Kubernetes cluster management and inspection.
- **iproute2**: For network configuration and inspection.
- **tcpdump**: For network packet capture and analysis.
- **strace**: For system call tracing.
- **perf**: For performance profiling and analysis.

#### Installation Commands
For Debian-based systems (e.g., Ubuntu):
```bash
sudo apt-get update
sudo apt-get install -y bpftool kubectl iproute2 tcpdump strace linux-tools-common linux-tools-generic linux-tools-`uname -r`
```

For Red Hat-based systems (e.g., CentOS, Fedora):
```bash
sudo yum install -y bpftool kubectl iproute2 tcpdump strace perf
```

For Arch Linux:
```bash
sudo pacman -S bpftool kubectl iproute2 tcpdump strace perf
```

## Exercise 1: Live State & Internal Subsystem Inspection

### Kernel Maps Inspection
Kernel maps are essential for understanding the state of eBPF programs. Use `bpftool` to inspect these maps.

```bash
sudo bpftool map list
```

This command lists all eBPF maps currently loaded in the kernel. You can inspect a specific map by its ID:

```bash
sudo bpftool map dump id <map_id>
```

Replace `<map_id>` with the ID of the map you wish to inspect.

### Memory Inspection
Inspecting memory usage and virtual memory mappings is crucial for understanding system performance and resource allocation. Use `pmap` to view memory mappings of a process:

```bash
pmap <pid>
```

Replace `<pid>` with the process ID of the target process.

### Buffer Inspection
Inspect kernel buffers to understand system logs and messages. Use `dmesg` to view kernel ring buffer messages:

```bash
dmesg
```

For real-time monitoring, use:

```bash
dmesg -w
```

### Process Inspection
Inspecting processes and their states is fundamental for system diagnostics. Use `ps` to list running processes:

```bash
ps aux
```

For detailed inspection of a specific process, use `strace`:

```bash
sudo strace -p <pid>
```

Replace `<pid>` with the process ID of the target process.

### Metrics Inspection
Inspect system metrics using `perf` to profile performance and identify bottlenecks:

```bash
sudo perf stat -a sleep 10
```

This command collects performance metrics for 10 seconds across all CPUs.

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmark Commands
Benchmarking is essential for understanding system performance under load. Use `sysbench` to benchmark CPU, memory, and file I/O performance:

```bash
sudo apt-get install -y sysbench
sysbench cpu run
sysbench memory run
sysbench fileio --file-total-size=1G prepare
sysbench fileio --file-total-size=1G --file-test-mode=rndrw run
sysbench fileio --file-total-size=1G cleanup
```

### Load Generation
Generate network load using `iperf3` to measure packet throughput and latency:

```bash
sudo apt-get install -y iperf3
# On server machine
iperf3 -s
# On client machine
iperf3 -c <server_ip>
```

Replace `<server_ip>` with the IP address of the server machine.

### Packet Throughput Profiling
Use `tcpdump` to capture and analyze network packets for throughput and latency:

```bash
sudo tcpdump -i eth0 -w capture.pcap
```

Replace `eth0` with the appropriate network interface.

### Latency Profiling
Profile network latency using `ping`:

```bash
ping -c 10 <target_ip>
```

Replace `<target_ip>` with the IP address of the target machine.

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Sudden Failure
Simulate a sudden failure by killing a critical process:

```bash
sudo kill -9 <pid>
```

Replace `<pid>` with the process ID of the target process.

### Simulating Packet Drop
Simulate packet drops using `tc` (Traffic Control):

```bash
sudo tc qdisc add dev eth0 root netem loss 10%
```

Replace `eth0` with the appropriate network interface.

### Simulating Partition
Simulate network partition by isolating a node using `iptables`:

```bash
sudo iptables -A INPUT -s <target_ip> -j DROP
sudo iptables -A OUTPUT -d <target_ip> -j DROP
```

Replace `<target_ip>` with the IP address of the target machine.

### Inspecting Recovery Logs
Inspect recovery logs using `journalctl`:

```bash
sudo journalctl -xe
```

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command     | Description                                                                 | Example                                                                 |
|-------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------|
| `bpftool`   | Inspect and debug eBPF programs and maps.                                   | `sudo bpftool map list`                                                   |
| `kubectl`   | Manage and inspect Kubernetes clusters.                                     | `kubectl get pods`                                                      |
| `iproute2`  | Configure and inspect network interfaces and routes.                        | `ip addr show`                                                          |
| `tcpdump`   | Capture and analyze network packets.                                        | `sudo tcpdump -i eth0 -w capture.pcap`                                  |
| `strace`    | Trace system calls and signals.                                             | `sudo strace -p <pid>`                                                  |
| `perf`      | Profile performance and identify bottlenecks.                               | `sudo perf stat -a sleep 10`                                            |
| `sysbench`  | Benchmark CPU, memory, and file I/O performance.                            | `sysbench cpu run`                                                      |
| `iperf3`    | Measure network throughput and latency.                                     | `iperf3 -c <server_ip>`                                                 |
| `ping`      | Measure network latency.                                                    | `ping -c 10 <target_ip>`                                                |
| `tc`        | Simulate network conditions like packet loss.                               | `sudo tc qdisc add dev eth0 root netem loss 10%`                          |
| `iptables`  | Simulate network partition by dropping packets.                             | `sudo iptables -A INPUT -s <target_ip> -j DROP`                         |
| `journalctl`| Inspect system logs and recovery logs.                                      | `sudo journalctl -xe`                                                   |

This lab guide provides a comprehensive set of tools and commands to diagnose and verify the operational state of a Linux-based infrastructure. By following these exercises, you will gain practical experience in system diagnostics, performance benchmarking, and fault recovery analysis.
