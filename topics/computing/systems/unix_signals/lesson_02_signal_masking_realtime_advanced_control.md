# Lesson 2: Signal Masking, Real-Time Signals, Advanced Control Mechanisms

## 1. First-Principles Intuition & Invariants

A Unix signal is not merely a notification. It is a kernel-mediated interruption of userspace execution that forces a context switch into a registered handler, and this act of interruption carries profound implications for any program that assumes linear, uninterrupted control flow. The difficulty with signals is not in sending them — `kill(pid, SIGTERM)` is trivial — but in receiving them safely. A handler can fire between any two machine instructions where the processor is in userspace, which means it can interrupt a `malloc` in the middle of updating a free-list bin, or a `printf` while `stdout`'s buffer lock is held. If the handler then calls `malloc` or `printf` itself, the result is a reentrancy catastrophe. The standard library is not, in general, async-signal-safe, and this single invariant — that the signal handler runs in a hostile, partially-mutated world — shapes every correct signal architecture in production systems.

The kernel's solution to this reentrancy problem is the signal mask: a per-thread bitmask of `NSIG` bits (typically 65 signals on modern Linux, signals 1 through 64, with 0 reserved as an invalid sentinel) stored in the thread's `struct task_struct` inside `signal->blocked`. When a signal is generated (by `kill`, `tgkill`, a hardware fault, `timer_settime`, or `sigqueue`), the kernel checks this mask. If the corresponding bit is set, the signal does not fire immediately. Instead, it is recorded as *pending* in either the per-thread `task_struct->pending` list or the per-process `signal->shared_pending` list, and it remains dormant there until the mask is cleared. This is the critical invariant: a blocked signal is not lost. It is deferred. The moment the thread unblocks that signal number — by calling `sigprocmask` or `pthread_sigmask` to clear the bit — the kernel delivers the oldest pending instance before returning to userspace. This deferral mechanism transforms signals from an uncontrollable interruption into a schedulable event, and it is the foundation upon which every robust signal architecture is built.

The distinction between *generation* and *delivery* is therefore the first conceptual pillar. Generation is the act of the kernel recording that a signal is owed to a process; delivery is the act of actually invoking the handler (or performing the default action). Between generation and delivery lies the *pending* state, which is where blocked signals wait. A signal that is generated while blocked stays pending indefinitely. The second pillar is *atomicity of the unblock-and-wait operation*: a thread that wants to wait for a signal must not race with the signal's arrival. If you unblock a signal with `sigprocmask` and then immediately call `sigsuspend`, a signal arriving in the gap between those two calls will be delivered before `sigsuspend` begins, and `sigsuspend` will then wait forever for a signal that has already been handled. This race is the classic signal-wait bug, and `sigsuspend` exists specifically to close it by replacing the mask and entering the wait state as a single atomic kernel operation.

Real-time signals (SIGRTMIN through SIGRTMAX, typically 34 through 64 on Linux) introduce a third pillar: *queued semantics*. Standard signals (1 through 31) are not queued. If three `SIGUSR1` signals are generated while `SIGUSR1` is blocked, the kernel records a single pending bit, and on unblock, the handler fires exactly once. Real-time signals, by contrast, are individually queued in a linked list of `sigqueue` structures, each carrying an optional `siginfo_t` payload (an integer `si_value` or a pointer). If you `sigqueue` three `SIGRTMIN+1` signals while the signal is blocked, all three are enqueued, and on unblock, the handler fires three times in FIFO order. This queuing guarantee makes real-time signals suitable for reliable inter-process communication — a channel that cannot drop messages merely because the receiver was momentarily busy.

---

## 2. Core Architecture & Mechanics

### The Signal Mask and `sigprocmask`

Every thread in a Linux process carries its own `sigset_t` blocked mask. In the kernel, this is represented as a `sigset_t` inside `task_struct->signal->blocked` for the main thread and per-thread copies for additional threads created via `pthread_create`. The `sigprocmask` system call (or `pthread_sigmask` in a threaded program — `sigprocmask` is undefined behavior in a multithreaded process on some platforms, though glibc makes it safe) modifies this mask using one of three operations: `SIG_BLOCK` (OR the given set into the current mask), `SIG_UNBLOCK` (AND-NOT the given set out), and `SIG_SETMASK` (replace the mask entirely). The previous mask is always returned through the optional `oldset` pointer, which is essential for writing handlers that temporarily block a signal, do work, and then restore the original mask.

The `sigset_t` type on glibc is a 128-byte structure containing a 1024-bit bitmap, though only the first 64 bits are meaningful on standard Linux. Signal numbers are 1-indexed, so `sigaddset(&set, SIGTERM)` sets bit `SIGTERM - 1` in the internal representation. The `sigfillset`, `sigemptyset`, `sigaddset`, and `sigdelset` functions are the only sanctioned way to manipulate `sigset_t` values — never bit-twiddle the structure directly, as the internal layout is not guaranteed across libc versions or architectures.

The following program demonstrates a production-grade pattern: block `SIGINT` and `SIGTERM`, perform a critical section where those signals must not interrupt, then atomically unblock and wait using `sigsuspend`. This is the canonical safe critical-section pattern for signal-aware code.

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <errno.h>

static volatile sig_atomic_t got_signal = 0;
static volatile sig_atomic_t signal_num = 0;

