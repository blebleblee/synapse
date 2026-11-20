# Operational Verification Labs: Ethical Hacking

## Objective & Lab Bench Setup

Modern embedded systems, IoT devices, and hardware security modules expose attack surfaces far beyond network protocols and software vulnerabilities. Physical access to a device grants an adversary the ability to probe signal lines, extract firmware from flash memory, observe cryptographic operations through side channels, and inject faults to bypass security boundaries. This laboratory guide trains the practitioner to execute hardware-level penetration testing using industry-standard tools: logic analyzers for protocol reverse engineering, UART and JTAG adapters for debug interface exploitation, and flash programmers for firmware extraction and modification. Each exercise moves from reconnaissance through exploitation to verification, mirroring the kill chain of a real-world hardware security assessment.

The lab bench must be equipped with a USB-based logic analyzer capable of sampling at least eight channels at 24 MHz or higher. The Saleae Logic series, Dreamsourcelab DSLogic, or any sigrok-compatible device suffices. A multi-protocol USB-to-serial adapter supporting UART, SPI, and I²C is essential; the FTDI FT2232H or FT4232H breakout boards are industry workhorses, offering both high-speed serial conversion and bit-bang SPI/I²C modes. A JTAG adapter compatible with OpenOCD, such as the SEGGER J-Link EDU, Bus Pirate, or FTDI-based adapter, enables boundary scan and on-chip debugging. Fine-tipped probes, jumper wires with 0.1-inch spacing, and a jeweler's magnifier or USB microscope facilitate signal interception on densely packed PCBs. A soldering iron and flux are necessary when test points are absent and direct wire attachment to IC pins or vias is required.

Software installation proceeds in a unified diagnostic suite. On Debian-based systems, execute `apt-get install sigrok-cli pulseview openocd flashrom binwalk gdb-multiarch minicom picocom screen` to install the signal analysis stack, firmware tools, and terminal emulators. On Fedora or Red Hat derivatives, substitute `dnf install sigrok-cli PulseView openocd flashrom binwalk gdb`. Verify sigrok installation by running `sigrok-cli --scan`; the output should enumerate connected logic analyzers. Confirm OpenOCD function with `openocd --version`; version 0.11.0 or later is preferred for ARM Cortex-M and RISC-V support. Flashrom version 1.2 or newer provides robust SPI flash detection across a wide range of chipsets. Binwalk 2.3.3 or later includes entropy analysis and filesystem carving for firmware images.

The target device for these exercises is a generic ARM Cortex-M microcontroller development board with exposed JTAG and UART test points, an SPI flash chip for bootloader and application firmware, and a serial console for diagnostic output. Common platforms include the STM32 Nucleo, NXP LPC-Link2, or any ESP32 development kit with accessible debug headers. If the device employs a proprietary or locked-down bootloader, the exercises adapt to demonstrate attack vectors against read-protection mechanisms and secure boot failures. A benchtop power supply or USB power delivery adapter provides stable voltage; observe current draw during fault injection experiments to detect anomalies indicative of security state transitions.

Physical workspace ergonomics matter. Secure the target device in a PCB holder or vise to prevent motion during probing. Use an anti-static mat and wrist strap to protect sensitive CMOS components from electrostatic discharge. Label each probe lead with colored heat-shrink tubing or adhesive tags corresponding to signal names: GND, TDI, TDO, TCK, TMS for JTAG; TX, RX, GND for UART; MOSI, MISO, SCK, CS for SPI. A labeled diagram of the target board's pinout, either from the vendor's documentation or reverse-engineered via continuity testing, should be taped to the bench for quick reference. Adequate lighting from an adjustable LED task lamp eliminates shadowing when working under magnification.

---

## Exercise 1: Live Hardware Probing & Signal Capture

The first step in any hardware penetration test is reconnaissance: identifying communication buses, enumerating debug interfaces, and capturing live traffic to understand the device's operational state machine. Begin by visually inspecting the target PCB under magnification. Locate unpopulated header footprints, test points, or silkscreen labels indicating UART, JTAG, SPI, or I²C connections. Common UART pinouts follow a GND-TX-RX-VCC pattern, though some designs omit VCC. JTAG interfaces typically expose five signals: TDI (Test Data In), TDO (Test Data Out), TCK (Test Clock), TMS (Test Mode Select), and TRST (Test Reset, sometimes optional). SPI flash chips present eight-pin SOIC or WSON packages with pins labeled CLK, MOSI, MISO, CS, WP, HOLD, VCC, and GND.

