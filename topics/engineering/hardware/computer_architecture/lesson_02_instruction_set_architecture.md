# Lesson 2: Instruction Set Architecture

## 1. First-Principles Intuition & Invariants

An Instruction Set Architecture (ISA) is the formal contract between hardware and software—the vocabulary through which a processor executes computational intent. Unlike higher-level abstractions where programmers craft algorithms in languages like C or Python, the ISA operates at the boundary where intent becomes physical: every instruction specifies which registers to read, which arithmetic units to activate, where to fetch operands, and how to store results. The ISA is simultaneously the lowest level of portable software (machine code runs unchanged across physically different implementations) and the highest level of hardware specification (it defines what the silicon must compute).

The foundational insight is this: an ISA is not merely a collection of operations but rather a *discipline for encoding meaning in fixed-width bit patterns*. A 32-bit or 64-bit instruction word is a compact message that the decoder hardware must unambiguously interpret in nanoseconds. This constraint—that interpretation must be deterministic and blazingly fast—shapes every design choice: the width of instruction formats, the number of operands per instruction, the range of immediate values, and whether operations can access memory directly or must load data into registers first.

The ISA establishes several critical invariants that downstream hardware must respect:

**First, the execution model invariant.** The ISA defines whether the processor is load-store (only loads and stores touch memory; all computation uses registers) or register-memory (arithmetic operations can directly access memory). This choice profoundly shapes the memory system. A load-store architecture like ARM or RISC-V forces explicit data movement, but this simplicity enables more aggressive out-of-order execution and cache optimization. A register-memory ISA like x86-64 allows fewer instructions per task but creates complex memory access patterns that stress the pipeline and increase cache miss penalties.

**Second, the register file contract.** The ISA specifies how many general-purpose registers exist, their width (32-bit, 64-bit, 128-bit), which are caller-saved, which are callee-saved, and whether special-purpose registers (program counter, stack pointer, status flags) are directly accessible. A processor with 32 general-purpose registers provides more scratch space for register allocation, reducing memory traffic; a processor with 8 registers forces frequent spilling to the stack. This is not merely a software convenience—it shapes instruction density, pipeline register pressure, and ultimately power consumption and thermal output.

**Third, the addressing mode contract.** The ISA specifies how instructions can compute memory addresses: can they use base + displacement (register plus a small offset), or must they compute the address in a separate register first? Can they perform post-increment (load from address, then increment the register)? Can they shift or scale an index register? These choices determine how many clock cycles a memory access requires and how efficiently the instruction fetch pipeline can be filled.

**Fourth, the flag/condition code contract.** The ISA defines whether arithmetic operations implicitly set flags (like the RFLAGS register in x86, where the zero, carry, overflow, and sign bits are set after every add or subtract), and whether instructions can conditionally execute based on those flags. ARM, for example, allows almost any instruction to execute conditionally based on the condition flags set by a prior comparison, dramatically reducing the number of branches needed—but this adds decoding complexity. x86-64 treats flags as side effects: they are set but not mandatory, and separate compare and jump instructions are used for conditionals.

From these invariants flow the entire ecosystem of calling conventions, register allocation strategies, and performance optimization techniques. An engineer working at this level must internalize how ISA choices ripple upward: a seemingly innocuous decision to allow memory-operand arithmetic operations in x86 cascades into more complex load-store units, higher cache miss penalties, and ultimately more power consumption than a load-store ISA would require for the same computational throughput.

## 2. Core Architecture & Mechanics

### The Instruction Decode Pipeline and Format Space