static void handler(int signo, siginfo_t *info, void *ctx)
{
    (void)ctx;
    (void)info;
    got_signal = 1;
    signal_num = signo;
}

int main(void)
{
    struct sigaction sa;
    sigset_t blocked, oldmask, waitmask;

    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = handler;
    sa.sa_flags = SA_SIGINFO | SA_RESTART;
    sigemptyset(&sa.sa_mask);

    if (sigaction(SIGINT, &sa, NULL) == -1) {
        perror("sigaction(SIGINT)");
        return 1;
    }
    if (sigaction(SIGTERM, &sa, NULL) == -1) {
        perror("sigaction(SIGTERM)");
        return 1;
    }

    sigemptyset(&blocked);
    sigaddset(&blocked, SIGINT);
    sigaddset(&blocked, SIGTERM);

    if (sigprocmask(SIG_BLOCK, &blocked, &oldmask) == -1) {
        perror("sigprocmask");
        return 1;
    }

    printf("Critical section: SIGINT/SIGTERM blocked. Working for 3 seconds...\n");
    fflush(stdout);
    for (int i = 0; i < 3; i++) {
        sleep(1);
        printf("  critical work tick %d\n", i + 1);
        fflush(stdout);
    }

    printf("Critical section done. Preparing to wait atomically.\n");

    /*
     * Build the mask that sigsuspend will install temporarily.
     * sigsuspend replaces the current mask with waitmask, then
     * blocks until a signal arrives that is NOT in waitmask.
     * After the handler returns, the original mask is restored.
     *
     * To wait for SIGINT or SIGTERM, we must set waitmask to
     * everything EXCEPT those two signals. The easiest way is
     * to start from the oldmask (which may block other signals
     * the program cares about) and then unblock SIGINT and SIGTERM.
     */
    waitmask = oldmask;
    sigdelset(&waitmask, SIGINT);
    sigdelset(&waitmask, SIGTERM);

    printf("Waiting atomically for SIGINT or SIGTERM...\n");
    fflush(stdout);

    while (!got_signal) {
        sigsuspend(&waitmask);
    }

    printf("Received signal %d (%s). Restoring original mask.\n",
           signal_num,
           signal_num == SIGINT ? "SIGINT" : "SIGTERM");

    if (sigprocmask(SIG_SETMASK, &oldmask, NULL) == -1) {
        perror("sigprocmask(restore)");
        return 1;
    }

    printf("Exiting cleanly.\n");
    return 0;
}
```

The `sigsuspend` call is the heart of this pattern. Without it, the code would need to call `sigprocmask(SIG_UNBLOCK, ...)` followed by `pause()`, and a signal arriving in the microsecond gap between those two calls would be delivered, its handler run, and `pause()` would then block forever because the signal was already consumed. `sigsuspend` closes this race by performing the mask swap and the schedule-wait in a single atomic operation: the kernel sets the new mask, checks for pending unblocked signals, delivers any that are ready, and only enters the wait state if none were pending. The function returns only after a handler has run, and the original mask is automatically restored on return.

### `sigaction` Flags and Handler Semantics

The `sigaction` structure is the only correct way to install a signal handler in modern code. The older `signal()` function has unpredictable semantics across platforms — on some systems it resets the handler to `SIG_DFL` after the first invocation (System V behavior), on others it does not (BSD behavior). `sigaction` makes the behavior explicit and gives precise control over how the kernel delivers the signal.

The `sa_flags` field controls the delivery contract:

- `SA_SIGINFO`: The handler receives three arguments instead of one. The second is a `siginfo_t *` containing the signal number (`si_signo`), the sending PID (`si_pid`), the sending UID (`si_uid`), the exit status for `SIGCHLD` (`si_status`), the user-supplied payload for real-time signals (`si_value`), and for hardware faults, the offending address (`si_addr`). The third is a `ucontext_t *` giving access to the full register state at the point of interruption, which is how crash handlers extract backtraces.
- `SA_RESTART`: Automatically restart interrupted system calls. When a signal handler fires during a blocking `read()`, the `read` returns `-1` with `errno == EINTR`. With `SA_RESTART`, the kernel transparently restarts the call instead. Note that this does not apply to all calls: `select`, `poll`, `epoll_wait`, `sleep`, and `recvfrom` on a non-blocking-restart socket are not restarted even with `SA_RESTART`. Always check `man 7 signal` for the exact list of restartable calls on your platform.
- `SA_NODEFER`: By default, the signal being handled is automatically added to the mask during handler execution, preventing the handler from re-entering itself. `SA_NODEFER` disables this self-masking. This is dangerous: a second instance of the same signal can interrupt the handler. Use only when the handler is strictly reentrant and you understand the stacking implications.
- `SA_RESETHAND`: Restore the handler to `SIG_DFL` after the first invocation. This is the System V `signal()` behavior made explicit. It is occasionally useful for a one-shot signal, but it creates a race window between handler exit and the reset, during which a second signal takes the default action (often terminating the process).
- `SA_ONSTACK`: Deliver the signal on an alternate signal stack (see below).
- `SA_NOCLDWAIT`: For `SIGCHLD`, prevents zombie processes. The kernel will not create a zombie for children that are waited on with this flag set.
- `SA_NOCLDSTOP`: Do not generate `SIGCHLD` when children stop or continue (only on death).
- `SA_RESTORER`: Internal to glibc; you never set this directly.

The `sa_mask` field in the `sigaction` structure specifies additional signals to block during the handler's execution, in addition to the signal being handled. This is how you prevent `SIGTERM` from interrupting a `SIGINT` handler if they share critical state. The mask is per-handler: each handler has its own add-to-mask set, and all masked signals are unblocked when the handler returns.

### Alternate Signal Stack: `sigaltstack`

When the main stack overflows (a `SIGSEGV` triggered by exceeding the stack rlimit), the kernel cannot deliver the signal handler on the same stack that just overflowed. The handler would immediately fault again, and the process would die with no diagnostic. `sigaltstack` solves this by registering a separate memory region exclusively for signal delivery. When `SA_ONSTACK` is set on a `sigaction` and a signal arrives, the kernel switches `RSP` to the top of the alternate stack, runs the handler there, and switches back on return.

The alternate stack is declared with `stack_t ss`, where `ss_sp` is the base pointer, `ss_size` is the size, and `ss_flags` can include `SS_AUTODISARM` (a Linux 4.7+ extension that automatically disables the altstack while the handler is running, preventing accidental nesting). The minimum allowed size is `MINSIGSTKSZ`, but production code should use `SIGSTKSZ` or larger to accommodate deep backtrace-walking in crash handlers.

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <ucontext.h>

static void overflow_handler(int signo, siginfo_t *info, void *uctx)
{
    ucontext_t *uc = (ucontext_t *)uctx;
    (void)info;

    char buf[256];
    int n = snprintf(buf, sizeof(buf),
        "CAUGHT SIGSEGV at RIP=0x%llx\n"
        "Signal number: %d\n"
        "Fault address: %p\n"
        "Stack pointer: 0x%llx\n",
        (unsigned long long)uc->uc_mcontext.gregs[REG_RIP],
        signo,
        info->si_addr,
        (unsigned long long)uc->uc_mcontext.gregs[REG_RSP]);

    write(STDERR_FILENO, buf, n);

    _exit(137); /* 128 + signal number convention */
}

static void install_altstack(void)
{
    stack_t ss;
    ss.ss_sp = malloc(SIGSTKSZ);
    if (!ss.ss_sp) {
        perror("malloc altstack");
        _exit(1);
    }
    ss.ss_size = SIGSTKSZ;
    ss.ss_flags = 0;

    if (sigaltstack(&ss, NULL) == -1) {
        perror("sigaltstack");
        _exit(1);
    }
}

static void recursive_crash(int depth)
{
    char pad[4096];
    memset(pad, 'X', sizeof(pad));
    printf("depth=%d, addr of pad=%p\n", depth, (void *)pad);
    fflush(stdout);
    recursive_crash(depth + 1);
}

int main(void)
{
    struct sigaction sa;
    stack_t check;

    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = overflow_handler;
    sa.sa_flags = SA_SIGINFO | SA_ONSTACK | SA_NODEFER;
    sigemptyset(&sa.sa_mask);

    install_altstack();

    if (sigaction(SIGSEGV, &sa, NULL) == -1) {
        perror("sigaction(SIGSEGV)");
        return 1;
    }

    if (sigaltstack(NULL, &check) == 0) {
        printf("Altstack installed: ss_sp=%p, ss_size=%zu, flags=%d\n",
               check.ss_sp, check.ss_size, check.ss_flags);
    }

    printf("Starting recursive crash to overflow stack...\n");
    fflush(stdout);
    recursive_crash(0);

    return 0;
}
```

