# Operational Verification Labs: Reverse Engineering

## Objective & Lab Bench Setup

Reverse engineering embedded systems and firmware requires direct physical interaction with target hardware through signal capture, memory extraction, and runtime manipulation. This laboratory guide establishes a complete hardware analysis workstation centered on open-source diagnostic tools that operate at the electrical signal layer, protocol decoder layer, and binary analysis layer. The practitioner will build proficiency in translating voltage transitions on physical pins into decoded bus transactions, extracting firmware images from non-volatile storage, and injecting faults to trigger exploitable error conditions.

The lab bench consists of three primary instrument categories. First, signal acquisition hardware captures digital waveforms from target device pins. A USB-based logic analyzer with eight or sixteen channels provides sufficient bandwidth for most embedded bus protocols, sampling at rates between 24 MHz and 100 MHz depending on model. The Saleae Logic series, DSLogic clones, or sigrok-compatible analyzers serve as practical choices. Second, interface adapters bridge the workstation to target debug and communication ports. A multi-protocol USB-UART adapter handles asynchronous serial consoles, while a JTAG/SWD probe based on FTDI FT2232H or STM32-based designs enables boundary scan and CPU debug access. Third, memory extraction tools interact directly with non-volatile storage. A dedicated SPI/I²C flasher such as a CH341A programmer or an FTDI-based flashrom-compatible adapter allows direct reading and writing of flash chips after physical desoldering or in-circuit via test points.

Software infrastructure mirrors the hardware stack. The sigrok project provides the core signal acquisition and protocol decoding framework through `sigrok-cli` and the graphical PulseView frontend. Protocol decoders for SPI, I²C, UART, JTAG, and dozens of other standards translate captured waveforms into human-readable transactions without requiring manual bit-level analysis. OpenOCD acts as the universal adapter between GDB and hardware debug interfaces, supporting ARM Cortex-M/A, RISC-V, MIPS, and legacy architectures through configurable target scripts. Flashrom handles non-volatile memory operations across hundreds of chip models, automatically detecting geometry and selecting appropriate erase algorithms. Binwalk performs firmware image analysis by identifying embedded file systems, compression headers, cryptographic constants, and executable code sections through entropy analysis and signature matching. Radare2 provides the disassembly and binary analysis foundation, supporting dozens of architectures with integrated debugger, emulator, and scripting capabilities.

Install the complete toolchain on a Debian-based workstation with the following sequence. Update package indices and install core utilities: `sudo apt-get update && sudo apt-get install -y build-essential git cmake pkg-config libusb-1.0-0-dev libftdi1-dev libhidapi-dev`. Install sigrok components for signal capture: `sudo apt-get install -y sigrok-cli pulseview`. Deploy OpenOCD for debug interface control: `sudo apt-get install -y openocd`. Add flashrom for memory operations: `sudo apt-get install -y flashrom`. Install firmware analysis tools: `sudo apt-get install -y binwalk radare2 python3-binwalk`. Deploy cross-architecture debugging support: `sudo apt-get install -y gdb-multiarch`. Finally, install terminal emulators for serial console interaction: `sudo apt-get install -y minicom screen picocom`.

Configure USB device permissions to allow non-root access to hardware interfaces. Create a udev rules file at `/etc/udev/rules.d/60-hardware-tools.rules` containing the following entries. For FTDI-based devices: `SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", MODE="0666", GROUP="plugdev"`. For Saleae Logic analyzers: `SUBSYSTEM=="usb", ATTRS{idVendor}=="0925", MODE="0666", GROUP="plugdev"`. For CH341A programmers: `SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5512", MODE="0666", GROUP="plugdev"`. For STLink debug probes: `SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3748", MODE="0666", GROUP="plugdev"`. Reload udev rules without reboot: `sudo udevadm control --reload-rules && sudo udevadm trigger`. Add the current user to the plugdev group: `sudo usermod -a -G plugdev $USER`. Log out and back in to activate group membership.

Physical workspace organization directly impacts analysis efficiency. Mount the logic analyzer near the workstation for rapid connection and disconnection during iterative probing. Keep a set of quality test clips, IC hooks, and jumper wires organized by length and color. Use a helping-hands tool or PCB vise to stabilize target boards during probing. Maintain a dedicated grounding point connected to workstation earth ground, and always connect logic analyzer ground channels to target device ground before probing signal lines to prevent floating voltage references that corrupt captures. Store adapter boards and programmers in labeled anti-static bags when not in use, and maintain a log of pinout mappings for frequently analyzed target devices to avoid redundant continuity testing during subsequent sessions.

The exercises that follow progress from passive signal observation through active memory extraction to invasive fault injection. Each builds upon techniques established in prior sections, culminating in a complete hardware attack surface assessment workflow applicable to IoT devices, industrial controllers, automotive ECUs, and consumer electronics. Success requires patience, systematic methodology, and willingness to iteratively refine probe placement and capture parameters until clean signal acquisition yields actionable intelligence about target device internal state and behavior.

