# Lesson 4: Code Generation and Runtime Semantics

## 1. First-Principles Intuition & Invariants

The transformation from abstract syntax trees and intermediate representations into executable machine code represents the final and most consequential phase of compilation, where the compiler must reconcile the elegant abstractions of high-level programming languages with the harsh physical realities of silicon, cache hierarchies, and instruction pipelines. Code generation is not merely a mechanical translation process but rather a sophisticated optimization problem constrained by the finite resources of the target architecture: a limited register file, a fixed instruction encoding space, specific addressing modes, and the immutable physics of memory latency and bandwidth.

Every high-level construct—whether a nested loop, a recursive function call, or a dynamically dispatched method invocation—must be lowered into a precise sequence of machine instructions that preserve the original program's semantics while navigating the treacherous waters of register pressure, instruction latency, and calling convention contracts. The compiler's code generator operates under a fundamental invariant: the generated assembly must produce observably identical behavior to the source program under the abstract machine model defined by the language specification, yet it must do so using only the primitive operations exposed by the target instruction set architecture.

Register allocation stands at the heart of this challenge. Modern processors provide between eight and thirty-two general-purpose registers depending on the architecture—x86-64 offers sixteen, AArch64 provides thirty-one—yet a typical function in the intermediate representation may reference hundreds of virtual registers or temporaries. The register allocator must solve a graph coloring problem under interference constraints: two virtual registers that are simultaneously live cannot occupy the same physical register. When the number of live ranges exceeds available registers, the allocator must spill values to memory, introducing load and store instructions that impose latency penalties measured in tens or hundreds of cycles depending on cache behavior.

Instruction selection transforms abstract three-address code operations into target-specific instruction sequences. A single high-level expression like `a = b * 4 + c` might map to a single LEA instruction on x86 (`lea rax, [rbx + rcx*4]`) or require multiple instructions on RISC architectures that prohibit complex addressing modes. The selector must understand instruction costs, pipeline characteristics, and the availability of specialized instructions for common patterns. An effective instruction selector recognizes that a left shift by a constant power of two is semantically equivalent to multiplication but executes faster and consumes less energy.

Calling conventions establish the contract governing inter-procedural communication: which registers hold arguments, where return values reside, which registers the callee must preserve, and how the stack frame is structured. These conventions are not arbitrary aesthetic choices but carefully engineered protocols that balance competing concerns. Argument registers enable parameter passing without memory traffic, callee-saved registers reduce save/restore overhead for leaf functions, and stack alignment requirements ensure efficient access to vector instructions that demand aligned operands. The x86-64 System V ABI mandates that the first six integer arguments travel in RDI, RSI, RDX, RCX, R8, and R9, while Windows x64 uses RCX, RDX, R8, and R9. The compiler's code generator must faithfully implement these conventions at every function boundary, or the resulting binary will violate the platform's ABI and fail unpredictably when interfacing with system libraries or other compilation units.

Memory management semantics flow from the language's execution model. Stack allocation follows a last-in-first-out discipline with deterministic deallocation at scope exit, enabling the compiler to generate simple pointer arithmetic on the stack pointer for local variable allocation. Heap allocation requires runtime support from a memory allocator like malloc or a garbage collector, and the compiler must emit calls to allocation routines, initialize object metadata, and potentially insert write barriers or reference counting operations depending on the language's memory reclamation strategy.

The linking phase resolves cross-module references and combines multiple object files into an executable or shared library. During compilation, the code generator emits symbolic references to external functions and global variables, which the linker must resolve by patching relocation entries with actual addresses. Position-independent code introduces additional complexity: shared libraries must execute at arbitrary load addresses, requiring the compiler to generate PC-relative addressing or indirect references through a Global Offset Table. The compiler and linker collaborate to maintain a coherent address space despite separate compilation and dynamic loading.

Control flow lowering transforms structured control constructs—if statements, loops, switch statements—into conditional and unconditional branches. The compiler must select branch instructions, predict branch directions to guide static scheduling, and arrange basic blocks to minimize taken branches and improve instruction cache locality. A simple if-else statement becomes a conditional branch based on a comparison result stored in flags registers or a boolean-valued register depending on the architecture. Loops compile into backward branches with loop-invariant code motion and induction variable optimizations applied during earlier passes.