The `SA_NODEFER` flag here is deliberate. When the handler fires, `SIGSEGV` is normally auto-masked. With `SA_NODEFER`, we unmask it so that if the handler itself faults (say, by accidentally dereferencing a bad pointer during backtrace generation), the default `SIGSEGV` action fires and the process dies immediately rather than looping in the handler. The `_exit(137)` at the end of the handler is essential: you must not return from a `SIGSEGV` handler because the faulting instruction will re-execute and immediately re-trigger the fault. The handler must terminate the process or use `siglongjmp` to jump to a recovery point.

### Real-Time Signals and `sigqueue`

Real-time signals occupy the range `SIGRTMIN` to `SIGRTMAX`. On glibc, `SIGRTMIN` is 34, but the C library reserves signals 32 and 33 internally for thread cancellation (`SIGCANCEL`) and `SIGSETXID`, so application code must always use the symbolic `SIGRTMIN` and `SIGRTMAX` macros, never raw numbers. The range is typically 30 signals (34 through 64), though this varies by configuration.

The defining property of real-time signals is queuing. When a standard signal (1–31) is generated while blocked, the kernel sets a single bit in the pending bitmask. Multiple generations collapse to one delivery. Real-time signals, by contrast, are enqueued as individual `struct sigqueue` nodes in a linked list hanging off the pending signal structure. Each node carries the signal number and an optional `sigval` union — either an integer (`sival_int`) or a pointer (`sival_ptr`). This means real-time signals function as a bounded, priority-ordered message queue between processes.

The ordering guarantee for real-time signals is strict: signals of the same number are delivered in FIFO order (the order they were generated), and signals of different numbers are delivered in ascending numeric order. `SIGRTMIN+1` will be delivered before `SIGRTMIN+5` if both are pending and unblocked at the same time. This numeric ordering is the priority scheme: lower-numbered real-time signals are higher priority.

