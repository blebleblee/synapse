# Lesson 2: Real-Time Systems Theory

## 1. First-Principles Intuition & Invariants

Real-time systems engineering stands at a fundamental crossroads that separates embedded systems from general-purpose computing. The core distinction is not speed—a real-time system need not be fast—but rather *predictability*. A real-time system must guarantee that every computational task completes within a known, bounded time window called its deadline. Missing a deadline constitutes a system failure, regardless of whether the computation itself was arithmetically correct. This inversion of priorities—correctness subordinated to timeliness—reshapes every architectural decision from task scheduling to memory management to interrupt handling.

Consider a simple motivating example: an antilock braking system (ABS) controller in an automotive platform. When a wheel speed sensor detects deceleration exceeding a threshold, the ABS control algorithm must execute within microseconds to modulate hydraulic pressure before brake lockup occurs. If this computation runs correctly but completes 50 milliseconds late, the vehicle has already skidded into the oncoming lane. The arithmetic was flawless; the system failed catastrophically. Conversely, a batch financial reporting system may tolerate hour-long delays without penalty, provided all transactions eventually settle correctly. Speed and correctness alone are insufficient design criteria for real-time embedded systems.

This lesson establishes the mathematical and operational foundations for designing systems that meet hard deadlines through formal schedulability analysis, priority scheme selection, and latency verification. We will ground these concepts in the execution model of a real-time kernel, the anatomy of context switching, and the concrete mechanisms by which interrupt handlers, task queues, and timing utilities implement deadline guarantees.

### The Execution Model and Task Abstraction

In real-time systems terminology, a *task* is an independent unit of execution with a defined period, deadline, and worst-case execution time (WCET). A periodic task repeats at fixed intervals; an aperiodic task triggers sporadically in response to external events. Each task possesses a *priority*, which determines its right to execute relative to other ready tasks. When a higher-priority task becomes ready, it preempts any lower-priority task currently running—a mechanism called *preemptive scheduling*.

The kernel maintains a *ready queue* data structure ordered by priority. When a task blocks (waiting for I/O, a semaphore, or a timer), it moves from the ready queue to an appropriate wait queue. When the blocking condition clears, the kernel moves the task back to ready. The *scheduler* implements a decision algorithm: whenever the processor becomes idle or a higher-priority task readies, the scheduler selects the highest-priority ready task and loads its context onto the CPU. This context switch—storing the suspended task's registers, instruction pointer, and memory management state, then restoring the resumed task's state—introduces a fixed latency that must be accounted for in deadline calculations.

The term *latency* in real-time systems refers to the time elapsed from when an external event occurs (or a task becomes ready) until that event has been fully serviced. Latency comprises multiple components. *Release latency* is the delay from event occurrence to task readiness; *scheduling latency* is the delay from task readiness to when the scheduler actually assigns CPU time; *execution latency* is the time the task runs before completing or blocking; and *interrupt latency* is the delay from interrupt assertion until the kernel's interrupt handler begins execution. For hard real-time systems, the sum of all latency contributors must never exceed the deadline.

### Worst-Case Execution Time and Timing Analysis

Before we can mathematically prove that a task set meets all deadlines, we must know the *worst-case execution time* (WCET) of each task. WCET is not merely the longest observed execution time of a task on test hardware; it is a rigorously derived upper bound that accounts for all possible execution paths, cache behavior, pipeline stalls, and branch prediction outcomes that could extend execution duration.

Computing WCET rigorously requires either static analysis tools that trace all possible instruction sequences through the code, or careful benchmarking on representative hardware followed by conservative margins. Static analysis tools examine the compiled object code, identify loops and branches, and construct a graph of all feasible execution paths. They propagate timing estimates through the graph, accounting for memory access penalties: a cache hit on a modern ARM Cortex-M4 microcontroller incurs roughly 1 cycle latency, while a main memory access may consume 10–20 cycles. The tool then selects the longest path through the graph as the WCET bound.

In practice, many embedded systems engineers resort to a combination of measurement and analysis. You instrument the task with timing probes—reading a high-resolution hardware timer at entry and exit—then execute the task under conditions designed to trigger worst-case behavior: forcing cache misses by accessing disjoint memory regions between iterations, ensuring branches take the longest paths, and loading the system with other tasks to maximize preemption. The observed execution time plus a conservative safety margin becomes your WCET estimate. This approach is less rigorous than formal static analysis but remains practical on resource-constrained platforms where sophisticated timing analysis tools are unavailable.

