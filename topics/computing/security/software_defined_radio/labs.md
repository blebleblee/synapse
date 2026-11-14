# Operational Verification Labs: Software Defined Radio

## Objective & Lab Bench Setup

Software Defined Radio systems represent a convergence of digital signal processing, embedded hardware control, and radio frequency engineering that creates a uniquely rich attack surface for hardware security researchers and penetration testers. Unlike traditional radio equipment where modulation schemes, filters, and frequency selection exist as fixed analog circuits, SDR platforms implement these functions in reconfigurable firmware and software stacks running on general-purpose processors, FPGAs, and specialized RF frontends. This architectural flexibility transforms radio communication from a black-box appliance into a transparent, programmable substrate where every modulation decision, every frequency hop, and every packet transmission becomes observable, recordable, and ultimately exploitable through direct hardware inspection and runtime analysis.

The operational verification exercises in this laboratory guide target real SDR hardware platforms commonly deployed in wireless infrastructure, IoT gateways, and embedded communication systems. You will work with actual RTL-SDR dongles, HackRF One transceivers, and USRP platforms to expose the hardware-software boundary where radio signal processing meets embedded Linux kernel drivers, USB control protocols, and firmware state machines. The methodology combines physical layer signal capture using logic analyzers and bus sniffers with software-layer introspection through kernel module instrumentation, memory dumping, and real-time register inspection. By the end of these exercises, you will have constructed a complete hardware security assessment workflow capable of identifying buffer overflows in USB control transfers, timing vulnerabilities in frequency synthesizer locking loops, and authentication bypasses in proprietary SDR control protocols.

Your laboratory bench requires both hardware instrumentation and a comprehensive diagnostic software suite. The physical infrastructure consists of a USB 2.0 or 3.0 logic analyzer capable of sampling at least 24 MS/s across eight channels, a USB-UART bridge adapter supporting 3.3V logic levels for serial console access, and optionally a JTAG debugger with ARM Cortex support for direct CPU register inspection on more advanced SDR platforms. The SDR devices themselves should include at minimum an RTL-SDR dongle based on the Realtek RTL2832U demodulator chip, which provides a low-cost entry point for USB protocol analysis and signal chain verification, and ideally a HackRF One or USRP B200 for full-duplex transceiver testing and firmware extraction exercises. All hardware should be connected through an isolated USB hub with per-port current monitoring to detect anomalous power consumption patterns that may indicate firmware crashes or thermal shutdowns during fault injection testing.

The software diagnostic environment runs on a standard x86-64 Linux workstation with kernel version 5.15 or newer to ensure compatibility with modern USB gadget drivers and eBPF tracing infrastructure. Install the core hardware analysis toolkit using your distribution's package manager, beginning with sigrok-cli for logic analyzer control and protocol decoding, OpenOCD for JTAG boundary scan and memory access, flashrom for SPI flash chip extraction, binwalk for firmware unpacking and filesystem analysis, and radare2 for disassembly and reverse engineering of extracted binary images. The complete installation sequence on Debian-based systems proceeds as follows:

```bash
apt-get update
apt-get install -y sigrok-cli pulseview openocd flashrom binwalk \
    radare2 gdb-multiarch minicom picocom screen \
    python3-numpy python3-scipy python3-matplotlib \
    gnuradio gr-osmosdr libusb-1.0-0-dev librtlsdr-dev \
    hackrf libhackrf-dev uhd-host python3-uhd \
    python3-usb python3-serial python3-construct
```

Verify the installation by confirming that sigrok-cli can enumerate connected logic analyzers, flashrom can detect supported SPI programmers, and OpenOCD includes configuration files for common ARM Cortex-M and Cortex-A cores. Check sigrok support with `sigrok-cli --scan`, which should enumerate any connected logic analyzer hardware and display supported protocol decoders including SPI, I2C, UART, USB, and custom wireless protocol parsers. Validate flashrom functionality with `flashrom --list-supported`, confirming that FT2232H-based SPI adapters appear in the supported programmer list. Finally, verify OpenOCD ARM support by inspecting `/usr/share/openocd/scripts/target/` for configuration files matching your SDR platform's processor architecture.

Establish a systematic workspace organization that separates raw hardware captures from analyzed data products and keeps extracted firmware images isolated from live system modifications. Create a project directory structure with subdirectories for logic analyzer traces, USB packet captures, firmware dumps, disassembled code, and analysis scripts. Within this workspace, maintain a detailed laboratory notebook documenting every hardware connection, every captured signal trace, and every observed anomaly with timestamps, environmental conditions, and reproduction procedures. This discipline proves essential when correlating intermittent hardware failures with specific signal conditions or when reconstructing exploitation sequences from fragmented trace data collected across multiple test sessions.

Configure your USB subsystem to grant non-root access to SDR devices and analysis tools by creating appropriate udev rules that assign connected hardware to a dedicated user group. Write a udev rules file at `/etc/udev/rules.d/99-sdr-security.rules` containing device matching patterns for RTL-SDR, HackRF, and USRP hardware along with mode and group assignments that enable unprivileged access while maintaining audit trail capabilities:

```
# RTL-SDR dongles using RTL2832U
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", GROUP="sdr", MODE="0660"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="sdr", MODE="0660"

# HackRF One transceiver
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6089", GROUP="sdr", MODE="0660"

# USRP B200/B210 devices
SUBSYSTEM=="usb", ATTRS{idVendor}=="2500", ATTRS{idProduct}=="0020", GROUP="sdr", MODE="0660"
SUBSYSTEM=="usb", ATTRS{idVendor}=="2500", ATTRS{idProduct}=="0021", GROUP="sdr", MODE="0660"

# Logic analyzers (Saleae, generic fx2lafw)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0925", ATTRS{idProduct}=="3881", GROUP="sdr", MODE="0660"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="608c", GROUP="sdr", MODE="0660"
```

After writing this rules file, reload the udev daemon with `udevadm control --reload-rules && udevadm trigger`, then add your user account to the sdr group using `usermod -a -G sdr $USER`. Log out and back in to activate the new group membership, then verify that you can access SDR devices without root privileges by running `rtl_test -t` for RTL-SDR dongles or `hackrf_info` for HackRF hardware. If device access fails, inspect kernel logs with `dmesg | tail -50` to identify permission errors or USB enumeration failures that may indicate hardware faults or missing kernel driver modules.

The laboratory exercises that follow progress from passive signal observation through active bus manipulation to full exploitation development, mirroring the reconnaissance-to-compromise workflow of professional hardware security assessments. Each exercise builds upon artifacts and insights from previous stages, culminating in a comprehensive threat model and exploitation framework specific to your target SDR platform. Approach each exercise methodically, documenting every observation and preserving all captured data for later correlation analysis. Hardware security research generates vast quantities of raw signal traces and binary dumps that only reveal their significance when examined in aggregate across multiple test conditions, so maintain rigorous data hygiene and version control throughout the assessment process.

## Exercise 1: Live Hardware Probing & Signal Capture

The first operational exercise establishes baseline signal chain observability by instrumenting the USB data path between your workstation and the SDR device, capturing both high-level USB packet semantics and low-level electrical signaling. This dual-layer visibility exposes timing relationships, protocol state machines, and unexpected device behaviors that higher-level software APIs deliberately abstract away. The exercise targets an RTL-SDR dongle as the specimen device, chosen for its ubiquity, simple USB control protocol, and well-documented vulnerability history including buffer overflows in vendor-supplied Windows drivers and timing attacks against the frequency synthesizer locking mechanism.

