# Operational Verification Labs: Mobile Development

## Objective & Toolchain Setup

This lab guide treats mobile development the way embedded and systems engineers treat firmware: not as a black box to click through in an IDE, but as a stack of compiled artifacts whose correctness, performance, and safety must be mechanically verified at every layer. The exercises that follow use Rust, C++, and Go as the primary implementation languages because each represents a distinct memory model and compilation philosophy that maps directly onto the constraints you face when writing mobile libraries, FFI bridges, and background processing engines for iOS and Android targets. By the end of these labs you will be able to interpret LLVM IR and disassembly for a cross-compiled ARM64 binary, attribute cache misses to specific data-layout decisions using `perf` and `cargo-flamegraph`, and confirm thread-safety guarantees using ThreadSanitizer under a controlled data-race harness.

The pedagogy here is instrument-first. Every claim about performance or safety will be verified with a command you can run, an output you can read, and a number you can compare against a baseline.

### Toolchain Installation

The lab environment targets a Linux host (Ubuntu 22.04 or Arch) cross-compiling to `aarch64-linux-android` and `aarch64-apple-ios` targets, with native execution for sanitizer runs (sanitizers require the native target because they inject runtime shims that Android's Bionic and iOS's dyld do not support in the same way as the host glibc/libSystem).

Install the complete toolchain in a single session:

```bash
# 1. Rust via rustup, with the Android NDK and iOS cross targets
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
source "$HOME/.cargo/env"
rustup target add aarch64-linux-android aarch64-apple-ios x86_64-unknown-linux-gnu
rustup component add llvm-tools-preview rust-src clippy rustfmt

# 2. LLVM/Clang 17 (provides llvm-dis, llc, opt, llvm-objdump, clang-tidy)
sudo apt-get install -y clang-17 llvm-17 lld-17 lldb-17 \
    libclang-17-dev clang-tools-17
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-17 100
sudo update-alternatives --install /usr/bin/llvm-objdump llvm-objdump /usr/bin/llvm-objdump-17 100

# 3. Android NDK r26b (provides the AArch64 cross-linker and sysroot)
wget https://dl.google.com/android/repository/android-ndk-r26b-linux.zip -O /tmp/ndk.zip
unzip /tmp/ndk.zip -d $HOME/android-ndk
export ANDROID_NDK_HOME="$HOME/android-ndk/android-ndk-r26b"
export PATH="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH"

# 4. Cargo tooling
cargo install cargo-flamegraph cargo-asm cargo-binutils flamegraph

# 5. Valgrind (leak + memcheck; native x86_64 only)
sudo apt-get install -y valgrind linux-tools-$(uname -r) linux-tools-generic

# 6. Go 1.22 with race detector support
wget https://go.dev/dl/go1.22.4.linux-amd64.tar.gz -O /tmp/go.tar.gz
sudo tar -C /usr/local -xzf /tmp/go.tar.gz
export PATH="/usr/local/go/bin:$PATH"

# Verify the entire chain
rustc --version && clang --version && go version && valgrind --version
```

Configure the Android cross-linker for Cargo by creating `.cargo/config.toml` at the project root:

```toml
[target.aarch64-linux-android]
linker = "aarch64-linux-android34-clang"
ar = "llvm-ar"

[target.aarch64-apple-ios]
linker = "rust-lld"

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
debug = true        # retain DWARF for profiler symbol resolution

[profile.bench]
opt-level = 3
debug = true
```

The `debug = true` flag on release and bench profiles is not a mistake. DWARF symbols are stripped from the final `.ipa` or `.apk` artifact by the packaging toolchain, but retaining them locally is what makes `perf report`, `cargo-flamegraph`, and LLDB symbolication actually useful during lab work. Without symbols you get raw addresses and nothing else.

---

## Exercise 1: AST, IR & Disassembly Analysis

### Motivation

Mobile libraries written in Rust or C++ are compiled once and linked into an application binary that runs on a device you cannot attach a kernel debugger to without special provisioning. The only window into what the compiler actually produced is the intermediate representation and the resulting machine code. This exercise builds the habit of reading LLVM IR and AArch64 disassembly as a routine verification step, not an emergency measure. You will implement a small but realistic signal-processing kernel — a fixed-point FIR filter — in Rust, observe how `rustc` lowers it through MIR to LLVM IR, and then confirm that the backend produces vectorized NEON instructions for the AArch64 target.

### The Implementation

Create a new library crate:

```bash
cargo new --lib mobile_fir && cd mobile_fir
```

Replace `src/lib.rs` with the following complete implementation:

