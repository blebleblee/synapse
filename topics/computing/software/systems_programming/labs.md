# Operational Verification Labs: Systems Programming

## Objective & Toolchain Setup

Systems programming demands rigorous verification at every layer of the compilation and execution pipeline. Where application development tolerates abstractions, systems work operates directly against hardware constraints: cache line alignment, branch predictor behavior, memory ordering semantics, and the physical cost of atomic operations measured in CPU cycles. This laboratory guide establishes a repeatable verification methodology using production-grade toolchains—Rust's Cargo ecosystem, LLVM's optimization passes, GDB and LLDB debuggers, Valgrind's memory error detectors, and Google's suite of sanitizers—to expose the gap between source-level intent and machine-level reality.

The exercises proceed from static analysis of compiler intermediate representations through dynamic profiling of cache behavior and culminate in stress testing concurrent data structures under sanitizer instrumentation. Each lab builds muscle memory for the diagnostic loop that defines professional systems work: hypothesize about performance or correctness, instrument the system to capture ground truth, interpret the data against hardware architecture, and iterate. By the end of this sequence, you will have internalized the workflow of reading LLVM IR to verify optimization decisions, using `perf` to attribute cache misses to specific data structures, and employing ThreadSanitizer to detect data races that manifest only under high concurrency.

Begin by establishing the complete toolchain. Install Rust via `rustup`, which provides `cargo`, `rustc`, and `rustfmt`. Ensure you have the nightly toolchain available for certain sanitizer features and unstable compiler flags. Install LLVM's toolchain including `clang`, `lldb`, and `llvm-objdump`. On Linux, install Valgrind via your package manager. For flamegraph generation, add `cargo-flamegraph` through Cargo. Verify your installation by running `rustc --version`, `clang --version`, `valgrind --version`, and `cargo install cargo-flamegraph`. On macOS, ensure Xcode Command Line Tools are installed for system debugging symbols. On Linux, install `linux-tools-common` and `linux-tools-generic` to access `perf`. The following commands establish the baseline environment:

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup install nightly
rustup component add rust-src --toolchain nightly

# Install LLVM and debugging tools (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y clang lldb llvm valgrind linux-tools-common linux-tools-generic
sudo sysctl -w kernel.perf_event_paranoid=1  # Allow perf without root

# Install Cargo extensions
cargo install cargo-flamegraph cargo-expand

# Verify installation
rustc --version
clang --version
valgrind --version
perf --version
```

Create a workspace directory for the exercises and initialize a Rust project that will serve as the laboratory environment. This project will contain multiple binaries, each corresponding to one exercise, along with shared library code demonstrating specific systems programming patterns.

```bash
mkdir systems-verification-lab
cd systems-verification-lab
cargo init --name systems_lab
```

Configure the project's `Cargo.toml` to enable multiple binary targets and set optimization profiles that expose compiler behavior. The release profile should enable link-time optimization and specific code generation parameters that affect cache alignment and inlining decisions.

```toml
[package]
name = "systems_lab"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "ast_analysis"
path = "src/bin/ast_analysis.rs"

[[bin]]
name = "cache_profile"
path = "src/bin/cache_profile.rs"

[[bin]]
name = "race_stress"
path = "src/bin/race_stress.rs"

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
debug = true
strip = false

[profile.bench]
inherits = "release"

[dependencies]
crossbeam = "0.8"
parking_lot = "0.12"

