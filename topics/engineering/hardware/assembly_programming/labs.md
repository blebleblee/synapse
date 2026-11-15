# Operational Verification Labs: Assembly Programming

## Objective & Operational Lab Setup

This laboratory curriculum delivers hands-on mastery of assembly language programming across two dominant instruction set architectures: x86-64 (Intel/AMD) and ARM64 (AArch64). The operational objective centers on building fluency in register-level programming, understanding CPU execution pipelines, and developing the diagnostic capability to reverse-engineer compiled binaries. Unlike high-level language abstractions, assembly programming exposes the raw mechanical interface between software and silicon—every instruction maps directly to microarchitectural state transitions, register file updates, and memory bus transactions.

The practitioner will construct complete, bootable assembly programs, dissect their execution through cycle-accurate simulation, and verify correctness against both functional specifications and microarchitectural performance models. This approach bridges the gap between theoretical computer architecture and operational embedded systems engineering, where firmware developers routinely inspect disassembled code, optimize interrupt service routines (ISRs) for latency, and debug hardware bring-up failures at the instruction level.

### Laboratory Hardware and Software Stack

The verification environment requires a Linux-based workstation equipped with native x86-64 execution capability and cross-compilation toolchains for ARM64 targets. The GNU Binutils suite provides the assembler (`as`), linker (`ld`), and disassembler (`objdump`), while the GNU Debugger (`gdb`) enables single-step instruction tracing and register inspection. For ARM64 emulation, QEMU provides cycle-approximate userspace and system-mode virtualization, allowing execution of bare-metal ARM64 binaries on x86-64 host machines without physical hardware.

Install the foundational toolchain on Ubuntu 22.04 LTS or equivalent distributions using the following sequence. The `build-essential` metapackage delivers GCC, Binutils, and Make, while `gcc-aarch64-linux-gnu` provides the ARM64 cross-compiler and assembler. QEMU's ARM system emulator (`qemu-system-aarch64`) and userspace emulator (`qemu-aarch64`) enable both bare-metal firmware testing and Linux userspace AArch64 binary execution respectively.

```bash
sudo apt update
sudo apt install -y build-essential gdb gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu qemu-system-arm qemu-user
```

Verify the x86-64 assembler by invoking `as --version`, which should report GNU assembler version 2.38 or later. Confirm ARM64 cross-assembly capability with `aarch64-linux-gnu-as --version`. Test QEMU ARM64 userspace emulation by executing `qemu-aarch64 --version`, ensuring version 6.2 or newer for robust AArch64 instruction support.

### Register Architecture and Calling Convention Foundations

The x86-64 architecture exposes sixteen 64-bit general-purpose registers (`RAX`, `RBX`, `RCX`, `RDX`, `RSI`, `RDI`, `RBP`, `RSP`, and `R8` through `R15`), alongside the instruction pointer `RIP` and flags register `RFLAGS`. The System V AMD64 ABI, standard across Linux and BSD systems, dictates function argument passing through registers `RDI`, `RSI`, `RDX`, `RCX`, `R8`, and `R9` in sequence, with integer return values placed in `RAX`. The stack grows downward from high memory addresses, and `RBP` traditionally anchors stack frames for local variable access, though modern optimizing compilers often elide frame pointers to free `RBP` as an additional general-purpose register.

ARM64's AArch64 architecture provides thirty-one 64-bit general-purpose registers `X0` through `X30`, plus a dedicated zero register `XZR` that always reads as zero and discards writes. Register `X30` serves as the link register (`LR`), automatically loaded with the return address during `BL` (branch-and-link) instructions. The Procedure Call Standard for the ARM 64-bit Architecture (AAPCS64) passes the first eight integer or pointer arguments through `X0` to `X7`, returning results in `X0` and `X1` for 128-bit values. The stack pointer `SP` must maintain 16-byte alignment at public function interfaces, a constraint enforced by hardware exception generation on misaligned accesses in certain execution states.

Both architectures implement flags registers capturing arithmetic outcomes. The x86-64 `RFLAGS` register contains the carry flag (CF), zero flag (ZF), sign flag (SF), and overflow flag (OF) among others, updated implicitly by arithmetic and logic instructions. ARM64 consolidates condition flags into the 32-bit `NZCV` field within the processor state register: negative (N), zero (Z), carry (C), and overflow (V). Conditional branches (`Bcc` in ARM64, `Jcc` in x86-64) inspect these flags to implement high-level control flow constructs like if-statements and loops.

### Memory Addressing Modes and Endianness

x86-64 operates as a little-endian architecture, storing the least significant byte of multi-byte integers at the lowest memory address. A 32-bit integer `0x12345678` residing at address `0x1000` occupies bytes `0x78`, `0x56`, `0x34`, `0x12` at addresses `0x1000`, `0x1001`, `0x1002`, `0x1003` respectively. The architecture supports complex addressing modes including base-plus-displacement (`[RBX + 0x10]`), base-plus-scaled-index (`[RBX + RCX*4]`), and RIP-relative addressing for position-independent code.

ARM64 defaults to little-endian operation but supports big-endian data access through memory attribute configuration in page tables. The load/store architecture prohibits direct memory operands in arithmetic instructions; all computations occur between registers, with explicit `LDR` (load register) and `STR` (store register) instructions mediating memory access. Addressing modes include register-offset (`[X1, X2]`), immediate-offset (`[X1, #16]`), and post-increment (`[X1], #8`) for efficient array traversal.

