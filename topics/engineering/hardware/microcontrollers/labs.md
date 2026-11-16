# Operational Verification Labs: Microcontrollers

## Objective & Operational Lab Setup

The microcontroller serves as the foundational computational substrate for embedded systems, bridging the deterministic execution of machine code with the analog chaos of physical sensors, actuators, and communication peripherals. This laboratory guide focuses on operational verification methodologies that transform datasheet specifications into measurable hardware-software integration points. Rather than abstract programming exercises divorced from silicon constraints, these labs ground the practitioner in the electrical realities of memory-mapped I/O, interrupt latency measurement, peripheral clock domain synchronization, and power consumption profiling under real-time operating conditions.

The operational verification approach treats the microcontroller as a black-box system under test, subjecting it to boundary-condition stress scenarios that expose timing violations, race conditions in interrupt service routines, and resource contention between DMA channels and CPU execution. Each exercise progresses from nominal operating conditions through parametric variation into deliberate failure injection, equipping the hardware engineer with diagnostic intuition for field debugging scenarios where oscilloscope traces, logic analyzer captures, and power supply current signatures reveal pathological behavior invisible to software-only analysis.

### Laboratory Hardware Requirements

The baseline testbench requires an ARM Cortex-M4 development board—specifically the STM32F407 Discovery or STM32 Nucleo-F446RE—selected for its widespread availability, comprehensive peripheral set including floating-point unit, and mature vendor toolchain support. The STM32F407 operates at 168 MHz maximum frequency with 192 KB SRAM and 1 MB Flash, providing sufficient headroom for real-time OS experimentation while maintaining accessible debugging infrastructure. Alternative platforms such as the Texas Instruments TM4C123GXL (Tiva C Series) or Nordic Semiconductor nRF52840 may substitute provided they expose GPIO, UART, SPI, I2C, ADC, and timer peripherals with external pin access for oscilloscope probing.

Critical bench instrumentation includes a four-channel digital storage oscilloscope with minimum 100 MHz bandwidth and 1 GSa/s sampling rate, necessary for capturing sub-microsecond interrupt response latencies and SPI clock edge timing violations. A sixteen-channel logic analyzer—either the Saleae Logic Pro 16 or budget-constrained alternative using sigrok-compatible hardware—provides parallel visibility into multi-wire bus protocols and interrupt assertion sequences that single-channel oscilloscopes cannot reconstruct. The USB-to-UART bridge integrated into most development boards suffices for initial console logging, but external FTDI FT232H adapters enable independent verification of baud rate accuracy and frame error injection testing.

Power measurement infrastructure differentiates rigorous operational verification from casual experimentation. A digital multimeter with USB logging capability (such as the Keysight U1272A or Brymen BM869s) captures time-series current draw during sleep-mode transitions, revealing parasitic wake events and peripheral clock gating failures. For sub-milliampere resolution required in ultra-low-power battery profiling, the Nordic Power Profiler Kit II or Otii Arc provides synchronized current-voltage-digital-trigger recording with nanosecond timestamp correlation to firmware execution traces. Laboratory-grade power supplies—minimum specifications include dual-channel output, 1 mV voltage resolution, and 1 mA current resolution with electronic load capability—enable controlled supply voltage droop injection to test brown-out reset thresholds.

### Toolchain Configuration and Debug Interface Setup

The GNU Arm Embedded Toolchain provides the compiler infrastructure, distributed as pre-built binaries for Linux, macOS, and Windows at developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain. Installation requires extracting the archive to `/opt/gcc-arm-none-eabi` on Unix systems or `C:\Program Files\gcc-arm-none-eabi` on Windows, followed by PATH environment modification to expose `arm-none-eabi-gcc`, `arm-none-eabi-objcopy`, and `arm-none-eabi-gdb` executables. Version 10.3-2021.10 or later includes critical Cortex-M4 DSP instruction support and hardware floating-point ABI linkage required for efficient signal processing operations.

OpenOCD (Open On-Chip Debugger) mediates between host-side GDB client sessions and the on-chip debug module accessed via ST-LINK/V2 hardware. Compilation from source ensures compatibility with bleeding-edge probe firmware, though distribution packages suffice for stable platforms. The configuration file for STM32F407 Discovery resides at `openocd/scripts/board/stm32f4discovery.cfg` and specifies SWD transport, reset configuration, and Flash programming algorithms. Launching OpenOCD with `openocd -f board/stm32f4discovery.cfg` establishes a GDB remote protocol server on TCP port 3333, enabling `arm-none-eabi-gdb` to attach, set breakpoints, single-step through assembly, and inspect peripheral register states during live execution.

ST-LINK utility installation provides vendor-specific Flash programming and option byte configuration beyond OpenOCD's capabilities. The STM32CubeProgrammer tool—available from st.com—unifies command-line and graphical interfaces for erasing sectors, verifying checksums, and setting read protection levels. Critical for operational labs, this utility configures boot pin strapping, voltage range selection for Flash write operations, and watchdog timer persistence across resets. The command-line invocation `STM32_Programmer_CLI -c port=SWD -w firmware.hex -v -rst` programs the target, verifies contents, and issues a system reset atomically, eliminating manual button-press synchronization errors during rapid iteration cycles.

### Memory-Mapped I/O Base Address Verification

Every microcontroller peripheral occupies a fixed address range within the 4 GB physical address space defined by the ARM Cortex-M4 architecture. The STM32F407 reference manual RM0090 chapter 2 enumerates these base addresses: GPIO Port A begins at `0x40020000`, USART2 at `0x40004400`, TIM2 at `0x40000000`, and ADC1 at `0x40012000`. Before any register manipulation, the practitioner must verify these mappings by reading the peripheral identification registers that encode silicon revision and feature presence. For GPIO Port A, the memory location `0x40020000` contains the MODER register controlling pin direction, while offset `+0x14` yields the ODR register for output data. A minimal C validation routine declares a volatile pointer to the base address, dereferences to read MODER, and compares against the documented reset value of `0xA8000000`, which configures PA13/PA14/PA15 as alternate function for JTAG/SWD.

The verification procedure begins with creating a bare-metal project initialized with the correct linker script and startup assembly. The linker script `STM32F407VGTx_FLASH.ld` must position the vector table at Flash origin `0x08000000`, define SRAM regions from `0x20000000` through `0x2001FFFF` for 128 KB, and reserve CCM (Core-Coupled Memory) from `0x10000000` for stack allocation. The startup file `startup_stm32f407xx.s` populates the vector table with default exception handlers, initializes the stack pointer from the linker-provided symbol `_estack`, copies initialized data from Flash to SRAM, and zero-fills the `.bss` section before branching to the C runtime entry point. Compiling with `arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O0 -g3` ensures Thumb-2 instruction encoding, hardware floating-point linkage, and maximal debug symbol retention for register inspection.

Flashing the validation firmware via OpenOCD confirms memory map correctness when the debugger can set breakpoints at expected addresses, read peripheral registers without bus faults, and single-step through initialization routines without triggering HardFault exceptions. The GDB command sequence `target remote localhost:3333`, `load`, `monitor reset halt`, `break main`, `continue` establishes the debug session, programs Flash, halts at reset vector, sets a function breakpoint, and resumes execution until main entry. Subsequent `x/4xw 0x40020000` dumps four 32-bit words from GPIO Port A base, displaying MODER, OTYPER, OSPEEDR, and PUPDR register contents for comparison against datasheet reset values. Discrepancies indicate incorrect device selection in the linker script or corrupted Flash programming, requiring sector erase and re-verification before proceeding to peripheral configuration exercises.

### Oscilloscope and Logic Analyzer Probe Configuration

Electrical signal integrity during high-speed peripheral communication demands proper oscilloscope probe grounding and bandwidth selection to avoid introducing measurement artifacts that masquerade as microcontroller misbehavior. Passive 10:1 voltage probes—standard accessories with most oscilloscopes—provide 10 MΩ input impedance and bandwidth extending to 200 MHz, suitable for GPIO transitions, UART signaling, and I2C clock edges below 1 MHz. The ground lead clip must connect to the shortest possible path on the development board's ground plane, ideally within 2 cm of the signal probe tip, to minimize inductive ringing that distorts sub-nanosecond edge measurements. Ground spring attachments replace the long ground lead for frequencies above 10 MHz, reducing parasitic inductance from ~500 nH to ~5 nH and eliminating the characteristic overshoot/undershoot ringing in square-wave captures.

Logic analyzer channel assignment requires careful documentation of probe-to-microcontroller pin mapping, with color-coded or numbered probes corresponding to protocol-specific signals: UART TX/RX, SPI MOSI/MISO/SCK/CS, I2C SDA/SCL, and general-purpose interrupt lines. The Saleae Logic software or sigrok PulseView provides protocol decoders that automatically parse captured bitstreams into human-readable transactions, but only when trigger and channel assignments align with electrical reality. For SPI verification, channel 0 connects to SCK (clock), channel 1 to MOSI (master-out), channel 2 to MISO (master-in), and channel 3 to CS (chip select), with the trigger condition set to falling edge on CS to capture complete transaction frames. Sample rate selection follows the Nyquist criterion: for a 10 MHz SPI clock, the logic analyzer must sample at minimum 20 MS/s, though 50–100 MS/s provides margin for jitter analysis and setup/hold time violation detection.

Triggering strategy separates signal from noise in environments where continuous acquisition generates gigabytes of irrelevant data. Edge triggering on a GPIO interrupt line—configured to assert when an external sensor detects motion—captures the precise moment of peripheral-to-CPU signaling, enabling interrupt latency measurement from physical event to ISR entry. Advanced pattern triggering supports multi-signal condition evaluation: trigger when UART TX transitions high AND timer PWM output goes low simultaneously, revealing race conditions in concurrent peripheral initialization sequences. Serial protocol triggers within logic analyzer software decode packet structures and trigger on specific byte sequences, such as a CAN bus error frame or an I2C NACK condition, filtering out routine transactions to isolate pathological behavior during stress testing.

Calibration verification ensures measurement fidelity by applying known reference signals to oscilloscope and logic analyzer inputs before connecting to the microcontroller. Most oscilloscopes provide a 1 kHz, 5V peak-to-peak calibration square wave on the front panel, used to adjust probe compensation for flat frequency response. The probe compensation trimmer capacitor—accessible via a screwdriver slot on the probe body—adjusts to eliminate the leading-edge peaking or droop that indicates impedance mismatch. Logic analyzers require threshold voltage calibration: for 3.3V CMOS logic, the input threshold should register at approximately 1.65V, verified by connecting a precision voltage reference and confirming the digital transition point. Incorrect thresholds produce intermittent misreads on signals with slow edge rates or noise, generating phantom protocol errors that waste hours of debugging effort chasing ghosts in otherwise functional firmware.

## Exercise 1: Foundational Practical Implementation

### GPIO Configuration and Toggle-Rate Measurement

