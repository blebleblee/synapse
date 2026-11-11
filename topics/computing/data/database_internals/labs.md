# Operational Verification Labs: Core

## Objective & Environment Setup

This lab guide is designed for hands-on practitioners and systems engineers to verify the internal workings of Linux/BSD systems. The goal is to inspect and analyze the live state of the system, benchmark performance, and inject faults to analyze recovery mechanisms.

### Required CLI Tools & Packages

* `htop` for process inspection
* `htop` for system resource monitoring
* `sysdig` for system call tracing
* `perf` for performance profiling
* `stress-ng` for load generation
* `fio` for disk benchmarking
* `tcpdump` for network packet capture

### Kernel Settings & Environment Variables

* Enable kernel debugging: `echo "kernel.panic_on_oops=1" >> /etc/sysctl.conf`
* Enable system call tracing: `echo "kernel.sysctl_debug=1" >> /etc/sysctl.conf`
* Set environment variable for `sysdig` tracing: `export SYSDIG_TRACE="1"`

## Exercise 1: Live State & Internal Memory Inspection

### Inspect Memory Usage

```bash
# Display memory usage by process
htop -u -p <process_id>

# Display memory usage by system
htop -u -s mem

# Display memory usage by cache
htop -u -s cache
```

### Inspect Buffer Cache

```bash
# Display buffer cache statistics
cat /proc/diskstats

# Display buffer cache hit ratio
cat /proc/meminfo | grep "Buffers"
```

### Inspect Process State

```bash
# Display process state
ps -ef

# Display process memory map
pmap -d <process_id>
```

## Exercise 2: Benchmarking & Saturation Profiling

### Disk Benchmarking

```bash
# Run sequential read benchmark
fio --name sequential_read --ioengine=libaio --direct=1 --bs=4k --iodepth=32 --runtime=60 --time_based --output=sequential_read.log

# Run sequential write benchmark
fio --name sequential_write --ioengine=libaio --direct=1 --bs=4k --iodepth=32 --runtime=60 --time_based --output=sequential_write.log
```

### Network Benchmarking

```bash
# Run TCP benchmark
stress-ng --tcp --rate=1000 --duration=60 --output=tcp_benchmark.log

# Run UDP benchmark
stress-ng --udp --rate=1000 --duration=60 --output=udp_benchmark.log
```

### System Performance Profiling

```bash
# Run system call tracing
sysdig -c syscall -p <process_id> -o syscall_trace.log

# Run performance profiling
perf stat -e cycles -p <process_id> -o performance_profile.log
```

## Exercise 3: Fault Injection & Recovery Analysis

### Simulate Sudden Failure

```bash
# Simulate sudden failure by killing a process
kill -9 <process_id>

# Inspect recovery logs
cat /var/log/syslog | grep "kernel panic"
```

### Simulate Packet Loss

```bash
# Simulate packet loss by dropping packets on the network
tc qdisc add dev <interface> root netem loss 10%

# Inspect recovery logs
cat /var/log/syslog | grep "packet loss"
```

### Simulate Corruption

```bash
# Simulate corruption by writing garbage data to disk
dd if=/dev/urandom of=<file> bs=1M count=10

# Inspect recovery logs
cat /var/log/syslog | grep "corruption"
```

## Diagnostic Cheat Sheet & Verification Checklist

| CLI Command | Operational Flag | Description |
| --- | --- | --- |
| `htop` | `-u` | Display memory usage by process |
| `htop` | `-s` | Display memory usage by system |
| `sysdig` | `-c` | System call tracing |
| `perf` | `-e` | Performance profiling |
| `stress-ng` | `--rate` | Load generation |
| `fio` | `--ioengine` | Disk benchmarking |
| `tc` | `qdisc add` | Network packet manipulation |
| `dd` | `if=/dev/urandom` | Simulate corruption |

Note: This is a basic guide and may require modifications to suit specific system configurations and requirements.
