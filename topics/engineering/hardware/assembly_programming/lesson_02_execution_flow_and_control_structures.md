# Lesson 2: Execution Flow, Control Structures, Flags

## 1. First-Principles Intuition & Invariants

The beating heart of any processor—whether x86-64, ARM64, or a modest 8-bit microcontroller—is the fetch-decode-execute cycle, a relentless loop that has remained conceptually unchanged since von Neumann first articulated the stored-program machine model in 1945. Yet understanding this cycle with sufficient depth to write performant, debuggable assembly requires more than memorizing instruction formats. You must internalize how the processor's state machine governs the flow of control, how condition codes encode the outcome of prior arithmetic operations, and how the hardware pipeline creates feedback loops between instruction dependencies and execution latency.

At the assembly level, your code exists in a tension between two worlds: the logical, sequential world of the program as written (in memory, as bytes), and the dynamic, pipelined world of the processor's execution units. A branch instruction is not simply a jump; it is a signal to the fetch unit to redirect the instruction stream, disrupting the pipeline and incurring a stall penalty. A conditional branch is even more complex: the processor must evaluate a condition code—itself the residue of a prior operation—and make a speculative prediction about the branch outcome to keep the pipeline full. When that prediction fails, the pipeline must flush.

This lesson peels back the abstraction layers to expose these mechanisms. We will trace instruction flow through real processor pipelines, dissect the condition code registers (RFLAGS in x86-64, PSTATE in ARM64), and build complete, compilable examples of branching, looping, and function calls that execute correctly on real hardware. The goal is not merely to understand *what* happens when you write a branch; it is to understand *why* it happens, at what latency cost, and how to structure your code to minimize pipeline stalls and maximize instruction-level parallelism.

The invariants that anchor this lesson are as follows: (1) The processor fetches, decodes, and executes instructions in a deterministic order dictated by the program counter (PC) register; branching instructions redirect the PC. (2) Condition codes are updated as a side effect of arithmetic and logical instructions; conditional branches consume these flags to determine the next instruction address. (3) The CPU pipeline overlaps the fetch, decode, and execute stages; control flow changes (branches) disrupt this overlap, incurring a pipeline flush penalty. (4) Function calls and returns are implemented using the call stack and link register, with strict conventions governing how registers and stack space are allocated and freed. (5) Optimizing control flow requires understanding both the latency of branch instructions and the predictability of branch patterns, since modern processors use sophisticated branch prediction hardware to speculate ahead.

## 2. Core Architecture & Mechanics

### The Fetch-Decode-Execute Cycle and Pipeline Stages

To reason about assembly code, you must model the processor as a state machine with explicit stages. The simplest model—the unpipelined, single-cycle processor—executes one instruction per clock cycle: in phase 1, the instruction at the program counter is fetched from memory; in phase 2, the instruction is decoded to extract the opcode and operands; in phase 3, the arithmetic logic unit (ALU) performs the operation; in phase 4, the result is written back to the register file or memory. This single-cycle model is instructive but bears little resemblance to modern processors, which exploit parallelism by overlapping these stages.

A classic five-stage pipeline partitions the execute cycle into five independent phases that operate in parallel on different instructions:

**Stage 1 (Fetch):** The instruction fetch unit reads the instruction at the address in the program counter from the L1 instruction cache, increments the PC (or loads a new PC if the prior instruction was a branch), and pushes the instruction into the decode stage.

**Stage 2 (Decode):** The instruction decoder extracts the opcode, operand specifiers, and immediate values; accesses the register file to read source operands; and pushes the decoded instruction to the execute stage.

**Stage 3 (Execute):** The ALU performs the arithmetic or logical operation on the operands, computes branch target addresses, or calculates memory addresses for load/store operations. Condition codes are updated based on the ALU result.

**Stage 4 (Memory):** Load and store instructions access the L1 data cache; other instructions pass through this stage without action.

**Stage 5 (Write-Back):** Results are written to the register file or—in the case of stores—committed to memory.

Under ideal conditions (no data dependencies, no branches), the pipeline sustains one instruction per cycle throughput once it is primed. A three-instruction sequence might look like this:

```text
Cycle 1: Fetch(I1)
Cycle 2: Fetch(I2)  Decode(I1)
Cycle 3: Fetch(I3)  Decode(I2)  Execute(I1)
Cycle 4: Fetch(I4)  Decode(I3)  Execute(I2)  Memory(I1)
Cycle 5: Fetch(I5)  Decode(I4)  Execute(I3)  Memory(I2)  WriteBack(I1)
```

However, this ideal is shattered when instructions have dependencies or when control flow changes occur. A data dependency arises when an instruction consumes the result of a prior instruction that has not yet written back. For instance, if instruction I1 computes a value into register X and instruction I3 immediately reads from X, the pipeline must stall: I3 cannot decode its operands until I1's result is available. A control dependency arises when a branch instruction redirects the instruction stream; the fetch unit cannot know which instruction to fetch next until the branch is resolved in the execute stage, forcing a bubble into the pipeline.

Let us trace a concrete example on a real five-stage x86-64 processor. Consider the following fragment:

```asm
mov rax, 0x1000       ; Load immediate
add rbx, rax          ; Add rax to rbx
jmp target            ; Unconditional branch
```

**Cycle 1:** The fetch unit loads the MOV instruction and increments PC to the next address.
**Cycle 2:** The MOV is decoded; operands are read (none are data dependencies here). Fetch loads the ADD.
**Cycle 3:** MOV executes in the ALU (result: 0x1000 in rax). Decode the ADD; the register file is read, but rax has not yet written back.
**Cycle 4:** The ADD stalls in the decode stage (data dependency on rax). The fetch stage is also blocked; the JMP has not been reached yet.
**Cycle 5:** MOV writes back (rax = 0x1000). ADD decodes and reads the now-available rax from the register file. Fetch loads the JMP.
**Cycle 6:** ADD executes. Fetch cannot proceed (waiting for JMP to be resolved).
**Cycle 7:** ADD writes back (rbx updated). JMP executes in the ALU (target address is computed).
**Cycle 8:** JMP writes back (PC loaded with target address). Fetch flushes the pipeline and begins fetching from the target.

The JMP causes a pipeline flush: any instructions that were fetched speculatively (between the JMP and its resolution) are discarded, and the pipeline must restart from the branch target. Modern processors mitigate this penalty through branch prediction: the fetch unit maintains a branch prediction unit (BPU) that speculates about the branch outcome before it is resolved, allowing the pipeline to continue fetching instructions without stalling. When the prediction is correct, the penalty is zero. When the prediction is wrong, the pipeline flushes and restarts from the correct address, incurring a penalty of several cycles (typically 10–20 cycles on modern superscalar processors).

### Condition Codes and Flag Registers

Condition codes are special registers that encode the outcome of prior arithmetic or logical instructions. They are the substrate upon which conditional branching is built. In x86-64, condition codes are stored in the lower 8 bits of the RFLAGS register; in ARM64, they are stored in the PSTATE register. Understanding these registers in minute detail is essential to writing efficient branching code.

**x86-64 RFLAGS Register:**

The RFLAGS register is 64 bits, but only the lower 16 bits are typically of interest to assembly programmers. The key condition code flags are:

- **CF (Carry Flag, bit 0):** Set if an unsigned arithmetic operation produced a result that overflowed the destination width (or underflowed below zero). For example, adding two 64-bit unsigned integers whose sum exceeds 2^64 sets CF. CF is also set by shift instructions to capture the bit shifted out of the destination.

- **PF (Parity Flag, bit 2):** Set if the least significant byte of the result has an even number of 1-bits. This flag is rarely used in modern code but is essential for error-checking algorithms (Hamming codes, checksums).

- **AF (Auxiliary Carry Flag, bit 4):** Set if an arithmetic operation produced a carry from bit 3 to bit 4 (used for BCD arithmetic on legacy systems; rarely used in modern x86-64 code).

- **ZF (Zero Flag, bit 6):** Set if the result is zero. This is one of the most frequently tested flags in branching code.