### Priority Assignment and Deadline Monotonicity

Once we have characterized each task with a period, deadline, and WCET, we must assign priorities to determine scheduling order. Different priority assignment schemes yield different guarantees about schedulability. The two most important schemes are *rate monotonic* (RM) and *deadline monotonic* (DM).

Rate monotonic priority assignment decrees that tasks with shorter periods receive higher priority. A task with a 10 millisecond period is assigned higher priority than a task with a 50 millisecond period. This scheme is optimal for periodic tasks where the relative deadline (the deadline measured from task release) equals the task period. The intuition is clear: tasks that must complete frequently need preferential access to the CPU to meet their tight deadlines.

Deadline monotonic priority assignment assigns higher priority to tasks with shorter relative deadlines, measured from task release to deadline. If Task A has a period of 100 milliseconds but a relative deadline of 30 milliseconds (it must complete 30 ms after release, though it releases again 100 ms later), while Task B has a period of 50 milliseconds and a relative deadline of 50 milliseconds, then Task A receives higher priority under DM. DM is optimal for task sets where relative deadlines may differ from periods—a common scenario in real-time systems where a task may have periodic release but an earlier completion requirement.

The choice between RM and DM affects not only schedulability analysis but also the implementation complexity of the priority queue. RM requires sorting tasks by period at design time; DM requires sorting by deadline, which may be hardcoded or computed dynamically at runtime. Most real-time kernels support fixed-priority scheduling, where each task's priority is set once and does not change; dynamic priority assignment (where priority varies over time) introduces complexity and is rarely used in hard real-time systems.

### Preemption, Blocking, and Priority Inversion

In a preemptive scheduling regime, the scheduler immediately suspends a lower-priority task when a higher-priority task becomes ready. This ensures that higher-priority tasks experience minimal additional delay. However, preemption introduces a subtle danger called *priority inversion*: a low-priority task acquires a shared resource (a semaphore, a lock, or simply exclusive access to a memory buffer), then a high-priority task attempts to acquire the same resource and blocks waiting for the low-priority task to release it. Now the high-priority task is delayed by a low-priority task—precisely the opposite of the priority scheme's intent.

If an intermediate-priority task becomes ready while the low-priority task still holds the resource, the scheduler runs the intermediate-priority task, further delaying the low-priority task's progress and thus extending the high-priority task's wait. This phenomenon, demonstrated vividly during the 1997 Mars Pathfinder mission when a real-time scheduling bug caused system resets during landing, motivates the *priority inheritance protocol*: when a lower-priority task holds a resource for which a higher-priority task is waiting, the lower-priority task's priority is temporarily elevated to match the higher-priority task's priority. Once the resource is released, priority reverts. This ensures that low-priority tasks holding contested resources execute at elevated priority, preventing intermediate-priority tasks from interfering.

An alternative mechanism, the *priority ceiling protocol*, assigns each resource a priority equal to the highest priority task that might access it. A task acquires a resource only if its current priority is at least as high as the resource's ceiling. If not, the task's priority is elevated to the ceiling before acquisition. This prevents priority inversion entirely by ensuring no higher-priority task can block on a resource held by a lower-priority task.

## 2. Core Architecture & Mechanics

### Schedulability Analysis: Rate Monotonic Theory

Rate monotonic (RM) scheduling analysis provides a sufficient (but not necessary) condition for guaranteeing that a periodic task set meets all deadlines under preemptive priority scheduling. The fundamental RM theorem states: a periodic task set with relative deadlines equal to periods is schedulable under RM priority assignment if and only if the total CPU utilization does not exceed a bound that depends on the number of tasks.

For *n* periodic tasks with periods *T₁, T₂, …, Tₙ* and execution times *C₁, C₂, …, Cₙ*, the CPU utilization is defined as:

$$U = \sum_{i=1}^{n} \frac{C_i}{T_i}$$

The RM utilization bound is:

$$U_{RM} = n \cdot (2^{1/n} - 1)$$

For *n* = 1 (a single task), this bound is exactly 1.0, meaning a task can use the entire CPU and still meet its deadline. For *n* = 2, the bound is approximately 0.828, meaning two tasks can collectively use at most 82.8% of CPU capacity. As *n* increases, the bound approaches *ln(2) ≈ 0.693*, meaning an arbitrarily large periodic task set requires collective CPU utilization below 69.3% to guarantee schedulability under RM.

