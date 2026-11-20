# Operational Verification Labs: Embedded Systems

## Objective & Operational Lab Setup

These operational verification laboratories ground the embedded systems practitioner in the disciplined, repeatable validation of microcontroller firmware, peripheral interfaces, and real-time system behavior. The exercises prioritize hands-on measurement, empirical characterization, and failure-mode analysis over abstract simulation. You will configure physical hardware test benches, instrument signal integrity with oscilloscopes and logic analyzers, and validate timing constraints against datasheets through direct observation. The laboratory methodology mirrors production verification workflows: establish baseline operation, perturb critical parameters to map performance envelopes, and stress subsystems to expose failure boundaries and recovery mechanisms.

The verification environment demands an STM32F4 or STM32F7 Nucleo development board, a Saleae Logic 8 or equivalent multi-channel logic analyzer capable of 100 MS/s sampling, a Rigol DS1054Z or Siglent SDS1104X-E oscilloscope with at least 100 MHz bandwidth, a BK Precision 1785B programmable DC power supply for voltage margining, and a suite of passive probes with 10 MΩ input impedance and 10 pF capacitance. The STM32 platform offers rich peripheral integration—GPIO banks with configurable drive strength, hardware timers with nanosecond resolution, DMA controllers for zero-copy data movement, and nested vectored interrupt controllers (NVIC) with 16-level preemption priority—making it an industry-standard reference for real-time embedded verification. The toolchain comprises STM32CubeIDE version 1.14 or later, GNU ARM Embedded Toolchain 12.2, OpenOCD 0.12 for JTAG/SWD debug transport, and PuTTY or screen for UART console capture. Install STM32CubeMX 6.10 for clock tree configuration and peripheral initialization code generation, ensuring that HSE crystal oscillator parameters match your board's 8 MHz external resonator. Verify that ST-LINK firmware on the Nucleo board reaches version V2.J45 or later by running `st-info --version` and upgrading via STM32CubeIDE if necessary.

Construct a benchtop workspace with anti-static mat grounding and regulated 24V DC bench supply feeding the programmable power supply's control input. Mount the Nucleo board on a non-conductive standoff fixture with direct coaxial connections from GPIO test points to oscilloscope Channel 1 and logic analyzer Channel 0. Provision a secondary UART-to-USB adapter (FTDI FT232RL or Silicon Labs CP2102) for independent console logging, isolating debug output from the ST-LINK virtual COM port to avoid USB enumeration latency corrupting timing measurements. Establish a reference ground star topology: connect oscilloscope ground clip, logic analyzer ground lead, power supply return, and Nucleo GND pin to a single brass busbar bolted to the anti-static mat. This star grounding eliminates ground loop currents that manifest as low-frequency noise on analog measurements and intermittent digital glitches on high-speed serial buses.

Configure the STM32F4 system clock tree to derive SYSCLK from the PLL, multiplying the 8 MHz HSE crystal to 168 MHz (STM32F407) or 180 MHz (STM32F429), then scaling AHB and APB1/APB2 prescalers to meet peripheral clock domain requirements: AHB at 168 MHz for core and DMA, APB1 at 42 MHz for I2C and USART, APB2 at 84 MHz for SPI and ADC. Open STM32CubeMX, select your board model from the Board Selector, navigate to Clock Configuration, and set PLL source to HSE, PLLM divider to 4, PLLN multiplier to 168, PLLP divider to 2, and verify that the clock tree diagram reflects SYSCLK at 168 MHz with zero warning flags. Generate initialization code in STM32CubeIDE format, import the project, and compile with `-O2` optimization to balance execution speed against debugger symbol fidelity. Flash the baseline firmware via `openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "program build/firmware.elf verify reset exit"` and confirm console output reports successful verification and CPU reset to address 0x08000000.

Calibrate measurement instruments before each exercise. On the oscilloscope, execute the probe compensation routine by attaching the 10X probe to the built-in 1 kHz square wave calibration terminal and adjusting the probe's trimmer capacitor until rise time measures 350 nanoseconds with zero overshoot or ringing. Set timebase to 500 nanoseconds per division, vertical scale to 1 volt per division, trigger mode to edge-rising at 1.65 volts (CMOS logic threshold), and coupling to DC. On the logic analyzer, configure sampling rate to 100 MS/s, threshold voltage to 1.65 V for 3.3V CMOS logic levels, and pre-trigger capture depth to 50% to record signal history before trigger events. Connect Channel 0 to PA5 (Arduino D13, onboard LED GPIO), Channel 1 to PA9 (USART1 TX), Channel 2 to PB3 (SPI1 SCK), and Channel 3 to PB5 (SPI1 MOSI), labeling each channel in the Saleae Logic 2 software with net name and expected protocol. Enable protocol analyzers: Async Serial on Channel 1 (115200 baud, 8N1), SPI on Channels 2–3 (Mode 0, MSB-first), and verify that the analyzer decodes a test transmission without framing errors.

Establish a disciplined measurement procedure that separates transient capture from steady-state characterization. For transient events—GPIO edge transitions, interrupt latency spikes, DMA burst transfers—configure the oscilloscope in single-shot trigger mode with 10 MS/s sampling to capture the full waveform without aliasing. For steady-state periodic signals—PWM duty cycles, UART bit timing, timer overflow frequencies—use infinite persistence mode and measure statistical parameters (mean, standard deviation, jitter) over 1000 cycles. Record all measurements in a laboratory notebook with timestamp, firmware git commit hash, ambient temperature (thermometer placed adjacent to MCU package), and supply voltage confirmed at multimeter test points. This metadata enables reproducibility when investigating anomalies reported during field deployment or thermal chamber qualification testing.

The verification methodology enforces traceability from datasheet specification to measured performance. Each exercise begins with a datasheet excerpt defining the parameter under test—GPIO toggle frequency, UART baud rate accuracy, ADC conversion time—followed by firmware implementation, measurement procedure, and acceptance criteria derived from the datasheet's minimum/typical/maximum columns. When measured values fall outside the datasheet-guaranteed range, the laboratory protocol escalates to root cause analysis: inspect power supply ripple with AC-coupled oscilloscope, verify crystal oscillator startup with 100X probe on OSC_IN pin, check solder joint continuity with multimeter resistance measurement, and correlate anomalies with thermal drift by heating the MCU package with a hot air rework station while monitoring the signal. This systematic fault isolation mirrors the techniques employed by hardware validation engineers qualifying silicon spin revisions and characterizing electromagnetic interference susceptibility in semi-anechoic chambers.

Prepare the firmware repository structure with modular drivers, hardware abstraction layers, and register-level access macros that expose the underlying silicon operation. Create a `drivers/` directory containing `gpio.c`, `uart.c`, `spi.c`, `timer.c`, and `nvic.c`, each implementing initialization, configuration, and operational functions that directly manipulate STM32F4 peripheral registers through CMSIS-defined base addresses and bitfield macros. For example, the GPIO driver toggles PA5 by writing `GPIOA->ODR ^= (1 << 5);` rather than invoking HAL library abstractions, allowing you to measure the exact instruction cycle latency from assembly disassembly. Compile with `-g3` to embed full DWARF debug symbols, enabling GDB to correlate instruction addresses with source lines during single-step verification. This transparency between C source code and hardware register state forms the foundation of empirical validation, as you will disassemble critical timing loops with `arm-none-eabi-objdump -d firmware.elf`, count instruction cycles from the ARMv7-M architecture reference manual, and confirm execution time with oscilloscope measurement of GPIO assertion to GPIO de-assertion intervals.

The laboratory exercises progress from foundational peripheral operation through parameter variation studies to stress testing under supply voltage margining, thermal extremes, and interrupt load saturation. Exercise 1 establishes GPIO toggle frequency and UART transmission integrity as baseline measurements, verifying that firmware execution matches datasheet timing guarantees. Exercise 2 introduces controlled parameter sweeps—varying SPI clock prescaler, PWM duty cycle, ADC sampling time—to map the transfer function from configuration register value to measured output characteristic, building empirical models that predict system behavior across the operational envelope. Exercise 3 subjects the firmware to hostile conditions: supply voltage dips to brownout threshold, ambient temperature ramps to maximum junction rating, interrupt request bursts that saturate NVIC priority arbitration. You will instrument failure modes—watchdog timer resets, hard fault exceptions, UART framing errors—and implement recovery protocols that restore operation without manual intervention. This exhaustive verification methodology ensures that embedded firmware survives the transition from benchtop prototype to production deployment in automotive, industrial, and aerospace environments where unattended operation over decade-long service lifetimes mandates exceptional resilience.

## Exercise 1: Foundational Practical Implementation

The first operational verification exercise establishes measurable baselines for GPIO toggle frequency, UART transmission accuracy, and timer-generated PWM duty cycle. These three subsystems form the bedrock of embedded firmware: GPIO for external signal assertion, UART for diagnostic logging and inter-processor communication, and hardware timers for precise temporal control of motor drives, LED brightness, and sample-and-hold ADC triggering. The exercise methodology enforces direct register-level implementation to eliminate abstraction layer timing overhead, enabling cycle-accurate measurement that correlates with ARM Cortex-M4 pipeline behavior and AHB bus arbitration.

Begin by implementing a bare-metal GPIO toggling routine that oscillates PA5 at maximum frequency, limited only by instruction throughput and bus access latency. Open `drivers/gpio.c` and define the initialization function that configures PA5 as general-purpose output, push-pull mode, no pull-up/pull-down resistors, and high-speed output drive. The STM32F4 GPIO peripheral requires two configuration steps: enable the GPIOA clock gate in the RCC AHB1ENR register and configure the pin mode in GPIOA MODER register. Write the following implementation:

```c
#include "stm32f4xx.h"

void gpio_init(void) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    GPIOA->MODER &= ~(0x3 << (5 * 2));
    GPIOA->MODER |= (0x1 << (5 * 2));
    GPIOA->OTYPER &= ~(1 << 5);
    GPIOA->OSPEEDR |= (0x3 << (5 * 2));
    GPIOA->PUPDR &= ~(0x3 << (5 * 2));
}

void gpio_toggle_fast(void) {
    while (1) {
        GPIOA->ODR ^= (1 << 5);
    }
}
```

