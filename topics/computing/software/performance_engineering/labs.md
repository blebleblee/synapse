# Operational Verification Labs: Performance Engineering

Performance engineering transforms empirical observation into predictable system behavior. While algorithmic complexity establishes theoretical bounds, real-world performance emerges from the mechanical interplay of memory hierarchies, instruction pipelines, branch predictors, and compiler optimization passes. These laboratories ground performance analysis in concrete measurement, teaching you to instrument programs, interpret profiler output, diagnose pathological cache behavior, and verify concurrency correctness through sanitizer tooling. You will compile programs to intermediate representations, disassemble optimized machine code, capture flamegraphs under load, and provoke data races to observe how ThreadSanitizer reconstructs happens-before orderings from instrumented memory accesses.

Modern performance work begins with compiler introspection. When you invoke `rustc` or `clang`, the compiler constructs an abstract syntax tree, lowers it to an intermediate representation, performs dataflow analysis and optimization passes, then emits target-specific machine code. Understanding this pipeline allows you to diagnose why a hot loop fails to vectorize, why a tail call never optimizes, or why a seemingly simple function generates hundreds of instructions. The LLVM intermediate representation serves as the universal language of optimization: a static single-assignment form where every value is defined exactly once, enabling aggressive constant propagation, dead code elimination, and loop transformations. By examining LLVM IR and the resulting assembly, you develop intuition for how high-level constructs map onto the microarchitectural substrate of execution units, register renaming, and out-of-order dispatch.

Memory hierarchy performance dominates modern application behavior. A cache miss to DRAM costs approximately two hundred cycles on contemporary x86-64 processors, while an L1 hit completes in four cycles. This two-order-of-magnitude latency gap means that memory access patterns dictate throughput far more than instruction count. Cache-oblivious algorithms, structure-of-arrays layout transformations, and prefetch instructions exist solely to exploit spatial and temporal locality. Profiling cache miss rates requires hardware performance counters, exposed through Linux `perf_event_open` and tools like `perf stat`. You will learn to correlate cache misses with specific source lines, identify false sharing between threads contending on adjacent cache lines, and measure memory bandwidth saturation when working sets exceed last-level cache capacity.

Concurrency correctness verification demands systematic exploration of thread interleavings. Data races occur when two threads access the same memory location without synchronization and at least one access is a write. The C++ memory model defines data races as undefined behavior, permitting compilers to assume freedom from races and optimize accordingly. ThreadSanitizer instruments every memory access and synchronization primitive, maintaining shadow state to reconstruct the happens-before partial order defined by the memory model. When a race is detected, ThreadSanitizer reports both access sites with full stack traces, allowing you to identify missing mutex acquisitions or atomic orderings. AddressSanitizer similarly instruments allocations to detect out-of-bounds accesses, use-after-free, and double-free errors by maintaining redzones and quarantine lists. These dynamic analysis tools impose significant runtime overhead but provide deterministic bug detection that stress testing alone cannot guarantee.

The laboratories that follow guide you through the full performance engineering workflow. You will compile Rust and C++ programs with varying optimization levels, compare their IR and disassembly, then profile memory access patterns and execution hotspots using hardware counters and sampling profilers. You will deliberately introduce data races and memory errors to observe sanitizer diagnostics, learning to interpret stack traces, understand shadow memory reports, and correlate sanitizer findings with source-level bugs. Each exercise provides complete, runnable code with exact compiler flags, profiler invocations, and expected output. By the end, you will possess a practiced fluency with the diagnostic toolchain that distinguishes performance-aware systems programmers from those who rely on hope and intuition.


## Objective & Toolchain Setup

The primary objective of these laboratories is to establish fluency with the production toolchain for performance analysis and verification. You will measure program behavior using hardware performance counters, disassemble optimized code to understand compiler transformations, profile cache miss rates and CPU cycles consumed per function, and verify memory safety and concurrency correctness through dynamic instrumentation. This is not abstract academic exercise; these are the techniques employed daily in production systems at scale, from latency-sensitive trading systems to throughput-critical data processing pipelines.

Your environment must include a modern Rust toolchain, Clang/LLVM for C++ compilation, and the suite of sanitizers and profilers that expose microarchitectural and memory subsystem behavior. Begin by installing Rust through `rustup`, which provides `cargo`, `rustc`, and `rustfmt`. Ensure you have at least Rust 1.70 or later, as newer releases include critical performance instrumentation improvements. Install LLVM and Clang version 15 or later, which includes AddressSanitizer, ThreadSanitizer, MemorySanitizer, and UndefinedBehaviorSanitizer as first-class features. On Debian-derived Linux distributions, invoke `apt install clang lldb valgrind linux-tools-generic` to acquire the necessary tools. On macOS, Xcode command-line tools provide `clang` and `lldb`, though you will need Homebrew to install `valgrind` if desired, noting that Valgrind support on macOS is incomplete and AddressSanitizer is preferred.

