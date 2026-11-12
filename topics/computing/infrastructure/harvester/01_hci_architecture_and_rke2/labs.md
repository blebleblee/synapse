# Operational Verification Labs: 01 Hci Architecture And Rke2

## Objective & Environment Setup

In this lab, we will perform operational verification of the **HCI (Hardware-Container Infrastructure)** architecture and **RKE2** (Rancher Kubernetes Engine 2) deployment within a Harvester environment. The objective is to validate the system's operational integrity through live inspection, performance benchmarking, and fault injection techniques.

### Prerequisites

Before beginning, ensure the following tools are installed and available in your environment:

- `bpftool`: eBPF inspection utility.
- `kubectl`: Kubernetes CLI for cluster interaction.
- `iproute2`: Network configuration and inspection.
- `tcpdump`: Packet capture and analysis.
- `strace`: System call tracing.
- `perf`: Performance profiling.
- `harvester`: Harvester CLI for infrastructure management.
- `rke2`: RKE2 binary for Kubernetes control plane verification.

### Environment Configuration

The lab assumes a Harvester-managed Kubernetes cluster running RKE2 with the following configuration:

```bash
# Verify Harvester cluster status
harvester cluster status

# Verify RKE2 version
rke2 --version

# Verify Kubernetes API server connectivity
kubectl cluster-info

# Check node status
kubectl get nodes -o wide

# Check RKE2 service status
systemctl status rke2-server
```

All commands in this lab are executed from a node within the Harvester-managed cluster, typically the control plane node.

---

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise focuses on inspecting the live state of the system, including kernel subsystems, memory, network buffers, and process states. The goal is to validate that the system is operating as expected and to detect any anomalies in real-time.

### 1.1 Kernel Map Inspection

We begin by inspecting the kernel's eBPF maps, which are critical for RKE2’s network policy enforcement and container networking.

```bash
# List all eBPF maps
bpftool map list

# Inspect a specific map (e.g., a BPF map used for network policy enforcement)
bpftool map dump id <map_id>
```

> Replace `<map_id>` with the actual ID from `bpftool map list`.

### 1.2 Memory and Process Inspection

Next, we inspect memory usage and running processes to ensure no resource exhaustion or unexpected behavior.

```bash
# View memory usage
free -h

# View top memory-consuming processes
ps aux --sort=-%mem | head -10

# Inspect kernel memory allocations
cat /proc/meminfo | grep -E "(MemTotal|MemFree|Cached|Buffers)"

# Inspect RKE2 processes
ps aux | grep rke2
```

### 1.3 Network Interface and Routing Inspection

We now inspect network interfaces and routing tables to ensure proper connectivity and routing behavior.

```bash
# View network interfaces and their status
ip addr show

# View routing table
ip route show

# Inspect network packet drops
cat /proc/net/dev

# Check for active connections
ss -tuln
```

### 1.4 Kubernetes Resource Inspection

We verify the state of Kubernetes resources to ensure that the cluster is operating correctly.

```bash
# Check pod status
kubectl get pods -A

# Check service status
kubectl get svc -A

# Check node conditions
kubectl describe nodes

# Inspect RKE2-specific CRDs
kubectl get crds | grep -E "(rke2|harvester)"
```

---

## Exercise 2: Benchmarking & Saturation Profiling

In this exercise, we simulate load on the system to evaluate performance under saturation. This includes generating network traffic, CPU load, and memory pressure.

### 2.1 Network Throughput Benchmarking

We use `iperf3` to benchmark network throughput between nodes.

```bash
# Start iperf3 server on one node
iperf3 -s -D

# Run client from another node
iperf3 -c <server_ip> -t 30 -P 10
```

### 2.2 CPU Load Generation

We simulate CPU load using `stress-ng` to evaluate system responsiveness.

```bash
# Install stress-ng
apt install stress-ng

# Generate CPU load
stress-ng --cpu 4 --timeout 60s
```

### 2.3 Memory Pressure Simulation