The general-purpose input-output peripheral forms the simplest interface between software execution and external electrical signals, providing the foundation for understanding memory-mapped I/O mechanics, register bitfield manipulation, and clock distribution constraints. This exercise programs GPIO Port D pin 12—the green LED on STM32F407 Discovery—to toggle at maximum achievable frequency, exposing the relationship between CPU clock speed, instruction execution latency, and physical signal propagation delay. The measured toggle rate reveals the cost of peripheral access through the AHB1 bus, demonstrating why DMA-based approaches outperform polled I/O for high-throughput data transfer.

The microcontroller emerges from reset with all peripheral clocks disabled to minimize power consumption, requiring explicit clock gate enablement before accessing any peripheral registers. The RCC (Reset and Clock Control) peripheral at base address `0x40023800` contains the AHB1ENR register at offset `+0x30`, where bit 3 enables the GPIO Port D clock. Writing `0x00000008` to `0x40023830` powers the Port D digital logic, allowing subsequent register writes to take effect rather than vanishing into an unpowered peripheral block. Clock gating verification reads back the AHB1ENR register: if bit 3 remains clear after the write operation, the RCC peripheral itself lacks clock or the bus interface suffers from a hardware fault requiring board-level diagnosis.

GPIO configuration requires setting four registers per port: MODER for pin direction (input/output/alternate-function/analog), OTYPER for output type (push-pull/open-drain), OSPEEDR for slew rate control (low/medium/high/very-high), and PUPDR for internal pull-up/pull-down resistor activation. Pin 12 output configuration writes `0x01000000` to GPIOD_MODER at `0x40020C00`, setting bits [25:24] to `01` for general-purpose output mode. GPIOD_OTYPER at offset `+0x04` receives `0x00000000` to select push-pull output capable of sourcing and sinking current, as opposed to open-drain mode requiring external pull-up resistors. GPIOD_OSPEEDR at offset `+0x08` receives `0x03000000` to set bits [25:24] to `11` for very-high-speed output (100 MHz on 50 pF load), minimizing rise/fall time for accurate frequency measurement.

The toggle loop itself exposes the instruction-level mechanics of peripheral access. The output data register GPIOD_ODR at offset `+0x14` contains one bit per pin, where writing `1` drives the pin high and `0` drives low. However, the STM32 architecture provides bit-set/reset registers BSRR at offset `+0x18` enabling atomic single-bit manipulation without read-modify-write hazards. Writing `0x00001000` to GPIOD_BSRR sets pin 12 high by activating bit 12 in the lower halfword, while `0x10000000` resets pin 12 low via bit 28 in the upper halfword. This atomic operation prevents race conditions when interrupt service routines and mainline code manipulate different pins within the same port simultaneously, a critical safety property for motor control or multi-channel communication applications.

The complete C implementation demonstrates bare-metal register manipulation without HAL abstraction layers:

```c
#include <stdint.h>

#define RCC_BASE        0x40023800UL
#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE + 0x30))
#define GPIOD_BASE      0x40020C00UL
#define GPIOD_MODER     (*(volatile uint32_t *)(GPIOD_BASE + 0x00))
#define GPIOD_OTYPER    (*(volatile uint32_t *)(GPIOD_BASE + 0x04))
#define GPIOD_OSPEEDR   (*(volatile uint32_t *)(GPIOD_BASE + 0x08))
#define GPIOD_BSRR      (*(volatile uint32_t *)(GPIOD_BASE + 0x18))

void delay_cycles(uint32_t cycles) {
    while (cycles--) {
        __asm__ volatile ("nop");
    }
}

int main(void) {
    // Enable GPIOD clock
    RCC_AHB1ENR |= (1 << 3);
    
    // Configure PD12 as output, push-pull, very high speed
    GPIOD_MODER   = (GPIOD_MODER & ~(3 << 24)) | (1 << 24);
    GPIOD_OTYPER  &= ~(1 << 12);
    GPIOD_OSPEEDR |= (3 << 24);
    
    // Maximum speed toggle loop
    while (1) {
        GPIOD_BSRR = (1 << 12);     // Set PD12 high
        GPIOD_BSRR = (1 << 28);     // Reset PD12 low
    }
}
```

Compiling with optimization disabled (`-O0`) produces assembly that reveals the memory access pattern. Each BSRR write translates to a 32-bit immediate load into a register followed by a store instruction to the peripheral address. The Cortex-M4 executes loads and stores through the AHB1 bus, which at 168 MHz system clock incurs zero wait states for on-chip peripheral access, yielding approximately 6 CPU cycles per toggle: 2 for immediate load, 1 for store, 1 for branch back to loop start, 2 for pipeline refill. The theoretical maximum toggle rate approaches 14 MHz, though actual measurement typically yields 10–12 MHz due to bus arbitration delays when the instruction fetch unit and data access unit compete for bus bandwidth.

Oscilloscope measurement procedure connects channel 1 probe tip to pin PD12 (physical location varies by board layout; consult schematic) with ground spring attached to the nearest ground via. Trigger settings select edge mode on channel 1, rising edge, 1.6V threshold for 3.3V CMOS logic. Time base adjusts to 50 ns/division to display 2–3 complete cycles per screen, enabling visual rise/fall time inspection. The frequency measurement function—typically activated via the MEAS menu—computes period from consecutive rising edges and inverts to display frequency. Measured values between 10–14 MHz confirm correct clock configuration and optimal compiler output; frequencies below 5 MHz indicate excessive wait states, disabled instruction cache, or incorrect system clock multiplier settings in the RCC_CFGR register.

Enabling compiler optimization with `-O2` or `-O3` transforms the assembly output through loop unrolling and instruction scheduling. The compiler may generate a branchless loop writing alternating values to BSRR, or even replace the loop with direct writes if the iteration count were finite. However, for infinite toggle loops, the maximum frequency remains bounded by peripheral bus latency rather than instruction execution speed. Comparing `-O0` versus `-O3` toggle rates quantifies the instruction fetch overhead: if optimization produces no frequency improvement, the bottleneck lies in AHB1 bus arbitration rather than CPU pipeline stalls.

The final operational verification injects a calibrated delay between toggle operations to establish timing accuracy. Inserting `delay_cycles(168)` between BSRR writes introduces a 1 microsecond pause (168 cycles at 168 MHz clock), reducing toggle rate to 500 kHz square wave. Oscilloscope measurement of the resulting period—expected value 2 microseconds—validates system clock configuration: if the measured period deviates by more than ±5%, the PLL multiplier or divider settings in RCC_PLLCFGR require recalibration against the external crystal oscillator frequency stamped on the board silkscreen (typically 8 MHz for STM32F407 Discovery).

### UART Serial Console Transmission

Universal asynchronous receiver-transmitter peripherals translate parallel byte-wide data into serialized bitstreams for inter-processor communication, sensor interfacing, and host-side debugging via USB-to-UART bridges. This exercise configures USART2 for 115200 baud, 8 data bits, no parity, 1 stop bit (8N1 format) transmission, implementing a polled transmit routine that outputs null-terminated strings to a terminal emulator. The operational focus emphasizes baud rate accuracy verification via oscilloscope period measurement, frame error detection through parity mismatch injection, and transmit buffer overrun diagnosis when software writes exceed peripheral throughput capacity.

USART2 peripheral resides at base address `0x40004400` on the APB1 bus, requiring clock enablement through RCC_APB1ENR register bit 17. Unlike AHB1 peripherals running at full system clock speed, APB1 operates at a divided frequency—typically 42 MHz for STM32F407 at 168 MHz system clock—directly impacting baud rate generator configuration. The USART baud rate derives from the formula BRR = f_CK / (16 × baud), where f_CK represents the peripheral clock frequency. For 115200 baud on 42 MHz APB1 clock: BRR = 42000000 / (16 × 115200) ≈ 22.786, requiring rounding to the nearest integer mantissa and fractional components encoded in the BRR register as mantissa:fraction in bits [15:4]:[3:0]. The integer portion 22 occupies bits [15:4] as `0x016`, while the fractional 0.786 maps to 12/16 (0.75) as `0xC`, yielding BRR = `0x016C` for near-exact 115200 baud generation.

GPIO alternate function configuration multiplexes the USART2 TX signal onto pin PA2, requiring GPIOA_MODER bits [5:4] set to `10` for alternate function mode, and GPIOA_AFRL (Alternate Function Register Low) bits [11:8] set to `0x07` selecting AF7 (USART1/2/3) for pin PA2. The RX pin PA3 receives identical treatment with GPIOA_MODER bits [7:6] as `10` and GPIOA_AFRL bits [15:12] as `0x07`, though this exercise focuses on transmit-only operation. Pull-up resistor activation via GPIOA_PUPDR ensures the TX line idles high when the USART peripheral is disabled, preventing spurious start bit detection by the receiving device.

USART2 control register 1 (CR1) at offset `+0x0C` contains the peripheral enable bit (UE, bit 13), transmitter enable (TE, bit 3), and receiver enable (RE, bit 2). Writing `0x2008` to USART2_CR1 activates the peripheral and transmitter while leaving the receiver disabled. Control register 2 (CR2) at offset `+0x10` configures stop bit count: clearing bits [13:12] selects 1 stop bit, while `01` selects 0.5 stops, `10` selects 2 stops, and `11` selects 1.5 stops for synchronous half-duplex modes. Control register 3 (CR3) at offset `+0x14` remains zero for this basic configuration, deferring DMA, hardware flow control, and error interrupt enables to advanced exercises.

The polled transmit routine monitors the TXE (Transmit Data Register Empty) flag in the status register (SR) at offset `+0x00`, bit 7. When TXE reads as `1`, the transmit data register (DR) at offset `+0x04` accepts a new byte, triggering serialization through the shift register and transmission over the TX pin. The software must wait for TXE assertion before each byte write to avoid overwriting data still in the shift register, a condition that corrupts the transmitted bitstream without generating error flags. The complete transmission function loops over a null-terminated string, writing one byte per TXE assertion:

