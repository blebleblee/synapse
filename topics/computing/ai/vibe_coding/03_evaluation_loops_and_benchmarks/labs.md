# Operational Verification Labs: 03 Evaluation Loops And Benchmarks

## Objective & Environment Setup

### Required CLI Tools & Packages

* `htop` for process inspection and system resource monitoring
* `sysdig` for system call tracing
* `stress-ng` for benchmarking and load generation
* `fio` for disk I/O benchmarking
* `iperf3` for network bandwidth benchmarking
* `linux-tools` for kernel settings and configuration

### Kernel Settings & Environment Variables

* Enable kernel tracing: `echo 0 > /proc/sys/kernel/kptr_restrict`
* Set kernel tracing buffer size: `echo 1024 > /proc/sys/kernel/ftrace_buffer_size`
* Set environment variable for kernel tracing: `export KTRACING=1`

### Environment Setup

* Install required packages: `sudo apt-get install htop sysdig stress-ng fio iperf3 linux-tools-common linux-tools-generic linux-tools-$(uname -r)`
* Configure kernel settings: `sudo sysctl -w kernel.kptr_restrict=0`
* Set environment variable: `export KTRACING=1`

## Exercise 1: Live State & Internal Memory Inspection

### Inspect Memory

* `htop` to inspect process and system memory usage
* `sysdig` to inspect system call tracing

### Inspect Buffers

* `sysdig` to inspect process and system buffer usage

### Inspect Processes

* `htop` to inspect process details
* `sysdig` to inspect system process details

### Inspect Metrics

* `htop` to inspect process and system metrics
* `sysdig` to inspect system call tracing

## Exercise 2: Benchmarking & Saturation Profiling

### Benchmarking

* `stress-ng --timeout 60 --cpu 4 --vm 4` to benchmark CPU usage
* `fio --name=mytest --ioengine=libaio --direct=1 --bs=4k --iodepth=16 --rw=read --size=1G` to benchmark disk I/O
* `iperf3 -c 192.168.1.1 -t 60` to benchmark network bandwidth

### Saturation Profiling

* `htop` to inspect system resource usage
* `sysdig` to inspect system call tracing

## Exercise 3: Fault Injection & Recovery Analysis

### Simulate Sudden Failure

* `echo 1 > /proc/sys/kernel/kptr_restrict` to enable kernel tracing
* `stress-ng --timeout 60 --cpu 4 --vm 4` to simulate sudden failure

### Simulate Packet Loss

* `tc qdisc add dev eth0 root netem rate 100kbit` to simulate packet loss
* `iperf3 -c 192.168.1.1 -t 60` to benchmark network bandwidth

### Simulate Corruption

* `fio --name=mytest --ioengine=libaio --direct=1 --bs=4k --iodepth=16 --rw=randwrite --size=1G` to simulate disk corruption
* `sysdig` to inspect system call tracing

## Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `htop` | N/A | Inspect process and system memory usage |
| `sysdig` | N/A | Inspect system call tracing |
| `stress-ng --timeout 60 --cpu 4 --vm 4` | `--timeout` | Benchmark CPU usage |
| `fio --name=mytest --ioengine=libaio --direct=1 --bs=4k --iodepth=16 --rw=read --size=1G` | `--name` | Benchmark disk I/O |
| `iperf3 -c 192.168.1.1 -t 60` | `-c` | Benchmark network bandwidth |
| `tc qdisc add dev eth0 root netem rate 100kbit` | `rate` | Simulate packet loss |
| `echo 1 > /proc/sys/kernel/kptr_restrict` | N/A | Enable kernel tracing |
| `echo 0 > /proc/sys/kernel/kptr_restrict` | N/A | Disable kernel tracing |

Note: This guide provides a step-by-step diagnostic verification using real Linux/BSD CLI commands, inspection tools, and reproduction scripts. The output is publication-grade Markdown.
