# Operational Verification Labs: Full Stack Development

## Objective & Toolchain Setup

Modern full-stack development demands rigorous operational verification at every layer of the compilation and runtime stack. The gap between a program that compiles and a program that executes correctly under production load is vast, bridged only through systematic instrumentation, profiling, and stress testing. This laboratory guide walks you through the concrete engineering practices that separate fragile prototypes from production-grade systems: abstract syntax tree inspection to understand compiler transformations, cache profiling to eliminate performance cliffs, and dynamic analysis to detect concurrency bugs that surface only under adversarial thread interleavings.

The exercises in this guide target the systems programmer who needs to reason about code not just at the source level but across the entire compilation pipeline—from high-level language constructs down through intermediate representations, machine code, and runtime memory layouts. You will work with Rust, C++, and Go codebases, leveraging their respective toolchains to expose latent defects, measure cache behavior, and validate thread safety properties. The methodology is grounded in first-principles understanding of how compilers emit code, how CPUs execute instructions, and how operating systems schedule threads, but the emphasis remains relentlessly practical: every command sequence you execute here can be integrated directly into continuous integration pipelines or local development workflows.

Begin by establishing a complete systems toolchain. Install Rust through `rustup`, which provisions the stable Rust compiler (`rustc`), the Cargo build system, and core utilities like `rustfmt` and `clippy`. Verify the installation with `rustc --version` and `cargo --version`, ensuring you have at least Rust 1.70 or later to access modern sanitizer integrations. Install LLVM tooling including `lldb` for debugging and `llvm-objdump` for disassembly inspection. On Linux systems, install Valgrind through your package manager (`apt install valgrind` on Debian-based distributions, `dnf install valgrind` on Fedora) to enable heap profiling and leak detection. For C++ development, install Clang with AddressSanitizer and ThreadSanitizer support, typically bundled in the `clang` package. For Go, install the official Go toolchain from `golang.org`, which includes integrated race detection and profiling tools. Install `perf` for CPU profiling on Linux (`linux-tools-common` and `linux-tools-generic` packages) and `cargo-flamegraph` for Rust-specific flame graph generation via `cargo install flamegraph`. Verify your installation by running `cargo --version`, `clang --version`, `go version`, `valgrind --version`, and `perf --version`. Ensure kernel settings permit `perf` access by setting `kernel.perf_event_paranoid` to 1 or lower via `sysctl -w kernel.perf_event_paranoid=1`.

Configure your development environment to emit debug symbols by default. In Rust projects, ensure your `Cargo.toml` includes a `[profile.dev]` section with `debug = true` and a `[profile.release]` section with `debug = true` to enable symbol generation even in optimized builds. This configuration allows profilers and debuggers to map machine addresses back to source lines. For C++ projects using CMake, set `CMAKE_BUILD_TYPE=RelWithDebInfo` to generate optimized code with symbols. For Go, the default build includes DWARF debug information, but you can disable optimization during profiling with `go build -gcflags="-N -l"` to prevent inlining and other transformations that obscure stack traces.

## Exercise 1: AST, IR & Disassembly Analysis

Understanding how high-level code transforms into machine instructions is foundational to diagnosing performance anomalies and security vulnerabilities. Compilers perform aggressive optimizations that can eliminate bounds checks, reorder memory operations, and inline function calls, all of which affect runtime behavior in non-obvious ways. This exercise walks you through the concrete steps of inspecting the abstract syntax tree (AST), examining intermediate representations (IR), and analyzing the final machine code emitted by the compiler. You will trace a simple Rust function through each compilation stage, observing how ownership semantics, borrow checking, and type information guide the optimizer's decisions.

Start by creating a minimal Rust project to serve as the analysis target. Execute `cargo new cache_analysis --bin` to scaffold a new binary project. Navigate into the `cache_analysis` directory and replace the contents of `src/main.rs` with the following complete implementation:

```rust
use std::hint::black_box;

fn sum_array(data: &[u64]) -> u64 {
    let mut total: u64 = 0;
    for &value in data {
        total = total.wrapping_add(value);
    }
    total
}

fn main() {
    let data: Vec<u64> = (0..1024).map(|i| i * 7).collect();
    let result = sum_array(&data);
    println!("Sum: {}", black_box(result));
}
```

