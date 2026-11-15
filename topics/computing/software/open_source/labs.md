# Operational Verification Labs: Open Source

## Objective & Toolchain Setup

Modern open source development demands rigorous verification across compilation pipelines, runtime behavior, and concurrency correctness. This laboratory guide trains software engineers to operate the full diagnostic stack: compiler intermediate representations, memory sanitizers, cache profilers, and race detectors. The exercises ground abstract source code in concrete machine execution—revealing how high-level constructs degrade into assembly, how memory access patterns trigger hardware penalties, and how subtle concurrency bugs manifest as data races or memory leaks.

The verification workflow begins at the compiler frontend, where abstract syntax trees (ASTs) and LLVM intermediate representation (IR) expose optimization decisions and inlining boundaries. From there, runtime instrumentation through AddressSanitizer and ThreadSanitizer intercepts memory corruption and data races at the point of failure, while Valgrind provides heap profiling and leak detection with full stack traces. Performance profiling through `perf` and `cargo-flamegraph` quantifies cache miss rates, branch mispredictions, and CPU cycle distributions across hot paths. Each exercise operates on real-world code: multithreaded data structures, network parsers, and performance-critical kernels where verification failures carry production consequences.

The toolchain setup establishes a Linux-based development environment with Rust, C++, and Go compilation stacks. Install Rust through `rustup`, which provides `cargo`, `rustc`, and the standard library source for line-level debugging. For C++ verification, install Clang with LLVM development headers to access sanitizer runtimes and compiler-rt libraries. GDB and LLDB serve as primary debuggers, with LLDB offering superior Rust integration through `rust-lldb` wrappers that decode standard library types. Valgrind requires kernel headers and debug symbols for libc to produce accurate stack traces. The `perf` subsystem, part of the Linux kernel tree, demands root privileges or relaxed `perf_event_paranoid` settings to access hardware performance counters. Finally, `cargo-flamegraph` wraps `perf record` output into interactive flame graphs for hotspot visualization.

Begin by verifying the toolchain installation. Execute `rustc --version` to confirm Rust 1.70 or later, which includes stabilized inline assembly and improved MIR (mid-level IR) diagnostics. Run `clang --version` and verify LLVM 15 or later for robust sanitizer coverage. Check GDB with `gdb --version` and ensure Python scripting support, required for Rust pretty-printers. Install Valgrind through the distribution package manager and verify with `valgrind --version`; version 3.20 or later provides accurate Rust stack unwinding. For performance profiling, install `perf` through `linux-tools-generic` or the equivalent kernel tools package, then test access with `perf stat echo "test"`—if permission is denied, either run as root or set `sudo sysctl kernel.perf_event_paranoid=1` to allow non-root access. Install `cargo-flamegraph` through `cargo install flamegraph`, which bundles the Perl script for SVG generation.

Configure the Rust toolchain for debug builds with full symbol information. Create a `.cargo/config.toml` in your project root with the following profile overrides: `[profile.dev]` should set `opt-level = 0` (disable optimizations), `debug = true` (embed DWARF debug info), and `incremental = true` (speed up rebuilds). For release profiling, define `[profile.release]` with `opt-level = 3`, `debug = true` (critical for `perf` symbol resolution), `lto = "thin"` (link-time optimization without excessive compile time), and `codegen-units = 1` (maximize inlining across crate boundaries). These settings ensure that sanitizers and debuggers can correlate machine instructions back to source lines while still exercising production-level optimizations.

Install compiler sanitizer support by adding the `rust-src` component through `rustup component add rust-src`, which allows sanitizers to instrument the standard library. For ThreadSanitizer (TSan), the Rust compiler requires nightly builds due to unstable target features; install the nightly toolchain with `rustup install nightly` and set per-project overrides via `rustup override set nightly` in the project directory. AddressSanitizer (ASan) works on stable Rust but requires specific target flags during compilation. Test ASan by compiling a trivial program with `RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu` and running the binary—if setup is correct, ASan will print its banner on startup.

Establish a reproducible verification environment by creating a dedicated lab directory with isolated project crates. Initialize a Rust workspace with `cargo new --lib verification-labs` and add individual exercise crates as workspace members. This structure allows each exercise to maintain independent dependencies and toolchain configurations while sharing common build artifacts. For C++ exercises, create parallel directories with CMake build systems configured for sanitizer integration via `CMAKE_CXX_FLAGS="-fsanitize=address,undefined -g3 -fno-omit-frame-pointer"`. The `-fno-omit-frame-pointer` flag is critical for accurate stack traces under sanitizers and profilers, as it prevents the compiler from reusing the frame pointer register for general computation.