Install `cargo-flamegraph` to generate interactive SVG flamegraphs from sampling profiler data. Execute `cargo install flamegraph` to acquire the tool, which wraps Linux `perf` or macOS DTrace to capture stack samples and fold them into hierarchical visualizations. Flamegraphs expose the call stack distribution of CPU time, making hot paths immediately visible. You will also need `cargo-asm` or `cargo-show-asm` to inspect emitted assembly for individual functions without wading through megabytes of compiler output. Install it via `cargo install cargo-show-asm`. For microbenchmarking, install the Criterion benchmarking framework, which provides statistical rigor and warmup phases to account for JIT compilation and CPU frequency scaling. Finally, ensure your kernel's `perf_event_paranoid` setting permits user-space performance counter access by checking `cat /proc/sys/kernel/perf_event_paranoid`. A value of 2 or lower allows unprivileged profiling; if necessary, temporarily lower it with `echo 1 | sudo tee /proc/sys/kernel/perf_event_paranoid`.

Verify your toolchain installation by creating a minimal Rust project. Execute `cargo new perflab && cd perflab` to generate a skeleton project. Open `Cargo.toml` and add a benchmark configuration section. Create a `benches` directory and confirm that `cargo bench` executes without error. Verify Clang functionality by creating a simple C++ source file, compiling it with `-fsanitize=address -g`, and confirming the resulting binary links against AddressSanitizer runtime libraries. Execute `clang++ --version` and confirm LLVM version 15 or later. Check `lldb` availability by invoking `lldb --version`. If `perf` is available on your Linux system, execute `perf list` to enumerate available hardware counters. You should see events like `cycles`, `instructions`, `cache-references`, and `cache-misses`. These raw counters will form the empirical foundation of your performance analysis work.

Your workspace should include separate directories for each exercise, with dedicated `Cargo.toml` files and source trees. The exercises assume a Linux environment with `perf` available, but macOS users can substitute DTrace or Instruments, and the Rust portions remain fully portable. When profiling, disable CPU frequency scaling to ensure reproducible measurements. On Linux, set the governor to performance mode with `echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`. Close unnecessary background applications to minimize measurement noise. Performance engineering demands discipline: run benchmarks multiple times, report median and variance, and isolate confounding factors. The laboratories intentionally introduce pathological cases to make performance cliffs visible and teachable. In production, you will encounter these same pathologies in subtler forms, and your practiced diagnostic fluency will determine whether you identify root causes in minutes or remain mired in speculation for days.


## Exercise 1: AST, IR & Disassembly Analysis

Compilers transform human-readable source code through multiple intermediate representations before emitting executable machine code. Understanding this transformation pipeline is essential for performance engineering because optimization decisions occur at each stage. The Rust compiler parses source into an abstract syntax tree, performs type checking and borrow checking, then lowers to mid-level intermediate representation (MIR) for region inference and optimization. MIR is converted to LLVM IR, where the LLVM optimization pipeline applies dataflow analysis, constant propagation, loop unrolling, vectorization, and instruction selection. Finally, the code generator emits target-specific assembly and machine code. By examining these intermediate forms, you learn to predict when optimizations will fire, diagnose why a loop fails to vectorize, and understand the true cost of abstractions.

Create a new Rust project named `ir-analysis` and define a simple summation function that exhibits different performance characteristics depending on optimization level. The function will sum integers in a vector, a task that should compile to efficient SIMD instructions under optimization but may produce naive scalar code at debug builds. Write the following in `src/lib.rs`:

```rust
pub fn sum_slice(data: &[i64]) -> i64 {
    let mut total = 0i64;
    for &value in data {
        total = total.wrapping_add(value);
    }
    total
}

pub fn sum_iterator(data: &[i64]) -> i64 {
    data.iter().copied().fold(0i64, i64::wrapping_add)
}

#[inline(never)]
pub fn sum_cold_path(data: &[i64]) -> i64 {
    if data.len() > 1000 {
        expensive_computation(data)
    } else {
        data.iter().sum()
    }
}

#[inline(never)]
fn expensive_computation(data: &[i64]) -> i64 {
    data.iter().map(|&x| x * 2).sum::<i64>() / 2
}
```

The `sum_slice` function uses explicit indexing-free iteration, which allows LLVM to recognize the pattern and emit vectorized code. The `sum_iterator` variant expresses the same intent through higher-order combinators. The `sum_cold_path` function intentionally prevents inlining with the `#[inline(never)]` attribute to observe call overhead. Compile this library in debug mode with `cargo build` and in release mode with `cargo build --release`. Examine the unoptimized code first to understand the baseline. Execute `cargo rustc -- --emit=llvm-ir` to generate `target/debug/deps/ir_analysis-*.ll`, the LLVM IR file. Open this file and locate the `sum_slice` function. You will see basic blocks, SSA-form temporaries with numeric suffixes, and explicit branch instructions. The debug build performs no optimization; every source-level operation translates directly to IR.

Now compile with optimizations and emit LLVM IR: `cargo rustc --release -- --emit=llvm-ir`. The release IR resides in `target/release/deps/ir_analysis-*.ll`. Search for `sum_slice` and observe the transformation. The loop body has been unrolled, and if your target supports AVX2, you will see vector instructions like `@llvm.x86.avx2.pmadd.wd` or explicit `<4 x i64>` vector types. LLVM recognized the reduction pattern and emitted horizontal add instructions to sum vector lanes. Compare the iterator-based `sum_iterator` function: it should produce nearly identical IR, demonstrating that Rust's zero-cost abstractions truly compile to the same machine code. The key LLVM optimization passes responsible for this transformation include loop vectorization (`-loop-vectorize`), scalar evolution analysis to prove trip counts, and cost modeling to decide vector width. These passes only fire when LLVM can prove the absence of aliasing, wrap-around behavior, and side effects.