```rust
//! mobile_fir/src/lib.rs
//!
//! A fixed-point FIR filter kernel designed to demonstrate LLVM vectorization
//! on AArch64 targets (Android / iOS). All arithmetic is Q15 fixed-point
//! (1 sign bit, 15 fractional bits) to match common DSP pipeline conventions
//! in audio and sensor-fusion stacks.

#![no_std]
#![cfg_attr(target_arch = "aarch64", feature(target_feature_11))]

/// Apply a 16-tap FIR filter to `input`, writing results to `output`.
///
/// Both slices must have the same length. `coeffs` holds 16 Q15 coefficients.
/// The accumulator is widened to i64 to prevent overflow before the final
/// right-shift back to Q15.
#[inline(never)]   // prevent inlining so the symbol is visible in disassembly
pub fn fir_filter_q15(
    input: &[i16],
    coeffs: &[i16; 16],
    output: &mut [i16],
) {
    assert_eq!(input.len(), output.len());
    let n = input.len();

    for i in 0..n {
        let mut acc: i64 = 0;
        for (k, &c) in coeffs.iter().enumerate() {
            let sample = if i >= k { input[i - k] } else { 0i16 };
            acc += (sample as i64) * (c as i64);
        }
        // Q15 -> Q15: shift right by 15, saturate to i16 range
        let result = (acc >> 15).clamp(i16::MIN as i64, i16::MAX as i64) as i16;
        output[i] = result;
    }
}

/// Compute the L2-norm squared of a Q15 signal vector.
/// Returns a u64 to hold the full accumulated energy without overflow for
/// signals up to 2^32 samples (impractical but safe by type).
#[inline(never)]
pub fn energy_q15(signal: &[i16]) -> u64 {
    signal.iter().map(|&s| (s as i64 * s as i64) as u64).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_single_tap() {
        // A filter with only the first coefficient set to 1.0 (0x7FFF in Q15)
        // is a near-identity: output[i] ≈ input[i] (small rounding from >>15).
        let input: Vec<i16> = (0i16..32).collect();
        let mut output = vec![0i16; 32];
        let mut coeffs = [0i16; 16];
        coeffs[0] = 0x4000; // 0.5 in Q15 — avoids saturation, easier to verify
        fir_filter_q15(&input, &coeffs, &mut output);
        for (i, (&inp, &out)) in input.iter().zip(output.iter()).enumerate() {
            let expected = ((inp as i64 * 0x4000i64) >> 15) as i16;
            assert_eq!(out, expected, "mismatch at index {}", i);
        }
    }

    #[test]
    fn energy_known_signal() {
        let signal: Vec<i16> = vec![100, -100, 100, -100];
        assert_eq!(energy_q15(&signal), 40000u64);
    }
}
```

Because this crate uses `#![no_std]`, add a small shim to `Cargo.toml` to allow running tests under the host's std:

```toml
[package]
name = "mobile_fir"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["staticlib", "rlib"]

[features]
default = []
std = []

[dev-dependencies]
# none required
```

Add `src/main.rs` only for the purpose of having an entry point that `cargo test` can use in std mode. Instead, run tests directly:

```bash
cargo test --target x86_64-unknown-linux-gnu
```

### Reading the LLVM IR

Instruct `rustc` to emit LLVM IR before optimization passes (MIR lowering output) and after the full optimization pipeline:

```bash
# Unoptimized IR — closest to what rustc's MIR produced
RUSTFLAGS="--emit=llvm-ir -C opt-level=0" \
    cargo build --target x86_64-unknown-linux-gnu 2>/dev/null
find target/ -name "*.ll" | head -5

# Optimized IR for the AArch64 Android target
RUSTFLAGS="--emit=llvm-ir -C opt-level=3 -C target-cpu=generic" \
    cargo build --target aarch64-linux-android 2>/dev/null
find target/ -name "*.ll" | grep aarch64
```

Open the optimized `.ll` file. Navigate to the `fir_filter_q15` function. You are looking for three structural features that confirm the optimizer did its job. First, the inner `coeffs.iter().enumerate()` loop over 16 elements should have been fully unrolled — you will see 16 blocks of `mul`, `add`, and `sext` instructions rather than a loop-back branch. Second, the Q15 accumulator should use `i64` arithmetic throughout before a final `trunc` back to `i16`. Third, if you rebuild with `-C target-feature=+neon`, the IR will contain `<8 x i16>` or `<4 x i32>` LLVM vector types, which is the LLVM representation of NEON SIMD lanes.

```bash
# Rerun with explicit NEON feature flag
RUSTFLAGS="--emit=llvm-ir -C opt-level=3 -C target-cpu=cortex-a55 -C target-feature=+neon" \
    cargo build --target aarch64-linux-android 2>/dev/null

# Grep for vectorized types in the IR
grep -E "<[0-9]+ x i(16|32|64)>" target/aarch64-linux-android/debug/deps/*.ll | head -20
```

### Cross-Compiled Disassembly

Produce the final object file and disassemble it:

```bash
# Build a release artifact with DWARF symbols
RUSTFLAGS="-C opt-level=3 -C target-cpu=cortex-a55 -C target-feature=+neon -g" \
    cargo build --release --target aarch64-linux-android

# Locate the rlib and extract the object file
AR_FILE=$(find target/aarch64-linux-android/release/deps -name "libmobile_fir*.rlib" | head -1)
mkdir -p /tmp/fir_obj && cp "$AR_FILE" /tmp/fir_obj/
cd /tmp/fir_obj && ar x libmobile_fir*.rlib
ls *.o

# Disassemble the object file
llvm-objdump --arch-name=aarch64 --disassemble-symbols=_ZN10mobile_fir14fir_filter_q1517h*.o \
    --no-show-raw-insn --demangle *.o 2>/dev/null | head -80

# If the mangled symbol is uncertain, list all symbols first
llvm-objdump --syms *.o | grep fir
```

What you are verifying in the disassembly output is the presence of NEON instructions: `smull` (signed multiply long), `smlal` (signed multiply accumulate long), `sqshrn` (saturating shift right narrow), and optionally `ld1` / `st1` vector load/store pairs. The presence of `sqshrn` is particularly meaningful because it performs both the right-shift and the saturation clamp that you wrote explicitly as `.clamp(i16::MIN as i64, i16::MAX as i64)` in the Rust source — the compiler recognized the pattern and replaced it with a single instruction.

### Using `cargo-asm` for a Faster Workflow

For native-target work during iterative development, `cargo-asm` gives you immediate annotated disassembly without manual `ar` extraction:

```bash
# Show disassembly for the energy function (native host target)
cargo asm --release mobile_fir::energy_q15

# Show disassembly with interleaved source lines
cargo asm --release --rust mobile_fir::fir_filter_q15
```

The `--rust` flag interleaves the Rust source with the corresponding assembly, which is the fastest way to verify that a specific line of source code maps to the instruction you expect. If you see a `bl` (branch-and-link) to `core::panicking::panic_bounds_check` in the output, the bounds elimination pass failed for some reason — typically an aliased slice pointer that the optimizer could not prove non-overlapping. In that case, restructure the slice access as a raw pointer with an explicit length check at the entry point to give the optimizer the alias information it needs.

---

## Exercise 2: Cache Miss & Throughput Profiling

### Motivation

Mobile SoCs — the Cortex-A55 efficiency cores in a Snapdragon 8 Gen 2, for example — have L1 data caches between 32 KB and 64 KB and L2 caches around 512 KB. The gap in throughput between an algorithm that fits its working set in L1 versus one that spills to main memory is not 10% or 20%; it is frequently 5x to 20x, and on a battery-constrained device the memory traffic also directly increases power draw. This exercise quantifies that gap precisely using `perf stat` and `cargo-flamegraph`, using a deliberately cache-hostile matrix traversal as the pathological baseline and an optimized tiled version as the corrected implementation.

### The Benchmark Harness

Create a new binary crate:

```bash
cargo new cache_bench && cd cache_bench
```

Add the benchmark and profiling dependencies to `Cargo.toml`:

```toml
[package]
name = "cache_bench"
version = "0.1.0"
edition = "2021"

[[bench]]
name = "matrix_traversal"
harness = false

[dependencies]

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[profile.bench]
opt-level = 3
debug = true
codegen-units = 1
lto = "fat"
```

Create `benches/matrix_traversal.rs`:

```rust
//! benches/matrix_traversal.rs
//!
//! Compares column-major (cache-hostile) vs row-major (cache-friendly) vs
//! cache-tiled matrix summation on a 1024×1024 i32 matrix (~4 MB working set,
//! comfortably above L1/L2 on most mobile SoCs).

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use std::hint::black_box as bb;

const N: usize = 1024;
const TILE: usize = 64; // 64×64 tile × 4 bytes = 16 KB — fits in L1

fn make_matrix() -> Vec<i32> {
    (0..N * N).map(|i| (i % 32767) as i32).collect()
}

/// Column-major traversal: strides across rows in memory, causing a cache miss
/// on nearly every access when N × sizeof(i32) > cache_line_size (which it
/// always does for N=1024, stride = 4096 bytes, cache line = 64 bytes).
fn sum_column_major(m: &[i32]) -> i64 {
    let mut acc: i64 = 0;
    for col in 0..N {
        for row in 0..N {
            acc += m[row * N + col] as i64;
        }
    }
    acc
}

/// Row-major traversal: sequential memory access, maximizing spatial locality.
fn sum_row_major(m: &[i32]) -> i64 {
    let mut acc: i64 = 0;
    for row in 0..N {
        for col in 0..N {
            acc += m[row * N + col] as i64;
        }
    }
    acc
}

/// Tiled traversal: processes TILE×TILE sub-matrices, keeping the active
/// working set within L1 cache for the duration of each inner loop nest.
fn sum_tiled(m: &[i32]) -> i64 {
    let mut acc: i64 = 0;
    let mut row_tile = 0;
    while row_tile < N {
        let mut col_tile = 0;
        while col_tile < N {
            let row_end = (row_tile + TILE).min(N);
            let col_end = (col_tile + TILE).min(N);
            for row in row_tile..row_end {
                for col in col_tile..col_end {
                    acc += m[row * N + col] as i64;
                }
            }
            col_tile += TILE;
        }
        row_tile += TILE;
    }
    acc
}

fn bench_traversals(c: &mut Criterion) {
    let matrix = make_matrix();
    let mut group = c.benchmark_group("matrix_sum");
    group.throughput(Throughput::Bytes((N * N * std::mem::size_of::<i32>()) as u64));

    group.bench_function("column_major", |b| {
        b.iter(|| sum_column_major(black_box(&matrix)))
    });
    group.bench_function("row_major", |b| {
        b.iter(|| sum_row_major(black_box(&matrix)))
    });
    group.bench_function("tiled_64", |b| {
        b.iter(|| sum_tiled(black_box(&matrix)))
    });

    group.finish();
}

criterion_group!(benches, bench_traversals);
criterion_main!(benches);
```

