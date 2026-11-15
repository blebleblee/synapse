# Lesson 3: Calling Conventions, Stack Frames, Linkage

## 1. First-Principles Intuition & Invariants

The moment a processor executes a `call` instruction, it faces a fundamental architectural problem: how does one function communicate with another across the boundary of compiled translation units while preserving the illusion that each function operates in its own isolated computational universe? This question lies at the heart of software modularity, and its answer—calling conventions—represents one of the most carefully negotiated contracts in computer architecture.

At the hardware level, a CPU possesses only a finite set of general-purpose registers, typically between eight and thirty-two depending on the architecture. When function A invokes function B, both functions may wish to use the same physical register for different logical purposes. Without a rigorous protocol governing register ownership, return address preservation, and parameter transmission, the called function would indiscriminately overwrite the caller's working state, rendering modular programming impossible. The calling convention establishes this protocol, dictating which registers the caller must preserve before a function call (caller-saved), which registers the callee must restore before returning (callee-saved), how parameters flow from caller to callee, and where return values materialize.

The stack emerges as the primary data structure enabling this coordination. Unlike registers, which exist as fixed physical storage elements within the CPU die itself, the stack resides in main memory and grows dynamically as functions nest deeper. The stack pointer register—`%rsp` on x86-64, `SP` (or `X31`) on ARM64—always points to the current top of this contiguous memory region, which by convention grows downward toward lower addresses on virtually all modern architectures. Each function call pushes a new activation record, or stack frame, onto this structure, encapsulating the function's local variables, saved register values, return address, and any parameters that could not fit in registers.

The Application Binary Interface (ABI) codifies these conventions into a formal specification that compilers, assemblers, and linkers must obey. The System V AMD64 ABI, used on Linux and most Unix-like systems for x86-64 processors, differs substantially from the Microsoft x64 calling convention used on Windows, and both differ again from the ARM Architecture Procedure Call Standard (AAPCS64) governing AArch64 systems. These specifications are not arbitrary; they reflect careful trade-offs between register pressure, cache locality, instruction encoding density, and the physical constraints of the underlying microarchitecture.

Consider the invariant that the stack pointer must remain aligned to a sixteen-byte boundary before any `call` instruction on x86-64 System V systems. This requirement emerges from the SSE instruction set, whose aligned move instructions (`movaps`, `movapd`) generate alignment faults if their memory operands cross cache line boundaries. A misaligned stack would cause subtle crashes in functions that use vectorized arithmetic, making this alignment requirement a hard architectural constraint rather than a performance suggestion. The ABI enforces this invariant by mandating that the `call` instruction itself pushes an eight-byte return address, implicitly misaligning the stack by eight bytes upon function entry, which the callee's prologue must then correct.

The distinction between caller-saved and callee-saved registers reflects a deep optimization principle: minimize the total number of memory operations across the call boundary. If a caller does not use a particular register after a function call, there is no need to save it; the callee can freely clobber it. Conversely, if a callee does not use a particular register, there is no need to save and restore it, even if the ABI designates it as callee-saved. This selective preservation reduces memory bandwidth consumption, but it imposes a strict discipline: the caller must assume that all caller-saved registers are destroyed across a call, and the callee must guarantee that all callee-saved registers hold identical values upon return.

The return address represents the most critical piece of state crossing the call boundary. On x86-64, the `call` instruction atomically pushes the address of the next instruction onto the stack and transfers control to the target address. The corresponding `ret` instruction pops this saved address and resumes execution, completing the round-trip. This hardware-managed return address storage creates an exploitable attack surface—buffer overflows that overwrite the saved return address can redirect control flow to arbitrary code—but it also enables the seamless function call abstraction that underpins all structured programming.

Parameter passing conventions balance register speed against stack overflow risk. The first six integer or pointer arguments on x86-64 System V travel in registers `%rdi`, `%rsi`, `%rdx`, `%rcx`, `%r8`, and `%r9`, while floating-point arguments occupy `%xmm0` through `%xmm7`. Arguments beyond these limits spill onto the stack in right-to-left order, meaning the seventh argument resides at `8(%rsp)` immediately after the `call` instruction executes. This hybrid approach exploits register speed for the common case of functions with few parameters while gracefully degrading to stack-based transmission for variadic or parameter-heavy interfaces.

