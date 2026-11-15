# Lesson 6: Safety-Critical Design Verification

## 1. First-Principles Intuition & Invariants

The embedded systems that control human life—aircraft avionics, cardiac pacemakers, automotive brake-by-wire systems, industrial reactor monitors—operate under a constraint that consumer electronics rarely encounter: the cost of failure is measured in lives, not lost revenue. This fundamental reality reshapes every decision from architecture selection through production deployment. Safety-critical design verification is not a checkbox to enable compliance certification; it is a systematic engineering discipline that transforms intuition about "what should work" into mathematical proof that failure modes are bounded, detectable, and recoverable.

The core invariant underpinning safety-critical systems is the *failure mode analysis hierarchy*. Every component, signal path, and computational step must be categorized by its failure modes (bit flips, timing violations, stuck-at-zero/one faults, intermittent transients), its *detection latency* (how many cycles before the fault is observable), and its *recovery mechanism* (can the system mask the fault, isolate it, or must it trigger a safe shutdown?). Unlike general-purpose computing, where Byzantine failure models and statistical availability metrics suffice, safety-critical systems demand *deterministic* fault detection and *bounded* recovery times measured in microseconds or milliseconds.

The second invariant is *traceability from requirement to object code*. Every safety requirement must map forward through architectural decisions, source code, test cases, and finally to executable binaries. Conversely, every line of generated machine code must be traceable backward to the requirement it satisfies. Breaks in this traceability chain—unrequired functionality, dead code paths, undocumented compiler optimizations—create audit exposure and hidden failure modes.

The third invariant is *defense in depth through redundancy and independence*. A single faulty sensor reading, corrupted register, or delayed interrupt should never directly cause system failure. Instead, independent monitoring layers (watchdogs, parity checkers, dual-channel comparison networks) detect anomalies and trigger controlled degradation or safe shutdown before user-facing hazard manifests. This philosophy of *fail-safe by design* requires architectural commitment: it cannot be retrofitted through testing alone.

The fourth invariant is *predictable timing under worst-case load*. Real-time safety-critical systems must guarantee response latencies even when all peripherals interrupt simultaneously, memory bandwidth saturates, or the CPU cache misses on every instruction fetch. Unlike throughput-optimized systems where average-case analysis suffices, safety systems must prove hard real-time deadlines through *worst-case execution time* (WCET) analysis, schedulability proof, and physical measurement under adversarial test conditions.

Finally, the fifth invariant is *certified coding discipline*. Unchecked C constructs—unbounded recursion, pointer arithmetic without range validation, implicit type conversions, undefined behavior on signed integer overflow—are actively forbidden in safety-critical codebases. Standards like MISRA C, CERT C, and DO-178C level requirements define a restricted subset of the language that eliminates entire classes of runtime failures before testing even begins.

## 2. Core Architecture & Mechanics

### Watchdog Timers: The Heartbeat of System Liveness

A watchdog timer is a hardware or firmware mechanism that monitors system liveness by requiring periodic "refresh" signals. If the main application fails to refresh the watchdog within a configurable time window (typically 10 ms to 100 ms for real-time systems), the watchdog triggers a controlled system reset, interrupts to a recovery handler, or signals a health alarm to external monitors.

Consider a cardiac pacemaker's main control loop. The pacemaker firmware executes a cyclic state machine: acquire ECG sensor samples, analyze rhythm, compute pacing pulse timing, command output drivers, then loop. If a watchdog refresh occurs only at the end of each successful loop iteration, the watchdog detects application stalls—whether caused by infinite loops in signal processing, memory corruption causing undefined jumps, or interrupt handler lockup—and can halt pacing output before tissue damage occurs.

The mechanical model of watchdog operation is straightforward. The watchdog maintains an internal counter, typically driven by a dedicated oscillator or a divided system clock. On each refresh command (writing a magic value to a watchdog control register), the counter resets to zero. The counter increments on each clock pulse. When the counter exceeds a programmed threshold (the *watchdog timeout window*), the watchdog asserts a reset signal or interrupt. The firmware must refresh the watchdog frequently enough that the counter never exceeds this threshold during normal operation.

The critical design decision is the timeout window duration. Set it too short (e.g., 5 ms) and benign delays—cache misses, interrupt latency, DMA backpressure—cause spurious resets. Set it too long (e.g., 1 second) and the system tolerates pathological stalls that could harm the application. The timeout window must be longer than the *maximum application loop latency* under worst-case load (all interrupts firing, all peripherals requesting service, cache thrashing) but short enough that user-facing hazards cannot develop before recovery activates.

