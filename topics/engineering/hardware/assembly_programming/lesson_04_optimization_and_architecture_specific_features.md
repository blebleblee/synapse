# Lesson 4: Optimization Techniques, SIMD, Architecture Extensions

## 1. First-Principles Intuition & Invariants

Modern processors are not infinitely fast. The gap between peak instruction throughput and real-world application performance is measured in orders of magnitude. A CPU capable of executing billions of instructions per second still spends much of its time stalled—waiting for cache misses to resolve, for dependent operations to complete, or for memory writes to propagate through the hierarchy. The fundamental task of optimization is to understand *why* this stalling occurs and to restructure code in ways that keep the processor pipeline full, exploit instruction-level parallelism (ILP), and make maximum use of specialized execution units.

This lesson begins with a foundational insight: modern processors are superscalar. They execute multiple instructions per clock cycle, but only when those instructions have no data dependencies and when the execution units are available. If instruction B depends on the result of instruction A, instruction B cannot execute until A completes—this is a *true data dependency*, and it cannot be optimized away. However, if instruction C is independent of both A and B, it *can* execute in parallel, provided the processor has a free execution unit and the instruction has been decoded and dispatched.

The processor's execution pipeline is a high-precision machine. Data flows through stages: fetch, decode, rename (on out-of-order cores), execute, memory access, and writeback. Each stage processes one or more instructions per cycle. When all stages are occupied with useful work, the pipeline is said to be "full." But pipelines stall—they introduce *bubbles*, empty cycles where no useful work occurs. Stalls are caused by data dependencies, cache misses, branch mispredictions, and resource contention (e.g., multiple instructions competing for a single execution unit).

Optimization is fundamentally about *scheduling*—arranging instructions so that independent operations are interleaved, allowing the pipeline to remain full. The x86-64 and ARM64 instruction sets expose scheduling opportunities through multiple execution ports, multiple cache hierarchies, and specialized units like SIMD (Single Instruction, Multiple Data) engines. SIMD is a particular form of data-level parallelism: one instruction operates on multiple data elements in a single register. A 256-bit AVX instruction can perform the same arithmetic operation on eight 32-bit integers simultaneously. This is not parallelism in the sense of multiple threads; it is parallelism within a single instruction stream.

Architecture-specific extensions—SSE, AVX, AVX-512 on x86-64, and NEON on ARM64—are not luxuries; they are essential for performance-critical code. Modern compilers attempt to vectorize loops automatically, but the compiler's view of the code is limited. A skilled assembly programmer can identify vectorization opportunities that a compiler misses, can structure loops to maximize cache locality, and can schedule instructions to minimize pipeline stalls.

The invariants we will explore in this lesson are these: First, *data dependencies are the primary limiter of performance*. Reducing dependencies or interleaving independent work is the primary lever for optimization. Second, *cache locality is the second limiter*. Memory bandwidth is finite, and latency is high. Code that repeatedly accesses the same small working set runs faster than code that randomly accesses large memory regions. Third, *SIMD parallelism is free*—the processor's execution units are already present; using them costs no extra clock cycles beyond what single-element operations would cost. Fourth, *branch prediction failure is expensive*. Modern processors speculatively execute code down a predicted branch path; if the prediction is wrong, the pipeline must be flushed and restarted. Minimizing branches and making branches predictable are key optimizations.

## 2. Core Architecture & Mechanics

### Instruction Scheduling and Pipeline Hazards

The x86-64 processor (we focus here on modern Intel and AMD implementations) executes instructions out of order. This does not mean instructions retire out of order—they do not—but rather that the processor decodes many instructions ahead of time, identifies dependencies, and executes them as soon as their operands are ready. This out-of-order execution engine is the reason why scheduling matters: the processor will find independent instructions and execute them in parallel if they are present in the decoded instruction window (typically 192 entries on a modern Core i9).

Consider a simple sequence:

```asm
mov rax, [rbx]        ; Load from memory into rax (latency ~4-12 cycles)
add rcx, rax          ; Add rax to rcx (depends on rax)
mov rdx, [rsi]        ; Load from memory into rdx (independent)
add r8, rdx           ; Add rdx to r8 (independent)
```

In this sequence, the first instruction loads `rax` from memory. On modern processors, this latency is typically 4 to 12 cycles, depending on whether the data is in the L1 cache, L2 cache, or main memory. The second instruction depends on `rax`, so it cannot execute until the load completes. However, the third and fourth instructions are independent of the first two. A modern out-of-order processor will dispatch the load from `rbx`, then dispatch the load from `rsi`, and while waiting for both loads to complete, it will execute the two add operations (assuming their operands are already available). The result is that the two independent operations are executed in parallel, reducing the overall latency.

This is a *data hazard*—specifically, a Read-After-Write (RAW) dependency. The processor's renaming logic handles this by assigning each register a physical register (distinct from the logical register visible to the programmer), allowing multiple versions of the same logical register to exist in the processor simultaneously. When the load writes to `rax`, it writes to a new physical register. The add instruction that depends on that load reads from the correct physical register. Instructions that do not depend on `rax` are unaffected and can execute in parallel.

There are two other types of data hazards. A Write-After-Read (WAR) hazard occurs when an instruction writes to a register after another instruction reads from it. For example:

```asm
mov rcx, rax          ; Read rax
mov rax, rbx          ; Write rax
```

Without register renaming, the write would appear to affect the read. But the processor renames `rax` in the second instruction to a new physical register, so there is no actual conflict. Similarly, a Write-After-Write (WAW) hazard occurs when two instructions write to the same register:

```asm
mov rax, rbx
mov rax, rcx
```

Again, renaming resolves this: each write is assigned a distinct physical register, and the second write implicitly invalidates the first.

*Control hazards* arise from branch instructions. When the processor encounters a branch, it does not know whether the branch will be taken. Modern processors use *branch predictors* to guess. If the guess is correct, execution proceeds smoothly. If the guess is wrong, the processor has speculatively executed instructions down the wrong path, wasting cycles. When the mispredict is detected, the pipeline is flushed (a *bubble* of typically 10–20 cycles is introduced), and execution resumes down the correct path. Minimizing branch misses is critical for performance.

The x86-64 processor typically has multiple execution ports, each capable of executing certain classes of instructions. A modern Intel Core i9 (Alder Lake generation) has six execution ports:

- Port 0: Arithmetic, logical, and shift operations; most scalar floating-point operations.
- Port 1: Arithmetic and logical operations; some floating-point operations.
- Port 2: Load operations (reading from memory).
- Port 3: Load operations.
- Port 4: Store operations (writing to memory).
- Port 5: Arithmetic, logical, and shift operations.

(These are simplifications; the actual port topology is more nuanced, but this gives the intuition.) If a program issues only arithmetic operations, they can execute in parallel across multiple ports. If a program issues many load operations, they compete for ports 2 and 3, creating a *resource conflict*. The processor can dispatch at most two load operations per cycle. If the program demands more, subsequent loads must wait.

### Loop Unrolling and Instruction-Level Parallelism

Loop unrolling is a classic optimization that exposes instruction-level parallelism. Consider a simple loop that adds a constant to each element of an array:

```asm
; rdi = pointer to array
; rsi = array length
; rdx = constant to add

xor rcx, rcx          ; rcx = loop counter (0)

.loop:
cmp rcx, rsi          ; Compare counter to length
jge .done             ; If counter >= length, exit loop
mov rax, [rdi + rcx*8] ; Load array[rcx]
add rax, rdx          ; Add constant
mov [rdi + rcx*8], rax ; Store back
inc rcx               ; Increment counter
jmp .loop             ; Jump back to loop start

.done:
; Result in array at rdi
```