The theorem provides a simple, closed-form test: compute utilization; if it falls below the bound, schedulability is guaranteed. However, this test is sufficient but not necessary—a task set may be schedulable even if utilization exceeds the bound. To determine schedulability with higher confidence, we employ response time analysis.

Response time analysis computes the maximum time a task may spend from release until completion, accounting for preemption by higher-priority tasks. Consider a task *i* with execution time *Cᵢ* and period *Tᵢ*. During the time interval from task *i*'s release until its completion, every higher-priority task *j* (with *j* < *i* under RM priority ordering, meaning *Tⱼ* < *Tᵢ*) may execute multiple times. The number of times task *j* executes during task *i*'s response time *Rᵢ* is *⌈Rᵢ / Tⱼ⌉* (ceiling function). Each execution of task *j* consumes *Cⱼ* units of time.

The response time *Rᵢ* satisfies the equation:

$$R_i = C_i + \sum_{j=1}^{i-1} \left\lceil \frac{R_i}{T_j} \right\rceil \cdot C_j$$

This equation is computed iteratively: start with *Rᵢ⁽⁰⁾ = Cᵢ*, then compute successive approximations:

$$R_i^{(k+1)} = C_i + \sum_{j=1}^{i-1} \left\lceil \frac{R_i^{(k)}}{T_j} \right\rceil \cdot C_j$$

Continue until convergence (*Rᵢ⁽ᵏ⁺¹⁾ = Rᵢ⁽ᵏ⁾*) or until *Rᵢ⁽ᵏ⁾* > *Dᵢ* (the task's deadline), at which point the task set is not schedulable under RM.

Let us work through a concrete example. Suppose we have three periodic tasks with the following parameters:

| Task | Period (ms) | Execution Time (ms) | Deadline (ms) |
|------|-------------|---------------------|---------------|
| τ₁   | 10          | 2                   | 10            |
| τ₂   | 20          | 5                   | 20            |
| τ₃   | 50          | 8                   | 50            |

Utilization is *U = 2/10 + 5/20 + 8/50 = 0.2 + 0.25 + 0.16 = 0.61*, which is well below the RM bound of *3 × (2^(1/3) - 1) ≈ 0.78*, so we expect schedulability.

Computing response times, starting with task τ₁:

*R₁⁽⁰⁾ = C₁ = 2*

*R₁⁽¹⁾ = C₁ + ⌈R₁⁽⁰⁾ / T₁⌉ × 0 = 2* (no higher-priority tasks)

So *R₁ = 2 ms*, which is less than deadline *D₁ = 10 ms*. Task τ₁ is schedulable.

For task τ₂:

*R₂⁽⁰⁾ = C₂ = 5*

*R₂⁽¹⁾ = C₂ + ⌈R₂⁽⁰⁾ / T₁⌉ × C₁ = 5 + ⌈5 / 10⌉ × 2 = 5 + 1 × 2 = 7*

*R₂⁽²⁾ = 5 + ⌈7 / 10⌉ × 2 = 5 + 1 × 2 = 7*

Converged at *R₂ = 7 ms* < *D₂ = 20 ms*. Task τ₂ is schedulable.

For task τ₃:

*R₃⁽⁰⁾ = C₃ = 8*

*R₃⁽¹⁾ = 8 + ⌈8 / 10⌉ × 2 + ⌈8 / 20⌉ × 5 = 8 + 1 × 2 + 1 × 5 = 15*

*R₃⁽²⁾ = 8 + ⌈15 / 10⌉ × 2 + ⌈15 / 20⌉ × 5 = 8 + 2 × 2 + 1 × 5 = 17*

*R₃⁽³⁾ = 8 + ⌈17 / 10⌉ × 2 + ⌈17 / 20⌉ × 5 = 8 + 2 × 2 + 1 × 5 = 17*

Converged at *R₃ = 17 ms* < *D₃ = 50 ms*. Task τ₃ is schedulable.

All tasks meet their deadlines under RM priority assignment; the task set is schedulable.

### Deadline Monotonic Analysis

When relative deadlines differ from periods, deadline monotonic scheduling and analysis become necessary. DM analysis is structurally identical to RM analysis, except tasks are ordered by deadline rather than period. The response time equation remains:

$$R_i = C_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i}{T_j} \right\rceil \cdot C_j$$

where *hp(i)* denotes the set of higher-priority tasks (those with shorter deadlines than task *i*).

