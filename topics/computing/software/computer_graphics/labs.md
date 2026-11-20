# Operational Verification Labs: Computer Graphics

## Objective & Toolchain Setup

This guide treats the graphics pipeline as a systems engineering problem. Every exercise targets a failure mode that appears in production renderers: uninitialized vertex memory caught by AddressSanitizer, a data race in a parallel tile renderer exposed by ThreadSanitizer, and a cache-thrashing scene traversal that flame graphs make immediately visible. The goal is to build diagnostic muscle memory so that when these failures appear in a real codebase — a game engine, a ray tracer, a GPU compute kernel host — you recognize the signal and act on it without hesitation.

The exercises are written in Rust and C++. Rust provides ownership-enforced memory safety with sanitizer escape hatches via `unsafe`; C++ provides the kind of raw pointer arithmetic that ships in most real-time graphics engines. Both are essential. Go appears in the tooling layer for benchmarking harnesses where its simplicity is an asset.

### Toolchain Installation

Install `rustup` first. It manages the Rust toolchain and gives you `cargo`, `rustc`, and `rustfmt` in one shot.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
rustup install nightly
rustup component add rust-src llvm-tools-preview
```

Install LLVM/Clang and the supporting native toolchain on Debian/Ubuntu:

```text
sudo apt-get update
sudo apt-get install -y clang llvm lld lldb valgrind \
    linux-perf libasan6 libtsan0 \
    cmake ninja-build pkg-config \
    libgl1-mesa-dev libglfw3-dev
```

Install `cargo-flamegraph` and `cargo-asm`:

```text
cargo install flamegraph
cargo install cargo-show-asm
```

Verify the full stack is wired together:

```text
rustc --version
clang --version
lldb --version
valgrind --version
cargo flamegraph --help
```

For the C++ exercises, establish a minimal `CMakeLists.txt` that compiles with Clang and links ASAN/TSAN via compiler flags. All exercises below that use C++ assume this build root.

---

## Exercise 1: AST, IR & Disassembly Analysis

### The Diagnostic Target

A vertex transformation pipeline is the first computational kernel every renderer executes. It takes an array of three-component position vectors, applies a 4×4 model-view-projection matrix, and writes homogeneous clip-space coordinates. This operation is trivially parallelizable and cache-friendly when laid out correctly — but its inner loop is also a canonical subject for LLVM autovectorization, and the gap between what you wrote and what the compiler actually emitted is worth reading in detail.

The objective of this exercise is threefold: inspect the Rust compiler's MIR (Mid-level Intermediate Representation) to understand ownership lowering, dump the LLVM IR to see how the matrix multiply is expressed before backend optimization, and finally read the native x86-64 disassembly to verify that SIMD instructions were emitted and the loop was vectorized.

### The Vertex Transform Kernel in Rust

Create a new Cargo project:

```text
cargo new --lib vtransform
cd vtransform
```

Replace `src/lib.rs` with the following complete implementation:

```rust
// src/lib.rs
//
// Vertex transformation kernel: applies a column-major 4x4 MVP matrix
// to a slice of Vec3 positions, producing Vec4 clip-space coordinates.
// All arithmetic is intentionally scalar to give the compiler maximum
// freedom to autovectorize and to give us something interesting to read
// in the IR.

#[derive(Clone, Copy, Debug, PartialEq)]
#[repr(C)]
pub struct Vec3 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

#[derive(Clone, Copy, Debug, PartialEq)]
#[repr(C)]
pub struct Vec4 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub w: f32,
}

/// Column-major 4x4 matrix stored as [col0, col1, col2, col3].
/// Each column is a Vec4.  This matches OpenGL / Metal / WebGPU convention.
#[derive(Clone, Copy, Debug)]
#[repr(C)]
pub struct Mat4 {
    pub cols: [Vec4; 4],
}

impl Mat4 {
    /// Construct an identity matrix.
    pub fn identity() -> Self {
        Mat4 {
            cols: [
                Vec4 { x: 1.0, y: 0.0, z: 0.0, w: 0.0 },
                Vec4 { x: 0.0, y: 1.0, z: 0.0, w: 0.0 },
                Vec4 { x: 0.0, y: 0.0, z: 1.0, w: 0.0 },
                Vec4 { x: 0.0, y: 0.0, z: 0.0, w: 1.0 },
            ],
        }
    }

    /// Construct a perspective projection matrix (right-handed, depth 0..1).
    /// fov_y_radians: vertical field of view in radians.
    /// aspect: width / height.
    /// near_z, far_z: clip plane distances (both positive).
    pub fn perspective(fov_y_radians: f32, aspect: f32, near_z: f32, far_z: f32) -> Self {
        let tan_half = (fov_y_radians * 0.5).tan();
        let sy = 1.0 / tan_half;
        let sx = sy / aspect;
        let nmf = near_z - far_z;
        Mat4 {
            cols: [
                Vec4 { x: sx,  y: 0.0, z: 0.0,                       w: 0.0 },
                Vec4 { x: 0.0, y: sy,  z: 0.0,                       w: 0.0 },
                Vec4 { x: 0.0, y: 0.0, z: (far_z + near_z) / nmf,   w: -1.0 },
                Vec4 { x: 0.0, y: 0.0, z: 2.0 * far_z * near_z / nmf, w: 0.0 },
            ],
        }
    }

