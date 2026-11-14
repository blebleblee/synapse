# Operational Verification Labs: Compilers

## Objective & Toolchain Setup

Modern compiler toolchains transform high-level source code through multiple intermediate representations before emitting machine code, and each transformation stage introduces opportunities for optimization, undefined behavior, and performance pathology. This laboratory sequence trains you to operationally verify compiler output across the full compilation pipeline: from abstract syntax tree construction through intermediate representation optimization to final code generation and runtime execution. You will instrument three production-grade toolchains—Rust's LLVM-based rustc, the GNU Compiler Collection, and Clang—using their native introspection interfaces, sanitizer runtimes, and performance profilers to diagnose miscompilation, memory corruption, data races, and microarchitectural bottlenecks.

The verification methodology follows a three-layer diagnostic model. First, you inspect static compiler artifacts—abstract syntax trees, LLVM intermediate representation, and x86-64 assembly—to understand optimization decisions and calling conventions. Second, you profile dynamic execution under controlled workloads, measuring instruction throughput, cache miss rates, and branch prediction accuracy using hardware performance counters. Third, you inject fault detection instrumentation through compiler-embedded sanitizers that rewrite memory operations, synchronization primitives, and control flow to expose undefined behavior that would otherwise manifest as silent corruption or non-deterministic crashes.

Begin by establishing a hermetic build environment with explicit compiler versioning. Install the Rust toolchain through rustup, which provides reproducible channel management and cross-compilation target support. On Ubuntu or Debian systems, execute `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` and select the stable channel. Verify installation with `rustc --version` and `cargo --version`, confirming you have rustc 1.83 or later with LLVM 18 backend support. Install the LLVM toolchain via `sudo apt install clang-18 lldb-18 llvm-18` to access clang, lldb debugger, and llvm-objdump disassembler. For dynamic analysis, install Valgrind memcheck with `sudo apt install valgrind`, though note that Valgrind's binary instrumentation incurs 10-50x slowdown and cannot detect all concurrency bugs. Install perf for hardware counter profiling via `sudo apt install linux-tools-common linux-tools-generic`, then enable unprivileged access with `sudo sysctl -w kernel.perf_event_paranoid=1` to allow non-root performance monitoring.

Augment the Rust toolchain with diagnostic cargo subcommands. Install flamegraph profiling with `cargo install flamegraph`, which wraps perf record and generates interactive SVG call graphs. Install cargo-asm for inline assembly inspection via `cargo install cargo-asm`, enabling you to view optimized machine code without leaving the source editor. Install cargo-expand to examine macro expansion with `cargo install cargo-expand`, critical for understanding procedural macro transformations. Finally, install miri, Rust's experimental interpreter for detecting undefined behavior in unsafe code, through `rustup component add miri`. Miri executes MIR (Mid-level Intermediate Representation) with strict validity checking, catching use-after-free, unaligned access, and data race conditions that sanitizers miss, though it cannot run code with FFI calls or inline assembly.

Create a laboratory workspace with isolated compilation environments. Initialize a Rust project with `cargo new --lib compiler_lab && cd compiler_lab`, then configure Cargo.toml to enable multiple optimization profiles and sanitizer targets. Replace the default profile section with explicit configurations for debug, release, and instrumented builds. Set `[profile.dev]` with `opt-level = 0` and `debug = true` for maximum debuggability. Configure `[profile.release]` with `opt-level = 3`, `lto = "fat"`, and `codegen-units = 1` to enable aggressive interprocedural optimization and link-time optimization across the entire dependency graph. Add a custom `[profile.bench]` inheriting from release but with `debug = true` to preserve symbol tables for profiler attribution. Define a `[profile.sanitize]` profile inheriting from release but with `opt-level = 1` to balance sanitizer overhead against optimization, as full `-O3` can obscure memory corruption by eliminating triggering code paths.

Configure sanitizer instrumentation through environment variables and rustflags. AddressSanitizer detects spatial memory safety violations—buffer overflows, use-after-free, double-free—by inserting red zones around heap allocations and maintaining shadow memory that tracks every byte's validity state. Enable it with `export RUSTFLAGS="-Z sanitizer=address"` and `export ASAN_OPTIONS="detect_leaks=1:abort_on_error=1"`. ThreadSanitizer detects data races and lock ordering violations through happens-before vector clock analysis, recording all memory accesses and synchronization operations to identify conflicting unsynchronized accesses. Enable with `export RUSTFLAGS="-Z sanitizer=thread"` and `export TSAN_OPTIONS="halt_on_error=1:history_size=7"`. MemorySanitizer tracks uninitialized memory propagation, though it requires recompiling the entire standard library and is primarily useful for C/C++ codebases. LeakSanitizer runs at process exit to detect unreachable heap allocations, enabled automatically with AddressSanitizer or independently via `detect_leaks=1`.

Establish a parallel C++ verification environment to compare compiler behavior across language boundaries. Create a CMakeLists.txt configuration with separate targets for GCC and Clang, each with debug and optimized variants. Define a debug target with `-O0 -g3 -fno-omit-frame-pointer -fno-inline` to disable optimization and preserve full stack traces. Define an optimized target with `-O3 -march=native -flto` to enable autovectorization, function inlining, and link-time optimization. Add sanitizer targets with `-fsanitize=address,undefined -fno-sanitize-recover=all` to abort on the first detected error rather than logging and continuing. For ThreadSanitizer, use `-fsanitize=thread -fPIE -pie` with position-independent executable linking, as TSAN requires full symbol relocation to instrument shared library calls.

## Exercise 1: AST, IR & Disassembly Analysis