This implementation directly manipulates the GPIO Output Data Register (ODR) using bitwise XOR to invert bit 5 without disturbing other pins. The `RCC_AHB1ENR_GPIOAEN` macro expands to bit position 0 in the RCC AHB1 peripheral clock enable register, gating the GPIOA clock from the AHB bus. The MODER register uses 2 bits per pin: `0b00` for input, `0b01` for general-purpose output, `0b10` for alternate function, `0b11` for analog. The OTYPER register selects push-pull (`0`) versus open-drain (`1`) output stage topology. The OSPEEDR register encodes output slew rate: `0b00` for low speed (8 MHz), `0b01` for medium (50 MHz), `0b10` for fast (100 MHz), `0b11` for high speed (180 MHz), with higher speeds enabling faster edge transitions at the cost of increased electromagnetic emissions and supply current transients.

Compile the firmware with `arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O2 -g3 -c gpio.c -o gpio.o` and link into the final ELF binary. Flash to the Nucleo board and connect the oscilloscope probe to PA5 with ground clip on the adjacent GND pin. Set the timebase to 50 nanoseconds per division and trigger on the rising edge at 1.65V threshold. Observe the waveform and measure the toggle frequency using the oscilloscope's built-in frequency counter. The STM32F407 running at 168 MHz AHB clock should achieve approximately 10.5 MHz GPIO toggle frequency, corresponding to a 95 nanosecond period. This frequency emerges from the instruction cycle breakdown: the XOR operation compiles to a single `EOR` ARM instruction (1 cycle), the memory-mapped write to ODR incurs an AHB bus transaction (1 cycle for address phase, 1 cycle for data phase), and the branch back to the loop start adds 1 cycle for the pipeline flush. Total: 4 cycles per toggle, yielding 168 MHz / 4 / 2 = 21 MHz theoretical maximum for a complete high-low cycle pair, but the actual measured frequency accounts for bus arbitration delays when DMA controllers and other AHB masters contend for memory access.

Disassemble the compiled object file with `arm-none-eabi-objdump -d gpio.o` and locate the `gpio_toggle_fast` function. The disassembly should reveal a tight loop structure:

```text
08000400 <gpio_toggle_fast>:
 8000400:   4b02        ldr     r3, [pc, #8]
 8000402:   6819        ldr     r1, [r3, #0]
 8000404:   f081 0120   eor.w   r1, r1, #32
 8000408:   6019        str     r1, [r3, #0]
 800040a:   e7fa        b.n     8000402 <gpio_toggle_fast+0x2>
```

The `ldr r3, [pc, #8]` instruction loads the GPIOA base address (0x40020000) into register R3 from a literal pool. The `ldr r1, [r3, #0]` fetches the current ODR value, the `eor.w` inverts bit 5, and the `str r1, [r3, #0]` writes back to ODR. The unconditional branch `b.n` creates the infinite loop. Count the instruction cycles: load-load-eor-store-branch equals 1-2-1-2-3 cycles in the Cortex-M4 pipeline, but the Harvard architecture allows instruction fetch to overlap with data access, collapsing effective latency to approximately 4 cycles per iteration when instruction cache hits and AHB bus grants occur without wait states. Verify this prediction by multiplying the measured toggle period by the CPU frequency: 95 ns × 168 MHz = 15.96 cycles per full high-low transition, or 7.98 cycles per toggle, confirming the 2X factor from alternating high and low states.

Record the baseline measurement: GPIO toggle frequency = 10.5 MHz ± 0.1 MHz, rise time = 6 nanoseconds, fall time = 4 nanoseconds, overshoot = 50 mV (1.5% of 3.3V supply), ringing frequency = 85 MHz (indicating parasitic inductance in the PCB trace and probe ground lead forming a resonant LC tank). The asymmetric rise and fall times result from the CMOS output stage's PMOS and NMOS transistor drive strength imbalance, with NMOS typically exhibiting 2X higher transconductance due to electron mobility exceeding hole mobility in silicon. The 85 MHz ringing corresponds to the square root of the reciprocal of the product of trace inductance (approximately 10 nH per cm) and load capacitance (probe 10 pF plus PCB parasitic 5 pF), yielding a resonant frequency of 1 / (2π√(LC)) = 1 / (2π√(10 nH × 15 pF)) = 130 MHz, damped by trace resistance to the observed 85 MHz.

Next, implement and verify UART transmission at 115200 baud with 8 data bits, no parity, 1 stop bit (8N1 framing). Configure USART1 peripheral on PA9 (TX) and PA10 (RX) using the following driver:

```c
#include "stm32f4xx.h"

void uart_init(void) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    RCC->APB2ENR |= RCC_APB2ENR_USART1EN;
    
    GPIOA->MODER &= ~((0x3 << (9 * 2)) | (0x3 << (10 * 2)));
    GPIOA->MODER |= (0x2 << (9 * 2)) | (0x2 << (10 * 2));
    GPIOA->AFR[1] &= ~((0xF << ((9 - 8) * 4)) | (0xF << ((10 - 8) * 4)));
    GPIOA->AFR[1] |= (0x7 << ((9 - 8) * 4)) | (0x7 << ((10 - 8) * 4));
    
    uint32_t apb2_clock = 84000000;
    uint32_t baud = 115200;
    uint16_t uartdiv = (apb2_clock + (baud / 2)) / baud;
    USART1->BRR = uartdiv;
    
    USART1->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_UE;
}

void uart_transmit_byte(uint8_t data) {
    while (!(USART1->SR & USART_SR_TXE));
    USART1->DR = data;
}

void uart_transmit_string(const char *str) {
    while (*str) {
        uart_transmit_byte(*str++);
    }
}
```

The GPIO alternate function configuration routes PA9 and PA10 to USART1 TX and RX through the AF7 alternate function mapping, documented in the STM32F407 datasheet Table 9. The baud rate generator divides the APB2 clock (84 MHz) by the value written to the Baud Rate Register (BRR). For 115200 baud, the divisor calculates as 84,000,000 / 115,200 = 729.166, which the USART peripheral interprets with 4-bit fractional precision: mantissa = 729, fraction = 0.166 × 16 = 2.66 ≈ 3, yielding BRR = (729 << 4) | 3 = 0x1CD3. The actual baud rate achieves (84,000,000 / 729.1875) = 115,207 baud, an error of 0.006%, well within the RS-232 standard's ±2% tolerance for reliable communication without external clock synchronization.

Flash the firmware and configure the logic analyzer to decode UART on PA9. Transmit the string "EMBEDDED\r\n" by calling `uart_transmit_string("EMBEDDED\r\n");` in the main loop with a 1-second delay between transmissions. Observe the logic analyzer capture and verify that each character's bit timing matches the expected 8.68 microsecond period (1 / 115200 = 8.68 μs). Measure the start bit duration, each data bit duration, and the stop bit duration with the analyzer's timing markers. The protocol analyzer should decode the ASCII characters correctly: 'E' (0x45), 'M' (0x4D), 'B' (0x42), 'E' (0x45), 'D' (0x44), 'D' (0x44), 'E' (0x45), 'D' (0x44), carriage return (0x0D), line feed (0x0A). Confirm that the stop bit remains high for exactly 8.68 microseconds before the next start bit, verifying that the transmitter obeys the 8N1 framing specification.

Zoom into a single UART frame on the logic analyzer and measure the bit-to-bit jitter. Position timing markers on the rising edge of consecutive start bits across 100 transmissions and compute the standard deviation of the inter-frame interval. The jitter should remain below 0.1% of the bit period (8.68 ns), attributable to the crystal oscillator's ±50 ppm frequency stability and the USART peripheral's 16X oversampling clock, which quantizes bit center detection to 1/16th of a bit period (542 ns). Export the logic analyzer timing data to CSV format, open in a spreadsheet, and plot a histogram of start-bit-to-start-bit intervals. The distribution should exhibit a Gaussian shape centered at 95.48 microseconds (11 bits × 8.68 μs) with standard deviation under 10 nanoseconds, confirming that the firmware's 1-second delay loop and USART transmit polling introduce negligible timing variability compared to the hardware baud rate generator's crystal-derived stability.

Complete the foundational exercise by generating a PWM signal at 10 kHz with 50% duty cycle using Timer 2 and PA0 as the output compare channel. The STM32F4 general-purpose timers operate as 16-bit or 32-bit up-counters that compare the counter register (CNT) against a capture/compare register (CCRx) to toggle output pins or trigger interrupts. Configure Timer 2 to run at 84 MHz (APB1 clock, doubled by the timer clock multiplier when APB1 prescaler ≠ 1), prescale by 84 to achieve 1 MHz timebase, and set the auto-reload register (ARR) to 100 for a 10 kHz overflow frequency. The output compare generates a PWM waveform by setting the output high when CNT < CCR1 and clearing it when CNT ≥ CCR1. For 50% duty cycle, write CCR1 = ARR / 2 = 50.

```c
#include "stm32f4xx.h"

void timer_pwm_init(void) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;
    
    GPIOA->MODER &= ~(0x3 << (0 * 2));
    GPIOA->MODER |= (0x2 << (0 * 2));
    GPIOA->AFR[0] &= ~(0xF << (0 * 4));
    GPIOA->AFR[0] |= (0x1 << (0 * 4));
    
    TIM2->PSC = 83;
    TIM2->ARR = 99;
    TIM2->CCR1 = 49;
    
    TIM2->CCMR1 &= ~TIM_CCMR1_OC1M;
    TIM2->CCMR1 |= (0x6 << TIM_CCMR1_OC1M_Pos);
    TIM2->CCMR1 |= TIM_CCMR1_OC1PE;
    
    TIM2->CCER |= TIM_CCER_CC1E;
    TIM2->CR1 |= TIM_CR1_ARPE | TIM_CR1_CEN;
}
```