```c
#include <stdint.h>

#define RCC_BASE        0x40023800UL
#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE + 0x30))
#define RCC_APB1ENR     (*(volatile uint32_t *)(RCC_BASE + 0x40))

#define GPIOA_BASE      0x40020000UL
#define GPIOA_MODER     (*(volatile uint32_t *)(GPIOA_BASE + 0x00))
#define GPIOA_AFRL      (*(volatile uint32_t *)(GPIOA_BASE + 0x20))
#define GPIOA_PUPDR     (*(volatile uint32_t *)(GPIOA_BASE + 0x0C))

#define USART2_BASE     0x40004400UL
#define USART2_SR       (*(volatile uint32_t *)(USART2_BASE + 0x00))
#define USART2_DR       (*(volatile uint32_t *)(USART2_BASE + 0x04))
#define USART2_BRR      (*(volatile uint32_t *)(USART2_BASE + 0x08))
#define USART2_CR1      (*(volatile uint32_t *)(USART2_BASE + 0x0C))
#define USART2_CR2      (*(volatile uint32_t *)(USART2_BASE + 0x10))
#define USART2_CR3      (*(volatile uint32_t *)(USART2_BASE + 0x14))

void uart_init(void) {
    // Enable GPIOA and USART2 clocks
    RCC_AHB1ENR |= (1 << 0);    // GPIOA
    RCC_APB1ENR |= (1 << 17);   // USART2
    
    // Configure PA2 as AF7 (USART2_TX), PA3 as AF7 (USART2_RX)
    GPIOA_MODER = (GPIOA_MODER & ~((3 << 4) | (3 << 6))) | ((2 << 4) | (2 << 6));
    GPIOA_AFRL  = (GPIOA_AFRL & ~((0xF << 8) | (0xF << 12))) | ((7 << 8) | (7 << 12));
    GPIOA_PUPDR = (GPIOA_PUPDR & ~((3 << 4) | (3 << 6))) | ((1 << 4) | (1 << 6));
    
    // Configure USART2: 115200 baud, 8N1
    USART2_BRR = 0x016C;        // 42 MHz / (16 * 115200) = 22.786 ≈ 22.75
    USART2_CR1 = 0x2008;        // UE=1, TE=1
    USART2_CR2 = 0x0000;        // 1 stop bit
    USART2_CR3 = 0x0000;        // No flow control
}

void uart_transmit_byte(uint8_t data) {
    while (!(USART2_SR & (1 << 7)));  // Wait for TXE
    USART2_DR = data;
}

void uart_transmit_string(const char *str) {
    while (*str) {
        uart_transmit_byte(*str++);
    }
}

int main(void) {
    uart_init();
    
    while (1) {
        uart_transmit_string("STM32F407 USART2 Operational Verification\r\n");
        for (volatile uint32_t i = 0; i < 1000000; i++);  // Crude delay
    }
}
```

Oscilloscope verification measures bit timing on the PA2 TX pin, confirming baud rate accuracy through period measurement of individual bit cells. The UART idle state holds TX high at 3.3V, transitioning low for the start bit, followed by 8 data bits LSB-first, and returning high for the stop bit. Transmitting ASCII 'A' (0x41) produces the bit sequence: start (0), LSB (1), bit1 (0), bit2 (0), bit3 (0), bit4 (0), bit5 (0), bit6 (1), MSB (0), stop (1). At 115200 baud, each bit occupies 1/115200 ≈ 8.68 microseconds. Oscilloscope cursor measurement between consecutive falling edges (start bit and bit1) should yield 8.68 µs ± 0.3 µs; deviations beyond ±3% indicate incorrect BRR calculation or APB1 clock misconfiguration requiring RCC_CFGR register inspection.

Terminal emulator connection routes through the ST-LINK virtual COM port enumerated by the host operating system. On Linux, the device appears as `/dev/ttyACM0` or `/dev/ttyUSB0`, accessed via `screen /dev/ttyACM0 115200` or `minicom -D /dev/ttyACM0 -b 115200`. Windows systems enumerate as `COMx` devices visible in Device Manager, accessed through PuTTY or TeraTerm with 115200 baud, 8 data bits, no parity, 1 stop bit configuration. Successful transmission displays the repeated verification string; missing characters or garbled output suggests baud rate mismatch, incorrect pin assignment, or insufficient power supply current causing brown-out resets during transmission bursts.

Parity error injection demonstrates frame error detection capabilities. Modifying USART2_CR1 to enable even parity (PCE=1, PS=0, bits [12:10] = `100`) appends a parity bit after the 8 data bits, expanding the frame to 11 bits total (start + 8 data + parity + stop). Transmitting 'A' (0x41, even parity 0) with the receiver configured for odd parity (PS=1) triggers a parity error flag in the receiver's status register. This exercise requires connecting two USART peripherals (USART2 TX to USART3 RX) on the same microcontroller or between two development boards, polling the PE (Parity Error) flag in USART3_SR bit 0 to detect the intentionally mismatched frame. Logic analyzer capture displays the physical parity bit state, confirming the transmitter generates even parity while the receiver expects odd, providing hands-on visibility into error detection mechanisms that abstract software layers obscure.

### Timer-Based Precise Delay Generation

Hardware timers provide deterministic microsecond-resolution delay generation immune to instruction execution variability, interrupt latency jitter, and compiler optimization unpredictability that plague software delay loops. This exercise configures TIM2—a 32-bit general-purpose timer on the APB1 bus—for one-shot mode delay generation with ±1 microsecond accuracy, verified via oscilloscope measurement of GPIO toggles separated by programmed intervals. The operational methodology exposes auto-reload register preloading, prescaler configuration for frequency division, and status flag polling versus interrupt-driven completion notification.

TIM2 peripheral base address `0x40000000` requires APB1 clock enablement through RCC_APB1ENR bit 0. The timer clock frequency derives from APB1 clock with a conditional doubler: if the APB1 prescaler in RCC_CFGR is not 1, the timer clock becomes 2×APB1, otherwise it equals APB1. For STM32F407 with APB1 at 42 MHz and APB1 prescaler set to divide-by-4, TIM2 receives 84 MHz clock. This frequency-doubling compensation maintains timer consistency across different APB1 prescaler configurations, though it introduces a configuration trap when engineers assume timer clock equals APB1 frequency directly.

The prescaler register (PSC) at offset `+0x28` divides the incoming clock by (PSC + 1), enabling microsecond-scale tick intervals. For 1 microsecond ticks on an 84 MHz timer clock: PSC = 84 - 1 = 83. The auto-reload register (ARR) at offset `+0x2C` defines the count limit: when the counter register (CNT) at offset `+0x24` increments to match ARR, the update event flag (UIF) in status register (SR) bit 0 asserts, and CNT reloads to zero if the timer operates in continuous mode, or halts if configured for one-shot mode via control register 1 (CR1) bit 3 (OPM, One-Pulse Mode). For a 1000 microsecond delay, ARR = 1000 - 1 = 999, since the counter increments from 0 to ARR inclusive before triggering the update event.

Timer initialization sequence follows a strict ordering to avoid triggering premature update events. First, disable the counter by clearing CR1 bit 0 (CEN, Counter Enable). Second, configure PSC and ARR registers. Third, force a register update by setting the update generation bit (UG) in event generation register (EGR) at offset `+0x14`, bit 0, which loads PSC and ARR into their active shadow registers without triggering the UIF flag. Fourth, clear the UIF flag in SR to prevent false completion detection. Finally, enable the counter via CR1 bit 0. For one-shot operation, set OPM bit 3 in CR1 before starting the counter; the hardware automatically clears CEN after the UIF assertion, halting further counting until software restarts the timer.

The complete implementation demonstrates microsecond-precision delay:

```c
#include <stdint.h>

#define RCC_BASE        0x40023800UL
#define RCC_APB1ENR     (*(volatile uint32_t *)(RCC_BASE + 0x40))

#define TIM2_BASE       0x40000000UL
#define TIM2_CR1        (*(volatile uint32_t *)(TIM2_BASE + 0x00))
#define TIM2_SR         (*(volatile uint32_t *)(TIM2_BASE + 0x10))
#define TIM2_EGR        (*(volatile uint32_t *)(TIM2_BASE + 0x14))
#define TIM2_CNT        (*(volatile uint32_t *)(TIM2_BASE + 0x24))
#define TIM2_PSC        (*(volatile uint32_t *)(TIM2_BASE + 0x28))
#define TIM2_ARR        (*(volatile uint32_t *)(TIM2_BASE + 0x2C))

#define GPIOD_BASE      0x40020C00UL
#define GPIOD_MODER     (*(volatile uint32_t *)(GPIOD_BASE + 0x00))
#define GPIOD_OSPEEDR   (*(volatile uint32_t *)(GPIOD_BASE + 0x08))
#define GPIOD_BSRR      (*(volatile uint32_t *)(GPIOD_BASE + 0x18))

void timer_init(void) {
    RCC_APB1ENR |= (1 << 0);    // Enable TIM2 clock
    
    TIM2_CR1 = 0;               // Disable counter
    TIM2_PSC = 83;              // 84 MHz / 84 = 1 MHz (1 µs tick)
    TIM2_ARR = 999;             // 1000 µs period
    TIM2_EGR = 1;               // Force register update
    TIM2_SR = 0;                // Clear status flags
}

void delay_us(uint32_t us) {
    TIM2_ARR = us - 1;
    TIM2_CNT = 0;
    TIM2_CR1 = (1 << 3) | (1 << 0);  // OPM=1, CEN=1
    while (!(TIM2_SR & (1 << 0)));   // Wait for UIF
    TIM2_SR = 0;                     // Clear UIF
}

int main(void) {
    // Enable GPIOD and configure PD12 as output
    RCC_APB1ENR |= (1 << 3);
    GPIOD_MODER = (GPIOD_MODER & ~(3 << 24)) | (1 << 24);
    GPIOD_OSPEEDR |= (3 << 24);
    
    timer_init();
    
    while (1) {
        GPIOD_BSRR = (1 << 12);     // Set PD12 high
        delay_us(1000);             // 1 ms delay
        GPIOD_BSRR = (1 << 28);     // Reset PD12 low
        delay_us(1000);             // 1 ms delay
    }
}
```

Oscilloscope measurement connects to PD12, triggering on rising edge with time base set to 500 µs/division to display the complete 2 ms period. Cursor measurements between consecutive rising edges quantify delay accuracy: the target 2000 µs should measure within ±2 µs, representing ±0.1% precision. Systematic errors beyond ±5% indicate incorrect prescaler calculation, misread APB1 clock frequency, or failure to account for the timer clock doubler. Jitter—cycle-to-cycle period variation—should remain below 1 µs, limited by interrupt latency if other enabled interrupts preempt execution between GPIO writes, or by bus arbitration if concurrent DMA transfers delay peripheral access.

Prescaler accuracy verification modifies PSC to generate intentionally incorrect tick rates. Setting PSC = 167 (divide by 168) targets 2 µs per tick on 84 MHz clock, doubling the delay per ARR count. With ARR = 500, the `delay_us(1000)` call generates a 1000 µs delay nominally, but with 2 µs ticks, the actual delay becomes 2 × 500 = 1000 µs only if the function argument is reinterpreted as tick count rather than microsecond duration. This diagnostic confirms whether the firmware correctly translates time durations into timer register values, exposing off-by-factor-of-N errors common when engineers confuse clock frequencies, prescaler values, and desired output timing.

The interrupt-driven alternative to polled delay frees CPU cycles for other tasks during the waiting period. Enabling the update interrupt via DIER (DMA/Interrupt Enable Register) at offset `+0x0C`, bit 0 (UIE), triggers an interrupt when UIF asserts, vectoring execution to the TIM2 global interrupt handler. The NVIC (Nested Vectored Interrupt Controller) requires interrupt enablement through the NVIC_ISER0 register for interrupt number 28 (TIM2), and priority configuration via NVIC_IPR7. The interrupt service routine clears UIF to acknowledge the event, sets a volatile flag visible to mainline code, and returns, allowing the main loop to proceed with other work while the timer counts in the background. Comparing polled versus interrupt-driven latency via oscilloscope reveals the interrupt overhead: typically 12–20 CPU cycles from UIF assertion to ISR entry, translating to 70–120 nanoseconds at 168 MHz, insignificant for millisecond-scale delays but critical for sub-10-microsecond response requirements in motor commutation or real-time communication protocols.

