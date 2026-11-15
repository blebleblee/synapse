# Operational Verification Labs: Programming

## Objective & Toolchain Setup

Modern software engineering demands operational fluency across the compilation pipeline, runtime diagnostics, and performance characterization. These laboratories ground the practice of verification in the concrete mechanics of language toolchains, compiler intermediate representations, sanitizer instrumentation, and hardware performance counters. The goal is not to memorize abstract theory but to build muscle memory for debugging, profiling, and hardening production systems through iterative measurement and refinement.

The verification workflow begins with compiler introspection. Understanding how source code transforms into Abstract Syntax Trees, lowers into LLVM Intermediate Representation, and finally emits machine code provides the foundation for diagnosing miscompilation, optimization failures, and undefined behavior. Disassembly analysis reveals instruction selection, register allocation, and branch prediction patterns that directly govern cache efficiency and instruction-level parallelism.

Performance profiling moves beyond wall-clock timing into the domain of hardware counters. Cache miss rates, translation lookaside buffer stalls, branch mispredictions, and instruction retirement metrics expose bottlenecks invisible to high-level profilers. Tools like `perf` and `cargo-flamegraph` translate raw counter samples into actionable flame graphs and annotated source listings, enabling precise optimization targeting.

Concurrency correctness requires dynamic analysis under stress. ThreadSanitizer instruments memory accesses to detect data races through happens-before relationship violations. LeakSanitizer tracks allocation lifetimes to surface memory leaks that escape static analysis. AddressSanitizer guards heap allocations with red zones and shadow memory to catch buffer overflows, use-after-free, and double-free errors. These sanitizers impose runtime overhead but provide deterministic failure reproduction that transforms intermittent bugs into debuggable test cases.

The laboratory environment assumes a UNIX-like system with a modern toolchain. Install Rust via `rustup`, which provides `cargo`, `rustc`, and `rustfmt`. Install LLVM for access to `llc`, `opt`, and `llvm-mca`. Install GCC or Clang for C++ compilation with sanitizer support. Install GDB or LLDB for interactive debugging, Valgrind for heap profiling, and `perf` for hardware counter sampling. On Linux, ensure the kernel parameter `kernel.perf_event_paranoid` is set to `1` or lower to allow unprivileged performance monitoring. On macOS, install Xcode Command Line Tools and use Instruments for profiling. Verify the installation by running `cargo --version`, `clang --version`, `gdb --version`, and `perf --version`.

Configure your shell environment to enable core dumps for post-mortem debugging. On Linux, execute `ulimit -c unlimited` and set `/proc/sys/kernel/core_pattern` to `core.%e.%p.%t` to generate core files with process name, PID, and timestamp. On macOS, core dumps are written to `/cores/` by default. Enable debug symbols in release builds by adding `debug = true` to the `[profile.release]` section of `Cargo.toml`, preserving optimization while retaining source-level debugging information.

## Exercise 1: AST, IR & Disassembly Analysis

The compilation pipeline transforms high-level source code through multiple intermediate representations before emitting machine code. Analyzing these stages reveals optimization opportunities, undefined behavior, and instruction-level performance characteristics. This exercise constructs a small Rust program with deliberate performance issues, then traces its transformation from syntax trees through LLVM IR to assembly, identifying specific compiler optimizations and missed opportunities.

Begin by creating a new Rust binary project and implementing a function that computes the sum of squared differences between two vectors. This pattern appears frequently in numerical computing, machine learning distance metrics, and signal processing. The initial implementation uses idiomatic iterator chains but contains a subtle inefficiency.

```rust
// src/main.rs

fn sum_squared_diff_naive(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x - y).powi(2))
        .sum()
}

fn sum_squared_diff_unchecked(a: &[f64], b: &[f64]) -> f64 {
    assert_eq!(a.len(), b.len());
    let mut sum = 0.0;
    for i in 0..a.len() {
        let diff = unsafe { a.get_unchecked(i) - b.get_unchecked(i) };
        sum += diff * diff;
    }
    sum
}

fn main() {
    let a: Vec<f64> = (0..1000).map(|x| x as f64).collect();
    let b: Vec<f64> = (0..1000).map(|x| (x as f64) + 0.5).collect();

    let result_naive = sum_squared_diff_naive(&a, &b);
    let result_unchecked = sum_squared_diff_unchecked(&a, &b);

    println!("Naive: {}", result_naive);
    println!("Unchecked: {}", result_unchecked);
}
```

