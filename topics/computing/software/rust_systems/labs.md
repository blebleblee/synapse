# Operational Verification Labs: Rust Systems

## Objective & Toolchain Setup

Modern systems programming demands rigorous operational verification that extends far beyond simple unit tests and clippy lints. The Rust compiler provides memory safety guarantees at compile time through its ownership and borrow checker, but runtime verification remains essential for exposing performance bottlenecks, subtle concurrency bugs that evade static analysis, and unintended algorithmic complexity. This laboratory guide establishes a complete verification workflow using LLVM-based sanitizers, native debuggers, and performance profiling tools that operate directly on compiled machine code and runtime behavior.

The verification toolchain consists of several layers. At the foundation sits the Rust compiler itself, built atop LLVM infrastructure, which generates intermediate representations amenable to deep inspection. The standard Cargo build system integrates seamlessly with sanitizer instrumentation through compiler flags and target specifications. For interactive debugging, LLDB provides source-level symbolic debugging with full Rust type awareness through DWARF debugging symbols enriched with Rust-specific metadata. Performance analysis requires both sampling profilers like `perf` that operate via hardware performance counters and flamegraph generators that transform raw profiling data into visual call graphs. Memory error detection leverages AddressSanitizer's shadow memory instrumentation, while ThreadSanitizer employs vector clock algorithms to detect data races across concurrent execution paths.

Begin by ensuring a complete Rust toolchain installation via rustup, which manages not only the stable compiler but also auxiliary components like rust-src for standard library source inspection and llvm-tools-preview for advanced LLVM utilities. Install the system toolchain with `rustup toolchain install stable` and verify with `rustc --version` to confirm LLVM backend integration. Install LLDB through your distribution's package manager—on Ubuntu and Debian systems this requires `apt install lldb`, while macOS ships LLDB as part of Xcode command-line tools via `xcode-select --install`. For performance profiling, install `cargo-flamegraph` with `cargo install flamegraph`, which wraps `perf` on Linux and DTrace on macOS to generate SVG flamegraphs from sampled stack traces. Valgrind remains useful for certain memory analysis tasks despite Rust's safety guarantees, installable via `apt install valgrind` on Linux systems.

Configure a dedicated workspace for these exercises with `cargo new --lib rust-verification-lab`, establishing a library crate that allows direct control over compilation targets and facilitates sanitizer integration. The workspace will contain multiple modules, each demonstrating specific verification techniques with complete, runnable implementations that expose common systems programming pathologies deliberately constructed for pedagogical purposes.

## Exercise 1: AST, IR & Disassembly Analysis

Understanding how Rust source code transforms through the compilation pipeline provides essential insight into optimizer behavior, inlining decisions, and the machine-level consequences of high-level abstractions. The Rust compiler performs multiple transformations: first parsing source into an abstract syntax tree, then lowering to high-level intermediate representation (HIR), converting to mid-level IR (MIR) where borrow checking occurs, and finally translating to LLVM IR before machine code generation. Each stage exposes different optimization opportunities and potential performance characteristics that may contradict intuitive expectations about code performance.

Create a module `src/transform.rs` containing a simple but instructive example that demonstrates optimizer strength reduction and constant folding:

```rust
pub fn polynomial_eval(x: i64) -> i64 {
    x * x * x + 2 * x * x + 3 * x + 4
}

pub fn polynomial_horner(x: i64) -> i64 {
    ((x + 2) * x + 3) * x + 4
}

pub struct Point3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Point3D {
    pub fn magnitude(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    pub fn normalize(&mut self) {
        let mag = self.magnitude();
        self.x /= mag;
        self.y /= mag;
        self.z /= mag;
    }
}

pub fn sum_array(data: &[i32]) -> i32 {
    let mut sum = 0;
    for &value in data {
        sum += value;
    }
    sum
}

pub fn sum_array_iterator(data: &[i32]) -> i32 {
    data.iter().sum()
}
```

Expose the MIR with `cargo rustc --lib -- --emit=mir`, which writes textual MIR to `target/debug/deps/*.mir`. Open this file and locate the `polynomial_eval` function. The MIR reveals the sequence of temporary assignments, borrow checking annotations, and basic block structure before LLVM optimization. Search for patterns like `_temp = CheckedAdd` or `_temp = CheckedMul` that represent overflow-checked arithmetic operations. Notice how the borrow checker annotates lifetime regions and validates that no mutable aliases exist simultaneously with shared borrows.

Generate LLVM IR with `cargo rustc --lib --release -- --emit=llvm-ir`, producing `target/release/deps/*.ll` in human-readable LLVM assembly. The release profile enables full optimization, exposing the dramatic transformations LLVM applies. Open the `.ll` file and search for `@_ZN20rust_verification_lab9transform14polynomial_eval`. The mangled symbol name follows Rust's name mangling scheme, which LLDB and other tools automatically demangle. Examine the function body: in release builds with optimization level 3, LLVM often reduces `polynomial_eval` to a small number of multiply and add instructions, potentially fusing operations through instruction scheduling and recognizing opportunities for strength reduction. Compare this to `polynomial_horner`, which already expresses Horner's method explicitly. Depending on LLVM's analysis, both may compile to nearly identical code, demonstrating that idiomatic high-level expressions do not necessarily sacrifice performance.