Next, examine the disassembly to see the final machine code. Use `cargo-show-asm` to isolate individual functions. Install it if you have not already with `cargo install cargo-show-asm`, then invoke `cargo asm --release ir_analysis::sum_slice`. You will see x86-64 assembly, likely starting with register moves to set up accumulators, then a loop containing `vpaddd` or `vpaddq` instructions if SIMD is engaged. Notice the absence of bounds checks: LLVM proved that slice iteration never accesses out-of-bounds memory and elided the checks entirely. This is the power of borrow checking combined with aggressive optimization. Compare this to the `sum_cold_path` disassembly with `cargo asm --release ir_analysis::sum_cold_path`. The function prologue will set up a stack frame, then you will see a call instruction invoking `expensive_computation`. The `#[inline(never)]` attribute prevented inlining, forcing call overhead and register spills.

To understand how optimization levels affect code generation, compile with varying `-C opt-level` settings. Execute `cargo rustc --release -- -C opt-level=1 --emit=asm` and compare the resulting assembly in `target/release/deps/ir_analysis-*.s` to the default `opt-level=3`. Level 1 disables expensive interprocedural optimizations and loop unrolling, so you will see tighter but potentially slower code. Level 2 applies most optimizations but avoids those that significantly increase code size. Level 3, the default for release builds, prioritizes speed over size. Additionally, examine the effect of link-time optimization, which enables cross-crate inlining and whole-program analysis. Add `lto = true` to the `[profile.release]` section in `Cargo.toml` and rebuild. LTO produces a single monolithic LLVM IR module before optimization, permitting inlining across crate boundaries and dead code elimination of unused public functions. Measure the resulting binary size with `ls -lh target/release/libir_analysis.rlib` and compare with and without LTO. The size reduction can be dramatic for large projects with many small functions.

Extend the exercise by introducing deliberate optimization barriers. Modify `sum_slice` to include an opaque function call within the loop:

```rust
pub fn sum_slice_with_call(data: &[i64]) -> i64 {
    let mut total = 0i64;
    for &value in data {
        total = total.wrapping_add(black_box(value));
    }
    total
}

#[inline(never)]
fn black_box<T>(val: T) -> T {
    val
}
```

The `black_box` function, marked `#[inline(never)]`, forces a function call for every iteration, preventing LLVM from hoisting, unrolling, or vectorizing the loop. Recompile and examine the assembly. You will see a call instruction inside the loop body, destroying performance. This technique is critical for microbenchmarking: without `black_box` or similar barriers, LLVM may optimize away your entire benchmark, computing results at compile time via constant folding. The standard library provides `std::hint::black_box` for precisely this purpose. Use it to prevent the optimizer from seeing through test inputs, ensuring your benchmark measures runtime execution rather than compile-time constant evaluation.

Finally, compare Rust's code generation to equivalent C++. Create a file `sum.cpp` with analogous functions:

```cpp
#include <cstdint>
#include <vector>

extern "C" int64_t sum_slice_cpp(const int64_t* data, size_t len) {
    int64_t total = 0;
    for (size_t i = 0; i < len; ++i) {
        total += data[i];
    }
    return total;
}

extern "C" int64_t sum_iterator_cpp(const int64_t* data, size_t len) {
    int64_t total = 0;
    const int64_t* end = data + len;
    for (const int64_t* p = data; p != end; ++p) {
        total += *p;
    }
    return total;
}
```

Compile with Clang at `-O3` and emit LLVM IR: `clang++ -O3 -S -emit-llvm sum.cpp -o sum.ll`. Open `sum.ll` and compare to the Rust IR. Both should exhibit similar vectorization patterns, demonstrating that LLVM's optimization passes operate uniformly across frontend languages. The key difference lies in aliasing analysis: Rust's borrow checker provides stronger aliasing guarantees, allowing LLVM to assume no aliasing without requiring `__restrict__` annotations. In C++, you would need to annotate pointers with `__restrict__` or rely on heuristics, which can be brittle. Compile the C++ code to assembly with `clang++ -O3 -S sum.cpp -o sum.s` and inspect the output. The instruction sequences should closely match the Rust assembly, confirming that both languages expose the same underlying hardware capabilities when properly optimized.

This exercise establishes the mental model for reasoning about compiler transformations. When you write high-level Rust or C++, you must predict how it will lower to IR and then to machine code. Optimization is not magic; it is a deterministic sequence of pattern matching and dataflow transformations. By studying IR and disassembly, you internalize the conditions that enable vectorization, inlining, and devirtualization. This fluency distinguishes engineers who write fast code from those who write slow code and hope profilers will save them. Profilers reveal where time is spent, but only compiler understanding reveals why.


## Exercise 2: Cache Miss & Throughput Profiling

Memory latency dominates modern performance. A single cache miss to DRAM costs approximately two hundred CPU cycles on contemporary hardware, while an L1 cache hit completes in four cycles. This fifty-to-one latency ratio means that memory access patterns determine throughput far more than instruction count. Cache-oblivious algorithms and data structure layout transformations exist solely to exploit the spatial and temporal locality of reference. Profiling cache behavior requires hardware performance counters, exposed through the `perf_event_open` system call on Linux and accessible via the `perf` command-line tool. These counters allow you to measure cycles, instructions, cache references, cache misses, branch mispredictions, and TLB misses at the granularity of individual functions or source lines. This exercise teaches you to capture these metrics, correlate them with source code, and diagnose pathological memory access patterns.

