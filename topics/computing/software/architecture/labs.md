# Operational Verification Labs: Architecture

## Objective & Toolchain Setup

Software architecture becomes tangible through compiler transformations, memory layout decisions, and runtime execution profiles. This laboratory sequence moves beyond abstract diagrams to investigate how architectural choices manifest in concrete machine behavior: abstract syntax trees that determine compilation boundaries, intermediate representations that expose optimization opportunities, cache miss patterns that reveal data structure efficiency, and concurrency bugs that emerge from inadequate synchronization primitives. Each exercise employs production-grade instrumentation to measure the gap between design intent and physical execution.

Modern toolchains provide deep observability into architectural decisions. The Rust compiler exposes its internal representation through `-Z` flags and MIR (Mid-level Intermediate Representation) dumps, allowing engineers to witness how high-level abstractions decompose into control flow graphs and lifetime annotations. LLVM's intermediate representation reveals vectorization decisions, inlining boundaries, and register allocation strategies. Disassemblers like `objdump` and debuggers like LLDB expose the final machine code, showing how architectural patterns translate to CPU instructions, memory access patterns, and branch prediction behavior.

Performance profilers bridge the gap between algorithmic complexity and hardware reality. Cache simulators like Cachegrind expose the cost of pointer chasing and cache line conflicts. CPU profilers like `perf` and `cargo-flamegraph` reveal hotspots where architectural decisions concentrate execution time. Sanitizers detect memory corruption, data races, and undefined behavior that emerge when architectural invariants are violated at runtime. Together, these tools form a verification pipeline that validates architectural decisions through empirical measurement rather than theoretical reasoning.

Begin by establishing the complete diagnostic toolchain. Install the Rust ecosystem through `rustup`, ensuring you have the nightly compiler for unstable introspection features. Install LLVM's toolchain for cross-language analysis, including `clang`, `llvm-dis`, and `llc`. Install GDB or LLDB for assembly-level debugging, Valgrind for memory profiling, and `perf` for hardware counter instrumentation. On Linux, enable kernel symbols with `sudo sysctl kernel.perf_event_paranoid=1` to access precise event sampling. Install `cargo-flamegraph` for flame graph generation and `cargo-asm` for targeted disassembly. Verify the installation by compiling a minimal Rust program with debug symbols enabled through `cargo build`, then inspect the binary with `objdump -d target/debug/program` to confirm symbol resolution and disassembly output.

The exercises progress from static analysis to dynamic profiling. The first exercise dissects compiler transformations, examining how architectural abstractions decompose through successive lowering stages from source code to machine instructions. The second exercise measures cache behavior and throughput, revealing how memory layout and access patterns interact with CPU microarchitecture. The third exercise stress-tests concurrent architectures, exposing race conditions, deadlocks, and memory leaks that violate synchronization contracts. Each exercise includes complete code, exact commands, and specific metrics to observe, eliminating ambiguity about verification procedures.

## Exercise 1: AST, IR & Disassembly Analysis

Architecture begins as abstract structures in source code—trait hierarchies, generic algorithms, layered abstractions—but ultimately compiles down to a linear sequence of machine instructions executing on physical hardware. The compiler's transformation pipeline reveals how architectural decisions propagate through successive lowering stages: parsing into abstract syntax trees, type checking and borrow analysis, translation to mid-level intermediate representation, optimization passes over LLVM IR, register allocation, and finally code generation. Each stage makes explicit what was implicit in the source, exposing optimization opportunities and performance bottlenecks. By instrumenting this pipeline, engineers can verify that architectural patterns yield the expected machine code without unexpected overhead from abstraction penalties, vtable dispatches, or missed optimizations.

Consider a polymorphic architecture built on trait objects versus static dispatch through monomorphization. The choice between `&dyn Trait` and generic `impl Trait` fundamentally alters the generated code: dynamic dispatch introduces vtable indirection and prevents inlining across trait boundaries, while static dispatch enables complete specialization at compile time but increases code size through template instantiation. This exercise makes these tradeoffs concrete by compiling identical logic under both dispatch strategies, then comparing the resulting intermediate representations and assembly code to measure instruction count, memory indirection, and branch prediction impact.

Create a new Rust project with `cargo new arch_analysis && cd arch_analysis`. Implement a trait-based architecture that processes data through a pipeline of transformations. The trait defines a single method that applies a transformation, and two concrete implementations provide different transformation logic. This mimics real architectural patterns where interfaces abstract over multiple implementations, such as storage backends, serialization formats, or compression algorithms.

```rust
// src/lib.rs
pub trait Processor {
    fn process(&self, data: &[u32]) -> Vec<u32>;
}

pub struct Doubler;
impl Processor for Doubler {
    fn process(&self, data: &[u32]) -> Vec<u32> {
        data.iter().map(|&x| x * 2).collect()
    }
}

pub struct Incrementer;
impl Processor for Incrementer {
    fn process(&self, data: &[u32]) -> Vec<u32> {
        data.iter().map(|&x| x + 1).collect()
    }
}

// Dynamic dispatch version using trait objects
pub fn process_dynamic(processors: &[&dyn Processor], data: &[u32]) -> Vec<u32> {
    let mut result = data.to_vec();
    for processor in processors {
        result = processor.process(&result);
    }
    result
}

// Static dispatch version using generics and monomorphization
pub fn process_static<P1: Processor, P2: Processor>(
    p1: &P1,
    p2: &P2,
    data: &[u32],
) -> Vec<u32> {
    let intermediate = p1.process(data);
    p2.process(&intermediate)
}

// Benchmark driver to prevent dead code elimination
pub fn run_dynamic_pipeline(data: &[u32]) -> Vec<u32> {
    let processors: [&dyn Processor; 2] = [&Doubler, &Incrementer];
    process_dynamic(&processors, data)
}

pub fn run_static_pipeline(data: &[u32]) -> Vec<u32> {
    process_static(&Doubler, &Incrementer, data)
}
```

