# Operational Verification Labs: Software Architecture

## Objective & Toolchain Setup

This guide treats the compiler toolchain as a diagnostic instrument, not just a build system. Each exercise is designed to make invisible architectural decisions visible: how the compiler transforms source into machine code, how memory layout drives cache performance, and how concurrency bugs manifest under sanitizer pressure. By the end of these labs you will be able to read LLVM IR, interpret flamegraph call trees, and correlate ThreadSanitizer reports with specific synchronization defects in your own codebase.

The labs are written for a Linux host (x86-64, kernel 5.15 or later). The commands assume `bash`. Everything compiles and runs on bare metal or inside a Docker container with `--privileged` for `perf` syscall access.

**Install the full toolchain** with the following sequence. Begin with Rust via `rustup`, which manages both the stable and nightly toolchains you need for some of the profiling extensions:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
source "$HOME/.cargo/env"
rustup toolchain install nightly
rustup component add llvm-tools-preview rust-src
cargo install cargo-flamegraph cargo-asm flamegraph
```

Install the system-level LLVM and Clang suite alongside Valgrind and Linux `perf`. On Debian/Ubuntu:

```bash
sudo apt-get update && sudo apt-get install -y \
    clang-15 llvm-15 llvm-15-tools \
    lld-15 \
    valgrind \
    linux-perf \
    linux-tools-$(uname -r) \
    gdb lldb \
    build-essential \
    libssl-dev pkg-config
```

Create symlinks so that bare `clang`, `llvm-objdump`, and `opt` resolve to version 15:

```bash
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-15 100
sudo update-alternatives --install /usr/bin/llvm-objdump llvm-objdump /usr/bin/llvm-objdump-15 100
sudo update-alternatives --install /usr/bin/opt opt /usr/bin/opt-15 100
```

For `perf` to record kernel call stacks without root, relax the paranoia level for the duration of the lab session:

```bash
echo 1 | sudo tee /proc/sys/kernel/perf_event_paranoid
echo 0 | sudo tee /proc/sys/kernel/kptr_restrict
```

Initialize the lab workspace:

```bash
mkdir -p ~/arch-labs && cd ~/arch-labs
cargo new --lib arch_lab_rs
```

---

## Exercise 1: AST, IR & Disassembly Analysis

### Theory Anchor

Every source file you write passes through a staged pipeline before it touches hardware. In Clang/LLVM that pipeline is: source text → Clang AST → LLVM IR (SSA form) → target-independent MIR → machine code. In `rustc` the equivalent stages are: source → HIR → MIR → LLVM IR → machine code. Understanding where your architectural decisions live inside this pipeline tells you where to look when performance, correctness, or binary size surprises you. A function you believe to be inlined may still appear as a call in the IR. A branch you believe is eliminated by the optimizer may survive all the way to the final `.text` section. These labs make that journey concrete and auditable.

LLVM IR is typed, in Static Single Assignment (SSA) form, and architecture-independent. Every local value is defined exactly once and flows forward. Phi nodes at the entry of basic blocks merge values from multiple predecessor paths. When you read IR you are reading the optimizer's working memory: the form it uses to apply dead code elimination, loop invariant code motion, and auto-vectorization before it ever considers register allocation.

### Part A: Clang AST and IR Emission

Create a small but architecturally interesting C++ source file. The function below contains a matrix-vector multiply loop, an early-exit branch, and a forced inline helper. Each of these will produce distinct artifacts at the AST, IR, and disassembly levels.

```cpp
// file: arch_labs/matvec.cpp
#include <cstddef>
#include <cstdint>

__attribute__((always_inline))
static float dot4(const float* __restrict__ a,
                  const float* __restrict__ b) {
    float acc = 0.0f;
    for (int i = 0; i < 4; ++i)
        acc += a[i] * b[i];
    return acc;
}

float matvec(const float* __restrict__ mat,
             const float* __restrict__ vec,
             float*       __restrict__ out,
             std::size_t              rows) {
    if (rows == 0) return 0.0f;
    float checksum = 0.0f;
    for (std::size_t r = 0; r < rows; ++r) {
        out[r] = dot4(mat + r * 4, vec);
        checksum += out[r];
    }
    return checksum;
}
```

Dump the full Clang AST. The `-ast-dump` flag causes the compiler front-end to halt after parsing and semantic analysis, printing the entire syntax tree in a readable indented format:

```bash
cd ~/arch-labs
clang -std=c++17 -Xclang -ast-dump -fsyntax-only arch_labs/matvec.cpp 2>&1 | less
```

Look for the `FunctionDecl` node for `matvec`. Observe that `dot4` appears as a `CallExpr` referencing the `FunctionDecl` for `dot4` inside the loop body. The AST knows nothing about inlining yet — that decision belongs to the IR optimizer. The `__attribute__((always_inline))` annotation is stored as an `AnnotateAttr` node attached to `dot4`'s declaration, which the IR generator will honor when it emits the first IR.

Now emit unoptimized LLVM IR:

```bash
clang -std=c++17 -S -emit-llvm -O0 \
    -o arch_labs/matvec.O0.ll \
    arch_labs/matvec.cpp
