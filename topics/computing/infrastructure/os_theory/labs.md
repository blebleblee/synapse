# Operational Verification Labs: Core

## Objective & Environment Setup

### Objective
The objective of this lab is to provide hands-on experience with diagnostic verification of core infrastructure and operating system components. This includes live state inspection, benchmarking, saturation profiling, and fault injection analysis using real Linux/BSD CLI commands, inspection tools, and reproduction scripts.

### Environment Setup
Ensure the following CLI tools are installed on your system:
- `bpftool`
- `kubectl`
- `iproute2`
- `tcpdump`
- `strace`
- `perf`

#### Installation Commands
For Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install -y bpfcc-tools kubectl iproute2 tcpdump strace linux-tools-common linux-tools-generic linux-tools-`uname -r`
```

For CentOS/RHEL:
```bash
sudo yum install -y bpfcc-tools kubectl iproute2 tcpdump strace perf
```

For Fedora:
```bash
sudo dnf install -y bpfcc-tools kubectl iproute2 tcpdump strace perf
```

For Arch Linux:
```bash
sudo pacman -S bpfcc kubectl iproute2 tcpdump strace perf
```

## Exercise 1: Live State & Internal Subsystem Inspection

### Kernel Maps Inspection
To inspect eBPF maps, use `bpftool`:
```bash
sudo bpftool map list
```

### Memory Inspection
To inspect memory usage and page tables, use `pmap` and `vmstat`:
```bash
pmap $(pidof <process_name>)
vmstat -s
```

### Buffer Inspection
To inspect network buffers, use `ss` and `netstat`:
```bash
ss -s
netstat -s
```

### Process Inspection
To inspect processes and their states, use `ps` and `top`:
```bash
ps aux
top
```

### Metrics Inspection
To inspect system metrics, use `vmstat` and `iostat`:
```bash
vmstat 1 5
iostat -x 1 5
```

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmark Commands
To benchmark CPU performance, use `sysbench`:
```bash
sudo apt-get install -y sysbench
sysbench cpu run
```

To benchmark memory performance, use `memtester`:
```bash
sudo apt-get install -y memtester
memtester 1G 1
```

### Load Generation
To generate CPU load, use `stress-ng`:
```bash
sudo apt-get install -y stress-ng
stress-ng --cpu 4 --timeout 60s
```

To generate network load, use `iperf`:
```bash
sudo apt-get install -y iperf
# On server
iperf -s
# On client
iperf -c <server_ip>
```

### Packet Throughput & Latency Profiling
To profile network packet throughput and latency, use `iperf` and `ping`:
```bash
# On server
iperf -s
# On client
iperf -c <server_ip>
ping <server_ip>
```

To capture network packets and analyze, use `tcpdump`:
```bash
sudo tcpdump -i <interface> -w capture.pcap
```

## Exercise 3: Fault Injection & Recovery Analysis

### Simulating Sudden Failure
To simulate a sudden failure, use `kill` to terminate a process:
```bash
kill -9 $(pidof <process_name>)
```

### Simulating Packet Drop
To simulate packet drops, use `tc`:
```bash
sudo tc qdisc add dev <interface> root netem loss 10%
```

### Simulating Partition
To simulate network partition, use `iptables`:
```bash
sudo iptables -A INPUT -s <target_ip> -j DROP
```

### Inspecting Recovery Logs
To inspect system logs for recovery, use `journalctl`:
```bash
sudo journalctl -xe
```

To inspect kernel logs, use `dmesg`:
```bash
dmesg
```

## Diagnostic Cheat Sheet & Verification Checklist

### Essential CLI Commands and Operational Flags

| Command      | Description                                                                 | Example Usage                                                                 |
|--------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `bpftool`    | Inspect eBPF maps and programs                                              | `sudo bpftool map list`                                                       |
| `pmap`       | Display memory map of a process                                             | `pmap $(pidof <process_name>)`                                                |
| `vmstat`     | Report virtual memory statistics                                            | `vmstat -s`                                                                 |
| `ss`         | Display socket statistics                                                   | `ss -s`                                                                     |
| `netstat`    | Display network connections, routing tables, interface statistics, etc.     | `netstat -s`                                                                |
| `ps`         | Report a snapshot of the current processes                                  | `ps aux`                                                                    |
| `top`        | Display a dynamic real-time view of a running system                        | `top`                                                                       |
| `iostat`     | Report CPU usage and I/O statistics for devices and partitions              | `iostat -x 1 5`                                                             |
| `sysbench`   | System performance benchmark tool                                           | `sysbench cpu run`                                                          |
| `memtester`  | Test memory for errors                                                      | `memtester 1G 1`                                                            |
| `stress-ng`  | Stress test a computer system in various selectable ways                    | `stress-ng --cpu 4 --timeout 60s`                                           |
| `iperf`      | Network bandwidth measurement tool                                          | `iperf -s` (server), `iperf -c <server_ip>` (client)                        |
| `ping`       | Send ICMP ECHO_REQUEST packets to network hosts                             | `ping <server_ip>`                                                          |
| `tcpdump`    | Dump traffic on a network                                                   | `sudo tcpdump -i <interface> -w capture.pcap`                               |
| `kill`       | Send a signal to a process                                                  | `kill -9 $(pidof <process_name>)`                                             |
| `tc`         | Configure traffic control rules                                             | `sudo tc qdisc add dev <interface> root netem loss 10%`                       |
| `iptables`   | Configure packet filtering rules                                            | `sudo iptables -A INPUT -s <target_ip> -j DROP`                             |
| `journalctl` | Query the systemd journal                                                   | `sudo journalctl -xe`                                                       |
| `dmesg`      | Print or control the kernel ring buffer                                     | `dmesg`                                                                     |

This lab guide provides a comprehensive set of tools and commands to perform operational verification on core infrastructure and operating system components. By following these exercises, you will gain hands-on experience with live state inspection, benchmarking, saturation profiling, and fault injection analysis.
