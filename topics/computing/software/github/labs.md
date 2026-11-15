# Operational Verification Labs: Github

## Objective & Toolchain Setup

The modern software engineering workflow demands rigorous operational verification across the entire compilation and runtime stack. When contributing to open-source repositories on GitHub or maintaining production systems, engineers must possess deep fluency in compiler intermediate representations, memory sanitizers, cache profiling, and concurrency analysis. This laboratory guide establishes a systematic verification methodology for Rust, C++, and Go projects, anchoring abstract correctness guarantees in concrete diagnostic instrumentation.

GitHub repositories represent living artifacts of distributed collaborative engineering. Each pull request, code review, and CI pipeline execution embodies a verification checkpoint. The gap between "code that compiles" and "code that performs correctly under production load" is bridged through deliberate instrumentation: static analysis via compiler intermediate representations, dynamic profiling with hardware performance counters, and adversarial stress testing with sanitizer runtimes. These techniques transform opaque runtime failures into actionable diagnostic signals, enabling engineers to operate with confidence across unfamiliar codebases.

The verification toolchain spans multiple abstraction layers. At the highest level, the Rust compiler (`rustc`) and LLVM infrastructure provide rich introspection into abstract syntax trees (ASTs), mid-level intermediate representation (MIR), and LLVM IR. Moving down the stack, CPU performance monitoring units (PMUs) expose cache miss rates, branch prediction stalls, and instruction-level parallelism through tools like `perf` and `cargo-flamegraph`. At the lowest level, dynamic sanitizers—AddressSanitizer (ASan), ThreadSanitizer (TSan), and Valgrind's Memcheck—instrument memory allocations and thread synchronization primitives to detect undefined behavior that static analysis cannot reach.

Before beginning these exercises, establish a complete systems toolchain. Install the Rust toolchain via `rustup` to obtain `cargo`, `rustc`, and `rustfmt`. On Linux systems, install LLVM and Clang to access `llvm-dis`, `llvm-objdump`, and `clang++` for C++ verification. Install the GNU toolchain (`gcc`, `g++`, `gdb`) and Valgrind for memory leak detection. For Go projects, install the official Go toolchain (`go`, `gofmt`, `go test`). On macOS, replace GDB with LLDB and use Instruments for profiling. For cache profiling, install `perf` (Linux) or leverage `cargo-flamegraph` as a cross-platform alternative. Install `cargo-expand` to inspect macro-expanded Rust code and `cargo-asm` to view assembly output. Verify the installation by running `rustc --version`, `clang --version`, `valgrind --version`, and `perf --version`. Clone a sample repository or create a local Git repository to serve as the verification substrate.

The exercises below assume a Unix-like environment with root or sudo access for hardware counter sampling. Windows users should leverage Windows Subsystem for Linux (WSL2) to access the full Linux perf subsystem. Each exercise follows a diagnostic loop: reproduce a failure or performance anomaly, instrument the system to capture diagnostic signals, interpret the output through first-principles reasoning about CPU cache hierarchies or memory models, and verify the fix through quantitative metrics. This operational discipline mirrors production incident response workflows, where logs and metrics guide iterative hypothesis refinement.

## Exercise 1: AST, IR & Disassembly Analysis

Static analysis of compiler intermediate representations exposes optimization decisions, inlining heuristics, and code generation patterns invisible in source code. Rust's multi-stage compilation pipeline—from AST to MIR to LLVM IR to machine code—provides multiple inspection points. By examining these representations, engineers diagnose unexpected binary bloat, verify bounds check elimination, and audit security-critical code paths for side-channel vulnerabilities. This exercise walks through the complete IR pipeline for a Rust function, then contrasts it with C++ LLVM IR and Go assembly.

Begin by creating a Rust library crate with a performance-critical function. Initialize a new project with `cargo new --lib ir_analysis && cd ir_analysis`. Open `src/lib.rs` and implement a vectorized summation function that processes slices of integers. The function signature `pub fn sum_slice(data: &[i32]) -> i64` accepts a borrowed slice and returns a 64-bit sum to avoid overflow. The implementation uses iterator combinators: `data.iter().map(|&x| x as i64).sum()`. This idiomatic Rust code delegates to LLVM's autovectorizer, which may emit SIMD instructions on x86-64 targets.