Consider modifying our previous example: suppose task τ₂ has an implicit deadline of 15 ms instead of 20 ms (it must complete within 15 milliseconds of release, but releases again every 20 milliseconds). Now the deadline ordering is: τ₂ (15 ms deadline) > τ₁ (10 ms deadline) > τ₃ (50 ms deadline). Task τ₂ receives highest priority under DM.

For task τ₂ (highest priority):

*R₂⁽⁰⁾ = C₂ = 5*

No higher-priority tasks, so *R₂ = 5 ms* < *D₂ = 15 ms*. Schedulable.

For task τ₁ (second priority):

*R₁⁽⁰⁾ = C₁ = 2*

*R₁⁽¹⁾ = 2 + ⌈2 / 20⌉ × 5 = 2 + 1 × 5 = 7*

*R₁⁽²⁾ = 2 + ⌈7 / 20⌉ × 5 = 2 + 1 × 5 = 7*

Converged at *R₁ = 7 ms* < *D₁ = 10 ms*. Schedulable.

For task τ₃ (lowest priority):

*R₃⁽⁰⁾ = 8*

*R₃⁽¹⁾ = 8 + ⌈8 / 20⌉ × 5 + ⌈8 / 10⌉ × 2 = 8 + 1 × 5 + 1 × 2 = 15*

*R₃⁽²⁾ = 8 + ⌈15 / 20⌉ × 5 + ⌈15 / 10⌉ × 2 = 8 + 1 × 5 + 2 × 2 = 17*

*R₃⁽³⁾ = 8 + ⌈17 / 20⌉ × 5 + ⌈17 / 10⌉ × 2 = 8 + 1 × 5 + 2 × 2 = 17*

Converged at *R₃ = 17 ms* < *D₃ = 50 ms*. Schedulable.

By reordering according to deadline rather than period, we maintain schedulability.

### Aperiodic Task Handling and Sporadic Servers

Real-time systems rarely consist solely of periodic tasks. Interrupt service routines (ISRs), event-driven computations, and user interactions produce aperiodic tasks with unpredictable arrival patterns. An aperiodic task possesses an execution time *Cₐ*, a deadline *Dₐ*, and an arrival pattern characterized by minimum interarrival time (for sporadic tasks) or no constraint (for truly aperiodic tasks).

One approach to handling aperiodic tasks is to assign them a fixed priority lower than all periodic tasks. Aperiodic tasks execute only when no periodic tasks are ready, guaranteeing that periodic deadline guarantees remain intact. However, this approach may miss aperiodic deadlines.

A more sophisticated mechanism is the *sporadic server*, which reserves CPU bandwidth for aperiodic tasks while preserving periodic deadline guarantees. A sporadic server is a synthetic periodic task with period *Tₛ* and execution budget *Cₛ*. At each period, the server receives *Cₛ* units of execution time. If aperiodic tasks arrive and the server's budget is nonzero, the server executes aperiodic work. If the server's budget is exhausted, aperiodic tasks must wait until the server's next period.

The sporadic server's period and budget are chosen such that the server can be treated as an ordinary periodic task in schedulability analysis. If we compute that a periodic task set including the sporadic server (with period *Tₛ* and execution time *Cₛ*) is schedulable, then we are guaranteed that the periodic tasks meet their deadlines even when aperiodic work arrives.

For example, suppose we have periodic tasks with total utilization *U = 0.4*, and we wish to handle aperiodic tasks with maximum execution requirement *Cₐ = 5 ms* arriving at minimum interval *Tₐ = 50 ms*. We create a sporadic server with period *Tₛ = 50 ms* and budget *Cₛ = 5 ms*, contributing utilization *5/50 = 0.1*. Total utilization becomes *0.4 + 0.1 = 0.5*. If the combined task set (periodic plus server) passes schedulability analysis, aperiodic tasks are guaranteed to complete within deadline *Tₐ = 50 ms* and periodic tasks remain deadline-safe.

### Jitter Control and Interrupt Handling

*Jitter* refers to variability in the timing of task execution. Release jitter is the variability in the time interval between when a task becomes ready and when it actually begins execution. Completion jitter is the variability in the time between task completion and when the result is available to dependent tasks. In hard real-time systems, jitter must be controlled and accounted for in deadline calculations.