The compilation process transforms source code through a sequence of progressively lower-level intermediate representations, each designed for different optimization phases. Rust's rustc front-end parses source into an abstract syntax tree, performs macro expansion and name resolution, then lowers to HIR (High-level Intermediate Representation) for type checking and trait resolution. After borrow checking, rustc generates MIR (Mid-level Intermediate Representation), a control-flow graph with explicit drops and panics suitable for interprocedural optimization. Finally, rustc translates MIR to LLVM IR, where the LLVM backend applies SSA-form dataflow optimization, instruction selection, register allocation, and code layout before emitting machine code. Understanding each representation's structure and optimization properties allows you to diagnose performance anomalies, verify security properties, and predict runtime behavior.

Begin by examining macro expansion and HIR generation. Create a Rust source file `src/lib.rs` with a simple macro-heavy implementation to observe how surface syntax desugars into explicit control flow. Write a `derive` macro invocation and a declarative macro that generates repetitive structure:

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

macro_rules! point_ops {
    ($($method:ident => $op:tt),*) => {
        impl Point {
            $(
                pub fn $method(&self, other: &Point) -> Point {
                    Point {
                        x: self.x $op other.x,
                        y: self.y $op other.y,
                    }
                }
            )*
        }
    };
}

point_ops! {
    add => +,
    sub => -,
    mul => *,
    div => /
}

pub fn distance(p1: &Point, p2: &Point) -> f64 {
    let dx = p1.x - p2.x;
    let dy = p1.y - p2.y;
    (dx * dx + dy * dy).sqrt()
}
```

Expand macros and view the desugared HIR with `cargo expand`. This command runs rustc with `-Zunpretty=expanded`, outputting fully-expanded Rust source where all macros, attributes, and derives have been replaced with their generated code. Observe how `#[derive(Debug)]` generates a verbose `fmt::Debug` implementation with explicit field access and formatting logic. Note that `Clone` produces a shallow copy implementation calling `clone()` on each field, while `PartialEq` generates a method comparing each field with short-circuit evaluation. The declarative macro expands into four nearly-identical method definitions, illustrating how macros reduce source duplication at the cost of longer compilation time and increased LLVM IR size.

Examine the MIR representation to observe how Rust's borrow checker and drop elaboration transform high-level operations into explicit control flow. Run `cargo rustc -- --emit=mir -o target/lib.mir` to generate MIR output, then inspect the distance function's MIR body. MIR uses a basic block structure where each block contains a sequence of statements followed by a terminator—return, goto, switch, or call. Statements include assignments, storage allocations, and drop flag updates. Observe that the subtraction operations `p1.x - p2.x` compile to explicit `CheckedSub` intrinsics in debug mode, which branch to a panic block on overflow, but in release mode with overflow-checks disabled, rustc emits unchecked `Sub` operations. The `sqrt()` call translates to an LLVM intrinsic `llvm.sqrt.f64`, allowing backend instruction selection to emit native x86-64 `sqrtsd` instruction.

Generate LLVM IR to inspect the representation that LLVM optimizers consume. Run `cargo rustc --release -- --emit=llvm-ir -C no-prepopulate-passes` to disable early optimization passes and view unoptimized IR. Open `target/release/deps/compiler_lab-*.ll` and locate the `distance` function. LLVM IR uses static single assignment form where every value is defined exactly once, enabling dataflow analysis to track value provenance precisely. The function begins with parameter declarations annotated with ABI attributes: `%p1` and `%p2` are pointers marked `noalias`, `readonly`, and `dereferenceable(16)`, telling LLVM that the pointers do not overlap, will not be written through, and point to at least 16 contiguous valid bytes. These attributes derive from Rust's borrow checker guarantees and enable aggressive alias analysis optimization.

The IR body loads the struct fields with `getelementptr` offset calculations and `load` instructions. The GEP instruction `getelementptr inbounds %Point, ptr %p1, i32 0, i32 0` computes the address of the first field without performing the load, using the `inbounds` flag to assert that the offset will not overflow the allocation. The subsequent `load double` instruction reads the 64-bit IEEE 754 double from memory with natural alignment. Subtraction translates to `fsub fast double %x1, %x2`, where the `fast` flag enables aggressive floating-point reassociation, contraction, and reciprocal transformations that violate strict IEEE 754 but improve throughput. The `sqrt` call becomes `call fast double @llvm.sqrt.f64(double %sum)`, an intrinsic that backends lower to native instructions.

Run LLVM's optimization pipeline manually to observe transformation sequences. Use `opt-18` with explicit pass specifications: `cargo rustc --release -- --emit=llvm-bc -o target/release/lib.bc && opt-18 -S -O3 target/release/lib.bc -o target/release/lib_opt.ll`. Compare the unoptimized and optimized IR. The optimizer inlines small functions, eliminating call overhead and exposing opportunities for cross-function constant propagation. It hoists loop-invariant `getelementptr` calculations, combines adjacent loads into vector operations, and eliminates dead stores. For the distance function, LLVM may recognize the pattern `sqrt(dx*dx + dy*dy)` and replace it with a single `hypot` intrinsic if available, which provides better numerical stability for extreme input magnitudes.

Disassemble the final machine code to verify instruction selection and register allocation. Run `cargo asm compiler_lab::distance` using cargo-asm, which invokes rustc with assembly emission and filters to the specified function. Alternatively, use `objdump -d -M intel --no-show-raw-insn target/release/libcompiler_lab.rlib` piped through `grep -A 20 "distance"` to extract the function body. On x86-64 with AVX extensions, the compiler loads the struct fields into `xmm0` and `xmm1` registers using `movsd xmm0, qword ptr [rdi]` for the first parameter's x-coordinate. Subtraction becomes `subsd xmm0, xmm2`, and multiplication uses `mulsd xmm0, xmm0` to square the delta. The square root operation translates to the native `sqrtsd xmm0, xmm0` instruction, which completes in 12-15 cycles on modern Intel CPUs with latency-optimized implementation.

