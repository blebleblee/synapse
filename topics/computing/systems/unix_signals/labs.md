# Operational Verification Labs: Unix Signals

## Objective & Toolchain Setup

Unix signals constitute the kernel's primary asynchronous interrupt mechanism for userspace process control, delivering coarse-grained notifications that range from terminal control events (SIGINT, SIGTSTP) to fatal hardware exceptions (SIGSEGV, SIGBUS) and real-time application-defined messages (SIGRTMIN through SIGRTMAX). Mastering signal semantics requires understanding their delivery as software interrupts that hijack the normal execution stream, invoking registered handlers in an async-signal-safe context where the majority of libc functions become illegal due to non-reentrancy and heap allocator state corruption risks. These laboratories ground signal behavior in concrete observable phenomena: handler preemption timing, race windows between signal delivery and sigprocmask atomicity, the distinction between reliable POSIX signals and legacy unreliable semantics, and the architectural constraints that force signal handlers into a severely restricted programming model where only a handful of syscalls (write, _exit, sigaction) and atomic operations remain safe.

The verification environment demands a complete systems toolchain anchored in LLVM/Clang for C compilation with precise control over optimization levels and sanitizer instrumentation, Rust's cargo ecosystem for memory-safe signal handling patterns, GDB and LLDB for single-stepping through handler invocation sequences, and specialized race detection via ThreadSanitizer. Install the baseline toolchain with `rustup default stable && rustup component add llvm-tools-preview`, then add system utilities: `sudo apt install clang lldb gdb valgrind strace`. Verify LLDB integration with `lldb --version` confirming LLVM 14+ and ensure AddressSanitizer availability via `clang -fsanitize=address --version`. The diagnostic workflow layers static analysis (cargo clippy, clang-tidy) over dynamic race detection (TSAN) and syscall tracing (strace -e signal=all), constructing a multi-level verification stack that exposes signal timing bugs invisible to unit tests. Each exercise builds on the principle that signal correctness cannot be proven through casual testing—only through deliberate race construction, controlled signal injection with kill(2) and pthread_kill(3), and inspection of handler execution state under memory corruption and concurrent modification scenarios.

Prepare the workspace with `mkdir -p signal_labs/{c_handlers,rust_async,race_stress} && cd signal_labs`. The C exercises compile with `-std=gnu11 -Wall -Wextra -g3 -O0` to preserve debugger fidelity, escalating to `-O2` for cache profiling and `-fsanitize=thread` for race detection. Rust exercises employ `cargo new --bin <name>` with explicit `signal-hook` and `libc` dependencies, verifying handler safety through `cargo clippy -- -W clippy::all -W clippy::pedantic` and race freedom via `cargo +nightly build -Z build-std --target x86_64-unknown-linux-gnu`. The cheat sheet consolidates async-signal-safe functions from POSIX.1-2008 §2.4.3, enumerates sigaction flag semantics (SA_RESTART, SA_NODEFER, SA_RESETHAND), and catalogs the 32 standard signals with their default dispositions and generation sources. This infrastructure transforms signal programming from an error-prone art into a mechanically verifiable discipline where every race condition and reentrancy violation manifests as a reproducible TSAN warning or LLDB breakpoint hit.

## Exercise 1: Signal Handler Preemption & Async-Signal-Safe Constraints

Signal handlers execute in a constrained context where the interrupted thread's state remains frozen on the kernel stack, the heap allocator may hold internal locks, and stdio buffers sit in partially flushed states—rendering the vast majority of libc functions unsafe for invocation. This exercise constructs deliberate violations of async-signal-safe programming rules, observing the resulting undefined behavior through allocator corruption, printf deadlock, and errno clobbering, then refactors handlers into compliant implementations using only the 117 functions guaranteed safe by POSIX. The core insight centers on reentrancy: a signal can arrive while the interrupted code holds a mutex or has partially updated a data structure, so handler code must avoid any operation that might wait on that same lock or observe inconsistent state.

Create `c_handlers/unsafe_handler.c` with a deliberately broken SIGINT handler that violates multiple safety rules. The program installs a handler calling malloc, printf, and a non-reentrant global counter, then triggers signals in a tight loop while the main thread performs the same operations, creating a race condition on both the heap allocator and the global variable:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>

static volatile int unsafe_counter = 0;