[dev-dependencies]
criterion = "0.5"
```

This configuration enables full link-time optimization in release builds while preserving debug symbols, allowing you to correlate performance measurements back to source code. The `codegen-units = 1` setting forces single-threaded compilation, maximizing intra-crate optimization at the cost of build time. The external dependencies provide battle-tested concurrent data structures (`crossbeam`) and high-performance synchronization primitives (`parking_lot`) that we will benchmark against naive implementations.

## Exercise 1: AST, IR & Disassembly Analysis

The first verification exercise establishes the habit of reading compiler output at three levels of abstraction: the abstract syntax tree (AST) as understood by the parser, the LLVM intermediate representation (IR) as seen by the optimizer, and the final machine code emitted by the code generator. This multi-level inspection reveals what the compiler actually does with your source code, exposing cases where high-level abstractions disappear through inlining, where bounds checks remain despite iterator guarantees, and where memory barriers appear in atomic operations.

Create the first binary target that implements a simple vector summation in multiple styles: a naive loop with indexing, an iterator-based fold, and an unsafe pointer-based implementation. The goal is not to advocate for unsafe code but to understand exactly how Rust's safe abstractions compile and when the optimizer can eliminate their overhead.

```rust
// src/bin/ast_analysis.rs

fn sum_indexed(data: &[i64]) -> i64 {
    let mut total = 0i64;
    for i in 0..data.len() {
        total += data[i];
    }
    total
}

fn sum_iterator(data: &[i64]) -> i64 {
    data.iter().fold(0i64, |acc, &x| acc + x)
}

fn sum_unsafe(data: &[i64]) -> i64 {
    let mut total = 0i64;
    let ptr = data.as_ptr();
    let len = data.len();
    unsafe {
        for i in 0..len {
            total += *ptr.add(i);
        }
    }
    total
}

fn sum_vectorized(data: &[i64]) -> i64 {
    data.chunks_exact(4)
        .fold([0i64; 4], |mut acc, chunk| {
            acc[0] += chunk[0];
            acc[1] += chunk[1];
            acc[2] += chunk[2];
            acc[3] += chunk[3];
            acc
        })
        .iter()
        .sum::<i64>()
        + data.chunks_exact(4).remainder().iter().sum::<i64>()
}