- **SF (Sign Flag, bit 7):** Set if the result is negative (i.e., the most significant bit of the result is 1, interpreted as a two's complement signed integer). For a 64-bit result, SF reflects bit 63.

- **OF (Overflow Flag, bit 11):** Set if a signed arithmetic operation produced a result that overflowed the range of signed integers representable in the destination width. For 64-bit signed integers, OF is set if the result is outside the range [−2^63, 2^63 − 1].

- **DF (Direction Flag, bit 10):** Controls the direction of string operations (CLD clears it, STD sets it); rarely used in modern code.

These flags are updated as a **side effect** of most arithmetic and logical instructions (ADD, SUB, AND, OR, XOR, etc.) but not by MOV, LEA (load effective address), or load/store instructions. The TEST instruction (logically ANDs two operands and discards the result, updating flags) is a common idiom for testing conditions without modifying a register.

**ARM64 PSTATE Condition Flags:**

In ARM64, condition flags are stored in the PSTATE register (Program State), specifically in the lower 4 bits (N, Z, C, V). These are conceptually similar to x86-64 but with different names and slightly different semantics:

- **N (Negative Flag):** Set if the result is negative (bit 63 of a 64-bit result is 1).
- **Z (Zero Flag):** Set if the result is zero.
- **C (Carry Flag):** Set if an unsigned arithmetic operation overflowed or if a shift operation shifted a 1 out of the destination.
- **V (Overflow Flag):** Set if a signed arithmetic operation overflowed.

Instructions like ADD, SUB, AND, ORR update PSTATE flags when the `S` (set flags) suffix is appended (e.g., `ADDS` instead of `ADD`). Without the `S` suffix, flags are not modified.

### Conditional Branch Instructions and the Branch Predicate

Conditional branch instructions test a condition (derived from the flags) and redirect the program counter if the condition is true. The condition is encoded in the instruction itself, typically in a 4-bit condition code field. Both x86-64 and ARM64 use similar mnemonic conventions: JE (jump if equal, i.e., if ZF is set) in x86-64 corresponds to B.EQ (branch if equal) in ARM64.

**Common x86-64 conditional branches:**

- **JE (Jump if Equal):** Branch if ZF is set (result of prior operation was zero).
- **JNE (Jump if Not Equal):** Branch if ZF is clear (result was non-zero).
- **JG (Jump if Greater):** Branch if the prior signed comparison result is greater. This tests (ZF == 0) AND (SF == OF).
- **JL (Jump if Less):** Branch if the prior signed comparison result is less. This tests (SF != OF).
- **JGE (Jump if Greater or Equal):** Branch if (SF == OF).
- **JLE (Jump if Less or Equal):** Branch if (ZF == 1) OR (SF != OF).
- **JA (Jump if Above):** Branch if the prior unsigned comparison result is greater. This tests (CF == 0) AND (ZF == 0).
- **JB (Jump if Below):** Branch if (CF == 1).
- **JAE (Jump if Above or Equal):** Branch if (CF == 0).
- **JBE (Jump if Below or Equal):** Branch if (CF == 1) OR (ZF == 1).
- **JO (Jump if Overflow):** Branch if (OF == 1).
- **JNO (Jump if No Overflow):** Branch if (OF == 0).
- **JS (Jump if Sign):** Branch if (SF == 1).
- **JNS (Jump if No Sign):** Branch if (SF == 0).

**Common ARM64 conditional branches:**

- **B.EQ:** Branch if equal (ZF == 1).
- **B.NE:** Branch if not equal (ZF == 0).
- **B.GT:** Branch if greater (signed). Tests (ZF == 0) AND (N == V).
- **B.LT:** Branch if less (signed). Tests (N != V).
- **B.GE:** Branch if greater or equal (signed). Tests (N == V).
- **B.LE:** Branch if less or equal (signed). Tests (ZF == 1) OR (N != V).
- **B.HI:** Branch if higher (unsigned). Tests (C == 1) AND (Z == 0).
- **B.LO:** Branch if lower (unsigned). Tests (C == 0).
- **B.HS:** Branch if higher or same (unsigned). Tests (C == 1).
- **B.LS:** Branch if lower or same (unsigned). Tests (C == 0) OR (Z == 1).
- **B.VS:** Branch if overflow set (V == 1).
- **B.VC:** Branch if overflow clear (V == 0).

The key insight is that every conditional branch consumes the state of the condition flags set by a **prior instruction**. This creates a dependency: the branch cannot be resolved until the prior instruction has executed and updated the flags. This dependency is one of the primary sources of pipeline stalls in assembly code.

### The CMP and TEST Instructions

The CMP (compare) instruction is a critical idiom for testing relationships without modifying registers. CMP subtracts the second operand from the first and updates the flags, but discards the result. This allows you to test whether two values are equal, ordered (greater/less), or have overflowed without using a register to hold the result.

For example:

```asm
cmp rax, rbx
jg greater_than
jl less_than
je equal
```

The CMP instruction computes rax - rbx, updates ZF, SF, and OF based on the result, and then discards the subtraction result. The subsequent conditional branches consume the flags. Similarly, TEST performs a bitwise AND without storing the result, updating flags to indicate whether the result is zero or negative:

```asm
test rax, rax
jz is_zero
```

This fragment tests whether rax is zero without modifying it.

### Absolute Versus Relative Addressing in Branches

Branch instructions can target addresses in two ways: absolute addressing (jump to a fixed memory address) or relative addressing (jump forward or backward by a fixed offset). Relative addressing is far more common in modern code because it enables position-independent executables (PIE) and reduces the complexity of relocation during linking.

In x86-64, most branch instructions use a signed 32-bit relative offset, which allows jumps within a ±2 GB range from the current instruction. For example, JE 0xabcd means "if equal, jump to the instruction at address (PC + 0xabcd)". The assembler computes this offset based on the label you provide.

In ARM64, conditional branches use a signed 19-bit relative offset (allowing jumps within ±1 MB), while unconditional branches (B) use a signed 26-bit offset (allowing jumps within ±128 MB).

Understanding the addressing mode is crucial for debugging and performance: a relative branch incurs no additional cost compared to an absolute branch, but relative branches must be recomputed if code is relocated, whereas absolute branches may require relocation entries in the binary.

### Loop Constructs and the LOOP Instruction Family

The x86-64 instruction set includes a family of LOOP instructions that automate common looping patterns. These instructions decrement RCX and conditionally branch based on the result:

- **LOOP label:** Decrement RCX. If RCX != 0, jump to label.
- **LOOPE label:** Decrement RCX. If RCX != 0 AND ZF == 1, jump to label.
- **LOOPNE label:** Decrement RCX. If RCX != 0 AND ZF == 0, jump to label.

For example:

```asm
mov rcx, 10
loop_start:
  ; loop body
  loop loop_start
```

This loop executes 10 times. However, modern processors handle LOOP instructions poorly: they are microcode-decoded into multiple fused operations, creating pipeline hazards. In performance-critical code, it is far more efficient to manually decrement a counter and use a conditional branch:

```asm
mov rcx, 10
loop_start:
  ; loop body
  dec rcx
  jnz loop_start
```

This achieves the same result with better pipeline behavior because DEC and JNZ are separate instructions that the processor can schedule more flexibly.

### Function Prologue, Epilogue, and the Call Stack

Functions are implemented using the call stack, a region of memory (typically in RAM) that stores return addresses, local variables, and spilled registers. The x86-64 calling convention (System V ABI, used on Unix-like systems) designates specific registers for passing arguments and returning results, and requires the caller to preserve certain registers across function calls (caller-saved) while the callee preserves others (callee-saved).

The CALL instruction pushes the return address (the address of the instruction immediately following the CALL) onto the stack and jumps to the target function. The RET instruction pops the return address from the stack and jumps to it, resuming execution in the caller.

A typical function prologue in x86-64 looks like this:

```asm
push rbp              ; Save the old frame pointer
mov rbp, rsp          ; Establish a new frame pointer
sub rsp, local_size   ; Allocate space for local variables
push rbx              ; Save callee-saved registers (if needed)
push r12
```

The prologue establishes a new stack frame by saving the old frame pointer, establishing a new one, and allocating space for local variables. Callee-saved registers (RBX, R12–R15, RBP, RSP) are saved if the function uses them; the caller-saved registers (RAX, RCX, RDX, RSI, RDI, R8–R11) do not need to be saved by the callee.

The epilogue reverses this process:

```asm
pop r12               ; Restore callee-saved registers
pop rbx
mov rsp, rbp          ; Deallocate local variables
pop rbp               ; Restore the old frame pointer
ret                   ; Return to the caller
```

In ARM64, the calling convention is similar but uses different registers. The stack pointer is X31 (SP), and the frame pointer is X29 (FP). A typical prologue allocates stack space and saves registers:

```asm
sub sp, sp, #local_size    ; Allocate stack space
stp x29, x30, [sp]         ; Save frame pointer and link register
mov x29, sp                ; Establish new frame pointer
```

The epilogue restores the registers and deallocates the stack:

```asm
ldp x29, x30, [sp]         ; Restore frame pointer and link register
add sp, sp, #local_size    ; Deallocate stack space
ret                        ; Return to caller
```

### Pipeline Hazards and Dependency Chains

The three primary pipeline hazards are structural hazards (resource conflicts), control hazards (branch mispredictions), and data hazards (dependencies between instructions).

**Data Hazards** arise when an instruction depends on the result of a prior instruction that has not yet written back. There are three types:

1. **Read-After-Write (RAW):** Instruction I2 reads a register that I1 writes. Example:

```asm
add rax, rbx       ; I1: writes rax
mov rcx, rax       ; I2: reads rax
```

In a five-stage pipeline, I1 writes back in cycle 5, but I2 decodes in cycle 2 (before I1 has written). I2 must stall until rax is available. Modern processors use **register renaming** to partially mitigate this: instructions are renamed to internal physical registers so that I1 and I2 can use different physical registers internally, reducing stalls. However, true dependencies (where I2 genuinely needs I1's result) cannot be eliminated.

2. **Write-After-Read (WAR):** Instruction I2 writes a register that I1 reads. This is an antidependency: it arises when out-of-order execution would cause I2's write to be visible to I1. Modern processors track these through register renaming.

3. **Write-After-Write (WAW):** Instruction I2 writes a register that I1 writes. This is an output dependency. If I1 and I2 are executed out of order, the final value of the register may be wrong. Register renaming again mitigates this.

**Control Hazards** arise when the processor cannot know the next instruction address until a branch is resolved. For an unconditional branch, the target is deterministic but still not available until the branch executes. For a conditional branch, the processor does not know whether to branch or fall through until the condition is evaluated. Modern branch prediction hardware attempts to speculate: the branch prediction unit maintains a branch history table (BHT) and predicts whether each conditional branch will be taken or not taken based on past outcomes. If the prediction is correct, the pipeline continues without stalling. If incorrect, the pipeline flushes and restarts from the correct address, incurring a penalty.

**Structural Hazards** arise when multiple instructions contend for the same hardware resource. For instance, only one instruction can write to the register file in a given cycle; if two instructions try to write in the same cycle, one must stall. Superscalar processors (which issue multiple instructions per cycle) are designed to avoid structural hazards through replication of resources (multiple ALUs, multiple memory ports, etc.).

## 3. High-Performance Optimization & Failure Modes

### Instruction Scheduling and Dependency Chains

Optimizing assembly code for performance requires understanding dependency chains: sequences of instructions where each instruction depends on the prior one, forcing the processor to execute them sequentially rather than in parallel. The length of the longest dependency chain is the **critical path latency**, which determines the minimum number of cycles needed to execute a block of code.

Consider the following loop that sums an array:

```asm
xor rax, rax           ; rax = 0 (accumulator)
xor rcx, rcx           ; rcx = 0 (index)
mov r8, 1000           ; r8 = array size

loop_start:
  mov rbx, [rdi + rcx*8]   ; rbx = array[rcx]
  add rax, rbx             ; rax += rbx
  add rcx, 8               ; rcx += 8
  cmp rcx, r8              ; compare rcx to 1000
  jl loop_start            ; if rcx < 1000, loop
```

This loop has a critical dependency chain in the accumulation path: MOV reads from memory into RBX, then ADD adds RBX to RAX, then in the next iteration, ADD accesses RAX again. If the memory load latency is 4 cycles and the ADD latency is 1 cycle, the critical path is 4 + 1 = 5 cycles per iteration. The processor cannot overlap iterations because each iteration depends on the prior iteration's accumulator value.

One optimization is **loop unrolling with multiple accumulators**, which breaks the dependency chain by using several accumulators and adding them at the end:

```asm
xor rax, rax           ; accumulator 1
xor rbx, rbx           ; accumulator 2
xor r9, r9             ; accumulator 3
xor r10, r10           ; accumulator 4
xor rcx, rcx           ; index
mov r8, 1000           ; array size

loop_start:
  mov r11, [rdi + rcx*8]        ; load element
  add rax, r11                  ; accumulator 1
  mov r11, [rdi + rcx*8 + 8]    ; load next element
  add rbx, r11                  ; accumulator 2
  mov r11, [rdi + rcx*8 + 16]   ; load next element
  add r9, r11                   ; accumulator 3
  mov r11, [rdi + rcx*8 + 24]   ; load next element
  add r10, r11                  ; accumulator 4
  add rcx, 32                   ; advance index by 4 elements
  cmp rcx, r8
  jl loop_start

; Final accumulation
add rax, rbx
add rax, r9
add rax, r10
```

By using four separate accumulators, the dependency chain in each iteration is now only 1 cycle (the load and add operate on different accumulators), so the processor can issue 4 load-add pairs in parallel. This increases throughput from 1 element per 5 cycles to 4 elements per 5 cycles, a 4x speedup.

This optimization trades increased register pressure and code size for reduced critical path latency.

## Conclusion

Control flow and execution optimization in assembly require a deep understanding of both the logical semantics of branching constructs and the microarchitectural realities of modern processors. While conditional jumps, loops, and subroutines provide the fundamental abstractions for structured control flow, their performance characteristics are governed by branch prediction accuracy, pipeline depth, and instruction-level parallelism. The flags register serves as the critical intermediary between computational results and control decisions, with each arithmetic or logical operation implicitly updating condition codes that subsequent branch instructions consume. Mastery of assembly control structures demands recognizing when high-level patterns like `if-then-else` or `while` loops map cleanly to jump sequences, and when architectural constraints—such as branch misprediction penalties or data dependency chains—necessitate aggressive optimization techniques like branchless selection, loop unrolling, or software pipelining.

The performance transformations demonstrated in loop optimization exemplify a central tension in systems programming: the semantic correctness of control flow constructs versus their execution efficiency on specific hardware. A naive loop structure that produces correct results may execute 4-5× slower than a dependency-chain-optimized variant that uses multiple accumulators or predication to expose instruction-level parallelism. Similarly, a branch-heavy decision tree may incur 15-20 cycle penalties per misprediction, while an equivalent branchless implementation using conditional moves executes in deterministic time regardless of input patterns. These optimization decisions cannot be made in isolation—they require profiling actual workloads, understanding the target processor's execution units and pipeline characteristics, and balancing code complexity against performance gains. The engineer's role is to recognize when control flow is the bottleneck, apply the appropriate microarchitectural optimization, and verify the result through measurement rather than assumption.

## Summary & Verification Matrix

| **Concept** | **Governing Invariant** | **Core Mechanism** | **Diagnostic Criterion** |
|-------------|-------------------------|-------------------|--------------------------|
| **Conditional Jumps** | Control transfer occurs iff specified flag condition is satisfied after TEST/CMP | Arithmetic/logical operations set FLAGS; Jcc reads FLAGS and updates RIP conditionally | Branch misprediction penalty: 10-20 cycles on modern x86; verify with `perf stat -e branch-misses` |
| **Loop Constructs** | LOOP decrements RCX and jumps iff RCX ≠ 0; manual loops use CMP+Jcc for arbitrary conditions | Counter register (RCX for LOOP, any register for manual) + conditional backward jump | Loop-carried dependencies limit ILP; critical path latency = max(load latency + dependent op latency) per iteration |
| **Subroutine Linkage** | CALL pushes return address then jumps; RET pops return address into RIP | Hardware return stack predicts RET targets; stack pointer (RSP) maintains call frame chain | Return stack depth (16-32 entries); overflow causes ~20-cycle misprediction; verify with `perf stat -e rs_events.empty_end` |
| **Branchless Selection** | CMOVcc updates destination iff condition true, otherwise destination unchanged | Predicated execution eliminates branch; both paths compute, condition selects result | Effective when: branch mispredict cost > max(both-path-cost); verify with cycle count comparison, not branch counters |
| **Loop Unrolling with Multiple Accumulators** | Breaking dependency chains exposes ILP by using independent registers across iterations | N accumulators process N elements per iteration; final reduction combines accumulators | Speedup ≈ min(unroll_factor, execution_width / critical_path_length); measure with wall-clock time or cycle counters |
| **Flags Register Behavior** | FLAGS updated implicitly by most arithmetic/logic ops; explicitly tested by Jcc/SETcc/CMOVcc | CF, ZF, SF, OF, PF, AF encode result properties; sequential ops overwrite prior flags | Use LAHF/PUSHFQ to snapshot flags; never assume flags persist across function calls without explicit save/restore |
