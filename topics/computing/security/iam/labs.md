# Operational Verification Labs: Identity and Access Management Hardware Security

## Objective & Lab Bench Setup

Identity and Access Management (IAM) in embedded systems and hardware security contexts represents the physical and cryptographic boundary between trusted execution environments and external adversaries. Unlike cloud IAM systems that rely on network authentication protocols and centralized policy engines, hardware IAM manifests as cryptographic key storage, secure boot chains, trusted platform modules, and physical access control mechanisms embedded in silicon. This laboratory guide dissects the hardware attack surface of IAM-adjacent components: smart cards, hardware security modules, TPM chips, JTAG debug interfaces, secure element integrated circuits, and the cryptographic coprocessors that underpin modern device identity schemes.

The penetration tester approaching hardware IAM must understand that identity in this domain is anchored not in usernames and passwords but in asymmetric key pairs burned into one-time programmable memory, challenge-response protocols executed by cryptographic accelerators, and attestation chains rooted in manufacturer-provisioned secrets. An IAM failure at the hardware layer permits an attacker to impersonate devices, extract root-of-trust secrets, bypass secure boot enforcement, or clone authentication tokens. These attacks demand physical access, intimate knowledge of bus protocols, and the ability to interpret register-level state machines that implement cryptographic operations.

Your laboratory bench constitutes a forensic workstation for hardware reverse engineering and fault injection. At minimum, provision a USB logic analyzer capable of 100 MHz sampling with at least eight channels—devices such as the Saleae Logic Pro series or open-hardware alternatives like the fx2lafw-compatible Cypress FX2LP adapters suffice for most targets. Augment this with a USB-to-UART bridge supporting 3.3V and 1.8V logic levels; the FTDI FT232H or Silicon Labs CP2102 provide reliable serial consoles and bit-banged SPI/I2C masters. For JTAG and SWD boundary-scan debugging, deploy an OpenOCD-compatible adapter—the Segger J-Link EDU, Black Magic Probe, or FTDI-based ARM-JTAG-SWD converters all provide vendor-neutral access to CoreSight debug infrastructure on ARM Cortex-M and Cortex-A targets.