## Exercise 1: Live Hardware Probing & Signal Capture

Begin with passive reconnaissance of an unknown embedded system by identifying active communication buses and capturing their traffic without modifying target behavior. This exercise uses a commodity IoT device such as a smart plug, camera, or thermostat as the target. The objective is to locate serial console or debug ports, capture boot messages, and decode any runtime protocol traffic visible on external pins.

Disassemble the target device carefully, photographing each step to enable reassembly. Examine the main PCB under magnification, identifying the primary microcontroller or system-on-chip by reading package markings. Search online datasheets for the identified chip to determine its architecture, typical pinouts, and supported debug interfaces. Look for unpopulated header footprints, test points, or component pads near the microcontroller that suggest UART, JTAG, or SWD connections. Common indicators include four-pin headers for UART (TX, RX, GND, VCC), ten-pin or twenty-pin headers for JTAG, or four-pin headers for ARM SWD (SWDIO, SWCLK, GND, VCC).

Connect the logic analyzer ground lead to a confirmed ground point on the target PCB, typically identified by continuity testing against the barrel jack ground, USB shield, or metal mounting holes. If uncertain, use a multimeter in continuity mode to verify that multiple points share common ground before proceeding. Attach logic analyzer probe channels to suspected communication pins using IC test hooks that grip component leads or through-hole pads without soldering. Begin with the assumption that a UART console exists for debugging during development, as manufacturers frequently leave these accessible even in production units.

Configure the logic analyzer for an initial wideband capture to detect active signaling. Launch `sigrok-cli` in continuous sampling mode with a moderate sample rate: `sigrok-cli --driver fx2lafw --config samplerate=4M --channels 0-7 --continuous --output-format bits`. Power on the target device while observing the terminal output. Look for channels that transition from idle high or low states into bursts of activity during boot. UART TX lines typically idle high and show character transmission as brief low pulses followed by data bits. Clock signals appear as regular square waves, while chip select or enable lines toggle during transaction windows.

Once activity is detected on one or more channels, terminate the continuous capture and configure a triggered single-shot acquisition. For UART detection, trigger on a falling edge that likely represents the start bit of the first boot message character. Execute: `sigrok-cli --driver fx2lafw --config samplerate=8M --channels 0=RX --triggers 0=f --samples 1M --output-file boot_capture.sr`. This captures one million samples starting from the falling edge on channel 0. Import the resulting `.sr` file into PulseView for protocol analysis: `pulseview boot_capture.sr`.

Within PulseView, add a UART protocol decoder by clicking the protocol decoder menu and selecting UART from the list. Configure decoder parameters by double-clicking the decoder instance. Set the RX channel to match the captured signal, typically channel 0. Configure baud rate detection by trying common values: 115200, 57600, 38400, 9600. Start with 115200 as it dominates modern embedded systems. Set data bits to 8, parity to none, and stop bits to 1 for standard asynchronous serial configuration. If decoded output shows garbage characters, systematically test other baud rates until readable ASCII text appears. Boot messages often contain manufacturer names, U-Boot or bootloader banners, kernel version strings, and filesystem mount operations.

Record the identified baud rate and pin location. Connect a USB-UART adapter to the target device, matching TX on the target to RX on the adapter, RX on target to TX on adapter, and ground to ground. Never connect the adapter's VCC line to the target unless the target requires external power through this pin, as voltage mismatches between 3.3V and 5V systems can damage microcontroller I/O pins. Launch a terminal emulator: `minicom -D /dev/ttyUSB0 -b 115200`. Configure minicom by pressing Ctrl+A, then Z for the menu, then O for options. Navigate to "Serial port setup" and verify the baud rate matches the discovered value, hardware flow control is disabled, and software flow control is disabled. Save the configuration as default.

Power cycle the target device while observing minicom output. The boot sequence should now appear in real-time, providing insight into the boot process, loaded kernel version, mounted filesystems, and any initialization errors. Many devices drop into an interactive shell after boot if no password is set, or prompt for login credentials. Common default credentials include `root:root`, `admin:admin`, or device-specific combinations found in manufacturer documentation or community reverse engineering efforts. If a shell is obtained, explore the filesystem structure, examine running processes with `ps`, check network configuration with `ifconfig` or `ip addr`, and search for interesting configuration files in `/etc`, credential stores in `/root` or `/home`, and custom binaries in `/usr/bin` or `/opt`.