### Assembler Syntax and Toolchain Workflows

GNU Assembler employs AT&T syntax for x86-64 by default, wherein instruction operands flow source-to-destination with register names prefixed by percent signs (`%rax`) and immediate values prefixed by dollar signs (`$42`). The `movq $5, %rax` instruction loads the immediate value 5 into the 64-bit `RAX` register. Intel syntax, preferred in disassembly and reverse engineering contexts, reverses operand order to destination-then-source and omits prefixes: `mov rax, 5`. The `.intel_syntax noprefix` directive switches the assembler to Intel notation within a source file.

ARM64 assembly universally employs a single syntax dialect. Instructions follow the pattern `MNEMONIC destination, source1, source2`, as in `ADD X0, X1, X2` which computes `X0 = X1 + X2`. Immediate values require no prefix but must fall within architecture-defined ranges: `MOV X0, #42` loads 42 into `X0`, while larger constants necessitate multi-instruction sequences using `MOVZ` (move with zero extension) and `MOVK` (move with keep) to construct 64-bit values across four 16-bit chunks.

The assembly workflow progresses from source text to object file to executable through distinct phases. The assembler translates mnemonic instructions into machine code opcodes, producing an ELF (Executable and Linkable Format) object file containing code sections, data sections, and symbol tables. The linker resolves symbolic references, assigns final virtual addresses, and generates an executable image. For standalone assembly programs without C runtime dependencies, the linker script must define the entry point and memory layout explicitly. The `-nostdlib` flag prevents linking against the standard C library, while `-static` produces a fully self-contained binary embedding all dependencies.

## Exercise 1: Foundational Practical Implementation

This exercise constructs a minimal x86-64 assembly program that interacts directly with the Linux kernel through system calls, bypassing all C library abstractions. The program writes the string "Hardware Lab\n" to standard output (file descriptor 1) and exits cleanly with return code zero. This operational foundation demonstrates register loading, immediate operand encoding, and the `syscall` instruction mechanism that transitions the CPU from user mode (ring 3) to kernel mode (ring 0) for privileged I/O operations.

### x86-64 System Call Interface Mechanics

Linux on x86-64 invokes system calls through the `syscall` instruction, which triggers a hardware-assisted control transfer to the kernel's system call dispatcher. The kernel expects the system call number in register `RAX`, with arguments passed through `RDI`, `RSI`, `RDX`, `R10`, `R8`, and `R9` in that sequence—note that `R10` substitutes for `RCX` in the userspace calling convention because the `syscall` instruction itself clobbers `RCX` with the return address. The `write` system call, numbered 1 on x86-64 Linux, requires three arguments: file descriptor in `RDI`, buffer pointer in `RSI`, and byte count in `RDX`. The `exit` system call, numbered 60, takes a single argument in `RDI` specifying the exit status code.

Create a working directory for assembly experiments and establish the first source file. The `.data` section declares initialized global variables stored in the executable's read-only data segment, while `.text` contains executable instructions. The `_start` symbol marks the program entry point, overriding the default C runtime entry `main`. The `.global _start` directive exports this symbol for visibility to the linker.

```bash
mkdir -p ~/asm_labs/x86_64
cd ~/asm_labs/x86_64
```

Compose the following complete x86-64 assembly source in a file named `hello_x86.s`. The `.ascii` directive embeds a raw string without null termination, while the subtraction `msg_len = . - msg` computes the string length at assembly time by subtracting the message's starting address from the current location counter.

```asm
.data
msg:
    .ascii "Hardware Lab\n"
    msg_len = . - msg

.text
.global _start

_start:
    # write(1, msg, msg_len)
    movq $1, %rax          # syscall number: sys_write
    movq $1, %rdi          # file descriptor: stdout
    leaq msg(%rip), %rsi   # buffer address (RIP-relative)
    movq $msg_len, %rdx    # byte count
    syscall
    
    # exit(0)
    movq $60, %rax         # syscall number: sys_exit
    xorq %rdi, %rdi        # exit code: 0 (XOR clears register)
    syscall
```

The `leaq msg(%rip), %rsi` instruction loads the effective address of `msg` using RIP-relative addressing, essential for position-independent executables. This addressing mode computes the target address as the current instruction pointer plus a signed offset, enabling the same binary to execute correctly regardless of its load address in virtual memory. The `xorq %rdi, %rdi` idiom zeros `RDI` more efficiently than `movq $0, %rdi` because XOR of identical operands always yields zero, and the instruction encoding consumes fewer bytes.

Assemble the source file into an ELF64 object file using the GNU assembler. The `-o` flag specifies the output filename, while `--64` enforces 64-bit mode even on systems with mixed architecture support.

```bash
as --64 -o hello_x86.o hello_x86.s
```

Inspect the generated object file's symbol table and section headers to verify correct assembly. The `nm` utility lists symbols, confirming `_start` appears as a global text symbol (type `T`). The `objdump -h` command displays section headers, showing `.text` at offset zero with execute permissions and `.data` containing the message string.

```bash
nm hello_x86.o
objdump -h hello_x86.o
```