void unsafe_handler(int signo) {
    int saved_errno = errno;
    
    // VIOLATION 1: malloc is not async-signal-safe
    char *buf = malloc(128);
    if (buf != NULL) {
        // VIOLATION 2: snprintf is not async-signal-safe
        snprintf(buf, 128, "Signal %d received, counter=%d\n", signo, unsafe_counter);
        
        // VIOLATION 3: printf holds internal locks
        printf("%s", buf);
        fflush(stdout);
        
        free(buf);
    }
    
    // VIOLATION 4: non-atomic read-modify-write on shared state
    unsafe_counter++;
    
    errno = saved_errno;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = unsafe_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    printf("Process %d: Press Ctrl-C repeatedly. Expect corruption or deadlock.\n", getpid());
    
    for (int i = 0; i < 50000; i++) {
        char *allocation = malloc(64);
        if (allocation != NULL) {
            snprintf(allocation, 64, "Main thread iteration %d\n", i);
            if (i % 1000 == 0) {
                printf("%s", allocation);
            }
            free(allocation);
        }
        unsafe_counter += 2;
    }
    
    printf("Final counter: %d (expected ~100000 if no races)\n", unsafe_counter);
    return 0;
}
```

Compile with `clang -o unsafe_handler unsafe_handler.c -Wall -Wextra -g3 -O0` and execute while triggering signals: `./unsafe_handler` then rapidly press Ctrl-C in the terminal. Observe symptoms ranging from garbled printf output (interleaved writes to stdout), to immediate deadlock (main thread waiting on malloc's arena lock while handler holds it), to segmentation faults from heap metadata corruption. Run under AddressSanitizer to expose heap corruption: `clang -fsanitize=address -o unsafe_asan unsafe_handler.c && ./unsafe_asan`. ASAN reports will show heap-use-after-free or double-free violations when signal preemption catches malloc mid-operation. The counter will show lost updates due to non-atomic increments—if main thread and handler both execute `unsafe_counter++` simultaneously, the final value undershoots the expected sum.

Trace syscalls during signal delivery with `strace -o trace.log -e signal=all,write ./unsafe_handler 2>&1` while pressing Ctrl-C. The trace reveals `rt_sigaction` installing the handler, `rt_sigreturn` restoring context after each handler run, and frequent `write` syscalls (from printf) showing mid-stream interruption. The log demonstrates that printf's internal buffering state breaks under preemption—multiple write calls for a single printf can be interleaved with handler output, producing character-level scrambling.

Now construct the compliant refactored version in `c_handlers/safe_handler.c`, restricting handler operations to the async-signal-safe subset. The safe handler uses only write(2) to an unbuffered file descriptor, sig_atomic_t for shared counters, and careful errno preservation. Remove all heap allocation, replace printf with raw write calls, and employ atomic flag patterns for main-thread communication:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <stdatomic.h>

static volatile sig_atomic_t signal_count = 0;
static volatile sig_atomic_t shutdown_flag = 0;

void safe_handler(int signo) {
    int saved_errno = errno;
    
    const char msg[] = "SIGINT received\n";
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
    
    signal_count++;
    
    if (signal_count >= 5) {
        shutdown_flag = 1;
    }
    
    errno = saved_errno;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = safe_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    printf("Process %d: Safe handler active. Press Ctrl-C 5 times to exit.\n", getpid());
    
    while (!shutdown_flag) {
        pause();
    }
    
    printf("\nShutdown after %d signals.\n", (int)signal_count);
    return 0;
}
```

Compile with `clang -o safe_handler safe_handler.c -Wall -Wextra -g3` and verify clean execution under ASAN: `clang -fsanitize=address -o safe_asan safe_handler.c && ./safe_asan`. The program now exhibits no heap corruption, no printf deadlocks, and correct signal counting. Run under LLDB to inspect handler execution: `lldb ./safe_handler`, set breakpoint `b safe_handler`, continue with `run`, then trigger SIGINT via Ctrl-C. LLDB halts inside the handler, allowing examination of the kernel-provided signal frame with `register read` (showing PC saved in the sigcontext) and `bt` (displaying the interrupted call stack beneath the signal trampoline). Step through the write syscall with `si` (step instruction) and observe the direct transition from user handler to kernel via the syscall instruction, with no libc wrapper overhead.

Extend the exercise by implementing a Rust equivalent using the `signal-hook` crate for safe async handling. Create `rust_async/safe_signals/Cargo.toml`:

```toml
[package]
name = "safe_signals"
version = "0.1.0"
edition = "2021"

[dependencies]
signal-hook = "0.3"
```

Implement `rust_async/safe_signals/src/main.rs` with atomic flag communication and signal-hook's iterator-based model that moves signal processing out of handler context:

```rust
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Duration;
use signal_hook::consts::SIGINT;
use signal_hook::iterator::Signals;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let shutdown = Arc::new(AtomicBool::new(false));
    let signal_count = Arc::new(AtomicUsize::new(0));
    
    let shutdown_clone = Arc::clone(&shutdown);
    let count_clone = Arc::clone(&signal_count);
    
    let mut signals = Signals::new(&[SIGINT])?;
    
    std::thread::spawn(move || {
        for sig in signals.forever() {
            eprintln!("Received signal {:?}", sig);
            count_clone.fetch_add(1, Ordering::SeqCst);
            
            if count_clone.load(Ordering::SeqCst) >= 5 {
                shutdown_clone.store(true, Ordering::SeqCst);
                break;
            }
        }
    });
    
    println!("Process {}: Rust safe handler. Press Ctrl-C 5 times to exit.", std::process::id());
    
    while !shutdown.load(Ordering::SeqCst) {
        std::thread::sleep(Duration::from_millis(100));
    }
    
    println!("\nShutdown after {} signals.", signal_count.load(Ordering::SeqCst));
    Ok(())
}
```

Build and run with `cargo run --release`. The signal-hook architecture solves reentrancy by deferring all complex operations to a dedicated signal-handling thread that reads from a lock-free signal notification pipe, keeping the actual signal handler restricted to a single write(2) syscall. Verify thread safety with `cargo +nightly build -Z build-std --target x86_64-unknown-linux-gnu` under TSAN (requires nightly Rust and custom target configuration). The Rust model demonstrates how language-level abstractions (Arc, atomic types, channel-based communication) provide memory-safe signal handling without sacrificing the async-signal-safe constraint.

Benchmark handler latency by sending signals from a separate process. Create `c_handlers/signal_latency.c` that forks a child process, installs a handler with timestamp recording, and measures the delay between kill(2) invocation and handler execution:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/types.h>
#include <sys/wait.h>