## Exercise 2: Parameter Variation & Empirical Analysis

### Baud Rate Tolerance Testing and Error Propagation

UART communication reliability degenerates when transmitter and receiver baud rate clocks deviate beyond the bit-sampling tolerance window, typically ±2% for standard 8N1 framing without hardware flow control. This exercise systematically varies the BRR register across ±10% of nominal 115200 baud configuration, measuring bit error rate through echo loopback testing and correlating transmission success with oscilloscope-measured bit period deviation. The operational learning objective establishes the empirical relationship between clock accuracy requirements and communication distance, cable capacitance, and receiver oversampling factor.

The nominal BRR value for 115200 baud on 42 MHz APB1 clock calculates to `0x016C` (22.75 decimal equivalent), achieving 115207 baud actual rate with +0.006% error. Introducing intentional misconfiguration explores the failure threshold: BRR values of `0x0150` (20.0 decimal, 131.25 kHz, +14% error) and `0x0190` (25.0 decimal, 105 kHz, -8.9% error) bracket the acceptable tolerance range. The test procedure programs the transmitter with nominal BRR while varying the receiver across this range, connecting USART2 TX to USART3 RX via a 10 cm jumper wire on the breadboard. Software transmits a 256-byte test pattern—incrementing sequence 0x00 through 0xFF—while the receiver compares incoming bytes against the expected pattern, logging mismatch count and the first error position.

The receiver oversampling factor influences tolerance to baud rate mismatch. STM32 USART peripherals default to 16× oversampling, sampling each bit 16 times within the bit period and selecting the majority value among the center 3 samples. This provides immunity to single-sample noise spikes but constrains the maximum baud rate deviation to approximately ±2% before the sampling window misaligns with the actual bit cell center. Reducing oversampling to 8× via CR1 bit 15 (OVER8) doubles the maximum baud rate achievable on a given peripheral clock (up to APB1/8 versus APB1/16) at the cost of tightened tolerance to ±1% error. The exercise compares 16× versus 8× oversampling by measuring the BRR value at which the first frame error occurs, plotting error rate versus baud rate offset percentage.

Frame error detection activates by enabling the FE (Framing Error) flag monitoring in USART_SR bit 1, which asserts when the receiver detects a low stop bit indicating asynchronous misalignment between transmitter and receiver. The interrupt-driven receiver ISR reads SR, then DR to clear the error flag, incrementing a frame-error counter accessible to the main diagnostic loop. Oscilloscope triggering on the RX pin with persistence mode enabled overlays multiple frame captures, revealing the progressive shift of bit cell boundaries as baud rate mismatch accumulates across the 10-bit frame. At +3% transmitter baud error, the 10th bit (stop bit) samples approximately 3% × 10 = 30% into the following start bit, visually apparent as the stop bit reading low rather than high.

The complete test harness automates parameter sweeping:

```c
#include <stdint.h>
#include <stdio.h>

#define USART2_BASE     0x40004400UL
#define USART3_BASE     0x40004800UL
#define USART_SR(base)  (*(volatile uint32_t *)((base) + 0x00))
#define USART_DR(base)  (*(volatile uint32_t *)((base) + 0x04))
#define USART_BRR(base) (*(volatile uint32_t *)((base) + 0x08))
#define USART_CR1(base) (*(volatile uint32_t *)((base) + 0x0C))

typedef struct {
    uint16_t brr_value;
    uint32_t error_count;
    uint32_t first_error_position;
} baud_test_result_t;

void usart_set_brr(uint32_t base, uint16_t brr) {
    USART_CR1(base) &= ~(1 << 13);  // Disable USART
    USART_BRR(base) = brr;
    USART_CR1(base) |= (1 << 13);   // Re-enable USART
}

baud_test_result_t test_baud_tolerance(uint16_t tx_brr, uint16_t rx_brr) {
    baud_test_result_t result = { rx_brr, 0, 0xFFFFFFFF };
    
    usart_set_brr(USART2_BASE, tx_brr);
    usart_set_brr(USART3_BASE, rx_brr);
    
    for (uint16_t i = 0; i < 256; i++) {
        // Transmit byte on USART2
        while (!(USART_SR(USART2_BASE) & (1 << 7)));
        USART_DR(USART2_BASE) = i;
        
        // Receive byte on USART3 with timeout
        uint32_t timeout = 100000;
        while (!(USART_SR(USART3_BASE) & (1 << 5)) && timeout--);
        
        if (timeout == 0) {
            result.error_count++;
            if (result.first_error_position == 0xFFFFFFFF) {
                result.first_error_position = i;
            }
            continue;
        }
        
        uint8_t received = USART_DR(USART3_BASE) & 0xFF;
        if (received != (i & 0xFF)) {
            result.error_count++;
            if (result.first_error_position == 0xFFFFFFFF) {
                result.first_error_position = i;
            }
        }
    }
    
    return result;
}

int main(void) {
    // Initialize USART2 TX on PA2, USART3 RX on PB11
    // (GPIO and clock configuration omitted for brevity)
    
    const uint16_t nominal_brr = 0x016C;  // 115200 baud
    
    // Sweep receiver BRR from -10% to +10%
    for (int16_t offset_percent = -10; offset_percent <= 10; offset_percent++) {
        uint16_t test_brr = nominal_brr * (100 + offset_percent) / 100;
        baud_test_result_t result = test_baud_tolerance(nominal_brr, test_brr);
        
        printf("RX BRR=0x%04X (%+d%%), Errors=%lu, First@%lu\r\n",
               result.brr_value, offset_percent, result.error_count, result.first_error_position);
    }
    
    while (1);
}
```

Expected results demonstrate error-free transmission within ±2% range (offset -2% to +2%), occasional errors at ±3%, and complete failure beyond ±5%. The first error position correlates with frame length: longer frames accumulate more timing error per byte. At +5% mismatch, the 10-bit frame accumulates 0.5 bit of slippage, causing the receiver to sample the stop bit midway through, intermittently detecting framing errors. The exercise quantifies this by logging the specific byte index where the first error occurs, observing that errors appear sooner (lower byte count) as baud mismatch increases.

Cable capacitance impact becomes measurable by extending the UART connection to 3 meters using CAT5 twisted-pair cable (approximately 50 pF/meter capacitance), increasing total load to ~150 pF from the nominal 30 pF of a 10 cm breadboard trace. The increased capacitance slows rise/fall times, reducing noise margin and effectively narrowing the baud rate tolerance window. Repeating the BRR sweep with the 3-meter cable shifts the error threshold inward: where the short connection tolerated ±2.5%, the long cable fails at ±1.8%, demonstrating the real-world constraint that high-speed serial communication over extended distances requires tighter clock accuracy or reduced baud rates.

Temperature-induced drift emulation artificially varies the system clock frequency by modifying the PLL multiplier in RCC_PLLCFGR, simulating crystal oscillator thermal coefficient effects. Reducing the PLL multiplier from 168 to 160 drops system frequency by ~4.8%, propagating through APB1 and timer clocks to shift UART baud rate by the same percentage. Re-running the tolerance sweep with this offset demonstrates how temperature extremes or manufacturing variance in crystal oscillators degrades communication margins, informing component selection requirements for industrial environments where -40°C to +85°C operation mandates ±20 ppm crystal tolerance and temperature-compensated oscillators (TCXO) for critical links.

### ADC Sampling Rate and Conversion Latency Profiling

Analog-to-digital conversion introduces sampling rate constraints, quantization noise, and aperture jitter that bound the maximum signal bandwidth and amplitude resolution achievable in sensor acquisition chains. This exercise profiles the STM32F407 ADC peripheral across sampling rates from 3 cycles/sample to 480 cycles/sample, measuring conversion latency via GPIO toggle instrumentation and characterizing effective number of bits (ENOB) through statistical analysis of converted samples from a precision voltage reference. The operational methodology exposes the tradeoff between throughput and precision, guiding practitioner selection of ADC parameters for motion control feedback loops versus slow environmental monitoring.

The STM32F407 integrates three 12-bit successive-approximation ADCs sharing a common 30 MHz maximum clock derived from APB2 via programmable prescaler. ADC1 base address `0x40012000` requires RCC_APB2ENR bit 8 enablement and ADC prescaler configuration in ADC_CCR (Common Control Register) at `0x40012300 + 0x04`, bits [17:16] selecting divide-by-2/4/6/8 prescaler. For 168 MHz system clock with APB2 at 84 MHz, a divide-by-4 prescaler yields 21 MHz ADC clock, safely below the 30 MHz maximum while providing 1.75 MHz maximum theoretical conversion rate (12-bit conversion + sampling time).

Sampling time configuration occurs per-channel via SMPRx registers, where each 3-bit field selects from eight durations: 3, 15, 28, 56, 84, 112, 144, or 480 ADC clock cycles. For ADC1 channel 0 (PA0), the SMPR2 register at offset `+0x10` bits [2:0] control sampling duration. The total conversion time combines sampling time and the fixed 12-cycle SAR conversion: at 21 MHz ADC clock with 3-cycle sampling, one conversion requires (3 + 12) / 21 MHz = 714 nanoseconds, yielding 1.4 MSps maximum throughput. Increasing sampling time to 480 cycles extends conversion to (480 + 12) / 21 MHz = 23.4 microseconds, reducing throughput to 42.7 kSps but improving settling for high-impedance sources and reducing quantization noise through effective oversampling.

The test procedure configures a precision 1.000V reference voltage (LM4040-1.0 or similar) connected to PA0 through a 1 kΩ series resistor, loading the ADC with realistic source impedance. GPIO PD12 toggles high immediately before initiating conversion (via ADC_CR2 SWSTART bit) and toggles low immediately after reading the ADC_DR register, providing oscilloscope-measurable conversion latency. Repeating 10,000 conversions at each sampling time setting accumulates a statistical distribution of ADC readings, from which mean, standard deviation, and ENOB calculate via the formula ENOB = (SINAD - 1.76) / 6.02, where SINAD derives from signal power versus noise power in the sample histogram.

The implementation demonstrates latency measurement:

```c
#include <stdint.h>
#include <math.h>

#define RCC_BASE        0x40023800UL
#define RCC_APB2ENR     (*(volatile uint32_t *)(RCC_BASE + 0x44))
#define RCC_AHB1ENR     (*(volatile uint32_t *)(RCC_BASE + 0x30))

#define GPIOA_BASE      0x40020000UL
#define GPIOA_MODER     (*(volatile uint32_t *)(GPIOA_BASE + 0x00))

#define GPIOD_BASE      0x40020C00UL
#define GPIOD_MODER     (*(volatile uint32_t *)(GPIOD_BASE + 0x00))
#define GPIOD_BSRR      (*(volatile uint32_t *)(GPIOD_BASE + 0x18))

#define ADC1_BASE       0x40012000UL
#define ADC_SR          (*(volatile uint32_t *)(ADC1_BASE + 0x00))
#define ADC_CR1         (*(volatile uint32_t *)(ADC1_BASE + 0x04))
#define ADC_CR2         (*(volatile uint32_t *)(ADC1_BASE + 0x08))
#define ADC_SMPR2       (*(volatile uint32_t *)(ADC1_BASE + 0x10))
#define ADC_SQR1        (*(volatile uint32_t *)(ADC1_BASE + 0x2C))
#define ADC_SQR3        (*(volatile uint32_t *)(ADC1_BASE + 0x34))
#define ADC_DR          (*(volatile uint32_t *)(ADC1_BASE + 0x4C))
#define ADC_CCR         (*(volatile uint32_t *)(0x40012300 + 0x04))

typedef enum {
    ADC_SAMPLE_3   = 0,
    ADC_SAMPLE_15  = 1,
    ADC_SAMPLE_28  = 2,
    ADC_SAMPLE_56  = 3,
    ADC_SAMPLE_84  = 4,
    ADC_SAMPLE_112 = 5,
    ADC_SAMPLE_144 = 6,
    ADC_SAMPLE_480 = 7
} adc_sample_time_t;

void adc_init(adc_sample_time_t sample_time) {
    RCC_AHB1ENR |= (1 << 0);    // GPIOA clock
    RCC_APB2ENR |= (1 << 8);    // ADC1 clock
    
    // Configure PA0 as analog input
    GPIOA_MODER |= (3 << 0);
    
    // ADC prescaler: divide APB2 by 4 (84 MHz / 4 = 21 MHz)
    ADC_CCR = (1 << 16);
    
    // Set sampling time for channel 0
    ADC_SMPR2 = (sample_time << 0);
    
    // Configure single conversion, channel 0
    ADC_SQR1 = 0;                 // 1 conversion
    ADC_SQR3 = 0;                 // Channel 0 first
    
    // Enable ADC, single conversion mode
    ADC_CR2 = (1 << 0);           // ADON
    
    // Configure PD12 for latency measurement
    GPIOD_MODER = (GPIOD_MODER & ~(3 << 24)) | (1 << 24);
}

uint16_t adc_read_single(void) {
    GPIOD_BSRR = (1 << 12);       // Set PD12 high
    ADC_CR2 |= (1 << 30);         // Start conversion (SWSTART)
    while (!(ADC_SR & (1 << 1))); // Wait for EOC
    uint16_t result = ADC_DR;
    GPIOD_BSRR = (1 << 28);       // Set PD12 low
    return result;
}

typedef struct {
    adc_sample_time_t sample_time;
    float mean;
    float std_dev;
    float enob;
    uint32_t sample_count;
} adc_statistics_t;

adc_statistics_t characterize_adc(adc_sample_time_t sample_time, uint32_t samples) {
    adc_statistics_t stats = { sample_time, 0.0f, 0.0f, 0.0f, samples };
    
    adc_init(sample_time);
    
    // Accumulate samples for mean calculation
    uint64_t sum = 0;
    uint16_t *buffer = malloc(samples * sizeof(uint16_t));
    
    for (uint32_t i = 0; i < samples; i++) {
        buffer[i] = adc_read_single();
        sum += buffer[i];
    }
    
    stats.mean = (float)sum / samples;
    
    // Calculate standard deviation
    float variance_sum = 0.0f;
    for (uint32_t i = 0; i < samples; i++) {
        float deviation = buffer[i] - stats.mean;
        variance_sum += deviation * deviation;
    }
    
    stats.std_dev = sqrtf(variance_sum / samples);
    
    // Calculate ENOB (simplified, assuming full-scale sine input)
    // RMS noise = std_dev, RMS signal ≈ mean for DC input
    float snr_db = 20.0f * log10f(stats.mean / stats.std_dev);
    stats.enob = (snr_db - 1.76f) / 6.02f;
    
    free(buffer);
    return stats;
}

int main(void) {
    const adc_sample_time_t test_times[] = {
        ADC_SAMPLE_3, ADC_SAMPLE_15, ADC_SAMPLE_28, ADC_SAMPLE_56,
        ADC_SAMPLE_84, ADC_SAMPLE_112, ADC_SAMPLE_144, ADC_SAMPLE_480
    };
    
    for (uint8_t i = 0; i < 8; i++) {
        adc_statistics_t stats = characterize_adc(test_times[i], 10000);
        printf("Sample Time %d: Mean=%.2f, StdDev=%.3f, ENOB=%.2f\r\n",
               test_times[i], stats.mean, stats.std_dev, stats.enob);
    }
    
    while (1);
}
```

Oscilloscope measurement of PD12 pulse width quantifies conversion latency across sampling time settings. At 3-cycle sampling, the pulse measures approximately 714 ns matching the theoretical calculation. At 480-cycle sampling, the pulse extends to 23.4 µs. Plotting latency versus sampling time confirms the linear relationship with slope determined by ADC clock frequency, validating the timing model and confirming correct prescaler configuration.

Statistical analysis reveals ENOB improvement with longer sampling times. At 3-cycle sampling with 1 kΩ source impedance, the ADC input capacitor (typically 4–12 pF) lacks sufficient charging time, introducing sample-to-sample variation that manifests as increased standard deviation (0.8–1.2 LSB) and reduced ENOB (10.5–11.0 bits from the nominal 12-bit converter). Extending to 480-cycle sampling allows full capacitor settling, reducing standard deviation to 0.3–0.5 LSB and achieving 11.5+ ENOB. The practitioner learns that datasheet 12-bit resolution represents only the quantization step size; effective resolution depends critically on analog front-end design and sampling time selection.

Source impedance sweeping explores the settling time requirement by replacing the 1 kΩ series resistor with 10 kΩ, 100 kΩ, and 1 MΩ values, measuring ENOB degradation at fixed 3-cycle sampling time. The 100 kΩ source produces 2–3 LSB standard deviation, effectively reducing ENOB to 9 bits, while 1 MΩ sources yield 10+ LSB noise (ENOB below 8 bits). The STM32F407 datasheet specifies 50 kΩ maximum recommended source impedance for 12-bit accuracy at minimum sampling time; this exercise empirically validates that specification and demonstrates the necessity of op-amp buffering for high-impedance sensors like pH electrodes or piezoelectric accelerometers.

DMA-based continuous acquisition eliminates the software polling overhead visible as inter-conversion dead time in oscilloscope captures. Configuring ADC in continuous conversion mode (ADC_CR2 CONT bit) with DMA triggering (ADC_CR2 DDS and DMA bits enabled) automatically transfers each ADC_DR reading to a memory buffer without CPU intervention, achieving back-to-back conversions limited only by the ADC conversion time. Comparing DMA versus polled acquisition via oscilloscope reveals the polling overhead: polled mode shows 2–5 µs gaps between conversions (firmware loop overhead), while DMA mode achieves continuous 714 ns period at 3-cycle sampling. This operational difference matters for real-time applications like motor current sensing requiring 100+ kSps sustained throughput without CPU saturation.

### Interrupt Latency Characterization Under Load

Interrupt response time—the interval between external interrupt assertion and ISR entry—determines the minimum achievable control loop update rate in real-time embedded systems. This exercise instruments EXTI (External Interrupt) line 0 with GPIO PA0 toggling via function generator, measuring GPIO PD12 output toggle within the ISR to quantify latency via oscilloscope dual-channel capture. Parameter variations include interrupt priority, concurrent interrupts, CPU loading via busy-wait loops, and interrupt nesting enablement, establishing the empirical relationship between system load and worst-case latency bounds.

EXTI line configuration multiplexes GPIO pins across all ports onto 16 external interrupt lines, where EXTI0 can monitor PA0, PB0, PC0, etc., selected via SYSCFG_EXTICR1 register. For PA0 as interrupt source, SYSCFG_EXTICR1 bits [3:0] clear to `0000` selecting Port A. The EXTI peripheral at base `0x40013C00` requires interrupt mask register (IMR) bit 0 set to unmask EXTI0, rising trigger selection register (RTSR) or falling trigger selection register (FTSR) bit 0 set to enable edge sensitivity, and pending register (PR) bit 0 written to 1 for flag clearing within the ISR. The NVIC enables EXTI0 interrupt via NVIC_ISER0 bit 6 (interrupt number 6) and configures priority through NVIC_IPR1 bits [23:20], where lower numerical values indicate higher priority.

The test harness configures PA0 for external interrupt and PD12 for ISR latency measurement:

```c
#include <stdint.h>

#define RCC_BASE          0x40023800UL
#define RCC_AHB1ENR       (*(volatile uint32_t *)(RCC_BASE + 0x30))
#define RCC_APB2ENR       (*(volatile uint32_t *)(RCC_BASE + 0x44))

#define GPIOA_BASE        0x40020000UL
#define GPIOA_MODER       (*(volatile uint32_t *)(GPIOA_BASE + 0x00))
#define GPIOA_PUPDR       (*(volatile uint32_t *)(GPIOA_BASE + 0x0C))

#define GPIOD_BASE        0x40020C00UL
#define GPIOD_MODER       (*(volatile uint32_t *)(GPIOD_BASE + 0x00))
#define GPIOD_BSRR        (*(volatile uint32_t *)(GPIOD_BASE + 0x18))

#define SYSCFG_BASE       0x40013800UL
#define SYSCFG_EXTICR1    (*(volatile uint32_t *)(SYSCFG_BASE + 0x08))

#define EXTI_BASE         0x40013C00UL
#define EXTI_IMR          (*(volatile uint32_t *)(EXTI_BASE + 0x00))
#define EXTI_RTSR         (*(volatile uint32_t *)(EXTI_BASE + 0x08))
#define EXTI_FTSR         (*(volatile uint32_t *)(EXTI_BASE + 0x0C))
#define EXTI_PR           (*(volatile uint32_t *)(EXTI_BASE + 0x14))

#define NVIC_ISER0        (*(volatile uint32_t *)(0xE000E100))
#define NVIC_IPR1         (*(volatile uint32_t *)(0xE000E404))

volatile uint32_t interrupt_count = 0;

void EXTI0_IRQHandler(void) {
    GPIOD_BSRR = (1 << 12);       // Set PD12 high (ISR entry marker)
    
    // Simulated ISR workload (configurable)
    for (volatile uint32_t i = 0; i < 100; i++);
    
    EXTI_PR = (1 << 0);           // Clear pending flag
    GPIOD_BSRR = (1 << 28);       // Set PD12 low (ISR exit marker)
    interrupt_count++;
}

void exti_init(void) {
    RCC_AHB1ENR |= (1 << 0) | (1 << 3);  // GPIOA, GPIOD
    RCC_APB2ENR |= (1 << 14);            // SYSCFG
    
    // Configure PA0 as input with pull-down
    GPIOA_MODER &= ~(3 << 0);
    GPIOA_PUPDR = (GPIOA_PUPDR & ~(3 << 0)) | (2 << 0);
    
    // Configure PD12 as output for latency measurement
    GPIOD_MODER = (GPIOD_MODER & ~(3 << 24)) | (1 << 24);
    
    // Connect PA0 to EXTI0
    SYSCFG_EXTICR1 &= ~(0xF << 0);
    
    // Configure EXTI0 for rising edge
    EXTI_IMR |= (1 << 0);
    EXTI_RTSR |= (1 << 0);
    EXTI_FTSR &= ~(1 << 0);
    
    // Set EXTI0 interrupt priority to 0 (highest)
    NVIC_IPR1 = (NVIC_IPR1 & ~(0xFF << 16)) | (0x00 << 20);
    
    // Enable EXTI0 interrupt in NVIC
    NVIC_ISER0 |= (1 << 6);
}

int main(void) {
    exti_init();
    
    while (1) {
        // Mainline CPU loading (configurable)
        __asm__ volatile ("nop");
    }
}
```