```

Open `matvec.O0.ll` and find the definition of `@_Z6matvec...`. Notice the alloca instructions at the top of the entry block: every local variable has been stack-allocated, even `r` and `checksum`. The loop is an explicit `br` instruction between labeled basic blocks. The `dot4` function has already been inlined at O0 because of `always_inline`; you will not find a `call` to `dot4` in the IR.

Now emit optimized IR at O3 and compare:

```bash
clang -std=c++17 -S -emit-llvm -O3 -march=native \
    -o arch_labs/matvec.O3.ll \
    arch_labs/matvec.cpp
```

The structure changes dramatically. The allocas are gone, replaced by SSA values carried directly through phi nodes. The inner loop over four elements has been vectorized into a `<4 x float>` multiply-add sequence using `llvm.fmuladd`. Count the basic blocks in the O0 IR versus the O3 IR for `matvec` and note the reduction. The O3 version may have between two and four blocks (entry, loop header, loop body, exit) compared to ten or more in O0.

To inspect how individual LLVM optimization passes transform the IR, use the `opt` tool directly with the new pass manager syntax:

```bash
# Emit bitcode from the O0 IR first
llvm-as arch_labs/matvec.O0.ll -o arch_labs/matvec.O0.bc

# Apply only loop vectorization and print the result
opt -passes="loop-vectorize,instcombine,simplifycfg" \
    -S arch_labs/matvec.O0.bc \
    -o arch_labs/matvec.vec.ll

# Diff the before and after
diff <(grep -v "^;" arch_labs/matvec.O0.ll) \
     <(grep -v "^;" arch_labs/matvec.vec.ll) | head -60
```

### Part B: Disassembly Correlation

Compile `matvec.cpp` to a shared object and disassemble it, correlating the assembly back to the IR:

```bash
clang -std=c++17 -O3 -march=native -shared -fPIC \
    -g -o arch_labs/libmatvec.so arch_labs/matvec.cpp

llvm-objdump -d --source --demangle arch_labs/libmatvec.so \
    | grep -A 60 "<matvec"
```

On x86-64 with AVX2 available you should see `vmovups`, `vfmadd213ps`, or equivalent fused multiply-add vector instructions operating on 128- or 256-bit YMM registers. The four-element dot product that was written as a scalar loop in source code has been fully unrolled and reduced to a single vector instruction sequence. Identify the loop induction variable in the disassembly: it will be a register incremented by 16 (four floats × four bytes) per iteration rather than by 1.

Now build the equivalent in Rust and compare the codegen. Add this to `~/arch-labs/arch_lab_rs/src/lib.rs`:

```rust
// src/lib.rs

#[inline(always)]
fn dot4(a: &[f32; 4], b: &[f32; 4]) -> f32 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
}

#[no_mangle]
pub extern "C" fn matvec_rs(
    mat: *const f32,
    vec_in: *const f32,
    out: *mut f32,
    rows: usize,
) -> f32 {
    if rows == 0 {
        return 0.0;
    }
    let vec_arr: &[f32; 4] = unsafe { &*(vec_in as *const [f32; 4]) };
    let mut checksum = 0.0f32;
    for r in 0..rows {
        let row_ptr = unsafe { mat.add(r * 4) as *const [f32; 4] };
        let row: &[f32; 4] = unsafe { &*row_ptr };
        let result = dot4(row, vec_arr);
        unsafe { *out.add(r) = result };
        checksum += result;
    }
    checksum
}
```

Build with `RUSTFLAGS` to target the native CPU and emit LLVM IR:

```bash
cd ~/arch-labs/arch_lab_rs

RUSTFLAGS="-C target-cpu=native --emit=llvm-ir" \
    cargo build --release 2>/dev/null