To inspect the AST, invoke the Rust compiler with the `-Zunpretty=ast` flag, which requires nightly Rust. Run `rustup install nightly` to obtain the nightly toolchain, then execute `rustc +nightly -Zunpretty=ast src/lib.rs > ast_output.txt`. Open `ast_output.txt` to observe the fully elaborated syntax tree, including resolved imports, expanded macros, and desugared iterator chains. The AST representation reveals how `iter()` desugars to a `core::slice::Iter` adapter and how `map()` composes with `sum()` through trait method calls. This low-level view exposes the indirection layers that disappear in optimized binaries.

Next, examine the mid-level intermediate representation (MIR), which represents Rust code after type checking and borrow checking but before LLVM optimization. MIR operates on a control flow graph of basic blocks, making lifetime and borrowing semantics explicit. Run `cargo rustc --lib -- --emit=mir` to generate `target/debug/deps/ir_analysis.mir`. Open this file and locate the `sum_slice` function. The MIR representation shows explicit lifetime annotations, borrow scopes, and match arms for `Option` handling in the iterator protocol. Observe how the iterator state machine manifests as a series of `switchInt` terminators, branching on `Option::Some` versus `Option::None`. This representation makes borrowing and ownership transfer explicit, enabling manual audit of use-after-free scenarios that sanitizers might miss in unsafe code.

To view LLVM IR, compile with `cargo rustc --lib --release -- --emit=llvm-ir`. The release mode enables optimizations, producing realistic IR. Navigate to `target/release/deps/` and locate the `.ll` file. Open it in a text editor and search for the `@_ZN11ir_analysis9sum_slice` symbol (the mangled name for `sum_slice`). The LLVM IR exposes vectorization via `<4 x i32>` vector types and `llvm.experimental.vector.reduce.add` intrinsics. Observe how LLVM represents the iterator loop as a counted loop with induction variables and how bounds checks are elided through range analysis. The IR includes metadata annotations like `!nontemporal`, `!invariant.load`, and `!noundef`, which guide downstream optimization passes and reflect Rust's strict aliasing and initialization guarantees.

Compare this output to C++ LLVM IR. Create a file `sum_slice.cpp` with an equivalent function using standard library algorithms: `#include <numeric>` and `int64_t sum_slice(const int32_t* data, size_t len) { return std::accumulate(data, data + len, 0LL); }`. Compile with `clang++ -O3 -emit-llvm -S sum_slice.cpp -o sum_slice.ll`. Inspect the generated IR. Unlike Rust, C++ does not embed ownership or lifetime metadata in the IR, so the resulting code lacks `noalias` annotations unless manually specified with `__restrict__`. The C++ version may also contain additional runtime checks for iterator validity that Rust eliminates through compile-time borrow checking.

Finally, examine the disassembled machine code. Run `cargo rustc --lib --release -- --emit=asm` to produce assembly output in `target/release/deps/`. Open the `.s` file and locate the `sum_slice` symbol. Observe the vectorized loop using SSE4.2 or AVX2 instructions like `vpaddd` (packed add doubleword) and `vphaddd` (horizontal add). Note the alignment checks and loop unrolling applied by LLVM's backend. Use `objdump -d target/release/libir_analysis.rlib` or `cargo asm ir_analysis::sum_slice` (via `cargo-asm`) to view the annotated disassembly. Cross-reference instruction addresses with source lines to verify that bounds checks have been optimized away.

To automate IR inspection in a CI pipeline, add a custom Cargo build script. Create `.cargo/config.toml` with `[build] rustflags = ["--emit=llvm-ir,asm"]`. Then, integrate `cargo-expand` to verify macro hygiene. Install it with `cargo install cargo-expand`, then run `cargo expand` to output fully macro-expanded source code. This technique surfaces hidden allocations, unexpected trait implementations, or panicking branches introduced by derive macros. Commit the expanded output to a Git branch and use `git diff` to detect unintended code generation changes across refactors.