Finally, validate the complete toolchain by running a minimal verification workflow. Create a test Rust program that deliberately triggers an out-of-bounds access, compile with AddressSanitizer enabled, and confirm that ASan halts execution with a detailed error report including the source file and line number. Next, write a C++ program with a use-after-free bug, compile with `-fsanitize=address`, and verify the sanitizer report. Run a simple multi-threaded Rust program under ThreadSanitizer to ensure TSan correctly identifies shared memory accesses. Profile a CPU-bound loop with `perf record` and generate a flame graph to confirm that `perf` captures symbol information from debug builds. This validation sequence confirms that the toolchain is fully operational and ready for the verification exercises.

## Exercise 1: AST, IR & Disassembly Analysis

This exercise dissects the compilation pipeline from source code to machine instructions, exposing optimization decisions that directly impact performance and debuggability. The workflow begins with Rust's high-level AST, proceeds through MIR (Rust's mid-level IR) and LLVM IR (low-level IR), and terminates in x86-64 assembly. Each intermediate representation reveals distinct optimization phases: MIR performs borrow checking and monomorphization, LLVM IR applies algebraic simplifications and loop transformations, and the assembly backend schedules instructions for microarchitectural execution units. Understanding these transformations is essential for diagnosing performance anomalies, verifying security-critical constant-time operations, and predicting inlining behavior in hot paths.

Create a new Rust crate with `cargo new --lib ast-analysis` and implement a performance-sensitive function that exercises common optimization patterns: function inlining, bounds check elimination, and SIMD autovectorization. The following implementation provides a concrete workload for IR inspection. Open `src/lib.rs` and define a vectorized sum function that operates on slices:

```rust
#![feature(portable_simd)]
use std::simd::{Simd, SimdUint};

pub fn scalar_sum(data: &[u32]) -> u64 {
    data.iter().map(|&x| x as u64).sum()
}

pub fn vectorized_sum(data: &[u32]) -> u64 {
    const LANES: usize = 8;
    let (prefix, chunks, suffix) = data.as_simd::<LANES>();
    
    let mut sum = Simd::<u32, LANES>::splat(0);
    for &chunk in chunks {
        sum += chunk;
    }
    
    let scalar_sum: u64 = prefix.iter().chain(suffix.iter())
        .map(|&x| x as u64)
        .sum();
    
    sum.reduce_sum() as u64 + scalar_sum
}

#[inline(never)]
pub fn cold_path(x: u32) -> u32 {
    if x > 1000 {
        x * 2 + 1
    } else {
        x + 1
    }
}

pub fn hot_inline(data: &mut [u32]) {
    for elem in data {
        *elem = cold_path(*elem);
    }
}
```

This code establishes three verification targets: `scalar_sum` as a baseline autovectorization candidate, `vectorized_sum` using explicit portable SIMD, and `hot_inline` with an `#[inline(never)]` function to observe call overhead. Begin the verification workflow by examining Rust's MIR, which operates after macro expansion and type checking but before LLVM lowering. Compile the crate with MIR emission enabled: `cargo rustc --lib -- --emit=mir -C opt-level=3`. This generates `target/release/deps/*.mir` files containing human-readable MIR for each function. Open the MIR file and locate the `scalar_sum` function definition.

MIR represents Rust code as a control flow graph of basic blocks with explicit temporaries and memory operations. Each statement corresponds to a single semantic action: assignment, function call, or terminator (branch, return, panic). Examine the MIR for `scalar_sum` and identify key optimization markers. The iterator chain should compile to a simple loop with bounds checks. If LLVM successfully vectorizes the loop, the MIR will show no evidence of vectorization—that transformation occurs entirely in LLVM IR. Look for the `_1 = CheckedAdd(...)` intrinsic, which represents overflow-checked addition. In release mode with optimizations enabled, LLVM should remove these checks after proving the sum cannot overflow a `u64`.

Next, inspect LLVM IR to observe algebraic simplification and loop vectorization. Generate LLVM IR with `cargo rustc --lib -- --emit=llvm-ir -C opt-level=3`. The output appears in `target/release/deps/*.ll` as textual LLVM assembly. LLVM IR uses static single assignment (SSA) form with infinite virtual registers and typed pointers (or opaque pointers in LLVM 15+). Locate the `@_ZN12ast_analysis10scalar_sum` function (the mangled name for `scalar_sum`). The function signature should show `%slice.0` (data pointer) and `%slice.1` (length) arguments.

Examine the loop body for vectorization evidence. If LLVM's loop vectorizer succeeds, the IR will contain vector types like `<8 x i32>` and vector instructions such as `load <8 x i32>` followed by `add <8 x i32>`. The vectorized loop processes multiple elements per iteration, with a scalar epilogue handling remainder elements. Compare this to the `vectorized_sum` function, which uses explicit SIMD intrinsics. The explicit version should compile to nearly identical vector instructions but with Rust-level control over lane width and alignment. Note that the `as_simd` method produces compile-time guarantees about alignment and chunk boundaries, eliminating runtime checks that LLVM's autovectorizer must insert.

