# Operational Verification Labs: Software Testing

## Objective & Toolchain Setup

Software testing in production systems engineering extends far beyond unit test assertions and integration smoke tests. The discipline demands operational verification through compiler intermediate representations, memory sanitizers, concurrency stress harnesses, and CPU cache performance profiling. This laboratory guide trains the hands-on software engineer to diagnose undefined behavior, data races, memory leaks, and performance bottlenecks using the production toolchain that ships with modern compilers and language runtimes. We ground every technique in the underlying system architecture—virtual memory mappings, CPU cache hierarchies, LLVM optimization passes, and kernel scheduler preemption—while maintaining an 80% focus on executable commands, runnable code, and repeatable diagnostic procedures.

The toolchain we deploy spans three industrial-grade languages and their native ecosystems. Rust provides memory safety guarantees through its borrow checker and offers first-class sanitizer integration via LLVM. C++ exposes low-level system primitives and remains the lingua franca of performance-critical infrastructure, from database engines to network protocol stacks. Go delivers goroutine-based concurrency with a runtime race detector and straightforward profiling instrumentation. Each language brings unique verification capabilities: Rust's compile-time ownership analysis, C++'s Valgrind heap tracing, and Go's built-in race detector. We exploit all three ecosystems to build a comprehensive operational verification practice.

Begin by establishing the complete toolchain on a Linux or macOS development workstation. Install Rust via `rustup`, which provides the stable compiler (`rustc`), package manager (`cargo`), and standard library. Ensure the `llvm-tools-preview` component is available for MIR and LLVM IR inspection. Install the Clang/LLVM suite for C++ development, including `clang++`, `lldb`, and the LLVM symbolizer required by AddressSanitizer and ThreadSanitizer. On Debian-derived systems, install `valgrind` for heap profiling and `linux-perf` (the `perf` command) for CPU event sampling. On macOS, install Xcode Command Line Tools for `lldb` and use Homebrew to install `valgrind` (though with limited support) or rely on Instruments for profiling. Verify Go installation via `go version`, ensuring at least Go 1.20 for modern race detector capabilities. Install `cargo-flamegraph` for CPU profiling via `cargo install flamegraph`, which wraps `perf` and generates interactive SVG flame graphs. Install `cargo-asm` and `cargo-expand` for inspecting generated assembly and macro expansions. This complete setup enables every diagnostic technique in the laboratories that follow.

Confirm toolchain readiness by running these verification commands. Execute `rustc --version` and ensure output matches a recent stable release. Run `cargo --version` to verify the build system. Check LLVM tools via `rustc --print sysroot` and confirm the presence of `lib/rustlib/x86_64-unknown-linux-gnu/bin/llvm-objdump` or equivalent. For C++, run `clang++ --version` and confirm LLVM-based compilation. Test sanitizer availability via `clang++ -fsanitize=address,undefined -o /dev/null -x c++ - <<< 'int main(){}'` and verify no errors. Check Valgrind with `valgrind --version`. Verify Go race detection via `go version` and `go build -race`. Install the `perf` kernel subsystem if on Linux by running `perf list` and confirming event output. On macOS, verify Instruments or `sample` command availability. With this verified toolchain, every exercise in this guide becomes directly executable without dependency resolution or environment troubleshooting.

Understanding the verification stack requires grounding in the compiler pipeline architecture. Modern compilers transform source code through multiple intermediate representations before emitting machine code. Rust compilation flows from source text through lexical analysis and parsing into an abstract syntax tree (AST), then lowers to high-level intermediate representation (HIR), mid-level intermediate representation (MIR), and finally LLVM IR before LLVM optimization passes generate machine code. Each stage exposes different classes of defects: the borrow checker operates on MIR to enforce ownership rules, LLVM sanitizers instrument IR to detect memory corruption, and the CPU executes machine code that reveals cache misses and branch mispredictions. C++ follows a similar path through Clang's AST and LLVM IR. Go compiles through its own SSA-based intermediate representation and runtime integration. By inspecting these layers, we diagnose problems at their architectural origin rather than chasing symptoms in debugger stack traces.

Memory sanitizers leverage compile-time instrumentation to detect undefined behavior that would otherwise corrupt program state silently until a distant crash. AddressSanitizer (ASan) instruments every memory access with shadow memory checks, detecting heap and stack buffer overflows, use-after-free, use-after-return, and double-free errors. ThreadSanitizer (TSan) records memory access ordering and detects data races through happens-before analysis. UndefinedBehaviorSanitizer (UBSan) instruments arithmetic operations, pointer casts, and object lifetime to catch signed integer overflow, null pointer dereference, and alignment violations. LeakSanitizer (LSan) tracks heap allocations and detects memory leaks at process exit. Each sanitizer imposes runtime overhead—ASan incurs 2× slowdown, TSan 5-15× slowdown—but catches bugs that no static analysis or traditional debugging can find. Production verification workflows run sanitizers in CI pipelines on every commit, trading CPU time for correctness guarantees.

Profiling tools expose performance bottlenecks through hardware performance counters and statistical sampling. The Linux `perf` subsystem reads CPU performance monitoring units (PMUs) to count cache misses, branch mispredictions, TLB misses, and cycle stalls. Sampling profilers like `perf record` interrupt the program periodically and capture call stacks, building a statistical profile of where CPU time is spent. Flame graphs visualize these profiles as hierarchical call trees, where bar width represents time spent. Intel VTune and AMD μProf provide hardware vendor-specific profiling with deeper PMU integration. Rust's `cargo-flamegraph` wraps `perf` to generate flame graphs directly from `cargo` commands. Go's `pprof` provides built-in CPU and heap profiling with interactive web visualizations. These tools transform vague performance complaints into precise cache miss counts and hot function identifications, enabling targeted optimization with measurable results.

Concurrency testing demands stress harnesses that amplify race conditions through high thread counts and preemption. A data race occurs when two threads access the same memory location concurrently with at least one write and no synchronization. Races are non-deterministic: they manifest sporadically depending on scheduler timing. Effective race detection combines static analysis (Rust's borrow checker), dynamic instrumentation (TSan's happens-before tracking), and stress testing (spawning hundreds of threads to increase collision probability). Go's race detector instruments goroutine memory accesses and detects races during normal execution. Rust prevents most races at compile time but cannot catch races in `unsafe` code or across FFI boundaries. C++ relies entirely on runtime detection via TSan. Verification labs must construct pathological test cases—tight loops, shared counters, unlocked data structures—that force races to surface reliably under instrumentation.

The laboratories that follow progress from compile-time analysis to runtime profiling to concurrency stress testing. Exercise 1 dissects compiler intermediate representations to understand optimization passes, inlining decisions, and code generation. Exercise 2 profiles cache behavior and CPU throughput to diagnose performance pathologies and validate optimization impact. Exercise 3 constructs data race stress tests and deploys LeakSanitizer to verify memory hygiene. Each exercise provides complete, executable code with zero placeholders, exact command invocations with all flags, and expected output interpretation. The developer cheat sheet consolidates the entire toolchain into a reference card for daily verification workflows. Mastery of these techniques transforms testing from an afterthought into a first-class engineering discipline grounded in compiler internals, CPU architecture, and operating system primitives.