For assembly-level inspection, generate native disassembly with `cargo rustc --lib --release -- --emit=asm`, creating `target/release/deps/*.s` containing platform-specific assembly. On x86_64, search for the `polynomial_eval` symbol and examine the instruction sequence. Release builds typically show tight instruction sequences using vector registers (`xmm` for scalar floating-point, `ymm` or `zmm` for vectorized operations), efficient addressing modes, and minimal register spilling. Count the number of `imul` (integer multiply) and `add` instructions to verify optimizer effectiveness.

Now examine the `Point3D::normalize` method in the LLVM IR. This function performs multiple floating-point operations and divides each coordinate by the magnitude. In unoptimized builds, each division appears as a separate `fdiv` instruction. In optimized builds, LLVM may recognize that the divisor is invariant across the three divisions and transform the code to compute the reciprocal once (`1.0 / mag`) followed by three multiplications (`self.x * reciprocal`), exploiting the fact that floating-point multiplication has lower latency than division on most microarchitectures. This optimization relies on reassociation and requires fast-math flags to relax strict IEEE 754 semantics, which Rust does not enable by default to preserve numerical correctness. To observe this transformation, rebuild with `RUSTFLAGS="-C target-cpu=native -C opt-level=3"` and compare the assembly.

For the array summation functions, examine both `sum_array` and `sum_array_iterator` in the LLVM IR. The explicit loop compiles to a basic block containing a phi node for the accumulator, a load from the slice pointer, an add instruction, and a branch back to the loop header. The iterator-based version using `data.iter().sum()` undergoes iterator fusion and inlining, ultimately producing identical or nearly identical machine code in release builds. This demonstrates Rust's zero-cost abstraction guarantee: high-level iterator combinators compile down to the same tight loops as hand-written index-based code. Verify this by comparing the assembly output for both functions side by side.

To interactively explore runtime behavior, compile with debug symbols using `cargo build` (debug profile includes symbols by default) and launch LLDB with `lldb target/debug/librust_verification_lab.dylib` on macOS or `lldb target/debug/librust_verification_lab.so` on Linux. Set a breakpoint on a specific function with `b rust_verification_lab::transform::polynomial_eval`, then manually invoke it by creating a test harness. Alternatively, create a small binary crate that depends on the library and exercises these functions. Use `disassemble --name rust_verification_lab::transform::polynomial_eval` within LLDB to view the disassembly with interleaved source lines. Step through instructions with `si` (step instruction) and inspect registers with `register read`. This direct machine-level observation confirms the transformations visible in static disassembly.

Understanding these compilation stages exposes how Rust's high-level safety and abstraction guarantees map to efficient machine code. The MIR reveals borrow checker mechanics, LLVM IR shows cross-function optimization and inlining decisions, and assembly confirms the final instruction-level performance characteristics. This layered inspection methodology allows systematic diagnosis of performance anomalies and verification that critical hot paths compile to expected machine code.

## Exercise 2: Cache Miss & Throughput Profiling

Performance analysis in systems programming requires understanding how memory access patterns interact with CPU cache hierarchy and how computational throughput depends on instruction-level parallelism and memory bandwidth. Modern processors feature multi-level caches with vastly different access latencies: L1 data cache hits complete in 3-4 cycles, L2 in 10-12 cycles, L3 in 40-75 cycles, while main memory access incurs 200+ cycle latencies. Data structure layout and access patterns determine whether algorithms remain cache-resident or suffer continuous cache misses that serialize execution and waste cycles waiting for memory subsystem responses.

Create a new module `src/cache_patterns.rs` implementing several data structures with deliberately contrasting memory layouts:

```rust
use std::time::Instant;

pub struct ArrayOfStructs {
    pub data: Vec<Particle>,
}

pub struct StructOfArrays {
    pub x: Vec<f64>,
    pub y: Vec<f64>,
    pub z: Vec<f64>,
    pub vx: Vec<f64>,
    pub vy: Vec<f64>,
    pub vz: Vec<f64>,
}

#[derive(Clone, Copy)]
pub struct Particle {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub vx: f64,
    pub vy: f64,
    pub vz: f64,
}

impl ArrayOfStructs {
    pub fn new(count: usize) -> Self {
        let data = (0..count)
            .map(|i| {
                let fi = i as f64;
                Particle {
                    x: fi * 0.1,
                    y: fi * 0.2,
                    z: fi * 0.3,
                    vx: fi * 0.01,
                    vy: fi * 0.02,
                    vz: fi * 0.03,
                }
            })
            .collect();
        ArrayOfStructs { data }
    }

    pub fn update_positions(&mut self, dt: f64) {
        for particle in &mut self.data {
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.z += particle.vz * dt;
        }
    }

    pub fn sum_kinetic_energy(&self) -> f64 {
        self.data
            .iter()
            .map(|p| {
                let v2 = p.vx * p.vx + p.vy * p.vy + p.vz * p.vz;
                0.5 * v2
            })
            .sum()
    }
}

impl StructOfArrays {
    pub fn new(count: usize) -> Self {
        let mut x = Vec::with_capacity(count);
        let mut y = Vec::with_capacity(count);
        let mut z = Vec::with_capacity(count);
        let mut vx = Vec::with_capacity(count);
        let mut vy = Vec::with_capacity(count);
        let mut vz = Vec::with_capacity(count);

        for i in 0..count {
            let fi = i as f64;
            x.push(fi * 0.1);
            y.push(fi * 0.2);
            z.push(fi * 0.3);
            vx.push(fi * 0.01);
            vy.push(fi * 0.02);
            vz.push(fi * 0.03);
        }

        StructOfArrays { x, y, z, vx, vy, vz }
    }

    pub fn update_positions(&mut self, dt: f64) {
        for i in 0..self.x.len() {
            self.x[i] += self.vx[i] * dt;
            self.y[i] += self.vy[i] * dt;
            self.z[i] += self.vz[i] * dt;
        }
    }

    pub fn sum_kinetic_energy(&self) -> f64 {
        let mut sum = 0.0;
        for i in 0..self.vx.len() {
            let v2 = self.vx[i] * self.vx[i] + self.vy[i] * self.vy[i] + self.vz[i] * self.vz[i];
            sum += 0.5 * v2;
        }
        sum
    }
}

pub fn benchmark_aos_vs_soa(particle_count: usize, iterations: usize) -> (u128, u128) {
    let mut aos = ArrayOfStructs::new(particle_count);
    let mut soa = StructOfArrays::new(particle_count);

    let dt = 0.01;

    let start_aos = Instant::now();
    for _ in 0..iterations {
        aos.update_positions(dt);
        std::hint::black_box(aos.sum_kinetic_energy());
    }
    let aos_duration = start_aos.elapsed().as_nanos();

    let start_soa = Instant::now();
    for _ in 0..iterations {
        soa.update_positions(dt);
        std::hint::black_box(soa.sum_kinetic_energy());
    }
    let soa_duration = start_soa.elapsed().as_nanos();

    (aos_duration, soa_duration)
}

#[derive(Clone)]
pub struct Matrix {
    pub data: Vec<f64>,
    pub rows: usize,
    pub cols: usize,
}

impl Matrix {
    pub fn new(rows: usize, cols: usize, init: f64) -> Self {
        Matrix {
            data: vec![init; rows * cols],
            rows,
            cols,
        }
    }

    pub fn get(&self, row: usize, col: usize) -> f64 {
        self.data[row * self.cols + col]
    }

    pub fn set(&mut self, row: usize, col: usize, value: f64) {
        self.data[row * self.cols + col] = value;
    }

    pub fn multiply_row_major(&self, other: &Matrix) -> Matrix {
        assert_eq!(self.cols, other.rows);
        let mut result = Matrix::new(self.rows, other.cols, 0.0);

        for i in 0..self.rows {
            for j in 0..other.cols {
                let mut sum = 0.0;
                for k in 0..self.cols {
                    sum += self.get(i, k) * other.get(k, j);
                }
                result.set(i, j, sum);
            }
        }
        result
    }

    pub fn multiply_cache_blocked(&self, other: &Matrix, block_size: usize) -> Matrix {
        assert_eq!(self.cols, other.rows);
        let mut result = Matrix::new(self.rows, other.cols, 0.0);

        for i_block in (0..self.rows).step_by(block_size) {
            for j_block in (0..other.cols).step_by(block_size) {
                for k_block in (0..self.cols).step_by(block_size) {
                    let i_end = (i_block + block_size).min(self.rows);
                    let j_end = (j_block + block_size).min(other.cols);
                    let k_end = (k_block + block_size).min(self.cols);

                    for i in i_block..i_end {
                        for j in j_block..j_end {
                            let mut sum = result.get(i, j);
                            for k in k_block..k_end {
                                sum += self.get(i, k) * other.get(k, j);
                            }
                            result.set(i, j, sum);
                        }
                    }
                }
            }
        }
        result
    }
}

pub fn benchmark_matrix_multiply(size: usize, block_size: usize) -> (u128, u128) {
    let a = Matrix::new(size, size, 1.5);
    let b = Matrix::new(size, size, 2.5);

    let start_naive = Instant::now();
    let _ = std::hint::black_box(a.multiply_row_major(&b));
    let naive_duration = start_naive.elapsed().as_nanos();

    let start_blocked = Instant::now();
    let _ = std::hint::black_box(a.multiply_cache_blocked(&b, block_size));
    let blocked_duration = start_blocked.elapsed().as_nanos();

    (naive_duration, blocked_duration)
}
```