# Find the emitted IR file
find target/release -name "*.ll" | head -5
```

Use `cargo-asm` to get a human-readable disassembly of `matvec_rs` without navigating the build artifacts manually:

```bash
cargo asm --release arch_lab_rs::matvec_rs 2>/dev/null || \
    cargo asm --release "matvec_rs"
```

Compare the Rust-generated assembly against the Clang output. Both should produce nearly identical vector instruction sequences for this workload because both are compiled by LLVM at the same optimization level. The difference, if any, will be in how `rustc` and `clang` chose to emit bounds check elimination or loop unrolling hints.

### Part C: Measuring the IR Transformation Budget

A meaningful architectural question is: how much does each optimization level cost in compile time, and what does it buy in code size? Run this measurement directly:

```bash
# Measure compile time at each opt level
for OPT in O0 O1 O2 O3 Os Oz; do
    TIME=$( { time clang -std=c++17 -${OPT} -march=native \
        -c -o /tmp/matvec_${OPT}.o arch_labs/matvec.cpp; } 2>&1 \
        | grep real | awk '{print $2}' )
    SIZE=$(size /tmp/matvec_${OPT}.o | tail -1 | awk '{print $1}')
    echo "${OPT}: text_bytes=${SIZE}  compile_time=${TIME}"
done
```

The `.text` section at O0 will be several times larger than at Os or Oz because every variable access goes through a stack round-trip. At O3 with `-march=native` the section is typically smaller than O0 despite doing more work, because inlining and vectorization eliminate scaffolding code.

---

## Exercise 2: Cache Miss & Throughput Profiling

### Theory Anchor

Modern CPUs execute arithmetic in picoseconds but wait nanoseconds to microseconds for memory. An L1 cache hit on a 3 GHz processor costs roughly one cycle, or 0.33 ns. An L3 miss that falls through to DRAM costs 50–200 ns, a factor of 150–600 slower. A software architecture that places logically related data in discontiguous memory, such as a classic object-oriented design with virtual dispatch through pointer-chased vtables, can spend the majority of its wall time stalled on cache fills rather than executing the instructions you care about. `perf stat` with hardware performance counters, combined with flamegraph visualization, makes this structural problem empirically auditable rather than hypothetical.

The root mechanism is the cache line: 64 bytes on x86-64, fetched atomically from the cache hierarchy. When you access one byte of a struct, the entire 64-byte line containing it is fetched. If your access pattern causes the hardware prefetcher to fail — because addresses are computed rather than strided — you pay a full DRAM round-trip for every cache miss. Structures of Arrays (SoA) versus Arrays of Structures (AoS) is the canonical architectural decision that this exercise makes measurable.

### Part A: Building the Benchmark

Write a complete benchmark that compares AoS and SoA layouts for a particle simulation update loop. Create `~/arch-labs/cache_bench/src/main.rs`:

```bash
cargo new --bin cache_bench
cd cache_bench
```

Replace `src/main.rs` with:

```rust
// src/main.rs
use std::time::Instant;

const N: usize = 1 << 22; // 4 million particles

// Arrays of Structures: each particle is a contiguous object.
// Accessing only position.x during a velocity-only update
// still pulls the entire 32-byte struct into cache.
#[repr(C)]
struct ParticleAoS {
    x: f32, y: f32, z: f32,
    vx: f32, vy: f32, vz: f32,
    mass: f32,
    padding: f32,
}

// Structure of Arrays: each field is its own contiguous array.
// A velocity-only update reads only the vx/vy/vz arrays,
// achieving perfect spatial locality.
struct ParticleSoA {
    x:    Vec<f32>,
    y:    Vec<f32>,
    z:    Vec<f32>,
    vx:   Vec<f32>,
    vy:   Vec<f32>,
    vz:   Vec<f32>,
    mass: Vec<f32>,
}

fn build_aos(n: usize) -> Vec<ParticleAoS> {
    (0..n).map(|i| ParticleAoS {
        x:  (i as f32) * 0.001,
        y:  (i as f32) * 0.002,
        z:  (i as f32) * 0.003,
        vx: (i as f32) * 0.0001,
        vy: (i as f32) * 0.0002,
        vz: (i as f32) * 0.0003,
        mass: 1.0,
        padding: 0.0,
    }).collect()
}

fn build_soa(n: usize) -> ParticleSoA {
    ParticleSoA {
        x:    (0..n).map(|i| (i as f32) * 0.001).collect(),
        y:    (0..n).map(|i| (i as f32) * 0.002).collect(),
        z:    (0..n).map(|i| (i as f32) * 0.003).collect(),
        vx:   (0..n).map(|i| (i as f32) * 0.0001).collect(),
        vy:   (0..n).map(|i| (i as f32) * 0.0002).collect(),
        vz:   (0..n).map(|i| (i as f32) * 0.0003).collect(),
        mass: vec![1.0f32; n],
    }
}

