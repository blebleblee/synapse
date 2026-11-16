# Lesson 2: Interrupt Handling, Concurrency Models, Critical Sections

## 1. First-Principles Intuition & Invariants

The execution model of embedded systems diverges fundamentally from sequential, single-threaded computation. In bare-metal firmware, a microcontroller must simultaneously service asynchronous hardware events—timer expirations, incoming serial data, GPIO state changes, sensor interrupts—while maintaining a main application loop. Interrupts are the mechanism by which external stimuli demand immediate CPU attention, interrupting the current instruction stream and forcing a context switch to specialized handler code. Understanding interrupts is not merely a matter of memorizing API calls; it requires deep comprehension of how the processor's control flow is physically hijacked, how execution state is preserved, and how multiple interrupt sources compete for scarce computational resources.

The core invariant that governs interrupt handling is **atomicity under asynchronicity**. When an interrupt fires, the CPU halts execution of its current instruction (or completes it, depending on architecture) and begins executing an interrupt service routine (ISR). From the perspective of the interrupted code, the ISR appears to execute instantaneously between two consecutive instructions. This creates a profound problem: if the interrupted code and the ISR both access shared data structures—a queue, a register, a flag variable—they may corrupt that data because there is no guarantee of atomic access. The solution is the critical section: a region of code where interrupts are masked (disabled) to ensure exclusive access to shared resources.

Priority is the second fundamental invariant. Real-world embedded systems rarely have just one interrupt source. A microcontroller might simultaneously service a high-priority sensor interrupt, a medium-priority communication interrupt, and a low-priority timer interrupt. If a low-priority ISR is executing when a high-priority interrupt fires, the CPU must abandon the low-priority ISR, service the high-priority interrupt, and return. This nesting creates a call stack of interrupted ISRs and introduces subtle failure modes: priority inversion, where a high-priority task is blocked waiting for a resource held by a low-priority task, and deadlock scenarios where ISRs and background code deadlock over a shared resource.

The third invariant is **determinism under constraints**. Embedded systems often operate in real-time environments where a deadline missed is a failure. If an ISR takes too long, it delays the servicing of other interrupts and prevents the main application from making progress. Unlike general-purpose operating systems that can preempt long-running tasks, firmware engineers must manually reason about interrupt latency budgets: how much time does each ISR consume, and does that leave enough time to service all higher-priority interrupts before the next interrupt of equal or lower priority arrives?

These three invariants—atomicity, priority, and determinism—form the conceptual foundation upon which all interrupt-driven firmware is built. They are not optional considerations; they are constraints that firmware engineers must respect or face data corruption, missed deadlines, and unpredictable system behavior.

## 2. Core Architecture & Mechanics

### Interrupt Vector Tables and Hardware Signaling

The interrupt vector table (IVT) is a data structure that resides in memory at a fixed address defined by the processor architecture. Each entry in the IVT is typically a pointer (or, in some architectures, an offset) to an interrupt service routine. When hardware asserts an interrupt signal, the CPU's interrupt controller (often called the Nested Vectored Interrupt Controller, NVIC, on ARM Cortex-M devices, or the Advanced Programmable Interrupt Controller, APIC, on x86 systems) prioritizes the interrupt, looks up the corresponding vector in the IVT, and forces the CPU to jump to that address.

Consider an ARM Cortex-M4 microcontroller. The processor has 16 built-in exceptions (resets, faults, SVCall, PendSV, SysTick) at fixed vector positions 0–15, and then external interrupts (GPIO, UART, SPI, timers) at positions 16 and beyond. The IVT for a Cortex-M4 is typically placed at address `0x00000000` (or `0x20000000` for RAM-based vectors on some devices). Each entry is a 32-bit address pointing to the corresponding handler.