Connect the logic analyzer's ground lead to a known ground point on the target board—any exposed copper pour connected to the power supply's negative terminal suffices. Attach logic analyzer channels to the UART TX and RX pins. If the pinout is unknown, use a multimeter in continuity mode to trace the PCB from the microcontroller's UART peripheral pins to external headers or test pads. Power the target device and initiate a capture in PulseView or via `sigrok-cli`. For UART, begin with a conservative sample rate of 1 MHz, which comfortably oversamples common baud rates from 9600 to 115200 bps. Execute `sigrok-cli --driver fx2lafw --config samplerate=1M --channels 0=TX,1=RX --time 10s --output-format ascii:width=80 > uart_capture.txt` to record ten seconds of serial traffic. The output file will contain human-readable ASCII if the baud rate and frame parameters are correctly detected by the protocol decoder.

Examine the captured waveform in PulseView. Enable the UART protocol decoder and iterate through standard baud rates: 9600, 19200, 38400, 57600, 115200, 230400, 460800, and 921600. Most embedded systems default to 115200 8N1 (eight data bits, no parity, one stop bit). If the decoded output displays garbled characters, the baud rate is incorrect. Adjust the decoder settings until coherent text appears. Look for boot messages, debug strings, or error logs that reveal software version numbers, memory addresses, or internal state information. For example, a message like `U-Boot 2021.04 (Jul 15 2023 - 10:42:03 +0000)` confirms the bootloader identity and build date, while `Starting kernel at 0x08000000` discloses the application entry point.

Once the UART baud rate is identified, establish a bidirectional terminal session using minicom, picocom, or screen. Execute `minicom -D /dev/ttyUSB0 -b 115200` to open an interactive console. Press the Enter key several times to determine if a command prompt appears. Many devices expose a root shell or bootloader console over UART with no authentication. If a login prompt appears, attempt default credentials: `root` with no password, `admin/admin`, or `root/toor`. Consult the device manufacturer's documentation or search vulnerability databases for known default credentials. If authentication blocks access, proceed to the next phase of hardware exploitation.

Next, investigate JTAG presence and functionality. JTAG is a boundary-scan standard (IEEE 1149.1) originally designed for PCB manufacturing test but widely repurposed for in-circuit debugging. A functional JTAG interface allows full control over the processor core: halting execution, reading and writing memory, setting breakpoints, and single-stepping through instructions. Connect the JTAG adapter's TDI, TDO, TCK, TMS, and GND lines to the corresponding target board pins. If TRST is present, connect it as well; otherwise, leave it floating. Power the target device and launch OpenOCD with an appropriate configuration. For an STM32F4 microcontroller using an FTDI-based adapter, execute `openocd -f interface/ftdi/um232h.cfg -f target/stm32f4x.cfg`. OpenOCD will enumerate the JTAG chain, reporting detected TAP (Test Access Port) controllers and their IDCODE values. A successful connection yields output resembling:

```text
Info : clock speed 1000 kHz
Info : JTAG tap: stm32f4x.cpu tap/device found: 0x4ba00477 (mfg: 0x23b (ARM Ltd), part: 0xba00, ver: 0x4)
Info : stm32f4x.cpu: hardware has 6 breakpoints, 4 watchpoints
Info : starting gdb server for stm32f4x.cpu on 3333
```

This output confirms the presence of an ARM Cortex-M4 core with six hardware breakpoints and four watchpoints. OpenOCD now listens on TCP port 3333 for GDB connections and port 4444 for Tcl command-line interface access. Open a second terminal and connect via telnet: `telnet localhost 4444`. Issue the command `reset halt` to reset the processor and immediately halt execution at the reset vector. Execute `mdw 0x08000000 64` to dump sixty-four words (256 bytes) of flash memory starting at address 0x08000000, the typical base address for STM32 internal flash. The output displays raw instruction opcodes and data constants in hexadecimal. Use `arm disassemble 0x08000000 32` to disassemble the first thirty-two instructions, revealing the reset handler and vector table structure.

If OpenOCD reports "No device found" or a TAP identification failure, the JTAG interface may be disabled by fuse settings, pulled to fixed logic levels by resistors, or protected by an authentication mechanism. Attempt to locate alternative debug interfaces. Some ARM Cortex-M devices implement Serial Wire Debug (SWD), a two-wire alternative to JTAG using only SWDIO and SWCLK. Reconfigure OpenOCD for SWD by modifying the transport line in the interface configuration: `transport select swd`. For devices with locked debug ports, consult vendor-specific debug authentication procedures or proceed to fault injection techniques to bypass protection.

