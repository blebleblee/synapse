# Operational Verification Labs: Core

## Objective & Lab Setup

The operational verification of core systems requires hands-on experimentation with process execution models, file descriptor management, signal handling, memory accounting, and inter-process communication primitives that form the foundation of Unix-like operating systems. This laboratory guide transcends theoretical treatment of the kernel scheduler, process lifecycle, and I/O multiplexing to deliver concrete, measurable experiments that reveal how the Linux kernel enforces resource limits, manages asynchronous events, and coordinates concurrent workloads.

Throughout these exercises, you will instrument live processes using strace, ltrace, perf, and /proc filesystem inspection to observe syscall latencies, context switches, and memory dynamics in real time. You will construct minimal reproducible test harnesses in Bash that trigger kernel behaviors—page faults, signal delivery races, file descriptor exhaustion—and measure the precise timing and ordering of events. This empirical approach grounds abstract concepts like process state machines and memory management in observable physical reality.

### Required Environment & Tools

Ensure you are operating on a Linux system with kernel version 4.15 or later, ideally 5.10 or newer. The following tools must be installed and available in your PATH:

- Core utilities: bash (5.0+), coreutils, util-linux (2.30+)
- Process instrumentation: strace, ltrace, perf-tools
- System introspection: /proc filesystem, sysfs, debugfs
- Performance analysis: flamegraph.pl, gnuplot (optional but recommended)
- Development: gcc, make, objdump, readelf
- Debugging: gdb, lldb (optional)

Verify your environment with these commands:

```bash
uname -r
bash --version
strace --version
perf --version
```

If any tool is absent, install via your distribution's package manager. For Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y build-essential strace ltrace linux-tools-generic perf-tools-unstable
```

For production-grade reproducibility, isolate one CPU core for testing to minimize scheduler jitter. If you have at least four cores, execute:

```bash
sudo bash -c 'echo 3 > /sys/devices/system/cpu/cpu3/online'
```

You can later pin processes to this isolated core using taskset. Create a dedicated working directory:

```bash
mkdir -p ~/labs/core-verification
cd ~/labs/core-verification
```

---

## Exercise 1: Process Lifecycle and Signal Handling

### Observing State Transitions Through Instrumentation

The first exercise establishes the fundamental process execution model by constructing a minimal signal-aware process monitor that captures the exact sequence of state transitions, signal delivery, and syscall invocations as a child process transitions from creation through execution to termination.

#### Conceptual Foundation

Every process in Linux occupies one of five canonical states: Running (executing on CPU), Runnable (in scheduler queue, awaiting CPU allocation), Interruptible Sleep (blocked waiting for I/O or event, responsive to signals), Uninterruptible Sleep (blocked in kernel critical section, ignoring signals), and Stopped or Traced (halted by debugger or SIGSTOP). The kernel scheduler enforces preemptive multitasking, granting each process a scheduling quantum—typically 100 milliseconds on modern kernels—before preemption and context switch to another process. Signals interrupt this execution flow by invoking asynchronous handlers in user space, creating a complex interleaving of synchronous syscalls and asynchronous signal delivery.

Direct observation requires inspection of the /proc filesystem, which exposes process state in /proc/[pid]/stat (numeric state field) and /proc/[pid]/status (human-readable description). The strace tool intercepts syscalls at the user-kernel boundary, revealing both parameters and return values of every system call, along with signal delivery events and their precise timing.

#### Implementation: Multi-Process Signal Monitor

The following Bash script demonstrates the exact sequence of syscalls, signal delivery, and process state transitions as a child process is created, executed, signaled, and terminated. Create the script in your working directory:

```bash
#!/bin/bash
set -euo pipefail

# lab_signal_monitor.sh
# Operational verification of process lifecycle and signal delivery.
# Spawns a child process, instruments it with strace, logs all events,
# and analyzes the event stream to extract state transitions.

WORK_DIR="${1:-.}"
cd "$WORK_DIR"

EVENT_LOG="signal_events.log"
STRACE_LOG="strace_raw.log"
STATE_LOG="process_states.log"
TIMING_LOG="event_timing.log"

: > "$EVENT_LOG"
: > "$STRACE_LOG"
: > "$STATE_LOG"
: > "$TIMING_LOG"

# Create a child process that demonstrates signal delivery and state transitions.
# This child process runs a defined workload, handles signals via trap handlers,
# and logs lifecycle events to stderr for correlation with strace output.

cat > child_process.sh << 'CHILD_EOF'
#!/bin/bash

CHILD_PID=$$
echo "[CHILD] Started with PID=$CHILD_PID at $(date +%s.%N)" >&2

# Register signal handlers to demonstrate signal delivery interception
trap 'echo "[CHILD] Received SIGUSR1 at $(date +%s.%N)" >&2; sleep 0.1' SIGUSR1
trap 'echo "[CHILD] Received SIGUSR2, exiting at $(date +%s.%N)" >&2; exit 42' SIGUSR2

# Execute mixed workload: CPU-bound computation, I/O operations, and blocking sleep.
# This workload ensures the child occupies multiple process states during execution.

