# Operational Verification Labs: Game Development

## Objective & Toolchain Setup

Game development demands intimate familiarity with the full compilation pipeline, memory subsystem behavior, and concurrency primitives that underpin modern engines. A single frame budget of 16.67 milliseconds at 60 FPS leaves no room for cache-thrashing data structures, inadvertent heap allocations in hot loops, or data races in parallel scene graph traversals. This laboratory sequence trains you to interrogate compiler intermediate representations, profile cache hierarchies under realistic workloads, and deploy dynamic analysis instrumentation to surface memory corruption and threading violations before they manifest as non-deterministic crashes in production builds.

You will construct a minimal Entity Component System (ECS) architecture in Rust and C++, then instrument it with LLVM-based sanitizers, hardware performance counters, and debugger scripting to validate correctness and performance invariants. The exercises progress from static compilation artifacts through dynamic runtime profiling to adversarial stress testing of concurrent subsystems. Each lab produces quantitative metrics—cache miss rates, allocation counts, race detector reports—that directly inform architectural refactoring decisions.

Begin by establishing a hermetic development environment. Install the Rust toolchain via `rustup`, ensuring you have the latest stable compiler and Cargo build system. Install LLVM/Clang version 15 or later to access modern AddressSanitizer and ThreadSanitizer instrumentation. Install Valgrind for supplementary heap profiling on Linux targets. On macOS, install Xcode Command Line Tools to obtain LLDB. Install `perf` on Linux for hardware counter access, and `cargo-flamegraph` for flame graph generation from sampled profiles. Verify your installation by running `rustc --version`, `clang --version`, `valgrind --version`, and `perf --version`. Create a new Cargo workspace with `cargo new game-ecs-lab --lib` and initialize a parallel C++ project with CMake for comparative analysis.

The laboratory structure isolates three verification domains. First, you will examine Abstract Syntax Trees (AST), LLVM Intermediate Representation (IR), and final assembly to understand how high-level game logic translates to machine code, identifying optimization opportunities and verifying inlining decisions. Second, you will profile cache behavior and throughput using hardware performance counters and sampling profilers, correlating L1/L2/L3 miss rates with data structure layout choices. Third, you will deploy ThreadSanitizer and AddressSanitizer under synthetic race conditions and use-after-free scenarios, validating that your ECS architecture satisfies memory safety and happens-before ordering guarantees across parallel update systems.

## Exercise 1: AST, IR & Disassembly Analysis

Modern game engines rely on aggressive compiler optimizations to meet frame budgets. Understanding how the compiler transforms your source code into machine instructions allows you to write cache-friendly, SIMD-vectorizable code and avoid performance cliffs caused by aliasing, bounds checks, or missed inlining opportunities. This exercise constructs a simple component storage system and traces its compilation through the AST, LLVM IR, and final x86-64 assembly, exposing optimization barriers and verifying that critical hot paths are devirtualized and inlined.

Create a Rust module `src/component.rs` implementing a struct-of-arrays (SoA) layout for position and velocity components. The SoA pattern improves cache locality during parallel iteration compared to array-of-structs (AoS) layouts, as consecutive SIMD lanes access contiguous memory. Define the component storage as follows, with explicit alignment directives to ensure cache line alignment and prevent false sharing across CPU cores:

```rust
#[repr(C, align(64))]
pub struct TransformComponents {
    pub positions_x: Vec<f32>,
    pub positions_y: Vec<f32>,
    pub positions_z: Vec<f32>,
    pub velocities_x: Vec<f32>,
    pub velocities_y: Vec<f32>,
    pub velocities_z: Vec<f32>,
    pub count: usize,
}

impl TransformComponents {
    pub fn new(capacity: usize) -> Self {
        Self {
            positions_x: Vec::with_capacity(capacity),
            positions_y: Vec::with_capacity(capacity),
            positions_z: Vec::with_capacity(capacity),
            velocities_x: Vec::with_capacity(capacity),
            velocities_y: Vec::with_capacity(capacity),
            velocities_z: Vec::with_capacity(capacity),
            count: 0,
        }
    }

    #[inline]
    pub fn add_entity(&mut self, px: f32, py: f32, pz: f32, vx: f32, vy: f32, vz: f32) {
        self.positions_x.push(px);
        self.positions_y.push(py);
        self.positions_z.push(pz);
        self.velocities_x.push(vx);
        self.velocities_y.push(vy);
        self.velocities_z.push(vz);
        self.count += 1;
    }

    #[inline(always)]
    pub fn integrate_motion(&mut self, dt: f32) {
        for i in 0..self.count {
            self.positions_x[i] += self.velocities_x[i] * dt;
            self.positions_y[i] += self.velocities_y[i] * dt;
            self.positions_z[i] += self.velocities_z[i] * dt;
        }
    }

    #[inline(always)]
    pub fn integrate_motion_parallel(&mut self, dt: f32) {
        use rayon::prelude::*;
        let chunk_size = 1024;
        
        (0..self.count).into_par_iter().chunks(chunk_size).for_each(|chunk| {
            for i in chunk {
                unsafe {
                    *self.positions_x.get_unchecked_mut(i) += *self.velocities_x.get_unchecked(i) * dt;
                    *self.positions_y.get_unchecked_mut(i) += *self.velocities_y.get_unchecked(i) * dt;
                    *self.positions_z.get_unchecked_mut(i) += *self.velocities_z.get_unchecked(i) * dt;
                }
            }
        });
    }
}
```

Add the Rayon dependency to `Cargo.toml` for parallel iteration: `rayon = "1.8"`. The `integrate_motion` function applies Euler integration in a tight loop, while `integrate_motion_parallel` distributes work across threads using Rayon's parallel iterator. The `#[inline(always)]` attribute forces inlining to eliminate function call overhead in the hot path.

Compile the module with full optimization and emit LLVM IR and assembly artifacts. Execute `cargo rustc --release -- --emit=llvm-ir,asm` to generate `target/release/deps/game_ecs_lab-<hash>.ll` (LLVM IR) and `game_ecs_lab-<hash>.s` (assembly). Open the `.ll` file and locate the `integrate_motion` function. You will observe that LLVM has unrolled the loop, vectorized the arithmetic using SIMD instructions (look for `<4 x float>` vector types and `fadd` operations on vector registers), and eliminated bounds checks due to the loop invariant `i < self.count`. The IR reveals how Rust's ownership system and lifetime annotations enable alias analysis: since `&mut self` guarantees exclusive access, LLVM knows the slices do not alias and can schedule loads and stores aggressively.

Examine the assembly output by searching for the mangled symbol name corresponding to `integrate_motion`. You will see x86-64 instructions such as `vmovups`, `vmulps`, and `vaddps`, indicating AVX vectorization. Count the instructions per loop iteration and note the absence of bounds check branches. Compare this to a naive AoS implementation where each entity is a struct containing six floats. In the AoS case, the compiler must stride through memory with a 24-byte offset, breaking vectorization and increasing cache line fetches. The SoA layout allows the compiler to issue sequential loads from contiguous memory, filling vector registers in a single burst.

Now instrument the compilation process to dump the AST and type-checking information. Use `cargo rustc -- -Z unpretty=hir` to emit the High-Level Intermediate Representation (HIR), which shows the desugared code after macro expansion and type inference. This reveals how Rust's iterator combinators desugar into explicit loops and how trait bounds are monomorphized. For deeper inspection, use `cargo rustc -- -Z ast-borrowed` to dump the AST before type checking. This is useful for understanding macro-generated code and verifying that procedural macros produce the expected structure.