Release jitter arises from several sources. Interrupt latency—the delay from interrupt assertion until the interrupt handler executes—contributes directly to the release jitter of tasks activated by interrupts. If an external sensor triggers an interrupt at time *t*, and the interrupt handler does not execute until time *t + Δ*, the activated task's release jitter is at least *Δ*. Additionally, if the processor is executing a lower-priority task when the interrupt arrives, the preemption latency (time spent finishing the current instruction or atomic section) adds further delay.

Modern microcontrollers minimize interrupt latency through several architectural features. The ARM Cortex-M series implements *zero-latency interrupt* capability: certain interrupt levels (configurable through the NVIC Control Register) can interrupt even interrupt handlers running at lower priority levels, bypassing the scheduler entirely. This ensures that truly time-critical interrupts complete with minimal added latency. The RTOS then handles any state management required by the interrupted task.

To account for jitter in deadline calculations, we modify the response time equations to include release jitter as an additional component. If task *i* experiences release jitter *Jᵢ*, its response time becomes:

$$R_i = J_i + C_i + \sum_{j \in \text{hp}(i)} \left\lceil \frac{R_i + J_i}{T_j} \right\rceil \cdot C_j$$

The jitter term *Jᵢ* shifts the task's effective release time, and the ceiling function's argument includes jitter to account for the fact that higher-priority tasks may arrive *Jⱼ* units earlier than expected, demanding more preemptions within the same wall-clock interval.

In embedded systems, jitter control often requires careful interrupt handler design. Interrupt handlers should be as brief as possible, performing only immediate response actions (toggling a digital output, reading a sensor register) before deferring longer computations to a task. This deferred-work pattern, implemented through tasklets or deferred procedure calls, minimizes the duration that interrupts are disabled (protecting shared state), reducing jitter for other tasks.

### Timing Verification and Hardware Instrumentation

Once schedulability is analytically proven, verification requires demonstrating that the actual embedded system honors the timing guarantees. This demands hardware instrumentation: high-resolution timing measurements, event logging, and statistical analysis.

Most modern microcontrollers include a *cycle counter* register (the CYCCNT register in ARM Cortex-M processors) that increments once per processor clock cycle, providing nanosecond-resolution timing on GHz-frequency processors. Kernel-level timing utilities typically read this counter at task entry and exit, computing actual execution times. Over a long test run (minutes to hours), we collect samples of actual execution times for each task, then compare the observed maximum against the WCET estimate.

The following pseudo-code illustrates task instrumentation in an RTOS context:

```c
// Define timing statistics structure
typedef struct {
    uint32_t min_exec_time;
    uint32_t max_exec_time;
    uint32_t total_samples;
    uint64_t sum_exec_time;
} task_timing_stats_t;

// Hook called at task entry
void task_entry_hook(task_t *task) {
    task->entry_time = read_cycle_counter();
}

// Hook called at task exit
void task_exit_hook(task_t *task) {
    uint32_t exit_time = read_cycle_counter();
    uint32_t exec_time = exit_time - task->entry_time;
    
    task_timing_stats_t *stats = &task->timing_stats;
    if (exec_time < stats->min_exec_time) {
        stats->min_exec_time = exec_time;
    }
    if (exec_time > stats->max_exec_time) {
        stats->max_exec_time = exec_time;
    }
    stats->sum_exec_time += exec_time;
    stats->total_samples++;
}
```

Beyond execution time, we must verify deadline compliance. Many RTOS implementations provide *deadline miss* detection: if a task does not complete by its deadline, a notification is logged or a callback triggered. A production embedded system should never miss a deadline; deadline miss events during testing indicate either insufficient CPU capacity (utilization too high) or an incorrect WCET estimate.

For systems with external deadlines—where missed deadlines cause physical consequences (brakes failing to activate, motors not stopping)—hardware watchdogs provide a safety net. A watchdog timer is a dedicated hardware circuit that resets the processor if not reset periodically. The kernel resets the watchdog at each tick; if the kernel is deadlocked or executing an infinite loop, the watchdog fires and resets the system. While not a replacement for proper schedulability analysis, watchdogs provide defense-in-depth against catastrophic failures.

## 3. High-Performance Optimization & Failure Modes

### Handling Overload Conditions and Graceful Degradation

Real-time systems must tolerate temporary CPU overload when aperiodic tasks arrive at higher rates than anticipated, or when certain periodic tasks occasionally consume more than their WCET estimates. Graceful degradation strategies prevent system collapse by sacrificing less critical functions to preserve deadlines for higher-criticality tasks.