Capture SPI traffic from the external flash chip by connecting logic analyzer channels to CLK, MOSI, MISO, and CS. SPI operates as a full-duplex synchronous protocol with a master (the microcontroller) generating clock and chip select signals and a slave (the flash memory) responding to commands. Power-cycle the target and trigger the logic analyzer on the falling edge of the CS line, indicating the start of a transaction. Enable the SPI protocol decoder in PulseView with the appropriate clock polarity and phase settings (typically mode 0: CPOL=0, CPHA=0 for most flash chips). Observe the command bytes: 0x03 indicates a standard read operation, 0x9F requests the JEDEC ID, 0x06 enables write operations, and 0x02 initiates a page program. Decode the address bytes following the command to determine which flash sectors the firmware accesses during boot. This information guides later firmware extraction and modification.

---

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

With debug interfaces identified and signal capture validated, the next objective is comprehensive memory extraction and register inspection. Firmware residing in non-volatile storage—SPI flash, EEPROM, or internal flash—constitutes the primary intellectual property and attack surface. Reading this firmware allows static analysis for vulnerabilities, reverse engineering of proprietary algorithms, and identification of hardcoded secrets such as cryptographic keys, API tokens, or backdoor credentials.

Begin by extracting firmware from an external SPI flash chip using flashrom. Disconnect the logic analyzer and connect the FTDI FT2232H adapter in SPI mode. The FT2232H channel A operates as an SPI master when configured with the appropriate pin mapping: AD0 (TCK/SCK) as clock, AD1 (TDI/MOSI) as master-out-slave-in, AD2 (TDO/MISO) as master-in-slave-out, and AD3 (TMS/CS) as chip select. Physically connect these pins to the corresponding SPI flash chip pins. On many devices, this requires desoldering the flash chip or lifting pin 1 (CS) to prevent the microcontroller from interfering with read operations. If desoldering is impractical, power down the microcontroller entirely by removing its power supply or asserting a hardware reset line.

Execute `flashrom -p ft2232_spi:type=232H,port=A` to probe the flash chip. Flashrom queries the JEDEC ID (manufacturer and device code) and reports the detected chip model, capacity, and supported erase block sizes. For a typical Winbond W25Q32 (32 Mbit / 4 MiB) flash, the output resembles:

```text
Found Winbond flash chip "W25Q32.V" (4096 kB, SPI) on ft2232_spi.
```

To read the entire flash contents into a file, execute `flashrom -p ft2232_spi:type=232H,port=A --read firmware_dump.bin`. The read operation proceeds at approximately 200-300 kB/s, completing in fifteen to twenty seconds for a 4 MiB chip. Verify the dump integrity by comparing checksums across multiple reads: `sha256sum firmware_dump.bin`. If checksums differ, inspect wiring for loose connections or electromagnetic interference from nearby switching regulators. Re-solder or reposition the FTDI adapter and retry. Once a stable, consistent dump is obtained, archive the file with metadata annotations: device model, date, and purpose. This original firmware image serves as the baseline for all subsequent modification and rewriting operations.

Analyze the extracted firmware with binwalk to identify embedded filesystems, compressed archives, and cryptographic signatures. Execute `binwalk firmware_dump.bin` to generate a summary of detected structures. Common findings include U-Boot bootloader headers at offset 0x0000, kernel images (zImage or uImage) compressed with gzip or LZMA, and SquashFS or JFFS2 filesystems containing the root directory tree. For example:

```text
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             U-Boot uImage header, ARM, Linux Kernel Image, Tue Jul 18 14:32:10 2023
64            0x40            gzip compressed data, maximum compression
262144        0x40000         Squashfs filesystem, little endian, version 4.0
```

Extract the filesystem with `binwalk --extract firmware_dump.bin`. Binwalk creates a directory named `_firmware_dump.bin.extracted` containing the decompressed kernel and mounted filesystem tree. Navigate into the SquashFS root and inspect `/etc/passwd`, `/etc/shadow`, and `/etc/config/` for user credentials and service configurations. Search for hardcoded secrets using `grep -r "password\|api_key\|secret\|token" .` within the extracted directory. Examine initialization scripts in `/etc/init.d/` to understand the boot sequence and identify services listening on network sockets. If encrypted partitions or obfuscated binaries are present, entropy analysis via `binwalk --entropy firmware_dump.bin` reveals high-entropy regions indicative of encryption or compression. High entropy confined to specific offsets suggests targeted protection of sensitive code or data.