This program constructs a vector of 1024 unsigned 64-bit integers, computes their sum using wrapping arithmetic to prevent overflow panics, and prints the result. The `black_box` intrinsic prevents the compiler from optimizing away the computation entirely by treating the result as opaque.

To inspect the abstract syntax tree, use the Rust compiler's `-Z` unstable options, which require nightly Rust. Install the nightly toolchain with `rustup toolchain install nightly` and set it as the default for this project with `rustup override set nightly`. Now execute `cargo rustc -- -Z unpretty=ast-tree` to emit the parsed and macro-expanded AST. The output reveals the tree structure of your program: the `fn` items representing function declarations, the `Vec::new` and `Iterator::collect` method calls desugared into their full forms, and the `for` loop expanded into a match statement over the iterator's `next` method. Observe how lifetimes are implicit at this stage; the borrow checker has not yet run, so lifetime annotations do not appear in the AST. This representation is closest to the source code but still shows how syntactic sugar like `for` loops desugar into more primitive constructs.

Next, examine the mid-level intermediate representation (MIR) by running `cargo rustc -- -Z unpretty=mir`. The MIR output is considerably more verbose, showing the function body decomposed into basic blocks connected by control-flow edges. Each basic block consists of a sequence of statements followed by a terminator (a branch, return, or panic). Locate the `sum_array` function in the output and observe how the `for` loop becomes a series of blocks: one for the loop header that checks the iterator state, one for the loop body that performs the addition, and one for loop exit. Notice the explicit drop instructions inserted by the compiler to deallocate the iterator when it goes out of scope, demonstrating Rust's automatic resource management. The MIR also shows the exact points where borrows are checked and released, making visible the borrow checker's enforcement of aliasing invariants. This representation is where most optimization passes operate, transforming the control-flow graph to eliminate dead code, inline functions, and vectorize loops.

To observe the final machine code, build the project in release mode and disassemble the resulting binary. Run `cargo build --release` to invoke the optimizer, then execute `llvm-objdump -d target/release/cache_analysis > disassembly.txt` to dump the disassembly to a file. Open `disassembly.txt` and locate the `cache_analysis::sum_array` symbol. You will find a tight loop consisting of load instructions (`mov` from memory), arithmetic operations (`add`), and a conditional branch (`jne` or `jnz`) back to the loop head. Modern LLVM often vectorizes this loop using SIMD instructions if the target CPU supports them; on x86-64 with AVX2, you may see `vpaddd` or `vpaddq` instructions operating on 256-bit registers, processing four `u64` values per iteration. Count the number of instructions in the loop body and compare it to the MIR representation. The optimizer has eliminated bounds checking because Rust's iterator protocol guarantees safe access, and it has unrolled or vectorized the loop to maximize throughput.

To quantify the impact of optimization levels, rebuild the project without optimization using `cargo build` (which defaults to debug mode) and disassemble the debug binary with `llvm-objdump -d target/debug/cache_analysis > disassembly_debug.txt`. Compare the two disassemblies side by side. The debug build retains individual instructions for each high-level operation, inserts bounds checks before every array access, and avoids inlining, making the code easier to debug but substantially slower. The release build, by contrast, aggressively inlines, elides safety checks that the type system guarantees will never fail, and restructures the loop for maximum instruction-level parallelism. This comparison reveals why release builds often run ten to one hundred times faster than debug builds for computationally intensive code.

Extend this analysis to a more complex scenario involving function inlining and dead code elimination. Add a second function to `main.rs`:

```rust
#[inline(never)]
fn compute_square(x: u64) -> u64 {
    x * x
}

fn process_data(data: &[u64]) -> u64 {
    let mut result = 0;
    for &value in data {
        result = result.wrapping_add(compute_square(value));
    }
    result
}
```

The `#[inline(never)]` attribute prevents the compiler from inlining `compute_square`, forcing a function call overhead. Rebuild in release mode and disassemble again. In the `process_data` function, you will observe a `call` instruction invoking `compute_square`, along with the associated register saving and stack frame setup. Now remove the `#[inline(never)]` attribute and rebuild. The `call` instruction disappears; the multiplication is now inline within the loop body, eliminating function call overhead. This demonstrates the compiler's inlining heuristic: small functions called in hot loops are inlined by default unless explicitly annotated otherwise.