for i in {1..10}; do
  echo "[CHILD] Iteration $i/10 starting at $(date +%s.%N)" >&2
  
  # CPU-bound work: compute Fibonacci numbers to consume CPU time
  result=0
  a=0
  b=1
  for ((j=0; j<1000; j++)); do
    result=$((a + b))
    a=$b
    b=$result
  done
  
  # Log completion of CPU work for trace synchronization
  echo "[CHILD] CPU work completed, result=$result at $(date +%s.%N)" >&2
  
  # Block in interruptible sleep, allowing signal delivery during this syscall
  sleep 0.5
done

echo "[CHILD] Workload complete, exiting normally at $(date +%s.%N)" >&2
exit 0
CHILD_EOF

chmod +x child_process.sh

# Capture wall-clock time at experiment start for precise duration calculation
CHILD_START=$(date +%s%N)
echo "=== Experiment Start: $(date) ===" >> "$EVENT_LOG"
echo "Spawning child process for instrumentation..." >&2

# Execute child process under strace with comprehensive syscall tracing.
# Flags:
#   -f        Follow child processes created via fork/clone
#   -e trace=all    Trace all system calls without filtering
#   -o FILE   Write trace output to FILE
#   -T        Display syscall duration in microseconds
#   -tt       Print wall-clock timestamp for each trace line
#   -s 256    Set maximum string argument length to 256 bytes

strace -f -e trace=all -o "$STRACE_LOG" -T -tt -s 256 ./child_process.sh &
CHILD_PID=$!

echo "Child process started with PID: $CHILD_PID" >&2
echo "[MONITOR] Child spawned at $(date +%s.%N)" >> "$EVENT_LOG"

# Allow child to enter its first sleep syscall before sending signals
sleep 1

# Send SIGUSR1 to demonstrate signal interruption of sleep syscall
echo "[MONITOR] Sending SIGUSR1 to PID $CHILD_PID at $(date +%s.%N)" >> "$EVENT_LOG"
kill -USR1 "$CHILD_PID" 2>/dev/null || true
sleep 0.5

# Send SIGUSR2 to trigger the exit handler in the child
echo "[MONITOR] Sending SIGUSR2 to PID $CHILD_PID at $(date +%s.%N)" >> "$EVENT_LOG"
kill -USR2 "$CHILD_PID" 2>/dev/null || true

# Wait for child process termination and capture exit status
wait "$CHILD_PID" 2>/dev/null
CHILD_EXIT=$?
CHILD_END=$(date +%s%N)

# Calculate precise execution duration in nanoseconds, convert to milliseconds
DURATION_NS=$((CHILD_END - CHILD_START))
DURATION_MS=$((DURATION_NS / 1000000))

echo "[MONITOR] Child terminated with exit code $CHILD_EXIT" >> "$EVENT_LOG"
echo "[MONITOR] Total execution duration: ${DURATION_MS} ms" >> "$EVENT_LOG"
echo "=== Experiment Complete ===" >> "$EVENT_LOG"

echo "Experiment complete. Child exited with code: $CHILD_EXIT" >&2
echo "Total duration: ${DURATION_MS} ms" >&2

# Parse strace output to extract syscall sequence and signal delivery events.
# This analysis correlates signal delivery with process state transitions.

echo "=== STRACE EVENT SEQUENCE ===" >> "$TIMING_LOG"
echo "Extracting syscalls, signals, and timings from strace output..." >&2

# Filter strace output to show only signal delivery and key syscalls (sleep, pause, exit)
grep -E '(SIGUSR|SIG_DFL|nanosleep|pause|exit)' "$STRACE_LOG" \
  | head -20 >> "$TIMING_LOG" 2>/dev/null || true

# Extract process state transitions from /proc during execution.
# Collect snapshots of /proc/[pid]/status to show state at key moments.

echo "" >> "$STATE_LOG"
echo "=== PROCESS STATE TRANSITIONS ===" >> "$STATE_LOG"
echo "State values: R=Running, S=Sleeping, D=Disk sleep, T=Stopped, Z=Zombie" >> "$STATE_LOG"
echo "" >> "$STATE_LOG"

# Parse strace output to show context switches (indicated by syscall returns with signal interruption)
echo "=== SIGNAL INTERRUPTION ANALYSIS ===" >> "$STATE_LOG"
grep -B2 -A2 'SIGUSR' "$STRACE_LOG" | head -30 >> "$STATE_LOG" 2>/dev/null || true

# Summary report
echo "" >> "$EVENT_LOG"
echo "=== ANALYSIS SUMMARY ===" >> "$EVENT_LOG"
echo "Total syscalls traced: $(wc -l < "$STRACE_LOG")" >> "$EVENT_LOG"
echo "Signal delivery events observed: $(grep -c 'SIG' "$STRACE_LOG" || echo 0)" >> "$EVENT_LOG"
echo "Process exit code: $CHILD_EXIT" >> "$EVENT_LOG"