Repeat the exercise in C++ to compare compiler behavior. Create a `component.hpp` header and `component.cpp` implementation with equivalent SoA storage. Use `clang++ -O3 -march=native -S -emit-llvm component.cpp -o component.ll` to generate LLVM IR, and `clang++ -O3 -march=native -S component.cpp -o component.s` for assembly. Clang's IR will be similar, but pay attention to aliasing annotations. Unlike Rust, C++ requires explicit `__restrict__` qualifiers to inform the compiler that pointers do not alias. Add `__restrict__` to the loop pointers and recompile. You will observe more aggressive vectorization in the generated assembly, as the compiler can now reorder memory operations without violating strict aliasing rules.

To quantify the impact of inlining, compile with and without the `#[inline(always)]` attribute and compare the resulting assembly. Use `objdump -d target/release/libgame_ecs_lab.rlib` to disassemble the static library and locate the function symbols. With inlining disabled, you will see a `call` instruction and stack frame setup overhead. With inlining enabled, the function body is embedded directly into the caller, eliminating the call/return sequence and enabling cross-function optimizations such as constant propagation and dead code elimination.

Finally, use LLVM's optimization remark system to understand why certain optimizations were applied or inhibited. Compile with `-Cremark=inline` to emit inlining decisions: `cargo rustc --release -- -C llvm-args=-pass-remarks=inline`. The output will show which functions were inlined and which were not, along with cost heuristics. Similarly, use `-pass-remarks=loop-vectorize` to diagnose vectorization failures. If a loop is not vectorized, the remark will explain why—typically due to non-constant trip counts, non-contiguous memory access, or potential aliasing.

This exercise establishes a mental model of the compilation pipeline. By reading IR and assembly, you verify that the compiler executes the optimizations you expect and identify pathological cases where high-level abstractions introduce performance penalties. In game development, where tight loops dominate frame time, this skill separates guesswork from empirical performance engineering.

## Exercise 2: Cache Miss & Throughput Profiling

Cache hierarchy behavior dominates modern CPU performance. A single L3 cache miss incurs a latency penalty of 40–100 nanoseconds, equivalent to hundreds of wasted instruction cycles. Game engines must minimize cache misses in critical update loops—physics integration, animation blending, frustum culling—to sustain high frame rates. This exercise profiles the ECS component system under realistic workloads, correlating cache miss rates with data structure layout and access patterns. You will use hardware performance counters via `perf` on Linux and Instruments on macOS, along with sampling profilers to generate flame graphs that identify hot spots and stall cycles.

Extend the `TransformComponents` module with a benchmark harness. Create a `benches/ecs_bench.rs` file with the following criterion-based benchmark that simulates a game loop updating 100,000 entities over 1,000 frames:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use game_ecs_lab::component::TransformComponents;

fn benchmark_integration(c: &mut Criterion) {
    let mut group = c.benchmark_group("motion_integration");
    
    for size in [1000, 10000, 100000].iter() {
        let mut components = TransformComponents::new(*size);
        
        for i in 0..*size {
            components.add_entity(
                i as f32, i as f32, i as f32,
                1.0, 1.0, 1.0,
            );
        }
        
        group.bench_with_input(BenchmarkId::new("serial", size), size, |b, _| {
            b.iter(|| {
                components.integrate_motion(black_box(0.016));
            });
        });
        
        group.bench_with_input(BenchmarkId::new("parallel", size), size, |b, _| {
            b.iter(|| {
                components.integrate_motion_parallel(black_box(0.016));
            });
        });
    }
    
    group.finish();
}