Most microcontroller watchdog timers support multiple watchdog registers and refresh mechanisms. An STM32H7 series ARM Cortex-M7, for example, implements a watchdog with an independent 12-bit down-counter clocked by the LSI (Low-Speed Internal) oscillator running at approximately 32 kHz. The firmware writes 0xAAAA to the IWDG_KR (Watchdog Key Register) to refresh the counter; writing 0x5555 enables write access to the reload value; writing 0xCCCC starts the watchdog. The reload value (stored in IWDG_RLR, bits 11:0) sets the counter's maximum value. When the counter decrements to zero, the watchdog asserts an internal reset that propagates through the NVIC and forces a system reset.

The firmware structure around watchdog refresh must enforce *temporal isolation*. A common anti-pattern is to refresh the watchdog at the top of the main loop and then perform a long computation (e.g., FFT signal processing) without intermediate refresh. If that computation hangs due to a corrupted loop index, the watchdog detects the stall only after the timeout window expires—potentially too late. Instead, long-running computations should break into bounded subtasks, each with its own watchdog refresh. This transforms a single long window into many short windows, tightening the fault detection latency.

```c
/* Pseudo-code: Watchdog-aware main loop structure */
void watchdog_init(void) {
    /* Enable write access to watchdog registers */
    IWDG->KR = 0x5555;
    /* Set reload value: (32000 Hz / prescaler) * timeout_ms / 1000 */
    /* For 40 ms timeout with prescaler=8: reload = (32000/8)*40/1000 = 160 */
    IWDG->RLR = 160;
    IWDG->PR = 3;  /* prescaler = 8 */
    /* Disable write access and start watchdog */
    IWDG->KR = 0xCCCC;
}

void watchdog_refresh(void) {
    IWDG->KR = 0xAAAA;
}

int main(void) {
    watchdog_init();
    
    while (1) {
        /* Process one iteration of state machine */
        acquire_sensor_data();
        
        watchdog_refresh();  /* Refresh after each bounded task */
        
        analyze_signals();
        
        watchdog_refresh();
        
        compute_control_output();
        
        watchdog_refresh();
        
        command_actuators();
        
        watchdog_refresh();
    }
    return 0;
}
```

### Memory Protection Units: Boundary Enforcement

A Memory Protection Unit (MPU) is a hardware peripheral that enforces access control policies at the memory bus level. The MPU divides the address space into regions, each with configurable access permissions (read-only, read-write, execute-only, no-access). Attempts to violate these permissions—writing to a read-only region, reading from an execute-only code segment, accessing unmapped addresses—trigger a hardware fault exception.

The MPU serves two critical safety functions. First, it *isolates application tasks* from each other's memory, preventing a faulty task from corrupting another task's stack, heap, or global data. A buffer overflow in one task cannot silently corrupt the control variables of a different task; instead, the MPU detects the access violation and delivers a fault exception, which can trigger diagnostics or graceful degradation. Second, the MPU *prevents common software vulnerabilities*: a return-oriented programming (ROP) attack attempting to execute data (shellcode stored in a heap buffer) fails because the MPU denies execute permissions on heap regions.

ARM Cortex-M microcontrollers (M3 and later) integrate an MPU with eight regions on M3/M4 variants and sixteen regions on M7/M33 variants. Each region is defined by a base address register and a size/attribute register. The size must be a power of 2 (minimum 32 bytes). Each region specifies whether the region is for code (XN=0, execute permitted) or data (XN=1, execute never), and access permissions as a three-bit code: 000 (no access), 001 (privileged read-write, user no-access), 010 (privileged and user read-write), 011 (privileged read-write, user read-only), 100 (privileged execute, user no-access), 101 (privileged read-execute, user no-access), 110 (privileged read-write-execute, user read-execute), and so forth.

The MPU check occurs on every memory access (fetch, load, store) at the memory management unit (MMU) stage of the CPU pipeline. If an access violates the programmed policy, the CPU raises a *MemManage* fault exception, vectoring control to the MemManage_Handler interrupt handler. This exception carries diagnostic information in the CFSR (Configurable Fault Status Register), which indicates whether the violation was an instruction access, data access, or attempted access during exception handling (nested faults are particularly dangerous and require special handling).

