# Operational Verification Labs: DLSS

## Objective & Toolchain Setup

Deep Learning Super Sampling (DLSS) represents NVIDIA's temporal upscaling technology that reconstructs high-resolution frames from lower-resolution input through convolutional neural networks executed on Tensor Cores. While production DLSS integration requires NVIDIA's proprietary SDK and NGX runtime, the operational verification principles—tensor pipeline profiling, memory layout optimization, frame coherence validation, and temporal accumulation buffer management—apply universally to any GPU-accelerated upscaling system. This laboratory guide provides hands-on exercises for engineers implementing custom upscaling algorithms, integrating vendor SDKs, or debugging performance anomalies in AI-assisted rendering pipelines.

The verification workflow centers on three operational concerns. First, we analyze the compiler's intermediate representation and assembly output to ensure vectorized SIMD paths are utilized for tensor operations and that memory access patterns exhibit spatial locality. Second, we profile cache behavior and memory bandwidth utilization under synthetic and real-world frame submission patterns to identify bottlenecks in the upload-compute-download pipeline. Third, we employ dynamic analysis sanitizers to detect data races in multi-threaded frame queues, validate reference counting semantics in GPU resource handles, and confirm that temporal history buffers are released correctly across resolution changes.

The laboratory environment requires a Linux host with NVIDIA or AMD GPU drivers, Rust toolchain via rustup, LLVM-based profiling tools, and Valgrind for heap analysis. Begin by installing the Rust toolchain, which provides Cargo for dependency management and rustc with LLVM backend for optimization inspection. Install system diagnostic tools including GDB for breakpoint debugging, LLDB for DWARF symbol inspection, Valgrind for heap leak detection, and the Linux `perf` subsystem for hardware performance counter access. For GPU-specific profiling, install NVIDIA Nsight Systems or AMD Radeon GPU Profiler depending on your hardware vendor. The verification exercises assume familiarity with graphics pipeline stages—vertex processing, rasterization, fragment shading, and post-processing—but do not require prior DLSS integration experience.

Install the core toolchain with the following sequence. First, acquire rustup from the official Rust installation endpoint and configure the stable channel as default. Execute `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` and follow the interactive prompts to install Cargo, rustc, and associated utilities. Verify installation by running `rustc --version` and `cargo --version` to confirm version 1.70 or later. Next, install LLVM development tools and Clang compiler infrastructure through your distribution's package manager. On Debian-based systems, execute `sudo apt-get install llvm clang lldb valgrind linux-tools-common linux-tools-generic` to acquire the complete analysis suite. For Rust-specific profiling, install cargo extensions by running `cargo install cargo-asm cargo-flamegraph cargo-expand`. The cargo-asm extension allows inspection of generated assembly for specific functions, cargo-flamegraph produces flame graph visualizations from perf data, and cargo-expand reveals macro expansions before compilation.

Configure your development environment to enable debug symbols and optimization simultaneously, a requirement for meaningful profiling under production-like conditions. Create a Cargo profile named `profiling` in your `Cargo.toml` workspace configuration that inherits from the release profile but enables debug info. Insert the following stanza into the root `Cargo.toml` manifest to define the custom profile:

```toml
[profile.profiling]
inherits = "release"
debug = true
strip = false
```

This configuration ensures that the compiler applies aggressive optimizations including loop unrolling, vectorization, and inline expansion while preserving DWARF debug information necessary for stack trace resolution during profiling. The `strip = false` directive prevents removal of symbol tables, allowing tools like `perf` and Valgrind to attribute samples and allocations to specific source lines.

For exercises involving GPU acceleration, install vendor-specific profiling tools. NVIDIA Nsight Systems provides timeline visualization of GPU command submission, kernel execution, and memory transfers. Download the Nsight Systems package from NVIDIA's developer portal and install according to the provided instructions, then verify access by executing `nsys --version`. AMD users should acquire Radeon GPU Profiler (RGP) from AMD's developer site, which offers similar frame capture and wavefront occupancy analysis. Both tools operate by injecting profiling hooks into Vulkan or Direct3D driver stacks, capturing detailed execution traces that reveal pipeline stalls, memory bandwidth saturation, and asynchronous compute inefficiencies.

Prepare a minimal Rust project structure to serve as the foundation for all laboratory exercises. Initialize a new Cargo workspace by executing `cargo new --lib dlss_labs` to create a library crate. Navigate into the project directory and establish a multi-module layout by creating subdirectories `src/upscale`, `src/temporal`, and `src/tensor`. Each module will house implementations for distinct DLSS pipeline stages: spatial upscaling via bilinear or Lanczos filtering, temporal accumulation with motion vector reprojection, and tensor operations for convolutional inference. Populate `Cargo.toml` with dependencies for linear algebra, image processing, and GPU compute:

```toml
[package]
name = "dlss_labs"
version = "0.1.0"
edition = "2021"

[dependencies]
ndarray = "0.15"
image = "0.24"
rayon = "1.8"
wgpu = "0.18"
bytemuck = { version = "1.14", features = ["derive"] }
pollster = "0.3"

[dev-dependencies]
criterion = "0.5"
```