For Go projects, leverage the built-in assembly dumper. Write a simple function in `sum.go`: `package main; func SumSlice(data []int32) int64 { var sum int64; for _, v := range data { sum += int64(v) }; return sum }`. Compile with `go build -gcflags="-S" sum.go 2> asm_output.txt`. The Go compiler emits assembly to stderr, so redirect it to a file. The output shows Go's custom calling convention, stack-based parameter passing, and runtime calls for slice bounds checks. Unlike Rust and C++, Go's runtime includes garbage collection barriers and preemption points, visible as calls to `runtime.morestack` and `runtime.gcWriteBarrier`.

This exercise establishes IR introspection as a standard verification step. Before merging pull requests that modify hot paths, generate and review LLVM IR diffs to ensure vectorization is preserved and no unexpected heap allocations appear. Automate this via GitHub Actions by running `cargo rustc -- --emit=llvm-ir` and archiving the `.ll` files as build artifacts. Over time, engineers develop intuition for recognizing optimizer regressions through IR patterns, such as inlining failures or dead code retention.

## Exercise 2: Cache Miss & Throughput Profiling

Modern CPU performance is dominated by memory hierarchy latency, not instruction throughput. A cache miss to DRAM incurs a 200-cycle penalty, while L1 cache hits complete in 4 cycles. Profiling cache behavior and identifying false sharing, TLB thrashing, or poor spatial locality separates code that "runs" from code that "runs fast." This exercise uses hardware performance counters to measure cache miss rates, correlates them with source code, and applies algorithmic transformations to improve throughput.

Select a compute-intensive Rust function as the profiling target. Create a new binary project with `cargo new --bin cache_profiling && cd cache_profiling`. Implement a naive matrix multiplication function in `src/main.rs`. Define a struct `struct Matrix { data: Vec<f64>, rows: usize, cols: usize }` with a method `fn multiply(&self, other: &Matrix) -> Matrix` that performs the standard triple-nested loop: `result[i][j] = sum(self[i][k] * other[k][j])`. Generate random matrices in `main()` with dimensions 512×512 using the `rand` crate. Add `rand = "0.8"` to `Cargo.toml`. Run the multiplication in a loop 10 times and print the elapsed duration using `std::time::Instant`.

Compile in release mode with `cargo build --release`. Run the binary and observe the baseline throughput. On a typical x86-64 system with 64-byte cache lines, the naive implementation exhibits poor cache utilization due to column-major access of the second matrix. Each access to `other[k][j]` strides across rows, causing cache line thrashing. To quantify this, profile with `perf`. Run `perf stat -e cache-references,cache-misses,L1-dcache-load-misses,instructions ./target/release/cache_profiling`. The output reports cache miss rates as a percentage. For the naive implementation, expect 30-50% L1 data cache miss rates due to the access pattern.

To correlate cache misses with source lines, record a performance profile with `perf record`. Execute `perf record -e cache-misses -g ./target/release/cache_profiling` to sample cache miss events with call stacks. This generates `perf.data`. Analyze it with `perf report`, which displays an interactive TUI showing the hottest functions and source lines. Navigate to the `multiply` method and observe that the innermost loop accumulates the majority of cache misses. Press `a` to annotate the assembly, revealing which load instructions cause stalls. The column-major access to `other[k][j]` generates irregular stride patterns that defeat the prefetcher.

Apply a cache-friendly transformation by transposing the second matrix before multiplication. Implement a `fn transpose(&self) -> Matrix` method that copies data in row-major order, then modify `multiply` to operate on the transposed version. Re-run `perf stat` and observe the cache miss rate drop to 5-10%. The throughput improvement should be 3-4x due to improved spatial locality. To verify the optimization, use `perf diff` to compare two `perf.data` files side by side. Run the original binary with `perf record -o before.data`, then run the optimized binary with `perf record -o after.data`, and execute `perf diff before.data after.data`. The differential report highlights functions with improved cache behavior.

For Rust-specific profiling, leverage `cargo-flamegraph`, which integrates `perf` with stack unwinding and generates flame graphs. Install it with `cargo install flamegraph`. Run `cargo flamegraph --bin cache_profiling`. This executes the binary under `perf record`, processes the samples, and generates `flamegraph.svg`. Open the SVG in a browser. The x-axis represents total samples (proportional to time), and the y-axis shows the call stack. Hover over wide bars to identify hot functions. The flame graph reveals not only CPU time but also inlining decisions. If a function is inlined, its samples merge into the caller, making the optimization visible.