Extend the analysis to SPI bus traffic if the device uses external flash storage for firmware. SPI typically presents as four signals: MISO (Master In Slave Out), MOSI (Master Out Slave In), SCK (Serial Clock), and CS (Chip Select, active low). Identify the flash chip by reading its package markings and consulting datasheets to determine its pinout. Common SPI flash chips include Winbond W25Q series, Macronix MX25L series, and GigaDevice GD25Q series in 8-pin SOIC or WSON packages.

Attach logic analyzer probes to the four SPI pins, ensuring ground continuity. Configure a capture triggered on chip select falling edge: `sigrok-cli --driver fx2lafw --config samplerate=24M --channels 0=CS,1=SCK,2=MOSI,3=MISO --triggers 0=f --samples 10M --output-file spi_capture.sr`. Power on the target to capture the boot-time flash read operations. Import the capture into PulseView and add an SPI protocol decoder. Configure the decoder with CS on channel 0, CLK on channel 1, MOSI on channel 2, and MISO on channel 3. Set CS polarity to active-low and clock polarity/phase according to the flash chip datasheet, typically CPOL=0, CPHA=0 for mode 0.

Examine decoded SPI transactions for read commands. Standard SPI flash read commands include `0x03` for low-speed read, `0x0B` for fast read, and `0x3B` or `0x6B` for dual/quad reads. Following the command byte, the master transmits a three-byte address, then clocks out data bytes from the flash. The address space layout reveals firmware organization, with bootloaders typically residing at address 0x000000, followed by kernel images, root filesystems, and configuration blocks. Record observed address ranges and transaction patterns for correlation with subsequent memory dump analysis.

If JTAG pins are identified, configure OpenOCD for boundary scan interrogation. Create an OpenOCD configuration file `target.cfg` specifying the interface adapter and target chip. For an FTDI-based adapter: `interface ftdi; ftdi_vid_pid 0x0403 0x6014; ftdi_layout_init 0x0008 0x000b; ftdi_layout_signal nTRST -data 0x0100; ftdi_layout_signal nSRST -data 0x0200; adapter_khz 1000`. For an ARM Cortex-M target: `source [find target/stm32f1x.cfg]`. Launch OpenOCD: `openocd -f target.cfg`. If successful, OpenOCD reports TAP detection and enters a command server mode listening on TCP port 4444 for telnet control and port 3333 for GDB connections.

Connect to the OpenOCD telnet interface: `telnet localhost 4444`. Issue the `scan_chain` command to enumerate detected TAPs. Record the IDCODE values returned, which uniquely identify each device in the JTAG chain. Use the `dap info` command on ARM targets to display debug access port configuration and available memory regions. Halt the target CPU with `halt`, then read the program counter to determine current execution location: `reg pc`. Examine memory at arbitrary addresses: `mdw 0x08000000 64` reads 64 words from flash base address. Dump the entire flash to a file: `dump_image firmware.bin 0x08000000 0x10000` extracts 64KB starting from address zero.

This passive reconnaissance phase establishes a comprehensive map of active communication channels, debug interfaces, and memory topology without modifying target firmware or behavior. The captured boot messages, protocol transactions, and memory contents provide the foundation for subsequent deep analysis and active exploitation exercises.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

Transition from passive observation to active interrogation by directly reading non-volatile memory, inspecting CPU registers during runtime, and reconstructing firmware images from fragmented dumps. This exercise focuses on three scenarios: extracting firmware via SPI flash programmer, performing live memory inspection through JTAG debug, and analyzing recovered images to identify exploitable vulnerabilities.

Begin with physical firmware extraction from an SPI flash chip. If in-circuit access is feasible through test points or exposed pins, attempt in-circuit programming without desoldering. Connect an FTDI FT2232H-based flashrom adapter or CH341A programmer to the target flash chip, matching MISO, MOSI, SCK, CS, and ground pins according to the chip datasheet. Verify connections with a multimeter in continuity mode before applying power. Ensure the target device is completely powered off and disconnected from external power sources to prevent bus contention between the microcontroller and programmer.

Enumerate detected flash chips: `flashrom -p ft2232_spi:type=232H`. Flashrom interrogates the chip using standard JEDEC Read ID commands and matches the returned manufacturer and device IDs against its internal database. Typical output resembles: `Found Winbond flash chip "W25Q128.V" (16384 kB, SPI) on ft2232_spi`. If no chip is detected, verify wiring and ensure the programmer supplies appropriate voltage levels. Some flash chips operate at 1.8V rather than 3.3V, requiring voltage translation or a compatible programmer.

Read the entire flash contents to a binary file: `flashrom -p ft2232_spi:type=232H --read firmware_dump.bin`. This operation typically completes in one to three minutes for 16MB chips at standard SPI clock rates. Flashrom automatically selects optimal read commands and validates the transfer by computing checksums. Upon completion, verify the dump integrity by reading again and comparing: `flashrom -p ft2232_spi:type=232H --read firmware_verify.bin && sha256sum firmware_dump.bin firmware_verify.bin`. Identical hashes confirm successful extraction without read errors.