fn main() {
    let data: Vec<i64> = (0..1000).collect();
    
    println!("Indexed sum: {}", sum_indexed(&data));
    println!("Iterator sum: {}", sum_iterator(&data));
    println!("Unsafe sum: {}", sum_unsafe(&data));
    println!("Vectorized sum: {}", sum_vectorized(&data));
    
    std::hint::black_box(sum_indexed(&data));
    std::hint::black_box(sum_iterator(&data));
    std::hint::black_box(sum_unsafe(&data));
    std::hint::black_box(sum_vectorized(&data));
}
```

The implementations are functionally identical but provide different optimization surfaces. The indexed version forces bounds checking on every iteration unless the optimizer can prove the index is in range. The iterator version exposes higher-level intent through the `fold` combinator, potentially enabling better optimization. The unsafe version explicitly bypasses bounds checks, serving as a performance baseline. The vectorized version manually unrolls the loop by processing four elements per iteration, exposing instruction-level parallelism.

Begin by examining the AST. Rust's `cargo-expand` tool runs the macro expander and pretty-prints the desugared source code, showing exactly what code the compiler sees after macro expansion and name resolution. This step reveals trait method resolutions, closure desugaring, and iterator adapter chains.

```bash
cargo expand --bin ast_analysis > ast_output.txt
```

Open `ast_output.txt` and locate the four functions. Observe how `sum_iterator` expands into calls to `core::iter::Iterator::fold`, how the closure becomes a concrete function, and how generic parameters are monomorphized to specific types. The desugared code makes explicit what was implicit in the source: every iterator method is a zero-cost abstraction that compiles to the same code as hand-written loops, provided the optimizer can see through the indirection.

Next, emit LLVM IR to see the code after parsing and type checking but before optimization. The `--emit=llvm-ir` flag produces a `.ll` file containing the unoptimized intermediate representation.

```bash
rustc --emit=llvm-ir src/bin/ast_analysis.rs --crate-type bin -C opt-level=0 -o ast_unopt.ll
```

The unoptimized IR is verbose, preserving all bounds checks, allocations, and function calls. Search for the `@_ZN12ast_analysis11sum_indexed` function (name mangling varies) and examine the basic block structure. You will see explicit bounds checking via `core::panicking::panic_bounds_check`, index calculation, array access via `getelementptr`, and the accumulation into a local stack slot. This IR represents the literal translation of source code into LLVM's strongly-typed assembly, before any optimization passes run.

Now compile with full optimization and emit IR again to see what the optimizer does:

```bash
rustc --emit=llvm-ir src/bin/ast_analysis.rs --crate-type bin -C opt-level=3 -C lto=fat -o ast_opt.ll
```

The optimized IR is dramatically shorter. The loop likely transforms into a tight vectorized sequence using SIMD intrinsics (`llvm.vector.reduce.add`), bounds checks disappear through scalar evolution analysis proving the index is always in range, and the iterator-based version compiles to identical code as the indexed version. Locate the functions again and compare their basic block structure. In many cases, the four implementations collapse into a single optimized sequence, proving that Rust's abstractions carry zero runtime cost when the optimizer has sufficient context.

To verify the final machine code, disassemble the compiled binary using `llvm-objdump` or `objdump`. First, build the binary in release mode with debug symbols:

```bash
cargo build --release --bin ast_analysis
llvm-objdump -d --demangle target/release/ast_analysis > ast_disasm.txt
```

Open `ast_disasm.txt` and search for `ast_analysis::sum_indexed`. The assembly reveals the actual CPU instructions: vectorized operations using SSE or AVX instructions (`vpaddd`, `vpaddq`), register allocation decisions, loop unrolling, and memory access patterns. Cross-reference the assembly with the LLVM IR to understand how high-level operations map to machine instructions. Note especially whether the compiler used scalar or vector operations, how it handled the loop counter, and whether it eliminated redundant loads.

For deeper analysis, use LLDB to inspect the binary at runtime and verify register contents. Set a breakpoint at the start of `sum_indexed`, step through the loop, and examine how data flows through registers.

```bash
lldb target/release/ast_analysis
(lldb) b ast_analysis::sum_indexed
(lldb) run
(lldb) register read
(lldb) disassemble
(lldb) step
(lldb) register read rax rcx rdx
```

Step through several iterations and observe the accumulator register updating, the index incrementing, and memory being accessed. The debugger provides ground truth about what code actually executes, resolving any ambiguity in the static IR or assembly listings.

This exercise establishes the fundamental verification pattern: write code with a hypothesis about how it should compile, emit IR to verify the optimizer's decisions, disassemble to confirm the final machine code, and debug to observe runtime behavior. Apply this pattern whenever performance-critical code behaves unexpectedly or when abstractions might impose overhead.

## Exercise 2: Cache Miss & Throughput Profiling

Cache behavior dominates performance in modern systems. DRAM access latency is two orders of magnitude higher than L1 cache latency, and the difference compounds under parallel workloads where cache line contention serializes memory operations. This exercise instruments a hash table implementation to measure cache misses, quantify false sharing, and optimize data layout for cache line alignment.

Create a second binary that implements a concurrent hash table with thread-local buckets. The first version uses a naive layout with bucket metadata interleaved with data, causing false sharing when multiple threads access adjacent buckets. The optimized version aligns each bucket to a cache line boundary and separates hot metadata from cold data.

```rust
// src/bin/cache_profile.rs

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use parking_lot::Mutex;

const CACHE_LINE: usize = 64;
const NUM_BUCKETS: usize = 256;
const OPERATIONS_PER_THREAD: usize = 100_000;

#[derive(Debug)]
struct NaiveBucket {
    lock: Mutex<()>,
    count: AtomicUsize,
    data: Vec<(u64, u64)>,
}

#[repr(align(64))]
#[derive(Debug)]
struct AlignedBucket {
    count: AtomicUsize,
    _pad1: [u8; 56],
    lock: Mutex<()>,
    _pad2: [u8; 63],
    data: Vec<(u64, u64)>,
}