Compile this code with optimization disabled to preserve the architectural structure without inlining or specialization collapsing the abstraction layers. Run `cargo rustc --lib --release -- --emit=mir -Z dump-mir=all` to generate MIR dumps for every compilation stage. The MIR output appears in the `target/release/deps/` directory with `.mir` extensions. Open the MIR file and locate the `process_dynamic` and `process_static` functions. In the dynamic version, observe the vtable lookup represented as an indirect call through a function pointer: the MIR will show a `Call` terminator where the callee is loaded from a projected field of the trait object fat pointer. In the static version, the call sites are direct, referencing the concrete `Doubler::process` and `Incrementer::process` methods without indirection. This represents the fundamental architectural difference: dynamic dispatch trades runtime flexibility for a mandatory memory load and indirect branch on every trait method invocation.

Examine the LLVM intermediate representation to see optimization opportunities after the initial lowering. Run `cargo rustc --lib --release -- --emit=llvm-ir` to generate LLVM IR in `target/release/deps/*.ll`. Open this file and search for the mangled function names corresponding to `process_dynamic` and `process_static`. The LLVM IR for the static dispatch version will show direct calls to fully specialized functions, enabling aggressive inlining: the optimizer can inline the entire pipeline into a single function body, eliminating call overhead and enabling cross-function optimizations like vectorization and loop fusion. The dynamic dispatch version shows `call` instructions through function pointers loaded from memory, marked with attributes that prevent inlining because the target is unknown at compile time. The optimizer cannot see through the vtable indirection, so each processor invocation remains a separate function call with parameter marshaling overhead and register spilling.

Generate the final assembly code to measure the machine instruction difference. Run `cargo asm arch_analysis::run_dynamic_pipeline` and `cargo asm arch_analysis::run_static_pipeline` using the `cargo-asm` tool, or use `objdump -d target/release/libarch_analysis.so` and manually locate the function symbols. In the dynamic pipeline, count the instructions between function prologue and epilogue: you will observe multiple `call` instructions through registers loaded from memory, along with address arithmetic to compute vtable offsets. In the static pipeline, if optimization succeeded, the entire processing logic may be inlined into a single vectorized loop with SIMD instructions like `vpmulld` or `vpaddd` for the doubling and increment operations, eliminating all call overhead. Measure the instruction count difference: dynamic dispatch typically adds 5-10 instructions per trait method call for vtable lookup, register indirect jump, and call frame setup.

Profile the execution to quantify the performance impact. Add a benchmark to `benches/dispatch.rs`:

```rust
// benches/dispatch.rs
use arch_analysis::*;
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn benchmark_dispatch(c: &mut Criterion) {
    let data: Vec<u32> = (0..1000).collect();
    
    let mut group = c.benchmark_group("dispatch");
    
    group.bench_function("dynamic", |b| {
        b.iter(|| {
            run_dynamic_pipeline(black_box(&data))
        });
    });
    
    group.bench_function("static", |b| {
        b.iter(|| {
            run_static_pipeline(black_box(&data))
        });
    });
    
    group.finish();
}

criterion_group!(benches, benchmark_dispatch);
criterion_main!(benches);
```

Add Criterion to `Cargo.toml`:

```toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "dispatch"
harness = false
```

Run `cargo bench --bench dispatch` to execute the benchmarks with statistical analysis. Criterion will report the median execution time, standard deviation, and throughput for each dispatch strategy. On typical x86-64 hardware, the static dispatch version should demonstrate 10-30% higher throughput depending on how well the compiler vectorizes the pipeline. The dynamic version suffers from instruction cache pressure due to scattered vtable entries and branch misprediction on the indirect calls, while the static version benefits from linear execution and prefetching.

Extend the analysis to examine architectural patterns beyond dispatch strategies. Implement a zero-cost abstraction using newtype wrappers and verify that the abstraction compiles away completely:

```rust
// src/lib.rs (add to existing code)
#[repr(transparent)]
pub struct UserId(u64);

impl UserId {
    pub fn new(id: u64) -> Self {
        UserId(id)
    }
    
    pub fn get(&self) -> u64 {
        self.0
    }
}

pub fn process_user_id(user: UserId) -> u64 {
    user.get() * 2
}

pub fn process_raw_id(id: u64) -> u64 {
    id * 2
}
```

Compile with optimizations and disassemble both functions. The `#[repr(transparent)]` attribute ensures the newtype has identical layout to its inner type, and optimizations eliminate all wrapper manipulation. Run `cargo asm arch_analysis::process_user_id` and `cargo asm arch_analysis::process_raw_id`. Both functions should generate identical assembly: a single left shift or multiplication instruction operating directly on the input register with no wrapper construction or extraction overhead. This validates the zero-cost abstraction principle: architectural patterns that enhance type safety and maintainability should not incur runtime penalties when properly designed.

Investigate how architectural layering affects optimization boundaries. Create a module hierarchy that crosses compilation unit boundaries:

```rust
// src/compute.rs
pub fn expensive_computation(x: u32) -> u32 {
    let mut result = x;
    for _ in 0..100 {
        result = result.wrapping_mul(31).wrapping_add(17);
    }
    result
}

// src/lib.rs (add to existing code)
mod compute;

pub fn process_with_cross_module(data: &[u32]) -> Vec<u32> {
    data.iter().map(|&x| compute::expensive_computation(x)).collect()
}
```

