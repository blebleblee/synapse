# Lesson 4: Device Drivers, Direct Memory Access, Bus Protocols

## 1. First-Principles Intuition & Invariants

The firmware engineer's task is fundamentally one of orchestrating communication between the CPU and peripheral hardware while maintaining correctness, latency predictability, and resource efficiency. At the core of this orchestration sits the device driver—a contract layer that abstracts the electrical and temporal properties of hardware into a coherent software interface. Understanding device drivers requires us to step back and ask: what problem are we actually solving?

Consider the CPU executing instructions sequentially, operating on data resident in its registers and cache hierarchy. Simultaneously, a serial UART is receiving bytes from an external sensor, a Direct Memory Access (DMA) controller is transferring audio frames into buffer memory, and an SPI flash chip is responding to read commands with variable latency. The CPU cannot afford to wait idly for each peripheral to complete its operation—that would waste execution cycles and create unacceptable latency jitter. Nor can the CPU ignore the peripheral entirely—data will be lost, synchronization will fail, and the system will become incoherent.

The device driver solves this tension through three interlocking mechanisms. First, it manages the device's control and status registers through a choreographed sequence of memory-mapped I/O (MMIO) writes and reads, commanding the hardware to perform its function and interrogating its state. Second, it coordinates data movement—either through polled reads and writes (suitable for low-throughput, latency-critical tasks) or through interrupt-driven and DMA-based transfers (necessary for high-throughput or background I/O). Third, it enforces synchronization invariants: ensuring that data written to shared memory is visible to the DMA controller before a transfer begins, that interrupt handlers do not race with the main firmware loop, and that hardware state machines do not operate on stale or partially-written configuration.

The physical instantiation of this contract is the MMIO address space. On ARM Cortex-M microcontrollers, peripherals like the UART, SPI controller, I2C master, and timer units are accessed through fixed memory addresses that do not correspond to DRAM or flash. Instead, reads and writes to these addresses are intercepted by the system interconnect and routed to the peripheral's internal registers. This creates a bijection between memory operations and hardware commands: writing `0x1` to the UART transmit data register physically causes the UART to latch that byte and begin signaling it on the serial bus; reading the UART status register tells us whether a byte has arrived or transmission is complete.

The invariants governing driver correctness are both electrical and computational. On the electrical side, we must respect bus timing (setup and hold times for SPI and I2C), signal voltage levels, and the order of operations dictated by the hardware's state machine. A typical example: when configuring an SPI peripheral, we must write the baud rate divisor, polarity, and phase settings before setting the enable bit; setting enable before configuration may leave the peripheral in an undefined state. On the computational side, we must ensure memory coherency between the CPU and DMA controller (through explicit cache flushes or uncached regions), prevent use-after-free bugs in ring buffers, and avoid race conditions between interrupt handlers and main-loop code that access the same buffers or control registers.

Direct Memory Access represents a qualitative shift in architecture. Rather than having the CPU copy data byte-by-byte (via repeated load and store instructions), the DMA controller—a semi-autonomous state machine with its own address pointers, byte counters, and control logic—moves data directly between peripherals and memory. This decouples the CPU's execution timeline from the I/O timeline, enabling the CPU to perform computation while high-throughput transfers proceed in the background. However, DMA introduces new failure modes: the CPU and DMA controller may attempt to write to overlapping memory regions simultaneously, causing data corruption; cache coherency issues may prevent the CPU from seeing DMA-written data; and circular buffer indexing errors can cause data to wrap incorrectly or for the firmware to access stale buffers while the DMA controller is still writing to them.

Bus protocols—UART, SPI, and I2C—are the physical layer through which the microcontroller exchanges data with external devices. Each protocol makes different tradeoffs between clock frequency, bus wiring complexity, and robustness. UART is the oldest and slowest, requiring only a transmit and receive line and tolerating clock skew through asynchronous start and stop bits. SPI is faster, synchronous, and point-to-point, making it ideal for connecting to memory chips and sensors but requiring dedicated chip-select lines for each device on the bus. I2C is slower than SPI but allows multiple devices on a shared bus through open-drain pull-ups and software-controlled addressing. Each protocol demands that the device driver understand and implement the signal timing, state transitions, and error-recovery procedures that the protocol defines.