Run the benchmark and record wall-clock throughput:

```bash
cargo bench --bench matrix_traversal 2>&1 | tee bench_results.txt
```

Criterion will report throughput in GiB/s for each variant. The column-major result will typically be 3–8× slower than row-major on a modern x86_64 host, and the tiled result will be within 5–15% of row-major while being meaningfully faster than column-major on working sets that exceed L2 but not L3.

### Hardware Performance Counter Profiling with `perf`

Wall-clock time tells you *that* there is a problem. Hardware performance counters tell you *why*. Linux's `perf` subsystem reads CPU-internal event registers — the same mechanism ARM's CoreSight uses on Android devices — to count cache misses, branch mispredictions, and instruction retired events at nanosecond resolution.

Write a standalone binary that exercises each traversal variant for a fixed number of iterations, isolated enough for `perf stat` attribution:

```rust
// src/main.rs
fn main() {
    const N: usize = 1024;
    const ITERS: usize = 20;
    let matrix: Vec<i32> = (0..N * N).map(|i| (i % 32767) as i32).collect();

    let mode = std::env::args().nth(1).unwrap_or_else(|| "row".to_string());

    let mut total: i64 = 0;
    for _ in 0..ITERS {
        total += match mode.as_str() {
            "col" => sum_column_major(&matrix),
            "row" => sum_row_major(&matrix),
            "tile" => sum_tiled(&matrix),
            _ => panic!("unknown mode: use col, row, or tile"),
        };
    }
    // prevent dead-code elimination
    println!("{}", total);
}

// Paste the three traversal functions from the benchmark here verbatim.
// (In a real project these live in lib.rs; duplicated here for a self-contained binary.)

const N: usize = 1024;
const TILE: usize = 64;

fn sum_column_major(m: &[i32]) -> i64 {
    let mut acc: i64 = 0;
    for col in 0..N {
        for row in 0..N {
            acc += m[row * N + col] as i64;
        }
    }
    acc
}

fn sum_row_major(m: &[i32]) -> i64 {
    let mut acc: i64 = 0;
    for row in 0..N {
        for col in 0..N {
            acc += m[row * N + col] as i64;
        }
    }
    acc
}

fn sum_tiled(m: &[i32]) -> i64 {
    let mut acc: i64 = 0;
    let mut row_tile = 0;
    while row_tile < N {
        let mut col_tile = 0;
        while col_tile < N {
            let row_end = (row_tile + TILE).min(N);
            let col_end = (col_tile + TILE).min(N);
            for row in row_tile..row_end {
                for col in col_tile..col_end {
                    acc += m[row * N + col] as i64;
                }
            }
            col_tile += TILE;
        }
        row_tile += TILE;
    }
    acc
}
```

Build the release binary and run `perf stat` for each traversal mode:

```bash
cargo build --release

# Column-major: expect high cache-miss rate
sudo perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses \
    ./target/release/cache_bench col 2>&1 | tee perf_col.txt

# Row-major: baseline for comparison
sudo perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses \
    ./target/release/cache_bench row 2>&1 | tee perf_row.txt

# Tiled: should show L1 miss rate comparable to row-major
sudo perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses \
    ./target/release/cache_bench tile 2>&1 | tee perf_tile.txt

# Print a comparison summary
echo "=== Column-major ===" && grep -E "cache-miss|cycles|seconds" perf_col.txt
echo "=== Row-major ===" && grep -E "cache-miss|cycles|seconds" perf_row.txt
echo "=== Tiled ===" && grep -E "cache-miss|cycles|seconds" perf_tile.txt
```