To inspect how the compiler handles generic code and monomorphization, modify `sum_array` to be generic over the integer type:

```rust
use std::ops::AddAssign;

fn sum_array<T: AddAssign + Copy + Default>(data: &[T]) -> T {
    let mut total = T::default();
    for &value in data {
        total += value;
    }
    total
}

fn main() {
    let data_u64: Vec<u64> = (0..1024).map(|i| i * 7).collect();
    let data_u32: Vec<u32> = (0..1024).map(|i| (i * 7) as u32).collect();
    
    let result_u64 = sum_array(&data_u64);
    let result_u32 = sum_array(&data_u32);
    
    println!("u64 sum: {}", black_box(result_u64));
    println!("u32 sum: {}", black_box(result_u32));
}
```

Rebuild and disassemble. Search for `sum_array` in the output and you will find two distinct symbols: one for `u64` and one for `u32`. The compiler has monomorphized the generic function, generating specialized machine code for each concrete type. This is how Rust achieves zero-cost abstractions: generic code incurs no runtime dispatch overhead because the compiler generates type-specific implementations at compile time. Compare the two specialized versions; the `u64` version uses 64-bit registers and instructions, while the `u32` version uses 32-bit operations, demonstrating that generic abstractions do not impose a one-size-fits-all performance penalty.

This exercise establishes the foundational skill of reading compiler output to validate assumptions about performance and safety. The AST shows syntactic structure, the MIR reveals control flow and borrow checker decisions, and the disassembly exposes the actual machine instructions executed by the CPU. Mastery of this workflow enables you to identify optimization opportunities, diagnose unexpected performance characteristics, and verify that security-critical operations are not optimized away.

## Exercise 2: Cache Miss & Throughput Profiling

Modern CPU performance is dominated not by raw instruction throughput but by memory access patterns and cache behavior. A memory load that hits L1 cache completes in approximately four cycles, while a load that misses all cache levels and fetches from main memory can take two hundred cycles or more. This two-order-of-magnitude latency difference means that cache-aware data structure design is the single most impactful optimization technique available to systems programmers. This exercise guides you through profiling cache miss rates using hardware performance counters, correlating misses with source code locations, and restructuring data layouts to improve spatial locality.

Begin by implementing a benchmark that exhibits poor cache behavior. Create a new Rust project with `cargo new cache_benchmark --bin` and replace `src/main.rs` with the following implementation:

```rust
use std::time::Instant;
use std::hint::black_box;

const SIZE: usize = 1024 * 1024; // 1 million elements
const STRIDE: usize = 64; // Cache line size in bytes / sizeof(u64) = 8 elements

struct Data {
    values: Vec<u64>,
}

impl Data {
    fn new(size: usize) -> Self {
        Data {
            values: (0..size).map(|i| i as u64).collect(),
        }
    }

    fn sequential_sum(&self) -> u64 {
        let mut sum = 0u64;
        for &value in &self.values {
            sum = sum.wrapping_add(value);
        }
        sum
    }

    fn strided_sum(&self, stride: usize) -> u64 {
        let mut sum = 0u64;
        let mut index = 0;
        while index < self.values.len() {
            sum = sum.wrapping_add(self.values[index]);
            index += stride;
        }
        sum
    }
}

fn main() {
    let data = Data::new(SIZE);

    let start = Instant::now();
    let sequential_result = black_box(data.sequential_sum());
    let sequential_duration = start.elapsed();

    let start = Instant::now();
    let strided_result = black_box(data.strided_sum(STRIDE));
    let strided_duration = start.elapsed();

    println!("Sequential sum: {} in {:?}", sequential_result, sequential_duration);
    println!("Strided sum: {} in {:?}", strided_result, strided_duration);
    println!("Ratio: {:.2}x", strided_duration.as_secs_f64() / sequential_duration.as_secs_f64());
}
```

This program allocates a one-million-element array and performs two summation passes: one that accesses elements sequentially and one that accesses every 64th element. Sequential access benefits from hardware prefetching and cache line reuse, while strided access defeats the prefetcher and incurs a cache miss on nearly every load. Build and run the benchmark with `cargo run --release`. On a typical modern processor, the strided version will be three to five times slower despite touching far fewer elements, demonstrating the dominance of memory latency over instruction count.