## 2. Core Architecture & Mechanics

### Device Driver Layering and Abstraction

A professional device driver for an embedded system is not a monolithic block of code but rather a layered architecture with clear separation of concerns. The lowest layer is the Hardware Abstraction Layer (HAL), which provides functions that directly manipulate MMIO registers—toggling enable bits, setting baud rates, reading status flags. Above the HAL sits the driver logic proper, which orchestrates sequences of HAL operations to implement higher-level concepts like "open a UART channel," "write a buffer," or "wait for transmission complete." At the top sits the public API that firmware code uses: simple functions like `uart_write()` or `spi_read()` that hide the complexity of driver state machines, buffer management, and interrupt handling.

This layering exists for sound engineering reasons. The HAL provides a stable, machine-readable contract with the silicon datasheet. If the microcontroller is updated to a newer revision with slightly different register layouts, only the HAL needs to change; the driver logic and public API remain untouched. The driver logic implements the state machines, error handling, and concurrency control that make the driver robust and predictable. The public API presents an idealized interface to firmware engineers, allowing them to think in terms of high-level I/O operations rather than register bit manipulation.

Consider a practical example: a UART driver for an STM32 microcontroller. At the HAL level, we define functions like `uart_set_baud_rate(uint32_t brr_value)` that directly write to the Baud Rate Register (BRR), or `uart_enable_tx_interrupt()` that sets the TXIE bit in the Control Register 1 (CR1). The driver logic sits above this and might implement a function `uart_transmit_blocking(const uint8_t *data, size_t length)` that repeatedly calls the HAL's `uart_write_byte()` function and polls the TX complete flag. Higher still, a truly production-grade driver might implement `uart_transmit_dma(const uint8_t *data, size_t length)` that configures a DMA channel to move data autonomously, then returns immediately to the caller—enabling the CPU to do other work while the serial line is being driven.

The architecture of a device driver also reflects the distinction between synchronous and asynchronous I/O. Synchronous operations (blocking) are straightforward: the caller invokes the driver, the driver performs the entire operation (or waits for completion), and then returns. This simplifies firmware logic but can introduce latency and CPU spinning. Asynchronous operations are non-blocking: the caller invokes the driver with a buffer and a completion callback; the driver initiates the operation and returns immediately. When the hardware completes the transfer, an interrupt fires, the driver's interrupt handler processes it and invokes the completion callback, allowing the firmware to react. Asynchronous I/O requires more sophisticated driver state management—tracking which buffers are pending, maintaining queues of pending operations, and coordinating between the main execution context and interrupt handlers.

### Memory-Mapped I/O and the MMIO Contract

At the electrical and computational core of device driver implementation lies memory-mapped I/O. The microcontroller's memory interconnect decodes addresses in the peripheral address space and routes reads and writes to the appropriate peripheral's internal registers. This creates a powerful abstraction: the peripheral's internal state is made visible and controllable through the CPU's load and store instruction set.

On an ARM Cortex-M4F microcontroller, the memory map typically divides the 4 GB address space into regions. Code typically resides at address `0x08000000` (flash). Static data, stacks, and heaps reside at `0x20000000` (SRAM). Peripherals are mapped starting at `0x40000000`. Within the peripheral space, different peripheral blocks occupy different address ranges: UART1 might be at `0x40011000`, UART2 at `0x40010800`, SPI1 at `0x40013000`, and so forth. Each peripheral presents a set of registers at sequential addresses. The UART might have a Data Register (DR) at offset `0x04`, a Status Register (SR) at offset `0x08`, and Control Registers (CR1, CR2, CR3) at offsets `0x0C`, `0x10`, and `0x14`.

The contract between the CPU and peripheral is deceptively simple: a write to an MMIO address causes data to appear in the peripheral's register file, triggering any side effects that register defines. A read from an MMIO address returns the current value of the peripheral's register, potentially with side effects (e.g., reading the UART Data Register might clear a "new data available" flag). However, this contract conceals substantial complexity. The peripheral's register file is not ordinary memory. Unlike SRAM, which retains whatever value is written until the next write, MMIO registers often have restricted write domains: some fields might be read-only, some might be write-only, and some might have hardware-settable bits that the CPU cannot modify. Furthermore, MMIO operations may have side effects that persist across instruction boundaries: writing to a timer's counter register might reset an internal prescaler; reading a status register might clear interrupt flags.