#[inline(never)]
fn update_positions_aos(particles: &mut Vec<ParticleAoS>, dt: f32) {
    for p in particles.iter_mut() {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.z += p.vz * dt;
    }
}

#[inline(never)]
fn update_positions_soa(soa: &mut ParticleSoA, dt: f32) {
    let n = soa.x.len();
    for i in 0..n {
        soa.x[i] += soa.vx[i] * dt;
        soa.y[i] += soa.vy[i] * dt;
        soa.z[i] += soa.vz[i] * dt;
    }
}

fn bench<F: FnMut()>(label: &str, mut f: F, iterations: u32) {
    // Warm-up: one iteration before timing
    f();
    let start = Instant::now();
    for _ in 0..iterations {
        f();
    }
    let elapsed = start.elapsed();
    println!("{}: {:.3} ms/iter  ({} iters)",
        label,
        elapsed.as_secs_f64() * 1000.0 / iterations as f64,
        iterations
    );
}

fn main() {
    println!("Allocating {} particles...", N);
    let mut aos = build_aos(N);
    let mut soa = build_soa(N);

    println!("AoS struct size: {} bytes", std::mem::size_of::<ParticleAoS>());
    println!("AoS total heap:  {} MiB",
        (N * std::mem::size_of::<ParticleAoS>()) / (1024 * 1024));
    println!("SoA total heap:  {} MiB",
        (N * 7 * 4) / (1024 * 1024));
    println!();

    let dt = 0.016_f32;

    bench("AoS position update", || update_positions_aos(&mut aos, dt), 10);
    bench("SoA position update", || update_positions_soa(&mut soa, dt), 10);
}
```

Build and run with the native CPU target:

```bash
RUSTFLAGS="-C target-cpu=native" cargo build --release
./target/release/cache_bench
```

On a typical modern x86-64 workstation the SoA update will run 1.5x–3x faster than the AoS update. The SoA loop reads only the `x`, `vx`, `y`, `vy`, `z`, and `vz` arrays — six contiguous streams that the hardware prefetcher can saturate. The AoS loop reads all eight fields of every 32-byte struct even though it uses only six of them, and each iteration advances the pointer by 32 bytes, reducing effective cache line utilization to 75%.

### Part B: Measuring with `perf stat`

The wall-time difference is real, but `perf stat` lets you see the hardware cause. Instrument both paths separately by wrapping them in standalone binaries, or use `perf stat` on the full benchmark and read the LLC miss rate:

```bash
perf stat -e cache-references,cache-misses,L1-dcache-loads,\
L1-dcache-load-misses,LLC-load-misses,cycles,instructions \
    ./target/release/cache_bench 2>&1
```

You are looking for two key ratios. The `cache-miss` rate (cache-misses / cache-references) will be meaningfully higher for the AoS run because the struct stride of 32 bytes means only two full objects fit per 64-byte cache line, and the update loop discards mass and padding fields after fetching them. The `LLC-load-misses` count measures the pressure on DRAM bandwidth. For a 4M × 32-byte AoS buffer the working set is 128 MiB, guaranteed to exceed a typical 8–32 MiB L3 cache and produce sustained DRAM traffic.

### Part C: Flamegraph Profiling

`cargo-flamegraph` wraps `perf record` and `flamegraph.pl` into a single ergonomic command. It records a CPU-time flamegraph by sampling the call stack at 99 Hz with hardware performance counter support:

```bash
# Allow perf to record without root inside the session
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid

RUSTFLAGS="-C target-cpu=native" \
    cargo flamegraph --bin cache_bench -- 2>/dev/null

# Opens flamegraph.svg in the current directory
ls -lh flamegraph.svg
```

Open `flamegraph.svg` in a browser. The x-axis is cumulative CPU time, not wall time. Each frame's width is proportional to the percentage of samples where that frame was at the top of the call stack (i.e., where the CPU was actually spending time). `update_positions_aos` and `update_positions_soa` will each occupy a horizontal band. If you see `__memcpy_avx_unaligned` or similar glibc memory primitives appearing adjacent to the AoS frame, that is evidence of prefetch-miss stalls materializing as time the CPU spends waiting for the memory subsystem between the actual compute instructions.

For a more surgical view, isolate just the update functions using `perf record` with the `--call-graph dwarf` option, which captures full stack traces via DWARF unwind information rather than frame-pointer chains:

```bash
RUSTFLAGS="-C target-cpu=native -C force-frame-pointers=yes" \
    cargo build --release