```
Interrupt Vector Table Layout (ARM Cortex-M4)
==================================================
Address     | Vector # | Handler
0x00000000  | 0        | Initial Stack Pointer (MSP)
0x00000004  | 1        | Reset Handler
0x00000008  | 2        | NMI Handler
0x0000000C  | 3        | Hard Fault Handler
0x00000010  | 4        | Memory Manage Fault Handler
0x00000014  | 5        | Bus Fault Handler
0x00000018  | 6        | Usage Fault Handler
0x0000001C  | 7–10     | Reserved
0x0000002C  | 11       | SVCall Handler
0x00000030  | 12       | Debug Monitor Handler
0x00000034  | 13       | Reserved
0x00000038  | 14       | PendSV Handler
0x0000003C  | 15       | SysTick Handler
0x00000040  | 16       | IRQ0 (External Interrupt 0)
0x00000044  | 17       | IRQ1 (External Interrupt 1)
...
```

When an external interrupt fires, the hardware does not simply jump to the handler; it performs a context save. On ARM Cortex-M, the CPU automatically pushes eight 32-bit registers onto the currently active stack (PSP for process stack, MSP for main stack) in this order: R0, R1, R2, R3, R12, LR (link register), PC (program counter), and xPSR (execution program status register). This automatic push takes 12 clock cycles on most Cortex-M variants and occurs atomically—the bus is locked, preventing other transactions. After the push, the CPU loads the PC from the IVT and begins executing the ISR. The LR register is set to a special exception return value (0xFFFFFFxx on Cortex-M) that signals the CPU to restore the context when the ISR executes a return instruction.

This hardware context-save mechanism is elegant but comes with constraints. First, the automatic push only saves eight registers; additional registers used by the ISR must be pushed manually. Second, the automatic push uses a fixed stack pointer (either PSP or MSP depending on the CPU mode at the time of interrupt), so ISRs must be aware of which stack they are using. Third, the xPSR register contains the interrupt number in its bits [8:0], allowing the ISR to determine which interrupt fired.

On x86-64 systems, the interrupt handling mechanism is more complex. The CPU uses an Interrupt Descriptor Table (IDT), where each entry is an 8-byte descriptor containing the address of the handler, privilege level information, and gate type (trap, interrupt, or task gate). When an interrupt fires, the CPU pushes the current state onto the stack (return address, flags, code segment, stack segment) and jumps to the handler. Unlike Cortex-M's automatic context save, x86-64 requires the handler to manually push any registers it uses. The x86-64 architecture also distinguishes between maskable interrupts (which can be disabled with `cli` instruction) and non-maskable interrupts (NMI), which cannot be masked.

### Priority, Nesting, and the Interrupt Mask Register