For devices with internal flash only, firmware extraction proceeds via the JTAG or SWD interface. Reconnect OpenOCD and establish a GDB session. Launch `gdb-multiarch` and connect to OpenOCD's GDB server: `target extended-remote localhost:3333`. Issue `monitor reset halt` to reset the processor and halt at the entry point. Determine the flash memory region from the microcontroller's datasheet; for STM32F4, internal flash begins at 0x08000000 and extends to 0x08100000 (1 MiB). Dump the entire flash region with `dump binary memory flash_dump.bin 0x08000000 0x08100000`. The operation completes in several minutes, depending on the JTAG adapter's clock speed and OpenOCD's buffer efficiency. Verify the dump by computing checksums and comparing against a second extraction.

Inspect CPU registers and peripheral state to understand the runtime security posture. In the GDB session, execute `info registers` to display general-purpose and special-function registers. On ARM Cortex-M, examine the Control register (CONTROL) to determine thread mode versus handler mode and privileged versus unprivileged execution. Check the PRIMASK, FAULTMASK, and BASEPRI registers for interrupt masking state. Read the Memory Protection Unit (MPU) configuration registers via `monitor mdw 0xE000ED90 8` to observe MPU_TYPE, MPU_CTRL, and region descriptors. If the MPU is enabled (MPU_CTRL bit 0 set), decode the region base addresses and permission attributes to map protected memory regions. Misconfigured MPU settings often leave critical peripherals or memory-mapped I/O accessible from unprivileged code, enabling privilege escalation attacks.

Peripheral register inspection reveals security-relevant configuration details. For cryptographic accelerators, read control and status registers to determine key sizes, algorithm modes, and key storage locations. On STM32 devices with a True Random Number Generator (TRNG), inspect the RNG_CR and RNG_SR registers at base address 0x50060800. If the TRNG is improperly seeded or its entropy source is externally influenced via GPIO pins, the generated random numbers become predictable, compromising cryptographic operations. For secure boot implementations, examine flash option bytes and read protection levels. Execute `monitor stm32f4x options_read` in OpenOCD to display option byte values. If RDP (Read Protection) is set to Level 0, full debug access is permitted. Level 1 disables external debugger access but allows user code to read flash. Level 2 permanently locks the device, disabling both debug and user readback. Verify that production devices enforce Level 2 to prevent firmware extraction via JTAG.

---

## Exercise 3: Fault Simulation & Exploit Verification

Fault injection attacks manipulate a device's physical operating conditions—voltage, clock, temperature, or electromagnetic fields—to induce transient computational errors that subvert security mechanisms. Glitching attacks target specific instruction sequences during authentication checks, secure boot signature verification, or privilege escalation transitions. By causing the processor to skip a conditional branch or corrupt a security flag in a register, an attacker bypasses access controls without exploiting software vulnerabilities. This exercise demonstrates voltage glitching to bypass a password authentication routine in a sample embedded application.

The target firmware implements a simple password check: the user enters a password via UART, and the device compares it against a hardcoded reference string stored in flash. If the strings match, the device grants access to a diagnostic shell; otherwise, it denies access and resets. The comparison is performed by a byte-wise loop that returns immediately upon detecting a mismatch. The assembly code for the comparison function, disassembled via GDB, resembles:

```text
08000a10:  ldrb r2, [r0], #1
08000a12:  ldrb r3, [r1], #1
08000a14:  cmp  r2, r3
08000a16:  bne  08000a24      ; branch if not equal
08000a18:  cbz  r2, 08000a20  ; check for null terminator
08000a1a:  b    08000a10      ; loop
08000a20:  movs r0, #1        ; return 1 (success)
08000a22:  bx   lr
08000a24:  movs r0, #0        ; return 0 (failure)
08000a26:  bx   lr
```

The vulnerability lies in the conditional branch at 0x08000a16. If a fault occurs precisely when this instruction executes, the processor may skip the branch and fall through to the success path, returning 1 despite an incorrect password. Inducing this fault requires precise timing and a controlled voltage transient.

