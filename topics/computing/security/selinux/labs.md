# Operational Verification Labs: SELinux

## Objective & Lab Bench Setup

SELinux—Security-Enhanced Linux—represents a mandatory access control (MAC) framework enforced directly within the Linux kernel through the Linux Security Module (LSM) interface. Unlike discretionary access control (DAC), where resource owners dictate permissions, SELinux enforces policy decisions based on security contexts assigned to subjects (processes) and objects (files, sockets, ports). Each access decision traverses the kernel's security server, which consults a compiled binary policy to render allow/deny verdicts according to type enforcement rules, role-based access control, and multi-level security constraints.

For the hardware hacker and penetration tester, SELinux verification transcends userspace policy audit. You must instrument the kernel's LSM hook invocation paths, trace policy decision points at the instruction level, and observe how security context transitions propagate through process creation, file system operations, and inter-process communication primitives. This laboratory guide grounds SELinux in physical system state—kernel memory structures, process credentials (`task_struct->cred->security`), inode extended attributes (`security.selinux`), and the policy database loaded into kernel virtual memory at boot.

Your verification bench requires a hardware-instrumented Linux system where you can attach JTAG debuggers to observe kernel execution, UART consoles to capture boot-time policy loading, and logic analyzers to verify that security decisions correlate with observable system behavior at the hardware level. The exercises progress from live runtime inspection of SELinux contexts through invasive memory dumping of policy structures, culminating in fault injection attacks that validate enforcement integrity when kernel memory or policy databases are corrupted.

**Hardware Bench Configuration:**

Establish a dedicated verification workstation running Fedora, CentOS Stream, or RHEL—distributions where SELinux operates in enforcing mode by default. The target device under test (DUT) should be an ARM or x86_64 development board with accessible JTAG pins (20-pin ARM Cortex Debug header or Intel XDP interface), exposed UART TX/RX lines for console access, and a flash storage interface (eMMC, SPI NOR, or SATA SSD) that you can electrically probe or reflash with modified kernels.

Install the core diagnostic suite: `dnf install selinux-policy-devel policycoreutils-python-utils setools-console audit libselinux-utils`. For hardware instrumentation, deploy OpenOCD for JTAG control, Sigrok for protocol analysis, and GDB with multiarch support for kernel-level debugging. Connect a USB logic analyzer (Saleae Logic Pro 16, DSLogic Plus, or equivalent 100+ MHz sampling device) to the DUT's UART, SPI, and GPIO lines. Attach a UART-to-USB bridge (FTDI FT232H, CP2102, or similar) to the primary console at 115200 baud, 8N1 framing. If the DUT uses JTAG debugging, connect an OpenOCD-compatible adapter (J-Link, ST-LINK V3, or Bus Blaster) to the Cortex Debug header, verifying continuity on JTAG TCK, TMS, TDI, TDO, and ground with a multimeter before power-on.

For software-layer verification, compile a custom kernel with `CONFIG_SECURITY_SELINUX_DEVELOP=y` and `CONFIG_SECURITY_SELINUX_BOOTPARAM=y`, enabling permissive boot modes and dynamic policy reloading. Build the kernel with debug symbols (`CONFIG_DEBUG_INFO=y`, `CONFIG_FRAME_POINTER=y`) and disable kernel address space layout randomization (`nokaslr` boot parameter) to ensure reproducible memory layouts during JTAG inspection. Flash this kernel to the DUT's boot partition using `flashrom` if targeting SPI NOR, or `dd` with verified checksums if using eMMC/SD.

Prepare a minimal SELinux policy source tree by extracting the reference policy: `semodule -l > /tmp/modules.txt`, then `semodule -E base -c > /tmp/base.cil`. This Common Intermediate Language (CIL) representation exposes the raw type enforcement rules, role definitions, and security class permissions that the kernel policy engine consults. You will manipulate this policy, recompile it with `secilc`, and observe kernel behavior as policy predicates change.

Position a grounded ESD-safe workmat beneath all hardware. Route power through a current-limited bench supply (3.3V or 5V rails depending on DUT voltage domain) with ammeter inline to detect abnormal current draw during fault injection. Keep a USB-connected flash drive with known-good firmware images and bootloader recovery binaries within arm's reach—corrupted SELinux policy or kernel patches can render systems unbootable, requiring blind reflashing via UART bootstrap or JTAG boundary scan.

## Exercise 1: Live Hardware Probing & Signal Capture