Compile the program with debug symbols and emit LLVM IR for inspection. The `--emit=llvm-ir` flag instructs `rustc` to output the intermediate representation before machine code generation. Execute `cargo rustc --release -- --emit=llvm-ir` and locate the generated `.ll` file in `target/release/deps/`. Open the file and search for the `sum_squared_diff_naive` function. The IR reveals iterator adaptors, bounds checking, and potential auto-vectorization barriers.

Examine the LLVM IR structure. Each function begins with a signature specifying parameter types, calling convention, and attributes like `nounwind` or `readonly`. Basic blocks represent control flow nodes, each terminated by a branch, return, or unreachable instruction. SSA (Static Single Assignment) form ensures every virtual register is assigned exactly once, simplifying dataflow analysis. Look for `call` instructions invoking iterator methods, `icmp` instructions performing bounds checks, and `br` instructions implementing conditional jumps.

The naive implementation likely contains redundant bounds checks. Each call to `zip` and `map` generates iterator state machines with length validation. While the optimizer can eliminate some checks through inlining and range analysis, complex iterator chains may defeat the analysis. The unchecked variant explicitly bypasses bounds checks using `get_unchecked`, trading safety for performance in contexts where length equality is guaranteed by assertion.

Now emit assembly to observe instruction selection and register allocation. Execute `cargo rustc --release -- --emit=asm` and open the generated `.s` file. Search for the `sum_squared_diff_naive` symbol. Modern x86-64 assembly uses AT&T syntax by default, where source operands precede destination operands and registers are prefixed with `%`. Look for `movsd` instructions loading doubles into SSE registers, `subsd` performing scalar subtraction, `mulsd` computing squares, and `addsd` accumulating the sum.

Check for SIMD vectorization by searching for packed floating-point instructions. If the loop vectorizes, you will observe `movupd` or `movapd` loading two doubles into a single 128-bit XMM register, `subpd` performing parallel subtraction, `mulpd` computing parallel squares, and `addpd` accumulating vector sums. The loop epilogue handles remainder elements that do not fit a complete SIMD vector. If vectorization is absent, the loop processes one element per iteration, leaving substantial performance on the table.

Quantify the vectorization decision using LLVM's machine code analyzer. Extract the assembly for the unchecked function and save it to a file. Execute `llvm-mca -mcpu=native < function.s` to simulate instruction scheduling, dispatch, and throughput on your CPU microarchitecture. The output reports iterations per cycle, bottleneck resources (ALU, load/store units, execution ports), and critical path length. Compare the naive and unchecked variants to measure the performance impact of bounds checking and iterator abstraction overhead.

Inspect the Abstract Syntax Tree using `rustc`'s internal debugging flags. Execute `cargo rustc -- -Zunpretty=hir` to print the High-Level Intermediate Representation, which desugars macros, expands iterator methods, and inserts implicit type coercions. The HIR reveals the actual function calls hidden behind iterator syntax. Search for `Iterator::zip`, `Iterator::map`, and `Iterator::sum` to understand the lowering process. This representation bridges the gap between surface syntax and the control flow graph used for optimization.

To observe optimization passes in action, enable verbose optimization remarks. Execute `cargo rustc --release -- -C llvm-args=-pass-remarks=inline,loop-vectorize`. The compiler will emit diagnostics explaining inlining decisions, vectorization successes, and optimization failures. If the vectorizer declines to optimize a loop, the remark will cite reasons such as conditional stores, function calls with side effects, or unanalyzable loop bounds. These remarks are invaluable for understanding why an expected optimization did not occur.

Finally, use GDB to correlate disassembly with source code. Compile with `cargo build --release` ensuring debug symbols are enabled, then launch `gdb target/release/your_binary`. Set a breakpoint on `sum_squared_diff_naive` with `break sum_squared_diff_naive`, run the program, and execute `disassemble` when the breakpoint hits. GDB interleaves assembly with source lines, showing exactly which instructions implement each Rust statement. Use `info registers` to inspect register contents and `x/8gx $rsp` to examine stack memory. Step through the loop with `stepi` to observe register updates and memory accesses at instruction granularity.

## Exercise 2: Cache Miss & Throughput Profiling