struct NaiveHashTable {
    buckets: Vec<NaiveBucket>,
}

struct AlignedHashTable {
    buckets: Vec<AlignedBucket>,
}

impl NaiveHashTable {
    fn new() -> Self {
        let buckets = (0..NUM_BUCKETS)
            .map(|_| NaiveBucket {
                lock: Mutex::new(()),
                count: AtomicUsize::new(0),
                data: Vec::new(),
            })
            .collect();
        Self { buckets }
    }

    fn insert(&self, key: u64, value: u64) {
        let bucket_idx = (key % NUM_BUCKETS as u64) as usize;
        let bucket = &self.buckets[bucket_idx];
        let _guard = bucket.lock.lock();
        bucket.count.fetch_add(1, Ordering::Relaxed);
        // Simulate work without actual storage for profiling focus
    }
}

impl AlignedHashTable {
    fn new() -> Self {
        let buckets = (0..NUM_BUCKETS)
            .map(|_| AlignedBucket {
                count: AtomicUsize::new(0),
                _pad1: [0u8; 56],
                lock: Mutex::new(()),
                _pad2: [0u8; 63],
                data: Vec::new(),
            })
            .collect();
        Self { buckets }
    }

    fn insert(&self, key: u64, value: u64) {
        let bucket_idx = (key % NUM_BUCKETS as u64) as usize;
        let bucket = &self.buckets[bucket_idx];
        let _guard = bucket.lock.lock();
        bucket.count.fetch_add(1, Ordering::Relaxed);
    }
}

fn benchmark_naive(table: Arc<NaiveHashTable>, thread_id: usize) {
    let start = thread_id as u64 * OPERATIONS_PER_THREAD as u64;
    for i in 0..OPERATIONS_PER_THREAD {
        table.insert(start + i as u64, thread_id as u64);
    }
}

fn benchmark_aligned(table: Arc<AlignedHashTable>, thread_id: usize) {
    let start = thread_id as u64 * OPERATIONS_PER_THREAD as u64;
    for i in 0..OPERATIONS_PER_THREAD {
        table.insert(start + i as u64, thread_id as u64);
    }
}

fn main() {
    let num_threads = 8;

    println!("=== Naive Hash Table (False Sharing) ===");
    let naive_table = Arc::new(NaiveHashTable::new());
    let start = std::time::Instant::now();
    let handles: Vec<_> = (0..num_threads)
        .map(|tid| {
            let table = Arc::clone(&naive_table);
            thread::spawn(move || benchmark_naive(table, tid))
        })
        .collect();
    for h in handles {
        h.join().unwrap();
    }
    let naive_duration = start.elapsed();
    println!("Naive time: {:?}", naive_duration);

    println!("\n=== Aligned Hash Table (Cache Line Optimized) ===");
    let aligned_table = Arc::new(AlignedHashTable::new());
    let start = std::time::Instant::now();
    let handles: Vec<_> = (0..num_threads)
        .map(|tid| {
            let table = Arc::clone(&aligned_table);
            thread::spawn(move || benchmark_aligned(table, tid))
        })
        .collect();
    for h in handles {
        h.join().unwrap();
    }
    let aligned_duration = start.elapsed();
    println!("Aligned time: {:?}", aligned_duration);
    println!("\nSpeedup: {:.2}x", naive_duration.as_secs_f64() / aligned_duration.as_secs_f64());
}
```

The naive implementation places the lock, atomic counter, and data vector adjacently in memory without regard for cache line boundaries. When multiple threads access different buckets, their operations contend for the same cache line even though they target logically independent data. The aligned version uses `#[repr(align(64))]` to force each bucket onto a separate cache line and inserts padding to ensure the lock and counter do not share a line.

Build and run the binary to observe the timing difference:

```bash
cargo build --release --bin cache_profile
./target/release/cache_profile
```

The aligned version should show significantly lower latency, especially as thread count increases. However, wall-clock time alone does not explain why. Use Linux's `perf` tool to measure hardware performance counters, specifically L1 and L3 cache misses.