This exercise establishes baseline visibility into SELinux's runtime enforcement by capturing security context transitions and policy lookups as they occur within the running kernel, correlating these events with physical system state observable through hardware instrumentation.

**Objective:** Instrument a live Linux system to capture SELinux security contexts during process execution and file access, then verify that these contexts propagate correctly through kernel data structures by inspecting process credentials and inode extended attributes via JTAG memory reads and UART console output.

Begin with the DUT booted into enforcing mode. Confirm SELinux status by executing `sestatus` at the console, which should report `SELinux status: enabled` and `Current mode: enforcing`. Verify the loaded policy with `seinfo --stats`, noting the number of types, classes, and allow rules compiled into the binary policy. This establishes the enforcement surface.

Now launch a privilege-separated service with a confined SELinux domain. Apache HTTP Server (`httpd`) serves as an ideal target: its daemon runs under the `httpd_t` type, and its content files reside in contexts like `httpd_sys_content_t`. Start the service with `systemctl start httpd`, then immediately query its security context: `ps -eZ | grep httpd`. The output displays the full context tuple `system_u:system_r:httpd_t:s0`, where `system_u` denotes the SELinux user, `system_r` the role, `httpd_t` the type (the primary enforcement dimension), and `s0` the MLS/MCS sensitivity level.

To observe context propagation at the hardware level, attach GDB to the running kernel via JTAG. Halt the processor, then navigate to the `httpd` process's `task_struct` in kernel memory. First, resolve the kernel virtual address of the target PID by reading `/proc/<pid>/stack` to identify a kernel function within the process's call stack, then use `crash` utility or manual JTAG commands to traverse the task list. The `task_struct` embeds a pointer to a `cred` structure at offset (architecture-dependent, typically `task_struct + 0x5c0` on x86_64). Within `cred`, locate the `security` field—a void pointer to the SELinux-specific `task_security_struct`, which contains the process's `sid` (security identifier, a 32-bit integer indexing the policy's context database).

Dump 64 bytes from the `task_security_struct` address using JTAG: `mon mdw <address> 16`. Cross-reference the `sid` value against the kernel's runtime SID table by setting a breakpoint at `security_compute_av` (the policy decision function) and capturing the `ssid` (source SID) and `tsid` (target SID) arguments during an `httpd` file access. Use `perf probe` to dynamically instrument this function if JTAG halting disrupts service operation: `perf probe 'security_compute_av ssid tsid tclass'`, then `perf record -e probe:security_compute_av -a` while triggering an HTTP request with `curl http://localhost/index.html`.

Simultaneously, capture UART console output with Sigrok. Connect the logic analyzer's channels: CH0 to UART TX, CH1 to UART RX, with ground reference. Launch `sigrok-cli --driver fx2lafw --config samplerate=24M --channels 0-1 --protocol-decoders uart:baudrate=115200 --protocol-decoder-annotations uart=rx-data --continuous`. Enable SELinux audit logging in permissive mode temporarily (`setenforce 0`, then `auditctl -w /var/www/html -p r`) to generate verbose AVC (Access Vector Cache) messages without blocking accesses. Trigger another `curl` request and observe the Sigrok UART decoder output synchronize with kernel log emissions: `avc: granted { read } for pid=1234 comm="httpd" name="index.html" dev="sda1" ino=56789 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:httpd_sys_content_t:s0 tclass=file`.

Now verify that file security contexts persist in on-disk extended attributes. Halt the DUT and extract the root filesystem image. If the storage is eMMC accessible via an SD card reader, remove the module and mount it on your workstation. If SPI NOR flash, use `flashrom -p ft2232_spi:type=232H -r rootfs.bin`, then extract with `binwalk -e rootfs.bin` and mount the resulting filesystem image. Navigate to `/var/www/html` and inspect `index.html`'s extended attributes: `getfattr -n security.selinux index.html`. The output—`system_u:object_r:httpd_sys_content_t:s0`—must match the `tcontext` observed in the live AVC log, confirming that the kernel's in-memory inode cache and on-disk storage maintain coherent security labels.