Memory access patterns dominate modern application performance. CPU core speeds have outpaced DRAM latency by two orders of magnitude, making cache efficiency the primary determinant of throughput. This exercise profiles a matrix transposition workload, measures cache miss rates using hardware performance counters, and optimizes memory layout to maximize spatial locality and minimize translation lookaside buffer pressure.

Create a new Rust project implementing both naive and blocked matrix transposition algorithms. The naive algorithm accesses the destination matrix in column-major order, causing cache line conflicts and thrashing. The blocked algorithm tiles the matrix into cache-friendly sub-blocks, preserving temporal locality.

```rust
// src/main.rs

use std::time::Instant;

const SIZE: usize = 4096;
const BLOCK: usize = 64;

fn transpose_naive(src: &[f64], dst: &mut [f64], n: usize) {
    for i in 0..n {
        for j in 0..n {
            dst[j * n + i] = src[i * n + j];
        }
    }
}

fn transpose_blocked(src: &[f64], dst: &mut [f64], n: usize, block_size: usize) {
    for i in (0..n).step_by(block_size) {
        for j in (0..n).step_by(block_size) {
            let i_end = (i + block_size).min(n);
            let j_end = (j + block_size).min(n);
            for ii in i..i_end {
                for jj in j..j_end {
                    dst[jj * n + ii] = src[ii * n + jj];
                }
            }
        }
    }
}

fn main() {
    let mut src = vec![0.0f64; SIZE * SIZE];
    let mut dst = vec![0.0f64; SIZE * SIZE];

    for i in 0..SIZE {
        for j in 0..SIZE {
            src[i * SIZE + j] = (i * SIZE + j) as f64;
        }
    }

    let start = Instant::now();
    transpose_naive(&src, &mut dst, SIZE);
    let elapsed_naive = start.elapsed();

    dst.fill(0.0);

    let start = Instant::now();
    transpose_blocked(&src, &mut dst, SIZE, BLOCK);
    let elapsed_blocked = start.elapsed();

    println!("Naive transpose: {:?}", elapsed_naive);
    println!("Blocked transpose: {:?}", elapsed_blocked);
    println!("Speedup: {:.2}x", elapsed_naive.as_secs_f64() / elapsed_blocked.as_secs_f64());

    let sum: f64 = dst.iter().sum();
    println!("Checksum: {}", sum);
}
```

Compile with full optimization and native CPU tuning. Execute `cargo build --release` with `RUSTFLAGS="-C target-cpu=native"` to enable architecture-specific SIMD instructions and cache line size awareness. The binary is now tuned for your processor's microarchitecture, using AVX2 or AVX-512 instructions if available.

Profile the application using Linux `perf` to capture hardware performance counter events. Begin with a high-level overview using `perf stat`. Execute `perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses ./target/release/matrix_transpose`. The output reports retired instructions, elapsed cycles, instructions per cycle (IPC), and cache miss rates. The naive implementation will exhibit a high L1 data cache miss rate, often exceeding ten percent, while the blocked version achieves miss rates below one percent.

Drill into cache hierarchy bottlenecks using specific counter events. Execute `perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses,dTLB-loads,dTLB-load-misses ./target/release/matrix_transpose`. The last-level cache (LLC) miss rate indicates when the working set exceeds on-chip cache capacity, forcing accesses to DRAM. Data translation lookaside buffer (dTLB) misses occur when the page table walk overhead dominates memory latency, common when striding across large arrays with poor spatial locality.

Generate a flame graph to visualize where CPU time is spent. Install `cargo-flamegraph` using `cargo install flamegraph`, then profile the application with `cargo flamegraph --release`. The tool invokes `perf record` with CPU sampling, captures stack traces, and generates an interactive SVG. Open the flame graph in a browser. Wide horizontal bars represent functions consuming significant CPU time. The naive transpose will dominate the graph, with sample counts concentrated in the inner loop. The blocked version distributes samples more evenly across block iterations, indicating better pipeline utilization.

Annotate the disassembly with cache miss samples to identify hot memory accesses. Execute `perf record -e cache-misses ./target/release/matrix_transpose`, then `perf report --stdio` to generate a text report. Use `perf annotate transpose_naive` to display the function's assembly with per-instruction miss counts. The store instruction writing to `dst[j * n + i]` will accumulate the majority of misses, confirming that column-major writes thrash the cache. Each write touches a different cache line before the line is reused, causing eviction before temporal locality can be exploited.