Link the object file into a statically-linked executable without standard library dependencies. The `-nostdlib` flag prevents linking against `libc`, while `-static` disables dynamic linking. The `-e _start` flag explicitly sets the entry point symbol, overriding the default `_start` resolution that the linker performs when no `-e` option appears.

```bash
ld -o hello_x86 -nostdlib -static -e _start hello_x86.o
```

Execute the resulting binary and verify the output string appears on the terminal followed by a newline. Confirm the exit status by immediately inspecting the `$?` shell variable, which should contain zero.

```bash
./hello_x86
echo $?
```

Disassemble the executable to observe the final machine code encoding and confirm instruction addresses. The `objdump -d` command disassembles all executable sections, displaying opcode bytes alongside AT&T syntax assembly. Note the `syscall` instruction encoding as `0f 05` and the compact two-byte XOR encoding `48 31 ff` for `xorq %rdi, %rdi`.

```bash
objdump -d hello_x86
```

### ARM64 Bare-Metal System Call Implementation

Transitioning to ARM64 architecture, construct an equivalent program using AArch64 assembly syntax and Linux ARM64 system call conventions. ARM64 invokes system calls through the `SVC #0` (Supervisor Call) instruction, which generates a synchronous exception that the kernel handles by examining the system call number in register `X8`. Arguments pass through `X0` to `X7`, with `write` numbered 64 and `exit` numbered 93 in the ARM64 system call table.

Create a dedicated directory for ARM64 experiments and compose the assembly source. The ARM64 assembler uses `=` for constant definition rather than subtraction expressions, but the message length calculation follows identical logic.

```bash
mkdir -p ~/asm_labs/arm64
cd ~/asm_labs/arm64
```

Write the following ARM64 assembly source to a file named `hello_arm64.s`. The `ADR` instruction loads a PC-relative address into a register, computing the target as the program counter plus a signed offset within ±1 MiB. The `MOV` instruction with immediate values uses implicit `MOVZ` encoding for small constants.

```asm
.data
msg:
    .ascii "Hardware Lab\n"
    msg_len = . - msg

.text
.global _start

_start:
    // write(1, msg, msg_len)
    MOV X8, #64            // syscall number: sys_write
    MOV X0, #1             // file descriptor: stdout
    ADR X1, msg            // buffer address (PC-relative)
    MOV X2, #msg_len       // byte count
    SVC #0
    
    // exit(0)
    MOV X8, #93            // syscall number: sys_exit
    MOV X0, #0             // exit code: 0
    SVC #0
```

Cross-assemble the source file using the ARM64 GNU assembler. The cross-toolchain prefix `aarch64-linux-gnu-` distinguishes ARM64 tools from native x86-64 equivalents.

```bash
aarch64-linux-gnu-as -o hello_arm64.o hello_arm64.s
```

Verify the object file structure and symbol table using the ARM64-targeted versions of `nm` and `objdump`. The output format matches x86-64 but the machine type field indicates `aarch64`.

```bash
aarch64-linux-gnu-nm hello_arm64.o
aarch64-linux-gnu-objdump -h hello_arm64.o
```

Link the object file into a statically-linked ARM64 executable. The linker requires explicit output architecture specification when cross-compiling.

```bash
aarch64-linux-gnu-ld -o hello_arm64 -nostdlib -static -e _start hello_arm64.o
```

Since the host machine runs x86-64, execute the ARM64 binary through QEMU's user-mode emulator. The `-L /usr/aarch64-linux-gnu` flag directs QEMU to search for shared libraries in the cross-compiler's sysroot, though unnecessary for this statically-linked binary.

```bash
qemu-aarch64 -L /usr/aarch64-linux-gnu hello_arm64
echo $?
```

Disassemble the ARM64 executable to inspect instruction encodings. The `SVC #0` instruction encodes as `D4 00 00 01`, and the compact immediate moves demonstrate ARM64's fixed-length 32-bit instruction format.

```bash
aarch64-linux-gnu-objdump -d hello_arm64
```

### Interactive Debugging with GDB

Launch the x86-64 executable under GDB's interactive debugger to single-step through instructions and inspect register state transitions. The `layout asm` command activates the text-based assembly view, displaying the instruction pointer position and upcoming instructions.

```bash
gdb ./hello_x86
```

Within the GDB session, set a breakpoint at the `_start` symbol and begin execution. The `si` (step instruction) command advances by a single instruction, updating the register display after each step. Monitor `RAX`, `RDI`, `RSI`, and `RDX` as they load system call parameters.

```gdb
(gdb) break _start
(gdb) run
(gdb) layout asm
(gdb) si
(gdb) info registers rax rdi rsi rdx
(gdb) si
(gdb) info registers rax rdi rsi rdx
```

Continue stepping through the `write` syscall, observing that execution halts at the kernel boundary and resumes after the syscall completes. Inspect memory at the message buffer address to confirm the string contents.

```gdb
(gdb) x/s $rsi
(gdb) si
```

Repeat the debugging process for the ARM64 binary using QEMU's GDB server mode. Launch QEMU with the `-g 1234` flag to suspend execution and wait for GDB connection on TCP port 1234.

```bash
qemu-aarch64 -L /usr/aarch64-linux-gnu -g 1234 hello_arm64
```

In a separate terminal, attach the ARM64 GDB client to the remote target. The `target remote localhost:1234` command establishes the connection, and the debugging workflow mirrors native execution.