Exception handling mechanisms impose runtime overhead and complicate code generation. Languages with exceptions require the compiler to maintain exception tables mapping instruction ranges to catch handlers, emit stack unwinding information for frame traversal, and potentially insert landing pads that restore program state when an exception propagates through a function. Zero-cost exception models attempt to eliminate overhead on the non-exceptional path by deferring all bookkeeping to the unwinding process, using metadata tables consulted only when an exception occurs.

The semantic gap between high-level language guarantees and machine-level behavior manifests in subtle ways. Floating-point arithmetic on real hardware violates mathematical associativity due to rounding errors, requiring the compiler to respect parenthesization and avoid certain algebraic transformations unless explicitly permitted by language flags like `-ffast-math`. Memory ordering semantics in concurrent programs demand careful attention to memory barriers and atomic instruction sequences, particularly on weakly-ordered architectures like ARM where loads and stores may complete out of program order without explicit synchronization.

Code generation quality directly impacts application performance, energy efficiency, and code size. An inefficient register allocation strategy that spills excessively can double or triple execution time for hot loops. Poor instruction selection that misses specialized instructions leaves performance on the table. Calling convention violations produce intermittent crashes that are extraordinarily difficult to debug. The compiler's code generator is the ultimate arbiter of how efficiently a program exploits the underlying hardware, and understanding its operation is essential for any systems programmer seeking to optimize performance-critical code.

## 2. Core Architecture & Mechanics

The code generation pipeline typically proceeds through several distinct phases, each transforming the program representation closer to executable machine code while maintaining semantic correctness. The process begins with the intermediate representation—often in Static Single Assignment form after optimization passes—and culminates in the emission of assembly code or direct generation of binary object files.

Instruction selection consumes the IR and produces a target-specific representation of machine instructions, often called a machine IR or selection DAG. This phase must tile the IR operations with available instruction templates while minimizing cost. A simple three-address operation like `r3 = r1 + r2` maps straightforwardly to an ADD instruction on most architectures, but complex addressing modes introduce choices. Consider loading from a memory location computed as `base + index * scale + offset`. On x86-64, this pattern matches a single memory operand: `mov rax, [rdi + rsi*4 + 16]`. On ARM, it might require separate shift and add instructions followed by a load.

Many compilers perform instruction selection using tree pattern matching or directed acyclic graph covering algorithms. The compiler encodes instruction templates as patterns with costs, then finds a minimum-cost covering of the IR expression tree. Dynamic programming algorithms efficiently compute optimal tilings for tree-shaped expressions, though DAG-structured expressions with shared subexpressions require more sophisticated techniques. Modern compilers like LLVM use a SelectionDAG representation that encodes both data dependencies and sequencing constraints, enabling the selector to exploit commutative and associative properties during matching.

```c
// Example IR sequence (pseudo-code)
%1 = load ptr %array_base
%2 = mul i64 %index, 4
%3 = add ptr %1, %2
%4 = load i32 %3
%5 = add i32 %4, 10
store i32 %5, ptr %result
```

On x86-64, an optimal instruction selection might collapse the address computation into the load's addressing mode:

```asm
mov    rax, [rdi]           ; load array_base
mov    edx, [rax + rsi*4]   ; load array_base[index]
add    edx, 10
mov    [rcx], edx           ; store to result
```

Register allocation follows instruction selection and assigns physical registers to the virtual registers or temporaries in the machine IR. The classical approach models the problem as graph coloring: construct an interference graph where nodes represent virtual registers and edges connect simultaneously live values that cannot share a physical register. A k-coloring of this graph, where k equals the number of available registers, yields a valid allocation. When no k-coloring exists, the allocator must select spill candidates, insert load and store instructions around their uses and definitions, and retry allocation.

The liveness analysis prerequisite computes which virtual registers are live at each program point. A variable is live at a point if there exists a path to a use of that variable without an intervening definition. The analyzer typically computes live-in and live-out sets for each basic block using iterative dataflow equations:

```
live_in[B] = use[B] ∪ (live_out[B] - def[B])
live_out[B] = ⋃(live_in[S] for S in successors(B))
```

Iteration continues until reaching a fixed point, which is guaranteed to occur because the sets grow monotonically in a finite lattice. Once liveness information is available, the allocator constructs the interference graph and applies a coloring heuristic.

Graph coloring is NP-complete in the general case, so production compilers employ heuristic algorithms. The Chaitin-Briggs allocator uses a simplification-based approach: repeatedly remove nodes with degree less than k from the graph, knowing they can be colored once their neighbors are colored. When no such node exists, select a spill candidate using a cost heuristic that considers the spill weight—a function of use frequency and loop nesting depth. After spilling and inserting loads and stores, the allocator repeats the process until achieving a valid coloring.

