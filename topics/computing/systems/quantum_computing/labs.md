# Operational Verification Labs: Quantum Computing

## Objective & Toolchain Setup

This lab guide bridges quantum computing concepts and classical systems engineering verification. You will implement a quantum circuit simulator in Rust, then subject it to the same rigorous instrumentation you would apply to any high-performance systems component: AST and IR inspection, cache profiling, concurrency sanitization, and memory leak analysis. The simulator encodes quantum states as complex-amplitude vectors, implements gate operations as dense matrix multiplications, and exposes a measurement interface. Every exercise operates on this real, non-trivial codebase.

The domain is well-suited to systems verification work because quantum simulators exhibit the same failure modes as any numerically intensive, potentially concurrent C++/Rust program: poor cache locality from large state vectors, data races when parallelizing gate applications across qubits, and floating-point memory footprint that scales exponentially with qubit count ($2^n$ complex amplitudes for $n$ qubits). These properties make it an ideal stress target.

**Toolchain Installation**

Install `rustup` and the nightly toolchain, since several profiling and sanitizer features require nightly compiler infrastructure:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup toolchain install nightly
rustup component add rust-src llvm-tools-preview --toolchain nightly
rustup default nightly
```

Install system-level diagnostics:

```bash
# Debian/Ubuntu
sudo apt-get install -y clang lldb valgrind linux-perf build-essential pkg-config

# macOS (Homebrew)
brew install llvm valgrind
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
```

Install Cargo toolchain extensions:

```bash
cargo install cargo-flamegraph
cargo install cargo-asm
cargo install cargo-llvm-ir
cargo install criterion --features html_reports
```

**Project Bootstrap**

Create the simulator project that all exercises will use:

```bash
cargo new --lib quantum_sim
cd quantum_sim
```

Replace `Cargo.toml` with the following:

```toml
[package]
name = "quantum_sim"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "simulate"
path = "src/main.rs"

[lib]
name = "quantum_sim"
path = "src/lib.rs"

[dependencies]
num-complex = "0.4"
rand = { version = "0.8", features = ["small_rng"] }
rayon = "1.8"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "gate_bench"
harness = false

[profile.bench]
opt-level = 3
lto = "thin"
codegen-units = 1
debug = true

[profile.release]
opt-level = 3
lto = "thin"
codegen-units = 1
debug = true

[profile.dev]
opt-level = 0
debug = true
```

Create `src/lib.rs` with the full simulator implementation:

```rust
use num_complex::Complex64;
use rand::Rng;
use std::f64::consts::FRAC_1_SQRT_2;

/// A statevector quantum simulator.
/// The state is stored as a flat Vec of 2^n Complex64 amplitudes,
/// indexed by the bitstring representation of the basis state.
/// For n=3, index 0b101 = 5 represents |101⟩.
pub struct QuantumState {
    pub num_qubits: usize,
    pub amplitudes: Vec<Complex64>,
}

impl QuantumState {
    /// Initialize an n-qubit register in the |0...0⟩ computational basis state.
    pub fn new(num_qubits: usize) -> Self {
        let dim = 1 << num_qubits;
        let mut amplitudes = vec![Complex64::new(0.0, 0.0); dim];
        amplitudes[0] = Complex64::new(1.0, 0.0);
        QuantumState { num_qubits, amplitudes }
    }

    /// Apply a single-qubit gate defined by its 2x2 unitary matrix [u00, u01; u10, u11]
    /// to qubit `target`. Iterates over all 2^n amplitude pairs.
    pub fn apply_single_qubit_gate(
        &mut self,
        target: usize,
        u00: Complex64,
        u01: Complex64,
        u10: Complex64,
        u11: Complex64,
    ) {
        let n = self.num_qubits;
        let dim = 1 << n;
        // Stride between the |0⟩ and |1⟩ component of the target qubit
        let half_stride = 1 << target;

        let mut i = 0;
        while i < dim {
            // Within each outer block, iterate over pairs
            let inner_end = i + half_stride;
            let mut j = i;
            while j < inner_end {
                let idx0 = j;
                let idx1 = j + half_stride;
                let a0 = self.amplitudes[idx0];
                let a1 = self.amplitudes[idx1];
                self.amplitudes[idx0] = u00 * a0 + u01 * a1;
                self.amplitudes[idx1] = u10 * a0 + u11 * a1;
                j += 1;
            }
            i += 2 * half_stride;
        }
    }

    /// Apply a controlled-NOT (CNOT) gate: control qubit `ctrl`, target qubit `tgt`.
    pub fn apply_cnot(&mut self, ctrl: usize, tgt: usize) {
        let dim = 1 << self.num_qubits;
        for idx in 0..dim {
            // Only flip target when control qubit is |1⟩
            if (idx >> ctrl) & 1 == 1 {
                let partner = idx ^ (1 << tgt);
                // Only process each pair once
                if idx < partner {
                    self.amplitudes.swap(idx, partner);
                }
            }
        }
    }

    /// Hadamard gate: puts a qubit into equal superposition.
    pub fn hadamard(&mut self, target: usize) {
        let f = Complex64::new(FRAC_1_SQRT_2, 0.0);
        self.apply_single_qubit_gate(target, f, f, f, -f);
    }

    /// Pauli-X gate: bit flip.
    pub fn pauli_x(&mut self, target: usize) {
        let zero = Complex64::new(0.0, 0.0);
        let one = Complex64::new(1.0, 0.0);
        self.apply_single_qubit_gate(target, zero, one, one, zero);
    }

    /// S gate: phase gate rotating by π/2.
    pub fn s_gate(&mut self, target: usize) {
        let one = Complex64::new(1.0, 0.0);
        let zero = Complex64::new(0.0, 0.0);
        let i = Complex64::new(0.0, 1.0);
        self.apply_single_qubit_gate(target, one, zero, zero, i);
    }