Create a benchmark harness `benches/cache_benchmark.rs` to exercise these patterns with sufficient data volume to expose cache effects:

```rust
use rust_verification_lab::cache_patterns::{
    benchmark_aos_vs_soa, benchmark_matrix_multiply,
};

fn main() {
    println!("=== Array of Structs vs Struct of Arrays ===");
    let particle_counts = [10_000, 100_000, 1_000_000];
    for &count in &particle_counts {
        let (aos_ns, soa_ns) = benchmark_aos_vs_soa(count, 100);
        let aos_ms = aos_ns as f64 / 1_000_000.0;
        let soa_ms = soa_ns as f64 / 1_000_000.0;
        let speedup = aos_ms / soa_ms;
        println!(
            "Particles: {:<8} | AoS: {:.2}ms | SoA: {:.2}ms | Speedup: {:.2}x",
            count, aos_ms, soa_ms, speedup
        );
    }

    println!("\n=== Matrix Multiplication Cache Blocking ===");
    let matrix_sizes = [128, 256, 512];
    let block_sizes = [16, 32, 64];
    for &size in &matrix_sizes {
        for &block_size in &block_sizes {
            let (naive_ns, blocked_ns) = benchmark_matrix_multiply(size, block_size);
            let naive_ms = naive_ns as f64 / 1_000_000.0;
            let blocked_ms = blocked_ns as f64 / 1_000_000.0;
            let speedup = naive_ms / blocked_ms;
            println!(
                "Size: {}x{} | Block: {:<2} | Naive: {:.2}ms | Blocked: {:.2}ms | Speedup: {:.2}x",
                size, size, block_size, naive_ms, blocked_ms, speedup
            );
        }
    }
}
```

Register the benchmark in `Cargo.toml`:

```toml
[[bench]]
name = "cache_benchmark"
harness = false
```

Execute the benchmark with `cargo build --release --benches && ./target/release/cache_benchmark`. Observe the performance differential between array-of-structs and struct-of-arrays layouts. The AoS layout stores each particle as a contiguous 48-byte structure (six f64 fields), meaning that accessing velocity components during position updates requires loading entire cache lines containing interleaved position and velocity data. When iterating through particles, each cache line fetch brings in data for only one or two particles, and only a subset of that data gets used in any single operation. The SoA layout segregates position and velocity arrays, ensuring that iterating through positions fetches cache lines containing only position data with no wasted bandwidth on unused velocity fields. Typical speedups range from 1.5x to 3x depending on dataset size and cache hierarchy.

For deeper cache analysis, profile with `perf` hardware performance counters on Linux. Build the benchmark in release mode and execute under `perf stat` with cache-specific events: `perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses ./target/release/cache_benchmark`. The output reports absolute counts and miss rates for each cache level. Compare L1 data cache miss rates between AoS and SoA implementations: the struct-of-arrays pattern should exhibit significantly lower L1 miss rates due to better spatial locality. Last-level cache (LLC) misses indicate memory bandwidth saturation and are critical for large datasets that exceed L3 capacity.

Generate flamegraphs to visualize CPU time distribution with `cargo flamegraph --bench cache_benchmark`. This requires root privileges or `perf_event_paranoid` configuration on Linux: `echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid`. The flamegraph SVG shows hierarchical call stacks with horizontal bar width proportional to CPU time consumed. Open `flamegraph.svg` in a browser and identify the hottest code paths. In the matrix multiplication benchmark, the naive row-major implementation exhibits wide bars in the innermost loop where cache misses occur, while the cache-blocked version distributes time more evenly across blocking loops, indicating better cache utilization and memory-level parallelism.

Examine the matrix multiplication implementations in detail. The naive triple-nested loop accesses matrix B in column-major order (incrementing row index while column index remains fixed), causing each access to the second matrix to fetch a new cache line since row-major storage places consecutive elements of the same row contiguously. With typical cache line sizes of 64 bytes (eight f64 values), accessing a column walks through memory in 8-element strides, wasting 7/8 of each fetched cache line. Cache blocking partitions the computation into sub-matrices that fit within L1 or L2 cache, transforming the access pattern into multiple passes over smaller blocks that remain cache-resident. Optimal block size depends on cache size: for a 32KB L1 data cache, a 32x32 block of f64 values consumes 8KB per matrix, leaving room for three blocks (two input matrices and one output submatrix) plus working space.