Function generator configuration applies a 1 kHz, 3.3V peak square wave to PA0, providing 1 ms period with 500 µs high/low phases. Oscilloscope channel 1 connects to PA0 (interrupt source), channel 2 to PD12 (ISR execution marker), with triggering on channel 1 rising edge. Cursor measurements from PA0 rising edge to PD12 rising edge quantify interrupt latency. For an unloaded system (mainline executing NOPs), typical latency measures 700–900 nanoseconds, representing interrupt detection (1–2 cycles), pipeline flush (2–3 cycles), vector fetch (2 cycles), register stacking (12 cycles for Cortex-M4 with FPU), and ISR prologue (4–6 cycles).

Priority inversion demonstration introduces a second interrupt source (EXTI1 on PA1) configured with lower priority (NVIC_IPR1 bits [31:28] set to `0x10` versus `0x00` for EXTI0). When both interrupts assert simultaneously—achieved by triggering PA0 and PA1 via dual-channel function generator with synchronous output—EXTI0 preempts EXTI1 regardless of assertion order, confirming priority enforcement. Oscilloscope captures show PD12 toggling for EXTI0 ISR before PD13 (added for EXTI1 visualization) toggles, with the delay between PD12 return low and PD13 rising edge representing the EXTI1 queuing delay.

CPU loading impact emerges by replacing mainline NOPs with computational work: a floating-point intensive loop calculating sine/cosine or a memory-intensive loop copying 1 KB buffers. Repeating the latency measurement under varying mainline load reveals minimal impact (< 5% latency increase) because interrupts preempt mainline code immediately. However, if the mainline loop disables interrupts via `__disable_irq()` intrinsic during critical sections, latency increases to include the maximum critical section duration, emphasizing the importance of minimizing interrupt-disabled regions in real-time systems.

Nested interrupt testing enables interrupt preemption by setting the PRIMASK register to allow higher-priority interrupts during ISR execution. The default Cortex-M behavior disables interrupts of equal or lower priority during ISR execution; enabling nesting permits a high-priority interrupt to preempt a lower-priority ISR. The test configures EXTI0 (priority 0) and TIM2 update interrupt (priority 1), triggering TIM2 interrupt mid-EXTI0 ISR execution by starting a timer with 50 µs period during the EXTI0 ISR. Oscilloscope capture shows PD12 high for EXTI0 entry, PD13 pulsing high for TIM2 ISR preemption, then PD12 returning low after TIM2 ISR completes, demonstrating the nesting behavior visually.

Worst-case latency bounds emerge from stress testing: mainline code executing continuous DMA transfers, SPI transactions, and ADC conversions saturates the AHB bus, delaying interrupt vector fetch from Flash memory. Measuring latency under full bus saturation yields 1.5–2.5 µs worst-case, representing Flash wait states (typically 5 cycles at 168 MHz for 3.3V supply) and bus arbitration delays. This empirical data informs the practitioner that interrupt-critical applications requiring < 1 µs response must place ISR code in tightly-coupled memory (CCM on STM32F4) or configure vector table in SRAM to eliminate Flash access latency.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Watchdog Timer Expiration and Reset Recovery

The independent watchdog timer (IWDG) provides last-resort protection against firmware runaway conditions where software fails to execute the periodic watchdog refresh sequence, triggering a system reset to restore operation. This exercise deliberately starves the watchdog timer through infinite loops, clock misconfiguration, and interrupt priority inversion, observing reset behavior via oscilloscope capture of the reset pin and validating firmware restart through persistent SRAM flag inspection. The operational methodology establishes watchdog configuration best practices, quantifying the minimum refresh interval overhead and measuring reset propagation delay through external hardware.

The IWDG peripheral operates from the 32 kHz LSI (Low-Speed Internal) oscillator independent of the main system clock, ensuring watchdog functionality persists through HSE oscillator failure or PLL lock loss. IWDG base address `0x40003000` provides key register (KR) at offset `+0x00` for unlock/refresh commands, prescaler register (PR) at offset `+0x04` dividing LSI by 4 to 256, and reload register (RLR) at offset `+0x08` defining the countdown value from 0 to 4095. Timeout calculation follows: period = (4 × 2^PR × RLR) / LSI_frequency, where PR ranges 0–7 and LSI typically measures 32 kHz ±10%.

Configuration begins by writing `0xCCCC` to IWDG_KR to start the watchdog, followed by `0x5555` to unlock PR and RLR write access. Setting PR = 4 (divide by 64) and RLR = 4095 yields maximum timeout: (4 × 64 × 4095) / 32000 = 32.76 seconds. Writing `0xAAAA` to KR refreshes the counter to RLR, resetting the timeout. The firmware must call this refresh sequence within the timeout period or the IWDG forces a system reset by asserting the internal reset line, indistinguishable from pressing the reset button.

The test implementation configures a 2-second watchdog timeout and deliberately fails to refresh:

```c
#include <stdint.h>

#define IWDG_BASE       0x40003000UL
#define IWDG_KR         (*(volatile uint32_t *)(IWDG_BASE + 0x00))
#define IWDG_PR         (*(volatile uint32_t *)(IWDG_BASE + 0x04))
#define IWDG_RLR        (*(volatile uint32_t *)(IWDG_BASE + 0x08))
#define IWDG_SR         (*(volatile uint32_t *)(IWDG_BASE + 0x0C))

#define RCC_BASE        0x40023800UL
#define RCC_CSR         (*(volatile uint32_t *)(RCC_BASE + 0x74))

#define GPIOD_BASE      0x40020C00UL
#define GPIOD_BSRR      (*(volatile uint32_t *)(GPIOD_BASE + 0x18))

#define SRAM_PERSIST    (*(volatile uint32_t *)(0x2001FFF0))

typedef enum {
    RESET_UNKNOWN = 0,
    RESET_POR     = 1,
    RESET_PIN     = 2,
    RESET_IWDG    = 3,
    RESET_WWDG    = 4,
    RESET_SFTR    = 5
} reset_cause_t;

reset_cause_t get_reset_cause(void) {
    uint32_t csr = RCC_CSR;
    reset_cause_t cause = RESET_UNKNOWN;
    
    if (csr & (1 << 31)) cause = RESET_POR;       // Low-power reset
    else if (csr & (1 << 26)) cause = RESET_PIN;  // Reset pin
    else if (csr & (1 << 29)) cause = RESET_IWDG; // IWDG reset
    else if (csr & (1 << 30)) cause = RESET_WWDG; // WWDG reset
    else if (csr & (1 << 28)) cause = RESET_SFTR; // Software reset
    
    RCC_CSR |= (1 << 24);  // Clear reset flags (RMVF)
    return cause;
}

void iwdg_init(uint16_t timeout_ms) {
    // Calculate PR and RLR for timeout_ms on 32 kHz LSI
    // timeout = (4 * 2^PR * RLR) / 32000
    // For 2000 ms: (4 * 64 * RLR) / 32000 = 2.0 → RLR = 250
    
    IWDG_KR = 0x5555;       // Unlock PR and RLR
    IWDG_PR = 4;            // Prescaler divide by 64
    IWDG_RLR = 250;         // Reload value for 2 s
    
    while (IWDG_SR & 0x3);  // Wait for PR and RLR update
    
    IWDG_KR = 0xCCCC;       // Start watchdog
}

void iwdg_refresh(void) {
    IWDG_KR = 0xAAAA;       // Refresh watchdog
}

int main(void) {
    reset_cause_t reset_cause = get_reset_cause();
    
    // Check persistent SRAM flag to count consecutive watchdog resets
    if (reset_cause != RESET_POR && reset_cause != RESET_PIN) {
        SRAM_PERSIST++;
    } else {
        SRAM_PERSIST = 0;
    }
    
    // Initialize GPIO PD12-PD15 to display reset count in binary
    // (GPIO init code omitted for brevity)
    
    // Display reset count on LEDs
    uint32_t count = SRAM_PERSIST & 0xF;
    if (count & 1) GPIOD_BSRR = (1 << 12);
    if (count & 2) GPIOD_BSRR = (1 << 13);
    if (count & 4) GPIOD_BSRR = (1 << 14);
    if (count & 8) GPIOD_BSRR = (1 << 15);
    
    iwdg_init(2000);
    
    // Deliberate failure: infinite loop without watchdog refresh
    while (1) {
        // No IWDG refresh call here
        for (volatile uint32_t i = 0; i < 1000000; i++);
    }
}
```

Oscilloscope measurement connects channel 1 to the NRST (reset) pin with 10 kΩ pull-up to 3.3V, triggering on falling edge. Upon IWDG timeout, NRST pulls low for approximately 20 µs (internal reset pulse width), then returns high as the microcontroller restarts. Measuring the time from program start (identifiable via PD12 initial toggle) to reset pulse yields the configured 2-second timeout, validating IWDG configuration accuracy. The LED pattern increments with each reset, demonstrating that SRAM content persists through IWDG reset but clears on power-on reset, providing a mechanism for reset-cause logging in production firmware.

LSI frequency calibration addresses the ±10% tolerance affecting watchdog timeout accuracy. The TIM5 peripheral captures LSI cycles relative to the HSE crystal—a precise reference—by configuring TIM5 input capture on channel 4 multiplexed to the LSI clock source. Measuring 10 consecutive LSI periods via timer capture and averaging yields the actual LSI frequency, enabling runtime compensation of IWDG timeout calculations. For example, if calibration reveals LSI at 28.8 kHz instead of the nominal 32 kHz, the firmware scales RLR proportionally to maintain target timeout accuracy within ±2%.

Interrupt priority inversion failure mode disables interrupts globally via `__disable_irq()` within a critical section that executes longer than the watchdog timeout. The test deliberately inserts a 3-second critical section after initializing a 2-second watchdog, demonstrating that even correct watchdog refresh calls cannot execute if interrupts remain masked. Oscilloscope capture shows NRST asserting after 2 seconds despite the presence of `iwdg_refresh()` calls in the source code, illustrating the critical requirement that watchdog refresh must execute at base priority level (no interrupt masking) to provide effective supervision.