Linear scan allocation offers a faster alternative suitable for just-in-time compilers where compilation speed matters. This algorithm sorts live intervals by their starting points, then iterates through them in order, assigning each to a free register or spilling when none are available. Linear scan runs in O(n log n) time compared to the potentially exponential complexity of graph coloring, but typically produces slightly lower quality allocations because it cannot handle complex interference patterns as effectively.

```
LinearScanAllocate(intervals):
    active = []
    sort intervals by start point
    for each interval i:
        ExpireOldIntervals(i)
        if len(active) == num_registers:
            SpillAtInterval(i)
        else:
            register[i] = free_register()
            add i to active sorted by end point

ExpireOldIntervals(i):
    for each interval j in active sorted by end point:
        if j.end >= i.start:
            return
        remove j from active
        add register[j] to free pool
```

Register allocation interacts critically with calling conventions. The allocator must preserve callee-saved registers by generating save and restore instructions in the function prologue and epilogue. It must place function arguments in the designated argument registers or stack locations according to the calling convention. Leaf functions that don't call other functions can avoid saving callee-saved registers they don't modify, reducing overhead. The allocator tracks which registers are actually used and generates minimal save/restore code.

Consider a function compiled for x86-64 System V ABI:

```c
long compute(long a, long b, long c, long d, long e, long f, long g) {
    long sum = a + b + c + d + e + f + g;
    return sum * 2;
}
```

The first six arguments arrive in RDI, RSI, RDX, RCX, R8, and R9, while the seventh comes from the stack. The generated code might look like:

```asm
compute:
    add    rdi, rsi          ; a += b
    add    rdi, rdx          ; a += c
    add    rdi, rcx          ; a += d
    add    rdi, r8           ; a += e
    add    rdi, r9           ; a += f
    add    rdi, [rsp+8]      ; a += g (seventh arg on stack)
    lea    rax, [rdi+rdi]    ; return sum * 2
    ret
```

The calling convention dictates that the return value resides in RAX, and since this function only uses argument registers and doesn't call other functions, no prologue or epilogue is necessary.

Frame layout determines how local variables, spilled registers, and saved registers are organized on the stack. The compiler allocates stack space in the function prologue by adjusting the stack pointer, then addresses locals relative to the frame pointer or stack pointer. Stack alignment requirements complicate this process—x86-64 requires 16-byte alignment at call sites, meaning the compiler must pad frame sizes to maintain alignment through nested calls.

```asm
function_prologue:
    push   rbp                ; save old frame pointer
    mov    rbp, rsp           ; establish new frame pointer
    sub    rsp, 64            ; allocate 64 bytes for locals (aligned)
    ; ... function body ...
    add    rsp, 64            ; deallocate locals
    pop    rbp                ; restore frame pointer
    ret
```

The frame pointer enables stack unwinding and debugging since it provides a stable reference point even as the stack pointer changes. Omitting the frame pointer saves a register and eliminates prologue/epilogue overhead but complicates debugging and exception handling. The `-fomit-frame-pointer` compiler flag controls this trade-off.

Exception handling infrastructure requires the compiler to generate metadata tables that map instruction ranges to exception handlers and encode unwinding information for stack traversal. The DWARF Call Frame Information format specifies how to reconstruct the previous frame's register values at any instruction, enabling exception propagation and debugger stack traces. When a function might throw or propagate exceptions, the compiler emits a LSDA (Language Specific Data Area) section describing catch clauses and cleanup actions.

Control flow lowering translates structured control constructs into conditional and unconditional branches. A simple if statement:

```c
if (x > 0) {
    y = x * 2;
} else {
    y = x * 3;
}
z = y + 1;
```

Compiles to a compare instruction that sets condition flags, followed by a conditional branch:

```asm
    cmp    edi, 0            ; compare x with 0
    jle    .L_else           ; jump if less or equal
.L_then:
    lea    eax, [rdi+rdi]    ; y = x * 2
    jmp    .L_endif
.L_else:
    lea    eax, [rdi+rdi*2]  ; y = x * 3
.L_endif:
    add    eax, 1            ; z = y + 1
```

Loops typically compile into a conditional branch at the end of the loop body that jumps backward to the loop header when the condition holds. Optimizing compilers often perform loop transformations like strength reduction and induction variable elimination before code generation, simplifying the generated code.