Create a new Rust project named `cache-profiling` with `cargo new --lib cache-profiling`. You will implement two matrix traversal patterns: row-major and column-major iteration over a two-dimensional array stored in row-major order. This canonical example exposes the cache hierarchy because row-major traversal exhibits spatial locality, fetching entire cache lines into L1, while column-major traversal incurs a cache miss on every access when the matrix exceeds cache capacity. Define the following in `src/lib.rs`:

```rust
pub struct Matrix {
    data: Vec<f64>,
    rows: usize,
    cols: usize,
}

impl Matrix {
    pub fn new(rows: usize, cols: usize) -> Self {
        Matrix {
            data: vec![0.0; rows * cols],
            rows,
            cols,
        }
    }

    pub fn fill_sequential(&mut self) {
        for i in 0..self.data.len() {
            self.data[i] = i as f64;
        }
    }

    #[inline(never)]
    pub fn sum_row_major(&self) -> f64 {
        let mut total = 0.0;
        for row in 0..self.rows {
            for col in 0..self.cols {
                total += self.data[row * self.cols + col];
            }
        }
        total
    }

    #[inline(never)]
    pub fn sum_column_major(&self) -> f64 {
        let mut total = 0.0;
        for col in 0..self.cols {
            for row in 0..self.rows {
                total += self.data[row * self.cols + col];
            }
        }
        total
    }
}
```

The `sum_row_major` function traverses the matrix in storage order, accessing consecutive memory addresses. Each cache line fetched from memory contains multiple adjacent elements, and subsequent accesses hit L1 cache. The `sum_column_major` function traverses by column, jumping by `cols * 8` bytes (the size of `f64`) on each inner loop iteration. When `cols` is large, this stride exceeds the cache line size, and each access misses L1 and possibly L2, fetching a new cache line that is mostly unused. The `#[inline(never)]` attribute ensures these functions appear in profiler output as distinct symbols.

Create a benchmark harness to drive the profiling workload. Add the following to `Cargo.toml`:

```toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "matrix_bench"
harness = false
```

Create `benches/matrix_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use cache_profiling::Matrix;

fn bench_matrix_traversal(c: &mut Criterion) {
    let mut group = c.benchmark_group("matrix_traversal");
    
    for size in [512, 1024, 2048].iter() {
        let mut matrix = Matrix::new(*size, *size);
        matrix.fill_sequential();
        
        group.bench_with_input(
            BenchmarkId::new("row_major", size),
            size,
            |b, _| b.iter(|| black_box(matrix.sum_row_major()))
        );
        
        group.bench_with_input(
            BenchmarkId::new("column_major", size),
            size,
            |b, _| b.iter(|| black_box(matrix.sum_column_major()))
        );
    }
    
    group.finish();
}

criterion_group!(benches, bench_matrix_traversal);
criterion_main!(benches);
```

The benchmark measures matrix summation for sizes 512×512, 1024×1024, and 2048×2048. A 1024×1024 matrix of `f64` occupies 8 MB, exceeding typical L2 cache capacity (256 KB to 1 MB) but fitting comfortably in L3 (several MB). A 2048×2048 matrix occupies 32 MB, often exceeding L3 and forcing DRAM accesses. Run the benchmark with `cargo bench` to establish baseline performance. Criterion will report throughput and latency for each configuration. You should observe that column-major traversal is significantly slower than row-major, with the gap widening as matrix size increases.

Now profile with hardware performance counters to measure cache misses directly. On Linux, use `perf stat` to capture aggregate counters. Build the benchmark in release mode with `cargo bench --no-run` to produce the binary, then locate it in `target/release/deps/matrix_bench-*`. Execute:

```bash
perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-load-misses \
  target/release/deps/matrix_bench-* --bench --profile-time=10
```

The `perf stat` command runs the benchmark and reports hardware counter totals. The `-e` flag specifies events: `cycles` measures CPU cycles elapsed, `instructions` counts retired instructions, `cache-references` counts all cache accesses, and `cache-misses` counts last-level cache misses. The `L1-dcache-load-misses` event counts L1 data cache misses. After execution, `perf` prints a summary showing instructions per cycle (IPC), cache miss rate, and absolute counts. For row-major traversal, expect an IPC near 2 to 3 and a low cache miss rate (under 1%). For column-major traversal, expect IPC below 1 and cache miss rates exceeding 10%, indicating memory-bound execution.

To attribute cache misses to specific source lines, use `perf record` and `perf report`. Record execution samples with:

```bash
perf record -e cache-misses -g --call-graph dwarf \
  target/release/deps/matrix_bench-* --bench --profile-time=10
```

The `-e cache-misses` flag samples on cache miss events, collecting a stack trace for each sample via `-g --call-graph dwarf`. This produces `perf.data` in the current directory. Analyze it with `perf report`, which opens an interactive TUI showing cache misses attributed to functions and source lines. Navigate to `sum_column_major` and press Enter to expand the call graph. You will see that the inner loop dominates cache misses. Press `a` to annotate the assembly, displaying the exact instruction responsible for most misses: the load from `self.data[row * self.cols + col]`. This is the strided access that defeats the cache prefetcher.