criterion_group!(benches, benchmark_integration);
criterion_main!(benches);
```

Add the criterion dependency to `Cargo.toml` under `[dev-dependencies]`: `criterion = "0.5"`. Run the benchmark with `cargo bench`. Criterion will execute each benchmark multiple times, compute statistics, and report throughput in iterations per second. The output will show that the serial version exhibits linear scaling with entity count, while the parallel version plateaus due to memory bandwidth saturation and thread synchronization overhead.

Now instrument the benchmark with hardware performance counters. On Linux, use `perf stat` to collect cache statistics. Run `perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses cargo bench --bench ecs_bench`. The output will report absolute counts and miss rates for L1 data cache, last-level cache (LLC), and total cache references. For the 100,000-entity benchmark, you will observe an L1 miss rate of 5–10% and an LLC miss rate of 1–2%, indicating that most working set fits in L2/L3 cache but experiences conflict misses due to cache line evictions.

To understand spatial locality, modify the benchmark to introduce strided access patterns. Change the integration loop to skip every other entity by incrementing the loop index by 2. Rerun `perf stat` and observe that cache miss rates double, as each access now straddles two cache lines instead of accessing consecutive elements. This demonstrates the importance of sequential memory layout in hot loops.

Next, profile instruction-level performance using `perf record` and `perf report`. Execute `perf record -g --call-graph=dwarf cargo bench --bench ecs_bench` to capture a call graph with full stack traces. The `-g` flag enables call graph recording, and `--call-graph=dwarf` uses DWARF debug information for accurate unwinding. After the benchmark completes, run `perf report` to launch an interactive TUI showing annotated hot spots. Navigate to the `integrate_motion` function and press `a` to display annotated assembly. You will see per-instruction sample counts, revealing which instructions stall the pipeline. Look for high sample counts on load instructions, indicating memory-bound bottlenecks.

Generate a flame graph for visual analysis. Install `cargo-flamegraph` with `cargo install flamegraph`, then run `cargo flamegraph --bench ecs_bench`. This produces an SVG flame graph showing the call stack hierarchy with widths proportional to sample counts. The widest bars represent the hottest functions. In a well-optimized ECS, the flame graph should show a single dominant bar for the integration loop, with minimal overhead from allocator calls or iterator machinery. If you observe wide bars for `Vec::push` or bounds checking, refactor to preallocate capacity and use unchecked indexing.

On macOS, use Instruments instead of `perf`. Build the benchmark in release mode with debug symbols: `cargo build --release --bench ecs_bench`. Launch Instruments and select the "Time Profiler" template. Drag the benchmark binary from `target/release/deps/` into the Instruments window and click Record. After profiling completes, expand the call tree to identify hot functions. Switch to the "System Trace" template to correlate CPU scheduling, thread states, and system calls. You will observe that the parallel benchmark incurs context switches and scheduler overhead, explaining why it does not scale linearly with thread count.

To isolate cache effects, use `perf c2c` (cache-to-cache) to detect false sharing. False sharing occurs when multiple threads access different variables that reside on the same cache line, causing cache coherence protocol overhead. Run `perf c2c record cargo bench --bench ecs_bench`, then analyze with `perf c2c report`. The report will highlight cache lines experiencing excessive invalidations. If false sharing is detected, increase the alignment of your component arrays to ensure each thread operates on distinct cache lines. The `#[repr(C, align(64))]` attribute on `TransformComponents` already mitigates this, but verify by comparing cache coherence traffic before and after alignment changes.

Finally, measure memory bandwidth utilization using `perf stat -e cycles,instructions,mem_load_retired.l3_miss,mem_load_retired.l3_hit`. Compute the instructions-per-cycle (IPC) metric by dividing `instructions` by `cycles`. A low IPC (below 1.0) indicates pipeline stalls due to memory latency. Compute the memory-level parallelism (MLP) by dividing L3 hits by L3 misses. High MLP means the CPU successfully overlaps multiple outstanding cache misses using prefetching and out-of-order execution. If MLP is low, introduce software prefetching hints using `std::intrinsics::prefetch_read_data` or rearrange data structures to improve streaming access patterns.

This exercise transforms cache behavior from an abstract concern into a quantifiable engineering constraint. By correlating hardware counters with source code, you develop intuition for which data structure transformations—SoA conversion, alignment padding, access reordering—yield measurable throughput improvements under realistic game workloads.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Multithreaded game engines introduce concurrency hazards that manifest as non-deterministic crashes, corrupted state, and subtle logic errors. Data races violate the C++ and Rust memory models, producing undefined behavior even on modern hardware with strong memory ordering guarantees. Memory leaks accumulate over long play sessions, degrading performance and eventually exhausting address space. This exercise deploys ThreadSanitizer (TSan) to detect race conditions in parallel ECS updates and AddressSanitizer (ASan) with LeakSanitizer (LSan) to surface use-after-free bugs and memory leaks. You will construct adversarial test cases that trigger races, validate that sanitizers report violations with actionable stack traces, and refactor the code to satisfy happens-before ordering using atomic operations and proper synchronization primitives.