To profile heap allocation behavior, use `valgrind` with the Massif tool. Run `valgrind --tool=massif ./target/release/cache_profiling`. This generates `massif.out.<pid>`. Analyze it with `ms_print massif.out.<pid>` to see heap usage over time. The output shows allocation peaks correlated with matrix instantiation. If profiling reveals excessive allocations in the hot loop, consider using stack-allocated arrays or arena allocators. For Rust, the `bumpalo` crate provides arena allocation with zero-cost deallocation.

Extend the profiling to multi-threaded code. Modify the matrix multiplication to use Rayon for parallel iteration. Add `rayon = "1.8"` to `Cargo.toml`, then replace the outer loop with `(0..self.rows).into_par_iter().map(|i| { ... }).collect()`. Re-run `perf stat` with the additional events `cycles,instructions,branches,branch-misses`. The output now includes IPC (instructions per cycle) and branch misprediction rates. Parallel code often exhibits lower IPC due to cache contention between threads. Use `perf record -e cache-misses -g --call-graph dwarf` to capture deep call stacks across thread boundaries. Rayon's work-stealing runtime appears in the call graph, and cache misses may concentrate in the synchronization primitives.

For false sharing detection, profile with `perf c2c` (cache-to-cache). Run `perf c2c record ./target/release/cache_profiling`, then analyze with `perf c2c report`. This tool identifies cache lines that are written by multiple threads, causing expensive cache coherence traffic. If false sharing is detected, apply padding to separate frequently written fields. In Rust, use `#[repr(align(64))]` or manually insert padding bytes to align fields to cache line boundaries.

To profile Go code, use the built-in profiler. Modify the Go matrix multiplication code to include `import "runtime/pprof"` and `import "os"`. Before the computation loop, open a file and start CPU profiling with `f, _ := os.Create("cpu.prof"); pprof.StartCPUProfile(f); defer pprof.StopCPUProfile()`. Run the binary, then analyze the profile with `go tool pprof cpu.prof`. The interactive shell supports commands like `top` to list hot functions and `list <function>` to annotate source lines with sample counts. Unlike `perf`, Go's profiler operates at the goroutine level, showing runtime scheduler overhead.

For C++ projects, integrate `perf` with symbol resolution by compiling with debug info: `g++ -O3 -g matrix.cpp -o matrix`. Run `perf record ./matrix`, then `perf report`. Ensure debug symbols are present by checking `file matrix` output. If symbols are stripped, install debug packages (e.g., `glibc-debuginfo` on Fedora) or compile with `-fno-omit-frame-pointer` to improve stack unwinding accuracy.

This exercise establishes quantitative cache profiling as a routine verification step. Before optimizing code, establish a baseline with `perf stat`. After refactoring, re-run the profiler and verify measurable improvement. Commit the `perf.data` files or flame graph SVGs to a `docs/profiling/` directory in the repository to document performance evolution. Over time, engineers internalize cache-friendly patterns like structure-of-arrays layout, loop tiling, and prefetching, reducing reliance on profilers for routine code.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs—data races, deadlocks, and memory leaks under contention—manifest non-deterministically and often escape unit tests. Dynamic sanitizers instrument thread synchronization and memory operations to detect undefined behavior at runtime. ThreadSanitizer (TSan) detects data races by tracking happens-before relationships between memory accesses. AddressSanitizer (ASan) detects use-after-free, buffer overflows, and double-free errors. This exercise demonstrates systematic stress testing of concurrent Rust and C++ code using these sanitizers, then verifies correctness through adversarial workloads.

Create a multi-threaded Rust project with deliberate concurrency bugs. Initialize with `cargo new --bin race_detection && cd race_detection`. Implement a shared counter using unsafe raw pointers to bypass Rust's type system. In `src/main.rs`, define `static mut COUNTER: i32 = 0;`. Write a function `fn increment_unsafe()` that reads, increments, and writes `COUNTER` without synchronization: `unsafe { let val = std::ptr::read_volatile(&COUNTER); std::ptr::write_volatile(&mut COUNTER, val + 1); }`. In `main()`, spawn 4 threads that each call `increment_unsafe()` 1000 times. Join the threads and print the final counter value. The output is non-deterministic due to the data race.