static volatile sig_atomic_t signal_received = 0;

void timing_handler(int signo) {
    (void)signo;
    signal_received = 1;
}

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ volatile ("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = timing_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    
    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    pid_t child = fork();
    if (child == -1) {
        perror("fork");
        return 1;
    }
    
    if (child == 0) {
        // Child: send signal after short delay
        usleep(100000);
        kill(getppid(), SIGUSR1);
        _exit(0);
    }
    
    // Parent: measure handler invocation latency
    uint64_t start = rdtsc();
    while (!signal_received) {
        __asm__ volatile ("pause");
    }
    uint64_t end = rdtsc();
    
    wait(NULL);
    
    uint64_t cycles = end - start;
    printf("Signal delivery latency: ~%lu cycles\n", cycles);
    printf("(Approximate, includes loop overhead. Typical range: 10,000-50,000 cycles)\n");
    
    return 0;
}
```

Compile with `clang -o signal_latency signal_latency.c -O2` and execute multiple times, observing cycle counts that typically range from 10,000 to 50,000 TSC ticks depending on scheduler quantum and kernel preemption latency. The measurement captures the entire round-trip from kill(2) syscall through kernel signal delivery queue, scheduler intervention, context switch into handler, and flag store completion. Run under `perf stat -e cycles,instructions,context-switches ./signal_latency` to correlate with context switch counts—each signal delivery forces at least one involuntary context switch as the kernel transfers control to the handler.

## Exercise 2: Signal Masking, Race Windows & sigprocmask Atomicity

Signal mask manipulation via sigprocmask(2) controls which signals the kernel delivers immediately versus queues for later processing, providing the critical synchronization primitive for protecting non-reentrant code sections against asynchronous preemption. However, the check-then-act pattern of testing a flag followed by blocking on a signal creates an unavoidable race window unless sigsuspend(2) atomically swaps the mask and enters the wait state. This exercise constructs both buggy signal-flag polling and correct sigsuspend-based synchronization, measuring the race window under load and verifying the fix through stress testing with rapid signal injection.

Create `c_handlers/mask_race.c` demonstrating the classic signal race condition where a signal arrives between checking a flag and entering pause(2). The main thread checks a volatile flag set by SIGUSR1, and if not set, calls pause(). The race occurs when SIGUSR1 arrives after the flag check but before pause() blocks—the signal handler sets the flag, but the main thread already committed to blocking, resulting in indefinite sleep despite the signal being delivered:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

static volatile sig_atomic_t event_flag = 0;

void event_handler(int signo) {
    (void)signo;
    event_flag = 1;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = event_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    
    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    printf("Process %d: BUGGY version with race window.\n", getpid());
    printf("In another terminal, run: kill -USR1 %d\n", getpid());
    printf("If signal arrives during race window, process hangs indefinitely.\n\n");
    
    // Simulate work that checks flag periodically
    for (int i = 0; i < 10; i++) {
        printf("Iteration %d: Checking event flag...\n", i);
        
        // RACE WINDOW: signal can arrive between this check and pause()
        if (event_flag == 0) {
            printf("  Flag not set, entering pause()...\n");
            pause();  // If signal arrived after check but before this, we hang
            printf("  Woke from pause()\n");
        }
        
        if (event_flag) {
            printf("Event received! Exiting.\n");
            return 0;
        }
        
        sleep(1);
    }
    
    printf("Timed out without receiving event.\n");
    return 1;
}
```

Compile with `clang -o mask_race mask_race.c -Wall -Wextra -g3` and run in one terminal, then immediately send SIGUSR1 from another: `./mask_race & sleep 0.5 && kill -USR1 $!`. The race manifests sporadically—sometimes the signal arrives cleanly during pause(), waking the process correctly, but occasionally it hits the window between the flag check and pause() call, causing indefinite hang. Instrument the race by adding a deliberate delay: insert `usleep(100000);` between the flag check and pause() call to widen the window, making the bug deterministic.

Trace the failure under strace to observe the signal arriving while the process executes code between the flag check and the pause syscall: `strace -o race_trace.log ./mask_race` then `kill -USR1 $(pidof mask_race)` during the sleep. The trace shows `rt_sigaction`, the pause() syscall invocation, `rt_sigreturn` from the handler, but if the signal arrived mid-race, you see pause() entered after the handler already executed, with no subsequent wakeup. The kernel correctly delivered the signal and ran the handler, but the userspace logic committed to blocking based on stale flag state.

Now implement the correct version using sigsuspend(2) to atomically unmask the signal and wait, eliminating the race window. Create `c_handlers/mask_correct.c`:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

static volatile sig_atomic_t event_flag = 0;