Construct a voltage glitching circuit using a fast-switching MOSFET (e.g., IRF7404) controlled by a GPIO pin on a separate microcontroller or FPGA. The MOSFET is placed in series with the target device's power supply, allowing the glitch controller to momentarily short VCC to GND, creating a voltage sag. The glitch duration must be on the order of tens to hundreds of nanoseconds—long enough to corrupt an instruction fetch or ALU operation, but short enough to avoid a full processor reset. A benchtop oscilloscope monitors the voltage rail at the target device's VCC pin to visualize the glitch waveform.

Load the target firmware into the microcontroller and initiate the password authentication routine. The glitch controller monitors the UART TX line using a logic analyzer trigger; when it detects the password prompt string, it begins a systematic glitch sweep. The controller increments the glitch delay in 100 ns steps, starting from the prompt transmission and continuing through the expected comparison duration. For each delay value, the controller issues the glitch pulse and observes whether the target grants access or denies it. When a successful glitch occurs, the logic analyzer captures the UART response: instead of "Access Denied," the device transmits "Access Granted" and presents the diagnostic shell prompt.

Record the successful glitch timing parameters: delay from prompt to glitch (e.g., 3200 ns) and glitch pulse width (e.g., 250 ns). These parameters are device-specific and depend on processor clock frequency, instruction pipeline depth, and power supply decoupling capacitor values. Repeat the attack ten times to confirm repeatability. If the success rate exceeds 80%, the vulnerability is reliably exploitable. Document the exact glitch waveform using the oscilloscope's screenshot or data export function. A successful glitch typically manifests as a sharp voltage drop from 3.3 V to below the processor's minimum operating voltage (approximately 2.0 V), followed by a rapid recovery as decoupling capacitors recharge.

To mitigate voltage glitching, recommend hardware countermeasures: increase power supply decoupling capacitance, add series inductors to slow transient response, and implement voltage supervisory ICs that reset the processor upon detecting out-of-spec conditions. Software countermeasures include redundant checks with inverted logic: instead of a single `if (compare_password(input, reference))` statement, perform the comparison twice and verify that both results agree, and that a canary variable remains unmodified throughout execution. Time the comparison function and verify that elapsed cycles match the expected count for a full string traversal.

Verify secure boot bypass via clock glitching. Many microcontrollers verify firmware signatures during boot by computing a cryptographic hash or RSA signature over the application image and comparing it against a reference stored in protected memory. If a glitch corrupts the comparison result or causes the verification function to return prematurely, the device boots unsigned code. Connect the glitch controller to the target's external clock oscillator enable pin or use electromagnetic injection near the processor package. Trigger the glitch precisely when the signature verification function executes, identified by setting a hardware breakpoint in GDB at the verification function's entry point and logging the cycle count.

Load a modified firmware image with an invalid signature into flash using flashrom. Power-cycle the target while executing the glitch sweep. Upon successful bypass, the device boots the unsigned firmware, evidenced by altered debug messages over UART or unexpected peripheral activity. A successful attack demonstrates a critical secure boot implementation failure. Recommend countermeasures: use internal oscillators with frequency monitors that detect abnormal clock behavior, perform signature verification multiple times with independent cryptographic libraries, and implement rollback protection via monotonic counters stored in one-time-programmable (OTP) memory.

Electromagnetic fault injection (EMFI) targets localized regions of the processor die by inducing transient currents in on-chip interconnects. Construct an EMFI probe from a hand-wound coil of 0.1 mm magnet wire (ten turns, 2 mm diameter) soldered to a coaxial cable. Drive the coil with a high-voltage pulse generator (300-500 V, sub-microsecond rise time) triggered by the glitch controller. Position the probe above the processor package using a micromanipulator or 3D-printed holder. Systematically raster-scan the probe across the die surface while the target executes the security-critical function. When the probe is positioned over the ALU or instruction fetch unit, the electromagnetic pulse induces sufficient current to flip bits in transit, causing computational errors. Map successful fault locations to die floorplan diagrams obtained from patent filings or academic decapsulation studies.

---

## Hardware Security Checklist & Diagnostic Cheat Sheet

This checklist and command reference provide a systematic framework for hardware penetration testing and security verification. Use this as a pre-deployment audit tool for embedded devices and IoT systems.

**Physical Interface Enumeration:**
- Locate and document all exposed test points, headers, and unpopulated footprints.
- Identify UART, JTAG, SWD, SPI, I²C, and SPI interfaces via visual inspection and continuity testing.
- Measure voltage levels on suspected signal lines using a multimeter (logic high ~3.3 V or ~1.8 V).
- Trace pinouts from microcontroller datasheets to PCB pads using schematic reverse engineering if documentation is unavailable.