Begin by enabling ThreadSanitizer in your Rust build. TSan instruments memory accesses and synchronization primitives to detect races at runtime, incurring a 5–15× slowdown and 5–10× memory overhead. Add a sanitizer-enabled profile to `.cargo/config.toml`:

```toml
[profile.tsan]
inherits = "dev"
opt-level = 1

[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=thread"]

[target.x86_64-apple-darwin]
rustflags = ["-Zsanitizer=thread"]
```

Create a test case that deliberately introduces a data race. Add the following to `src/component.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use std::thread;

    #[test]
    fn test_race_condition_unsynchronized() {
        let mut components = Arc::new(std::sync::Mutex::new(TransformComponents::new(1000)));
        
        for i in 0..1000 {
            let mut c = components.lock().unwrap();
            c.add_entity(i as f32, i as f32, i as f32, 1.0, 1.0, 1.0);
        }
        
        let components_clone = Arc::clone(&components);
        let handle = thread::spawn(move || {
            let mut c = components_clone.lock().unwrap();
            c.integrate_motion(0.016);
        });
        
        {
            let mut c = components.lock().unwrap();
            c.integrate_motion(0.016);
        }
        
        handle.join().unwrap();
    }

    #[test]
    fn test_race_condition_racy_read_write() {
        let components = Arc::new(std::sync::RwLock::new(TransformComponents::new(1000)));
        
        for i in 0..1000 {
            let mut c = components.write().unwrap();
            c.add_entity(i as f32, i as f32, i as f32, 1.0, 1.0, 1.0);
        }
        
        let mut handles = vec![];
        
        for _ in 0..4 {
            let comp = Arc::clone(&components);
            handles.push(thread::spawn(move || {
                let c = comp.read().unwrap();
                let sum: f32 = c.positions_x.iter().sum();
                drop(c);
                sum
            }));
        }
        
        let comp = Arc::clone(&components);
        let writer = thread::spawn(move || {
            let mut c = comp.write().unwrap();
            c.integrate_motion(0.016);
        });
        
        for h in handles {
            h.join().unwrap();
        }
        writer.join().unwrap();
    }

    #[test]
    fn test_use_after_free_simulation() {
        let mut components = Box::new(TransformComponents::new(100));
        
        for i in 0..100 {
            components.add_entity(i as f32, i as f32, i as f32, 1.0, 1.0, 1.0);
        }
        
        let raw_ptr = &mut *components as *mut TransformComponents;
        drop(components);
        
        unsafe {
            (*raw_ptr).integrate_motion(0.016);
        }
    }

    #[test]
    fn test_memory_leak() {
        for _ in 0..1000 {
            let components = Box::new(TransformComponents::new(10000));
            std::mem::forget(components);
        }
    }
}
```

The first test uses a `Mutex` correctly, ensuring mutual exclusion. The second test uses `RwLock` correctly for concurrent reads and exclusive writes. The third test deliberately creates a use-after-free by dropping a `Box` and dereferencing the dangling pointer. The fourth test leaks memory by calling `std::mem::forget`, preventing the destructor from running.

Run the tests with ThreadSanitizer: `RUSTFLAGS="-Zsanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu`. TSan will report any detected races with stack traces showing the conflicting accesses. For the correctly synchronized tests, TSan will report no issues. For the racy test (if you introduce one by removing locks), TSan will output:

```text
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 4 at 0x7f8c4800a010 by thread T1:
    #0 integrate_motion src/component.rs:35
    #1 test_race_condition_racy_read_write::{{closure}} src/component.rs:78
  Previous read of size 4 at 0x7f8c4800a010 by thread T2:
    #0 integrate_motion src/component.rs:36
    #1 test_race_condition_racy_read_write::{{closure}} src/component.rs:72
```