Profile memory bandwidth consumption by running the benchmark under `perf stat -e cycles,instructions,mem_load_retired.l1_miss,mem_load_retired.l3_miss`. The instructions-per-cycle (IPC) metric reveals execution efficiency: values below 1.0 indicate stalls due to memory latency or dependency chains, while values approaching processor issue width (4-6 for modern x86_64) suggest compute-bound execution. Matrix multiplication should achieve higher IPC in the blocked version due to sustained cache residency allowing the processor to overlap arithmetic operations with memory prefetching.

To observe cache line effects at finer granularity, use `perf record --call-graph dwarf ./target/release/cache_benchmark` followed by `perf report` for interactive exploration. This captures stack traces at sampling intervals and attributes cache misses to specific source lines. Navigate through the call hierarchy to identify functions and loops with high miss rates. The `--call-graph dwarf` option ensures complete stack unwinding through Rust's zero-cost abstractions and inlined functions.

These cache profiling techniques expose how algorithmic choices and data layout decisions directly impact hardware utilization. Systems programming demands awareness of cache line boundaries, false sharing in concurrent code, prefetch behavior, and memory bandwidth limits. Rust's zero-cost abstractions compile to efficient machine code, but achieving optimal performance requires deliberate attention to memory access patterns that respect cache hierarchy mechanics.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency correctness extends beyond Rust's compile-time data race prevention. While the type system enforces Send and Sync trait bounds to prevent concurrent access to non-thread-safe types, subtle race conditions emerge in unsafe code blocks, incorrect synchronization primitive usage, lock-free algorithms with memory ordering bugs, and external FFI boundaries. ThreadSanitizer dynamically instruments memory accesses to detect races through happens-before relationship tracking, while LeakSanitizer identifies memory leaks that escape Rust's RAII guarantees through reference cycles, forgotten drop implementations, or manual memory management in unsafe code.

Create a module `src/concurrency_bugs.rs` with deliberately flawed concurrent implementations:

```rust
use std::sync::{Arc, Mutex, RwLock};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;
use std::time::Duration;

pub struct LeakyCache {
    data: Mutex<Vec<Box<[u8; 1024]>>>,
}

impl LeakyCache {
    pub fn new() -> Self {
        LeakyCache {
            data: Mutex::new(Vec::new()),
        }
    }

    pub fn insert(&self, item: Box<[u8; 1024]>) {
        let mut data = self.data.lock().unwrap();
        data.push(item);
    }

    pub fn clear_some(&self) {
        let mut data = self.data.lock().unwrap();
        if data.len() > 100 {
            data.drain(0..50);
        }
    }
}

pub fn stress_test_leaky_cache(iterations: usize, threads: usize) {
    let cache = Arc::new(LeakyCache::new());
    let mut handles = vec![];

    for _ in 0..threads {
        let cache_clone = Arc::clone(&cache);
        let handle = thread::spawn(move || {
            for _ in 0..iterations {
                let item = Box::new([0u8; 1024]);
                cache_clone.insert(item);
                if rand::random::<f64>() < 0.1 {
                    cache_clone.clear_some();
                }
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }
}

pub struct UnsafeCounter {
    value: AtomicUsize,
    update_count: usize,
}

impl UnsafeCounter {
    pub fn new() -> Self {
        UnsafeCounter {
            value: AtomicUsize::new(0),
            update_count: 0,
        }
    }

    pub fn increment(&mut self) {
        self.value.fetch_add(1, Ordering::Relaxed);
        self.update_count += 1;
    }

    pub fn get_value(&self) -> usize {
        self.value.load(Ordering::Relaxed)
    }

    pub fn get_update_count(&self) -> usize {
        self.update_count
    }
}

pub fn race_unsafe_counter(iterations: usize, threads: usize) -> (usize, usize) {
    let counter = Arc::new(Mutex::new(UnsafeCounter::new()));
    let mut handles = vec![];

    for _ in 0..threads {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..iterations {
                let mut c = counter_clone.lock().unwrap();
                c.increment();
                drop(c);
                thread::sleep(Duration::from_micros(1));
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let final_counter = counter.lock().unwrap();
    (final_counter.get_value(), final_counter.get_update_count())
}

pub struct SharedState {
    data: RwLock<Vec<i32>>,
    cache: Mutex<Vec<i32>>,
}

impl SharedState {
    pub fn new() -> Self {
        SharedState {
            data: RwLock::new(vec![]),
            cache: Mutex::new(vec![]),
        }
    }

    pub fn update_with_deadlock_risk(&self, value: i32) {
        let mut data = self.data.write().unwrap();
        data.push(value);
        
        let mut cache = self.cache.lock().unwrap();
        cache.push(value);
        
        drop(cache);
        drop(data);
    }

    pub fn read_with_deadlock_risk(&self) -> (usize, usize) {
        let cache = self.cache.lock().unwrap();
        let cache_len = cache.len();
        drop(cache);
        
        let data = self.data.read().unwrap();
        let data_len = data.len();
        drop(data);
        
        (data_len, cache_len)
    }

    pub fn concurrent_update_and_read(&self) {
        let mut handles = vec![];
        
        for i in 0..4 {
            let state = Arc::new(self);
            let handle = thread::spawn(move || {
                if i % 2 == 0 {
                    state.update_with_deadlock_risk(i);
                } else {
                    let _ = state.read_with_deadlock_risk();
                }
            });
            handles.push(handle);
        }
        
        for handle in handles {
            let _ = handle.join();
        }
    }
}

pub struct LockFreeStack<T> {
    head: AtomicUsize,
    _phantom: std::marker::PhantomData<T>,
}

struct Node<T> {
    data: T,
    next: usize,
}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        LockFreeStack {
            head: AtomicUsize::new(0),
            _phantom: std::marker::PhantomData,
        }
    }

    pub unsafe fn push(&self, data: T) {
        let node = Box::into_raw(Box::new(Node { data, next: 0 })) as usize;
        loop {
            let old_head = self.head.load(Ordering::Relaxed);
            (*(node as *mut Node<T>)).next = old_head;
            
            if self.head.compare_exchange_weak(
                old_head,
                node,
                Ordering::Release,
                Ordering::Relaxed
            ).is_ok() {
                break;
            }
        }
    }

    pub unsafe fn pop(&self) -> Option<T> {
        loop {
            let head_ptr = self.head.load(Ordering::Relaxed);
            if head_ptr == 0 {
                return None;
            }
            
            let node = &*(head_ptr as *const Node<T>);
            let next = node.next;
            
            if self.head.compare_exchange_weak(
                head_ptr,
                next,
                Ordering::Acquire,
                Ordering::Relaxed
            ).is_ok() {
                let boxed = Box::from_raw(head_ptr as *mut Node<T>);
                return Some(boxed.data);
            }
        }
    }
}

pub fn race_lock_free_stack(iterations: usize, threads: usize) {
    let stack = Arc::new(LockFreeStack::new());
    let mut handles = vec![];

    for thread_id in 0..threads {
        let stack_clone = Arc::clone(&stack);
        let handle = thread::spawn(move || {
            unsafe {
                for i in 0..iterations {
                    stack_clone.push(thread_id * 10000 + i);
                    if i % 2 == 0 {
                        let _ = stack_clone.pop();
                    }
                }
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }
}
```