The prescaler register (PSC) divides the 84 MHz timer clock by (PSC + 1), so PSC = 83 yields 1 MHz. The auto-reload register (ARR) defines the period: CNT counts from 0 to ARR and resets, producing (1 MHz / 100) = 10 kHz frequency. The output compare mode register (CCMR1) configures channel 1 for PWM mode 1 (OC1M = 0b110), which sets the output high when CNT < CCR1 and low otherwise. The preload enable bit (OC1PE) ensures that writes to CCR1 only take effect at the next update event, preventing glitches when modifying duty cycle mid-period. The capture/compare enable register (CCER) activates the output on PA0, and the control register (CR1) enables auto-reload preload (ARPE) and starts the counter (CEN).

Connect the oscilloscope to PA0 and verify the PWM output. Set the timebase to 20 microseconds per division to display five complete cycles. Measure the period with the oscilloscope's period counter: it should read 100.0 microseconds ± 0.1 μs, corresponding to exactly 10.000 kHz. Measure the positive pulse width: it should read 50.0 microseconds ± 0.1 μs, confirming 50% duty cycle. Use the oscilloscope's duty cycle measurement function to verify 50.0% ± 0.1%. Zoom into the rising and falling edges and measure the transition times: rise time should be approximately 40 nanoseconds (10% to 90% of 3.3V), fall time approximately 30 nanoseconds, with minimal overshoot due to the timer's internal synchronous output stage driving the GPIO through a short on-chip routing path that minimizes parasitic inductance.

Vary the duty cycle by modifying CCR1 and observe the pulse width response. Set CCR1 = 25 for 25% duty cycle, CCR1 = 75 for 75% duty cycle, and CCR1 = 10 for 10% duty cycle. In each case, measure the positive pulse width and confirm it equals (CCR1 / ARR) × 100 microseconds. Plot the measured pulse width versus CCR1 value, fitting a linear regression to verify that the hardware implements the theoretical relationship with zero nonlinearity. The regression should yield slope = 1.00 μs per count, intercept = 0.00 μs, and R² = 0.9999, demonstrating that the timer output compare operates with 1-count resolution and no quantization hysteresis or dead-band artifacts.

Document the baseline measurements in the laboratory notebook: GPIO toggle frequency = 10.5 MHz with 95 ns period, UART baud rate = 115,207 baud with 0.006% error and 8 ns jitter, PWM frequency = 10.000 kHz with 50.0% duty cycle and 1-count linearity. These empirical baselines establish the firmware's nominal operating point, against which subsequent parameter variations and stress tests will be compared to detect degradation, nonlinearity, and failure modes.

## Exercise 2: Parameter Variation & Empirical Analysis

The second operational verification exercise constructs empirical transfer functions by sweeping critical configuration parameters and measuring the resulting system response. This methodology quantifies the relationship between register values and observable behavior, validating datasheet specifications and exposing nonlinear regions, discontinuities, and unspecified corner cases. You will vary the SPI clock prescaler to map communication throughput versus bit error rate, sweep ADC sampling time to characterize conversion accuracy versus acquisition speed, and modulate PWM duty cycle to measure output voltage linearity under resistive and capacitive loading. Each parameter sweep generates a dataset that you will analyze through regression, deviation calculation, and failure threshold identification, culminating in empirical models that predict system performance across the operational envelope.

Begin by configuring the SPI1 peripheral on PB3 (SCK), PB4 (MISO), and PB5 (MOSI) to communicate with a 25LC640 SPI EEPROM (64 Kbit, 8 KB capacity, 20 MHz maximum clock frequency). The SPI protocol transmits data synchronously over a shared clock line, with the master device (STM32F4) generating clock pulses and the slave device (EEPROM) responding on the rising or falling edge according to the configured clock polarity (CPOL) and phase (CPHA). SPI Mode 0 defines CPOL = 0 (clock idle low) and CPHA = 0 (data sampled on first clock edge, shifted on second edge), matching the 25LC640's native protocol timing.

Implement the SPI driver with configurable baud rate prescaler:

```c
#include "stm32f4xx.h"

void spi_init(uint8_t prescaler) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOBEN;
    RCC->APB2ENR |= RCC_APB2ENR_SPI1EN;
    
    GPIOB->MODER &= ~((0x3 << (3 * 2)) | (0x3 << (4 * 2)) | (0x3 << (5 * 2)));
    GPIOB->MODER |= (0x2 << (3 * 2)) | (0x2 << (4 * 2)) | (0x2 << (5 * 2));
    GPIOB->AFR[0] &= ~((0xF << (3 * 4)) | (0xF << (4 * 4)) | (0xF << (5 * 4)));
    GPIOB->AFR[0] |= (0x5 << (3 * 4)) | (0x5 << (4 * 4)) | (0x5 << (5 * 4));
    
    SPI1->CR1 = (prescaler << SPI_CR1_BR_Pos) | SPI_CR1_MSTR | SPI_CR1_SSM | SPI_CR1_SSI | SPI_CR1_SPE;
}

uint8_t spi_transfer(uint8_t data) {
    while (!(SPI1->SR & SPI_SR_TXE));
    SPI1->DR = data;
    while (!(SPI1->SR & SPI_SR_RXNE));
    return SPI1->DR;
}

void eeprom_write_byte(uint16_t address, uint8_t data) {
    spi_transfer(0x06);
    spi_transfer(0x02);
    spi_transfer((address >> 8) & 0xFF);
    spi_transfer(address & 0xFF);
    spi_transfer(data);
    for (volatile uint32_t i = 0; i < 10000; i++);
}

uint8_t eeprom_read_byte(uint16_t address) {
    spi_transfer(0x03);
    spi_transfer((address >> 8) & 0xFF);
    spi_transfer(address & 0xFF);
    return spi_transfer(0x00);
}
```

The SPI baud rate register (BR) in CR1 encodes the prescaler as a 3-bit field: 0b000 = /2, 0b001 = /4, 0b010 = /8, 0b011 = /16, 0b100 = /32, 0b101 = /64, 0b110 = /128, 0b111 = /256. The APB2 clock runs at 84 MHz, so the SPI clock frequency equals 84 MHz divided by the prescaler value. The EEPROM write sequence transmits the Write Enable command (0x06), Write command (0x02), 16-bit address in big-endian byte order, and the data byte. The polling loop delays for 5 milliseconds to allow the EEPROM's internal write cycle to complete, as specified in the 25LC640 datasheet (maximum 5 ms write time). The read sequence transmits the Read command (0x03), 16-bit address, and clocks out the data byte by transmitting a dummy 0x00.

Connect the 25LC640 to the STM32F4 Nucleo board: pin 1 (CS) to PB6 configured as GPIO output high, pin 2 (SO/MISO) to PB4, pin 3 (WP) to 3.3V, pin 4 (VSS) to GND, pin 5 (SI/MOSI) to PB5, pin 6 (SCK) to PB3, pin 7 (HOLD) to 3.3V, pin 8 (VCC) to 3.3V. Initialize the chip select pin with:

```c
void eeprom_cs_init(void) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOBEN;
    GPIOB->MODER &= ~(0x3 << (6 * 2));
    GPIOB->MODER |= (0x1 << (6 * 2));
    GPIOB->BSRR = (1 << 6);
}

void eeprom_cs_low(void) {
    GPIOB->BSRR = (1 << (6 + 16));
}

void eeprom_cs_high(void) {
    GPIOB->BSRR = (1 << 6);
}
```

The bit set/reset register (BSRR) allows atomic pin manipulation: writing bit N in the lower 16 bits sets the pin, writing bit (N + 16) in the upper 16 bits resets it. Modify the write and read functions to assert and de-assert chip select:

```c
void eeprom_write_byte(uint16_t address, uint8_t data) {
    eeprom_cs_low();
    spi_transfer(0x06);
    eeprom_cs_high();
    for (volatile uint32_t i = 0; i < 10; i++);
    
    eeprom_cs_low();
    spi_transfer(0x02);
    spi_transfer((address >> 8) & 0xFF);
    spi_transfer(address & 0xFF);
    spi_transfer(data);
    eeprom_cs_high();
    for (volatile uint32_t i = 0; i < 10000; i++);
}

uint8_t eeprom_read_byte(uint16_t address) {
    eeprom_cs_low();
    spi_transfer(0x03);
    spi_transfer((address >> 8) & 0xFF);
    spi_transfer(address & 0xFF);
    uint8_t data = spi_transfer(0x00);
    eeprom_cs_high();
    return data;
}
```

Sweep the SPI clock prescaler from /2 to /256 and measure the read throughput and bit error rate at each setting. Implement a test routine that writes a 256-byte test pattern (0x00, 0x01, 0x02, ..., 0xFF) to EEPROM addresses 0x0000–0x00FF, reads it back, and compares against the expected values:

```c
uint32_t test_spi_throughput_and_errors(uint8_t prescaler) {
    spi_init(prescaler);
    
    for (uint16_t addr = 0; addr < 256; addr++) {
        eeprom_write_byte(addr, (uint8_t)addr);
    }
    
    uint32_t errors = 0;
    uint32_t start_tick = DWT->CYCCNT;
    
    for (uint16_t addr = 0; addr < 256; addr++) {
        uint8_t read_data = eeprom_read_byte(addr);
        if (read_data != (uint8_t)addr) {
            errors++;
        }
    }
    
    uint32_t end_tick = DWT->CYCCNT;
    uint32_t elapsed_cycles = end_tick - start_tick;
    
    uart_transmit_string("Prescaler ");
    uart_transmit_byte('0' + prescaler);
    uart_transmit_string(": ");
    
    uint32_t clock_mhz = 84000000 / (2 << prescaler);
    uart_transmit_string("SPI Clock ");
    uart_transmit_byte('0' + (clock_mhz / 1000000));
    uart_transmit_string(" MHz, Errors ");
    uart_transmit_byte('0' + errors);
    uart_transmit_string(", Cycles ");
    uart_transmit_string("\r\n");
    
    return errors;
}
```

Enable the Data Watchpoint and Trace (DWT) cycle counter in the Cortex-M4 core to measure elapsed CPU cycles with nanosecond precision:

```c
void dwt_init(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}
```

Run the sweep loop in `main()`:

```c
int main(void) {
    SystemClock_Config();
    dwt_init();
    uart_init();
    eeprom_cs_init();
    
    for (uint8_t prescaler = 0; prescaler <= 7; prescaler++) {
        uint32_t errors = test_spi_throughput_and_errors(prescaler);
        for (volatile uint32_t i = 0; i < 1000000; i++);
    }
    
    while (1);
}
```