This distinction necessitates compiler awareness. Optimizing compilers perform dead-store elimination: if they see two consecutive writes to the same memory address with no intervening reads, they may eliminate the first write. With ordinary SRAM this is correct, but with MMIO registers it is catastrophic. Writing `0` then `1` to an enable bit might have different effects than writing `1` alone—the intermediate `0` might trigger hardware behavior (reset, clear pending state, etc.). Similarly, the compiler might cache the result of a read: if the code reads a status register, checks a bit, performs some computation, and reads the status register again, the compiler might reuse the cached result rather than issuing a second read. Again, this is correct for SRAM but incorrect for MMIO, where the register's value may have changed due to hardware activity.

To prevent these optimizations, device drivers use the `volatile` keyword on MMIO pointer types. A `volatile` qualifier tells the compiler that the value at this address may change due to external factors (hardware) and must not be cached or reordered. Modern embedded development patterns define MMIO access through `volatile` pointers or volatile struct types that map registers onto the memory map.

Here is a concrete example of a HAL register structure for an ARM Cortex-M UART:

```c
typedef struct {
    volatile uint32_t CR1;      // Offset 0x00: Control Register 1
    volatile uint32_t CR2;      // Offset 0x04: Control Register 2
    volatile uint32_t CR3;      // Offset 0x08: Control Register 3
    volatile uint32_t BRR;      // Offset 0x0C: Baud Rate Register
    volatile uint32_t GTPR;     // Offset 0x10: Guard Time & Prescaler
    volatile uint32_t RTOR;     // Offset 0x14: Receiver Timeout Register
    volatile uint32_t RQR;      // Offset 0x18: Request Register
    volatile uint32_t ISR;      // Offset 0x1C: Interrupt & Status Register
    volatile uint32_t ICR;      // Offset 0x20: Interrupt Clear Register
    volatile uint32_t RDR;      // Offset 0x24: Receive Data Register
    volatile uint32_t TDR;      // Offset 0x28: Transmit Data Register
} USART_TypeDef;

#define USART1 ((USART_TypeDef *) 0x40011000)
#define USART2 ((USART_TypeDef *) 0x40010800)
```

With these definitions, accessing a register becomes as simple as `USART1->CR1 |= (1 << 0)` to set the enable bit, or `uint8_t byte = USART1->RDR` to read a received byte. The compiler, seeing that these pointers are `volatile`, will not optimize away these accesses.

### Interrupt-Driven I/O and Vector Tables

The CPU cannot poll every peripheral constantly to check for new data. Polling wastes CPU cycles, introduces latency jitter, and creates power inefficiency (the CPU cannot enter low-power sleep states while polling). Interrupt-driven I/O solves this by allowing peripherals to signal the CPU that an event has occurred—data has arrived, transmission is complete, an error has occurred. The CPU, in response, pauses its current execution and jumps to an interrupt handler—a special function that processes the event.

Interrupts are managed through the NVIC (Nested Vectored Interrupt Controller) on ARM Cortex-M processors. Each interrupt source (UART1 Receive, UART1 Transmit, SPI1 Complete, Timer1 Overflow, etc.) is assigned a unique interrupt number. The NVIC maintains an interrupt vector table—an array of function pointers—where each entry corresponds to an interrupt number. When an interrupt asserts, the NVIC looks up the corresponding vector, saves the CPU's current program counter and registers onto the stack, and branches to the interrupt handler.

The interrupt vector table is typically placed at the lowest memory address in flash (e.g., `0x08000000` on STM32). Entries in the table are function pointers to interrupt handlers. The Cortex-M architecture reserves the first 16 entries for core exceptions (Reset, Non-Maskable Interrupt, HardFault, MemManage Fault, Bus Fault, Usage Fault, etc.). Device-specific interrupts begin at vector 16. For example, on an STM32F407, UART1 receive interrupt might be vector 37, and UART1 transmit interrupt might also be 37 (the same handler distinguishes them by reading the status register).