perf record --call-graph fp -F 999 \
    ./target/release/cache_bench

perf report --stdio --no-children -g fractal,0.5,caller \
    | head -80
```

The `--call-graph fp` option uses frame pointers (hence `-C force-frame-pointers=yes`) for fast, low-overhead unwinding. The report shows self-time (time spent in the function itself, not in callees) and child-time separately, which lets you see that `update_positions_aos` has high self-time meaning the CPU is burning cycles inside the function itself waiting for data, rather than making call-site overhead.

### Part D: Cargo Bench with Criterion

For reproducible micro-benchmarks with statistical confidence intervals, add Criterion to the workspace. Add to `Cargo.toml`:

```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "layout"
harness = false
```

Create `benches/layout.rs`:

```rust
// benches/layout.rs
use cache_bench::{
    build_aos, build_soa,
    update_positions_aos, update_positions_soa,
};
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

pub fn criterion_benchmark(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_layout");
    group.sample_size(20);

    for n in [1 << 18, 1 << 20, 1 << 22] {
        let mut aos = build_aos(n);
        group.bench_with_input(BenchmarkId::new("AoS", n), &n, |b, _| {
            b.iter(|| update_positions_aos(&mut aos, 0.016))
        });

        let mut soa = build_soa(n);
        group.bench_with_input(BenchmarkId::new("SoA", n), &n, |b, _| {
            b.iter(|| update_positions_soa(&mut soa, 0.016))
        });
    }
    group.finish();
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
```

For the bench to compile you need to expose the functions from `src/lib.rs`. Move the struct definitions and functions into `src/lib.rs`, make them `pub`, and add `pub use` re-exports from `src/main.rs`. Then run:

```bash
RUSTFLAGS="-C target-cpu=native" cargo bench --bench layout
```

Criterion prints throughput with 95% confidence intervals and flags whether the result is statistically different from the previous run. It also generates an HTML report in `target/criterion/memory_layout/report/index.html` with violin plots showing the distribution of iteration times. These plots reveal whether the variance is caused by OS scheduling jitter (uniform distribution) or by cache-miss behavior (heavy right tail from occasional DRAM trips).

---

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

### Theory Anchor

A data race occurs when two threads access the same memory location concurrently, at least one access is a write, and there is no synchronization ordering the two accesses. The C++ and Rust memory models both define data races as undefined behavior, which means the compiler is free to assume they do not occur and to generate code that is incorrect when they do. ThreadSanitizer (TSan) instruments every memory access and lock operation at compile time, maintaining a happens-before graph at runtime that catches races deterministically rather than relying on scheduling timing. LeakSanitizer (LSan) intercepts the allocator and walks the heap at program exit, reporting every allocation that was not freed and not reachable from a root pointer. Both tools are essential: TSan finds errors that appear only under specific scheduling interleavings, and LSan finds errors that may never produce a crash but silently drain process memory over hours.

### Part A: Planting and Detecting a Data Race in C++

Create a deliberately racy C++ program that simulates a concurrent counter pattern — the classic mistake of assuming that increment is atomic:

```bash
mkdir -p ~/arch-labs/race_lab
```

```cpp
// ~/arch-labs/race_lab/counter_race.cpp
#include <cstdint>
#include <cstdio>
#include <thread>
#include <vector>

// Shared mutable state without synchronization.
// The read-modify-write sequence is NOT atomic on x86-64:
// it compiles to a load, add, store sequence that is
// interruptible between any two operations.
static uint64_t g_counter = 0;

static void increment_loop(uint64_t iterations) {
    for (uint64_t i = 0; i < iterations; ++i) {
        // This is a data race: no mutex, no std::atomic<>.
        ++g_counter;
    }
}

int main() {
    constexpr int    kThreads    = 8;
    constexpr uint64_t kIterations = 100'000;

    std::vector<std::thread> workers;
    workers.reserve(kThreads);

    for (int t = 0; t < kThreads; ++t)
        workers.emplace_back(increment_loop, kIterations);

    for (auto& th : workers)
        th.join();

    uint64_t expected = (uint64_t)kThreads * kIterations;
    printf("Expected: %lu\n", expected);
    printf("Got:      %lu\n", g_counter);
    printf("Lost:     %lu increments (%.2f%%)\n",
           expected - g_counter,
           100.0 * (expected - g_counter) / expected);

    return 0;
}
```

First build and run without sanitizers to show the race producing incorrect results:

```bash
cd ~/arch-labs/race_lab

clang++ -std=c++17 -O1 -pthread \
    -o counter_race counter_race.cpp

./counter_race
./counter_race
./counter_race
```

You will get a different wrong answer each run. On a machine with eight hardware threads and 800,000 total increments the actual count will typically land between 100,000 and 800,000, depending on how the kernel scheduled the threads. Now build with TSan:

```bash
clang++ -std=c++17 -O1 -pthread \
    -fsanitize=thread \
    -fno-omit-frame-pointer \
    -g \
    -o counter_race_tsan counter_race.cpp

./counter_race_tsan 2>&1 | head -40
```

TSan will emit a report immediately on the first detected race, before the program exits. The report structure is:

```text
WARNING: ThreadSanitizer: data race (pid=XXXXX)
  Write of size 8 at 0x... by thread T2:
    #0 increment_loop(unsigned long)
       counter_race.cpp:17:9
  Previous write of size 8 at 0x... by thread T1:
    #0 increment_loop(unsigned long)
       counter_race.cpp:17:9
  Location is global 'g_counter' ...
```

TSan's report names the two conflicting accesses, their memory addresses, the source file lines, and the thread identifiers. It captures the full stack at the moment of the conflicting access, not at some arbitrary later point. This precision is what makes TSan reports actionable: you get the exact line and the exact two threads involved.

Fix the race by converting `g_counter` to `std::atomic<uint64_t>` and confirm TSan reports nothing:

```cpp
// counter_race_fixed.cpp  (save separately to verify the fix)
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <thread>
#include <vector>

static std::atomic<uint64_t> g_counter{0};

static void increment_loop(uint64_t iterations) {
    for (uint64_t i = 0; i < iterations; ++i)
        g_counter.fetch_add(1, std::memory_order_relaxed);
}

int main() {
    constexpr int      kThreads    = 8;
    constexpr uint64_t kIterations = 100'000;

    std::vector<std::thread> workers;
    workers.reserve(kThreads);
    for (int t = 0; t < kThreads; ++t)
        workers.emplace_back(increment_loop, kIterations);
    for (auto& th : workers)
        th.join();

    uint64_t expected = (uint64_t)kThreads * kIterations;
    uint64_t got      = g_counter.load(std::memory_order_seq_cst);
    printf("Expected: %lu  Got: %lu  Match: %s\n",
           expected, got, expected == got ? "YES" : "NO");
    return 0;
}
```

```bash
clang++ -std=c++17 -O1 -pthread \
    -fsanitize=thread \
    -fno-omit-frame-pointer \
    -g \
    -o counter_fixed_tsan counter_race_fixed.cpp

./counter_fixed_tsan 2>&1
```

TSan should exit silently with no warnings and the count should match exactly every run.

### Part B: ThreadSanitizer on Rust

Rust's ownership model prevents most data races at compile time, but `unsafe` code, `Arc<Mutex<T>>` misuse, and lock-free structures using raw `AtomicPtr` can still introduce races. TSan in Rust is a first-class toolchain feature via `rustup`'s nightly toolchain:

```bash
cd ~/arch-labs/arch_lab_rs
```

Add a deliberately unsafe concurrent module to `src/lib.rs`:

```rust
// Add to src/lib.rs

use std::sync::Arc;
use std::thread;

/// This function contains a classic TOCTOU data race using
/// unsafe raw pointer aliasing across thread boundaries.
/// It is intentionally wrong to demonstrate TSan detection.
#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub fn racy_shared_write() -> u64 {
    let shared: Arc<std::cell::UnsafeCell<u64>> =
        Arc::new(std::cell::UnsafeCell::new(0));

    let handles: Vec<_> = (0..4).map(|_| {
        let s = Arc::clone(&shared);
        thread::spawn(move || {
            for _ in 0..25_000u64 {
                // SAFETY: intentionally unsound - multiple threads
                // write to the same address without synchronization.
                unsafe {
                    let ptr = s.get();
                    let val = ptr.read_volatile();
                    ptr.write_volatile(val + 1);
                }
            }
        })
    }).collect();

    for h in handles { h.join().unwrap(); }
    unsafe { *shared.get() }
}
```

Add a test that calls the racy function:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_racy_write_tsan() {
        let result = racy_shared_write();
        // The result will be wrong due to races, but we want TSan to catch it.
        println!("Result (expect ~100000): {}", result);
    }
}
```