Add the `rand` dependency to `Cargo.toml`:

```toml
[dependencies]
rand = "0.8"
```

Build with ThreadSanitizer instrumentation by setting `RUSTFLAGS` environment variable: `RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu`. ThreadSanitizer requires nightly Rust and specific target triple specification. Switch to nightly with `rustup default nightly` and add the target with `rustup target add x86_64-unknown-linux-gnu`. Create a test harness `tests/concurrency_test.rs`:

```rust
use rust_verification_lab::concurrency_bugs::{
    stress_test_leaky_cache, race_unsafe_counter, race_lock_free_stack,
};

#[test]
fn test_leaky_cache_stress() {
    stress_test_leaky_cache(1000, 4);
}

#[test]
fn test_unsafe_counter_race() {
    let (value, updates) = race_unsafe_counter(100, 8);
    println!("Final value: {}, Total updates: {}", value, updates);
}

#[test]
fn test_lock_free_stack_race() {
    race_lock_free_stack(500, 8);
}
```

Execute ThreadSanitizer instrumented tests with `RUSTFLAGS="-Z sanitizer=thread" cargo test --target x86_64-unknown-linux-gnu`. ThreadSanitizer output appears in stderr when races are detected, reporting the conflicting memory accesses with stack traces showing the exact source locations of racing reads and writes. Examine the report for `UnsafeCounter::increment`: despite mutex protection for the counter instance, the `update_count` field is a plain usize without atomic synchronization, creating a data race when multiple threads call `increment` on the same instance. The race manifests as missing updates to `update_count` because non-atomic reads and writes can be torn (partial writes visible to readers) or reordered by the compiler and CPU.

The lock-free stack implementation contains a classic ABA problem: between loading the head pointer and performing the compare-exchange, another thread may pop the node, free it, allocate a new node that reuses the same address, and push it back onto the stack. The compare-exchange succeeds incorrectly because the pointer value matches, but the node identity has changed. ThreadSanitizer detects this as racing accesses to the same memory location without proper synchronization, though the full ABA pathology requires careful inspection of allocation patterns. Correct lock-free data structures require hazard pointers, epoch-based reclamation, or other memory reclamation schemes that ThreadSanitizer helps validate but does not automatically solve.

For memory leak detection, build with LeakSanitizer enabled: `RUSTFLAGS="-Z sanitizer=leak" cargo test --target x86_64-unknown-linux-gnu`. LeakSanitizer reports allocations that remain reachable at program termination but are not properly freed. The `LeakyCache` implementation continuously grows the internal vector without bounds, accumulating heap allocations that persist even after `clear_some` removes only a fraction of entries. While Rust's RAII ensures that drop occurs when the Arc reference count reaches zero, unbounded growth within a long-lived structure constitutes a memory leak from the application perspective. LeakSanitizer output lists allocation stack traces and byte counts for leaked memory regions.