To quantify cache misses precisely, profile the benchmark using `perf`, the Linux performance analysis toolkit. Run `perf stat -e cache-misses,cache-references,L1-dcache-load-misses,L1-dcache-loads ./target/release/cache_benchmark`. The `perf stat` command executes the program and reports hardware performance counter values at completion. The output shows total cache references (all memory accesses that queried the cache), cache misses (accesses that missed all cache levels and fetched from DRAM), L1 data cache loads, and L1 data cache load misses. Record these values. The sequential summation should exhibit a cache miss rate below 1%, indicating that nearly all accesses hit L1 or L2. The strided summation, by contrast, will show a miss rate above 50%, with most accesses missing L1 and many missing L2 and L3 as well.

To correlate cache misses with specific source code lines, use `perf record` to capture detailed profiling data. Execute `perf record -e cache-misses -g ./target/release/cache_benchmark` to record a call-graph profile of cache miss events. The `-g` flag enables stack trace capture, allowing `perf` to attribute misses to specific function call chains. After the program completes, run `perf report` to launch an interactive terminal interface displaying the hottest code paths. Navigate to the `strided_sum` function and observe that nearly all cache misses are attributed to the array load instruction inside the loop. Exit the report with `q` and generate a flame graph for a visual representation of where time is spent. Install `flamegraph` if not already present with `cargo install flamegraph`, then execute `perf script | stackcollapse-perf.pl | flamegraph.pl > cache_misses.svg`. Open `cache_misses.svg` in a browser to see a hierarchical visualization of cache miss attribution across the call stack.

Extend the benchmark to demonstrate the impact of data structure layout on cache behavior. Add a new struct that uses array-of-structs (AoS) layout versus struct-of-arrays (SoA) layout:

```rust
#[derive(Clone, Copy)]
struct Point {
    x: f64,
    y: f64,
    z: f64,
}

struct PointsAoS {
    points: Vec<Point>,
}

struct PointsSoA {
    x: Vec<f64>,
    y: Vec<f64>,
    z: Vec<f64>,
}

impl PointsAoS {
    fn new(size: usize) -> Self {
        PointsAoS {
            points: (0..size).map(|i| Point {
                x: i as f64,
                y: (i * 2) as f64,
                z: (i * 3) as f64,
            }).collect(),
        }
    }

    fn sum_x(&self) -> f64 {
        self.points.iter().map(|p| p.x).sum()
    }
}

impl PointsSoA {
    fn new(size: usize) -> Self {
        PointsSoA {
            x: (0..size).map(|i| i as f64).collect(),
            y: (0..size).map(|i| (i * 2) as f64).collect(),
            z: (0..size).map(|i| (i * 3) as f64).collect(),
        }
    }

    fn sum_x(&self) -> f64 {
        self.x.iter().copied().sum()
    }
}

fn benchmark_aos_vs_soa() {
    let size = 1024 * 1024;
    
    let aos = PointsAoS::new(size);
    let start = Instant::now();
    let aos_result = black_box(aos.sum_x());
    let aos_duration = start.elapsed();

    let soa = PointsSoA::new(size);
    let start = Instant::now();
    let soa_result = black_box(soa.sum_x());
    let soa_duration = start.elapsed();

    println!("AoS sum_x: {} in {:?}", aos_result, aos_duration);
    println!("SoA sum_x: {} in {:?}", soa_result, soa_duration);
    println!("Speedup: {:.2}x", aos_duration.as_secs_f64() / soa_duration.as_secs_f64());
}
```

Add a call to `benchmark_aos_vs_soa()` in `main`. The AoS layout stores each point as a contiguous `Point` struct, meaning that accessing only the `x` coordinate still loads the full 24-byte struct into cache, wasting two-thirds of each cache line. The SoA layout stores all `x` coordinates contiguously in a single array, allowing the CPU to load cache lines fully utilized by useful data. Run `cargo run --release` and observe that the SoA version is approximately three times faster, directly corresponding to the bandwidth saved by not loading unused `y` and `z` coordinates. Profile both versions with `perf stat -e cache-misses,cache-references` to confirm that the SoA version has a significantly lower cache miss rate.