Interpret the `cache-misses / cache-references` ratio as the miss rate. For the column-major case on a 4 MB matrix, you should see a miss rate between 12% and 25% because the access pattern defeats the hardware prefetcher: each new column access is 4096 bytes away from the previous, which is a stride larger than typical prefetch lookahead windows. The row-major and tiled cases should show miss rates below 2%.

### Flame Graph Generation

`perf stat` gives aggregate counters; `cargo-flamegraph` gives you a function-level breakdown of *where* CPU time is actually spent:

```bash
# Generate a flamegraph for the column-major case (the slow path)
sudo cargo flamegraph --release --bin cache_bench -- col
# Output: flamegraph.svg in the current directory
firefox flamegraph.svg

# Generate one for the tiled case to compare hot frames
sudo cargo flamegraph --release --bin cache_bench -- tile
mv flamegraph.svg flamegraph_tile.svg
firefox flamegraph_tile.svg
```

In the column-major flame graph, you will see `sum_column_major` as the dominant frame, and within it the stall cycles manifest as a wide, flat bar proportional to memory latency. In the tiled version the frame is similarly dominant in terms of instructions retired, but narrower in wall time — the stalls are gone because the working set fits in cache. If you do not see expected symbols, confirm that `debug = true` is set in `[profile.bench]` and that `/proc/sys/kernel/perf_event_paranoid` is set to `1` or lower: `echo 1 | sudo tee /proc/sys/kernel/perf_event_paranoid`.

---

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

### Motivation

Mobile applications are aggressively concurrent: the main thread drives UI rendering at 60–120 Hz while background threads handle network I/O, sensor fusion, and audio processing. The bugs that emerge from this concurrency — data races, use-after-free across thread boundaries, forgotten allocations in JNI layers — are non-deterministic and therefore invisible to ordinary unit tests. This exercise uses ThreadSanitizer (TSan) in a deliberately broken Go concurrent map, then uses AddressSanitizer (ASan) and Valgrind Memcheck on a C FFI layer to catch a cross-language use-after-free. These are the exact sanitizer configurations you would use in a mobile CI pipeline.

### Part A: Data Race Detection with Go's Race Detector

Go's built-in race detector is TSan compiled directly into the Go runtime — it instruments every memory read and write to record the last thread that accessed each address, and fires a report the moment two goroutines access the same address without an intervening synchronization event. The detector has near-zero false positive rate because it tracks happens-before relationships through Go's channel and sync primitives.

Create the test harness:

```bash
mkdir -p $HOME/labs/race_lab && cd $HOME/labs/race_lab
go mod init race_lab
```

Write `counter.go` — a deliberately unsafe shared counter that a mobile background processing engine might use to aggregate sensor samples:

```go
// counter.go
package main

import (
	"fmt"
	"sync"
	"time"
)

// UnsafeCounter simulates a shared accumulator written from multiple goroutines
// without synchronization — a realistic pattern when developers mistakenly
// assume that goroutine-local increments will not alias.
type UnsafeCounter struct {
	value int64
}

func (c *UnsafeCounter) Increment(delta int64) {
	// INTENTIONAL RACE: no mutex, no atomic. Two goroutines reading and
	// writing c.value simultaneously produce undefined results.
	c.value += delta
}

func (c *UnsafeCounter) Read() int64 {
	return c.value
}

// SafeCounter is the corrected version using sync/atomic operations.
type SafeCounter struct {
	mu    sync.Mutex
	value int64
}

func (c *SafeCounter) Increment(delta int64) {
	c.mu.Lock()
	c.value += delta
	c.mu.Unlock()
}

func (c *SafeCounter) Read() int64 {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.value
}

// stressUnsafe launches `workers` goroutines each incrementing the counter
// `ops` times. Returns the final (racy) value.
func stressUnsafe(workers, ops int) int64 {
	c := &UnsafeCounter{}
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < ops; j++ {
				c.Increment(1)
			}
		}()
	}
	wg.Wait()
	return c.Read()
}

// stressSafe is the reference-correct version.
func stressSafe(workers, ops int) int64 {
	c := &SafeCounter{}
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < ops; j++ {
				c.Increment(1)
			}
		}()
	}
	wg.Wait()
	return c.Read()
}

func main() {
	const workers = 16
	const ops = 100_000
	expected := int64(workers * ops)

	start := time.Now()
	got := stressUnsafe(workers, ops)
	elapsed := time.Since(start)
	fmt.Printf("unsafe: got=%d expected=%d correct=%v elapsed=%v\n",
		got, expected, got == expected, elapsed)

	start = time.Now()
	got = stressSafe(workers, ops)
	elapsed = time.Since(start)
	fmt.Printf("safe:   got=%d expected=%d correct=%v elapsed=%v\n",
		got, expected, got == expected, elapsed)
}
```

