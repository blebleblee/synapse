# Operational Verification Labs: Operating System Theory & Kernel Subsystems

## Objective & Environment Setup

### Objective
This operational lab provides hands-on diagnostic verification of foundational operating system abstractions: virtual memory management, page tables, process address space layout (VMA), system call boundaries, and VFS file descriptor mechanics. Exercises utilize standard OS inspection utilities (`pmap`, `perf`, `strace`, `valgrind`, and the Linux `/proc` pseudo-filesystem).

### Required Tooling
Ensure operating system diagnostic utilities are installed:
- `procps` (`ps`, `pmap`, `sysctl`, `free`)
- `perf` (Linux performance counters)
- `strace` (System call tracer)
- Standard C compiler toolchain (`gcc`, `make`)

---

## Exercise 1: Process Virtual Address Space & Page Table Inspection

Inspect how the operating system kernel isolates process memory, builds Virtual Memory Areas (VMAs), and maps physical page frames.

### 1.1 Process Memory Mapping & Segment Layout
Inspect the segment boundaries (Text, Data, BSS, Heap, Memory Mapped Files, Stack) for a target process:

```bash
# Launch a background process or target shell
sleep 300 &
PID=$!

# Dissect process Virtual Memory Areas (VMAs)
pmap -X $PID
```

Examine detailed memory allocation in `/proc/$PID/smaps`:
```bash
# Inspect Private/Shared Dirty pages and RSS allocation
cat /proc/$PID/smaps | grep -E "(Size|Rss|Pss|Shared_Clean|Private_Dirty)" | head -n 20
```

### 1.2 Copy-On-Write (COW) Memory Verification
Compile and run a small C harness demonstrating fork-time Copy-On-Write behavior:

```bash
cat << 'EOF' > cow_test.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main() {
    size_t size = 64 * 1024 * 1024; // 64 MB
    char *buf = malloc(size);
    memset(buf, 'A', size);
    printf("Parent PID: %d, Allocated 64MB\n", getpid());
    
    if (fork() == 0) {
        printf("Child PID: %d created (COW shared pages)\n", getpid());
        sleep(5);
        // Trigger page fault and copy by writing
        memset(buf, 'B', size);
        printf("Child PID: %d dirtied pages (Private Dirty split)\n", getpid());
        sleep(10);
        exit(0);
    }
    sleep(15);
    return 0;
}
EOF

gcc -O2 cow_test.c -o cow_test
./cow_test &
```

While running, compare `Shared_Clean` vs `Private_Dirty` before and after the child writes:
```bash
grep -E "(Rss|Private_Dirty|Shared_Clean)" /proc/$(pgrep -n cow_test)/smaps_rollup
```

---

## Exercise 2: System Call Boundaries & Context Switch Profiling

Measure CPU mode transitions from userspace (Ring 3) to kernel space (Ring 0) and profile involuntary context switches.

### 2.1 Syscall Latency & Frequency Profiling
Profile system call overhead and CPU time distribution using `strace`:

```bash
# Collect syscall count, time, and error summary for a target workload
strace -c dd if=/dev/zero of=/dev/null bs=1k count=100000
```

### 2.2 Voluntary vs. Involuntary Context Switching
Measure scheduling preemption and CPU cache thrashing during high thread contention:

```bash
# Measure context switches and CPU migrations
perf stat -e context-switches,cpu-migrations,page-faults,cycles,instructions sleep 2
```

---

## Exercise 3: VFS Inode Tables, Page Cache & Out-Of-Memory (OOM) Testing

Examine kernel page cache write-back mechanics, dirty memory limits, and the OOM killer scoring system.

### 3.1 Kernel Page Cache & Dirty Page Flushing
Observe page cache dynamics during heavy unbuffered I/O:

```bash
# Monitor kernel dirty memory state
cat /proc/meminfo | grep -E "(Cached|Dirty|Writeback)"

# Trigger kernel page cache drop
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Re-inspect dropped page cache counters
cat /proc/meminfo | grep -E "(Cached|Dirty|Writeback)"
```

### 3.2 OOM Score & Process Priority Mechanics
Inspect how the kernel calculates process kill priority during physical memory exhaustion:

```bash
# Inspect a process OOM badness score (0 = immune, 1000 = prime candidate)
cat /proc/$PID/oom_score
cat /proc/$PID/oom_score_adj
```

Adjust OOM score adjustment to protect critical system processes:
```bash
echo -1000 | sudo tee /proc/$PID/oom_score_adj
```

---

## Operating System Theory Diagnostic Cheat Sheet

| Subsystem | Command / Interface | Diagnostic Purpose |
| :--- | :--- | :--- |
| **Address Space** | `pmap -x <PID>` | Inspect process segment boundaries and RSS |
| **Memory Map** | `/proc/<PID>/smaps_rollup` | Fast summary of PSS, USS, and Private Dirty memory |
| **Syscall Cost** | `strace -c <command>` | Aggregate syscall execution frequency and latency |
| **Scheduling** | `perf stat -e context-switches` | Measure voluntary and involuntary preemption |
| **Page Faults** | `sar -B 1 5` | Monitor minor (memory) and major (disk I/O) page faults |
| **Page Cache** | `/proc/meminfo` | Inspect Active/Inactive, Dirty, and Writeback memory |
| **OOM Engine** | `/proc/<PID>/oom_score` | Determine kernel termination priority under memory pressure |