Compare Rust's assembly output against equivalent C++ code compiled with Clang and GCC to identify compiler-specific optimization strategies. Write a C++ translation of the distance function:

```cpp
struct Point {
    double x;
    double y;
};

double distance(const Point* p1, const Point* p2) {
    double dx = p1->x - p2->x;
    double dy = p1->y - p2->y;
    return sqrt(dx * dx + dy * dy);
}
```

Compile with Clang using `clang++-18 -O3 -march=native -S -masm=intel distance.cpp -o distance_clang.s` and with GCC using `g++ -O3 -march=native -S -masm=intel distance.cpp -o distance_gcc.s`. Examine the prologues: Clang often generates more compact code with aggressive inlining hints, while GCC may emit additional alignment padding and branch prediction annotations. Both compilers recognize the Euclidean distance pattern, but their vectorization strategies differ. Clang's loop vectorizer uses cost models that prefer wider SIMD operations, while GCC's vectorizer emphasizes code size and may choose narrower vectors for small trip counts.

Construct a microbenchmark that exposes optimization decisions through measurable throughput differences. Create a benchmark suite using Criterion, Rust's standard statistical benchmarking framework. Add Criterion to `Cargo.toml` under `[dev-dependencies]` with `criterion = "0.5"`, then configure a benchmark harness with `[[bench]]` declaring `name = "distance_bench"` and `harness = false`. Write the benchmark in `benches/distance_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use compiler_lab::{Point, distance};

fn distance_benchmark(c: &mut Criterion) {
    let p1 = Point { x: 1.0, y: 2.0 };
    let p2 = Point { x: 4.0, y: 6.0 };
    
    c.bench_function("distance", |b| {
        b.iter(|| {
            distance(black_box(&p1), black_box(&p2))
        })
    });
    
    c.bench_function("distance_batch", |b| {
        let points: Vec<Point> = (0..1000)
            .map(|i| Point { x: i as f64, y: (i * 2) as f64 })
            .collect();
        
        b.iter(|| {
            let mut sum = 0.0;
            for i in 0..points.len() - 1 {
                sum += distance(
                    black_box(&points[i]),
                    black_box(&points[i + 1])
                );
            }
            black_box(sum)
        })
    });
}

criterion_group!(benches, distance_benchmark);
criterion_main!(benches);
```

The `black_box` function prevents the optimizer from constant-folding benchmark inputs or eliminating dead code, ensuring the compiler must emit actual computation. Run `cargo bench` to execute the suite with statistical analysis. Criterion runs each benchmark for multiple iterations, measures timing distributions, detects outliers using Tukey's method, and reports throughput with confidence intervals. Typical output shows the single distance call completes in 5-8 nanoseconds on modern CPUs, dominated by the `sqrtsd` instruction's latency. The batch benchmark reveals vectorization effectiveness: if the compiler successfully autovectorizes the loop, throughput scales near-linearly with vector width, processing 2-4 distance calculations per iteration using packed SIMD instructions.

Inject deliberate optimization barriers to quantify compiler transformation impact. Modify the distance function to use volatile loads, preventing the compiler from caching field values in registers:

```rust
pub fn distance_volatile(p1: &Point, p2: &Point) -> f64 {
    let p1_ptr = p1 as *const Point;
    let p2_ptr = p2 as *const Point;
    unsafe {
        let dx = std::ptr::read_volatile(&(*p1_ptr).x) 
               - std::ptr::read_volatile(&(*p2_ptr).x);
        let dy = std::ptr::read_volatile(&(*p1_ptr).y) 
               - std::ptr::read_volatile(&(*p2_ptr).y);
        (dx * dx + dy * dy).sqrt()
    }
}
```

Benchmark this variant and observe a 3-5x throughput degradation compared to the normal version. Disassemble the volatile implementation to confirm that the compiler emits separate memory loads for each field access rather than hoisting and reusing cached values. This experiment demonstrates how optimization barriers force conservative code generation, illustrating the cost of disabling compiler analysis.

## Exercise 2: Cache Miss & Throughput Profiling

Modern CPU performance depends critically on data locality and instruction-level parallelism, both of which compilers optimize through code layout, prefetching, and instruction scheduling. Cache hierarchies introduce a three-order-of-magnitude latency gap: L1 cache access completes in 4-5 cycles, L2 in 12-15 cycles, L3 in 40-60 cycles, and DRAM in 200-300 cycles. When working set size exceeds cache capacity, performance collapses as the CPU stalls waiting for memory. Compilers attempt to improve locality by reordering structure fields, padding to cache line boundaries, and fusing loops to maximize temporal reuse. However, high-level abstractions often obscure memory access patterns, and only runtime profiling with hardware performance counters reveals the ground truth of cache behavior.

Begin by establishing a memory-intensive workload that stresses the cache hierarchy. Implement a matrix multiplication kernel with three different memory layouts: row-major, column-major, and tiled. Create a new source file `benches/matrix_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

const SIZES: &[usize] = &[64, 128, 256, 512, 1024];

fn matrix_multiply_row_major(a: &[f64], b: &[f64], c: &mut [f64], n: usize) {
    for i in 0..n {
        for j in 0..n {
            let mut sum = 0.0;
            for k in 0..n {
                sum += a[i * n + k] * b[k * n + j];
            }
            c[i * n + j] = sum;
        }
    }
}