Device driver interrupt handlers are typically kept short and fast. A typical pattern for a UART receive interrupt is to read the incoming byte from the data register, store it in a circular buffer, update the write pointer, and return. The actual processing of the received data (parsing a command, echoing it back, etc.) happens in the main firmware loop, not in the interrupt handler. This minimization of interrupt handler work reduces interrupt latency jitter and prevents high-priority interrupts from being blocked by low-priority handler code.

Here is a practical example of a UART receive interrupt handler:

```c
// Circular buffer for received data
#define RX_BUFFER_SIZE 256
static uint8_t rx_buffer[RX_BUFFER_SIZE];
static size_t rx_write_idx = 0;
static size_t rx_read_idx = 0;

// UART1 Receive Interrupt Handler
void USART1_IRQHandler(void) {
    // Check if RXNE (Receive Data Register Not Empty)
    if (USART1->ISR & (1 << 5)) {
        uint8_t byte = USART1->RDR;
        
        // Write byte to circular buffer
        rx_buffer[rx_write_idx] = byte;
        rx_write_idx = (rx_write_idx + 1) % RX_BUFFER_SIZE;
        
        // Optionally signal that data is available
        // (e.g., set a flag, post a semaphore, etc.)
    }
}

// Main firmware loop reads from rx_read_idx at its own pace
uint8_t uart_read_byte(void) {
    while (rx_read_idx == rx_write_idx) {
        // Buffer is empty; wait or perform other work
        __asm("NOP");
    }
    uint8_t byte = rx_buffer[rx_read_idx];
    rx_read_idx = (rx_read_idx + 1) % RX_BUFFER_SIZE;
    return byte;
}
```

In this pattern, the interrupt handler is exceedingly simple: it reads the incoming byte and updates a pointer. The main firmware loop checks the buffer periodically and consumes the data at its own pace. This decoupling prevents the interrupt handler from blocking on I/O or consuming excessive time, which would interfere with other interrupt handlers.

### Direct Memory Access Controller Architecture

The DMA controller is a semi-autonomous finite state machine that can move data between memory and peripherals (or between memory regions) without CPU intervention. On ARM Cortex-M microcontrollers, the DMA controller typically supports multiple channels (e.g., STM32 devices have 8 or 16 DMA channels). Each channel is independently configurable with a source address, destination address, byte count, transfer width (8-bit, 16-bit, 32-bit), and increment modes (source and destination can be fixed or incrementing).

The DMA controller is controlled through a set of MMIO registers. For a typical DMA channel, these registers include:

- **Channel Control Register (CCR)**: Enables the channel, sets transfer direction (memory-to-peripheral, peripheral-to-memory, memory-to-memory), configures increment modes, sets transfer width, enables interrupts.
- **Source Address Register (CSAR)**: The starting address from which data will be read.
- **Destination Address Register (CDAR)**: The starting address to which data will be written.
- **Transfer Count Register (CCOUNT)**: The number of items to transfer (item size determined by transfer width).
- **Status/Interrupt Registers**: Indicate transfer completion, errors, and allow clearing of interrupt flags.

When the DMA channel is enabled, it begins transferring data according to its configuration. If configured for peripheral-to-memory transfer, the DMA controller asserts a request signal to the peripheral (e.g., "I'm ready to receive a byte"). The peripheral, upon completing its operation, signals to the DMA that data is ready. The DMA then reads from the peripheral's data register, stores the byte in memory at the destination address, increments the destination pointer (if increment mode is enabled), decrements the transfer count, and repeats. This continues until the transfer count reaches zero, at which point the DMA generates a completion interrupt.

The DMA controller's inclusion in the microcontroller represents a profound architectural shift. Previously, data movement was synonymous with CPU execution. Now, data movement can proceed independently. This enables scenarios like receiving an audio stream via I2S (Inter-IC Sound) while the CPU processes the previous frame, or reading a large block from an SD card while the CPU executes application logic. However, this independence creates new correctness challenges.

### Scatter-Gather Operations and Advanced DMA

Simple DMA transfers move data from a contiguous source region to a contiguous destination region. However, many real-world scenarios require more complex transfers. Imagine buffering audio frames where each frame is stored at a different address in a dynamically-allocated circular buffer, or receiving network packets where each packet is placed in a different buffer managed by a memory allocator. Simple contiguous transfers are insufficient; we need scatter-gather operations.

