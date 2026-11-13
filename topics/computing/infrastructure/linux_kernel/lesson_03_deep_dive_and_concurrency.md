Here is the fully corrected, publication-grade, raw Markdown:

# Lesson 3: Advanced Internal Mechanics, Concurrency & Recovery

## 1. Concurrency Control, Lockless Queues & Conflict Resolution

Concurrency is a hierarchical problem at the kernel level, with different mechanisms suited to different timescales and contention patterns. The coarsest tool is the mutex, a sleepable lock that suspends the thread while held. Mutexes are suitable for long-critical sections, such as disk I/O or complex data structure modifications, where the holder may block. The finer tool is the spinlock, which busy-waits while held. Spinlocks must be held for very short durations because a thread holding a spinlock cannot sleep; if it did, the spinning thread would spin forever. The kernel enforces this via `spin_lock_irqsave`, which disables interrupts on the local CPU, and the `_irq` suffix in the `_irq` lock family.

For read-heavy workloads, the read-write semaphore (`rwlock`) allows multiple readers or one writer. However, the modern kernel has largely replaced the old `rwlock` with `rwlock_bh` (blocking-helper) and `seqlock`, which are better suited for short critical sections. The `seqlock` is particularly elegant: readers do not take a lock but instead check a sequence counter before and after reading, and if it changed, they retry. This is ideal for data that is rarely updated but frequently read.

The kernel uses lockless data structures and RCU (read-copy-update) for the highest performance. RCU allows readers to access data without any locks at all, while writers create a new copy and swap the pointer atomically. The old value is freed only after all pre-existing readers have finished, which the kernel tracks via grace periods. This is the foundation of many of the kernel's fastest paths. Lockless queues use atomic compare-and-swap (CAS) operations to enqueue and dequeue without any locks. The `llist` and `xchmp` primitives are the building blocks here.

The Completely Fair Scheduler (CFS) also relies on these primitives. Each task has a `vruntime` (virtual runtime), which is the amount of time it has spent on the CPU, normalized by its priority. The scheduler always runs the task with the lowest `vruntime`, and the red-black tree used to store tasks is modified with lockless primitives where possible.

The OOM killer uses a scoring function to decide which process to terminate when memory is low:

```math
OOM\_score = s_{10} \cdot \frac{100 - \text{runtime}}{\text{total\_runtime}} \cdot \frac{100 - \text{priority}}{100} \cdot \frac{100 - \text{swappiness}}{100} \cdot \frac{100 - \text{cgroup\_memory\_limit}}{100}
```

The OOM killer also has a `cgroup_memory_limit` term, which gives a bonus to processes in cgroups with low memory limits.

## 2. State Reconciliation & Recovery State Machines

The kernel maintains internal state machines for every subsystem, and each must be designed to recover gracefully from failure. The memory management subsystem, for example, has a complex state machine that tracks page states (anonymous, file-backed, dirty, writeback, anonymous-dirty, etc.) and a set of mechanisms for reclaiming memory under pressure. When the system runs low on memory, the kswapd daemon wakes up and begins evicting pages. The OOM killer is the last line of defense, and it only activates when the kernel can no longer satisfy memory requests.

The filesystem layer also has a recovery state machine. Ext4 and XFS use journaling to record metadata changes before they are applied, so that a crash can be recovered by replaying the journal. The journal is a circular buffer, and each transaction is committed atomically. The kernel also maintains a `dirty_pages` list, and the writeback mechanism periodically flushes dirty pages to disk. If a write fails, the kernel marks the page as writeback-failed and retries later.

The network stack has its own recovery mechanisms. TCP retransmits lost segments, and the kernel maintains a retransmission timer for each outstanding segment. The TCP congestion control algorithm (CUBIC is the default) adjusts the congestion window based on packet loss. The kernel also has a `tcp_drop` handler that discards malformed packets and sends an ICMP unreachable message.

## 3. Resource Accounting, Eviction & Cleanup Engines

The cgroup subsystem provides fine-grained resource accounting and control. Each cgroup has a memory controller that tracks memory usage and enforces limits. When a cgroup exceeds its memory limit, the kernel can either throttle the cgroup or invoke the OOM killer. The OOM killer's `cgroup_memory_limit` term gives a bonus to processes in cgroups with low memory limits, which means that processes in cgroups with small limits are more likely to be killed.

The kernel also has a `page_cache` that caches file data in memory. The page cache is managed by a LRU list, and pages that are not accessed frequently are evicted first. The kernel also has a `slab` cache for small, frequently allocated objects, and it uses a buddy allocator for larger contiguous memory regions.

The kernel also has a `dentry` cache and an `inode` cache, which cache directory and file metadata. These caches are also managed by LRU lists and can be shrunk under memory pressure.

## 4. Production Failure Domains & Byzantine Edge Cases

The kernel has several failure modes, ranging from recoverable errors to fatal panics. A kernel panic is a non-recoverable error that halts the system. Panics are triggered by several conditions, including a double fault, a page fault in kernel mode with no valid exception handler, and an assertion failure. The kernel also has an `oops` mechanism, which is a less severe form of failure that prints a stack trace and allows the system to continue running.

The kernel also has a `BUG()` macro that asserts a condition and prints a stack trace. The `BUG_ON()` macro is used when the condition is expected to be true in normal operation. The `BUG_or_panic()` macro is used when the condition is so severe that the system should panic.

The kernel also has a `WARN_ON()` macro, which prints a stack trace but does not halt the system. `WARN_ON_ONCE()` is used when the condition is expected to occur only once.

The kernel also has a `panic_on_oom()` flag, which causes the system to panic instead of invoking the OOM killer when memory is low. This is useful in embedded systems where the OOM killer is not desired.

The kernel also has a `panic_on_oom_critical()` flag, which causes the system to panic when memory is critically low. This is used in systems where a graceful shutdown is preferred over the OOM killer.

The kernel also has a `panic_on_oom_deadlock()` flag, which causes the system to panic when a deadlock is detected during OOM handling. This is used to prevent the system from hanging indefinitely.

The kernel also has a `panic_on_oom_oom_kill_failed()` flag, which causes the system to panic when the OOM killer fails to kill any process. This is used when the OOM killer is the only way to free memory.