# Display results to console
echo "" >&2
echo "=== RESULTS ===" >&2
cat "$EVENT_LOG" >&2
echo "" >&2
echo "Raw strace output saved to: $STRACE_LOG" >&2
echo "Event log saved to: $EVENT_LOG" >&2
echo "State transitions saved to: $STATE_LOG" >&2
echo "Timing analysis saved to: $TIMING_LOG" >&2
```

Execute the script with:

```bash
chmod +x lab_signal_monitor.sh
./lab_signal_monitor.sh .
```

#### Analysis and Interpretation

The script produces four output files that together reveal the process lifecycle. Examine the raw strace output to identify critical syscalls:

```bash
grep 'nanosleep\|pause\|exit_group' strace_raw.log | head -20
```

The nanosleep syscall represents the child's blocking sleep, while exit_group signals process termination. Between these syscalls, observe the timing annotations (in the -tt output) to measure the exact duration of each syscall and the time elapsed between events.

Signal delivery manifests in strace as interrupted syscalls. Look for lines containing "SIGUSR1" or "SIGUSR2" preceded by a syscall in progress. The kernel's signal handler interrupts the syscall, executes the trap handler in user space, and then either resumes the syscall (via ERESTART logic) or returns an error code like EINTR. This behavior depends on the SA_RESTART flag when the signal handler was installed.

The process state transitions—Running, Sleeping, Stopped—appear in the /proc/[pid]/stat file. While this script does not continuously poll /proc, production monitoring tools like top or custom monitoring daemons can capture these transitions. The key insight is that signals are delivered only when the kernel scheduler returns control to user space, either after a syscall completes or during a preemption event.

#### Key Observations

Measure the latency between sending a signal (kill -USR1) and observing its delivery in strace output. This latency reveals the scheduler's response time. On an idle system, expect microsecond-to-millisecond latencies; on a loaded system, latencies may reach tens of milliseconds. This demonstrates that signal delivery is not instantaneous—the kernel must wait for a scheduling opportunity to execute the signal handler.

Second, observe the behavior of nanosleep when interrupted by SIGUSR1. The strace output will show nanosleep returning with errno=EINTR. The child process's trap handler then executes (printing the "[CHILD] Received SIGUSR1" message), and the next syscall appears in the trace. If the child does not explicitly restart nanosleep, the sleep terminates early—this is the basis for implementing efficient signaling in concurrent systems.

Third, examine the exit behavior triggered by SIGUSR2. The strace output will show the child exiting with exit_group(42), matching the exit code set in the trap handler. This demonstrates that signals can alter program flow and termination status.

---

## Exercise 2: File Descriptor Management and I/O Multiplexing

### Observing File Descriptor Lifecycle and Event Notification

File descriptor management is central to Unix I/O. This exercise instruments file descriptor operations—creation, duplication, inheritance across fork, and closure—to reveal both the kernel's accounting mechanisms and the performance characteristics of different I/O multiplexing strategies.

#### Conceptual Foundation

A file descriptor is an integer handle managed per-process that refers to an open file, pipe, socket, or other I/O resource. The kernel maintains a file descriptor table for each process, typically allowing 1024 or more open descriptors. File descriptors are inherited across fork and exec, enabling inter-process communication and shell pipelines. The three standard descriptors—0 (stdin), 1 (stdout), 2 (stderr)—are created by the shell and inherited by all child processes.

I/O multiplexing allows a single process to monitor multiple file descriptors simultaneously. Three mechanisms are available: select (traditional, limited to 1024 descriptors), poll (newer, no arbitrary limit), and epoll (Linux-specific, scalable to hundreds of thousands of descriptors via an internal hash table). Each mechanism trades simplicity for scalability.

#### Implementation: File Descriptor Monitor and Multiplexing Comparison

Create a comprehensive C program that demonstrates file descriptor lifecycle management and compares the latency characteristics of select, poll, and epoll under varying load. This program will create pairs of pipes, send events through them, and measure the time required for each multiplexing mechanism to detect events.

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/select.h>
#include <sys/poll.h>
#include <sys/epoll.h>
#include <sys/time.h>
#include <errno.h>
#include <time.h>

#define NUM_PIPES 100
#define ITERATIONS 1000

typedef struct {
    int read_fd;
    int write_fd;
    unsigned long events_sent;
    unsigned long events_received;
} pipe_pair_t;

/* Get high-resolution timestamp in nanoseconds */
static uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000UL + ts.tv_nsec;
}

/* Test select() multiplexing mechanism */
static uint64_t benchmark_select(pipe_pair_t *pipes, int num_pipes, int iterations) {
    fd_set readfds;
    int max_fd = 0;
    uint64_t total_latency = 0;
    int i, j, nready;

    /* Find maximum fd for select */
    for (i = 0; i < num_pipes; i++) {
        if (pipes[i].read_fd > max_fd)
            max_fd = pipes[i].read_fd;
    }

    for (j = 0; j < iterations; j++) {
        /* Pick random pipe and write one byte */
        int pipe_idx = rand() % num_pipes;
        unsigned char byte = 42;
        
        uint64_t before = get_time_ns();
        
        ssize_t ret = write(pipes[pipe_idx].write_fd, &byte, 1);
        if (ret < 0) {
            perror("write");
            return 0;
        }
        pipes[pipe_idx].events_sent++;

        /* Reset and populate fd set */
        FD_ZERO(&readfds);
        for (i = 0; i < num_pipes; i++) {
            FD_SET(pipes[i].read_fd, &readfds);
        }

        /* Wait for readiness with 1-second timeout */
        struct timeval tv = {.tv_sec = 1, .tv_usec = 0};
        nready = select(max_fd + 1, &readfds, NULL, NULL, &tv);
        
        if (nready > 0) {
            /* Drain readable descriptors */
            for (i = 0; i < num_pipes; i++) {
                if (FD_ISSET(pipes[i].read_fd, &readfds)) {
                    unsigned char buf;
                    if (read(pipes[i].read_fd, &buf, 1) > 0) {
                        pipes[i].events_received++;
                    }
                }
            }
        }

        uint64_t after = get_time_ns();
        total_latency += (after - before);
    }

    return total_latency;
}

/* Test poll() multiplexing mechanism */
static uint64_t benchmark_poll(pipe_pair_t *pipes, int num_pipes, int iterations) {
    struct pollfd *pollfds;
    uint64_t total_latency = 0;
    int i, j, nready;

    pollfds = malloc(num_pipes * sizeof(struct pollfd));
    if (!pollfds) {
        perror("malloc");
        return 0;
    }

    for (j = 0; j < iterations; j++) {
        int pipe_idx = rand() % num_pipes;
        unsigned char byte = 42;

        uint64_t before = get_time_ns();

        ssize_t ret = write(pipes[pipe_idx].write_fd, &byte, 1);
        if (ret < 0) {
            perror("write");
            free(pollfds);
            return 0;
        }
        pipes[pipe_idx].events_sent++;

        /* Populate pollfd array */
        for (i = 0; i < num_pipes; i++) {
            pollfds[i].fd = pipes[i].read_fd;
            pollfds[i].events = POLLIN;
            pollfds[i].revents = 0;
        }

        /* Wait for readiness */
        nready = poll(pollfds, num_pipes, 1000);
        
        if (nready > 0) {
            for (i = 0; i < num_pipes; i++) {
                if (pollfds[i].revents & POLLIN) {
                    unsigned char buf;
                    if (read(pipes[i].read_fd, &buf, 1) > 0) {
                        pipes[i].events_received++;
                    }
                }
            }
        }

        uint64_t after = get_time_ns();
        total_latency += (after - before);
    }

    free(pollfds);
    return total_latency;
}

/* Test epoll() multiplexing mechanism */
static uint64_t benchmark_epoll(pipe_pair_t *pipes, int num_pipes, int iterations) {
    int epfd;
    struct epoll_event *events;
    uint64_t total_latency = 0;
    int i, j, nready;

    epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) {
        perror("epoll_create1");
        return 0;
    }

    events = malloc(num_pipes * sizeof(struct epoll_event));
    if (!events) {
        perror("malloc");
        close(epfd);
        return 0;
    }

    /* Register all read fds with epoll */
    for (i = 0; i < num_pipes; i++) {
        struct epoll_event event = {
            .events = EPOLLIN,
            .data.u32 = i
        };
        if (epoll_ctl(epfd, EPOLL_CTL_ADD, pipes[i].read_fd, &event) < 0) {
            perror("epoll_ctl");
            free(events);
            close(epfd);
            return 0;
        }
    }

    for (j = 0; j < iterations; j++) {
        int pipe_idx = rand() % num_pipes;
        unsigned char byte = 42;

        uint64_t before = get_time_ns();

        ssize_t ret = write(pipes[pipe_idx].write_fd, &byte, 1);
        if (ret < 0) {
            perror("write");
            free(events);
            close(epfd);
            return 0;
        }
        pipes[pipe_idx].events_sent++;

        /* Wait for readiness */
        nready = epoll_wait(epfd, events, num_pipes, 1000);
        
        if (nready > 0) {
            for (i = 0; i < nready; i++) {
                unsigned int pipe_idx = events[i].data.u32;
                unsigned char buf;
                if (read(pipes[pipe_idx].read_fd, &buf, 1) > 0) {
                    pipes[pipe_idx].events_received++;
                }
            }
        }

        uint64_t after = get_time_ns();
        total_latency += (after - before);
    }

    free(events);
    close(epfd);
    return total_latency;
}

int main(int argc, char *argv[]) {
    pipe_pair_t pipes[NUM_PIPES];
    int i;

    srand(time(NULL));

    /* Create pipe pairs */
    printf("Creating %d pipe pairs...\n", NUM_PIPES);
    for (i = 0; i < NUM_PIPES; i++) {
        int pipefd[2];
        if (pipe(pipefd) < 0) {
            perror("pipe");
            exit(EXIT_FAILURE);
        }
        pipes[i].read_fd = pipefd[0];
        pipes[i].write_fd = pipefd[1];
        pipes[i].events_sent = 0;
        pipes[i].events_received = 0;
    }

    printf("Running benchmarks with %d iterations...\n\n", ITERATIONS);

    /* Benchmark select */
    printf("=== select() benchmark ===\n");
    uint64_t select_time = benchmark_select(pipes, NUM_PIPES, ITERATIONS);
    double select_latency_us = (double)select_time / (ITERATIONS * 1000.0);
    printf("Total time: %lu ns\n", select_time);
    printf("Average latency per iteration: %.2f us\n", select_latency_us);
    printf("Events sent: %lu\n", pipes[0].events_sent * NUM_PIPES);
    printf("\n");

    /* Reset counters */
    for (i = 0; i < NUM_PIPES; i++) {
        pipes[i].events_sent = 0;
        pipes[i].events_received = 0;
    }

    /* Benchmark poll */
    printf("=== poll() benchmark ===\n");
    uint64_t poll_time = benchmark_poll(pipes, NUM_PIPES, ITERATIONS);
    double poll_latency_us = (double)poll_time / (ITERATIONS * 1000.0);
    printf("Total time: %lu ns\n", poll_time);
    printf("Average latency per iteration: %.2f us\n", poll_latency_us);
    printf("Events sent: %lu\n", pipes[0].events_sent * NUM_PIPES);
    printf("\n");

    /* Reset counters */
    for (i = 0; i < NUM_PIPES; i++) {
        pipes[i].events_sent = 0;
        pipes[i].events_received = 0;
    }

    /* Benchmark epoll */
    printf("=== epoll() benchmark ===\n");
    uint64_t epoll_time = benchmark_epoll(pipes, NUM_PIPES, ITERATIONS);
    double epoll_latency_us = (double)epoll_time / (ITERATIONS * 1000.0);
    printf("Total time: %lu ns\n", epoll_time);
    printf("Average latency per iteration: %.2f us\n", epoll_latency_us);
    printf("Events sent: %lu\n", pipes[0].events_sent * NUM_PIPES);
    printf("\n");

    /* Comparative analysis */
    printf("=== COMPARATIVE ANALYSIS ===\n");
    printf("select() baseline: 1.0x\n");
    printf("poll() relative:   %.2fx\n", (double)poll_time / select_time);
    printf("epoll() relative:  %.2fx\n", (double)epoll_time / select_time);
    printf("\n");

    if (epoll_time < poll_time) {
        printf("epoll() is faster than poll() by %.1f%% on this system.\n",
               ((double)poll_time - epoll_time) / poll_time * 100.0);
    } else {
        printf("poll() is faster than epoll() by %.1f%% on this system.\n",
               ((double)epoll_time - poll_time) / epoll_time * 100.0);
    }

    /* Cleanup */
    for (i = 0; i < NUM_PIPES; i++) {
        close(pipes[i].read_fd);
        close(pipes[i].write_fd);
    }

    return EXIT_SUCCESS;
}
```