Write `counter_test.go` to exercise both paths under the race detector:

```go
// counter_test.go
package main

import (
	"sync/atomic"
	"testing"
)

func TestUnsafeCounterRace(t *testing.T) {
	// This test WILL trigger a race detector report when run with -race.
	// The final value will often differ from expected, but the race fires
	// well before that — on the first conflicting access.
	const workers = 8
	const ops = 50_000
	got := stressUnsafe(workers, ops)
	expected := int64(workers * ops)
	if got != expected {
		t.Logf("unsafe counter: got %d, expected %d (non-deterministic — race confirmed)", got, expected)
	}
}

func TestSafeCounterNoRace(t *testing.T) {
	const workers = 8
	const ops = 50_000
	got := stressSafe(workers, ops)
	expected := int64(workers * ops)
	if got != expected {
		t.Fatalf("safe counter: got %d, expected %d — this should never happen", got, expected)
	}
}

// BenchmarkUnsafeCounter measures raw throughput of the racy path.
// Run WITHOUT -race to get uncontended throughput.
func BenchmarkUnsafeCounter(b *testing.B) {
	c := &UnsafeCounter{}
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			c.Increment(1)
		}
	})
}

// BenchmarkSafeCounterMutex measures mutex-protected throughput.
func BenchmarkSafeCounterMutex(b *testing.B) {
	c := &SafeCounter{}
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			c.Increment(1)
		}
	})
}

// BenchmarkSafeCounterAtomic provides a reference using sync/atomic directly.
func BenchmarkSafeCounterAtomic(b *testing.B) {
	var v int64
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			atomic.AddInt64(&v, 1)
		}
	})
}
```

Run all three verification modes:

```bash
# 1. Confirm the race fires
go test -race -v -run TestUnsafeCounterRace ./... 2>&1 | tee race_report.txt
cat race_report.txt

# 2. Confirm the safe path is clean
go test -race -v -run TestSafeCounterNoRace ./... 2>&1

# 3. Throughput comparison (no -race flag — sanitizer overhead would dominate)
go test -bench=. -benchmem -benchtime=5s ./... 2>&1 | tee bench_results.txt
```

The race detector report will identify the two goroutines, their stack traces at the point of conflicting access, and the first observed access that the second one raced against. It looks like this:

```
==================
WARNING: DATA RACE
Write at 0x00c0001b4000 by goroutine 8:
  main.(*UnsafeCounter).Increment(...)
      /home/user/labs/race_lab/counter.go:16
  main.stressUnsafe.func1()
      /home/user/labs/race_lab/counter.go:36

Previous write at 0x00c0001b4000 by goroutine 7:
  main.(*UnsafeCounter).Increment(...)
      /home/user/labs/race_lab/counter.go:16
  main.stressUnsafe.func1()
      /home/user/labs/race_lab/counter.go:36
==================
```

The `BenchmarkSafeCounterAtomic` benchmark will typically be 3–6× faster than `BenchmarkSafeCounterMutex` on a multi-core machine because `sync/atomic.AddInt64` compiles to a single `LOCK XADD` instruction that only acquires the cache line's exclusive state, while `sync.Mutex` involves two separate atomic CAS operations plus memory barriers for acquisition and release.

### Part B: Use-After-Free Detection with AddressSanitizer and Valgrind

A common mobile bug pattern is allocating a buffer in a Rust or C library, passing a pointer through JNI to Java, and then freeing the buffer before the Java side has finished reading it — or freeing it twice when the ownership model is unclear. This exercise constructs that exact scenario in C with a deliberately introduced use-after-free, then detects it with both ASan and Valgrind Memcheck.

Create the C source file:

```c
/* uaf_demo.c
 *
 * Simulates a mobile audio buffer pipeline where a decoded PCM buffer
 * is freed prematurely while a callback still holds a reference to it.
 * Compile with and without -fsanitize=address to observe the difference.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define FRAME_SIZE  4096
#define SAMPLE_RATE 48000

typedef struct {
    int16_t *samples;
    size_t   frame_count;
    uint32_t sample_rate;
} AudioBuffer;

/* Allocate a new audio buffer filled with a sawtooth test signal. */
AudioBuffer *audio_buffer_create(size_t frame_count, uint32_t sample_rate) {
    AudioBuffer *buf = (AudioBuffer *)malloc(sizeof(AudioBuffer));
    if (!buf) return NULL;
    buf->samples = (int16_t *)malloc(frame_count * sizeof(int16_t));
    if (!buf->samples) { free(buf); return NULL; }
    buf->frame_count  = frame_count;
    buf->sample_rate  = sample_rate;
    for (size_t i = 0; i < frame_count; i++) {
        buf->samples[i] = (int16_t)((i % 256) * 128 - 16384);
    }
    return buf;
}

/* Free the audio buffer. */
void audio_buffer_free(AudioBuffer *buf) {
    if (!buf) return;
    free(buf->samples);
    free(buf);
}

/* Compute RMS energy of the buffer. This would be called from a background
 * processing thread in a real pipeline. */
double audio_buffer_rms(const AudioBuffer *buf) {
    double sum = 0.0;
    for (size_t i = 0; i < buf->frame_count; i++) {
        double s = (double)buf->samples[i];
        sum += s * s;
    }
    return __builtin_sqrt(sum / (double)buf->frame_count);
}

int main(void) {
    AudioBuffer *buf = audio_buffer_create(FRAME_SIZE, SAMPLE_RATE);
    if (!buf) { fprintf(stderr, "allocation failed\n"); return 1; }

    printf("buffer created: %zu frames at %u Hz\n",
           buf->frame_count, buf->sample_rate);

    /* --- INTENTIONAL BUG: free the buffer before computing RMS --- */
    audio_buffer_free(buf);

    /* Use-after-free: buf->samples was freed, but we read it here.
     * Without sanitizers, this silently reads freed heap memory and
     * returns a garbage value or crashes non-deterministically. */
    double rms = audio_buffer_rms(buf);
    printf("RMS (should not reach here): %.4f\n", rms);

    return 0;
}
```

Compile and run without sanitizers first to observe the silent corruption:

```bash
clang -O1 -o uaf_demo uaf_demo.c -lm
./uaf_demo
# Likely prints a garbage RMS value or crashes — non-deterministic
```

Now compile with AddressSanitizer:

```bash
clang -O1 -fsanitize=address -fno-omit-frame-pointer -g \
    -o uaf_demo_asan uaf_demo.c -lm
./uaf_demo_asan 2>&1 | tee asan_report.txt
cat asan_report.txt
```

The ASan report will identify the exact freed allocation, the stack trace at the point of `free()`, and the stack trace at the point of the use-after-free read:

```
==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x602000000050
READ of size 2 at 0x602000000050 thread T0
    #0 0x... in audio_buffer_rms uaf_demo.c:46
    #1 0x... in main uaf_demo.c:64

0x602000000050 is located 0 bytes inside of 8192-byte region [0x602000000050,0x602000002050)
freed by thread T0 here:
    #0 0x... in free
    #1 0x... in audio_buffer_free uaf_demo.c:34
    #2 0x... in main uaf_demo.c:60

previously allocated by thread T0 here:
    #0 0x... in malloc
    #1 0x... in audio_buffer_create uaf_demo.c:22
    #2 0x... in main uaf_demo.c:54
```

Now run the same binary under Valgrind Memcheck to compare the diagnostic quality. Valgrind operates on uninstrumented binaries, which makes it portable but slower:

```bash
# Recompile without ASan, with debug symbols
clang -O0 -g -fno-omit-frame-pointer -o uaf_demo_dbg uaf_demo.c -lm

valgrind --tool=memcheck \
         --leak-check=full \
         --track-origins=yes \
         --show-reachable=yes \
         --num-callers=20 \
         --error-exitcode=1 \
         ./uaf_demo_dbg 2>&1 | tee valgrind_report.txt
cat valgrind_report.txt
```

Valgrind will report an `Invalid read of size 2` at the same line, with the allocation and deallocation call stacks. Because `--track-origins=yes` is set, it also traces the origin of uninitialized values through the heap rather than just flagging the access point.

The practical difference between ASan and Valgrind in a mobile CI context is speed and integration: ASan runs at roughly 2× overhead and integrates directly into Clang's compilation pipeline, making it suitable for unit test execution on every commit. Valgrind runs at roughly 20–50× overhead but requires no recompilation and can analyze binaries you do not have source for — which matters when debugging third-party SDKs that mobile developers commonly integrate.

### LeakSanitizer in Rust

For Rust code that interfaces with C through FFI, enable LeakSanitizer directly through Cargo. Write a small FFI shim that wraps `audio_buffer_create` and deliberately leaks the returned pointer:

```rust
// src/ffi_leak.rs — to be added to the cache_bench project or a new binary crate

use std::ffi::c_void;

extern "C" {
    // We call malloc directly to simulate a C allocation that Rust forgets to free.
    fn malloc(size: usize) -> *mut c_void;
}

pub fn leak_allocation(size: usize) -> *mut c_void {
    // Allocate via libc malloc — Rust's allocator has no knowledge of this.
    // The resulting pointer is intentionally leaked (never passed to free).
    unsafe { malloc(size) }
}

fn main() {
    let _p = leak_allocation(4096);
    println!("allocated 4096 bytes through libc malloc — intentionally leaked");
    // process exits here without freeing _p
}
```