## Exercise 1: AST, IR & Disassembly Analysis

Understanding what the compiler actually generates from your source code is foundational to diagnosing performance issues, verifying optimization effectiveness, and detecting subtle bugs introduced by aggressive compiler transformations. Modern compilers perform dozens of optimization passes—inlining, loop unrolling, constant propagation, dead code elimination, vectorization—and the only way to confirm their behavior is to inspect the intermediate representations and final assembly. This exercise walks through Rust's HIR and MIR, LLVM IR, and disassembly to observe how high-level constructs lower into machine instructions. We construct a non-trivial example with branching, heap allocation, and function calls to expose interesting optimization decisions.

Begin by creating a new Rust project that implements a simple hash table probe sequence. The code intentionally includes bounds checking, dynamic allocation, and conditional branches to produce rich IR worth analyzing. Create the project via `cargo new --bin ir-analysis && cd ir-analysis`. Open `src/main.rs` and replace the contents with the following complete implementation:

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone)]
struct Entry {
    key: u64,
    value: String,
    occupied: bool,
}

impl Entry {
    fn new() -> Self {
        Entry {
            key: 0,
            value: String::new(),
            occupied: false,
        }
    }
    
    fn set(&mut self, key: u64, value: String) {
        self.key = key;
        self.value = value;
        self.occupied = true;
    }
}

struct HashTable {
    buckets: Vec<Entry>,
    size: usize,
}

impl HashTable {
    fn new(capacity: usize) -> Self {
        let mut buckets = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            buckets.push(Entry::new());
        }
        HashTable { buckets, size: 0 }
    }
    
    fn hash_key(key: u64) -> u64 {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish()
    }
    
    fn insert(&mut self, key: u64, value: String) -> bool {
        let hash = Self::hash_key(key);
        let capacity = self.buckets.len();
        let mut index = (hash % capacity as u64) as usize;
        let start_index = index;
        
        loop {
            if !self.buckets[index].occupied {
                self.buckets[index].set(key, value);
                self.size += 1;
                return true;
            }
            
            if self.buckets[index].key == key {
                self.buckets[index].value = value;
                return false;
            }
            
            index = (index + 1) % capacity;
            if index == start_index {
                return false;
            }
        }
    }
    
    fn get(&self, key: u64) -> Option<&String> {
        let hash = Self::hash_key(key);
        let capacity = self.buckets.len();
        let mut index = (hash % capacity as u64) as usize;
        let start_index = index;
        
        loop {
            if !self.buckets[index].occupied {
                return None;
            }
            
            if self.buckets[index].key == key {
                return Some(&self.buckets[index].value);
            }
            
            index = (index + 1) % capacity;
            if index == start_index {
                return None;
            }
        }
    }
}

fn main() {
    let mut table = HashTable::new(16);
    
    for i in 0..10 {
        table.insert(i, format!("value_{}", i));
    }
    
    for i in 0..10 {
        match table.get(i) {
            Some(v) => println!("Key {}: {}", i, v),
            None => println!("Key {} not found", i),
        }
    }
    
    println!("Final size: {}", table.size);
}
```

This implementation provides enough complexity to generate interesting IR: vector allocation, bounds checking, conditional branches, string formatting, and loop structures. The hash table uses linear probing for collision resolution, which creates a loop with multiple exit conditions that the optimizer must analyze.

Compile the program in release mode to observe production optimization levels. Run `cargo build --release` and confirm successful compilation. The release profile enables LLVM's optimization level 3, which performs aggressive inlining, loop transformations, and vectorization. Now inspect the MIR, which is Rust's mid-level intermediate representation after borrow checking but before LLVM translation. Execute `cargo rustc --release -- --emit=mir` and examine the generated MIR files in `target/release/deps/`. Find the file matching your crate name with a `.mir` extension, typically `ir_analysis-<hash>.mir`. Open this file in a text editor.

The MIR representation exposes the control flow graph explicitly. Search for the `fn insert` function definition. You will observe a series of basic blocks labeled `bb0`, `bb1`, etc., each containing a sequence of statements followed by a terminator (branch, return, or switch). Notice how the loop in the `insert` function translates into a cycle in the control flow graph with multiple back edges. The MIR shows bounds checks explicitly as `assert` statements before array indexing. In release mode, LLVM may eliminate some of these checks through range analysis, but they remain visible in MIR. Observe how the `String` allocation (`String::new()` and `format!`) lowers into calls to allocator functions. This is where Rust's zero-cost abstractions become concrete: the high-level `Vec` and `String` types compile down to raw pointer arithmetic and allocator calls.

Next, examine the LLVM IR to observe how MIR lowers into LLVM's intermediate form. Run `cargo rustc --release -- --emit=llvm-ir` and find the corresponding `.ll` file in `target/release/deps/`. Open this file and search for the mangled name of the `insert` function. LLVM IR uses SSA (static single assignment) form where each virtual register is assigned exactly once. You will see instructions like `%3 = load i64, i64* %2, align 8` and `br i1 %5, label %6, label %7`. The IR shows explicit pointer arithmetic for vector indexing, including the stride calculation for `Entry` struct offsets. Notice how LLVM represents the loop: a `phi` node merges the loop index from multiple incoming edges, and a conditional branch tests the loop exit condition.

Compare the MIR and LLVM IR to understand the lowering process. In MIR, you see Rust-level constructs like `_3 = &(*_2)[_4]` for indexing. In LLVM IR, this becomes `%5 = getelementptr inbounds %Entry, %Entry* %4, i64 %index`, which computes the pointer address explicitly. The LLVM IR also exposes inlining decisions: small functions like `Entry::new` may be inlined directly into their call sites, eliminating function call overhead. To verify this, search for calls to `Entry::new` in the LLVM IR—if the function is inlined, you will see its body copied into the caller rather than a `call` instruction.

Now inspect the final assembly to observe the machine code output. Run `cargo rustc --release -- --emit=asm` and find the `.s` file in `target/release/deps/`. Open this file and search for the `insert` function's assembly. You will see x86-64 instructions like `movq`, `addq`, `cmpq`, and `jne` (jump if not equal). The assembly reveals the register allocation chosen by LLVM's register allocator: frequently accessed variables like the loop index may reside in registers (`%rax`, `%rcx`) while others spill to the stack. Observe the loop structure: a label marking the loop head, a sequence of instructions performing the hash table probe, and a conditional jump back to the loop head.

To make assembly inspection more convenient, install `cargo-asm`, which provides a user-friendly interface for viewing generated assembly. Run `cargo install cargo-asm`, then execute `cargo asm --release ir_analysis::HashTable::insert`. This command disassembles the `insert` function and displays annotated assembly with source line mappings. The output shows which assembly instructions correspond to which source lines, making it easy to identify expensive operations. Look for the bounds check: it may compile to a `cmp` instruction followed by a conditional jump to a panic handler. In optimized code, LLVM often eliminates redundant bounds checks through range analysis, so you may see fewer checks than you wrote explicitly.

Compare debug and release builds to observe optimization impact. Run `cargo build` (without `--release`) to compile with minimal optimizations, then generate assembly via `cargo rustc -- --emit=asm`. Compare the debug assembly to the release assembly. Debug builds retain all bounds checks, avoid inlining, and preserve function call overhead. Release builds eliminate redundant checks, inline aggressively, and reorder instructions for better CPU pipeline utilization. The size difference is dramatic: release assembly is often 3-5× smaller than debug assembly for the same function. This exercise demonstrates why profiling must always use release builds—debug performance characteristics do not reflect production behavior.

Extend the analysis by adding a CPU-intensive function and observing vectorization. Append the following function to `src/main.rs`:

```rust
pub fn sum_array(data: &[i32]) -> i32 {
    let mut sum = 0i32;
    for &value in data {
        sum = sum.wrapping_add(value);
    }
    sum
}
```

Recompile with `cargo build --release` and inspect the assembly for `sum_array` via `cargo asm --release ir_analysis::sum_array`. On x86-64 with AVX2 support, LLVM may vectorize this loop using SIMD instructions like `vpaddd` (vector packed add). The assembly will show the loop processing 4 or 8 integers per iteration using 128-bit or 256-bit vector registers (`%xmm0`, `%ymm0`). If you do not see vectorization, check the target CPU features via `rustc --print target-cpus` and recompile with `RUSTFLAGS="-C target-cpu=native" cargo build --release` to enable native CPU instructions. Vectorization is one of LLVM's most powerful optimizations, and observing it in the assembly confirms the compiler is exploiting data parallelism.

To observe inlining decisions explicitly, use the inline attribute and compare outputs. Modify the `hash_key` function to disable inlining:

```rust
#[inline(never)]
fn hash_key(key: u64) -> u64 {
    let mut hasher = DefaultHasher::new();
    key.hash(&mut hasher);
    hasher.finish()
}
```

Recompile and inspect the `insert` function's assembly. You will now see a `call` instruction invoking `hash_key` rather than the function body inlined. Remove `#[inline(never)]` and recompile to restore inlining. The performance difference is measurable: function call overhead on x86-64 is roughly 2-5 nanoseconds, which accumulates significantly in tight loops. This technique lets you verify that critical functions are inlined as expected.