Experiment with block size tuning. Modify the `BLOCK` constant to powers of two from sixteen to two hundred fifty-six, recompile, and measure performance. The optimal block size balances cache capacity and loop overhead. Blocks that are too small incur excessive loop iteration overhead. Blocks that exceed L1 cache capacity (typically thirty-two kilobytes for data) spill to L2, reducing throughput. Profile each configuration with `perf stat` and plot cache miss rates against block size. The optimal point typically aligns with the square root of L1 cache capacity divided by element size, ensuring the working set fits comfortably in L1.

Analyze memory bandwidth saturation using `perf` memory event sampling. Execute `perf mem record ./target/release/matrix_transpose`, then `perf mem report` to generate a memory access profile. The report categorizes accesses by latency: L1 hits (sub-nanosecond), L2 hits (few nanoseconds), L3 hits (tens of nanoseconds), and DRAM accesses (hundreds of nanoseconds). The naive implementation will show a high proportion of L3 and DRAM accesses, while the blocked version concentrates accesses in L1 and L2.

Finally, simulate cache behavior using Valgrind's Cachegrind tool. Execute `valgrind --tool=cachegrind --cache-sim=yes ./target/release/matrix_transpose`. Cachegrind models L1 instruction and data caches, plus a unified last-level cache, reporting instruction fetch misses, data read misses, and data write misses. The output file `cachegrind.out.<pid>` can be visualized with `cg_annotate` to show per-line cache miss counts. This deterministic simulation complements hardware counters by providing reproducible measurements independent of system load and background processes.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs manifest non-deterministically, often evading conventional testing under light load. ThreadSanitizer and LeakSanitizer instrument memory accesses and allocation lifetimes to detect races, use-after-free, and resource leaks through dynamic analysis. This exercise constructs a multi-threaded reference counting system with deliberate data races and memory leaks, then hardens it using sanitizers and stress testing under high contention.

Create a Rust project implementing a thread-safe reference-counted cache. The initial implementation uses interior mutability with `Mutex` but contains subtle race conditions in eviction logic. A second variant leaks memory by failing to drop evicted entries. A third variant uses `Arc` and `RwLock` correctly, serving as the reference implementation.