void event_handler(int signo) {
    (void)signo;
    event_flag = 1;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = event_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    
    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    // Block SIGUSR1 initially to prevent premature delivery
    sigset_t mask, oldmask, waitmask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGUSR1);
    
    if (sigprocmask(SIG_BLOCK, &mask, &oldmask) == -1) {
        perror("sigprocmask");
        return 1;
    }
    
    printf("Process %d: CORRECT version using sigsuspend.\n", getpid());
    printf("In another terminal, run: kill -USR1 %d\n", getpid());
    
    // Prepare wait mask: unblock SIGUSR1 during sigsuspend only
    waitmask = oldmask;
    sigdelset(&waitmask, SIGUSR1);
    
    for (int i = 0; i < 10; i++) {
        printf("Iteration %d: Waiting for event...\n", i);
        
        // Check flag with signal masked
        if (event_flag == 0) {
            // Atomically unblock SIGUSR1 and wait
            // No race: signal cannot arrive between check and wait
            sigsuspend(&waitmask);
        }
        
        if (event_flag) {
            printf("Event received! Exiting.\n");
            sigprocmask(SIG_SETMASK, &oldmask, NULL);
            return 0;
        }
    }
    
    printf("Timed out without receiving event.\n");
    sigprocmask(SIG_SETMASK, &oldmask, NULL);
    return 1;
}
```

Compile with `clang -o mask_correct mask_correct.c -Wall -Wextra -g3` and stress-test with rapid signal delivery: `./mask_correct & for i in {1..100}; do kill -USR1 $! 2>/dev/null; usleep 10000; done`. The process cleanly receives the first signal and exits, never hanging regardless of signal timing. The sigsuspend(2) syscall guarantees atomicity—the kernel checks for pending signals, and if SIGUSR1 is queued, delivers it immediately without entering sleep. If not pending, the kernel blocks with SIGUSR1 unmasked, ensuring the next delivery wakes the process.

Inspect the syscall sequence with `strace -e signal=all,rt_sigprocmask,rt_sigsuspend ./mask_correct` while sending signals. The trace reveals `rt_sigprocmask(SIG_BLOCK, [USR1], ...)` installing the mask, `rt_sigsuspend([...] without USR1)` atomically waiting, and `rt_sigreturn` completing the handler. Contrast with the buggy version's separate `pause()` call that lacks atomic mask manipulation.

Extend to multi-threaded signal handling by creating `c_handlers/thread_signals.c`, where pthread_sigmask(3) controls per-thread masks and pthread_kill(3) directs signals to specific threads. The program spawns a worker thread with SIGUSR1 blocked globally except in a designated signal-handling thread, demonstrating signal routing in threaded applications:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <errno.h>

static volatile sig_atomic_t signals_received = 0;

void* signal_thread(void* arg) {
    (void)arg;
    sigset_t mask;
    int sig;
    
    sigemptyset(&mask);
    sigaddset(&mask, SIGUSR1);
    sigaddset(&mask, SIGINT);
    
    printf("Signal thread %lu: waiting for signals via sigwait...\n", pthread_self());
    
    while (1) {
        if (sigwait(&mask, &sig) == 0) {
            printf("Signal thread caught signal %d\n", sig);
            signals_received++;
            
            if (sig == SIGINT) {
                printf("SIGINT received, exiting signal thread.\n");
                break;
            }
        }
    }
    
    return NULL;
}

void* worker_thread(void* arg) {
    int id = *(int*)arg;
    
    printf("Worker thread %d (%lu): performing work with signals blocked.\n", id, pthread_self());
    
    for (int i = 0; i < 5; i++) {
        printf("  Worker %d: iteration %d\n", id, i);
        sleep(1);
    }
    
    printf("Worker thread %d exiting.\n", id);
    return NULL;
}

int main(void) {
    pthread_t sig_thread, workers[3];
    int worker_ids[3] = {1, 2, 3};
    
    // Block SIGUSR1 and SIGINT in all threads (inherited by children)
    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGUSR1);
    sigaddset(&mask, SIGINT);
    
    if (pthread_sigmask(SIG_BLOCK, &mask, NULL) != 0) {
        perror("pthread_sigmask");
        return 1;
    }
    
    printf("Main thread: signals blocked, starting threads.\n");
    
    // Create dedicated signal handling thread
    if (pthread_create(&sig_thread, NULL, signal_thread, NULL) != 0) {
        perror("pthread_create signal_thread");
        return 1;
    }
    
    // Create worker threads that inherit blocked mask
    for (int i = 0; i < 3; i++) {
        if (pthread_create(&workers[i], NULL, worker_thread, &worker_ids[i]) != 0) {
            perror("pthread_create worker");
            return 1;
        }
    }
    
    printf("\nMain thread: Send signals with: kill -USR1 %d\n", getpid());
    printf("Press Ctrl-C to shut down.\n\n");
    
    // Wait for workers to complete
    for (int i = 0; i < 3; i++) {
        pthread_join(workers[i], NULL);
    }
    
    // Send SIGINT to self to wake signal thread
    kill(getpid(), SIGINT);
    pthread_join(sig_thread, NULL);
    
    printf("\nTotal signals received: %d\n", signals_received);
    return 0;
}
```

Compile with `clang -o thread_signals thread_signals.c -pthread -Wall -Wextra -g3` and run, then send signals from another terminal: `./thread_signals & sleep 1; for i in {1..5}; do kill -USR1 $!; sleep 1; done; kill -INT $!`. Observe that SIGUSR1 signals route exclusively to the signal thread despite the process-wide delivery—the kernel delivers signals to any thread where the signal is unblocked, and since only the signal thread has SIGUSR1 unmasked, it becomes the sole recipient. The worker threads continue uninterrupted, never seeing signal interruptions in their sleep() calls.

Verify thread-safety with ThreadSanitizer: `clang -fsanitize=thread -o thread_tsan thread_signals.c -pthread -g3 && ./thread_tsan`, then send signals as before. TSAN confirms no data races on the `signals_received` variable because it's only modified within the signal thread, eliminating concurrent access. The sigwait(3) pattern avoids async-signal-safe constraints entirely by converting asynchronous signals into synchronous thread wakeups, allowing arbitrary code execution without reentrancy concerns.