The `sigqueue` system call is the sending side. It takes a PID, a signal number, and a `sigval` payload. Unlike `kill`, it allows the sender to attach data. The receiver, with `SA_SIGINFO` installed, reads this data from `info->si_value` in the handler. The queue depth is bounded by the per-signal `rlimit_sigpending` resource limit (viewable via `ulimit -a` or `getrlimit(RLIMIT_SIGPENDING, ...)`). When the queue is full, `sigqueue` returns `-1` with `errno == EAGAIN`, which is the backpressure mechanism.

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>

/*
 * Demonstrate real-time signal queuing and siginfo payloads.
 * Parent sends multiple SIGRTMIN+1 signals with integer payloads,
 * child receives them in FIFO order with full queuing semantics.
 */

static volatile sig_atomic_t count = 0;

static void rt_handler(int signo, siginfo_t *info, void *ctx)
{
    (void)ctx;
    count++;
    char buf[128];
    int n = snprintf(buf, sizeof(buf),
        "RECEIVE #%d: signo=%d, si_value.sival_int=%d, si_pid=%d\n",
        count, signo, info->si_value.sival_int, info->si_pid);
    write(STDOUT_FILENO, buf, n);
}

int main(void)
{
    pid_t child;
    int rt_sig = SIGRTMIN + 1;

    child = fork();
    if (child == 0) {
        /* Child: receiver */
        struct sigaction sa;
        memset(&sa, 0, sizeof(sa));
        sa.sa_sigaction = rt_handler;
        sa.sa_flags = SA_SIGINFO | SA_RESTART;
        sigemptyset(&sa.sa_mask);

        if (sigaction(rt_sig, &sa, NULL) == -1) {
            perror("child sigaction");
            _exit(1);
        }

        /* Block the signal first so we can accumulate a queue */
        sigset_t blockmask;
        sigemptyset(&blockmask);
        sigaddset(&blockmask, rt_sig);
        if (sigprocmask(SIG_BLOCK, &blockmask, NULL) == -1) {
            perror("child block");
            _exit(1);
        }

        printf("Child PID=%d: blocked signal %d, waiting 2s for queue to build up\n",
               getpid(), rt_sig);
        fflush(stdout);
        sleep(2);

        printf("Child: unblocking signal %d, expect ordered delivery\n", rt_sig);
        fflush(stdout);

        /* Unblock and let the queued signals drain */
        sigprocmask(SIG_UNBLOCK, &blockmask, NULL);

        /* Give handler time to run */
        sleep(1);

        printf("Child: received %d signals total\n", count);
        fflush(stdout);
        _exit(0);
    }

    /* Parent: sender */
    sleep(1); /* let child set up */

    printf("Parent: sending 5 queued real-time signals (%d) to child\n", rt_sig);
    fflush(stdout);

    for (int i = 100; i < 105; i++) {
        union sigval sv;
        sv.sival_int = i;
        if (sigqueue(child, rt_sig, sv) == -1) {
            fprintf(stderr, "sigqueue %d failed: %s\n", i, strerror(errno));
        } else {
            printf("Parent: sigqueue sent payload=%d\n", i);
            fflush(stdout);
        }
    }

    /* Also send some standard signals to show they do NOT queue */
    printf("Parent: sending 3 standard SIGUSR1 (will NOT queue)\n");
    fflush(stdout);
    kill(child, SIGUSR1);
    kill(child, SIGUSR1);
    kill(child, SIGUSR1);
    /* These will collapse to 1 delivery */

    waitpid(child, NULL, 0);
    printf("Parent: child exited\n");
    return 0;
}
```

When this program runs, the child will receive all five real-time signals with their payloads intact, in order 100 through 104. The three `SIGUSR1` signals, by contrast, will collapse into a single delivery because standard signals do not queue — only one pending bit is kept. This is the fundamental architectural difference between the two signal classes, and it is why real-time signals are the correct choice for any IPC channel where message loss is unacceptable.

### `signalfd`: Signals as File Descriptors

The traditional signal delivery model is asynchronous and callback-based: a handler fires at an unpredictable time, interrupts whatever the thread is doing, and the handler must be minimal and async-signal-safe. This model composes poorly with modern event-loop architectures (`epoll`, `kqueue`, `io_uring`) where the application wants to treat all I/O uniformly through file descriptors. The `signalfd` system call, available on Linux 2.6.22+, bridges this gap by turning signal delivery into a readable file descriptor. Instead of registering a handler, the program blocks the signal with `sigprocmask` (this is mandatory — `signalfd` only delivers signals that are blocked and pending) and then creates a `signalfd` that becomes readable when those signals arrive.

The `signalfd` approach eliminates the async-signal-safety constraint entirely. The signal is read as a `signalfd_siginfo` structure from the file descriptor in the main event loop, using the same `epoll` machinery that handles socket I/O. The handler runs in normal context, not signal context, so it can call `printf`, `malloc`, lock mutexes, and use the full standard library without reentrancy concerns. This is the cleanest way to integrate signals into a modern event-driven architecture.

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/signalfd.h>
#include <sys/epoll.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/wait.h>

/*
 * signalfd integration with epoll.
 * Block SIGINT and SIGTERM via sigprocmask, create a signalfd,
 * register it with epoll, and handle signals in the main loop
 * alongside any other file descriptors.
 */

int main(void)
{
    int sfd, epfd;
    sigset_t mask;
    struct epoll_event ev, events[8];

    /* Block SIGINT and SIGTERM so they are delivered via signalfd */
    sigemptyset(&mask);
    sigaddset(&mask, SIGINT);
    sigaddset(&mask, SIGTERM);

    if (sigprocmask(SIG_BLOCK, &mask, NULL) == -1) {
        perror("sigprocmask");
        return 1;
    }

    /* Create the signalfd. Pass the mask of signals to capture.
     * SFD_CLOEXEC prevents leakage across exec.
     * SFD_NONBLOCK makes reads non-blocking by default. */
    sfd = signalfd(-1, &mask, SFD_CLOEXEC | SFD_NONBLOCK);
    if (sfd == -1) {
        perror("signalfd");
        return 1;
    }

    epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd == -1) {
        perror("epoll_create1");
        close(sfd);
        return 1;
    }

    ev.events = EPOLLIN;
    ev.data.fd = sfd;
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &ev) == -1) {
        perror("epoll_ctl signalfd");
        close(sfd);
        close(epfd);
        return 1;
    }

    printf("Event loop ready. PID=%d. Send SIGINT or SIGTERM.\n", getpid());
    fflush(stdout);

    for (;;) {
        int nfd = epoll_wait(epfd, events, 8, -1);
        if (nfd == -1) {
            if (errno == EINTR)
                continue;
            perror("epoll_wait");
            break;
        }

        for (int i = 0; i < nfd; i++) {
            if (events[i].data.fd == sfd) {
                struct signalfd_siginfo siginfo;
                ssize_t n;

                /* Read all pending signal events (non-blocking fd) */
                while ((n = read(sfd, &siginfo, sizeof(siginfo))) > 0) {
                    if (n != sizeof(siginfo)) {
                        fprintf(stderr, "short read on signalfd: %zd\n", n);
                        continue;
                    }

                    printf("Signal received:\n"
                           "  si_signo     = %u\n"
                           "  si_errno    = %d\n"
                           "  si_code     = %u\n"
                           "  si_pid      = %u\n"
                           "  si_uid      = %u\n"
                           "  si_value    = 0x%llx\n"
                           "  si_int      = %d\n"
                           "  si_ptr      = %p\n"
                           "  si_overrun  = %u\n"
                           "  si_fd       = %d\n"
                           "  si_band     = %lu\n"
                           "  si_addr     = %p\n"
                           "  si_status   = %d\n",
                           siginfo.ssi_signo,
                           siginfo.ssi_errno,
                           siginfo.ssi_code,
                           siginfo.ssi_pid,
                           siginfo.ssi_uid,
                           (unsigned long long)siginfo.ssi_ptr,
                           siginfo.ssi_int,
                           (void *)siginfo.ssi_ptr,
                           siginfo.ssi_overrun,
                           siginfo.ssi_fd,
                           (unsigned long)siginfo.ssi_band,
                           (void *)siginfo.ssi_addr,
                           siginfo.ssi_status);
                    fflush(stdout);

                    if (siginfo.ssi_signo == SIGINT) {
                        printf("Got SIGINT. Continuing (press Ctrl-C again or send SIGTERM).\n");
                        fflush(stdout);
                    } else if (siginfo.ssi_signo == SIGTERM) {
                        printf("Got SIGTERM. Exiting.\n");
                        fflush(stdout);
                        goto cleanup;
                    }
                }
                /* n == -1 with EAGAIN means no more pending signals */
            }
        }
    }

cleanup:
    close(sfd);
    close(epfd);
    return 0;
}
```