```rust
// src/main.rs

use std::collections::HashMap;
use std::sync::{Arc, Mutex, RwLock};
use std::thread;
use std::time::Duration;

#[derive(Clone)]
struct CacheBuggy {
    map: Arc<Mutex<HashMap<u64, String>>>,
}

impl CacheBuggy {
    fn new() -> Self {
        CacheBuggy {
            map: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    fn insert(&self, key: u64, value: String) {
        let mut map = self.map.lock().unwrap();
        map.insert(key, value);
    }

    fn get(&self, key: u64) -> Option<String> {
        let map = self.map.lock().unwrap();
        map.get(&key).cloned()
    }

    fn evict_if_large(&self) {
        let len = {
            let map = self.map.lock().unwrap();
            map.len()
        };
        if len > 100 {
            let mut map = self.map.lock().unwrap();
            if map.len() > 100 {
                let keys: Vec<u64> = map.keys().take(50).copied().collect();
                for k in keys {
                    map.remove(&k);
                }
            }
        }
    }
}

#[derive(Clone)]
struct CacheLeaky {
    map: Arc<Mutex<HashMap<u64, Box<String>>>>,
}

impl CacheLeaky {
    fn new() -> Self {
        CacheLeaky {
            map: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    fn insert(&self, key: u64, value: String) {
        let mut map = self.map.lock().unwrap();
        let leaked = Box::new(value);
        map.insert(key, leaked);
    }

    fn get(&self, key: u64) -> Option<String> {
        let map = self.map.lock().unwrap();
        map.get(&key).map(|b| (**b).clone())
    }

    fn evict_if_large(&self) {
        let mut map = self.map.lock().unwrap();
        if map.len() > 100 {
            let keys: Vec<u64> = map.keys().take(50).copied().collect();
            for k in keys {
                let removed = map.remove(&k);
                std::mem::forget(removed);
            }
        }
    }
}

#[derive(Clone)]
struct CacheCorrect {
    map: Arc<RwLock<HashMap<u64, String>>>,
}

impl CacheCorrect {
    fn new() -> Self {
        CacheCorrect {
            map: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    fn insert(&self, key: u64, value: String) {
        let mut map = self.map.write().unwrap();
        map.insert(key, value);
        if map.len() > 100 {
            let keys: Vec<u64> = map.keys().take(50).copied().collect();
            for k in keys {
                map.remove(&k);
            }
        }
    }

    fn get(&self, key: u64) -> Option<String> {
        let map = self.map.read().unwrap();
        map.get(&key).cloned()
    }
}

fn stress_test_buggy() {
    let cache = CacheBuggy::new();
    let mut handles = vec![];

    for thread_id in 0..8 {
        let cache_clone = cache.clone();
        let handle = thread::spawn(move || {
            for i in 0..1000 {
                let key = (thread_id * 1000 + i) as u64;
                cache_clone.insert(key, format!("value_{}", key));
                cache_clone.evict_if_large();
                if i % 10 == 0 {
                    cache_clone.get(key);
                }
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Buggy cache test completed");
}

fn stress_test_leaky() {
    let cache = CacheLeaky::new();
    let mut handles = vec![];

    for thread_id in 0..8 {
        let cache_clone = cache.clone();
        let handle = thread::spawn(move || {
            for i in 0..1000 {
                let key = (thread_id * 1000 + i) as u64;
                cache_clone.insert(key, format!("value_{}", key));
                cache_clone.evict_if_large();
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Leaky cache test completed");
}

fn stress_test_correct() {
    let cache = CacheCorrect::new();
    let mut handles = vec![];

    for thread_id in 0..8 {
        let cache_clone = cache.clone();
        let handle = thread::spawn(move || {
            for i in 0..1000 {
                let key = (thread_id * 1000 + i) as u64;
                cache_clone.insert(key, format!("value_{}", key));
                if i % 10 == 0 {
                    cache_clone.get(key);
                }
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Correct cache test completed");
}

fn main() {
    println!("=== Testing Buggy Implementation ===");
    stress_test_buggy();

    println!("\n=== Testing Leaky Implementation ===");
    stress_test_leaky();

    println!("\n=== Testing Correct Implementation ===");
    stress_test_correct();
}
```

Compile the program with ThreadSanitizer instrumentation. Rust enables sanitizers through compiler flags. Execute `RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu` on Linux. ThreadSanitizer requires a nightly compiler, so ensure `rustup default nightly` is active. Note that ThreadSanitizer is not supported on all platforms; macOS requires Xcode's TSan runtime, and Windows support is limited.

Run the instrumented binary and observe race reports. Execute `./target/x86_64-unknown-linux-gnu/debug/your_binary`. ThreadSanitizer monitors memory accesses, tracking read and write operations along with synchronization primitives like mutexes and atomics. When two threads access the same memory location without synchronization and at least one access is a write, TSan reports a data race with stack traces for both conflicting accesses.

The buggy implementation contains a time-of-check-to-time-of-use race in `evict_if_large`. The function first reads the map length without holding the lock, then reacquires the lock to perform eviction. Between the check and the eviction, another thread may insert or remove entries, invalidating the length check. ThreadSanitizer will report a race between the unlocked length read and concurrent insertions. The report includes source file locations, thread IDs, and call stacks, pinpointing the exact conflicting operations.

Analyze the race report structure. Each TSan warning begins with a header indicating the race type and memory address. The first section shows the stack trace for the earlier access, including function names and source locations. The second section shows the later conflicting access. A third section displays the allocation stack if the memory was heap-allocated. A fourth section may show synchronization points, such as mutex acquisitions, to clarify the happens-before relationships. The absence of synchronization between accesses confirms the race.

Fix the race by eliminating the time-of-check-to-time-of-use pattern. The correct implementation performs the length check and eviction within a single critical section, holding the lock throughout. Recompile with ThreadSanitizer and verify the race is eliminated. TSan output should now be silent for the correct variant. This confirms that all memory accesses are properly synchronized according to the C++11 memory model, which Rust inherits.

Enable LeakSanitizer to detect memory leaks. LeakSanitizer piggybacks on AddressSanitizer infrastructure but focuses on heap allocation tracking. Compile with `RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu`. Run the binary and observe leak reports. LeakSanitizer scans reachable memory at program termination, identifying allocations not reachable from global variables, stack variables, or CPU registers. These orphaned allocations represent leaks.