Brown-out detection interaction complicates watchdog behavior during marginal power supply conditions. The STM32F4 integrates a brownout reset (BOR) that triggers at selectable thresholds: 1.8V, 2.1V, 2.4V, or 2.7V configured via option bytes. When supply voltage sags below the BOR threshold, the microcontroller enters reset immediately without waiting for IWDG timeout. The test injects controlled supply voltage droop using a laboratory power supply with programmable output voltage and electronic load, measuring the voltage at which reset occurs. Comparing IWDG-triggered resets (NRST pulse after 2 s) versus BOR-triggered resets (NRST immediate assertion as voltage drops) establishes the operational boundary where power supply quality must meet to avoid spurious resets masquerading as watchdog timeouts.

Recovery protocol after watchdog reset requires firmware to log the reset cause to non-volatile memory before restarting the failed task. The RCC_CSR register flags persist until explicitly cleared, enabling the bootloader or main application to detect whether the reset originated from power-on, external pin, software, window watchdog, or independent watchdog. Production firmware typically increments a persistent error counter in EEPROM or backup SRAM, transmits a diagnostic message via UART or CAN, and attempts graceful degradation (e.g., reverting to safe default configuration) rather than immediately restarting the faulted task. The exercise implements a three-strikes policy: after three consecutive IWDG resets, the firmware enters a fail-safe mode toggling an error LED at 1 Hz rather than re-attempting the faulted operation, awaiting external intervention.

### SPI Communication Under Clock Skew and Noise Injection

Serial Peripheral Interface bus timing margins degrade under clock skew between master and slave, transmission line reflections on long interconnects, and crosstalk-induced voltage glitches that corrupt data edges. This exercise stresses SPI communication between two STM32F407 devices by introducing deliberate clock phase offset, capacitive loading, and adjacent GPIO toggling noise, measuring bit error rate and characterizing setup/hold time violations via logic analyzer capture. The operational focus reveals the hardware-level failure modes that protocol analyzers and high-level drivers obscure, equipping the practitioner with diagnostic skills for field debugging multi-board SPI networks in industrial environments.

SPI1 peripheral on STM32F407 operates at maximum 42 MHz clock (APB2/2 prescaler minimum) in master mode, interfacing to external SPI slaves such as serial Flash (W25Q128), DAC (MCP4921), or sensor ICs (MPU6050). The standard four-wire interface consists of SCK (serial clock), MOSI (master-out-slave-in), MISO (master-in-slave-out), and CS (chip select, active low). Clock polarity (CPOL) and phase (CPHA) configure timing: CPOL=0/CPHA=0 samples data on rising edge, CPOL=0/CPHA=1 samples on falling edge, with corresponding transmit edge opposites. Mismatched CPOL/CPHA between master and slave shifts the sampling window by half a clock period, guaranteeing data corruption.

The baseline configuration connects SPI1 master (PA5 SCK, PA6 MISO, PA7 MOSI, PA4 CS) to SPI2 slave (PB13 SCK, PB14 MISO, PB15 MOSI, PB12 CS) via 10 cm breadboard jumpers, operating at 10.5 MHz (APB2 84 MHz divided by 8). Logic analyzer channels 0–3 monitor SCK, MOSI, MISO, CS respectively, triggering on CS falling edge. The software transmits a 256-byte incrementing pattern, with the slave echoing received bytes back to the master for comparison:

```c
#include <stdint.h>
#include <string.h>

#define SPI1_BASE       0x40013000UL
#define SPI2_BASE       0x40003800UL

#define SPI_CR1(base)   (*(volatile uint32_t *)((base) + 0x00))
#define SPI_CR2(base)   (*(volatile uint32_t *)((base) + 0x04))
#define SPI_SR(base)    (*(volatile uint32_t *)((base) + 0x08))
#define SPI_DR(base)    (*(volatile uint32_t *)((base) + 0x0C))

#define GPIOA_BASE      0x40020000UL
#define GPIOA_MODER     (*(volatile uint32_t *)(GPIOA_BASE + 0x00))
#define GPIOA_AFRL      (*(volatile uint32_t *)(GPIOA_BASE + 0x20))
#define GPIOA_AFRH      (*(volatile uint32_t *)(GPIOA_BASE + 0x24))
#define GPIOA_BSRR      (*(volatile uint32_t *)(GPIOA_BASE + 0x18))

void spi1_master_init(void) {
    // Enable clocks (GPIOA, SPI1)
    // Configure PA5/PA6/PA7 as AF5 (SPI1), PA4 as GPIO output (CS)
    GPIOA_MODER = (GPIOA_MODER & ~0xFF00) | 0xA900;
    GPIOA_AFRL = (GPIOA_AFRL & ~0xFFF00000) | 0x55500000;
    GPIOA_BSRR = (1 << 4);  // Set CS high (idle)
    
    // Configure SPI1: master, CPOL=0, CPHA=0, 10.5 MHz (BR=3, div by 8)
    SPI_CR1(SPI1_BASE) = (1 << 2)     // MSTR (master mode)
                       | (3 << 3)     // BR (baud rate prescaler /8)
                       | (1 << 9)     // SSM (software slave management)
                       | (1 << 8);    // SSI (internal slave select)
    
    SPI_CR1(SPI1_BASE) |= (1 << 6);   // SPE (SPI enable)
}

void spi2_slave_init(void) {
    // Configure PB12/PB13/PB14/PB15 as AF5 (SPI2)
    // Configure SPI2: slave, CPOL=0, CPHA=0
    SPI_CR1(SPI2_BASE) = 0;           // Slave mode (MSTR=0)
    SPI_CR1(SPI2_BASE) |= (1 << 6);   // SPE (SPI enable)
}

uint8_t spi1_transfer(uint8_t data) {
    GPIOA_BSRR = (1 << 20);           // CS low (start transaction)
    
    while (!(SPI_SR(SPI1_BASE) & (1 << 1)));  // Wait TXE
    SPI_DR(SPI1_BASE) = data;
    
    while (!(SPI_SR(SPI1_BASE) & (1 << 0)));  // Wait RXNE
    uint8_t received = SPI_DR(SPI1_BASE);
    
    while (SPI_SR(SPI1_BASE) & (1 << 7));     // Wait BSY clear
    GPIOA_BSRR = (1 << 4);            // CS high (end transaction)
    
    return received;
}

void spi2_slave_echo(void) {
    while (!(SPI_SR(SPI2_BASE) & (1 << 0)));  // Wait RXNE
    uint8_t received = SPI_DR(SPI2_BASE);
    
    while (!(SPI_SR(SPI2_BASE) & (1 << 1)));  // Wait TXE
    SPI_DR(SPI2_BASE) = received;
}

typedef struct {
    uint32_t transmitted;
    uint32_t errors;
    uint8_t first_error_position;
    uint8_t first_error_expected;
    uint8_t first_error_received;
} spi_ber_result_t;

spi_ber_result_t spi_stress_test(uint32_t iterations) {
    spi_ber_result_t result = {0};
    
    for (uint32_t i = 0; i < iterations; i++) {
        uint8_t test_byte = i & 0xFF;
        uint8_t received = spi1_transfer(test_byte);
        result.transmitted++;
        
        if (received != test_byte) {
            result.errors++;
            if (result.errors == 1) {
                result.first_error_position = test_byte;
                result.first_error_expected = test_byte;
                result.first_error_received = received;
            }
        }
    }
    
    return result;
}

int main(void) {
    spi1_master_init();
    spi2_slave_init();
    
    spi_ber_result_t result = spi_stress_test(10000);
    
    printf("SPI Stress Test: %lu transmitted, %lu errors (%.3f%% BER)\r\n",
           result.transmitted, result.errors, 
           100.0f * result.errors / result.transmitted);
    
    if (result.errors > 0) {
        printf("First error at position %u: expected 0x%02X, got 0x%02X\r\n",
               result.first_error_position,
               result.first_error_expected,
               result.first_error_received);
    }
    
    while (1);
}
```

Baseline testing with 10 cm jumpers at 10.5 MHz yields zero errors over 10,000 transfers, confirming correct configuration. Logic analyzer capture shows clean SCK transitions with MOSI/MISO data valid centered in the clock high phase (CPHA=0), meeting setup and hold time requirements of 5 ns typical for 3.3V CMOS logic.

Clock phase mismatch injection reconfigures SPI2 slave with CPHA=1 (sample on falling edge) while maintaining SPI1 master at CPHA=0 (sample on rising edge). This half-clock-period offset shifts the slave's sampling window to capture data during the master's transition edge rather than the stable phase, producing random bit errors. Running the stress test yields 40–60% BER, with logic analyzer capture revealing the misalignment: slave samples occur at SCK falling edges when MOSI/MISO are transitioning rather than stable. The first error position varies due to propagation delay variations, but systematic analysis shows errors clustered around bit positions with slow edge rates (0x00 ↔ 0xFF transitions).

Capacitive loading stress extends the interconnect to 1 meter using coaxial cable (50 pF/meter) plus external 100 pF capacitor to ground at the slave end, totaling ~200 pF load. This slows SCK edge rates from < 5 ns to 20–30 ns, reducing noise margin and potentially violating setup/hold times at higher clock frequencies. Testing at 10.5 MHz shows error-free operation, but increasing to 21 MHz (BR=2, APB2/4) generates sporadic errors (0.1–1% BER) as the slower edges encroach on the 10 ns setup time requirement. Oscilloscope measurement of SCK rise time at the slave confirms 28 ns, exceeding the 20 ns maximum specified for reliable 21 MHz operation.

Crosstalk injection uses adjacent GPIO pins (PA8–PA11) toggling at maximum rate during SPI transfers, coupling noise onto the SPI signal traces through parasitic capacitance. Routing the SPI and GPIO traces in parallel on a breadboard at 2 mm spacing with 5 cm overlap generates 1–2 pF/cm mutual capacitance, coupling ~200 mV glitches onto SPI signals. The stress test reveals intermittent errors (0.01% BER) correlating with GPIO transition timing, captured on the logic analyzer as brief voltage deviations on MOSI/MISO coinciding with SCK sampling edges. Adding 22 Ω series termination resistors at the master SPI outputs damps ringing and reduces error rate to near-zero by matching the transmission line characteristic impedance.

Simultaneous transmission collision occurs when both master and slave attempt to drive MISO simultaneously due to incorrect CS timing. The test deliberately extends CS assertion by 2 clock cycles before and after the actual data transfer, overlapping with the slave's previous transaction. Logic analyzer capture shows MISO contention as both devices drive opposite levels, producing intermediate voltage (~1.6V) that neither 0 nor 1 logic levels recognize reliably. Current measurement on MISO reveals 20–40 mA spike during contention versus normal 2–4 mA, indicating potential for GPIO latchup if sustained. Correct CS timing—assert before first clock, deassert after last clock completes—eliminates contention and produces clean MISO transitions.