Run the test with TSan via the nightly toolchain:

```bash
RUSTFLAGS="-Z sanitizer=thread" \
    cargo +nightly test \
    --target x86_64-unknown-linux-gnu \
    -- --nocapture test_racy_write_tsan 2>&1 | head -50
```

TSan will intercept the racy `write_volatile` calls and emit a data race report with Rust-demangled symbol names and source line numbers. The report format is identical to the C++ TSan output because both use the same LLVM TSan runtime.

### Part C: AddressSanitizer and LeakSanitizer

AddressSanitizer (ASan) detects heap buffer overflows, use-after-free, stack buffer overflows, and use-after-return. LeakSanitizer runs as an optional component of ASan and fires at process exit. Create a C++ program that exercises both a heap overflow and a deliberate leak:

```cpp
// ~/arch-labs/race_lab/asan_demo.cpp
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cstdio>

struct Config {
    char  name[16];
    int   value;
};

// Leaks: allocates a Config but never frees it.
// This simulates a one-time initialization that
// forgets to register a cleanup handler.
static Config* g_leaked_config = nullptr;

void init_config(const char* name, int value) {
    g_leaked_config = static_cast<Config*>(malloc(sizeof(Config)));
    // Bug: strncpy does not null-terminate when src >= n chars.
    // If name is exactly 16 bytes, name[16] through name[15+extra]
    // will be written past the end of the struct.
    strncpy(g_leaked_config->name, name, sizeof(Config::name));
    g_leaked_config->value = value;
    // Deliberate heap buffer overflow: write one byte past the struct.
    char* raw = reinterpret_cast<char*>(g_leaked_config);
    raw[sizeof(Config)] = 0xFF;  // out-of-bounds write
}

int main(int argc, char** argv) {
    const char* cfg_name = (argc > 1) ? argv[1] : "default-config-name";
    init_config(cfg_name, 42);

    printf("Config name:  %.16s\n", g_leaked_config->name);
    printf("Config value: %d\n",   g_leaked_config->value);

    // g_leaked_config is never freed: LSan will report this.
    return 0;
}
```