One mechanism is *overload scheduling*, which dynamically reduces lower-priority task execution to ensure higher-priority tasks meet deadlines. When the kernel detects that utilization will exceed 100% if all tasks execute fully, it *skips* lower-priority task releases or reduces their execution budget. For instance, a diagnostic logging task might be skipped every few cycles when CPU is saturated, whereas the primary control task always executes.

Implementing overload scheduling requires monitoring cumulative utilization at runtime.

The kernel tracks pending releases and their cumulative CPU demand; when the sum of pending execution times plus the remaining time until their deadlines exceeds available CPU capacity, the scheduler invokes an overload policy—typically dropping or deferring the lowest-criticality tasks first. This is formalized in *criticality-aware scheduling*, where tasks are assigned explicit criticality levels (safety-critical, mission-critical, non-essential), and the scheduler guarantees that higher-criticality tasks never miss deadlines even if lower-criticality tasks are starved. In dual-criticality systems, tasks operate with two WCET estimates: a typical-case estimate for normal operation and a conservative worst-case estimate for degraded mode. If a high-criticality task exceeds its normal WCET, the system transitions to high-criticality mode, suspending all low-criticality tasks to ensure sufficient margin for safety-critical functions. Another approach is *adaptive reservation*, where each task is allocated a CPU time budget per period; tasks that consistently underrun their budgets donate unused capacity to a shared slack pool, which overloaded tasks can borrow. This provides statistical multiplexing benefits while maintaining hard guarantees for tasks that never exceed their reservations.

Beyond CPU overload, real-time systems must anticipate failure modes including priority inversion deadlocks (where priority inheritance chains form cycles), interrupt storms (where a malfunctioning device triggers interrupts faster than the ISR can clear them, starving all tasks), and memory exhaustion (particularly in systems without virtual memory or swap). Interrupt storms are mitigated by rate-limiting ISRs—after N interrupts within a time window, the ISR disables that interrupt source and logs a fault, preventing system lockup. Memory exhaustion is addressed through static allocation wherever possible; dynamic allocation, if used, must have deterministic allocators with pre-allocated pools and hard limits per task. Comprehensive fault injection testing—deliberately inducing overload, priority inversions, and resource starvation during development—validates that the system degrades predictably rather than collapsing catastrophically. Observability infrastructure (real-time trace buffers, deadline miss counters, ISR execution histograms) must remain operational even under overload, providing forensic data for post-incident analysis. The hallmark of a mature real-time system is not that it never encounters adverse conditions, but that its behavior under stress is deterministic, bounded, and designed.

## Summary & Verification Matrix

| Invariant / Mechanism | Governing Equation / Condition | Purpose | Diagnostic Criterion |
|----------------------|-------------------------------|---------|---------------------|
| **RM Schedulability** | $\sum_{i=1}^{n} \frac{C_i}{T_i} \leq n(2^{1/n} - 1)$ | Sufficient (but not necessary) guarantee that all periodic tasks meet deadlines under rate-monotonic priority assignment | Utilization sum ≤ bound for task count; exact test via response-time analysis if bound exceeded |
| **EDF Schedulability** | $\sum_{i=1}^{n} \frac{C_i}{T_i} \leq 1$ | Necessary and sufficient condition for earliest-deadline-first scheduling of periodic tasks | Total utilization ≤ 100%; any excess guarantees deadline misses |
| **Priority Inheritance** | Blocked task inherits priority of highest-priority waiter during critical section | Bounds priority inversion duration to at most the length of one critical section per resource | Maximum blocking time $B_i = \max(CS_k)$ for each lower-priority resource $k$ that can block task $i$ |
| **Watchdog Timer** | Hardware counter reset by kernel tick; fires if not reset within timeout interval | Detects kernel deadlock, infinite loops, or catastrophic failures that prevent normal scheduling | Watchdog reset interval must be shorter than shortest acceptable system freeze duration; missed resets trigger system reset |
| **Overload Policy** | When $\sum \frac{C_i^{\text{actual}}}{T_i} > 1$, drop or defer lowest-criticality tasks | Graceful degradation under transient CPU saturation; preserves high-criticality deadlines | Monitor deadline miss counters by criticality level; high-criticality misses indicate insufficient capacity even after shedding load |
| **WCET Validation** | Measured execution time ≤ analytical WCET estimate for all test scenarios | Ensures schedulability analysis assumptions hold in real hardware/software | Path coverage of high-WCET branches; margin between measured max and analytical WCET indicates safety buffer |