To detect the race with ThreadSanitizer, recompile with the instrumentation flag. Run `RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu`. Note that TSan requires a specific target triple and is incompatible with release mode optimizations. Execute the instrumented binary with `./target/x86_64-unknown-linux-gnu/debug/race_detection`. TSan emits a detailed report identifying the racing memory accesses. The output includes stack traces for both the write and read operations, showing the conflicting threads and the shared address. The report highlights the `increment_unsafe` function as the source of the race. This diagnostic precision enables immediate localization of the bug.

Fix the race by replacing the unsafe code with atomic operations. Change `static mut COUNTER: i32` to `static COUNTER: AtomicI32 = AtomicI32::new(0);` (import `std::sync::atomic::{AtomicI32, Ordering}`). Replace `increment_unsafe()` with `COUNTER.fetch_add(1, Ordering::Relaxed)`. Recompile with TSan and verify the race is eliminated. The binary now runs to completion without TSan reports, and the final counter value is deterministic (4000).

Extend the test to expose lock-order deadlocks. Introduce two mutexes: `static MUTEX_A: Mutex<()> = Mutex::new(()); static MUTEX_B: Mutex<()> = Mutex::new(());`. Spawn two threads: thread A locks A then B, thread B locks B then A. Use `std::sync::Mutex` and call `lock().unwrap()` in sequence. Run the binary under TSan. The sanitizer detects the potential deadlock by analyzing lock acquisition order across threads. TSan's report shows the inversion: one thread acquired A before B, while another acquired B before A. This violation of consistent lock ordering is flagged as a potential deadlock, even if the actual deadlock does not manifest during the particular run.

To stress test for memory leaks, integrate AddressSanitizer. Compile with `RUSTFLAGS="-Z sanitizer=address" cargo build`. ASan detects heap overflows and use-after-free errors. Introduce a deliberate leak by allocating memory without deallocation. Modify `main()` to repeatedly allocate `Box::new([0u8; 1024])` inside a loop without dropping it, using `std::mem::forget()`. Run the binary under ASan. The sanitizer reports a memory leak at exit, listing the allocation site and stack trace. ASan's leak detector runs at program termination, so it only reports leaks for allocations that are never freed.

For C++ projects, sanitizers are enabled via compiler flags. Create a C++ program with a data race: `int counter = 0; void increment() { for (int i = 0; i < 1000; ++i) ++counter; }`. Spawn multiple threads with `std::thread`. Compile with `clang++ -fsanitize=thread -O1 -g race.cpp -o race`. The `-O1` flag enables minimal optimization while preserving debug info. Run `./race`. TSan detects the race and prints a report with line numbers. Fix the race by replacing `int counter` with `std::atomic<int> counter{0}` and `++counter` with `counter.fetch_add(1, std::memory_order_relaxed)`. Recompile and verify the race is eliminated.

To detect memory leaks in C++, compile with `-fsanitize=address`: `clang++ -fsanitize=address -g leak.cpp -o leak`. Introduce a leak by calling `new int[1024]` without `delete[]`. Run the binary. ASan reports the leak with the allocation stack trace. Extend the test to detect use-after-free errors. Allocate memory with `int* p = new int{42}`, then `delete p`, followed by `std::cout << *p`. ASan immediately terminates the program upon the use-after-free, printing the allocation, deallocation, and access stack traces. This tripartite report enables rapid root cause identification.

For Go, enable the race detector with `go run -race main.go`. Implement a data race by having multiple goroutines increment a shared variable without synchronization: `var counter int; for i := 0; i < 10; i++ { go func() { counter++ }() }`. The race detector prints a report showing the conflicting accesses and the goroutine stacks. Fix the race by using a `sync.Mutex` or `atomic.AddInt64`. Go's race detector is integrated into the runtime, requiring no separate compilation step.