Finally, inspect optimization remarks to understand what the compiler did and why. LLVM can emit human-readable remarks explaining optimization decisions. Run `RUSTFLAGS="-C llvm-args=-pass-remarks=inline" cargo build --release 2>&1 | grep inline` to see which functions LLVM inlined and why. You will see output like `remark: <unknown>:0:0: 'ir_analysis::HashTable::hash_key' inlined into 'ir_analysis::HashTable::insert' with (cost=45, threshold=325)`. The cost-benefit analysis determines whether inlining is profitable based on function size and call frequency. To see all optimization remarks, use `-pass-remarks=.*`, but this generates voluminous output. Focus on `inline`, `loop-vectorize`, and `loop-unroll` for the most actionable insights.

This exercise establishes the foundational skill of reading compiler output to verify assumptions about code generation. When performance profiling reveals a hot function, inspecting its assembly often immediately reveals the problem: a missing vectorization, an unexpected function call, or redundant bounds checks. This diagnostic capability is essential for low-level performance work and distinguishes proficient systems programmers from those who treat the compiler as a black box.

## Exercise 2: Cache Miss & Throughput Profiling

CPU performance in modern systems is dominated by memory hierarchy latency rather than raw instruction throughput. A cache miss to DRAM incurs 50-200 nanoseconds of latency, during which the CPU stalls or speculatively executes unrelated work. A TLB miss adds another 10-30 nanoseconds. In contrast, an L1 cache hit takes 1-2 nanoseconds, and arithmetic operations complete in fractions of a nanosecond. This 100× latency gap means that memory access patterns—sequential vs. random, cache-friendly vs. cache-hostile—determine throughput far more than algorithmic complexity for many workloads. This exercise profiles cache behavior using hardware performance counters, constructs pathological access patterns to demonstrate cache effects, and optimizes memory layout to reduce misses.

The Linux `perf` subsystem provides access to CPU performance monitoring units (PMUs) that count hardware events like cache references, cache misses, branch mispredictions, and cycle stalls. These counters are sampled by the CPU with negligible overhead, making them suitable for production profiling. We will use `perf stat` to count events and `perf record` combined with `cargo-flamegraph` to generate call stack profiles. On macOS, the closest equivalent is Instruments or the `sample` command, though with less granular PMU access. Windows users can substitute Intel VTune or AMD μProf.

Create a new Rust project to benchmark cache-sensitive operations. Run `cargo new --bin cache-profiling && cd cache-profiling`. Add the `rand` crate for random number generation by editing `Cargo.toml`:

```toml
[package]
name = "cache-profiling"
version = "0.1.0"
edition = "2021"

[dependencies]
rand = "0.8"

[profile.release]
debug = true
```

The `debug = true` setting preserves debug symbols in release builds, enabling `perf` to map instruction addresses back to source lines. Now implement a benchmark that demonstrates cache effects through array traversal. Replace `src/main.rs` with:

```rust
use rand::prelude::*;
use std::time::Instant;

const ARRAY_SIZE: usize = 64 * 1024 * 1024; // 64M elements = 256MB
const ITERATIONS: usize = 100_000_000;

fn sequential_access(data: &[u32]) -> u64 {
    let mut sum = 0u64;
    let len = data.len();
    for _ in 0..ITERATIONS {
        let index = (sum as usize) % len;
        sum = sum.wrapping_add(data[index] as u64);
    }
    sum
}

fn random_access(data: &[u32], indices: &[usize]) -> u64 {
    let mut sum = 0u64;
    for &index in indices {
        sum = sum.wrapping_add(data[index] as u64);
    }
    sum
}

fn strided_access(data: &[u32], stride: usize) -> u64 {
    let mut sum = 0u64;
    let len = data.len();
    let mut index = 0;
    for _ in 0..ITERATIONS {
        sum = sum.wrapping_add(data[index] as u64);
        index = (index + stride) % len;
    }
    sum
}

struct Node {
    value: u64,
    next: Option<Box<Node>>,
    padding: [u64; 6], // Cache line padding
}

impl Node {
    fn new(value: u64) -> Box<Node> {
        Box::new(Node {
            value,
            next: None,
            padding: [0; 6],
        })
    }
}

fn linked_list_traversal(head: &Node) -> u64 {
    let mut sum = 0u64;
    let mut current = head;
    for _ in 0..ITERATIONS {
        sum = sum.wrapping_add(current.value);
        current = match &current.next {
            Some(node) => node,
            None => head,
        };
    }
    sum
}

fn build_linked_list(size: usize) -> Box<Node> {
    let mut head = Node::new(0);
    let mut current = &mut head;
    
    for i in 1..size {
        current.next = Some(Node::new(i as u64));
        current = current.next.as_mut().unwrap();
    }
    
    head
}

fn main() {
    println!("Initializing test data...");
    let mut data: Vec<u32> = (0..ARRAY_SIZE as u32).collect();
    let mut rng = StdRng::seed_from_u64(42);
    let mut indices: Vec<usize> = (0..ITERATIONS).map(|_| rng.gen_range(0..ARRAY_SIZE)).collect();
    
    println!("\n=== Sequential Access (Cache-Friendly) ===");
    let start = Instant::now();
    let result = sequential_access(&data);
    let duration = start.elapsed();
    println!("Result: {}", result);
    println!("Time: {:.2?}", duration);
    println!("Throughput: {:.2} M accesses/sec", ITERATIONS as f64 / duration.as_secs_f64() / 1e6);
    
    println!("\n=== Random Access (Cache-Hostile) ===");
    let start = Instant::now();
    let result = random_access(&data, &indices);
    let duration = start.elapsed();
    println!("Result: {}", result);
    println!("Time: {:.2?}", duration);
    println!("Throughput: {:.2} M accesses/sec", ITERATIONS as f64 / duration.as_secs_f64() / 1e6);
    
    println!("\n=== Strided Access (stride=1, Sequential) ===");
    let start = Instant::now();
    let result = strided_access(&data, 1);
    let duration = start.elapsed();
    println!("Result: {}", result);
    println!("Time: {:.2?}", duration);
    println!("Throughput: {:.2} M accesses/sec", ITERATIONS as f64 / duration.as_secs_f64() / 1e6);
    
    println!("\n=== Strided Access (stride=16, Moderate) ===");
    let start = Instant::now();
    let result = strided_access(&data, 16);
    let duration = start.elapsed();
    println!("Result: {}", result);
    println!("Time: {:.2?}", duration);
    println!("Throughput: {:.2} M accesses/sec", ITERATIONS as f64 / duration.as_secs_f64() / 1e6);
    
    println!("\n=== Strided Access (stride=4096, Page Boundary) ===");
    let start = Instant::now();
    let result = strided_access(&data, 4096);
    let duration = start.elapsed();
    println!("Result: {}", result);
    println!("Time: {:.2?}", duration);
    println!("Throughput: {:.2} M accesses/sec", ITERATIONS as f64 / duration.as_secs_f64() / 1e6);
    
    println!("\n=== Linked List Traversal (Pointer Chasing) ===");
    println!("Building linked list...");
    let list_size = 100000;
    let head = build_linked_list(list_size);
    let start = Instant::now();
    let result = linked_list_traversal(&head);
    let duration = start.elapsed();
    println!("Result: {}", result);
    println!("Time: {:.2?}", duration);
    println!("Throughput: {:.2} M accesses/sec", ITERATIONS as f64 / duration.as_secs_f64() / 1e6);
}
```

This benchmark constructs five access patterns with dramatically different cache behavior. Sequential access traverses the array linearly, exploiting CPU prefetchers that detect the pattern and stream cache lines ahead of demand. Random access defeats prefetching entirely, causing a cache miss on nearly every access. Strided access with small strides (1, 16) benefits from spatial locality within cache lines (typically 64 bytes). Strided access with large strides (4096 elements = 16KB) jumps between memory pages, stressing the TLB. Linked list traversal forces pointer chasing, where each load depends on the previous load's result, serializing execution and preventing prefetching.

Compile and run the benchmark to observe baseline performance. Execute `cargo build --release && ./target/release/cache-profiling`. On a modern x86-64 CPU with DDR4 memory, expect sequential access to achieve 300-500 million accesses per second, while random access drops to 10-30 million accesses per second—a 10-30× slowdown. Strided access performance degrades as stride increases. Linked list traversal performs similarly to random access because each node allocation is scattered in the heap, causing cache misses.

Now profile cache behavior using `perf stat` to count hardware events. Run the benchmark under `perf stat` with cache event counters:

```bash
perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses ./target/release/cache-profiling
```

The output displays event counts for the entire program execution. Key metrics include instructions per cycle (IPC), cache miss rate, and L1 data cache miss rate. High IPC (>2.0) indicates good CPU utilization, while low IPC (< 0.5) suggests memory stalls. Cache miss rate above 10% is pathological for sequential workloads but expected for random access. The `cache-misses` counter tracks last-level cache (LLC) misses—typically L3 on modern Intel and AMD CPUs—which incur the longest latency.

Interpret the output by comparing sequential and random access phases. During sequential access, expect low cache miss rates (< 1%) and high IPC (>2.5), indicating efficient execution. During random access, cache miss rates spike to 30-70%, and IPC drops below 0.5, showing the CPU is stalled waiting for memory. The strided access phases demonstrate how stride size affects cache efficiency: small strides remain cache-friendly, while large strides thrash the cache.

To profile at function granularity, use `perf record` to sample call stacks and generate a flame graph. Run:

```bash
cargo flamegraph --release -- 
```

This command wraps `perf record` and `perf script`, then generates an interactive SVG flame graph in `flamegraph.svg`. Open this file in a web browser. The flame graph displays the call stack hierarchy with bar widths proportional to CPU time. Hover over bars to see function names and percentages. The bottom of the graph shows `main`, with branches upward representing called functions. Wide bars indicate hot functions consuming significant CPU time.

In the flame graph for this benchmark, you will see five distinct plateaus corresponding to the five access pattern tests. The sequential access phase shows a wide bar for `sequential_access`, indicating it runs efficiently without deep call stacks or excessive branching. The random access phase also shows a wide bar for `random_access`, but with lower overall height (fewer samples collected in the same wall-clock time) due to memory stalls. The linked list traversal phase shows the deepest stack with overhead from heap allocation and pointer indirection.

Flame graphs excel at identifying unexpected overhead. If you see significant time in allocator functions (`malloc`, `free`) or standard library routines, the program is spending CPU time on bookkeeping rather than useful work. If `perf` samples concentrate in a small helper function that should be inlined, investigate whether inlining is being prevented by visibility or size heuristics. Flame graphs also expose I/O blocking: if the graph shows time in system calls like `read` or `write`, the program is bottlenecked on I/O, not CPU.

Extend the profiling by measuring specific CPU events. Modern Intel and AMD CPUs expose hundreds of performance counters through PMUs. List available events via `perf list` and filter for relevant categories:

```bash
perf list | grep -E 'cache|mem|tlb'
```

This outputs cache-related events like `L1-dcache-load-misses`, `L1-icache-load-misses` (instruction cache), `LLC-loads`, `LLC-load-misses`, `dTLB-load-misses`, and `iTLB-load-misses` (instruction TLB). Profile TLB behavior specifically:

```bash
perf stat -e dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses ./target/release/cache-profiling
```

