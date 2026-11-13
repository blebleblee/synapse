Operational Verification Labs: Distributed Systems
=====================================================

### Objective and Environment Setup

This comprehensive guide takes you on a hands-on journey to master the operational verification of distributed systems. By the end of this tutorial, you will be equipped with the skills to diagnose and troubleshoot complex distributed systems using real-world tools and frameworks.

To begin, ensure you have the following tools installed on your system:

* `kubectl` (version 1.22 or later)
* `iproute2` (version 5.15 or later)
* `etcdctl` (version 3.5 or later)
* `crictl` (version 1.22 or later)
* `helm` (version 3.7 or later)
* `ss` (version 1.0 or later)
* `ethtool` (version 5.15 or later)
* `tcpdump` (version 4.99 or later)
* `perf` (version 5.15 or later)
* `strace` (version 5.15 or later)
* `bpftool` (version 5.15 or later)

Create a Kubernetes cluster using the following command:
```bash
kubectl create cluster --name distributed-systems
```
Verify the cluster is up and running:
```bash
kubectl get nodes
```

### Exercise 1: Live State and Internal Subsystem Inspection

In this exercise, you will inspect the live state of your distributed system and analyze the internal subsystems.

1. **Inspect the node's network configuration**:
```bash
ip -s link
```
This command displays the node's network configuration, including the IP addresses, MAC addresses, and MTU values.

2. **Verify the pod's network configuration**:
```bash
kubectl get pods -A
```
This command displays a list of all pods in the cluster, including their IP addresses and network configuration.

3. **Inspect the pod's network traffic**:
```bash
tcpdump -i any -s 0 -c 100
```
This command captures and displays the first 100 packets of network traffic on any interface.

4. **Analyze the pod's system calls**:
```bash
strace -p <pod_id>
```
Replace `<pod_id>` with the ID of the pod you want to analyze.

5. **Verify the pod's resource utilization**:
```bash
kubectl top pod <pod_name>
```
Replace `<pod_name>` with the name of the pod you want to analyze.

### Exercise 2: Benchmarking and Saturation Profiling

In this exercise, you will benchmark and profile the performance of your distributed system under saturation conditions.

1. **Benchmark the pod's network throughput**:
```bash
iperf3 -c <pod_ip> -t 10 -p 5201
```
Replace `<pod_ip>` with the IP address of the pod you want to benchmark.

2. **Profile the pod's CPU utilization**:
```bash
perf stat -e cpu-clock -p <pod_id>
```
Replace `<pod_id>` with the ID of the pod you want to profile.

3. **Profile the pod's memory utilization**:
```bash
perf stat -e cache-misses -p <pod_id>
```
Replace `<pod_id>` with the ID of the pod you want to profile.

4. **Verify the pod's resource limits**:
```bash
kubectl describe pod <pod_name>
```
Replace `<pod_name>` with the name of the pod you want to analyze.

### Exercise 3: Fault Injection and Recovery Analysis

In this exercise, you will inject faults into your distributed system and analyze its recovery behavior.

1. **Inject a network fault**:
```bash
ethtool -p <interface_name>
```
Replace `<interface_name>` with the name of the interface you want to inject the fault into.

2. **Inject a CPU fault**:
```bash
perf stat -e cpu-clock -p <pod_id>
```
Replace `<pod_id>` with the ID of the pod you want to inject the fault into.

3. **Inject a memory fault**:
```bash
bpftool map show
```
This command displays a list of all BPF maps in the system.

4. **Verify the pod's recovery behavior**:
```bash
kubectl get pods -A
```
This command displays a list of all pods in the cluster, including their recovery status.

### Diagnostic Cheat Sheet and Verification Checklist

| Diagnostic Tool | Command | Description |
| --- | --- | --- |
| `ip -s link` | `ip -s link` | Inspect node's network configuration |
| `ss -tipm` | `ss -tipm` | Verify pod's network configuration |
| `kubectl get pods -A` | `kubectl get pods -A` | Verify pod's network configuration |
| `tcpdump -i any -s 0 -c 100` | `tcpdump -i any -s 0 -c 100` | Inspect pod's network traffic |
| `strace -p <pod_id>` | `strace -p <pod_id>` | Analyze pod's system calls |
| `kubectl top pod <pod_name>` | `kubectl top pod <pod_name>` | Verify pod's resource utilization |
| `iperf3 -c <pod_ip> -t 10 -p 5201` | `iperf3 -c <pod_ip> -t 10 -p 5201` | Benchmark pod's network throughput |
| `perf stat -e cpu-clock -p <pod_id>` | `perf stat -e cpu-clock -p <pod_id>` | Profile pod's CPU utilization |
| `perf stat -e cache-misses -p <pod_id>` | `perf stat -e cache-misses -p <pod_id>` | Profile pod's memory utilization |
| `kubectl describe pod <pod_name>` | `kubectl describe pod <pod_name>` | Verify pod's resource limits |
| `ethtool -p <interface_name>` | `ethtool -p <interface_name>` | Inject network fault |
| `perf stat -e cpu-clock -p <pod_id>` | `perf stat -e cpu-clock -p <pod_id>` | Inject CPU fault |
| `bpftool map show` | `bpftool map show` | Inject memory fault |
| `kubectl get pods -A` | `kubectl get pods -A` | Verify pod's recovery behavior |

Note: This is a comprehensive guide and the exercises are designed to be performed in sequence. Make sure to complete each exercise before moving on to the next one.
