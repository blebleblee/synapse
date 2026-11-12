# Operational Verification Labs: 02 In Kernel Verifier Internals

## Objective & Environment Setup

This lab is designed to provide hands-on experience with the **Linux kernel’s eBPF verifier internals**, focusing on how the kernel validates eBPF programs before execution. The goal is to inspect, benchmark, and test the behavior of the verifier under various conditions using real-world tools and environments.

### Required CLI Tools

To perform this lab, ensure the following tools are installed and available in your environment:

- `bpftool`: A utility for inspecting and manipulating eBPF programs.
- `kubectl`: Kubernetes CLI for managing containerized environments.
- `iproute2`: Network configuration utilities.
- `tcpdump`: Packet capture and analysis tool.
- `strace`: System call tracing utility.
- `perf`: Performance analysis tool for kernel profiling.
- `gcc`, `make`, `clang`: For compiling eBPF programs from source.

### Environment Configuration

The lab assumes a Linux kernel version **5.10 or newer**, with eBPF support enabled. You must also have access to a system with:

- Root privileges (to load eBPF programs).
- A running kernel with `CONFIG_BPF=y` and `CONFIG_BPF_SYSCALL=y`.
- Optional: A Kubernetes cluster with `bpftool` and `kubectl` installed for containerized testing.

### Verification Steps

Before beginning, confirm that the kernel supports eBPF:

```bash
grep CONFIG_BPF /boot/config-$(uname -r)
```

Expected output:
```
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
```

Also confirm that `bpftool` is installed:

```bash
bpftool --version
```

Expected output:
```
bpftool v1.0.0
```

## Exercise 1: Live State & Internal Subsystem Inspection

In this exercise, we will inspect the internal state of the kernel’s eBPF subsystem, including loaded programs, maps, and verifier statistics.

### Step 1: List All Loaded eBPF Programs

Use `bpftool prog` to list all currently loaded eBPF programs:

```bash
bpftool prog show
```

This command will output a table of loaded programs, including their ID, tag, type, and path. Example output:

```
123: socket_filter  name my_filter  tag 1234567890abcdef  jited
```

### Step 2: Inspect eBPF Maps

Use `bpftool map show` to inspect all eBPF maps currently in use:

```bash
bpftool map show
```

Example output:
```
124: hash  name my_hash_map  key_size 4  value_size 8  max_entries 1024
```

### Step 3: Inspect Verifier Statistics

Use `/proc` filesystem to inspect internal verifier statistics:

```bash
cat /proc/sys/kernel/bpf_stats_enabled
```

If the output is `1`, enable statistics collection:

```bash
echo 1 > /proc/sys/kernel/bpf_stats_enabled
```

Then inspect the stats:

```bash
cat /proc/sys/kernel/bpf_verifier_stats
```

Example output:
```
verifier_stats:
  alloc_insns: 100
  free_insns: 99
  alloc_mem: 10240
  free_mem: 10239
```

### Step 4: Trace eBPF Program Loading with `strace`

Use `strace` to trace system calls related to loading an eBPF program:

```bash
strace -e trace=clone,execve,bpf bpftool prog load my_program.o /sys/fs/bpf/my_program
```

This will show how the kernel handles the program loading process, including memory allocation and verifier invocation.

## Exercise 2: Benchmarking & Saturation Profiling

In this exercise, we will generate load on the eBPF verifier and profile its behavior under saturation.

### Step 1: Compile a Sample eBPF Program

Create a simple eBPF program to load and test:

```c
// simple_filter.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("socket")
int filter(struct __sk_buff *skb)
{
    return 0;
}

char _license[] SEC("license") = "GPL";
```

Compile it using `clang` and `llc`:

```bash
clang -O2 -target bpf -c simple_filter.c -o simple_filter.o
```

### Step 2: Load and Benchmark the Program

Load the program and benchmark its performance using `perf`:

```bash
bpftool prog load simple_filter.o /sys/fs/bpf/simple_filter
```

Then, run a benchmark to simulate high-frequency program loading:

```bash
perf stat -e bpf:prog_load,bpf:prog_run -I 1000 -o perf_output.log &
for i in {1..1000}; do
    bpftool prog load simple_filter.o /sys/fs/bpf/test_$i
done
```

### Step 3: Monitor Verifier Memory Usage

Monitor memory usage during program loading using `cat /proc/meminfo`:

```bash
watch -n 1 'cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable)"'
```

### Step 4: Analyze Verifier Logs

Use `dmesg` to inspect kernel logs for verifier-related messages:

```bash
dmesg | grep -i bpf
```

Look for messages like:
```
bpf: prog 123: loaded successfully
bpf: verifier: max_insns reached
```

## Exercise 3: Fault Injection & Recovery Analysis

In this exercise, we simulate a fault condition in the eBPF verifier and analyze how the system recovers.

### Step 1: Simulate a Faulty eBPF Program

Create a program that intentionally violates verifier rules:

```c
// faulty_program.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("socket")
int faulty_filter(struct __sk_buff *skb)
{
    char *ptr = (char *)skb;
    ptr[1000000] = 0; // Out-of-bounds write
    return 0;
}

char _license[] SEC("license") = "GPL";
```

Compile and attempt to load it:

```bash
clang -O2 -target bpf -c faulty_program.c -o faulty_program.o
bpftool prog load faulty_program.o /sys/fs/bpf/faulty_program
```

Expected result: The kernel should reject the program with a verifier error.

### Step 2: Inspect Verifier Error Logs

Check the kernel logs for the verifier error:

```bash
dmesg | tail -n 20
```

You should see an error like:
```
bpf: verifier: load failed: invalid memory access
```

### Step 3: Simulate Memory Pressure

Use `stress-ng` to simulate memory pressure and observe how the verifier behaves:

```bash
stress-ng --vm 4 --vm-bytes 1G --timeout 60s
```

Monitor the system during stress:

```bash
watch -n 1 'cat /proc/sys/kernel/bpf_verifier_stats'
```

### Step 4: Analyze Recovery Behavior

After the stress test, inspect the system state:

```bash
bpftool prog show
bpftool map show
```

Ensure that no eBPF programs are left in an invalid state.

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Description |
|------|---------|-------------|
| List loaded eBPF programs | `bpftool prog show` | Shows all loaded programs |
| List eBPF maps | `bpftool map show` | Displays all eBPF maps |
| Enable verifier stats | `echo 1 > /proc/sys/kernel/bpf_stats_enabled` | Enables internal stats |
| View verifier stats | `cat /proc/sys/kernel/bpf_verifier_stats` | Shows verifier memory usage |
| Trace program loading | `strace -e trace=bpf bpftool prog load ...` | Traces system calls |
| Monitor memory usage | `watch -n 1 'cat /proc/meminfo'` | Monitors memory during load |
| View kernel logs | `dmesg | grep -i bpf` | Inspects verifier logs |
| Load a program | `bpftool prog load <file> <path>` | Loads an eBPF program |
| Stress test system | `stress-ng --vm 4 --vm-bytes 1G` | Simulates memory pressure |
| Check program status | `bpftool prog show` | Verifies loaded programs |

---

This lab provides a comprehensive operational verification of the Linux kernel’s eBPF verifier internals. By following these steps, practitioners can gain deep insight into how the kernel validates and manages eBPF programs, and how it handles edge cases and failures.