This loop processes one element per iteration. The loop body has a data dependency chain: the load depends on the counter, the add depends on the load, the store depends on the add, and the increment and compare depend on the counter. This dependency chain limits parallelism; only the next iteration can potentially execute in parallel, and only after the current iteration's load has completed. The loop also has a high branch-to-work ratio: three branches (the compare, conditional jump, and unconditional jump) for a single add operation.

Now consider an unrolled version that processes four elements per iteration:

```asm
; rdi = pointer to array
; rsi = array length
; rdx = constant to add

xor rcx, rcx          ; rcx = loop counter (0)

.loop:
cmp rcx, rsi          ; Compare counter to length
jge .done             ; If counter >= length, exit loop

mov rax, [rdi + rcx*8]       ; Load array[rcx + 0]
mov rbx, [rdi + rcx*8 + 8]   ; Load array[rcx + 1]
mov r8,  [rdi + rcx*8 + 16]  ; Load array[rcx + 2]
mov r9,  [rdi + rcx*8 + 24]  ; Load array[rcx + 3]

add rax, rdx          ; Add constant to element 0
add rbx, rdx          ; Add constant to element 1
add r8,  rdx          ; Add constant to element 2
add r9,  rdx          ; Add constant to element 3

mov [rdi + rcx*8],      rax  ; Store result 0
mov [rdi + rcx*8 + 8],  rbx  ; Store result 1
mov [rdi + rcx*8 + 16], r8   ; Store result 2
mov [rdi + rcx*8 + 24], r9   ; Store result 3

add rcx, 4            ; Increment counter by 4
jmp .loop             ; Jump back to loop start

.done:
; Result in array at rdi
```

This unrolled loop processes four elements per iteration. The key insight is that the four loads are independent of each other—none depends on the result of another. Similarly, the four adds are independent (they all add the same constant, which is already in `rdx`). The processor can dispatch all four loads in rapid succession, and while waiting for the loads to complete, it can dispatch the add operations. The store operations can also be issued in parallel once their operands are ready.

The dependency chain has been broken. Instead of a single element's latency dominating each iteration, the latency of four elements is now partially hidden by parallelism. Additionally, the branch-to-work ratio is improved: five branch operations (one compare, one conditional jump, one unconditional jump, and two increments for the counter management) for four add operations is better than three branches for one add. The loop overhead is amortized across more work.

However, loop unrolling introduces costs. The code size is larger (by a factor of four in this example). If the loop unrolling factor is too large, the unrolled loop body may not fit in the instruction cache, causing i-cache misses. Additionally, loop unrolling assumes the array length is a multiple of the unroll factor. In practice, the loop must be guarded with a check to handle remainder elements:

```asm
; rdi = pointer to array
; rsi = array length
; rdx = constant to add

mov rax, rsi          ; Copy length to rax
and rax, 3            ; rax = length % 4 (mask to get remainder)
shr rsi, 2            ; rsi = length / 4 (number of full iterations)

xor rcx, rcx          ; rcx = loop counter (0)

; Unrolled loop for full iterations
.loop_unrolled:
cmp rcx, rsi
jge .remainder

; ... unrolled loop body (as above) ...

add rcx, 1            ; Increment by 1 (since we process 4 elements per iteration)
jmp .loop_unrolled

; Handle remainder elements
.remainder:
xor rcx, rcx
.loop_remainder:
cmp rcx, rax
jge .done
mov r10, [rdi + rsi*8*4 + rcx*8]  ; Load from remainder section
add r10, rdx
mov [rdi + rsi*8*4 + rcx*8], r10
inc rcx
jmp .loop_remainder

.done:
```

(This example has some pointer arithmetic complexity; a real implementation would be cleaner, but the principle is clear.)

### SIMD Vectorization: SSE and AVX

SIMD instructions operate on multiple data elements packed into a single register. SSE (Streaming SIMD Extensions) uses 128-bit registers; AVX (Advanced Vector Extensions) uses 256-bit registers; AVX-512 uses 512-bit registers. A 256-bit AVX register can hold eight 32-bit integers, four 64-bit integers, eight 32-bit floating-point numbers, or four 64-bit floating-point numbers.