Begin by connecting your RTL-SDR dongle to the workstation through an instrumented USB hub that provides test points for D+ and D- differential signal probing. If your USB hub lacks exposed test points, carefully strip back the outer insulation of a USB cable to access the twisted-pair data lines while leaving ground and power intact. Alternatively, use a USB breakout board or extension cable with built-in header pins that bring out all four USB lines for logic analyzer connection. Once you have physical access to the USB data signals, connect logic analyzer probes to D+ and D-, ensuring that probe ground clips attach to the USB cable shield or workstation chassis ground to establish a common reference. Configure the logic analyzer for 24 MS/s sampling rate with a capture buffer depth of at least 16 megasamples, allocating two channels for the USB differential pair and reserving additional channels for future expansion to SPI or I2C instrumentation during firmware extraction exercises.

Launch the sigrok PulseView GUI with `pulseview &` to configure capture parameters and protocol decoders before initiating trace acquisition. In the device configuration dialog, select your logic analyzer hardware and verify that all probe assignments match your physical wiring, with channels 0 and 1 assigned to USB D+ and D- respectively. Set the sampling rate to 24 MHz and trigger mode to immediate capture, since USB enumeration begins the moment the device receives power and you need to capture the initial descriptor exchange that occurs before any higher-level software intervention. Add the USB 1.1/2.0 FS protocol decoder to the signal display by right-clicking in the decoder sidebar and selecting Protocols → USB → usb_signalling, then configure the decoder to use channels 0 and 1 as the D+ and D- inputs. The decoder will automatically detect USB packet boundaries, decode packet types, and extract endpoint addresses and transfer payloads from the captured differential signals.

With the logic analyzer armed and ready, hot-plug the RTL-SDR dongle into the instrumented USB port to capture the complete enumeration sequence from device attachment through driver binding. You should observe a characteristic burst of activity as the device transitions through powered, default, address, and configured states according to the USB 2.0 specification. The initial traffic consists of GET_DESCRIPTOR requests from the host querying device, configuration, and string descriptors that identify the RTL2832U chip and declare its supported endpoints and interface classes. Expand the decoded packets in PulseView to verify that the device descriptor reports a vendor ID of 0x0bda (Realtek) and product ID of 0x2832 or 0x2838 depending on dongle variant, with bcdUSB field indicating USB 2.0 compliance and bDeviceClass set to 0x00 for device-defined interfaces.

Export the captured trace for offline analysis by saving it in sigrok's native .sr format, which preserves both raw sample data and decoder annotations for later reprocessing. Save the current capture as `rtl_enum_baseline.sr` and create a detailed markdown note documenting the environmental conditions including USB port number, kernel version from `uname -r`, and loaded kernel modules from `lsmod | grep -E 'rtl|dvb|usb'`. This baseline capture serves as a known-good reference for detecting anomalous behavior during later fault injection and protocol fuzzing exercises where you deliberately violate timing constraints or inject malformed control transfers.

Transition from passive observation to active characterization by instrumenting the USB stack with kernel tracepoints that expose control transfer contents and timing information not visible in the electrical signaling layer. The Linux kernel USB subsystem provides a comprehensive tracing infrastructure through the usbmon facility, which intercepts all USB requests and responses at the host controller driver boundary. Enable usbmon for all USB buses by loading the kernel module with `modprobe usbmon`, then identify which bus number hosts your RTL-SDR device by examining `lsusb` output and noting the bus number in the device listing. The bus number appears before the device number in the format `Bus XXX Device YYY`, where XXX is the bus identifier you will monitor.

Capture USB traffic at the kernel level using the text-based usbmon interface exposed through debugfs. Mount debugfs if not already mounted with `mount -t debugfs none /sys/kernel/debug`, then initiate a capture session with `cat /sys/kernel/debug/usb/usbmon/1u > rtl_usbmon_baseline.txt` where `1u` represents bus 1 in the unified text format that includes setup packets, data payloads, and completion status codes. In a separate terminal, trigger SDR activity by running `rtl_test -s 2048000 -t 5` to configure the device for 2.048 MS/s sample rate and stream data for five seconds. This command exercises the control plane through frequency tuning and gain adjustment requests, then activates the data plane by initiating bulk transfers that stream I/Q samples from the RTL2832U to the host.

After the test completes, terminate the usbmon capture with Ctrl-C and inspect the resulting trace file to identify the control transfer sequences that configure the RTL2832U's registers and initialize the tuner chip. Search for SETUP packets directed to endpoint 0 using `grep -A 5 'S Co:' rtl_usbmon_baseline.txt` where the Co mnemonic indicates a control output (host-to-device) transfer. Each SETUP packet contains an 8-byte header encoding the bmRequestType, bRequest, wValue, wIndex, and wLength fields that specify the vendor-specific operation being performed. For RTL-SDR devices, common control requests include register writes to configure the demodulator, I2C transactions forwarded to the tuner chip, and EEPROM accesses that read device calibration data.

Parse the hex-encoded control transfer payloads to reconstruct the initialization sequence and identify potential injection points for attack payloads. A typical RTL-SDR initialization includes writing to demodulator register 0x0061 to enable software control mode, issuing I2C transactions on bus 1 to configure the R820T tuner chip's frequency synthesizer and gain stages, and reading calibration constants from EEPROM addresses 0x00 through 0x0f. Document each control transfer with its associated register address, payload contents, and apparent function, building a state machine diagram that maps software API calls like `rtlsdr_set_center_freq()` to their underlying USB protocol implementation. This mapping proves essential when constructing protocol-level exploits that must bypass higher-level validation logic by injecting malformed packets directly into the USB control pipe.

Extend the characterization to the data plane by analyzing bulk transfer patterns that stream I/Q samples from the device to host memory. Return to the logic analyzer capture and locate the IN token sequences on endpoint 0x81, which represents the bulk input endpoint used for sample streaming. Measure the inter-packet timing and verify that bulk transfers occur at regular intervals determined by the configured sample rate and USB packet size. For a 2.048 MS/s sample rate with 8-bit I/Q samples and 512-byte USB packets, you should observe bulk transfers approximately every 125 microseconds corresponding to each 256-sample packet duration. Deviations from this regular timing pattern indicate buffer underruns, USB bandwidth congestion, or device firmware errors that may expose denial-of-service vulnerabilities or timing side channels.

Quantify the USB bandwidth utilization by calculating theoretical and measured data rates from the captured timing parameters. Each I/Q sample pair consists of two 8-bit values for a total of 16 bits per complex sample, so a 2.048 MS/s sample rate generates 4.096 MB/s of raw sample data before considering USB protocol overhead. USB 2.0 high-speed bulk transfers pack data into 512-byte maximum packet size segments with approximately 512 bytes of per-transaction overhead including packet headers, handshaking, and inter-packet gaps, yielding an effective bandwidth efficiency around 92% for sustained bulk streaming. Measure the actual transfer rate by dividing the total captured sample count by the trace duration, then compare this measured rate against the theoretical maximum to identify headroom available for higher sample rates or detect bandwidth saturation that may trigger sample dropping and spectral artifacts.

Correlate the USB-layer observations with higher-level SDR application behavior by simultaneously capturing USB traffic and GNU Radio flowgraph execution traces. Install GNU Radio if not already present with `apt-get install gnuradio gr-osmosdr`, then create a simple FM receiver flowgraph that demonstrates tuning, gain control, and demodulation while you monitor the USB control transfers that implement each operation. Launch GNU Radio Companion with `gnuradio-companion` and construct a flowgraph containing an RTL-SDR source block connected through a low-pass filter and frequency demodulator to an audio sink. Configure the source block for 2.048 MS/s sample rate and tune to a local FM broadcast station around 100 MHz.