Switch statements with dense case labels often compile into jump tables—arrays of code addresses indexed by the switch expression. The compiler generates a bounds check, scales the index by pointer size, and performs an indirect jump through the table. Sparse switches may use binary search trees or hash tables instead.

```c
switch (x) {
    case 0: return 10;
    case 1: return 20;
    case 2: return 30;
    case 3: return 40;
    default: return 0;
}
```

Dense switch code generation:

```asm
    cmp    edi, 3
    ja     .L_default        ; unsigned compare catches negative
    lea    rax, [rip+.L_jumptable]
    movsxd rdi, edi
    jmp    [rax + rdi*8]
    
.L_jumptable:
    .quad  .L_case0
    .quad  .L_case1
    .quad  .L_case2
    .quad  .L_case3

.L_case0:
    mov    eax, 10
    ret
.L_case1:
    mov    eax, 20
    ret
; ... etc
```

Position-independent code generation enables shared libraries to load at arbitrary addresses. The compiler cannot embed absolute addresses for global variables or function calls because the actual load address is unknown at compile time. Instead, it generates PC-relative references or indirect accesses through tables.

On x86-64, calls to external functions route through the Procedure Linkage Table, and accesses to global variables indirect through the Global Offset Table. The compiler emits relocations that the dynamic linker resolves at load time:

```asm
    ; Call external function
    call   external_func@PLT
    
    ; Access global variable
    mov    rax, [rip + global_var@GOTPCREL]
    mov    edx, [rax]
```

The `@PLT` and `@GOTPCREL` suffixes instruct the assembler to generate appropriate relocations. The PLT stub initially jumps to the dynamic linker resolver, which patches the GOT entry with the actual function address, enabling subsequent calls to jump directly to the target.

Thread-local storage introduces additional complexity because each thread requires a distinct copy of thread-local variables. The compiler generates TLS access sequences that call runtime support functions or use special addressing modes to reach the thread's TLS block. On x86-64, the FS segment register points to the thread control block, and the compiler generates FS-relative addressing for TLS access.

Generating debug information requires the compiler to emit DWARF sections that map machine code addresses back to source locations, describe variable locations throughout the program, and encode type information. This metadata enables debuggers to present source-level views of the executing program despite aggressive optimizations that obscure the correspondence between source and machine code.

The final emission phase outputs assembly code or directly generates an object file with encoded instructions, relocation entries, symbol tables, and metadata sections. The compiler must respect the target object file format—ELF on Linux, Mach-O on macOS, COFF/PE on Windows—and generate appropriate sections and headers. This phase translates symbolic register names and instruction mnemonics into binary opcodes, encodes operands according to the instruction encoding format, and computes branch offsets for short-range branches or emits relocations for long-range branches.

## 3. High-Performance Optimization & Failure Modes

Code generation quality profoundly impacts application performance because it determines how effectively the program exploits the target processor's resources. A superior instruction selection strategy that leverages specialized instructions can yield order-of-magnitude improvements for critical kernels. Effective register allocation minimizes memory traffic and cache pressure, while poor allocation that spills excessively can transform a CPU-bound workload into a memory-bandwidth-limited one.

Instruction scheduling reorders instructions within basic blocks to hide latency and maximize instruction throughput. Modern superscalar processors execute multiple instructions per cycle using out-of-order execution, but scheduling remains valuable because it reduces register pressure, improves instruction cache locality, and respects instruction latencies and dependencies. The scheduler constructs a dependency graph representing data and control dependencies, then topologically sorts the graph while minimizing cycle count given the processor's instruction issue width and functional unit availability.

List scheduling algorithms maintain a ready queue of instructions whose dependencies are satisfied and greedily select instructions based on priority heuristics. The priority function might favor instructions with many dependent instructions (to expose parallelism early), instructions with long latency (to issue them early and hide latency), or instructions that free registers (to reduce pressure). Constructing an optimal schedule is NP-complete, but effective heuristics produce near-optimal results for most code.

```
ListSchedule(basic_block):
    ready = instructions with no predecessors
    scheduled = []
    time = 0
    
    while ready is not empty or pending is not empty:
        for each functional_unit:
            if unit.available_at <= time and ready is not empty:
                inst = select_highest_priority(ready)
                issue(inst, unit, time)
                scheduled.append((inst, time))
                remove inst from ready
                for each successor of inst:
                    if all predecessors of successor are scheduled:
                        add successor to ready
        time += 1
```