The TLB (translation lookaside buffer) caches virtual-to-physical address translations. A TLB miss requires a page table walk, adding 10-30 nanoseconds. Programs with large working sets or strided access patterns suffer high TLB miss rates. The 4096-stride test in the benchmark deliberately stresses the TLB by jumping between pages. Expect high TLB miss counts during that phase.

To understand memory bandwidth saturation, measure memory controller events. On Intel CPUs with `uncore` PMU support:

```bash
perf stat -e uncore_imc/data_reads/,uncore_imc/data_writes/ ./target/release/cache-profiling
```

This reports DRAM read and write bandwidth in bytes. Divide by execution time to calculate GB/s. Modern DDR4 memory controllers deliver 50-100 GB/s aggregate bandwidth, but random access patterns achieve only 5-15 GB/s due to bank conflicts and row buffer misses. Sequential access saturates bandwidth near the theoretical maximum.

Optimize the benchmark by improving cache locality. Modify the random access pattern to use a smaller array that fits in L3 cache. Replace the array size constant:

```rust
const ARRAY_SIZE: usize = 2 * 1024 * 1024; // 2M elements = 8MB (fits in L3)
```

Recompile and rerun. Sequential access performance changes little because it was already streaming from memory efficiently. Random access performance improves dramatically—potentially 5-10× faster—because most accesses now hit L3 cache instead of DRAM. This demonstrates that working set size relative to cache capacity determines performance. Applications should structure data to maximize L3 cache residency for hot code paths.

Another optimization is cache line alignment and padding. Modern CPUs fetch 64-byte cache lines. If a frequently accessed struct straddles two cache lines, every access loads two lines, doubling bandwidth. Ensure hot structures align to cache line boundaries using `#[repr(align(64))]`. The `Node` struct in the benchmark includes padding to fill a cache line, preventing false sharing in multithreaded scenarios. False sharing occurs when two threads modify different variables that reside in the same cache line, causing the line to bounce between CPU cores, devastating performance.

Benchmark the impact of alignment by removing padding from `Node`:

```rust
struct Node {
    value: u64,
    next: Option<Box<Node>>,
    // padding removed
}
```

Recompile and profile linked list traversal. Performance degrades slightly because nodes are now more densely packed, increasing the number of cache lines fetched per traversal iteration. This is a subtle effect, but it accumulates in tight loops.

For Go developers, use the built-in profiler to measure similar cache effects. Create `cache_profiling.go`:

```go
package main

import (
    "fmt"
    "math/rand"
    "runtime"
    "runtime/pprof"
    "os"
    "time"
)

const (
    arraySize  = 64 * 1024 * 1024
    iterations = 100000000
)

func sequentialAccess(data []uint32) uint64 {
    var sum uint64
    length := len(data)
    for i := 0; i < iterations; i++ {
        index := int(sum) % length
        sum += uint64(data[index])
    }
    return sum
}

func randomAccess(data []uint32, indices []int) uint64 {
    var sum uint64
    for _, index := range indices {
        sum += uint64(data[index])
    }
    return sum
}

func main() {
    runtime.GOMAXPROCS(1) // Single-threaded for consistent profiling
    
    cpuProfile, _ := os.Create("cpu.prof")
    pprof.StartCPUProfile(cpuProfile)
    defer pprof.StopCPUProfile()
    
    fmt.Println("Initializing test data...")
    data := make([]uint32, arraySize)
    for i := range data {
        data[i] = uint32(i)
    }
    
    rng := rand.New(rand.NewSource(42))
    indices := make([]int, iterations)
    for i := range indices {
        indices[i] = rng.Intn(arraySize)
    }
    
    fmt.Println("\n=== Sequential Access ===")
    start := time.Now()
    result := sequentialAccess(data)
    duration := time.Since(start)
    fmt.Printf("Result: %d\n", result)
    fmt.Printf("Time: %v\n", duration)
    fmt.Printf("Throughput: %.2f M accesses/sec\n", float64(iterations)/duration.Seconds()/1e6)
    
    fmt.Println("\n=== Random Access ===")
    start = time.Now()
    result = randomAccess(data, indices)
    duration = time.Since(start)
    fmt.Printf("Result: %d\n", result)
    fmt.Printf("Time: %v\n", duration)
    fmt.Printf("Throughput: %.2f M accesses/sec\n", float64(iterations)/duration.Seconds()/1e6)
}
```

Compile and profile via `go build -o cache_profiling && ./cache_profiling`, then analyze the CPU profile with `go tool pprof -http=:8080 cpu.prof`. The pprof web interface displays flame graphs, call trees, and source-annotated profiles. Go's profiler samples at 100 Hz by default, providing statistical insight into where CPU time is spent. The web interface allows filtering by function, viewing assembly, and comparing profiles before and after optimization.

This exercise demonstrates that modern CPU performance is memory-bound for most workloads. Cache-friendly sequential access achieves 10-30× higher throughput than cache-hostile random access on the same hardware. Profiling with hardware performance counters quantifies this effect precisely, enabling data-driven optimization decisions. The combination of `perf stat` for event counts, `perf record` for call stack sampling, and flame graphs for visualization forms the foundation of production performance engineering.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrency bugs are the most insidious class of software defects because they manifest non-deterministically, evade deterministic testing, and often remain latent until production load triggers a rare scheduling interleaving. A data race occurs when two threads access the same memory location concurrently without synchronization, and at least one access is a write. Races produce undefined behavior: reads may return torn values from partial writes, writes may be reordered by the CPU or compiler, and the program may crash unpredictably. This exercise constructs pathological concurrency tests that reliably surface races, deploys ThreadSanitizer to detect them, and uses LeakSanitizer to verify memory hygiene in multithreaded programs.

Rust's borrow checker prevents most data races at compile time by enforcing that mutable references are exclusive. However, races can still occur in `unsafe` code, across FFI boundaries, or through incorrect use of atomics and locks. C++ and Go rely entirely on runtime race detection via TSan and Go's race detector, respectively. Effective testing combines static analysis, dynamic instrumentation, and stress harnesses that amplify race windows.

Create a new Rust project for concurrency testing. Run `cargo new --bin race-testing && cd race-testing`. Add dependencies for multithreading and atomic operations by editing `Cargo.toml`:

```toml
[package]
name = "race-testing"
version = "0.1.0"
edition = "2021"

[dependencies]
crossbeam = "0.8"

[profile.release]
debug = true
```

Implement a deliberately racy counter to demonstrate ThreadSanitizer. Replace `src/main.rs` with:

```rust
use std::sync::Arc;
use std::thread;
use std::sync::atomic::{AtomicUsize, Ordering};

// Racy counter (unsafe, unsynchronized access)
struct RacyCounter {
    value: usize,
}

impl RacyCounter {
    fn new() -> Self {
        RacyCounter { value: 0 }
    }
    
    unsafe fn increment(&mut self) {
        let current = self.value;
        self.value = current + 1;
    }
    
    fn get(&self) -> usize {
        self.value
    }
}

// Safe counter (properly synchronized)
struct SafeCounter {
    value: AtomicUsize,
}

impl SafeCounter {
    fn new() -> Self {
        SafeCounter {
            value: AtomicUsize::new(0),
        }
    }
    
    fn increment(&self) {
        self.value.fetch_add(1, Ordering::SeqCst);
    }
    
    fn get(&self) -> usize {
        self.value.load(Ordering::SeqCst)
    }
}

fn test_racy_counter() {
    println!("\n=== Testing Racy Counter (UNSAFE) ===");
    
    let counter = Arc::new(std::sync::Mutex::new(RacyCounter::new()));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100000 {
                unsafe {
                    let mut guard = counter_clone.lock().unwrap();
                    let ptr = &mut *guard as *mut RacyCounter;
                    (*ptr).increment();
                }
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let final_value = counter.lock().unwrap().get();
    println!("Expected: 1000000, Got: {}", final_value);
    if final_value == 1000000 {
        println!("✓ Counter correct (race not triggered this run)");
    } else {
        println!("✗ Counter incorrect (race detected)");
    }
}

fn test_safe_counter() {
    println!("\n=== Testing Safe Counter ===");
    
    let counter = Arc::new(SafeCounter::new());
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..100000 {
                counter_clone.increment();
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let final_value = counter.get();
    println!("Expected: 1000000, Got: {}", final_value);
    if final_value == 1000000 {
        println!("✓ Counter correct");
    } else {
        println!("✗ Counter incorrect");
    }
}

fn test_double_checked_locking() {
    use std::sync::Mutex;
    
    println!("\n=== Testing Double-Checked Locking (Racy) ===");
    
    struct Resource {
        initialized: bool,
        data: Vec<i32>,
    }
    
    let resource = Arc::new(Mutex::new(Resource {
        initialized: false,
        data: Vec::new(),
    }));
    
    let mut handles = vec![];
    
    for thread_id in 0..10 {
        let resource_clone = Arc::clone(&resource);
        let handle = thread::spawn(move || {
            for _ in 0..1000 {
                unsafe {
                    let ptr = &*resource_clone.lock().unwrap() as *const Resource as *mut Resource;
                    let res = &mut *ptr;
                    
                    if !res.initialized {
                        let mut locked = resource_clone.lock().unwrap();
                        if !locked.initialized {
                            locked.data = vec![thread_id; 100];
                            locked.initialized = true;
                        }
                    }
                }
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let final_resource = resource.lock().unwrap();
    println!("Resource initialized: {}, data length: {}", final_resource.initialized, final_resource.data.len());
}

fn test_leak() {
    println!("\n=== Testing Memory Leak ===");
    
    for i in 0..100 {
        let leaked = Box::new(vec![i; 1000]);
        std::mem::forget(leaked);
    }
    
    println!("Allocated and leaked 100 vectors");
}

fn main() {
    test_racy_counter();
    test_safe_counter();
    test_double_checked_locking();
    test_leak();
}
```

This program implements three race conditions and one memory leak. The `RacyCounter` uses `unsafe` to bypass Rust's borrow checker and perform unsynchronized reads and writes to a shared counter. Multiple threads increment the counter concurrently, causing lost updates. The `SafeCounter` uses `AtomicUsize` with sequentially consistent ordering to provide race-free increments. The double-checked locking test demonstrates a classic race where threads read `initialized` without synchronization, then re-check under a lock—a pattern that is unsafe in C++ and requires careful ordering in Rust. The leak test allocates memory and deliberately leaks it via `std::mem::forget`.

Compile and run the program without instrumentation to observe baseline behavior. Execute `cargo build --release && ./target/release/race-testing`. The racy counter may produce the correct result (1000000) due to lucky scheduling, or it may produce incorrect results. The race is non-deterministic: it may trigger 10% of the time, 50%, or never, depending on CPU core count, scheduler load, and random timing. This unreliability is why races are so difficult to debug with traditional testing.

Now compile with ThreadSanitizer to detect the races deterministically. TSan is part of the LLVM sanitizer suite and instruments memory accesses to track happens-before relationships. Run:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/race-testing
```

Note that TSan requires the `nightly` Rust toolchain because sanitizers are unstable features. If you encounter errors, switch to nightly via `rustup default nightly`, then retry. TSan output is verbose and diagnostic. When a race is detected, TSan prints a detailed report:

```
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7f3c4000abc0 by thread T2:
    #0 race_testing::RacyCounter::increment
    #1 race_testing::test_racy_counter::{{closure}}
    ...
  Previous read of size 8 at 0x7f3c4000abc0 by thread T1:
    #0 race_testing::RacyCounter::increment
    #1 race_testing::test_racy_counter::{{closure}}
    ...
  Location is heap block of size 8 at 0x7f3c4000abc0 allocated by main thread:
    #0 malloc
    ...
==================
```

This report identifies the racing instructions: one thread wrote to the counter while another thread was reading it. TSan provides stack traces for both accesses, the location of the allocation, and thread IDs. The "Previous read" and "Write" labels indicate the conflicting operations. TSan uses vector clocks to track happens-before relationships and detects races regardless of actual scheduling—it reports potential races even if they did not manifest in the current execution.

Inspect the TSan output for all three race conditions. The racy counter produces multiple reports as different thread pairs race. The double-checked locking test generates reports for races on the `initialized` flag. The safe counter produces no reports because atomics establish proper synchronization. TSan's false positive rate is extremely low—nearly all reports indicate real bugs.

To stress-test concurrency and increase race detection probability, raise thread counts and iteration counts. Modify the racy counter test:

```rust
for _ in 0..100 {  // Increase from 10 to 100 threads
    let counter_clone = Arc::clone(&counter);
    let handle = thread::spawn(move || {
        for _ in 0..1000000 {  // Increase from 100000 to 1000000
            unsafe {
                let mut guard = counter_clone.lock().unwrap();
                let ptr = &mut *guard as *mut RacyCounter;
                (*ptr).increment();
            }
        }
    });
    handles.push(handle);
}
```

Recompile without TSan (`cargo build --release`) and run. The final counter value will almost certainly be incorrect now, demonstrating that high thread contention amplifies race manifestation. This technique is essential for testing: a concurrency bug that surfaces 1% of the time with 10 threads may surface 90% of the time with 100 threads.

Deploy LeakSanitizer to detect memory leaks. LSan is integrated with AddressSanitizer and runs automatically at process exit. Compile with ASan:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/race-testing
```

LSan reports leaked allocations at the end of execution:

```
=================================================================
==12345==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 400000 byte(s) in 100 object(s) allocated from:
    #0 malloc
    #1 alloc::alloc::alloc
    #2 race_testing::test_leak
    ...

SUMMARY: AddressSanitizer: 400000 byte(s) leaked in 100 allocation(s).
```