```bash
perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses ./target/release/cache_profile
```

The output reports total cache references, cache misses, and the miss rate at each cache level. The naive version will exhibit a higher miss rate, particularly in L1 data cache loads, because false sharing forces cache line invalidation between threads. The aligned version reduces misses by ensuring each thread operates on distinct cache lines.

For deeper analysis, record a trace and analyze it with `perf record` and `perf report`:

```bash
perf record -e cache-misses -g ./target/release/cache_profile
perf report --stdio
```

The report attributes cache misses to specific functions and call stacks. Examine the `benchmark_naive` and `benchmark_aligned` functions to see where misses occur. The naive version will show misses concentrated around the atomic fetch-add and lock acquisition because these operations trigger cache coherence traffic. The aligned version distributes misses more evenly, as each thread's working set fits within its own cache lines.

To visualize the performance difference at the microarchitecture level, use `perf annotate` to see instruction-level cache miss attribution:

```bash
perf annotate --stdio ast_analysis::sum_indexed
```

This command disassembles the function and annotates each instruction with its cache miss percentage. Look for hot spots where memory accesses cause stalls, such as pointer dereferences in tight loops or atomic operations under contention.

For profiling throughput and identifying CPU-bound bottlenecks, generate a flame graph using `cargo-flamegraph`. This tool samples the program's call stack at regular intervals and produces an interactive SVG showing where CPU time is spent.

```bash
cargo flamegraph --bin cache_profile -- 
```

The flame graph visualizes the call stack hierarchy, with wider bars indicating functions that consume more CPU time. Hover over bars to see exact percentages. Compare flame graphs of the naive and aligned versions to see how contention shifts CPU time from productive work (hashing, inserting) to synchronization overhead (lock acquisition, cache coherence).

This exercise demonstrates the critical importance of cache-aware data layout. Even correct, thread-safe code suffers severe performance degradation when cache lines are shared unnecessarily. Apply these profiling techniques to any concurrent data structure where performance falls short of expectations, especially lock-free algorithms where atomic operations become bottlenecks under high contention.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs manifest probabilistically, often appearing only under high load or specific thread interleavings. ThreadSanitizer (TSan) detects data races by instrumenting memory accesses and tracking happens-before relationships between threads. AddressSanitizer (ASan) detects memory safety violations including use-after-free, buffer overflows, and memory leaks. This exercise deliberately introduces concurrency and memory bugs, then uses sanitizers to diagnose them.

Create a third binary implementing a lock-free concurrent counter with intentional races and a memory pool with deliberate leaks.