Scatter-gather DMA works by maintaining a linked list of DMA descriptors in memory. Each descriptor specifies a source address, destination address, and transfer count for a single operation. The DMA controller executes descriptors sequentially, and after completing one descriptor, it reads the next descriptor from memory and continues. This allows the DMA to move data to or from non-contiguous regions without CPU intervention.

On ARM Cortex-M processors with advanced DMA controllers (like the DMA-401 on Cortex-A processors or enhanced versions on some microcontrollers), scatter-gather is implemented through DMA configuration structures. The firmware populates a linked list of descriptors in memory, programs the DMA with the address of the first descriptor, and lets the DMA run autonomously. Each descriptor includes a link pointer to the next descriptor, allowing the DMA to chain operations.

Here is a conceptual example of a scatter-gather descriptor structure:

```c
typedef struct {
    volatile uint32_t src_addr;     // Source address for this transfer
    volatile uint32_t dst_addr;     // Destination address for this transfer
    volatile uint32_t count;         // Number of items to transfer
    volatile uint32_t next_desc;     // Pointer to next descriptor (or 0 if last)
} DMA_Descriptor;

// Ring buffer with scatter-gather
#define NUM_BUFFERS 4
#define BUFFER_SIZE 1024

static uint8_t buffers[NUM_BUFFERS][BUFFER_SIZE];
static DMA_Descriptor descriptors[NUM_BUFFERS];

void setup_scatter_gather_dma(void) {
    for (int i = 0; i < NUM_BUFFERS; i++) {
        descriptors[i].src_addr = PERIPHERAL_DATA_ADDR;
        descriptors[i].dst_addr = (uint32_t)&buffers[i][0];
        descriptors[i].count = BUFFER_SIZE;
        descriptors[i].next_desc = (uint32_t)&descriptors[(i + 1) % NUM_BUFFERS];
    }
    
    // Configure DMA to start with first descriptor
    DMA->SRC_ADDR = descriptors[0].src_addr;
    DMA->DST_ADDR = descriptors[0].dst_addr;
    DMA->COUNT = descriptors[0].count;
    DMA->NEXT_DESC = (uint32_t)&descriptors[1];
    DMA->CTRL = DMA_ENABLE | DMA_SG_ENABLE;
}
```

Scatter-gather enables sophisticated buffer management strategies. A common pattern is a circular ring of descriptors where the DMA controller continuously loops through the descriptors, always writing to the oldest buffer while the firmware reads from newer buffers. This provides natural flow control: when the firmware falls behind and hasn't consumed the current buffer, the DMA wraps around and overwrites stale data, preventing data loss in a predictable manner.

### Cache Coherency and Memory Barriers

One of the deepest challenges in device driver implementation on modern microcontrollers is cache coherency. When the CPU performs a store to memory, the store might initially land in the CPU's L1 cache rather than propagating immediately to main memory. If the DMA controller then attempts to read from that memory address, it sees the stale value in DRAM, not the CPU's cached value. Conversely, when the DMA controller writes to memory, the CPU's cache might retain a stale copy, causing the CPU to read the old value.

The ARM architecture provides memory barriers to enforce ordering and cache coherency. The DMB (Data Memory Barrier) instruction ensures that all memory operations before the barrier complete before any memory operations after the barrier begin. The DSB (Data Synchronization Barrier) instruction is stronger, requiring all operations to complete and be visible to all observers. The ISB (Instruction Synchronization Barrier) flushes the instruction pipeline and is primarily used after changing system registers or exception configurations.

For DMA coherency, the typical pattern is to issue a DMB or DSB after the CPU writes data that the DMA will read, and before the CPU reads data that the DMA has written. Many microcontroller vendors provide cache flush and invalidate instructions (e.g., `SCB->DCIMVAC` for cache invalidate by virtual address on Cortex-M7) to explicitly evict cache lines, ensuring that the CPU sees DMA-written data.

Here is a practical pattern for setting up a DMA transfer with proper cache synchronization:

```c
void dma_transfer_with_cache_sync(uint32_t src, uint32_t dst, size_t count) {
    // Flush CPU cache for source region if CPU wrote the source data
    // (This is a simplified example; real code would flush cache lines)
    if (SCB->CCR & SCB_CCR_DC_Msk) {  // If D-Cache is enabled
```