Build and run with both ASan and LSan:

```bash
clang++ -std=c++17 -O1 \
    -fsanitize=address \
    -fno-omit-frame-pointer \
    -g \
    -o asan_demo race_lab/asan_demo.cpp

ASAN_OPTIONS=detect_leaks=1 ./asan_demo 2>&1
```

ASan will halt the program on the out-of-bounds write to `raw[sizeof(Config)]` and print:

```text
==XXXXX==ERROR: AddressSanitizer: heap-buffer-overflow
WRITE of size 1 at 0x... thread T0
    #0 0x... in init_config asan_demo.cpp:28
    ...
Shadow bytes around the buggy address: ...
```

The shadow byte map shows the memory state around the fault: each byte of output encodes whether the corresponding 8 bytes of real memory are addressable (`00`), partially addressable, or in a redzone (marked with `fa` for heap redzone). This encoding is the core mechanism of ASan: it maintains a parallel shadow memory at a fixed offset, writing 1 shadow byte per 8 bytes of application memory, and instruments every load and store to check the shadow before the actual access.

Fix the overflow by removing the `raw[sizeof(Config)]` write, then rerun to see only the leak report:

```bash
# Edit asan_demo.cpp: remove line 28 (raw[sizeof(Config)] = 0xFF;)
# Then rebuild and rerun:

ASAN_OPTIONS=detect_leaks=1 ./asan_demo 2>&1
```

Now LSan reports at process exit:

```text
=================================================================
==XXXXX==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 20 bytes in 1 object(s) allocated from:
    #0 0x... in malloc ...
    #1 0x... in init_config asan_demo.cpp:19
    #2 0x... in main asan_demo.cpp:35
```

LSan walks the heap at exit, finds all allocations, and marks any that are not reachable from a root pointer (stack, global data segment, or thread-local storage) as leaked. The 20-byte allocation is `sizeof(Config)` = 16 (name) + 4 (int) + 0 (no padding needed here) = 20 bytes. Fix the leak by adding `free(g_leaked_config)` before `return 0` and rerun to confirm silence.

### Part D: Valgrind Memcheck as a Complementary Tool

While ASan instruments at compile time and runs at near-native speed, Valgrind Memcheck instruments at runtime by executing your program inside a JIT-compiled synthetic CPU. It runs roughly 10–50x slower but requires no recompilation, making it valuable for diagnosing production binaries or third-party shared libraries you do not control:

```bash
# Compile without sanitizers, with debug symbols
clang++ -std=c++17 -O1 -g \
    -o asan_demo_plain race_lab/asan_demo.cpp

# Run under Valgrind Memcheck with full leak checking
valgrind --tool=memcheck \
    --leak-check=full \
    --show-leak-kinds=all \
    --track-origins=yes \
    --verbose \
    ./asan_demo_plain 2>&1 | grep -A 30 "HEAP SUMMARY\|Invalid write\|definitely lost"
```

The `--track-origins=yes` flag tells Memcheck to track where each uninitialized value was first created, which helps when diagnosing `Conditional jump or move depends on uninitialised value(s)` errors that are otherwise extremely difficult to attribute to a source line. This is slower than the default mode — Valgrind must maintain an additional shadow word per memory byte to store the origin — but it is indispensable for complex initialization-order bugs.

For Rust programs under Valgrind, build in debug mode without the standard library's allocator guard pages interfering, and use the system allocator to get Valgrind-compatible malloc/free semantics:

```rust
// Add to src/main.rs when running under Valgrind
use std::alloc::System;
#[global_allocator]
static A: System = System;
```

```bash
cargo build  # debug build
valgrind --tool=memcheck \
    --leak-check=full \
    ./target/debug/cache_bench 2>&1 | tail -20
```

---

## Developer Cheat Sheet & Toolchain Checklist

The table below provides the canonical command for each diagnostic task. These are the commands you run before merging a pull request that touches memory management, concurrency, or performance-critical paths.

| Task | Command |
|---|---|
| Emit Clang AST | `clang -Xclang -ast-dump -fsyntax-only file.cpp` |
| Emit unoptimized LLVM IR | `clang -O0 -S -emit-llvm -o out.ll file.cpp` |
| Emit optimized LLVM IR | `clang -O3 -march=native -S -emit-llvm -o out.ll file.cpp` |
| Apply individual LLVM passes | `opt -passes="<pass1>,<pass2>" -S in.bc -o out.ll` |
| Rust IR emission | `RUSTFLAGS="--emit=llvm-ir" cargo build --release` |
| Rust assembly for a function | `cargo asm --release crate::module::function` |
| Hardware perf counters | `perf stat -e cache-misses,LLC-load-misses,cycles,instructions ./bin` |
| CPU flamegraph | `cargo flamegraph --bin name` |
| Perf call-graph record | `perf record --call-graph fp -F 999 ./bin` |
| Perf annotated report | `perf report --stdio --no-children -g fractal,0.5,caller` |
| Criterion benchmark | `RUSTFLAGS="-C target-cpu=native" cargo bench --bench name` |
| TSan (C++) | `clang++ -fsanitize=thread -g -fno-omit-frame-pointer` |
| TSan (Rust nightly) | `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| ASan + LSan (C++) | `clang++ -fsanitize=address -g && ASAN_OPTIONS=detect_leaks=1 ./bin` |
| Valgrind Memcheck | `valgrind --leak-check=full --track-origins=yes ./bin` |
| Check all Rust warnings | `cargo check && cargo clippy -- -D warnings` |
| Run tests with output | `cargo test -- --nocapture` |

**Pre-merge verification checklist.** Before merging code that touches shared state, memory allocation, or hot paths, run through this sequence:

Run `cargo check` first to confirm the codebase compiles without warnings. Run `cargo clippy -- -D warnings` to surface idiomatic issues that the compiler permits but that signal architectural problems. Run `cargo test -- --nocapture` with `RUSTFLAGS="-Z sanitizer=thread"` on nightly to exercise all concurrent paths under TSan. For C++ code, build with `-fsanitize=address,undefined -g` and run the test suite; both ASan and UBSan fire at first contact with their respective error classes, so a full passing test suite under these flags provides strong safety guarantees. Run `perf stat` with LLC miss counters on any benchmark that accesses more than a few hundred kilobytes of memory to verify that your data layout is not introducing unexpected DRAM pressure. Finally, run `cargo bench` or the equivalent Criterion suite and compare against the baseline recorded in your CI artifact store to confirm that the change does not regress throughput by more than the noise floor, which Criterion quantifies automatically as a percentage change with confidence bounds.

The discipline of running this sequence before every merge transforms architecture review from a discussion about design patterns into an empirical comparison of measured behavior. The compiler, sanitizers, and profiler replace opinion with evidence.