Consider the same array-addition loop, now vectorized with AVX:

```asm
; rdi = pointer to array
; rsi = array length
; rdx = constant to add (32-bit value, to be broadcasted to all elements)

; Broadcast rdx to all elements of a 256-bit register
mov eax, edx          ; Move 32-bit constant to eax
movd xmm0, eax        ; Move to lowest 32 bits of xmm0 (128-bit register)
vpbroadcastd ymm0, xmm0  ; Broadcast to all 8 32-bit lanes of ymm0 (256-bit AVX register)

xor rcx, rcx          ; rcx = loop counter (0)

.loop:
cmp rcx, rsi          ; Compare counter to length
jge .done

vmovdqa ymm1, [rdi + rcx*4]  ; Load 8 elements into ymm1
vpaddd ymm2, ymm1, ymm0     ; Add ymm0 to ymm1, result in ymm2
vmovdqa [rdi + rcx*4], ymm2 ; Store result back

add rcx, 8            ; Increment counter by 8 (one AVX register holds 8 elements)
jmp .loop

.done:
```

In this loop, each iteration processes eight elements. The latency of the load, add, and store operations is similar to the scalar case, but we process eight times as much data. The throughput of the loop is eight times higher (modulo cache and memory bandwidth limitations).

The SIMD instruction set includes a wealth of operations: packed arithmetic (add, subtract, multiply, divide), comparisons, shifts, shuffles, and blends. The Intel Manual documents hundreds of SIMD instructions. A few key operations for assembly programmers:

- `vmovdqa ymm1, [rdi]`: Load 256 bits from memory into ymm1 (aligned access).
- `vmovdqu ymm1, [rdi]`: Load 256 bits from memory into ymm1 (unaligned access, slightly slower).
- `vpaddd ymm2, ymm1, ymm0`: Add eight 32-bit integers element-wise.
- `vpaddq ymm2, ymm1, ymm0`: Add four 64-bit integers element-wise.
- `vpmulld ymm2, ymm1, ymm0`: Multiply eight 32-bit integers element-wise (result truncated to 32 bits).
- `vpshufd ymm2, ymm1, imm8`: Shuffle 32-bit elements within each 128-bit lane, selecting which element goes where.
- `vpblendvb ymm3, ymm1, ymm2, ymm_mask`: Blend ymm1 and ymm2 element-wise based on ymm_mask.

The key limitation of SIMD is that it requires data to be organized in vectors. If the data is already in arrays or structures of arrays (SoA) format, vectorization is straightforward. If the data is in a structure of arrays format (array of structures, or AoS), conversion is necessary. For example, if an array contains structures like `{int x; int y; int z;}`, the elements are interleaved in memory, and vectorization is harder.

### ARM64 NEON SIMD

ARM64 SIMD is provided by the NEON extension. NEON registers are 128 bits wide (designated V0–V31), and they can hold eight 16-bit elements, four 32-bit elements, two 64-bit elements, or one 128-bit element. (Newer ARM architectures like SVE support 256-bit and larger vectors, but NEON is the baseline.)

The ARM64 SIMD instruction set is conceptually similar to x86 SIMD but uses different mnemonics. A few key operations:

- `ld1 {v0.4s}, [x0]`: Load four 32-bit elements into v0.
- `add v1.4s, v0.4s, v2.4s`: Add four 32-bit elements.
- `st1 {v1.4s}, [x1]`: Store four 32-bit elements from v1.
- `fmul v1.4s, v0.4s, v2.4s`: Multiply four 32-bit floating-point elements.
- `ext v1.16b, v0.16b, v2.16b, #n`: Extract and concatenate elements (useful for shuffling).

The syntax for NEON specifies the element type in the mnemonic: `.4s` means four 32-bit signed integers, `.2d` means two 64-bit signed integers, `.4h` means four 16-bit signed integers.