To visualize cache behavior at a finer granularity, use `cachegrind`, a Valgrind tool that simulates cache hierarchies. Run `valgrind --tool=cachegrind --cachegrind-out-file=cachegrind.out ./target/release/cache_benchmark`. After completion, execute `cg_annotate cachegrind.out` to display a line-by-line breakdown of cache misses attributed to each source line. The output shows instruction cache misses (I refs), L1 data cache misses (D1 refs), and last-level cache misses (LL refs). Identify the loop in `strided_sum` and observe the high LL miss rate, confirming that the strided access pattern defeats the entire cache hierarchy.

This exercise establishes proficiency in measuring and optimizing memory-bound code. The workflow of profiling with `perf`, correlating misses to source lines, and restructuring data layouts to improve locality is universally applicable across performance-critical systems. Understanding that cache misses dominate performance more than instruction count or branch prediction is the foundational insight that separates novice programmers from senior systems engineers.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs are among the most insidious defects in systems software: they manifest nondeterministically, reproduce only under specific thread interleavings, and often escape detection during development only to cause catastrophic failures in production. Memory safety bugs like use-after-free and double-free are similarly elusive, often lying dormant for millions of operations before triggering corruption or crashes. This exercise trains you to employ dynamic analysis tools that detect these bugs reliably: ThreadSanitizer for data races, AddressSanitizer for memory corruption, and LeakSanitizer for memory leaks. You will write deliberately buggy code, observe how the sanitizers detect and report the defects, and validate the fixes through stress testing.

Start by implementing a multithreaded Rust program that contains a data race. Create a new project with `cargo new race_detector --bin` and replace `src/main.rs` with the following:

```rust
use std::sync::Arc;
use std::thread;

struct Counter {
    value: u64,
}

impl Counter {
    fn new() -> Self {
        Counter { value: 0 }
    }

    fn increment(&mut self) {
        self.value += 1;
    }

    fn get(&self) -> u64 {
        self.value
    }
}

fn main() {
    let counter = Arc::new(Counter::new());
    let mut handles = vec![];

    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100_000 {
                unsafe {
                    let ptr = Arc::as_ptr(&counter_clone) as *mut Counter;
                    (*ptr).increment();
                }
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Final count: {}", counter.get());
}
```

This program spawns ten threads that each increment a shared counter one hundred thousand times. The expected final value is one million, but because the increment operation is not atomic and threads access the counter without synchronization, the program contains a data race. The unsafe block bypasses Rust's borrow checker, which would normally prevent shared mutable access. Run `cargo run --release` multiple times. The final count will vary unpredictably, often falling well short of one million, because concurrent increments interfere with each other: one thread may read the value, then get preempted, then another thread increments and writes back, then the first thread resumes and writes its stale value, losing the second thread's update.

To detect this race automatically, rebuild with ThreadSanitizer enabled. Rust's `cargo` build system does not directly support ThreadSanitizer, but you can invoke `rustc` with the appropriate flags. First, install the nightly toolchain if not already present: `rustup toolchain install nightly`. Set the nightly toolchain as active for this project: `rustup override set nightly`. Now build with ThreadSanitizer: `RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu`. Note that ThreadSanitizer is only available on Linux and macOS. After the build completes, run the instrumented binary: `./target/x86_64-unknown-linux-gnu/debug/race_detector`. ThreadSanitizer will detect the data race and print a detailed report:

```text
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7ffabcdef000 by thread T2:
    #0 Counter::increment race_detector.rs:13
    #1 race_detector::main::{{closure}} race_detector.rs:27
  Previous read of size 8 at 0x7ffabcdef000 by thread T1:
    #0 Counter::increment race_detector.rs:13
    #1 race_detector::main::{{closure}} race_detector.rs:27
```

The report identifies the conflicting memory accesses, the threads involved, and the exact source code lines. This race occurs because `value += 1` decomposes into a read, an addition, and a write, and these three operations are not atomic. Two threads can read the same value, increment it independently, and both write back the incremented value, losing one update.

Fix the race by replacing the unsafe shared mutation with proper synchronization. Replace the `Counter` implementation with an atomic counter:

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