Generate a flamegraph to visualize CPU time distribution. Install `cargo-flamegraph` if you have not already, then execute:

```bash
cargo flamegraph --bench matrix_bench -- --bench --profile-time=10
```

This wraps `perf record` with a sampling profiler, captures stack traces, and folds them into an interactive SVG. Open `flamegraph.svg` in a browser. The flamegraph displays functions as horizontal bars, with width proportional to CPU time. You should see `sum_column_major` consuming significantly more CPU time than `sum_row_major` for large matrices. Click on the bars to zoom into call stacks. Flamegraphs make hot paths immediately visible and are indispensable for profiling production services under load.

Extend the exercise by introducing cache-oblivious optimization. Implement a blocked matrix traversal that processes the matrix in tiles small enough to fit in L1 cache:

```rust
impl Matrix {
    #[inline(never)]
    pub fn sum_blocked(&self, block_size: usize) -> f64 {
        let mut total = 0.0;
        for block_row in (0..self.rows).step_by(block_size) {
            for block_col in (0..self.cols).step_by(block_size) {
                let row_end = (block_row + block_size).min(self.rows);
                let col_end = (block_col + block_size).min(self.cols);
                for row in block_row..row_end {
                    for col in block_col..col_end {
                        total += self.data[row * self.cols + col];
                    }
                }
            }
        }
        total
    }
}
```

Benchmark `sum_blocked` with block sizes of 32, 64, and 128. A block size of 64 means each tile is 64×64 `f64` elements, occupying 32 KB, comfortably fitting in L1 data cache (typically 32 KB per core). Profile with `perf stat` and confirm that cache miss rates drop dramatically compared to column-major traversal. The blocked algorithm maintains spatial locality within each tile, and the outer loops traverse tiles in row-major order, preserving coarse-grained locality. This technique generalizes to matrix multiplication, convolution, and any algorithm with nested loops over multidimensional arrays.

Finally, measure memory bandwidth saturation. When working sets exceed L3 cache, performance becomes bound by DRAM bandwidth rather than latency. Use `perf stat` with additional events:

```bash
perf stat -e cycles,instructions,cache-misses,mem_load_retired.l3_miss,mem_inst_retired.all_loads \
  target/release/deps/matrix_bench-* --bench --profile-time=10
```

The `mem_load_retired.l3_miss` event counts loads that missed L3 and fetched from DRAM. The `mem_inst_retired.all_loads` event counts total load instructions. Divide L3 misses by total loads to estimate the fraction of memory accesses hitting DRAM. For large matrices traversed column-major, this fraction approaches 100%, and throughput saturates at DRAM bandwidth (typically 20 to 40 GB/s per channel on modern systems). Compare this to row-major traversal, where most accesses hit L3 or L2, and throughput is limited by execution units rather than memory bandwidth.

This exercise establishes the empirical workflow for diagnosing memory bottlenecks. You have learned to capture hardware counter metrics, attribute cache misses to source lines, generate flamegraphs to identify hot paths, and apply algorithmic transformations to improve locality. In production systems, cache miss profiling reveals pathological hash table probing, inefficient serialization formats, and poorly laid-out data structures. The techniques you practiced here scale from microbenchmarks to full applications running under realistic load. Performance engineering is measurement-driven, and hardware performance counters provide the ground truth that intuition and microbenchmarks alone cannot deliver.


## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency correctness is non-negotiable in systems programming. A data race occurs when two threads access the same memory location without synchronization and at least one access is a write. Under the C++ and Rust memory models, data races constitute undefined behavior, permitting compilers to assume freedom from races and optimize accordingly. A single unprotected write can corrupt unrelated data structures through store tearing or reordering. ThreadSanitizer detects races dynamically by instrumenting every memory access and synchronization primitive, maintaining shadow state to reconstruct the happens-before partial order. AddressSanitizer detects spatial and temporal memory errors: buffer overflows, use-after-free, and double-free bugs. LeakSanitizer identifies memory leaks by intercepting allocations and checking for unreachable blocks at exit. This exercise teaches you to deliberately introduce concurrency and memory errors, interpret sanitizer diagnostics, and correlate findings with source-level bugs.

Create a new Rust project named `sanitizer-testing` with `cargo new sanitizer-testing`. You will implement a concurrent counter with intentional data races, a use-after-free scenario, and a memory leak. Begin with the racy counter. Define the following in `src/main.rs`:

```rust
use std::sync::Arc;
use std::thread;

struct RacyCounter {
    value: u64,
}

impl RacyCounter {
    fn new() -> Self {
        RacyCounter { value: 0 }
    }

    fn increment(&mut self) {
        self.value += 1;
    }

    fn get(&self) -> u64 {
        self.value
    }
}

fn test_racy_counter() {
    let counter = Arc::new(std::cell::UnsafeCell::new(RacyCounter::new()));
    let mut handles = vec![];

    for _ in 0..4 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100_000 {
                unsafe {
                    (*counter_clone.get()).increment();
                }
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    unsafe {
        println!("Final counter value: {}", (*counter.get()).get());
    }
}

fn main() {
    test_racy_counter();
}
```