```rust
// src/bin/race_stress.rs

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use std::alloc::{alloc, dealloc, Layout};

const ITERATIONS: usize = 1_000_000;
const THREADS: usize = 8;

struct RacyCounter {
    value: AtomicUsize,
    non_atomic: usize,
}

impl RacyCounter {
    fn new() -> Self {
        Self {
            value: AtomicUsize::new(0),
            non_atomic: 0,
        }
    }

    fn increment_correct(&self) {
        self.value.fetch_add(1, Ordering::SeqCst);
    }

    fn increment_racy(&mut self) {
        self.non_atomic += 1;
    }
}

struct LeakyPool {
    allocations: Vec<*mut u8>,
}

impl LeakyPool {
    fn new() -> Self {
        Self {
            allocations: Vec::new(),
        }
    }

    fn allocate(&mut self, size: usize) -> *mut u8 {
        unsafe {
            let layout = Layout::from_size_align_unchecked(size, 8);
            let ptr = alloc(layout);
            self.allocations.push(ptr);
            ptr
        }
    }

    fn leak_half(&mut self) {
        let half = self.allocations.len() / 2;
        self.allocations.truncate(half);
    }

    fn free_all(&mut self) {
        for &ptr in &self.allocations {
            unsafe {
                let layout = Layout::from_size_align_unchecked(1024, 8);
                dealloc(ptr, layout);
            }
        }
        self.allocations.clear();
    }
}

fn test_data_race() {
    println!("=== Testing Data Race (Intentional Bug) ===");
    let counter = Arc::new(parking_lot::Mutex::new(RacyCounter::new()));
    
    let handles: Vec<_> = (0..THREADS)
        .map(|_| {
            let counter = Arc::clone(&counter);
            thread::spawn(move || {
                for _ in 0..ITERATIONS / THREADS {
                    let mut guard = counter.lock();
                    guard.increment_racy();
                }
            })
        })
        .collect();

    for h in handles {
        h.join().unwrap();
    }

    let final_value = counter.lock().non_atomic;
    println!("Expected: {}, Got: {} (race detected: {})", 
             ITERATIONS, final_value, final_value != ITERATIONS);
}

fn test_correct_atomic() {
    println!("\n=== Testing Correct Atomic Operations ===");
    let counter = Arc::new(RacyCounter::new());
    
    let handles: Vec<_> = (0..THREADS)
        .map(|_| {
            let counter = Arc::clone(&counter);
            thread::spawn(move || {
                for _ in 0..ITERATIONS / THREADS {
                    counter.increment_correct();
                }
            })
        })
        .collect();

    for h in handles {
        h.join().unwrap();
    }

    let final_value = counter.value.load(Ordering::SeqCst);
    println!("Expected: {}, Got: {} (correct: {})", 
             ITERATIONS, final_value, final_value == ITERATIONS);
}

fn test_memory_leak() {
    println!("\n=== Testing Memory Leak (Intentional) ===");
    let mut pool = LeakyPool::new();
    
    for _ in 0..1000 {
        pool.allocate(1024);
    }
    
    pool.leak_half();
    pool.free_all();
    
    println!("Leaked approximately {} KB", (1000 - 500) * 1024 / 1024);
}

fn test_use_after_free() {
    println!("\n=== Testing Use-After-Free (Intentional Bug) ===");
    unsafe {
        let layout = Layout::from_size_align_unchecked(64, 8);
        let ptr = alloc(layout);
        *ptr = 42;
        dealloc(ptr, layout);
        let value = *ptr;
        println!("Read value after free: {}", value);
    }
}

fn main() {
    test_correct_atomic();
    test_data_race();
    test_memory_leak();
    test_use_after_free();
}
```

This binary contains four tests: a correct atomic counter, a racy non-atomic counter, a memory pool that deliberately leaks allocations, and a use-after-free access. Running the binary without instrumentation produces unpredictable results—the data race may or may not manifest depending on thread scheduling, and the memory errors may appear benign due to allocator behavior.

First, compile and run with ThreadSanitizer to detect the data race. Rust requires the nightly toolchain and specific environment variables to enable TSan:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build --bin race_stress --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/race_stress
```

ThreadSanitizer instruments every memory access and lock operation, tracking the happens-before relationships established by synchronization primitives. When it detects two unsynchronized accesses to the same memory location where at least one is a write, it reports a data race with full stack traces showing both conflicting accesses.

The output will include a detailed report like:

```text
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7fff12345678 by thread T2:
    #0 race_stress::RacyCounter::increment_racy race_stress.rs:32
    #1 race_stress::test_data_race::{{closure}} race_stress.rs:67
    
  Previous write of size 8 at 0x7fff12345678 by thread T1:
    #0 race_stress::RacyCounter::increment_racy race_stress.rs:32
    #1 race_stress::test_data_race::{{closure}} race_stress.rs:67
```

The report identifies the exact line where the race occurs (`non_atomic += 1`), the memory address, and the threads involved. This output confirms that multiple threads are modifying `non_atomic` without synchronization, violating the memory model. The correct atomic version does not trigger warnings because `fetch_add` establishes proper synchronization through atomic orderings.

Next, compile with AddressSanitizer to detect the memory leak and use-after-free:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo +nightly build --bin race_stress --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/race_stress
```

