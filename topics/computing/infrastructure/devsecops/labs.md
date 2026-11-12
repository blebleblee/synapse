# Operational Verification Labs: Core

## Objective & Environment Setup

### Required CLI Tools

* `bpftool` (eBPF inspection and management)
* `kubectl` (Kubernetes cluster management)
* `iproute2` (network interface and routing configuration)
* `tcpdump` (network packet capture and analysis)
* `strace` (system call tracing and debugging)
* `perf` (performance monitoring and profiling)

### Environment Configuration

* Install and configure a Linux/BSD environment (e.g., Ubuntu, CentOS, or FreeBSD)
* Set up a Kubernetes cluster using `kubectl` (e.g., Minikube or a cloud provider)
* Install and configure `bpftool` and `iproute2` for eBPF and network interface management
* Ensure `tcpdump` and `strace` are installed and configured for network packet capture and system call tracing

## Exercise 1: Live State & Internal Subsystem Inspection

### Inspecting Kernel Maps

```bash
# Display kernel map information
bpftool map show
```

### Inspecting Memory and Buffers

```bash
# Display memory usage and buffer information
free -h
cat /proc/meminfo
```

### Inspecting Processes and Metrics

```bash
# Display running processes and system metrics
ps -ef
top -b
```

### Inspecting Network Interface and Routing Configuration

```bash
# Display network interface and routing configuration
ip link show
ip route show
```

## Exercise 2: Benchmarking & Saturation Profiling

### Running a Benchmark Command

```bash
# Run a benchmark command (e.g., `iperf3` for network throughput)
iperf3 -c <server_ip> -t 10 -i 1
```

### Generating Load and Profiling Packet Throughput

```bash
# Generate load and profile packet throughput (e.g., using `tc` and `iperf3`)
tc qdisc add dev <interface> root tbf rate 100Mbit
tc qdisc show
iperf3 -c <server_ip> -t 10 -i 1
```

### Profiling Latency

```bash
# Profile latency (e.g., using `tcpdump` and `tc`)
tcpdump -i <interface> -n -s 0 -c 100 -W 100 -vv
tc qdisc show
```

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating a Sudden Failure

```bash
# Simulate a sudden failure (e.g., by killing a critical process)
kill -9 <process_id>
```

### Simulating a Packet Drop

```bash
# Simulate a packet drop (e.g., by configuring `tc` to drop packets)
tc qdisc add dev <interface> root netem rate 100Mbit loss 10%
tc qdisc show
```

### Simulating a Partition

```bash
# Simulate a partition (e.g., by creating a new partition and mounting it)
mkfs.ext4 /dev/sdb1
mount /dev/sdb1 /mnt
```

### Inspecting Recovery Logs

```bash
# Inspect recovery logs (e.g., using `journalctl`)
journalctl -u <service_name>
```

## Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `bpftool map show` |  | Display kernel map information |
| `free -h` |  | Display memory usage and buffer information |
| `ps -ef` |  | Display running processes |
| `top -b` |  | Display system metrics |
| `ip link show` |  | Display network interface configuration |
| `ip route show` |  | Display routing configuration |
| `iperf3 -c <server_ip> -t 10 -i 1` |  | Run a benchmark command |
| `tc qdisc add dev <interface> root tbf rate 100Mbit` |  | Generate load and profile packet throughput |
| `tcpdump -i <interface> -n -s 0 -c 100 -W 100 -vv` |  | Profile latency |
| `kill -9 <process_id>` |  | Simulate a sudden failure |
| `tc qdisc add dev <interface> root netem rate 100Mbit loss 10%` |  | Simulate a packet drop |
| `mkfs.ext4 /dev/sdb1` |  | Simulate a partition |
| `journalctl -u <service_name>` |  | Inspect recovery logs |

Note: This is a comprehensive guide for operational verification labs, covering essential CLI commands and configurations for inspecting kernel maps, memory, buffers, processes, and metrics, as well as benchmarking, saturation profiling, fault injection, and recovery analysis. The diagnostic cheat sheet and verification checklist provide a quick reference for essential CLI commands and operational flags.