The ndarray crate provides N-dimensional array abstractions for tensor computations, image handles loading and format conversion, rayon enables data-parallel iteration over pixel arrays, and wgpu offers portable GPU compute via the WebGPU standard. The bytemuck crate facilitates zero-copy casting between Rust structs and GPU buffer contents, critical for minimizing upload overhead. Criterion will drive our microbenchmark harness in Exercise 2.

## Exercise 1: AST, IR & Disassembly Analysis

The first operational verification exercise focuses on compiler-level inspection to confirm that our upscaling kernels generate efficient machine code. Modern upscaling algorithms rely on vector operations—parallel multiply-accumulate across four-wide RGBA pixel channels, bilinear interpolation with SIMD horizontal additions, and motion vector application via gather loads. The Rust compiler, through its LLVM backend, can automatically vectorize these patterns when memory layouts are conducive and loop bounds are known at compile time. However, suboptimal struct packing, iterator chains with opaque closures, or hidden bounds checks can inhibit vectorization, resulting in scalar instruction sequences that leave GPU or CPU vector units idle.

We begin by implementing a spatial upscaling kernel that performs bilinear interpolation over a two-dimensional pixel grid. The algorithm reads four neighboring texels from the low-resolution input, computes fractional offsets, and produces a weighted blend for each high-resolution output pixel. This pattern is emblematic of DLSS's initial spatial upsampling stage before temporal refinement. Create a new file `src/upscale/bilinear.rs` and define the core interpolation function:

```rust
use ndarray::{Array2, Array3, s};

/// Performs bilinear upscaling from src (H, W, 4) to dst (H*scale, W*scale, 4).
/// Each output pixel is a weighted blend of the four nearest input texels.
pub fn bilinear_upscale(src: &Array3<f32>, scale: usize) -> Array3<f32> {
    let (src_h, src_w, channels) = src.dim();
    assert_eq!(channels, 4, "Expected RGBA input");
    
    let dst_h = src_h * scale;
    let dst_w = src_w * scale;
    let mut dst = Array3::<f32>::zeros((dst_h, dst_w, 4));
    
    let inv_scale = 1.0 / scale as f32;
    
    for dst_y in 0..dst_h {
        for dst_x in 0..dst_w {
            // Map destination pixel to source coordinate space
            let src_y_f = (dst_y as f32 + 0.5) * inv_scale - 0.5;
            let src_x_f = (dst_x as f32 + 0.5) * inv_scale - 0.5;
            
            let src_y0 = src_y_f.floor().max(0.0) as usize;
            let src_x0 = src_x_f.floor().max(0.0) as usize;
            let src_y1 = (src_y0 + 1).min(src_h - 1);
            let src_x1 = (src_x0 + 1).min(src_w - 1);
            
            let fy = src_y_f - src_y0 as f32;
            let fx = src_x_f - src_x0 as f32;
            
            // Fetch four texels
            let t00 = src.slice(s![src_y0, src_x0, ..]);
            let t10 = src.slice(s![src_y1, src_x0, ..]);
            let t01 = src.slice(s![src_y0, src_x1, ..]);
            let t11 = src.slice(s![src_y1, src_x1, ..]);
            
            // Bilinear weights
            let w00 = (1.0 - fx) * (1.0 - fy);
            let w10 = (1.0 - fx) * fy;
            let w01 = fx * (1.0 - fy);
            let w11 = fx * fy;
            
            // Blend across four channels
            for c in 0..4 {
                dst[[dst_y, dst_x, c]] = 
                    t00[c] * w00 + t10[c] * w10 + t01[c] * w01 + t11[c] * w11;
            }
        }
    }
    
    dst
}
```

This implementation follows the standard bilinear interpolation algorithm: for each output pixel, compute its fractional position in source space, identify the four surrounding texels, and blend them using horizontal and vertical lerp weights. The inner loop over channels performs four scalar multiplications and additions per output pixel. Our first verification task is to inspect the generated assembly to determine whether the compiler has vectorized this channel loop using SIMD instructions.

Compile the function with optimization and inspect the assembly output using cargo-asm. First, add a public re-export in `src/lib.rs` to ensure the symbol is not eliminated by dead code analysis:

```rust
pub mod upscale {
    pub mod bilinear;
}
```

Then execute `cargo asm --release dlss_labs::upscale::bilinear::bilinear_upscale` to dump the assembly for the target function. The output will display x86-64 assembly annotated with source line correspondence. Search for SIMD instruction mnemonics: `vmulps`, `vaddps`, `vmovups`, or AVX-512 variants like `vmulps ymm` or `zmm`. If the compiler has successfully vectorized the channel loop, you will observe packed floating-point multiply and add instructions operating on 128-bit or 256-bit registers, indicating that four RGBA channels are processed in parallel.