This code wraps a simple counter in `UnsafeCell` to bypass Rust's borrow checker and deliberately introduces a data race. Four threads concurrently increment the counter without synchronization. The expected final value is 400,000, but due to lost updates from race conditions, the actual value will be less. Run the program with `cargo run` multiple times. The final value varies non-deterministically, confirming the race.

ThreadSanitizer is integrated into the Rust toolchain via the `-Z sanitizer=thread` flag, which requires nightly Rust. Install nightly with `rustup install nightly`, then compile and run with:

```bash
cargo +nightly run -Z build-std --target x86_64-unknown-linux-gnu --release -- -Z sanitizer=thread
```

Note that as of recent Rust versions, ThreadSanitizer support is still stabilizing, and the syntax may vary. An alternative approach uses environment variables and rebuild. Set `RUSTFLAGS` to enable the sanitizer:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --target x86_64-unknown-linux-gnu
```

If ThreadSanitizer is correctly enabled, the program will report a data race upon execution. The output includes both conflicting accesses with full stack traces:

```
WARNING: ThreadSanitizer: data race (pid=...)
  Write of size 8 at 0x7f... by thread T2:
    #0 RacyCounter::increment src/main.rs:10
    #1 test_racy_counter::{{closure}} src/main.rs:23
    ...
  Previous write of size 8 at 0x7f... by thread T1:
    #0 RacyCounter::increment src/main.rs:10
    #1 test_racy_counter::{{closure}} src/main.rs:23
    ...
```

ThreadSanitizer identifies the exact source line (`self.value += 1`) where the race occurs and the threads involved. This is the gold standard for race detection: precise, deterministic, and actionable. Fix the race by replacing `UnsafeCell` and raw pointer access with `Mutex`:

```rust
use std::sync::{Arc, Mutex};