The frame pointer, typically `%rbp` on x86-64, serves as an optional but invaluable reference anchor within the stack frame. When a function establishes a frame pointer by saving the caller's `%rbp` and setting `%rbp` to the current `%rsp`, all local variables and saved registers gain fixed, compile-time-known offsets relative to `%rbp`, regardless of subsequent stack pointer adjustments caused by variable-length arrays or dynamic stack allocation via `alloca()`. Debuggers rely heavily on frame pointers to unwind stack traces, though modern compilers can omit them when optimization flags like `-fomit-frame-pointer` are active, trading debuggability for an extra general-purpose register.

Leaf functions—those that call no other functions—enjoy special optimization privileges. Because a leaf function never issues a `call` instruction, it need not preserve the stack alignment invariant beyond its own entry point, and it can freely use the 128-byte red zone below `%rsp` on x86-64 System V systems for scratch space without adjusting the stack pointer. This red zone remains safe from asynchronous signal handler corruption because the kernel's signal delivery mechanism accounts for it, though this guarantee does not extend to Windows x64, which lacks a red zone entirely.

## 2. Core Architecture & Mechanics

The x86-64 System V ABI partitions the sixteen general-purpose registers into three functional categories: caller-saved volatile registers, callee-saved non-volatile registers, and special-purpose registers with hardwired semantics. Understanding this taxonomy requires examining the role each register plays in the calling sequence.

The six integer argument registers—`%rdi`, `%rsi`, `%rdx`, `%rcx`, `%r8`, and `%r9`—are caller-saved, meaning the callee may overwrite them without consequence. When a function needs to invoke another function while preserving arguments for subsequent use, it must explicitly save these registers to the stack before the call and restore them afterward. The return value materializes in `%rax` for integers and pointers, or `%xmm0` for single floating-point values, with wider return types like 128-bit integers split across `%rax` and `%rdx`. The caller must not assume these registers retain their pre-call values.

The callee-saved registers—`%rbx`, `%rbp`, and `%r12` through `%r15`—impose a stricter discipline: if a function modifies any of these registers, it must restore their original values before returning. This guarantee allows the caller to trust that these registers survive across function calls, enabling the compiler to allocate long-lived variables to them without spillage. The stack pointer `%rsp` itself is implicitly callee-saved, though its value changes during function execution; the ABI requires only that `%rsp` point to the same address upon return that it held upon entry, modulo the return address pop performed by `ret`.

The registers `%r10` and `%r11` occupy a unique caller-saved category: they serve as scratch registers that the caller cannot assume survive a function call, but they also act as temporary storage for the dynamic linker during lazy symbol resolution in position-independent code. The `%rcx` register, beyond its role as the fourth integer argument, doubles as the shift count for variable-length shift instructions, while `%rdx` participates in multiplication and division operations, producing or consuming the upper bits of wide arithmetic results.

A canonical function call sequence on x86-64 System V proceeds as follows. The caller evaluates arguments right-to-left, placing the first six integers or pointers into `%rdi`, `%rsi`, `%rdx`, `%rcx`, `%r8`, and `%r9`. Arguments beyond the sixth are pushed onto the stack in reverse order, so that the seventh argument sits at the lowest address and is thus nearest to the return address. Before executing `call`, the caller ensures that `%rsp` is sixteen-byte aligned, possibly by subtracting eight from `%rsp` if the current alignment is only eight-byte. The `call` instruction then pushes the return address (the address of the instruction immediately following `call`) onto the stack, decrementing `%rsp` by eight and transferring control to the target address.

Upon entry, the callee's prologue typically saves the frame pointer and establishes a new frame:

```
push   %rbp
mov    %rsp, %rbp
sub    $N, %rsp
```

This sequence first saves the caller's `%rbp`, then sets `%rbp` to the current stack pointer, creating a stable reference point, and finally allocates `N` bytes of stack space for local variables by decrementing `%rsp`. The value `N` must be chosen such that `(%rsp + 8) mod 16 == 0` after the subtraction, maintaining the sixteen-byte alignment invariant required by the ABI. If the function uses callee-saved registers, the prologue pushes them immediately after establishing the frame pointer.