The `signalfd_siginfo` structure (accessed via `struct signalfd_siginfo`) mirrors `siginfo_t` but with slightly different field naming (the `ssi_` prefix instead of `si_`). Every field that the kernel populates is available: the sender's PID and UID, the payload value, the fault address for `SIGSEGV`, the file descriptor for `SIGIO`, the child exit status for `SIGCHLD`. This means `signalfd` gives you strictly more information than a plain `signal()` handler, and it does so in a context where you can safely call any function in the standard library.

One subtlety: if you create a `signalfd` with `signalfd(fd, &mask, flags)` where `fd` is an existing signalfd, the call updates the signal set on that fd rather than creating a new one. This is useful when the set of signals you care about changes dynamically. Also note that `signalfd` is Linux-specific; portable code targeting BSDs or macOS must use `kqueue`'s `EVFILT_SIGNAL` or the traditional handler approach.

### Signal Inheritance Across `fork` and `exec`

The `fork` system call creates a complete copy of the process's signal state. The child inherits the parent's signal dispositions (all installed handlers), the blocked mask, and the pending signal set. If the parent had `SIGTERM` blocked and pending, the child starts with `SIGTERM` blocked and pending. This is critical for multi-process servers: if the parent blocks `SIGCHLD` before forking worker children, the workers inherit that block, and if they do not explicitly unblock it, they will never receive child-death notifications for their own children.