Capture the UART console output and the SPI waveforms on the logic analyzer. For each prescaler setting, record the SPI clock frequency measured on PB3, the number of bit errors detected, and the elapsed CPU cycles for the 256-byte read operation. Convert elapsed cycles to throughput in kilobytes per second: throughput = (256 bytes) / (elapsed_cycles / 168,000,000 Hz). Tabulate the results:

| Prescaler | Divisor | SPI Clock (MHz) | Errors | Elapsed Cycles | Throughput (KB/s) |
|-----------|---------|-----------------|--------|----------------|-------------------|
| 0         | /2      | 42.0            | 256    | 1,200,000      | 35.84             |
| 1         | /4      | 21.0            | 128    | 1,400,000      | 30.72             |
| 2         | /8      | 10.5            | 32     | 1,800,000      | 23.89             |
| 3         | /16     | 5.25            | 0      | 2,600,000      | 16.55             |
| 4         | /32     | 2.625           | 0      | 4,200,000      | 10.24             |
| 5         | /64     | 1.3125          | 0      | 7,400,000      | 5.82              |
| 6         | /128    | 0.65625         | 0      | 13,800,000     | 3.12              |
| 7         | /256    | 0.328125        | 0      | 26,600,000     | 1.62              |

The data reveals that SPI clocks exceeding the EEPROM's 20 MHz maximum specification produce catastrophic bit error rates: at 42 MHz (prescaler 0), all 256 bytes fail verification; at 21 MHz (prescaler 1), 50% fail; at 10.5 MHz (prescaler 2), 12.5% fail. At and below 5.25 MHz (prescaler 3), the error rate drops to zero, confirming the datasheet's maximum clock frequency specification. The throughput decreases linearly with clock frequency, as expected from the SPI protocol's synchronous byte-by-byte transmission. The elapsed CPU cycle count increases inversely with SPI clock frequency because the polling loops in `spi_transfer` stall the CPU while waiting for TXE and RXNE flags, making the transfer time dominated by the SPI peripheral's hardware clock rather than CPU instruction throughput.

Plot the bit error rate versus SPI clock frequency on semi-log axes. The error rate exhibits a sharp threshold at 20 MHz: zero errors below, exponential increase above, characteristic of setup-and-hold time violations in the EEPROM's input capture registers. When the SPI clock period shrinks below the EEPROM's specified minimum (50 ns for 20 MHz), the data signal fails to settle before the clock edge samples it, causing metastable capture and random bit flips. This empirical failure threshold validates the datasheet specification and demonstrates the catastrophic consequences of exceeding maximum rated parameters.

Next, characterize the STM32F4 ADC conversion time versus sampling time setting. The ADC peripheral converts analog voltages from 0–3.3V to 12-bit digital values (0–4095) through successive approximation, requiring a sample-and-hold phase to charge an internal capacitor to the input voltage, followed by a conversion phase to compare the held voltage against a binary-weighted DAC. The sampling time (programmable from 3 to 480 ADC clock cycles) trades off acquisition speed against input impedance tolerance: shorter sampling times demand lower source impedance to charge the sample capacitor within the allotted time.

Configure ADC1 on PA1 (Arduino A1) with configurable sampling time:

```c
#include "stm32f4xx.h"

void adc_init(uint8_t sampling_cycles) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    
    GPIOA->MODER |= (0x3 << (1 * 2));
    
    ADC1->CR2 = 0;
    ADC1->CR1 = 0;
    ADC1->SQR1 = 0;
    ADC1->SQR3 = 1;
    
    ADC1->SMPR2 &= ~(0x7 << (1 * 3));
    ADC1->SMPR2 |= (sampling_cycles << (1 * 3));
    
    ADC->CCR = (0x1 << ADC_CCR_ADCPRE_Pos);
    
    ADC1->CR2 |= ADC_CR2_ADON;
}

uint16_t adc_read(void) {
    ADC1->CR2 |= ADC_CR2_SWSTART;
    while (!(ADC1->SR & ADC_SR_EOC));
    return ADC1->DR;
}
```

The sample time register (SMPR2) encodes the sampling duration for channels 0–9 as a 3-bit field per channel: 0b000 = 3 cycles, 0b001 = 15 cycles, 0b010 = 28 cycles, 0b011 = 56 cycles, 0b100 = 84 cycles, 0b101 = 112 cycles, 0b110 = 144 cycles, 0b111 = 480 cycles. The common control register (CCR) sets the ADC clock prescaler: 0b01 = PCLK2/4 = 21 MHz. The total conversion time equals (sampling_cycles + 12) / 21 MHz, where 12 cycles accounts for the successive approximation conversion phase (12 bits × 1 cycle per bit).

Connect a 10 kΩ potentiometer between 3.3V and GND with the wiper to PA1, forming a voltage divider with adjustable output from 0–3.3V. Alternatively, use the programmable DC power supply to generate a stable 1.65V reference. For each sampling time setting (3, 15, 28, 56, 84, 112, 144, 480 cycles), perform 1000 ADC conversions and compute the mean, standard deviation, and conversion time:

```c
void test_adc_sampling_time(uint8_t sampling_cycles) {
    adc_init(sampling_cycles);
    
    uint32_t sum = 0;
    uint32_t sum_sq = 0;
    uint32_t start_tick = DWT->CYCCNT;
    
    for (uint16_t i = 0; i < 1000; i++) {
        uint16_t value = adc_read();
        sum += value;
        sum_sq += value * value;
    }
    
    uint32_t end_tick = DWT->CYCCNT;
    uint32_t elapsed_cycles = end_tick - start_tick;
    
    uint32_t mean = sum / 1000;
    uint32_t variance = (sum_sq / 1000) - (mean * mean);
    uint32_t std_dev = 0;
    for (uint32_t i = 0; i * i <= variance; i++) {
        std_dev = i;
    }
    
    uint32_t conversion_time_ns = (sampling_cycles + 12) * 1000 / 21;
    
    uart_transmit_string("Sampling ");
    uart_transmit_string(" cycles: Mean ");
    uart_transmit_string(", StdDev ");
    uart_transmit_string(", Time ");
    uart_transmit_string(" ns\r\n");
}
```

Run the sweep and record the results:

| Sampling Cycles | Conversion Time (ns) | Mean ADC Value | Std Dev | Theoretical Voltage (V) | Measured Voltage (V) |
|-----------------|----------------------|----------------|---------|-------------------------|----------------------|
| 3               | 714                  | 1856           | 24      | 1.65                    | 1.50                 |
| 15              | 1286                 | 1984           | 18      | 1.65                    | 1.60                 |
| 28              | 1905                 | 2032           | 12      | 1.65                    | 1.64                 |
| 56              | 3238                 | 2045           | 8       | 1.65                    | 1.65                 |
| 84              | 4571                 | 2047           | 6       | 1.65                    | 1.65                 |
| 112             | 5905                 | 2048           | 4       | 1.65                    | 1.65                 |
| 144             | 7429                 | 2048           | 4       | 1.65                    | 1.65                 |
| 480             | 23429                | 2048           | 4       | 1.65                    | 1.65                 |

The measured ADC value converts to voltage via: V = (ADC_value / 4095) × 3.3V. The theoretical value for 1.65V input equals 2048 (exactly half-scale). The data demonstrates that insufficient sampling time causes systematic under-reading: at 3 cycles (714 ns), the 10 kΩ source impedance and 12 pF sample capacitor form an RC time constant of 120 ns, requiring approximately 5τ = 600 ns to settle within 1 LSB (0.8 mV). The 714 ns sampling window allows only 6τ, producing 9% undershoot. At 56 cycles (3.2 μs = 27τ), the error vanishes. The standard deviation decreases with sampling time, reflecting reduced thermal noise aliasing when the longer acquisition window averages over multiple noise periods.

Plot ADC measurement error versus sampling time on log-log axes. Fit an exponential decay model: error = A × exp(−t / τ), where τ = RC = 120 ns. The fit should yield τ = 118 ns ± 5 ns, validating the theoretical RC time constant calculation. This empirical model enables engineers to select the minimum sampling time that achieves target accuracy for a given source impedance, optimizing conversion throughput without sacrificing precision.

Finally, characterize PWM duty cycle linearity under resistive and capacitive loading. Modify the timer PWM driver to accept duty cycle as a percentage and measure the average output voltage with a multimeter:

```c
void timer_pwm_set_duty(uint8_t duty_percent) {
    if (duty_percent > 100) duty_percent = 100;
    TIM2->CCR1 = (TIM2->ARR + 1) * duty_percent / 100 - 1;
}

void test_pwm_linearity(void) {
    timer_pwm_init();
    
    for (uint8_t duty = 0; duty <= 100; duty += 10) {
        timer_pwm_set_duty(duty);
        for (volatile uint32_t i = 0; i < 1000000; i++);
        uart_transmit_string("Duty ");
        uart_transmit_string("%: Measure voltage\r\n");
        for (volatile uint32_t i = 0; i < 10000000; i++);
    }
}
```

Connect a 1 kΩ resistor from PA0 to GND (resistive load) and measure the average output voltage with a multimeter in DC mode. The multimeter's low-pass input filter averages the PWM waveform, yielding V_avg = V_supply × duty_cycle. Record the voltage at each duty cycle setting. Then replace the 1 kΩ resistor with a 1 kΩ resistor in series with a 10 μF capacitor (RC filter with 10 ms time constant, 100X longer than the 100 μs PWM period), creating a capacitive load. Measure the voltage at each duty cycle setting again.

Tabulate the results:

| Duty Cycle (%) | Resistive Load (V) | Capacitive Load (V) | Theoretical (V) | Resistive Error (%) | Capacitive Error (%) |
|----------------|--------------------|---------------------|-----------------|---------------------|----------------------|
| 0              | 0.00               | 0.00                | 0.00            | 0.0                 | 0.0                  |
| 10             | 0.33               | 0.33                | 0.33            | 0.0                 | 0.0                  |
| 20             | 0.66               | 0.66                | 0.66            | 0.0                 | 0.0                  |
| 30             | 0.99               | 0.99                | 0.99            | 0.0                 | 0.0                  |
| 40             | 1.32               | 1.32                | 1.32            | 0.0                 | 0.0                  |
| 50             | 1.65               | 1.65                | 1.65            | 0.0                 | 0.0                  |
| 60             | 1.98               | 1.98                | 1.98            | 0.0                 | 0.0                  |
| 70             | 2.31               | 2.31                | 2.31            | 0.0                 | 0.0                  |
| 80             | 2.64               | 2.64                | 2.64            | 0.0                 | 0.0                  |
| 90             | 2.97               | 2.97                | 2.97            | 0.0                 | 0.0                  |
| 100            | 3.30               | 3.30                | 3.30            | 0.0                 | 0.0                  |

Both resistive and capacitive loads produce zero error across the full duty cycle range, demonstrating that the timer hardware implements ideal linearity with no dead-band, hysteresis, or quantization artifacts. Plot measured voltage versus duty cycle and fit a linear regression: slope = 0.033 V per percent, intercept = 0.00 V, R² = 1.0000. The multimeter's 0.01V resolution limits error detection below 0.3%, confirming that the PWM output accurately reproduces the commanded duty cycle with precision limited only by the timer's 1-count resolution (1% for ARR = 100).

Document the parameter sweep results: SPI communication requires clock frequencies below the slave device's maximum rating to avoid setup-and-hold violations; ADC sampling time must exceed 5× the source RC time constant to achieve sub-LSB accuracy; PWM duty cycle exhibits perfect linearity under both resistive and capacitive loading with zero dead-band. These empirical transfer functions enable predictive modeling of system behavior, allowing engineers to optimize performance parameters without iterative trial-and-error prototyping.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The third operational verification exercise subjects the embedded firmware to hostile operating conditions that exceed nominal specifications, forcing subsystems to their failure thresholds and instrumenting recovery mechanisms. You will reduce supply voltage to the brownout detection limit, inject interrupt request bursts to saturate NVIC priority arbitration, heat the MCU package to maximum junction temperature, and corrupt peripheral configurations to trigger hardware fault exceptions. Each stress test identifies the failure mode, measures the degradation onset point, and validates that watchdog timers, exception handlers, and state machine rollback restore operation without manual intervention. This exhaustive boundary analysis ensures that production firmware survives automotive voltage transients, industrial thermal extremes, and electromagnetic interference pulses that characterize real-world deployment environments.

Begin by constructing a supply voltage margining test that sweeps VDD from 3.6V (maximum rating) down to 1.7V (brownout reset threshold) while monitoring GPIO toggle frequency, UART framing errors, and CPU clock integrity. The STM32F4 datasheet specifies 1.8V minimum operating voltage and 3.6V maximum, with brownout reset (BOR) thresholds configurable via option bytes. The programmable DC power supply enables precise voltage control with 10 mV resolution and 1 mA current compliance, allowing you to map the degradation onset voltage for each subsystem.

Configure the brownout detection level to BOR Level 3 (rising threshold 2.7V, falling threshold 2.6V) by writing the FLASH option bytes. Use ST-LINK Utility or OpenOCD to modify the option bytes register:

```text
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "init; reset halt; flash read_bank 0 option_bytes.bin 0x1FFFC000 16; exit"
```

Examine the option bytes with a hex editor and verify that byte 8 (BOR_LEV bits in FLASH_OPTCR register) equals 0b11 for Level 3. If modification is required:

```text
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "init; reset halt; stm32f2x unlock 0; flash write_bank 0 modified_option_bytes.bin 0x1FFFC000; stm32f2x lock 0; reset; exit"
```

Connect the programmable DC power supply to the Nucleo board's VDD pins (CN7 pin 5 and CN10 pin 1), disconnecting the ST-LINK 3.3V supply by removing the JP5 jumper. Connect the supply's negative terminal to GND (CN7 pin 8 and CN10 pin 20) using twisted-pair wire to minimize ground impedance. Set the supply to 3.3V, enable output, and verify that the board boots by observing the ST-LINK LED flashing during enumeration.

Implement a voltage margining test that continuously toggles PA5, transmits UART strings, and monitors the system clock frequency using the RCC Clock Security System (CSS):

```c
#include "stm32f4xx.h"

volatile uint32_t css_fault_count = 0;

void NMI_Handler(void) {
    if (RCC->CIR & RCC_CIR_CSSF) {
        css_fault_count++;
        RCC->CIR |= RCC_CIR_CSSC;
    }
}

void css_init(void) {
    RCC->CR |= RCC_CR_CSSON;
}

int main(void) {
    SystemClock_Config();
    css_init();
    gpio_init();
    uart_init();
    
    while (1) {
        gpio_toggle_fast();
        uart_transmit_string("VOLTAGE_OK\r\n");
        for (volatile uint32_t i = 0; i < 168000; i++);
    }
}
```

The Clock Security System monitors the HSE oscillator and generates an NMI (non-maskable interrupt) if the external crystal fails to oscillate, indicating that the supply voltage has dropped below the oscillator's startup threshold (approximately 2.2V for the 8 MHz crystal). The NMI handler increments a fault counter and clears the CSS flag by writing to the RCC Clock Interrupt Clear Register (CICR).

Connect the oscilloscope to PA5 and the logic analyzer to PA9 (UART TX). Configure the supply to output 3.6V and ramp down to 1.7V in 100 mV steps, dwelling 10 seconds at each voltage. At each step, measure the GPIO toggle frequency and count UART framing errors on the logic analyzer. Record the supply current drawn from the power supply to characterize power consumption versus voltage.

Expected results:

| Supply Voltage (V) | GPIO Toggle (MHz) | UART Errors | CSS Faults | Supply Current (mA) | Status         |
|--------------------|-------------------|-------------|------------|---------------------|----------------|
| 3.6                | 10.5              | 0           | 0          | 48                  | Normal         |
| 3.3                | 10.5              | 0           | 0          | 42                  | Normal         |
| 3.0                | 10.5              | 0           | 0          | 38                  | Normal         |
| 2.7                | 10.4              | 0           | 0          | 34                  | Marginal       |
| 2.6                | 9.8               | 2           | 0          | 32                  | Degraded       |
| 2.4                | 8.5               | 15          | 0          | 28                  | Severe Errors  |
| 2.2                | 0                 | All         | 1          | 18                  | CSS Fault      |
| 2.0                | 0                 | All         | 1          | 12                  | Brownout Reset |
| 1.8                | 0                 | All         | 1          | 0                   | No Operation   |

The data reveals that GPIO toggle frequency remains stable down to 2.7V, then degrades by 7% at 2.6V and 19% at 2.4V as the CMOS output driver's saturation voltage increases with reduced gate overdrive. UART framing errors emerge at 2.6V when the HSE crystal oscillator's phase noise increases, causing the UART baud rate generator to produce timing jitter that violates the receiver's sampling window. At 2.2V, the crystal stops oscillating entirely, triggering the CSS fault and halting CPU execution until the brownout reset at 2.0V forces a system restart. The supply current decreases monotonically with voltage, following the relationship P = CV²f for CMOS dynamic power dissipation, where C is gate capacitance, V is supply voltage, and f is switching frequency.

Plot GPIO toggle frequency and UART error rate versus supply voltage on dual Y-axes. The plots should show a cliff-edge failure at 2.2V where the crystal oscillator stops, rather than gradual degradation, confirming that the HSE oscillator acts as the primary voltage-dependent failure mechanism. This empirical failure threshold establishes the minimum operating voltage for reliable operation at 2.7V, providing a 300 mV margin above the CSS trip point and 700 mV above the brownout reset level.

Next, stress-test the NVIC interrupt controller by generating simultaneous interrupt requests from multiple peripherals and measuring the maximum sustainable interrupt rate before the CPU saturates. Configure Timer 3, Timer 4, and USART2 to generate interrupts at programmable rates, incrementing counters in each ISR to measure servicing throughput:

```c
#include "stm32f4xx.h"

volatile uint32_t tim3_count = 0;
volatile uint32_t tim4_count = 0;
volatile uint32_t usart2_count = 0;

void TIM3_IRQHandler(void) {
    if (TIM3->SR & TIM_SR_UIF) {
        tim3_count++;
        TIM3->SR &= ~TIM_SR_UIF;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
}

void TIM4_IRQHandler(void) {
    if (TIM4->SR & TIM_SR_UIF) {
        tim4_count++;
        TIM4->SR &= ~TIM_SR_UIF;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
}

void USART2_IRQHandler(void) {
    if (USART2->SR & USART_SR_RXNE) {
        uint8_t data = USART2->DR;
        usart2_count++;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
}

void timer3_init(uint16_t period) {
    RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
    TIM3->PSC = 83;
    TIM3->ARR = period - 1;
    TIM3->DIER = TIM_DIER_UIE;
    TIM3->CR1 = TIM_CR1_CEN;
    NVIC_SetPriority(TIM3_IRQn, 2);
    NVIC_EnableIRQ(TIM3_IRQn);
}

void timer4_init(uint16_t period) {
    RCC->APB1ENR |= RCC_APB1ENR_TIM4EN;
    TIM4->PSC = 83;
    TIM4->ARR = period - 1;
    TIM4->DIER = TIM_DIER_UIE;
    TIM4->CR1 = TIM_CR1_CEN;
    NVIC_SetPriority(TIM4_IRQn, 3);
    NVIC_EnableIRQ(TIM4_IRQn);
}

void usart2_rx_interrupt_init(void) {
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;
    
    GPIOA->MODER |= (0x2 << (2 * 2)) | (0x2 << (3 * 2));
    GPIOA->AFR[0] |= (0x7 << (2 * 4)) | (0x7 << (3 * 4));
    
    USART2->BRR = (42000000 / 115200);
    USART2->CR1 = USART_CR1_RE | USART_CR1_RXNEIE | USART_CR1_UE;
    
    NVIC_SetPriority(USART2_IRQn, 4);
    NVIC_EnableIRQ(USART2_IRQn);
}

int main(void) {
    SystemClock_Config();
    uart_init();
    
    timer3_init(1000);
    timer4_init(500);
    usart2_rx_interrupt_init();
    
    uint32_t last_tim3 = 0;
    uint32_t last_tim4 = 0;
    uint32_t last_usart2 = 0;
    
    while (1) {
        for (volatile uint32_t i = 0; i < 1680000; i++);
        
        uint32_t tim3_delta = tim3_count - last_tim3;
        uint32_t tim4_delta = tim4_count - last_tim4;
        uint32_t usart2_delta = usart2_count - last_usart2;
        
        last_tim3 = tim3_count;
        last_tim4 = tim4_count;
        last_usart2 = usart2_count;
        
        uart_transmit_string("TIM3: ");
        uart_transmit_string(" Hz, TIM4: ");
        uart_transmit_string(" Hz, USART2: ");
        uart_transmit_string(" chars/s\r\n");
    }
}
```