**UART Reconnaissance Commands:**
```bash
# Scan for logic analyzer and capture 10 seconds of UART traffic
sigrok-cli --scan
sigrok-cli --driver fx2lafw --config samplerate=1M --channels 0=TX,1=RX --time 10s -o uart.sr

# Establish interactive terminal at 115200 baud
minicom -D /dev/ttyUSB0 -b 115200

# Test common baud rates systematically
for baud in 9600 19200 38400 57600 115200 230400; do
  echo "Testing $baud"; screen /dev/ttyUSB0 $baud; done
```

**JTAG/SWD Debug Access Commands:**
```bash
# Launch OpenOCD for STM32F4 via FTDI adapter
openocd -f interface/ftdi/um232h.cfg -f target/stm32f4x.cfg

# Connect via Telnet and halt processor
telnet localhost 4444
> reset halt
> mdw 0x08000000 64    # dump 64 words from flash base
> arm disassemble 0x08000000 32

# Connect GDB and extract firmware
gdb-multiarch
(gdb) target extended-remote localhost:3333
(gdb) monitor reset halt
(gdb) dump binary memory flash.bin 0x08000000 0x08100000
```

**SPI Flash Extraction Commands:**
```bash
# Probe SPI flash via FT2232H
flashrom -p ft2232_spi:type=232H,port=A

# Read entire flash to file
flashrom -p ft2232_spi:type=232H,port=A --read firmware.bin

# Verify dump integrity
sha256sum firmware.bin

# Write modified firmware (verify first!)
flashrom -p ft2232_spi:type=232H,port=A --verify firmware_mod.bin
flashrom -p ft2232_spi:type=232H,port=A --write firmware_mod.bin
```

**Firmware Analysis Commands:**
```bash
# Identify embedded structures and filesystems
binwalk firmware.bin

# Extract all detected components
binwalk --extract firmware.bin

# Perform entropy analysis to detect encryption
binwalk --entropy firmware.bin

# Search for hardcoded secrets
grep -r "password\|api_key\|secret\|token" _firmware.bin.extracted/

# Disassemble ARM binary
arm-none-eabi-objdump -D -m arm -b binary firmware.bin > disasm.txt
```

**Register and Memory Protection Inspection:**
```bash
# Read MPU configuration (ARM Cortex-M)
(gdb) monitor mdw 0xE000ED90 8

# Read flash option bytes (STM32)
> stm32f4x options_read

# Check secure boot fuses and read protection
> mdw 0x1FFFC000 4    # STM32 option bytes address (varies by series)
```

**Glitch Attack Setup and Verification:**
- Construct voltage glitch circuit with MOSFET in series with VCC.
- Trigger glitch pulse via GPIO synchronized to target instruction sequence.
- Monitor VCC rail with oscilloscope (100 MHz bandwidth minimum, 1 GS/s sample rate).
- Log successful glitch parameters: delay (ns), pulse width (ns), voltage drop magnitude.
- Verify repeatability over at least ten trials; success rate above 80% indicates exploitable vulnerability.

**Electromagnetic Fault Injection:**
- Wind 10-turn coil (0.1 mm magnet wire, 2 mm diameter) for EMFI probe.
- Drive coil with 300-500 V pulse generator (sub-microsecond rise time).
- Raster-scan probe across processor die surface while executing security function.
- Map successful fault coordinates to processor floorplan.

**Countermeasure Verification:**
- Confirm voltage supervisory IC presence and threshold settings.
- Verify secure boot signature validation executes twice with inverted logic.
- Check for monotonic counter rollback protection in OTP memory.
- Measure authentication function execution time for timing consistency.
- Test glitch resistance by attempting documented glitch parameters and verifying detection or reset.

**Documentation Standards:**
- Record all findings with timestamps, device serial numbers, and firmware versions.
- Photograph PCB with annotated pinouts and probe connection points.
- Archive original firmware dumps with checksums before any modification.
- Document successful exploit parameters and countermeasure recommendations in structured report format.

This operational verification framework provides the foundational skill set for hardware-level security assessment. Mastery of these techniques enables the practitioner to identify and exploit physical attack surfaces in embedded systems, validate security architectures against fault injection threats, and recommend hardware and software countermeasures grounded in empirical testing. Every extracted firmware image, captured signal trace, and successful glitch attack deepens understanding of the adversarial model and informs the design of resilient, attack-resistant systems.