The leaky implementation calls `std::mem::forget` on removed cache entries, preventing `Drop` execution. The heap memory remains allocated but unreachable, constituting a classic leak. LeakSanitizer reports the allocation stack for each leaked block, showing where the memory was allocated. The report aggregates leaks by allocation site, displaying total leaked bytes and block count. In this example, the leaks originate from `Box::new` calls in the `insert` method, with memory size proportional to string length.

Quantify leak severity by inspecting the report summary. LeakSanitizer categorizes leaks as direct, indirect, or reachable. Direct leaks have no references from other allocated memory. Indirect leaks are referenced by direct leaks but not by program roots. Reachable leaks are accessible from roots but may not be freed. The buggy implementation will show direct leaks totaling several megabytes after processing eight thousand insertions with fifty evictions per batch.

Stress test the fixed implementation under high contention to verify correctness. Increase thread count to match CPU core count with `thread::available_parallelism()`. Reduce sleep durations and increase iteration counts to maximize contention on the shared lock. Execute the program under ThreadSanitizer repeatedly, using `for i in {1..100}; do ./target/debug/your_binary; done` to run one hundred trials. Data races manifest non-deterministically due to scheduling variance; repeated execution increases detection probability.

Combine sanitizers with fuzz testing for exhaustive concurrency coverage. Install `cargo-fuzz` using `cargo install cargo-fuzz`, then create a fuzz target invoking cache operations with random keys and values. The fuzzer explores input space systematically, triggering edge cases and race windows. Run the fuzzer under AddressSanitizer and ThreadSanitizer simultaneously to catch both memory corruption and concurrency bugs. Fuzz testing discovers bugs that stress tests miss by exploring unusual operation sequences and timing interleavings.

Finally, measure sanitizer overhead to understand deployment constraints. Compile the same program with and without sanitizers, then benchmark throughput. AddressSanitizer typically imposes two-fold overhead in CPU time and three-fold overhead in memory due to shadow memory bookkeeping. ThreadSanitizer overhead reaches ten-fold due to comprehensive memory access tracking. LeakSanitizer adds minimal overhead during execution but requires a full heap scan at termination. These costs limit sanitizer use to testing and continuous integration environments, not production deployments.

## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the essential commands, environment configurations, and diagnostic workflows for operational verification across compilation analysis, performance profiling, and dynamic sanitization.

**Toolchain Installation and Configuration**

Install Rust toolchain including stable and nightly compilers with `rustup install stable nightly`, then set the default with `rustup default stable`. Install LLVM tools for intermediate representation analysis with your package manager: `apt install llvm` on Debian-based systems or `brew install llvm` on macOS. Install Clang for C++ compilation with sanitizer support using `apt install clang` or `brew install llvm`. Install GDB or LLDB for debugging with `apt install gdb` or ensure Xcode Command Line Tools are installed on macOS. Install Valgrind for memory profiling with `apt install valgrind` on Linux; macOS support is experimental. Install Linux `perf` tools with `apt install linux-tools-common linux-tools-generic` on Ubuntu or equivalent packages for your distribution.

Configure core dumps for post-mortem debugging by setting `ulimit -c unlimited` in your shell profile. On Linux, configure core file naming with `echo 'core.%e.%p.%t' | sudo tee /proc/sys/kernel/core_pattern`. Enable unprivileged performance monitoring with `echo 1 | sudo tee /proc/sys/kernel/perf_event_paranoid`. Add debug symbols to release builds by editing `Cargo.toml` with the section `[profile.release]` followed by `debug = true` and `strip = false`.

Enable architecture-specific optimizations by setting `RUSTFLAGS="-C target-cpu=native"` in your environment or `.cargo/config.toml` with the section `[build]` followed by `rustflags = ["-C", "target-cpu=native"]`. For link-time optimization across compilation units, add `lto = true` under `[profile.release]`. For single-codegen-unit builds that maximize optimization at the cost of compile time, add `codegen-units = 1`.

**Compilation Pipeline Introspection**