The callee performs its computation, accessing parameters via `%rdi`, `%rsi`, and so on, or via positive offsets from `%rbp` for stack-passed arguments (e.g., `16(%rbp)` accesses the seventh argument, since `8(%rbp)` holds the return address and `0(%rbp)` holds the saved frame pointer). Local variables reside at negative offsets from `%rbp`, such as `-8(%rbp)` for the first local, `-16(%rbp)` for the second, and so forth. Before returning, the epilogue restores callee-saved registers, deallocates local storage, and restores the caller's frame pointer:

```
mov    %rbp, %rsp
pop    %rbp
ret
```

The `ret` instruction pops the return address from the stack into the instruction pointer, transferring control back to the caller. Upon return, the caller must deallocate any stack-passed arguments by adding the appropriate byte count to `%rsp`, though in practice the compiler often skips this step and simply continues executing with the stack pointer adjusted, allowing subsequent function calls to overwrite the stale argument space.

ARM64's AAPCS64 calling convention exhibits structural similarities but differs in critical details. The architecture provides thirty-one general-purpose registers named `X0` through `X30`, each sixty-four bits wide, plus the stack pointer `SP` and program counter `PC`. The first eight integer or pointer arguments occupy `X0` through `X7`, while floating-point arguments use `V0` through `V7` (the lower sixty-four bits of the 128-bit SIMD registers). Return values appear in `X0` for integers, `V0` for floats, with wide return types split across multiple registers.

The link register `X30`, conventionally called `LR`, holds the return address rather than pushing it onto the stack. The `BL` (branch with link) instruction atomically sets `LR` to the address of the next instruction and transfers control to the target, while the `RET` instruction (which is actually an alias for `BR X30`) jumps to the address in `LR`. This register-based return address storage avoids a stack memory operation on every function call, improving performance on deeply pipelined ARM cores, though non-leaf functions must still save `LR` to the stack if they call other functions.

The frame pointer on ARM64 is `X29`, often abbreviated `FP`, and `X19` through `X28` are callee-saved, giving the compiler ten non-volatile registers for register allocation. The temporary registers `X9` through `X15` are caller-saved, as are the argument registers `X0` through `X7`. The stack grows downward toward lower addresses, and the ABI mandates sixteen-byte alignment for `SP` at all times, not just across function calls.

A typical ARM64 function prologue and epilogue pair looks like this:

```
stp    x29, x30, [sp, #-16]!
mov    x29, sp
sub    sp, sp, #N
...
mov    sp, x29
ldp    x29, x30, [sp], #16
ret
```