AddressSanitizer replaces the default allocator with an instrumented version that tracks every allocation and deallocation, maintaining shadow memory that records the state of each byte (allocated, freed, poisoned). When the program exits, ASan reports any allocations that were never freed:

```text
=================================================================
==12346==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 512000 byte(s) in 500 object(s) allocated from:
    #0 0x7f1234567890 in __interceptor_malloc
    #1 0x5555abcdef01 in alloc::alloc::alloc race_stress.rs:45
    #2 0x5555abcdef02 in race_stress::LeakyPool::allocate race_stress.rs:46
    #3 0x5555abcdef03 in race_stress::test_memory_leak race_stress.rs:112
```

The report shows that 500 allocations totaling 512 KB were leaked, providing stack traces to the allocation sites. This allows you to trace the leak back to `test_memory_leak` where we deliberately truncated the allocation vector without freeing the memory.

For the use-after-free, ASan reports:

```text
=================================================================
==12347==ERROR: AddressSanitizer: heap-use-after-free on address 0x603000001234 at pc 0x5555abcdef04
READ of size 1 at 0x603000001234 thread T0
    #0 0x5555abcdef04 in race_stress::test_use_after_free race_stress.rs:120
    
0x603000001234 is located 0 bytes inside of 64-byte region freed by thread T0 here:
    #0 0x7f1234567890 in __interceptor_free
    #1 0x5555abcdef05 in alloc::alloc::dealloc race_stress.rs:119
```

The report identifies the exact address, the type of violation (read-after-free), and provides stack traces for both the access and the deallocation. This makes it trivial to diagnose use-after-free bugs that would otherwise require hours of debugging or only manifest in production under rare conditions.

To stress test for races that require specific interleavings, run the binary repeatedly under high load while monitoring for failures:

```bash
for i in {1..100}; do
    echo "Iteration $i"
    RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --bin race_stress --target x86_64-unknown-linux-gnu 2>&1 | grep -i "WARNING"
    if [ $? -eq 0 ]; then
        echo "Race detected in iteration $i"
        break
    fi
done
```

This loop runs the test 100 times, terminating early if TSan detects a race. The probabilistic nature of data races means they may not appear on every run, but repeated execution under instrumentation dramatically increases detection probability.

For production readiness, integrate sanitizer runs into your continuous integration pipeline. Configure separate CI jobs that build and test with each sanitizer, failing the build if any violations are detected. This prevents concurrency and memory bugs from reaching production.

```bash
#!/bin/bash
# ci-sanitizer-check.sh

set -e

echo "Running ThreadSanitizer..."
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu

echo "Running AddressSanitizer..."
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu

echo "Running LeakSanitizer..."
RUSTFLAGS="-Z sanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu

echo "All sanitizer checks passed."
```

This exercise demonstrates that correct concurrent code requires both algorithmic correctness (proper use of synchronization primitives) and verification that the implementation matches the design. Sanitizers provide the ground truth that code review and testing cannot, detecting subtle violations of the memory model that manifest only under specific thread interleavings or memory access patterns.

## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the essential commands and workflows for daily systems programming verification. Bookmark this page and internalize these commands until they become reflexive.

**Compiler Intermediate Representation Analysis:**

```bash
# Expand macros and desugar syntax
cargo expand --bin <binary_name>

# Emit unoptimized LLVM IR
rustc --emit=llvm-ir src/bin/<file>.rs --crate-type bin -C opt-level=0

# Emit optimized LLVM IR
rustc --emit=llvm-ir src/bin/<file>.rs --crate-type bin -C opt-level=3 -C lto=fat

# Emit assembly
rustc --emit=asm src/bin/<file>.rs --crate-type bin -C opt-level=3

# Disassemble release binary
llvm-objdump -d --demangle target/release/<binary_name>
```

**Cache and Performance Profiling:**