fn matrix_multiply_tiled(a: &[f64], b: &[f64], c: &mut [f64], n: usize) {
    const TILE: usize = 64;
    for i in (0..n).step_by(TILE) {
        for j in (0..n).step_by(TILE) {
            for k in (0..n).step_by(TILE) {
                let i_max = (i + TILE).min(n);
                let j_max = (j + TILE).min(n);
                let k_max = (k + TILE).min(n);
                
                for ii in i..i_max {
                    for jj in j..j_max {
                        let mut sum = c[ii * n + jj];
                        for kk in k..k_max {
                            sum += a[ii * n + kk] * b[kk * n + jj];
                        }
                        c[ii * n + jj] = sum;
                    }
                }
            }
        }
    }
}

fn matrix_benchmark(c: &mut Criterion) {
    let mut group = c.benchmark_group("matrix_multiply");
    
    for size in SIZES.iter() {
        let n = *size;
        let a = vec![1.0; n * n];
        let b = vec![2.0; n * n];
        let mut c = vec![0.0; n * n];
        
        group.bench_with_input(
            BenchmarkId::new("row_major", n),
            &n,
            |bench, &n| {
                bench.iter(|| {
                    matrix_multiply_row_major(
                        black_box(&a),
                        black_box(&b),
                        black_box(&mut c),
                        n
                    )
                })
            }
        );
        
        group.bench_with_input(
            BenchmarkId::new("tiled", n),
            &n,
            |bench, &n| {
                bench.iter(|| {
                    matrix_multiply_tiled(
                        black_box(&a),
                        black_box(&b),
                        black_box(&mut c),
                        n
                    )
                })
            }
        );
    }
    
    group.finish();
}

criterion_group!(benches, matrix_benchmark);
criterion_main!(benches);
```

Run the benchmark suite with `cargo bench --bench matrix_bench` and observe throughput degradation as matrix size increases. For small matrices that fit in L1 cache (64x64 matrices occupy 32 KB per matrix, totaling 96 KB well within typical 128 KB L1), the row-major implementation achieves high throughput with minimal cache misses. As size grows to 512x512 (2 MB per matrix, exceeding typical 256 KB L2 but fitting in 8 MB L3), throughput collapses for the row-major version due to strided access to matrix B, which loads one element from each cache line without spatial reuse. The tiled implementation maintains better throughput by breaking the computation into cache-sized blocks, maximizing temporal locality.

Profile cache behavior using Linux perf to measure hardware performance counters. Run the benchmark under perf with explicit cache event sampling: `perf stat -e cycles,instructions,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses cargo bench --bench matrix_bench`. The output reports cycles per instruction (CPI), L1 data cache miss rate, and last-level cache (LLC) miss rate. For the row-major 1024x1024 multiplication, expect L1 miss rates near 50% and LLC miss rates around 20-30%, indicating heavy DRAM traffic. The tiled version reduces LLC misses to 5-10% by improving spatial locality within tiles.

Generate detailed per-function cache miss attribution using perf record and perf report. Record cache miss samples with `perf record -e cache-misses -g cargo bench --bench matrix_bench`, which samples the instruction pointer and call stack at each cache miss event. Analyze the results with `perf report --stdio --sort=dso,symbol` to display cache misses attributed to each function and dynamic shared object. The row-major multiplication function dominates the cache miss profile, with hotspots concentrated in the innermost loop where matrix B is accessed with stride equal to the row width. Disassemble the hotspot code with `perf annotate matrix_multiply_row_major` to view cache miss samples overlaid on assembly instructions, identifying specific load instructions responsible for misses.

Examine compiler-generated prefetch instructions to verify hardware-prefetcher assistance. Modern CPUs include automatic stride prefetchers that detect sequential or regular-stride memory access patterns and issue speculative loads ahead of demand. Disassemble the optimized matrix kernel with `cargo asm --bench matrix_bench --rust` and search for `prefetch` instructions. Clang and GCC may emit software prefetch intrinsics `__builtin_prefetch` translated to `prefetcht0` or `prefetchnta` instructions for cache-friendly or non-temporal (streaming) patterns respectively. Rust's LLVM backend typically relies on hardware prefetchers rather than inserting software prefetch, as incorrect prefetching can pollute caches and degrade performance. Verify prefetcher behavior by running the benchmark with prefetching disabled via model-specific registers, achievable only with privileged access and kernel module support.

Quantify instruction-level parallelism and pipeline stalls using micro-architectural performance counters. Run perf with extended event sets: `perf stat -e cycles,instructions,uops_issued.any,uops_retired.retire_slots,resource_stalls.any cargo bench --bench matrix_bench`. The `uops_issued` and `uops_retired` counters measure micro-operation throughput, indicating how many operations the CPU dispatches and completes per cycle. Modern Intel CPUs retire up to 4-6 micro-ops per cycle under ideal conditions, but memory-bound workloads exhibit significant `resource_stalls.any` indicating execution units idled waiting for cache misses. Compare the row-major and tiled implementations: the tiled version should show higher instructions-per-cycle (IPC) and lower stall rates due to better memory-level parallelism, where multiple independent cache misses overlap.

Profile with flamegraph visualization to identify hot code paths and time attribution. Run `cargo flamegraph --bench matrix_bench`, which uses perf to sample the call stack at 997 Hz and generates an interactive SVG flame graph. Each horizontal bar represents a function on the call stack, with width proportional to the number of samples capturing that function. The row-major multiplication function dominates the profile, consuming 80-90% of total execution time. Within the function, the innermost loop body—loading from B, multiplying, and accumulating—accounts for the majority of samples. Hover over bars to see exact sample counts and percentages. Use flamegraphs to compare multiple implementations side-by-side, quickly identifying which optimization reduced hotspot CPU time.

Investigate compiler autovectorization effectiveness by examining LLVM's vectorization remarks. Enable optimization remarks with `-C llvm-args=-pass-remarks=loop-vectorize` and rebuild: `RUSTFLAGS="-C llvm-args=-pass-remarks=loop-vectorize" cargo build --release`. The compiler emits diagnostic messages indicating which loops were vectorized, which were not, and why. For the matrix multiplication kernel, LLVM may report that the innermost k-loop was not vectorized due to unknown trip count or potential aliasing between the output and input arrays, despite noalias attributes. Manually annotate loops with `#[cfg(target_arch = "x86_64")] unsafe { std::arch::x86_64::_mm_prefetch(...) }` or restructure code to provide explicit loop bounds and pointer alignment hints.

