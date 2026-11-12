# Operational Verification Labs: 04 Multus And Vlan Networking

## Objective & Environment Setup

### Objective
The objective of this lab is to perform operational verification of Multus CNI (Container Network Interface) and VLAN networking in a Kubernetes cluster. This lab will guide you through live state inspection, benchmarking, and fault injection to ensure that Multus and VLAN networking are functioning correctly.

### Environment Setup
Ensure that the following tools are installed on your system:
- `bpftool`
- `kubectl`
- `iproute2`
- `tcpdump`
- `strace`
- `perf`

Additionally, you need a Kubernetes cluster with Multus CNI and VLAN networking configured. The cluster should have at least two nodes, and VLAN interfaces should be properly set up on each node.

## Exercise 1: Live State & Internal Subsystem Inspection

### Inspecting Kernel Maps
Multus CNI uses eBPF for efficient network management. To inspect the eBPF maps, use `bpftool`:

```sh
sudo bpftool map list
```

Identify the map related to Multus and inspect its contents:

```sh
sudo bpftool map dump pinned /sys/fs/bpf/multus_map
```

### Inspecting Memory and Buffers
Use `iproute2` to inspect network interfaces and their associated buffers:

```sh
ip link show
ip addr show
```

Inspect the VLAN interfaces specifically:

```sh
ip link show type vlan
```

### Inspecting Processes and Metrics
Use `strace` to trace system calls made by the Multus CNI plugin:

```sh
sudo strace -p $(pgrep multus-cni)
```

Use `perf` to profile the performance of the Multus CNI plugin:

```sh
sudo perf top -p $(pgrep multus-cni)
```

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmarking Network Throughput
Use `iperf` to benchmark network throughput between two pods connected via VLAN interfaces. First, deploy two pods:

```sh
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: iperf-server
  namespace: default
spec:
  containers:
  - name: iperf-server
    image: networkstatic/iperf
    command: ["iperf", "-s"]
---
apiVersion: v1
kind: Pod
metadata:
  name: iperf-client
  namespace: default
spec:
  containers:
  - name: iperf-client
    image: networkstatic/iperf
    command: ["iperf", "-c", "iperf-server"]
EOF
```

Monitor the throughput:

```sh
kubectl logs iperf-client
```

### Packet Throughput and Latency Profiling
Use `tcpdump` to capture and analyze network packets between the pods:

```sh
sudo tcpdump -i <vlan-interface> -w capture.pcap
```

Analyze the captured packets:

```sh
tcpdump -r capture.pcap
```

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Packet Drop
Use `tc` to simulate packet drop on the VLAN interface:

```sh
sudo tc qdisc add dev <vlan-interface> root netem loss 10%
```

Monitor the impact on network performance:

```sh
kubectl logs iperf-client
```

### Simulating Partition
Simulate a network partition by disabling the VLAN interface:

```sh
sudo ip link set <vlan-interface> down
```

Monitor the recovery process:

```sh
kubectl get pods -w
```

Re-enable the VLAN interface:

```sh
sudo ip link set <vlan-interface> up
```

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command          | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `bpftool map list` | List all eBPF maps.                                                       |
| `bpftool map dump pinned /sys/fs/bpf/multus_map` | Dump contents of the Multus eBPF map.       |
| `ip link show`   | Show all network interfaces.                                                |
| `ip addr show`   | Show IP addresses assigned to network interfaces.                           |
| `ip link show type vlan` | Show VLAN interfaces.                                                 |
| `strace -p <pid>` | Trace system calls made by a process.                                     |
| `perf top -p <pid>` | Profile performance of a process.                                       |
| `iperf -s`       | Start an iperf server.                                                      |
| `iperf -c <server>` | Start an iperf client connecting to the server.                           |
| `tcpdump -i <interface> -w <file>` | Capture packets on a network interface.                 |
| `tcpdump -r <file>` | Read and analyze captured packets.                                      |
| `tc qdisc add dev <interface> root netem loss <percentage>%` | Simulate packet loss.             |
| `ip link set <interface> down` | Disable a network interface.                                    |
| `ip link set <interface> up` | Enable a network interface.                                       |

By following this lab guide, you will gain a comprehensive understanding of Multus CNI and VLAN networking in a Kubernetes cluster, ensuring that your network setup is robust and reliable.