struct Counter {
    value: AtomicU64,
}

impl Counter {
    fn new() -> Self {
        Counter {
            value: AtomicU64::new(0),
        }
    }

    fn increment(&self) {
        self.value.fetch_add(1, Ordering::Relaxed);
    }

    fn get(&self) -> u64 {
        self.value.load(Ordering::Relaxed)
    }
}

fn main() {
    let counter = Arc::new(Counter::new());
    let mut handles = vec![];

    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100_000 {
                counter_clone.increment();
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Final count: {}", counter.get());
}
```

The `AtomicU64` type provides atomic read-modify-write operations that the CPU executes as single, indivisible instructions. The `fetch_add` method atomically reads the current value, adds one, and writes back the result, preventing the lost-update race. Rebuild and run with ThreadSanitizer again. The race report disappears, and the final count is consistently one million.

To test AddressSanitizer, which detects memory corruption, create a new project: `cargo new asan_test --bin`. Implement a use-after-free bug:

```rust
fn main() {
    let mut data = vec![1, 2, 3, 4, 5];
    let ptr = data.as_mut_ptr();
    
    drop(data); // Deallocate the vector
    
    unsafe {
        // Use-after-free: access deallocated memory
        println!("Value: {}", *ptr);
    }
}
```

This program allocates a vector, obtains a raw pointer to its data, deallocates the vector, then dereferences the pointer. This is a use-after-free bug: the pointer refers to freed memory, and accessing it invokes undefined behavior. Run the program normally with `cargo run --release`. On many executions, it will print a value (often the original value or garbage) without crashing, because the freed memory has not yet been reused. This nondeterminism makes use-after-free bugs extremely difficult to diagnose without instrumentation.

Build with AddressSanitizer: `RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu`. Run the instrumented binary: `./target/x86_64-unknown-linux-gnu/debug/asan_test`. AddressSanitizer detects the use-after-free and aborts with a detailed report:

```text
==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x60300000eff0 at pc 0x000000401234
READ of size 4 at 0x60300000eff0 thread T0
    #0 0x401234 in asan_test::main asan_test.rs:9
freed by thread T0 here:
    #0 0x402000 in free
    #1 0x401200 in drop asan_test.rs:6
previously allocated by thread T0 here:
    #0 0x403000 in malloc
    #1 0x401100 in vec::new asan_test.rs:2
```

The report shows the use-after-free read, the allocation site, and the deallocation site, providing complete context to diagnose the bug. Fix the code by removing the unsafe dereference or ensuring the vector is not dropped while the pointer is live.

To test LeakSanitizer, which detects memory leaks, extend the previous program to leak memory:

```rust
use std::alloc::{alloc, Layout};

fn main() {
    for _ in 0..1000 {
        unsafe {
            let layout = Layout::from_size_align(1024, 8).unwrap();
            let ptr = alloc(layout);
            // Intentionally do not deallocate
            std::hint::black_box(ptr);
        }
    }
    println!("Done");
}
```

This program allocates one thousand 1KB blocks and never frees them. Build with AddressSanitizer, which includes LeakSanitizer by default: `RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu`. Run the binary. At program exit, LeakSanitizer scans for unreachable allocations and reports:

```text
==12345==ERROR: LeakSanitizer: detected memory leaks
Direct leak of 1024000 bytes in 1000 objects allocated from:
    #0 0x401000 in malloc
    #1 0x401100 in alloc asan_test.rs:6
SUMMARY: AddressSanitizer: 1024000 byte(s) leaked in 1000 allocation(s).
```

The report quantifies the leak and identifies the allocation site. Fix the leak by calling `std::alloc::dealloc` with the corresponding layout before the program exits.

For C++ code, the same sanitizers are accessible through Clang compiler flags. Create a minimal C++ program `race.cpp`:

```cpp
#include <thread>
#include <vector>
#include <iostream>

int counter = 0;

void increment() {
    for (int i = 0; i < 100000; ++i) {
        counter++;
    }
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(increment);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "Final count: " << counter << std::endl;
    return 0;
}
```

Build with ThreadSanitizer: `clang++ -fsanitize=thread -g -O1 race.cpp -o race`. Run `./race`. ThreadSanitizer detects the race on `counter` and reports the conflicting accesses. Fix by replacing `int counter` with `std::atomic<int> counter`. Build with AddressSanitizer for memory errors: `clang++ -fsanitize=address -g -O1 race.cpp -o race`. For leak detection, AddressSanitizer includes LeakSanitizer automatically unless disabled with `ASAN_OPTIONS=detect_leaks=0`.

Go provides built-in race detection through the `-race` flag. Create `race.go`:

```go
package main

import (
    "fmt"
    "sync"
)

var counter int

func increment(wg *sync.WaitGroup) {
    defer wg.Done()
    for i := 0; i < 100000; i++ {
        counter++
    }
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go increment(&wg)
    }
    wg.Wait()
    fmt.Println("Final count:", counter)
}
```

Run with race detection: `go run -race race.go`. The Go race detector identifies the unsynchronized access to `counter` and prints a report. Fix by using `sync/atomic` or protecting `counter` with a `sync.Mutex`.

This exercise establishes mastery of dynamic analysis tools that are indispensable for production systems development. ThreadSanitizer, AddressSanitizer, and LeakSanitizer detect entire classes of bugs that are otherwise nearly impossible to reproduce and diagnose. Integrating these tools into continuous integration pipelines ensures that concurrency and memory safety bugs are caught before they reach production.

## Developer Cheat Sheet & Toolchain Checklist

This reference consolidates the critical commands, environment configurations, and debugging workflows established in the preceding exercises. Commit these patterns to muscle memory; they form the operational backbone of production-grade systems engineering.

**Initial Toolchain Setup:**
Install Rust via `rustup` and verify with `rustc --version` and `cargo --version`. Install Clang with sanitizer support: `apt install clang` (Debian/Ubuntu) or equivalent. Install Valgrind: `apt install valgrind`. Install Go from `golang.org` and verify with `go version`. Install `perf`: `apt install linux-tools-common linux-tools-generic`. Install Rust profiling tools: `cargo install flamegraph`. Configure kernel for profiling: `sysctl -w kernel.perf_event_paranoid=1`. Verify full stack with `rustc --version`, `cargo --version`, `clang --version`, `valgrind --version`, `go version`, `perf --version`.

**Compiler Inspection Workflow (Rust):**
Install nightly toolchain: `rustup toolchain install nightly`, `rustup override set nightly`. Emit AST: `cargo rustc -- -Z unpretty=ast-tree`. Emit MIR: `cargo rustc -- -Z unpretty=mir`. Build release: `cargo build --release`. Disassemble: `llvm-objdump -d target/release/<binary> > disassembly.txt`. Compare debug vs release: `cargo build`, `llvm-objdump -d target/debug/<binary> > disassembly_debug.txt`, then diff the outputs. For LLVM IR: `cargo rustc --release -- --emit=llvm-ir`, inspect `target/release/deps/<crate>.ll`.

**Cache Profiling Workflow:**
Profile cache events: `perf stat -e cache-misses,cache-references,L1-dcache-load-misses,L1-dcache-loads <binary>`. Record detailed profile: `perf record -e cache-misses -g <binary>`. Inspect report: `perf report`. Generate flame graph: `perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg`. Simulate cache with Cachegrind: `valgrind --tool=cachegrind --cachegrind-out-file=cachegrind.out <binary>`, then `cg_annotate cachegrind.out`. For fine-grained profiling, use `perf record -e cycles:pp -g` to capture instruction-level attribution.

**Sanitizer Invocation (Rust):**
ThreadSanitizer: `RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu`, run `./target/x86_64-unknown-linux-gnu/debug/<binary>`. AddressSanitizer: `RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu`, run the debug binary. LeakSanitizer is included with AddressSanitizer by default. MemorySanitizer (for uninitialized reads): `RUSTFLAGS="-Z sanitizer=memory" cargo build --target x86_64-unknown-linux-gnu`. Note that sanitizers require nightly Rust: `rustup override set nightly`.

**Sanitizer Invocation (C++):**
ThreadSanitizer: `clang++ -fsanitize=thread -g -O1 source.cpp -o binary`. AddressSanitizer: `clang++ -fsanitize=address -g -O1 source.cpp -o binary`. UndefinedBehaviorSanitizer: `clang++ -fsanitize=undefined -g -O1 source.cpp -o binary`. Combine sanitizers: `clang++ -fsanitize=address,undefined -g -O1 source.cpp -o binary`. For leak detection specifically: `clang++ -fsanitize=leak -g source.cpp -o binary`. Disable optimizations for clearer stack traces: `-O0` instead of `-O1`.

**Race Detection (Go):**
Run with race detector: `go run -race source.go`. Build with race detector: `go build -race -o binary source.go`. Test with race detector: `go test -race ./...`. The Go race detector incurs significant runtime overhead (typically 5-10x slower) but is production-safe for testing and staging environments.

**Memory Profiling (Valgrind):**
Check for leaks: `valgrind --leak-check=full --track-origins=yes <binary>`. Full error checking: `valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all --track-origins=yes <binary>`. Heap profiling: `valgrind --tool=massif <binary>`, then visualize with `ms_print massif.out.<pid>`. Callgrind for call-graph profiling: `valgrind --tool=callgrind <binary>`, then analyze with `callgrind_annotate callgrind.out.<pid>` or visualize with `kcachegrind`.

**GDB Debugging Workflow:**
Launch with symbols: `gdb target/debug/<binary>`. Set breakpoint: `break main.rs:42`. Run: `run`. Inspect variables: `print variable_name`. Step through: `next` (step over), `step` (step into), `continue`. Backtrace: `backtrace` or `bt`. Thread inspection: `info threads`, `thread <n>`. Watchpoint on memory: `watch *0x7ffabcdef000`. For Rust, install `rust-gdb` wrapper which loads pretty-printers: `rust-gdb target/debug/<binary>`.

**LLDB Debugging Workflow (macOS/Clang):**
Launch: `lldb target/debug/<binary>`. Set breakpoint: `breakpoint set --file main.rs --line 42` or `b main.rs:42`. Run: `run`. Inspect: `frame variable` or `p variable_name`. Step: `next`, `step`, `continue`. Backtrace: `bt`. Thread inspection: `thread list`, `thread select <n>`. For Rust, use `rust-lldb` wrapper.

**Integration into CI/CD:**
Incorporate sanitizer runs in test suites by adding CI stages that build with sanitizers and execute test suites. Example GitHub Actions snippet for Rust:

```yaml
- name: Test with ThreadSanitizer
  run: |
    rustup toolchain install nightly
    RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu
```

For C++ projects using CMake, enable sanitizers in `CMakeLists.txt`:

```cmake
if(ENABLE_SANITIZERS)
  add_compile_options(-fsanitize=address,undefined -g)
  add_link_options(-fsanitize=address,undefined)
endif()
```

Invoke with `cmake -DENABLE_SANITIZERS=ON`. For Go, add `go test -race ./...` to the CI pipeline.

**Performance Benchmarking (Rust):**
Use Criterion for stable benchmarks: add `criterion = "0.5"` to `[dev-dependencies]`, create `benches/benchmark.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_function(c: &mut Criterion) {
    c.bench_function("sum_array", |b| {
        let data: Vec<u64> = (0..1024).collect();
        b.iter(|| {
            let sum: u64 = data.iter().copied().sum();
            black_box(sum);
        });
    });
}

criterion_group!(benches, benchmark_function);
criterion_main!(benches);
```

Run with `cargo bench`. For CPU profiling of benchmarks, use `cargo flamegraph --bench benchmark`.

**Common Pitfall Resolution:**
If `perf record` fails with permission denied, lower `perf_event_paranoid`: `sudo sysctl -w kernel.perf_event_paranoid=1`. If sanitizers cause excessive slowdown in tests, run a subset of tests with sanitizers and the full suite without. If ThreadSanitizer reports false positives on intentional benign races, annotate with `std::sync::atomic::compiler_fence` or use relaxed atomics. If AddressSanitizer increases binary size beyond disk limits, build only critical tests with sanitizers. If LeakSanitizer reports leaks in third-party libraries, suppress with `LSAN_OPTIONS=suppressions=lsan.supp` and create a suppression file listing known leaks.

This consolidated reference provides immediate access to the operational commands and workflows required for production systems verification. Mastery of these tools is not optional; they are the standard practice for any codebase that demands reliability, security, and performance at scale.