Force explicit SIMD vectorization using portable-SIMD intrinsics to compare against autovectorization. Rust's `std::simd` module provides portable SIMD types like `f64x4` representing a vector of four 64-bit floats. Rewrite the inner loop using explicit SIMD operations:

```rust
#![feature(portable_simd)]
use std::simd::prelude::*;

fn matrix_multiply_simd(a: &[f64], b: &[f64], c: &mut [f64], n: usize) {
    for i in 0..n {
        for j in (0..n).step_by(4) {
            let mut sum = f64x4::splat(0.0);
            for k in 0..n {
                let a_val = f64x4::splat(a[i * n + k]);
                let b_vec = f64x4::from_slice(&b[k * n + j..]);
                sum += a_val * b_vec;
            }
            sum.copy_to_slice(&mut c[i * n + j..]);
        }
    }
}
```

Benchmark the SIMD version and verify that throughput improves by a factor approaching the vector width (4x for 256-bit AVX2, 8x for 512-bit AVX-512). Disassemble the SIMD implementation to confirm the compiler emits packed operations: `vmulpd ymm0, ymm1, ymm2` for vectorized multiplication and `vaddpd ymm0, ymm0, ymm1` for accumulation. Compare instruction counts between scalar and SIMD versions: the SIMD code executes fewer instructions but may exhibit lower IPC if memory bandwidth becomes the bottleneck rather than computation.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs—data races, deadlocks, use-after-free in shared state—represent the most insidious class of software defects because they manifest non-deterministically, depending on thread scheduling and memory ordering. Compilers provide dynamic analysis tools that instrument synchronization primitives and memory accesses to detect races at runtime. ThreadSanitizer embeds happens-before tracking into every load, store, lock acquisition, and atomic operation, building a vector clock graph to identify conflicting unsynchronized accesses. AddressSanitizer detects spatial and temporal memory safety violations by inserting red zones around allocations and maintaining shadow memory tracking each byte's validity. LeakSanitizer scans reachable memory at process exit to identify heap allocations never freed. This exercise trains you to deploy these sanitizers systematically, interpret their diagnostic output, and construct stress tests that expose latent concurrency bugs.

Begin by implementing a deliberately-racy concurrent counter to establish baseline sanitizer behavior. Create a new source file `src/racy_counter.rs`:

```rust
use std::sync::Arc;
use std::thread;

pub struct RacyCounter {
    value: u64,
}

impl RacyCounter {
    pub fn new() -> Self {
        RacyCounter { value: 0 }
    }
    
    pub fn increment(&mut self) {
        self.value += 1;
    }
    
    pub fn get(&self) -> u64 {
        self.value
    }
}

pub fn stress_test_racy(iterations: u64) -> u64 {
    let counter = Arc::new(std::sync::Mutex::new(RacyCounter::new()));
    let mut handles = vec![];
    
    for _ in 0..4 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..iterations {
                let mut c = counter_clone.lock().unwrap();
                let val = c.get();
                drop(c);
                
                thread::yield_now();
                
                let mut c = counter_clone.lock().unwrap();
                c.value = val + 1;
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let final_count = counter.lock().unwrap().get();
    final_count
}
```

This code exhibits a time-of-check-to-time-of-use race: each thread locks the mutex, reads the counter value, unlocks, yields to increase race window, then locks again and writes the incremented value. Between the read and write, other threads may have modified the value, causing lost updates. Run the stress test without sanitizers: `cargo run --release` calling `stress_test_racy(10000)` and printing the result. The expected value is 40000 (4 threads × 10000 iterations), but actual results range from 15000-35000 depending on thread scheduling, demonstrating non-deterministic race behavior.

Enable ThreadSanitizer to detect the race condition at runtime. Set sanitizer flags and rebuild: `export RUSTFLAGS="-Z sanitizer=thread" && cargo clean && cargo build --release`. Run the instrumented binary with `cargo run --release`. ThreadSanitizer immediately detects the race and prints a diagnostic report:

```
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7f8a3c000d00 by thread T2:
    #0 compiler_lab::racy_counter::stress_test_racy::{{closure}} src/racy_counter.rs:25
    #1 std::sys::thread::Thread::new::thread_start ...
    
  Previous read of size 8 at 0x7f8a3c000d00 by thread T1:
    #0 compiler_lab::racy_counter::RacyCounter::get src/racy_counter.rs:14
    #1 compiler_lab::racy_counter::stress_test_racy::{{closure}} src/racy_counter.rs:21
    
  Location is heap block of size 8 at 0x7f8a3c000d00 allocated by main thread:
    #0 malloc ThreadSanitizer interceptor
    #1 alloc::alloc::alloc ...
    
  Thread T2 (tid=12348) created by main thread at:
    #0 pthread_create ThreadSanitizer interceptor
    #1 std::sys::thread::Thread::new ...
```

