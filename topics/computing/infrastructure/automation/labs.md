# Operational Verification Labs: Core

## Objective & Environment Setup

This lab guide is designed for hands-on practitioners and systems engineers to verify the operational integrity of Linux/BSD systems. The following CLI tools are required for this lab:

* `bpftool`
* `kubectl`
* `iproute2`
* `tcpdump`
* `strace`
* `perf`

### Environment Configuration

To set up the environment, create a new Linux/BSD VM or container with the following configuration:

* Kernel version: 5.10 or later
* Distribution: Ubuntu 20.04 or later, CentOS 8 or later, or FreeBSD 13 or later
* Networking: Enable IP forwarding and set up a bridge interface (e.g., `br0`)
* Storage: Allocate at least 10 GB of disk space for the VM or container

### Required Packages and Tools

Install the required packages and tools using the following commands:

```bash
sudo apt-get update
sudo apt-get install -y bpftool kubectl iproute2 tcpdump strace perf
```

### Verification Environment

Create a verification environment by setting up a Kubernetes cluster using `kubectl`:

```bash
kubectl create cluster --config=kubeconfig.yaml
```

Replace `kubeconfig.yaml` with your actual Kubernetes configuration file.

## Exercise 1: Live State & Internal Subsystem Inspection

### Inspect Kernel Maps

Use `bpftool` to inspect the kernel maps:

```bash
bpftool map show
```

This command displays the list of kernel maps, including their names, IDs, and sizes.

### Inspect Memory

Use `free` and `top` to inspect the system memory:

```bash
free -m
top -c
```

These commands display the system memory usage and the list of running processes, respectively.

### Inspect Buffers

Use `ip` to inspect the network buffers:

```bash
ip link show
ip addr show
```

These commands display the list of network interfaces and their addresses, respectively.

### Inspect Processes

Use `ps` and `top` to inspect the running processes:

```bash
ps -ef
top -c
```

These commands display the list of running processes and their resource usage, respectively.

### Inspect Metrics

Use `sysctl` to inspect the system metrics:

```bash
sysctl -a
```

This command displays the list of system metrics, including their names and values.

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmarking

Use `iperf` to benchmark the network throughput:

```bash
iperf -c <server_ip> -t 10 -i 1
```

Replace `<server_ip>` with the IP address of the server.

### Saturation Profiling

Use `tcpdump` to profile the network saturation:

```bash
tcpdump -i any -n -s 0 -c 100 -W 100 -vv -X
```

This command captures 100 packets and displays the packet headers and contents.

### Load Generation

Use `stress` to generate load on the system:

```bash
stress -c 4 -m 4 -t 10
```

This command generates 4 CPU-bound and 4 memory-bound threads for 10 seconds.

## Exercise 3: Fault Injection & Recovery Analysis

### Fault Injection

Use `iptables` to inject a packet drop fault:

```bash
iptables -A INPUT -p tcp --dport 22 -j DROP
```

This command drops all incoming TCP packets on port 22.

### Recovery Analysis

Use `dmesg` to analyze the system logs during recovery:

```bash
dmesg | grep "packet drop"
```

This command displays the system logs related to packet drops.

## Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Description | Flags |
| --- | --- | --- |
| `bpftool map show` | Inspect kernel maps |  |
| `free -m` | Inspect system memory |  |
| `top -c` | Inspect running processes |  |
| `ip link show` | Inspect network buffers |  |
| `ps -ef` | Inspect running processes |  |
| `sysctl -a` | Inspect system metrics |  |
| `iperf -c <server_ip> -t 10 -i 1` | Benchmark network throughput |  |
| `tcpdump -i any -n -s 0 -c 100 -W 100 -vv -X` | Profile network saturation |  |
| `stress -c 4 -m 4 -t 10` | Generate load on system |  |
| `iptables -A INPUT -p tcp --dport 22 -j DROP` | Inject packet drop fault |  |
| `dmesg | grep "packet drop"` | Analyze system logs during recovery |  |

Note: This is a basic diagnostic cheat sheet and verification checklist. You may need to modify the CLI commands and flags based on your specific environment and requirements.