For deeper hardware correlation, attach the logic analyzer to the DUT's eMMC or SPI data lines during a file read. Configure Sigrok with the appropriate protocol decoder: `sigrok-cli --driver fx2lafw --config samplerate=100M --channels 0-7 --protocol-decoders spi:clk=0:mosi=1:miso=2:cs=3` for SPI, capturing the raw read transaction when `httpd` accesses `index.html`. Cross-reference the captured flash address offsets with the filesystem's inode table (use `debugfs` or `dumpe2fs` on the extracted image to map inode 56789 to physical blocks), verifying that the extended attribute block read precedes the file data read. This demonstrates that SELinux context lookups propagate from persistent storage through kernel page cache to enforcement decisions in the security server, all observable through the hardware layer.

**Verification Checklist:**

- UART console logs display AVC messages correlating with user-triggered file accesses.
- JTAG memory inspection reveals `task_struct->cred->security` pointing to valid `task_security_struct` with non-zero SID.
- Extended attribute reads via `getfattr` match `tcontext` fields in AVC logs.
- Sigrok protocol decoder output captures filesystem read transactions preceding security context checks.

## Exercise 2: Bus Sniffing, Register Inspection & Memory Dumping

This exercise escalates instrumentation to invasive inspection of the SELinux policy database in kernel memory, reverse-engineering the compiled policy format, and correlating binary policy structures with enforcement decisions captured at the hardware bus level.

**Objective:** Dump the kernel's runtime SELinux policy database via JTAG, disassemble its internal data structures (policydb tables, security classes, access vectors), inject a modified policy to alter enforcement rules, and verify the changes through both userspace tooling and hardware-level memory snapshots.

SELinux policy resides in kernel memory as a `policydb` structure, managed by the security server (`security/selinux/ss/policydb.c` in the kernel source). This structure contains hash tables mapping type identifiers to `type_datum` records, role definitions to `role_datum` objects, and precomputed access vectors in a sparse matrix indexed by source type, target type, and security class. To locate this structure, compile the kernel with debug symbols and extract its address from `System.map` or `/proc/kallsyms`: `grep policydb /proc/kallsyms`. Note the address of the global `policydb` symbol—typically in the kernel's data segment, e.g., `ffffffff82a00000` on x86_64.

Halt the DUT via JTAG and dump a 1 MB region surrounding the `policydb` address: `mon mdw 0xffffffff82a00000 0x100000`. Save this memory snapshot to a file using GDB's `dump memory policydb.bin 0xffffffff82a00000 0xffffffff82b00000`. Transfer the binary dump to your analysis workstation.

Parse the policy database by cross-referencing kernel source definitions. The `policydb` structure begins with a `symtab` array containing symbol tables for types, roles, users, booleans, and classes. Each `symtab` entry is a hash table (`hashtab_t`) with buckets pointing to linked lists of `hashtab_node` structures. The `type_datum` records embedded in these nodes contain the string name of each type (e.g., `httpd_t`, `httpd_sys_content_t`) and associated attribute bitmasks. Use a custom Python script leveraging `ctypes` to walk these structures, or employ `radare2` for interactive disassembly: `r2 -b 64 policydb.bin`, then define the `policydb` struct layout with `pf` commands and navigate pointer chains with `px` and `ps`.

Focus on the `te_avtab` (type enforcement access vector table), a critical structure storing allow/deny rules. Each entry in `te_avtab` is a `avtab_node` containing source type, target type, security class, and allowed permissions as a bitmask. Iterate through the table by following the bucket array and linked list pointers, extracting tuples. For example, locate the rule permitting `httpd_t` to read `httpd_sys_content_t` files: search for a `(httpd_t, httpd_sys_content_t, file, {read getattr open})` entry. The `read` permission corresponds to bit 2 in the `file` class permission bitmask (refer to `security/selinux/include/classmap.h` in kernel source). Confirm that this bit is set in the dumped `avtab_node->datum.data` field.

Now inject a policy modification. Using `semodule` or direct CIL compilation, craft a new policy rule that denies `httpd_t` the `write` permission on `httpd_sys_rw_content_t` (writable content type). Compile the policy with `secilc`, load it into the kernel with `semodule -i custom.cil`, then immediately halt via JTAG before the policy cache stabilizes. Dump the `policydb` region again, compare the new snapshot against the baseline, and identify the altered `avtab_node`. Specifically, locate the entry for `(httpd_t, httpd_sys_rw_content_t, file)` and verify that the `write` permission bit (bit 3) has been cleared in the permissions bitmask.