Compile with `cargo rustc --lib --release -- -C lto=off` to disable link-time optimization, simulating separate compilation of modules. Disassemble `process_with_cross_module` and observe that `expensive_computation` remains as an external function call even though it is pure and side-effect-free. The optimizer cannot inline across the module boundary without LTO enabled. Now recompile with `cargo rustc --lib --release -- -C lto=thin` to enable thin LTO, which performs cross-module inlining. Disassemble again and observe that `expensive_computation` is now inlined into the caller, and the optimizer may even unroll or eliminate the entire loop if it detects the computation is predictable. This demonstrates that architectural module boundaries have real performance implications: fine-grained modules improve maintainability but can fragment optimization opportunities unless LTO recovers cross-boundary visibility.

Document your findings by recording instruction counts, function call overhead measurements, and optimization effectiveness for each architectural pattern. Compare the MIR, LLVM IR, and final assembly to identify where abstractions remain zero-cost and where they introduce measurable overhead. This empirical verification grounds architectural decisions in hardware reality rather than theoretical complexity analysis.

## Exercise 2: Cache Miss & Throughput Profiling

Modern CPU performance is dominated not by instruction execution but by memory latency. While an ALU operation completes in a single cycle, a cache miss to main memory stalls the pipeline for hundreds of cycles. Architectural decisions about data structure layout, access patterns, and memory locality determine whether an algorithm runs at L1 cache speed or suffers repeated stalls waiting for DRAM. This exercise instruments cache behavior using hardware performance counters and profiling tools to measure how different architectural patterns interact with the memory hierarchy. By comparing array-of-structs versus struct-of-arrays layouts, linked structures versus contiguous storage, and random versus sequential access, engineers can quantify the cache efficiency of their architectural choices.

Cache hierarchies exploit temporal and spatial locality through progressively larger but slower memory tiers: L1 data cache (32-64 KB, ~4 cycles), L2 cache (256 KB-1 MB, ~12 cycles), L3 cache (8-32 MB, ~40 cycles), and main memory (gigabytes, ~200 cycles). A cache line is typically 64 bytes, meaning every memory access loads an entire line even if only a single byte is needed. Architectures that pack related data into contiguous cache lines and access it sequentially maximize bandwidth utilization, while scattered pointer chasing and random access patterns trigger cache evictions and memory stalls. The difference between a cache-friendly and cache-hostile architecture can be 10-100× in throughput for memory-bound workloads.

Create a new project with `cargo new cache_profiling && cd cache_profiling`. Implement two data structure architectures for storing particle data: array-of-structs (AoS) which mirrors object-oriented design principles, and struct-of-arrays (SoA) which optimizes for vectorization and cache utilization. The particle structure contains position, velocity, and mass, and the simulation updates positions based on velocities, a typical pattern in game engines, physics simulations, and scientific computing.

```rust
// src/lib.rs
#[derive(Clone, Copy)]
pub struct Particle {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub vx: f32,
    pub vy: f32,
    pub vz: f32,
    pub mass: f32,
}

pub struct ParticlesAoS {
    particles: Vec<Particle>,
}

impl ParticlesAoS {
    pub fn new(count: usize) -> Self {
        let particles = (0..count)
            .map(|i| Particle {
                x: i as f32,
                y: i as f32 * 2.0,
                z: i as f32 * 3.0,
                vx: 1.0,
                vy: -1.0,
                vz: 0.5,
                mass: 1.0,
            })
            .collect();
        ParticlesAoS { particles }
    }

    pub fn update_positions(&mut self, dt: f32) {
        for particle in &mut self.particles {
            particle.x += particle.vx * dt;
            particle.y += particle.vy * dt;
            particle.z += particle.vz * dt;
        }
    }

    pub fn len(&self) -> usize {
        self.particles.len()
    }
}

pub struct ParticlesSoA {
    x: Vec<f32>,
    y: Vec<f32>,
    z: Vec<f32>,
    vx: Vec<f32>,
    vy: Vec<f32>,
    vz: Vec<f32>,
    mass: Vec<f32>,
}

impl ParticlesSoA {
    pub fn new(count: usize) -> Self {
        let x: Vec<f32> = (0..count).map(|i| i as f32).collect();
        let y: Vec<f32> = (0..count).map(|i| i as f32 * 2.0).collect();
        let z: Vec<f32> = (0..count).map(|i| i as f32 * 3.0).collect();
        let vx = vec![1.0; count];
        let vy = vec![-1.0; count];
        let vz = vec![0.5; count];
        let mass = vec![1.0; count];
        
        ParticlesSoA { x, y, z, vx, vy, vz, mass }
    }

    pub fn update_positions(&mut self, dt: f32) {
        for i in 0..self.x.len() {
            self.x[i] += self.vx[i] * dt;
            self.y[i] += self.vy[i] * dt;
            self.z[i] += self.vz[i] * dt;
        }
    }

    pub fn len(&self) -> usize {
        self.x.len()
    }
}
```

The AoS layout interleaves all fields of each particle in memory: `x₀ y₀ z₀ vx₀ vy₀ vz₀ mass₀ x₁ y₁ z₁ ...`. When updating positions, the code accesses `x`, `vx`, then skips over `y`, `z`, `vy`, `vz`, and `mass` to reach the next particle's `x` field. This strided access pattern wastes cache line bandwidth because only 8 bytes of each 28-byte struct are used during position updates, resulting in a 28.5% cache line utilization. The SoA layout stores each field in a separate contiguous array: `x₀ x₁ x₂ ... xₙ` followed by `y₀ y₁ y₂ ... yₙ` and so on. During position updates, the code streams through the `x` array, then the `y` array, achieving near-perfect cache line utilization because all 64 bytes of each loaded cache line contain relevant data.

Benchmark the throughput difference between the two layouts. Create `benches/cache.rs`:

```rust
// benches/cache.rs
use cache_profiling::*;
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn benchmark_layouts(c: &mut Criterion) {
    let sizes = [1000, 10_000, 100_000, 1_000_000];
    let dt = 0.016f32; // 60 FPS timestep
    
    let mut group = c.benchmark_group("particle_update");
    
    for &size in &sizes {
        group.bench_with_input(BenchmarkId::new("AoS", size), &size, |b, &size| {
            let mut particles = ParticlesAoS::new(size);
            b.iter(|| {
                particles.update_positions(black_box(dt));
            });
        });
        
        group.bench_with_input(BenchmarkId::new("SoA", size), &size, |b, &size| {
            let mut particles = ParticlesSoA::new(size);
            b.iter(|| {
                particles.update_positions(black_box(dt));
            });
        });
    }
    
    group.finish();
}

criterion_group!(benches, benchmark_layouts);
criterion_main!(benches);
```

Add Criterion to `Cargo.toml` as before. Run `cargo bench --bench cache` to measure throughput. The SoA layout should demonstrate 2-3× higher throughput on large particle counts where the dataset exceeds L3 cache capacity. At 1 million particles, the AoS struct occupies 28 MB while the SoA layout occupies the same total memory but accesses it in a streaming pattern that maximizes prefetcher effectiveness and cache line utilization.

Profile the cache behavior directly using hardware performance counters. On Linux, use `perf stat` to measure cache misses. Compile the benchmark with `cargo build --release --bench cache`, then run it under `perf` instrumentation:

```bash
perf stat -e cache-references,cache-misses,instructions,cycles \
  ./target/release/deps/cache-* --bench --profile-time=10
```

The `perf stat` output reports hardware events for the entire benchmark execution. The critical metrics are cache miss rate (cache-misses / cache-references) and instructions per cycle (IPC). The AoS layout will show a higher cache miss rate, often 15-25%, because each particle access pattern has poor spatial locality. The SoA layout achieves a lower miss rate, often under 5%, because sequential array traversal benefits from hardware prefetching. The IPC metric reveals CPU utilization: the AoS version will show lower IPC, often below 1.0, indicating the CPU is stalled waiting for memory most of the time. The SoA version achieves higher IPC, often 2-3, because the CPU can execute multiple independent instructions while waiting for memory through out-of-order execution and vectorization.

Instrument cache behavior at a more granular level using Cachegrind, Valgrind's cache simulator. Cachegrind models the L1 and last-level cache, reporting cache misses per function. Create a dedicated binary for profiling:

```rust
// src/main.rs
use cache_profiling::*;

fn main() {
    let size = 1_000_000;
    let dt = 0.016f32;
    let iterations = 100;

    println!("Profiling AoS layout...");
    let mut aos = ParticlesAoS::new(size);
    for _ in 0..iterations {
        aos.update_positions(dt);
    }

    println!("Profiling SoA layout...");
    let mut soa = ParticlesSoA::new(size);
    for _ in 0..iterations {
        soa.update_positions(dt);
    }
}
```

Compile with debug symbols and run under Cachegrind:

```bash
cargo build --release
valgrind --tool=cachegrind --cachegrind-out-file=cachegrind.out \
  ./target/release/cache_profiling
```

Analyze the output with `cg_annotate cachegrind.out`. The report breaks down cache misses by function and line number. Locate the `update_positions` implementations and examine the D1 misses (L1 data cache misses) and LL misses (last-level cache misses). The AoS version will show a high miss rate per array access because of the strided pattern, while the SoA version shows a much lower miss rate concentrated at array boundaries. The total instruction count will be similar, confirming that the performance difference is memory-bound rather than compute-bound.

Extend the analysis to linked data structures, which represent the worst case for cache efficiency. Implement a linked list of particles and compare it to the array-based structures:

```rust
// src/lib.rs (add to existing code)
pub struct ParticleNode {
    particle: Particle,
    next: Option<Box<ParticleNode>>,
}

pub struct ParticlesLinkedList {
    head: Option<Box<ParticleNode>>,
    count: usize,
}

impl ParticlesLinkedList {
    pub fn new(count: usize) -> Self {
        let mut head = None;
        for i in (0..count).rev() {
            head = Some(Box::new(ParticleNode {
                particle: Particle {
                    x: i as f32,
                    y: i as f32 * 2.0,
                    z: i as f32 * 3.0,
                    vx: 1.0,
                    vy: -1.0,
                    vz: 0.5,
                    mass: 1.0,
                },
                next: head,
            }));
        }
        ParticlesLinkedList { head, count }
    }

    pub fn update_positions(&mut self, dt: f32) {
        let mut current = &mut self.head;
        while let Some(node) = current {
            node.particle.x += node.particle.vx * dt;
            node.particle.y += node.particle.vy * dt;
            node.particle.z += node.particle.vz * dt;
            current = &mut node.next;
        }
    }

    pub fn len(&self) -> usize {
        self.count
    }
}
```

Add the linked list to the benchmark. Each node allocation scatters particles across the heap with no spatial locality, and traversal requires a dependent load chain where each next pointer must be fetched before the following node can be accessed, defeating prefetching and pipelining. Run the benchmark again. The linked list will be 10-50× slower than the SoA layout due to catastrophic cache miss rates often exceeding 90%. Every pointer dereference triggers a cache miss because the allocator does not guarantee contiguous placement, and the CPU cannot prefetch ahead because each address depends on loading the previous pointer.

Profile the linked list under `perf` to quantify the disaster. Run `perf record -g ./target/release/deps/cache-* --bench --profile-time=10`, then visualize the results with `perf report`. The linked list version will show that most execution time is spent in memory stalls, visible as high sample counts in the `update_positions` method with no concentrated hotspot in the instruction stream. Generate a flame graph to visualize the execution profile:

```bash
cargo install flamegraph
cargo flamegraph --bench cache -- --bench --profile-time=10
```

Open `flamegraph.svg` in a browser. The SoA version shows a tight flame graph with execution concentrated in the update loop and vectorized instructions. The linked list version shows a wide, flat profile with execution time distributed across memory access overhead rather than productive computation. This visualization makes the cache efficiency difference immediately apparent: efficient architectures concentrate execution in tight loops that the CPU can optimize, while inefficient architectures fragment execution across memory stalls.

Compare allocation strategies by benchmarking an arena-allocated linked list where nodes are packed contiguously. Use the `typed-arena` crate to allocate nodes from a contiguous memory region:

```toml
[dependencies]
typed-arena = "2.0"
```

```rust
// src/lib.rs (add to existing code)
use typed_arena::Arena;

pub struct ParticleNodeArena<'a> {
    particle: Particle,
    next: Option<&'a mut ParticleNodeArena<'a>>,
}

pub struct ParticlesArenaList<'a> {
    arena: Arena<ParticleNodeArena<'a>>,
    head: Option<&'a mut ParticleNodeArena<'a>>,
    count: usize,
}

impl<'a> ParticlesArenaList<'a> {
    pub fn new(count: usize) -> Self {
        let arena = Arena::new();
        // Note: Arena allocation requires unsafe or restructuring for mutable iteration
        // This example demonstrates the concept; production code would use indices
        ParticlesArenaList {
            arena,
            head: None,
            count,
        }
    }

    pub fn len(&self) -> usize {
        self.count
    }
}
```

The arena allocator improves locality by allocating nodes sequentially in a contiguous buffer, reducing the cache miss rate compared to scattered heap allocation. Benchmark this version and observe that it performs significantly better than the heap-allocated linked list, though still worse than arrays due to the pointer indirection overhead. This demonstrates that allocation strategy is an architectural decision with measurable performance impact.

Document the cache profiling results in a table summarizing cache miss rates, throughput, and memory bandwidth utilization for each architectural pattern. Record the conditions under which each architecture performs well: SoA for streaming updates, AoS for operations that need all fields, and linked structures only when dynamic insertion/deletion dominates over iteration. Use these empirical measurements to inform architectural decisions in cache-sensitive domains like high-performance computing, real-time systems, and game engines.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrent architectures introduce subtle correctness hazards that only manifest under specific thread interleavings and timing conditions. Data races occur when multiple threads access shared memory without proper synchronization, leading to torn reads, lost updates, and undefined behavior. Memory leaks accumulate when resources are allocated but never freed, eventually exhausting available memory. Deadlocks freeze the system when threads circularly wait for locks held by each other. These bugs are notoriously difficult to reproduce because they depend on nondeterministic scheduling decisions made by the operating system kernel. This exercise employs sanitizers and stress testing to systematically expose concurrency bugs that might escape testing under normal conditions.

Rust's type system prevents data races at compile time through ownership and the `Send`/`Sync` trait system, but unsafe code, incorrect synchronization primitives, and logic errors can still introduce races. ThreadSanitizer (TSan) instruments compiled code to detect unsynchronized conflicting accesses at runtime, reporting the exact source locations of racing operations. AddressSanitizer (ASan) detects memory safety violations including use-after-free, buffer overflows, and memory leaks. LeakSanitizer (LSan), integrated into ASan, tracks allocations and reports memory that remains allocated at program exit. By combining these tools with stress testing under high concurrency, engineers can validate that their concurrent architectures maintain invariants under all possible thread interleavings.

Create a new project with `cargo new concurrency_testing && cd concurrency_testing`. Implement a concurrent counter using atomic operations and a shared counter using mutexes, intentionally introducing bugs to demonstrate sanitizer detection. The atomic counter will have a subtle race condition in a compound operation, while the mutex counter will leak memory by forgetting to deallocate a resource.

```rust
// src/lib.rs
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};

pub struct AtomicCounter {
    count: AtomicUsize,
}

impl AtomicCounter {
    pub fn new() -> Self {
        AtomicCounter {
            count: AtomicUsize::new(0),
        }
    }

    pub fn increment(&self) {
        self.count.fetch_add(1, Ordering::Relaxed);
    }

    pub fn get(&self) -> usize {
        self.count.load(Ordering::Relaxed)
    }

    // Buggy compound operation: not atomic despite using atomic primitives
    pub fn increment_if_even(&self) -> bool {
        let current = self.count.load(Ordering::Relaxed);
        if current % 2 == 0 {
            self.count.fetch_add(1, Ordering::Relaxed);
            true
        } else {
            false
        }
    }
}

pub struct MutexCounter {
    count: Arc<Mutex<usize>>,
    leaked_vec: Option<Vec<u8>>, // Intentionally leaked
}

impl MutexCounter {
    pub fn new() -> Self {
        MutexCounter {
            count: Arc::new(Mutex::new(0)),
            leaked_vec: Some(vec![0u8; 1024 * 1024]), // 1 MB allocation
        }
    }

    pub fn increment(&self) {
        let mut count = self.count.lock().unwrap();
        *count += 1;
    }

    pub fn get(&self) -> usize {
        let count = self.count.lock().unwrap();
        *count
    }
}

impl Drop for MutexCounter {
    fn drop(&mut self) {
        // Intentionally forget to drop leaked_vec
        if let Some(leaked) = self.leaked_vec.take() {
            std::mem::forget(leaked);
        }
    }
}
```