Emit LLVM intermediate representation with `cargo rustc --release -- --emit=llvm-ir`, then locate the `.ll` file in `target/release/deps/`. Emit assembly with `cargo rustc --release -- --emit=asm`, then locate the `.s` file. Emit both simultaneously with `cargo rustc --release -- --emit=llvm-ir,asm`. Inspect the High-Level Intermediate Representation with `cargo rustc -- -Zunpretty=hir` to observe desugared syntax and type coercions.

Enable optimization remarks to understand compiler decisions with `cargo rustc --release -- -C llvm-args=-pass-remarks=inline,loop-vectorize`. For missed optimizations, use `-pass-remarks-missed=loop-vectorize`. For analysis notes, use `-pass-remarks-analysis=loop-vectorize`. Direct remarks to a YAML file with `-pass-remarks-output=remarks.yaml` for machine parsing.

Analyze instruction scheduling and throughput with LLVM machine code analyzer by extracting assembly for a function and piping to `llvm-mca -mcpu=native`. Specify microarchitecture explicitly with `-mcpu=skylake` or equivalent. Inspect bottleneck resources and critical path length in the output report.

**Performance Profiling Workflow**

Profile high-level metrics with `perf stat -e cycles,instructions,cache-references,cache-misses ./binary`. Add memory hierarchy events with `-e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses`. Add TLB events with `-e dTLB-loads,dTLB-load-misses`. Add branch prediction events with `-e branches,branch-misses`. List all available events with `perf list`.

Capture CPU samples for flame graph generation with `perf record -F 99 -g ./binary`, then generate the report with `perf report`. Annotate disassembly with sample counts using `perf annotate function_name`. Use `cargo-flamegraph` for integrated profiling with `cargo flamegraph --release`, which automatically invokes `perf record`, captures stack traces, and generates an SVG flame graph.

Profile memory access latency with `perf mem record ./binary`, then generate the report with `perf mem report`. The report categorizes accesses by cache level and latency bucket. Use Valgrind Cachegrind for deterministic cache simulation with `valgrind --tool=cachegrind --cache-sim=yes ./binary`, then analyze with `cg_annotate cachegrind.out.<pid>`.

Benchmark with precision using `cargo bench` for criterion-based micro-benchmarks. For custom timing, use `std::time::Instant` with sufficient iteration count to amortize measurement overhead. Warm up the benchmark by running the workload once before timing to populate instruction caches and branch predictors.

**Sanitizer Diagnostic Commands**

Enable ThreadSanitizer with `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build --target x86_64-unknown-linux-gnu`. Run the instrumented binary and observe race reports in standard error. ThreadSanitizer flags include `TSAN_OPTIONS="halt_on_error=0"` to continue after the first race and `TSAN_OPTIONS="history_size=7"` to adjust memory tracking depth.

Enable AddressSanitizer with `RUSTFLAGS="-Z sanitizer=address" cargo +nightly build --target x86_64-unknown-linux-gnu`. Run the binary to detect buffer overflows, use-after-free, and double-free errors. AddressSanitizer flags include `ASAN_OPTIONS="detect_leaks=1"` to enable LeakSanitizer and `ASAN_OPTIONS="halt_on_error=0"` to report multiple errors per run.

Enable MemorySanitizer for uninitialized memory detection with `RUSTFLAGS="-Z sanitizer=memory" cargo +nightly build --target x86_64-unknown-linux-gnu`. MemorySanitizer requires recompiling the entire dependency tree with instrumentation, limiting its practicality for large projects.

Enable LeakSanitizer standalone with `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly build` for lower overhead than full AddressSanitizer. Leak reports appear at program termination with allocation stacks for orphaned blocks. Suppress known leaks by creating a suppression file and exporting `LSAN_OPTIONS="suppressions=lsan.supp"`.

Combine sanitizers in continuous integration by running test suites under each sanitizer separately. Use `cargo test` with sanitizer flags to instrument test binaries. Increase timeout limits for sanitized tests due to instrumentation overhead. Fail the build on any sanitizer warnings to enforce zero-tolerance for memory errors and data races.

**Interactive Debugging Session Workflow**

Launch GDB with `gdb ./target/release/binary`, set breakpoints with `break function_name` or `break file.rs:line`, then run with `run`. Examine the call stack with `backtrace`, inspect variables with `print variable` or `info locals`, and inspect registers with `info registers`. Display memory with `x/32gx $rsp` to show thirty-two eight-byte words starting at the stack pointer. Step by instruction with `stepi`, by line with `step` or `next`.