    /// T gate: phase gate rotating by π/4.
    pub fn t_gate(&mut self, target: usize) {
        let one = Complex64::new(1.0, 0.0);
        let zero = Complex64::new(0.0, 0.0);
        let t = Complex64::new(FRAC_1_SQRT_2, FRAC_1_SQRT_2);
        self.apply_single_qubit_gate(target, one, zero, zero, t);
    }

    /// Measure all qubits: sample a basis state according to Born rule probabilities.
    /// Returns the measured bitstring as a usize index and collapses the state.
    pub fn measure_all<R: Rng>(&mut self, rng: &mut R) -> usize {
        let probs: Vec<f64> = self.amplitudes.iter()
            .map(|a| a.norm_sqr())
            .collect();
        let r: f64 = rng.gen();
        let mut cumulative = 0.0;
        let mut outcome = probs.len() - 1;
        for (i, p) in probs.iter().enumerate() {
            cumulative += p;
            if r < cumulative {
                outcome = i;
                break;
            }
        }
        // Collapse the state
        let dim = self.amplitudes.len();
        for i in 0..dim {
            self.amplitudes[i] = if i == outcome {
                Complex64::new(1.0, 0.0)
            } else {
                Complex64::new(0.0, 0.0)
            };
        }
        outcome
    }

    /// Compute the total probability mass (must equal 1.0 for a valid state).
    pub fn norm_squared(&self) -> f64 {
        self.amplitudes.iter().map(|a| a.norm_sqr()).sum()
    }
}

/// Build an n-qubit GHZ (Greenberger-Horne-Zeilinger) state:
/// (|00...0⟩ + |11...1⟩) / sqrt(2)
/// This is the canonical maximally entangled state used as a circuit benchmark.
pub fn build_ghz_state(num_qubits: usize) -> QuantumState {
    let mut state = QuantumState::new(num_qubits);
    state.hadamard(0);
    for q in 0..(num_qubits - 1) {
        state.apply_cnot(q, q + 1);
    }
    state
}

/// Quantum Fourier Transform over n qubits.
/// Applies the QFT circuit in-place using Hadamard and controlled phase rotations.
pub fn quantum_fourier_transform(state: &mut QuantumState) {
    let n = state.num_qubits;
    for qubit in (0..n).rev() {
        state.hadamard(qubit);
        for ctrl in (0..qubit).rev() {
            let k = (qubit - ctrl) as u32 + 1;
            let angle = std::f64::consts::PI / (1u64 << k) as f64;
            let phase = Complex64::new(angle.cos(), angle.sin());
            let one = Complex64::new(1.0, 0.0);
            let zero = Complex64::new(0.0, 0.0);
            // Controlled phase rotation: apply phase to |11⟩ component
            apply_controlled_phase(state, ctrl, qubit, one, zero, phase);
        }
    }
    // Bit-reverse permutation
    bit_reverse_permutation(state);
}

fn apply_controlled_phase(
    state: &mut QuantumState,
    ctrl: usize,
    tgt: usize,
    _u00: Complex64,
    _u01: Complex64,
    phase: Complex64,
) {
    let dim = 1 << state.num_qubits;
    for idx in 0..dim {
        if (idx >> ctrl) & 1 == 1 && (idx >> tgt) & 1 == 1 {
            state.amplitudes[idx] *= phase;
        }
    }
}

fn bit_reverse_permutation(state: &mut QuantumState) {
    let n = state.num_qubits;
    let dim = 1 << n;
    for i in 0..dim {
        let j = reverse_bits(i, n);
        if i < j {
            state.amplitudes.swap(i, j);
        }
    }
}