```c
/* ARM Cortex-M4 MPU initialization example */

/* Define MPU region structure */
typedef struct {
    uint32_t base_addr;
    uint32_t size_bits;     /* 5 = 32B, 6 = 64B, ..., 31 = 4GB */
    uint8_t access_code;    /* 3-bit access permission code */
    uint8_t cacheable;      /* WT (0) or WB (1) */
} mpu_region_t;

void mpu_init(void) {
    /* Region 0: Flash (code + read-only data) - Privileged R/X, User R/X */
    MPU->RBAR = 0x08000000;  /* Base address */
    MPU->RASR = (1 << 30)      /* Enable this region */
             | (30 << 1)       /* Size = 2^31 = 2GB (covers all flash) */
             | (0b110 << 24)   /* Access: PrU R/X, U R/X */
             | (1 << 28);      /* Cacheable */
    
    /* Region 1: RAM (data + stack) - Privileged R/W, User R/W */
    MPU->RBAR = 0x20000000;
    MPU->RASR = (1 << 30)
             | (15 << 1)       /* Size = 2^16 = 64KB */
             | (0b011 << 24)   /* Access: Pr R/W, U R/W */
             | (1 << 28);
    
    /* Region 2: Peripheral registers (MMIO) - Privileged R/W, no cache */
    MPU->RBAR = 0x40000000;
    MPU->RASR = (1 << 30)
             | (27 << 1)       /* Size = 2^28 = 256MB */
             | (0b001 << 24)   /* Access: Pr R/W only */
             | (0 << 28);      /* Not cacheable */
    
    /* Enable MPU and set default handler for violations */
    MPU->CTRL = (1 << 0)       /* ENABLE */
              | (1 << 2);      /* PRIVDEFENA: privileged code accesses
                                  unmapped regions allowed by default */
    
    __DSB();  /* Data Synchronization Barrier */
    __ISB();  /* Instruction Synchronization Barrier */
}

void MemManage_Handler(void) {
    uint32_t cfsr = SCB->CFSR;
    uint32_t mmfsr = (cfsr >> 0) & 0xFF;  /* Memory Management Fault Status */
    
    if (mmfsr & 0x01) {
        /* Instruction access violation */
        log_error("MPU Fault: Instruction access to protected region\n");
    }
    if (mmfsr & 0x02) {
        /* Data access violation */
        log_error("MPU Fault: Data access to protected region at 0x%08X\n",
                  SCB->MMFAR);  /* Faulting address */
    }
    if (mmfsr & 0x08) {
        /* MUNSTKERR: access during unstacking */
        log_error("MPU Fault: Stack frame corruption detected\n");
    }
    
    /* Trigger safe shutdown or recovery */
    system_safe_shutdown();
}
```

The MPU is most effective when combined with an RTOS that enforces task isolation. Each task (or thread) receives its own MPU region configuration when scheduled; the context switch handler updates the MPU registers to reflect the new task's memory layout. This requires the RTOS kernel to operate in privileged mode (to modify MPU registers) while user tasks operate in unprivileged mode, unable to directly reconfigure memory protections.

### Stack Sentinel Patterns and Canary Values

While the MPU provides hardware-enforced memory protection, stack overflow—the most common memory corruption vulnerability in embedded systems—often occurs within a single task's stack region. By the time the MPU detects a stack overflow (access beyond the stack region), the damage may be irreversible: return addresses overwritten, saved registers corrupted, frame pointers modified.

A complementary software technique is the *stack canary*: a known pattern written below the stack pointer at task initialization. During context switches or periodic checks, the firmware verifies that the canary is still intact. If the canary has been overwritten, a stack overflow is detected before the overwritten return address is executed, preventing control flow hijacking.

The canary pattern is typically a random 32-bit or 64-bit value generated at boot time and stored in read-only memory or protected registers. The pattern should be difficult to predict (random) and unlikely to appear through coincidence. Common choices are 0xDEADBEEF (memorable but predictable) or cryptographically random values (preferred for safety-critical systems).

```c
/* Stack canary initialization and checking */

#define CANARY_VALUE 0x0DEADBEEF

struct task_control_block {
    uint32_t *stack_base;
    uint32_t stack_size;
    uint32_t *canary_location;  /* Address of canary value on stack */
};

void task_init(struct task_control_block *tcb, uint32_t stack_size) {
    tcb->stack_base = malloc(stack_size);
    tcb->stack_size = stack_size;
    tcb->canary_location = tcb->stack_base;  /* Canary at bottom of stack */
    *tcb->canary_location = CANARY_VALUE;
}

int check_stack_canary(struct task_control_block *tcb) {
    if (*tcb->canary_location != CANARY_VALUE) {
        log_error("Stack overflow detected in task\n");
        return -1;  /* Stack corruption */
    }
    return 0;  /* Stack intact */
}

void context_switch(struct task_control_block *from, 
                    struct task_control_block *to) {
    if (check_stack_canary(from) != 0) {
        /* Previous task corrupted its stack */
        system_safe_shutdown();
    }
    /* Save registers of 'from' task, restore registers of 'to' task */
    /* Update MPU regions if using per-task memory protection */
}
```

