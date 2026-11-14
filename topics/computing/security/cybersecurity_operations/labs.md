# Operational Verification Labs: Cybersecurity Operations

## Objective & Lab Bench Setup

The hardware security bench is the ground truth of embedded exploitation. Every assumption about a target's runtime behavior, every claim about memory layout or boot sequence, and every hypothesis about a cryptographic check must ultimately be verified against a live silicon surface. This lab guide operationalizes that verification across three progressive exercises: live signal probing of debug interfaces, non-intrusive bus sniffing followed by intrusive memory dumping, and finally JTAG-mediated fault injection to defeat a firmware security check. Every command, configuration file, and procedural step is written to execute on a Debian-based workstation with a USB logic analyzer, an FTDI FT2232H-based JTAG/SPI adapter, and a representative ARM Cortex-M target board (the lab reference is an STM32F4 Discovery, though any Cortex-M with exposed SWD and an external SPI flash will substitute).

Before any probing begins, install the diagnostic suite and verify that every instrument enumerates correctly. The toolchain spans five independent layers: `sigrok-cli` for protocol decoding from logic analyzer captures, `openocd` for JTAG/SWD target control, `flashrom` for direct SPI NOR EEPROM read/write, `binwalk` for firmware image structure analysis, and `radare2` for static disassembly and binary patching. Two supporting instruments—`gdb-multiarch` for live target debugging and `minicom` for serial console interaction—complete the bench.

Run the full environment installation and verification as a single block:

```bash
sudo apt-get update
sudo apt-get install -y sigrok-cli openocd flashrom binwalk radare2 \
  gdb-multiarch minicom telnet libftdi1-2 libftdi-dev python3-pip \
  openocd-data git build-essential pkg-config

# Verify each tool is present and report its version
sigrok-cli --version
openocd --version