If in-circuit extraction fails due to bus contention or pull-up/pull-down resistors that prevent proper chip select control, physically desolder the flash chip using hot air rework or a desoldering iron. Exercise caution with thermal management, as excessive heat damages the chip or adjacent components. Once removed, mount the chip in a SOIC test clip or universal programmer socket. Repeat the flashrom read operation with the isolated chip, which eliminates interference from the target circuit.

Analyze the extracted firmware image with binwalk to identify embedded components: `binwalk firmware_dump.bin`. Binwalk scans the binary for known file signatures, compression headers, filesystem magic numbers, and cryptographic constants. Typical output identifies bootloader regions, compressed kernel images, SquashFS or JFFS2 root filesystems, and padding sections. Example output: `0x0 U-Boot bootloader; 0x80000 LZMA compressed data; 0x200000 Squashfs filesystem, little endian, version 4.0`. Record these offsets for targeted extraction.

Extract the identified filesystem: `binwalk --extract firmware_dump.bin`. Binwalk creates a directory named `_firmware_dump.bin.extracted` containing carved components. Navigate into this directory and locate the filesystem image, typically a file with `.squashfs` or `.jffs2` extension. Mount the filesystem for inspection: `sudo mount -t squashfs -o loop 200000.squashfs /mnt/firmware`. If mounting fails due to compression or endianness, use `unsquashfs 200000.squashfs` to extract contents into a directory named `squashfs-root`.

Explore the extracted filesystem to identify attack surfaces. Search for hardcoded credentials in configuration files: `grep -r "password\|passwd\|pwd" /mnt/firmware/etc`. Examine network service configurations: `cat /mnt/firmware/etc/inetd.conf`. Locate custom binaries provided by the manufacturer: `find /mnt/firmware -type f -executable`. Copy interesting binaries to the workstation for detailed analysis: `cp /mnt/firmware/usr/bin/custom_daemon ~/analysis/`.

Perform static analysis on extracted binaries with radare2. Load the binary: `r2 custom_daemon`. Analyze all functions and symbols: `aaa`. This command performs recursive analysis, identifying function boundaries, cross-references, and basic blocks. List all detected functions: `afl`. Navigate to the main function: `s main` seeks to the main symbol. Disassemble the current function: `pdf`. Radare2 displays assembly instructions with annotations indicating function calls, memory accesses, and control flow.

Search for dangerous function calls that indicate potential vulnerabilities. Locate `strcpy` calls that may lead to buffer overflows: `/c strcpy`. Radare2 highlights all cross-references to `strcpy` within the binary. Examine each call site to determine if the source buffer length is validated before copying. Similarly, search for `system`, `popen`, or `exec` family functions that may enable command injection if attacker-controlled data reaches their arguments. Use the cross-reference view to trace data flow from external inputs such as network sockets or command-line arguments to these dangerous sinks.

Enable radare2's built-in emulation engine to test hypothetical inputs: `aei; aeim`. Initialize the emulation environment and memory map. Set hypothetical register values representing attacker-controlled inputs: `aer arg0=0x41414141`. Step through instructions: `aes` executes a single step. Continue execution until a function call: `aec`. This dynamic analysis within the emulator reveals control flow under specific input conditions without running the binary on live hardware.

Transition to live runtime inspection via JTAG debug access. Configure OpenOCD as in Exercise 1, then launch GDB with multiarch support: `gdb-multiarch`. Connect to the OpenOCD GDB server: `target extended-remote localhost:3333`. Load symbol information if available: `file custom_daemon`. If symbols are stripped, analysis proceeds with raw memory addresses and disassembly.

Halt the target CPU: `monitor halt`. Inspect the current program counter: `info registers pc`. Disassemble at the current location: `x/20i $pc`. Set a hardware breakpoint on a function of interest identified during static analysis: `hbreak *0x08001234`. Resume execution: `continue`. When the breakpoint triggers, examine function arguments in registers according to the calling convention. For ARM Thumb, arguments reside in `r0` through `r3`: `info registers r0 r1 r2 r3`. Dump memory pointed to by these registers to inspect buffer contents: `x/64xb $r0`.

Single-step through the function to observe register and memory modifications: `stepi`. After each instruction, re-examine registers and key memory locations to understand the operation's effect. Watch for stack pointer decrements indicating local variable allocation, memory writes that may overflow buffers, and function calls that transfer control to exploitable library routines.

Dump the entire RAM contents for offline analysis: `dump binary memory ram_dump.bin 0x20000000 0x20010000`. This captures 64KB of SRAM starting at the typical ARM Cortex-M base address. Analyze the RAM dump for interesting strings, function pointers, or cryptographic material: `strings ram_dump.bin | grep -i "key\|token\|secret"`. Cross-reference discovered strings with the firmware filesystem to locate configuration files or storage locations for sensitive data.

