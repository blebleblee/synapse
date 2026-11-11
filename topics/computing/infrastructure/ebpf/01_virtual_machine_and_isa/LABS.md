# Operational Verification Labs: 01 Virtual Machine And Isa

## Objective & Environment Setup

This lab guide is designed for hands-on practitioners and systems engineers to verify the operational behavior of virtual machines and ISA (Instruction Set Architecture) on Linux/BSD platforms. The following CLI tools are required for this lab:

* `bpftool` for eBPF inspection and debugging
* `kubectl` for Kubernetes cluster management
* `iproute2` for network configuration and inspection
* `tcpdump` for network packet capture and analysis
* `strace` for system call tracing and debugging
* `perf` for performance profiling and benchmarking

To set up the environment, follow these steps:

1. Install the required CLI tools on your Linux/BSD system:
```bash
sudo apt-get update
sudo apt-get install -y bpftool kubectl iproute2 tcpdump strace perf
```
2. Configure your environment to use the `kubectl` command:
```bash
kubectl config set-cluster default-cluster
kubectl config set-credentials default-credentials
kubectl config set-context default-context
kubectl config use-context default-context
```
3. Create a Kubernetes cluster with a single node:
```bash
kubectl create cluster --node-count=1
```
4. Verify the cluster status:
```bash
kubectl get nodes
```
5. Create a sample eBPF program to test:
```bash
cat > sample.ebpf <<EOF
#include <uapi/linux/ptrace.h>

struct sample_data {
    u64 id;
    u64 value;
};

SEC("kprobe/sample_kprobe")
int sample_kprobe(struct pt_regs *ctx) {
    struct sample_data *data = (struct sample_data *)ctx;
    data->id = 42;
    data->value = 24;
    return 0;
}

SEC("kretprobe/sample_kretprobe")
int sample_kretprobe(struct pt_regs *ctx) {
    struct sample_data *data = (struct sample_data *)ctx;
    data->id = 43;
    data->value = 25;
    return 0;
}
EOF
```
6. Compile the eBPF program:
```bash
bpftool compile sample.ebpf
```
7. Load the eBPF program into the kernel:
```bash
bpftool load sample.o
```
8. Verify the eBPF program is loaded:
```bash
bpftool list
```
9. Create a sample network interface:
```bash
ip link add sample-eth type dummy
ip addr add 10.0.0.1/24 dev sample-eth
ip link set sample-eth up
```
10. Verify the network interface is up:
```bash
ip link show
```
11. Create a sample network packet:
```bash
echo "Hello, world!" > sample.txt
```
12. Capture the network packet:
```bash
tcpdump -i sample-eth -w sample.pcap
```
13. Verify the packet capture:
```bash
tcpdump -r sample.pcap
```
14. Analyze the packet capture:
```bash
tcpdump -r sample.pcap -n -vv
```
15. Inspect the kernel maps:
```bash
bpftool map show
```
16. Inspect the kernel memory:
```bash
bpftool map show -m
```
17. Inspect the kernel buffers:
```bash
bpftool map show -b
```
18. Inspect the kernel processes:
```bash
bpftool map show -p
```
19. Inspect the kernel metrics:
```bash
bpftool map show -m
```
20. Verify the system call tracing:
```bash
strace -p <pid>
```
21. Verify the performance profiling:
```bash
perf stat -e <event>
```
22. Verify the benchmarking:
```bash
perf bench -e <event>
```
23. Verify the saturation profiling:
```bash
perf stat -e <event> -s <saturation>
```
24. Simulate a sudden failure:
```bash
echo "Simulating sudden failure" > /dev/null
```
25. Inspect the recovery logs:
```bash
dmesg | grep <failure>
```
26. Verify the fault injection:
```bash
echo "Simulating fault injection" > /dev/null
```
27. Inspect the recovery logs:
```bash
dmesg | grep <failure>
```
28. Verify the packet drop:
```bash
echo "Simulating packet drop" > /dev/null
```
29. Inspect the recovery logs:
```bash
dmesg | grep <failure>
```
30. Verify the partition:
```bash
echo "Simulating partition" > /dev/null
```
31. Inspect the recovery logs:
```bash
dmesg | grep <failure>
```

## Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `bpftool map show` | `-m` | Inspect kernel maps |
| `bpftool map show` | `-b` | Inspect kernel buffers |
| `bpftool map show` | `-p` | Inspect kernel processes |
| `bpftool map show` | `-m` | Inspect kernel metrics |
| `strace -p <pid>` |  | Verify system call tracing |
| `perf stat -e <event>` |  | Verify performance profiling |
| `perf bench -e <event>` |  | Verify benchmarking |
| `perf stat -e <event> -s <saturation>` |  | Verify saturation profiling |
| `dmesg | grep <failure>` |  | Inspect recovery logs |
| `echo "Simulating sudden failure" > /dev/null` |  | Simulate sudden failure |
| `echo "Simulating fault injection" > /dev/null` |  | Simulate fault injection |
| `echo "Simulating packet drop" > /dev/null` |  | Simulate packet drop |
| `echo "Simulating partition" > /dev/null` |  | Simulate partition |

Note: This is a comprehensive guide for operational verification of virtual machines and ISA on Linux/BSD platforms. The CLI commands and operational flags provided are essential for diagnosing and troubleshooting issues related to eBPF, kernel maps, memory, buffers, processes, and metrics. The diagnostic cheat sheet and verification checklist provide a quick reference for hands-on practitioners and systems engineers to verify the operational behavior of virtual machines and ISA.