To expose subtler leaks, introduce reference cycles using `Rc` and `RefCell`:

```rust
use std::rc::Rc;
use std::cell::RefCell;

pub struct CyclicNode {
    value: i32,
    next: Option<Rc<RefCell<CyclicNode>>>,
}

impl CyclicNode {
    pub fn new(value: i32) -> Rc<RefCell<Self>> {
        Rc::new(RefCell::new(CyclicNode { value, next: None }))
    }
}

pub fn create_reference_cycle() {
    let node1 = CyclicNode::new(1);
    let node2 = CyclicNode::new(2);
    
    node1.borrow_mut().next = Some(Rc::clone(&node2));
    node2.borrow_mut().next = Some(Rc::clone(&node1));
}
```

Add a test for this cycle: `#[test] fn test_reference_cycle() { create_reference_cycle(); }`. LeakSanitizer reports the leaked cycle because neither `node1` nor `node2` ever reaches a reference count of zero due to mutual references. Rust's standard library provides `Weak` pointers to break such cycles: one direction holds a strong `Rc` while the reverse direction uses `Weak`, allowing cleanup when the strong reference count drops to zero.

Combine sanitizers with `perf` for comprehensive race and performance analysis. Profile ThreadSanitizer instrumented code with `perf record -g ./target/x86_64-unknown-linux-gnu/debug/concurrency_test`, then examine the report with `perf report`. ThreadSanitizer overhead is substantial (5-15x slowdown), but the instrumented execution exposes timing-sensitive races that vanish in optimized builds due to altered scheduling.

Validate synchronization primitive usage with assertions and property-based testing. For the lock-free stack, implement a sequential specification and compare concurrent execution results against it using a model checker or randomized testing framework like `loom`, which systematically explores thread interleavings:

```toml
[dev-dependencies]
loom = "0.7"
```

Write a loom-based test in `tests/loom_test.rs`:

```rust
#[cfg(loom)]
use loom::sync::atomic::{AtomicUsize, Ordering};
#[cfg(loom)]
use loom::thread;

#[cfg(loom)]
#[test]
fn loom_lock_free_stack() {
    loom::model(|| {
        let stack = loom::sync::Arc::new(AtomicUsize::new(0));
        
        let stack_clone = stack.clone();
        let t1 = thread::spawn(move || {
            stack_clone.store(1, Ordering::SeqCst);
        });
        
        let stack_clone = stack.clone();
        let t2 = thread::spawn(move || {
            stack_clone.store(2, Ordering::SeqCst);
        });
        
        t1.join().unwrap();
        t2.join().unwrap();
        
        let final_val = stack.load(Ordering::SeqCst);
        assert!(final_val == 1 || final_val == 2);
    });
}
```

Run loom tests with `cargo test --test loom_test --features loom`. Loom exhaustively tests all possible interleavings and memory orderings, detecting races and deadlocks that probabilistic testing might miss. Extend this approach to the full lock-free stack implementation by instrumenting the unsafe code with loom's atomic primitives and thread APIs.

These sanitizer and model checking techniques expose concurrency bugs that evade Rust's type system. While safe Rust prevents data races through Send/Sync enforcement and borrow checking, unsafe code and external synchronization patterns require dynamic verification. Combining ThreadSanitizer for deployed code profiling, LeakSanitizer for memory hygiene, and loom for algorithmic correctness creates a comprehensive concurrency verification strategy.

## Developer Cheat Sheet & Toolchain Checklist

This reference consolidates essential commands and diagnostic procedures for rapid troubleshooting and verification workflows. Memorizing these patterns enables immediate investigation when encountering performance anomalies, memory errors, or concurrency failures.

**Compilation & IR Inspection:**
- Generate MIR: `cargo rustc --lib -- --emit=mir`
- Generate LLVM IR: `cargo rustc --lib --release -- --emit=llvm-ir`
- Generate assembly: `cargo rustc --lib --release -- --emit=asm`
- View expanded macros: `cargo expand --lib` (requires `cargo install cargo-expand`)
- Check without building: `cargo check --all-targets`

**Optimization Control:**
- Set optimization level: `RUSTFLAGS="-C opt-level=3" cargo build --release`
- Enable native CPU features: `RUSTFLAGS="-C target-cpu=native" cargo build --release`
- Disable overflow checks: `RUSTFLAGS="-C overflow-checks=off" cargo build --release`
- Link-time optimization: Add `lto = true` to `[profile.release]` in `Cargo.toml`