We simulate memory pressure using `stress-ng` and monitor system behavior.

```bash
# Allocate memory
stress-ng --vm 2 --vm-bytes 512M --timeout 60s
```

### 2.4 Performance Profiling with `perf`

We profile system performance using `perf` to identify bottlenecks.

```bash
# Profile RKE2 processes
perf record -p $(pgrep rke2-server) -g -o rke2_perf.data

# Analyze the profile
perf report -i rke2_perf.data
```

---

## Exercise 3: Fault Injection & Recovery Analysis

In this exercise, we simulate system faults such as network partitions, process termination, and node failures to evaluate the system's resilience and recovery mechanisms.

### 3.1 Network Partition Simulation

We simulate a network partition using `iptables` to isolate a node.

```bash
# Block traffic to a specific node
iptables -A OUTPUT -d <target_node_ip> -j DROP

# Verify the rule is active
iptables -L OUTPUT -n -v
```

### 3.2 Process Termination and Recovery

We terminate a critical RKE2 process and observe recovery behavior.

```bash
# Identify RKE2 process
ps aux | grep rke2

# Terminate the process
kill -9 <rke2_pid>

# Monitor recovery
journalctl -u rke2-server -f
```

### 3.3 Node Failure Simulation

We simulate a node failure by stopping the RKE2 service and observing cluster behavior.

```bash
# Stop RKE2 service
systemctl stop rke2-server

# Check cluster status
kubectl get nodes

# Restart RKE2 service
systemctl start rke2-server

# Monitor recovery
kubectl get nodes -w
```

### 3.4 Log Analysis for Recovery Events

We analyze system logs to confirm recovery events and fault handling.

```bash
# Check RKE2 logs
journalctl -u rke2-server --since "10 minutes ago"

# Check Kubernetes events
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Purpose |
|------|---------|---------|
| Check RKE2 version | `rke2 --version` | Verify installed version |
| Check cluster status | `kubectl cluster-info` | Confirm API server accessibility |
| List nodes | `kubectl get nodes -o wide` | Verify node health |
| Inspect RKE2 service | `systemctl status rke2-server` | Confirm service operation |
| List eBPF maps | `bpftool map list` | Inspect BPF maps |
| Dump BPF map | `bpftool map dump id <map_id>` | Inspect BPF map contents |
| Check memory usage | `free -h` | Monitor memory consumption |
| Check top processes | `ps aux --sort=-%mem` | Identify memory hogs |
| Inspect network interfaces | `ip addr show` | Verify network configuration |
| Inspect routing table | `ip route show` | Validate routing behavior |
| Monitor network drops | `cat /proc/net/dev` | Detect packet loss |
| Inspect active connections | `ss -tuln` | Check open ports |
| List pods | `kubectl get pods -A` | Verify pod status |
| List services | `kubectl get svc -A` | Confirm service availability |
| Describe nodes | `kubectl describe nodes` | Check node conditions |
| Inspect CRDs | `kubectl get crds` | Validate custom resources |
| Run iperf3 benchmark | `iperf3 -c <ip>` | Test network throughput |
| Generate CPU load | `stress-ng --cpu 4` | Simulate CPU pressure |
| Generate memory load | `stress-ng --vm 2` | Simulate memory pressure |
| Profile RKE2 | `perf record -p <pid>` | Analyze performance |
| Simulate network partition | `iptables -A OUTPUT -d <ip> -j DROP` | Test network resilience |
| Terminate RKE2 process | `kill -9 <pid>` | Test process recovery |
| Stop RKE2 service | `systemctl stop rke2-server` | Simulate node failure |
| Check logs | `journalctl -u rke2-server` | Monitor recovery events |
| Check Kubernetes events | `kubectl get events` | Identify system events |

---

This lab provides a comprehensive operational verification framework for the HCI architecture and RKE2 deployment. By following these steps, practitioners can ensure that the system is functioning correctly under normal and faulted conditions.