The Timer 3 ISR runs at 1 kHz (ARR = 999, prescaler = 84, giving 1 MHz / 1000 = 1 kHz), Timer 4 at 2 kHz (ARR = 499), and USART2 receives characters injected externally. Each ISR contains a delay loop consuming 100 CPU cycles (approximately 600 ns at 168 MHz) to simulate real ISR processing overhead. The NVIC priorities configure Timer 3 at priority 2 (higher urgency), Timer 4 at priority 3, and USART2 at priority 4 (lowest urgency), enabling preemption where Timer 3 can interrupt Timer 4 and USART2 mid-execution.

Connect a second UART-to-USB adapter to USART2 RX (PA3) and transmit a continuous stream of characters at 115200 baud using a Python script:

```python
import serial
import time

ser = serial.Serial('/dev/ttyUSB1', 115200)

while True:
    ser.write(b'X' * 100)
    time.sleep(0.001)
```

This generates 100,000 characters per second (100 chars × 1000 Hz), far exceeding the CPU's interrupt handling capacity. Monitor the interrupt count deltas reported on USART1 console and observe the saturation point. Gradually increase the USART2 transmission rate by reducing the Python sleep interval and measure when the USART2 interrupt count stops tracking the input rate.

Expected results at various USART2 input rates:

| USART2 Input (chars/s) | TIM3 Count (Hz) | TIM4 Count (Hz) | USART2 Count (chars/s) | CPU Load (%) |
|------------------------|-----------------|-----------------|------------------------|--------------|
| 1,000                  | 1000            | 2000            | 1000                   | 3            |
| 10,000                 | 1000            | 2000            | 10000                  | 30           |
| 50,000                 | 998             | 1995            | 48500                  | 85           |
| 100,000                | 982             | 1920            | 62000                  | 98           |
| 150,000                | 950             | 1800            | 65000                  | 100          |

The data reveals that the CPU saturates at approximately 100,000 interrupts per second total (1 kHz + 2 kHz + 97 kHz), corresponding to 1680 CPU cycles per interrupt (168 MHz / 100 kHz). Since each ISR consumes 100 cycles plus approximately 50 cycles for interrupt entry/exit overhead (NVIC state save, stack push, vector fetch, NVIC state restore, stack pop), the theoretical maximum is 168,000,000 / 150 = 1,120,000 interrupts per second, but the main loop execution and memory access contention reduce effective throughput to 100 kHz. Above this saturation point, lower-priority interrupts (USART2) experience starvation as higher-priority Timer 3 and Timer 4 interrupts preempt execution, causing the USART2 receive FIFO to overflow and drop characters.

Instrument the overflow condition by enabling the USART overrun error flag and counting dropped characters:

```c
void USART2_IRQHandler(void) {
    if (USART2->SR & USART_SR_ORE) {
        USART2->SR &= ~USART_SR_ORE;
        usart2_count++;
    }
    if (USART2->SR & USART_SR_RXNE) {
        uint8_t data = USART2->DR;
        usart2_count++;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
}
```

The overrun error flag (ORE) asserts when a new character arrives while the receive data register (DR) still holds an unread character from the previous reception. This occurs when the ISR service latency exceeds the character transmission time (8.68 μs at 115200 baud). Plot the overrun error rate versus USART2 input rate, revealing an exponential increase above the saturation threshold.

Validate interrupt priority preemption by triggering Timer 3, Timer 4, and USART2 interrupts simultaneously and measuring the execution order on the logic analyzer. Connect three GPIO outputs (PA6, PA7, PA8) to the logic analyzer and toggle them at ISR entry and exit:

```c
void TIM3_IRQHandler(void) {
    GPIOA->BSRR = (1 << 6);
    if (TIM3->SR & TIM_SR_UIF) {
        tim3_count++;
        TIM3->SR &= ~TIM_SR_UIF;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
    GPIOA->BSRR = (1 << (6 + 16));
}

void TIM4_IRQHandler(void) {
    GPIOA->BSRR = (1 << 7);
    if (TIM4->SR & TIM_SR_UIF) {
        tim4_count++;
        TIM4->SR &= ~TIM_SR_UIF;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
    GPIOA->BSRR = (1 << (7 + 16));
}

void USART2_IRQHandler(void) {
    GPIOA->BSRR = (1 << 8);
    if (USART2->SR & USART_SR_RXNE) {
        uint8_t data = USART2->DR;
        usart2_count++;
        for (volatile uint32_t i = 0; i < 100; i++);
    }
    GPIOA->BSRR = (1 << (8 + 16));
}
```

Trigger the three interrupts within a 1 μs window by synchronizing the timer periods to expire simultaneously. Observe the logic analyzer capture: PA6 (TIM3, priority 2) should assert first, followed by PA7 (TIM4, priority 3) after PA6 de-asserts, and finally PA8 (USART2, priority 4) last. If Timer 3 interrupts during Timer 4 execution, PA7 should de-assert mid-pulse when the NVIC preempts Timer 4 to service Timer 3, then resume after Timer 3 completes. This nested interrupt behavior validates that the NVIC priority hierarchy operates correctly under contention.

Finally, stress-test thermal performance by heating the STM32F4 package to 85°C (maximum commercial junction temperature rating) and monitoring clock accuracy and peripheral operation. Mount a resistive heater (10Ω, 10W ceramic power resistor) adjacent to the MCU package and power it from the 24V bench supply through a current-limiting resistor to dissipate 5W heat flux. Attach a K-type thermocouple to the top of the MCU package using thermal epoxy and monitor temperature with a multimeter in temperature measurement mode.

Implement a thermal monitoring routine that reads the internal temperature sensor via ADC channel 16:

```c
void temp_sensor_init(void) {
    ADC1->CR2 = 0;
    ADC1->SQR3 = 16;
    ADC1->SMPR1 |= (0x7 << (6 * 3));
    ADC->CCR |= ADC_CCR_TSVREFE;
    ADC1->CR2 |= ADC_CR2_ADON;
}

int16_t read_temp_celsius(void) {
    ADC1->CR2 |= ADC_CR2_SWSTART;
    while (!(ADC1->SR & ADC_SR_EOC));
    uint16_t adc_value = ADC1->DR;
    
    int16_t temp = ((int32_t)adc_value * 3300 / 4095 - 760) * 10 / 25 + 25;
    return temp;
}
```

The temperature sensor generates 760 mV at 25°C with 2.5 mV/°C temperature coefficient, according to the STM32F407 datasheet Section 6.3.21. The conversion formula calculates temperature as: T = ((V_sense - 0.76) / 0.0025) + 25, where V_sense = (ADC_value / 4095) × 3.3V.

Heat the MCU package from 25°C to 85°C in 10°C increments, dwelling 5 minutes at each temperature to allow thermal equilibrium. At each temperature, measure GPIO toggle frequency, UART baud rate accuracy, and internal temperature sensor reading:

| Package Temp (°C) | Internal Sensor (°C) | GPIO Toggle (MHz) | UART Error Rate | HSE Frequency (MHz) |
|-------------------|----------------------|-------------------|-----------------|---------------------|
| 25                | 28                   | 10.50             | 0.00%           | 8.000000            |
| 35                | 38                   | 10.50             | 0.00%           | 8.000001            |
| 45                | 48                   | 10.50             | 0.00%           | 8.000003            |
| 55                | 58                   | 10.49             | 0.00%           | 7.999995            |
| 65                | 68                   | 10.49             | 0.01%           | 7.999988            |
| 75                | 78                   | 10.48             | 0.02%           | 7.999972            |
| 85                | 88                   | 10.47             | 0.05%           | 7.999950            |

The internal temperature sensor reads 3°C higher than the external thermocouple due to self-heating from the 168 MHz core dissipating approximately 200 mW, elevating junction temperature above package case temperature. GPIO toggle frequency decreases by 0.3% from 25°C to 85°C, reflecting the negative temperature coefficient of CMOS propagation delay as carrier mobility decreases with lattice vibrations. The HSE crystal frequency drifts by −6.25 ppm (0.00005 MHz) over the temperature range, consistent with the crystal's specified ±20 ppm temperature stability. UART error rate increases marginally at elevated temperature due to accumulated baud rate drift from both the crystal frequency shift and temperature-dependent APB2 clock prescaler settling time.

Implement a watchdog timer recovery protocol that resets the system if the main loop stalls due to a hard fault or infinite loop. Configure the Independent Watchdog (IWDG) with a 5-second timeout:

```c
void iwdg_init(void) {
    IWDG->KR = 0xCCCC;
    IWDG->KR = 0x5555;
    IWDG->PR = 0x06;
    IWDG->RLR = 0x0FFF;
    IWDG->KR = 0xAAAA;
}

void iwdg_refresh(void) {
    IWDG->KR = 0xAAAA;
}
```

The IWDG runs from the 32 kHz LSI oscillator, independent of the HSE crystal and CPU clock, ensuring that it continues operating even if the main clock fails. The prescaler (PR = 6) divides by 256, yielding 125 Hz counter clock. The reload register (RLR = 0x0FFF = 4095) counts down at 125 Hz, producing a (4095 / 125) = 32.76-second timeout. Adjust RLR to 625 for a 5-second timeout: RLR = (5 seconds × 125 Hz) - 1 = 624.

Inject a deliberate infinite loop to trigger watchdog reset:

```c
int main(void) {
    SystemClock_Config();
    iwdg_init();
    uart_init();
    
    uart_transmit_string("System Start\r\n");
    
    for (uint32_t i = 0; i < 10; i++) {
        iwdg_refresh();
        uart_transmit_string("Running\r\n");
        for (volatile uint32_t j = 0; j < 1680000; j++);
    }
    
    uart_transmit_string("Entering infinite loop - watchdog will reset\r\n");
    while (1);
}
```

Observe the UART console output: the system prints "Running" ten times, then "Entering infinite loop", then resets after 5 seconds and repeats the sequence. Measure the reset interval with the oscilloscope by monitoring the NRST pin: it should pulse low for approximately 1 millisecond every 5 seconds, confirming the watchdog timeout. Check the Reset Status Register (RCC_CSR) to identify the reset source:

```c
void check_reset_source(void) {
    if (RCC->CSR & RCC_CSR_IWDGRSTF) {
        uart_transmit_string("Reset: Watchdog\r\n");
    } else if (RCC->CSR & RCC_CSR_PORRSTF) {
        uart_transmit_string("Reset: Power-On\r\n");
    } else if (RCC->CSR & RCC_CSR_SFTRSTF) {
        uart_transmit_string("Reset: Software\r\n");
    }
    RCC->CSR |= RCC_CSR_RMVF;
}
```

The watchdog reset flag (IWDGRSTF) sets after a watchdog timeout, distinguishing it from power-on reset (PORRSTF) or software reset (SFTRSTF via NVIC_SystemReset). This diagnostic capability enables firmware to log reset events and implement adaptive recovery strategies, such as entering safe mode or transmitting a distress beacon after repeated watchdog resets indicate persistent firmware failure.

Document the stress test results: supply voltage margining reveals the HSE oscillator as the primary failure mechanism at 2.2V; interrupt saturation occurs at 100 kHz aggregate rate with lower-priority interrupts experiencing starvation; thermal drift induces 0.3% clock frequency degradation at 85°C; watchdog timer provides autonomous recovery from firmware hang conditions. These boundary failure characterizations inform the firmware's defensive programming strategies: validate sensor readings against plausibility thresholds to detect ADC corruption from voltage transients, prioritize critical interrupts above background tasks to prevent starvation, and refresh the watchdog at least every 4 seconds to preempt timeout under normal operation. The combination of empirical failure thresholds and automated recovery protocols ensures that embedded systems exhibit graceful degradation and self-healing behavior rather than catastrophic failure when exposed to the harsh realities of production deployment.

## Operational Reference Guide & Diagnostic Checklist

This operational reference consolidates the verification procedures, measurement techniques, and diagnostic workflows developed through the laboratory exercises into a practitioner-ready checklist for embedded systems validation. The guide serves as a field manual for hardware engineers qualifying new silicon revisions, firmware developers troubleshooting production anomalies, and manufacturing test engineers designing automated test equipment. Each section provides acceptance criteria derived from datasheet specifications, measurement procedures with instrument settings, and root cause analysis decision trees for common failure modes.

### GPIO Verification Checklist

**Baseline Configuration:** PA5 as general-purpose output, push-pull, high-speed (180 MHz), no pull resistors. Firmware toggles PA5 in tight loop with direct ODR register XOR.

**Measurement Procedure:**
1. Connect oscilloscope 10X probe to PA5 with ground clip on adjacent GND pin
2. Set timebase to 50 ns/div, vertical scale to 1 V/div, trigger on rising edge at 1.65V
3. Measure toggle frequency with oscilloscope frequency counter (expect 10.5 MHz ± 1%)
4. Measure rise time 10–90% (expect < 10 ns), fall time 90–10% (expect < 10 ns)
5. Measure overshoot amplitude (accept < 10% of VDD), ringing frequency (document)

**Acceptance Criteria:**
- Toggle frequency: 10.5 MHz ± 1% (9 cycles per complete high-low transition at 168 MHz CPU clock)
- Rise/fall time: < 10 ns for high-speed GPIO configuration
- Overshoot: < 300 mV (< 10% of 3.3V supply)
- No contact-bounce or glitches visible on infinite persistence display

**Failure Modes & Root Causes:**
- Low toggle frequency (< 9 MHz): CPU clock not running at 168 MHz. Verify PLL configuration in RCC_PLLCFGR. Check HSE oscillator startup with probe on OSC_IN pin.
- Slow rise time (> 20 ns): GPIO output speed setting incorrect. Verify OSPEEDR register reads 0b11 for high speed. Check PCB trace length and load capacitance.
- Excessive ringing (> 100 MHz): Parasitic inductance in probe ground lead. Use shortest possible ground connection. Add 10Ω series resistor at GPIO pin to dampen resonance.
- Asymmetric rise/fall: Normal CMOS behavior (NMOS stronger than PMOS). No action required unless rise-fall asymmetry exceeds 3:1 ratio.

### UART Verification Checklist

**Baseline Configuration:** USART1 on PA9 (TX) / PA10 (RX), 115200 baud, 8N1 framing, APB2 clock 84 MHz, BRR = 0x1CD3 calculated from 84 MHz / 115200.

**Measurement Procedure:**
1. Connect logic analyzer Channel 0 to PA9 (UART TX), threshold 1.65V, sampling 100 MS/s
2. Enable Async Serial protocol analyzer: 115200 baud, 8 data bits, no parity, 1 stop bit, LSB first
3. Transmit test string "EMBEDDED\r\n" with 1-second interval
4. Measure start bit duration, each data bit duration, stop bit duration with timing markers
5. Verify protocol analyzer decodes all characters correctly without framing errors
6. Measure inter-character jitter by computing standard deviation of start-bit-to-start-bit intervals over 100 frames

**Acceptance Criteria:**
- Bit duration: 8.68 μs ± 0.5% (1 / 115200 = 8.680556 μs)
- Baud rate error: < 2% (RS-232 tolerance for reliable communication)
- Start-to-start jitter: < 10 ns standard deviation (< 0.1% of bit period)
- Protocol decode: Zero framing errors, zero parity errors (if parity enabled)

**Failure Modes & Root Causes:**
- Incorrect baud rate (> 2% error): BRR register value wrong. Recalculate: BRR = (APB_clock + baud/2) / baud. Verify APB2 clock frequency with RCC_CFGR inspection.
- Framing errors: Start bit not followed by 8 data bits and stop bit. Check transmitter and receiver both configured for 8N1. Verify HSE crystal oscillating at correct frequency with oscilloscope on OSC_IN.
- High jitter (> 100 ns): Main loop execution time variable. Use hardware timer to generate fixed transmission interval instead of delay loop. Check for interrupt handlers preempting main loop.
- Garbled characters: Electrical noise coupling into UART signal. Add 100Ω series resistor at transmitter output. Use twisted-pair or shielded cable for UART connection. Ground shield at one end only to avoid ground loops.

### SPI Verification Checklist

**Baseline Configuration:** SPI1 on PB3 (SCK) / PB4 (MISO) / PB5 (MOSI), Mode 0 (CPOL=0, CPHA=0), prescaler /16 for 5.25 MHz clock, communicating with 25LC640 EEPROM.

**Measurement Procedure:**
1. Connect logic analyzer Channel 0 to PB3 (SCK), Channel 1 to PB4 (MISO), Channel 2 to PB5 (MOSI)
2. Enable SPI protocol analyzer: Mode 0, MSB first, 8 bits per transfer
3. Write test pattern 0x00–0xFF to EEPROM addresses 0x0000–0x00FF
4. Read back test pattern and compare against expected values
5. Count bit errors: errors = sum of (read_value XOR expected_value)
6. Measure SPI clock frequency and duty cycle on Channel 0

**Acceptance Criteria:**
- SPI clock frequency: Matches configured prescaler (84 MHz / prescaler)
- SPI clock duty cycle: 50% ± 5%
- Bit error rate: Zero errors for clock ≤ 20 MHz (EEPROM maximum rating)
- Read throughput: > 10 KB/s for prescaler /16

**Failure Modes & Root Causes:**
- Bit errors at high clock rates (> 20 MHz): Exceeding slave device maximum clock frequency. Reduce SPI clock by increasing prescaler. Verify slave datasheet maximum clock specification.
- Clock duty cycle distortion (< 40% or > 60%): PCB trace impedance mismatch causing ringing. Add series termination resistor (22–47Ω) at master SCK output. Check signal integrity with oscilloscope on SCK at slave input pin.
- Data corruption on specific addresses: EEPROM write not completed before read. Increase write delay to 5 ms minimum per datasheet specification. Poll EEPROM status register instead of fixed delay.
- No MISO data (all reads return 0xFF): MISO pin not connected or configured as output instead of input. Verify GPIO alternate function mapping in AFR register. Check continuity with multimeter.

### ADC Verification Checklist

**Baseline Configuration:** ADC1 Channel 1 on PA1, 12-bit resolution, sampling time 56 cycles, ADC clock 21 MHz (PCLK2/4), input voltage 1.65V from potentiometer or precision reference.

**Measurement Procedure:**
1. Apply stable 1.65V to PA1 (half of 3.3V supply for mid-scale test)
2. Perform 1000 ADC conversions in loop, storing results in array
3. Compute mean, standard deviation, minimum, maximum
4. Calculate voltage from ADC value: V = (ADC_value / 4095) × 3.3V
5. Compare measured voltage against applied voltage (verify with multimeter)

**Acceptance Criteria:**
- Mean ADC value: 2048 ± 10 for 1.65V input (mid-scale, 12-bit)
- Standard deviation: < 4 LSB (reflecting thermal noise and quantization)
- Absolute error: < 0.5% (16 mV for 3.3V reference)
- Monotonicity: No missing codes when sweeping input from 0–3.3V

**Failure Modes & Root Causes:**
- Under-reading (mean < 2038): Insufficient sampling time for high source impedance. Increase SMPR register value. Calculate required sampling time: t_sample > 5 × R_source × C_sample (where C_sample = 12 pF per datasheet).
- High noise (standard deviation > 10 LSB): Analog supply noise or digital switching coupling into ADC input. Add 100 nF ceramic + 10 μF tantalum decoupling capacitor on VDDA. Use separate analog ground plane.
- Nonlinearity: Differential nonlinearity (DNL) or integral nonlinearity (INL) exceeding ±2 LSB specification. Verify VREF+ connected to 3.3V and VREF- connected to GND. Calibrate ADC using built-in calibration routine in ADC_CR2.
- Offset error: All readings shifted by constant value. Perform single-point calibration by measuring known voltage and computing: ADC_corrected = ADC_raw - (ADC_measured_at_V_known - ADC_expected_at_V_known).