Now generate assembly to observe instruction scheduling and register allocation. Run `cargo rustc --lib -- --emit=asm -C opt-level=3` and open `target/release/deps/*.s`. x86-64 assembly uses AT&T syntax by default in rustc/LLVM output: `movq %rax, %rbx` moves from `%rax` to `%rbx`. Locate the `scalar_sum` function and identify the main loop. A successfully vectorized loop will use SIMD instructions such as `vpaddd` (packed doubleword add) or `vpaddq` (packed quadword add) operating on YMM registers (256-bit) or ZMM registers (512-bit on AVX-512 CPUs). The instruction sequence should load 8 or more elements simultaneously, accumulate them in vector registers, and perform a horizontal reduction at the loop exit.

Contrast the vectorized assembly with the `cold_path` function, which was marked `#[inline(never)]`. This function should appear as a separate symbol with a standard calling convention: arguments passed in registers (`%rdi`, `%rsi`, `%rdx` for the first three arguments), a stack frame setup with `pushq %rbp; movq %rsp, %rbp`, and a `retq` instruction. The `hot_inline` function should contain a `callq` instruction targeting `cold_path`, demonstrating the function call overhead. If you remove the `#[inline(never)]` attribute, recompile, and inspect the assembly, the `cold_path` body should be directly embedded into `hot_inline`, eliminating the call overhead but increasing code size.

To quantify the performance impact of these transformations, write a criterion benchmark that measures the throughput of `scalar_sum` versus `vectorized_sum`. Create `benches/sum_bench.rs` and add the following benchmark harness:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};
use ast_analysis::{scalar_sum, vectorized_sum};

fn benchmark_sum(c: &mut Criterion) {
    let data: Vec<u32> = (0..1_000_000).map(|x| x % 1000).collect();
    
    let mut group = c.benchmark_group("sum");
    group.throughput(Throughput::Elements(data.len() as u64));
    
    group.bench_function("scalar", |b| {
        b.iter(|| scalar_sum(black_box(&data)))
    });
    
    group.bench_function("vectorized", |b| {
        b.iter(|| vectorized_sum(black_box(&data)))
    });
    
    group.finish();
}

criterion_group!(benches, benchmark_sum);
criterion_main!(benches);
```

Add the criterion dependency to `Cargo.toml` under `[dev-dependencies]` with `criterion = "0.5"` and define the benchmark target with `[[bench]]` specifying `name = "sum_bench"` and `harness = false`. Run the benchmark with `cargo bench` and observe the throughput measurements in elements per second. On modern x86-64 CPUs with AVX2, the vectorized version should achieve 4-8x higher throughput than the scalar version when LLVM successfully autovectorizes. If the scalar version shows similar performance, LLVM's autovectorization succeeded, and the explicit SIMD provides no additional benefit—this outcome validates the compiler's optimization effectiveness.

Finally, use `cargo-asm` to directly inspect the assembly of individual functions without parsing full assembly files. Install the tool with `cargo install cargo-asm` and run `cargo asm ast_analysis::scalar_sum --rust --build-type release`. This command disassembles the compiled function and annotates each assembly instruction with the corresponding Rust source line, making it trivial to correlate high-level code with machine instructions. Use this workflow to verify that critical security-sensitive code, such as constant-time cryptographic operations, compiles without data-dependent branches or memory accesses that could leak secrets through timing side channels.

This exercise establishes the verification discipline of validating compiler transformations rather than trusting them. In production systems, subtle changes to source code or compiler versions can silently disable vectorization or inline critical functions, regressing performance by orders of magnitude. By integrating IR and assembly inspection into the development workflow, engineers gain the ability to diagnose these regressions immediately and adjust source code to restore optimal code generation.

## Exercise 2: Cache Miss & Throughput Profiling

Performance optimization in modern systems engineering fundamentally reduces to minimizing CPU stalls caused by cache misses, branch mispredictions, and pipeline hazards. This exercise uses Linux `perf` and `cargo-flamegraph` to quantify hardware-level performance counters and visualize CPU cycle distribution across function call stacks. The workflow profiles a cache-sensitive workload, identifies hot paths consuming CPU cycles, and measures the impact of data structure layout on memory access patterns. Successful profiling requires understanding hardware performance monitoring units (PMUs), which expose microarchitectural events such as L1 data cache misses, TLB misses, and instructions retired per cycle.

Create a new Rust crate with `cargo new --bin cache-profile` and implement two data structure variants that exhibit dramatically different cache behavior: a structure-of-arrays (SoA) layout that maximizes cache locality, and an array-of-structures (AoS) layout that causes cache thrashing. Open `src/main.rs` and define the following particle simulation workload:

```rust
use std::time::Instant;