    /// Multiply this matrix by a Vec4 column vector: result = M * v.
    #[inline(always)]
    pub fn mul_vec4(&self, v: Vec4) -> Vec4 {
        let c = &self.cols;
        Vec4 {
            x: c[0].x * v.x + c[1].x * v.y + c[2].x * v.z + c[3].x * v.w,
            y: c[0].y * v.x + c[1].y * v.y + c[2].y * v.z + c[3].y * v.w,
            z: c[0].z * v.x + c[1].z * v.y + c[2].z * v.z + c[3].z * v.w,
            w: c[0].w * v.x + c[1].w * v.y + c[2].w * v.z + c[3].w * v.w,
        }
    }
}

/// Transform a slice of Vec3 world-space positions into Vec4 clip-space
/// coordinates using the supplied MVP matrix.  Positions are promoted to
/// homogeneous form with w=1 before multiplication.
///
/// # Panics
/// Panics if `output.len() < input.len()`.
pub fn transform_vertices(mvp: &Mat4, input: &[Vec3], output: &mut [Vec4]) {
    assert!(
        output.len() >= input.len(),
        "output buffer too small: {} < {}",
        output.len(),
        input.len()
    );
    for (i, v) in input.iter().enumerate() {
        let h = Vec4 { x: v.x, y: v.y, z: v.z, w: 1.0 };
        output[i] = mvp.mul_vec4(h);
    }
}