For targets without JTAG access, leverage the UART shell obtained in Exercise 1 to perform userspace memory inspection. If the shell runs as root, read `/proc/kcore` or `/dev/mem` to access physical memory. Use `dd` to extract specific regions: `dd if=/dev/mem bs=1 skip=$((0x08000000)) count=$((0x100000)) of=/tmp/flash_dump.bin`. Transfer the resulting file to the workstation via netcat or serial transfer protocols.

Compile and deploy custom kernel modules if the target allows unsigned module loading and provides kernel headers. Write a minimal module that exports arbitrary memory reads through a `/proc` interface. Cross-compile for the target architecture using a toolchain matching the kernel version discovered during boot message capture. Load the module via `insmod` and use `cat /proc/memdump` to stream memory contents. This technique bypasses userspace restrictions and provides raw physical memory access without requiring hardware debug interfaces.

Correlate findings from static analysis, live debugging, and memory dumps to construct a complete picture of the target's attack surface. Map identified vulnerabilities to exploitation scenarios, prioritizing issues with remote network reachability, lack of authentication, and insufficient input validation. Document exploitable conditions, including required network access, prerequisite authentication states, and necessary timing or race conditions. This comprehensive assessment forms the basis for the fault injection and exploit verification exercise.

## Exercise 3: Fault Simulation & Exploit Verification

Validate discovered vulnerabilities through controlled fault injection and runtime manipulation, demonstrating exploitability under realistic conditions. This exercise covers three techniques: voltage glitching to bypass boot security, timing manipulation to induce race conditions, and memory corruption to hijack control flow. Success requires precise hardware control and iterative parameter tuning to reliably trigger target-specific fault conditions.

Voltage glitching exploits the microcontroller's sensitivity to supply rail transients, causing instruction decode errors, register corruption, or security check bypasses. The target mechanism involves briefly dropping VCC below the minimum operating voltage, inducing unpredictable CPU behavior that may skip branch instructions, corrupt comparison results, or fault conditional execution logic. This technique proves particularly effective against bootloader security checks, JTAG lock fuses, and cryptographic verification routines where a single skipped instruction grants unauthorized access.

Construct a voltage glitching rig using a MOSFET-based power switching circuit controlled by the logic analyzer's output pins configured in pattern generator mode. Select a low on-resistance N-channel MOSFET such as IRLZ44N capable of handling the target's current draw. Connect the MOSFET drain to the target's VCC input, source to the power supply positive rail, and gate to a logic analyzer output channel through a 100-ohm series resistor. Place a Schottky diode across the target's VCC and ground to clamp negative voltage spikes during switching transitions. This configuration allows the logic analyzer to insert precise glitches by briefly pulling the MOSFET gate low, interrupting current flow for microseconds.

Identify the target instruction window during boot by analyzing UART console output timing. Note the delay between power-on and the appearance of a security prompt or locked-down banner. Use an oscilloscope to observe VCC while simultaneously capturing UART output, correlating message timestamps with supply voltage stability. The vulnerable window typically occurs during flash read operations that load and verify boot signatures, lasting tens to hundreds of microseconds.

Configure the logic analyzer in pattern generator mode to produce a single negative pulse after a programmable delay from power-on. Since most logic analyzers lack native pattern generation, use a microcontroller development board such as Arduino or STM32 Nucleo programmed to generate the glitch pulse. Write firmware that waits a configurable delay after reset, then drives a GPIO pin low for a precise duration before returning high: `delay_microseconds(boot_delay); digitalWrite(GLITCH_PIN, LOW); delay_nanoseconds(glitch_width); digitalWrite(GLITCH_PIN, HIGH);`. Connect the GPIO pin to the MOSFET gate, replacing the logic analyzer output.

Begin with conservative parameters: 100ms boot delay and 100ns glitch width. Power cycle the target while the glitch circuit is active, observing UART output for anomalous behavior. Successful glitches manifest as unexpected boot paths, missing security prompts, or dropped characters in console output indicating CPU instruction corruption. Systematically sweep the delay parameter in 1ms increments across the boot window, testing each configuration ten times to account for timing jitter and metastability effects.

When anomalous behavior appears, refine the delay in finer increments around the successful range. Narrow the delay to 100μs precision, then sweep glitch width from 50ns to 500ns in 10ns steps. Record all parameter combinations that produce security bypasses. The goal is identifying a parameter sweet spot with high reliability, typically achieving successful exploitation in 70-90% of attempts. Parameters outside this range either fail to induce faults or cause complete system crashes requiring power cycle recovery.