If the assembly contains only scalar `mulss` and `addss` instructions, the compiler failed to vectorize due to aliasing concerns or opaque array bounds. The ndarray slice operation returns a dynamically-typed view, preventing the compiler from proving that loop iterations are independent. To enable vectorization, we must refactor the inner loop to operate on fixed-size arrays rather than dynamic slices. Replace the channel loop with explicit array indexing:

```rust
// Replace the dynamic slice-based loop with fixed indexing
let t00_r = src[[src_y0, src_x0, 0]];
let t00_g = src[[src_y0, src_x0, 1]];
let t00_b = src[[src_y0, src_x0, 2]];
let t00_a = src[[src_y0, src_x0, 3]];

let t10_r = src[[src_y1, src_x0, 0]];
let t10_g = src[[src_y1, src_x0, 1]];
let t10_b = src[[src_y1, src_x0, 2]];
let t10_a = src[[src_y1, src_x0, 3]];

let t01_r = src[[src_y0, src_x1, 0]];
let t01_g = src[[src_y0, src_x1, 1]];
let t01_b = src[[src_y0, src_x1, 2]];
let t01_a = src[[src_y0, src_x1, 3]];

let t11_r = src[[src_y1, src_x1, 0]];
let t11_g = src[[src_y1, src_x1, 1]];
let t11_b = src[[src_y1, src_x1, 2]];
let t11_a = src[[src_y1, src_x1, 3]];

dst[[dst_y, dst_x, 0]] = t00_r * w00 + t10_r * w10 + t01_r * w01 + t11_r * w11;
dst[[dst_y, dst_x, 1]] = t00_g * w00 + t10_g * w10 + t01_g * w01 + t11_g * w11;
dst[[dst_y, dst_x, 2]] = t00_b * w00 + t10_b * w10 + t01_b * w01 + t11_b * w11;
dst[[dst_y, dst_x, 3]] = t00_a * w00 + t10_a * w10 + t01_a * w01 + t11_a * w11;
```

Recompile and inspect the assembly output again. With explicit per-channel computation, the compiler can recognize the parallel structure and emit SIMD instructions. Verify that the generated code uses vector registers and that the critical inner loop has been reduced to fewer than twenty instructions, indicating successful vectorization.

Next, examine the LLVM intermediate representation to understand how optimization passes transform the source code. The IR operates at a higher abstraction level than assembly, representing control flow as basic blocks connected by conditional and unconditional branches. Cargo does not provide direct IR dumping, but we can invoke rustc manually with IR emission flags. Execute the following command from your project root:

```bash
rustc --emit=llvm-ir --crate-type=lib -C opt-level=3 src/lib.rs -o target/dlss_labs.ll
```

Open `target/dlss_labs.ll` in a text editor and locate the LLVM function corresponding to `bilinear_upscale`. The IR will display type annotations, memory operations, and intrinsic function calls. Look for `llvm.fmuladd` intrinsics, which represent fused multiply-add operations that execute in a single CPU cycle on modern processors. The presence of vector types like `<4 x float>` confirms that the optimizer has promoted scalar operations to SIMD. Additionally, inspect loop structures for `llvm.loop` metadata annotations that indicate unrolling factor and vectorization width.

The IR inspection reveals how high-level array indexing translates to pointer arithmetic and bounds checks. LLVM's `gep` (GetElementPtr) instruction computes memory addresses from base pointers and multi-dimensional indices. Each array access incurs a bounds check unless the optimizer can prove indices are in range. To eliminate these checks, consider using unchecked indexing via unsafe code when you have established invariants through domain-specific validation. However, retain safe indexing during initial development to catch logic errors early.

Extend the verification by introducing a deliberate performance regression and observing its impact on generated code. Modify the interpolation weights to depend on a runtime parameter rather than compile-time constants. Replace the weight computation with a function call:

```rust
fn compute_weight(frac: f32, idx: usize) -> f32 {
    match idx {
        0 => (1.0 - frac) * (1.0 - frac),
        1 => (1.0 - frac) * frac,
        2 => frac * (1.0 - frac),
        3 => frac * frac,
        _ => unreachable!(),
    }
}
```

Use this function to compute weights dynamically and recompile. Inspect the assembly and observe that the compiler can no longer inline the weight computation if the function is defined in a separate module or if link-time optimization is disabled. The generated code will include call instructions, increasing instruction count and introducing branch misprediction penalties. This exercise demonstrates the importance of inlining hot-path computations and the fragility of optimization heuristics.

Finally, use GDB to single-step through the compiled function and inspect register allocations. Compile the library with debug symbols using the profiling profile defined earlier: `cargo build --profile=profiling`. Launch GDB and load the resulting shared library: `gdb target/profiling/libdlss_labs.so`. Set a breakpoint at the function entry: `break dlss_labs::upscale::bilinear::bilinear_upscale`. Since the library has no main entry point, you must link it into a test harness or use a scripting interface to invoke the function. Alternatively, write a minimal integration test in `tests/bilinear_test.rs`:

```rust
use dlss_labs::upscale::bilinear::bilinear_upscale;
use ndarray::Array3;

#[test]
fn test_bilinear_2x_upscale() {
    let src = Array3::<f32>::zeros((16, 16, 4));
    let dst = bilinear_upscale(&src, 2);
    assert_eq!(dst.dim(), (32, 32, 4));
}
```

Run the test under GDB by executing `cargo test --profile=profiling` and attaching GDB to the test process. Use `layout asm` to display the disassembly window and `stepi` to execute one instruction at a time. Observe the CPU register file as the function executes, noting how SIMD registers (`xmm0`, `ymm0`, or `zmm0` depending on target features) accumulate intermediate results. This low-level inspection confirms that your code compiles to efficient vector operations and that register pressure does not cause spills to memory.

## Exercise 2: Cache Miss & Throughput Profiling

Spatial upscaling is memory-bound: each output pixel requires reads from four input texels, and non-unit-stride access patterns can cause cache misses if data layout does not match traversal order. DLSS operates on large frame buffers—1920×1080 input upscaled to 3840×2160 output requires processing over eight million pixels per frame. At 60 frames per second, the upscaler must sustain approximately 500 megapixels per second of throughput. This exercise establishes a microbenchmark harness using Criterion, profiles cache behavior with `perf`, and optimizes memory layout to maximize bandwidth utilization.

Begin by creating a benchmark suite in `benches/upscale_bench.rs`. Criterion integrates with Cargo's benchmark infrastructure and provides statistical analysis of timing distributions across multiple iterations. The benchmark will measure throughput in megapixels per second for various input resolutions and scaling factors:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};
use dlss_labs::upscale::bilinear::bilinear_upscale;
use ndarray::Array3;

fn bench_bilinear_upscale(c: &mut Criterion) {
    let sizes = vec![
        (480, 270, 2),   // 480p -> 960p
        (960, 540, 2),   // 540p -> 1080p
        (1920, 1080, 2), // 1080p -> 4K
    ];
    
    for (width, height, scale) in sizes {
        let src = Array3::<f32>::from_elem((height, width, 4), 0.5);
        let output_pixels = (height * scale) * (width * scale);
        
        let mut group = c.benchmark_group(format!("bilinear_{}x{}_{}x", width, height, scale));
        group.throughput(Throughput::Elements(output_pixels as u64));
        
        group.bench_function("bilinear_upscale", |b| {
            b.iter(|| {
                let _dst = bilinear_upscale(black_box(&src), black_box(scale));
            });
        });
        
        group.finish();
    }
}

criterion_group!(benches, bench_bilinear_upscale);
criterion_main!(benches);
```

This benchmark suite measures execution time for three representative resolutions, reporting throughput in output pixels per second. The `black_box` function prevents the optimizer from eliminating the computation by treating inputs and outputs as opaque. The `Throughput` annotation allows Criterion to report performance in domain-specific units rather than raw nanoseconds.

Execute the benchmark suite by running `cargo bench`. Criterion will perform warm-up iterations, collect timing samples, detect outliers, and compute statistical summaries. The output displays median execution time, standard deviation, and throughput in elements per second. On a modern CPU with 32 KB L1 data cache and 256 KB L2 cache, the 1080p upscale should achieve approximately 100 megapixels per second using scalar code, increasing to 300-400 megapixels per second with SIMD vectorization.

Next, profile cache behavior using Linux perf to identify memory bottlenecks. The `perf stat` command reports hardware performance counters including cache references, cache misses, and instructions retired. Run the benchmark under perf with cache event monitoring:

```bash
perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses \
    cargo bench --bench upscale_bench -- bilinear_1920x1080_2x --profile-time=10