### Dual-Channel Monitoring and Voter Networks

For systems where even a single fault in the monitoring layer could cause failure, *dual-channel* (or tri-channel) comparison networks provide independent fault detection. The core idea is that a critical computation is performed twice by independent hardware or software instances, and their results are continuously compared. Divergence indicates a fault in one channel.

An automotive brake-by-wire system exemplifies this pattern. The brake pedal position sensor is read by two independent sensor acquisition paths (different analog-to-digital converters, different CPU cores, or even different microcontrollers). The two readings are compared; if they differ by more than a small tolerance (e.g., 1%), the system enters a failsafe mode (regenerative braking reduction, eventual emergency brake actuation). This ensures that a single sensor fault or ADC malfunction cannot cause uncontrolled braking force.

The comparison network must itself be redundant and fault-tolerant. If the comparison logic is implemented in a single CPU core, a fault in that core could prevent divergence detection. Better architectures use:

1. **Diverse hardware**: Different microcontroller families, architectures, and vendors for redundant channels. A fault specific to one CPU family (e.g., a silicon errata affecting ARM Cortex-M4 branch prediction) does not affect the other channel.

2. **Diverse software**: Redundant channels run different implementations of the same algorithm (written by different teams, using different compilers, different numerical approaches). This minimizes the probability that both channels fail on the same input.

3. **Separate power supplies**: Each channel has its own voltage regulator and power distribution network, isolated from the others. A power supply fault affecting one channel does not cascade to the others.

4. **Voter isolation**: The voting network (comparison and decision logic) is implemented on a *separate* processor or FPGA, not on either of the primary channels. This prevents a fault on a primary channel from silencing the voter.

A simplified three-channel voter (majority voting) for a safety-critical measurement looks like this:

```c
/* Three-channel majority voter for safety-critical sensor fusion */

typedef struct {
    int32_t channel_a;
    int32_t channel_b;
    int32_t channel_c;
    int32_t voter_output;
    uint8_t fault_flags;  /* Bit 0: A fault, Bit 1: B fault, Bit 2: C fault */
} voted_sensor_t;

#define SENSOR_TOLERANCE 5  /* Maximum acceptable divergence */

void three_channel_vote(voted_sensor_t *sensor) {
    int32_t ab_diff = abs(sensor->channel_a - sensor->channel_b);
    int32_t bc_diff = abs(sensor->channel_b - sensor->channel_c);
    int32_t ac_diff = abs(sensor->channel_a - sensor->channel_c);
    
    sensor->fault_flags = 0;
    
    /* Determine which channels agree */
    if (ab_diff > SENSOR_TOLERANCE) {
        sensor->fault_flags |= 0x03;  /* A and B disagree */
    }
    if (bc_diff > SENSOR_TOLERANCE) {
        sensor->fault_flags |= 0x06;  /* B and C disagree */
    }
    if (ac_diff > SENSOR_TOLERANCE) {
        sensor->fault_flags |= 0x05;  /* A and C disagree */
    }
    
    /* Majority voting: which two channels agree? */
    if ((sensor->fault_flags & 0x03) == 0) {
        /* A and B agree, use their average */
        sensor->voter_output = (sensor->channel_a + sensor->channel_b) / 2;
    } else if ((sensor->fault_flags & 0x06) == 0) {
        /* B and C agree, use their average */
        sensor->voter_output = (sensor->channel_b + sensor->channel_c) / 2;
    } else if ((sensor->fault_flags & 0x05) == 0) {
        /* A and C agree, use their average */
        sensor->voter_output = (sensor->channel_a + sensor->channel_c) / 2;
    } else {
        /* All three channels disagree: data invalid, trigger fault handler */
        sensor->voter_output = 0;
        sensor->fault_flags |= 0x80;  /* Triple fault flag */
    }
}
```

### Exception Handling and Recovery Chains

Safety-critical systems must handle exceptions—faults, interrupts, error conditions—in a predictable, deterministic manner. Unlike application-level exception handling (try-catch blocks), hardware exceptions (CPU faults, peripheral errors, watchdog timeouts) demand immediate, bounded response with clear escalation paths.