The atomic counter's `increment_if_even` method contains a race condition despite using atomic operations. The check and increment are not atomic as a unit: another thread could increment the counter between the load and the conditional fetch_add, violating the even-value precondition. This represents a common bug in lock-free programming where individual operations are atomic but compound operations are not. The mutex counter intentionally leaks memory by forgetting the allocated vector in its destructor, simulating resource leaks from improper cleanup.

Create a stress test that spawns many threads executing concurrent operations, increasing the probability of exposing race conditions:

```rust
// tests/stress_test.rs
use concurrency_testing::*;
use std::sync::Arc;
use std::thread;

#[test]
fn stress_test_atomic_counter() {
    let counter = Arc::new(AtomicCounter::new());
    let threads: Vec<_> = (0..16)
        .map(|_| {
            let counter = counter.clone();
            thread::spawn(move || {
                for _ in 0..10_000 {
                    counter.increment_if_even();
                }
            })
        })
        .collect();

    for t in threads {
        t.join().unwrap();
    }

    let final_count = counter.get();
    println!("Final count: {}", final_count);
    // The count will be unpredictable due to the race condition
}

#[test]
fn stress_test_mutex_counter() {
    let counter = Arc::new(MutexCounter::new());
    let threads: Vec<_> = (0..16)
        .map(|_| {
            let counter = counter.clone();
            thread::spawn(move || {
                for _ in 0..1_000 {
                    counter.increment();
                }
            })
        })
        .collect();

    for t in threads {
        t.join().unwrap();
    }

    let final_count = counter.get();
    println!("Final count: {}", final_count);
    assert_eq!(final_count, 16_000);
}

#[test]
fn leak_test() {
    // Create and drop many counters to accumulate leaks
    for _ in 0..100 {
        let _ = MutexCounter::new();
    }
}
```

Build the tests with ThreadSanitizer enabled. ThreadSanitizer is available through LLVM sanitizers and requires nightly Rust:

```bash
rustup install nightly
export RUSTFLAGS="-Z sanitizer=thread"
cargo +nightly test --target x86_64-unknown-linux-gnu -- --test-threads=1
```

ThreadSanitizer instruments memory accesses and synchronization operations, maintaining shadow state to detect conflicting accesses. Run the atomic counter stress test. ThreadSanitizer will report a data race in the `increment_if_even` method, identifying the load and store operations that conflict without proper synchronization:

```text
WARNING: ThreadSanitizer: data race (pid=12345)
  Read of size 8 at 0x7fff12345678 by thread T2:
    #0 AtomicCounter::increment_if_even src/lib.rs:24
    ...
  Previous write of size 8 at 0x7fff12345678 by thread T1:
    #0 AtomicCounter::increment_if_even src/lib.rs:26
    ...
```

The report shows the exact source lines where the conflicting accesses occurred and the threads involved. This confirms the race condition: the load at line 24 and the store at line 26 are not synchronized with each other across threads, allowing interleaving that violates atomicity.

Fix the race condition by using compare-and-swap to make the compound operation atomic:

```rust
// src/lib.rs (fix the buggy method)
impl AtomicCounter {
    pub fn increment_if_even(&self) -> bool {
        let mut current = self.count.load(Ordering::Relaxed);
        loop {
            if current % 2 != 0 {
                return false;
            }
            match self.count.compare_exchange_weak(
                current,
                current + 1,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => return true,
                Err(actual) => current = actual,
            }
        }
    }
}
```

The compare-and-swap loop atomically checks the condition and updates the counter, retrying if another thread modified the value concurrently. Run ThreadSanitizer again to verify the race is eliminated. The test should pass without warnings.

Test memory leaks using AddressSanitizer with LeakSanitizer enabled. AddressSanitizer requires rebuilding with a different sanitizer flag:

```bash
export RUSTFLAGS="-Z sanitizer=address"
cargo +nightly test --target x86_64-unknown-linux-gnu leak_test
```

LeakSanitizer runs at program exit and reports memory that was allocated but never freed. The `leak_test` creates 100 counter instances, each leaking 1 MB, for a total of 100 MB leaked. LeakSanitizer will report:

```text
==12345==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 104857600 byte(s) in 100 object(s) allocated from:
    #0 malloc
    #1 alloc::vec::Vec<T>::with_capacity
    #2 MutexCounter::new src/lib.rs:37
    #3 leak_test tests/stress_test.rs:54
```

The report identifies the allocation site and the total leaked memory. Fix the leak by properly dropping the vector:

```rust
// src/lib.rs (fix the drop implementation)
impl Drop for MutexCounter {
    fn drop(&mut self) {
        // Properly drop leaked_vec instead of forgetting it
        self.leaked_vec.take();
    }
}
```

Run the leak test again. LeakSanitizer should report no leaks, confirming proper resource cleanup.

Extend the testing to detect deadlocks. Implement a classic deadlock scenario where two threads acquire locks in opposite order:

```rust
// src/lib.rs (add to existing code)
use std::sync::Mutex;

pub struct BankAccount {
    balance: Mutex<i64>,
}

impl BankAccount {
    pub fn new(initial: i64) -> Self {
        BankAccount {
            balance: Mutex::new(initial),
        }
    }

    pub fn transfer(&self, other: &BankAccount, amount: i64) {
        let mut my_balance = self.balance.lock().unwrap();
        let mut other_balance = other.balance.lock().unwrap();
        
        *my_balance -= amount;
        *other_balance += amount;
    }
}
```

Create a test that triggers the deadlock:

```rust
// tests/stress_test.rs (add to existing tests)
#[test]
#[ignore] // Ignore by default since it deadlocks
fn deadlock_test() {
    use concurrency_testing::BankAccount;
    use std::sync::Arc;
    use std::thread;

    let account1 = Arc::new(BankAccount::new(1000));
    let account2 = Arc::new(BankAccount::new(1000));

    let a1 = account1.clone();
    let a2 = account2.clone();
    let t1 = thread::spawn(move || {
        for _ in 0..100 {
            a1.transfer(&a2, 10);
        }
    });

    let a1 = account1.clone();
    let a2 = account2.clone();
    let t2 = thread::spawn(move || {
        for _ in 0..100 {
            a2.transfer(&a1, 10);
        }
    });

    t1.join().unwrap();
    t2.join().unwrap();
}
```

Thread 1 locks account1 then account2, while thread 2 locks account2 then account1. Eventually, thread 1 will hold account1's lock while waiting for account2, and thread 2 will hold account2's lock while waiting for account1, deadlocking. Run this test with a timeout to detect the hang: `timeout 5 cargo test deadlock_test -- --ignored`. The test will timeout after 5 seconds, confirming the deadlock.

ThreadSanitizer can detect potential deadlocks by analyzing lock acquisition order. Run the test under ThreadSanitizer:

```bash
export RUSTFLAGS="-Z sanitizer=thread"
timeout 5 cargo +nightly test --target x86_64-unknown-linux-gnu deadlock_test -- --ignored
```

ThreadSanitizer may report a lock order inversion warning before the actual deadlock occurs, identifying the conflicting lock acquisitions. Fix the deadlock by enforcing a consistent lock ordering using pointer addresses:

```rust
// src/lib.rs (fix the transfer method)
impl BankAccount {
    pub fn transfer(&self, other: &BankAccount, amount: i64) {
        // Acquire locks in consistent order based on pointer address
        let (first, second) = if (self as *const _) < (other as *const _) {
            (&self.balance, &other.balance)
        } else {
            (&other.balance, &self.balance)
        };

        let mut first_balance = first.lock().unwrap();
        let mut second_balance = second.lock().unwrap();

        if std::ptr::eq(self, other) {
            return; // Same account, no transfer
        }

        if (self as *const _) < (other as *const _) {
            *first_balance -= amount;
            *second_balance += amount;
        } else {
            *second_balance += amount;
            *first_balance -= amount;
        }
    }
}
```

This implementation always acquires locks in ascending pointer order, preventing circular wait. Run the deadlock test again. It should complete without hanging.

Test destructors and cleanup with AddressSanitizer to detect use-after-free bugs. Implement a reference-counted structure with manual memory management:

```rust
// src/lib.rs (add to existing code)
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

pub struct UnsafeCounter {
    ptr: *mut usize,
}

impl UnsafeCounter {
    pub fn new() -> Self {
        unsafe {
            let layout = Layout::new::<usize>();
            let ptr = alloc(layout) as *mut usize;
            ptr::write(ptr, 0);
            UnsafeCounter { ptr }
        }
    }

    pub fn increment(&self) {
        unsafe {
            *self.ptr += 1;
        }
    }

    pub fn get(&self) -> usize {
        unsafe { *self.ptr }
    }
}

impl Drop for UnsafeCounter {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::new::<usize>();
            dealloc(self.ptr as *mut u8, layout);
        }
    }
}

unsafe impl Send for UnsafeCounter {}
```

Create a test that uses the counter after freeing it:

```rust
// tests/stress_test.rs (add to existing tests)
#[test]
#[should_panic]
fn use_after_free_test() {
    use concurrency_testing::UnsafeCounter;
    
    let counter = UnsafeCounter::new();
    counter.increment();
    drop(counter);
    
    // Access after drop - use-after-free bug
    // This is intentionally unsafe and should be detected by ASan
    // Uncomment to test: println!("{}", counter.get());
}
```

AddressSanitizer poisons freed memory and detects accesses to it. If you uncomment the final line and run with ASan enabled, it will report a heap-use-after-free error with the exact allocation, deallocation, and access locations.

Document your sanitizer findings by recording the types of bugs detected, the specific sanitizer warnings, and the fixes applied. Create a sanitizer testing checklist for concurrent architectures: run ThreadSanitizer on all concurrent code paths, run AddressSanitizer on all resource management code, stress test with high thread counts, and verify deterministic behavior under different scheduling conditions. This systematic verification process catches concurrency bugs that would be nearly impossible to diagnose through traditional debugging.

## Developer Cheat Sheet & Toolchain Checklist

Architectural verification requires a systematic toolchain workflow that progresses from static analysis through profiling to runtime instrumentation. This checklist codifies the laboratory procedures into a repeatable process for any codebase. Start with static analysis to understand compilation decisions, proceed to profiling to measure runtime behavior, and finish with sanitizers to detect correctness violations. Each phase uses different tools that expose different architectural properties, and together they provide complete visibility into how design decisions manifest in actual execution.

### Static Analysis & Compilation Pipeline

**Examine MIR and optimization decisions:**
```bash
cargo rustc --lib --release -- --emit=mir -Z dump-mir=all
cargo rustc --lib --release -- --emit=llvm-ir
```
MIR files appear in `target/release/deps/*.mir`. LLVM IR appears in `target/release/deps/*.ll`. Search for function names to inspect control flow, inlining decisions, and lifetime annotations.

**Disassemble specific functions:**
```bash
cargo install cargo-asm
cargo asm <crate>::<function>
```
Or use objdump for full binary disassembly: `objdump -d -M intel -S target/release/binary`.

**Inspect symbol table and binary size:**
```bash
nm -C -S --size-sort target/release/binary | head -20
bloaty target/release/binary
```
Identify largest functions, detect unexpected symbols, and verify that zero-cost abstractions disappear.

**Check optimization levels and features:**
```bash
cargo rustc --release -- -C opt-level=3 -C lto=fat -C codegen-units=1
```
Fat LTO maximizes cross-crate optimization. Single codegen unit enables better optimization at the cost of longer compile times.