```

The output displays absolute counts and miss rates for each cache level. A well-optimized upscaler should exhibit L1 data cache miss rates below five percent, indicating that most texel accesses hit in the 32 KB first-level cache. High L1 miss rates suggest poor spatial locality: the traversal order does not match the row-major memory layout, causing cache lines to be evicted before reuse. Last-level cache (LLC) misses indicate that the working set exceeds the aggregate cache hierarchy, forcing memory subsystem round-trips.

Examine the memory access pattern in the bilinear kernel. For each output pixel at coordinates `(dst_y, dst_x)`, we fetch four texels from positions `(src_y0, src_x0)`, `(src_y0, src_x1)`, `(src_y1, src_x0)`, and `(src_y1, src_x1)`. If the source array is stored in row-major order, accessing horizontally adjacent texels exhibits good spatial locality—they reside in the same cache line. However, accessing vertically adjacent texels requires stepping by the row stride (width × channels), potentially spanning multiple cache lines. For a 1920-pixel-wide RGBA image, each row occupies 30,720 bytes, far exceeding the 64-byte cache line size. Accessing `(src_y1, src_x0)` after `(src_y0, src_x0)` incurs a cache miss if the two rows are not co-resident.

Optimize cache utilization by blocking the traversal loop to process small tiles that fit in L1 cache. Divide the output image into 32×32 tiles and process each tile completely before moving to the next. This ensures that source data remains cache-hot during tile processing:

```rust
pub fn bilinear_upscale_blocked(src: &Array3<f32>, scale: usize) -> Array3<f32> {
    let (src_h, src_w, channels) = src.dim();
    assert_eq!(channels, 4, "Expected RGBA input");
    
    let dst_h = src_h * scale;
    let dst_w = src_w * scale;
    let mut dst = Array3::<f32>::zeros((dst_h, dst_w, 4));
    
    let inv_scale = 1.0 / scale as f32;
    let tile_size = 32;
    
    for tile_y_start in (0..dst_h).step_by(tile_size) {
        for tile_x_start in (0..dst_w).step_by(tile_size) {
            let tile_y_end = (tile_y_start + tile_size).min(dst_h);
            let tile_x_end = (tile_x_start + tile_size).min(dst_w);
            
            for dst_y in tile_y_start..tile_y_end {
                for dst_x in tile_x_start..tile_x_end {
                    let src_y_f = (dst_y as f32 + 0.5) * inv_scale - 0.5;
                    let src_x_f = (dst_x as f32 + 0.5) * inv_scale - 0.5;
                    
                    let src_y0 = src_y_f.floor().max(0.0) as usize;
                    let src_x0 = src_x_f.floor().max(0.0) as usize;
                    let src_y1 = (src_y0 + 1).min(src_h - 1);
                    let src_x1 = (src_x0 + 1).min(src_w - 1);
                    
                    let fy = src_y_f - src_y0 as f32;
                    let fx = src_x_f - src_x0 as f32;
                    
                    let w00 = (1.0 - fx) * (1.0 - fy);
                    let w10 = (1.0 - fx) * fy;
                    let w01 = fx * (1.0 - fy);
                    let w11 = fx * fy;
                    
                    for c in 0..4 {
                        dst[[dst_y, dst_x, c]] = 
                            src[[src_y0, src_x0, c]] * w00 +
                            src[[src_y1, src_x0, c]] * w10 +
                            src[[src_y0, src_x1, c]] * w01 +
                            src[[src_y1, src_x1, c]] * w11;
                    }
                }
            }
        }
    }
    
    dst
}
```

Add a benchmark for the blocked variant and compare cache miss rates. Re-run perf stat and observe that L1 miss rates decrease by 20-30 percent due to improved temporal locality within tiles. The blocked implementation trades off some instruction-level parallelism for better cache reuse, a favorable tradeoff when memory bandwidth is the bottleneck.

Further optimize memory layout by transposing the source array from height-width-channel (HWC) to channel-height-width (CHW) order. In CHW layout, all red channel values are contiguous in memory, followed by all green values, then blue, then alpha. This layout is advantageous for channel-parallel SIMD operations but detrimental for spatial interpolation that accesses all four channels of a single texel. Implement both layouts and profile their performance under different access patterns to understand the layout-algorithm interaction.

Introduce a synthetic memory pressure scenario by allocating a large dummy buffer before running the upscaler. This forces the operating system to evict cache lines and simulates contention with other rendering pipeline stages:

```rust
fn bench_with_memory_pressure(c: &mut Criterion) {
    let src = Array3::<f32>::from_elem((1080, 1920, 4), 0.5);
    
    // Allocate 512 MB of dummy data to pollute cache
    let _pressure = vec![0u8; 512 * 1024 * 1024];
    
    c.bench_function("bilinear_upscale_under_pressure", |b| {
        b.iter(|| {
            let _dst = bilinear_upscale(black_box(&src), black_box(2));
        });
    });
}
```

Benchmark this scenario and observe throughput degradation. High LLC miss rates under memory pressure indicate that the upscaler's working set exceeds available cache capacity, a condition that will occur in production when multiple pipeline stages execute concurrently.

Finally, use `perf record` to capture a detailed profile with call stack information. Execute the benchmark under perf record with frequency sampling:

```bash
perf record -F 997 -g --call-graph=dwarf cargo bench --bench upscale_bench -- bilinear_1920x1080_2x
```

The `-F 997` flag samples the instruction pointer at 997 Hz, a prime number chosen to avoid phase-locking with periodic application behavior. The `-g --call-graph=dwarf` options enable stack unwinding using DWARF debug info, allowing attribution of samples to source lines. After the benchmark completes, generate a flame graph visualization:

```bash
perf script | stackcollapse-perf.pl | flamegraph.pl > upscale_flame.svg
```

Open the SVG in a web browser and identify hot functions. The flame graph displays the call stack as a hierarchy of colored bars, with width proportional to time spent in each function. The bilinear interpolation loop should dominate the profile, occupying 80-90 percent of the flame graph width. If significant time is spent in allocator functions (`malloc`, `free`) or array bounds checking, investigate opportunities to pre-allocate buffers and eliminate redundant checks.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Production DLSS integration operates in a multi-threaded environment where rendering threads submit frames asynchronously while the upscaler processes prior frames in background threads. Temporal accumulation requires maintaining history buffers across multiple frames, introducing potential for data races if synchronization primitives are misapplied. This exercise instruments the codebase with ThreadSanitizer to detect concurrency bugs, employs AddressSanitizer to catch heap corruption, and uses Valgrind's Massif tool to profile memory allocation patterns and identify leaks in resource management.

Begin by implementing a temporal accumulation buffer that averages the current frame with historical frames using exponential decay. Temporal accumulation reduces noise and stabilizes detail in upscaled output by blending multiple frames weighted by motion vectors. Create a new module `src/temporal/accumulator.rs`:

```rust
use ndarray::Array3;
use std::sync::{Arc, RwLock};

