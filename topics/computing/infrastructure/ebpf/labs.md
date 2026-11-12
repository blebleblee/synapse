# Operational Verification Labs: 04 Co Re And BTF Relocation

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with CO-RE (Compile Once – Run Everywhere) and BTF (BPF Type Format) relocations in eBPF programs. This lab will guide you through the process of compiling, deploying, and verifying eBPF programs that leverage CO-RE and BTF relocations to ensure compatibility across different kernel versions and configurations.

### Environment Setup
Ensure you have the following tools installed on your Linux system:

- `bpftool`: For inspecting and managing BPF objects.
- `kubectl`: If you are deploying eBPF programs in a Kubernetes environment.
- `iproute2`: For network configuration and inspection.
- `tcpdump`: For network packet capture and analysis.
- `strace`: For tracing system calls and signals.
- `perf`: For performance analysis and profiling.

Additionally, ensure your Linux kernel is compiled with BTF support. You can verify this by checking the presence of BTF data in the kernel:

```sh
file /sys/kernel/btf/vmlinux
```

The output should indicate that the file is a BTF data file.

## Exercise 1: Live State & Internal Subsystem Inspection

### Inspecting Kernel Maps
Kernel maps are essential for eBPF programs to store and share data. Use `bpftool` to inspect these maps:

```sh
sudo bpftool map list
```

This command lists all BPF maps currently loaded in the kernel. You can inspect a specific map by its ID:

```sh
sudo bpftool map dump id <map_id>
```

Replace `<map_id>` with the ID of the map you want to inspect.

### Inspecting BPF Programs
To inspect BPF programs loaded in the kernel, use:

```sh
sudo bpftool prog list
```

This command lists all BPF programs currently loaded. To inspect a specific program, use:

```sh
sudo bpftool prog show id <prog_id>
```

Replace `<prog_id>` with the ID of the program you want to inspect.

### Inspecting BTF Data
To inspect BTF data, you can use `bpftool` to dump the BTF information:

```sh
sudo bpftool btf dump file /sys/kernel/btf/vmlinux format c
```

This command dumps the BTF data in C format, which is useful for understanding the types and structures available for CO-RE relocations.

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmarking eBPF Programs
To benchmark eBPF programs, you can use `perf` to measure the performance of specific BPF functions. First, identify the BPF program ID:

```sh
sudo bpftool prog list
```

Then, use `perf` to profile the BPF program:

```sh
sudo perf record -e bpf_trace:prog_<prog_id> -a -g sleep 10
sudo perf report
```

Replace `<prog_id>` with the ID of the BPF program you want to profile.

### Simulating Load
To simulate load and measure the performance impact on eBPF programs, you can use `stress-ng` to generate CPU and memory load:

```sh
sudo apt-get install stress-ng
sudo stress-ng --cpu 4 --vm 2 --vm-bytes 1G --timeout 60s
```

While the load is being generated, use `perf` to profile the BPF program as described above.

### Packet Throughput and Latency Profiling
To profile packet throughput and latency, you can use `iperf` to generate network traffic and `tcpdump` to capture and analyze the packets:

```sh
# On the server
iperf3 -s

# On the client
iperf3 -c <server_ip> -t 60
```

Replace `<server_ip>` with the IP address of the server.

To capture and analyze the packets, use `tcpdump`:

```sh
sudo tcpdump -i <interface> -w capture.pcap
```

Replace `<interface>` with the network interface you want to capture packets on.

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Sudden Failure
To simulate a sudden failure, you can use `kill` to terminate a process that is interacting with a BPF program:

```sh
# Find the PID of the process
ps aux | grep <process_name>

# Kill the process
sudo kill -9 <pid>
```

Replace `<process_name>` with the name of the process and `<pid>` with the process ID.

### Simulating Packet Drop
To simulate packet drop, you can use `tc` to introduce packet loss on a network interface:

```sh
sudo tc qdisc add dev <interface> root netem loss 10%
```

Replace `<interface>` with the network interface you want to apply the packet loss on.

### Inspecting Recovery Logs
To inspect recovery logs, you can use `dmesg` to view kernel messages:

```sh
sudo dmesg | tail -n 50
```

This command displays the last 50 kernel messages, which may include logs related to the recovery process.

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command | Description |
|---------|-------------|
| `sudo bpftool map list` | List all BPF maps. |
| `sudo bpftool map dump id <map_id>` | Dump the contents of a specific BPF map. |
| `sudo bpftool prog list` | List all BPF programs. |
| `sudo bpftool prog show id <prog_id>` | Show details of a specific BPF program. |
| `sudo bpftool btf dump file /sys/kernel/btf/vmlinux format c` | Dump BTF data in C format. |
| `sudo perf record -e bpf_trace:prog_<prog_id> -a -g sleep 10` | Record performance data for a specific BPF program. |
| `sudo perf report` | Generate a performance report. |
| `stress-ng --cpu 4 --vm 2 --vm-bytes 1G --timeout 60s` | Generate CPU and memory load. |
| `iperf3 -s` | Start an iperf server. |
| `iperf3 -c <server_ip> -t 60` | Start an iperf client. |
| `sudo tcpdump -i <interface> -w capture.pcap` | Capture network packets. |
| `sudo kill -9 <pid>` | Terminate a process. |
| `sudo tc qdisc add dev <interface> root netem loss 10%` | Introduce packet loss on a network interface. |
| `sudo dmesg | tail -n 50` | View the last 50 kernel messages. |

By following this lab guide, you will gain a comprehensive understanding of CO-RE and BTF relocations in eBPF programs and how to verify their correctness and performance in a live environment.