const PARTICLE_COUNT: usize = 1_000_000;
const ITERATIONS: usize = 100;

// Array-of-Structures: poor cache locality
#[derive(Clone)]
struct ParticleAoS {
    x: f64,
    y: f64,
    z: f64,
    vx: f64,
    vy: f64,
    vz: f64,
}

// Structure-of-Arrays: excellent cache locality
#[derive(Clone)]
struct ParticlesSoA {
    x: Vec<f64>,
    y: Vec<f64>,
    z: Vec<f64>,
    vx: Vec<f64>,
    vy: Vec<f64>,
    vz: Vec<f64>,
}

impl ParticlesSoA {
    fn new(count: usize) -> Self {
        Self {
            x: vec![0.0; count],
            y: vec![0.0; count],
            z: vec![0.0; count],
            vx: vec![1.0; count],
            vy: vec![1.0; count],
            vz: vec![1.0; count],
        }
    }
}

fn update_aos(particles: &mut [ParticleAoS], dt: f64) {
    for p in particles {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.z += p.vz * dt;
    }
}

fn update_soa(particles: &mut ParticlesSoA, dt: f64) {
    let len = particles.x.len();
    for i in 0..len {
        particles.x[i] += particles.vx[i] * dt;
        particles.y[i] += particles.vy[i] * dt;
        particles.z[i] += particles.vz[i] * dt;
    }
}