Compile and run the benchmark:

```bash
gcc -O2 -o fd_multiplexing fd_multiplexing.c -lrt
./fd_multiplexing
```

#### Results and Interpretation

The benchmark reveals critical performance characteristics that determine which multiplexing mechanism is optimal for a given workload. Select exhibits consistent latency regardless of descriptor count because it uses a fixed-size bitmap (limited to 1024 descriptors on many systems). Poll and epoll scale better with large descriptor counts because they use dynamic data structures. However, on systems with very few descriptors, the simpler overhead of select may make it faster.

The key measurement is latency per event—the time from writing to a pipe until the multiplexing call detects and reports readiness. This latency depends on kernel scheduling, context switching, and the internal implementation of each mechanism. Epoll typically shows the lowest latency on modern Linux systems because it uses event-driven kernels (when available) to avoid scanning all registered descriptors on each call.

Run the benchmark multiple times and correlate results with system load using tools like vmstat or iostat in a separate terminal. The comparative latencies shift under different load conditions, revealing how scheduler behavior affects I/O responsiveness.

---

## Exercise 3: Memory Accounting and Page Fault Instrumentation

### Measuring Virtual Memory Dynamics and Kernel Page Reclamation

Memory management in Linux involves complex interactions between user-space allocation, kernel page tables, and the page replacement algorithm. This exercise instruments memory operations to reveal page fault rates, working set size, and kernel swapping behavior.