Before executing the flowgraph, initiate a new usbmon capture with `cat /sys/kernel/debug/usb/usbmon/1u > rtl_gnuradio_execution.txt`, then click Run in GNU Radio Companion to start sample streaming. Observe the audio output to confirm successful reception, then stop the flowgraph after 10 seconds and terminate the usbmon capture. Analyze the captured control transfers to identify the exact register programming sequences generated by the gr-osmosdr source block's tuning and gain adjustment methods. Search for repeated control transfers that occur during steady-state operation, which represent either polling loops checking device status or periodic recalibration sequences that may introduce timing vulnerabilities. Note any unexpected or redundant control transfers that suggest inefficient driver implementation or firmware quirks requiring workarounds in the host software.

Construct a USB protocol timing diagram that maps each high-level SDR operation to its constituent control transfers, data transfers, and inter-transfer timing constraints. Use the timestamps from both logic analyzer and usbmon captures to measure critical timing parameters including control transfer round-trip latency, bulk transfer scheduling jitter, and the delay between frequency tuning requests and frequency synthesizer lock indication. These timing measurements establish baseline performance metrics against which you will compare behavior during fault injection exercises, where injected delays or out-of-order transfers reveal race conditions and timing-dependent validation bypasses in device firmware.

Automate the USB traffic capture and analysis workflow by writing a Python script that leverages pyusb to programmatically enumerate devices, send control transfers, and capture responses with precise timing measurements. Install the required libraries with `pip3 install pyusb pyserial construct`, then create a script that replicates the initialization sequence observed in the usbmon traces using raw USB control transfer API calls. The following script demonstrates enumerating RTL-SDR devices and issuing a vendor-specific control request to read the device EEPROM:

```python
#!/usr/bin/env python3
import usb.core
import usb.util
import sys
import time

# RTL-SDR vendor/product IDs
RTL_VENDOR_ID = 0x0bda
RTL_PRODUCT_IDS = [0x2832, 0x2838]

# Vendor request codes (from librtlsdr)
EEPROM_READ_REQ = 0x02
EEPROM_WRITE_REQ = 0x03
DEMOD_READ_REG = 0x00
DEMOD_WRITE_REG = 0x01

def find_rtl_device():
    """Locate RTL-SDR device by vendor/product ID."""
    for product_id in RTL_PRODUCT_IDS:
        dev = usb.core.find(idVendor=RTL_VENDOR_ID, idProduct=product_id)
        if dev is not None:
            return dev
    return None

def read_eeprom(dev, offset, length):
    """Read data from RTL-SDR EEPROM at specified offset."""
    # Control transfer: IN, vendor, device
    # bRequest=EEPROM_READ_REQ, wValue=0, wIndex=offset, wLength=length
    bmRequestType = usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
    data = dev.ctrl_transfer(bmRequestType, EEPROM_READ_REQ, 0, offset, length, timeout=1000)
    return bytes(data)

def read_demod_register(dev, page, address):
    """Read RTL2832U demodulator register."""
    block = page & 0xff
    reg = (address >> 8) & 0xff
    addr = address & 0xff
    
    bmRequestType = usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
    data = dev.ctrl_transfer(bmRequestType, DEMOD_READ_REG, addr, (block << 8) | reg, 1, timeout=1000)
    return data[0]

def write_demod_register(dev, page, address, value):
    """Write RTL2832U demodulator register."""
    block = page & 0xff
    reg = (address >> 8) & 0xff
    addr = address & 0xff
    
    bmRequestType = usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
    data = bytes([value])
    dev.ctrl_transfer(bmRequestType, DEMOD_WRITE_REG, addr, (block << 8) | reg, data, timeout=1000)

def main():
    print("[*] Searching for RTL-SDR device...")
    dev = find_rtl_device()
    
    if dev is None:
        print("[-] No RTL-SDR device found")
        sys.exit(1)
    
    print(f"[+] Found device: {dev.product} (Bus {dev.bus} Device {dev.address})")
    
    # Detach kernel driver if active
    if dev.is_kernel_driver_active(0):
        print("[*] Detaching kernel driver...")
        dev.detach_kernel_driver(0)
    
    # Set configuration
    dev.set_configuration()
    
    # Read EEPROM header (first 16 bytes)
    print("\n[*] Reading EEPROM header...")
    eeprom_header = read_eeprom(dev, 0x0000, 16)
    print(f"[+] EEPROM data: {eeprom_header.hex()}")
    
    # Parse EEPROM signature
    if eeprom_header[0:2] == b'\x28\x32':
        print("[+] Valid RTL2832U EEPROM signature detected")
    else:
        print("[!] Invalid EEPROM signature")
    
    # Read vendor/product strings offset
    vendor_str_offset = eeprom_header[9]
    product_str_offset = eeprom_header[10]
    print(f"[*] Vendor string at offset: 0x{vendor_str_offset:02x}")
    print(f"[*] Product string at offset: 0x{product_str_offset:02x}")
    
    # Read demodulator USB control register
    print("\n[*] Reading demodulator USB control register (0x2000)...")
    usb_ctrl = read_demod_register(dev, 2, 0x0000)
    print(f"[+] USB_CTRL register value: 0x{usb_ctrl:02x}")
    
    # Write to USB control register to enable software control
    print("[*] Enabling software control mode...")
    write_demod_register(dev, 2, 0x0000, 0x08)
    
    # Verify write
    usb_ctrl_verify = read_demod_register(dev, 2, 0x0000)
    print(f"[+] USB_CTRL register after write: 0x{usb_ctrl_verify:02x}")
    
    if usb_ctrl_verify & 0x08:
        print("[+] Software control mode enabled successfully")
    else:
        print("[-] Failed to enable software control mode")
    
    # Timing measurement: control transfer latency
    print("\n[*] Measuring control transfer latency...")
    iterations = 100
    start_time = time.perf_counter()
    for _ in range(iterations):
        read_demod_register(dev, 2, 0x0000)
    end_time = time.perf_counter()
    
    avg_latency = (end_time - start_time) / iterations * 1000  # Convert to milliseconds
    print(f"[+] Average control transfer latency: {avg_latency:.3f} ms")
    
    # Reattach kernel driver
    usb.util.dispose_resources(dev)
    print("\n[*] Released device resources")

if __name__ == "__main__":
    main()
```

Execute this script with `python3 rtl_usb_probe.py` and verify that it successfully enumerates the device, reads EEPROM contents, and measures control transfer latency. The measured latency typically ranges from 0.5 to 2 milliseconds depending on USB controller implementation and system load, establishing a baseline against which you can detect anomalous delays during fault injection testing. Extend this script to automate register sweeps, EEPROM dumping, and timing analysis across multiple devices, building a comprehensive database of normal behavior patterns that anomaly detection algorithms can reference during security assessment workflows.

Complete this exercise by archiving all captured traces, timing measurements, and analysis scripts into a versioned Git repository with detailed commit messages documenting the testing methodology and observed results. Tag this commit as `ex1-baseline` to mark it as the reference implementation for subsequent fault injection and exploitation exercises. The systematic capture and documentation discipline established in this exercise forms the foundation for repeatable, auditable hardware security research that withstands peer review and supports vulnerability disclosure processes with hardware vendors and CERT coordination centers.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

The second exercise transitions from USB protocol analysis to direct hardware inspection by accessing the SPI flash memory that stores RTL-SDR firmware and configuration data, then extracting and analyzing the firmware image to identify potential vulnerabilities in register access patterns, buffer handling, and cryptographic implementations. This exercise requires physical access to the PCB and use of an SPI programmer to read flash contents without relying on potentially compromised software layers. The methodology applies equally to other SDR platforms including HackRF One and USRP devices, which similarly store firmware in external SPI flash chips that implement standard JEDEC serial flash interfaces.