fn test_safe_counter() {
    let counter = Arc::new(Mutex::new(0u64));
    let mut handles = vec![];

    for _ in 0..4 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100_000 {
                let mut guard = counter_clone.lock().unwrap();
                *guard += 1;
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Final counter value: {}", *counter.lock().unwrap());
}

fn main() {
    test_safe_counter();
}
```

Recompile and run with ThreadSanitizer. No race is reported, and the final value is always 400,000. The `Mutex` provides mutual exclusion, ensuring that only one thread accesses the counter at a time. The happens-before edges established by `lock()` and `unlock()` synchronize memory, making the increment atomic from the perspective of the memory model.

Next, introduce a use-after-free error to test AddressSanitizer. Modify `src/main.rs`:

```rust
fn test_use_after_free() {
    let mut vec = vec![1, 2, 3, 4, 5];
    let ptr = vec.as_ptr();
    drop(vec);
    unsafe {
        println!("Dereferencing freed memory: {}", *ptr);
    }
}

fn main() {
    test_use_after_free();
}
```

This code obtains a raw pointer to a `Vec`, drops the vector to free its memory, then dereferences the pointer. In optimized builds, this may appear to work due to allocator reuse patterns or luck, but it is undefined behavior. Compile with AddressSanitizer:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly run --target x86_64-unknown-linux-gnu
```

AddressSanitizer reports a heap-use-after-free error:

```
ERROR: AddressSanitizer: heap-use-after-free on address 0x... at pc 0x... bp 0x... sp 0x...
READ of size 4 at 0x... thread T0
    #0 test_use_after_free src/main.rs:6
    ...
freed by thread T0 here:
    #0 dealloc ...
    #1 drop ...
    #2 test_use_after_free src/main.rs:4
    ...
previously allocated by thread T0 here:
    #0 malloc ...
    #1 alloc ...
    #2 test_use_after_free src/main.rs:2
    ...
```

AddressSanitizer provides three stack traces: where the invalid access occurred, where the memory was freed, and where it was originally allocated. This triangulation makes debugging straightforward. The shadow memory maintained by AddressSanitizer marks freed regions as poisoned, and any access to poisoned memory triggers a report.

Introduce a memory leak to test LeakSanitizer. Modify `src/main.rs`:

```rust
fn test_memory_leak() {
    let leaked = Box::new(vec![0u8; 1024 * 1024]);
    std::mem::forget(leaked);
    println!("Leaked 1 MB");
}

fn main() {
    test_memory_leak();
}
```

The `std::mem::forget` function prevents the `Box` destructor from running, leaking the allocation. Compile with LeakSanitizer, which is integrated into AddressSanitizer:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly run --target x86_64-unknown-linux-gnu
```

At program exit, LeakSanitizer reports:

```
ERROR: LeakSanitizer: detected memory leaks

Direct leak of 1048576 byte(s) in 1 object(s) allocated from:
    #0 malloc ...
    #1 alloc ...
    #2 test_memory_leak src/main.rs:2
    ...
```

LeakSanitizer identifies the allocation site and the number of leaked bytes. This is invaluable for diagnosing leaks in long-running services where small leaks accumulate over time and eventually exhaust memory. Unlike Valgrind's Memcheck, which performs shadow memory checks at every access and imposes 10x to 50x slowdown, AddressSanitizer and LeakSanitizer use compile-time instrumentation and red-zone padding, imposing only 2x to 3x slowdown, making them practical for continuous integration and even some production deployments.

Extend the exercise by testing with C++ and comparing sanitizer output. Create a file `racy.cpp`:

```cpp
#include <iostream>
#include <thread>
#include <vector>

int counter = 0;

void increment(int iterations) {
    for (int i = 0; i < iterations; ++i) {
        counter++;
    }
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(increment, 100000);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "Final counter: " << counter << std::endl;
    return 0;
}
```

Compile with ThreadSanitizer:

```bash
clang++ -fsanitize=thread -g -O1 racy.cpp -o racy -pthread
./racy
```

ThreadSanitizer reports a data race on the global `counter` variable, with stack traces identical in structure to the Rust report. Fix the race with `std::atomic`:

```cpp
#include <atomic>

std::atomic<int> counter{0};

void increment(int iterations) {
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
}
```

Recompile and run. No race is reported, and the final value is 400,000. The `fetch_add` operation is atomic, and even `memory_order_relaxed` suffices because we only require atomicity, not ordering with respect to other variables.

Test AddressSanitizer on a use-after-free in C++. Create `uaf.cpp`:

```cpp
#include <iostream>

int main() {
    int* ptr = new int[10];
    delete[] ptr;
    std::cout << ptr[0] << std::endl;
    return 0;
}
```

Compile with AddressSanitizer:

```bash
clang++ -fsanitize=address -g -O1 uaf.cpp -o uaf
./uaf
```

AddressSanitizer reports a heap-use-after-free with full stack traces. The diagnostic format is nearly identical to Rust's, demonstrating that the underlying LLVM sanitizer infrastructure is shared. Finally, test LeakSanitizer with a C++ leak. Create `leak.cpp`:

```cpp
#include <iostream>

int main() {
    int* leak = new int[1024 * 1024];
    std::cout << "Leaked memory\n";
    return 0;
}
```

Compile with AddressSanitizer, which includes LeakSanitizer by default:

```bash
clang++ -fsanitize=address -g -O1 leak.cpp -o leak
./leak
```

LeakSanitizer reports the leak at exit. Note that LeakSanitizer is disabled by default in some configurations; if no leak is reported, explicitly enable it with `ASAN_OPTIONS=detect_leaks=1 ./leak`.

This exercise establishes fluency with dynamic analysis tools that detect undefined behavior at runtime. Sanitizers impose modest overhead and integrate seamlessly into continuous integration pipelines, catching bugs before they reach production. In systems programming, where undefined behavior can corrupt critical state or create security vulnerabilities, sanitizers are non-negotiable. You have learned to compile with sanitizer flags, interpret diagnostic output, and correlate findings with source-level bugs. Extend this practice to all concurrent and memory-unsafe code you write. Every data race, use-after-free, and memory leak is a potential production incident. Sanitizers transform these silent corruptions into loud, actionable failures during development.


## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the commands, compiler flags, and diagnostic workflows practiced in the preceding exercises into a quick-reference guide for daily performance engineering work. Keep this checklist accessible when profiling, debugging, or optimizing production code.

**Compiler Introspection and Disassembly:**
Emit LLVM IR for a Rust crate: `cargo rustc --release -- --emit=llvm-ir`. The `.ll` file resides in `target/release/deps/`. Emit assembly: `cargo rustc --release -- --emit=asm`. Inspect disassembly of a single function: `cargo install cargo-show-asm`, then `cargo asm --release crate_name::function_name`. Compare optimization levels by setting `-C opt-level=1` or `-C opt-level=2` in `RUSTFLAGS` or via `cargo rustc -- -C opt-level=1`. Enable link-time optimization in `Cargo.toml` under `[profile.release]` with `lto = true` for whole-program optimization. For C++, emit LLVM IR with `clang++ -S -emit-llvm -O3 source.cpp -o output.ll` and assembly with `clang++ -S -O3 source.cpp -o output.s`.

**Performance Counter Profiling:**
Measure aggregate hardware counters with `perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-load-misses,branches,branch-misses ./binary`. Calculate instructions per cycle (IPC) by dividing instructions by cycles; high IPC (above 2) indicates efficient execution, while low IPC (below 1) suggests memory or branch stalls. Capture per-function cache miss attribution with `perf record -e cache-misses -g --call-graph dwarf ./binary`, then analyze with `perf report`. Annotate assembly with `perf annotate` after recording. Generate flamegraphs with `cargo flamegraph --bench benchmark_name -- --bench --profile-time=10`, producing an interactive SVG showing CPU time distribution across call stacks. Ensure `perf_event_paranoid` is set to 1 or lower: `cat /proc/sys/kernel/perf_event_paranoid`. Temporarily lower it with `echo 1 | sudo tee /proc/sys/kernel/perf_event_paranoid`. Disable CPU frequency scaling for reproducible measurements: `echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`.

**Sanitizer Compilation and Execution:**
Enable AddressSanitizer in Rust with `RUSTFLAGS="-Z sanitizer=address" cargo +nightly run --target x86_64-unknown-linux-gnu`. Enable ThreadSanitizer with `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --target x86_64-unknown-linux-gnu`. Note that sanitizers require nightly Rust and may need rebuild with `-Z build-std`. For C++, compile with `clang++ -fsanitize=address -g -O1 source.cpp -o binary` for AddressSanitizer, `-fsanitize=thread` for ThreadSanitizer, `-fsanitize=memory` for MemorySanitizer, and `-fsanitize=undefined` for UndefinedBehaviorSanitizer. Combine sanitizers with comma separation: `-fsanitize=address,undefined`. LeakSanitizer is integrated into AddressSanitizer but can be explicitly enabled via environment variable: `ASAN_OPTIONS=detect_leaks=1 ./binary`. Sanitizer output includes stack traces for allocation, deallocation, and access sites; use debug symbols (`-g`) for readable traces. Sanitizers impose 2x to 3x runtime overhead, making them suitable for development and CI but potentially prohibitive for production unless sampling or partial instrumentation is employed.

**Benchmarking and Microbenchmark Hygiene:**
Use Criterion for statistical benchmarking in Rust: add `criterion = "0.5"` to `[dev-dependencies]` and create a benchmark target with `harness = false`. Wrap measured code in `black_box` to prevent constant folding: `black_box(expensive_function())`. Run benchmarks with `cargo bench`. For C++, use Google Benchmark: `#include <benchmark/benchmark.h>` and wrap measured code in `benchmark::DoNotOptimize(value)` to prevent elimination. Ensure benchmarks run long enough to amortize setup overhead and capture variance. Report median, mean, and standard deviation. Disable CPU frequency scaling and close background processes to minimize measurement noise. Profile the benchmark binary itself with `perf` to attribute time to source lines: `perf record -g --call-graph dwarf target/release/deps/benchmark-*`, then analyze with `perf report`.

**Cache Optimization Workflow:**
Identify cache-bound code by comparing IPC (instructions per cycle) and cache miss rates. Low IPC combined with high cache misses indicates memory bottlenecks. Use `perf stat` with events `L1-dcache-load-misses`, `LLC-load-misses`, and `mem_load_retired.l3_miss` to isolate cache levels. Apply algorithmic transformations: loop tiling to fit working sets into L1, structure-of-arrays layout to improve vectorization, and prefetch instructions for known access patterns. Measure memory bandwidth saturation by monitoring `mem_load_retired.l3_miss` under load; when bandwidth saturates, further parallelism does not improve throughput. Profile with `perf c2c` to detect false sharing between threads: `perf c2c record ./binary`, then `perf c2c report` to identify cache lines contended by multiple cores.

**Concurrency Debugging and Verification:**
Always compile concurrent code with ThreadSanitizer during development. Data races are undefined behavior and may manifest as silent corruption, crashes, or security vulnerabilities. Use atomic operations (`std::sync::atomic` in Rust, `std::atomic` in C++) for lock-free algorithms, specifying appropriate memory orderings: `Relaxed` for independent operations, `Acquire/Release` for synchronization, `SeqCst` for total ordering. Verify lock-free algorithms with model checkers like Loom for Rust (`cargo install loom`) or CDSChecker for C++. Test under high contention by spawning many threads and verifying correctness invariants. Use stress testing with sanitizers enabled: run the program repeatedly under varied scheduling to expose rare races. For production, consider enabling AddressSanitizer in staging environments with sampling to detect memory corruption without full overhead.

**Common Performance Pitfalls and Diagnostics:**
Branch mispredictions: measure with `perf stat -e branches,branch-misses`. Mitigate by eliminating unpredictable branches (use branchless code with conditional moves) or by sorting data to improve predictor accuracy. TLB misses: measure with `perf stat -e dTLB-load-misses,iTLB-load-misses`. Mitigate by using huge pages (`madvise` with `MADV_HUGEPAGE` or `transparent_hugepage`) to reduce TLB pressure. False sharing: detect with `perf c2c` and mitigate by padding structures to cache line boundaries (64 bytes) or using thread-local accumulators. Contended locks: profile with `perf record -e sched:sched_switch` to identify threads blocked on mutexes, then refactor to reduce critical section size or switch to lock-free structures. Memory allocator overhead: profile with `perf record -e malloc` or use `jemalloc` or `mimalloc` as allocator replacements to reduce fragmentation and improve cache locality.

**Toolchain Installation Verification:**
Confirm Rust installation with `rustc --version` and `cargo --version`. Install nightly for sanitizers: `rustup install nightly`. Install Clang and LLVM: `clang++ --version` should report version 15 or later. Install `perf` on Linux: `perf --version`. On Debian-based systems: `apt install linux-tools-generic`. Install `valgrind`: `valgrind --version`. Install `cargo-flamegraph`: `cargo install flamegraph`. Install `cargo-show-asm`: `cargo install cargo-show-asm`. Verify `perf` permissions: `cat /proc/sys/kernel/perf_event_paranoid` should be 1 or lower. Verify sanitizer support by compiling and running the examples in Exercise 3.

This cheat sheet distills the essential commands and workflows into a format suitable for rapid consultation during performance work. Internalize these patterns through repeated practice. Performance engineering is an empirical discipline: you measure, hypothesize, optimize, and measure again. The toolchain provides the instrumentation to close the loop. Guesswork and intuition fail at scale; hardware counters and sanitizers provide ground truth. Return to these exercises whenever you encounter unfamiliar performance characteristics or concurrency bugs. The patterns you have practiced here apply universally, from embedded firmware to distributed systems. Fluency with profilers, sanitizers, and disassembly distinguishes engineers who deliver predictable, fast, correct systems from those who ship hope and pray.