#### Conceptual Foundation

Virtual memory abstracts physical RAM, allowing processes to address far more memory than physically available. The kernel manages translation between virtual addresses (visible to the process) and physical addresses (managed by the kernel). A page fault occurs when a process accesses a virtual page not currently resident in physical memory, triggering an interrupt that causes the kernel to load the page from disk or allocate new physical memory. Faults are categorized as major faults (requiring disk I/O) or minor faults (requiring only page table updates).

The kernel's page replacement algorithm—typically a least-recently-used (LRU) variant—evicts pages when memory pressure increases. Understanding when page faults occur, their frequency, and their correlation with memory pressure is essential for diagnosing performance problems in memory-intensive applications.

#### Implementation: Memory Fault Tracer and Working Set Analyzer

Create a C program that allocates memory, triggers page faults, and measures fault latency:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>
#include <sys/times.h>
#include <time.h>

#define PAGE_SIZE 4096
#define MB(x) ((x) * 1024 * 1024)
#define NUM_PAGES(bytes) ((bytes) / PAGE_SIZE)

/* Capture clock ticks to measure fault latency */
static clock_t fault_ticks_start;
static long faults_observed;

void fault_handler(int sig) {
    (void)sig;
    faults_observed++;
}

int main(int argc, char *argv[]) {
    size_t alloc_mb = 100;
    size_t page_count;
    unsigned char *buffer;
    int i;
    struct tms tms_before, tms_after;

    if (argc > 1)
        alloc_mb = atoi(argv[1]);

    page_count = NUM_PAGES(MB(alloc_mb));
    printf("Allocating %zu MB (%zu pages)\n", alloc_mb, page_count);

    /* Allocate buffer but do not yet fault pages in */
    buffer = malloc(MB(alloc_mb));
    if (!buffer) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }

    printf("Buffer allocated at %p\n", (void *)buffer);
    printf("Measuring page fault latency...\n\n");

    faults_observed = 0;
    times(&tms_before);
    fault_ticks_start = tms_before.tms_utime;

    /* Sequential access: touch every page in order */
    printf("=== Sequential Access Pattern ===\n");
    long sequential_start = get_time_ns();
    for (i = 0; i < (int)page_count; i++) {
        /* Access first byte of each page to trigger fault */
        buffer[i * PAGE_SIZE] = i & 0xFF;
    }
    long sequential_elapsed = get_time_ns() - sequential_start;
    printf("Time for sequential access: %.2f ms\n", 
           (double)sequential_elapsed / 1000000.0);
    printf("Average latency per page fault: %.2f us\n",
           (double)sequential_elapsed / (page_count * 1000.0));

    /* Reset for random access test */
    memset(buffer, 0, MB(alloc_mb));

    printf("\n=== Random Access Pattern ===\n");
    srand(42);
    long random_start = get_time_ns();
    for (i = 0; i < (int)page_count; i++) {
        size_t random_page = rand() % page_count;
        buffer[random_page * PAGE_SIZE] = (i & 0xFF);
    }
    long random_elapsed = get_time_ns() - random_start;
    printf("Time for random access: %.2f ms\n",
           (double)random_elapsed / 1000000.0);
    printf("Average latency per page access: %.2f us\n",
           (double)random_elapsed / (page_count * 1000.0));

    /* Locality test: hot/cold pages */
    printf("\n=== Spatial Locality Test ===\n");
    printf("Accessing small working set repeatedly...\n");
    size_t working_set_pages = 10;
    long locality_start = get_time_ns();
    for (i = 0; i < 100000; i++) {
        size_t page = (i % working_set_pages) * PAGE_SIZE;
        buffer[page]++;
    }
    long locality_elapsed = get_time_ns() - locality_start;
    printf("Time for 100,000 accesses to %zu pages: %.2f ms\n",
           working_set_pages, (double)locality_elapsed / 1000000.0);
    printf("Average latency per access: %.2f us\n",
           (double)locality_elapsed / 100000.0);

    times(&tms_after);
    printf("\n=== Timing Summary ===\n");
    printf("User time: %ld ticks\n", tms_after.tms_utime - tms_before.tms_utime);
    printf("System time: %ld ticks\n", tms_after.tms_stime - tms_before.tms_stime);

    free(buffer);
    return EXIT_SUCCESS;
}
```

Compile with:

```bash
gcc -O0 -o memory_faults memory_faults.c
```

Run with strace to observe page fault syscalls (SIGSEGV/SIGBUS handling):

```bash
strace -c -e fault ./memory_faults 100
```

For deeper analysis, use perf to sample page faults:

```bash
perf record -e page-faults,major-faults ./memory_faults 100
perf report
```

#### Interpretation

Sequential access patterns show predictable, low-latency page faults because the kernel can prefetch adjacent pages. Random access patterns exhibit higher latency and more frequent major faults (disk I/O) when the working set exceeds available memory. Spatial locality tests demonstrate cache efficiency: accessing a small set of pages repeatedly keeps them resident in physical memory and L1/L2/L3 caches, resulting in sub-microsecond latencies.

Correlate these measurements with /proc/meminfo and /proc/vmstat to observe system-wide memory pressure, reclamation activity, and swap usage. The relationship between page fault latency and memory pressure is nonlinear—latency remains low until physical memory is exhausted, at which point major faults dominate and latencies spike to milliseconds or more.

---

## Exercise 4: Signal Delivery Races and Atomicity

### Detecting and Measuring Signal Delivery Race Conditions

Signal handling introduces concurrency without explicit threading, creating potential race conditions between signal delivery and user-space code. This exercise constructs scenarios that trigger signal-safety violations and measures the kernel's delivery latency under contention.

#### Conceptual Foundation

Signals are delivered asynchronously, interrupting whatever code is executing. If user-space code modifies data that a signal handler also accesses, undefined behavior results unless the data is protected with mechanisms like sig_atomic_t or signal masking. The kernel guarantees that signals will not interrupt syscalls that have been marked as restartable (SA_RESTART flag), but non-restartable syscalls may return EINTR, requiring user-space retry logic.

Signal delivery latency depends on when the kernel chooses to check for pending signals. Signals are typically checked at syscall return, preemption, or when transitioning from kernel to user space. Measurement reveals the granularity of signal delivery and the overhead of signal handler invocation.

#### Implementation: Signal Race Detector

Create a program that deliberately triggers race conditions and measures signal delivery latency under various conditions:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <pthread.h>
#include <time.h>

volatile sig_atomic_t signal_count = 0;
volatile uint64_t signal_delivery_time_ns = 0;

static uint64_t get_time_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000UL + ts.tv_nsec;
}

void signal_handler(int sig) {
    signal_delivery_time_ns = get_time_ns();
    signal_count++;
}

int main(void) {
    struct sigaction sa;
    pid_t pid;
    int i, status;
    uint64_t latencies[1000];
    int latency_count = 0;

    printf("=== Signal Delivery Latency Test ===\n\n");

    /* Setup signal handler */
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0; /* Do not set SA_RESTART */
    if (sigaction(SIGUSR1, &sa, NULL) < 0) {
        perror("sigaction");
        exit(EXIT_FAILURE);
    }

    pid = fork();
    if (pid < 0) {
        perror("fork");
        exit(EXIT_FAILURE);
    }

    if (pid == 0) {
        /* Child: generate signals to parent */
        usleep(100000); /* Let parent settle */
        
        for (i = 0; i < 100; i++) {
            usleep(10000); /* 10ms between signals */
            kill(getppid(), SIGUSR1);
        }
        exit(EXIT_SUCCESS);
    } else {
        /* Parent: receive signals and measure latency */
        printf("Receiving %d signals from child process...\n", 100);
        printf("Measuring signal delivery latency...\n\n");

        signal_count = 0;
        uint64_t parent_start = get_time_ns();

        while (signal_count < 100) {
            /* Idle CPU: allow signals to arrive */
            uint64_t before = get_time_ns();
            pause(); /* Block until signal arrives */
            uint64_t after = get_time_ns();
            
            if (signal_count > 0) {
                uint64_t latency = signal_delivery_time_ns - before;
                if (latency < 1000000000UL) { /* Sanity check */
                    latencies[latency_count++] = latency;
                }
            }
        }

        uint64_t parent_end = get_time_ns();
        printf("Total signals received: %d\n", signal_count);
        printf("Total elapsed time: %.2f ms\n\n",
               (double)(parent_end - parent_start) / 1000000.0);

        /* Analyze latency distribution */
        if (latency_count > 0) {
            uint64_t min = latencies[0];
            uint64_t max = latencies[0];
            uint64_t sum = 0;

            for (i = 0; i < latency_count; i++) {
                sum += latencies[i];
                if (latencies[i] < min) min = latencies[i];
                if (latencies[i] > max) max = latencies[i];
            }

            printf("Signal Delivery Latency Statistics:\n");
            printf("  Minimum: %.2f us\n", (double)min / 1000.0);
            printf("  Maximum: %.2f us\n", (double)max / 1000.0);
            printf("  Average: %.2f us\n", (double)sum / (latency_count * 1000.0));
            printf("  Samples: %d\n\n", latency_count);
        }

        wait(&status);
    }

    return EXIT_SUCCESS;
}
```