fn reverse_bits(mut x: usize, n: usize) -> usize {
    let mut result = 0;
    for _ in 0..n {
        result = (result << 1) | (x & 1);
        x >>= 1;
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::SeedableRng;
    use rand::rngs::SmallRng;

    #[test]
    fn test_initial_state_is_zero_ket() {
        let state = QuantumState::new(3);
        assert!((state.amplitudes[0].re - 1.0).abs() < 1e-12);
        for i in 1..8 {
            assert!(state.amplitudes[i].norm() < 1e-12);
        }
    }

    #[test]
    fn test_hadamard_preserves_norm() {
        let mut state = QuantumState::new(4);
        state.hadamard(0);
        state.hadamard(1);
        state.hadamard(2);
        let norm = state.norm_squared();
        assert!((norm - 1.0).abs() < 1e-10, "Norm after Hadamards: {}", norm);
    }

    #[test]
    fn test_ghz_state_structure() {
        let state = build_ghz_state(3);
        // GHZ: amplitude at index 0 (|000⟩) and index 7 (|111⟩) should each be 1/sqrt(2)
        let expected = 0.5; // |amplitude|^2
        assert!((state.amplitudes[0].norm_sqr() - expected).abs() < 1e-10);
        assert!((state.amplitudes[7].norm_sqr() - expected).abs() < 1e-10);
        // All other amplitudes must be zero
        for i in 1..7 {
            assert!(state.amplitudes[i].norm() < 1e-10, "Non-zero at index {}", i);
        }
    }

    #[test]
    fn test_pauli_x_flips_qubit() {
        let mut state = QuantumState::new(2);
        state.pauli_x(0);
        // |00⟩ -> |01⟩ (qubit 0 flipped), so index 0b01 = 1 should have amplitude 1
        assert!((state.amplitudes[1].re - 1.0).abs() < 1e-12);
        assert!(state.amplitudes[0].norm() < 1e-12);
    }

    #[test]
    fn test_qft_preserves_norm() {
        let mut state = QuantumState::new(4);
        state.hadamard(0);
        state.hadamard(2);
        quantum_fourier_transform(&mut state);
        let norm = state.norm_squared();
        assert!((norm - 1.0).abs() < 1e-10, "QFT norm: {}", norm);
    }

    #[test]
    fn test_measurement_collapses_to_valid_state() {
        let mut state = build_ghz_state(3);
        let mut rng = SmallRng::seed_from_u64(42);
        let outcome = state.measure_all(&mut rng);
        // Post-measurement, outcome must be either 0 (|000⟩) or 7 (|111⟩)
        assert!(outcome == 0 || outcome == 7, "Unexpected outcome: {}", outcome);
        // Norm must still be 1.0 after collapse
        assert!((state.norm_squared() - 1.0).abs() < 1e-12);
    }
}
```

Create `src/main.rs`:

```rust
use quantum_sim::{QuantumState, build_ghz_state, quantum_fourier_transform};
use rand::SeedableRng;
use rand::rngs::SmallRng;

fn main() {
    println!("=== Quantum Simulator: GHZ State Demo ===");
    let mut state = build_ghz_state(4);
    println!("4-qubit GHZ state norm: {:.12}", state.norm_squared());

    println!("\n=== Quantum Fourier Transform: 8 qubits ===");
    let mut qft_state = QuantumState::new(8);
    for q in 0..8 {
        qft_state.hadamard(q);
    }
    quantum_fourier_transform(&mut qft_state);
    println!("QFT norm after transform: {:.12}", qft_state.norm_squared());

    println!("\n=== Measurement Demo: GHZ 3-qubit ===");
    let mut rng = SmallRng::seed_from_u64(2024);
    for trial in 0..8 {
        let mut s = build_ghz_state(3);
        let outcome = s.measure_all(&mut rng);
        println!("  Trial {}: outcome index {} = |{:03b}⟩", trial, outcome, outcome);
    }
}
```

Create the benchmark file `benches/gate_bench.rs`:

```rust
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use quantum_sim::{QuantumState, build_ghz_state, quantum_fourier_transform};

fn bench_hadamard_all_qubits(c: &mut Criterion) {
    let mut group = c.benchmark_group("hadamard_sweep");
    for num_qubits in [8usize, 10, 12, 14, 16] {
        let dim = 1u64 << num_qubits;
        group.throughput(Throughput::Elements(dim));
        group.bench_with_input(
            BenchmarkId::from_parameter(num_qubits),
            &num_qubits,
            |b, &n| {
                b.iter(|| {
                    let mut state = QuantumState::new(n);
                    for q in 0..n {
                        state.hadamard(q);
                    }
                    state
                });
            },
        );
    }
    group.finish();
}

fn bench_ghz_construction(c: &mut Criterion) {
    let mut group = c.benchmark_group("ghz_construction");
    for num_qubits in [8usize, 10, 12, 14, 16] {
        let dim = 1u64 << num_qubits;
        group.throughput(Throughput::Elements(dim));
        group.bench_with_input(
            BenchmarkId::from_parameter(num_qubits),
            &num_qubits,
            |b, &n| {
                b.iter(|| build_ghz_state(n));
            },
        );
    }
    group.finish();
}

fn bench_qft(c: &mut Criterion) {
    let mut group = c.benchmark_group("quantum_fourier_transform");
    for num_qubits in [8usize, 10, 12, 14] {
        let dim = 1u64 << num_qubits;
        group.throughput(Throughput::Elements(dim));
        group.bench_with_input(
            BenchmarkId::from_parameter(num_qubits),
            &num_qubits,
            |b, &n| {
                b.iter(|| {
                    let mut state = QuantumState::new(n);
                    for q in 0..n { state.hadamard(q); }
                    quantum_fourier_transform(&mut state);
                    state
                });
            },
        );
    }
    group.finish();
}

criterion_group!(benches, bench_hadamard_all_qubits, bench_ghz_construction, bench_qft);
criterion_main!(benches);
```

Verify everything compiles and all tests pass before proceeding to any exercise:

```bash
cargo test
cargo build --release
```

---

## Exercise 1: AST, IR & Disassembly Analysis

The goal of this exercise is to trace the quantum simulator's most critical hot path, `apply_single_qubit_gate`, from Rust source through Rust's High-level Intermediate Representation (HIR), through LLVM IR, and down to native x86-64 machine code. This discipline is not academic: it teaches you exactly what LLVM's optimizer does to your loop structure, whether auto-vectorization fired, and whether the abstraction cost of `num_complex::Complex64` evaporated or survived into the final binary.

**Step 1: Rust MIR and HIR Inspection**

Rust's compiler frontend lowers source code first to HIR (a desugared AST), then to MIR (Mid-level IR), which is where the borrow checker operates and where many lifetime errors become concrete. Use `rustc`'s unstable flag to dump MIR for the library crate:

```bash
RUSTFLAGS="-Zunpretty=mir" cargo +nightly rustc --lib -- 2>&1 | less
```

You will see each function decomposed into basic blocks labeled `bb0`, `bb1`, and so on. Locate `apply_single_qubit_gate` in the output. What you care about here is the loop structure: Rust's MIR exposes the `loop` as a back-edge between basic blocks, and the `Vec` index operations appear as explicit bounds-check branches before each `amplitudes[idx0]` access. Note that bounds checks are present in MIR even when LLVM will later eliminate them through range analysis. The MIR dump makes this cost visible and attributable.

```bash
RUSTFLAGS="-Zunpretty=mir-cfg" cargo +nightly rustc --lib -- 2>&1 | head -200
```

The `-mir-cfg` variant emits a Graphviz DOT representation. Pipe it to `dot` if you have it installed (`sudo apt install graphviz`) to visualize the control flow graph of the gate function:

```bash
RUSTFLAGS="-Zunpretty=mir-cfg" cargo +nightly rustc --lib -- 2>&1 | \
  grep -A 10000 "fn apply_single_qubit_gate" | \
  head -300 > /tmp/gate_cfg.dot
dot -Tpng /tmp/gate_cfg.dot -o /tmp/gate_cfg.png
```

**Step 2: LLVM IR Inspection**

LLVM IR is the most useful layer for understanding what the optimizer actually does to your code. At this layer you can verify whether the `Complex64` struct's multiply-add operations were inlined, whether the loop was unrolled, and whether SIMD vector instructions (`<4 x double>`) were emitted. Dump optimized LLVM IR with:

```bash
RUSTFLAGS="--emit=llvm-ir -C opt-level=3 -C lto=no" \
  cargo +nightly rustc --release --lib
```

This writes `.ll` files to `target/release/deps/`. Locate the one for `quantum_sim`:

```bash
ls target/release/deps/*.ll
# Something like: target/release/deps/quantum_sim-<hash>.ll
```

Open it and search for `apply_single_qubit_gate`:

```bash
grep -n "apply_single_qubit_gate\|fadd\|fmul\|<2 x double>\|<4 x double>" \
  target/release/deps/quantum_sim-*.ll | head -60
```

What to look for: if `<2 x double>` or `<4 x double>` vector types appear inside the loop body, LLVM's auto-vectorizer processed your Complex64 arithmetic into SSE2/AVX operations. If you see only scalar `fadd` and `fmul` instructions, vectorization did not fire. The reason is typically aliasing: LLVM cannot prove that the two amplitude slots `amplitudes[idx0]` and `amplitudes[idx1]` do not alias, particularly when accessed through a mutable Vec slice. You will address this in a later exercise.

Use `cargo-llvm-ir` for a cleaner extraction workflow:

```bash
cargo llvm-ir --release quantum_sim::QuantumState::apply_single_qubit_gate
```

This renders only the function you care about, stripped of unrelated IR noise. Study the loop preamble: LLVM will have emitted a vectorized prologue with a scalar epilogue to handle the residual iterations when the trip count is not a multiple of the vector width.

**Step 3: Native Disassembly with cargo-asm**

Compile the release binary and extract the disassembly of `apply_single_qubit_gate` using `cargo-asm`, which integrates with `rustfilt` to demangle Rust symbols:

```bash
cargo asm --release "quantum_sim::QuantumState::apply_single_qubit_gate"
```

If the output is empty (function was inlined at all call sites), force a non-inline annotation and recheck. First, add `#[inline(never)]` to the function signature in `src/lib.rs`:

```rust
#[inline(never)]
pub fn apply_single_qubit_gate(
    &mut self,
    target: usize,
    u00: Complex64,
    // ... rest of signature unchanged
```

Then re-run:

```bash
cargo asm --release "quantum_sim::QuantumState::apply_single_qubit_gate"
```

What you are examining in the disassembly is the loop kernel. On a modern x86-64 machine you should see something structurally similar to the following (the exact registers vary by LLVM version):

```asm
.LBB3_8:
  vmovupd  ymm0, [rsi + rax*8]        ; load a0 (Complex64 = 2x f64 = 16 bytes)
  vmovupd  ymm1, [rsi + rdx*8]        ; load a1
  vmulpd   ymm2, ymm0, ymm4           ; u00.re * a0.re, u00.im * a0.im (vectorized fmul)
  vmulpd   ymm3, ymm1, ymm6           ; u01.re * a1.re, ...
  vaddpd   ymm2, ymm2, ymm3           ; fused add
  vmovupd  [rsi + rax*8], ymm2        ; store result back to amplitudes[idx0]
  add      rax, 4
  cmp      rax, r9
  jl       .LBB3_8
```

The presence of `vmovupd`, `vmulpd`, and `vaddpd` (256-bit AVX2 variants) confirms SIMD vectorization. If you see only `mulsd`/`addsd` (scalar double), apply the following hint to assist LLVM's alias analysis by routing through a raw slice pointer:

```rust
#[inline(never)]
pub fn apply_single_qubit_gate(
    &mut self,
    target: usize,
    u00: Complex64,
    u01: Complex64,
    u10: Complex64,
    u11: Complex64,
) {
    let n = self.num_qubits;
    let dim = 1 << n;
    let half_stride = 1 << target;
    // Safety: we index idx0 and idx1 within [0, dim), and idx0 != idx1 always
    // because they differ by half_stride which is >= 1.
    let ptr = self.amplitudes.as_mut_ptr();

    let mut i = 0usize;
    while i < dim {
        let inner_end = i + half_stride;
        let mut j = i;
        while j < inner_end {
            let idx0 = j;
            let idx1 = j + half_stride;
            unsafe {
                let a0 = *ptr.add(idx0);
                let a1 = *ptr.add(idx1);
                *ptr.add(idx0) = u00 * a0 + u01 * a1;
                *ptr.add(idx1) = u10 * a0 + u11 * a1;
            }
            j += 1;
        }
        i += 2 * half_stride;
    }
}
```

Rerun `cargo asm` and compare the output. The unsafe raw pointer access removes the Vec bounds-check overhead and gives LLVM clearer aliasing semantics. This is the same pattern used in BLAS implementations and in the `faer` linear algebra crate.

**Step 4: Verifying Correctness After IR Optimization**

After any IR-level change, run the full test suite to confirm behavioral correctness is preserved:

```bash
cargo test -- --nocapture
```

Expected output:

```
running 6 tests
test tests::test_initial_state_is_zero_ket ... ok
test tests::test_hadamard_preserves_norm ... ok
test tests::test_ghz_state_structure ... ok
test tests::test_pauli_x_flips_qubit ... ok
test tests::test_qft_preserves_norm ... ok
test tests::test_measurement_collapses_to_valid_state ... ok

test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

Then use GDB to verify that the production binary's optimized `apply_single_qubit_gate` is actually reached during the main demo, confirming your IR analysis was performed on the right build artifact:

```bash
cargo build --release
rust-gdb target/release/simulate
```

Inside GDB:

```gdb
(gdb) set disassembly-flavor intel
(gdb) break quantum_sim::QuantumState::apply_single_qubit_gate
(gdb) run
(gdb) disassemble
(gdb) info registers ymm0 ymm1 ymm2
(gdb) continue
(gdb) quit
```

The `info registers ymm0` command confirms the AVX YMM registers are live at the breakpoint. If GDB does not show YMM registers, your CPU does not support AVX2; fall back to `xmm` (SSE2) and expect 128-bit vector operations instead.

---

## Exercise 2: Cache Miss & Throughput Profiling

The statevector representation makes cache behavior the dominant performance factor in quantum simulation. For an $n$-qubit system, the amplitude vector occupies $2^n \times 16$ bytes (each `Complex64` is two `f64` values, 16 bytes total). At $n = 20$ qubits that is 16 MB, comfortably exceeding a typical 8 MB L3 cache. The access pattern of `apply_single_qubit_gate` strides through this vector with stride $2 \times \texttt{half\_stride} = 2^{target+1}$, so a gate applied to a high-index qubit accesses memory with exponentially larger strides, causing TLB misses and cache line bouncing. This exercise quantifies that phenomenon precisely.

**Step 1: Flamegraph Profiling**

Build in release mode with debug symbols retained (already configured in `Cargo.toml` via `debug = true` under `[profile.release]`) and produce a flamegraph:

```bash
cargo flamegraph --bin simulate -- 2>&1
```

If this fails with a perf permissions error:

```bash
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid
echo 0  | sudo tee /proc/sys/kernel/kptr_restrict
cargo flamegraph --bin simulate
```

The resulting `flamegraph.svg` opens in any browser. You are looking for two things: the width of `apply_single_qubit_gate` relative to `build_ghz_state` and `quantum_fourier_transform`, and whether `jemalloc` or the system allocator's `mmap` overhead appears as a non-trivial width in the allocation call stack.

**Step 2: `perf stat` for Hardware Counters**

`perf stat` provides hardware performance counter data directly from the CPU PMU (Performance Monitoring Unit). Run it against the release binary to gather cache-miss rates:

```bash
perf stat -e cycles,instructions,cache-references,cache-misses,\
L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses,\
branch-instructions,branch-misses \
./target/release/simulate 2>&1
```

A representative output for a 16-qubit QFT might look like:

```
 Performance counter stats for './target/release/simulate':

     4,821,340,112      cycles
     9,043,721,884      instructions              #    1.88  insn per cycle
        92,445,021      cache-references
        14,221,803      cache-misses              #   15.38 % of all cache refs
       841,340,290      L1-dcache-loads
        48,993,201      L1-dcache-load-misses     #    5.82% of all L1-dcache accesses
        18,331,201      LLC-loads
         9,882,312      LLC-load-misses           #   53.91% of all LL-cache accesses

       1.481233501 seconds time elapsed
```

An LLC miss rate above 30% indicates the working set has exceeded the L3 cache. For the QFT specifically, this is expected and physically unavoidable for large qubit counts: the bit-reversal permutation accesses every amplitude exactly once in a scrambled order that defeats all hardware prefetchers. The Hadamard sweep accesses amplitudes with stride `2 * half_stride` bytes; for `target = 15` on a 16-qubit system, that stride is $2^{16}$ bytes = 64 KB, which exceeds a typical L1 cache (32-64 KB) entirely and stresses L2.

**Step 3: `perf record` and `perf report` for Per-Function Attribution**

```bash
perf record -g --call-graph dwarf ./target/release/simulate
perf report --stdio --no-children | head -50
```

Expected output structure:

```
# Overhead  Command       Shared Object        Symbol
# ........  ............  ...................  ...................................
#
    47.23%  simulate      simulate             quantum_sim::quantum_fourier_transform
    31.11%  simulate      simulate             quantum_sim::QuantumState::apply_single_qubit_gate
    12.44%  simulate      simulate             quantum_sim::build_ghz_state
     5.98%  simulate      simulate             quantum_sim::QuantumState::apply_cnot
     2.21%  simulate      libc.so.6            __memcpy_avx_unaligned
```

The `quantum_fourier_transform` dominating overhead at 47% is correct: QFT applies $O(n^2)$ gate operations versus the GHZ circuit's $O(n)$.

**Step 4: Criterion Microbenchmarks**

Criterion provides statistically rigorous latency distributions, tracking mean, standard deviation, and outlier attribution across multiple measurements. Run the benchmark suite:

```bash
cargo bench 2>&1 | tee /tmp/bench_results.txt
```

Criterion writes HTML reports to `target/criterion/`. Open `target/criterion/hadamard_sweep/report/index.html` in a browser to see the violin plot and regression lines. The terminal output will resemble:

```
hadamard_sweep/8        time:   [4.3122 µs 4.3344 µs 4.3611 µs]
                        thrpt:  [58.699 Melem/s 58.994 Melem/s 59.302 Melem/s]
hadamard_sweep/10       time:   [19.221 µs 19.388 µs 19.564 µs]
                        thrpt:  [52.284 Melem/s 52.763 Melem/s 53.231 Melem/s]
hadamard_sweep/12       time:   [84.312 µs 84.892 µs 85.491 µs]
                        thrpt:  [47.879 Melem/s 48.207 Melem/s 48.537 Melem/s]
hadamard_sweep/14       time:   [511.33 µs 514.02 µs 517.01 µs]
                        thrpt:  [31.701 Melem/s 31.886 Melem/s 32.053 Melem/s]
hadamard_sweep/16       time:   [3.8821 ms 3.9103 ms 3.9419 ms]
                        thrpt:  [16.615 Melem/s 16.750 Melem/s 16.870 Melem/s]
```

Notice the throughput drop from roughly 59 Melem/s at $n=8$ to 16 Melem/s at $n=16$. The state vector at $n=8$ is $256 \times 16 = 4$ KB, well inside L1. At $n=16$ it is $65536 \times 16 = 1$ MB, exceeding L2 for most microarchitectures. This throughput cliff is the cache effect measured directly. The relationship is causal, not coincidental: once you lose L2 residency, you are bound by L3 or DRAM bandwidth rather than compute throughput.

**Step 5: Memory Footprint Analysis with Valgrind Massif**

Massif is Valgrind's heap profiler, tracking peak allocation and temporal allocation patterns:

```bash
valgrind --tool=massif --pages-as-heap=yes \
  --massif-out-file=/tmp/massif.out \
  ./target/release/simulate

ms_print /tmp/massif.out | head -80
```

The `--pages-as-heap=yes` flag includes mmap allocations (which is how large Vecs get their backing memory on Linux), giving the true resident set size rather than just malloc-tracked heap. For a 16-qubit QFT you should see peak allocation near $1$ MB for the state vector alone. The snapshot timeline will show a sawtooth pattern corresponding to `QuantumState::new` calls within each benchmark iteration, confirming that GHZ and QFT construction each allocate and free the full state vector.

---

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Quantum simulators are natural parallelism candidates: when a gate operates on qubit $k$, it only touches amplitude pairs that differ in bit $k$. Gates on disjoint qubits are therefore independent and can be applied concurrently. This exercise adds a parallel gate sweep using Rayon and then uses ThreadSanitizer to verify that no data races exist in the concurrent implementation.

**Step 1: Parallel Gate Implementation**

Add the following parallel Hadamard sweep function to `src/lib.rs`:

```rust
use rayon::prelude::*;

/// Apply Hadamard gates to all qubits in parallel using Rayon.
/// Each qubit's gate touches non-overlapping index pairs (they differ in bit `target`),
/// so qubits at different indices can be processed concurrently with no data races.
/// However, gates on the SAME qubit applied concurrently would race.
/// This function applies each qubit's Hadamard sequentially over qubits
/// but parallelizes the inner amplitude-pair loop for each qubit.
pub fn parallel_hadamard_all(state: &mut QuantumState) {
    let n = state.num_qubits;
    let f = num_complex::Complex64::new(FRAC_1_SQRT_2, 0.0);

    for target in 0..n {
        let dim = 1 << n;
        let half_stride = 1 << target;

        // Collect the disjoint pairs of (idx0, idx1) indices for this gate
        let pairs: Vec<(usize, usize)> = (0..dim)
            .step_by(2 * half_stride)
            .flat_map(|i| (i..(i + half_stride)).map(move |j| (j, j + half_stride)))
            .collect();

        // Apply gate in parallel across pairs; each pair modifies a unique pair of indices
        pairs.par_iter().for_each(|&(idx0, idx1)| {
            // Safety: idx0 != idx1 always (differ by half_stride >= 1),
            // and all pairs in the flat_map are disjoint, so no two par_iter
            // threads access the same index. We need raw pointers to split the
            // borrow so Rayon can dispatch work across threads.
            let ptr = state.amplitudes.as_ptr() as *mut num_complex::Complex64;
            unsafe {
                let a0 = *ptr.add(idx0);
                let a1 = *ptr.add(idx1);
                *ptr.add(idx0) = f * a0 + f * a1;
                *ptr.add(idx1) = f * a0 - f * a1;
            }
        });
    }
}

/// Intentionally racy parallel gate: applies Hadamard to ALL qubits simultaneously
/// without coordination, introducing data races. Used to demonstrate ThreadSanitizer.
/// DO NOT USE IN PRODUCTION.
pub fn racy_parallel_hadamard_all(state: &mut QuantumState) {
    let n = state.num_qubits;
    let f = num_complex::Complex64::new(FRAC_1_SQRT_2, 0.0);
    let dim = 1 << n;

    // This parallelizes over ALL amplitude indices simultaneously across all qubits,
    // producing overlapping (idx0, idx1) pairs from different qubits that share indices.
    (0..dim).into_par_iter().for_each(|idx| {
        let ptr = state.amplitudes.as_ptr() as *mut num_complex::Complex64;
        for target in 0..n {
            let half_stride = 1 << target;
            let partner = idx ^ half_stride;
            unsafe {
                let a_self = *ptr.add(idx);
                let a_partner = *ptr.add(partner);
                // RACE: another thread may simultaneously write ptr.add(idx) or ptr.add(partner)
                *ptr.add(idx) = f * a_self + f * a_partner;
            }
        }
    });
}
```

Add a test for the parallel implementation in the `#[cfg(test)]` block:

```rust
#[test]
fn test_parallel_hadamard_preserves_norm() {
    let mut state = QuantumState::new(6);
    parallel_hadamard_all(&mut state);
    let norm = state.norm_squared();
    assert!((norm - 1.0).abs() < 1e-10, "Parallel Hadamard norm: {}", norm);
}
```

```bash
cargo test test_parallel_hadamard_preserves_norm -- --nocapture
```

**Step 2: ThreadSanitizer (TSan) on the Racy Implementation**

ThreadSanitizer is built into the Rust nightly toolchain via the `-Zsanitizer=thread` flag. It instruments every memory load and store, tracks happens-before relationships, and reports races at runtime. Build and run with TSan enabled:

```bash
RUSTFLAGS="-Zsanitizer=thread" \
  cargo +nightly test --target x86_64-unknown-linux-gnu \
  -- --nocapture 2>&1 | tee /tmp/tsan_output.txt
```

To specifically exercise the racy function, add a test that calls it:

```rust
#[test]
fn test_racy_hadamard_for_tsan_detection() {
    let mut state = QuantumState::new(4);
    racy_parallel_hadamard_all(&mut state);
    // We do not assert correctness here because the result is non-deterministic.
    // The only point of this test is to let TSan observe the race.
    let _ = state.norm_squared();
}
```

```bash
RUSTFLAGS="-Zsanitizer=thread" \
  cargo +nightly test --target x86_64-unknown-linux-gnu \
  test_racy_hadamard_for_tsan_detection -- --nocapture 2>&1
```

TSan will produce output structured like this:

```
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7f3a2b4c1080 by thread T3:
    #0 quantum_sim::racy_parallel_hadamard_all::{{closure}}
           src/lib.rs:198:17
    #1 rayon::iter::par_iter::...
    ...

  Previous write of size 8 at 0x7f3a2b4c1080 by thread T1:
    #0 quantum_sim::racy_parallel_hadamard_all::{{closure}}
           src/lib.rs:198:17
    ...

SUMMARY: ThreadSanitizer: data race src/lib.rs:198:17
==================
```

The report identifies the exact source line (`198:17` in the closure), the memory address involved, and both the writing thread and the previously-writing thread. This is precisely the kind of information a systems programmer needs to diagnose a race: not just "there is a race" but "thread T3 wrote address X, and thread T1 wrote address X four nanoseconds earlier with no synchronization in between."

Confirm that the correct `parallel_hadamard_all` function (which has disjoint pair access) produces no TSan reports:

```bash
RUSTFLAGS="-Zsanitizer=thread" \
  cargo +nightly test --target x86_64-unknown-linux-gnu \
  test_parallel_hadamard_preserves_norm -- --nocapture 2>&1
```

Expected output: clean test pass with no TSan warnings. This demonstrates the correctness of the partition: disjoint index pairs accessed by independent Rayon tasks constitute a data-race-free parallel program, even without mutexes, because the happens-before graph has no conflicting accesses on the same address.

**Step 3: AddressSanitizer (ASan) for Bounds and Heap Safety**

ASan instruments pointer accesses and detects stack overflows, heap buffer overreads, use-after-free, and use-after-return. The unsafe raw pointer access in `apply_single_qubit_gate` is exactly the kind of code ASan is designed to validate.

Add a deliberately out-of-bounds test to verify ASan catches it:

```rust
#[cfg(test)]
mod asan_tests {
    use super::*;

    #[test]
    #[should_panic]
    fn test_out_of_bounds_gate_panics_in_debug() {
        // In debug mode, Vec indexing panics on out-of-bounds.
        // In release with unsafe ptr, this would be UB that ASan catches.
        let mut state = QuantumState::new(2);
        // Applying a gate to qubit 5 on a 2-qubit system: half_stride = 32,
        // but dim = 4. The inner loop runs from 0..32 accessing indices 0+32=32,
        // which is out of the 4-element Vec. In safe Rust this panics.
        state.hadamard(5);
    }
}
```

Build and run with ASan:

```bash
RUSTFLAGS="-Zsanitizer=address" \
  cargo +nightly test --target x86_64-unknown-linux-gnu \
  -- --nocapture 2>&1 | tee /tmp/asan_output.txt
```

For the in-bounds tests, ASan produces no errors. For any test that exercises the unsafe pointer path with an out-of-bounds target qubit index, ASan reports:

```
=================================================================
==12346==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...
READ of size 16 at 0x... thread T0
    #0 0x... in quantum_sim::QuantumState::apply_single_qubit_gate
       src/lib.rs:52:28
    #1 0x... in quantum_sim::QuantumState::hadamard
       src/lib.rs:88:9
    ...
SUMMARY: AddressSanitizer: heap-buffer-overflow src/lib.rs:52:28
Shadow bytes around the buggy address:
  0x...: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x...: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
=>0x...[fd]fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
```

The shadow byte legend `fd` indicates a heap redzone, confirming the access is past the end of the allocated Vec. The source attribution to `src/lib.rs:52` pins the fault to the exact line of the unsafe pointer dereference.

**Step 4: LeakSanitizer (LSan) Diagnostics**

LSan tracks heap allocations that are never freed. While Rust's ownership model prevents most leaks, they can still occur through `Box::leak`, reference cycles with `Rc`, or FFI ownership transfers. Add an intentional leak to demonstrate LSan's detection:

```rust
/// Leaks a QuantumState allocation to demonstrate LSan detection.
/// Returns a raw pointer that is never freed.
#[allow(dead_code)]
pub fn intentionally_leaked_state(n: usize) -> *const QuantumState {
    let state = Box::new(QuantumState::new(n));
    Box::into_raw(state)
}
```

Add a test that calls it:

```rust
#[test]
fn test_lsan_detects_leak() {
    let _ptr = intentionally_leaked_state(10);
    // The Box was converted to a raw pointer and never reconstituted.
    // LSan will report this as a leak at process exit.
}
```

Run with LSan (which is a subset of ASan on Linux):

```bash
RUSTFLAGS="-Zsanitizer=leak" \
  cargo +nightly test --target x86_64-unknown-linux-gnu \
  test_lsan_detects_leak -- --nocapture 2>&1
```

LSan output:

```
=================================================================
==12347==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 131088 bytes in 1 object(s) allocated from:
    #0 0x... in __rust_alloc
    #1 0x... in alloc::alloc::alloc_impl
    #2 0x... in quantum_sim::QuantumState::new
           src/lib.rs:28:34
    #3 0x... in quantum_sim::intentionally_leaked_state
           src/lib.rs:220:22
    #4 0x... in quantum_sim::asan_tests::test_lsan_detects_leak
           src/lib.rs:233:18

SUMMARY: LeakSanitizer: 131088 byte(s) leaked in 1 allocation(s).
```

The 131,088-byte figure is $2^{10} \times 16 = 16,384$ bytes for the amplitude vector of a 10-qubit state plus the `QuantumState` struct overhead and allocator alignment padding. The allocation chain trace walks from the LSan instrumented allocator all the way back to `QuantumState::new`, giving you everything needed to locate and fix the leak: replace `intentionally_leaked_state` with a function that returns `Box<QuantumState>` and relies on Rust's drop semantics.

**Step 5: Combined Sanitizer Run for Full Coverage**

Run the complete test suite under ASan with leak detection enabled to verify no latent issues exist in the production path:

```bash
RUSTFLAGS="-Zsanitizer=address" \
  LSAN_OPTIONS="detect_leaks=1" \
  cargo +nightly test --target x86_64-unknown-linux-gnu \
  -- --nocapture 2>&1
```

A clean run produces:

```
running 8 tests
test tests::test_initial_state_is_zero_ket ... ok
test tests::test_hadamard_preserves_norm ... ok
test tests::test_ghz_state_structure ... ok
test tests::test_pauli_x_flips_qubit ... ok
test tests::test_qft_preserves_norm ... ok
test tests::test_measurement_collapses_to_valid_state ... ok
test tests::test_parallel_hadamard_preserves_norm ... ok
test asan_tests::test_out_of_bounds_gate_panics_in_debug ... ok

test result: ok. 8 passed; 0 failed; 0 ignored
```

No ASan or LSan diagnostics after `test result` means the production code paths are clean.

---

## Developer Cheat Sheet & Toolchain Checklist

**Environment Verification**

| Command | Expected Output |
|---|---|
| `rustup show` | Active toolchain: nightly |
| `rustc --version` | `rustc 1.78.0-nightly` or later |
| `cargo --version` | `cargo 1.78.0-nightly` or later |
| `clang --version` | `clang version 14.0` or later |
| `lldb --version` | `lldb-14` or later |
| `valgrind --version` | `valgrind-3.19` or later |
| `perf --version` | `perf version 6.x` or later |
| `cargo asm --version` | `cargo-asm 0.1.x` |
| `cargo flamegraph --version` | `cargo-flamegraph 0.6.x` |

**Cargo Verification Commands**

| Command | Purpose |
|---|---|
| `cargo check` | Type-check without producing artifacts (fastest feedback loop) |
| `cargo test` | Run all unit and integration tests in debug mode |
| `cargo test --release` | Run tests with optimizations (catches release-mode UB) |
| `cargo bench` | Run Criterion benchmarks and emit HTML reports |
| `cargo build --release` | Full optimized build (LTO, codegen-units=1) |
| `cargo clean` | Wipe all build artifacts and start from scratch |

**MIR / IR / Assembly Inspection**

| Command | Purpose |
|---|---|
| `RUSTFLAGS="-Zunpretty=mir" cargo +nightly rustc --lib` | Dump Mid-level IR for all functions |
| `RUSTFLAGS="--emit=llvm-ir -C opt-level=3" cargo +nightly rustc --release --lib` | Write optimized LLVM IR `.ll` files to `target/release/deps/` |
| `cargo llvm-ir --release quantum_sim::QuantumState::apply_single_qubit_gate` | Extract LLVM IR for one function |
| `cargo asm --release "quantum_sim::QuantumState::apply_single_qubit_gate"` | Disassemble one function in Intel syntax |

**Sanitizer Invocations**

| Sanitizer | Invocation |
|---|---|
| AddressSanitizer | `RUSTFLAGS="-Zsanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| ThreadSanitizer | `RUSTFLAGS="-Zsanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| LeakSanitizer | `RUSTFLAGS="-Zsanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| MemorySanitizer | `RUSTFLAGS="-Zsanitizer=memory" cargo +nightly test --target x86_64-unknown-linux-gnu` |
| All (ASan + LSan) | `RUSTFLAGS="-Zsanitizer=address" LSAN_OPTIONS="detect_leaks=1" cargo +nightly test --target x86_64-unknown-linux-gnu` |

**Profiling Commands**

| Command | Purpose |
|---|---|
| `cargo flamegraph --bin simulate` | CPU flamegraph SVG via Linux perf |
| `perf stat -e cycles,instructions,cache-misses,LLC-load-misses ./target/release/simulate` | Hardware counter summary |
| `perf record -g --call-graph dwarf ./target/release/simulate && perf report` | Per-symbol CPU time attribution |
| `valgrind --tool=massif --pages-as-heap=yes ./target/release/simulate && ms_print massif.out` | Heap and mmap allocation timeline |
| `valgrind --tool=callgrind ./target/release/simulate && callgrind_annotate callgrind.out.*` | Instruction-level cache simulation |

**GDB/LLDB Quick Reference**

| Command | Context |
|---|---|
| `rust-gdb target/release/simulate` | Launch GDB with Rust pretty-printers |
| `(gdb) set disassembly-flavor intel` | Use Intel syntax for disassembly |
| `(gdb) break quantum_sim::QuantumState::apply_single_qubit_gate` | Breakpoint on demangled Rust symbol |
| `(gdb) info registers ymm0 ymm1` | Inspect AVX2 YMM registers |
| `(gdb) x/16gf $rsi` | Examine 16 doubles starting at address in RSI |
| `(lldb) b quantum_sim::QuantumState::hadamard` | LLDB breakpoint on Rust symbol |
| `(lldb) register read ymm0` | Read YMM register in LLDB |
| `(lldb) memory read --size 8 --format f --count 16 0x...` | Read f64 values from address |

**Key Physical Thresholds to Remember**

For the statevector $2^n \times 16$ bytes, the cache residency transitions are as follows. At $n \leq 11$ (32 KB) the full state fits in a 32 KB L1-D cache. At $n \leq 13$ (128 KB) it fits in a typical 256 KB L2. At $n \leq 19$ (8 MB) it fits in a typical 8 MB L3. Beyond $n = 20$ (16 MB) each gate application is DRAM-bound, and throughput drops to memory bandwidth rather than compute rate. These thresholds explain every performance inflection point visible in the Criterion benchmark output and in `perf stat` LLC miss rates.