```bash
aarch64-linux-gnu-gdb hello_arm64
```

```gdb
(gdb) target remote localhost:1234
(gdb) break _start
(gdb) continue
(gdb) layout asm
(gdb) si
(gdb) info registers x8 x0 x1 x2
```

## Exercise 2: Parameter Variation & Empirical Analysis

This exercise advances to arithmetic computation and control flow, implementing a recursive Fibonacci sequence calculator in both x86-64 and ARM64 assembly. The operational focus shifts to function calling conventions, stack frame management, and performance characterization through instruction cycle counting. The recursive algorithm exposes pipeline stall behavior, branch misprediction penalties, and stack memory access latency, providing empirical data for microarchitectural optimization.

### Recursive Fibonacci Implementation on x86-64

The Fibonacci sequence follows the recurrence relation F(n) = F(n-1) + F(n-2) with base cases F(0) = 0 and F(1) = 1. Recursive implementation translates directly to assembly through function calls that push return addresses and register values onto the stack. The System V ABI mandates preserving `RBX`, `RBP`, and `R12` through `R15` across function calls, requiring explicit push and pop sequences in the function prologue and epilogue.

Compose the following x86-64 assembly source in `fibonacci_x86.s`. The function receives argument `n` in `RDI` and returns the result in `RAX`. The prologue saves `RBX` on the stack and preserves the argument in `RBX` across recursive calls, since `RDI` might be clobbered by the first recursive invocation.

```asm
.text
.global _start

fibonacci:
    # Prologue: save callee-saved register
    pushq %rbx
    movq %rdi, %rbx        # save n in RBX
    
    # Base case: if n <= 1, return n
    cmpq $1, %rbx
    jle .base_case
    
    # Recursive case: fib(n-1)
    movq %rbx, %rdi
    subq $1, %rdi
    call fibonacci
    pushq %rax             # save fib(n-1) on stack
    
    # Recursive case: fib(n-2)
    movq %rbx, %rdi
    subq $2, %rdi
    call fibonacci
    
    # Combine results: fib(n-1) + fib(n-2)
    popq %rbx              # retrieve fib(n-1)
    addq %rbx, %rax        # RAX = fib(n-2) + fib(n-1)
    popq %rbx              # restore RBX
    ret
    
.base_case:
    movq %rbx, %rax        # return n
    popq %rbx
    ret

_start:
    # Compute fib(10)
    movq $10, %rdi
    call fibonacci
    
    # Exit with result as exit code
    movq %rax, %rdi
    movq $60, %rax
    syscall
```

Assemble and link the Fibonacci implementation, then execute and capture the exit code. The exit status should equal F(10) = 55.

```bash
as --64 -o fibonacci_x86.o fibonacci_x86.s
ld -o fibonacci_x86 -nostdlib -static -e _start fibonacci_x86.o
./fibonacci_x86
echo $?
```

### Stack Frame Analysis and Memory Layout

Trace the stack evolution during recursive calls by launching the program under GDB and inspecting the stack pointer at each function entry. Set a breakpoint inside the `fibonacci` function and examine stack memory layout.

```bash
gdb ./fibonacci_x86
```

```gdb
(gdb) break fibonacci
(gdb) run
(gdb) info registers rsp rbp
(gdb) x/8xg $rsp
(gdb) continue
(gdb) info registers rsp rbp
(gdb) x/8xg $rsp
```

The stack grows downward with each recursive call, consuming 16 bytes per frame: 8 bytes for the saved `RBX` register and 8 bytes for the return address pushed by `call`. The maximum recursion depth of 10 requires approximately 160 bytes of stack space, negligible compared to Linux's default 8 MiB stack allocation. However, deeper recursion or additional local variables could trigger stack overflow, observable as a segmentation fault when the stack pointer crosses into unmapped memory regions.

### ARM64 Fibonacci with Link Register Preservation

Translate the Fibonacci implementation to ARM64, adhering to AAPCS64 conventions. The link register `X30` (LR) holds the return address, automatically loaded by `BL` instructions but not automatically saved. Leaf functions that make no further calls can return via `RET` without stack manipulation, but non-leaf functions must preserve `X30` across nested calls.

Write the ARM64 source to `fibonacci_arm64.s`. The function uses `X19` as the callee-saved register to preserve the argument `n`, following the AAPCS64 requirement that `X19` through `X28` must be restored before returning.

```asm
.text
.global _start

fibonacci:
    # Prologue: save link register and callee-saved register
    STP X30, X19, [SP, #-16]!   // push LR and X19, pre-decrement SP
    MOV X19, X0                  // save n in X19
    
    # Base case: if n <= 1, return n
    CMP X19, #1
    BLE .base_case
    
    # Recursive case: fib(n-1)
    SUB X0, X19, #1
    BL fibonacci
    MOV X20, X0                  // save fib(n-1) in X20 (also callee-saved)
    
    # Recursive case: fib(n-2)
    SUB X0, X19, #2
    BL fibonacci
    
    # Combine results: fib(n-1) + fib(n-2)
    ADD X0, X20, X0              // X0 = fib(n-1) + fib(n-2)
    LDP X30, X19, [SP], #16      // pop LR and X19, post-increment SP
    RET
    
.base_case:
    MOV X0, X19                  // return n
    LDP X30, X19, [SP], #16
    RET

_start:
    # Compute fib(10)
    MOV X0, #10
    BL fibonacci
    
    # Exit with result as exit code
    MOV X8, #93
    SVC #0
```