The report identifies the exact source lines and thread IDs involved in the race. Use this information to insert appropriate synchronization primitives—mutexes, read-write locks, or atomic operations with explicit memory ordering.

Now enable AddressSanitizer and LeakSanitizer. Create a new sanitizer profile in `.cargo/config.toml`:

```toml
[profile.asan]
inherits = "dev"
opt-level = 1

[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=address"]

[target.x86_64-apple-darwin]
rustflags = ["-Zsanitizer=address"]
```

Run the use-after-free test: `RUSTFLAGS="-Zsanitizer=address" cargo +nightly test test_use_after_free_simulation --target x86_64-unknown-linux-gnu`. ASan will abort with a detailed report:

```text
==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x60300000eff0 at pc 0x00000051a2b4 bp 0x7ffc8e3b5a90 sp 0x7ffc8e3b5a88
WRITE of size 4 at 0x60300000eff0 thread T0
    #0 0x51a2b3 in integrate_motion src/component.rs:35:13
    #1 0x51a4f6 in test_use_after_free_simulation src/component.rs:98:13

0x60300000eff0 is located 0 bytes inside of 96-byte region [0x60300000eff0,0x60300000f050)
freed by thread T0 here:
    #0 0x4c8d3a in __rust_dealloc
    #1 0x51a3c1 in test_use_after_free_simulation src/component.rs:96:9

previously allocated by thread T0 here:
    #0 0x4c8bfa in __rust_alloc
    #1 0x51a2f9 in test_use_after_free_simulation src/component.rs:91:9
```

The report shows the allocation, deallocation, and illegal access stack traces, pinpointing the exact lifecycle violation.

Run the leak test: `RUSTFLAGS="-Zsanitizer=address" ASAN_OPTIONS=detect_leaks=1 cargo +nightly test test_memory_leak --target x86_64-unknown-linux-gnu`. LeakSanitizer will report:

```text
==12345==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 96000 byte(s) in 1000 object(s) allocated from:
    #0 0x4c8bfa in __rust_alloc
    #1 0x51a5c2 in test_memory_leak src/component.rs:103:13

SUMMARY: AddressSanitizer: 96000 byte(s) leaked in 1000 allocation(s).
```

The report quantifies the total leaked memory and identifies the allocation site. Use this to locate and fix the leak by ensuring proper cleanup in destructors or RAII wrappers.

To stress-test concurrent code, create a randomized fuzzing harness using `proptest` or `quickcheck`. Define property-based tests that generate random sequences of reads, writes, and synchronization operations, then verify invariants such as sum preservation or monotonic counter increments. Run the fuzzer with ThreadSanitizer enabled to surface rare race conditions that only manifest under specific interleavings.

For production deployment, integrate sanitizer runs into your CI pipeline. Configure GitHub Actions or GitLab CI to execute a sanitizer-enabled test suite on every pull request. Use the `TSAN_OPTIONS` and `ASAN_OPTIONS` environment variables to customize reports: `TSAN_OPTIONS=halt_on_error=1:second_deadlock_stack=1` aborts on the first race and prints full deadlock information. `ASAN_OPTIONS=detect_stack_use_after_return=1:check_initialization_order=1` enables additional checks for stack-allocated variables and static initialization order.

Compare the sanitizer results between Rust and C++ implementations. In C++, compile with `-fsanitize=thread` and `-fsanitize=address` flags. Clang's sanitizers share the same instrumentation infrastructure as Rust's, but C++ code is more susceptible to races due to manual memory management and lack of borrow checking. You will observe that Rust's ownership system prevents entire classes of bugs at compile time, reducing the runtime sanitizer workload to logical races in `unsafe` blocks and FFI boundaries.

This exercise establishes a rigorous testing discipline that catches concurrency and memory safety bugs before they reach production. By integrating sanitizers into your development workflow, you transform debugging from reactive crash triage into proactive invariant enforcement, ensuring that your game engine satisfies the strict memory model guarantees required by modern multithreaded architectures.

