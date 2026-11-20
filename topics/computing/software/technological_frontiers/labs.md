# Operational Verification Labs: Technological Frontiers

## Objective & Toolchain Setup

This lab guide treats the compiler toolchain as a diagnostic instrument. Rather than accepting program behavior at face value, you will learn to interrogate each layer of the software stack: from the abstract syntax tree the compiler first constructs, down through LLVM IR and machine code, and back up through sanitizers and profilers that observe the running process. The exercises are designed for a systems programmer who already writes working code and wants to understand why it performs and behaves the way it does, and how to catch the class of bugs that unit tests routinely miss.

The labs target a Linux x86-64 host. All three primary languages—Rust, C++, and Go—are exercised. The diagnostic instruments span static analysis (compiler IR dumps), dynamic analysis (AddressSanitizer, ThreadSanitizer, Valgrind's Memcheck and Helgrind), and performance profiling (perf, cargo-flamegraph, pprof). Every command is intended to be executed verbatim in a terminal.

**Installing the full toolchain** requires the following steps executed in order. First, install the Rust toolchain via rustup:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustup install nightly
rustup component add rust-src llvm-tools-preview
cargo install cargo-flamegraph flamegraph
```

Next, install the LLVM/Clang suite and system profiling tools. On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y \
  clang-17 llvm-17 lldb-17 \
  valgrind \
  linux-perf \
  golang-go \
  binutils \
  build-essential \
  libssl-dev \
  pkg-config
sudo ln -sf /usr/bin/clang-17 /usr/local/bin/clang
sudo ln -sf /usr/bin/clang++-17 /usr/local/bin/clang++
sudo ln -sf /usr/bin/lldb-17 /usr/local/bin/lldb
sudo ln -sf /usr/bin/llvm-objdump-17 /usr/local/bin/llvm-objdump
```

Verify the entire installation before beginning any exercise:

```bash
rustc --version
cargo --version
clang --version
lldb --version
valgrind --version
go version
perf --version
cargo flamegraph --version
```

Each exercise produces artifacts that build on the previous one. Work through them in sequence.

---

## Exercise 1: AST, IR & Disassembly Analysis

### Theory Anchor

A compiler transforms source text through a pipeline of progressively lower-level representations. Understanding this pipeline is not academic ceremony—it is the most direct way to verify that the optimizations you expect are actually occurring, to diagnose unexpected code generation, and to understand why two semantically equivalent source fragments can produce radically different machine code. The pipeline for both Clang and rustc terminates at LLVM IR before machine code emission, which means the diagnostic techniques for examining IR are almost identical between C++ and Rust.

The stages that matter here are: parsing into an AST (a structural tree representing the grammar of the source), lowering into LLVM IR (a typed, SSA-form intermediate representation), running optimization passes over that IR (inlining, loop unrolling, vectorization, dead code elimination), and finally emitting machine code that is assembled into object files. Each stage is a checkpoint where you can halt emission and inspect what the compiler has decided.

### Part A: Clang AST Dump and IR Emission for C++

Create the following C++ file, `matrix.cpp`. It performs a naive row-major matrix multiplication—a function that is rich enough to show interesting optimization behavior:

```cpp
#include <cstddef>
#include <cstring>

static const size_t N = 64;

void matmul(const float* __restrict__ A,
            const float* __restrict__ B,
            float* __restrict__ C,
            size_t n) {
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            float acc = 0.0f;
            for (size_t k = 0; k < n; ++k) {
                acc += A[i * n + k] * B[k * n + j];
            }
            C[i * n + j] = acc;
        }
    }
}

int main() {
    alignas(64) float A[N * N];
    alignas(64) float B[N * N];
    alignas(64) float C[N * N];
    memset(A, 0, sizeof(A));
    memset(B, 0, sizeof(B));
    matmul(A, B, C, N);
    return 0;
}
```

Dump the full Clang AST to stdout. The `-Xclang -ast-dump` flags inject a frontend plugin invocation that prints the AST before IR generation:

```bash
clang++ -Xclang -ast-dump -fsyntax-only matrix.cpp 2>&1 | less
```

Scan the output for the `FunctionDecl` node named `matmul`. Observe the `ForStmt` hierarchy nesting three levels deep, each `BinaryOperator` node carrying its result type (`float`), and how the `__restrict__` annotation appears on the `ParmVarDecl` nodes as a `RestrictAttr`. This is the structural representation the compiler reasons over before any lowering begins.

Now emit unoptimized LLVM IR:

```bash
clang++ -O0 -S -emit-llvm -o matrix_O0.ll matrix.cpp
```

Then emit optimized IR at O3 with vectorization remarks enabled so the compiler reports every auto-vectorization decision:

```bash
clang++ -O3 -march=native -S -emit-llvm \
  -Rpass=loop-vectorize \
  -Rpass-missed=loop-vectorize \
  -Rpass-analysis=loop-vectorize \
  -o matrix_O3.ll matrix.cpp
```

Open both `.ll` files side by side. In `matrix_O0.ll`, each array index calculation is explicit: you will see `getelementptr` instructions computing every byte offset, `load` and `store` instructions for every intermediate variable including `acc`, and no SIMD types. In `matrix_O3.ll`, look for `<4 x float>` or `<8 x float>` vector types—these are the SSE/AVX packed floating-point registers. The vectorizer has recognized that the innermost accumulation loop iterates over independent floating-point values and has unrolled and widened the loop into SIMD operations. The `-Rpass` output in your terminal will tell you exactly which loops were vectorized and at what width.

Examine the disassembly of the final object file to confirm the vector instructions made it through to machine code:

```bash
clang++ -O3 -march=native -c -o matrix.o matrix.cpp
llvm-objdump -d --x86-asm-syntax=intel matrix.o | grep -A 60 "<matmul>"
```

Look for `vmovaps`, `vfmadd231ps`, and `vmulps` mnemonics. These are AVX2 fused multiply-add instructions operating on 256-bit registers. If you see `addss` and `mulss` instead (scalar single-precision), it means vectorization failed—the `-Rpass-missed` output from the IR step will explain why.

### Part B: Rust MIR and LLVM IR Inspection

Create a new Cargo project:

```bash
cargo new --lib frontiers_lab && cd frontiers_lab
```

Replace `src/lib.rs` with the following:

```rust
#[no_mangle]
pub fn sum_squares(data: &[f64]) -> f64 {
    data.iter().map(|x| x * x).sum()
}

#[no_mangle]
pub fn conditional_accumulate(data: &[i64], threshold: i64) -> i64 {
    let mut total: i64 = 0;
    for &val in data {
        if val > threshold {
            total = total.wrapping_add(val);
        }
    }
    total
}
```

Rust's intermediate representation below the AST but above LLVM IR is called MIR (Mid-level Intermediate Representation). MIR is a control-flow graph of basic blocks with explicit borrows, moves, and drops. Inspecting it reveals how the borrow checker has modeled your program and shows exactly when destructors will be inserted:

```bash
RUSTFLAGS="--emit=mir" cargo build --release 2>&1
# MIR files are written alongside object files:
find target/ -name "*.mir" | xargs ls -lh
find target/ -name "*.mir" | head -1 | xargs less
```

Look for the `bb0`, `bb1`, ... basic block labels, the `StorageLive` and `StorageDead` annotations marking when stack slots become active, and the `drop` terminator for any type with a `Drop` implementation. For the functions above, you will see that the iterator chain in `sum_squares` has been inlined and represented as a simple loop in MIR with no heap allocation.

To emit LLVM IR from rustc directly, bypass Cargo and call rustc:

```bash
rustc --edition 2021 -C opt-level=3 -C target-cpu=native \
  --emit=llvm-ir -o /tmp/frontiers_lab.ll src/lib.rs
less /tmp/frontiers_lab.ll
```

Search for `sum_squares` in the IR. With opt-level 3 and target-cpu=native, you should find the same `<4 x double>` vector types that appeared in the C++ matrix example, confirming that rustc routes through the same LLVM backend and benefits from identical auto-vectorization passes.

Finally, disassemble the release binary to verify:

```bash
cargo build --release
llvm-objdump -d --x86-asm-syntax=intel \
  target/release/libfrontiers_lab.rlib 2>/dev/null || \
llvm-objdump -d --x86-asm-syntax=intel \
  target/release/deps/libfrontiers_lab-*.rlib | grep -A 40 "sum_squares"
```

### Part C: Go SSA Dump

Create a standalone Go file, `compute.go`:

```go
package main

import "fmt"

func sumSquares(data []float64) float64 {
	var acc float64
	for _, v := range data {
		acc += v * v
	}
	return acc
}

func escapeAnalysis(n int) *int {
	x := n * 2
	return &x
}

func main() {
	data := []float64{1, 2, 3, 4, 5}
	fmt.Println(sumSquares(data))
	p := escapeAnalysis(21)
	fmt.Println(*p)
}
```

Go's compiler exposes its SSA (Static Single Assignment) IR through an environment variable. The `GOSSAFUNC` variable names a function and causes the compiler to write a self-contained HTML file showing every SSA transformation pass:

```bash
GOSSAFUNC=sumSquares go build -o compute compute.go
# Produces ssa.html in the current directory
```

Open `ssa.html` in a browser. The left panel lists every compilation pass: `start`, `opt`, `lower`, `regalloc`, `genssa`. Clicking each pass shows the CFG for that pass with live variable annotations. This is the canonical way to understand what the Go compiler is doing to your numeric code and to verify that bounds-check elimination (BCE) has fired for slice accesses inside loops. For `sumSquares`, the `opt` pass should show that the bounds check on `data[i]` has been eliminated because the loop condition already constrains `i` to valid range.

Run escape analysis to understand why `escapeAnalysis` causes a heap allocation:

```bash
go build -gcflags="-m=2" compute.go 2>&1
```

The `-m=2` flag produces verbose escape analysis output. You will see a line stating that `&x escapes to heap` because the function returns a pointer to a local variable. This is the Go compiler reporting that it has promoted `x` from the stack frame to the heap to extend its lifetime. Understanding this output is critical for writing allocation-free hot paths.

---

## Exercise 2: Cache Miss & Throughput Profiling

### Theory Anchor

Modern CPUs execute instructions at speeds that DRAM cannot match. A cache hit in L1 costs roughly 4 cycles; an L2 hit costs roughly 12 cycles; an L3 hit around 40 cycles; and a main memory access costs 200–300 cycles. Any hot loop that exhibits irregular memory access patterns—or that processes data structures larger than the L3 cache—will be bound not by arithmetic throughput but by memory latency. Profiling for cache behavior is therefore a prerequisite for understanding why a theoretically fast algorithm is slow in practice.

The hardware performance monitoring unit (PMU) built into every x86-64 processor can count hardware events including cache misses, branch mispredictions, TLB misses, and retired instructions. The Linux `perf` subsystem exposes these counters through a file descriptor interface. `perf stat` aggregates counters over a process lifetime; `perf record` samples the program counter at a given frequency and builds a statistical call graph.

### Part A: Perf Stat Baseline on C++

Create `cache_bench.cpp`. This program deliberately exhibits two access patterns—row-major (cache-friendly) and column-major (cache-hostile)—over the same data:

```cpp
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <cstdio>

static const size_t ROWS = 4096;
static const size_t COLS = 4096;

static float matrix[ROWS][COLS];

void fill_matrix() {
    for (size_t i = 0; i < ROWS; ++i)
        for (size_t j = 0; j < COLS; ++j)
            matrix[i][j] = static_cast<float>(i * COLS + j);
}

double sum_row_major() {
    double acc = 0.0;
    for (size_t i = 0; i < ROWS; ++i)
        for (size_t j = 0; j < COLS; ++j)
            acc += matrix[i][j];
    return acc;
}

double sum_col_major() {
    double acc = 0.0;
    for (size_t j = 0; j < COLS; ++j)
        for (size_t i = 0; i < ROWS; ++i)
            acc += matrix[i][j];
    return acc;
}

int main() {
    fill_matrix();

    auto t0 = std::chrono::high_resolution_clock::now();
    volatile double r = sum_row_major();
    auto t1 = std::chrono::high_resolution_clock::now();
    volatile double c = sum_col_major();
    auto t2 = std::chrono::high_resolution_clock::now();

    auto row_us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
    auto col_us = std::chrono::duration_cast<std::chrono::microseconds>(t2 - t1).count();

    printf("Row-major sum: %.2f  time: %ld us\n", r, row_us);
    printf("Col-major sum: %.2f  time: %ld us\n", c, col_us);
    return 0;
}
```

Compile with optimization but without auto-vectorization, so the cache effect is unconfounded by SIMD width differences:

```bash
clang++ -O2 -fno-vectorize -fno-slp-vectorize \
  -o cache_bench cache_bench.cpp
```

Run under `perf stat` with explicit hardware cache counters. The `-e` flag selects event names; `cache-misses` and `cache-references` are kernel-normalized aliases for the PMU's last-level cache events:

```bash
sudo perf stat \
  -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses,\
branch-instructions,branch-misses,instructions,cycles \
  ./cache_bench
```

The output will show two rows of interest: `L1-dcache-load-misses` will be dramatically higher for the column-major traversal because each access to `matrix[i][j]` jumps 4096×4 = 16 384 bytes forward in memory, guaranteed to miss every cache line that was just loaded. For a 4096×4096 float matrix, the working set is 64 MiB, far exceeding any L1 or L2 cache. The row-major traversal accesses consecutive 4-byte floats within the same 64-byte cache line, achieving a spatial locality ratio of 16 hits per miss.

Record the numeric difference. On a typical server-class CPU you should see the column-major variant take 5–15× longer with a cache miss rate near 100% for L1-dcache, while the row-major variant achieves a miss rate below 7%.

### Part B: cargo-flamegraph for Rust CPU Profiling

Add a CPU-intensive function to `src/lib.rs` in the `frontiers_lab` project. Replace the entire file:

```rust
use std::collections::HashMap;

#[no_mangle]
pub fn sum_squares(data: &[f64]) -> f64 {
    data.iter().map(|x| x * x).sum()
}

#[no_mangle]
pub fn conditional_accumulate(data: &[i64], threshold: i64) -> i64 {
    let mut total: i64 = 0;
    for &val in data {
        if val > threshold {
            total = total.wrapping_add(val);
        }
    }
    total
}

pub fn frequency_map(data: &[u32]) -> HashMap<u32, usize> {
    let mut map = HashMap::with_capacity(data.len() / 4);
    for &v in data {
        *map.entry(v).or_insert(0) += 1;
    }
    map
}

pub fn sieve_of_eratosthenes(limit: usize) -> Vec<usize> {
    let mut is_prime = vec![true; limit + 1];
    is_prime[0] = false;
    if limit >= 1 {
        is_prime[1] = false;
    }
    let mut i = 2;
    while i * i <= limit {
        if is_prime[i] {
            let mut j = i * i;
            while j <= limit {
                is_prime[j] = false;
                j += i;
            }
        }
        i += 1;
    }
    is_prime.iter().enumerate()
        .filter_map(|(n, &p)| if p { Some(n) } else { None })
        .collect()
}
```

Create `src/main.rs` to drive the profiling workload:

```rust
use frontiers_lab::{sum_squares, conditional_accumulate, frequency_map, sieve_of_eratosthenes};

fn main() {
    let data_f64: Vec<f64> = (0..1_000_000).map(|x| x as f64).collect();
    let data_i64: Vec<i64> = (0..1_000_000).map(|x| x as i64).collect();
    let data_u32: Vec<u32> = (0..1_000_000u32).map(|x| x % 10_000).collect();

    // Run each function many times to generate enough samples for perf
    for _ in 0..50 {
        let _ = sum_squares(&data_f64);
    }
    for _ in 0..50 {
        let _ = conditional_accumulate(&data_i64, 500_000);
    }
    for _ in 0..20 {
        let _ = frequency_map(&data_u32);
    }
    for _ in 0..10 {
        let _ = sieve_of_eratosthenes(5_000_000);
    }
}
```

Update `Cargo.toml` to include the binary and to retain debug symbols in release builds (required for meaningful flamegraphs):

```toml
[package]
name = "frontiers_lab"
version = "0.1.0"
edition = "2021"

[lib]
name = "frontiers_lab"
path = "src/lib.rs"

[[bin]]
name = "frontiers_lab"
path = "src/main.rs"

[profile.release]
debug = true
opt-level = 3

[dependencies]
```

Generate the flamegraph. cargo-flamegraph wraps `perf record` and then calls the flamegraph stack-collapsing scripts automatically:

```bash
sudo cargo flamegraph --bin frontiers_lab --root \
  -- 2>&1
# Output: flamegraph.svg in the current directory
```

Open `flamegraph.svg` in a browser. Each horizontal bar represents a function; its width is proportional to the fraction of CPU samples where that function was on the call stack. The widest bars in the flame are your bottlenecks. You should find that `sieve_of_eratosthenes` and `frequency_map` consume the majority of CPU time. Click any bar to zoom into that subtree and see which callee is responsible for the most time within it.

### Part C: Go pprof CPU and Memory Profiles

Create `profiled.go`:

```go
package main

import (
	"fmt"
	"math/rand"
	"os"
	"runtime/pprof"
	"sort"
)

func generateData(n int) []int {
	data := make([]int, n)
	for i := range data {
		data[i] = rand.Intn(1_000_000)
	}
	return data
}

func countFrequencies(data []int) map[int]int {
	freq := make(map[int]int, len(data)/10)
	for _, v := range data {
		freq[v]++
	}
	return freq
}

func topK(freq map[int]int, k int) []int {
	type pair struct {
		key, count int
	}
	pairs := make([]pair, 0, len(freq))
	for k, v := range freq {
		pairs = append(pairs, pair{k, v})
	}
	sort.Slice(pairs, func(i, j int) bool {
		return pairs[i].count > pairs[j].count
	})
	result := make([]int, 0, k)
	for i := 0; i < k && i < len(pairs); i++ {
		result = append(result, pairs[i].key)
	}
	return result
}

func main() {
	cpuFile, err := os.Create("cpu.prof")
	if err != nil {
		panic(err)
	}
	defer cpuFile.Close()

	memFile, err := os.Create("mem.prof")
	if err != nil {
		panic(err)
	}
	defer memFile.Close()

	if err := pprof.StartCPUProfile(cpuFile); err != nil {
		panic(err)
	}
	defer pprof.StopCPUProfile()

	for i := 0; i < 100; i++ {
		data := generateData(500_000)
		freq := countFrequencies(data)
		top := topK(freq, 10)
		if i == 0 {
			fmt.Println("Top-10 most frequent values:", top[:3], "...")
		}
	}

	if err := pprof.WriteHeapProfile(memFile); err != nil {
		panic(err)
	}

	fmt.Println("Profiles written: cpu.prof, mem.prof")
}
```

Build and run:

```bash
go build -o profiled profiled.go
./profiled
```

Analyze the CPU profile interactively in the pprof tool. The `-http` flag starts a local web server with a flame graph, call graph, and source annotation views:

```bash
go tool pprof -http=:8080 profiled cpu.prof
```

Navigate to `http://localhost:8080` in a browser and select the **Flame Graph** view from the View menu. You should see `sort.Slice` and the anonymous comparison closure dominating CPU time, followed by `countFrequencies`. This confirms that the `topK` sort is the primary cost per iteration, not the frequency counting.

Analyze the heap profile:

```bash
go tool pprof -http=:8081 profiled mem.prof
```

The allocation graph will show that `generateData` allocates `[]int` slices on the heap for each of the 100 iterations, and `topK` allocates a `[]pair` slice on each call. These are candidates for sync.Pool or pre-allocated buffers in a production path where allocation pressure is a concern. The heap profile quantifies allocation volume before you commit to any optimization.

---

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

### Theory Anchor

A data race occurs when two goroutines (or threads) access the same memory location concurrently, at least one access is a write, and there is no synchronizing operation between them. The result is undefined behavior. In C and C++, this is formalized by the memory model: a data race is undefined behavior with no defined outcome, meaning the compiler and hardware are both permitted to produce arbitrary results. In Go and Rust, the memory models are defined more carefully, but data races in `unsafe` Rust and unprotected Go goroutines still produce programs with unpredictable behavior. The only reliable way to detect these races is dynamic instrumentation that observes actual memory accesses at runtime—static analysis alone cannot handle them.

ThreadSanitizer (TSan) is a compiler instrumentation pass available in both Clang and rustc. It inserts shadow memory tracking around every load and store, records which thread last touched each aligned 8-byte word, and reports a race when two conflicting accesses are detected. Valgrind's Helgrind tool performs a similar analysis without recompilation by intercepting POSIX pthread calls. AddressSanitizer (ASan) detects spatial memory safety violations: buffer overflows, use-after-free, and heap corruption. LeakSanitizer (LSan) is typically bundled with ASan and reports memory that was allocated but never freed at process exit.

### Part A: ThreadSanitizer on a C++ Data Race

Create `race_demo.cpp`. This program has a deliberate, non-obvious data race: a global counter incremented from multiple threads without synchronization:

```cpp
#include <pthread.h>
#include <cstdio>
#include <cstdlib>

static long counter = 0;
static const int NUM_THREADS = 8;
static const int INCREMENTS_PER_THREAD = 100000;

struct ThreadArgs {
    int id;
};

void* increment_worker(void* arg) {
    ThreadArgs* ta = static_cast<ThreadArgs*>(arg);
    for (int i = 0; i < INCREMENTS_PER_THREAD; ++i) {
        // Data race: non-atomic read-modify-write
        counter += 1;
    }
    return nullptr;
}

int main() {
    pthread_t threads[NUM_THREADS];
    ThreadArgs args[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; ++i) {
        args[i].id = i;
        pthread_create(&threads[i], nullptr, increment_worker, &args[i]);
    }
    for (int i = 0; i < NUM_THREADS; ++i) {
        pthread_join(threads[i], nullptr);
    }

    long expected = static_cast<long>(NUM_THREADS) * INCREMENTS_PER_THREAD;
    printf("Expected: %ld  Actual: %ld  Lost: %ld\n",
           expected, counter, expected - counter);
    return 0;
}
```

First, build and run without sanitizers to observe that the race is non-deterministic and that the counter almost always ends up below the expected value due to lost updates:

```bash
clang++ -O1 -pthread -o race_demo race_demo.cpp
for i in $(seq 1 5); do ./race_demo; done
```

Now compile with TSan. TSan adds roughly 5–15× overhead in memory and CPU, which is acceptable for test harnesses but not production:

```bash
clang++ -O1 -pthread -fsanitize=thread -fno-omit-frame-pointer \
  -g -o race_demo_tsan race_demo.cpp
./race_demo_tsan
```

TSan will produce a report similar to the following (abbreviated for readability; your output will include source locations):

```text
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x... by thread T2:
    #0 increment_worker race_demo.cpp:16
    #1 <null> <null>:0

  Previous write of size 8 at 0x... by thread T1:
    #0 increment_worker race_demo.cpp:16
    #1 <null> <null>:0

  Location is global variable 'counter' at race_demo.cpp:4
==================
```

The report names the two threads, the access size (8 bytes, matching `long`), the source location, and the global variable. This is the canonical format for TSan output. Each `SUMMARY: ThreadSanitizer: N data race(s)` line at the bottom counts distinct racy access pairs.

The fix is to use `std::atomic<long>`:

```cpp
#include <atomic>
static std::atomic<long> counter{0};
// In the worker:
counter.fetch_add(1, std::memory_order_relaxed);
```

Recompile with the fix and TSan, verify the report is gone, and confirm the counter value is now exactly 800,000:

```bash
# Apply the fix inline:
sed -i 's/static long counter = 0;/static std::atomic<long> counter{0};/' race_demo.cpp
sed -i 's/counter += 1;/counter.fetch_add(1, std::memory_order_relaxed);/' race_demo.cpp
sed -i '1a #include <atomic>' race_demo.cpp

clang++ -O1 -pthread -fsanitize=thread -fno-omit-frame-pointer \
  -g -o race_demo_fixed race_demo.cpp
./race_demo_fixed
```

### Part B: AddressSanitizer and LeakSanitizer on C++

Create `asan_demo.cpp` with three distinct memory errors that ASan is designed to catch—a stack buffer overflow, a heap use-after-free, and a memory leak:

```cpp
#include <cstdlib>
#include <cstring>
#include <cstdio>

void stack_overflow_demo() {
    char buf[16];
    // Write 4 bytes past the end of the buffer
    memset(buf, 'A', 20);
    printf("Stack buffer (should not reach here): %c\n", buf[0]);
}

void use_after_free_demo() {
    int* p = static_cast<int*>(malloc(sizeof(int) * 4));
    p[0] = 42;
    free(p);
    // Access after free: undefined behavior
    printf("UAF read (should not reach here): %d\n", p[1]);
}

void leak_demo() {
    char* leak = static_cast<char*>(malloc(1024));
    snprintf(leak, 1024, "this memory is never freed");
    // Intentionally do NOT free 'leak'
    printf("Leaked buffer contains: %.10s...\n", leak);
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s [overflow|uaf|leak]\n", argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "overflow") == 0) stack_overflow_demo();
    else if (strcmp(argv[1], "uaf") == 0)  use_after_free_demo();
    else if (strcmp(argv[1], "leak") == 0) leak_demo();
    return 0;
}
```

Compile with ASan and LSan (LSan is automatically enabled as part of ASan on Linux) and full debug symbols:

```bash
clang++ -O1 -fsanitize=address -fno-omit-frame-pointer \
  -g -o asan_demo asan_demo.cpp
```

Trigger each error type in turn and read the reports:

```bash
./asan_demo overflow
./asan_demo uaf
./asan_demo leak
```

For the stack overflow, ASan will print a `stack-buffer-overflow` report showing the access address, the shadow memory byte state (indicating the redzone after the buffer), the write size, and the full stack trace. The shadow memory byte `f2` indicates a stack right redzone—ASan places poisoned redzone bytes around stack allocations and checks them on every access.

For the use-after-free, the report will include two stack traces: the allocation site and the deallocation site in addition to the access site. This is the most valuable information when debugging heap corruption in production—knowing where the object was freed is usually more useful than knowing where it was incorrectly accessed.

For the leak, the LSan report appears at process exit and identifies the allocation site with a full stack trace. Set the `ASAN_OPTIONS` environment variable to control behavior:

```bash
ASAN_OPTIONS=detect_leaks=1:leak_check_at_exit=1 ./asan_demo leak
```

### Part C: Rust ThreadSanitizer via LLVM

Rust's ownership model eliminates data races in safe code by construction: the type system prevents two `&mut T` references from existing to the same location simultaneously, and sharing data across threads requires wrapping it in `Arc<Mutex<T>>` or using atomic types. However, `unsafe` Rust code can still introduce races, as can FFI boundaries. ThreadSanitizer is available on the nightly toolchain:

Create `src/bin/tsan_demo.rs`:

```rust
use std::thread;

static mut SHARED_COUNTER: i64 = 0;

fn main() {
    let mut handles = Vec::new();

    for _ in 0..4 {
        let h = thread::spawn(|| {
            for _ in 0..100_000 {
                unsafe {
                    // Data race: non-atomic access to static mut
                    SHARED_COUNTER += 1;
                }
            }
        });
        handles.push(h);
    }

    for h in handles {
        h.join().unwrap();
    }

    unsafe {
        println!("Counter: {}", SHARED_COUNTER);
    }
}
```

Add to `Cargo.toml`:

```toml
[[bin]]
name = "tsan_demo"
path = "src/bin/tsan_demo.rs"
```

Compile and run with TSan using the nightly toolchain's `-Z sanitizer` flag:

```bash
RUSTFLAGS="-Z sanitizer=thread" \
  cargo +nightly run --bin tsan_demo --target x86_64-unknown-linux-gnu 2>&1
```

The output will contain a TSan data race report identical in format to the C++ report above, naming the `SHARED_COUNTER` symbol and the two conflicting threads. This confirms that TSan operates on Rust programs through the same LLVM instrumentation infrastructure.

The correct Rust solution replaces `static mut` with `std::sync::atomic::AtomicI64`:

```rust
use std::sync::atomic::{AtomicI64, Ordering};
use std::thread;

static SHARED_COUNTER: AtomicI64 = AtomicI64::new(0);

fn main() {
    let mut handles = Vec::new();
    for _ in 0..4 {
        let h = thread::spawn(|| {
            for _ in 0..100_000 {
                SHARED_COUNTER.fetch_add(1, Ordering::Relaxed);
            }
        });
        handles.push(h);
    }
    for h in handles { h.join().unwrap(); }
    println!("Counter: {}", SHARED_COUNTER.load(Ordering::SeqCst));
}
```

Rerunning under TSan with this fix should produce no race reports and a counter of exactly 400,000.

### Part D: Valgrind Memcheck for Deep Heap Analysis

Valgrind's Memcheck operates at a different level from ASan. Where ASan uses compile-time instrumentation and shadow memory at the application level, Memcheck runs the entire program inside a software-emulated CPU (the Valgrind JIT), intercepting every memory operation. This makes it roughly 20–50× slower than native execution but capable of catching errors that ASan misses, including use of uninitialized memory and errors in programs not compiled with ASan.

Create `valgrind_demo.c`:

```c
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int sum_uninitialized(int n) {
    int* arr = malloc(n * sizeof(int));
    // Intentionally skip initializing arr
    int s = 0;
    for (int i = 0; i < n; ++i) s += arr[i];
    free(arr);
    return s;
}

char* build_string() {
    char* buf = malloc(10);
    strcpy(buf, "hello");
    return buf;  // Caller must free; we will forget to.
}

int main() {
    printf("Uninitialized sum: %d\n", sum_uninitialized(5));
    char* s = build_string();
    printf("String: %s\n", s);
    // Forget to free s — Memcheck will report this.
    return 0;
}
```

Compile with debug symbols but without ASan (Memcheck and ASan are mutually exclusive):

```bash
gcc -g -O0 -o valgrind_demo valgrind_demo.c
valgrind --tool=memcheck \
         --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         ./valgrind_demo 2>&1 | tee valgrind_output.txt
less valgrind_output.txt
```

The `--track-origins=yes` flag is critical. Without it, Memcheck reports that an uninitialized value was used but cannot tell you where it was allocated. With it, the report will include a `Uninitialised value was created by a heap allocation` annotation pointing directly to the `malloc` call in `sum_uninitialized`. The leak summary at the end will categorize the unreachable `build_string` allocation as `definitely lost`, which is the most actionable category—it means no pointer to that memory exists anywhere at process exit.

---

## Developer Cheat Sheet & Toolchain Checklist

The following reference consolidates every tool and flag used across all three exercises. These are the commands you should reach for first when encountering each class of problem.

### Compiler IR and Disassembly

| Goal | Command |
|---|---|
| Clang AST dump | `clang++ -Xclang -ast-dump -fsyntax-only file.cpp` |
| Clang unoptimized LLVM IR | `clang++ -O0 -S -emit-llvm -o out.ll file.cpp` |
| Clang optimized IR with vectorization remarks | `clang++ -O3 -march=native -S -emit-llvm -Rpass=loop-vectorize -o out.ll file.cpp` |
| Disassemble object (Intel syntax) | `llvm-objdump -d --x86-asm-syntax=intel file.o` |
| Rust MIR emission | `RUSTFLAGS="--emit=mir" cargo build --release` |
| Rust LLVM IR emission | `rustc --edition 2021 -C opt-level=3 --emit=llvm-ir -o out.ll src/lib.rs` |
| Go SSA dump for a named function | `GOSSAFUNC=funcName go build -o binary file.go` |
| Go escape analysis (verbose) | `go build -gcflags="-m=2" file.go` |

### Cache and CPU Profiling

| Goal | Command |
|---|---|
| Hardware counter summary | `sudo perf stat -e cache-references,cache-misses,instructions,cycles ./binary` |
| Sampling profile (1000 Hz, call graph) | `sudo perf record -F 1000 -g ./binary && sudo perf report` |
| Rust flamegraph | `sudo cargo flamegraph --bin name --root` |
| Go CPU profile + web UI | `go tool pprof -http=:8080 binary cpu.prof` |
| Go heap profile + web UI | `go tool pprof -http=:8081 binary mem.prof` |

### Sanitizers

| Goal | Command |
|---|---|
| C++ ThreadSanitizer | `clang++ -O1 -pthread -fsanitize=thread -fno-omit-frame-pointer -g` |
| C++ AddressSanitizer + LSan | `clang++ -O1 -fsanitize=address -fno-omit-frame-pointer -g` |
| Enable leak detection at exit | `ASAN_OPTIONS=detect_leaks=1:leak_check_at_exit=1 ./binary` |
| Rust ThreadSanitizer (nightly) | `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly run --target x86_64-unknown-linux-gnu` |
| Rust AddressSanitizer (nightly) | `RUSTFLAGS="-Z sanitizer=address" cargo +nightly run --target x86_64-unknown-linux-gnu` |
| Valgrind Memcheck with origin tracking | `valgrind --tool=memcheck --leak-check=full --track-origins=yes ./binary` |
| Valgrind Helgrind (thread errors) | `valgrind --tool=helgrind ./binary` |

### Cargo Verification Commands

| Goal | Command |
|---|---|
| Type-check without linking | `cargo check` |
| Run all tests | `cargo test` |
| Run tests with output shown | `cargo test -- --nocapture` |
| Benchmarks (nightly, criterion) | `cargo bench` |
| Clippy lint pass | `cargo clippy -- -D warnings` |
| Miri (undefined behavior interpreter) | `cargo +nightly miri run` |

### Toolchain Validation Checklist

Before beginning any profiling or sanitizer session, verify these preconditions. Misconfigured toolchains produce silent failures—ASan attached to a binary compiled without `-fno-omit-frame-pointer` produces unresolvable stack traces; `perf record` on a system with `/proc/sys/kernel/perf_event_paranoid` set to 3 will silently record no samples.

Execute the following checklist in a fresh terminal before each lab session:

```bash
# 1. Confirm frame pointer is preserved (required for perf and flamegraphs)
clang++ --version | grep -o 'clang version [0-9.]*'

# 2. Allow perf sampling without root (set paranoia to 1 for the session)
sudo sh -c 'echo 1 > /proc/sys/kernel/perf_event_paranoid'

# 3. Confirm Rust nightly is available for sanitizer flags
rustup show | grep nightly

# 4. Confirm Valgrind can execute a trivial binary
echo 'int main(){}' > /tmp/t.c && gcc -g -o /tmp/t /tmp/t.c
valgrind --error-exitcode=1 /tmp/t && echo "Valgrind OK"

# 5. Confirm Go pprof binary is present
go tool pprof -help 2>&1 | head -1

# 6. Confirm cargo-flamegraph has perf access
cargo flamegraph --help 2>&1 | head -1
```

All six checks should produce output without errors. If the nightly check fails, run `rustup install nightly`. If Valgrind fails, the binary or library is incompatible with the installed Valgrind version—verify with `valgrind --version` that you have at least 3.19.0 for glibc 2.35+ compatibility. If `perf_event_paranoid` cannot be set, run all `perf` and `cargo flamegraph` commands with `sudo`.

The discipline these labs establish—examining what the compiler actually produced rather than what you believe you wrote, measuring where time is actually spent rather than where you believe it goes, and using instrumentation to surface races and leaks before they reach production—is the foundation of professional systems software engineering. Each tool in this chain is a falsifier: it disproves the assumption that your code behaves the way you intended it to.