Profile signal handler overhead by instrumenting the timing_handler from Exercise 1 with perf: `perf record -e cycles:u,instructions:u,cache-misses -g ./signal_latency`, then analyze with `perf report` and `perf annotate`. The flamegraph reveals cycles spent in kernel signal delivery paths (do_signal, handle_signal) and the cost of saving/restoring the full register context. For high-frequency signal delivery, this overhead becomes non-trivial—switching to signalfd(2) or io_uring with IORING_OP_POLL_ADD provides lower-latency alternatives for notification-heavy workloads.

## Exercise 3: Signal-Driven Data Race Construction & TSAN Verification

Signals introduce concurrency into ostensibly single-threaded programs by preempting execution at arbitrary instructions, creating implicit data races on non-atomic variables accessed from both main code and signal handlers. This exercise deliberately constructs race conditions where signal handlers and main-thread code concurrently modify shared state without proper synchronization, observing the resulting corruption through lost updates, torn reads, and inconsistent invariants. ThreadSanitizer exposes these bugs by instrumenting memory accesses and detecting unsynchronized read-write conflicts, while manual analysis correlates race manifestations with specific instruction interleavings.

Create `c_handlers/signal_race.c` with a SIGUSR1 handler and main loop that both increment a shared counter using non-atomic operations. The race occurs because the increment operation compiles to a read-modify-write sequence (load, add, store) that is not indivisible—a signal arriving mid-sequence causes both execution contexts to load the same initial value, perform their increments, and write back results, losing one update:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>

static int shared_counter = 0;  // Deliberately non-atomic

void racing_handler(int signo) {
    (void)signo;
    shared_counter++;  // RACE: non-atomic read-modify-write
}

void trigger_signals(int count, pid_t target) {
    for (int i = 0; i < count; i++) {
        kill(target, SIGUSR1);
        usleep(100);
    }
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = racing_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    
    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    pid_t pid = getpid();
    printf("Process %d: Starting race test.\n", pid);
    printf("Each thread increments counter 1000 times.\n");
    printf("Expected final value: 2000. Actual will be lower due to races.\n\n");
    
    // Spawn thread to send signals
    pthread_t trigger_thread;
    pthread_create(&trigger_thread, NULL, (void*(*)(void*))trigger_signals, (void*)(intptr_t)1000);
    
    // Main thread also increments counter
    for (int i = 0; i < 1000; i++) {
        shared_counter++;  // RACE: concurrent with handler
        usleep(100);
    }
    
    pthread_join(trigger_thread, NULL);
    
    printf("Final counter value: %d (lost %d updates)\n", shared_counter, 2000 - shared_counter);
    
    if (shared_counter < 2000) {
        printf("RACE DETECTED: Lost updates confirm data race.\n");
    }
    
    return 0;
}
```

Compile without sanitizers first to observe the race: `clang -o signal_race signal_race.c -pthread -Wall -Wextra -O2` and run multiple times: `for i in {1..10}; do ./signal_race; done`. The final counter varies between ~1200-1900, never reaching 2000, with lost updates ranging from hundreds to a thousand. The non-determinism arises from varying preemption points—each execution's signal delivery timing differs, catching the main thread at different instruction offsets within the increment sequence.

Now compile with ThreadSanitizer: `clang -fsanitize=thread -o signal_race_tsan signal_race.c -pthread -g3 -O1` and execute: `./signal_race_tsan`. TSAN immediately reports data races:

```text
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 4 at 0x... by signal handler:
    #0 racing_handler signal_race.c:12
    
  Previous write of size 4 at 0x... by main thread:
    #0 main signal_race.c:34
```

The report pinpoints both conflicting accesses: the handler's increment and the main thread's increment, confirming the race hypothesis. TSAN's vector clock algorithm tracks happens-before relationships and detects that these accesses lack synchronization edges. The line numbers guide immediate fix identification.

Extend the race to a more insidious invariant violation by creating `c_handlers/invariant_race.c` where a signal handler observes a data structure mid-update, seeing torn state that violates internal consistency constraints. The example maintains a Point structure with x and y coordinates that should always satisfy `y = x * 2`, but the non-atomic update sequence allows the handler to observe intermediate state where the invariant is broken:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef struct {
    int x;
    int y;  // Invariant: y should always equal x * 2
} Point;

static Point global_point = {0, 0};
static volatile sig_atomic_t violations = 0;

void invariant_checker(int signo) {
    (void)signo;
    
    // Read both fields (non-atomic, can see torn state)
    int x = global_point.x;
    int y = global_point.y;
    
    if (y != x * 2) {
        violations++;
    }
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = invariant_checker;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    
    if (sigaction(SIGALRM, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    // Send SIGALRM every 10us
    struct itimerval timer;
    timer.it_value.tv_sec = 0;
    timer.it_value.tv_usec = 10;
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 10;
    
    if (setitimer(ITIMER_REAL, &timer, NULL) == -1) {
        perror("setitimer");
        return 1;
    }
    
    printf("Running invariant race test for 1 second...\n");
    printf("Updating Point with invariant y = x * 2\n");
    printf("Signal handler checks invariant concurrently.\n\n");
    
    // Update point rapidly, creating race windows
    for (int i = 0; i < 100000; i++) {
        global_point.x = i;         // First update
        // RACE WINDOW: signal can arrive here
        global_point.y = i * 2;     // Second update
    }
    
    // Stop timer
    timer.it_value.tv_usec = 0;
    setitimer(ITIMER_REAL, &timer, NULL);
    
    printf("Invariant violations detected: %d\n", (int)violations);
    
    if (violations > 0) {
        printf("RACE DETECTED: Handler observed torn state between x and y updates.\n");
    }
    
    return 0;
}
```