/// Perspective-divide clip coordinates to normalized device coordinates.
/// Modifies the slice in place.  Vertices at w=0 are left unchanged to
/// avoid division by zero; callers should cull them before rasterization.
pub fn perspective_divide(coords: &mut [Vec4]) {
    for v in coords.iter_mut() {
        if v.w.abs() > f32::EPSILON {
            let inv_w = 1.0 / v.w;
            v.x *= inv_w;
            v.y *= inv_w;
            v.z *= inv_w;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx_eq(a: f32, b: f32, eps: f32) -> bool {
        (a - b).abs() < eps
    }

    #[test]
    fn identity_transform_is_passthrough() {
        let mvp = Mat4::identity();
        let input = vec![
            Vec3 { x: 1.0, y: 2.0, z: 3.0 },
            Vec3 { x: -1.0, y: 0.5, z: 10.0 },
        ];
        let mut output = vec![Vec4 { x: 0.0, y: 0.0, z: 0.0, w: 0.0 }; 2];
        transform_vertices(&mvp, &input, &mut output);
        assert!(approx_eq(output[0].x, 1.0, 1e-6));
        assert!(approx_eq(output[0].y, 2.0, 1e-6));
        assert!(approx_eq(output[0].z, 3.0, 1e-6));
        assert!(approx_eq(output[0].w, 1.0, 1e-6));
    }

    #[test]
    fn perspective_divide_normalizes_w() {
        let mut coords = vec![Vec4 { x: 2.0, y: 4.0, z: 6.0, w: 2.0 }];
        perspective_divide(&mut coords);
        assert!(approx_eq(coords[0].x, 1.0, 1e-6));
        assert!(approx_eq(coords[0].y, 2.0, 1e-6));
        assert!(approx_eq(coords[0].z, 3.0, 1e-6));
    }

    #[test]
    fn perspective_matrix_maps_near_to_zero() {
        let fov = std::f32::consts::FRAC_PI_2; // 90 degrees
        let near = 0.1_f32;
        let far = 100.0_f32;
        let proj = Mat4::perspective(fov, 1.0, near, far);
        // A point exactly at z = -near in view space (w=1 means eye-space z
        // must be fed as a Vec4 directly to the projection matrix).
        // For a point at (0,0,-near,1) the projected z after perspective
        // divide should be 0.0 for depth range [0,1].
        let v = Vec4 { x: 0.0, y: 0.0, z: -near, w: 1.0 };
        let clip = proj.mul_vec4(v);
        let ndc_z = clip.z / clip.w;
        assert!(approx_eq(ndc_z, 0.0, 1e-5), "ndc_z={}", ndc_z);
    }

    #[test]
    #[should_panic(expected = "output buffer too small")]
    fn transform_panics_on_short_output() {
        let mvp = Mat4::identity();
        let input = vec![Vec3 { x: 0.0, y: 0.0, z: 0.0 }; 4];
        let mut output = vec![Vec4 { x: 0.0, y: 0.0, z: 0.0, w: 0.0 }; 2];
        transform_vertices(&mvp, &input, &mut output);
    }
}
```

Run the tests first to confirm correctness:

```text
cargo test
```

All four tests must pass before you proceed to IR inspection. Never inspect the IR of broken code — you will not be able to distinguish compiler behavior from your own bugs.

### Inspecting the MIR

Rust's MIR is the control-flow graph the borrow checker operates on. It is desugared from the source but not yet lowered to LLVM IR. Reading it teaches you how the compiler models ownership, borrows, and panics before any optimization occurs.

```text
RUSTFLAGS="--emit=mir" cargo build --release 2>/dev/null
find target/ -name "*.mir" | head -5
```

Open the MIR file for `vtransform`. The `transform_vertices` function in MIR will show explicit `assert!` terminator nodes for the bounds check, `StorageLive`/`StorageDead` markers for every local variable, and borrow annotations on the input and output slices. Notice that the loop iterator desugars into a `loop` block with a `SwitchInt` terminator on the iterator's `next()` discriminant. This is the structure the borrow checker proved safe; the eventual LLVM IR is a mechanical lowering of exactly this graph.

### Dumping the LLVM IR

```text
RUSTFLAGS="--emit=llvm-ir -C opt-level=3 -C target-cpu=native" \
    cargo build --release 2>/dev/null
find target/ -name "*.ll" | xargs grep -l "transform_vertices"
```

Open the `.ll` file and search for `transform_vertices`. You will find the inner loop body expressed as a sequence of `fmul` and `fadd` instructions operating on `float` scalars. If LLVM's loop vectorizer ran (which it should at `-O3` with `target-cpu=native`), you will instead see `<4 x float>` vector types and `shufflevector` instructions interleaving the four multiply-accumulate chains into a single SIMD lane. The vectorization report can be surfaced explicitly:

```text
RUSTFLAGS="-C opt-level=3 -C target-cpu=native \
    -C llvm-args=-rpass=loop-vectorize \
    -C llvm-args=-rpass-missed=loop-vectorize" \
    cargo build --release 2>&1 | grep "loop-vectorize"
```

A vectorization miss at this point is a serious finding. The most common cause in graphics kernels is a pointer aliasing ambiguity that LLVM cannot prove away. The fix is to annotate slices with `noalias` semantics (Rust already does this for `&mut` borrows) or to split the loop into a form LLVM can analyze without alias tracking. If you see `missed` messages, check whether you accidentally passed overlapping slices by wrapping both in a single `Vec` backing allocation.

### Reading the Native Disassembly

`cargo-show-asm` queries the compiler for the final object code without requiring you to locate the binary manually:

```text
cargo asm --release vtransform::transform_vertices
```

Look for `vmovups`, `vfmadd213ps`, `vaddps`, or `vmulps` instructions. These are 256-bit AVX2 floating-point operations; each one processes eight single-precision floats simultaneously. If you see only `movss` and `mulss` (scalar single), vectorization did not happen. Count the number of `vfmadd` instructions per loop iteration — a fully vectorized 4×4 multiply should collapse into roughly eight FMA instructions per vector lane, not the thirty-two scalar multiplications the source implies.

For C++ comparison, write the equivalent function in a file `vtransform.cpp` and compile it directly with Clang:

```cpp
// vtransform.cpp
#include <cstddef>
#include <cassert>

struct Vec3 { float x, y, z; };
struct Vec4 { float x, y, z, w; };

struct Mat4 {
    // Column-major: cols[c][r]
    float cols[4][4];
};

static inline Vec4 mat4_mul_vec4(const Mat4* __restrict__ m, Vec4 v) {
    return Vec4{
        m->cols[0][0]*v.x + m->cols[1][0]*v.y + m->cols[2][0]*v.z + m->cols[3][0]*v.w,
        m->cols[0][1]*v.x + m->cols[1][1]*v.y + m->cols[2][1]*v.z + m->cols[3][1]*v.w,
        m->cols[0][2]*v.x + m->cols[1][2]*v.y + m->cols[2][2]*v.z + m->cols[3][2]*v.w,
        m->cols[0][3]*v.x + m->cols[1][3]*v.y + m->cols[2][3]*v.z + m->cols[3][3]*v.w,
    };
}

void transform_vertices(const Mat4* __restrict__ mvp,
                        const Vec3* __restrict__ in,
                        Vec4* __restrict__ out,
                        size_t count)
{
    for (size_t i = 0; i < count; ++i) {
        Vec4 h{ in[i].x, in[i].y, in[i].z, 1.0f };
        out[i] = mat4_mul_vec4(mvp, h);
    }
}
```

```text
clang++ -O3 -march=native -ffast-math -S -o vtransform.s vtransform.cpp
grep -E "vmulps|vfmadd|vaddps|vmovups" vtransform.s | head -20
```

The `__restrict__` qualifiers are the C++ equivalent of Rust's exclusive reference guarantee. Without them, Clang cannot prove `in` and `out` do not alias, and vectorization is typically suppressed. This is the first-principles lesson of the exercise: alias freedom is not a convenience annotation, it is the precondition under which the compiler can generate the SIMD code that makes graphics pipelines fast.

---

## Exercise 2: Cache Miss & Throughput Profiling

### Why Cache Behavior Defines Renderer Performance

A rasterizer's inner loop walks triangles, samples textures, and writes color and depth values to a framebuffer. Each of these operations is a memory access pattern, and the gap between L1 cache bandwidth (~1 TB/s) and main memory bandwidth (~50 GB/s) is what separates a 60 fps title from a 10 fps prototype. The standard diagnostic toolkit for this gap is `perf stat` on Linux combined with flame graphs from `cargo-flamegraph`. Together they tell you both where time is spent and why the memory hierarchy is the bottleneck.

This exercise implements two versions of a software rasterizer's depth buffer update: one that walks the framebuffer in row-major order (cache-friendly) and one that walks it in a strided pattern that simulates what happens when triangles are split incorrectly across tile boundaries. You will measure the difference with hardware performance counters and use a flame graph to confirm the profiler is pointing at the right function.

### The Software Depth Buffer in Rust

Create a second Cargo project:

```text
cargo new --lib depthbuf
cd depthbuf
```

Add the `rand` dependency to `Cargo.toml` for the benchmark data generator:

```toml
[package]
name = "depthbuf"
version = "0.1.0"
edition = "2021"

[dependencies]
rand = "0.8"

[lib]
name = "depthbuf"
crate-type = ["cdylib", "rlib"]

[[bench]]
name = "depth_bench"
harness = false

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
```

Write `src/lib.rs`:

```rust
// src/lib.rs
//
// Two depth buffer update strategies:
//   - sequential: row-major scan, L1/L2 friendly
//   - strided:    column-major scan, L1-hostile on wide buffers

pub struct DepthBuffer {
    pub width: usize,
    pub height: usize,
    pub data: Vec<f32>,
}

impl DepthBuffer {
    /// Allocate a depth buffer filled with 1.0 (maximum depth, far plane).
    pub fn new(width: usize, height: usize) -> Self {
        DepthBuffer {
            width,
            height,
            data: vec![1.0_f32; width * height],
        }
    }

    /// Reset all depth values to 1.0 (clear before a new frame).
    #[inline(never)]
    pub fn clear(&mut self) {
        self.data.fill(1.0_f32);
    }

    /// Row-major depth update: iterate pixels left-to-right, top-to-bottom.
    /// Each pixel is tested against `incoming_depth`; if closer (smaller z),
    /// the buffer is updated.  This is the cache-friendly access pattern.
    #[inline(never)]
    pub fn update_sequential(&mut self, incoming: &[f32]) {
        assert_eq!(incoming.len(), self.width * self.height);
        for (slot, &depth) in self.data.iter_mut().zip(incoming.iter()) {
            if depth < *slot {
                *slot = depth;
            }
        }
    }

    /// Column-major (strided) depth update: iterate pixels top-to-bottom
    /// within each column.  Equivalent work but hostile to cache because
    /// consecutive accesses are `width * 4` bytes apart.
    #[inline(never)]
    pub fn update_strided(&mut self, incoming: &[f32]) {
        assert_eq!(incoming.len(), self.width * self.height);
        let w = self.width;
        let h = self.height;
        for col in 0..w {
            for row in 0..h {
                let idx = row * w + col;
                let depth = incoming[idx];
                if depth < self.data[idx] {
                    self.data[idx] = depth;
                }
            }
        }
    }

    /// Tile-blocked depth update: processes the depth buffer in square tiles
    /// of `tile_size` pixels.  Within each tile the access is row-major,
    /// bounding the working set to tile_size^2 * 4 bytes, which should fit
    /// in L1 for tile_size <= 32 (4 KB on a 32x32 tile).
    #[inline(never)]
    pub fn update_tiled(&mut self, incoming: &[f32], tile_size: usize) {
        assert_eq!(incoming.len(), self.width * self.height);
        let w = self.width;
        let h = self.height;
        let ts = tile_size;
        let mut ty = 0;
        while ty < h {
            let tile_h = (ty + ts).min(h) - ty;
            let mut tx = 0;
            while tx < w {
                let tile_w = (tx + ts).min(w) - tx;
                for row in ty..ty + tile_h {
                    for col in tx..tx + tile_w {
                        let idx = row * w + col;
                        let depth = incoming[idx];
                        if depth < self.data[idx] {
                            self.data[idx] = depth;
                        }
                    }
                }
                tx += ts;
            }
            ty += ts;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sequential_and_strided_produce_identical_results() {
        let w = 64;
        let h = 64;
        let n = w * h;
        // Build a known depth pattern
        let incoming: Vec<f32> = (0..n).map(|i| (i as f32 / n as f32) * 0.9).collect();

        let mut buf_seq = DepthBuffer::new(w, h);
        buf_seq.update_sequential(&incoming);

        let mut buf_str = DepthBuffer::new(w, h);
        buf_str.update_strided(&incoming);

        for i in 0..n {
            assert!(
                (buf_seq.data[i] - buf_str.data[i]).abs() < 1e-7,
                "Mismatch at pixel {}: seq={} str={}",
                i, buf_seq.data[i], buf_str.data[i]
            );
        }
    }

    #[test]
    fn tiled_matches_sequential() {
        let w = 128;
        let h = 128;
        let n = w * h;
        let incoming: Vec<f32> = (0..n).map(|i| 1.0 - (i as f32 / n as f32)).collect();

        let mut buf_seq = DepthBuffer::new(w, h);
        buf_seq.update_sequential(&incoming);

        let mut buf_tile = DepthBuffer::new(w, h);
        buf_tile.update_tiled(&incoming, 32);

        for i in 0..n {
            assert!(
                (buf_seq.data[i] - buf_tile.data[i]).abs() < 1e-7,
                "Mismatch at pixel {}", i
            );
        }
    }

    #[test]
    fn clear_resets_to_one() {
        let mut buf = DepthBuffer::new(16, 16);
        let zeros = vec![0.0_f32; 16 * 16];
        buf.update_sequential(&zeros);
        buf.clear();
        assert!(buf.data.iter().all(|&v| (v - 1.0).abs() < 1e-7));
    }
}
```

```text
cargo test
```

### Writing the Criterion Benchmark

Create `benches/depth_bench.rs`:

```rust
// benches/depth_bench.rs

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use depthbuf::DepthBuffer;
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};

fn make_depth_data(size: usize) -> Vec<f32> {
    let mut rng = SmallRng::seed_from_u64(0xDEAD_BEEF_1234_5678);
    (0..size).map(|_| rng.gen::<f32>()).collect()
}

fn bench_depth_strategies(c: &mut Criterion) {
    let mut group = c.benchmark_group("depth_buffer");
    // Use a 1920x1080 framebuffer — a realistic full-HD render target.
    let width = 1920_usize;
    let height = 1080_usize;
    let n = width * height;
    let incoming = make_depth_data(n);

    group.bench_with_input(
        BenchmarkId::new("sequential", "1920x1080"),
        &(&incoming, width, height),
        |b, (data, w, h)| {
            let mut buf = DepthBuffer::new(*w, *h);
            b.iter(|| {
                buf.update_sequential(black_box(data));
            });
        },
    );

    group.bench_with_input(
        BenchmarkId::new("strided", "1920x1080"),
        &(&incoming, width, height),
        |b, (data, w, h)| {
            let mut buf = DepthBuffer::new(*w, *h);
            b.iter(|| {
                buf.update_strided(black_box(data));
            });
        },
    );

    group.bench_with_input(
        BenchmarkId::new("tiled_32", "1920x1080"),
        &(&incoming, width, height),
        |b, (data, w, h)| {
            let mut buf = DepthBuffer::new(*w, *h);
            b.iter(|| {
                buf.update_tiled(black_box(data), 32);
            });
        },
    );

    group.bench_with_input(
        BenchmarkId::new("tiled_64", "1920x1080"),
        &(&incoming, width, height),
        |b, (data, w, h)| {
            let mut buf = DepthBuffer::new(*w, *h);
            b.iter(|| {
                buf.update_tiled(black_box(data), 64);
            });
        },
    );

    group.finish();
}

criterion_group!(benches, bench_depth_strategies);
criterion_main!(benches);
```

```text
cargo bench
```

You should observe that `sequential` runs in roughly 1–3 ms on a modern laptop, `strided` runs in 10–30 ms (a 5–10× penalty), and `tiled_32` falls somewhere between the two, often close to sequential because the 32×32 tile working set (4 KB of depth data) stays entirely within the 32–64 KB L1 data cache.

### Measuring Hardware Cache Events with `perf`

Criterion reports wall time. To confirm the cache miss hypothesis rather than simply observing the timing difference, use `perf stat`:

```text
cargo build --release --benches
perf stat -e cache-references,cache-misses,L1-dcache-loads,\
L1-dcache-load-misses,LLC-loads,LLC-load-misses \
    target/release/deps/depth_bench-* \
    --bench depth_buffer/sequential/1920x1080 \
    -- --profile-time 5
```

Repeat with `strided`:

```text
perf stat -e cache-references,cache-misses,L1-dcache-loads,\
L1-dcache-load-misses,LLC-loads,LLC-load-misses \
    target/release/deps/depth_bench-* \
    --bench depth_buffer/strided/1920x1080 \
    -- --profile-time 5
```

Compare `L1-dcache-load-misses` between the two runs. For the strided case you should see the L1 miss rate approach 100% — every access is a miss because consecutive loop iterations are `width * 4 = 7680` bytes apart, far beyond any cache line boundary (64 bytes). For sequential, the miss rate will be close to 1/16 (one miss per 16 floats, which is one cache line's worth of data), reflecting the hardware prefetcher successfully streaming ahead.

### Generating a Flame Graph

```text
cargo flamegraph --bench depth_bench -- \
    --bench depth_buffer/strided/1920x1080 --profile-time 10
```

Open `flamegraph.svg` in a browser. You will see `update_strided` occupying a broad stack frame with `perf`'s cycle attribution. The wide flat bar with no child frames confirms that all time is spent in the tight loop itself — there is no deeper call tree to optimize. The diagnostic conclusion is unambiguous: the work is memory-bound, not compute-bound. The fix is tiling, not algorithmic restructuring.

---

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

### The Parallel Tile Renderer Problem

Modern software renderers divide the framebuffer into tiles and dispatch them to a thread pool. Each thread renders a disjoint set of tiles and writes to a non-overlapping region of the framebuffer. If the tile decomposition is correct, there are no data races. If a programmer makes an off-by-one error in the tile boundary calculation, two threads will write to the same pixel, producing a data race that is undefined behavior in C++ and a logic bug in Rust's safe code (Rust prevents the race at compile time, but the boundary error still produces incorrect output).

This exercise has two parts. First, you implement the tile renderer in C++ with a deliberate off-by-one that creates a data race, then you detect it with ThreadSanitizer. Second, you implement the Rust version using `rayon` and demonstrate that the borrow checker forces correct tile decomposition at compile time, then introduce an `unsafe` bypass to show what ThreadSanitizer catches even in Rust.

### C++ Tile Renderer with Deliberate Data Race

Create `tilerender.cpp`:

```cpp
// tilerender.cpp
//
// A minimal parallel tile renderer that fills a framebuffer with a
// procedural gradient.  The tile decomposition has a deliberate off-by-one
// error on the right edge of each tile, causing adjacent threads to write
// to the same column of pixels.
//
// Compile with ThreadSanitizer:
//   clang++ -O1 -g -fsanitize=thread -std=c++17 -pthread \
//           -o tilerender tilerender.cpp

#include <vector>
#include <thread>
#include <cstdint>
#include <cstdio>
#include <cmath>
#include <cassert>

struct Pixel {
    uint8_t r, g, b, a;
};

struct Framebuffer {
    int width;
    int height;
    std::vector<Pixel> data;

    Framebuffer(int w, int h) : width(w), height(h), data(w * h) {}

    Pixel& at(int x, int y) {
        assert(x >= 0 && x < width && y >= 0 && y < height);
        return data[y * width + x];
    }
};

// Render one horizontal tile [x_start, x_end) x [y_start, y_end).
// The gradient maps pixel position to color deterministically.
static void render_tile(Framebuffer* fb,
                         int x_start, int x_end,
                         int y_start, int y_end)
{
    for (int y = y_start; y < y_end; ++y) {
        for (int x = x_start; x < x_end; ++x) {
            float u = static_cast<float>(x) / static_cast<float>(fb->width);
            float v = static_cast<float>(y) / static_cast<float>(fb->height);
            float r = u;
            float g = v;
            float b = 0.5f + 0.5f * std::sin(u * 6.283f + v * 3.1415f);
            fb->at(x, y) = Pixel{
                static_cast<uint8_t>(r * 255.0f),
                static_cast<uint8_t>(g * 255.0f),
                static_cast<uint8_t>(b * 255.0f),
                255
            };
        }
    }
}

int main() {
    const int WIDTH  = 256;
    const int HEIGHT = 256;
    const int TILE_W = 64;
    const int TILE_H = 64;

    Framebuffer fb(WIDTH, HEIGHT);

    std::vector<std::thread> threads;

    for (int ty = 0; ty < HEIGHT; ty += TILE_H) {
        for (int tx = 0; tx < WIDTH; tx += TILE_W) {
            int x_start = tx;
            // BUG: x_end extends one pixel past the tile boundary,
            // overlapping with the next tile's x_start.  When two
            // threads process adjacent tiles, they race on column
            // (tx + TILE_W).
            int x_end   = std::min(tx + TILE_W + 1, WIDTH);
            int y_start = ty;
            int y_end   = std::min(ty + TILE_H, HEIGHT);

            threads.emplace_back(render_tile, &fb,
                                 x_start, x_end, y_start, y_end);
        }
    }

    for (auto& t : threads) {
        t.join();
    }

    // Verify a known pixel value at the center to confirm rendering ran.
    Pixel center = fb.at(WIDTH / 2, HEIGHT / 2);
    printf("Center pixel: r=%u g=%u b=%u a=%u\n",
           center.r, center.g, center.b, center.a);
    printf("Render complete: %d x %d framebuffer\n", WIDTH, HEIGHT);
    return 0;
}
```

Compile and run without sanitizers first to observe that the program appears to work correctly:

```text
clang++ -O1 -g -std=c++17 -pthread -o tilerender tilerender.cpp
./tilerender
```

Now compile and run with ThreadSanitizer:

```text
clang++ -O1 -g -fsanitize=thread -std=c++17 -pthread \
        -o tilerender_tsan tilerender.cpp
./tilerender_tsan
```

ThreadSanitizer will emit a report similar to the following:

```text
WARNING: ThreadSanitizer: data race (pid=XXXXX)
  Write of size 4 at 0x... by thread T5:
    #0 render_tile(Framebuffer*, int, int, int, int) tilerender.cpp:44
    #1 ...

  Previous write of size 4 at 0x... by thread T4:
    #0 render_tile(Framebuffer*, int, int, int, int) tilerender.cpp:44
    #1 ...
```

The report names the exact source line, the two threads involved, and the memory address. The fix is mechanical: change `tx + TILE_W + 1` to `tx + TILE_W`. Recompile with ThreadSanitizer and confirm the report disappears.

### Rust Parallel Renderer with AddressSanitizer

Create a new Cargo project:

```text
cargo new --lib tilerust
cd tilerust
```

Add `rayon` to `Cargo.toml`:

```toml
[package]
name = "tilerust"
version = "0.1.0"
edition = "2021"

[dependencies]
rayon = "1.10"
```

Write `src/lib.rs`:

```rust
// src/lib.rs
//
// Parallel tile renderer using Rayon.  The safe Rust version demonstrates
// that the borrow checker enforces disjoint tile ownership at compile time.
// The unsafe version bypasses this guarantee and is instrumented for TSAN.

use rayon::prelude::*;

#[derive(Clone, Copy, Default)]
#[repr(C)]
pub struct Pixel {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: u8,
}

pub struct Framebuffer {
    pub width:  usize,
    pub height: usize,
    pub data:   Vec<Pixel>,
}

impl Framebuffer {
    pub fn new(width: usize, height: usize) -> Self {
        Framebuffer {
            width,
            height,
            data: vec![Pixel::default(); width * height],
        }
    }

    /// Render all tiles in parallel using Rayon.  Rayon's `chunks_mut`
    /// splits the data slice into non-overlapping mutable sub-slices,
    /// and the borrow checker enforces that no two closures hold mutable
    /// references to the same slice.  Attempting to do so is a compile
    /// error, not a runtime race.
    pub fn render_parallel(&mut self, tile_height: usize) {
        let width = self.width;
        let height = self.height;

        self.data
            .chunks_mut(tile_height * width)
            .enumerate()
            .par_bridge()
            .for_each(|(tile_row, tile_data)| {
                let y_start = tile_row * tile_height;
                for (local_idx, pixel) in tile_data.iter_mut().enumerate() {
                    let local_row = local_idx / width;
                    let col       = local_idx % width;
                    let y         = y_start + local_row;
                    let u = col as f32 / width as f32;
                    let v = y   as f32 / height as f32;
                    let r = (u * 255.0) as u8;
                    let g = (v * 255.0) as u8;
                    let b = ((0.5 + 0.5 * (u * 6.283 + v * 3.1415).sin()) * 255.0) as u8;
                    *pixel = Pixel { r, g, b, a: 255 };
                }
            });
    }

    /// Intentionally unsafe version that shares a raw pointer across threads.
    /// This is what happens when a programmer tries to bypass Rust's ownership
    /// rules with unsafe pointer aliasing.  AddressSanitizer and
    /// ThreadSanitizer will catch the resulting race.
    ///
    /// # Safety
    /// This function deliberately creates a data race to demonstrate TSAN
    /// detection.  Do not call this in production code.
    pub unsafe fn render_parallel_racy(&mut self, tile_height: usize) {
        use std::sync::Arc;
        use std::thread;

        let width  = self.width;
        let height = self.height;
        let ptr = self.data.as_mut_ptr();
        // Wrap the raw pointer in a type that is Send so we can ship it
        // across thread boundaries.  This is the invariant violation:
        // multiple threads write to overlapping regions.
        struct SendPtr(*mut Pixel);
        unsafe impl Send for SendPtr {}

        let ptr = Arc::new(SendPtr(ptr));
        let mut handles = Vec::new();

        let mut y = 0_usize;
        while y < height {
            let y_end = (y + tile_height + 1).min(height); // off-by-one intentional
            let ptr_clone = Arc::clone(&ptr);
            let handle = thread::spawn(move || {
                for row in y..y_end {
                    for col in 0..width {
                        let idx = row * width + col;
                        let u = col as f32 / width as f32;
                        let v = row as f32 / height as f32;
                        unsafe {
                            *ptr_clone.0.add(idx) = Pixel {
                                r: (u * 255.0) as u8,
                                g: (v * 255.0) as u8,
                                b: 128,
                                a: 255,
                            };
                        }
                    }
                }
            });
            handles.push(handle);
            y += tile_height;
        }

        for h in handles {
            h.join().unwrap();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn safe_render_fills_all_pixels() {
        let mut fb = Framebuffer::new(128, 128);
        fb.render_parallel(32);
        // Every pixel must have been written (alpha = 255 everywhere).
        for pixel in &fb.data {
            assert_eq!(pixel.a, 255, "Pixel not written");
        }
    }

    #[test]
    fn safe_render_top_left_is_black() {
        let mut fb = Framebuffer::new(256, 256);
        fb.render_parallel(64);
        // Top-left pixel: u=0, v=0 → r=0, g=0
        let p = fb.data[0];
        assert_eq!(p.r, 0);
        assert_eq!(p.g, 0);
    }

    #[test]
    fn safe_render_deterministic() {
        let mut fb1 = Framebuffer::new(64, 64);
        fb1.render_parallel(16);
        let mut fb2 = Framebuffer::new(64, 64);
        fb2.render_parallel(16);
        for (a, b) in fb1.data.iter().zip(fb2.data.iter()) {
            assert_eq!(a.r, b.r);
            assert_eq!(a.g, b.g);
            assert_eq!(a.b, b.b);
        }
    }
}
```

Run the safe tests:

```text
cargo test
```

Now run with ThreadSanitizer to exercise the `unsafe` path. TSAN requires the nightly toolchain and the `rust-src` component that you installed during setup:

```text
RUSTFLAGS="-Z sanitizer=thread" \
    cargo +nightly test --target x86_64-unknown-linux-gnu -- \
    --nocapture 2>&1 | head -60
```

To specifically trigger the racy path, write a small integration test binary at `src/main.rs` or add it inline:

```rust
// src/bin/race_demo.rs
use tilerust::Framebuffer;

fn main() {
    let mut fb = Framebuffer::new(256, 256);
    // Safety: intentionally racy for TSAN demonstration only.
    unsafe { fb.render_parallel_racy(64); }
    println!("Rendered {} pixels", fb.data.len());
}
```

```text
RUSTFLAGS="-Z sanitizer=thread" \
    cargo +nightly run --bin race_demo \
    --target x86_64-unknown-linux-gnu 2>&1 | head -40
```

ThreadSanitizer will report a data race on the overlapping row pixels with full Rust stack traces. The report will reference the `unsafe` block by line number, which is exactly the information a code reviewer needs to identify the invariant violation.

### AddressSanitizer for Out-of-Bounds Framebuffer Writes in C++

AddressSanitizer (ASAN) catches a different class of bug: writing past the end of an allocated buffer. In a rasterizer, this happens when a triangle's bounding box is computed incorrectly and the fill loop iterates past the framebuffer edge. The following C++ snippet demonstrates the vulnerability and the sanitizer's response:

```cpp
// asan_demo.cpp
// Compile: clang++ -O1 -g -fsanitize=address -o asan_demo asan_demo.cpp

#include <cstdio>
#include <cstdlib>
#include <cstring>

struct Pixel { unsigned char r, g, b, a; };

// Rasterize a horizontal span [x_start, x_end) on scanline y.
// BUG: no bounds check on x_end against fb_width.
static void fill_span(Pixel* fb, int fb_width,
                       int y, int x_start, int x_end,
                       unsigned char r, unsigned char g, unsigned char b)
{
    for (int x = x_start; x < x_end; ++x) {
        int idx = y * fb_width + x;
        fb[idx] = Pixel{r, g, b, 255};  // OOB write when x_end > fb_width
    }
}

int main() {
    const int W = 64;
    const int H = 64;
    Pixel* fb = static_cast<Pixel*>(malloc(W * H * sizeof(Pixel)));
    memset(fb, 0, W * H * sizeof(Pixel));

    // Intentional bug: x_end is 72, which is 8 pixels past the right edge.
    fill_span(fb, W, 10, 0, W + 8, 255, 128, 0);

    printf("Span filled (should not reach here cleanly)\n");
    free(fb);
    return 0;
}
```

```text
clang++ -O1 -g -fsanitize=address -o asan_demo asan_demo.cpp
./asan_demo
```

ASAN will halt execution and print a detailed report:

```text
==XXXXX==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...
WRITE of size 4 at 0x... thread T0
    #0 fill_span asan_demo.cpp:18
    #1 main asan_demo.cpp:32
Shadow bytes around the buggy address: ...
```

The shadow byte map in the ASAN report shows exactly which bytes are valid heap memory and which are in the ASAN red zone placed beyond the allocation. The fix is a single bounds clamp: `int x_end_clamped = (x_end < fb_width) ? x_end : fb_width;`. After applying it, recompile and confirm that ASAN reports no errors.

---

## Developer Cheat Sheet & Toolchain Checklist

### Diagnostic Command Reference

The following commands are your first-response toolkit for graphics pipeline debugging. Each entry states what it measures and what a bad result looks like.

| Command | What it measures | Actionable signal |
|---|---|---|
| `cargo test` | Functional correctness of all `#[test]` functions | Any failure is a regression; fix before profiling |
| `cargo check` | Type and borrow errors without compiling | Faster than `build`; run on every save |
| `cargo bench` | Wall-time throughput via Criterion | Regressions > 5% warrant investigation |
| `cargo asm --release <fn>` | Native disassembly of a named function | Absence of `vmulps`/`vfmadd` indicates missed vectorization |
| `cargo flamegraph` | CPU-time attribution via `perf record` | Wide flat frames with no children indicate memory-bound loops |
| `RUSTFLAGS="-Z sanitizer=address" cargo +nightly test` | Heap OOB reads/writes, use-after-free | Any ASAN report is a bug; zero false positives expected |
| `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test` | Data races in concurrent code | Any TSAN report in `unsafe` code requires immediate audit |
| `RUSTFLAGS="-Z sanitizer=memory" cargo +nightly test` | Reads from uninitialized memory | Critical for C FFI layers and raw buffer allocation |
| `clang++ -fsanitize=address` | Heap OOB in C++ rasterizer code | Full shadow map; ASAN_OPTIONS=detect_leaks=1 adds leak check |
| `clang++ -fsanitize=thread` | Data races in C++ parallel renderer | Requires `-O1` minimum; `-O0` produces false positives |
| `perf stat -e cache-misses,L1-dcache-load-misses` | Hardware cache event counts | Miss rate > 10% on a tight loop signals layout problem |
| `valgrind --tool=massif` | Heap allocation profile over time | Growing heap with no corresponding free signals a leak |
| `valgrind --tool=cachegrind` | Simulated cache behavior | `D1mr` (L1 data miss rate) > 1 miss per 16 accesses is poor |

### Pre-Commit Checklist for Graphics Code

Every graphics subsystem change — a new render pass, a modified vertex buffer layout, a changed tile decomposition — should clear this checklist before merge.

Run `cargo test` and confirm zero failures. Run `cargo check` and resolve every warning, because warnings in graphics code are often the linker's way of telling you that an aliasing assumption or unused field will cause a subtle bug under optimization. Run `cargo bench` and compare the output against the baseline on the same machine; graphics pipelines are hardware-sensitive and you must control for thermal throttling by running benchmarks twice and taking the second result.

For any function that uses `unsafe`, run `cargo +nightly test` with both AddressSanitizer and ThreadSanitizer in separate invocations. These two sanitizers cannot be combined in a single binary because their shadow memory mappings conflict. If the codebase crosses the C FFI boundary (calling OpenGL, Vulkan, or Metal through `bindgen`-generated wrappers), run Valgrind's Memcheck on the full binary in addition to ASAN, because ASAN cannot track memory allocated inside shared libraries compiled without `-fsanitize=address`.

After correctness is confirmed, run `cargo flamegraph` on the dominant render path and verify that the flamegraph shows no unexpected call depth: a rasterizer's inner loop should appear as a single wide frame at the bottom of the stack, not as a chain of nested calls that indicate virtual dispatch or repeated small allocations inside the per-pixel loop. If the flame graph shows allocation functions (`malloc`, `jemalloc::alloc`) inside the inner loop, you have a geometry submission path that is allocating per-draw-call and needs a free-list or arena allocator.

Finally, dump the LLVM IR for the three hottest functions identified by the flame graph with `RUSTFLAGS="--emit=llvm-ir -C opt-level=3 -C target-cpu=native" cargo build --release` and verify that SIMD vector types (`<4 x float>`, `<8 x float>`) are present in the IR for any function that processes vertex or pixel arrays. If they are absent, check for pointer aliasing, early returns inside the loop body, or non-power-of-two loop trip counts that suppress vectorization, and annotate accordingly.

### Toolchain Installation Verification Script

Save this as `verify_toolchain.sh` at the root of any graphics project to confirm the full diagnostic stack is present before beginning work:

```bash
#!/usr/bin/env bash
# verify_toolchain.sh
# Confirms every diagnostic tool used in these labs is installed and functional.

set -euo pipefail

PASS="\033[0;32mPASS\033[0m"
FAIL="\033[0;31mFAIL\033[0m"

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        printf "%-40s %b\n" "$name" "$PASS"
    else
        printf "%-40s %b\n" "$name" "$FAIL"
    fi
}

echo "=== Graphics Toolchain Verification ==="
check "rustc (stable)"            "rustc --version"
check "rustc (nightly)"           "rustup run nightly rustc --version"
check "cargo"                     "cargo --version"
check "cargo-flamegraph"          "cargo flamegraph --help"
check "cargo-show-asm"            "cargo asm --help"
check "clang"                     "clang --version"
check "clang++ (C++17 support)"   "echo 'int main(){}' | clang++ -std=c++17 -x c++ - -o /dev/null"
check "ASAN (clang)"              "echo 'int main(){}' | clang -fsanitize=address -x c - -o /dev/null"
check "TSAN (clang)"              "echo 'int main(){}' | clang -fsanitize=thread -x c - -o /dev/null"
check "lldb"                      "lldb --version"
check "valgrind"                  "valgrind --version"
check "perf"                      "perf --version"
check "rust-src component"        "rustup component list --installed | grep rust-src"
check "llvm-tools-preview"        "rustup component list --installed | grep llvm-tools"

echo ""
echo "Any FAIL above must be resolved before running the lab exercises."
```

```text
chmod +x verify_toolchain.sh
./verify_toolchain.sh
```

Every line must print `PASS` before the first exercise begins. A failing `perf` check typically means `linux-perf` is not installed or the user lacks `CAP_PERFMON` capability; fix the latter with `sudo sysctl -w kernel.perf_event_paranoid=1` for the duration of the lab session.
