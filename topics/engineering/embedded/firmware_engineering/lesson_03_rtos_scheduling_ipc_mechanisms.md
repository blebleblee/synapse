# Lesson 3: Real-Time Operating Systems, Scheduling Algorithms, Inter-Process Communication

## 1. First-Principles Intuition & Invariants

Real-time operating systems exist to solve a fundamental problem that conventional operating systems deliberately ignore: the guarantee that a computation will complete within a bounded, deterministic time window. When a surgeon's robotic arm must halt within 2 milliseconds of detecting unexpected resistance, when an automotive braking controller must respond to wheel slip within 10 milliseconds, or when a flight control surface actuator must update its position every 5 milliseconds regardless of system load, the traditional notion of "fairness" in scheduling becomes not just irrelevant but actively dangerous. Real-time systems trade the statistical averaging and best-effort resource sharing of general-purpose operating systems for iron-clad temporal guarantees, transforming time itself from a statistical property into a first-class correctness requirement.

The conceptual leap from general-purpose to real-time systems centers on a philosophical inversion: whereas Linux or Windows treat deadlines as advisory hints to be optimized statistically across thousands of tasks, an RTOS treats deadlines as hard contracts whose violation constitutes system failure as severe as a segmentation fault or divide-by-zero exception. This distinction manifests in every architectural decision. A general-purpose scheduler might context-switch to a lower-priority task because it has been starved for CPU time, implementing a fairness policy that prevents indefinite postponement. An RTOS scheduler will deliberately starve low-priority tasks indefinitely if higher-priority work continues arriving, because temporal correctness for critical tasks supersedes fairness. The low-priority background telemetry task that updates a diagnostic display may not execute for minutes or hours if the motor control loop demands continuous attention, and this is not a bug but the intended design.

Real-time guarantees rest on three immutable invariants that permeate every line of RTOS kernel code. First, bounded execution time: every kernel operation—context switches, interrupt service routine prologues and epilogues, semaphore acquisition, message queue operations—must complete within a statically analyzable worst-case execution time (WCET). If a semaphore `take()` operation might traverse an unbounded linked list or trigger a page fault that could stall for milliseconds waiting on NAND flash, the RTOS cannot provide deterministic guarantees. This requirement eliminates entire classes of algorithms: no dynamic memory allocation in critical paths because `malloc()` traverses free lists of unpredictable length, no virtual memory with demand paging because page faults inject unbounded latency, no garbage collection because stop-the-world pauses violate temporal contracts.

Second, priority-driven preemption: at every instant, the highest-priority ready task must be executing unless it voluntarily yields or blocks on a resource. This invariant demands that the scheduler maintain a ready queue data structure permitting O(1) extraction of the highest-priority task, typically implemented as a bitmap indexing an array of per-priority FIFO queues. When an interrupt service routine unblocks a task with priority higher than the currently executing task, the kernel must perform an immediate context switch in the ISR's return path, saving the preempted task's register context to its stack and restoring the higher-priority task's context. The mathematical elegance of priority-driven scheduling lies in its composability: if task A has higher priority than task B, and task B has higher priority than task C, then A will always preempt B, and B will always preempt C, creating a total ordering that permits formal schedulability analysis.

Third, predictable synchronization: when tasks share resources or communicate, the primitives they use must not introduce unbounded priority inversions where a high-priority task waits indefinitely for a lower-priority task to release a shared resource. Classic semaphores fail this requirement catastrophically. Consider three tasks: high-priority H, medium-priority M, and low-priority L. If L acquires a semaphore protecting a shared hardware register, then gets preempted by M which runs for an extended period performing unrelated computation, H cannot acquire the semaphore until M completes and L finally runs to release it—H is blocked by M despite having higher priority. Priority inheritance protocols solve this by temporarily elevating L's priority to H's level while L holds the semaphore, ensuring M cannot preempt L and artificially extend H's blocking time.

The mathematical framework for reasoning about real-time schedulability originates in the seminal work of Liu and Layland, who proved in 1973 that rate-monotonic scheduling (RMS)—assigning priorities inversely proportional to task periods—is optimal among static-priority algorithms for periodic tasks. Their schedulability bound states that a set of n periodic tasks with worst-case execution times C_i and periods T_i is schedulable under rate-monotonic priorities if the total utilization U = Σ(C_i / T_i) satisfies U ≤ n(2^(1/n) - 1). For large n, this bound approaches approximately 69%, meaning rate-monotonic scheduling guarantees schedulability if the CPU utilization remains below 69%. Tasks violating this bound may still be schedulable, but require exact analysis using response-time calculation or simulation to verify deadline compliance.