Once reliable parameters are established, automate the attack with a script that power-cycles the target, triggers the glitch at the optimal delay, monitors UART output for success indicators such as shell prompts, and logs results: `while true; do power_cycle_target; sleep 0.5; trigger_glitch; timeout 5 expect_shell_prompt && echo "Success" >> results.log || echo "Failure" >> results.log; done`. Run the automation for 100 iterations to measure success rate and identify any environmental factors affecting reliability.

Transition to timing-based race condition exploitation in userspace applications. Race conditions occur when multiple execution threads or processes access shared resources without proper synchronization, allowing attackers to manipulate state during the critical window between check and use operations. A common pattern involves file operations where an application checks file permissions or ownership, then performs privileged operations on that file without maintaining exclusive access control.

Identify race-vulnerable code patterns in binaries extracted during Exercise 2. Search for sequences where `access()` precedes `open()`, or where file metadata checks via `stat()` occur before `read()` or `write()`. Disassemble the vulnerable function with radare2 and measure the instruction count between check and use operations. Convert instruction count to approximate timing by multiplying by the target CPU's clock period, accounting for memory access latency and pipeline stalls.

Construct a race condition exploit that rapidly swaps the target file between check and use operations. Write a script that creates a legitimate file passing security checks, then continuously replaces it with a symlink to a privileged target during the vulnerable window: `while true; do ln -sf /etc/shadow /tmp/racefile; rm /tmp/racefile; touch /tmp/racefile; done`. Launch this script in the background while repeatedly triggering the vulnerable application: `for i in {1..1000}; do /usr/bin/vulnerable_app /tmp/racefile; done`. Monitor for successful exploitation where the application operates on the privileged file instead of the intended target.

Improve exploitation reliability by reducing latency between the check and use operations through CPU affinity pinning and priority elevation. Pin the exploit script to one CPU core: `taskset -c 0 ./race_exploit.sh`. Pin the target application to a different core to prevent scheduler interference: `taskset -c 1 /usr/bin/vulnerable_app`. Elevate the exploit script's priority: `nice -n -20 ./race_exploit.sh`. These optimizations reduce timing jitter and increase the probability that the symlink replacement occurs during the critical window.

Validate memory corruption vulnerabilities identified during static analysis through live exploitation. Select a buffer overflow candidate where user-controlled input reaches an unbounded string copy or format string operation. Craft an input payload that overflows the target buffer, overwriting return addresses or function pointers with attacker-controlled values. For stack-based overflows, the payload structure consists of padding bytes filling the buffer, a new return address pointing to shellcode or return-oriented programming gadgets, and optional NOP sled or payload data.

Determine the exact buffer size and offset to the saved return address through dynamic analysis with GDB. Connect to the target via OpenOCD as in Exercise 2, set a breakpoint at the vulnerable function's return instruction, and inspect the stack: `x/32wx $sp`. Note the address of the saved return address on the stack. Craft a pattern string using a tool like `pattern_create.rb` from Metasploit: `pattern_create.rb -l 200`. Send this pattern as input to the vulnerable function, observe the crash, and use `pattern_offset.rb` to calculate the exact offset: `pattern_offset.rb -q 0x41424344`. This reveals the number of padding bytes required before overwriting the return address.

Construct the final exploit payload. For a simple proof-of-concept that hijacks control flow without deploying complex shellcode, overwrite the return address to point to an existing function that demonstrates exploitation, such as a debug function or privileged operation exposed in the binary. Encode the target address in little-endian format matching the target architecture: `python3 -c "import struct; print('A' * 64 + struct.pack('<I', 0x08001234))" > payload.bin`. Deliver the payload via the vulnerable input vector, whether network socket, file upload, or command-line argument.

Observe the exploit's effect through UART console output or debugger control flow. Successful exploitation redirects execution to the attacker-specified address, evidenced by unexpected function calls, register modifications, or privilege escalations. If the target implements modern mitigations such as stack canaries or ASLR, adapt the exploit accordingly. Defeat stack canaries through information disclosure vulnerabilities that leak the canary value, then incorporate the leaked value into the payload to maintain canary integrity. Bypass ASLR by exploiting partial overwrites that modify only the least significant bytes of return addresses, leveraging the fact that randomization entropy often affects only the upper address bits.

For targets with non-executable stack protections, employ return-oriented programming by chaining short instruction sequences ending in return instructions, called gadgets, to construct arbitrary computation without injecting executable code. Extract gadget candidates from the target binary using radare2's ROP search: `/R pop {r0, pc}` locates gadgets that pop values from the stack into registers. Chain gadgets by placing their addresses on the stack in sequence, with intermediate stack values serving as gadget arguments. The resulting exploit payload consists entirely of return addresses and data, never executing injected bytes, thus bypassing NX protections.

