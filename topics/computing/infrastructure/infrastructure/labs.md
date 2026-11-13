Operational Verification Labs: Infrastructure
==============================================

### Objective and Environment Setup

The objective of this guide is to provide hands-on experience with operational verification techniques specific to infrastructure. This involves using real tools to diagnose and troubleshoot issues in a cloud-native environment. To begin, ensure you have the following tools installed:

* `kubectl` (version 1.20 or later)
* `iproute2` (version 5.10 or later)
* `etcdctl` (version 3.5 or later)
* `crictl` (version 1.21 or later)
* `helm` (version 3.7 or later)

Additionally, install the following diagnostic instruments:

* `ss` (version 1.0 or later)
* `ethtool` (version 5.10 or later)
* `tcpdump` (version 4.9 or later)
* `perf` (version 5.10 or later)
* `strace` (version 5.10 or later)
* `bpftool` (version 5.10 or later)

### Exercise 1: Live State and Internal Subsystem Inspection

In this exercise, we will inspect the live state of a Kubernetes cluster and its internal subsystems.

#### Step 1: Inspect Node Status

Run the following command to inspect the status of all nodes in the cluster:
```bash
kubectl get nodes -o wide
```
This command provides information about each node, including its IP address, operating system, and kernel version.

#### Step 2: Inspect Pod Status

Run the following command to inspect the status of all pods in the cluster:
```bash
kubectl get pods -A -o wide
```
This command provides information about each pod, including its name, namespace, and status.

#### Step 3: Inspect Network Interface

Run the following command to inspect the network interface of a specific node:
```bash
ip -s link show eth0
```
This command provides information about the network interface, including its MAC address, IP address, and MTU.

#### Step 4: Inspect etcd Cluster

Run the following command to inspect the etcd cluster:
```bash
etcdctl member list
```
This command provides information about each etcd member, including its IP address and port.

### Exercise 2: Benchmarking and Saturation Profiling

In this exercise, we will benchmark and profile the performance of a Kubernetes cluster under saturation conditions.

#### Step 1: Run Benchmarking Tool

Run the following command to run the benchmarking tool:
```bash
kubectl run benchmarking-tool --image=nginx --port=80
```
This command creates a new pod with the `nginx` image and exposes port 80.

#### Step 2: Run Saturation Test

Run the following command to run the saturation test:
```bash
kubectl exec -it benchmarking-tool -- perf stat -e CPU_CLK_UNHALTED.THREAD -a sleep 10
```
This command runs the `perf` tool to measure the CPU clock frequency of the `benchmarking-tool` pod.

#### Step 3: Analyze Results

Run the following command to analyze the results:
```bash
kubectl logs benchmarking-tool
```
This command provides information about the benchmarking tool, including its output and any errors.

### Exercise 3: Fault Injection and Recovery Analysis

In this exercise, we will inject faults into a Kubernetes cluster and analyze its recovery behavior.

#### Step 1: Inject Fault

Run the following command to inject a fault into the cluster:
```bash
kubectl exec -it node1 -- ethtool -p eth0
```
This command injects a fault into the `eth0` interface of node1.

#### Step 2: Analyze Recovery

Run the following command to analyze the recovery behavior:
```bash
kubectl get events -o wide
```
This command provides information about the events that occurred during the fault injection, including any errors or warnings.

### Diagnostic Cheat Sheet and Verification Checklist

| Tool | Command | Description |
| --- | --- | --- |
| `kubectl` | `get nodes` | Inspect node status |
| `kubectl` | `get pods` | Inspect pod status |
| `ip` | `link show` | Inspect network interface |
| `etcdctl` | `member list` | Inspect etcd cluster |
| `perf` | `stat` | Benchmark and profile performance |
| `strace` | `run` | Analyze system calls |
| `bpftool` | `list` | Analyze BPF programs |

Verification Checklist:

* Ensure all tools are installed and up-to-date.
* Run each exercise in sequence, following the instructions provided.
* Analyze the output and results of each exercise.
* Verify that the cluster is functioning correctly after each exercise.

Note: This is a sample guide and should not be used in production without proper testing and validation.