The report identifies the conflicting memory accesses: a write at line 25 and a previous read at line 14, both targeting the same address 0x7f8a3c000d00 (the counter's value field), with no synchronization edge between them. ThreadSanitizer's vector clock analysis determined that the read and write are concurrent and unsynchronized, thus constituting a data race. The stack traces show the exact calling context, and the allocation stack trace identifies where the heap block was allocated. Note that ThreadSanitizer reports the first detected race and terminates; additional races may exist but remain unreported.

Fix the race by eliminating the lock-release-reacquire pattern. Modify the code to hold the lock across the entire read-modify-write sequence:

```rust
pub fn stress_test_fixed(iterations: u64) -> u64 {
    let counter = Arc::new(std::sync::Mutex::new(RacyCounter::new()));
    let mut handles = vec![];
    
    for _ in 0..4 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..iterations {
                let mut c = counter_clone.lock().unwrap();
                c.increment();
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    counter.lock().unwrap().get()
}
```

Rebuild with ThreadSanitizer and verify that the sanitizer reports no races. Run with increased iteration counts to stress-test: `stress_test_fixed(100000)` should always return exactly 400000. Measure the performance cost of sanitizer instrumentation by comparing runtimes with and without TSAN: expect 5-15x slowdown due to vector clock maintenance and shadow memory updates on every access.

Demonstrate AddressSanitizer detecting heap use-after-free bugs. Create a new test file `tests/use_after_free.rs`:

```rust
#[test]
fn test_use_after_free() {
    let mut vec = vec![1, 2, 3, 4, 5];
    let ptr = vec.as_mut_ptr();
    
    drop(vec);
    
    unsafe {
        *ptr = 42;
        println!("Wrote to freed memory: {}", *ptr);
    }
}
```

Enable AddressSanitizer with `export RUSTFLAGS="-Z sanitizer=address" && export ASAN_OPTIONS="detect_leaks=1:abort_on_error=1"`, then clean and rebuild: `cargo clean && cargo test --test use_after_free`. AddressSanitizer detects the illegal write and aborts with a detailed report:

```
ERROR: AddressSanitizer: heap-use-after-free on address 0x602000000010 at pc 0x55a8e7b2c3a1
WRITE of size 4 at 0x602000000010 thread T0
    #0 0x55a8e7b2c3a0 in use_after_free::test_use_after_free tests/use_after_free.rs:8
    #1 0x55a8e7b2c5f3 in use_after_free::test_use_after_free::{{closure}} ...
    
0x602000000010 is located 0 bytes inside of 20-byte region [0x602000000010,0x602000000024)
freed by thread T0 here:
    #0 0x55a8e7a2b567 in __rust_dealloc AddressSanitizer interceptor
    #1 0x55a8e7b2c2f1 in alloc::alloc::dealloc ...
    #2 0x55a8e7b2c265 in drop::Vec<i32> ...
    
previously allocated by thread T0 here:
    #0 0x55a8e7a2b3f7 in __rust_alloc AddressSanitizer interceptor
    #1 0x55a8e7b2c1a3 in alloc::alloc::alloc ...
```

The report precisely identifies the illegal write at address 0x602000000010, the instruction performing the write, the allocation and deallocation stack traces, and the size of the freed region. AddressSanitizer maintains a quarantine of recently-freed allocations to catch temporal errors, trading memory overhead for detection coverage. The shadow memory encoding uses a compressed representation where each 8-byte region of application memory maps to one shadow byte indicating validity state.

Construct a double-free test to verify temporal safety detection:

```rust
#[test]
fn test_double_free() {
    let layout = std::alloc::Layout::from_size_align(16, 8).unwrap();
    
    unsafe {
        let ptr = std::alloc::alloc(layout);
        std::alloc::dealloc(ptr, layout);
        std::alloc::dealloc(ptr, layout);
    }
}
```

Run with AddressSanitizer enabled: `cargo test --test use_after_free test_double_free`. ASAN detects the double-free and aborts immediately:

```
ERROR: AddressSanitizer: attempting double-free on 0x602000000010 in thread T0:
    #0 0x55a8e7a2b567 in __rust_dealloc AddressSanitizer interceptor
    #1 0x55a8e7b2d4a2 in std::alloc::dealloc ...
```

The sanitizer intercepted the second deallocation and recognized that the memory region was already freed, preventing heap metadata corruption that would otherwise cause allocator crashes or silent memory corruption.

Test LeakSanitizer's heap leak detection by deliberately leaking allocations. Create `tests/memory_leak.rs`:

```rust
#[test]
fn test_memory_leak() {
    let mut leaks = Vec::new();
    
    for i in 0..100 {
        let leaked = Box::new(vec![0u8; 1024]);
        let ptr = Box::into_raw(leaked);
        leaks.push(ptr);
        
        if i % 10 == 0 {
            unsafe {
                let _ = Box::from_raw(leaks.pop().unwrap());
            }
        }
    }
}
```

Run with LeakSanitizer enabled through AddressSanitizer: `cargo test --test memory_leak`. At process exit, LeakSanitizer scans all reachable memory starting from roots (stack, registers, global variables) and marks reachable allocations. Any heap allocation not marked is reported as a leak:

```
ERROR: LeakSanitizer: detected memory leaks

Direct leak of 92160 bytes in 90 objects allocated from:
    #0 0x55a8e7a2b3f7 in __rust_alloc AddressSanitizer interceptor
    #1 0x55a8e7b2e1a3 in alloc::alloc::alloc ...
    #2 0x55a8e7b2e265 in alloc::vec::Vec::new ...
    
SUMMARY: AddressSanitizer: 92160 bytes leaked in 90 allocations
```

LeakSanitizer accurately identifies the 90 leaked allocations (100 total minus 10 deallocated), summing to 92160 bytes (90 × 1024). This confirms that the sanitizer's reachability analysis correctly distinguished leaked memory from intentionally-persistent allocations.

Deploy Miri, Rust's interpreter-based undefined behavior detector, to catch errors that AddressSanitizer misses. Miri executes MIR with strict validity checking, detecting uninitialized memory reads, invalid pointer arithmetic, and violations of Rust's aliasing rules. Create a test that violates Stacked Borrows, Rust's formal aliasing model:

```rust
#[test]
fn test_aliasing_violation() {
    let mut data = 42;
    let r1 = &mut data;
    let ptr = r1 as *mut i32;
    let r2 = unsafe { &mut *ptr };
    
    *r1 = 1;
    *r2 = 2;
    
    assert_eq!(data, 2);
}
```

Run under Miri: `cargo +nightly miri test test_aliasing_violation`. Miri detects the aliasing violation:

```
error: Undefined Behavior: trying to reborrow for Unique at alloc1234, but parent tag <12> does not have appropriate permissions
  --> tests/aliasing.rs:6:27
   |
6  |     let r2 = unsafe { &mut *ptr };
   |                           ^^^^^ trying to reborrow for Unique at alloc1234, but parent tag <12> does not have appropriate permissions
```

Miri's Stacked Borrows model tracks a "borrow stack" for each memory location, pushing new borrows when references are created and popping when they are used. The code creates a mutable reference `r1`, then creates a second mutable reference `r2` through a raw pointer, violating Rust's aliasing guarantee that mutable references are exclusive. When `r1` is dereferenced again after `r2` was created, Miri detects that `r1`'s tag has been invalidated by the conflicting borrow.

Compare sanitizer coverage across multiple implementations of a lock-free queue to verify concurrency correctness. Implement a simple Michael-Scott two-lock queue with deliberate synchronization bugs:

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    data: Option<T>,
    next: AtomicPtr<Node<T>>,
}