The second critical piece of interrupt hardware is the priority mechanism. Each interrupt source has a priority level (often 4 bits on embedded systems, yielding 16 priority levels). The CPU will only accept an interrupt if its priority is higher than the current priority level (the CPU's interrupt mask). This prevents lower-priority interrupts from interrupting higher-priority ISRs.

On ARM Cortex-M, priority levels are configured in the Interrupt Priority registers (IPRx) in the NVIC. Each interrupt gets an 8-bit priority field, though only the upper bits are implemented (typically bits [7:5] or [7:4] depending on configuration). A lower numerical value indicates higher priority. The current interrupt priority is tracked in the Interrupt Program Status Register (IPSR) in the xPSR. When an interrupt fires, the NVIC compares its priority against the current priority; if the new interrupt has higher priority, it is accepted immediately, preempting the current ISR. If it has equal or lower priority, it is latched and serviced after the current ISR completes.

The following diagram illustrates the priority arbitration flow:

```
Interrupt Arbitration Flow
===================================

Hardware Interrupt Asserted
            |
            v
    NVIC Priority Comparator
            |
            +-- Is priority > current CPU priority?
            |       |
            |       +-- YES: Accept interrupt, save context, jump to handler
            |       |
            |       +-- NO: Latch interrupt, continue current execution
            |
            v
    ISR Executes
            |
            v
    ISR Returns (exception return)
            |
            v
    Check Latched Interrupts
            |
            +-- Any pending? Jump to highest-priority pending handler
            |
            +-- None pending? Resume interrupted code
```

This priority scheme enables nested interrupts. Consider a scenario: the CPU is executing a low-priority ISR for a GPIO interrupt (priority level 15). While the GPIO ISR runs, a high-priority timer interrupt fires (priority level 3). Because the timer interrupt has higher priority, the NVIC immediately halts the GPIO ISR, saves its context, and jumps to the timer ISR. When the timer ISR completes, the CPU resumes the GPIO ISR from where it was interrupted. This nesting can go arbitrarily deep, limited only by stack space and the number of distinct interrupt priorities.

However, this elegance masks a dangerous pitfall: **priority inversion**. Imagine the main application (running at priority level 16, the lowest, outside the interrupt mask) acquires a mutex protecting a shared queue. While the application holds the mutex, a high-priority ISR (priority level 3) fires and attempts to access the same queue. The ISR calls a function that tries to acquire the mutex, blocks (because the application still holds it), and resumes immediately because ISRs cannot be suspended by a blocking operation—they run to completion or loop forever. The high-priority ISR is now effectively blocked by the low-priority application code, and the system deadlocks. This scenario demands careful API design: ISRs should never attempt to acquire locks held by lower-priority code. Instead, the application should use lockless data structures (ring buffers, atomic operations) for ISR-to-application communication.

### Memory Barriers and Atomicity

At the instruction level, the problem of shared data becomes acute. Suppose a global variable `flag` is accessed by both the main application and an ISR. The application might execute:

```c
flag = 1;
if (some_condition) {
    // do work
}
```

The compiler might optimize this into machine code that stores `flag` and then performs the conditional check. But if an interrupt fires between the store and the check, the ISR might read `flag` before the store completes (due to store buffering in modern CPUs), or the ISR might execute code that depends on `flag` being written atomically. The result is a race condition.

Embedded systems solve this problem with memory barriers and atomic operations. A memory barrier is a CPU instruction that prevents the CPU from reordering memory operations across the barrier. On ARM, the `DMB` (Data Memory Barrier) instruction ensures that all memory operations before the barrier complete before any operations after the barrier begin. The `DSB` (Data Synchronization Barrier) is stronger: it waits for all memory operations to complete and also flushes the instruction pipeline. On x86-64, the `mfence` (memory fence) instruction provides similar semantics.

For simple shared variables accessed by both ISRs and background code, the `volatile` keyword in C prevents the compiler from caching values in registers and forces a memory read or write on every access. However, `volatile` alone does not guarantee atomicity on multi-word variables or compound operations. A safer approach is to use atomic operations provided by the compiler or CPU. The C11 standard introduces `_Atomic` types and `atomic_*` functions that map to CPU-level atomic instructions. On ARM, atomic operations use the `LDREX` (Load Exclusive) and `STREX` (Store Exclusive) instructions, which implement a reservation system: `LDREX` loads a value and marks the address as reserved; `STREX` writes the value only if the reservation is still held. If an interrupt fires between `LDREX` and `STREX`, the reservation is cleared, and `STREX` fails, signaling the application to retry.

On ARM Cortex-M, there is no true multiprocessor contention (typically), so `LDREX`/`STREX` are primarily used to prevent ISR interference. For example, an atomic increment of a counter:

```c
// Non-atomic increment (subject to ISR corruption)
counter++;

// Atomic increment using LDREX/STREX (pseudocode)
do {
    uint32_t value = __ldrex(&counter);
    value++;
} while (__strex(value, &counter) != 0);

// Atomic increment using compiler builtin
__atomic_add_fetch(&counter, 1, __ATOMIC_RELAXED);
```

The `__ATOMIC_RELAXED` memory order specifies that no memory barrier is needed; the operation is atomic at the instruction level but does not synchronize with other threads. Stronger memory orders like `__ATOMIC_ACQUIRE` or `__ATOMIC_RELEASE` add implicit barriers.

### Context Switching and Stack Management

When an interrupt fires, the CPU switches from one execution context to another. The context includes not only the general-purpose registers but also the stack pointer, program counter, and any CPU state registers. On ARM Cortex-M, the automatic context save pushes eight registers; any additional registers used by the ISR must be manually preserved.

Consider a concrete example. A timer ISR increments a millisecond counter and checks if it has reached a threshold to trigger a background task. The ISR uses registers R0 through R3 (which are caller-saved and may be in use by the interrupted code) and R4 through R11 (which are callee-saved and must be preserved). The ISR must manually push R4–R11 before using them and pop them before returning.

```c
__attribute__((naked)) void TIMER_ISR(void) {
    // R0-R3, R12, LR, PC, xPSR already pushed by hardware
    asm volatile(
        "push {r4-r11}\n"           // Save callee-saved registers
        "ldr r0, =millisecond_counter\n"
        "ldr r1, [r0]\n"
        "add r1, #1\n"
        "str r1, [r0]\n"
        "pop {r4-r11}\n"            // Restore callee-saved registers
        "bx lr\n"                   // Exception return (restores context)
        :
        :
        : "memory"
    );
}
```

The `naked` attribute tells the compiler not to generate a prologue or epilogue; the ISR is responsible for all register management. The `bx lr` instruction performs an exception return: it loads the PC from the LR (which holds the special exception return value), restores the context from the stack, and resumes execution.

Stack management is critical in interrupt-driven systems. Each ISR and the main application must have sufficient stack space. A deep call chain of nested ISRs can exhaust the stack and corrupt data. Firmware engineers must analyze the worst-case stack depth: identify the deepest call chain from any ISR, add the automatic context save (8 registers × 4 bytes = 32 bytes on Cortex-M), and add any additional stack frames for function calls within the ISR. Modern ARM compilers provide tooling to compute stack usage, but manual analysis is still necessary for safety-critical systems.

### The Critical Section and Interrupt Masking

The critical section is the primary synchronization primitive in embedded firmware. A critical section is a region of code where interrupts are disabled, ensuring that the code executes atomically with respect to interrupt handlers. On ARM Cortex-M, critical sections are entered by disabling interrupts and exited by re-enabling them.

```c
// Enter critical section
uint32_t primask = __get_PRIMASK();
__disable_irq();

// Critical section: access shared data
shared_queue_push(item);

// Exit critical section
if (!(primask & 0x01)) {
    __enable_irq();
}
```

The `__get_PRIMASK()` function reads the Interrupt Mask Register (PRIMASK), which has a single bit indicating whether interrupts are masked. By saving this value before disabling interrupts, the code can restore the previous state, allowing nested critical sections. If the interrupted code was already in a critical section, the nested critical section should not re-enable interrupts prematurely.

However, this approach has a cost: disabling interrupts increases interrupt latency. Any interrupt that fires while interrupts are masked must wait until they are re-enabled. In systems with hard real-time constraints, long critical sections can cause deadline misses. A more sophisticated approach is to use a priority mask that disables only lower-priority interrupts, leaving higher-priority interrupts free to execute.

On ARM Cortex-M, the `BASEPRI` register masks interrupts at a specified priority level or higher. For example, setting `BASEPRI` to 0x60 disables interrupts with priority levels 12–15 (assuming 4-bit priority fields), while allowing higher-priority interrupts (0–11) to execute. This approach, called priority-based locking, allows the firmware to protect against ISRs of equal or lower priority while remaining preemptible by higher-priority ISRs.

```c
// Priority-based critical section (Cortex-M)
#define CRITICAL_PRIORITY 0x60  // Mask priority 12-15

uint32_t basepri_save = __get_BASEPRI();
__set_BASEPRI(CRITICAL_PRIORITY);

// Critical section: protected against ISRs with priority >= CRITICAL_PRIORITY
shared_data_modified = 1;

__set_BASEPRI(basepri_save);
```

This approach is safer than blanket interrupt disabling but requires careful analysis. The critical section is now safe against ISRs with priority >= `CRITICAL_PRIORITY`, but ISRs with higher priority can still preempt it. If a high-priority ISR attempts to access the same shared data, a race condition occurs. The solution is to ensure that all accesses to a given piece of shared data occur at the same priority level or are protected by an equivalent critical section at the ISR's priority level.

## 3. High-Performance Optimization & Failure Modes

### Interrupt Latency and Real-Time Constraints

Interrupt latency is the time from when an interrupt is asserted to when the ISR begins executing. It has several components: hardware latency (the time for the NVIC to prioritize and signal the CPU), context save latency (the automatic push of registers), and ISR prologue latency (any additional register saves or function call overhead). On ARM Cortex-M, total interrupt latency is typically 12–16 clock cycles, though this can vary based on memory access patterns and pipeline state.

In real-time systems, interrupt latency directly translates to deadline miss probability. If a periodic interrupt must fire every 1 millisecond and interrupt latency is 16 microseconds, the ISR has 984 microseconds to complete before the next interrupt arrives (assuming no other interrupts). If the ISR exceeds this budget, either the next interrupt is delayed or, if preemption is configured, the next interrupt preempts the current one, increasing latency further.

Optimizing for latency requires profiling and careful coding. First, measure actual interrupt latency using a GPIO pin toggled in the main loop and toggled again in the ISR; observe the time difference on an oscilloscope. Second, minimize ISR execution time: avoid expensive operations like division, floating-point math, or function calls. If the ISR must perform complex work (parsing incoming data, updating multiple data structures), defer that work to a background task and have the ISR only set a flag or push a minimal amount of data into a queue.

Consider a UART receive ISR. The naive implementation might parse the received byte and update a complex state machine:

```c
void UART_ISR(void) {
    uint8_t byte = UART_DATA;
    parse_protocol_byte(byte);  // Expensive function call
    update_state_machine();      // More expensive work
}
```

This ISR is slow and monopolizes the CPU, delaying other interrupts. A better approach is to buffer the raw data and defer parsing to the main loop:

```c
#define RX_BUFFER_SIZE 256
static uint8_t rx_buffer[RX_BUFFER_SIZE];
static volatile uint16_t rx_head = 0;
static volatile uint16_t rx_count = 0;

void UART_ISR(void) {
    uint8_t byte = UART_DATA;
    rx_buffer[rx_head] = byte;
    rx_head = (rx_head + 1) & (RX_BUFFER_SIZE - 1);
    __atomic_add_fetch(&rx_count, 1, __ATOMIC_RELAXED);
}

// In main loop:
void main(void) {
    while (1) {
        if (rx_count > 0) {
            uint8_t byte = rx_buffer[rx_tail];
            rx_tail = (rx_tail + 1) & (RX_BUFFER_SIZE - 1);
            __atomic_sub_fetch(&rx_count, 1, __ATOMIC_RELAXED);
            parse_protocol_byte(byte);
        }
    }
}
```

This approach keeps the ISR tight (just a buffer write and counter increment) and moves the expensive parsing to the main loop where latency is less critical.

### Priority Inversion, Deadlock, and Recovery

Priority inversion occurs when a high-priority task is effectively blocked by a low-priority task. The classic scenario involves three tasks: high-priority ISR H, low-priority application L, and medium-priority ISR M. Task L acquires a mutex protecting a shared resource. ISR H fires and attempts to acquire the same mutex, but it is held by L, so H cannot proceed. But L cannot release the mutex because it is preempted by M, which has higher priority than L. So M runs while H waits, and H (which has the highest priority) is blocked by L (which has the lowest). The system exhibits pathological behavior: the high-priority ISR does not execute, and all three tasks are effectively stalled.

Embedded firmware avoids this scenario by enforcing a strict discipline: **ISRs must never block or attempt to acquire locks held by background code**. Instead, ISRs communicate with the application through lockless mechanisms like ring buffers or atomic flags. If an ISR absolutely must access shared data, the application must use priority-based critical sections that mask ISRs at the ISR's priority level, ensuring the ISR is never blocked by the application.

A second failure mode is **ISR deadlock**, where two ISRs at the same priority level both attempt to acquire the same lock. This is impossible in typical interrupt hardware because only one ISR at a given priority level can execute at a time; the second ISR will not fire until the first completes. However, if an ISR attempts to acquire a lock held by itself (re-entrant locking), it will deadlock. This can happen if an ISR calls a library function that also acquires the lock. The solution is to ensure ISRs are re-entrant or to use re-entrant-safe library functions that do not acquire locks.

A third failure mode is **stack overflow due to deep nesting**. If a series of high-priority ISRs all fire in quick succession, each one preempts the previous, and the call stack grows with each context save. If the stack grows into the heap or overwrites other data, memory corruption occurs. The remedy is to compute the maximum stack depth, allocate sufficient stack space, and use stack canaries or memory protection units to detect overflows.

Recovery from these failure modes is difficult in bare-metal systems because there is no operating system to detect deadlocks or preempt runaway code. The only reliable recovery is prevention through careful design: analyze priority levels, enforce lockless communication between ISRs and the application, compute maximum stack depth, and test with stress scenarios that trigger all interrupt sources simultaneously.

### Optimization Patterns: Polling vs. Interrupts, Busy-Waiting, and DMA Integration

Embedded systems often face a choice between polling and interrupt-driven designs.

**Polling** is appropriate when latency requirements are relaxed, CPU utilization is low, or the event rate is predictable (e.g., sampling a sensor every 100ms). Polling eliminates interrupt overhead and simplifies timing analysis but wastes CPU cycles and increases response latency. **Interrupts** are necessary when latency must be bounded (sub-microsecond response) or when multiple asynchronous events must be serviced concurrently. The tradeoff is determinism versus efficiency: polling yields predictable execution but poor resource utilization; interrupts maximize efficiency but introduce jitter and priority inversion risk.

**Busy-waiting** inside an ISR—spinning on a hardware flag or shared variable—is almost always incorrect. It blocks lower-priority ISRs, wastes CPU cycles, and can cause deadlock if the condition depends on another ISR. The correct pattern is to signal the condition (via flag or semaphore) and return immediately, allowing the application or a deferred handler to poll or block on the condition outside interrupt context.

**DMA integration** offloads bulk data transfers (UART RX buffers, SPI transactions, ADC sample arrays) from the CPU to hardware, reducing interrupt frequency and freeing CPU cycles for application logic. The typical pattern is to configure a circular DMA buffer, enable transfer-complete and half-transfer interrupts, and process data in chunks within the ISR or a deferred task. DMA eliminates per-byte interrupts (reducing overhead by 10–100×) but requires careful cache coherency management on systems with data caches: invalidate cache lines before reading DMA-written data, flush cache lines before DMA reads application-written data. Failure to manage coherency results in stale or corrupted data.

The optimization hierarchy is: prefer DMA for bulk transfers, use interrupts for low-latency events, reserve polling for low-rate or non-critical events, and never busy-wait in ISR context.

## 4. Summary & Verification Matrix

| **Invariant/Mechanism** | **Purpose** | **Verification Criteria** |
|-------------------------|-------------|---------------------------|
| ISR execution time ≤ worst-case deadline | Ensure no interrupt is starved by a long-running ISR | Measure ISR duration with logic analyzer; compute WCET including preemption overhead; verify Σ(ISR_time × rate) < CPU budget |
| Priority inversion bounded by priority ceiling | Prevent unbounded blocking of high-priority tasks | Audit all shared resources; assign locks priority = max(task priorities); test with simultaneous interrupt load |
| Lock-free queues or double-buffering for ISR↔task communication | Eliminate deadlock and reduce ISR overhead | Verify all ISR→task paths use atomic operations or DMA; no mutex/semaphore acquisition in ISR context |
| Stack depth = max nesting depth + safety margin | Prevent stack overflow under maximum preemption | Compute call tree depth for all ISR paths; measure actual stack usage with canary or MPU; stress-test with simultaneous interrupts |
| DMA cache coherency management | Ensure correct data visibility between CPU and DMA | Validate cache invalidate/flush on all DMA buffers; test on hardware with cache enabled; verify with bus analyzer or memory dump |