Verify exploit robustness across multiple target instances and firmware versions. Test the exploit against devices running different firmware builds to identify version-specific offsets or mitigations. Document prerequisites for reliable exploitation, including required network access, prerequisite authentication state, and environmental conditions such as free memory or CPU load. Quantify success rates and develop fallback strategies for targets where initial exploitation attempts fail due to entropy or timing variability.

Compile findings into a comprehensive hardware security assessment report documenting each vulnerability, exploitation technique, required hardware access level, estimated attacker cost and skill requirements, and recommended mitigations. Prioritize issues by exploitability and impact, focusing on remotely exploitable vulnerabilities requiring no physical access, followed by local issues requiring UART or JTAG access, and finally physical attacks requiring device disassembly. This structured assessment provides manufacturers and security teams with actionable intelligence for hardening embedded systems against hardware-level attacks.

## Hardware Security Checklist & Diagnostic Cheat Sheet

This reference section consolidates critical commands, wiring diagrams, and troubleshooting procedures for rapid deployment during field assessments. Maintain a printed copy in the hardware toolkit for offline reference when encountering unfamiliar targets or connectivity issues.

### Signal Acquisition Quick Reference

**Logic Analyzer Connection Sequence:**
1. Identify target device ground via continuity testing against chassis, USB shield, or barrel jack negative terminal.
2. Connect logic analyzer ground clip to verified ground point before attaching any signal probes.
3. Attach signal probes to suspected communication pins using IC hooks or test clips, noting physical pin numbers.
4. Configure sample rate at minimum 4× the target bus frequency for clean edge capture (SPI at 10 MHz requires 40 MS/s).
5. Set trigger conditions matching expected bus idle states: falling edge for UART start bits, low level for SPI chip select.

**Common Bus Identification by Signaling Pattern:**
- UART: Single wire shows periodic bursts during boot, idle high (3.3V or 5V), individual bits approximately equal duration.
- SPI: Four wires, one shows regular clock transitions (SCK), one pulses low before transactions (CS), two carry data (MOSI/MISO).
- I²C: Two wires, one shows clock during transactions (SCL), one shows data with start/stop conditions (SDA), both idle high with pull-up resistors.
- JTAG: Four or five wires, TMS and TDI idle high, TCK shows clock during operations, TDO responds to scan chain interrogation.

**Sigrok-CLI Essential Commands:**

Scan for connected devices: `sigrok-cli --scan`

Continuous capture on eight channels: `sigrok-cli --driver fx2lafw --config samplerate=8M --channels 0-7 --continuous`

Triggered capture on falling edge: `sigrok-cli --driver fx2lafw --config samplerate=24M --channels 0=CS,1=CLK,2=MOSI,3=MISO --triggers 0=f --samples 10M --output-file capture.sr`

Live protocol decode for UART: `sigrok-cli --driver fx2lafw --config samplerate=1M --channels 0=RX --protocol-decoders uart:baudrate=115200 --continuous`

### UART Terminal Configuration

**Minicom setup for 115200 8N1:** `minicom -D /dev/ttyUSB0 -b 115200`

**Disable flow control in minicom:**
- Press Ctrl+A, then Z for menu
- Press O for configuration
- Navigate to "Serial port setup"
- Press F to disable hardware flow control
- Press G to disable software flow control
- Press Enter to save, then "Save setup as dfl" for persistence

**Alternative terminals:**

Screen (no configuration required): `screen /dev/ttyUSB0 115200`

Picocom (lightweight): `picocom -b 115200 /dev/ttyUSB0`

**Common UART baud rates to test:** 115200, 57600, 38400, 19200, 9600, 230400, 460800, 921600

### Flash Memory Extraction

**Flashrom chip detection:** `flashrom -p ft2232_spi:type=232H`

**Read entire flash to file:** `flashrom -p ft2232_spi:type=232H --read firmware.bin`

**Write flash from file (DESTRUCTIVE):** `flashrom -p ft2232_spi:type=232H --write firmware_modified.bin`

**Verify flash contents:** `flashrom -p ft2232_spi:type=232H --verify firmware.bin`

**For CH341A programmers, replace interface specification:** `flashrom -p ch341a_spi`

**Common flash chip pinouts (SOIC-8 package, looking at chip top with pin 1 marked):**
```
Pin 1: CS (Chip Select)
Pin 2: MISO (Master In Slave Out)
Pin 3: WP (Write Protect, connect to VCC)
Pin 4: GND
Pin 5: MOSI (Master Out Slave In)
Pin 6: SCK (Serial Clock)
Pin 7: HOLD (connect to VCC)
Pin 8: VCC (3.3V)
```

### OpenOCD Debug Access

**Basic FTDI interface configuration (save as ftdi.cfg):**
```
interface ftdi
ftdi_vid_pid 0x0403 0x6014
ftdi_layout_init 0x0008 0x000b
ftdi_layout_signal nTRST -data 0x0100
ftdi_layout_signal nSRST -data 0x0200
adapter_khz 1000
```