Supplement hardware probing with a surgical toolkit for physical access: precision screwdrivers, spudgers, hot-air rework stations for desoldering surface-mount packages, and magnification optics (jeweler's loupes or USB microscopes at 10–50× magnification). For non-invasive probing, stock fine-pitch test hooks, micro-grabber clips, and 0.1-inch jumper wires; for invasive techniques, maintain flux-core solder, copper braid desoldering wick, and Kapton tape for insulating adjacent traces. Firmware extraction and analysis require a software stack: install `sigrok-cli` for protocol decoding, `openocd` for JTAG/SWD automation, `flashrom` for SPI flash manipulation, `binwalk` for firmware image parsing, and `radare2` for disassembly and binary analysis. On Debian-derived distributions, provision these tools via `apt-get install sigrok-cli openocd flashrom binwalk radare2 gdb-multiarch minicom`. Verify installation by executing `sigrok-cli --scan` to enumerate connected logic analyzers and `openocd --version` to confirm ARM and RISC-V target support.

Establish a safe working environment with electrostatic discharge precautions: ground yourself and the target device through ESD wrist straps and conductive mats. Many hardware IAM components—particularly smart card controllers and TPM chips—operate at 1.8V or lower logic levels; applying 5V TTL signals to these pins induces irreversible latch-up failures. Always verify target voltage domains with a multimeter before connecting probes, and configure your USB-UART and logic analyzer voltage thresholds accordingly. Prepare a laboratory notebook—physical or digital—to record pinouts, waveform screenshots, memory dumps, and observed security failures; reproducibility in hardware exploitation demands meticulous documentation of physical setup, tool configuration, and signal timing.

## Exercise 1: Live Hardware Probing & Signal Capture

Begin by identifying and enumerating the hardware IAM components on your target device. Common embedded IAM implementations include discrete Trusted Platform Module (TPM) chips adhering to the Trusted Computing Group (TCG) specification, secure elements such as NXP's A700x series or Infineon SLE97 devices, and integrated cryptographic coprocessors within system-on-chip designs. Consult the target's service manual or datasheets to locate these components; TPM chips typically present as 32-pin QFN or VQFN packages labeled with vendor identifiers (Infineon SLB9670, STMicroelectronics ST33TP, Nuvoton NPCT75x). Secure elements often reside on dedicated smart card-form PCBs connected via ISO 7816 contact interfaces or I2C buses. Integrated coprocessors require SoC documentation to map cryptographic peripheral base addresses and memory-mapped register layouts.

Your first probing objective targets the Low Pin Count (LPC) bus connecting a discrete TPM to the host processor, or alternatively, the I2C/SPI bus interfacing a secure element. The LPC protocol, a legacy Intel specification for slow peripheral communication, multiplexes address, data, and control signals across four bidirectional lines (LAD[0:3]), clocked by a 33 MHz LCLK signal and framed by LFRAME# start-of-cycle assertions. To capture TPM communication, connect your logic analyzer to the LPC bus: identify LAD0 through LAD3 (typically found on pins adjacent to the TPM's LCLK input), ground your analyzer to a PCB ground plane, and attach the LCLK signal to your analyzer's clock input channel. Modern logic analyzers with protocol-aware decoding—such as those supported by PulseView (the sigrok GUI frontend)—automatically parse LPC cycles into memory read, I/O read, I/O write, and DMA transactions.

Configure your capture session for continuous acquisition at 100 MHz sampling to avoid aliasing the 33 MHz LPC clock; invoke `sigrok-cli` with parameters specifying the analyzer device, channel mapping, and protocol decoder stack:

```bash
sigrok-cli --driver fx2lafw --config samplerate=100000000 \
  --channels 0=LCLK,1=LAD0,2=LAD1,3=LAD2,4=LAD3,5=LFRAME \
  --protocol-decoders lpc:lclk=LCLK:lad0=LAD0:lad1=LAD1:lad2=LAD2:lad3=LAD3:lframe=LFRAME \
  --output-format ascii --output-file tpm_lpc_capture.txt
```

Trigger the capture manually, then boot the target system and observe the TPM initialization sequence during the platform's secure boot handshake. The decoded output reveals I/O write transactions to TPM command registers at LPC I/O address 0xFED40000 (the TCG-mandated TPM locality zero base address), followed by read cycles polling the TPM status register for command completion. Inspect the byte sequences written to the command FIFO: TPM commands follow the Trusted Platform Module Library Specification, with each command prefaced by a two-byte tag (0x8001 for TPM_ST_NO_SESSIONS, 0x8002 for TPM_ST_SESSIONS), a four-byte command size, and a four-byte command code. A TPM2_Startup command (code 0x00000144) initializes the TPM after power-on, while TPM2_PCR_Extend (code 0x00000182) measures boot components into Platform Configuration Registers for attestation.

Parallel to LPC protocol analysis, probe the reset and physical presence signals that constitute the TPM's hardware IAM enforcement layer. The TPM reset pin (often labeled TPM_RST# or nRST) receives an active-low pulse during platform initialization; holding this line low indefinitely prevents TPM command processing, a simple denial-of-service vector against measured boot. More critically, locate the physical presence interface—typically a General Purpose Input/Output (GPIO) line from the host processor to the TPM's PP (physical presence) pin or a platform-specific register accessible only through System Management Mode. Physical presence signals authorize sensitive operations like clearing the TPM's owner hierarchy or disabling platform configuration; an attacker who can assert this signal through hardware manipulation bypasses software-based authentication for TPM administration.

To verify physical presence enforcement, connect a jumper wire from the identified PP GPIO to ground (asserting physical presence) while issuing a TPM2_Clear command through the Linux TSS software stack or Windows TPM management console. Monitor the LPC bus for the command's authorization session: without physical presence, the TPM returns TPM_RC_AUTH_FAIL (0x0000098E); with the hardware signal asserted, the TPM acknowledges the clear operation and resets its non-volatile storage. Document this hardware bypass in your notes: many OEM platforms fail to protect physical presence GPIOs with locked configuration registers, permitting post-manufacture assertion via accessible test points.

For I2C-based secure elements, reconfigure your logic analyzer for dual-channel I2C capture. The I2C protocol employs two open-drain lines: Serial Data (SDA) and Serial Clock (SCL), both pulled high through resistors and driven low by active devices. Identify these signals on your target—secure elements often share an I2C bus with other peripherals like EEPROMs or sensor ICs. Connect your logic analyzer's ground to the board ground, SDA to channel zero, and SCL to channel one. Launch a capture session with I2C protocol decoding enabled:

```bash
sigrok-cli --driver fx2lafw --config samplerate=24000000 \
  --channels 0=SDA,1=SCL \
  --protocol-decoders i2c:scl=SCL:sda=SDA \
  --output-format ascii --output-file secure_element_i2c.txt
```

Trigger authentication transactions by initiating a device login or cryptographic signing operation on the target platform. The decoded I2C trace exposes the secure element's seven-bit slave address (commonly 0x60 for ATECC608 family devices or 0x42 for Infineon SLI series), followed by write transactions containing command packets. Secure element commands adhere to vendor-specific formats: the Microchip CryptoAuthentication family uses a packet structure comprising a one-byte command opcode, a one-byte parameter byte, two-byte parameter fields, and optional data payloads, all suffixed with a two-byte CRC-16 checksum. An authentication challenge-response sequence begins with a Nonce command (opcode 0x16) loading a random number into the device's TempKey register, followed by a GenDig command (opcode 0x15) computing an HMAC-SHA256 digest combining the nonce with a stored secret key, and concludes with a CheckMac command (opcode 0x28) verifying the host's response.

Analyze the captured I2C traffic for cryptographic material leakage. While secure elements are designed to never emit private keys on the bus, implementation flaws occasionally expose intermediate state. Examine the data payloads returned by Read commands (opcode 0x02): configuration zones and data slots may contain unencrypted metadata, certificate fragments, or even key material if slot read protection was not locked during device provisioning. Cross-reference captured slot contents against the device's datasheet to identify misconfigured read/write permissions—a common vulnerability in prototype hardware that persists into production runs.

Extend your I2C capture to explore fault injection opportunities. Many secure elements implement anti-tamper features: supply voltage monitoring (brownout detection), clock frequency monitoring (detecting glitching attempts), and secure erase on physical intrusion. Test these defenses by introducing controlled perturbations. Momentarily short the secure element's supply voltage pin to ground through a 100-ohm resistor while an authentication operation is in progress; monitor the I2C bus for partial command responses or error codes. Devices with robust brownout detection abort the operation and return execution failure indicators, but poorly designed implementations may leave TempKey registers in partially computed states that leak bits of the secret key through side-channel analysis of subsequent operations.

Conclude this exercise by enumerating all cryptographic interfaces on your target: JTAG debug ports, SPI flash chips storing bootloader code and key material, UART consoles exposing cryptographic API shells, and USB interfaces presenting smart card readers or FIDO authenticators. For each interface, record the physical pin locations, bus protocol parameters (baud rates, clock frequencies, voltage levels), and observed transaction patterns. This reconnaissance map forms the foundation for deeper exploitation in subsequent exercises, where you will dump cryptographic secrets, bypass authentication state machines, and inject faulted execution flows.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

Having established live signal capture capabilities, advance to invasive memory extraction from IAM-adjacent components. The objective is to retrieve cryptographic key material, firmware images, and configuration data stored in non-volatile memory (NVM) regions that anchor hardware identity. Targets include SPI NOR flash chips containing bootloader code and encrypted key blobs, I2C EEPROMs storing device certificates and provisioning data, and one-time programmable (OTP) fuse arrays burned into secure element silicon.

Begin with external SPI flash extraction, a ubiquitous attack vector in embedded IAM systems. SPI flash chips provide bulk storage for bootloader firmware, root-of-trust code, and encrypted key containers; compromising this storage permits offline analysis, firmware modification, and cryptographic oracle attacks against key-derivation functions. Identify the SPI flash chip on your target board—common packages include 8-pin SOIC (Small Outline Integrated Circuit) or WSON (Very Small Outline No-Lead) form factors, with vendor markings like Winbond W25Q, Macronix MX25L, or Micron N25Q series. Consult the chip's datasheet to confirm pinout: SPI flash follows a standard six-signal interface comprising Chip Select (CS#), Serial Clock (SCK), Serial Input (SI or MOSI), Serial Output (SO or MISO), Write Protect (WP#), and Hold (HOLD#).

For non-invasive in-circuit extraction, employ a SOIC-8 test clip (e.g., Pomona 5250 series) to attach to the flash chip without desoldering. Confirm that the target board is powered down and disconnected from external power supplies; residual voltage on the SPI bus can damage your programmer. Connect the test clip to an FT232H-based USB-SPI adapter or a dedicated flash programmer like the CH341A. Verify connectivity by reading the flash chip's JEDEC ID, a three-byte manufacturer and device identifier:

```bash
flashrom -p ft2232_spi:type=232H,port=A --read-id
```

Successful identification returns the vendor code (0xEF for Winbond, 0xC2 for Macronix), memory type, and capacity. If the read fails, check for active chip-select contention: the host processor may assert CS# even when powered down due to internal pull-down resistors or residual charge in decoupling capacitors. Resolve this by desoldering the flash chip entirely or cutting the CS# trace and isolating the chip with a bodge wire. Alternatively, power the target board into a quiescent state where the host processor holds CS# high (inactive), enabling shared bus access.

Proceed to full flash extraction. Modern SPI flash chips support fast-read commands operating at up to 104 MHz clock rates; however, in-circuit parasitic capacitance and signal reflections necessitate conservative clock speeds. Configure `flashrom` for a 10 MHz read operation to ensure data integrity:

```bash
flashrom -p ft2232_spi:type=232H,port=A,speed=10000 --read flash_dump.bin
```

The extraction process streams the entire flash contents—typically 4 MB to 16 MB—into a binary file. Monitor for read errors indicating bad blocks or ECC failures; SPI flash does not implement error correction at the protocol level, so bit flips manifest as mismatched checksums during verification reads. If errors occur, retry the read operation multiple times and compare dumps with binary diff tools like `vbindiff` or `hexdump` to identify stable versus corrupted regions.

Analyze the extracted firmware image with `binwalk` to decompress and parse embedded file systems, cryptographic certificates, and key material. Execute a recursive extraction pass to unpack compressed bootloader stages, U-Boot images, and SquashFS root filesystems:

```bash
binwalk -e flash_dump.bin
```

Binwalk identifies file signatures through magic-byte pattern matching: examine the output for LZMA-compressed blobs (bootloader stages), U-Boot legacy images (ARM or MIPS kernel loaders), and PKCS#7/PEM-encoded X.509 certificates. Certificates stored in plaintext reveal the device's identity chain: inspect subject distinguished names, issuer authorities, and validity periods to map the trust hierarchy. Many embedded systems store asymmetric private keys in PKCS#8 DER format, encrypted with a password-derived key. Locate these encrypted blobs by searching for the PKCS#8 ASN.1 structure preamble (hexadecimal sequence `30 82` indicating a DER-encoded sequence):

```bash
hexdump -C flash_dump.bin | grep "30 82"
```

Extract candidate key blobs into separate files and attempt decryption with common passwords (`admin`, `password`, `123456`, manufacturer default credentials) using OpenSSL:

```bash
openssl pkcs8 -in encrypted_key.der -inform DER -out decrypted_key.pem
```

If decryption succeeds, the extracted private key grants full device impersonation capabilities—an attacker can sign challenges, establish authenticated TLS sessions, and enroll rogue devices into management infrastructure. Document the key extraction chain meticulously: note whether the encryption password was hardcoded in firmware (enabling trivial decryption) or derived from hardware-specific entropy like CPU serial numbers (requiring additional reverse engineering of key-derivation code).

Parallel to flash extraction, probe I2C EEPROM chips storing device provisioning data. Unlike flash memory, EEPROMs are byte-addressable and lack block-erase requirements, making them ideal for storing small cryptographic parameters and configuration tables. Identify the EEPROM on your target board—common devices include the Microchip 24LC series (24LC256, 24LC512) or STMicroelectronics M24 series. These chips adhere to the I2C EEPROM standard: an eight-bit device address (composed of a four-bit device type code `1010`, three address pins A2-A0, and a read/write bit), followed by one or two address bytes specifying the internal memory location.

Connect your FT232H to the EEPROM's SDA and SCL lines. Use the `i2cdetect` utility from the `i2c-tools` package to scan for active I2C devices:

```bash
i2cdetect -y 0
```

The scan reveals populated addresses; typical EEPROMs respond at 0x50–0x57. Read the entire EEPROM contents using `i2cdump`:

```bash
i2cdump -y 0 0x50 b > eeprom_dump.txt
```

Parse the dumped data for structured formats: many devices store configuration as type-length-value (TLV) encoded records or JSON blobs. Search for human-readable strings indicating key labels (`device_cert`, `root_ca`, `oem_secret`), then reverse-engineer the structure by correlating adjacent hexadecimal values with expected field lengths. Configuration mistakes frequently expose sensitive material: unencrypted symmetric keys used for secure boot signature verification, API tokens for cloud IAM services, and even hardcoded cryptographic seeds used to derive per-device identity keys.

Advance to invasive memory extraction from secure elements and TPM chips. These devices employ cryptographic boundaries preventing external readout of private key storage: secure elements lock data slots with access policies that permit cryptographic operations (signing, decryption) but prohibit direct key export, while TPM chips protect key objects through authorization hierarchies and encrypted blobs. However, physical attacks circumvent these software protections by directly accessing silicon memory arrays.

The first invasive technique is JTAG boundary-scan extraction. ARM-based secure elements often retain JTAG interfaces for manufacturing test and debug; disabling these interfaces requires blowing OTP fuses that vendors neglect to program. Locate JTAG test points on the PCB—signals include Test Clock (TCK), Test Mode Select (TMS), Test Data In (TDI), Test Data Out (TDO), and optionally Test Reset (TRST). Connect your JTAG adapter (e.g., Segger J-Link, Black Magic Probe) to these signals and launch OpenOCD to enumerate the scan chain:

```bash
openocd -f interface/jlink.cfg -f target/at91sam7x.cfg
```

If the JTAG interface is active, OpenOCD reports detected TAPs (Test Access Ports) and CPU core identifiers. Issue a system reset halt to stop code execution at the first instruction fetch, then dump the internal SRAM and flash memory:

```bash
telnet localhost 4444
> reset halt
> dump_image sram.bin 0x20000000 0x10000
> dump_image flash.bin 0x00000000 0x40000
```

The dumped SRAM may contain plaintext cryptographic keys loaded from secure storage during boot initialization, while flash dumps expose firmware logic that reveals key-derivation algorithms. Disassemble the firmware with `radare2` to trace key-handling code paths:

```bash
r2 -a arm -b 32 flash.bin
[0x00000000]> aaa
[0x00000000]> afl
```

Search for cryptographic library calls (AES, SHA256, HMAC functions) and backtrace to callers that populate key buffers. Set breakpoints on these functions using GDB's remote debugging capability—OpenOCD exposes a GDB server on port 3333—and inspect register contents and stack frames during live execution:

```bash
gdb-multiarch
(gdb) target remote localhost:3333
(gdb) break *0x00001234
(gdb) continue
(gdb) x/32xw $sp
```

When execution halts at the breakpoint, examine memory regions pointed to by register arguments (R0-R3 on ARM): these buffers contain plaintext keys, nonces, and intermediate HMAC states. Copy these values from GDB's memory examination output into a hex editor and reconstruct the full cryptographic key by correlating fragment offsets with the algorithm's internal state layout.

For secure elements with JTAG debug permanently disabled, escalate to fault injection attacks targeting the cryptographic state machine. Voltage glitching induces momentary computational errors that skip authentication checks or corrupt comparison operations. Construct a glitching harness by connecting a high-speed MOSFET switch between the secure element's supply voltage pin and ground, controlled by a GPIO output from an FPGA or microcontroller. The glitch generator asserts a 10-nanosecond low pulse on the supply rail at a precise moment during command processing—typically coinciding with an authentication comparison or signature verification instruction.

Trigger glitches synchronously with I2C command transmission: initiate a CheckMac command over I2C while your glitch controller monitors the SCL line. When the CheckMac command reaches its internal comparison stage (identifiable through iterative experimentation and side-channel analysis of power consumption), inject the voltage glitch. A successful fault causes the comparison to evaluate incorrectly, returning success despite an invalid MAC. Repeat this process 10,000–100,000 times with varying glitch timings and widths, recording successful authentication bypasses. Statistical analysis of successful glitch parameters reveals the instruction fetch timing and vulnerability windows.

Document all memory dumps and extracted keys with cryptographic provenance: record the extraction method (JTAG, SPI flash, glitch), storage location (EEPROM offset, SRAM address), and intended purpose (signing key, encryption key, attestation seed). Verify extracted keys by performing cryptographic operations with them: sign a test payload using an extracted private key and validate the signature against the device's public certificate. Successful validation confirms complete compromise of the hardware IAM boundary.

## Exercise 3: Fault Simulation & Exploit Verification

Transitioning from passive reconnaissance to active exploitation, this exercise synthesizes signal capture, firmware analysis, and fault injection into reproducible attacks against hardware IAM implementations. The objective is to demonstrate practical bypasses of authentication state machines, cloning of cryptographic identity, and persistence of backdoor access through bootloader modification.

Select a specific IAM failure mode to target: bypassing secure boot verification, extracting platform attestation keys from a TPM, or cloning a FIDO2 authenticator token. Each scenario demands a tailored exploitation workflow combining hardware manipulation, cryptographic analysis, and software reverse engineering.

**Scenario 1: Secure Boot Bypass via Bootloader Modification.** Secure boot chains anchor device identity by cryptographically verifying each boot stage: the SoC's immutable ROM code verifies the first-stage bootloader (FSBL) against a public key hash burned into OTP fuses, the FSBL verifies the second-stage bootloader (SSBL or U-Boot), and the bootloader verifies the Linux kernel and device tree. Compromising this chain allows persistent backdoor installation that survives firmware updates and factory resets.

Extract the SPI flash firmware image as detailed in Exercise 2. Parse the bootloader with binwalk to identify U-Boot or proprietary bootloader images. Disassemble the bootloader binary with `radare2` to locate the signature verification function—search for calls to cryptographic primitives like RSA-PSS verification or ECDSA-P256 signature checking. ARM bootloaders typically invoke Mbed TLS or OpenSSL library functions; identify these by searching for string references to error messages like "signature verification failed" or "invalid public key":

```bash
r2 -a arm -b 32 uboot_stage2.bin
[0x00000000]> iz
[0x00000000]> axt str.signature_verification_failed
```

The cross-references reveal the verification function's address. Analyze the function's logic: it reads the next boot stage from flash, computes a SHA256 hash digest, and verifies the signature using the public key embedded in the bootloader's data section. Bypass this verification by patching the conditional branch that follows the signature check. In ARM assembly, successful verification typically proceeds with a branch-if-equal (BEQ) after comparing the signature verification result to zero; invert this to branch-if-not-equal (BNE) or replace the entire branch with a no-operation (NOP) slide:

```assembly
; Original code
CMP     R0, #0          ; Compare verification result to zero
BEQ     boot_next_stage ; Branch if equal (success)
B       fail_handler    ; Branch to failure handler

; Patched code
CMP     R0, #0
NOP                     ; Replaced BEQ with NOP
B       boot_next_stage ; Unconditional branch to success path
```

Apply the patch using a hex editor or `radare2`'s write commands:

```bash
[0x00001234]> wa nop
[0x00001234]> wa b 0x00001250
```

Write the modified bootloader back to SPI flash using `flashrom`:

```bash
flashrom -p ft2232_spi:type=232H,port=A --write uboot_patched.bin
```

Reconnect the target device and power it on while monitoring the UART console. The patched bootloader skips signature verification and boots an unsigned kernel, confirming successful secure boot bypass. To weaponize this, replace the kernel image with a backdoored variant containing a persistent reverse shell or credential harvester. The backdoored firmware survives reboot and appears legitimate to software-level integrity checks that rely on the compromised bootloader's attestation.

**Scenario 2: TPM Platform Configuration Register (PCR) Replay Attack.** TPM-based attestation verifies system integrity by measuring boot components into PCRs—20 or 24 hardware-enforced registers that accumulate cryptographic hashes via extend operations. A remote verifier challenges the platform to sign its PCR values with an attestation identity key (AIK), proving the boot chain's integrity. Defeat this by capturing legitimate PCR values during a known-good boot, then replaying them during a compromised boot with modified firmware.

Instrument the LPC bus during a legitimate boot sequence, capturing TPM2_PCR_Extend commands as detailed in Exercise 1. Each extend operation updates a PCR via the formula `PCR_new = HASH(PCR_old || data)`, where `data` is the measured boot component (bootloader hash, kernel hash, configuration). Record the sequence of extend operations: PCR 0 measures the firmware, PCR 1 measures firmware configuration, PCR 4 measures the bootloader, and PCR 8-9 measure the kernel and initramfs.

Modify the target firmware to include a backdoor, then boot the system while intercepting LPC traffic. The modified firmware causes the TPM to compute different PCR values, failing remote attestation. To defeat this, interpose a hardware proxy between the TPM and the host processor. Construct the proxy using an FPGA (e.g., Lattice iCE40, Xilinx Spartan) or a fast microcontroller (STM32H7 at 480 MHz) capable of real-time LPC protocol translation. Connect the proxy's LPC master interface to the host processor's LPC bus and the proxy's slave interface to the TPM.

Program the proxy to intercept TPM2_PCR_Extend commands. When the backdoored bootloader extends PCR 4 with its compromised hash, replace the data field with the original bootloader's hash captured during the legitimate boot. The proxy maintains a lookup table mapping PCR indices to pre-recorded legitimate measurement values, substituting these into extend commands before forwarding them to the TPM:

```c
// Simplified LPC proxy logic
if (lpc_command == TPM2_PCR_Extend && pcr_index == 4) {
    // Replace actual measurement with known-good value
    memcpy(lpc_data_buffer, legitimate_pcr4_measurement, 32);
}
forward_to_tpm(lpc_command, lpc_data_buffer);
```

The TPM computes PCR values using the substituted measurements, generating attestation signatures over "clean" PCR states despite executing compromised firmware. Remote verifiers accept the replayed PCR values as proof of integrity, unaware of the hardware interposition attack. This technique demonstrates the fragility of TPM attestation against adversaries with physical access: the cryptographic root of trust resides in the TPM silicon, but the measurement data path remains vulnerable to interception.

**Scenario 3: FIDO2 Authenticator Cloning via Secure Element Extraction.** FIDO2 hardware authenticators store per-service credential private keys in secure element data slots, generating cryptographic signatures to prove user presence without transmitting passwords. Clone an authenticator by extracting its private keys and resident credential metadata, then programming a second device with identical key material.

Target a commercially available FIDO2 token based on a Microchip ATECC608 secure element—common in low-cost USB security keys. Disassemble the token's enclosure to access the PCB, then identify the ATECC608 chip (8-pin SOIC package). Desolder the chip using hot-air rework at 350°C, exercising caution to avoid thermal damage to adjacent components. Mount the extracted chip on a SOIC-8 breakout board for bench-top analysis.

Connect the breakout board to your I2C master interface (FT232H or Raspberry Pi GPIO) and power the chip with 3.3V. Issue an ATECC608 Info command (opcode 0x30) to read the device's configuration zone and data slot lock status:

```bash
# Using cryptoauthtools Python library
from cryptoauthlib import *
device = atcab_init()
config_data = bytearray(128)
atcab_read_config_zone(config_data)
print(config_data.hex())
```

Parse the configuration data to identify unlocked slots and their read/write policies. Slots configured with `ReadKey` permissions allow retrieval of stored keys after authentication with a separate key—a common misconfiguration in development tokens that persists into production. Attempt to read each data slot sequentially:

```python
for slot in range(16):
    try:
        key_data = bytearray(32)
        atcab_read_zone(ATCA_ZONE_DATA, slot, 0, 0, key_data, 32)
        print(f"Slot {slot}: {key_data.hex()}")
    except:
        print(f"Slot {slot}: Read protected")
```

Successfully extracted keys represent ECDSA-P256 or Ed25519 private keys for FIDO2 credentials. Correlate these keys with resident credential metadata stored in adjacent slots: credential IDs (random 32-byte identifiers), relying party IDs (domain names like `github.com`), and user handles. Reconstruct the full credential structure in a JSON document:

```json
{
  "credentials": [
    {
      "rpId": "github.com",
      "credentialId": "a3f8b2...",
      "privateKey": "d4e5f6...",
      "userHandle": "user123"
    }
  ]
}
```

Program a second ATECC608 chip with the extracted key material using the CryptoAuthLib provisioning commands. Write the private keys into corresponding data slots, replicate the configuration zone lock status, and set slot policies to match the original device. The cloned authenticator responds identically to FIDO2 challenges, enabling session hijacking and persistent access to the victim's accounts.

Validate the clone by performing a FIDO2 authentication ceremony. Connect the cloned token to a host and navigate to a registered website (e.g., GitHub, Google accounts). The web application's JavaScript invokes the WebAuthn API, sending an authentication challenge to the token. The token signs the challenge with the extracted private key and returns the assertion response. The server verifies the signature against the credential's public key (enrolled during registration) and grants access, completing the impersonation attack.

## Hardware Security Checklist & Diagnostic Cheat Sheet

Consolidate your penetration testing methodology into a reusable verification protocol. This checklist enumerates common hardware IAM vulnerabilities and their diagnostic procedures, enabling systematic evaluation of new targets.

**Physical Access Control:**  
Verify that cryptographic components (TPMs, secure elements) are located on internal PCBs inaccessible without breaking tamper-evident seals. Check for exposed JTAG test points, unpopulated header footprints adjacent to secure components, and PCB silkscreen labels indicating debug interfaces. Use a multimeter continuity test to confirm that unused debug pins are tied to ground or supply rails, preventing external connection.

**Secure Boot Integrity:**  
Extract and disassemble the bootloader firmware. Locate signature verification functions and confirm they use industry-standard algorithms (RSA-PSS-2048 or ECDSA-P256). Verify that public keys are stored in OTP fuses rather than rewritable flash; consult the SoC datasheet for OTP memory map locations and read these values via JTAG or vendor-specific programming interfaces. Attempt to flash modified bootloaders and confirm that the ROM bootloader rejects unsigned or incorrectly signed images.

**TPM Configuration and Provisioning:**  
Read TPM NV indices using `tpm2-tools` to enumerate provisioned keys and policies:

```bash
tpm2_nvreadpublic
tpm2_getcap properties-variable
```

Confirm that the endorsement hierarchy is provisioned with a manufacturer-issued EK certificate and that the platform hierarchy is password-protected. Verify that PCR banks use SHA256 or stronger hash algorithms and that critical PCRs (0, 1, 4, 7) are extended during boot. Test physical presence enforcement by attempting TPM2_Clear without asserting the hardware PP signal; the operation should fail with authorization error 0x98E.

**I2C/SPI Bus Security:**  
Probe I2C and SPI buses with a logic analyzer during system boot and runtime operation. Confirm that cryptographic commands (key generation, signature, decryption) do not emit plaintext key material on the bus. Verify that secure elements implement command-response timeouts; test by holding SDA or SCL low during a command and confirming the device returns an error rather than hanging indefinitely. Check for clock glitching resilience by injecting extra clock edges during data transmission and observing error handling behavior.

**Secure Element Configuration Locking:**  
For CryptoAuthentication devices, read the lock status of configuration and data zones using Info commands:

```python
lock_config = bytearray(4)
atcab_info_lock_stat(lock_config)
if lock_config[2] == 0x00:
    print("Configuration zone UNLOCKED - device misconfigured")
else:
    print("Configuration zone LOCKED")
```

Unlocked zones permit reconfiguration of slot access policies, enabling attackers to downgrade security settings. Verify that all production devices ship with zones locked and that slot policies restrict key export.

**Firmware Update Authentication:**  
Analyze over-the-air (OTA) firmware update mechanisms. Capture update packets using Wireshark or logic analyzer traffic dumps. Verify that firmware images are signed with asymmetric cryptography and that public keys are stored in immutable storage. Attempt to flash unsigned or incorrectly signed firmware and confirm rejection by the bootloader. Test rollback protection by attempting to install an older firmware version; robust implementations maintain a monotonic counter in OTP or TPM NV storage that prevents version downgrade attacks.

**Side-Channel Leakage:**  
Perform differential power analysis (DPA) on cryptographic operations. Connect a current sense resistor (0.1–1 ohm) in series with the secure element's supply voltage and measure voltage drop across the resistor with a high-bandwidth oscilloscope (at least 1 GHz bandwidth, 5 GS/s sample rate). Trigger acquisitions synchronously with I2C command transmission and average 10,000 traces per operation. Apply correlation power analysis (CPA) to recover AES key bytes by correlating measured power consumption with Hamming-weight models of intermediate cipher states. Successful key recovery indicates inadequate DPA countermeasures (e.g., missing algorithmic masking or power randomization).

**Diagnostic Command Reference:**  
Compile a quick-reference table for common bus interrogation and memory extraction commands:

| Operation | Tool | Command |
|-----------|------|---------|
| Enumerate I2C devices | i2c-tools | `i2cdetect -y 0` |
| Dump I2C EEPROM | i2c-tools | `i2cdump -y 0 0x50 b` |
| Read SPI flash JEDEC ID | flashrom | `flashrom -p ft2232_spi:type=232H --read-id` |
| Extract SPI flash image | flashrom | `flashrom -p ft2232_spi:type=232H --read dump.bin` |
| Scan JTAG chain | OpenOCD | `openocd -f interface/jlink.cfg -c "init; scan_chain; exit"` |
| Dump SRAM via JTAG | OpenOCD | `dump_image sram.bin 0x20000000 0x10000` |
| Capture LPC traffic | sigrok-cli | `sigrok-cli --driver fx2lafw --channels 0=LCLK,1-4=LAD --protocol-decoders lpc` |
| Disassemble ARM firmware | radare2 | `r2 -a arm -b 32 firmware.bin; aaa; pdf @main` |
| Debug via GDB remote | gdb-multiarch | `target remote localhost:3333; break *0x1000; continue` |

Maintain a laboratory notebook documenting each target's physical layout, pinouts, bus protocol parameters, and observed vulnerabilities. Photograph PCBs with high-resolution macro lenses, annotate component locations in image editing software, and archive signal captures with detailed metadata (sample rate, trigger conditions, decoded protocol output). Reproducibility distinguishes professional penetration testing from ad-hoc tinkering: a properly documented hardware IAM assessment enables peer review, client reporting, and knowledge transfer to development teams tasked with remediation.

Execute this verification protocol iteratively: initial reconnaissance identifies attack surface, memory extraction exposes cryptographic material, and fault injection validates exploitability. Successful hardware IAM compromise yields persistent backdoor access, cloned device identities, and extracted root-of-trust secrets—outcomes that underscore the necessity of defense-in-depth strategies combining physical tamper resistance, cryptographic algorithm hardening, and secure provisioning processes anchored in hardware roots of trust that resist physical adversaries.
