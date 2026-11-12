# Operational Verification Labs: 02 Virtual Machines And Kubevirt

## Objective & Environment Setup

### Objective
The objective of this lab is to perform a comprehensive operational verification of virtual machines (VMs) and KubeVirt in a Kubernetes environment. This lab will guide you through live state inspection, benchmarking, and fault injection to ensure the robustness and performance of your virtualized infrastructure.

### Environment Setup
Ensure you have the following tools installed on your system:
- `bpftool`: For eBPF program inspection.
- `kubectl`: For Kubernetes cluster management.
- `iproute2`: For network interface configuration and inspection.
- `tcpdump`: For network packet capture and analysis.
- `strace`: For system call tracing.
- `perf`: For performance analysis and profiling.

Additionally, you need a running Kubernetes cluster with KubeVirt installed. Ensure that your cluster is properly configured and that you have the necessary permissions to deploy and manage VMs.

## Exercise 1: Live State & Internal Subsystem Inspection

### Kernel Maps Inspection
Kernel maps are essential for understanding the state of eBPF programs and their interactions with the kernel. Use `bpftool` to inspect these maps.

```bash
# List all eBPF maps
sudo bpftool map list

# Inspect a specific map by ID (replace <map_id> with the actual ID)
sudo bpftool map dump id <map_id>
```

### Memory and Buffer Inspection
Inspecting memory and buffers can help you understand the state of your VMs and the underlying kernel.

```bash
# List all processes and their memory usage
ps aux --sort=-%mem

# Inspect memory usage of a specific process (replace <pid> with the actual PID)
pmap <pid>

# Inspect kernel memory usage
free -h

# Inspect slab cache usage
slabtop
```

### Process Inspection
Use `strace` to trace system calls made by a specific process, which can be useful for debugging and understanding process behavior.

```bash
# Trace system calls of a specific process (replace <pid> with the actual PID)
sudo strace -p <pid>
```

### Metrics Inspection
KubeVirt provides metrics that can be inspected using `kubectl`.

```bash
# Get metrics for all VMs
kubectl get vms -o json | jq '.items[].status.metrics'

# Get metrics for a specific VM (replace <vm_name> with the actual VM name)
kubectl get vm <vm_name> -o json | jq '.status.metrics'
```

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmarking VM Performance
Use `perf` to benchmark the performance of your VMs.

```bash
# Record performance data for a specific process (replace <pid> with the actual PID)
sudo perf record -p <pid> -g -- sleep 60

# Analyze the recorded performance data
sudo perf report
```

### Load Generation
Generate load on your VMs to test their performance under stress.

```bash
# Install stress-ng for load generation
sudo apt-get install stress-ng

# Generate CPU and memory load
stress-ng --cpu 4 --vm 2 --vm-bytes 1G --timeout 60s
```

### Packet Throughput and Latency Profiling
Use `tcpdump` to capture and analyze network packets for throughput and latency.

```bash
# Capture packets on a specific interface (replace <interface> with the actual interface name)
sudo tcpdump -i <interface> -w capture.pcap

# Analyze the captured packets
tcpdump -r capture.pcap
```

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Sudden Failure
Simulate a sudden failure by terminating a VM process.

```bash
# List all VM processes
ps aux | grep qemu-kvm

# Terminate a specific VM process (replace <pid> with the actual PID)
sudo kill -9 <pid>
```

### Simulating Packet Drop
Simulate packet drop using `tc` (part of `iproute2`).

```bash
# Add a netem rule to drop 10% of packets on a specific interface (replace <interface> with the actual interface name)
sudo tc qdisc add dev <interface> root netem loss 10%

# Remove the netem rule
sudo tc qdisc del dev <interface> root
```

### Simulating Partition
Simulate a network partition by isolating a VM from the network.

```bash
# Isolate a VM by removing its network interface (replace <interface> with the actual interface name)
sudo ip link set <interface> down

# Restore the network interface
sudo ip link set <interface> up
```

### Inspecting Recovery Logs
Inspect the logs to verify the recovery process.

```bash
# Get logs for all VMs
kubectl logs -l kubevirt.io/vm

# Get logs for a specific VM (replace <vm_name> with the actual VM name)
kubectl logs -l kubevirt.io/vm=<vm_name>
```

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command          | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `bpftool map list` | List all eBPF maps.                                                       |
| `bpftool map dump id <map_id>` | Dump the contents of a specific eBPF map.                       |
| `ps aux --sort=-%mem` | List all processes sorted by memory usage.                              |
| `pmap <pid>` | Inspect memory usage of a specific process.                                 |
| `free -h` | Display memory usage in a human-readable format.                              |
| `slabtop` | Display slab cache usage in real-time.                                      |
| `strace -p <pid>` | Trace system calls of a specific process.                                 |
| `kubectl get vms -o json` | Get metrics for all VMs in JSON format.                             |
| `kubectl get vm <vm_name> -o json` | Get metrics for a specific VM in JSON format.             |
| `perf record -p <pid> -g -- sleep 60` | Record performance data for a specific process.       |
| `perf report` | Analyze recorded performance data.                                          |
| `stress-ng --cpu 4 --vm 2 --vm-bytes 1G --timeout 60s` | Generate CPU and memory load.         |
| `tcpdump -i <interface> -w capture.pcap` | Capture packets on a specific interface.          |
| `tcpdump -r capture.pcap` | Analyze captured packets.                                           |
| `sudo kill -9 <pid>` | Terminate a specific process.                                           |
| `sudo tc qdisc add dev <interface> root netem loss 10%` | Simulate packet drop on an interface.   |
| `sudo tc qdisc del dev <interface> root` | Remove a netem rule.                              |
| `sudo ip link set <interface> down` | Isolate a VM by disabling its network interface.        |
| `sudo ip link set <interface> up` | Restore a VM's network interface.                         |
| `kubectl logs -l kubevirt.io/vm` | Get logs for all VMs.                                       |
| `kubectl logs -l kubevirt.io/vm=<vm_name>` | Get logs for a specific VM.                     |

By following this lab guide, you will gain a deep understanding of the operational state, performance, and fault tolerance of your virtual machines and KubeVirt environment.