The `STP` (Store Pair) and `LDP` (Load Pair) instructions atomically save and restore two 64-bit registers, maintaining the 16-byte stack alignment requirement. The pre-decrement and post-increment addressing modes (`[SP, #-16]!` and `[SP], #16`) adjust the stack pointer as part of the memory operation, eliminating separate `SUB SP, SP, #16` instructions.

Assemble, link, and execute the ARM64 Fibonacci implementation through QEMU userspace emulation.

```bash
aarch64-linux-gnu-as -o fibonacci_arm64.o fibonacci_arm64.s
aarch64-linux-gnu-ld -o fibonacci_arm64 -nostdlib -static -e _start fibonacci_arm64.o
qemu-aarch64 -L /usr/aarch64-linux-gnu fibonacci_arm64
echo $?
```

### Performance Profiling and Instruction Cycle Estimation

Measure execution time using the `time` utility to capture user-mode CPU time. Recursive Fibonacci exhibits exponential time complexity O(2^n) due to redundant subproblem recomputation, making execution time sensitive to input magnitude.

```bash
time ./fibonacci_x86
```

For deeper microarchitectural analysis, employ the `perf` tool on x86-64 systems to collect hardware performance counter statistics. The `perf stat` command profiles retired instructions, branch misses, and cache references.

```bash
perf stat -e cycles,instructions,branches,branch-misses ./fibonacci_x86
```

Typical output reveals an instruction-per-cycle (IPC) ratio below 1.0 due to frequent branch mispredictions during recursive calls. Modern out-of-order processors sustain IPC values approaching 4.0 on optimized code with predictable branches and high cache hit rates, but recursive algorithms with dynamic control flow stall the pipeline. The branch miss rate approaches 10-20% because the conditional returns at base cases alternate unpredictably depending on the recursion path.

Compute the theoretical instruction count by analyzing the disassembly. Each recursive call executes approximately 15 instructions (prologue, comparison, two calls, arithmetic, epilogue), and the recursion tree for F(10) contains 177 function invocations (the sum of the Fibonacci sequence up to F(11)). This yields an estimated 2,655 instructions, closely matching the `perf` instruction count when accounting for syscall overhead.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

This exercise explores edge cases, exception handling, and fault injection to develop robust diagnostic skills. The operational scenarios include stack overflow from excessive recursion, invalid memory access triggering segmentation faults, and integer overflow in arithmetic computations. The practitioner will instrument assembly code with defensive checks, configure kernel coredump capture, and dissect postmortem crash dumps to identify fault addresses and register states at the moment of failure.

### Stack Overflow Induction and Kernel Signal Analysis

Modify the Fibonacci program to accept a command-line argument specifying the recursion depth, enabling controlled testing of stack exhaustion. The argument parsing requires reading the `argc` and `argv` values that the Linux kernel places on the stack before transferring control to `_start`. At program entry, the stack contains `argc` (8 bytes) at `[RSP]`, followed by a null-terminated array of argument string pointers starting at `[RSP+8]`.

Rewrite `fibonacci_x86.s` to parse the first command-line argument as a decimal integer using a manual digit-to-integer conversion loop. The implementation scans the ASCII string, subtracts `'0'` (0x30) from each digit character, and accumulates the value through repeated multiplication by 10.

```asm
.text
.global _start

fibonacci:
    pushq %rbx
    movq %rdi, %rbx
    cmpq $1, %rbx
    jle .base_case
    movq %rbx, %rdi
    subq $1, %rdi
    call fibonacci
    pushq %rax
    movq %rbx, %rdi
    subq $2, %rdi
    call fibonacci
    popq %rbx
    addq %rbx, %rax
    popq %rbx
    ret
.base_case:
    movq %rbx, %rax
    popq %rbx
    ret

# Convert ASCII string to integer
atoi:
    xorq %rax, %rax          # accumulator = 0
    movq %rdi, %rsi          # string pointer
.atoi_loop:
    movzbq (%rsi), %rcx      # load byte, zero-extend to 64-bit
    cmpq $0, %rcx            # null terminator?
    je .atoi_done
    subq $0x30, %rcx         # ASCII digit to numeric value
    imulq $10, %rax          # accumulator *= 10
    addq %rcx, %rax          # accumulator += digit
    incq %rsi                # advance pointer
    jmp .atoi_loop
.atoi_done:
    ret

_start:
    # Parse command-line argument
    movq (%rsp), %rax        # argc
    cmpq $2, %rax            # check for exactly 1 argument
    jl .default_arg
    movq 16(%rsp), %rdi      # argv[1] (skip argv[0])
    call atoi
    movq %rax, %rdi
    jmp .compute_fib
.default_arg:
    movq $10, %rdi           # default to fib(10)
.compute_fib:
    call fibonacci
    movq %rax, %rdi
    movq $60, %rax
    syscall
```

Assemble and link the updated program, then execute with progressively larger arguments to trigger stack overflow. Linux's default stack limit of 8,388,608 bytes (8 MiB) allows approximately 524,288 recursive calls with 16 bytes per frame, but the exponential branching of Fibonacci exhausts computation time long before reaching stack limits. Instead, test with a linear recursion pattern or manually reduce the stack limit using `ulimit`.