This identifies the `test_leak` function as the source of leaked memory. LSan tracks heap allocations and checks for reachable memory at exit. Any allocation not reachable from the stack or global data is reported as leaked. LSan is less useful in Rust than in C++ because Rust's ownership system prevents most leaks statically. However, leaks can still occur via reference cycles in `Rc` or `Arc`, FFI, or explicit `std::mem::forget`.

For C++ developers, the workflow is identical. Create `race_testing.cpp`:

```cpp
#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <mutex>

class RacyCounter {
private:
    int value = 0;
public:
    void increment() {
        int current = value;
        value = current + 1;
    }
    int get() const { return value; }
};

class SafeCounter {
private:
    std::atomic<int> value{0};
public:
    void increment() {
        value.fetch_add(1, std::memory_order_seq_cst);
    }
    int get() const { return value.load(std::memory_order_seq_cst); }
};

void test_racy_counter() {
    std::cout << "\n=== Testing Racy Counter ===\n";
    RacyCounter counter;
    std::vector<std::thread> threads;
    
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back([&counter]() {
            for (int j = 0; j < 100000; ++j) {
                counter.increment();
            }
        });
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    std::cout << "Expected: 1000000, Got: " << counter.get() << "\n";
}

void test_safe_counter() {
    std::cout << "\n=== Testing Safe Counter ===\n";
    SafeCounter counter;
    std::vector<std::thread> threads;
    
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back([&counter]() {
            for (int j = 0; j < 100000; ++j) {
                counter.increment();
            }
        });
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    std::cout << "Expected: 1000000, Got: " << counter.get() << "\n";
}

void test_leak() {
    std::cout << "\n=== Testing Memory Leak ===\n";
    for (int i = 0; i < 100; ++i) {
        int* leaked = new int[1000];
        (void)leaked;
    }
    std::cout << "Allocated and leaked 100 arrays\n";
}

int main() {
    test_racy_counter();
    test_safe_counter();
    test_leak();
    return 0;
}
```

Compile with TSan and ASan:

```bash
clang++ -std=c++17 -fsanitize=thread -g -O2 -o race_testing_tsan race_testing.cpp
clang++ -std=c++17 -fsanitize=address -g -O2 -o race_testing_asan race_testing.cpp
./race_testing_tsan
./race_testing_asan
```

TSan reports the race in `RacyCounter::increment` identical to the Rust version. ASan with LSan reports the leaked arrays in `test_leak`. The C++ sanitizer workflow is mature and widely deployed in production testing at Google, Meta, and Microsoft.

For Go developers, use the built-in race detector. Create `race_testing.go`:

```go
package main

import (
    "fmt"
    "sync"
)

type RacyCounter struct {
    value int
}

func (c *RacyCounter) Increment() {
    current := c.value
    c.value = current + 1
}

func (c *RacyCounter) Get() int {
    return c.value
}

type SafeCounter struct {
    mu    sync.Mutex
    value int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    c.value++
    c.mu.Unlock()
}

func (c *SafeCounter) Get() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.value
}

func testRacyCounter() {
    fmt.Println("\n=== Testing Racy Counter ===")
    counter := &RacyCounter{}
    var wg sync.WaitGroup
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 100000; j++ {
                counter.Increment()
            }
        }()
    }
    
    wg.Wait()
    fmt.Printf("Expected: 1000000, Got: %d\n", counter.Get())
}

func testSafeCounter() {
    fmt.Println("\n=== Testing Safe Counter ===")
    counter := &SafeCounter{}
    var wg sync.WaitGroup
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 100000; j++ {
                counter.Increment()
            }
        }()
    }
    
    wg.Wait()
    fmt.Printf("Expected: 1000000, Got: %d\n", counter.Get())
}

func main() {
    testRacyCounter()
    testSafeCounter()
}
```

Compile and run with race detection:

```bash
go build -race -o race_testing race_testing.go
./race_testing
```

Go's race detector reports:

```
==================
WARNING: DATA RACE
Write at 0x00c0000a6010 by goroutine 7:
  main.(*RacyCounter).Increment()
      /path/race_testing.go:11 +0x3c
  main.testRacyCounter.func1()
      /path/race_testing.go:33 +0x47

Previous read at 0x00c0000a6010 by goroutine 6:
  main.(*RacyCounter).Increment()
      /path/race_testing.go:10 +0x2c
  main.testRacyCounter.func1()
      /path/race_testing.go:33 +0x47
==================
```

Go's race detector is implemented in the runtime and has lower overhead than TSan (roughly 2-10× slowdown vs. 5-15×). It is production-ready and widely used in Google's Go services. Enable it in CI pipelines via `go test -race ./...` to detect races across the entire test suite.

Stress testing requires constructing scenarios that maximize contention. A useful pattern is the "rendezvous" test, where all threads synchronize at a barrier before racing to access shared state. Create a Rust rendezvous test:

```rust
use std::sync::{Arc, Barrier};
use std::thread;

fn test_rendezvous() {
    println!("\n=== Rendezvous Stress Test ===");
    
    let shared_data = Arc::new(std::sync::Mutex::new(vec![0u64; 1000]));
    let barrier = Arc::new(Barrier::new(100));
    let mut handles = vec![];
    
    for thread_id in 0..100 {
        let data_clone = Arc::clone(&shared_data);
        let barrier_clone = Arc::clone(&barrier);
        
        let handle = thread::spawn(move || {
            barrier_clone.wait();
            
            for i in 0..1000 {
                let mut guard = data_clone.lock().unwrap();
                guard[i] = guard[i].wrapping_add(thread_id);
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let final_data = shared_data.lock().unwrap();
    let sum: u64 = final_data.iter().sum();
    println!("Final sum: {}", sum);
}
```

This test spawns 100 threads, synchronizes them at a barrier, then releases them simultaneously to contend for the mutex. The barrier ensures maximum thread density at the critical section, amplifying race windows. Without proper synchronization (e.g., if the mutex is removed), TSan will report hundreds of races.

This exercise demonstrates that concurrency testing requires both static and dynamic techniques. Rust's borrow checker eliminates entire classes of races at compile time, but dynamic instrumentation via TSan catches the remaining cases in `unsafe` code and FFI. Go and C++ rely entirely on runtime detection. High thread counts, rendezvous synchronization, and repeated execution increase race detection probability. LeakSanitizer ensures memory hygiene. Together, these tools form a comprehensive verification strategy for production multithreaded systems.

## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the verification toolchain into a quick-reference card for daily development workflows. Copy these commands into shell aliases or CI pipeline scripts for immediate access.

### Compiler IR Inspection

**Rust MIR (Mid-Level Intermediate Representation):**
```bash
cargo rustc --release -- --emit=mir
find target/release/deps -name '*.mir' | head -1 | xargs less
```

**Rust LLVM IR:**
```bash
cargo rustc --release -- --emit=llvm-ir
find target/release/deps -name '*.ll' | head -1 | xargs less
```

**Rust Assembly:**
```bash
cargo rustc --release -- --emit=asm
find target/release/deps -name '*.s' | head -1 | xargs less
```