The rate-monotonic optimality proof rests on a critical insight about task deadline misses under fixed-priority scheduling. If any fixed-priority assignment can schedule a task set, then the rate-monotonic assignment—shortest period receives highest priority—can also schedule it. The proof proceeds by contradiction: assume a non-rate-monotonic assignment schedules the tasks but the rate-monotonic assignment fails. Then there exist two adjacent-priority tasks where the lower-priority task has a shorter period, violating rate-monotonic ordering. Swapping their priorities cannot harm the higher-priority task (it now preempts more aggressively) and cannot harm the lower-priority task during its own period (the higher-priority task's longer period means it arrives less frequently). This swap contradiction establishes that rate-monotonic must succeed if any static assignment succeeds.

Earliest-deadline-first (EDF) scheduling extends optimality to dynamic priorities by making tasks with nearer absolute deadlines preempt tasks with farther deadlines. EDF achieves 100% CPU utilization schedulability—if U ≤ 1.0, the task set is schedulable—but at the cost of runtime overhead to maintain a priority queue sorted by absolute deadline and frequent priority adjustments as tasks arrive and complete. The engineering tradeoff between RMS and EDF mirrors a fundamental tension in embedded systems: static analysis and predictable behavior versus optimal resource utilization. Safety-critical systems overwhelmingly choose rate-monotonic scheduling because its static priority assignment permits exhaustive pre-deployment analysis, while dynamic-priority EDF requires runtime monitoring and offers fewer formal guarantees about behavior under overload conditions.

Inter-task communication in real-time systems demands mechanisms that preserve temporal determinism while preventing race conditions and data corruption. The classical primitives—semaphores, mutexes, message queues, and event flags—each encode different synchronization semantics with distinct performance and correctness properties. A binary semaphore models a token that tasks can atomically acquire and release, serving as a mutual exclusion lock (mutex) when initialized to 1 or as a synchronization signal when initialized to 0. Counting semaphores generalize this to manage pools of N identical resources, permitting at most N concurrent acquisitions. Message queues provide buffered, asynchronous communication where a sender task enqueues a data structure and a receiver task dequeues it, with the queue acting as a temporal decoupling mechanism that allows sender and receiver to operate at different rates.

The kernel implementation of these primitives directly impacts system determinism. A semaphore `take()` operation must atomically check availability, block the calling task if unavailable, and add the task to a wait queue. The atomic section must disable interrupts or use a kernel spinlock to prevent race conditions, but the duration of this critical section determines interrupt latency—the maximum time an external event waits before the CPU acknowledges it. If the wait queue uses a sorted priority list requiring O(n) insertion time, a system with 50 tasks could inject hundreds of microseconds of non-preemptible kernel execution, obliterating real-time guarantees. High-performance RTOS implementations use priority-sorted bitmaps indexing fixed arrays of per-priority FIFO queues, reducing insertion to O(1) and bounding worst-case execution time independent of task count.

Priority inversion transcends academic curiosity to constitute the most common real-time bug in production firmware. The Mars Pathfinder mission nearly failed in 1997 due to unbounded priority inversion in its VxWorks RTOS configuration. A low-priority meteorological task held a semaphore protecting the inter-task communication bus, was preempted by medium-priority tasks performing unrelated work, and blocked the high-priority attitude control task from accessing the bus. The spacecraft's watchdog timer detected the stalled high-priority task and triggered a system reset, causing intermittent reboots until engineers remotely enabled priority inheritance in VxWorks. This incident crystallized the engineering lesson that priority inheritance is not an optimization but a correctness requirement in any system where tasks of differing priorities share resources.

Priority inheritance operates by tracking semaphore ownership and dynamically elevating a resource-holding task's priority to match the highest-priority blocked waiter. When high-priority task H attempts to acquire a semaphore held by low-priority task L, the kernel immediately raises L's effective priority to H's level, ensuring medium-priority tasks cannot preempt L and extend H's blocking duration. When L releases the semaphore, its priority reverts to its original base level. Priority ceiling protocol extends this idea by assigning each semaphore a static ceiling priority equal to the highest priority of any task that might acquire it, then elevating any task to the ceiling priority upon acquisition. This prevents deadlock by ensuring tasks acquire semaphores in a consistent priority order and bounds blocking time more tightly than basic priority inheritance.

The interaction between interrupt service routines and task scheduling creates subtle architectural constraints. ISRs execute outside the task scheduling context, operating at elevated processor privilege levels with interrupts partially or fully masked. An ISR cannot block waiting for a semaphore—blocking implies yielding the processor to another task, but no task context exists to switch to within the interrupt handler. Instead, ISRs communicate with tasks using lock-free mechanisms: setting event flags, posting to message queues with non-blocking `try_post()` operations, or signaling semaphores to unblock waiting tasks. The ISR performs minimal work—acknowledge the interrupt source, read urgent hardware registers, signal a task—then returns quickly to minimize interrupt latency for lower-priority interrupts and allow the scheduler to dispatch newly-unblocked high-priority tasks.

Deferred interrupt handling reconciles the tension between fast interrupt response and complex processing requirements. A hardware UART receives a byte, triggering an interrupt. The ISR reads the byte from the data register to prevent overrun, enqueues it to a circular buffer, and signals a semaphore. A dedicated UART handler task blocks on that semaphore, waking when data arrives to perform slower protocol parsing, checksum validation, and command dispatch. This split-phase design keeps the ISR deterministically fast—perhaps 500 nanoseconds to save registers, read one hardware register, increment a buffer pointer, and signal—while delegating variable-duration parsing to a task that participates in normal priority-based scheduling. The task's priority determines how urgently the system processes incoming UART data relative to other real-time activities.

Memory architecture fundamentally constrains real-time behavior through cache effects and memory bus arbitration. Modern ARM Cortex-M7 and Cortex-R52 processors incorporate instruction and data caches that reduce average memory access latency but introduce timing variability. A cache miss might stall the pipeline for 10-50 cycles while fetching from external SDRAM, whereas a hit completes in 1-2 cycles. This variability appears directly in worst-case execution time analysis: the same instruction sequence exhibits different execution times depending on cache state. Safety-critical systems often disable data caches entirely or use tightly-coupled memory (TCM)—small on-chip SRAM with deterministic single-cycle access—for time-critical code and data structures. Instruction caches are typically left enabled because instruction fetch patterns are more predictable than data access patterns, and modern processors provide cache-locking mechanisms to permanently load critical interrupt vectors and frequently-executed code into cache lines that cannot be evicted.

Direct Memory Access (DMA) controllers introduce another temporal wildcard. A DMA engine transferring a megabyte from an SD card to SDRAM monopolizes the memory bus for milliseconds, stalling the CPU whenever it attempts to access external memory. Real-time systems must account for DMA traffic in their timing budgets, either by scheduling DMA transfers during known idle periods, prioritizing CPU bus access over DMA using bus arbitration policies, or placing time-critical task stacks and data structures in non-contended TCM. The architectural lesson mirrors the broader real-time philosophy: shared resources—whether mutexes, hardware peripherals, or memory buses—must be analyzed and managed explicitly because implicit resource sharing produces timing emergencies.

Task stack sizing represents a pragmatic engineering challenge with no general algorithmic solution. Each task requires a dedicated stack to store local variables, function call frames, and saved register contexts during preemption. Undersizing the stack causes silent memory corruption when stack overflow overwrites adjacent memory regions; oversizing wastes precious SRAM in memory-constrained microcontrollers. Static analysis tools attempt to compute worst-case stack depth by traversing call graphs and summing frame sizes, but function pointers, recursion, and interrupt nesting defeat pure static analysis. Practical firmware development combines static analysis with runtime stack watermarking: fill each stack with a known pattern (e.g., 0xA5A5A5A5) at initialization, then periodically scan for the deepest address still containing the pattern to measure actual high-water mark usage during testing. Safety margins of 25-50% are common to account for untested code paths and future modifications.

## 2. Core Architecture & Mechanics

The scheduler constitutes the RTOS kernel's beating heart, orchestrating task execution through data structures and algorithms that must operate in microseconds while maintaining mathematical correctness. At its core sits the ready queue, a data structure answering the question: which task should run next? The naive implementation—a single linked list sorted by priority—immediately fails the determinism requirement because inserting a task requires O(n) traversal time proportional to the number of tasks. Instead, production RTOS kernels employ a two-level structure: a priority bitmap and an array of per-priority FIFO queues.

```text
Priority Bitmap (32-bit, one bit per priority level):
Bit 31: Priority 31 (highest)
Bit 30: Priority 30
...
Bit  1: Priority 1
Bit  0: Priority 0 (lowest, idle task)

Ready Queue Array:
ready_queues[31] -> Task_H -> NULL                (priority 31)
ready_queues[30] -> NULL                          (priority 30, empty)
ready_queues[29] -> Task_M1 -> Task_M2 -> NULL    (priority 29)
...
ready_queues[0]  -> Task_Idle -> NULL             (priority 0)
```

The bitmap provides O(1) identification of the highest-priority non-empty queue using a single machine instruction: count-leading-zeros (CLZ) on ARM or bit-scan-reverse (BSR) on x86. If the bitmap reads 0x84000001 in binary (bit 31, bit 26, and bit 0 set), CLZ returns 0, indicating priority 31 has ready tasks. The scheduler indexes `ready_queues[31]` and dequeues the head task in O(1) time. Task insertion is equally fast: set the corresponding bitmap bit and append to the tail of the appropriate priority queue.

Context switching—the mechanical act of saving one task's execution state and restoring another's—exposes the intimate coupling between RTOS kernel and processor architecture. On ARM Cortex-M processors, the hardware itself performs partial context switching through automatic stacking. When an interrupt fires, the processor automatically pushes eight registers (R0-R3, R12, LR, PC, xPSR) to the current task's stack, then loads the vector table entry into PC to begin executing the ISR. The RTOS PendSV (Pendable Service) interrupt handler completes the context switch by manually saving the remaining registers (R4-R11) and switching the stack pointer.

```text
PendSV_Handler (ARM Cortex-M4 assembly):

    ; Disable interrupts
    CPSID   I
    
    ; Save remaining context of current task
    MRS     R0, PSP                  ; Load current Process Stack Pointer
    TST     LR, #0x10               ; Test bit 4 of LR (FPU context flag)
    IT      EQ                       ; If FPU active
    VSTMDBEQ R0!, {S16-S31}         ; Save FPU registers S16-S31
    STMDB   R0!, {R4-R11}           ; Save R4-R11 to task stack
    
    ; Store updated stack pointer in current TCB
    LDR     R1, =current_tcb         ; Load address of current TCB pointer
    LDR     R1, [R1]                 ; Dereference to get TCB address
    STR     R0, [R1]                 ; Store stack pointer in TCB->stack_ptr
    
    ; Call scheduler to select next task (C function)
    BL      scheduler_get_next_task  ; Returns new TCB pointer in R0
    
    ; Update current_tcb global
    LDR     R1, =current_tcb
    STR     R0, [R1]
    
    ; Restore context of next task
    LDR     R0, [R0]                 ; Load stack pointer from new TCB->stack_ptr
    LDMIA   R0!, {R4-R11}           ; Restore R4-R11 from new task stack
    TST     LR, #0x10               ; Test FPU flag again
    IT      EQ
    VLDMIAEQ R0!, {S16-S31}         ; Restore FPU registers if active
    MSR     PSP, R0                  ; Update Process Stack Pointer
    
    ; Re-enable interrupts and return
    CPSIE   I
    BX      LR                       ; Return from exception, hardware restores R0-R3, R12, LR, PC, xPSR
```

This assembly ritual occurs hundreds or thousands of times per second in a heavily-loaded system, making its performance critical. The context switch duration directly determines the minimum quantum for which a task can execute before being preempted—if switching costs 2 microseconds, scheduling tasks for 10-microsecond quanta wastes 20% of CPU time just switching. Modern Cortex-M processors complete context switches in 12-25 cycles (150-400 nanoseconds at 100 MHz) excluding function call overhead, keeping switching cost below 1% for tasks running at 1-millisecond periods.

Task Control Blocks (TCBs) encode all per-task metadata required for scheduling, synchronization, and resource tracking. The kernel maintains a TCB for each task, typically allocated from a static array at compile time to avoid dynamic memory allocation.

```c
typedef enum {
    TASK_READY,      // In ready queue, eligible to run
    TASK_RUNNING,    // Currently executing
    TASK_BLOCKED,    // Waiting on semaphore/queue/delay
    TASK_SUSPENDED   // Administratively stopped
} task_state_t;

typedef struct tcb {
    uint32_t *stack_ptr;           // Current top of stack (SP value)
    uint32_t stack_base;            // Bottom of stack for overflow checking
    uint32_t stack_size;            // Total stack allocation in bytes
    uint8_t  priority;              // Base priority (0-31)
    uint8_t  effective_priority;    // Current priority (elevated by inheritance)
    task_state_t state;             // Current scheduling state
    uint32_t wake_time;             // Absolute tick count for delayed tasks
    struct tcb *next;               // Next TCB in ready/wait queue
    char name[16];                  // Debug identifier
    uint32_t runtime_ticks;         // Accumulated execution time
    void *wait_object;              // Semaphore/queue currently blocking on
} tcb_t;
```

The scheduler maintains a global `current_tcb` pointer indicating the running task, updating it during each context switch. The `stack_ptr` field holds the saved stack pointer value, pointing to the topmost occupied stack location where R4-R11 (and possibly FPU registers) were pushed. The dual-priority system—base priority and effective priority—enables priority inheritance: when a task acquires a semaphore, its effective priority may rise to match higher-priority waiters, but its base priority remains unchanged for restoration when releasing the semaphore.

Semaphore implementation reveals the delicate choreography between atomic operations and task state transitions. A semaphore maintains a count and a priority-ordered wait queue of blocked tasks.

```c
typedef struct {
    int32_t count;                // Available tokens (>=0) or blocked waiters (<0)
    tcb_t *wait_queue;             // Priority-ordered list of blocked tasks
    uint8_t protocol;              // PRIORITY_INHERIT or PRIORITY_CEILING
    uint8_t ceiling_priority;      // For priority ceiling protocol
    tcb_t *owner;                  // Current holder (for mutexes)
} semaphore_t;

void semaphore_take(semaphore_t *sem) {
    uint32_t saved_primask = disable_interrupts();  // Begin critical section
    
    if (sem->count > 0) {
        // Resource available, acquire immediately
        sem->count--;
        if (sem->protocol == PRIORITY_CEILING) {
            current_tcb->effective_priority = sem->ceiling_priority;
        }
        sem->owner = current_tcb;
        restore_interrupts(saved_primask);
        return;
    }
    
    // Resource unavailable, must block
    sem->count--;  // Count goes negative, tracking waiter count
    
    // Apply priority inheritance if enabled
    if (sem->protocol == PRIORITY_INHERIT && sem->owner != NULL) {
        if (current_tcb->effective_priority > sem->owner->effective_priority) {
            sem->owner->effective_priority = current_tcb->effective_priority;
            // If owner is ready (not blocked elsewhere), re-insert in ready queue
            if (sem->owner->state == TASK_READY) {
                ready_queue_remove(sem->owner);
                ready_queue_insert(sem->owner);
            }
        }
    }
    
    // Insert current task into wait queue (priority-ordered)
    current_tcb->state = TASK_BLOCKED;
    current_tcb->wait_object = sem;
    wait_queue_insert(&sem->wait_queue, current_tcb);
    
    // Remove from ready queue and trigger context switch
    ready_queue_remove(current_tcb);
    restore_interrupts(saved_primask);
    
    // Trigger PendSV to perform context switch
    trigger_context_switch();
    
    // Execution resumes here when another task does semaphore_give()
}

void semaphore_give(semaphore_t *sem) {
    uint32_t saved_primask = disable_interrupts();
    
    if (sem->owner == current_tcb) {
        sem->owner = NULL;
        // Restore original priority if it was elevated
        if (current_tcb->effective_priority != current_tcb->priority) {
            current_tcb->effective_priority = current_tcb->priority;
            // May need to re-insert in ready queue if priority dropped below others
            ready_queue_remove(current_tcb);
            ready_queue_insert(current_tcb);
        }
    }
    
    if (sem->count < 0) {
        // Waiters exist, unblock highest-priority waiter
        tcb_t *woken_task = wait_queue_remove_highest(&sem->wait_queue);
        woken_task->state = TASK_READY;
        woken_task->wait_object = NULL;
        ready_queue_insert(woken_task);
        sem->count++;
        
        // Transfer ownership to woken task if using inheritance
        if (sem->protocol == PRIORITY_INHERIT) {
            sem->owner = woken_task;
        }
        
        // If woken task has higher priority, trigger context switch
        if (woken_task->effective_priority > current_tcb->effective_priority) {
            restore_interrupts(saved_primask);
            trigger_context_switch();
            return;
        }
    } else {
        // No waiters, just increment count
        sem->count++;
    }
    
    restore_interrupts(saved_primask);
}
```

The critical sections protected by `disable_interrupts()` must be kept microscopically short—typically 10-30 instructions—because they represent unbounded interrupt latency. During this window, external events arriving at lower-priority interrupts cannot be serviced. The wait queue insertion uses the same priority-bitmap-indexed array structure as the ready queue to maintain O(1) performance, preventing unbounded loop iterations inside the critical section.

Message queues provide buffered asynchronous communication with flow control semantics. A queue holds a fixed-size circular buffer of message slots, along with separate wait queues for sending and receiving tasks.

```c
typedef struct {
    void **buffer;                 // Array of message pointers
    uint16_t capacity;              // Total slots
    uint16_t count;                 // Current occupied slots
    uint16_t read_index;            // Next slot to dequeue from
    uint16_t write_index;           // Next slot to enqueue to
    tcb_t *send_wait_queue;         // Tasks blocked in queue_send()
    tcb_t *recv_wait_queue;         // Tasks blocked in queue_receive()
} queue_t;

bool queue_send(queue_t *q, void *msg, uint32_t timeout_ticks) {
    uint32_t saved_primask = disable_interrupts();
    
    if (q->count < q->capacity) {
        // Space available, enqueue immediately
        q->buffer[q->write_index] = msg;
        q->write_index = (q->write_index + 1) % q->capacity;
        q->count++;
        
        // Unblock one receiving task if any are waiting
        if (q->recv_wait_queue != NULL) {
            tcb_t *woken = wait_queue_remove_highest(&q->recv_wait_queue);
            woken->state = TASK_READY;
            ready_queue_insert(woken);
            
            if (woken->effective_priority > current_tcb->effective_priority) {
                restore_interrupts(saved_primask);
                trigger_context_switch();
                return true;
            }
        }
        
        restore_interrupts(saved_primask);
        return true;
    }
    
    // Queue full, must block or timeout
    if (timeout_ticks == 0) {
        restore_interrupts(saved_primask);
        return false;  // Non-blocking send failed
    }
    
    current_tcb->state = TASK_BLOCKED;
    current_tcb->wake_time = system_tick_count + timeout_ticks;
    wait_queue_insert(&q->send_wait_queue, current_tcb);
    ready_queue_remove(current_tcb);
    restore_interrupts(saved_primask);
    trigger_context_switch();
    
    // Execution resumes here when queue space becomes available or timeout expires
    return (current_tcb->state == TASK_READY);  // True if unblocked by queue_receive, false if timeout
}
```

The circular buffer indexing with modulo arithmetic avoids shifting data when enqueueing and dequeueing, keeping both operations O(1). The dual wait queues permit tasks to block waiting to send (when the queue is full) or receive (when empty), with the kernel automatically unblocking the appropriate waiter when the complementary operation occurs. ISRs can use non-blocking variants (`queue_send_from_isr()`) that return immediately rather than blocking, posting messages to wake task-level handlers.

Timing services—delays, timeouts, periodic execution—require a system tick interrupt driving a monotonic tick counter. Most RTOS configurations use the SysTick timer on ARM Cortex-M processors, configured to interrupt every 1 millisecond (1 kHz tick rate).

```c
volatile uint32_t system_tick_count = 0;

void SysTick_Handler(void) {
    system_tick_count++;
    
    // Scan delayed task list for tasks ready to wake
    tcb_t *task = delayed_task_list;
    while (task != NULL) {
        if (task->wake_time <= system_tick_count) {
            // Time expired, move to ready queue
            tcb_t *next = task->next;
            delayed_list_remove(task);
            task->state = TASK_READY;
            ready_queue_insert(task);
            task = next;
        } else {
            task = task->next;
        }
    }
    
    // Trigger scheduler in case a woken task has higher priority
    trigger_context_switch();
}

void task_delay(uint32_t ticks) {
    uint32_t saved_primask = disable_interrupts();
    
    current_tcb->state = TASK_BLOCKED;
    current_tcb->wake_time = system_tick_count + ticks;
    delayed_list_insert(current_tcb);
    ready_queue_remove(current_tcb);
    
    restore_interrupts(saved_primask);
    trigger_context_switch();
    // Execution resumes after ticks milliseconds
}
```

The delayed task list is typically maintained as a delta list where each node stores the time delta to the next wakeup rather than absolute times, reducing the number of comparisons in the SysTick handler. The handler need only decrement the head node's delta each tick and wake tasks when the delta reaches zero, rather than scanning the entire list comparing absolute times.

Periodic task execution patterns—the motor control loop running every 5 milliseconds, the sensor sampling task every 100 milliseconds—employ a self-rescheduling pattern that compensates for execution time to maintain precise periods.

```c
void motor_control_task(void *param) {
    const uint32_t period_ticks = 5;  // 5 ms period
    uint32_t next_wake_time = system_tick_count;
    
    while (1) {
        // Perform control loop work
        read_encoder_position();
        compute_pid_output();
        update_pwm_duty_cycle();
        
        // Delay until next period, accounting for execution time
        next_wake_time += period_ticks;
        uint32_t current_time = system_tick_count;
        if (next_wake_time > current_time) {
            task_delay(next_wake_time - current_time);
        } else {
            // Deadline overrun, task took longer than period
            next_wake_time = current_time;  // Resync to avoid infinite catch-up
            deadline_miss_count++;
        }
    }
}
```

This absolute-time delay pattern maintains constant period despite varying execution time. If the control loop computation takes 2.3 milliseconds, the task delays 2.7 milliseconds until the 5-millisecond mark. If computation takes 4.8 milliseconds, it delays 0.2 milliseconds. The deadline-overrun detection identifies when computation exceeds the period, indicating that either the algorithm needs optimization or the period needs lengthening.

## 3. High-Performance Optimization & Failure Modes

Interrupt latency—the delay from external event assertion to the first instruction of the ISR executing—determines system responsiveness and constrains real-time guarantee quality. Latency arises from three sources: hardware synchronization (1-3 clock cycles to synchronize the asynchronous external signal to the CPU clock domain), interrupt controller prioritization and arbitration (2-5 cycles for the NVIC to determine the highest-priority pending interrupt), and register stacking (12-25 cycles for the processor to automatically push R0-R3, R12, LR, PC, xPSR). A 100 MHz Cortex-M4 thus exhibits minimum interrupt latency around 200-300 nanoseconds in the best case.

Worst-case latency includes additional factors: if interrupts are globally disabled in a critical section, latency extends by the critical section duration. If a lower-priority ISR is executing when a higher-priority interrupt arrives, the processor must complete the current instruction (1-5 cycles), push context (12-25 cycles), then tail-chain directly to the higher-priority handler, adding 20-40 cycles. If the higher-priority interrupt arrives while the processor is executing a multi-cycle instruction like integer divide (2-12 cycles on Cortex-M4) or writing to memory through a slow peripheral bus, that instruction completes before handling the interrupt.

Critical sections represent the primary threat to determinism. Every microsecond spent with interrupts disabled extends worst-case latency for every lower-priority interrupt. Brutal discipline is required: critical sections must touch only memory-resident data structures, never perform I/O, and avoid loops with iteration counts proportional to task count or message queue depth. When priority-ordered insertion into a wait queue requires iteration, the structure must be redesigned to use the bitmap-indexed array pattern permitting O(1) insertion. Code review must scrutinize every `disable_interrupts()` / `restore_interrupts()` pair, measuring instruction counts and verifying that nested critical sections properly preserve the interrupt enable state.

Priority inversion pathologies extend beyond the classic three-task scenario. Transitive blocking occurs when high-priority task H blocks on semaphore S1 held by medium-priority M, which itself blocks on semaphore S2 held by low-priority L. Basic priority inheritance elevates M to H's priority but does not propagate further to L, so L executes at its original low priority while H waits. Proper priority inheritance implementation must transitively propagate priority elevation through the entire blocking chain: when H blocks on S1, M inherits H's priority; when M is found to be blocked on S2, L inherits M's elevated priority. This requires that semaphore wait queues track not just blocked tasks but also the reasons for blocking, enabling the kernel to walk the dependency graph.

Deadlock emerges when circular wait conditions trap multiple tasks permanently. Task A holds semaphore S1 and attempts to acquire S2, while task B holds S2 and attempts to acquire S1—both tasks block indefinitely waiting for the other. Priority ceiling protocol prevents deadlock by assigning each semaphore a ceiling priority and elevating any task to that ceiling when acquiring the semaphore. If tasks acquire semaphores in any order, the priority elevation ensures that once a task holds any semaphore, no other task can preempt it until all semaphores are released, eliminating the possibility of circular wait. The cost is reduced concurrency: tasks that could safely run concurrently (because they access disjoint resource sets) are artificially serialized by the coarse-grained ceiling priorities.

Stack overflow constitutes the most insidious firmware bug, manifesting as intermittent corruption that evaporates when adding debug logging (which alters stack layout and timing). Hardware memory protection units (MPUs) provide runtime detection by configuring guard regions immediately below each task stack marked as no-access. Any stack overflow triggers a MemManage exception, immediately halting the system rather than silently corrupting adjacent memory. The MPU configuration requires one region per task stack, consuming precious MPU region slots (Cortex-M4 provides eight regions; Cortex-M33 provides eight or sixteen depending on configuration).

```c
void configure_task_mpu_guard(tcb_t *task) {
    // Configure MPU region N as 32-byte guard zone below stack
    uint32_t guard_base = task->stack_base - 32;
    MPU->RBAR = guard_base | MPU_REGION_VALID | region_number;
    MPU->RASR = MPU_RASR_ENABLE_Msk |          // Enable region
                MPU_RASR_XN_Msk |               // Execute-never
                (0 << MPU_RASR_AP_Pos) |        // No access (AP=0b000)
                (4 << MPU_RASR_SIZE_Pos);       // 32 bytes (2^5)
}
```

Software-based stack checking instruments function prologues to verify stack pointer against a per-task limit, but the instrumentation itself consumes stack space and CPU cycles, creating a Heisenberg-style measurement perturbation. Stack canaries—placing a known magic value at the stack top and periodically verifying it remains unmodified—detect overflow after the fact but cannot prevent the corruption itself.

Memory fragmentation plagues systems that allocate message buffers or data structures from a shared heap. As tasks allocate and free variable-sized blocks, the heap develops "holes" of free space too small to satisfy allocation requests despite adequate total free memory. Hard real-time systems eschew dynamic allocation entirely, using fixed-size pools pre-allocated at initialization. A message queue that transmits variable-size messages allocates from a pool of 64-byte blocks, wasting space on small messages but guaranteeing bounded allocation time and eliminating fragmentation.

```c
typedef struct {
    void *blocks[MAX_BLOCKS];
    uint32_t block_size;
    uint32_t free_count;
    uint32_t free_bitmap[(MAX_BLOCKS + 31) / 32];  // One bit per block
} memory_pool_t;

void* pool_alloc(memory_pool_t *pool) {
    uint32_t saved_primask = disable_interrupts();
    
    if (pool->free_count == 0) {
        restore_interrupts(saved_primask);
        return NULL;  // Pool exhausted
    }
    
    // Find first set bit in bitmap (first free block)
    for (int i = 0; i < (MAX_BLOCKS + 31) / 32; i++) {
        uint32_t word = pool->free_bitmap[i];
        if (word != 0) {
            int bit = __builtin_ctz(word);  // Count trailing zeros (ARM CLZ equivalent)
            int block_index = i * 32 + bit;
            pool->free_bitmap[i] &= ~(1 << bit);  // Clear bit
            pool->free_count--;
            restore_interrupts(saved_primask);
            return pool->blocks[block_index];
        }
    }
    
    restore_interrupts(saved_primask);
    return NULL;  // Should never reach here
}
```

The bitmap allocation permits O(1) allocation and deallocation without list traversal, and the fixed block size eliminates fragmentation entirely. The tradeoff is inflexibility—message sizes must fit within the block size, requiring padding or falling back to alternative mechanisms for oversized messages.

Timer drift accumulates when periodic tasks use relative delays rather than absolute scheduling. If a task delays 10 milliseconds, performs work, then delays 10 milliseconds again, the period is actually 10 milliseconds plus the execution time. Over thousands of iterations, this drift can accumulate to hundreds of milliseconds, causing a motor control loop nominally running at 100 Hz to drift down to 95 Hz. The absolute-time delay pattern shown earlier eliminates drift by scheduling against absolute tick counts, but requires monitoring for deadline overruns where execution time exceeds the period.

Deadline overrun analysis determines whether a task set remains schedulable as workload increases. Response-time analysis computes the worst-case time from task release to completion by iteratively solving:

R_i = C_i + Σ_(j ∈ hp(i)) ⌈R_i / T_j⌉ · C_j

where R_i is task i's response time, C_i is its worst-case execution time, hp(i) is the set of higher-priority tasks, and T_j is the period of higher-priority task j. The ceiling brackets represent the maximum number of times higher-priority task j can preempt task i during R_i time units. This equation is solved iteratively starting with R_i = C_i, then recomputing until convergence. If R_i ≤ D_i (deadline), the task meets its deadline. This analysis requires accurate WCET measurements, typically obtained through combination of static analysis tools, simulator profiling, and on-target instrumentation.

Cache effects inject timing variability that complicates WCET analysis on high-performance processors. A function may execute in 500 cycles on the first call (cache-cold, all instruction fetches miss) and 200 cycles on subsequent calls (cache-warm). Static analysis tools conservatively assume all accesses miss, producing overly pessimistic WCET bounds. Cache-locking mechanisms on ARM Cortex-R and Cortex-A processors allow software to load critical code into cache lines marked as locked, preventing eviction and guaranteeing cache-hit timing, but this reduces available cache for non-critical code. The architectural lesson mirrors broader real-time tradeoffs: determinism requires either avoiding features with timing variability (disable caches) or managing them explicitly (cache locking, scratchpad memories, predictable replacement policies).

Interrupt flooding occurs when a misbehaving peripheral generates interrupts faster than the ISR can service them, starving task-level execution. A UART receiving data at 921600 baud with per-byte interrupts fires 92,160 interrupts per second; at 2 microseconds per ISR, this consumes 18% of CPU time. DMA-based reception reduces this to one interrupt per buffer (e.g., every 64 bytes), cutting interrupt rate by 64× to 1,440 per second and CPU consumption to 0.3%. Rate-limiting in the interrupt controller can disable an interrupt source after N consecutive assertions without acknowledging, forcing software to poll or use a lower-priority interrupt for recovery.

The tension between modularity and efficiency appears starkly in RTOS kernel design. A microkernel architecture isolates device drivers and protocol stacks in separate protection domains, communicating through message passing, maximizing robustness at the cost of message-passing overhead for every cross-domain call. A monolithic kernel places drivers and kernel in the same address space, eliminating message-passing overhead but sacrificing isolation—a buggy driver can corrupt kernel data structures. Safety-critical systems typically choose monolithic kernels with rigorous qualification and testing to minimize overhead, accepting the reduced isolation because the entire firmware image undergoes certification as a unit.

Certification against safety standards (DO-178C for avionics, IEC 61508 for industrial, ISO 26262 for automotive) imposes engineering rigor that extends beyond functional correctness to include structural coverage, requirements traceability, and tool qualification. A DO-178C Level A (software whose failure could cause catastrophic loss of aircraft) RTOS must demonstrate that every source line and branch has been executed during testing (Modified Condition/Decision Coverage, MC/DC), that every requirement maps to a test case, and that the compiler and linker themselves have been validated to not introduce errors. These requirements drive architectural decisions: smaller, simpler kernels reduce certification cost; deterministic algorithms with bounded loops permit exhaustive testing; absence of dynamic memory allocation eliminates a class of potential failures.

The final lesson in real-time systems mirrors the broader embedded discipline: guarantees come from design, not luck. A system that "usually" responds within 10 milliseconds is not a real-time system—it is a general-purpose system that happens to be lightly loaded. Real-time engineering demands worst-case analysis, static allocation, deterministic algorithms, and architectural discipline to transform "usually" into "always," converting statistical properties into engineering guarantees.
