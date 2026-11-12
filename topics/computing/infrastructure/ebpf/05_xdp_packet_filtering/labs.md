# Operational Verification Labs: 05 XDP Packet Filtering

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with XDP (eXpress Data Path) packet filtering in a Linux environment. We will explore how to deploy, inspect, benchmark, and test XDP programs using real CLI tools and scripts. This lab will cover live state inspection, benchmarking, and fault injection to ensure the robustness and performance of XDP filters.

### Environment Setup
Ensure you have the following tools installed on your Linux system:
- `bpftool`: For inspecting and managing BPF programs and maps.
- `iproute2`: For configuring network interfaces and XDP programs.
- `tcpdump`: For packet capture and analysis.
- `strace`: For tracing system calls and signals.
- `perf`: For performance analysis and profiling.
- `kubectl`: If you are deploying XDP in a Kubernetes environment.

Additionally, ensure your Linux kernel supports XDP. You can verify this by checking the kernel configuration:
```sh
grep CONFIG_XDP /boot/config-$(uname -r)
```
You should see `CONFIG_XDP=y` or `CONFIG_XDP=m` indicating XDP support.

## Exercise 1: Live State & Internal Subsystem Inspection

### Inspecting XDP Programs and Maps
To inspect XDP programs and maps, use `bpftool`. First, list all BPF programs:
```sh
sudo bpftool prog list
```
Identify the XDP program by its type and name. Then, inspect the program details:
```sh
sudo bpftool prog show id <prog_id>
```
Replace `<prog_id>` with the actual ID of your XDP program.

### Inspecting XDP Maps
XDP programs often use BPF maps for state storage. List all BPF maps:
```sh
sudo bpftool map list
```
Identify the map associated with your XDP program and inspect its details:
```sh
sudo bpftool map show id <map_id>
```
Replace `<map_id>` with the actual ID of your XDP map.

### Inspecting Network Interfaces
To inspect the network interface where XDP is attached, use `ip`:
```sh
ip link show dev <interface>
```
Replace `<interface>` with the actual network interface name (e.g., `eth0`).

### Inspecting Packet Capture
Use `tcpdump` to capture packets on the interface where XDP is attached:
```sh
sudo tcpdump -i <interface> -w capture.pcap
```
Replace `<interface>` with the actual network interface name. The capture will be saved to `capture.pcap`.

### Inspecting System Calls
Use `strace` to trace system calls made by the XDP program:
```sh
sudo strace -p <pid>
```
Replace `<pid>` with the process ID of the XDP program.

### Inspecting Performance Metrics
Use `perf` to profile the XDP program:
```sh
sudo perf record -e bpf_trace_printk -a -g -p <pid>
sudo perf report
```
Replace `<pid>` with the process ID of the XDP program. This will record and report performance metrics.

## Exercise 2: Benchmarking & Saturation Profiling

### Generating Load
Use `iperf3` to generate network load:
```sh
# On the server
iperf3 -s

# On the client
iperf3 -c <server_ip> -t 60
```
Replace `<server_ip>` with the IP address of the server.

### Measuring Packet Throughput
Use `iperf3` to measure packet throughput:
```sh
# On the server
iperf3 -s

# On the client
iperf3 -c <server_ip> -t 60 -i 1
```
Replace `<server_ip>` with the IP address of the server. The `-i 1` option provides interval reports every second.

### Measuring Latency
Use `ping` to measure latency:
```sh
ping <server_ip>
```
Replace `<server_ip>` with the IP address of the server.

### Profiling with `perf`
Use `perf` to profile the XDP program under load:
```sh
sudo perf record -e bpf_trace_printk -a -g -p <pid>
sudo perf report
```
Replace `<pid>` with the process ID of the XDP program. This will record and report performance metrics under load.

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Packet Drop
Use `tc` to simulate packet drop:
```sh
sudo tc qdisc add dev <interface> root netem loss 10%
```
Replace `<interface>` with the actual network interface name. This command introduces a 10% packet loss rate.

### Inspecting Recovery Logs
Use `dmesg` to inspect kernel logs for recovery actions:
```sh
sudo dmesg -w
```
This command will continuously display kernel messages, including any recovery actions taken by the XDP program.

### Simulating Interface Partition
Use `ifconfig` to simulate interface partition:
```sh
sudo ifconfig <interface> down
```
Replace `<interface>` with the actual network interface name. This command will bring the interface down, simulating a partition.

### Inspecting Recovery Logs After Partition
Use `dmesg` to inspect kernel logs for recovery actions after partition:
```sh
sudo dmesg -w
```
This command will continuously display kernel messages, including any recovery actions taken by the XDP program after the interface is brought back up:
```sh
sudo ifconfig <interface> up
```

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command          | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `bpftool prog list` | List all BPF programs.                                                      |
| `bpftool prog show id <prog_id>` | Show details of a specific BPF program.                                 |
| `bpftool map list` | List all BPF maps.                                                          |
| `bpftool map show id <map_id>` | Show details of a specific BPF map.                                       |
| `ip link show dev <interface>` | Show details of a network interface.                                      |
| `tcpdump -i <interface> -w capture.pcap` | Capture packets on a network interface.                             |
| `strace -p <pid>` | Trace system calls made by a process.                                           |
| `perf record -e bpf_trace_printk -a -g -p <pid>` | Record performance metrics for a process.                     |
| `iperf3 -s` | Start an iperf3 server.                                                   |
| `iperf3 -c <server_ip> -t 60` | Run an iperf3 client test.                                              |
| `ping <server_ip>` | Measure latency to a server.                                                  |
| `tc qdisc add dev <interface> root netem loss 10%` | Simulate packet loss on a network interface.                  |
| `dmesg -w` | Continuously display kernel messages.                                             |
| `ifconfig <interface> down` | Bring a network interface down.                                           |
| `ifconfig <interface> up` | Bring a network interface up.                                             |

By following this lab guide, you will gain a comprehensive understanding of XDP packet filtering, including deployment, inspection, benchmarking, and fault injection. This hands-on experience will equip you with the skills to effectively manage and optimize XDP programs in real-world scenarios.