Software pipelining optimizes loops by overlapping iterations to increase instruction-level parallelism. The compiler identifies loop-carried dependencies and computes a schedule that initiates a new iteration every few cycles while previous iterations are still executing, achieving higher throughput than executing iterations sequentially. This technique is particularly effective for loops with long-latency operations like memory accesses or floating-point computations.

Register pressure management represents a critical optimization concern. Excessive register pressure forces spilling, which introduces memory traffic that can saturate cache bandwidth and stall the processor. Compilers employ several strategies to reduce pressure: schedule instructions to minimize live ranges, perform rematerialization where recomputing a value costs less than spilling it, and split live ranges across regions with different pressure characteristics.

Rematerialization replaces loads of spilled registers with instruction sequences that recompute the value. If a value can be computed cheaply—for example, loading a constant or computing a stack offset—rematerialization avoids memory traffic. The compiler compares the cost of the recomputation sequence against the cost of a load plus the cache miss probability to decide whether rematerialization is profitable.

```c
// Original code with high register pressure
int x = 42;  // Might be spilled
// ... many instructions using other registers ...
use(x);      // Reload x from stack

// Rematerialization replaces the reload with recomputation
// ... many instructions ...
use(42);     // Recompute constant instead of loading
```

Calling convention optimization becomes crucial for performance in codebases with small, frequently called functions. Inlining eliminates call overhead entirely by substituting the function body at call sites, but code size growth limits inlining aggressiveness. Tail call optimization transforms tail-recursive calls into jumps, converting recursion into iteration and eliminating stack frame allocation. Languages like Scheme guarantee tail call optimization, making deep recursion practical.

Register allocation for SSA-form programs exploits the property that each variable is defined exactly once. SSA deconstruction after register allocation must handle phi nodes by inserting copies or using parallel copy semantics. Modern allocators often maintain SSA form throughout allocation, coalescing phi operands when possible and only breaking SSA form during final emission.

Instruction selection optimizations recognize idioms and complex patterns that map to specialized instructions. Strength reduction transforms expensive operations like multiplication and division by constants into cheaper shift and add sequences. Fused multiply-add instructions combine multiplication and addition with a single rounding, improving both performance and numerical accuracy. Vector instructions operate on multiple data elements in parallel, offering substantial speedups for data-parallel workloads.

Consider optimizing a loop that computes a dot product:

```c
float dot_product(float *a, float *b, size_t n) {
    float sum = 0.0f;
    for (size_t i = 0; i < n; i++) {
        sum += a[i] * b[i];
    }
    return sum;
}
```

A scalar implementation generates one multiply-add per iteration. Vectorization using AVX2 instructions processes eight floats per iteration:

```asm
dot_product:
    vxorps     ymm0, ymm0, ymm0     ; sum = 0.0f (256-bit vector)
    xor        eax, eax             ; i = 0
.L_loop:
    vmovups    ymm1, [rdi + rax*4]  ; load a[i:i+7]
    vmovups    ymm2, [rsi + rax*4]  ; load b[i:i+7]
    vfmadd231ps ymm0, ymm1, ymm2    ; sum += a[i:i+7] * b[i:i+7]
    add        rax, 8                ; i += 8
    cmp        rax, rdx
    jb         .L_loop
    ; horizontal sum of ymm0 into xmm0
    vextractf128 xmm1, ymm0, 1
    vaddps     xmm0, xmm0, xmm1
    vhaddps    xmm0, xmm0, xmm0
    vhaddps    xmm0, xmm0, xmm0
    ret
```

The vectorized version achieves roughly 8× throughput improvement when memory bandwidth permits. Autovectorization transforms scalar loops into vector operations automatically, but requires careful attention to alignment, aliasing, and reduction patterns.

Failure modes in code generation manifest as incorrect code, performance pathologies, or runtime crashes. Register allocation errors where the allocator assigns the same physical register to interfering virtual registers produce nondeterministic bugs because values get clobbered unpredictably. These bugs are extraordinarily difficult to debug because they depend on optimization levels and may appear or disappear with seemingly unrelated code changes.

Calling convention mismatches cause stack corruption and crashes when a caller and callee disagree about argument locations or stack cleanup responsibility. On x86, the distinction between `cdecl` (caller cleans stack) and `stdcall` (callee cleans stack) conventions means that a mismatch causes stack pointer corruption after the call returns. On x86-64, the unified calling convention eliminates this class of bugs, but mixing ABIs (System V vs. Windows x64) still causes failures.