### Performance Profiling

**Benchmark with statistical analysis:**
```bash
cargo bench --bench <name>
```
Criterion provides percentile distributions, outlier detection, and throughput measurements. Compare across configurations by naming benchmarks systematically.

**CPU profiling with hardware counters:**
```bash
perf stat -e cycles,instructions,cache-references,cache-misses,branches,branch-misses <binary>
perf record -g -F 999 <binary>
perf report
```
The `-F` flag sets sampling frequency. Higher frequencies provide finer resolution but increase overhead. Generate flame graphs: `perf script | stackcollapse-perf.pl | flamegraph.pl > profile.svg`.

**Integrated flame graph generation:**
```bash
cargo install flamegraph
cargo flamegraph --bench <name> -- --bench --profile-time=10
```
Opens `flamegraph.svg` showing call stack samples. Wide plateaus indicate hotspots where optimization should focus.

**Cache simulation with Cachegrind:**
```bash
valgrind --tool=cachegrind --cachegrind-out-file=cachegrind.out <binary>
cg_annotate cachegrind.out
```
Reports L1 and last-level cache miss rates per function and source line. Use `--cache-sim=no --branch-sim=yes` to profile branch prediction instead.

**Memory allocation profiling with Massif:**
```bash
valgrind --tool=massif --massif-out-file=massif.out <binary>
ms_print massif.out
```
Tracks heap usage over time. Identifies memory growth, allocation hotspots, and peak usage.

### Concurrency & Correctness Verification

**ThreadSanitizer for race detection:**
```bash
export RUSTFLAGS="-Z sanitizer=thread"
cargo +nightly test --target x86_64-unknown-linux-gnu -- --test-threads=1
```
Reports unsynchronized conflicting accesses with source locations and thread stacks. Requires nightly Rust and cannot be combined with other sanitizers.

**AddressSanitizer for memory safety:**
```bash
export RUSTFLAGS="-Z sanitizer=address"
cargo +nightly test --target x86_64-unknown-linux-gnu
```
Detects buffer overflows, use-after-free, double-free, and memory leaks. LeakSanitizer runs automatically at exit.

**MemorySanitizer for uninitialized reads:**
```bash
export RUSTFLAGS="-Z sanitizer=memory"
cargo +nightly test --target x86_64-unknown-linux-gnu
```
Detects reads of uninitialized memory. Requires building the standard library with MSan, so it is used less frequently than ASan.

**Run sanitizers on long-running workloads:**
```bash
export TSAN_OPTIONS="halt_on_error=0 log_path=tsan.log"
cargo +nightly run --release --target x86_64-unknown-linux-gnu
```
Sanitizers produce false positives on some third-party code. Use suppression files to filter known issues: `export TSAN_OPTIONS="suppressions=tsan_suppressions.txt"`.

**Stress testing under concurrency:**
```bash
for i in {1..100}; do cargo test --release <test> || break; done
```
Run tests repeatedly to increase the probability of exposing race conditions. Vary thread counts with `RUST_TEST_THREADS` environment variable.

### Build Configuration & Verification

**Full optimization for release:**
```toml
[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
```
Fat LTO and single codegen unit maximize optimization. Panic abort eliminates unwinding overhead but prevents recovery.

**Debug symbols in release builds:**
```toml
[profile.release]
debug = true
```
Enables profiling with source line annotations without disabling optimizations. Use `strip` to remove symbols from shipped binaries.

**Target-specific optimization:**
```bash
RUSTFLAGS="-C target-cpu=native" cargo build --release
```
Enables CPU-specific instructions like AVX2, AVX-512. Produces binaries that may not run on older CPUs.

**Verify binary reproducibility:**
```bash
cargo clean && cargo build --release
sha256sum target/release/binary > checksum1.txt
cargo clean && cargo build --release
sha256sum target/release/binary > checksum2.txt
diff checksum1.txt checksum2.txt
```
Reproducible builds produce identical binaries from identical sources. Non-reproducibility indicates non-deterministic compilation.

### Standard Workflow for Architectural Verification

1. **Implement feature with type system verification.** Rust's borrow checker and trait system enforce architectural invariants at compile time. Use newtypes, trait bounds, and lifetime annotations to encode design constraints.

2. **Inspect compilation artifacts.** Examine MIR and LLVM IR to verify that abstractions compile away. Disassemble critical functions to confirm expected instruction sequences.

3. **Benchmark performance.** Use Criterion to measure throughput across representative workloads. Compare alternative implementations quantitatively.

4. **Profile with hardware counters.** Run `perf stat` to identify bottlenecks. Low IPC indicates memory stalls; high cache miss rates suggest poor locality.

5. **Generate flame graphs.** Identify hotspots visually. Wide plateaus indicate optimization opportunities.

6. **Simulate cache behavior.** Use Cachegrind on memory-intensive code to validate cache-friendly design.

7. **Run sanitizers.** ThreadSanitizer for concurrent code, AddressSanitizer for unsafe code. Fix all reported issues.

8. **Stress test under load.** Run tests repeatedly with high concurrency to expose nondeterministic bugs.

9. **Verify release configuration.** Build with full optimization and profiling symbols. Measure final performance against requirements.

10. **Document architectural decisions.** Record why specific patterns were chosen, what alternatives were considered, and what measurements justified the decision.

This workflow transforms architectural design from abstract reasoning into empirical verification grounded in hardware behavior. Each tool exposes different aspects of the architecture: compilers reveal abstraction costs, profilers reveal execution patterns, and sanitizers reveal correctness violations. Together, they provide complete confidence that the architecture delivers its intended properties in actual execution rather than only in theory.