Begin by identifying the flash memory chip on your RTL-SDR dongle through visual PCB inspection and datasheet correlation. Power down the device and remove any RF shielding cans or heatsinks that obscure the PCB components. Locate the SPI flash chip, typically an 8-pin SOIC or DIP package marked with manufacturer logos such as Winbond (W25Q), Macronix (MX25L), or GigaDevice (GD25). Common capacities range from 1 to 8 megabytes, with part numbers like W25Q80 indicating an 8-megabit (1 megabyte) device. Photograph the chip marking and decode the part number using manufacturer datasheets to confirm pinout, voltage levels, and supported SPI clock frequencies.

The standard SPI flash pinout assigns pin 1 as chip select (CS#), pin 2 as serial data output (SO/MISO), pin 3 as write protect (WP#), pin 4 as ground (GND), pin 5 as serial data input (SI/MOSI), pin 6 as serial clock (SCK), pin 7 as hold (HOLD#), and pin 8 as supply voltage (VCC). For in-circuit programming, you must connect an SPI programmer to these pins while ensuring that the host microcontroller's SPI interface remains isolated to prevent bus contention. The most reliable approach uses a Pomona 5250 SOIC test clip that clamps onto the chip package and provides flying lead connections to your programmer, eliminating the need for desoldering or PCB modifications that risk permanent damage to the target device.

Connect an FT2232H-based SPI programmer to your workstation via USB, then wire the programmer's SPI interface to the flash chip test clip following the standard color-coded pinout. The FT2232H MPSSE mode provides a high-speed SPI master interface capable of operating at clock rates up to 30 MHz, sufficient for rapid flash extraction while remaining within the timing specifications of most serial flash devices. Wire the FT2232H's ADBUS0 to chip select, ADBUS1 to serial clock, ADBUS2 to MOSI, and ADBUS3 to MISO, ensuring that all signals share a common ground reference with the target device. Do not connect the programmer's 3.3V output to the flash VCC pin if the target board remains powered from USB, as this creates a power conflict that may damage components. Instead, verify that the flash chip receives stable 3.3V from the onboard regulator while you perform in-circuit programming.

Test the programming setup by running flashrom in probe mode to detect the flash chip without performing any write operations. Execute `flashrom -p ft2232_spi:type=2232H,port=A,divisor=4` where the divisor parameter sets the SPI clock frequency to approximately 6 MHz by dividing the FT2232H's 60 MHz base clock. Flashrom will interrogate the chip using the standard JEDEC Read ID command (0x9F) and report the manufacturer ID, device ID, and capacity. Verify that the detected chip matches the physical markings on the package, then record the full flashrom output including supported erase block sizes and protection status register contents. If flashrom fails to detect the chip, reduce the clock divisor to 8 or 16 to account for signal integrity issues caused by long probe wires or capacitive loading from the in-circuit connection.

Once chip detection succeeds, extract the complete flash contents with `flashrom -p ft2232_spi:type=2232H,port=A,divisor=4 --read rtl_firmware_dump.bin`. This operation reads the entire flash array sequentially and writes the raw binary image to disk, typically completing within 30 to 120 seconds depending on chip capacity and clock frequency. Do not interrupt this process, as partial dumps prove difficult to analyze and may miss critical firmware sections located at high address offsets. After the read completes, immediately verify the dump integrity by computing its SHA-256 hash with `sha256sum rtl_firmware_dump.bin > rtl_firmware_dump.sha256`, then perform a second read and compare hashes to confirm that both dumps match exactly. Hash mismatches indicate signal integrity problems, insufficient power supply decoupling, or flash chip degradation requiring replacement before proceeding with analysis.

Analyze the extracted firmware structure using binwalk to identify embedded filesystems, compression wrappers, and code regions within the raw flash image. Run `binwalk -e rtl_firmware_dump.bin` to automatically detect and extract any recognized file formats including U-Boot images, SquashFS filesystems, LZMA-compressed sections, and raw executable code. Binwalk's signature database recognizes hundreds of embedded file formats and produces a detailed scan report listing each detected structure's offset, type, and description. Review the scan output to construct a mental model of the flash memory layout, typically consisting of a bootloader at offset 0x0000, configuration data in the first few kilobytes, firmware code and read-only data in the middle sections, and calibration constants or user settings in the final blocks.

If binwalk identifies a compressed filesystem or U-Boot image, navigate into the extraction directory and inspect the unpacked contents. SquashFS filesystems contain a complete Linux root filesystem with standard directory hierarchies including /bin, /lib, /etc, and /usr, revealing the full userspace application stack, configuration files, and shared libraries present on the SDR platform. Examine configuration files for hardcoded credentials, network service bindings, and debug interfaces that may provide post-exploitation persistence mechanisms. Inspect shell scripts in /etc/init.d and /etc/rc.d to understand the boot sequence and identify services that launch without authentication or privilege separation.

For firmware images that do not contain identifiable filesystems, analyze the raw binary data using radare2 to disassemble code sections and identify interesting functions. Load the firmware dump with `r2 -b 16 -a arm rtl_firmware_dump.bin` assuming ARM Thumb-2 code, then auto-analyze with `aaaa` to detect function boundaries, cross-references, and string constants. Search for USB control transfer handling code by locating string references to register names like "USB_CTRL", "DEMOD_REG", or error messages related to buffer allocation and DMA transfer setup. The disassembly reveals implementation details including buffer sizes, bounds checking logic, and error handling paths that suggest potential overflow conditions or race conditions exploitable through carefully crafted USB control sequences.

Identify potential vulnerabilities by searching for unsafe string handling functions like strcpy, sprintf, and gets that lack bounds checking, or memory allocation patterns that fail to validate size parameters before allocating buffers. Construct call graphs showing data flow from USB control transfer reception through parsing, validation, and execution stages, highlighting any code paths where user-controlled data directly influences memory allocation sizes, array indices, or function pointers. Document each suspicious code pattern with annotated disassembly snippets, pseudo-code interpretations, and hypothesized exploitation primitives including buffer overflow offsets, ROP gadget candidates, or logic bugs that enable authentication bypasses.

Extend the firmware analysis to identify cryptographic operations and assess their implementation quality. Search the binary image for AES S-box constants, known SHA-256 initialization vectors, or RSA public key moduli that indicate the presence of cryptographic primitives. Use radare2's `/x` command to search for byte patterns, for example `/x 637c777bf26b6fc53001672bfed7ab76` locates the AES forward S-box first row. When cryptographic code appears, carefully review the implementation for classic vulnerabilities including constant-time violations that leak key material through timing side channels, missing or improperly seeded random number generation, and hardcoded keys or initialization vectors that allow offline cryptanalysis.

Correlate the firmware-level findings with the USB protocol observations from Exercise 1 by mapping high-level control transfer request codes to their implementing functions in the disassembled firmware. Create a mapping table that pairs each vendor-specific request code with its handler function address, parameter interpretation, and observable side effects. This correlation proves essential when constructing exploits that must trigger specific vulnerable code paths by sending precisely crafted USB control transfers. For example, if firmware analysis reveals that EEPROM write requests lack size validation, construct a USB fuzzing harness that sends oversized payloads to trigger buffer overflows in the EEPROM write handler.

Transition from passive firmware inspection to active register-level debugging by connecting a JTAG adapter to the RTL-SDR's main processor, enabling real-time inspection of CPU registers, memory contents, and execution state during normal operation. This technique requires identifying JTAG test points on the PCB, typically marked as TCK, TMS, TDI, TDO, and TRST or accessible through unpopulated header footprints near the main processor. Use a continuity tester to map suspected test points to the processor's JTAG pins identified from the CPU datasheet, then wire a compatible JTAG adapter such as an FT2232H in JTAG mode or a dedicated ARM debugger to these test points.

Configure OpenOCD to communicate with the target processor by creating a configuration file that specifies the JTAG adapter interface and target CPU type. For an RTL2832U with ARM Cortex-M0 core, create `rtl2832u.cfg` containing:

```tcl
# JTAG adapter configuration (FT2232H)
adapter driver ftdi
ftdi vid_pid 0x0403 0x6010
ftdi channel 0
ftdi layout_init 0x0008 0x000b
adapter speed 1000

# Target configuration (ARM Cortex-M0)
transport select jtag
source [find target/stm32f0x.cfg]

# Halt on connect
init
halt
```

Launch OpenOCD with `openocd -f rtl2832u.cfg` and observe the initialization output confirming successful JTAG chain detection and CPU identification. Once OpenOCD establishes communication, open a separate terminal and connect gdb-multiarch to the OpenOCD remote debugging interface with `gdb-multiarch` followed by `target extended-remote :3333` at the gdb prompt. You now have full debugger access to the running CPU including the ability to read and write memory, set hardware breakpoints, and single-step through firmware execution.

Use the JTAG debugging connection to inspect register contents during USB control transfer processing. Set a hardware breakpoint on the control transfer handler function identified during firmware analysis, for example `break *0x08001234` where the address corresponds to the handler entry point. Trigger a USB control transfer from the host using the Python script developed in Exercise 1, observing that execution halts at the breakpoint. Inspect the stack frame with `backtrace` to verify the call path, examine register contents with `info registers`, and dump memory buffers with `x/32xb 0x20000000` to view the control transfer setup packet and associated data payload.

Single-step through the control transfer handler using `stepi` commands while monitoring register values to understand exactly how firmware parses and validates request parameters. Pay particular attention to bounds checking logic, noting whether the firmware validates wLength against maximum buffer sizes before allocating memory or copying data. If validation appears absent or incorrect, document the specific code address, register state, and buffer addresses involved in the potential vulnerability. Capture the complete debugging session transcript including all register dumps and memory snapshots for later reference during exploit development.

Automate the register inspection workflow by writing an OpenOCD TCL script that periodically dumps specific memory regions and registers to log files during normal operation. Create `rtl_monitor.tcl` containing:

```tcl
# Continuous memory monitoring script for OpenOCD

proc dump_registers {} {
    global reg_log
    set timestamp [clock seconds]
    puts $reg_log "\n=== Register dump at $timestamp ==="
    
    # ARM Cortex-M registers
    set regs {r0 r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 sp lr pc xpsr}
    foreach reg $regs {
        set val [reg $reg]
        puts $reg_log "$reg: $val"
    }
}

proc dump_usb_buffers {} {
    global mem_log
    set timestamp [clock seconds]
    puts $mem_log "\n=== USB buffer dump at $timestamp ==="
    
    # Control transfer buffer (adjust address for your target)
    set ctrl_buf_addr 0x20000000
    set ctrl_buf_size 64
    puts $mem_log "Control buffer at $ctrl_buf_addr:"
    puts $mem_log [read_memory $ctrl_buf_addr 8 $ctrl_buf_size]
    
    # Bulk transfer buffer
    set bulk_buf_addr 0x20000100
    set bulk_buf_size 512
    puts $mem_log "Bulk buffer at $bulk_buf_addr:"
    puts $mem_log [read_memory $bulk_buf_addr 8 $bulk_buf_size]
}

proc monitor_loop {} {
    global reg_log mem_log
    
    set reg_log [open "rtl_registers.log" "w"]
    set mem_log [open "rtl_memory.log" "w"]
    
    puts "Starting continuous monitoring..."
    for {set i 0} {$i < 1000} {incr i} {
        dump_registers
        dump_usb_buffers
        after 100
    }
    
    close $reg_log
    close $mem_log
    puts "Monitoring complete. Logs written."
}

# Execute monitoring
monitor_loop
```

Run this monitoring script in OpenOCD with `script rtl_monitor.tcl` while simultaneously executing SDR operations from the host, then analyze the resulting log files to correlate USB activity with firmware register and memory state changes. This automated capture provides a detailed timeline of firmware execution that reveals transient state corruption, buffer overwrites, or register clobbering that may not produce immediate failures but accumulate over time to trigger exploitable conditions.

Complete this exercise by integrating all extracted firmware images, disassembly databases, debugging transcripts, and monitoring logs into a comprehensive security assessment report documenting identified vulnerabilities with severity ratings, exploitation difficulty assessments, and recommended mitigations. Archive all binary artifacts and analysis tools in the project repository with detailed README documentation explaining how to reproduce each analysis step, ensuring that future researchers can validate findings and extend the assessment to additional SDR platforms and firmware versions.

## Exercise 3: Fault Simulation & Exploit Verification

The third exercise synthesizes insights from USB protocol analysis and firmware reverse engineering to construct and validate working exploits against identified vulnerabilities in the RTL-SDR firmware and driver stack. The methodology encompasses both software-layer exploitation through malformed USB packets and hardware-layer fault injection using voltage and clock glitching techniques that bypass cryptographic protections and enable unauthorized firmware modifications. These techniques directly apply to offensive security engagements targeting wireless infrastructure, IoT deployments, and air-gapped systems that rely on SDR platforms for command and control or covert data exfiltration.

Begin with software-layer exploitation by constructing a USB fuzzing framework that systematically explores the control transfer attack surface identified during firmware analysis. The fuzzer generates malformed control transfers targeting specific vulnerable code paths including EEPROM write handlers with missing bounds checks, register access functions that fail to validate addresses, and I2C forwarding logic that incorrectly handles overlong transfer sequences. Implement the fuzzer using Python's pyusb library to maintain precise control over packet timing and payload construction while monitoring target device state through parallel usbmon capture and logic analyzer observation.

Create `rtl_usb_fuzzer.py` implementing a structured fuzzing campaign that progresses through increasing mutation aggressiveness:

```python
#!/usr/bin/env python3
import usb.core
import usb.util
import sys
import time
import random
import struct
import subprocess
import signal

RTL_VENDOR_ID = 0x0bda
RTL_PRODUCT_IDS = [0x2832, 0x2838]

# Vendor request codes (targets for fuzzing)
EEPROM_READ_REQ = 0x02
EEPROM_WRITE_REQ = 0x03
DEMOD_READ_REG = 0x00
DEMOD_WRITE_REG = 0x01
I2C_WRITE_REQ = 0x05
I2C_READ_REQ = 0x06

class RTLFuzzer:
    def __init__(self):
        self.dev = None
        self.crash_count = 0
        self.iteration = 0
        self.usbmon_proc = None
        
    def find_device(self):
        """Locate RTL-SDR device."""
        for product_id in RTL_PRODUCT_IDS:
            dev = usb.core.find(idVendor=RTL_VENDOR_ID, idProduct=product_id)
            if dev is not None:
                return dev
        return None
    
    def init_device(self):
        """Initialize device and detach kernel driver."""
        self.dev = self.find_device()
        if self.dev is None:
            print("[-] No RTL-SDR device found")
            return False
        
        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)
        
        self.dev.set_configuration()
        return True
    
    def start_usbmon(self):
        """Start usbmon capture in background."""
        bus = self.dev.bus
        filename = f"fuzz_usbmon_{int(time.time())}.txt"
        self.usbmon_proc = subprocess.Popen(
            ['cat', f'/sys/kernel/debug/usb/usbmon/{bus}u'],
            stdout=open(filename, 'w'),
            stderr=subprocess.DEVNULL
        )
        print(f"[*] usbmon capture started: {filename}")
    
    def stop_usbmon(self):
        """Stop usbmon capture."""
        if self.usbmon_proc:
            self.usbmon_proc.send_signal(signal.SIGTERM)
            self.usbmon_proc.wait()
    
    def check_device_alive(self):
        """Verify device responds to basic control transfer."""
        try:
            bmRequestType = usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
            data = self.dev.ctrl_transfer(bmRequestType, EEPROM_READ_REQ, 0, 0, 1, timeout=500)
            return True
        except:
            return False
    
    def fuzz_eeprom_write(self):
        """Fuzz EEPROM write requests with oversized payloads."""
        print("\n[*] Fuzzing EEPROM write requests...")
        
        # Test various payload sizes beyond normal bounds
        test_sizes = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        
        for size in test_sizes:
            self.iteration += 1
            payload = bytes([random.randint(0, 255) for _ in range(size)])
            offset = random.randint(0, 0xff)
            
            print(f"[{self.iteration}] EEPROM write: offset=0x{offset:02x}, size={size}")
            
            try:
                bmRequestType = usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
                self.dev.ctrl_transfer(bmRequestType, EEPROM_WRITE_REQ, 0, offset, payload, timeout=1000)
                
                # Check if device still responds
                if not self.check_device_alive():
                    print(f"[!] CRASH DETECTED after EEPROM write with size {size}")
                    self.crash_count += 1
                    return False
                
            except usb.core.USBError as e:
                print(f"[!] USB error: {e}")
                if not self.check_device_alive():
                    print(f"[!] CRASH DETECTED (USB error, device unresponsive)")
                    self.crash_count += 1
                    return False
            
            time.sleep(0.1)
        
        return True
    
    def fuzz_register_access(self):
        """Fuzz demodulator register read/write with invalid addresses."""
        print("\n[*] Fuzzing register access...")
        
        # Test register addresses including out-of-bounds
        test_addrs = list(range(0, 0x100)) + [0xff00, 0xffff, 0x10000, 0x20000]
        
        for addr in test_addrs:
            self.iteration += 1
            page = random.randint(0, 15)
            value = random.randint(0, 255)
            
            print(f"[{self.iteration}] Register write: page={page}, addr=0x{addr:04x}, val=0x{value:02x}")
            
            try:
                block = page & 0xff
                reg = (addr >> 8) & 0xff
                addr_low = addr & 0xff
                
                bmRequestType = usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
                data = bytes([value])
                self.dev.ctrl_transfer(bmRequestType, DEMOD_WRITE_REG, addr_low, (block << 8) | reg, data, timeout=1000)
                
                if not self.check_device_alive():
                    print(f"[!] CRASH DETECTED after register write to 0x{addr:04x}")
                    self.crash_count += 1
                    return False
                
            except usb.core.USBError as e:
                print(f"[!] USB error: {e}")
                if not self.check_device_alive():
                    print(f"[!] CRASH DETECTED (device unresponsive)")
                    self.crash_count += 1
                    return False
            
            time.sleep(0.05)
        
        return True
    
    def fuzz_i2c_transfers(self):
        """Fuzz I2C forwarding with malformed transfers."""
        print("\n[*] Fuzzing I2C transfers...")
        
        # Test I2C writes with various lengths
        test_lens = [1, 2, 4, 8, 16, 32, 64, 128, 256]
        
        for length in test_lens:
            self.iteration += 1
            i2c_addr = random.choice([0x1a, 0x34, 0x50, 0xff])  # Common tuner addresses + invalid
            payload = bytes([random.randint(0, 255) for _ in range(length)])
            
            print(f"[{self.iteration}] I2C write: addr=0x{i2c_addr:02x}, len={length}")
            
            try:
                bmRequestType = usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
                self.dev.ctrl_transfer(bmRequestType, I2C_WRITE_REQ, i2c_addr, 0, payload, timeout=1000)
                
                if not self.check_device_alive():
                    print(f"[!] CRASH DETECTED after I2C write with length {length}")
                    self.crash_count += 1
                    return False
                
            except usb.core.USBError as e:
                print(f"[!] USB error: {e}")
                if not self.check_device_alive():
                    print(f"[!] CRASH DETECTED")
                    self.crash_count += 1
                    return False
            
            time.sleep(0.1)
        
        return True
    
    def run_campaign(self):
        """Execute complete fuzzing campaign."""
        print("[*] RTL-SDR USB Fuzzer")
        print("[*] Initializing device...")
        
        if not self.init_device():
            return
        
        self.start_usbmon()
        
        try:
            # Run fuzzing phases
            phases = [
                self.fuzz_eeprom_write,
                self.fuzz_register_access,
                self.fuzz_i2c_transfers
            ]
            
            for phase in phases:
                if not phase():
                    print("\n[!] Fuzzing halted due to device crash")
                    break
                time.sleep(1)
            
            print(f"\n[*] Fuzzing campaign complete")
            print(f"[*] Total iterations: {self.iteration}")
            print(f"[*] Crashes detected: {self.crash_count}")
            
        except KeyboardInterrupt:
            print("\n[*] Fuzzing interrupted by user")
        
        finally:
            self.stop_usbmon()
            usb.util.dispose_resources(self.dev)

def main():
    fuzzer = RTLFuzzer()
    fuzzer.run_campaign()

if __name__ == "__main__":
    main()
```

Execute the fuzzer with `python3 rtl_usb_fuzzer.py` and monitor system logs with `dmesg -w` in a separate terminal to detect kernel USB subsystem errors, driver crashes, or device disconnections indicating successful crash induction. Document each crash with its triggering input parameters, associated usbmon traffic preceding the failure, and recovery method required to restore device functionality. Crashes that require physical device power cycling indicate severe firmware corruption or hardware protection faults potentially exploitable for persistent compromise.

Analyze crash dumps and kernel logs to determine root cause and exploitation potential for each identified crash. Look for kernel messages indicating USB transfer timeouts, which suggest firmware watchdog failures or infinite loops triggered by malformed requests. DMA buffer corruption messages indicate memory safety violations that may enable arbitrary code execution if you can control the corrupted buffer contents. Use the usbmon traces captured during fuzzing to reconstruct the exact sequence of control transfers leading to each crash, then minimize the test case to the smallest input that reliably reproduces the failure.

For crashes that appear exploitable, develop a proof-of-concept that demonstrates controlled memory corruption or code execution. If EEPROM write fuzzing triggers a crash with register corruption visible through JTAG inspection, construct a carefully crafted payload that overwrites a function pointer or return address with a controlled value pointing to attacker-supplied code. Inject the exploit payload through the USB control transfer interface while simultaneously monitoring memory contents through the JTAG connection to verify that the target address receives the intended value before firmware attempts to dereference it.

Transition to hardware-layer fault injection by constructing a voltage glitching apparatus that momentarily disrupts CPU power supply during security-critical operations like signature verification or access control checks. The glitcher connects to the target's power rail through a high-speed MOSFET switch controlled by a microcontroller that can insert microsecond-duration power drops synchronized to specific code execution points. Build a basic glitcher using an Arduino or STM32 development board connected to an IRLZ44N logic-level N-channel MOSFET, with the MOSFET drain connected to the target VCC and source connected to a stable power supply. The microcontroller drives the MOSFET gate through a series resistor, enabling rapid switching between normal power delivery and glitch insertion.

Wire the glitcher inline with the RTL-SDR's 3.3V power rail by cutting the VCC trace on the PCB and soldering fine wire bridges that route power through the glitcher's MOSFET. Install a current sense resistor (0.1 ohm, 1W) in series with the power path and connect a logic analyzer across this resistor to monitor instantaneous current draw, providing feedback about CPU instruction execution and identifying high-activity periods suitable for glitch insertion. Configure the glitcher microcontroller to accept trigger inputs from the logic analyzer's pattern matching engine, enabling synchronized glitch delivery timed to specific USB packet reception events or register access patterns.

Develop a glitch timing calibration procedure that sweeps glitch width and offset parameters while monitoring target behavior through USB control transfer responses and JTAG register inspection. Create `glitch_calibrate.py` that systematically varies glitch parameters:

```python
#!/usr/bin/env python3
import serial
import time
import usb.core
import usb.util

class VoltageGlitcher:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino reset
        
    def set_glitch_params(self, delay_us, width_us):
        """Configure glitch timing parameters."""
        cmd = f"GLITCH {delay_us} {width_us}\n"
        self.ser.write(cmd.encode())
        response = self.ser.readline().decode().strip()
        return response == "OK"
    
    def arm(self):
        """Arm glitcher for next trigger."""
        self.ser.write(b"ARM\n")
        response = self.ser.readline().decode().strip()
        return response == "ARMED"
    
    def trigger(self):
        """Manually trigger glitch."""
        self.ser.write(b"TRIGGER\n")
        response = self.ser.readline().decode().strip()
        return response == "FIRED"
    
    def get_status(self):
        """Query glitcher status."""
        self.ser.write(b"STATUS\n")
        response = self.ser.readline().decode().strip()
        return response

def test_glitch_effect(glitcher, delay, width):
    """Test specific glitch parameters and check device response."""
    glitcher.set_glitch_params(delay, width)
    glitcher.arm()
    
    # Trigger USB operation that executes target code
    dev = usb.core.find(idVendor=0x0bda, idProduct=0x2832)
    if dev is None:
        return "DEVICE_LOST"
    
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)
    dev.set_configuration()
    
    try:
        # Initiate control transfer while glitch fires
        bmRequestType = usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE
        glitcher.trigger()
        data = dev.ctrl_transfer(bmRequestType, 0x02, 0, 0, 16, timeout=500)
        
        # Verify data integrity
        if len(data) == 16:
            return "SUCCESS"
        else:
            return "CORRUPTED"
            
    except usb.core.USBError:
        return "ERROR"
    finally:
        usb.util.dispose_resources(dev)

def main():
    print("[*] Voltage Glitching Calibration")
    
    glitcher = VoltageGlitcher('/dev/ttyACM0')
    print(f"[+] Glitcher status: {glitcher.get_status()}")
    
    # Sweep glitch parameters
    results = []
    for delay in range(0, 1000, 50):  # Delay in microseconds
        for width in range(10, 200, 10):  # Width in microseconds
            result = test_glitch_effect(glitcher, delay, width)
            results.append((delay, width, result))
            print(f"[*] delay={delay}us, width={width}us -> {result}")
            time.sleep(0.5)
    
    # Analyze results
    print("\n[*] Glitch Parameter Analysis:")
    for delay, width, result in results:
        if result in ["CORRUPTED", "ERROR"]:
            print(f"[!] Interesting result at delay={delay}us, width={width}us: {result}")

if __name__ == "__main__":
    main()
```

Execute the calibration script with `python3 glitch_calibrate.py` while monitoring target device behavior through JTAG and logic analyzer capture. Successful glitches manifest as corrupted EEPROM read results, skipped instruction sequences visible in JTAG trace, or USB enumeration failures indicating firmware crash. Record all parameter combinations that produce anomalous behavior, then refine the sweep around these regions with finer granularity to identify the precise timing window where glitches bypass security checks without causing complete system failure.

Apply calibrated glitch parameters to bypass firmware signature verification during boot, enabling installation of modified firmware with debugging backdoors or disabled security features. Many embedded systems verify firmware integrity by computing a hash or signature over flash contents and comparing against a stored reference value, typically implemented as a tight loop reading flash data and updating a cryptographic accumulator. Voltage glitching this verification routine can cause individual comparison instructions to skip or produce incorrect results, allowing the boot process to proceed with tampered firmware that would normally be rejected.

Identify the signature verification routine in the firmware disassembly by searching for cryptographic constants, comparison operations against fixed values, or branch instructions that diverge to failure paths when verification fails. Set a JTAG hardware breakpoint at the verification routine entry point, then boot the device while capturing current trace with the logic analyzer to correlate instruction execution timing with current waveform features. Use this correlation to calibrate glitch delivery such that the power drop occurs precisely during the critical comparison instruction, increasing the probability of bypassing the check without crashing the entire boot sequence.

Construct a modified firmware image that includes a USB backdoor providing unauthorized EEPROM access and register manipulation capabilities. Modify the extracted firmware to add a new vendor-specific control request handler that accepts arbitrary memory write commands without authentication or bounds checking, effectively granting complete control over device state through the USB interface. Recompile or patch the firmware binary to insert this backdoor code, recalculate any checksums or signatures present in the image, then write the modified firmware to a second flash chip for offline testing before attempting to install it on the target device through glitch-assisted signature bypass.

Test the backdoor functionality by programming the modified firmware onto a sacrificial RTL-SDR device using the SPI programmer, verifying that the new control request handler responds correctly to test commands. Once functionality is confirmed in the controlled test environment, attempt to install the backdoored firmware on a production device using voltage glitching to bypass signature verification during boot. Document the complete attack chain including glitch parameters, timing synchronization method, and success rate across multiple boot attempts, providing quantitative assessment of the practical exploitation difficulty for this vulnerability.

Complete this exercise by documenting all developed exploits, glitch calibration data, and modified firmware images in a structured vulnerability disclosure report suitable for submission to the device manufacturer and relevant CERT organizations. Include detailed remediation recommendations such as implementing monotonic boot counters that detect glitch-induced verification bypasses, adding redundant verification stages with independent power domains, and enabling hardware-level memory protection that prevents firmware modification without secure boot key material. Archive all exploit code, calibration scripts, and hardware schematics in the project repository with clear warnings about responsible disclosure obligations and legal restrictions on unauthorized device modification.

## Hardware Security Checklist & Diagnostic Cheat Sheet

This final section consolidates the methodologies, tool invocations, and diagnostic procedures developed throughout the laboratory exercises into a practical reference checklist for conducting systematic hardware security assessments on SDR platforms and similar embedded wireless devices. The checklist follows a standard penetration testing methodology adapted for hardware targets, progressing from reconnaissance through exploitation to post-compromise persistence and impact assessment.

### Phase 1: Reconnaissance & Device Enumeration

Connect target SDR device to isolated USB hub with current monitoring capability. Document physical device characteristics including manufacturer markings, FCC ID, and visible chip part numbers. Photograph PCB from multiple angles with sufficient resolution to read component markings and trace routing.

Query USB device descriptors and enumerate endpoints with `lsusb -v -d 0bda:2832`, replacing vendor and product IDs with values specific to your target platform. Record bcdUSB version, device class, vendor and product strings, and all interface and endpoint descriptors. Note any unusual configurations such as hidden interfaces, vendor-specific classes, or isochronous endpoints suggesting audio or video streaming capabilities.

Capture USB enumeration sequence with logic analyzer at 24 MS/s, ensuring complete coverage from device attachment through driver binding. Export trace in sigrok .sr format for archival and annotate descriptor exchanges with semantic labels indicating function assignments.

Identify communication pathways beyond USB including UART serial consoles, JTAG debug interfaces, SPI flash memory, and I2C peripheral buses. Test suspected UART pins by probing with oscilloscope set to trigger on 3.3V logic transitions while device boots, looking for characteristic serial data waveforms at standard baud rates (9600, 115200, 921600). Connect USB-UART adapter configured for 115200 8N1 and launch minicom with `minicom -D /dev/ttyUSB0` to capture boot console output.

Locate JTAG interface by identifying processor pinout from datasheet and testing continuity between suspected test points and CPU JTAG pins. Use OpenOCD boundary scan to enumerate JTAG chain topology with `openocd -f interface/ftdi/ft2232h.cfg -c "adapter speed 100" -c "transport select jtag" -c "jtag_scan chain" -c "shutdown"`.

### Phase 2: Firmware Extraction & Analysis

Extract SPI flash contents using flashrom and Pomona SOIC clip attached to in-circuit chip. Power device through normal USB connection but verify flash chip receives stable 3.3V before initiating read operation. Execute extraction with `flashrom -p ft2232_spi:type=2232H,port=A,divisor=4 --read firmware_$(date +%Y%m%d_%H%M%S).bin`.

Verify dump integrity by computing SHA-256 hash and performing secondary read to confirm reproducible results. Mismatch indicates signal integrity issues requiring lower clock speed (increase divisor to 8 or 16) or improved probe grounding.

Analyze firmware structure with `binwalk -e firmware.bin` to identify embedded filesystems, compressed sections, and code regions. Manually inspect extracted components including bootloader, kernel image, root filesystem, and configuration data partitions.

Disassemble firmware code sections with radare2, beginning with automated analysis via `r2 -A -b 16 -a arm firmware.bin`. Search for vulnerability indicators including unsafe string handling (`/c strcpy,sprintf,gets`), hardcoded credentials (`/c password,secret,key`), and cryptographic operations (`/x 637c777bf26b6fc53001672bfed7ab76` for AES S-box).

Construct memory map documenting flash layout with base addresses, sizes, and content types for each identified region. Correlate this static analysis with runtime observations from JTAG debugging to validate assumptions about code execution flow and data storage organization.

### Phase 3: Protocol Analysis & Attack Surface Mapping

Capture USB control and bulk transfers during normal operation using usbmon facility. Enable monitoring with `modprobe usbmon && cat /sys/kernel/debug/usb/usbmon/1u > usbmon_baseline.txt`, then exercise all device functionality including frequency tuning, gain adjustment, sample rate configuration, and streaming activation.

Parse captured traffic to extract control transfer parameters and reconstruct register programming sequences. Build state machine diagram mapping high-level API calls to USB protocol operations, identifying trust boundaries where user-controlled data enters firmware processing without validation.

Identify fuzzing targets including EEPROM access, register read/write, I2C forwarding, and DMA buffer management. Prioritize targets based on code complexity, data-dependent behavior, and proximity to memory allocation or pointer dereference operations visible in firmware disassembly.

Enumerate all vendor-specific request codes by testing sequential request values from 0x00 through 0xff and observing device responses. Document each functional request with parameter interpretation, observable side effects, and potential security implications.

### Phase 4: Vulnerability Discovery & Exploitation

Execute systematic USB fuzzing campaign targeting each identified attack vector with progressively aggressive input mutations. Begin with boundary value testing using maximum and oversized length parameters, then proceed to format string injection, integer overflow payloads, and rapid request sequences designed to trigger race conditions.

Monitor device state during fuzzing through parallel usbmon capture, kernel log observation (`dmesg -w`), and JTAG register inspection where available. Document all crashes, hangs, and anomalous behavior with complete reproduction procedures including timing parameters and environmental conditions.

Triage discovered vulnerabilities by analyzing crash dumps and firmware execution traces to determine root cause and exploitation feasibility. Classify findings as denial of service, information disclosure, memory corruption, or authentication bypass based on observed behavior and surrounding code context.

Develop proof-of-concept exploits for high-severity vulnerabilities demonstrating concrete impact such as arbitrary code execution, persistent device compromise, or unauthorized hardware control. Test exploits in controlled environment using sacrificial hardware before attempting against production devices.

### Phase 5: Hardware Fault Injection

Construct voltage glitching apparatus using high-speed MOSFET switch inline with target device power rail. Calibrate glitch parameters by sweeping delay and width while monitoring device behavior through USB responses and JTAG inspection.

Identify security-critical code sections susceptible to glitch-induced bypass including signature verification, access control checks, and cryptographic operations. Use JTAG breakpoints and current trace correlation to synchronize glitch delivery with target instruction execution.

Evaluate glitch-assisted firmware modification by attempting to bypass boot-time signature verification and install backdoored firmware image. Measure success rate across multiple attempts and document minimum glitch parameters required for reliable exploitation.

### Phase 6: Documentation & Disclosure

Compile comprehensive vulnerability report documenting discovered issues with CVSSv3 severity scores, detailed reproduction procedures, proof-of-concept exploit code, and recommended mitigations. Include supporting evidence such as disassembly snippets, memory dumps, and captured signal traces demonstrating vulnerability triggers.

Prepare vendor disclosure package following coordinated disclosure guidelines with 90-day remediation window. Submit findings through vendor security contact or CERT coordinator with detailed technical analysis and offer of assistance with remediation validation.

Archive all research artifacts including firmware dumps, capture traces, exploit code, and analysis scripts in secure repository with access controls preventing unauthorized distribution before public disclosure date.

### Diagnostic Command Reference

**USB Device Enumeration:**
```bash
lsusb -v -d 0bda:2832
usb-devices | grep -A 20 RTL
cat /sys/kernel/debug/usb/devices | grep -A 30 'Vendor=0bda'
```

**USB Traffic Capture:**
```bash
modprobe usbmon
cat /sys/kernel/debug/usb/usbmon/1u > capture.txt
tcpdump -i usbmon1 -w capture.pcap
```

**Logic Analyzer Control:**
```bash
sigrok-cli --scan
sigrok-cli -d fx2lafw --config samplerate=24M --samples 16M -o capture.sr
pulseview capture.sr
```

**SPI Flash Operations:**
```bash
flashrom --list-supported | grep -i ft2232
flashrom -p ft2232_spi:type=2232H,port=A --read dump.bin
flashrom -p ft2232_spi:type=2232H,port=A --write modified.bin
```

**Firmware Analysis:**
```bash
binwalk -e firmware.bin
strings -n 8 firmware.bin | grep -E 'password|secret|key'
r2 -A -b 16 -a arm firmware.bin
radare2 -q -c 'aaa; afl; pdf @ main' firmware.bin
```

**JTAG Debugging:**
```bash
openocd -f interface/ftdi/ft2232h.cfg -f target/stm32f0x.cfg
gdb-multiarch -ex 'target extended-remote :3333' firmware.elf
```

**Serial Console Access:**
```bash
minicom -D /dev/ttyUSB0 -b 115200
screen /dev/ttyUSB0 115200
picocom -b 115200 /dev/ttyUSB0
```

This consolidated reference enables rapid deployment of hardware security assessment workflows against new target platforms, reducing reconnaissance time and ensuring comprehensive coverage of common embedded vulnerability classes. Maintain this checklist as a living document, updating tool commands and methodology refinements as new exploitation techniques and defensive technologies emerge in the hardware security research community.