fn main() {
    // Benchmark Array-of-Structures
    let mut particles_aos: Vec<ParticleAoS> = vec![
        ParticleAoS {
            x: 0.0, y: 0.0, z: 0.0,
            vx: 1.0, vy: 1.0, vz: 1.0,
        };
        PARTICLE_COUNT
    ];
    
    let start = Instant::now();
    for _ in 0..ITERATIONS {
        update_aos(&mut particles_aos, 0.016);
    }
    let aos_duration = start.elapsed();
    
    // Benchmark Structure-of-Arrays
    let mut particles_soa = ParticlesSoA::new(PARTICLE_COUNT);
    
    let start = Instant::now();
    for _ in 0..ITERATIONS {
        update_soa(&mut particles_soa, 0.016);
    }
    let soa_duration = start.elapsed();
    
    println!("AoS: {:.2?}", aos_duration);
    println!("SoA: {:.2?}", soa_duration);
    println!("Speedup: {:.2}x", aos_duration.as_secs_f64() / soa_duration.as_secs_f64());
}
```

This workload updates particle positions based on velocities, a common pattern in scientific computing and game engines. The AoS layout stores all six fields (x, y, z, vx, vy, vz) contiguously for each particle, while the SoA layout groups all x-coordinates together, then all y-coordinates, and so on. When the update loop reads vx and writes x, the AoS layout requires loading an entire 48-byte structure into cache lines (typically 64 bytes) even though only 16 bytes are accessed. The SoA layout packs accessed fields into consecutive cache lines, achieving near-perfect cache utilization.

Compile the program in release mode with debug symbols: `cargo build --release`. Run the binary with `./target/release/cache-profile` and observe the reported timings. On typical x86-64 hardware, the SoA version should execute 2-4x faster than the AoS version despite performing identical arithmetic operations. This speedup originates entirely from reduced cache misses. To quantify the difference, profile the binary with `perf stat`, which aggregates hardware performance counters across the entire execution:

```bash
perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses ./target/release/cache-profile
```

The `-e` flag specifies event counters to track. The output reports total cycles consumed, instructions retired, and cache behavior metrics. Focus on the `L1-dcache-load-misses` counter, which counts L1 data cache misses that escalate to L2 or L3 cache lookups. The AoS workload should exhibit significantly higher L1 miss rates than the SoA workload, often 5-10x more misses. The `instructions` counter should be similar between both workloads, confirming that the performance difference arises from memory stalls rather than instruction count.

To understand which specific functions contribute to cache misses, use `perf record` to capture a time-based profile with call stack samples. Run `perf record -e cache-misses -g --call-graph dwarf ./target/release/cache-profile`. The `-e cache-misses` flag samples on cache miss events, the `-g` flag enables call stack capture, and `--call-graph dwarf` uses DWARF debug information for accurate stack unwinding through optimized code. This command generates `perf.data` containing raw sample data. Inspect the profile with `perf report`, which presents an interactive TUI showing functions ranked by sample count. The `update_aos` and `update_soa` functions should dominate the profile, with `update_aos` showing substantially more cache miss samples.

For visual analysis, convert the `perf.data` profile into a flame graph, which renders call stacks as horizontal bars where width represents CPU time. Install `cargo-flamegraph` if not already present and run `cargo flamegraph --bin cache-profile`. This command wraps `perf record` and `perf script` to generate an interactive SVG file at `flamegraph.svg`. Open the SVG in a web browser and examine the flame graph. The x-axis represents the sampled time, and the y-axis shows the call stack depth. Hover over bars to see function names and sample counts. The `update_aos` bar should be wider than `update_soa`, reflecting the increased CPU time spent handling cache misses and memory stalls.

Flame graphs reveal not only which functions consume cycles but also their calling context. If the profiled program had multiple code paths invoking the same function, the flame graph would show separate stacks for each caller, enabling engineers to identify which caller sites are performance-critical. This technique is invaluable for optimizing large codebases where a hot function is called from dozens of locations—profiling identifies which specific call sites drive the majority of CPU consumption.

To isolate the cache miss penalty more precisely, use `perf stat` to measure cycles per instruction (CPI), a metric that quantifies pipeline efficiency. Run `perf stat -e cycles,instructions ./target/release/cache-profile` and calculate CPI manually by dividing cycles by instructions. Modern out-of-order CPUs achieve IPC (instructions per cycle) values near 2-4 for compute-bound workloads. If CPI exceeds 1.0 (or IPC falls below 1.0), the CPU spends significant time stalled on memory or branch mispredictions. The AoS workload should exhibit higher CPI due to memory stalls, while the SoA workload should achieve lower CPI and higher IPC, confirming that cache locality directly improves instruction throughput.

Extend the exercise by profiling TLB (Translation Lookaside Buffer) misses, which occur when virtual-to-physical address translations are not cached in the TLB. Run `perf stat -e dTLB-loads,dTLB-load-misses ./target/release/cache-profile`. The data TLB caches page table entries for recently accessed virtual memory pages. High TLB miss rates indicate that the working set exceeds the TLB capacity, forcing the CPU to walk multi-level page tables for every access. Large-scale simulations with gigabyte-scale datasets often suffer from TLB thrashing, and the only mitigation is to use huge pages (2 MB or 1 GB pages instead of 4 KB), which reduce TLB pressure by mapping larger memory regions per entry.

Finally, use `perf annotate` to correlate cache misses with specific assembly instructions. After capturing a cache-miss profile with `perf record -e cache-misses`, run `perf annotate --stdio` to display annotated disassembly of hot functions. Each assembly instruction is annotated with the percentage of cache miss samples that occurred on that instruction. In the `update_aos` function, the load instructions accessing `p.vx`, `p.vy`, and `p.vz` should show high miss percentages, confirming that these memory accesses trigger cache misses. In contrast, the `update_soa` function should show lower miss percentages uniformly distributed across the loop, reflecting sequential access to contiguous memory.

This exercise establishes the discipline of quantifying performance through hardware counters rather than relying on wall-clock timings, which are confounded by OS scheduling and background processes. Cache miss rates and CPI provide reproducible metrics that directly correlate with microarchitectural behavior, enabling engineers to validate optimizations with scientific rigor. In production systems, performance regressions often manifest as subtle increases in cache miss rates caused by layout changes or allocator behavior—continuous profiling with `perf` detects these regressions before they degrade user-facing latency.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs—data races, deadlocks, and use-after-free in multithreaded contexts—constitute the most challenging class of software defects due to their nondeterministic nature and resistance to traditional testing. This exercise employs ThreadSanitizer (TSan) to detect data races through dynamic race detection, AddressSanitizer (ASan) to catch memory corruption in concurrent code, and Valgrind's Memcheck and Helgrind tools to identify memory leaks and lock-order violations. The workflow instruments a deliberately buggy concurrent data structure, triggers failures under stress testing, and interprets sanitizer reports to localize the root cause.

ThreadSanitizer operates by intercepting all memory accesses and synchronization primitives (mutexes, atomics, memory fences) at runtime, maintaining a vector clock for each thread to detect happens-before relationships. When two threads access the same memory location without proper synchronization and at least one access is a write, TSan reports a data race. The sanitizer imposes 5-15x runtime overhead and 5-10x memory overhead, making it unsuitable for production deployment but essential for pre-release testing. AddressSanitizer detects spatial memory errors (buffer overflows, use-after-free) and temporal errors (accessing freed memory) by poisoning allocator metadata and instrumenting every memory access with shadow memory checks.

Create a new Rust crate with `cargo new --bin race-detection` and implement a broken concurrent hash table that exhibits multiple race conditions. Open `src/main.rs` and define the following structure:

```rust
use std::collections::HashMap;
use std::sync::Arc;
use std::thread;
use std::sync::atomic::{AtomicUsize, Ordering};

// Deliberately unsafe concurrent hash table
struct UnsafeHashTable {
    map: HashMap<u64, u64>,
    reads: AtomicUsize,
    writes: AtomicUsize,
}