```bash
# Hardware performance counters
perf stat -e cache-references,cache-misses,L1-dcache-load-misses,LLC-load-misses <binary>

# Record cache miss trace
perf record -e cache-misses -g <binary>
perf report --stdio

# Annotate instruction-level cache misses
perf annotate --stdio <function_name>

# Generate flame graph
cargo flamegraph --bin <binary_name>
```

**Memory and Concurrency Sanitizers:**

```bash
# ThreadSanitizer (data race detection)
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --bin <binary_name> --target x86_64-unknown-linux-gnu

# AddressSanitizer (memory safety)
RUSTFLAGS="-Z sanitizer=address" cargo +nightly run --bin <binary_name> --target x86_64-unknown-linux-gnu

# LeakSanitizer (memory leaks)
RUSTFLAGS="-Z sanitizer=leak" cargo +nightly run --bin <binary_name> --target x86_64-unknown-linux-gnu

# Valgrind (alternative memory checker)
valgrind --leak-check=full --show-leak-kinds=all ./target/debug/<binary_name>
```

**Debugging Runtime Behavior:**

```bash
# Start LLDB debugger
lldb target/debug/<binary_name>

# Common LLDB commands
(lldb) b <function_name>        # Set breakpoint
(lldb) run                      # Start execution
(lldb) step                     # Step into
(lldb) next                     # Step over
(lldb) register read            # Show all registers
(lldb) register read rax rcx    # Show specific registers
(lldb) memory read <address>    # Examine memory
(lldb) disassemble              # Show disassembly
(lldb) bt                       # Show backtrace
```

**Cargo Configuration Checklist:**

```toml
# Cargo.toml optimization profile
[profile.release]
opt-level = 3              # Maximum optimization
lto = "fat"                # Link-time optimization
codegen-units = 1          # Single-threaded compilation for better optimization
debug = true               # Preserve debug symbols for profiling
strip = false              # Keep symbols in binary
panic = "abort"            # Faster panics for production

[profile.dev]
opt-level = 0              # Fast compilation
debug = true               # Full debug info
split-debuginfo = "unpacked"  # Faster debug builds

[profile.bench]
inherits = "release"       # Benchmark with release settings
```

**Pre-Commit Hook for Sanitizer Checks:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running ThreadSanitizer on tests..."
if ! RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu 2>&1 | grep -q "test result: ok"; then
    echo "ThreadSanitizer detected issues. Commit aborted."
    exit 1
fi

echo "Running AddressSanitizer on tests..."
if ! RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu 2>&1 | grep -q "test result: ok"; then
    echo "AddressSanitizer detected issues. Commit aborted."
    exit 1
fi

echo "All sanitizer checks passed."
exit 0
```

**Verification Workflow Summary:**

For every performance-critical or concurrency-sensitive change, execute this verification sequence:

1. **Emit and inspect LLVM IR** to verify the optimizer generated efficient code. Check that bounds checks disappeared, loops unrolled, and abstractions compiled to zero-cost machine code.

2. **Profile with `perf`** to measure cache misses and identify hot paths. Use `perf annotate` to attribute cache misses to specific instructions and data structures.

3. **Generate a flame graph** to visualize where CPU time is spent. Look for unexpected synchronization overhead, excessive allocations, or imbalanced workload distribution.

4. **Run under ThreadSanitizer** to detect data races. Any warning indicates a violation of the memory model requiring immediate attention.

5. **Run under AddressSanitizer** to catch memory safety violations including buffer overflows, use-after-free, and leaks. Integrate sanitizer runs into CI to prevent regressions.

6. **Debug with LLDB** to observe runtime state and verify assumptions about register allocation, memory layout, and execution flow.

This systematic approach transforms verification from an ad-hoc afterthought into a disciplined engineering practice. Internalize these tools and workflows until they become second nature, enabling you to write systems code with confidence that it performs as designed and executes without undefined behavior.