To correlate policy changes with enforcement, trigger a write attempt from the `httpd` process while capturing kernel memory states. Configure Apache to write logs to a directory labeled `httpd_sys_rw_content_t`. Before the policy change, `echo "test" > /var/log/httpd/test.log` via a CGI script should succeed. After injecting the deny rule and reloading policy, repeat the write attempt. Use `perf probe` to capture the `security_compute_av` function's return value: `perf probe 'security_compute_av%return $retval'`, then `perf record -e probe:security_compute_av -a` during the write. The return value should transition from `0` (success, all requested permissions granted) to a non-zero error code (permissions denied).

Simultaneously, attach the logic analyzer to the DUT's system bus if accessible (x86 platforms with PCH debug headers, or ARM SoCs with AXI bus probes). Configure Sigrok to decode memory transactions: ARM CoreSight ETM (Embedded Trace Macrocell) streams or Intel Processor Trace (PT) captured via JTAG can reconstruct instruction-level execution flow. Set a trigger on memory reads to the `policydb->te_avtab` address range, capturing the exact moment the security server consults the modified rule. Cross-reference the captured bus addresses with the `avtab_node` offsets extracted from your memory dump, confirming that the deny decision corresponds to reading the altered permission bitmask from kernel memory.

For deeper validation, use `openocd` to single-step the kernel through `security_compute_av`. Configure OpenOCD with your JTAG adapter: `openocd -f interface/jlink.cfg -f target/stm32f4x.cfg` (adjust target config for your DUT's SoC). Connect via GDB: `gdb-multiarch vmlinux`, then `target remote localhost:3333`. Set a breakpoint at `security_compute_av+0x40` (adjust offset to the `avtab_search` call site identified via `objdump -d vmlinux | grep security_compute_av`). Continue execution until the breakpoint hits during the write attempt, then inspect CPU registers to observe the source SID (`httpd_t`), target SID (`httpd_sys_rw_content_t`), and security class (`file`) being passed to the policy lookup. Step through the `avtab_search` function, watching the hashtable traversal in CPU registers and memory accesses on the logic analyzer, until the function returns the deny verdict.

Finally, validate on-disk policy persistence. After a policy reload, the kernel writes the compiled binary policy to `/sys/fs/selinux/load` (or reads from `/etc/selinux/targeted/policy/policy.XX`). Extract this file from the DUT: `scp root@dut:/etc/selinux/targeted/policy/policy.33 .`. Parse it with `sedispol`: `sedispol policy.33 list avtab | grep httpd_t | grep httpd_sys_rw_content_t`, confirming that the deny rule appears in the persistent policy database. If targeting flash storage, capture the write transaction with Sigrok on the SPI or eMMC bus, decoding the sector addresses and verifying that the policy file's inode update precedes the enforcement change observed in kernel memory.

**Verification Checklist:**

- JTAG memory dump of `policydb` reveals hash tables and `avtab_node` structures with valid type/role/class identifiers.
- Modified policy rule (injected via `semodule`) appears in memory dump with altered permission bitmask.
- `perf probe` return values from `security_compute_av` transition from success to denial after policy reload.
- Logic analyzer captures bus transactions reading from `te_avtab` address range during enforcement decisions.
- On-disk policy file (parsed with `sedispol`) matches in-memory `policydb` contents.

## Exercise 3: Fault Simulation & Exploit Verification

This exercise validates SELinux's resilience against memory corruption and policy tampering by injecting faults into kernel memory, deliberately corrupting policy data structures, and observing whether enforcement degrades or the kernel detects integrity violations.

**Objective:** Corrupt the kernel's `policydb` structure via JTAG memory writes, inject malicious policy rules through direct memory patching, and verify whether SELinux enforcement fails open (permitting unauthorized accesses) or the kernel's integrity checks trigger panics or policy reloads.

SELinux lacks cryptographic integrity validation of its runtime policy database—once loaded into kernel memory, the `policydb` structure relies on kernel memory protection (read-only page mappings, SMAP/SMEP) rather than checksums or signatures. This design decision prioritizes performance (policy lookups occur on every system call involving LSM hooks) but exposes enforcement to memory corruption vulnerabilities. Kernel bugs like buffer overflows or use-after-free flaws in device drivers or network subsystems could theoretically allow an attacker to overwrite `avtab_node` permission bitmasks, silently disabling enforcement rules.

Begin by identifying a target enforcement rule to corrupt. Using the previous exercise's memory dump, locate the `avtab_node` for `(unconfined_t, shadow_t, file, {read})`, which prevents unconfined processes from directly reading `/etc/shadow`. Note the kernel virtual address of this node's `datum.data` field (the permission bitmask). This address should reside in kernel data pages marked writable during policy initialization but potentially locked read-only afterward via `virt_to_page()->flags &= ~PG_writable`.

Check page permissions via JTAG. Halt the kernel, read the `policydb` region's page table entries by traversing the four-level page table from `CR3` (x86_64) or `TTBR0` (ARM64). Use `mon mdw <PML4_address>` to dump the PML4 entry for the virtual address, follow the pointer chain through PDPT, PD, and PT, and inspect the final PTE's permission bits. If the `W` (writable) bit is set, you can directly modify the policy via JTAG memory writes. If cleared, you must first corrupt the PTE to restore write permissions—a realistic attack scenario if exploiting a kernel write-what-where primitive.

Inject the fault: using GDB over JTAG, write a new bitmask to the `datum.data` field that adds `write` permission to the unconfined-to-shadow rule. The original bitmask permits only `read` (bit 2), so write a value with bits 2 and 3 set: `set *(uint32_t *)0xffffffff82a12345 = 0x0000000C` (adjust address and bitmask value to match your dump). Resume kernel execution with `continue`, then attempt an operation previously denied: `echo "malicious" >> /etc/shadow` as an unconfined user. If SELinux enforcement fails open, the write succeeds without an AVC denial. Confirm by checking `/var/log/audit/audit.log` for the absence of a deny message and verifying the file modification: `tail /etc/shadow`.

To validate that the corruption persisted, re-halt the kernel via JTAG and dump the `avtab_node` again. The `datum.data` field should still reflect the injected bitmask. Cross-reference with a Sigrok bus capture: trigger the `/etc/shadow` write while the logic analyzer monitors memory bus transactions, confirming that the `security_compute_av` function reads the corrupted permission bitmask from the altered address. The bus capture should show a memory read to `0xffffffff82a12345` returning the injected value `0x0000000C`, followed by the kernel permitting the write without invoking denial logic.

Now test kernel integrity checks. SELinux itself does not validate `policydb` checksums, but the kernel's memory subsystem may detect corruption if you overwrite page metadata or linked list pointers. Deliberately corrupt a `hashtab_node` next pointer in the `policydb->symtab[SYM_TYPES]` hash table: set it to an invalid address like `0xdeadbeef`. Resume execution and trigger a policy lookup involving that type (e.g., `ls -Z /var/www/html`). The kernel should experience a page fault or null pointer dereference when traversing the corrupted linked list, triggering a kernel oops or panic. Capture the panic message via UART and correlate the faulting instruction pointer with the `hashtab_search` function in `security/selinux/ss/hashtab.c`.

For a more sophisticated attack simulation, inject a complete rogue `avtab_node` into the policy. Allocate a memory region within the kernel's heap using JTAG (search for a free slab cache block via `/proc/slabinfo` and GDB inspection of `kmem_cache` structures), write a fabricated `avtab_node` with arbitrary source/target SIDs and a permissive bitmask (`0xFFFFFFFF` granting all permissions), then splice it into the `te_avtab` bucket linked list by overwriting a legitimate node's `next` pointer. Resume execution and verify that the rogue rule becomes active: create a process with an unusual context combination that should be denied (e.g., `chcon -t user_t /tmp/malicious`, then `runcon -t user_t -r user_r /tmp/malicious`), and observe whether the fabricated rule permits operations that the original policy forbids.

Finally, test policy reload resilience. Trigger a policy reload while the kernel is mid-execution: `load_policy -q /etc/selinux/targeted/policy/policy.33` during a high-throughput workload (e.g., `ab -n 10000 -c 100 http://localhost/`). Use JTAG to observe the `selinux_load_policy` function, setting breakpoints at the memory allocation sites for the new `policydb` and the deallocation of the old one. Confirm that the kernel swaps policies atomically via RCU (read-copy-update) synchronization: the old `policydb` pointer remains valid until all CPUs complete grace periods (`synchronize_rcu()` call site). Corrupt the new policy during the reload window—after allocation but before the pointer swap—by halting at the `policydb_load_isids` function and modifying initial SID assignments. Observe whether the corruption propagates to the active policy or the kernel detects the anomaly and aborts the reload.

**Verification Checklist:**

- Direct JTAG memory write to `avtab_node` permission bitmask permits previously denied operations without AVC logs.
- Sigrok bus capture shows `security_compute_av` reading corrupted bitmask value from targeted memory address.
- Corrupting hash table pointers triggers kernel oops/panic with instruction pointer in `hashtab_search`.
- Injected rogue `avtab_node` enables enforcement bypass for arbitrary context pairs.
- Policy reload during high load completes atomically or detects mid-reload corruption and aborts.

## Hardware Security Checklist & Diagnostic Cheat Sheet

**Pre-Operation Hardware Validation:**

Before initiating any SELinux verification exercise, perform electrical continuity checks on all instrumentation connections. Use a multimeter to verify ground continuity between the logic analyzer's ground clip, UART bridge ground, JTAG adapter ground, and the DUT's ground plane—resistance should measure below 1 ohm. Confirm JTAG signal integrity by probing TCK with an oscilloscope: the clock should exhibit clean square waves at the configured frequency (typically 1-10 MHz) with rise/fall times under 10 nanoseconds and no ringing or reflections. If JTAG communication fails, reduce the adapter's clock speed (`adapter speed 1000` in OpenOCD) and verify pull-up resistors on TMS and TDI lines (10kΩ to VCC).

Test UART console capture by transmitting a known pattern from the DUT: `echo "TEST_PATTERN_12345" > /dev/console`, then confirm Sigrok decodes the ASCII string correctly. If characters are garbled, verify baud rate matching (115200 is standard, but some embedded boards use 57600 or 921600), check for correct bit order (LSB-first is default for UART), and ensure the logic analyzer's sampling rate is at least 10× the baud rate (2.4 Msps minimum for 115200 baud).

**Runtime SELinux State Interrogation Commands:**

- **Policy Version and Statistics:** `sestatus -v` reports the policy version loaded at boot (typically version 33 for recent kernels), the policy store path, and the mode (enforcing, permissive, disabled). `seinfo --stats` enumerates type counts, role counts, and total allow rules. For detailed rule inspection, `sesearch --allow -s httpd_t -t httpd_sys_content_t -c file` queries specific type enforcement rules.

- **Context Verification:** `ls -Z /path/to/file` displays the file's security context. `ps -eZ` lists all processes with their contexts. `id -Z` shows the current shell's context. `secon -t` extracts just the type component from a context string, useful for scripting.

- **AVC Log Filtering:** `ausearch -m avc -ts recent` queries the audit log for recent AVC denials. `audit2allow -a` converts denials into policy allow rules (useful for debugging but dangerous in production—never blindly apply generated rules). `sealert -a /var/log/audit/audit.log` provides human-readable denial summaries.

- **Boolean Toggles:** `getsebool -a` lists all policy booleans and their states. `setsebool -P httpd_can_network_connect on` persistently enables a boolean, altering enforcement without recompiling policy.

**JTAG Memory Inspection Procedures:**

- **Kernel Symbol Resolution:** Extract kernel virtual addresses from `/proc/kallsyms` or `System.map`. If KASLR is enabled, calculate the runtime offset by comparing a known symbol's expected address (from `System.map`) against its runtime address in `/proc/kallsyms`, then apply this delta to all target addresses.

- **Structure Traversal:** For pointer-heavy data structures like linked lists or hash tables, dump 64-128 bytes per node to ensure you capture the full structure and the `next` pointer. Use `offsetof()` calculations from kernel source headers to navigate fields: e.g., `task_struct->cred` is at offset `0x5c0` on x86_64 kernel 5.15.

- **Watchpoint Setup:** GDB hardware watchpoints trigger on memory access. Set a watchpoint on a specific `avtab_node` address to capture when the security server reads that rule: `watch *(uint32_t *)0xffffffff82a12345`. This halts execution the moment the address is accessed, allowing single-step analysis.

**Sigrok Protocol Decoder Configuration:**

- **UART Decoding:** `sigrok-cli --driver fx2lafw --config samplerate=24M --channels D0=RX --protocol-decoders uart:baudrate=115200:parity=none:data_bits=8:stop_bits=1 --protocol-decoder-annotations uart=rx-data --continuous -o uart.log`

- **SPI Flash Capture:** `sigrok-cli --driver fx2lafw --config samplerate=100M --channels D0=CLK,D1=MOSI,D2=MISO,D3=CS --protocol-decoders spi:clk=D0:mosi=D1:miso=D2:cs=D3 --protocol-decoders spiflash:device=W25Q128 --protocol-decoder-annotations spiflash=cmd,data -o spiflash.log`

- **I2C Bus Sniffing (for EEPROM context storage):** `sigrok-cli --driver fx2lafw --config samplerate=10M --channels D0=SCL,D1=SDA --protocol-decoders i2c:scl=D0:sda=D1 --protocol-decoder-annotations i2c=address-read,data-read -o i2c.log`

**Flashrom Extraction and Verification:**

- **SPI NOR Read:** `flashrom -p ft2232_spi:type=232H -r firmware.bin` dumps the entire flash. Verify integrity with `sha256sum firmware.bin` against a known-good hash. If read fails, reduce SPI clock speed: `flashrom -p ft2232_spi:type=232H,spispeed=1000 -r firmware.bin`.

- **Partial Read for Policy Region:** If the policy resides in a known flash offset (determined via `binwalk` or bootloader analysis), use `flashrom`'s partial read: `flashrom -p ft2232_spi:type=232H -r policy.bin --ifd -i bios` (adjust region name based on flash descriptor).

- **Write Protection Check:** `flashrom -p ft2232_spi:type=232H --wp-status` reports hardware write-protect status. If WP pin is asserted or status register bits are locked, you cannot inject corrupted policy images without physical modification (desoldering the flash, applying voltage to WP# pin, or using chip-off techniques).

**Fault Injection Safety Protocols:**

Before corrupting kernel memory or policy structures, establish a recovery path. Flash a bootable rescue image to a separate partition or external USB drive with a minimal initramfs containing `setenforce 0` and `load_policy` binaries. Configure the bootloader to default to this rescue image after three consecutive failed boots (systemd's automatic reboot-on-panic with `systemd.watchdog-device` and GRUB's `recordfail` counter).

When injecting faults via JTAG, keep the halt duration under 100 milliseconds to prevent watchdog timer resets. If the SoC includes a hardware watchdog, disable it via JTAG register writes before halting: for ARM Cortex-A, clear the WDT enable bit in the SoC's control register (address varies by vendor—consult the TRM). For Intel x86, write to the WDAT (Watchdog Action Table) or TCO (Total Cost of Ownership) watchdog registers via PCH access.

Log all JTAG operations to a timestamped file: `openocd -f openocd.cfg -l jtaglog_$(date +%s).txt`. Cross-reference UART console timestamps with JTAG halt/resume events to reconstruct the sequence of events during fault injection. If the DUT fails to resume after fault injection, perform a full JTAG boundary scan reset: `openocd -c "init; reset halt; reset run; shutdown"`.

**Kernel Panic Analysis:**

When faults trigger kernel panics, capture the full backtrace via UART. The panic message includes the faulting instruction pointer (RIP/PC), the call stack, and register states. Use `addr2line -e vmlinux <RIP_address>` to resolve the faulting function and source line. If the panic occurs in `hashtab_search` or `avtab_search`, confirm that the corrupted pointer dereference matches your injected fault. If the panic is unrelated (e.g., in a network driver or filesystem), the fault may have triggered a cascading failure—inspect the memory dump for collateral damage to adjacent kernel structures.

**Post-Exercise Cleanup:**

After completing verification exercises, restore the DUT to a clean state. Reboot into enforcing mode (`setenforce 1`), verify no lingering permissive domains exist (`semanage permissive -l` should return empty), and confirm audit logs reflect normal enforcement. Clear temporary policy modules: `semodule -r custom_module`. If you injected corrupted policy via direct memory writes, reload the original policy from disk: `load_policy /etc/selinux/targeted/policy/policy.33`.

For hardware instrumentation, power down the DUT before disconnecting JTAG or logic analyzer probes to prevent ESD damage. Store flash dumps and memory snapshots in a version-controlled archive with SHA256 manifests for reproducibility. Label each dump with the kernel version, policy version, and exercise number to enable comparative analysis across multiple verification runs.

This laboratory methodology transforms SELinux from an abstract kernel subsystem into a tangible enforcement mechanism observable through hardware instrumentation, memory forensics, and fault injection. By grounding policy decisions in physical system state—CPU registers, memory bus transactions, flash storage sectors—you gain the operational insight required to audit enforcement integrity, validate security boundaries, and assess resilience against kernel-level attacks. The techniques documented here extend beyond SELinux to any LSM framework, providing a replicable template for hardware-assisted security verification in embedded, cloud, and adversarial environments.