Compile with `clang -o invariant_race invariant_race.c -Wall -Wextra -O2` and execute: `./invariant_race`. The program reports hundreds to thousands of violations, confirming that SIGALRM frequently arrives during the window between the two assignments, allowing the handler to read `x = i` but `y = (i-1) * 2`, violating the invariant. This pattern mirrors real bugs in interrupt handlers reading partially updated hardware registers or signal handlers accessing multi-field structures.

Run under TSAN: `clang -fsanitize=thread -o invariant_race_tsan invariant_race.c -g3 -O1 && ./invariant_race_tsan`. TSAN reports multiple data races on both `global_point.x` and `global_point.y`, identifying the unsynchronized access pattern. The fix requires either atomic operations or signal masking around the critical section. Implement the masked version:

```c
int main(void) {
    // ... (setup as before)
    
    sigset_t mask, oldmask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGALRM);
    
    for (int i = 0; i < 100000; i++) {
        // Mask SIGALRM during update
        sigprocmask(SIG_BLOCK, &mask, &oldmask);
        
        global_point.x = i;
        global_point.y = i * 2;
        
        // Unmask SIGALRM
        sigprocmask(SIG_SETMASK, &oldmask, NULL);
    }
    
    // ... (rest as before)
}
```

Recompile and run—violations drop to zero. The sigprocmask calls create a critical section where SIGALRM cannot preempt the update sequence, eliminating the torn read. However, this approach incurs significant overhead (two syscalls per iteration). Profile the impact: `perf stat -e cycles,syscalls:sys_enter_rt_sigprocmask ./invariant_race_masked` shows millions of sigprocmask calls dominating execution time.

The performant solution employs C11 atomic operations, allowing lock-free invariant maintenance. Create `c_handlers/atomic_point.c`:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>

typedef struct {
    _Atomic int x;
    _Atomic int y;
} AtomicPoint;

static AtomicPoint global_point = {0, 0};
static atomic_int violations = 0;