Run with LeakSanitizer:

```bash
# LeakSanitizer requires nightly and the sanitizer feature gate on Linux
rustup override set nightly

RUSTFLAGS="-Z sanitizer=leak" \
    cargo +nightly run --target x86_64-unknown-linux-gnu 2>&1 | tee lsan_report.txt

cat lsan_report.txt
# Expected output:
# ==PID==ERROR: LeakSanitizer: detected memory leaks
# Direct leak of 4096 byte(s) in 1 object(s) allocated from:
#     #0 ... in malloc
#     #1 ... in mobile_fir::ffi_leak::leak_allocation ...
#     #2 ... in mobile_fir::ffi_leak::main ...
```

Restore stable toolchain after the LSan run:

```bash
rustup override set stable
```

---

## Developer Cheat Sheet & Toolchain Checklist

The following reference consolidates every command introduced in this lab guide into a reproducible verification procedure. In a CI environment, integrate these as separate pipeline stages gated in dependency order: build must pass before analysis runs, unit tests must pass before sanitizer runs, and benchmarks run only on a dedicated performance runner to prevent noise from shared infrastructure.

**Compilation & Static Analysis**

| Task | Command |
|---|---|
| Build native debug | `cargo build` |
| Build native release with DWARF | `cargo build --release` (with `debug = true` in profile) |
| Cross-compile to Android AArch64 | `cargo build --release --target aarch64-linux-android` |
| Emit unoptimized LLVM IR | `RUSTFLAGS="--emit=llvm-ir -C opt-level=0" cargo build` |
| Emit optimized LLVM IR | `RUSTFLAGS="--emit=llvm-ir -C opt-level=3" cargo build --release` |
| Disassemble a symbol | `cargo asm --release <crate>::<fn_path>` |
| Disassemble with source interleave | `cargo asm --release --rust <crate>::<fn_path>` |
| Cross-compiled objdump | `llvm-objdump --arch-name=aarch64 --disassemble --demangle <file>.o` |
| Run Clippy lints | `cargo clippy -- -D warnings` |

**Testing & Sanitizers**

| Task | Command |
|---|---|
| Run unit tests | `cargo test` |
| Run tests with AddressSanitizer | `RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| Run tests with ThreadSanitizer | `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| Run tests with LeakSanitizer | `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly run --target x86_64-unknown-linux-gnu` |
| Go race detector tests | `go test -race ./...` |
| Go race detector benchmark | `go test -race -bench=. ./...` |
| Valgrind Memcheck | `valgrind --tool=memcheck --leak-check=full --track-origins=yes <binary>` |
| Clang ASan binary | `clang -fsanitize=address -fno-omit-frame-pointer -g -O1 <src>.c -o <out>` |

**Performance Profiling**

| Task | Command |
|---|---|
| Criterion benchmark | `cargo bench --bench <name>` |
| Flame graph (Rust binary) | `sudo cargo flamegraph --release --bin <name> -- <args>` |
| `perf stat` cache counters | `sudo perf stat -e cycles,cache-misses,L1-dcache-load-misses <binary>` |
| `perf stat` full event set | `sudo perf stat -e cycles,instructions,cache-references,cache-misses,branch-misses <binary>` |
| Enable perf for non-root | `echo 1 \| sudo tee /proc/sys/kernel/perf_event_paranoid` |
| Go benchmarks | `go test -bench=. -benchmem -benchtime=5s ./...` |
| Go CPU profile | `go test -bench=. -cpuprofile=cpu.prof ./... && go tool pprof cpu.prof` |

**Cross-Target Verification Checklist**

Before releasing a mobile library, run the following checks in order. Each item is a gate: if it fails, fix it before proceeding to the next.

The first check is `cargo check --target aarch64-linux-android` to verify that all types, traits, and feature flags resolve correctly for the Android ABI without spending time on a full code-generation pass. The second check is `cargo clippy --target aarch64-linux-android -- -D warnings`, which catches common mobile-specific issues such as `std::collections::HashMap` usage in a `no_std` context and incorrect ABI annotations on `extern "C"` functions. The third check is `cargo test` on the native host with both AddressSanitizer and ThreadSanitizer enabled in separate passes, since sanitizers run on the host target. The fourth check is a Criterion benchmark run to establish the performance baseline for the release build, with the resulting HTML report committed to a known-good directory for regression comparison. The fifth and final check is a Valgrind Memcheck run on any C FFI layer with `--error-exitcode=1` so that CI fails rather than producing a warning-only report that engineers ignore.

The discipline behind this sequence is that the most common mobile field bugs — silent data corruption, use-after-free across JNI boundaries, data races in audio callbacks — are undetectable at the application layer by the time they ship to devices. They are only detectable at this layer, with these tools, in this order, before the binary is packaged and signed.