```bash
as --64 -o fibonacci_arg_x86.o fibonacci_arg_x86.s
ld -o fibonacci_arg_x86 -nostdlib -static -e _start fibonacci_arg_x86.o
ulimit -s 128       # restrict stack to 128 KiB
./fibonacci_arg_x86 20
./fibonacci_arg_x86 50
```

Attempting recursion depth 50 generates millions of calls, likely triggering a stack overflow segmentation fault (signal 11, SIGSEGV). The kernel terminates the process and optionally writes a coredump file containing the process's memory image at the fault instant. Enable coredump generation by setting the core file size limit to unlimited.

```bash
ulimit -c unlimited
./fibonacci_arg_x86 50
```

If the program crashes, inspect the generated coredump using GDB. The `core` file appears in the current directory (or at the path configured in `/proc/sys/kernel/core_pattern`). Load the executable and coredump into GDB to examine the faulting instruction and stack backtrace.

```bash
gdb ./fibonacci_arg_x86 core
```

```gdb
(gdb) info registers rsp rip
(gdb) x/i $rip
(gdb) backtrace
```

The backtrace reveals thousands of nested `fibonacci` frames, confirming stack exhaustion. The stack pointer `RSP` resides near the bottom of the stack region (low addresses in the virtual address space), having collided with the unmapped guard page that the kernel positions below the stack to detect overflows.

### Segmentation Fault Through Invalid Memory Dereference

Construct a deliberate invalid memory access to study the kernel's memory protection mechanisms and coredump diagnostics. Write a minimal assembly program that attempts to write to address 0x0 (null pointer dereference) or to a read-only memory segment.

Create `segfault_x86.s` with an intentional null pointer write.

```asm
.text
.global _start

_start:
    movq $0x42, %rax
    movq $0x0, %rbx          # null pointer
    movq %rax, (%rbx)        # write to address 0x0
    movq $60, %rax
    xorq %rdi, %rdi
    syscall
```

Assemble, link, and execute the program, which immediately triggers a segmentation fault. The kernel sends SIGSEGV because the process lacks a valid memory mapping at address 0x0, enforced by the memory management unit (MMU).

```bash
as --64 -o segfault_x86.o segfault_x86.s
ld -o segfault_x86 -nostdlib -static -e _start segfault_x86.o
./segfault_x86
```

Load the resulting coredump into GDB and examine the faulting instruction and register contents. The `info registers` command shows `RBX` containing 0x0, and the instruction pointer `RIP` points to the `movq %rax, (%rbx)` instruction.

```bash
gdb ./segfault_x86 core
```

```gdb
(gdb) info registers rip rbx rax
(gdb) x/i $rip
(gdb) disassemble
```

Inspect the Linux kernel's signal delivery by enabling verbose signal reporting with `strace`, which traces system calls and signals. The output reveals the `SIGSEGV` signal with fault address `si_addr=0x0`, confirming the null pointer access.

```bash
strace ./segfault_x86
```

### Integer Overflow Detection and Arithmetic Exception Handling

x86-64 arithmetic instructions set the overflow flag (OF) in `RFLAGS` when signed integer operations exceed representable ranges, but do not generate exceptions by default. Detect overflow conditions explicitly by testing the flag after arithmetic and branching to error handlers. The `jo` (jump if overflow) instruction branches when OF equals 1.

Implement a signed 64-bit addition function with overflow checking. The function returns 0 for success or 1 for overflow in `RAX`, storing the result in memory only when valid.

```asm
.text
.global _start

# add_checked(int64_t a, int64_t b, int64_t *result)
# RDI = a, RSI = b, RDX = result pointer
# Returns: 0 success, 1 overflow
add_checked:
    movq %rdi, %rax
    addq %rsi, %rax          # a + b, sets OF on overflow
    jo .overflow_detected
    movq %rax, (%rdx)        # store result
    xorq %rax, %rax          # return 0
    ret
.overflow_detected:
    movq $1, %rax            # return 1
    ret

_start:
    # Test case 1: valid addition
    movq $100, %rdi
    movq $200, %rsi
    leaq result1(%rip), %rdx
    call add_checked
    movq %rax, %r12          # save status
    
    # Test case 2: overflow (0x7FFFFFFFFFFFFFFF + 1)
    movq $0x7FFFFFFFFFFFFFFF, %rdi
    movq $1, %rsi
    leaq result2(%rip), %rdx
    call add_checked
    movq %rax, %r13          # save status
    
    # Exit with combined status (should be 1)
    addq %r12, %r13
    movq %r13, %rdi
    movq $60, %rax
    syscall

.data
result1: .quad 0
result2: .quad 0
```

Assemble and execute, verifying the exit code equals 1 (the overflow case). Inspect the result storage locations in the debugger to confirm the first addition stored 300 while the second left `result2` unchanged.

```bash
as --64 -o overflow_x86.o overflow_x86.s
ld -o overflow_x86 -nostdlib -static -e _start overflow_x86.o
./overflow_x86
echo $?
gdb ./overflow_x86
```

```gdb
(gdb) break add_checked
(gdb) run
(gdb) continue
(gdb) print/d *(long*)&result1
(gdb) continue
(gdb) print/d *(long*)&result2
```

### ARM64 Exception Level Transitions and Synchronous Exceptions