void invariant_checker(int signo) {
    (void)signo;
    
    int x = atomic_load_explicit(&global_point.x, memory_order_acquire);
    int y = atomic_load_explicit(&global_point.y, memory_order_acquire);
    
    if (y != x * 2) {
        atomic_fetch_add_explicit(&violations, 1, memory_order_relaxed);
    }
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = invariant_checker;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    
    if (sigaction(SIGALRM, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    struct itimerval timer;
    timer.it_value.tv_sec = 0;
    timer.it_value.tv_usec = 10;
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 10;
    
    if (setitimer(ITIMER_REAL, &timer, NULL) == -1) {
        perror("setitimer");
        return 1;
    }
    
    printf("Running atomic invariant test...\n");
    
    for (int i = 0; i < 100000; i++) {
        atomic_store_explicit(&global_point.x, i, memory_order_release);
        atomic_store_explicit(&global_point.y, i * 2, memory_order_release);
    }
    
    timer.it_value.tv_usec = 0;
    setitimer(ITIMER_REAL, &timer, NULL);
    
    int viol = atomic_load(&violations);
    printf("Invariant violations detected: %d\n", viol);
    
    if (viol > 0) {
        printf("Note: Atomics prevent torn reads, but inter-field consistency still requires locking.\n");
    } else {
        printf("SUCCESS: No violations with atomic operations (or got lucky with timing).\n");
    }
    
    return 0;
}
```

Compile with `clang -o atomic_point atomic_point.c -std=c11 -Wall -Wextra -O2` and run: `./atomic_point`. Violations may still occur because atomics guarantee individual field consistency but not multi-field transaction atomicity—the handler can read an updated x but a not-yet-updated y if the signal arrives between the two stores. The correct solution for multi-field invariants either masks signals during updates or uses a versioned structure with atomic pointer swap.

Implement the versioned approach in `c_handlers/versioned_point.c`:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdatomic.h>

typedef struct {
    int x;
    int y;
} Point;

static Point point_buffers[2] = {{0, 0}, {0, 0}};
static _Atomic(Point*) current_point = &point_buffers[0];
static atomic_int violations = 0;

void invariant_checker(int signo) {
    (void)signo;
    
    Point* p = atomic_load_explicit(&current_point, memory_order_acquire);
    
    if (p->y != p->x * 2) {
        atomic_fetch_add_explicit(&violations, 1, memory_order_relaxed);
    }
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = invariant_checker;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    
    if (sigaction(SIGALRM, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }
    
    struct itimerval timer;
    timer.it_value.tv_sec = 0;
    timer.it_value.tv_usec = 10;
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 10;
    
    if (setitimer(ITIMER_REAL, &timer, NULL) == -1) {
        perror("setitimer");
        return 1;
    }
    
    printf("Running versioned structure test...\n");
    
    for (int i = 0; i < 100000; i++) {
        Point* current = atomic_load(&current_point);
        Point* next = (current == &point_buffers[0]) ? &point_buffers[1] : &point_buffers[0];
        
        next->x = i;
        next->y = i * 2;
        
        atomic_store_explicit(&current_point, next, memory_order_release);
    }
    
    timer.it_value.tv_usec = 0;
    setitimer(ITIMER_REAL, &timer, NULL);
    
    printf("Invariant violations detected: %d\n", atomic_load(&violations));
    printf("SUCCESS: Atomic pointer swap ensures handlers always see consistent state.\n");
    
    return 0;
}
```

Compile and execute: `clang -o versioned_point versioned_point.c -std=c11 -O2 && ./versioned_point`. Violations now drop to zero—the atomic pointer swap ensures the handler sees either the old or new Point structure atomically, never intermediate state. This double-buffering pattern applies broadly to concurrent data structure updates under signal preemption.

Stress-test all race patterns with a signal bombardment harness. Create `c_handlers/signal_storm.c` that spawns multiple threads each sending a different signal (SIGUSR1, SIGUSR2, SIGALRM) at high frequency to a worker thread incrementing a shared counter protected only by various synchronization strategies:

```c
#define _GNU_SOURCE
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <stdatomic.h>

static atomic_int counter_atomic = 0;
static int counter_unprotected = 0;

void storm_handler(int signo) {
    (void)signo;
    atomic_fetch_add_explicit(&counter_atomic, 1, memory_order_relaxed);
    counter_unprotected++;
}

void* signal_sender(void* arg) {
    int signo = (int)(intptr_t)arg;
    pid_t target = getpid();
    
    for (int i = 0; i < 10000; i++) {
        kill(target, signo);
    }
    
    return NULL;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = storm_handler;
    sigfillset(&sa.sa_mask);  // Block all signals during handler execution
    sa.sa_flags = SA_RESTART;
    
    sigaction(SIGUSR1, &sa, NULL);
    sigaction(SIGUSR2, &sa, NULL);
    sigaction(SIGALRM, &sa, NULL);
    
    printf("Signal storm test: 3 threads sending 10k signals each.\n");
    printf("Expected counter: 30000\n\n");
    
    pthread_t senders[3];
    pthread_create(&senders[0], NULL, signal_sender, (void*)(intptr_t)SIGUSR1);
    pthread_create(&senders[1], NULL, signal_sender, (void*)(intptr_t)SIGUSR2);
    pthread_create(&senders[2], NULL, signal_sender, (void*)(intptr_t)SIGALRM);
    
    for (int i = 0; i < 3; i++) {
        pthread_join(senders[i], NULL);
    }
    
    sleep(1);  // Allow pending signals to drain
    
    printf("Atomic counter:       %d (should be ~30000)\n", atomic_load(&counter_atomic));
    printf("Unprotected counter:  %d (will show lost updates)\n", counter_unprotected);
    printf("Lost updates:         %d\n", 30000 - counter_unprotected);
    
    return 0;
}
```

Compile with TSAN and execute: `clang -fsanitize=thread -o signal_storm signal_storm.c -pthread -g3 && ./signal_storm`. TSAN floods the output with data race reports on `counter_unprotected`, confirming pervasive concurrent access violations. The atomic counter reaches near 30,000, while the unprotected counter shows thousands of lost updates. The sigfillset mask on sa.sa_mask prevents signal-handler-to-signal-handler races (nested invocations) but does not eliminate main-thread-to-handler races.

Benchmark the overhead of different synchronization strategies by timing 1 million signal deliveries under various protection schemes: `perf stat -e cycles,instructions ./signal_storm` for the atomic version, then compare against a masked version that blocks signals around counter updates. The atomic approach incurs near-zero overhead per signal (single lock-prefixed instruction), while masking requires two sigprocmask syscalls per update, increasing cycles by 100-1000x.

## Developer Cheat Sheet & Toolchain Checklist

### Async-Signal-Safe Function Reference (POSIX.1-2008 Subset)

The following functions are guaranteed safe for invocation from signal handlers. All other libc functions risk deadlock or corruption:

**Core I/O:** `read, write, open, close, dup, dup2, pipe, lseek, fsync, fstat`  
**Process Control:** `_exit, fork, kill, raise, sigaction, sigpending, sigprocmask, sigsuspend, waitpid`  
**File System:** `access, chdir, chmod, chown, link, mkdir, rename, rmdir, stat, unlink`  
**Memory:** `mmap, munmap` (but not malloc/free)  
**Atomics:** All C11 `atomic_*` functions, `__sync_*` GCC builtins  
**Signal-Specific:** `alarm, pause, sigaddset, sigdelset, sigemptyset, sigfillset, sigismember`

**Universally Unsafe (Never Call from Handlers):**
`malloc, calloc, free, realloc, printf, fprintf, sprintf, pthread_mutex_lock, pthread_cond_wait, fopen, fclose, fflush, exit, longjmp` (unless jumping from same handler invocation)

### sigaction Flag Semantics

- `SA_RESTART`: Automatically restart interrupted syscalls (read, write, wait, etc.). Without this, syscalls return EINTR, requiring manual retry loops.
- `SA_NODEFER`: Do not mask the signal during handler execution, allowing recursive delivery. Dangerous—use only for handlers provably safe under reentrancy.
- `SA_RESETHAND`: Reset disposition to SIG_DFL after one delivery (one-shot handler). Mimics legacy signal() behavior.
- `SA_SIGINFO`: Use three-argument handler (`void (*)(int, siginfo_t*, void*)`) providing signal source, fault address (for SIGSEGV), and originating PID.
- `SA_ONSTACK`: Execute handler on alternate signal stack configured via sigaltstack(2). Essential for handling stack overflow (SIGSEGV from guard page breach).

### Standard Signal Catalog (Partial)

| Signal    | Default Action | Generation Source                          |
|-----------|----------------|--------------------------------------------|
| SIGHUP    | Terminate      | Terminal disconnect, daemon config reload  |
| SIGINT    | Terminate      | Ctrl-C (tty interrupt character)           |
| SIGQUIT   | Core dump      | Ctrl-\ (tty quit character)                |
| SIGILL    | Core dump      | Illegal instruction execution              |
| SIGSEGV   | Core dump      | Invalid memory access (page fault)         |
| SIGPIPE   | Terminate      | Write to closed pipe/socket                |
| SIGALRM   | Terminate      | alarm() timer expiration                   |
| SIGTERM   | Terminate      | Graceful shutdown request (kill default)   |
| SIGUSR1/2 | Terminate      | User-defined application signals           |
| SIGCHLD   | Ignore         | Child process termination/stop             |
| SIGSTOP   | Stop (forced)  | Unconditional process suspension           |
| SIGCONT   | Resume         | Resume stopped process                     |

### Race-Free Signal Patterns

**Flag-Based Notification:**
```c
static volatile sig_atomic_t flag = 0;

void handler(int sig) { flag = 1; }

// Main loop with race-free check
sigset_t mask, oldmask, waitmask;
sigemptyset(&mask);
sigaddset(&mask, SIGUSR1);
sigprocmask(SIG_BLOCK, &mask, &oldmask);

waitmask = oldmask;
sigdelset(&waitmask, SIGUSR1);

while (!flag) {
    sigsuspend(&waitmask);  // Atomically unmask and wait
}
sigprocmask(SIG_SETMASK, &oldmask, NULL);
```

**Self-Pipe Trick (Convert Async Signal to I/O Event):**
```c
int pipefd[2];
pipe(pipefd);
set_nonblocking(pipefd[0]);
set_nonblocking(pipefd[1]);

void handler(int sig) {
    char c = sig;
    write(pipefd[1], &c, 1);  // Async-signal-safe write
}

// Main loop polls pipe instead of using signal flags
struct pollfd pfd = { .fd = pipefd[0], .events = POLLIN };
poll(&pfd, 1, -1);
char sig;
read(pipefd[0], &sig, 1);
// Process signal in normal context
```

### Compilation & Sanitizer Invocations

**Basic C Build with Maximum Warnings:**
```bash
clang -std=gnu11 -Wall -Wextra -Wpedantic -Wconversion \
      -Wshadow -Wstrict-prototypes -g3 -O0 -o prog prog.c
```

**AddressSanitizer (Heap Corruption Detection):**
```bash
clang -fsanitize=address -fno-omit-frame-pointer -g3 -O1 \
      -o prog_asan prog.c
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 ./prog_asan
```

**ThreadSanitizer (Race Detection):**
```bash
clang -fsanitize=thread -g3 -O1 -o prog_tsan prog.c -pthread
TSAN_OPTIONS=halt_on_error=1:history_size=7 ./prog_tsan
```

**Valgrind Memcheck:**
```bash
valgrind --leak-check=full --track-origins=yes \
         --show-leak-kinds=all ./prog
```

**Syscall Tracing with Signal Focus:**
```bash
strace -e signal=all -e trace=rt_sigaction,rt_sigprocmask,rt_sigsuspend \
       -f -o trace.log ./prog
```

**Rust with Signal-Hook (Safe Async Handling):**
```bash
cargo add signal-hook
cargo clippy -- -W clippy::all -W clippy::pedantic
cargo test --release
```

**GDB Signal-Specific Debugging:**
```bash
gdb ./prog
(gdb) handle SIGUSR1 nostop print pass  # Let program receive it
(gdb) break safe_handler
(gdb) run
# Trigger signal from another terminal: kill -USR1 <pid>
(gdb) info signals  # Show signal handling configuration
(gdb) info registers  # Inspect sigcontext register state
```

### Performance Profiling Signals

**Measure Signal Delivery Latency:**
```bash
perf stat -e cycles,instructions,context-switches -r 10 ./signal_latency
```

**Flamegraph of Handler Overhead:**
```bash
perf record -e cycles:u -g --call-graph dwarf -- ./signal_storm
perf script | stackcollapse-perf.pl | flamegraph.pl > signals.svg
```

**LLVM Profiling Data Collection:**
```bash
clang -fprofile-instr-generate -fcoverage-mapping -o prog prog.c
LLVM_PROFILE_FILE="prof-%p.profraw" ./prog
llvm-profdata merge -sparse prof-*.profraw -o prog.profdata
llvm-cov show ./prog -instr-profile=prog.profdata
```

This laboratory infrastructure transforms signal handling from an esoteric systems programming hazard into a mechanically verifiable discipline. Every race condition, every reentrancy violation, and every timing-dependent bug becomes reproducible through controlled signal injection, observable under sanitizer instrumentation, and correctable via atomic primitives or mask-based critical sections. The exercises progress from basic safety violations through mask atomicity to full multi-threaded signal routing, building the complete mental model required to architect robust signal-driven systems without silent corruption or deadlock.