Unaligned memory accesses generate exceptions or silent performance degradation depending on the architecture. x86 tolerates unaligned accesses with a performance penalty, while ARM historically faulted on unaligned accesses (though modern ARM cores support them with degraded performance). The compiler must ensure that stack frames maintain required alignment and that vector operations access aligned addresses or use unaligned load/store instructions.

Incorrect exception handling metadata causes crashes during unwinding or leaks resources if cleanup code doesn't execute. Testing exception paths requires deliberate injection of exceptions in various locations, which many test suites neglect. Fuzzing with controlled exception injection helps uncover these latent bugs.

Position-independent code generation bugs manifest as relocation overflows where a PC-relative offset exceeds the range encodable in the instruction format. On x86-64, most PC-relative offsets are 32-bit signed, limiting the addressable range to ±2GB from the instruction. Large shared libraries may violate this constraint, requiring the compiler to use indirect addressing through tables.

Register allocation bugs interact with instruction scheduling in subtle ways. If the scheduler moves a use of a register before the allocator inserts a reload after a spill, the program reads stale values. Compilers prevent this by preserving dependencies through spill code insertion or by performing scheduling before allocation.

Debugging optimized code challenges developers because optimizations obscure the relationship between source and machine code. Variables may not have consistent locations, control flow may be reordered, and entire computations may be eliminated if the compiler proves them unused. Debug information helps but cannot fully bridge the semantic gap. Compiling with `-Og` enables optimizations that don't interfere with debugging, trading some performance for debuggability.

Profiling-guided optimization collects runtime profile data from instrumented binaries and uses it to guide optimization decisions. The compiler prioritizes optimizations on hot paths, uses actual branch frequencies to guide block layout for improved instruction cache locality, and devirtualizes indirect calls using observed target frequencies. PGO typically yields 10-30% performance improvements by focusing optimization effort where it matters most.

Link-time optimization enables interprocedural optimizations across translation units by deferring code generation until link time. The compiler emits IR instead of object code, and the linker runs optimization and code generation passes with whole-program visibility. LTO enables aggressive inlining across file boundaries, dead code elimination of unused functions, and interprocedural register allocation. The cost is increased link time and memory consumption, but the performance gains often justify the overhead for production builds.

Code size optimization matters for embedded systems with limited storage and for reducing instruction cache pressure. The compiler can prioritize size over speed by selecting compact instruction sequences, outlining common code sequences into functions, and using compression-friendly encodings. The `-Os` and `-Oz` flags control size optimization aggressiveness.

Security hardening transforms apply defensive mitigations during code generation. Stack canaries insert random values before return addresses to detect buffer overflows. Control Flow Integrity instruments indirect branches to verify that targets match expected signatures. AddressSanitizer inserts checks around memory accesses to detect out-of-bounds accesses and use-after-free bugs. These transformations impose runtime overhead but provide valuable defense-in-depth against exploitation.

The interaction between language semantics and code generation is subtle and consequential. Undefined behavior in C and C++ permits aggressive optimizations—the compiler assumes signed integer overflow never occurs and eliminates bounds checks accordingly—but also introduces security vulnerabilities when undefined behavior manifests in ways the programmer didn't anticipate. Modern compilers offer sanitizer modes that detect undefined behavior at runtime, trading performance for safety during testing.

Memory model semantics govern concurrent code generation. Sequential consistency requires that all threads observe operations in a total order consistent with program order, imposing strict constraints on reordering. Relaxed memory models permit reordering for performance but require explicit synchronization. The compiler must respect memory ordering constraints specified by atomic operations, inserting memory barriers or using atomic instruction sequences as required by the target architecture's memory model.

Code generation for heterogeneous systems that combine CPUs with GPUs or specialized accelerators requires coordinating memory spaces, offloading computations to accelerators, and managing asynchronous execution. The compiler must partition code between host and device, generate kernel code in the device's instruction set, and emit runtime calls to manage data transfers and kernel launches. OpenMP and CUDA provide pragmas and language extensions that guide the compiler in generating heterogeneous code.

The code generator is the final arbiter of program behavior, transforming high-level intent into the precise instruction sequences that execute on silicon. Understanding its operation—the constraints it navigates, the optimizations it applies, and the failure modes that lurk in incorrect implementations—is essential knowledge for systems programmers who demand control over performance, correctness, and the faithful translation of their algorithms into executing machine code.