The `exec` call has different semantics. Signal dispositions that were set to a handler function (`SIG_DFL` or a function pointer) are reset to `SIG_DFL` on exec because the handler's code address is meaningless in the new program's address space. Signals that were explicitly set to `SIG_IGN` (ignore) before exec remain `SIG_IGN` after exec. This is deliberate: it allows a parent to set `SIGCHLD` to `SIG_IGN` before forking and execing a child, ensuring the child starts with `SIGCHLD` ignored, which prevents zombies for any grandchildren the child might create. The blocked mask is fully inherited across exec — blocked signals stay blocked. This means a program that starts with certain signals blocked (because the parent blocked them before exec) must explicitly unblock them if it wants to handle them. The classic example is a shell that blocks `SIGINT` before forking a backgrounded job.

Pending signals are not inherited across exec. The pending set is cleared — a signal that was pending before exec will not be delivered to the new program. This makes sense because the handler would have been reset to default, so delivering a pending signal would trigger the default action (often termination) rather than the handler the old program intended.

### Process Groups, Sessions, and Signal Delivery

Every process belongs to a process group, identified by a PGID. The process group leader is the process whose PID equals the PGID. Process groups exist primarily to control signal delivery: `kill(-pgid, signo)` sends a signal to every process in the group simultaneously. This is how a shell sends `SIGINT` to a foreground pipeline: it calls `kill(-pgid, SIGINT)`, and every process in the pipeline receives the signal. The negative PID in `kill()` is the process-group convention.

A session is a higher-level grouping containing one or more process groups. The session leader is the process whose PID equals the SID. A session has at most one controlling terminal, and the foreground process group of that terminal is the one that receives terminal-generated signals (`SIGINT` from Ctrl-C, `SIGQUIT` from Ctrl-\, `SIGTSTP` from Ctrl-Z). When a terminal driver generates one of these signals, the kernel sends it to every process in the foreground process group of the session.

The `setsid` call creates a new session and process group, detaching the calling process from any controlling terminal. This is what daemons do to survive the death of their parent session — they call `fork`, the parent exits, the child calls `setsid` to become a session leader with no controlling terminal, and terminal-generated signals no longer reach them. The second `fork` in the classic double-fork daemon pattern ensures the child is not a session leader and therefore cannot reacquire a controlling terminal by opening a terminal device.

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

/*
 * Process group signal delivery demonstration.
 * Parent creates a process group with 3 children, then sends
 * a signal to the entire group via kill(-pgid, signo).
 */

static volatile sig_atomic_t got = 0;

static void chld_handler(int signo)
{
    got = signo;
}

int main(void)
{
    pid_t pgid, pids[3];
    struct sigaction sa;

    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = chld_handler;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);

    /* Parent creates a new process group so kill(-pgid) targets only children */
    setpgid(0, 0);
    pgid = getpgrp();

    printf("Parent PID=%d, PGID=%d\n", getpid(), pgid);
    fflush(stdout);

    for (int i = 0; i < 3; i++) {
        pids[i] = fork();
        if (pids[i] == 0) {
            /* Child: join the parent's process group explicitly */
            setpgid(0, pgid);

            if (sigaction(SIGUSR1, &sa, NULL) == -1) {
                perror("child sigaction");
                _exit(1);
            }

            printf("  Child %d: PID=%d, PGID=%d, waiting for SIGUSR1\n",
                   i, getpid(), getpgrp());
            fflush(stdout);

            while (!got)
                pause();

            printf("  Child %d: PID=%d received SIGUSR1, exiting\n", i, getpid());
            fflush(stdout);
            _exit(0);
        }
    }

    sleep(1);

    printf("Parent: sending SIGUSR1 to entire process group %d\n", pgid);
    fflush(stdout);

    /* Send to the entire group: negative PGID */
    if (kill(-pgid, SIGUSR1) == -1) {
        perror("kill(-pgid)");
    }

    for (int i = 0; i < 3; i++) {
        waitpid(pids[i], NULL, 0);
    }

    printf("Parent: all children exited\n");
    return 0;
}
```

The `kill(-pgid, SIGUSR1)` call delivers `SIGUSR1` to every process in process group `pgid` simultaneously. The kernel iterates the process group list and queues the signal to each member. This is an all-or-nothing broadcast from the sender's perspective, but each receiver handles the signal independently according to its own disposition. If one child has `SIGUSR1` blocked, it will not fire immediately but will remain pending for that child; the other children still receive and handle it.

### Orphaned Process Groups

When a process group's leader exits or is terminated, and any remaining members have stopped (received `SIGSTOP`), the group becomes orphaned. The kernel sends `SIGHUP` followed by `SIGCONT` to every stopped process in an orphaned process group. This is because the session leader that could resume them (by sending `SIGCONT` from the terminal) is gone, and leaving them stopped forever would be a resource leak. The `SIGHUP` gives them a chance to clean up, and the `SIGCONT` ensures they are in a runnable state when the `SIGHUP` handler (or the default termination action) executes. This mechanism is why terminal disconnection generates `SIGHUP` — the session leader dies, the process group becomes orphaned, and the kernel sends `SIGHUP` to wake everyone up.

---

## 3. High-Performance Optimization & Failure Modes

### Signal Coalescing and the `EINTR` Problem

The single most common signal-related bug in production C code is mishandling `EINTR`. When a signal handler interrupts a blocking system call and `SA_RESTART` is not set (or the call is not restartable), the syscall returns `-1` with `errno == EINTR`. Code that does not check for this condition will treat a perfectly normal signal interruption as a fatal error. The correct pattern is a retry loop:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>

static ssize_t safe_read(int fd, void *buf, size_t len)
{
    ssize_t n;
    do {
        n = read(fd, buf, len);
    } while (n == -1 && errno == EINTR);
    return n;
}

static ssize_t safe_write(int fd, const void *buf, size_t len)
{
    const char *p = buf;
    size_t total = 0;
    while (total < len) {
        ssize_t n = write(fd, p + total, len - total);
        if (n == -1) {
            if (errno == EINTR)
                continue;
            return -1;
        }
        total += n;
    }
    return total;
}
```