Here is the same array-addition loop in ARM64 NEON:

```asm
; x0 = pointer to array
; x1 = array length
; x2 = constant to add

; Broadcast constant to all elements of a NEON register
mov w3, w2            ; Move constant to w3 (32-bit)
dup v0.4s, w3         ; Duplicate to all four 32-bit lanes of v0

xor x3, x3            ; x3 = loop counter (0)

.loop:
cmp x3, x1            ; Compare counter to length
b.ge .done

ld1 {v1.4s}, [x0, x3, lsl #2]  ; Load four elements (lsl #2 = multiply by 4)
add v2.4s, v1.4s, v0.4s        ; Add element-wise
st1 {v2.4s}, [x0, x3, lsl #2]  ; Store result back

add x3, x3, 4         ; Increment counter by 4
b .loop

.done:
```

In ARM64, the loop processes four 32-bit elements per iteration (NEON is 128-bit wide, and each element is 32 bits). This is slower than the eight-element AVX loop, but the principle is identical.

### Cache-Aware Programming

The CPU cache hierarchy is invisible to the assembly programmer, but optimizing for the cache is critical for performance. Modern processors have an L1 instruction cache (typically 32–48 KB), an L1 data cache (typically 32–48 KB), an L2 cache (typically 256–512 KB per core), and an L3 cache (shared, typically 8–20 MB). Access times vary: L1 hit is 4 cycles, L2 hit is 12 cycles, L3 hit is 40–75 cycles, and main memory is 150–300 cycles.

The working set is the set of data actively used by a program. If the working set fits in the L1 cache, the program runs fast. If the working set is larger than L1 but fits in L2, it runs slower. If the working set exceeds L3, performance degrades dramatically due to repeated main-memory accesses.

A classic example is matrix multiplication. Suppose we multiply two 1024×1024 matrices of 32-bit floats (4 bytes each). Each matrix is 4 MB, and the total is 8 MB—too large for the L3 cache on most processors. If we naively loop:

```asm
; rdi = pointer to matrix A (1024x1024, row-major)
; rsi = pointer to matrix B (1024x1024, row-major)
; rdx = pointer to matrix C (result, 1024x1024)

; Pseudocode:
; for i = 0 to 1023:
;   for j = 0 to 1023:
;     C[i][j] = 0
;     for k = 0 to 1023:
;       C[i][j] += A[i][k] * B[k][j]
```

This loops accesses matrix B in a column-major manner (each access skips 1024 elements). Matrix B will cause cache misses on nearly every access, because consecutive accesses to the same column are separated by 4096 bytes (1024 floats × 4 bytes), which exceeds the cache line size.

A better approach is *loop tiling* (or *blocking*). We divide the matrices into smaller blocks, say 64×64, and compute the result block by block:

```asm
; Pseudocode:
; for ii = 0 to 1023 step 64:
;   for jj = 0 to 1023 step 64:
;     for kk = 0 to 1023 step 64:
;       for i = ii to ii+63:
;         for j = jj to jj+63:
;           for k = kk to kk+63:
;             C[i][j] += A[i][k] * B[k][j]
```

Now, the inner loops operate on 64×64 blocks, which fit in the cache. The 64×64 block of A is reused 64 times (once for each value of j), and the 64×64 block of B is reused 64 times (once for each value of i). Cache efficiency improves dramatically. The exact block size depends on the cache size and the data type, but 64 is a reasonable choice for most modern processors.

### Atomic Operations and Memory Ordering

In multithreaded code, concurrent access to shared data requires synchronization. Atomic operations guarantee that a read, modify, or write is indivisible and visible to all threads. x86-64 atomic instructions use the `lock` prefix:

```asm
lock add [rdi], rax   ; Atomically add rax to memory at rdi
```