To systematically stress test concurrent code, use property-based testing frameworks. For Rust, integrate `proptest` or `loom`. Install `loom` with `cargo add loom --dev`. Loom provides a model checker that exhaustively explores thread interleavings. Modify the test to use `loom::thread::spawn` instead of `std::thread::spawn`. Run `cargo test` to execute the Loom model checker. It systematically explores all possible schedules, detecting races that probabilistic testing would miss. For C++, use Google's ThreadSanitizer in continuous integration pipelines. Add a CI step that compiles with `-fsanitize=thread` and runs the test suite under TSan.

To detect memory leaks in long-running services, use Valgrind's Memcheck tool. Run `valgrind --leak-check=full --show-leak-kinds=all ./target/release/service`. Valgrind reports definite leaks, possible leaks, and still-reachable memory. Definite leaks indicate memory that is no longer accessible. Possible leaks include memory reachable through interior pointers. Still-reachable memory is reachable from global variables and may be intentional. Analyze the Valgrind output to identify allocation sites that lack corresponding deallocations. Integrate Valgrind into nightly CI runs to detect leaks introduced by recent commits.

For kernel-level memory leak detection, use kmemleak on Linux. Enable it by booting with `kmemleak=on` and monitor `/sys/kernel/debug/kmemleak`. This technique applies to kernel module development and eBPF program verification, where user-space tools cannot introspect kernel memory.

This exercise establishes sanitizer-driven verification as mandatory for concurrent code. Before merging pull requests that modify shared state, run the code under TSan and ASan. Automate this via GitHub Actions by adding a CI job that compiles with sanitizers and executes the test suite. Over time, the cost of sanitizer instrumentation becomes routine, and engineers develop disciplined synchronization patterns that minimize the need for debugging.

## Developer Cheat Sheet & Toolchain Checklist

This reference consolidates the verification commands and workflow patterns demonstrated throughout the exercises. Pin this checklist to your GitHub repository's `CONTRIBUTING.md` or embed it in a pre-commit hook to enforce verification before pushing code.

**Rust Compilation & IR Inspection:**
```bash
# AST (requires nightly)
rustc +nightly -Zunpretty=ast src/lib.rs > ast_output.txt

# MIR
cargo rustc --lib -- --emit=mir

# LLVM IR (release mode)
cargo rustc --lib --release -- --emit=llvm-ir

# Assembly
cargo rustc --lib --release -- --emit=asm

# Macro expansion
cargo expand > expanded.rs

# Disassembly via cargo-asm
cargo install cargo-asm
cargo asm crate_name::function_name
```

**C++ Compilation & IR Inspection:**
```bash
# LLVM IR
clang++ -O3 -emit-llvm -S source.cpp -o output.ll

# Assembly
clang++ -O3 -S -masm=intel source.cpp -o output.s

# Disassembly
objdump -d -M intel binary > disasm.txt
```

**Go Assembly:**
```bash
go build -gcflags="-S" main.go 2> asm_output.txt
```

**Cache & Performance Profiling (Linux):**
```bash
# Hardware counters
perf stat -e cache-references,cache-misses,L1-dcache-load-misses,instructions ./binary

# Record cache misses with call stacks
perf record -e cache-misses -g ./binary

# Interactive report
perf report

# Annotate assembly
perf annotate

# Compare profiles
perf diff before.data after.data

# Flame graph (Rust)
cargo install flamegraph
cargo flamegraph --bin binary_name

# False sharing detection
perf c2c record ./binary
perf c2c report
```

**Heap Profiling (Valgrind):**
```bash
# Memory leak detection
valgrind --leak-check=full --show-leak-kinds=all ./binary

# Heap usage over time
valgrind --tool=massif ./binary
ms_print massif.out.<pid>
```

**Sanitizers (Rust):**
```bash
# AddressSanitizer (heap safety)
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/binary

# ThreadSanitizer (data race detection)
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/binary

# LeakSanitizer (memory leaks)
RUSTFLAGS="-Z sanitizer=leak" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/binary
```

**Sanitizers (C++):**
```bash
# AddressSanitizer
clang++ -fsanitize=address -O1 -g source.cpp -o binary

# ThreadSanitizer
clang++ -fsanitize=thread -O1 -g source.cpp -o binary

# UndefinedBehaviorSanitizer
clang++ -fsanitize=undefined -g source.cpp -o binary

# Combined (ASan + UBSan)
clang++ -fsanitize=address,undefined -g source.cpp -o binary
```