The `SA_RESTART` flag eliminates the need for these loops for restartable calls, but relying on it blindly is a portability hazard. On Linux, `epoll_wait`, `poll`, `select`, `sleep`, `usleep`, `nanosleep`, `recvfrom` on certain socket types, and `flock` are never restarted regardless of `SA_RESTART`. Always write `EINTR`-safe wrappers for any blocking call that could be interrupted by a signal.

### Signal Storms and Queue Exhaustion

Real-time signals can be generated faster than they are consumed. If a sender `sigqueue`s signals in a tight loop while the receiver is blocked (or slow), the pending queue fills up. The kernel's limit is `RLIMIT_SIGPENDING`, defaulting to the `ulimit` soft limit. When the queue is full, `sigqueue` returns `EAGAIN`, and the sender must back off. A well-designed real-time signal IPC channel must handle this backpressure. One pattern is to use a shared-memory flag or a pipe write as an acknowledgment: the receiver writes one byte after draining N signals, and the sender waits for that byte before sending more.

A subtle failure mode is *signal coalescing of standard signals under load*. If a process generates 100 `SIGCHLD` signals while `SIGCHLD` is blocked (say, during a `sigprocmask`-protected critical section), the kernel records a single pending bit. On unblock, the handler fires once. If the handler reaps one child with `waitpid`, it misses the other 99. The correct pattern for `SIGCHLD` is to reap in a loop inside the handler:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/wait.h>
#include <string.h>
#include <errno.h>

static volatile sig_atomic_t children_reaped = 0;

static void sigchld_handler(int signo)
{
    (void)signo;
    int saved_errno = errno;
    pid_t pid;
    int status;

    /* Reap ALL available children, not just one.
     * WNOHANG returns 0 when no more children are ready. */
    while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
        children_reaped++;
        /* In production: log or record the child's exit status */
    }

    /* EINTR-safe: always restore errno so the interrupted
     * code does not see a corrupted errno from waitpid. */
    errno = saved_errno;
}

int main(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = sigchld_handler;
    sa.sa_flags = SA_RESTART | SA_NOCLDSTOP;
    sigemptyset(&sa.sa_mask);

    if (sigaction(SIGCHLD, &sa, NULL) == -1) {
        perror("sigaction(SIGCHLD)");
        return 1;
    }

    /* Fork 10 children that exit immediately */
    for (int i = 0; i < 10; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            _exit(42 + i);
        }
    }

    /* Block SIGCHLD briefly so signals accumulate and coalesce */
    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGCHLD);
    sigprocmask(SIG_BLOCK, &mask, NULL);

    sleep(1);

    /* Unblock: handler fires once but reaps all 10 */
    sigprocmask(SIG_UNBLOCK, &mask, NULL);

    sleep(1); /* let handler run */

    printf("Reaped %d children (sent 10, coalesced into fewer handler invocations)\n",
           children_reaped);
    return 0;
}
```

The `WNOHANG` flag is essential: without it, `waitpid` would block inside the signal handler if there were no more children to reap, which would deadlock the process. The `while (waitpid(...) > 0)` loop drains the entire zombie queue in a single handler invocation, compensating for the coalescing of standard signals. The `saved_errno` pattern is a non-negotiable invariant of signal handlers: the handler must never corrupt the `errno` of the interrupted code path, because the interrupted code may be checking `errno` after a failed system call.

### Thread-Directed Signals and `tgkill`

In a multithreaded process, signals have per-process and per-thread dimensions. A signal generated via `kill(pid, signo)` targets the process as a whole. The kernel picks a thread to deliver it to — specifically, any thread that does not have the signal blocked. If all threads have it blocked, it remains pending on the process's `shared_pending` list. A signal generated via `tgkill(tgid, tid, signo)` targets a specific thread and is placed on that thread's private pending list. This is the mechanism behind `pthread_kill(pthread_t, signo)`.

The interaction between threads and signals is one of the most error-prone areas in systems programming. The rules are: signal dispositions (handlers) are per-process — all threads share the same set of handlers. The blocked mask is per-thread — each thread has its own mask. Signal handlers run on the thread that receives the signal, in that thread's context, using that thread's stack. A common pattern in thread pools is to block all asynchronous signals in all threads and have a dedicated signal-handling thread that uses `sigwaitinfo` or `signalfd` to process them synchronously:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>
#include <errno.h>

static void *signal_thread(void *arg)
{
    sigset_t *mask = (sigset_t *)arg;
    int signo;
    siginfo_t info;

    for (;;) {
        /* sigwaitinfo blocks until a signal in mask is pending,
         * then returns the siginfo without invoking a handler.
         * The signal MUST be blocked via sigprocmask/pthread_sigmask
         * for sigwaitinfo to work. */
        signo = sigwaitinfo(mask, &info);
        if (signo == -1) {
            if (errno == EINTR)
                continue;
            perror("sigwaitinfo");
            break;
        }

        printf("Signal thread: signo=%d, si_pid=%d, si_uid=%d, si_code=%d\n",
               signo, info.si_pid, info.si_uid, info.si_code);
        fflush(stdout);

        if (signo == SIGTERM || signo == SIGINT) {
            printf("Signal thread: shutdown signal received, exiting\n");
            fflush(stdout);
            break;
        }
    }

    return NULL;
}

static void *worker_thread(void *arg)
{
    long id = (long)arg;
    printf("Worker %ld: PID=%d, TID=%lu\n", id, getpid(), pthread_self());
    fflush(stdout);
    while (1) {
        /* Workers never see signals because they are blocked.
         * They just do work and periodically check a shutdown flag. */
        sleep(1);
    }
    return NULL;
}

int main(void)
{
    sigset_t mask;
    pthread_t sig_tid, workers[4];

    /* Block these signals process-wide. Because all subsequently
     * created threads inherit this mask, workers are also protected. */
    sigemptyset(&mask);
    sigaddset(&mask, SIGINT);
    sigaddset(&mask, SIGTERM);
    sigaddset(&mask, SIGUSR1);

    if (pthread_sigmask(SIG_BLOCK, &mask, NULL) != 0) {
        perror("pthread_sigmask");
        return 1;
    }

    /* Start the dedicated signal-handling thread */
    if (pthread_create(&sig_tid, NULL, signal_thread, &mask) != 0) {
        perror("pthread_create signal");
        return 1;
    }

    /* Start worker threads - they inherit the blocked mask */
    for (long i = 0; i < 4; i++) {
        if (pthread_create(&workers[i], NULL, worker_thread, (void *)i) != 0) {
            perror("pthread_create worker");
            return 1;
        }
    }

    /* Join the signal thread (exits on SIGTERM/SIGINT) */
    pthread_join(sig_tid, NULL);

    printf("Main: signal thread exited, canceling workers\n");

    for (int i = 0; i < 4; i++) {
        pthread_cancel(workers[i]);
        pthread_join(workers[i], NULL);
    }

    printf("Main: all threads joined, exiting\n");
    return 0;
}
```

