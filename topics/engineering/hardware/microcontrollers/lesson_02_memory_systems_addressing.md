# Lesson 2: Memory Systems, Addressing Modes, Interrupts

## 1. First-Principles Intuition & Invariants

Memory is the lifeblood of any microcontroller system. Unlike general-purpose computers where memory access is largely an abstraction hidden behind caches and virtual address translation, embedded systems require intimate knowledge of physical memory layout, access timing, and the consequences of every load and store operation. This lesson establishes the fundamental relationship between the CPU, address space, and the physical substrate that stores both code and data.

At the heart of microcontroller design lies a profound constraint: silicon real estate is precious. A modern microcontroller might pack an ARM Cortex-M4 processor core, 256 KB of Flash memory, 64 KB of SRAM, peripheral control registers, and an interrupt controller onto a die smaller than a postage stamp. This compression forces engineers to make deliberate trade-offs between memory size, access speed, power consumption, and cost that simply do not exist in desktop computing. The address space—the range of addresses the CPU can reference—must accommodate code storage, runtime data, stack frames, peripheral registers, and interrupt vector tables, all competing for a limited namespace.

The microcontroller's memory architecture fundamentally differs from that of a desktop processor in one critical way: *everything is memory-mapped*. There is no separate I/O port space, no privileged I/O instructions like x86's `IN` and `OUT`. Instead, peripheral control registers occupy addresses within the CPU's addressable space. Writing to address `0x40004000` might configure a GPIO pin; writing to `0x40003008` might trigger a timer interrupt. This unification simplifies hardware design but demands that firmware engineers understand the exact layout of the address space and the register definitions within it.

To master microcontroller systems, you must internalize three core invariants. First, *memory is heterogeneous*. Flash memory is non-volatile and persistent across power cycles, but writes are slow (typically milliseconds) and limited in cycle count. SRAM is volatile, fast, and ideal for runtime state, but expensive in area. EEPROM is non-volatile and byte-erasable, but even slower than Flash. Each type serves a specific purpose, and misusing them leads to performance collapse or data corruption. Second, *address space is zero-sum*. Every byte allocated to one purpose is unavailable for another. A peripheral that requires 256 bytes of memory-mapped registers consumes address space that cannot be used for code or data. Third, *timing is deterministic and measurable*. Unlike general-purpose CPUs where cache misses introduce variable latency, microcontroller memory access timing is predictable. A read from SRAM takes a fixed number of cycles; a write to Flash takes a deterministic amount of time (though much longer). This determinism is essential for real-time systems where hard deadlines must never be missed.

Addressing modes—the syntactic and semantic mechanisms by which the CPU specifies which memory location to access—are not merely convenience features. They directly influence code density, execution latency, and power consumption. In ARM Thumb-2 instruction set used by ARM Cortex-M series processors, an instruction encoding choice between direct addressing and indirect addressing with index can change code size by 50% and alter execution time by one or more cycles. For embedded systems where every byte of Flash and every cycle of execution matters, understanding addressing modes is as fundamental as understanding opcodes themselves.

Interrupts represent a second axis of complexity orthogonal to memory addressing. An interrupt is an asynchronous event—a GPIO pin changing state, a timer counting to zero, a serial port receiving data—that forces the CPU to abandon its current execution path and service the event. The microcontroller must preserve the entire execution context (registers, program counter, status flags), jump to an interrupt service routine (ISR), execute the ISR, restore the saved context, and resume the original execution stream. All of this must happen transparently and with minimal latency, or real-time guarantees evaporate. The interrupt vector table is the metadata structure that maps interrupt numbers to ISR addresses; the interrupt priority controller determines which interrupt fires first when multiple events occur simultaneously.

## 2. Core Architecture & Mechanics

### Memory Hierarchy and Physical Organization

Modern microcontrollers employ a simplified memory hierarchy compared to general-purpose processors. There are typically no L1, L2, or L3 caches. Instead, the memory subsystem presents a flat, single-level view: fast SRAM for runtime access, slow Flash for code and constant data, and optional EEPROM for configuration or telemetry data that must survive power loss. Understanding the address space layout is the first concrete task.