ARM64 organizes privilege levels into exception levels (EL0 through EL3), with userspace code executing at EL0 and the kernel at EL1. Illegal instructions, misaligned accesses, and explicit `SVC` instructions generate synchronous exceptions that transition to higher exception levels. Unlike x86-64's segmentation fault model, ARM64 exposes exception class and fault address through special registers (`ESR_EL1` and `FAR_EL1`) accessible only in kernel mode.

Construct an ARM64 program that executes an undefined instruction to trigger an illegal instruction exception. The A64 instruction set reserves certain opcode ranges for undefined behavior, ensuring the processor takes an exception rather than executing unpredictable operations.

Write `illegal_arm64.s` with an embedded undefined instruction word.

```asm
.text
.global _start

_start:
    .word 0x00000000         # undefined instruction (opcode all zeros)
    MOV X8, #93
    MOV X0, #0
    SVC #0
```

Assemble, link, and execute through QEMU, which emulates the illegal instruction exception and terminates the process with signal SIGILL (signal 4).

```bash
aarch64-linux-gnu-as -o illegal_arm64.o illegal_arm64.s
aarch64-linux-gnu-ld -o illegal_arm64 -nostdlib -static -e _start illegal_arm64.o
qemu-aarch64 -L /usr/aarch64-linux-gnu illegal_arm64
echo $?
```

The exit code reflects signal number 4, plus 128 if the process was terminated by a signal (exit code 132 = 128 + 4). Use QEMU's debugging interface to inspect the exception before termination.

```bash
qemu-aarch64 -L /usr/aarch64-linux-gnu -g 1234 illegal_arm64
```

Attach GDB in a second terminal and step to the undefined instruction. The debugger reports an illegal instruction exception.

```bash
aarch64-linux-gnu-gdb illegal_arm64
```

```gdb
(gdb) target remote localhost:1234
(gdb) break _start
(gdb) continue
(gdb) si
```

## Operational Reference Guide & Diagnostic Checklist

This section consolidates essential assembly programming patterns, debugging procedures, and performance optimization guidelines derived from the laboratory exercises. The operational reference serves as a rapid-lookup manual for field troubleshooting, code review, and embedded firmware development.

### Instruction Set Quick Reference

**x86-64 Core Instructions (AT&T Syntax):**

- `movq $imm, %reg` – Load 64-bit immediate into register
- `movq %src, %dst` – Copy register to register
- `leaq addr, %reg` – Load effective address (pointer arithmetic)
- `pushq %reg` – Decrement RSP by 8, store register
- `popq %reg` – Load register from [RSP], increment RSP by 8
- `call label` – Push return address, jump to label
- `ret` – Pop return address, jump to it
- `addq %src, %dst` – dst += src, set flags
- `subq %src, %dst` – dst -= src, set flags
- `cmpq %src, %dst` – Compute dst - src, set flags, discard result
- `je label` – Jump if ZF=1 (equal)
- `jne label` – Jump if ZF=0 (not equal)
- `jl label` – Jump if SF≠OF (signed less-than)
- `jle label` – Jump if ZF=1 or SF≠OF (signed less-or-equal)
- `syscall` – Invoke system call, number in RAX

**ARM64 Core Instructions (AArch64):**

- `MOV Xd, #imm` – Load immediate (0-65535) into register
- `MOV Xd, Xn` – Copy register to register
- `ADR Xd, label` – Load PC-relative address (±1 MiB)
- `LDR Xd, [Xn, #offset]` – Load 64-bit from memory
- `STR Xd, [Xn, #offset]` – Store 64-bit to memory
- `STP Xn, Xm, [SP, #-16]!` – Push register pair (pre-decrement)
- `LDP Xn, Xm, [SP], #16` – Pop register pair (post-increment)
- `BL label` – Branch-and-link (call), save return in X30
- `RET` – Return via X30
- `ADD Xd, Xn, Xm` – Xd = Xn + Xm
- `SUB Xd, Xn, Xm` – Xd = Xn - Xm
- `CMP Xn, #imm` – Compute Xn - imm, set NZCV flags
- `B.EQ label` – Branch if Z=1 (equal)
- `B.NE label` – Branch if Z=0 (not equal)
- `B.LT label` – Branch if N≠V (signed less-than)
- `B.LE label` – Branch if Z=1 or N≠V (signed less-or-equal)
- `SVC #0` – Supervisor call (system call), number in X8

### Calling Convention Summary

**System V AMD64 ABI (x86-64 Linux/BSD):**

- Integer/pointer arguments: RDI, RSI, RDX, RCX, R8, R9
- Return value: RAX (64-bit), RDX:RAX (128-bit)
- Callee-saved registers: RBX, RBP, R12-R15
- Caller-saved registers: RAX, RCX, RDX, RSI, RDI, R8-R11
- Stack alignment: 16-byte boundary before `call`
- Red zone: 128 bytes below RSP (leaf functions may use without adjusting RSP)

**AAPCS64 (ARM64 Linux):**

- Integer/pointer arguments: X0-X7
- Return value: X0 (64-bit), X1 (second register for 128-bit)
- Callee-saved registers: X19-X28, X29 (frame pointer), X30 (link register)
- Caller-saved registers: X0-X18
- Stack alignment: 16-byte boundary at function call
- No red zone equivalent; stack pointer adjustments required