pub struct TemporalAccumulator {
    history: Arc<RwLock<Option<Array3<f32>>>>,
    alpha: f32,
}

impl TemporalAccumulator {
    pub fn new(alpha: f32) -> Self {
        assert!(alpha > 0.0 && alpha <= 1.0, "Alpha must be in (0, 1]");
        Self {
            history: Arc::new(RwLock::new(None)),
            alpha,
        }
    }
    
    pub fn accumulate(&self, current: Array3<f32>) -> Array3<f32> {
        let mut history_guard = self.history.write().unwrap();
        
        match history_guard.as_ref() {
            None => {
                // First frame: no history available
                *history_guard = Some(current.clone());
                current
            }
            Some(prev) => {
                // Exponential moving average: out = alpha * current + (1 - alpha) * prev
                assert_eq!(prev.dim(), current.dim(), "Frame dimensions changed");
                
                let blended = &current * self.alpha + prev * (1.0 - self.alpha);
                *history_guard = Some(blended.clone());
                blended
            }
        }
    }
    
    pub fn reset(&self) {
        let mut history_guard = self.history.write().unwrap();
        *history_guard = None;
    }
}
```

This accumulator maintains a single history frame protected by a read-write lock. The `accumulate` method blends the current frame with stored history using an exponential moving average, a simple form of temporal filtering. The alpha parameter controls the blend ratio: values near 1.0 emphasize the current frame (reducing temporal stability), while values near 0.0 emphasize history (increasing blur).

Write a multi-threaded stress test that simulates concurrent frame submission from multiple producer threads. Create a test in `tests/temporal_stress.rs`:

```rust
use dlss_labs::temporal::accumulator::TemporalAccumulator;
use ndarray::Array3;
use std::sync::Arc;
use std::thread;

#[test]
fn test_concurrent_accumulation() {
    let accumulator = Arc::new(TemporalAccumulator::new(0.3));
    let num_threads = 8;
    let frames_per_thread = 100;
    
    let handles: Vec<_> = (0..num_threads)
        .map(|thread_id| {
            let acc = Arc::clone(&accumulator);
            thread::spawn(move || {
                for frame_idx in 0..frames_per_thread {
                    let frame_value = (thread_id as f32 + frame_idx as f32) / 1000.0;
                    let frame = Array3::<f32>::from_elem((540, 960, 4), frame_value);
                    let _result = acc.accumulate(frame);
                }
            })
        })
        .collect();
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    // Final verification: history should contain blended result
    let final_frame = Array3::<f32>::zeros((540, 960, 4));
    let _final_result = accumulator.accumulate(final_frame);
}
```

This test spawns eight threads that each submit 100 frames to the accumulator concurrently. The test does not verify output correctness—its purpose is to exercise the synchronization logic under contention and expose data races. Run the test under ThreadSanitizer by setting the appropriate rustflags and rebuilding:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu -Z build-std --tests
```

ThreadSanitizer requires nightly Rust and a custom target specification to instrument the standard library. If a data race exists, ThreadSanitizer will report conflicting accesses with stack traces showing the racing instructions. The current implementation uses RwLock correctly, so no races should be detected. Introduce a deliberate race by removing the lock and observe the sanitizer output:

```rust
// DELIBERATELY BROKEN: remove RwLock to induce race
pub struct TemporalAccumulatorRacy {
    history: Option<Array3<f32>>,
    alpha: f32,
}
```

Rerun the test with the racy implementation. ThreadSanitizer will report a data race on the `history` field, identifying the exact source lines where conflicting reads and writes occurred. The report includes thread IDs, call stacks, and the nature of the conflict (read-write or write-write). This demonstrates the sanitizer's ability to detect subtle concurrency bugs that might not manifest as crashes but produce incorrect results.

Next, employ AddressSanitizer to detect heap corruption and use-after-free errors. AddressSanitizer instruments memory allocations with guard zones and maintains shadow memory to track allocation status. Create a test that deliberately leaks memory and accesses freed allocations:

```rust
#[test]
fn test_accumulator_lifecycle() {
    let accumulator = TemporalAccumulator::new(0.5);
    
    // Submit frames
    for _ in 0..10 {
        let frame = Array3::<f32>::zeros((1080, 1920, 4));
        let _result = accumulator.accumulate(frame);
    }
    
    // Reset should clear history
    accumulator.reset();
    
    // Verify history is empty by submitting a new frame
    let new_frame = Array3::<f32>::ones((1080, 1920, 4));
    let result = accumulator.accumulate(new_frame);
    
    // Result should equal input since history was cleared
    assert!(result.iter().all(|&x| x == 1.0));
}
```

Run this test under AddressSanitizer:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu -Z build-std --tests
```

AddressSanitizer will not report errors in the correct implementation, but if we introduce a use-after-free by unsafely dereferencing a raw pointer to freed memory, the sanitizer will detect it immediately. Modify the accumulator to store a raw pointer instead of an owned Array3 and access it after deallocation:

```rust
// DELIBERATELY BROKEN: use-after-free via raw pointer
pub struct TemporalAccumulatorUnsafe {
    history_ptr: *mut Array3<f32>,
    alpha: f32,
}

impl Drop for TemporalAccumulatorUnsafe {
    fn drop(&mut self) {
        unsafe {
            if !self.history_ptr.is_null() {
                let _ = Box::from_raw(self.history_ptr);
            }
        }
    }
}

impl TemporalAccumulatorUnsafe {
    pub fn accumulate_unsafe(&mut self, current: Array3<f32>) -> Array3<f32> {
        unsafe {
            if self.history_ptr.is_null() {
                self.history_ptr = Box::into_raw(Box::new(current.clone()));
                current
            } else {
                // Use-after-free: access pointer after Drop may have freed it
                let prev = &*self.history_ptr;
                let blended = &current * self.alpha + prev * (1.0 - self.alpha);
                *self.history_ptr = blended.clone();
                blended
            }
        }
    }
}
```

Run the test with this unsafe implementation under AddressSanitizer. The sanitizer will report a heap-use-after-free error with the exact instruction address and allocation/deallocation stack traces. This demonstrates the sanitizer's effectiveness at catching memory safety violations that would otherwise cause silent corruption or segmentation faults.

Profile heap allocation patterns using Valgrind's Massif tool to identify memory leaks and excessive allocation churn. Massif tracks the heap over time and generates a report showing peak memory usage and allocation sites. Run the stress test under Massif:

```bash
valgrind --tool=massif --massif-out-file=massif.out cargo test --release test_concurrent_accumulation
```

After the test completes, analyze the Massif output using `ms_print`:

```bash
ms_print massif.out
```

The report displays a timeline of heap usage, annotated with allocation sites. Look for monotonically increasing memory usage that indicates a leak: memory is allocated but never freed. The accumulator implementation should exhibit stable memory usage after the first frame allocation, with subsequent frames reusing the history buffer. If memory usage grows linearly with frame count, investigate whether Array3 clones are being unnecessarily retained.

Extend the stress test to simulate a long-running rendering loop that processes thousands of frames. Monitor memory usage over time using system tools like `top` or `/proc/self/status` to confirm that heap size stabilizes:

```rust
#[test]
fn test_long_running_accumulation() {
    use std::fs;
    
    let accumulator = TemporalAccumulator::new(0.3);
    
    for frame_idx in 0..10000 {
        let frame = Array3::<f32>::from_elem((1080, 1920, 4), frame_idx as f32 / 10000.0);
        let _result = accumulator.accumulate(frame);
        
        // Sample memory usage every 1000 frames
        if frame_idx % 1000 == 0 {
            let status = fs::read_to_string("/proc/self/status").unwrap();
            let vmrss_line = status.lines()
                .find(|line| line.starts_with("VmRSS:"))
                .unwrap();
            println!("Frame {}: {}", frame_idx, vmrss_line);
        }
    }
}
```

Run this test and verify that VmRSS (resident set size) stabilizes after the initial allocation. Any monotonic growth indicates a memory leak that must be addressed before production deployment.

Finally, use the LeakSanitizer to detect memory leaks automatically. LeakSanitizer is integrated with AddressSanitizer and runs at program exit to identify unreachable allocations. Run the lifecycle test under LeakSanitizer:

```bash
RUSTFLAGS="-Z sanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu -Z build-std --tests
```

LeakSanitizer will report any allocations that were not freed before program termination, along with the allocation stack traces. The correct implementation should produce no leaks. Introduce a deliberate leak by cloning the history buffer without dropping it:

```rust
pub fn leak_history(&self) -> Array3<f32> {
    let history_guard = self.history.read().unwrap();
    history_guard.as_ref().unwrap().clone()
    // Clone is returned but the history buffer is never updated or freed
}
```

Call this function in the test and observe that LeakSanitizer flags the leaked allocation at program exit. This confirms that the sanitizer can detect leaks even when references are stored in complex data structures protected by synchronization primitives.

## Developer Cheat Sheet & Toolchain Checklist

This section provides a concise reference for the operational verification workflow, listing essential commands, compiler flags, and diagnostic procedures for DLSS-related development.

**Assembly Inspection:**
Inspect generated assembly for a specific function to verify SIMD vectorization:
```bash
cargo asm --release dlss_labs::upscale::bilinear::bilinear_upscale
```
Look for SIMD instructions: `vmulps`, `vaddps`, `vmovups` (SSE/AVX) or `fmul`, `fadd` (scalar fallback).

**LLVM IR Emission:**
Generate LLVM intermediate representation to analyze optimization passes:
```bash
rustc --emit=llvm-ir --crate-type=lib -C opt-level=3 src/lib.rs -o target/dlss_labs.ll
```
Search the IR for `llvm.fmuladd` intrinsics and `<4 x float>` vector types.

**Benchmark Execution:**
Run performance benchmarks with Criterion and report throughput:
```bash
cargo bench --bench upscale_bench
```
Criterion outputs median time, standard deviation, and throughput in elements per second.

**Cache Profiling with perf stat:**
Measure cache miss rates during benchmark execution:
```bash
perf stat -e cache-references,cache-misses,L1-dcache-load-misses,LLC-load-misses \
    cargo bench --bench upscale_bench -- bilinear_1920x1080_2x