ARM Cortex-M processors define seven fault exception types, each with its own exception handler and severity:

1. **HardFault**: Catch-all fault for any unhandled exception or failure in the exception handling system itself. The HardFault handler is the last line of defense; if it exits normally, the system hangs.

2. **MemManage**: Memory protection violations (MPU faults, attempted fetch from invalid addresses). Indicates corruption or invalid pointer dereference.

3. **BusFault**: Bus protocol errors (invalid memory access through AHB interconnect, parity errors on external memory). Often indicates hardware failure.

4. **UsageFault**: Illegal instruction execution, divide-by-zero, unaligned memory access on systems that fault on misalignment.

5. **SecureFault**: (ARMv8-M with TrustZone): Violations of security boundary (attempted access to secure memory from non-secure context).

6. **DebugMonitor**: (When attached to debugger) Breakpoint or watchpoint hit.

Each exception handler must follow a *recovery chain* pattern: detect the fault, log diagnostic information, attempt recovery if possible, or escalate to a safe shutdown if recovery is not possible.

```c
/* Exception handler recovery chain for ARM Cortex-M */

volatile struct {
    uint32_t fault_count;
    uint32_t last_fault_type;
    uint32_t fault_address;
} system_fault_log;

void HardFault_Handler(void) {
    /* HardFault: system is in critical condition */
    system_fault_log.fault_count++;
    system_fault_log.last_fault_type = FAULT_HARD;
    
    /* Log diagnostic information before shutdown */
    log_all_registers();
    log_stack_trace();
    
    /* Attempt restart via watchdog reset if possible */
    NVIC_SystemReset();  /* Request system reset */
    
    /* If reset fails, spin indefinitely */
    while (1) {
        __WFE();  /* Wait for event, minimizes power consumption */
    }
}

void MemManage_Handler(void) {
    uint32_t cfsr = SCB->CFSR;
    uint32_t mmfsr = (cfsr >> 0) & 0xFF;
    uint32_t fault_addr = SCB->MMFAR;
    
    system_fault_log.fault_count++;
    system_fault_log.last_fault_type = FAULT_MEMMANAGE;
    system_fault_log.fault_address = fault_addr;
    
    /* Recovery strategy 1: If fault is in task stack, kill that task */
    if (is_stack_violation(fault_addr)) {
        kill_current_task();
        return;  /* Let context switch to next task */
    }
    
    /* Recovery strategy 2: If fault is in dynamically allocated memory,
       attempt to free and reallocate */
    if (is_heap_violation(fault_addr)) {
        heap_emergency_recover();
        return;
    }
    
    /* Recovery strategy 3: If fault is in peripheral MMIO, log and
       disable that peripheral */
    if (is_peripheral_violation(fault_addr)) {
        log_error("Peripheral fault at 0x%08X\n", fault_addr);
        disable_faulty_peripheral(fault_addr);
        return;
    }
    
    /* No recovery possible: escalate to HardFault */
    SCB->ICSR |= SCB_ICSR_PENDSTSET_Msk;  /* Pend SysTick (or escalate) */
}

void BusFault_Handler(void) {
    system_fault_log.fault_count++;
    system_fault_log.last_fault_type = FAULT_BUS;
    
    /* Bus faults typically indicate hardware failure or corruption
       of external memory. Recovery options are limited. */
    log_error("Bus fault detected\n");
    
    /* If on embedded multi-core system, attempt to isolate this core
       and continue on other cores */
    if (system_is_multi_core()) {
        isolate_this_core();
        return;
    }
    
    /* Single-core system: escalate to safe shutdown */
    system_safe_shutdown();
}

int is_stack_violation(uint32_t addr) {
    struct task_control_block *tcb = get_current_task();
    return (addr >= tcb->stack_base && 
            addr < tcb->stack_base + tcb->stack_size);
}
```

## 3. High-Performance Optimization & Failure Modes

### Worst-Case Execution Time Analysis

Real-time safety-critical systems must guarantee that every task completes within its deadline, even under worst-case conditions (maximum interrupt load, cache misses on every access, memory contention). The *Worst-Case Execution Time* (WCET) is the longest possible execution time for a task measured from entry to exit, taking into account all possible code paths and hardware effects.

WCET analysis is fundamentally different from performance profiling (average-case or typical-case execution time). A task might execute in 5 µs on average but 50 µs in the worst case due to cache misses and interrupt preemption. Safety-critical schedulability proof demands