**Launch OpenOCD with ARM Cortex-M target:** `openocd -f ftdi.cfg -f target/stm32f1x.cfg`

**Connect via telnet:** `telnet localhost 4444`

**Essential OpenOCD telnet commands:**
- Halt CPU: `halt`
- Resume execution: `resume`
- Reset target: `reset halt`
- Read 64 words from address: `mdw 0x08000000 64`
- Write word to address: `mww 0x20000000 0x12345678`
- Dump memory region: `dump_image firmware.bin 0x08000000 0x10000`
- Load binary to flash: `load_image firmware.bin 0x08000000`
- Erase flash: `flash erase_sector 0 0 last`

**GDB connection sequence:**

Launch GDB: `gdb-multiarch`

Connect to OpenOCD: `target extended-remote localhost:3333`

Load symbols: `file binary_with_symbols`

Set breakpoint: `hbreak *0x08001234`

Continue execution: `continue`

### Binwalk Firmware Analysis

**Scan for embedded components:** `binwalk firmware.bin`

**Extract all identified components:** `binwalk --extract firmware.bin`

**Entropy analysis to locate compressed or encrypted sections:** `binwalk --entropy firmware.bin`

**Search for specific signature (e.g., private keys):** `binwalk --raw="\x2d\x2d\x2d\x2d\x2d\x42\x45\x47\x49\x4e" firmware.bin`

**Mount extracted SquashFS:** `sudo mount -t squashfs -o loop extracted.squashfs /mnt/firmware`

**Extract SquashFS without mounting:** `unsquashfs extracted.squashfs`

**Search extracted filesystem for credentials:** `grep -r "password\|passwd\|pwd\|secret\|token" squashfs-root/`

### Radare2 Binary Analysis

**Load binary:** `r2 binary_file`

**Analyze all functions:** `aaa`

**List functions:** `afl`

**Disassemble current function:** `pdf`

**Seek to address:** `s 0x08001234`

**Seek to function:** `s sym.main`

**Search for string:** `/ password`

**Search for function call:** `/c strcpy`

**Cross-references to current location:** `axt`

**Visual mode (interactive disassembly):** `VV`

**Decompile to pseudocode (if r2ghidra installed):** `pdg`

**Initialize emulation:** `aei; aeim`

**Set register value:** `aer r0=0x41414141`

**Execute single instruction:** `aes`

### Troubleshooting Common Issues

**Logic analyzer not detected:**
- Verify USB connection and try different port
- Check udev rules: `cat /etc/udev/rules.d/60-hardware-tools.rules`
- Reload udev: `sudo udevadm control --reload-rules && sudo udevadm trigger`
- Verify user group membership: `groups` (should include plugdev)

**UART shows garbled characters:**
- Verify baud rate matches target (try all common rates systematically)
- Check voltage levels with multimeter (3.3V vs 5V mismatch)
- Confirm correct TX/RX swap (target TX to adapter RX, target RX to adapter TX)
- Disable hardware and software flow control in terminal emulator

**SPI flash not detected by flashrom:**
- Verify wiring matches chip datasheet pinout
- Ensure target device is completely powered off
- Check for bus contention from pull-up/pull-down resistors
- Measure voltage at chip VCC pin (should be 3.3V or 1.8V stable)
- Try slower clock rates: `flashrom -p ft2232_spi:type=232H,spispeed=1M`

**OpenOCD cannot connect to target:**
- Verify JTAG/SWD pinout against microcontroller datasheet
- Check for security fuses or debug lock enabled in target firmware
- Try different adapter clock rates: `adapter_khz 100` (slower for noisy connections)
- Verify target has stable power supply and is not in reset state
- For SWD, ensure only SWDIO, SWCLK, and GND are connected (no JTAG pins)

**Binwalk extraction produces corrupted files:**
- Manually carve sections using dd: `dd if=firmware.bin bs=1 skip=$((0x80000)) count=$((0x100000)) of=kernel.bin`
- Check for custom compression or obfuscation in bootloader code
- Examine entropy graph to distinguish compressed sections from encrypted sections
- Use `--dd` option to specify exact carve offsets: `binwalk --dd="squashfs:squashfs" firmware.bin`

**GDB cannot access memory regions:**
- Verify OpenOCD memory map configuration matches target
- Use OpenOCD `mdw` commands via telnet instead of GDB for problematic regions
- Check for MPU (Memory Protection Unit) restrictions in target firmware
- Halt target before memory access: `monitor halt` from GDB

This checklist provides immediate reference for the most frequent operations and failure modes encountered during hardware reverse engineering. Combine these diagnostic procedures with systematic methodology, documenting each step and its outcome to build a reproducible workflow applicable across diverse embedded targets.