```
Target L1 miss rates below 5% and LLC miss rates below 1% for memory-bound kernels.

**Flame Graph Generation:**
Capture a detailed execution profile with call stack information:
```bash
perf record -F 997 -g --call-graph=dwarf cargo bench --bench upscale_bench
perf script | stackcollapse-perf.pl | flamegraph.pl > upscale_flame.svg
```
Open the SVG in a browser to identify hot functions and optimization opportunities.

**ThreadSanitizer:**
Detect data races in multi-threaded code:
```bash
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu -Z build-std
```
ThreadSanitizer reports conflicting accesses with thread IDs and stack traces.

**AddressSanitizer:**
Catch heap corruption, buffer overflows, and use-after-free errors:
```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu -Z build-std
```
AddressSanitizer reports errors immediately upon detection with allocation/deallocation stacks.

**LeakSanitizer:**
Identify memory leaks by detecting unreachable allocations at program exit:
```bash
RUSTFLAGS="-Z sanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu -Z build-std
```
LeakSanitizer produces a report listing leaked allocations and their allocation sites.

**Valgrind Massif:**
Profile heap allocation patterns over time to identify memory leaks and excessive churn:
```bash
valgrind --tool=massif --massif-out-file=massif.out cargo test --release
ms_print massif.out
```
Massif generates a timeline of heap usage annotated with allocation sites.

**GDB Single-Stepping:**
Debug compiled code with full symbol resolution and register inspection:
```bash
cargo build --profile=profiling
gdb target/profiling/libdlss_labs.so
(gdb) break dlss_labs::upscale::bilinear::bilinear_upscale
(gdb) run
(gdb) layout asm
(gdb) stepi
```
Use `info registers` to inspect CPU and SIMD register contents during execution.

**Cargo Profile Configuration:**
Define a custom profile in `Cargo.toml` that enables both optimization and debug symbols:
```toml
[profile.profiling]
inherits = "release"
debug = true
strip = false
```
Build with `cargo build --profile=profiling` to obtain optimized binaries with full debug info.

**Dependency Versions for Reproducibility:**
Pin exact versions of critical dependencies to ensure reproducible builds across environments:
```toml
ndarray = "=0.15.6"
image = "=0.24.7"
rayon = "=1.8.0"
wgpu = "=0.18.0"
```
Update versions deliberately and test for regressions after each upgrade.

**Sanitizer Compatibility:**
Sanitizers require nightly Rust and custom target builds. Install the nightly toolchain:
```bash
rustup install nightly
rustup component add rust-src --toolchain nightly
```
Use `cargo +nightly` to invoke nightly-specific features during sanitizer runs.

**GPU Profiling (NVIDIA):**
Capture a detailed GPU execution trace using Nsight Systems:
```bash
nsys profile --trace=cuda,nvtx --output=dlss_trace cargo run --release
nsys-ui dlss_trace.qdrep
```
Analyze kernel launch times, memory transfer durations, and compute/graphics queue contention.

**GPU Profiling (AMD):**
Capture a frame with Radeon GPU Profiler:
```bash
radeon-profile --capture cargo run --release
```
RGP provides wavefront occupancy, memory bandwidth saturation, and pipeline stall analysis.

**Continuous Integration Workflow:**
Integrate verification steps into CI pipelines to catch regressions automatically. Example GitHub Actions workflow:
```yaml
name: Verification
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test --all-features
      - run: cargo bench --no-run
  sanitize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: dtolnay/rust-toolchain@nightly
      - run: cargo +nightly test -Z build-std --target x86_64-unknown-linux-gnu
        env:
          RUSTFLAGS: "-Z sanitizer=address"
```

This checklist provides the operational foundation for systematic verification of DLSS-like upscaling implementations, ensuring correctness, performance, and memory safety through disciplined application of compiler analysis, profiling tools, and dynamic sanitizers.