Compile and run:

```bash
gcc -O2 -o signal_latency signal_latency.c -lrt
./signal_latency
```

#### Interpretation

The output reveals signal delivery latency under idle conditions. With minimal contention, latencies should be in the microsecond range. Compare this to the output when the system is under load (run stress-ng in another terminal). Under load, signal delivery latencies increase because the kernel must defer signal processing until a scheduling opportunity arises.

---

## Exercise 5: Systematic Verification Workflow

### Combining Instrumentation Tools into a Coherent Diagnostic Methodology

Production systems require systematic, repeatable verification of core behavior. This exercise integrates strace, perf, /proc inspection, and custom harnesses into a cohesive workflow that captures system state, reproduces issues, and validates fixes.

#### Implementation: Automated Core Verification Suite

Create a master script that coordinates multiple verification tools:

```bash
#!/bin/bash
set -euo pipefail

# core_verification_suite.sh
# Integrated verification workflow for core system behaviors.
# Captures strace, perf, /proc state, and performance metrics.

WORK_DIR="${1:-.}"
cd "$WORK_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="core_verification_${TIMESTAMP}"
mkdir -p "$REPORT_DIR"

echo "Core Verification Suite"
echo "======================="
echo "Report directory: $REPORT_DIR"
echo ""

# Function to capture /proc state snapshot
capture_proc_snapshot() {
    local label="$1"
    local outdir="$REPORT_DIR/proc_$label"
    mkdir -p "$outdir"
    
    for pid in $(pgrep -f 'child_process.sh' 2>/dev/null || echo ""); do
        echo "Capturing /proc state for PID $pid..."
        cp "/proc/$pid/stat" "$outdir/stat_$pid" 2>/dev/null || true
        cp "/proc/$pid/status" "$outdir/status_$pid" 2>/dev/null || true
        cp "/proc/$pid/maps" "$outdir/maps_$pid" 2>/dev/null || true
    done
    
    cp /proc/meminfo "$outdir/meminfo" 2>/dev/null || true
    cp /proc/vmstat "$outdir/vmstat" 2>/dev/null || true
}

# Run Exercise 1: Signal monitoring
echo "Running Exercise 1: Signal Monitoring..."
cd "$REPORT_DIR"
bash ../lab_signal_monitor.sh . 2>&1 | tee signal_monitor.log
capture_proc_snapshot "signal"
cd ..

# Run Exercise 3: Memory faults
echo ""
echo "Running Exercise 3: Memory Faults..."
if [ -f memory_faults ]; then
    perf record -o "$REPORT_DIR/perf_memory.data" -e page-faults,major-faults \
        ./memory_faults 50 2>&1 | tee "$REPORT_DIR/memory_faults.log"
    perf report -i "$REPORT_DIR/perf_memory.data" > "$REPORT_DIR/perf_memory_report.txt" 2>&1 || true
else
    echo "Skipping: memory_faults not compiled"
fi

# Run Exercise 2: File descriptor multiplexing
echo ""
echo "Running Exercise 2: File Descriptor Multiplexing..."
if [ -f fd_multiplexing ]; then
    perf record -o "$REPORT_DIR/perf_fd.data" -e syscalls:sys_enter_epoll_wait,syscalls:sys_enter_poll,syscalls:sys_enter_select \
        ./fd_multiplexing 2>&1 | tee "$REPORT_DIR/fd_multiplexing.log"
else
    echo "Skipping: fd_multiplexing not compiled"
fi

# Run Exercise 4: Signal latency
echo ""
echo "Running Exercise 4: Signal Latency..."
if [ -f signal_latency ]; then
    perf record -o "$REPORT_DIR/perf_signal.data" -e signals:signal_deliver ./signal_latency 2>&1 | tee "$REPORT_DIR/signal_latency.log"
else
    echo "Skipping: signal_latency not compiled"
fi

# Generate summary report
cat > "$REPORT_DIR/SUMMARY.txt" << 'EOF'
CORE VERIFICATION SUITE REPORT
===============================

This report captures system behavior across five core operational domains:

1. Process Lifecycle and Signal Handling
   - Traces all syscalls executed by a child process
   - Measures signal delivery latency and interrupt handling
   - Correlates /proc state transitions with kernel events

2. File Descriptor Management and I/O Multiplexing
   - Compares latency of select(), poll(), and epoll()
   - Measures event detection performance under load
   - Determines optimal multiplexing strategy for workload

3. Memory Accounting and Page Faults
   - Measures page fault latency for sequential and random access
   - Correlates working set size with cache performance
   - Observes kernel page reclamation under memory pressure

4. Signal Delivery Races and Atomicity
   - Measures signal delivery latency under various contention levels
   - Detects signal-safety violations
   - Validates signal masking and restart behavior

5. Systematic Verification Workflow
   - Integrates strace, perf, and /proc inspection
   - Produces reproducible verification artifacts
   - Enables correlation of system events across multiple layers

DIRECTORY STRUCTURE
====================

Each exercise produces:
  - Raw instrumentation output (strace, perf records)
  - Parsed analysis and statistics
  - /proc snapshots for state correlation
  - Performance reports and comparisons

Use perf report -i perf_*.data to view detailed profiling results.
Use grep and awk to correlate events across log files.

NEXT STEPS
==========

1. Review raw logs for anomalies or unexpected behaviors
2. Correlate events across multiple log files using timestamps
3. Compare results from multiple runs to establish baseline variance
4. Use perf report to drill down into syscall hot spots
5. Adjust workload parameters and re-run to test hypotheses
EOF

echo ""
echo "Verification complete. Results in: $REPORT_DIR"
echo "Summary: $REPORT_DIR/SUMMARY.txt"
```

Save as core_verification_suite.sh and run:

```bash
chmod +x core_verification_suite.sh
./core_verification_suite.sh
```

The suite generates a comprehensive report directory containing all instrumentation artifacts, analysis logs, and correlation data.

---

## Conclusion

These exercises provide a rigorous empirical foundation for understanding core operating system behaviors. By instrumenting live processes, measuring precise timing of events, and correlating data across multiple observation layers, you develop deep intuition about how the kernel manages processes, memory, I/O, and signals. The techniques and tools introduced here—strace, perf, /proc inspection, and custom harnesses—form the core of production diagnostics and performance optimization work.

The key insight unifying all exercises is that observable, measurable phenomena replace abstract models. Rather than reasoning about process states theoretically, you observe them directly in strace output. Rather than assuming signal delivery is instantaneous, you measure it in microseconds. Rather than guessing which multiplexing mechanism is faster, you benchmark them systematically. This empirical discipline, grounded in concrete measurement and reproducible experimentation, is the essence of operational verification and the foundation for building reliable systems.