Every instruction begins as a sequence of bits arriving from the instruction cache. The first hardware stage that processes these bits is the decoder, which must extract the opcode, register specifiers, and immediate values with such reliability and speed that modern out-of-order processors decode multiple instructions per cycle (e.g., Intel's x86 decodes up to four instructions per cycle; ARM Cortex-A78 decodes up to four). The decoder's job is to map the compact bit pattern into a set of microoperations (µops) that the execution engine understands.

The format of an instruction word is therefore a critical engineering lever. RISC architectures like MIPS, SPARC, and ARM typically use a fixed 32-bit format (or alternatively, a variable-length encoding where instructions are 32-bit or 16-bit). Within that fixed width, they partition bits into opcode, source registers, destination register, and immediate fields. For example, a MIPS R-format (register) instruction allocates 6 bits for opcode, 5 bits each for two source registers, 5 bits for a destination register, 5 bits for a shift amount, and 6 bits for a function code:

```
Bits [31:26] : Opcode (6 bits)
Bits [25:21] : RS (Source register 1)
Bits [20:16] : RT (Source register 2)
Bits [15:11] : RD (Destination register)
Bits [10:6]  : Shamt (Shift amount)
Bits [5:0]   : Funct (Function code)
```

This rigid structure means the hardware decoder can extract register specifiers in parallel: as soon as the instruction word is fetched, the decoder can route bits [25:21] to the register file to read RS, and bits [20:16] to read RT, all in a single cycle. There is no ambiguity, no variable-length parsing, no conditional logic to figure out where the operands are. This simplicity is the entire point of the RISC philosophy.

Contrast this with x86-64, where instructions are 1 to 15 bytes long and their structure depends on prefix bytes, which specify operand width, address size, and repeat semantics. A single x86 instruction might begin with legacy prefixes (66h for operand-size override, 67h for address-size override), then a mandatory prefix (0Fh for two-byte opcodes), then the actual opcode, then a ModRM byte that encodes the addressing mode, then an optional SIB (scale-index-base) byte for complex addressing, then a 1-, 2-, 4-, or 8-byte displacement, and finally a 1-, 2-, 4-, or 8-byte immediate. The decoder must serially scan the instruction stream, counting bytes, tracking state, and determining when it has consumed the entire instruction. Modern x86 decoders use translation tables and parallel-scanning hardware to accelerate this process, but it remains fundamentally more complex than RISC decoding.

The tradeoff is clear: RISC pays a performance penalty in code density (more instructions are needed to express the same computation) but gains speed and predictability in decoding. x86 achieves better code density (fewer bytes per instruction), allowing smaller instruction caches and lower memory bandwidth, but forces the decoder to work harder and creates opportunities for pipeline stalls if the decoder cannot keep up. In modern practice, x86 processors employ a microinstruction cache that stores the decoded µops, amortizing decoding overhead across multiple cycles of execution—but this adds silicon area and complexity.

### Addressing Modes and Memory Access Encoding

The choice of addressing modes is where ISA design reveals its assumptions about how software will access memory. A simple ISA provides only two addressing modes: register-indirect (the address is a register value) and register-indirect with displacement (address = register + signed offset). MIPS exemplifies this minimalism: all memory operations use one of these two modes, encoded in a single 16-bit offset field. To load from a complex address like `array[index * 8 + base_offset]`, MIPS requires separate instructions to compute the address in a register, then load from it.

By contrast, x86-64 supports a rich addressing mode called "scale-index-base" (SIB), where the address is computed as `base + (index * scale) + displacement`. The scale factor can be 1, 2, 4, or 8, making it trivial to access arrays of 1-byte, 2-byte, 4-byte, or 8-byte elements. A single x86 instruction like `mov rax, [rbx + rcx * 8 + 16]` loads from address `rbx + rcx*8 + 16` directly. MIPS would require three instructions: left-shift `rcx` by 3 (multiply by 8), add to `rbx`, then load.

The deeper engineering rationale reveals itself when you consider register allocation and instruction scheduling. In MIPS, computing a complex address requires intermediate registers and separate instructions. In x86, the address computation is "free"—it happens in the address generation unit without consuming a general-purpose register or a pipeline slot. However, x86's hardware must decode this complex addressing mode and compute the final address, which increases the critical path of the load instruction. MIPS keeps the load instruction simple, deferring address computation to prior instructions that can execute in parallel.

Modern ARM (ARV8) takes a middle ground: it provides base + displacement and indexed modes but no scale factor in the addressing hardware. To access an array element, ARM software typically pre-computes the scaled index in a register, then uses that as the index in the address calculation. This reduces addressing complexity compared to x86 while remaining more powerful than MIPS's minimal modes.

### Register Files and Calling Conventions

The register file is the ISA's scratchpad memory—the fastest, most accessible storage available to instructions. A wider register file (more registers) allows the compiler's register allocator to keep more live values in registers rather than spilling them to the stack. Spilling is expensive: it requires a store instruction to write to stack memory, then a load instruction to read it back later. Each store/load pair may incur cache misses if the stack working set exceeds cache capacity, causing stalls of tens or hundreds of cycles.

MIPS defines 32 general-purpose registers (GPRs), each 32 bits wide (or 64 bits in MIPS-64). By convention, register 0 is always hardwired to zero (writes to it are ignored), making it a source of free zeroes and simplifying logic. SPARC similarly defines 32 GPRs, though with an unusual overlapping-register-window architecture where the register file actually contains 128 physical registers, partitioned into four overlapping windows to accelerate function calls.

ARM AArch64 (64-bit ARM) defines 31 general-purpose registers (X0–X30), plus a zero register (XZR). The reduction from 32 to 31 is a pragmatic choice: dedicating one register as always-zero saves chip area and simplifies certain operations, and empirically, modern compilers are rarely bottlenecked by register pressure given 31 usable registers. However, this represents a smaller register file than MIPS or SPARC, placing slightly more pressure on register allocation and spilling.

x86-64 defines only 16 general-purpose registers (RAX, RBX, RCX, RDX, RSI, RDI, R8–R15), each 64 bits wide. This is historically constrained—the 8086 (1978) defined only 8 registers, and the evolution to 16 registers in x86-64 (2003) was a major architectural expansion. The small register file means that even modest functions must spill temporaries to the stack. A compiler targeting x86-64 must carefully allocate registers because running out forces expensive memory accesses.

The ISA must also establish a *calling convention*—the contract between a caller and callee regarding which registers are "live" at a function call boundary. When function A calls function B, how does A know which registers B will clobber? If B is free to clobber any register, then A must save all registers to the stack before the call. If B is only allowed to clobber certain registers (and must preserve others), then A saves only those registers B might clobber.

The System V AMD64 ABI (Application Binary Interface), used on x86-64 in Unix-like systems, defines that RBX, RBP, R12–R15 are *callee-saved* (the callee must restore them) and RAX, RCX, RDX, RSI, RDI, R8–R11 are *caller-saved* (the caller must save them if it needs them across the call). This convention allows the callee to preserve certain registers without costly saves/restores, but the caller must save any caller-saved registers it is using before making a call. The tradeoff reflects the reality that most functions are leaf functions (they don't call other functions) and can exploit callee-saved registers to minimize stack traffic.

ARM's AArch64 ABI defines X19–X29 as callee-saved and X0–X18, X30 as caller-saved, with X29 (FP) and X30 (LR, link register) having special roles in stack frames. The larger callee-saved set (11 registers vs. x86's 5) reflects ARM's larger register file, encouraging functions to use callee-saved registers and reducing save/restore overhead.

### The Instruction Fetch-Execute Model

An ISA defines not only what instructions do but also the order in which they execute. The *sequential execution model* is the conceptual baseline: instructions execute in program order, each completing fully (all side effects visible) before the next instruction starts. This is what a programmer sees when writing assembly or C code. The reality in modern processors is dramatically more complex—instructions are fetched, decoded, and issued speculatively out of order, with results forwarded to dependent instructions before earlier instructions complete—but the ISA must guarantee that the *observable behavior* remains consistent with sequential semantics. If a program writes to memory location X, then reads from X, the read must see the write, even if the processor internally reordered them.

This contract is enforced by memory consistency models. The ISA specifies which reorderings are visible to the program. For example, many ISAs guarantee that a *store* followed by a *load* from the same address will always see the store's result (store-load forwarding), but they may allow a load followed by a store to a different address to be reordered in the program's observable behavior, as long as no other processor or I/O device observes the reordering. This is the essence of the *memory model*—it defines which memory orderings are guaranteed and which are not, allowing hardware to optimize aggressively while preserving correctness.

RISC-V defines a relatively weak memory model: stores and loads to different addresses can be reordered unless explicitly synchronized with a fence instruction. x86-64 defines a stronger model: stores are always visible in program order (a load cannot pass a prior store to a different address), making x86 easier to reason about but slightly more expensive to implement because the memory subsystem must enforce stricter ordering. ARM AArch64 is similar to RISC-V: it allows aggressive reordering but provides explicit synchronization instructions (barriers) for cases where ordering must be preserved.

### Immediate Encoding and Operand Size Trade-offs

Instructions must encode not only register references but also immediate (constant) values. An immediate is a small constant encoded directly in the instruction word, allowing operations like "add register X to the constant 5" without requiring a separate load instruction. The challenge is that the immediate must fit in a limited number of bits within the instruction word.

MIPS I-format instructions allocate 16 bits for the immediate, allowing constants from -32768 to 32767 (or 0 to 65535 unsigned). For larger constants, MIPS provides the `lui` (load upper immediate) instruction, which loads a constant into the upper 16 bits of the register, then an `addi` instruction adds a 16-bit immediate to the lower bits. Loading a 32-bit constant requires two instructions.

ARM AArch64 improves on this with a more sophisticated immediate encoding: the immediate is represented as an 8-bit constant rotated right by an even number of positions (0, 2, 4, ..., 30 bits). This allows commonly used constants like 0xFF (255), 0xFFFF (65535), 0x1000 (4096), and many bit masks to be encoded in a single instruction, while still keeping the immediate field to 12 bits. Larger constants still require two instructions (using `movz` and `movk` to build up the value) but the scheme is more efficient for typical immediates.

x86-64 allows 32-bit immediates in some instructions (like `mov rax, 0x12345678`), but the instruction becomes longer to accommodate it. The tradeoff is that x86 instructions vary in length, while RISC instructions maintain fixed width.

The choice of immediate encoding size reflects assumptions about software patterns. If compilers frequently generate instructions with small immediates (which they do—most immediates are offsets to array elements, structure fields, or stack frames), then efficient immediate encoding for small values is worthwhile. If large immediates are rare, it is acceptable to require multi-instruction sequences to build them up.

## 3. High-Performance Optimization & Failure Modes

### Register Allocation and Spill Pressure

A compiler using a given ISA must allocate the available registers to hold program variables. If a function has more than N live variables (where N is the number of general-purpose registers), the compiler must *spill*—store some variables to stack memory, freeing up a register for others. A spill requires a store instruction (copying the register to the stack) and later a load instruction (restoring the variable), each potentially incurring memory latency.

Consider a function computing a complex expression across many statements. In MIPS with 32 registers, the compiler can often keep all intermediate results in registers. The same function on x86-64, with only 16 registers and several reserved for special purposes (RSP for stack pointer, RBP for frame pointer in some calling conventions), may spill dozens of times. Each spill adds 4–5 cycles of latency (a store to cache and a later load from cache). If a hot loop spills frequently, the performance loss can be 20–50%.

This is why ARM AArch64, with 31 registers, tends to achieve better code quality than x86-64 for register-intensive computations. The extra registers allow the compiler to keep more values live, reducing spills. Empirically, a function that fits in 24 registers on ARM will likely require 2–4 spills on x86-64, increasing runtime by 10–15% for register-intensive workloads.

Compiler writers combat spill pressure through aggressive optimization: *live range analysis* determines which variables are simultaneously live, *register coalescing* merges variables that never interfere, and *rematerialization* recomputes a value instead of spilling it if the computation is cheaper than memory access. Nevertheless, the underlying ISA register count is a fundamental constraint that no optimization can fully overcome.

### Instruction Density and Instruction Cache Misses

Code density—how many bytes of memory are required to express a given algorithm—directly impacts instruction cache utilization. An ISA with variable-length instructions (like x86, which ranges from 1 to 15 bytes per instruction) can achieve better density than a fixed 32-bit ISA (where each instruction is 4 bytes) if the algorithm uses many simple, short instructions. A function that fits in 100 bytes on x86 might require 200 bytes on MIPS, occupying twice the cache footprint.

For workloads where instruction cache is a bottleneck—such as web servers handling thousands of requests with diverse code paths, or OS kernels context-switching between many processes—dense code is valuable. x86's variable-length instructions and memory-operand addressing modes pack more computation into fewer bytes. The penalty is that the decoder must work harder.

Conversely, for code that fits comfortably in the instruction cache—such as a tight loop or a single-threaded computational kernel—code density is irrelevant. MIPS, ARM, and RISC-V code for such workloads runs just as fast as x86, despite the larger instruction footprint, because both fetch quickly from cache.

The ISA designer must choose: prioritize density (variable-length, memory operands, complex addressing) and accept decode complexity, or prioritize simplicity (fixed-length, register operands, simple addressing) and accept larger code size. Modern processors partly decouple these choices through microcode or the microinstruction cache, decoding x86 instructions once and storing the µops for reuse. But this adds silicon and power overhead.

### Out-of-Order Execution and Memory Dependencies

The ISA defines the data dependencies between instructions: if instruction A writes to register X and instruction B reads from register X, there is a *data dependency* between them; B cannot execute until A's result is available. The hardware's job is to respect these dependencies while executing as many independent instructions in parallel as possible.

Consider a sequence like:

```
add r1, r2, r3       ; r1 = r2 + r3
add r4, r1, r5       ; r4 = r1 + r5 (depends on r1)
mul r6, r7, r8       ; r6 = r7 * r8 (independent)
sub r9, r4, r10      ; r9 = r4 - r10 (depends on r4, which depends on r1)
```

In sequential execution, these instructions take 4 cycles (assuming each completes in 1 cycle). In out-of-order execution, the processor can issue the `mul` instruction in parallel with the `add r1` and `add r4` instructions, as long as the hardware tracks the data dependency chain. The `mul` will execute simultaneously with the adds, completing on the same cycle as `r4` is ready. This instruction-level parallelism (ILP) is one of the primary sources of performance in modern processors.

However, memory operations create a subtle complication. Consider:

```
load r1, [r2]         ; r1 = *r2 (read from memory)
add r3, r1, r4        ; r3 = r1 + r4 (depends on load result)
store r3, [r5]        ; *r5 = r3
```

The load instruction's result is not known until the memory access completes, which may take 4–400 cycles depending on whether the data is in the L1 cache, L2, L3, or main memory. The dependent add instruction cannot start until the load result arrives. To hide this latency, the processor must execute other independent instructions while the load is pending.

The ISA's addressing mode choices influence how effectively the processor can parallelize memory operations. An ISA with simple addressing modes (base + displacement only) makes it easy for the processor to predict which memory locations a sequence of loads/stores will access, allowing prefetching and cache optimization. An ISA with complex addressing modes (like x86's scale-index-base) makes prediction harder because the address depends on the index register's current value, which may be unknown until a prior instruction completes.

For example, a loop like:

```
loop:
  mov rax, [rbx + rcx*8]    ; load array[i]
  add rax, rdx
  mov [rbx + rcx*8 + 16], rax ; store result
  add rcx, 1
  cmp rcx, rsi
  jl loop
```

The second store address depends on rcx, which is only known after the `add rcx, 1` completes. The processor must stall or speculate about the store address, potentially misspeculating and requiring recovery. A simpler ISA might use explicit address registers:

```
loop:
  mov rax, [rsi]           ; load from [rsi]
  add rax, rdx
  mov [rsi + 16], rax      ; store with simple displacement
  add rsi, 8               ; increment pointer
  cmp rsi, rdi
  jl loop
```

Here, the store address is known as soon as the prior store retires, and prefetching is more predictable. The fundamental tradeoff is again between instruction density (x86's scale-index-base is compact) and execution latency (simpler addressing enables better prefetching).

### Pipeline Hazards and Forwarding

An ISA's instruction semantics can create pipeline hazards—situations where the processor must stall because instruction dependencies cannot be resolved quickly. The primary hazard types are:

**Data hazards** occur when an instruction needs a value produced by a prior instruction bef