pub struct LockFreeQueue<T> {
    head: AtomicPtr<Node<T>>,
    tail: AtomicPtr<Node<T>>,
}

impl<T> LockFreeQueue<T> {
    pub fn new() -> Self {
        let sentinel = Box::into_raw(Box::new(Node {
            data: None,
            next: AtomicPtr::new(ptr::null_mut()),
        }));
        
        LockFreeQueue {
            head: AtomicPtr::new(sentinel),
            tail: AtomicPtr::new(sentinel),
        }
    }
    
    pub fn enqueue(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data: Some(data),
            next: AtomicPtr::new(ptr::null_mut()),
        }));
        
        loop {
            let tail = self.tail.load(Ordering::Relaxed);
            let next = unsafe { (*tail).next.load(Ordering::Relaxed) };
            
            if next.is_null() {
                if unsafe { (*tail).next.compare_exchange(
                    ptr::null_mut(),
                    new_node,
                    Ordering::Release,
                    Ordering::Relaxed
                ).is_ok() } {
                    let _ = self.tail.compare_exchange(
                        tail,
                        new_node,
                        Ordering::Release,
                        Ordering::Relaxed
                    );
                    break;
                }
            } else {
                let _ = self.tail.compare_exchange(
                    tail,
                    next,
                    Ordering::Release,
                    Ordering::Relaxed
                );
            }
        }
    }
    
    pub fn dequeue(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Relaxed);
            let tail = self.tail.load(Ordering::Relaxed);
            let next = unsafe { (*head).next.load(Ordering::Acquire) };
            
            if head == tail {
                if next.is_null() {
                    return None;
                }
                let _ = self.tail.compare_exchange(
                    tail,
                    next,
                    Ordering::Release,
                    Ordering::Relaxed
                );
            } else {
                if next.is_null() {
                    continue;
                }
                
                let data = unsafe { (*next).data.take() };
                
                if self.head.compare_exchange(
                    head,
                    next,
                    Ordering::Release,
                    Ordering::Relaxed
                ).is_ok() {
                    unsafe { drop(Box::from_raw(head)); }
                    return data;
                }
            }
        }
    }
}
```

This implementation contains a subtle bug: the `head` load uses `Ordering::Relaxed` rather than `Ordering::Acquire`, potentially allowing the `data.take()` operation to be reordered before the visibility of the node being fully initialized. Run ThreadSanitizer stress tests with multiple producers and consumers to expose the race. Additionally, the deallocation of the old head node can race with concurrent enqueues reading `(*tail).next`, causing use-after-free. ThreadSanitizer will report these races after sufficient iteration count.

## Developer Cheat Sheet & Toolchain Checklist

**Compilation Artifact Inspection Commands:**

```bash
cargo expand                                    # Macro expansion and desugared HIR
cargo rustc -- --emit=mir -o target/lib.mir    # MIR intermediate representation
cargo rustc -- --emit=llvm-ir                   # Unoptimized LLVM IR
cargo rustc -- --emit=llvm-bc -o lib.bc        # LLVM bitcode for manual optimization
opt-18 -S -O3 lib.bc -o lib_opt.ll             # Run LLVM optimizer manually
cargo asm <crate>::<function>                   # Disassemble specific function
objdump -d -M intel target/release/lib         # Full disassembly with Intel syntax
```

**Performance Profiling with perf:**

```bash
perf stat -e cycles,instructions,cache-misses,branch-misses <cmd>
perf record -g -e cycles:u <cmd>               # Sample call stacks at CPU cycles
perf record -e cache-misses -g <cmd>           # Sample cache miss events
perf report --stdio --sort=dso,symbol          # Text-based profile report
perf annotate <function>                        # Source/assembly annotation with samples
cargo flamegraph                                # Generate interactive flame graph
```

**Sanitizer Configurations:**

```bash
# AddressSanitizer (heap corruption, use-after-free)
export RUSTFLAGS="-Z sanitizer=address"
export ASAN_OPTIONS="detect_leaks=1:abort_on_error=1:symbolize=1"