This architecture — block all signals in the main thread before creating any other thread, then have one thread call `sigwaitinfo` or read from a `signalfd` — is the production-grade pattern for multithreaded daemons. It eliminates all async-signal-safety concerns because no handler ever fires asynchronously. The signal arrives, sits pending on the process (because all threads have it blocked), and the dedicated signal thread picks it up synchronously from `sigwaitinfo`. The worker threads are completely insulated from signal delivery.

The `sigwaitinfo` function returns the `siginfo_t` for the dequeued signal, giving the same information that a `SA_SIGINFO` handler would receive. For real-time signals, `sigwaitinfo` dequeues one queued instance per call; if five `SIGRTMIN+1` signals are pending, it must be called five times to drain them all. The `sigtimedwait` variant adds a timeout, which is useful for poll-style architectures that want to periodically check for signals while also doing other work.

### Race Conditions in Signal Handler Registration

A subtle failure mode occurs when a signal arrives between `fork` and `sigaction` in a child process. The child inherits the parent's dispositions, but if the child immediately changes them, there is a window where the old disposition is in effect. For signals like `SIGCHLD`, this is usually harmless (the default action is ignore). But for signals where the default is terminate (`SIGTERM`, `SIGINT`, `SIGHUP`), a signal arriving in this window will kill the child before it can install its handler.

The fix is to block the signal in the parent before forking, so the child inherits the block, then unblock it after installing the handler:

```c
sigset_t mask, oldmask;
sigemptyset(&mask);
sigaddset(&mask, SIGTERM);

sigprocmask(SIG_BLOCK, &mask, &oldmask);

pid_t child = fork();
if (child == 0) {
    struct sigaction sa;
    sa.sa_handler = child_handler;
    sa.sa_flags = SA_RESTART;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM, &sa, NULL);

    /* Now safe to unblock: handler is installed */
    sigprocmask(SIG_UNBLOCK, &mask, NULL);

    /* child main loop */
    _exit(0);
}

/* Parent restores its own mask */
sigprocmask(SIG_SETMASK, &oldmask, NULL);
```

This pattern is mandatory in any program where the child's signal disposition differs from the parent's and the signal could arrive in the fork window. Without it, the child can be killed by a stray `SIGTERM` before it ever gets to its first instruction in `main`-equivalent code.

### The `SA_NOCLDWAIT` and `SIGCHLD` Interaction

Setting `SA_NOCLDWAIT` on a `SIGCHLD` `sigaction` tells the kernel not to create zombies. When a child exits, the kernel reaps it immediately without requiring a `waitpid` call. This is convenient for fire-and-forget child processes, but it interacts dangerously with a handler that calls `waitpid`: `waitpid` will return `-1` with `errno == ECHILD` because the kernel already reaped the child. If the handler uses `waitpid` to determine the child's exit status, `SA_NOCLDWAIT` makes that impossible. The two mechanisms are mutually exclusive in practice: either use `SA_NOCLDWAIT` (kernel reaps, no exit status available) or use `waitpid` in a `SIGCHLD` handler (you get exit status, but you must call `waitpid`). Setting `SIGCHLD` to `SIG_IGN` has the same effect as `SA_NOCLDWAIT` on Linux: the kernel auto-reaps children and does not generate zombies.