### Timer PWM Verification Checklist

**Baseline Configuration:** Timer 2 Channel 1 on PA0, 10 kHz frequency (ARR = 99), 50% duty cycle (CCR1 = 49), prescaler 84 for 1 MHz timebase, PWM mode 1.

**Measurement Procedure:**
1. Connect oscilloscope to PA0, timebase 20 μs/div to display 5 cycles
2. Measure period with oscilloscope period counter (expect 100.0 μs)
3. Measure positive pulse width with cursor or pulse-width measurement (expect 50.0 μs)
4. Measure duty cycle with oscilloscope duty cycle measurement (expect 50.0%)
5. Vary CCR1 from 0 to 99 and plot measured pulse width vs. CCR1 value

**Acceptance Criteria:**
- Frequency accuracy: 10.000 kHz ± 0.1% (100.0 μs period)
- Duty cycle accuracy: Matches (CCR1 / ARR) × 100% within 1 count resolution
- Linearity: R² > 0.9999 for pulse width vs. CCR1 regression
- Edge timing: Rise time < 50 ns, fall time < 50 ns

**Failure Modes & Root Causes:**
- Incorrect frequency: ARR or PSC register value wrong. Recalculate: f_pwm = f_timer / ((PSC + 1) × (ARR + 1)). Verify timer input clock from RCC_CFGR (APB1 clock × 2 when APB1 prescaler ≠ 1).
- Duty cycle offset: CCR1 value not taking effect. Enable preload bit (OC1PE in CCMR1) and auto-reload preload (ARPE in CR1). Verify update event occurs to transfer preload to active register.
- Glitches when changing duty cycle: Modifying CCR1 mid-period without preload. Always enable OC1PE to defer CCR1 update until next period boundary.
- No output on PA0: GPIO alternate function not configured. Verify MODER = 0b10 (alternate function) and AFR = 0x01 (AF1 = TIM2_CH1) for PA0.

### Interrupt Latency Verification Checklist

**Baseline Configuration:** Timer 3 generating 1 kHz interrupt, priority 2, ISR toggles PA6 for latency measurement.

**Measurement Procedure:**
1. Connect oscilloscope Channel 1 to PA6 (ISR entry marker), Channel 2 to Timer 3 output (interrupt source)
2. Configure edge trigger on Channel 2 rising edge
3. Measure time from Channel 2 rising edge to Channel 1 rising edge (ISR latency)
4. Repeat 100 measurements and compute mean, minimum, maximum, standard deviation
5. Vary interrupt load by enabling additional interrupt sources and re-measure

**Acceptance Criteria:**
- Base interrupt latency: 12–20 CPU cycles (71–119 ns at 168 MHz), comprising NVIC state save, vector fetch, ISR entry
- Maximum latency under load: < 50 cycles when lower-priority interrupts active
- Latency jitter: < 10 cycles standard deviation
- Priority inversion: Zero occurrences (lower-priority ISR never preempts higher-priority)

**Failure Modes & Root Causes:**
- High latency (> 100 cycles): CPU saturated by interrupt load. Reduce aggregate interrupt rate or increase ISR execution speed. Verify main loop not running with interrupts globally disabled.
- Priority inversion: Higher-priority interrupt delayed by lower-priority ISR. Check NVIC priority group and preemption priority configuration in NVIC_SetPriority. Ensure preempt priority differs between interrupt sources.
- Variable latency: Instruction cache misses or bus contention. Enable I-cache and D-cache in Cortex-M4. Place time-critical ISRs in SRAM instead of Flash for deterministic fetch.
- Missed interrupts: Interrupt flag not cleared in ISR. Always read and clear pending bit (TIM->SR &= ~TIM_SR_UIF) before exiting ISR to acknowledge interrupt.

### Supply Voltage Margining Checklist

**Baseline Configuration:** Supply voltage swept from 3.6V to 1.7V in 100 mV steps, monitoring GPIO toggle frequency, UART errors, CSS faults, and brownout reset.

**Measurement Procedure:**
1. Configure programmable DC supply to output 3.3V, connect to VDD with JP5 removed
2. Enable oscilloscope continuous capture on PA5 (GPIO toggle) and logic analyzer on PA9 (UART)
3. Decrease supply voltage by 100 mV, wait 10 seconds for thermal equilibrium
4. Record GPIO frequency, UART error count, CSS fault count at each voltage
5. Continue until brownout reset occurs (UART stops, MCU ceases operation)

**Acceptance Criteria:**
- Nominal operation: 3.6V to 2.7V with < 1% frequency deviation, zero UART errors
- Marginal operation: 2.7V to 2.2V with < 10% frequency deviation, < 1% UART error rate
- Clock security system trip: 2.2V ± 0.1V (HSE oscillator stop)
- Brownout reset: 2.0V ± 0.1V per datasheet BOR Level 3 specification

**Failure Modes & Root Causes:**
- Early degradation (> 2.7V): Crystal oscillator load capacitors incorrect value. Verify CL1 and CL2 match datasheet recommendation (typically 20 pF for 8 MHz crystal). Measure actual oscillation amplitude on OSC_IN pin.
- No CSS fault: Clock security system not enabled. Set CSSON bit in RCC_CR. Verify NMI_Handler configured to catch CSS fault and clear CSSC bit in RCC_CIR.
- Brownout reset at wrong voltage: BOR level mismatch. Check FLASH option bytes BOR_LEV field. Program to Level 3 (2.7V rising, 2.6V falling) for industrial temperature range operation.
- Oscillator restart failure: Crystal drive level too low. Reduce series resistor on oscillator output (typically 1 kΩ to 100Ω) to increase drive strength.

### Thermal Stress Testing Checklist

**Baseline Configuration:** MCU package heated from 25°C to 85°C (commercial temperature range maximum), monitoring internal temperature sensor, GPIO toggle frequency, and UART baud rate accuracy.

**Measurement Procedure:**
1. Attach thermocouple to MCU package top center using thermal epoxy
2. Position 10W resistive heater 5 mm from MCU package side
3. Increase heater current to raise package temperature by 10°C increments
4. Wait 5 minutes at each temperature for thermal equilibrium
5. Read internal temperature sensor via ADC Channel 16
6. Measure GPIO toggle frequency and UART baud rate at each temperature

**Acceptance Criteria:**
- Internal sensor accuracy: Within ±5°C of thermocouple reading
- Clock frequency drift: < 1% over 25–85°C range (< 1.68 MHz at 168 MHz)
- UART baud rate error: < 2% over temperature range
- Functional operation: No resets, faults, or peripheral failures at 85°C

**Failure Modes & Root Causes:**
- Large temperature sensor error (> 10°C): Calibration required. Perform two-point calibration at known temperatures and apply linear correction: T_calibrated = (T_raw - offset) × gain.
- Excessive clock drift (> 2%): Crystal temperature coefficient specification exceeded. Use TCXO (temperature-compensated crystal oscillator) instead of standard crystal for ±10 ppm over temperature.
- Thermal shutdown: Junction temperature exceeding 105°C absolute maximum. Improve thermal design: add heatsink, increase airflow, reduce clock frequency to lower power dissipation.
- Peripheral failure at elevated temperature: Setup/hold time violations due to increased propagation delay. Add wait states to Flash access (set LATENCY field in FLASH_ACR). Reduce peripheral clock frequencies.

### Watchdog Recovery Verification Checklist

**Baseline Configuration:** Independent watchdog (IWDG) enabled with 5-second timeout, firmware refreshes every 1 second in normal operation, infinite loop injected to trigger reset.

**Measurement Procedure:**
1. Configure IWDG: prescaler 256, reload 625 for 5-second timeout
2. Implement main loop that refreshes IWDG every 1 second and prints "Running" to UART
3. After 10 iterations, enter infinite loop without refreshing watchdog
4. Monitor UART console for reset message
5. Measure time from last watchdog refresh to reset with oscilloscope on NRST pin

**Acceptance Criteria:**
- Watchdog timeout accuracy: 5.0 seconds ± 10% (accounting for 32 kHz LSI oscillator tolerance)
- Reset pulse width: 1 ms minimum per datasheet specification
- Reset source identification: RCC_CSR register IWDGRSTF bit set after watchdog reset
- Firmware restart: System boots and resumes normal operation after reset

**Failure Modes & Root Causes:**
- No watchdog reset: IWDG not enabled. Verify IWDG->KR written with 0xCCCC unlock, 0x5555 access enable, configuration values, then 0xAAAA to start. Check LS oscillator running (LSIRDY bit in RCC_CSR).
- Premature reset (< 5 seconds): Reload value too small or refresh not occurring. Increase RLR value. Verify iwdg_refresh() called periodically from main loop and not blocked by long-running functions.
- No reset (> 10 seconds): Prescaler value incorrect or LSI frequency deviation. Recalculate: timeout = (4 × 2^PR × RLR) / f_LSI. Measure actual LSI frequency by routing to MCO pin and capturing with frequency counter.
- Reset loop: Firmware fails immediately after reset. Check reset source in RCC_CSR and log to nonvolatile storage. Implement progressive failure handling: enter safe mode after 3 consecutive watchdog resets.

This operational reference guide and diagnostic checklist consolidates the empirical validation methodology into a field-deployable resource for embedded systems verification. Practitioners apply these procedures during initial board bring-up, firmware qualification testing, production line functional test, and field return failure analysis. The combination of datasheet-derived acceptance criteria, standardized measurement procedures, and root cause decision trees enables systematic troubleshooting that isolates hardware faults, firmware defects, and environmental stress factors. The exhaustive verification coverage—from GPIO toggle timing through watchdog recovery—ensures that embedded systems exhibit predictable, deterministic behavior across the full operational envelope, surviving the hostile realities of automotive voltage transients, industrial thermal extremes, and electromagnetic interference that characterize production deployment environments.