## Developer Cheat Sheet & Toolchain Checklist

This section provides a consolidated reference for the diagnostic commands, compiler flags, and debugging workflows used throughout the laboratory exercises. Bookmark this page for quick access during production troubleshooting and performance optimization sessions.

### Compilation and IR Inspection

Emit LLVM IR and assembly from Rust: `cargo rustc --release -- --emit=llvm-ir,asm`. Locate artifacts in `target/release/deps/`. Emit HIR for desugared code: `cargo rustc -- -Z unpretty=hir`. Emit optimization remarks: `cargo rustc --release -- -C llvm-args=-pass-remarks=inline,loop-vectorize`.

Emit LLVM IR from C++: `clang++ -O3 -march=native -S -emit-llvm source.cpp -o output.ll`. Emit assembly: `clang++ -O3 -march=native -S source.cpp -o output.s`. Enable optimization remarks: `clang++ -O3 -Rpass=inline -Rpass=loop-vectorize source.cpp`.

Disassemble Rust static library: `objdump -d target/release/libproject.rlib`. Disassemble C++ object file: `objdump -d output.o`. Use `--demangle` to decode Rust/C++ mangled names.

### Performance Profiling with Hardware Counters

Profile cache behavior on Linux: `perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses command`. Compute L1 miss rate: `(L1-dcache-load-misses / L1-dcache-loads) * 100`. Compute LLC miss rate: `(LLC-load-misses / LLC-loads) * 100`.

Record call graph with DWARF unwinding: `perf record -g --call-graph=dwarf command`. Analyze with annotated assembly: `perf report`, navigate to function, press `a`. Generate flame graph: `cargo flamegraph --bench benchmark_name`.

Detect false sharing: `perf c2c record command`, then `perf c2c report`. Inspect cache line invalidations and identify hot cache lines.

Measure IPC and memory bandwidth: `perf stat -e cycles,instructions,mem_load_retired.l3_miss,mem_load_retired.l3_hit command`. Compute IPC: `instructions / cycles`. Compute MLP: `mem_load_retired.l3_hit / mem_load_retired.l3_miss`.

On macOS, use Instruments Time Profiler and System Trace templates. Build with debug symbols: `cargo build --release`. Import binary into Instruments and record profile.

### Dynamic Analysis with Sanitizers

Enable ThreadSanitizer in Rust: `RUSTFLAGS="-Zsanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu`. Configure TSan options: `TSAN_OPTIONS=halt_on_error=1:second_deadlock_stack=1`.

Enable AddressSanitizer and LeakSanitizer: `RUSTFLAGS="-Zsanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu`. Configure ASan options: `ASAN_OPTIONS=detect_leaks=1:detect_stack_use_after_return=1:check_initialization_order=1`.

Enable sanitizers in C++: compile with `-fsanitize=thread` or `-fsanitize=address`. Link with sanitizer runtime: `-fsanitize=thread` automatically links `libtsan`. For ASan: `-fsanitize=address` links `libasan`.

Interpret TSan reports: look for "data race" warnings with conflicting read/write stack traces. Identify the shared variable address and source lines. Insert synchronization primitives (mutexes, atomics with `Ordering::SeqCst` or stronger) at the reported locations.

Interpret ASan reports: heap-use-after-free shows allocation, deallocation, and illegal access traces. Stack-use-after-return indicates returning pointers to stack variables. Global-buffer-overflow detects out-of-bounds accesses to static arrays. Fix by ensuring proper lifetime management and bounds checks.

### Debugger Integration

Launch Rust binary in LLDB: `rust-lldb target/release/binary`. Launch in GDB: `rust-gdb target/release/binary`. Set breakpoints: `b component.rs:35`. Run: `r`. Step: `s` (step into), `n` (step over), `c` (continue). Inspect variables: `p variable_name`. Print backtrace: `bt`.