# ThreadSanitizer (data races, lock ordering)
export RUSTFLAGS="-Z sanitizer=thread"
export TSAN_OPTIONS="halt_on_error=1:history_size=7:second_deadlock_stack=1"

# MemorySanitizer (uninitialized reads, requires rebuilt std)
export RUSTFLAGS="-Z sanitizer=memory -Z build-std"
export MSAN_OPTIONS="symbolize=1:halt_on_error=1"

# LeakSanitizer standalone
export RUSTFLAGS="-Z sanitizer=leak"

# Miri undefined behavior detector
cargo +nightly miri test
cargo +nightly miri run
```

**Benchmarking Best Practices:**

```bash
cargo bench                                     # Run all benchmarks with Criterion
cargo bench --bench <name>                      # Run specific benchmark suite
cargo bench -- --save-baseline <name>           # Save baseline for comparison
cargo bench -- --baseline <name>                # Compare against saved baseline
RUSTFLAGS="-C target-cpu=native" cargo bench    # Enable native CPU optimization
```

**Compiler Optimization Flags:**

```bash
-C opt-level=3                                  # Maximum optimization
-C lto=fat                                      # Link-time optimization across all crates
-C codegen-units=1                              # Single codegen unit for better inlining
-C target-cpu=native                            # Use CPU-specific instructions (AVX, etc.)
-C llvm-args=-pass-remarks=loop-vectorize       # Emit vectorization diagnostics
```

**LLVM Optimization Pass Selection:**

```bash
opt-18 -O3 -S input.bc -o output.ll            # Standard -O3 pipeline
opt-18 -passes='mem2reg,instcombine,gvn,simplifycfg' -S input.bc
opt-18 -print-after-all -O3 input.bc 2>&1 | less    # Dump IR after each pass
```

**ThreadSanitizer Race Detection Checklist:**

1. Rebuild with `-Z sanitizer=thread` and clean intermediate artifacts
2. Run multithreaded stress tests with high iteration counts (10⁶–10⁷)
3. Check TSAN reports for "data race" or "lock-order-inversion" warnings
4. Verify synchronization: all shared mutable state protected by locks or atomics
5. Confirm ordering constraints: acquire-release pairs for cross-thread visibility

**AddressSanitizer Memory Safety Checklist:**

1. Enable with `-Z sanitizer=address` and `detect_leaks=1`
2. Run all tests including fuzzing campaigns if available
3. Verify no "heap-use-after-free", "heap-buffer-overflow", or "double-free" errors
4. Check LeakSanitizer summary for unreachable allocations
5. For false positives, use ASAN_OPTIONS suppressions or `#[no_mangle]` annotations

**Cache Profiling Diagnostic Protocol:**

1. Measure baseline: `perf stat -e L1-dcache-load-misses,LLC-load-misses <cmd>`
2. If LLC miss rate >10%, suspect working set exceeds cache capacity
3. Profile hotspots: `perf record -e cache-misses -g <cmd>` then `perf report`
4. Disassemble hotspot: `perf annotate <function>` to identify miss instructions
5. Apply locality optimizations: tiling, structure padding, prefetch hints
6. Re-measure and verify LLC miss rate reduction

**Microbenchmark Validation Criteria:**

- Runtime coefficient of variation <5% across runs
- Black-box inputs to prevent constant folding
- Sufficient iteration count to amortize loop overhead (>10³ iterations)
- Verify compiler did not eliminate computation via assembly inspection
- Compare multiple optimization levels to quantify transformation impact

**LLVM IR Verification Quick Reference:**

- `noalias` attribute: function parameters do not alias
- `dereferenceable(N)`: pointer valid for at least N bytes
- `align N`: pointer alignment guarantee
- `nsw`/`nuw`: no signed/unsigned wrap, enables overflow-based transforms
- `fast` floating-point flags: enable aggressive reassociation and contraction
- `!invariant.load`: load from immutable memory, hoistable out of loops

**Debugging Sanitizer False Positives:**

- ASAN false positive: verify allocation size matches access pattern
- TSAN false positive: check for correct acquire-release ordering, add annotations
- MSAN false positive: initialize padding bytes explicitly, use `memset` for aggregates
- Leak false positive: global/static allocations are intentional, suppress if needed
- Stacked Borrows violation in Miri: review raw pointer usage, ensure proper reborrowing

**Compiler Backend Selection for Cross-Validation:**

- Rustc LLVM 18 backend: default, most mature optimization pipeline
- GCC: compare code generation with `rustc -C linker=gcc -C link-arg=-fuse-ld=gold`
- Cranelift: fast compile times for debug builds via `cargo +nightly build -Z codegen-backend=cranelift`
- Compare disassembly across backends to identify backend-specific optimization bugs

This laboratory sequence establishes a reproducible methodology for verifying compiler correctness, optimization effectiveness, and runtime safety properties through systematic instrumentation and measurement. Mastery requires iterative practice: compile with multiple optimization levels, profile under representative workloads, inject deliberate bugs to test sanitizer coverage, and compare implementations across languages to build intuition for compiler transformation behavior. The toolchain commands and diagnostic protocols provided here form the foundation for continuous verification in production software engineering.