impl UnsafeHashTable {
    fn new() -> Self {
        Self {
            map: HashMap::new(),
            reads: AtomicUsize::new(0),
            writes: AtomicUsize::new(0),
        }
    }
    
    fn insert(&mut self, key: u64, value: u64) {
        self.writes.fetch_add(1, Ordering::Relaxed);
        self.map.insert(key, value);
    }
    
    fn get(&self, key: u64) -> Option<u64> {
        self.reads.fetch_add(1, Ordering::Relaxed);
        self.map.get(&key).copied()
    }
    
    fn stats(&self) -> (usize, usize) {
        (self.reads.load(Ordering::Relaxed), 
         self.writes.load(Ordering::Relaxed))
    }
}

fn main() {
    let table = Arc::new(std::cell::UnsafeCell::new(UnsafeHashTable::new()));
    let mut handles = vec![];
    
    // Spawn writer threads
    for tid in 0..4 {
        let table_clone = Arc::clone(&table);
        handles.push(thread::spawn(move || {
            for i in 0..10000 {
                unsafe {
                    (*table_clone.get()).insert(tid * 10000 + i, i);
                }
            }
        }));
    }
    
    // Spawn reader threads
    for tid in 0..4 {
        let table_clone = Arc::clone(&table);
        handles.push(thread::spawn(move || {
            for i in 0..10000 {
                unsafe {
                    let _ = (*table_clone.get()).get(tid * 10000 + i);
                }
            }
        }));
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    unsafe {
        let stats = (*table.get()).stats();
        println!("Reads: {}, Writes: {}", stats.0, stats.1);
    }
}
```

This code uses `UnsafeCell` to bypass Rust's borrow checker, deliberately creating data races where multiple threads concurrently read and write the HashMap without synchronization. The HashMap's internal structure is not thread-safe—concurrent inserts can corrupt bucket chains, and concurrent reads during writes can observe partially updated state or invalid pointers. This program will likely crash or produce incorrect results, but the crash is nondeterministic and depends on thread interleaving, making manual debugging nearly impossible without a race detector.

Compile and run the program under ThreadSanitizer to detect the races. Since TSan requires nightly Rust, ensure the nightly toolchain is installed with `rustup install nightly` and set it for this project with `rustup override set nightly`. Compile with TSan enabled using `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --target x86_64-unknown-linux-gnu`. The program will execute under TSan instrumentation, and when races are detected, TSan will print detailed reports to stderr.

A typical TSan report includes the following sections: a WARNING header identifying the race type (data race, lock-order inversion), the memory address involved, and two stack traces showing the conflicting accesses. The first stack trace shows where one thread wrote to the shared location, and the second shows where another thread accessed it without synchronization. TSan also reports the thread IDs involved, enabling engineers to correlate races with specific spawned threads. Examine the TSan output and locate the data race involving the HashMap. The report should show concurrent access to internal HashMap fields such as bucket pointers or the hash table length.

To fix the data race, wrap the HashMap in a `Mutex` or use a concurrent data structure such as `DashMap` from the `dashmap` crate, which provides a lock-free concurrent hash map. Replace the `UnsafeHashTable` with a synchronized version:

```rust
use std::sync::Mutex;

struct SafeHashTable {
    map: Mutex<HashMap<u64, u64>>,
    reads: AtomicUsize,
    writes: AtomicUsize,
}

impl SafeHashTable {
    fn new() -> Self {
        Self {
            map: Mutex::new(HashMap::new()),
            reads: AtomicUsize::new(0),
            writes: AtomicUsize::new(0),
        }
    }
    
    fn insert(&self, key: u64, value: u64) {
        self.writes.fetch_add(1, Ordering::Relaxed);
        self.map.lock().unwrap().insert(key, value);
    }
    
    fn get(&self, key: u64) -> Option<u64> {
        self.reads.fetch_add(1, Ordering::Relaxed);
        self.map.lock().unwrap().get(&key).copied()
    }
    
    fn stats(&self) -> (usize, usize) {
        (self.reads.load(Ordering::Relaxed), 
         self.writes.load(Ordering::Relaxed))
    }
}
```

Recompile and run under TSan—the sanitizer should report no data races. However, the mutex introduces contention, reducing throughput compared to a lock-free design. To measure the contention impact, profile the synchronized version with `perf record -e sched:sched_switch` to count context switches, which increase when threads block on mutexes. High context switch rates indicate lock contention, suggesting the need for finer-grained locking or lock-free algorithms.

Next, introduce a memory leak to demonstrate Valgrind's leak detection. Modify the program to allocate HashMap entries through `Box::leak`, which deliberately leaks memory:

```rust
fn insert_leak(&self, key: u64, value: u64) {
    self.writes.fetch_add(1, Ordering::Relaxed);
    let leaked = Box::leak(Box::new((key, value)));
    self.map.lock().unwrap().insert(leaked.0, leaked.1);
}
```

Replace `insert` calls with `insert_leak` in the writer threads. Compile the program without sanitizers using `cargo build --release`, then run under Valgrind's Memcheck tool: `valgrind --leak-check=full --show-leak-kinds=all ./target/release/race-detection`. Valgrind will execute the program under a virtual machine that tracks every memory allocation and deallocation. When the program exits, Memcheck reports leaked memory blocks with full stack traces showing where each leak was allocated.

The Valgrind report categorizes leaks as "definitely lost" (no references remain), "indirectly lost" (referenced by leaked blocks), "possibly lost" (interior pointers remain), or "still reachable" (references exist but were not freed). Focus on "definitely lost" leaks, which represent unambiguous memory leaks. The report should show multiple leaks originating from `Box::leak` calls in the `insert_leak` function, with stack traces pointing to the exact source line in `main.rs`. Fix the leak by removing `Box::leak` and returning to normal HashMap insertions.

To detect lock-order violations that cause deadlocks, use Valgrind's Helgrind tool, which tracks lock acquisition order across threads and reports potential deadlock cycles. Create a deadlock scenario by acquiring two mutexes in inconsistent order across threads:

```rust
use std::sync::Mutex;

fn deadlock_example() {
    let lock_a = Arc::new(Mutex::new(0));
    let lock_b = Arc::new(Mutex::new(0));
    
    let lock_a1 = Arc::clone(&lock_a);
    let lock_b1 = Arc::clone(&lock_b);
    let handle1 = thread::spawn(move || {
        let _guard_a = lock_a1.lock().unwrap();
        thread::sleep(std::time::Duration::from_millis(10));
        let _guard_b = lock_b1.lock().unwrap();
    });
    
    let lock_a2 = Arc::clone(&lock_a);
    let lock_b2 = Arc::clone(&lock_b);
    let handle2 = thread::spawn(move || {
        let _guard_b = lock_b2.lock().unwrap();
        thread::sleep(std::time::Duration::from_millis(10));
        let _guard_a = lock_a2.lock().unwrap();
    });
    
    handle1.join().unwrap();
    handle2.join().unwrap();
}
```

Thread 1 acquires lock A then lock B, while thread 2 acquires lock B then lock A. If both threads acquire their first lock simultaneously, they will deadlock waiting for each other's lock. Run this code under Helgrind: `valgrind --tool=helgrind ./target/debug/race-detection`. Helgrind detects the lock-order inversion and reports a potential deadlock with stack traces showing both acquisition orders. The report states "lock order violation" followed by the two conflicting lock acquisition sequences, enabling engineers to identify and fix the inconsistent ordering.

Finally, test AddressSanitizer on a use-after-free scenario in a concurrent context. Introduce a bug where one thread frees a buffer while another thread continues reading from it:

```rust
use std::alloc::{alloc, dealloc, Layout};

fn use_after_free_race() {
    let layout = Layout::from_size_align(1024, 8).unwrap();
    let ptr = unsafe { alloc(layout) };
    let ptr_copy = ptr;
    
    let handle1 = thread::spawn(move || {
        unsafe {
            dealloc(ptr, layout);
        }
    });
    
    let handle2 = thread::spawn(move || {
        thread::sleep(std::time::Duration::from_millis(10));
        unsafe {
            let _ = *ptr_copy; // Use-after-free
        }
    });
    
    handle1.join().unwrap();
    handle2.join().unwrap();
}
```

Compile with AddressSanitizer on stable Rust: `RUSTFLAGS="-Z sanitizer=address" cargo +nightly build --target x86_64-unknown-linux-gnu` and run the binary. ASan will detect the use-after-free when thread 2 accesses the deallocated buffer and halt execution with a detailed report showing the deallocation stack trace, the use-after-free stack trace, and the memory address involved. The report includes shadow memory state, indicating whether the freed region was poisoned by ASan's allocator instrumentation.

This exercise establishes the operational discipline of integrating sanitizers into continuous integration pipelines. Production-grade open source projects run TSan and ASan in nightly test suites to catch concurrency and memory bugs before they reach users. The sanitizers' runtime overhead precludes production deployment, but their deterministic detection of races and memory errors surpasses the effectiveness of manual testing by orders of magnitude. Combine sanitizers with fuzzing frameworks such as `cargo-fuzz` to generate pathological inputs that stress concurrent code paths, maximizing coverage of rare interleavings that trigger bugs.

## Developer Cheat Sheet & Toolchain Checklist

This reference section consolidates critical commands, compiler flags, and sanitizer invocations for daily verification workflows. Each entry provides the exact command syntax and expected output interpretation, eliminating ambiguity in operational procedures.

**Rust Compilation with Debug Symbols:**
```bash
cargo build --release
# Generates target/release/<binary> with DWARF debug info if profile.release.debug = true in Cargo.toml
```

**Emit LLVM IR:**
```bash
cargo rustc --lib -- --emit=llvm-ir -C opt-level=3
# Output: target/release/deps/*.ll
```

**Emit MIR:**
```bash
cargo rustc --lib -- --emit=mir -C opt-level=3
# Output: target/release/deps/*.mir
```

**Emit Assembly:**
```bash
cargo rustc --lib -- --emit=asm -C opt-level=3
# Output: target/release/deps/*.s (AT&T syntax)
```

**Disassemble Function with cargo-asm:**
```bash
cargo asm <crate_name>::<function_name> --rust --build-type release
# Annotated assembly with source line correlation
```

**Basic perf stat:**
```bash
perf stat -e cycles,instructions,cache-misses,branch-misses ./target/release/<binary>
# Reports hardware counter totals
```

**Record perf profile with call graphs:**
```bash
perf record -e cycles -g --call-graph dwarf -F 997 ./target/release/<binary>
# Generates perf.data, use 'perf report' to analyze
```

**Generate flame graph:**
```bash
cargo flamegraph --bin <binary_name>
# Outputs flamegraph.svg
```

**Annotate assembly with perf samples:**
```bash
perf record -e cache-misses ./target/release/<binary>
perf annotate --stdio
# Shows per-instruction cache miss percentages
```

**Run with AddressSanitizer (stable Rust with nightly flag):**
```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly run --target x86_64-unknown-linux-gnu
# Detects buffer overflows, use-after-free, memory leaks
```

**Run with ThreadSanitizer (requires nightly):**
```bash
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --target x86_64-unknown-linux-gnu
# Detects data races, lock-order inversions
```

**Run Valgrind Memcheck for leaks:**
```bash
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./target/release/<binary>
# Reports leaked allocations with stack traces
```

**Run Valgrind Helgrind for lock violations:**
```bash
valgrind --tool=helgrind ./target/debug/<binary>
# Detects lock-order inversions and race conditions (prefer debug builds for symbols)
```

**C++ Compilation with Sanitizers:**
```bash
clang++ -fsanitize=address,undefined -g3 -fno-omit-frame-pointer -O2 source.cpp -o binary
# Enables ASan and UBSan with full debug info
```

**GDB with Rust pretty-printers:**
```bash
rust-gdb ./target/debug/<binary>
# Auto-loads Rust standard library formatters for Vec, HashMap, etc.
```

**LLDB with Rust support:**
```bash
rust-lldb ./target/debug/<binary>
# Provides Rust-aware type inspection and backtraces
```

**Check if perf requires root:**
```bash
cat /proc/sys/kernel/perf_event_paranoid
# If > 1, run 'sudo sysctl kernel.perf_event_paranoid=1' to allow non-root profiling
```

**Profile cache behavior:**
```bash
perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses ./target/release/<binary>
# Quantifies L1 and last-level cache (LLC) miss rates
```

**Profile TLB misses:**
```bash
perf stat -e dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses ./target/release/<binary>
# Identifies page table walk overhead
```

**Branch misprediction analysis:**
```bash
perf stat -e branches,branch-misses ./target/release/<binary>
# High miss rates indicate unpredictable control flow
```

**Cargo test with sanitizers:**
```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu
# Runs entire test suite under ASan
```

**Benchmark with criterion:**
```bash
cargo bench --bench <bench_name>
# Outputs statistical analysis of throughput and latency
```

**Install required tools:**
```bash
rustup component add rust-src
rustup install nightly
cargo install cargo-asm cargo-flamegraph
sudo apt install valgrind linux-tools-generic clang lldb
```

**Verify toolchain setup:**
```bash
rustc --version && clang --version && perf --version && valgrind --version
# Confirms all tools are installed and accessible
```

**Set release profile with debug symbols (Cargo.toml):**
```toml
[profile.release]
debug = true
opt-level = 3
lto = "thin"
codegen-units = 1
```

**Critical sanitizer flags for C++ projects:**
```bash
-fsanitize=address          # Heap/stack buffer overflow, use-after-free
-fsanitize=thread           # Data races (mutually exclusive with ASan)
-fsanitize=undefined        # Undefined behavior (signed overflow, null deref)
-fsanitize=memory           # Uninitialized memory reads (requires instrumented libc)
-fno-omit-frame-pointer     # Accurate stack traces
-g3                         # Maximum debug info including macro definitions
```

This cheat sheet serves as the operational reference for all verification workflows, ensuring engineers execute commands correctly and interpret outputs precisely. Commit this reference to project repositories alongside CI configuration to standardize verification practices across development teams.