Consider a representative ARM Cortex-M4 microcontroller with a 32-bit address space. The address range spans from `0x00000000` to `0xFFFFFFFF`, a 4 GB namespace. However, only a fraction of this is physically implemented. A typical layout might allocate the first 256 KB for Flash memory (starting at `0x00000000`), the next 64 KB for SRAM (starting at `0x20000000`), and the remaining space for peripheral control registers and reserved regions. This non-contiguous mapping reflects the physical organization: Flash is slower but non-volatile and suited for code; SRAM is fast but volatile and suited for runtime state.

Flash memory operates fundamentally differently from SRAM or even conventional disk storage. A microcontroller's Flash array is organized into pages (typically 2 KB to 4 KB) and sectors (often 64 KB). Individual bit cells cannot be cleared one at a time; the entire page must be erased (all bits set to 1) before writing. Writing involves charging floating-gate transistors to store charge in a specific pattern that represents data. Reading is a matter of sensing the charge state. From a firmware perspective, this means a single write operation might require erasing a 2 KB or 4 KB page containing code or constant data, then reprogramming the entire page with the new values. A naive flash write that occurs every few milliseconds will exhaust the chip's rated erase cycles (typically 10,000 to 100,000 for single-level cell Flash) within days. Production firmware must manage Flash writes carefully, batching updates and distributing them across time.