Conditional breakpoints: `b component.rs:35 if i == 500`. Watch variables: `watch components.count`. Catch panics: `catch throw` (GDB), `break rust_panic` (LLDB).

Attach to running process: `gdb -p PID` or `lldb -p PID`. Useful for debugging hangs or infinite loops in production.

### Benchmark Execution and Comparison

Run Criterion benchmarks: `cargo bench --bench benchmark_name`. Generate baseline: `cargo bench --bench benchmark_name -- --save-baseline baseline_name`. Compare against baseline: `cargo bench --bench benchmark_name -- --baseline baseline_name`.

Criterion outputs statistical summaries with confidence intervals. Look for "change" percentages to quantify performance impact of refactorings. A change of ±5% is typically within noise; ±10% or more indicates a real effect.

Run micro-benchmarks with controlled CPU affinity: `taskset -c 0 cargo bench --bench benchmark_name`. This pins execution to a single core, reducing variance from scheduler migrations.

### Memory Profiling with Valgrind

Profile heap allocations: `valgrind --tool=massif target/release/binary`. Analyze with `ms_print massif.out.<pid>`. The output shows heap usage over time, identifying allocation spikes and leaks.

Detect memory leaks: `valgrind --leak-check=full target/release/binary`. Valgrind reports "definitely lost" (unreachable allocations) and "possibly lost" (pointers lost due to aliasing). Fix by ensuring proper `Drop` implementations and avoiding `std::mem::forget`.

Profile cache behavior: `valgrind --tool=cachegrind target/release/binary`. Analyze with `cg_annotate cachegrind.out.<pid>`. The output shows instruction-level cache miss rates, L1/L2/LLC hit rates, and branch prediction accuracy.

### Toolchain Version Management

List installed Rust toolchains: `rustup toolchain list`. Install nightly: `rustup toolchain install nightly`. Set default: `rustup default nightly`. Override for specific project: `rustup override set nightly`.

Update toolchains: `rustup update`. Check current version: `rustc --version`, `cargo --version`. Install specific component: `rustup component add llvm-tools-preview`.

Verify LLVM version: `clang --version`, `llvm-config --version`. Ensure version 15+ for modern sanitizer features. On macOS, verify Xcode Command Line Tools: `xcode-select --install`.

### Continuous Integration Sanitizer Integration

Add sanitizer job to GitHub Actions `.github/workflows/ci.yml`:

```yaml
name: Sanitizer Tests

on: [push, pull_request]

jobs:
  tsan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: nightly
          override: true
      - name: Run ThreadSanitizer
        run: |
          RUSTFLAGS="-Zsanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu
        env:
          TSAN_OPTIONS: halt_on_error=1

  asan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: nightly
          override: true
      - name: Run AddressSanitizer
        run: |
          RUSTFLAGS="-Zsanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu
        env:
          ASAN_OPTIONS: detect_leaks=1
```

Configure sanitizers to fail CI on any violation: `halt_on_error=1` for TSan, `exitcode=1` for ASan.

### Quick Diagnostic Workflow

For performance regression: run `cargo bench` with baseline comparison. If throughput drops, profile with `perf record` and flame graph to identify hot spots. Check cache miss rates with `perf stat`. If L1 miss rate exceeds 10%, audit data structure layout for cache-unfriendly patterns.

For crash or undefined behavior: build with ASan and reproduce. ASan will report the exact violation. If race suspected, run with TSan. For memory leaks, run with LSan. For stack corruption, enable ASan stack checks.

For optimization verification: emit LLVM IR and assembly. Search for target function in `.ll` file. Verify inlining (no function call preamble), vectorization (SIMD vector types), and loop unrolling (repeated instruction sequences). If optimizations missing, check aliasing, bounds checks, and inline hints.

This cheat sheet codifies the empirical verification workflow that separates effective performance engineering from speculative optimization. By systematically applying these tools to each code change, you build a quantitative understanding of how high-level design decisions propagate through the compilation pipeline to affect runtime behavior at the cache line and instruction level.