The `lock` prefix causes the processor to acquire an exclusive lock on the cache line containing the target memory address. Other processors cannot read or write to that cache line until the lock is released. This is expensive—a `lock add` might take 20+ cycles on some processors—because it serializes the operation across all cores.

For performance, atomic operations should be used sparingly. A common pattern is to accumulate results in thread-local variables (avoiding locks) and then synchronize only at the end:

```asm
; Thread 0:
xor rax, rax          ; rax = thread-local accumulator
xor rcx, rcx          ; rcx = loop counter
.loop0:
cmp rcx, [rsi]        ; Compare counter to work item count
jge .done0
; Process work item rcx
add rax, [rdi + rcx*8]  ; Accumulate result
inc rcx
jmp .loop0
.done0:
lock add [rdx], rax   ; Atomically add thread-local result to global accumulator
```

Additionally, x86-64 has strong memory ordering guarantees by default. Stores are always visible to other processors in order (though they may be buffered in the store queue for a few cycles). Loads can be reordered ahead of stores, but stores cannot be reordered. This simplifies synchronization compared to architectures like ARM or PowerPC, which have weaker memory ordering and require explicit memory barriers.

The `mfence` instruction (memory fence) enforces strong ordering:

```asm
mov rax, 1
mov [rdi], rax        ; Write 1 to memory
mfence                ; Ensure all stores complete
mov rax, [rsi]        ; This load will not execute until the store above completes
```

In practice, `mfence` is rarely needed on x86-64 for typical synchronization patterns; the default strong ordering is sufficient.

## 3. High-Performance Optimization & Failure Modes

### Instruction Scheduling: A Practical Example

To concretely illustrate the power of instruction scheduling, consider a compute-bound kernel that processes a stream of 32-bit integers, computing a reduction (e.g., sum of all elements). Here is a naive version:

```asm
; rdi = pointer to array of 32-bit integers
; rsi = number of elements
; Returns sum in eax

xor rax, rax          ; rax = accumulator (0)
xor rcx, rcx          ; rcx = loop counter (0)

.loop:
cmp rcx, rsi
jge .done
movsxd r8, [rdi + rcx*4]  ; Load element (sign-extend to 64-bit)
add rax, r8           ; Add to accumulator
inc rcx
jmp .loop

.done:
; eax contains sum (lower 32 bits)
```

This loop has a critical data dependency: each iteration depends on the previous iteration's add. The load has a latency of ~4–12 cycles (depending on cache), and the add completes in 1 cycle on modern processors. However, because the add depends on `rax` from the previous iteration, the next add cannot begin until this add completes. The latency of the load dominates, and the processor is stalled for 4–11 cycles per iteration. With N elements, the total time is roughly N × load_latency cycles, plus some loop overhead.

Now consider a scheduled version that uses multiple accumulator registers:

```asm
; rdi = pointer to array
; rsi = number of elements
; Returns sum in eax

xor rax, rax          ; Accumulator 0
xor rbx, rbx          ; Accumulator 1
xor r8, r8            ; Accumulator 2
xor r9, r9            ; Accumulator 3
xor rcx, rcx          ; Loop counter

; Unroll by 4, with separate accumulators to break dependency chains
.loop:
cmp rcx, rsi
jge .done

movsxd r10, [rdi + rcx*4]
add rax, r10          ; Add to accumulator 0
inc rcx

movsxd r10, [rdi + rcx*4]
add rbx, r10          ; Add to accumulator 1 (independent of rax)
inc rcx

movsxd r10, [rdi + rcx*4]
add r8, r10           ; Add to accumulator 2 (independent of rax and rbx)
inc rcx

movsxd r10, [rdi + rcx*4]
add r9, r10           ; Add to accumulator 3 (independent of others)
inc rcx

jmp .loop

.done:
; Combine accumulators
add rax, rbx
add rax, r8
add rax, r9
; eax contains sum
```

In this version, each of the four accumulators is independent. The processor can dispatch all four loads rapidly (the two ports for loads can each handle