Disassemble the current function with `disassemble` or a specific function with `disassemble function_name`. Set assembly flavor to Intel syntax with `set disassembly-flavor intel`. Display mixed source and assembly with `disassemble /m`. Enable TUI mode with `tui enable` for split-screen source and assembly views.

Attach GDB to a running process with `gdb -p <pid>`, useful for diagnosing hung or misbehaving applications. Generate core dumps with `kill -ABRT <pid>`, then analyze with `gdb ./binary core.file`. Extract variable values and backtraces from core dumps for post-mortem analysis without access to the live process.

Use conditional breakpoints to reduce noise with `break file.rs:line if variable == value`. Use watchpoints to pause execution when memory changes with `watch *0xaddress`. Use catchpoints to break on system events with `catch syscall` or `catch throw`.

Configure Rust-specific pretty printers for GDB by installing `rust-gdb`, a wrapper that loads visualizers for standard library types. Inspect `Vec`, `String`, `HashMap`, and other collections with human-readable output instead of raw pointer and capacity fields.

**Valgrind Memory Analysis**

Run Memcheck for heap error detection with `valgrind --leak-check=full --show-leak-kinds=all ./binary`. Memcheck reports invalid reads and writes, use-after-free, double-free, and memory leaks with allocation stacks. Increase precision with `--track-origins=yes` to trace uninitialized values to their allocation site, at the cost of four-fold overhead.

Run Cachegrind for cache profiling with `valgrind --tool=cachegrind --cache-sim=yes ./binary`, then visualize with `cg_annotate cachegrind.out.<pid>`. The annotated output shows per-line instruction fetch, data read, and data write miss counts. Compare cache behavior across implementations by generating reports for each variant and diffing the results with `cg_diff`.

Run Callgrind for call graph profiling with `valgrind --tool=callgrind ./binary`, then visualize with `kcachegrind callgrind.out.<pid>`. Callgrind traces function call relationships and instruction counts, producing detailed call graphs with cycle attribution. This tool is invaluable for understanding hotspots in large codebases with complex call chains.

Run Helgrind for thread error detection with `valgrind --tool=helgrind ./binary`. Helgrind detects data races, lock order violations, and misuse of POSIX threading primitives. While less precise than ThreadSanitizer, Helgrind runs on platforms without TSan support and provides complementary diagnostics.

Suppress false positives by creating a suppression file with `valgrind --gen-suppressions=all ./binary`, capturing suppression rules for known benign warnings. Pass suppressions with `--suppressions=file.supp` to clean up output for genuine errors.

**Continuous Integration Verification Pipeline**

Integrate sanitizer checks into CI by running test suites under each sanitizer. Create separate jobs for AddressSanitizer, ThreadSanitizer, and LeakSanitizer to parallelize execution and isolate failures. Use nightly Rust toolchain for sanitizer support and ensure target triples match the CI environment architecture.

Run static analysis with Clippy using `cargo clippy -- -D warnings` to treat warnings as errors. Enable additional lint groups with `-W clippy::all -W clippy::pedantic -W clippy::cargo`. Suppress false positives with `#[allow(clippy::lint_name)]` annotations sparingly, documenting rationale in comments.

Run formatting checks with `cargo fmt --check` to enforce consistent style. Run security audits with `cargo audit` to detect dependencies with known vulnerabilities, integrating with the RustSec advisory database. Run dependency license checks to ensure compliance with project policies.

Enable code coverage with `cargo-llvm-cov` by installing with `cargo install cargo-llvm-cov`, then running `cargo llvm-cov --html` to generate an HTML report. Set coverage thresholds in CI to fail builds when coverage drops below target percentages. Exclude generated code and test utilities from coverage calculation using `#[cfg(not(tarpaulin_include))]` attributes.

Configure matrix builds testing multiple Rust versions, operating systems, and architectures to catch platform-specific bugs. Test against stable, beta, and nightly channels to detect regressions before they reach stable. Use `cargo check --target <triple>` for cross-compilation smoke tests without full builds.

Archive build artifacts including binaries, test reports, sanitizer logs, and performance profiles for post-mortem analysis. Integrate with alerting systems to notify developers of CI failures immediately. Maintain a separate performance tracking pipeline running benchmarks on dedicated hardware, storing results in a time-series database for regression detection across commits.