### System Call Tables

**x86-64 Linux System Call Numbers (partial):**

- 0: `read(fd, buf, count)`
- 1: `write(fd, buf, count)`
- 2: `open(path, flags, mode)`
- 3: `close(fd)`
- 60: `exit(status)`
- 231: `exit_group(status)`

**ARM64 Linux System Call Numbers (partial):**

- 63: `read(fd, buf, count)`
- 64: `write(fd, buf, count)`
- 56: `openat(dirfd, path, flags, mode)`
- 57: `close(fd)`
- 93: `exit(status)`
- 94: `exit_group(status)`

### Debugging Workflow Patterns

**Single-Stepping Through Instructions:**

```bash
gdb ./program
(gdb) break _start
(gdb) run
(gdb) layout asm
(gdb) layout regs
(gdb) si                    # step one instruction
(gdb) info registers        # display all registers
(gdb) info registers rax rbx  # display specific registers
(gdb) x/8xg $rsp            # examine 8 quadwords at stack pointer
(gdb) x/s $rdi              # examine string at address in RDI
```

**Examining Memory Mappings:**

```gdb
(gdb) info proc mappings    # display virtual memory regions
(gdb) maintenance info sections  # ELF section addresses
```

**ARM64 Remote Debugging with QEMU:**

Terminal 1:
```bash
qemu-aarch64 -L /usr/aarch64-linux-gnu -g 1234 program
```

Terminal 2:
```bash
aarch64-linux-gnu-gdb program
(gdb) target remote localhost:1234
(gdb) break _start
(gdb) continue
```

### Performance Counter Profiling Commands

**x86-64 Cycle and Instruction Counting:**

```bash
perf stat -e cycles,instructions,branches,branch-misses,cache-references,cache-misses ./program
```

**Estimating Instructions-Per-Cycle (IPC):**

Divide retired instructions by elapsed cycles. Modern out-of-order CPUs achieve IPC of 2-4 on optimized code. Recursive algorithms with unpredictable branches typically yield IPC below 1.0.

**Identifying Performance Bottlenecks:**

- High branch-miss rate (>5%): refactor control flow, reduce conditionals
- High cache-miss rate (>10%): improve data locality, reduce pointer chasing
- Low IPC (<1.0): pipeline stalls from data dependencies or memory latency

### Common Failure Modes and Diagnostics

**Stack Overflow:**

- Symptoms: Segmentation fault after many recursive calls
- Diagnosis: `ulimit -s` check, GDB backtrace depth
- Mitigation: Convert recursion to iteration, increase stack limit with `ulimit -s unlimited`

**Null Pointer Dereference:**

- Symptoms: SIGSEGV with fault address 0x0
- Diagnosis: GDB `info registers`, examine faulting instruction operands
- Mitigation: Validate pointers before dereferencing, add null checks

**Misaligned Memory Access:**

- Symptoms: SIGBUS on ARM, performance penalty on x86-64
- Diagnosis: Check address alignment (`addr % 8 == 0` for 64-bit loads)
- Mitigation: Use aligned allocations, pad structures

**Arithmetic Overflow:**

- Symptoms: Incorrect results, silent wraparound
- Diagnosis: Inspect overflow flag (OF) after arithmetic, use `jo` conditional
- Mitigation: Validate operand ranges, use checked arithmetic functions

**System Call Failures:**

- Symptoms: Unexpected behavior, missing output
- Diagnosis: Check return value in RAX/X0 (negative errno on failure)
- Mitigation: Test return codes, use `strace` to monitor syscalls

### Coredump Analysis Procedure

Enable coredumps system-wide:
```bash
ulimit -c unlimited
echo "core.%e.%p" | sudo tee /proc/sys/kernel/core_pattern
```

Load coredump in GDB:
```bash
gdb ./program core.program.12345
(gdb) where              # backtrace
(gdb) info registers     # register snapshot at crash
(gdb) x/i $rip           # faulting instruction
(gdb) disassemble        # surrounding code
```

### Optimization Guidelines

**Register Allocation:**

Prefer callee-saved registers (RBX, R12-R15 on x86-64; X19-X28 on ARM64) for loop counters and frequently-accessed variables to minimize save/restore overhead across function calls.

**Instruction Selection:**

Use compact instruction encodings: `xorq %rax, %rax` (3 bytes) instead of `movq $0, %rax` (7 bytes). ARM64's fixed-length instructions eliminate this concern but require multi-instruction sequences for large immediates.

**Branch Prediction:**

Structure conditionals to favor the likely path first. Modern CPUs assume forward branches are not taken and backward branches (loops) are taken. Minimize conditional branches in hot loops; unroll short loops manually.

**Cache Optimization:**

Access memory sequentially to exploit spatial locality. Array traversal should increment pointers by the element size. Avoid pointer chasing through linked lists in performance-critical code.

**Pipeline Efficiency:**

Interleave independent instructions to avoid data hazards. In a sequence computing multiple values, alternate between different register sets to reduce read-after-write stalls.

This operational guide provides the essential reference framework for assembly-level development, debugging, and performance optimization across x86-64 and ARM64 architectures. The laboratory exercises and diagnostic patterns equip the practitioner with empirical skills to analyze, instrument, and troubleshoot low-level code in embedded systems, firmware, and performance-critical applications.