**Debugging:**
- Launch LLDB: `lldb target/debug/binary_name`
- Set breakpoint: `b rust_crate::module::function`
- Run with arguments: `r arg1 arg2`
- Step instruction: `si`, step over: `n`, continue: `c`
- Print variable: `p variable_name`, print with format: `p/x variable_name`
- Disassemble current function: `disassemble`, specific function: `disassemble --name function_name`
- Examine registers: `register read`, specific register: `register read rax`
- Backtrace: `bt`, frame selection: `frame select 3`

**Sanitizer Builds:**
- AddressSanitizer: `RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu`
- ThreadSanitizer: `RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu`
- LeakSanitizer: `RUSTFLAGS="-Z sanitizer=leak" cargo test --target x86_64-unknown-linux-gnu`
- MemorySanitizer: `RUSTFLAGS="-Z sanitizer=memory" cargo build --target x86_64-unknown-linux-gnu`
- UndefinedBehaviorSanitizer: `RUSTFLAGS="-Z sanitizer=undefined" cargo build`

**Performance Profiling (Linux):**
- Flamegraph generation: `cargo flamegraph --release -- benchmark_args`
- Hardware counters: `perf stat -e cycles,instructions,cache-misses cargo bench`
- Cache analysis: `perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-misses command`
- Record samples: `perf record -g --call-graph dwarf cargo bench`
- View report: `perf report --stdio` or interactive: `perf report`
- Annotate source: `perf annotate function_name`

**Memory Profiling:**
- Valgrind memcheck: `valgrind --leak-check=full --show-leak-kinds=all target/debug/binary`
- Cachegrind simulation: `valgrind --tool=cachegrind target/debug/binary`
- Massif heap profiler: `valgrind --tool=massif target/debug/binary`
- View massif output: `ms_print massif.out.<pid>`

**Testing & Benchmarking:**
- Run tests: `cargo test`, single test: `cargo test test_name`
- Show output: `cargo test -- --nocapture`
- Benchmark: `cargo bench`, specific bench: `cargo bench bench_name`
- Criterion benchmarks: Add `criterion = "0.5"` dependency, run with `cargo bench`

**Toolchain Management:**
- Install nightly: `rustup toolchain install nightly`
- Set default: `rustup default nightly`
- Install component: `rustup component add rust-src llvm-tools-preview`
- Add target: `rustup target add x86_64-unknown-linux-gnu`
- Check installed targets: `rustup target list --installed`

**Build Configuration Patterns:**

For `Cargo.toml` release profile optimization:
```toml
[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
strip = true
```

For debug profile with symbols:
```toml
[profile.dev]
opt-level = 0
debug = true
```

For benchmarking profile:
```toml
[profile.bench]
inherits = "release"
debug = true
```

**Common Pitfalls & Solutions:**

- *Performance regression after refactor:* Check LLVM IR with `--emit=llvm-ir` to verify inlining occurred. Functions exceeding ~50 lines may not inline without `#[inline]` attribute.
- *Unexpected allocations:* Profile with `perf record -e syscalls:sys_enter_mmap` to trace heap allocations. Use `#[inline]` on small generic functions to enable monomorphization optimizations.
- *Cache thrashing:* Run `perf stat -e cache-references,cache-misses` to measure miss rate. Restructure data with struct-of-arrays or padding to cache line boundaries (64 bytes).
- *False sharing:* Add `#[repr(align(64))]` to hot structures accessed by multiple threads. Verify with `perf c2c record` and `perf c2c report` (cache-to-cache snooping analysis).
- *Sanitizer false positives:* ThreadSanitizer may report races in external C libraries. Suppress with `TSAN_OPTIONS="suppressions=tsan_suppressions.txt"` and create suppression file.
- *Memory ordering confusion:* Use `Ordering::SeqCst` initially for correctness, profile with `perf stat -e cpu/event=0xc4,umask=0x01/`, then relax to `Acquire/Release` only when proven safe.

**Pre-Deployment Checklist:**
1. Run `cargo clippy -- -D warnings` to enforce lint compliance
2. Execute `cargo test --release` to verify optimized builds pass tests
3. Profile with `perf stat -d` to collect detailed hardware metrics
4. Generate flamegraph: `cargo flamegraph --release` and inspect for unexpected hot spots
5. Run ThreadSanitizer build: `RUSTFLAGS="-Z sanitizer=thread" cargo test`
6. Check binary size: `ls -lh target/release/binary`, consider `strip` if excessive
7. Validate no debug symbols in release: `objdump -h target/release/binary | grep debug`
8. Benchmark against performance baseline: `cargo bench -- --save-baseline main`

This operational verification methodology ensures that Rust systems code not only compiles safely but executes efficiently under production workloads. The layered approach—from IR inspection through sanitizer validation to hardware performance profiling—exposes both correctness bugs that escape static analysis and performance characteristics invisible in microbenchmarks. Mastery of these tools transforms systems programming from trial-and-error debugging into systematic, evidence-based engineering.