**Rust Assembly for Specific Function (requires cargo-asm):**
```bash
cargo install cargo-asm
cargo asm --release crate_name::module::function_name
```

**LLVM Optimization Remarks:**
```bash
RUSTFLAGS="-C llvm-args=-pass-remarks=inline" cargo build --release 2>&1 | grep inline
RUSTFLAGS="-C llvm-args=-pass-remarks=loop-vectorize" cargo build --release 2>&1 | grep vector
```

**C++ LLVM IR:**
```bash
clang++ -S -emit-llvm -O2 -o output.ll source.cpp
```

**C++ Assembly:**
```bash
clang++ -S -O2 -o output.s source.cpp
```

### Memory Sanitizers

**AddressSanitizer (Detects: heap/stack buffer overflow, use-after-free, double-free):**
```bash
# Rust (requires nightly)
RUSTFLAGS="-Z sanitizer=address" cargo +nightly build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/binary

# C++
clang++ -fsanitize=address -g -O1 -o binary source.cpp
./binary
```

**ThreadSanitizer (Detects: data races):**
```bash
# Rust (requires nightly)
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/binary

# C++
clang++ -fsanitize=thread -g -O2 -o binary source.cpp
./binary

# Go (built-in)
go build -race -o binary
./binary
go test -race ./...
```

**UndefinedBehaviorSanitizer (Detects: signed overflow, null dereference, alignment violations):**
```bash
# C++
clang++ -fsanitize=undefined -g -O2 -o binary source.cpp
./binary
```

**LeakSanitizer (Detects: memory leaks, integrated with ASan):**
```bash
# Automatically enabled with AddressSanitizer
# Standalone:
clang++ -fsanitize=leak -g -o binary source.cpp
./binary
```

**MemorySanitizer (Detects: uninitialized memory reads, Linux x86-64 only):**
```bash
clang++ -fsanitize=memory -g -O2 -o binary source.cpp
./binary
```

### Performance Profiling

**Linux perf Event Counting:**
```bash
# Basic stats
perf stat ./binary

# Cache analysis
perf stat -e cycles,instructions,cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses ./binary

# TLB analysis
perf stat -e dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses ./binary

# Branch prediction
perf stat -e branches,branch-misses ./binary

# Memory bandwidth (Intel uncore)
perf stat -e uncore_imc/data_reads/,uncore_imc/data_writes/ ./binary
```

**Flame Graph Generation:**
```bash
# Rust (via cargo-flamegraph)
cargo install flamegraph
cargo flamegraph --release -- [args]
# Output: flamegraph.svg

# Manual perf workflow
perf record -F 99 -g ./binary [args]
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

**Go CPU Profiling:**
```bash
# Runtime profiling
go test -cpuprofile=cpu.prof -bench=.
go tool pprof -http=:8080 cpu.prof

# Application profiling (requires runtime/pprof in code)
go build -o binary
./binary  # Generates cpu.prof
go tool pprof -http=:8080 cpu.prof
```

**Go Heap Profiling:**
```bash
go test -memprofile=mem.prof -bench=.
go tool pprof -http=:8080 mem.prof
```

**Cachegrind (Valgrind cache simulation):**
```bash
valgrind --tool=cachegrind ./binary
cg_annotate cachegrind.out.<pid>
```

### Debugger Integration

**LLDB with Rust:**
```bash
cargo build
rust-lldb target/debug/binary

# Common commands:
# (lldb) b main.rs:42          # Breakpoint at line
# (lldb) r                      # Run
# (lldb) bt                     # Backtrace
# (lldb) fr v                   # Frame variables
# (lldb) p variable_name        # Print variable
```

**GDB with C++:**
```bash
g++ -g -o binary source.cpp
gdb ./binary

# Common commands:
# (gdb) break main              # Breakpoint at function
# (gdb) run                     # Run
# (gdb) backtrace              # Backtrace
# (gdb) print variable         # Print variable
# (gdb) info locals            # Local variables
```

**Valgrind Memcheck (Heap correctness):**
```bash
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./binary
```

### Build Configuration

**Rust Release with Debug Symbols:**
```toml
[profile.release]
debug = true
```

**Rust Native CPU Target:**
```bash
RUSTFLAGS="-C target-cpu=native" cargo build --release
```

**C++ Optimization Levels:**
```bash
clang++ -O0  # No optimization (debug)
clang++ -O1  # Basic optimization
clang++ -O2  # Aggressive optimization (default release)
clang++ -O3  # Maximum optimization
clang++ -Os  # Optimize for size
```

**Go Build Tags for Tests:**
```bash
go test -tags=integration ./...
go test -short ./...  # Skip long tests
```

### CI Pipeline Integration

**Rust CI Verification Script:**
```bash
#!/bin/bash
set -e

cargo fmt --check
cargo clippy -- -D warnings
cargo test --all-features
cargo test --release

RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu

cargo bench --no-run
```

**C++ CI Verification Script:**
```bash
#!/bin/bash
set -e

clang++ -fsanitize=address -g -O2 -o test_asan tests.cpp && ./test_asan
clang++ -fsanitize=thread -g -O2 -o test_tsan tests.cpp && ./test_tsan
clang++ -fsanitize=undefined -g -O2 -o test_ubsan tests.cpp && ./test_ubsan

clang-format --dry-run --Werror *.cpp
clang-tidy *.cpp -- -std=c++17
```

**Go CI Verification Script:**
```bash
#!/bin/bash
set -e

go fmt ./...
go vet ./...
go test -race ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html
```

### Toolchain Installation

**Rust Toolchain Setup:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup component add llvm-tools-preview
cargo install cargo-asm cargo-expand flamegraph
```

**C++ Toolchain Setup (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install clang llvm lld valgrind linux-tools-common linux-tools-generic
```

**Go Toolchain Setup:**
```bash
# Install Go via official installer
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

### Quick Diagnostic Workflow

When investigating a performance issue or suspected bug:

1. **Reproduce under profiling:**
   ```bash
   perf stat -e cycles,instructions,cache-misses ./binary
   ```

2. **Generate flame graph:**
   ```bash
   cargo flamegraph --release
   ```

3. **Check for races (if multithreaded):**
   ```bash
   RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test
   ```

4. **Check for memory corruption:**
   ```bash
   RUSTFLAGS="-Z sanitizer=address" cargo +nightly test
   ```

5. **Inspect hot function assembly:**
   ```bash
   cargo asm --release crate::hot_function
   ```

6. **Verify optimization assumptions:**
   ```bash
   RUSTFLAGS="-C llvm-args=-pass-remarks=inline" cargo build --release 2>&1 | grep function_name
   ```

This workflow takes 5-10 minutes and catches 80% of correctness and performance issues. Automate it in pre-commit hooks or CI pipelines for continuous verification. The combination of compiler IR inspection, sanitizer instrumentation, and hardware performance counter profiling provides complete visibility into program behavior from source code to silicon execution.