The `STP` (store pair) instruction atomically writes both `X29` (the caller's frame pointer) and `X30` (the return address) to the stack while pre-decrementing `SP` by sixteen bytes, maintaining alignment. The epilogue reverses this with `LDP` (load pair), which atomically restores both registers while post-incrementing `SP`.

The red zone concept, present on x86-64 System V, does not exist on ARM64. Any memory below the stack pointer is subject to corruption by interrupt handlers or signal delivery, so functions must always adjust `SP` before accessing local storage. This makes ARM64 function prologues slightly more expensive, as even leaf functions must decrement `SP` if they need stack space.

Variadic functions—those accepting a variable number of arguments—complicate parameter passing. On x86-64, the `%al` register must contain the count of vector (XMM) registers used for floating-point arguments before a call to a variadic function, enabling the callee to locate the boundary between register-passed and stack-passed arguments. The variadic function typically spills all register-passed arguments onto the stack in a contiguous array, then uses the `va_list`, `va_start`, `va_arg`, and `va_end` macros (which expand to architecture-specific pointer arithmetic) to iterate through them.

Position-independent code (PIC), required for shared libraries, introduces additional calling convention wrinkles. On x86-64, function calls in PIC use the `call` instruction with a PC-relative offset targeting an entry in the Procedure Linkage Table (PLT), which contains a trampoline stub that indirects through the Global Offset Table (GOT). The dynamic linker resolves symbols lazily, patching GOT entries on first call. This indirection imposes a performance cost but enables library code to reside at arbitrary addresses in the process address space.

Tail call optimization represents a powerful transformation where a function call immediately followed by a return can be replaced with a jump, reusing the caller's stack frame. The compiler must verify that the callee's parameter requirements are compatible with the available resources and that no callee-saved registers have been modified. When applicable, a tail call eliminates the stack frame overhead entirely, transforming recursion into iteration at the machine code level.

The following diagram illustrates the x86-64 stack frame layout for a function with local variables and saved registers:

```
High Addresses
+---------------------------+
| Caller's Stack Frame      |
+---------------------------+
| 7th Argument (if any)     |  16(%rbp)
+---------------------------+
| Return Address            |   8(%rbp) ← pushed by call
+---------------------------+
| Saved %rbp                |   0(%rbp) ← %rbp points here after prologue
+---------------------------+
| Saved Callee-Saved Regs   |  -8(%rbp), -16(%rbp), ...
+---------------------------+
| Local Variables           | -24(%rbp), -32(%rbp), ...
+---------------------------+
| Padding (if needed)       |
+---------------------------+ ← %rsp points here (16-byte aligned)
| Red Zone (128 bytes)      | ← leaf functions may use without adjusting %rsp
+---------------------------+
Low Addresses
```

## 3. High-Performance Optimization & Failure Modes

The calling convention imposes unavoidable overhead—register saves, stack adjustments, and memory traffic—that becomes the dominant cost in workloads with high call frequency. Optimizing compilers employ several strategies to minimize this tax, though each introduces trade-offs and potential failure modes.

Inlining eliminates the calling convention entirely by textually substituting the callee's body into the caller's code. This transformation removes the `call` and `ret` instructions, avoids register save/restore sequences, and enables interprocedural optimizations like constant propagation and dead code elimination. However, inlining inflates code size, potentially degrading instruction cache performance. Modern compilers use heuristics based on function size, call frequency, and optimization level to decide when inlining is profitable. The `inline` keyword in C serves as a hint rather than a mandate; the compiler may ignore it or inline functions not marked `inline`.

Register allocation across function boundaries requires interprocedural analysis. If a compiler can prove that a called function modifies fewer callee-saved registers than the ABI permits, it can avoid saving all of them. Link-time optimization (LTO) enables such analysis by deferring code generation until all translation units are available, allowing the optimizer to view the entire call graph. This technique is particularly effective in static executables but less so in shared libraries, where the complete call graph remains unknown until runtime.

The frame pointer omission optimization (`-fomit-frame-pointer`) reclaims `%rbp` as a general-purpose register, reducing register pressure and eliminating the frame pointer save/restore overhead. However, this complicates debugging and stack unwinding. Exception handling on x86-64 relies on `.eh_frame` metadata generated by the compiler to reconstruct stack frames without a frame pointer, but this metadata bloats the binary and increases linker complexity. The trade-off is stark: omitting the frame pointer yields a measurable performance gain (often 2-5% in register-intensive code) but makes post-mortem debugging nearly impossible without DWARF unwind information.

The System V red zone offers a clever optimization for leaf functions: the 128 bytes below `%rsp` remain reserved for the current function even across asynchronous signals, allowing leaf functions to avoid adjusting `%rsp` for small local variables. However, this optimization is architecture-specific and absent on Windows x64, where any memory below `%rsp` is volatile. Code that mixes System V and Windows calling conventions, such as when interfacing with proprietary libraries, must be carefully audited to avoid red zone violations.

Alignment faults represent a common failure mode. If a function violates the sixteen-byte stack alignment invariant before a `call` instruction, callees using SSE instructions will crash with `SIGSEGV` or `STATUS_DATATYPE_MISALIGNMENT`. These bugs are insidious because they manifest deep in the call chain, far from the site of the alignment violation. Debugging requires disassembling the crashing instruction to identify the misaligned memory operand, then tracing back through the call stack to find where `%rsp` was corrupted. Compiler instrumentation flags like `-fsanitize=alignment` can detect these errors, though at significant runtime cost.

Buffer overflows that overwrite the saved return address on the stack enable arbitrary code execution, the foundation of stack smashing attacks. Modern systems deploy several mitigations: stack canaries (random values placed between local variables and the return address, checked before `ret`), non-executable stacks (NX bit in page tables), and address space layout randomization (ASLR, which randomizes stack base addresses). However, these defenses are imperfect. Stack canaries can be leaked or brute-forced, NX can be bypassed with return-oriented programming (ROP), and ASLR entropy on 32-bit systems is insufficient. Secure code must validate all buffer bounds and use memory-safe abstractions.

Tail call optimization failures degrade performance in recursive algorithms. If the compiler cannot prove that a tail call is safe—perhaps because callee-saved registers have been modified or because the argument layout differs—it must emit a full `call`/`ret` sequence, consuming stack space and risking stack overflow in deeply recursive code. The `[[gnu::musttail]]` attribute in C++, or the `-foptimize-sibling-calls` flag, forces the compiler to emit tail calls or report an error, catching these failures at compile time.

Calling convention mismatches between caller and callee produce catastrophic failures: arguments land in the wrong registers or stack slots, return values are misinterpreted, and callee-saved registers are not restored. These bugs arise when interfacing assembly code with C, when mixing Windows and System V calling conventions in the same binary, or when using function pointers with incorrect type signatures. The symptoms are subtle—random crashes, data corruption, or silent logic errors—and the root cause is difficult to diagnose without examining disassembly. Strong type systems and strict adherence to ABI specifications are the only reliable defenses.

Register pressure in the calling convention impacts performance in hot loops. When a function exhausts available caller-saved registers and begins spilling temporaries to the stack, memory latency degrades throughput. Profiling tools like `perf` can quantify spill overhead by counting stack load/store operations. Solutions include algorithmic restructuring to reduce live ranges, loop fission to separate independent computations, or manual register allocation in assembly for critical inner loops.

The dynamic linker's lazy symbol resolution introduces unpredictable latency on the first call to a shared library function. The PLT stub invokes the resolver, which performs symbol lookup and patches the GOT, a process that can take thousands of cycles. Real-time systems often disable lazy binding with `LD_BIND_NOW=1`, forcing all symbols to resolve at load time, trading startup latency for predictable call latency. Alternatively, the `__attribute__((ifunc))` feature in GNU toolchains allows runtime selection of function implementations without PLT overhead, useful for CPU-specific dispatch.

Exception handling interacts poorly with calling conventions in C++. When an exception is thrown, the runtime must unwind the stack, invoking destructors and deallocating frames until it reaches a matching `catch` block. This unwinding relies on `.eh_frame` metadata that encodes the stack layout and callee-saved register locations. If this metadata is incorrect—due to hand-written assembly without proper CFI directives, or due to compiler bugs—the unwinder will corrupt registers or crash. The `noexcept` specifier allows the compiler to elide exception handling metadata for functions that provably cannot throw, reducing binary size and improving performance.

Calling convention evolution poses long-term maintenance challenges. The transition from 32-bit x86 (which passes all arguments on the stack) to x86-64 (which uses registers) broke binary compatibility, forcing a complete ecosystem rebuild. Future architectural extensions—such as Intel's Control-Flow Enforcement Technology (CET), which adds hardware shadow stacks to defeat ROP attacks—will likely require ABI revisions and new calling convention variants. Code that interfaces directly with assembly or relies on specific stack layouts must be audited and potentially rewritten for these transitions.

Profiling and benchmarking reveal that function call overhead dominates in microbenchmarks but often disappears in real-world workloads due to inlining and branch prediction. Premature optimization that hand-codes assembly to shave cycles from calling sequences usually backfires by inhibiting compiler optimizations. The correct approach is to profile first, identify genuine bottlenecks, then apply targeted optimizations—inlining hot paths, reducing call frequency through batching, or using indirect function dispatch for polymorphism—while trusting the compiler for everything else. The calling convention is a foundation, not a straitjacket, and modern toolchains exploit it with remarkable sophistication when given the freedom to do so.