SRAM, by contrast, presents a conventional read-write interface. Each address can be read or written in a single cycle (typically 1-4 cycles depending on the microcontroller's clock speed and memory interface). SRAM is where the stack lives, where local variables are stored, and where interrupt contexts are saved. Because SRAM is volatile, all data stored there is lost on power loss; initialization code must rebuild any necessary state from Flash constants or EEPROM.

EEPROM occupies a middle ground. Unlike Flash, EEPROM can be written byte-by-byte without erasing entire sectors. A write operation programs a single byte by charging a floating-gate transistor, a process that typically takes 3-10 milliseconds on microcontrollers. This slower write speed is acceptable for application settings or calibration data that changes infrequently. The erase cycle count is often higher than Flash (100,000 to 1,000,000 cycles), making EEPROM suitable for data that must be updated over the lifetime of the product.

The address space layout reflects these technologies and their roles. A representative mapping on an ARM Cortex-M4 with 256 KB of Flash and 64 KB of SRAM might look like this:

```
Address Range         | Contents              | Size
--------------------|------------------------|----------
0x00000000–0x0003FFFF | Flash Memory          | 256 KB
0x04000000–0x0400FFFF | EEPROM (if present)   | 64 KB
0x20000000–0x2000FFFF | SRAM (working RAM)    | 64 KB
0x40000000–0x400DFFFF | Peripheral Registers  | ~900 KB
0xE0000000–0xE00FFFFF | ARM Cortex-M Private  | 1 MB
                      | Peripheral Region     |
```

The ARM Cortex-M private peripheral region (the range starting at `0xE0000000`) contains the NVIC (Nested Vectored Interrupt Controller), System Tick Timer, and debug components. These are defined by the ARM architecture and present on every Cortex-M processor, though a vendor may locate vendor-specific peripherals elsewhere. This standardization is one reason ARM processors dominate the microcontroller market; a developer's knowledge of the address space and interrupt architecture transfers across many different chips from different manufacturers.

### Memory-Mapped I/O and Peripheral Access

Memory-mapped I/O is the architectural pattern by which the microcontroller integrates peripherals into the address space. Instead of a GPIO pin controller occupying a special I/O port namespace (as in x86 with `IN`/`OUT` instructions), the GPIO controller occupies a region of memory addresses. Writing a value to `0x4000_4400` might set a GPIO output high; reading from `0x4000_4404` might return the current state of GPIO input pins.

Peripheral registers are typically organized into a structure, with each register at a fixed offset from a base address. For example, an UART peripheral might be mapped starting at `0x4000_8000`, with control registers at fixed offsets:

```
Base Address: 0x4000_8000 (UART0)
+0x00: DATA Register (read/write character data)
+0x04: STATUS Register (read-only flags)
+0x08: CONTROL Register (write-only configuration)
+0x0C: BAUD Register (write-only baud rate divider)
```

From firmware perspective, configuring the UART involves writing to these addresses in a specific sequence. To set up the UART for 9600 baud with 8 data bits and 1 stop bit, the code might resemble:

```c
// Define base address
#define UART0_BASE  0x40008000

// Define register offsets
#define UART_DATA   (*(volatile uint32_t *)(UART0_BASE + 0x00))
#define UART_STATUS (*(volatile uint32_t *)(UART0_BASE + 0x04))
#define UART_CTRL   (*(volatile uint32_t *)(UART0_BASE + 0x08))
#define UART_BAUD   (*(volatile uint32_t *)(UART0_BASE + 0x0C))

void uart_init(void) {
    // Set baud rate divisor for 9600 baud at 48 MHz clock
    // Divisor = Clock / (16 * Baud) = 48000000 / (16 * 9600) = 312
    UART_BAUD = 312;
    
    // Configure: 8 data bits, 1 stop bit, no parity, enable TX/RX
    UART_CTRL = 0x30;  // Bits 4-5 set: enable TX and RX
    
    // Wait for status to indicate ready
    while (!(UART_STATUS & 0x02)) {
        // Poll until TX ready
    }
}

void uart_putchar(char c) {
    // Write character to data register; hardware transmits it
    UART_DATA = c;
    
    // Wait for transmission to complete
    while (!(UART_STATUS & 0x02)) {
        // Poll TX complete flag
    }
}
```

The `volatile` keyword is critical in memory-mapped I/O. Without it, a C compiler might aggressively optimize away consecutive reads from the same address, assuming the value never changes. In reality, a hardware peripheral might change the value autonomously (e.g., receiving a character), so each read must actually occur.

Memory-mapped I/O introduces a subtle but profound constraint: *peripheral registers are not cached*. When the CPU reads from `0x4000_8004` (the UART status register), the access must actually reach the peripheral hardware, not a cached copy. On most microcontrollers, peripherals are placed in a memory region marked as uncacheable and unbufferable, ensuring that reads and writes hit the hardware immediately. This deterministic behavior is essential for real-time I/O but means that a naive sequence of peripheral register accesses might stall the CPU while waiting for hardware acknowledgment.

### Addressing Modes: The Language of Memory Access

CPU instruction sets provide multiple addressing modes—syntactic mechanisms for specifying operands—to balance code density, execution latency, and programmability. ARM's Thumb-2 instruction set (used by Cortex-M processors) employs several key modes that firmware engineers must understand and exploit.

**Immediate Addressing** is the simplest: the operand is encoded directly in the instruction. For example, `MOV R0, #0x42` loads the constant `0x42` into register R0. In Thumb-2, immediate values are limited to an 8-bit value rotated by an even number of bits, a constraint driven by instruction encoding space. This restriction means not all constants can be encoded directly; loading an arbitrary 32-bit constant might require two instructions:

```
MOVW R0, #0x1234     ; Load lower 16 bits
MOVT R0, #0x5678     ; Load upper 16 bits (R0 now contains 0x56781234)
```

The MOVW (move wide) and MOVT (move top) instructions are essential for loading full 32-bit addresses into registers.

**Register Addressing** specifies an operand in a CPU register. For instance, `ADD R0, R1` adds R1 to R0. This is the fastest mode because no memory access occurs; the operand is already in the processor.

**Direct Addressing** (also called **PC-Relative Addressing** in some contexts) encodes an address directly in the instruction or derives it from the program counter. For example, `LDR R0, [PC, #8]` loads a 32-bit value from 8 bytes after the current instruction. This mode is commonly used to load constants stored in code memory immediately following a function:

```
    LDR R0, [PC, #12]     ; Load constant from address PC+12+8
    BL  some_function
    ; ... more code ...
    DCD 0x12345678         ; Constant data at this address
```

PC-relative addressing reduces code relocation complexity and improves position independence.

**Indirect Addressing** (also called **Register-Indirect**) specifies that the operand address is stored in a register. `LDR R0, [R1]` loads a 32-bit value from the address in R1. This is fundamental for accessing arrays, structures, and dynamically allocated memory:

```c
// If R1 contains the address of an array, [R1] fetches the first element
int *array_ptr = (int *)0x20000000;  // Pointer to array in SRAM
int value = array_ptr[0];  // LDR R0, [R1] where R1 holds the address
```

**Indexed Addressing** combines a base register with an offset. `LDR R0, [R1, #4]` loads a value from the address (R1 + 4). The offset can be an immediate value or another register:

```
LDR R0, [R1, #4]      ; Offset by constant (address = R1 + 4)
LDR R0, [R1, R2]      ; Offset by register (address = R1 + R2)
LDR R0, [R1, R2, LSL #2]  ; Scaled by register (address = R1 + (R2 << 2))
```

Scaled indexing is particularly valuable for array access. If R1 points to an array of 32-bit integers and R2 contains an index, `LDR R0, [R1, R2, LSL #2]` fetches the element at index R2 (the scale factor 2 accounts for 4-byte integers: 2^2 = 4).

**Auto-Increment and Auto-Decrement Addressing** modifies the base register after the memory access, enabling efficient iteration:

```
LDR R0, [R1], #4      ; Load from R1, then increment R1 by 4
LDR R0, [R1, #-4]!    ; Decrement R1 by 4, then load from new R1
```

The post-indexed form `[R1], #4` loads from R1 and then increments; the pre-indexed form `[R1, #4]!` increments first (or decrements if the offset is negative), then loads. These modes are essential for tight loops that traverse arrays or stacks.

The choice of addressing mode directly impacts performance. On a Cortex-M4 running at 100 MHz, different modes have measurable latencies:

- Register addressing: 1 cycle
- Immediate (already in instruction): 1 cycle
- Direct memory access (SRAM): 1-2 cycles
- Peripheral register access: 2-3 cycles (due to the peripheral interface latency)
- Indexed addressing with register offset: 1-2 cycles
- Scaled indexed addressing: 1-2 cycles

For a function that must iterate over an array of 10,000 elements, the choice between auto-increment addressing and manual index arithmetic can determine whether the loop completes in microseconds or tens of microseconds. In a real-time system, that difference might mean meeting a deadline or missing it entirely.

### The Stack and Context Management

The stack is a contiguous region of SRAM managed by the Stack Pointer (SP, also R13 in ARM) register. The stack grows downward in address space (from high addresses toward low addresses) on most ARM microcontrollers. When a function is called or an interrupt fires, the CPU pushes register values onto the stack; when the function returns, it pops them off.

Understanding stack layout is critical for debugging and optimizing real-time systems. Consider a simple function call sequence:

```c
void main(void) {
    int x = 42;         // Local variable
    int y = compute(x); // Function call
}

int compute(int arg) {
    int local = arg * 2;
    return local;
}
```

When `main` calls `compute`, the ARM calling convention (AArch32 for 32-bit ARM) dictates that `x` (the argument) is passed in register R0, and the return address is stored in the Link Register (LR, R14). Inside `compute`, the function might save callee-saved registers (those it intends to modify) by pushing them onto the stack:

```
[Before call]  SP -> [Top of main's local variables]
[At function entry] PUSH {R4-R11, LR}  ; Save callee-saved regs and return address
               SP -> [Saved R4]
               SP+4 -> [Saved R5]
               ...
               SP+36 -> [Saved LR]
[Inside function] Allocate local variables on stack
               SP -> [local variable "local"]
```

When `compute` returns, the sequence is reversed:

```
               POP {R4-R11, PC}  ; Restore saved registers and jump to return address
               SP -> [Previous SP position]
```

The `POP {R4-R11, PC}` instruction restores registers and branches to the address loaded into the program counter from the stack. This single instruction replaces a separate return instruction, reducing code size and latency.

Stack overflow is a silent killer in embedded systems. If the stack grows uncontrollably (due to unbounded recursion or allocation of excessively large local arrays), it will overwrite SRAM containing critical data, heap memory, or peripheral state. Many microcontrollers include a stack overflow detection mechanism in the form of a stack limit register, though enabling this protection costs a small amount of runtime overhead.

### Interrupt Vector Table and NVIC Architecture

The Interrupt Vector Table (IVT) is a critical metadata structure residing at the base of Flash memory (address `0x00000000` on most ARM Cortex-M chips). Each entry in the IVT is a 32-bit address pointing to an interrupt service routine. The IVT serves two purposes: it defines which ISR executes for each interrupt type, and on ARM Cortex-M, it also contains the initial Stack Pointer and Reset vector at the very beginning.

A typical ARM Cortex-M4 IVT layout begins with a reserved region and standard ARM exceptions, followed by vendor-specific interrupts:

```
Offset  | Vector Name              | Address / Meaning
--------|--------------------------|----------------------------------
0x00    | Initial SP               | Stack pointer value at startup
0x04    | Reset                    | Address of reset handler
0x08    | Non-Maskable Int (NMI)   | Address of NMI ISR
0x0C    | Hard Fault               | Address of hard fault handler
0x10    | Memory Management Fault  | MMU fault handler
0x14    | Bus Fault                | Bus fault handler
0x18    | Usage Fault              | Invalid instruction fault handler
0x1C–0x2C | Reserved               | (ARM reserved)
0x30    | SVC (Supervisor Call)    | Supervisor call handler
0x34    | Debug Monitor            | Debug-related handler
0x38    | Reserved                 | (ARM reserved)
0x3C    | PendSV                   | Pending Service Call handler
0x40    | System Tick              | System Tick Timer ISR
0x44    | UART0 Interrupt          | Vendor-defined interrupt 0
0x48    | GPIO Interrupt           | Vendor-defined interrupt 1
...     | ...                      | ...
```

At startup, the ARM Cortex-M hardware automatically reads the first two entries from the IVT: the initial Stack Pointer value is loaded into SP, and the Reset vector is fetched and executed. This hardwired bootstrap sequence means the IVT must always reside at `0x00000000` (or a remapped address if the microcontroller supports IVT relocation).

Defining the IVT in C code requires careful use of compiler directives and section attributes. A typical approach uses a linker section named `.isr_vector`:

```c
// In vector_table.c
typedef void (*isr_t)(void);

// ISR declarations (defined elsewhere)
extern void Reset_Handler(void);
extern void NMI_Handler(void);
extern void HardFault_Handler(void);
extern void UART0_Handler(void);
extern void GPIO_Handler(void);
extern void Default_Handler(void);

// Place in .isr_vector section at start of Flash
__attribute__((section(".isr_vector")))
const isr_t vector_table[] = {
    (isr_t)0x20010000,           // Initial Stack Pointer (SRAM top)
    Reset_Handler,               // Reset
    NMI_Handler,                 // NMI
    HardFault_Handler,           // Hard Fault
    0,                           // Memory Management (not used)
    0,                           // Bus Fault (not used)
    0,                           // Usage Fault (not used)
    0, 0, 0, 0,                  // Reserved
    Default_Handler,             // SVC
    Default_Handler,             // Debug Monitor
    0,                           // Reserved
    Default_Handler,             // PendSV
    Default_Handler,             // SysTick
    UART0_Handler,               // UART0 (interrupt 16)
    GPIO_Handler,                // GPIO (interrupt 17)
    // ... more vendor interrupts
};
```

The linker script ensures this array is placed at the very start of Flash:

```
SECTIONS {
    .flash_start 0x00000000 : {
        KEEP(*(.isr_vector))
        *(.text)
        *(.data)
    } > FLASH
}
```

The Nested Vectored Interrupt Controller (NVIC) is a hardware component that manages interrupt prioritization, masking, and dispatch. Unlike simpler microcontroller designs where interrupts are serviced in a fixed order, the NVIC allows programmers to assign priority levels to each interrupt. On a Cortex-M4, priorities typically range from 0 (highest) to 255 (lowest), though many implementations use only a subset (e.g., 0–15 on a 4-bit priority field). When multiple interrupts occur simultaneously, the NVIC services the highest-priority interrupt first.

The NVIC registers are memory-mapped in the private peripheral region starting at `0xE000_E000`. Critical registers include:

- **ISER (Interrupt Set-Enable Register)**: Writing a 1 to bit N enables interrupt N. Reading returns the current enable state.
- **ICER (Interrupt Clear-Enable Register)**: Writing a 1 to bit N disables interrupt N.
- **ISPR (Interrupt Set-Pending Register)**: Writing a 1 to bit N marks interrupt N as pending (queued for service).
- **ICPR (Interrupt Clear-Pending Register)**: Writing a 1 to bit N clears the pending flag on interrupt N.
- **IPR (Interrupt Priority Register)**: Sets the priority level (0–15 or 0–255) for each interrupt. Four interrupts share each 32-bit IPR register, with each interrupt's priority occupying 4 bits (in the upper nibble of the byte).

Configuring the NVIC to enable and prioritize interrupts is a fundamental task. To enable the UART0 interrupt (assuming it is interrupt number 16 in the chip's design) and set its priority to 2:

```c
#define NVIC_BASE    0xE000E000
#define NVIC_ISER    ((volatile uint32_t *)(NVIC_BASE + 0x100))
#define NVIC_IPR     ((volatile uint8_t *)(NVIC_BASE + 0x300))

void enable_uart0_interrupt(void) {
    // Enable interrupt 16 (UART0)
    // ISER[0] controls interrupts 0–31; interrupt 16 is bit 16 of ISER[0]
    NVIC_ISER[0] |= (1 << 16);
    
    // Set priority to 2
    // IPR[16] is IPR[16/4] = IPR[4], and the priority field is bits [7:4] of that byte
    // On ARM Cortex-M4, priority is right-aligned in the upper 4 bits of the byte
    NVIC_IPR[16] = (2 << 4);  // Shift left by 4 to place in upper nibble
}
```

### Context Switching and Interrupt Latency

When an interrupt fires, the CPU must suspend its current execution, save critical state (registers and program counter), execute the ISR, restore the saved state, and resume execution at the point of interruption.

This context-switch overhead—termed **interrupt latency**—consists of three phases: entry latency (the time to recognize the interrupt, stack registers, and fetch the ISR vector), execution latency (the ISR's own runtime), and exit latency (unstacking registers and resuming the interrupted code). On ARM Cortex-M processors, hardware automatically stacks eight core registers (R0–R3, R12, LR, PC, and xPSR) in a single atomic bus transaction, achieving entry latencies as low as 12 clock cycles. Tail-chaining optimization further reduces overhead when multiple interrupts are pending: if a second interrupt arrives while the first ISR is completing, the processor skips the unstack-restack cycle and directly vectors to the new ISR, reducing back-to-back interrupt overhead to near-zero. Developers must balance ISR complexity against latency budgets; long-running ISRs delay lower-priority interrupts and increase jitter in time-critical tasks. Best practice mandates minimal ISR work—set a flag, enqueue data, trigger a deferred task—and delegate heavy processing to main-loop or RTOS task contexts where preemption and scheduling policies apply.

---

## Summary & Verification Matrix

| **Concept** | **Governing Invariant** | **Core Mechanism** | **Diagnostic Criterion** |
|-------------|-------------------------|-------------------|--------------------------|
| **Memory Architecture** | Harvard separation prevents instruction/data conflicts; Von Neumann unifies address space | Flash for code (read-mostly), SRAM for data/stack (read-write), memory-mapped I/O unifies peripheral access | Check linker map for section placement; verify stack does not overwrite `.bss`/`.data`; confirm peripheral base addresses match datasheet |
| **Addressing Modes** | Effective address = f(instruction operands, registers, immediates); mode determines memory access pattern | Immediate (constant in opcode), direct (absolute address), indirect (register holds address), indexed/offset (base + displacement) | Disassemble critical code paths; verify pointer arithmetic correctness; profile cache/bus utilization for indirect access patterns |
| **Interrupt Priority & Preemption** | Lower priority number = higher urgency; preemption allowed only when `new_priority < active_priority` | NVIC priority registers (IPR) define levels; BASEPRI/PRIMASK gates entire classes; nested exceptions follow strict priority inversion rules | Trace interrupt execution order under simultaneous triggers; measure worst-case latency for highest-priority ISR; validate that critical ISRs never miss deadlines |
| **ISR Design Discipline** | ISR runtime must be bounded and minimal; deferred work offloads processing to non-interrupt context | Atomic flag-setting, FIFO enqueue, or semaphore post in ISR; main loop or RTOS task performs heavy lifting | Profile ISR execution time (start/end GPIO toggle + oscilloscope); confirm no blocking calls (printf, malloc, delay loops); verify interrupt re-enable timing |
| **NVIC Configuration** | Each interrupt requires enable (ISER), priority (IPR), and peripheral-side trigger setup | Write 1 to `NVIC_ISER[n]` bit corresponding to IRQ number; set priority in `NVIC_IPR[n]` upper nibble; configure peripheral interrupt enable/flag registers | Read back ISER/IPR to confirm settings; force interrupt via `NVIC_ISPR` to test ISR linkage; clear pending flags (`NVIC_ICPR`, peripheral status registers) to prevent spurious triggers |
| **Context Switch Overhead** | Interrupt latency = entry (stack push) + execution (ISR body) + exit (stack pop); tail-chaining eliminates redundant unstack-restack | Hardware stacks R0–R3, R12, LR, PC, xPSR in 12 cycles (Cortex-M4); software may stack FPU registers (S0–S15) if floating-point context active | Measure GPIO toggle interval across ISR boundary; compare against theoretical minimum (entry + exit cycles); identify deviations caused by cache misses, bus contention, or lazy FPU stacking |