**Sanitizers (Go):**
```bash
# Race detector
go run -race main.go
go test -race ./...

# Build with race detector
go build -race -o binary main.go
```

**Model Checking (Rust):**
```bash
# Loom (concurrency model checker)
cargo add loom --dev
# Replace std::thread with loom::thread in tests
cargo test
```

**Benchmarking (Rust):**
```bash
# Criterion.rs (statistical benchmarks)
cargo add criterion --dev
cargo bench

# Built-in benchmarks (nightly)
#[bench] attribute
cargo +nightly bench
```

**Continuous Integration Workflow:**
```yaml
# .github/workflows/verify.yml
name: Verification
on: [push, pull_request]
jobs:
  sanitizers:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: nightly
          override: true
      - name: AddressSanitizer
        run: RUSTFLAGS="-Z sanitizer=address" cargo test --target x86_64-unknown-linux-gnu
      - name: ThreadSanitizer
        run: RUSTFLAGS="-Z sanitizer=thread" cargo test --target x86_64-unknown-linux-gnu
  profiling:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install perf
        run: sudo apt-get install linux-tools-common linux-tools-generic
      - name: Profile
        run: cargo build --release && perf stat -e cache-misses ./target/release/binary
```

**Pre-commit Hook Template:**
```bash
#!/bin/bash
# .git/hooks/pre-commit
set -e

# Run tests with sanitizers
RUSTFLAGS="-Z sanitizer=address" cargo test --target x86_64-unknown-linux-gnu
RUSTFLAGS="-Z sanitizer=thread" cargo test --target x86_64-unknown-linux-gnu

# Check formatting
cargo fmt -- --check

# Lint
cargo clippy -- -D warnings

# Verify no performance regressions
cargo bench --no-run
```

**Debugging Workflows:**
```bash
# GDB (C++/Rust)
gdb ./binary
(gdb) break main
(gdb) run
(gdb) backtrace
(gdb) info registers
(gdb) x/16xb $rsp  # examine stack

# LLDB (macOS/Rust)
lldb ./binary
(lldb) breakpoint set -n main
(lldb) run
(lldb) bt
(lldb) register read

# Rust backtrace
RUST_BACKTRACE=1 ./binary
RUST_BACKTRACE=full ./binary

# Core dumps
ulimit -c unlimited
./binary  # crash
gdb ./binary core
```

**Ecosystem-Specific Tools:**
```bash
# Rust: Miri (interpret MIR for UB detection)
cargo +nightly miri test

# Rust: cargo-careful (stdlib with extra checks)
cargo install cargo-careful
cargo +nightly careful test

# Go: pprof (CPU/memory profiling)
import _ "net/http/pprof"
go tool pprof http://localhost:6060/debug/pprof/profile

# C++: cppcheck (static analysis)
cppcheck --enable=all --inconclusive source.cpp
```

**Performance Tuning Heuristics:**
- Cache miss rate > 10%: investigate data layout and access patterns
- IPC < 1.0: check for branch mispredictions or memory stalls
- Flame graph shows wide bars in allocator: reduce heap allocations
- TSan reports races in lock-free code: verify memory ordering semantics
- ASan overhead > 3x: batch operations to amortize instrumentation cost

**Common Pitfalls:**
- Running sanitizers in release mode: use debug or minimal optimization (`-O1`)
- Missing debug symbols: compile with `-g` for meaningful stack traces
- Ignoring TSan suppressions: legitimate races in third-party code require suppression files
- Over-relying on unit tests: stress tests and adversarial workloads expose concurrency bugs
- Profiling on laptop CPUs: thermal throttling skews results; use server-class hardware

This checklist transforms operational verification from ad-hoc debugging sessions into systematic engineering discipline. Each command represents a hypothesis test: the code either passes the sanitizer, exhibits acceptable cache behavior, or reveals a latent bug. By integrating these tools into daily workflows and CI pipelines, engineers elevate code quality from "it compiles" to "it performs correctly under adversarial conditions." The diagnostic muscle memory developed through these exercises generalizes across languages and platforms, equipping practitioners to debug production incidents, optimize hot paths, and review pull requests with quantitative rigor.