The final diagnostic integrates protocol analyzer software (Saleae Logic, sigrok PulseView) to decode SPI transactions automatically, flagging framing errors, parity mismatches, and unexpected CS behavior. Comparing raw waveform captures against decoded packet view distinguishes electrical signal integrity issues (glitches, slow edges, crosstalk) from protocol-level errors (incorrect byte count, wrong command sequence), accelerating root-cause diagnosis. The practitioner develops the skill to correlate software-level symptoms (incorrect sensor readings, Flash programming failures) with oscilloscope signatures (voltage overshoot, insufficient setup time) and protocol analyzer flags (MISO glitch during byte 47), enabling systematic field debugging without educated guessing.

## Operational Reference Guide & Diagnostic Checklist

### Peripheral Clock Configuration Verification Matrix

Microcontroller peripheral malfunction frequently traces to incorrect clock enablement or frequency misconfiguration rather than firmware logic errors. The following diagnostic procedure systematically verifies clock tree propagation from crystal oscillator through PLL multipliers to individual peripheral buses.

**Crystal Oscillator HSE Verification:**
1. Measure XTAL1 and XTAL2 pins with oscilloscope 10:1 probe, ground spring attached within 1 cm of microcontroller ground pin.
2. Confirm sinusoidal waveform at crystal fundamental frequency (8 MHz typical for STM32F407 Discovery).
3. Measure amplitude: expect 1.5–2.5V peak-peak; < 1V indicates insufficient oscillation, requiring load capacitor adjustment (C1/C2, typically 20–30 pF).
4. Check startup time: HSE should stabilize within 5 ms of power application; extended startup suggests crystal ESR > 80Ω spec limit.

**PLL Lock Indication:**
Read RCC_CR register bit 25 (PLLRDY); must read 1 before switching system clock to PLL output. Failure to lock indicates:
- Incorrect PLL multiplier (PLLN) / divider (PLLM/PLLP) configuration in RCC_PLLCFGR
- HSE failure propagating to PLL input
- VCO frequency outside 100–432 MHz operating range (VCO = HSE × PLLN / PLLM)

**Peripheral Clock Enable Audit:**
For each peripheral register access, verify corresponding bit set in RCC_AHB1ENR, RCC_AHB2ENR, RCC_APB1ENR, or RCC_APB2ENR:
- GPIOA–GPIOK: RCC_AHB1ENR bits 0–10
- USART1: RCC_APB2ENR bit 4
- USART2/3: RCC_APB1ENR bits 17–18
- SPI1: RCC_APB2ENR bit 12
- SPI2/3: RCC_APB1ENR bits 14–15
- TIM2–TIM5: RCC_APB1ENR bits 0–3
- ADC1–3: RCC_APB2ENR bits 8–10

Attempting register writes to unpowered peripherals produces no effect; reads return undefined values or 0x00000000.

**APB Prescaler Impact on Peripheral Frequency:**
APB1 and APB2 prescalers in RCC_CFGR bits [12:10] and [15:13] affect UART baud rate, timer tick rate, and ADC conversion time:
- If APB prescaler = 1, timer clock = APB clock
- If APB prescaler > 1, timer clock = 2 × APB clock (frequency doubler compensation)
- ADC clock always derives from APB2 without doubler: ADC_CLK = APB2 / ADC_prescaler

Verify actual frequencies by configuring timer to toggle GPIO at known rate, measuring with oscilloscope:
```c
TIM2_PSC = 0;          // No prescaler
TIM2_ARR = 839;        // If TIM2_CLK = 84 MHz, toggle at 100 kHz
// Measure GPIO toggle: 100 kHz ± 1 kHz confirms TIM2_CLK = 84 MHz
```

### UART Communication Failure Decision Tree

**Symptom: No transmission observed on oscilloscope**
1. Verify TX pin configured as alternate function (GPIOA_MODER bits [5:4] = 10 for PA2/USART2)
2. Verify AF selection (GPIOA_AFRL bits [11:8] = 0x07 for USART2)
3. Check USART clock enabled (RCC_APB1ENR bit 17 for USART2)
4. Confirm USART enabled (USART_CR1 bit 13 = 1, bit 3 = 1 for transmitter)
5. Read USART_SR bit 7 (TXE): if stuck at 0, transmit shift register jammed; disable/re-enable USART

**Symptom: Transmission visible but receiver shows garbled data**
1. Calculate expected bit period: 1 / baud_rate (8.68 µs for 115200 baud)
2. Measure actual bit period with oscilloscope cursors: deviation > ±3% indicates baud rate mismatch
3. Recalculate BRR: BRR = APB_clock / (16 × baud_rate) for 16× oversampling
4. Verify APB1 clock frequency: may differ from assumed value due to HSE frequency or PLL configuration error
5. Check terminal emulator settings: baud, parity, stop bits must exactly match USART configuration

**Symptom: Intermittent character loss**
1. Confirm RX pin has pull-up resistor (GPIOA_PUPDR bits [7:6] = 01) to prevent floating input noise
2. Check for buffer overrun: USART_SR bit 3 (ORE) indicates receiver overrun; software read DR too slowly
3. Enable receive interrupt (USART_CR1 bit 5 RXNEIE = 1) to reduce latency
4. Measure interrupt latency: time from RX stop bit to ISR entry should be < 100 µs; longer indicates interrupt priority conflict

**Symptom: Parity errors (USART_SR bit 0 = 1)**
1. Verify transmitter and receiver parity configuration match (USART_CR1 bits [10:9])
2. Check noise on RX line: scope shows glitches > 0.4V may corrupt bit values
3. Reduce baud rate to increase noise margin: 115200 → 57600 halves bit error rate in noisy environments

### GPIO Interrupt Troubleshooting Protocol

**EXTI Interrupt Not Firing:**
1. Verify GPIO clock enabled in RCC_AHB1ENR corresponding port bit
2. Check SYSCFG clock enabled (RCC_APB2ENR bit 14) for EXTI multiplexer configuration
3. Confirm SYSCFG_EXTICRx selects correct port for interrupt line
4. Verify EXTI_IMR bit set to unmask interrupt
5. Check EXTI_RTSR or EXTI_FTSR enables correct edge sensitivity
6. Confirm NVIC_ISER enables corresponding interrupt number
7. Read EXTI_PR to check if interrupt flag set but not acknowledged; ISR must write 1 to clear

**Interrupt Fires But ISR Does Not Execute:**
1. Verify interrupt handler function name matches vector table entry exactly (e.g., `EXTI0_IRQHandler` not `EXTI0_Handler`)
2. Check PRIMASK register: `0` enables interrupts, `1` disables globally (`__get_PRIMASK()` intrinsic)
3. Inspect NVIC_IABR (Interrupt Active Bit Register): if bit set, interrupt already active; possible infinite loop in ISR
4. Compare interrupt priority in NVIC_IPRx against current execution priority; equal/lower priority interrupts do not preempt

**Spurious Interrupts on Multiple Lines:**
1. Check for floating inputs: all unused GPIO must configure with pull-up/down or analog mode to prevent noise-induced transitions
2. Verify EXTI_PR clearing in ISR: omitting flag clear causes immediate re-entry
3. Inspect for crosstalk: parallel GPIO traces with high slew rate outputs couple noise onto adjacent EXTI inputs; separate by ≥3× trace width

### ADC Conversion Accuracy Degradation Sources

**Symptom: ADC readings noisy (standard deviation > 2 LSB)**
1. Increase sampling time: minimum 3 cycles insufficient for high-impedance sources; use 28+ cycles for Rsource > 10 kΩ
2. Add external 100 nF bypass capacitor at analog input, < 2 cm from MCU pin
3. Verify VREF+ connected to clean 3.3V supply with < 10 mV ripple; separate analog and digital grounds if possible
4. Check ADC clock ≤ 30 MHz: higher frequencies exceed slew rate and introduce nonlinearity

**Symptom: ADC readings consistently offset from expected value**
1. Perform ADC calibration: short input to VREF+ and VSSA, measure endpoints, apply linear correction
2. Verify VREF+ voltage: typical 3.27V from LDO regulator; measure with multimeter referenced to VSSA
3. Check for voltage drop in series resistance: ADC input impedance during sampling ~1 MΩ parallel with 4–12 pF; Rsource > 50 kΩ causes attenuation
4. Inspect for EMI coupling: adjacent PWM signals at > 20 kHz couple through PCB capacitance; add grounded guard trace between ADC input and noise source

**Symptom: ADC conversion triggers but DR register never updates**
1. Verify ADC enabled (ADC_CR2 bit 0 = 1) before starting conversion
2. Check EOC flag (ADC_SR bit 1): if never sets, ADC clock disabled or prescaler misconfigured
3. Confirm channel selected in ADC_SQR3 matches physical input pin
4. Read ADC_DR clears EOC flag automatically; polling SR before DR ready produces stale data

### Power Consumption Anomaly Diagnosis

**Symptom: Current draw higher than datasheet specification**
1. Disable all peripherals in RCC_AHB1ENR/AHB2ENR/APB1ENR/APB2ENR; measure baseline current
2. Re-enable peripherals individually, noting current increase for each:
   - GPIO output driving LED: +5–20 mA depending on LED current and pull-up resistor
   - Active USART: +1.5 mA per peripheral
   - ADC continuous conversion: +2.4 mA
   - Floating GPIO inputs: +50–200 µA per pin due to Schmitt trigger oscillation
3. Check all unused pins configured as analog input (GPIOx_MODER = 11) to minimize leakage
4. Verify external pull-up resistors: 10 kΩ to 3.3V draws 330 µA per resistor; use 100 kΩ for low-power designs

**Symptom: Cannot enter low-power sleep mode**
1. Verify all wakeup sources configured: EXTI, RTC, or peripheral interrupt must enable in NVIC
2. Check SysTick timer disabled: SysTick interrupt prevents WFI (Wait For Interrupt) from sleeping
3. Confirm debugger detached: JTAG/SWD active prevents deep sleep; disconnect ST-LINK before power measurement
4. Inspect RCC_AHB1LPENR/APB1LPENR/APB2LPENR: peripherals remain powered in sleep unless explicitly disabled in low-power enable registers
5. Measure wakeup latency: expect 3–10 µs from EXTI assertion to instruction execution resumption; longer indicates regulator startup delay from Stop mode

**Brown-Out Reset Loop:**
1. Measure supply voltage ripple during peak current: STM32F407 BOR threshold 2.1–2.4V depending on option byte configuration
2. Add bulk capacitance (100–470 µF) at power input to reduce droop during current spikes (ADC conversion, Flash write)
3. Check power supply current limit: insufficient limit causes voltage collapse triggering BOR → reset → boot current spike → BOR
4. Inspect option bytes via ST-LINK Utility: BOR_LEV field in user option byte selects threshold; higher threshold (2.7V) provides margin but reduces operating voltage range

This operational reference consolidates the empirical diagnostic procedures developed through the three exercises, providing a field-deployable troubleshooting framework for microcontroller hardware-software integration failures.
