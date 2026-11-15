# Operational Verification Labs: Design Patterns

## Objective & Toolchain Setup

Design patterns represent reusable architectural templates that solve recurring problems in software construction, yet their true validation extends far beyond syntactic correctness. The conventional academic treatment of patterns—abstract UML diagrams and theoretical categorizations—fails to address the operational reality that patterns exist to manage complexity, enforce invariants, and optimize runtime performance under real hardware constraints. This laboratory guide grounds pattern implementations in concrete verification: we examine how the Strategy pattern affects instruction cache locality, how the Observer pattern scales under ThreadSanitizer scrutiny, how the Builder pattern interacts with move semantics and heap allocators, and how the Singleton pattern behaves under memory ordering relaxations on weakly-ordered architectures.

Each exercise drives a complete cycle from implementation through disassembly analysis, cache profiling, concurrency stress testing, and sanitizer diagnostics. We deploy Rust's ownership system and zero-cost abstractions as the primary implementation vehicle, with comparative C++ examples where architectural differences illuminate pattern tradeoffs. The verification methodology follows a layered approach: first, we validate semantic correctness through unit tests and type-system guarantees; second, we measure performance characteristics using `perf`, `cargo-flamegraph`, and `cachegrind`; third, we stress-test concurrency invariants with ThreadSanitizer and Miri; finally, we inspect the machine code artifact through LLVM IR dumps and disassembly to confirm that high-level abstractions compile to the expected low-level operations.

### Toolchain Installation and Environment Verification

Install the Rust toolchain through `rustup`, which manages the compiler (`rustc`), package manager (`cargo`), and standard library. Execute `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` and select the stable toolchain. Verify installation with `rustc --version` and `cargo --version`. Install the nightly toolchain for advanced instrumentation with `rustup toolchain install nightly` and add the Miri interpreter for undefined behavior detection via `rustup +nightly component add miri`. For comparative C++ analysis, install Clang 18 or later through your distribution's package manager, ensuring LLVM tooling is available. On Ubuntu/Debian systems, execute `sudo apt install clang-18 llvm-18 lld-18`. Verify with `clang-18 --version` and confirm that `llvm-objdump-18` is accessible.

Install performance profiling and dynamic analysis tools. For cache and instruction-level profiling, install `perf` through your kernel's tools package: `sudo apt install linux-tools-common linux-tools-generic linux-tools-$(uname -r)`. Extend flamegraph visualization with `cargo install flamegraph`, which wraps `perf` and generates interactive SVG call graphs. Install Valgrind for memory error detection and cache simulation: `sudo apt install valgrind`. On systems where Valgrind does not support the latest architecture features, rely on LLVM's AddressSanitizer and ThreadSanitizer, which Rust integrates directly through `cargo` flags. Install the LLDB debugger for Rust-aware inspection: `sudo apt install lldb-18`. Finally, install `cargo-bloat` to analyze binary size contributions from monomorphization: `cargo install cargo-bloat`.

Create a workspace directory and initialize a Cargo project for the laboratory exercises. Execute `cargo new --lib design_patterns_lab` and navigate into the generated directory. Open `Cargo.toml` and configure the project for performance profiling and sanitizer instrumentation. Add the following profile configurations to separate debug information from optimization:

```toml
[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
debug = true

[profile.bench]
inherits = "release"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
```

The release profile enables full link-time optimization and reduces codegen units to maximize inlining and devirtualization, while preserving debug symbols for `perf` attribution. The `criterion` crate provides statistically rigorous microbenchmarking with outlier detection and HTML report generation.

Verify that sanitizers are operational by creating a test file `src/lib.rs` with a deliberate data race. Write the following code:

```rust
use std::sync::Arc;
use std::thread;

pub fn test_data_race() {
    let counter = Arc::new(0);
    let c1 = Arc::clone(&counter);
    let c2 = Arc::clone(&counter);

    let h1 = thread::spawn(move || {
        unsafe {
            let ptr = Arc::as_ptr(&c1) as *mut i32;
            *ptr += 1;
        }
    });

    let h2 = thread::spawn(move || {
        unsafe {
            let ptr = Arc::as_ptr(&c2) as *mut i32;
            *ptr += 1;
        }
    });

    h1.join().unwrap();
    h2.join().unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detect_race() {
        test_data_race();
    }
}
```

Compile and run with ThreadSanitizer enabled: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu`. ThreadSanitizer should report a data race on the counter variable. If the sanitizer output appears, your environment is correctly configured. Remove this test code before proceeding to the actual exercises.

## Exercise 1: Strategy Pattern – AST, IR & Disassembly Analysis

The Strategy pattern encapsulates interchangeable algorithms behind a common interface, enabling runtime selection of behavior without conditional branching in client code. In statically-typed systems languages, this pattern manifests through trait objects (Rust) or virtual function tables (C++), both of which introduce an indirect function call through a vtable pointer. The performance implications are non-trivial: vtable indirection defeats branch prediction and pollutes the instruction cache, yet modern compilers can often devirtualize calls when type information is monomorphically known. This exercise implements a compression strategy pattern and verifies whether the compiler eliminates indirection through inlining and monomorphization, then measures the performance delta between static dispatch and dynamic dispatch under realistic workloads.

### Implementation: Compression Strategy with Trait Objects and Generics

Create a new file `src/strategy.rs` and implement a compression strategy abstraction. We define a `CompressionStrategy` trait with an `compress` method, then provide concrete implementations for LZ4-style fast compression and a hypothetical high-ratio compressor. The first implementation uses trait objects (`Box<dyn Trait>`) for runtime polymorphism; the second uses generic monomorphization for static dispatch.

```rust
use std::io::{self, Write};

pub trait CompressionStrategy {
    fn compress(&self, input: &[u8], output: &mut Vec<u8>) -> io::Result<usize>;
    fn name(&self) -> &str;
}

pub struct FastCompressor;

impl CompressionStrategy for FastCompressor {
    fn compress(&self, input: &[u8], output: &mut Vec<u8>) -> io::Result<usize> {
        // Simplified run-length encoding for demonstration
        let mut count = 0;
        for chunk in input.chunks(256) {
            output.push(chunk.len() as u8);
            output.write_all(chunk)?;
            count += chunk.len() + 1;
        }
        Ok(count)
    }

    fn name(&self) -> &str {
        "FastCompressor"
    }
}

pub struct HighRatioCompressor;

impl CompressionStrategy for HighRatioCompressor {
    fn compress(&self, input: &[u8], output: &mut Vec<u8>) -> io::Result<usize> {
        // Simulate expensive compression with dummy computation
        let mut count = 0;
        for &byte in input {
            let transformed = byte.wrapping_mul(197).wrapping_add(131);
            output.push(transformed);
            count += 1;
        }
        Ok(count)
    }

    fn name(&self) -> &str {
        "HighRatioCompressor"
    }
}

pub struct Compressor {
    strategy: Box<dyn CompressionStrategy>,
}

impl Compressor {
    pub fn new(strategy: Box<dyn CompressionStrategy>) -> Self {
        Self { strategy }
    }

    pub fn compress(&self, input: &[u8]) -> io::Result<Vec<u8>> {
        let mut output = Vec::new();
        self.strategy.compress(input, &mut output)?;
        Ok(output)
    }

    pub fn strategy_name(&self) -> &str {
        self.strategy.name()
    }
}

pub fn compress_with_generic<S: CompressionStrategy>(
    strategy: &S,
    input: &[u8],
) -> io::Result<Vec<u8>> {
    let mut output = Vec::new();
    strategy.compress(input, &mut output)?;
    Ok(output)
}
```

Add this module to `src/lib.rs` by inserting `pub mod strategy;` at the top of the file. Now create a benchmark suite to measure the performance difference between dynamic dispatch and static monomorphization. Create `benches/strategy_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use design_patterns_lab::strategy::*;

fn generate_test_data(size: usize) -> Vec<u8> {
    (0..size).map(|i| (i % 256) as u8).collect()
}

fn bench_dynamic_dispatch(c: &mut Criterion) {
    let mut group = c.benchmark_group("strategy_dynamic");
    
    for size in [1024, 8192, 65536].iter() {
        let data = generate_test_data(*size);
        
        group.bench_with_input(BenchmarkId::new("fast", size), &data, |b, d| {
            let compressor = Compressor::new(Box::new(FastCompressor));
            b.iter(|| {
                black_box(compressor.compress(black_box(d)).unwrap());
            });
        });
        
        group.bench_with_input(BenchmarkId::new("high_ratio", size), &data, |b, d| {
            let compressor = Compressor::new(Box::new(HighRatioCompressor));
            b.iter(|| {
                black_box(compressor.compress(black_box(d)).unwrap());
            });
        });
    }
    
    group.finish();
}

fn bench_static_dispatch(c: &mut Criterion) {
    let mut group = c.benchmark_group("strategy_static");
    
    for size in [1024, 8192, 65536].iter() {
        let data = generate_test_data(*size);
        
        group.bench_with_input(BenchmarkId::new("fast", size), &data, |b, d| {
            let strategy = FastCompressor;
            b.iter(|| {
                black_box(compress_with_generic(black_box(&strategy), black_box(d)).unwrap());
            });
        });
        
        group.bench_with_input(BenchmarkId::new("high_ratio", size), &data, |b, d| {
            let strategy = HighRatioCompressor;
            b.iter(|| {
                black_box(compress_with_generic(black_box(&strategy), black_box(d)).unwrap());
            });
        });
    }
    
    group.finish();
}

criterion_group!(benches, bench_dynamic_dispatch, bench_static_dispatch);
criterion_main!(benches);
```

Add a `[[bench]]` section to `Cargo.toml`:

```toml
[[bench]]
name = "strategy_bench"
harness = false
```

Execute the benchmark suite with `cargo bench --bench strategy_bench`. Criterion will run each benchmark configuration multiple times, compute statistical distributions, and generate an HTML report in `target/criterion/`. Open `target/criterion/report/index.html` in a browser to inspect the violin plots and confidence intervals. Observe the performance delta between dynamic and static dispatch, particularly for the smaller 1KB workload where vtable overhead dominates.

### LLVM IR and Disassembly Inspection

To verify whether the compiler devirtualizes the static dispatch path, emit LLVM IR and inspect the generated code. Execute `cargo rustc --release --lib -- --emit=llvm-ir` and locate the IR file in `target/release/deps/design_patterns_lab-*.ll`. Search for the `compress_with_generic` function instantiation. The monomorphized version should inline the `compress` method directly, eliminating any `call` instruction through a function pointer. In contrast, the dynamic dispatch path will retain an `load` from the vtable followed by an indirect `call`.

For disassembly analysis, compile with full optimization and examine the machine code. Execute `cargo build --release` and then disassemble the library with `objdump -d -C target/release/libdesign_patterns_lab.rlib > strategy_asm.txt`. Alternatively, use LLVM's `llvm-objdump-18 -d -C target/release/libdesign_patterns_lab.so` if building a dynamic library. Search for the `compress_with_generic` symbol. In the monomorphized case, you should observe a direct call or inlined body; in the trait object case, you will see an address load followed by a `call *%rax` or similar indirect call instruction.

Generate a flamegraph to visualize the call stack and identify hot paths. Execute `cargo flamegraph --bench strategy_bench --root -- --bench`. This requires root privileges to configure `perf` events. The resulting `flamegraph.svg` displays the aggregated time spent in each function. Compare the width of the `compress` method in the dynamic and static dispatch variants. The static dispatch version should show negligible overhead from the function call itself, while the dynamic version may reveal measurable time in vtable indirection, especially on CPUs with aggressive speculative execution that struggle with indirect branches.

### Cache Performance Analysis with Cachegrind

Vtable indirection impacts instruction cache behavior because the target address is not known until runtime, preventing the CPU from prefetching the callee's instructions. Use Valgrind's Cachegrind tool to measure L1 instruction cache misses. First, create a minimal test harness in `tests/strategy_cache.rs`:

```rust
use design_patterns_lab::strategy::*;

fn main() {
    let data: Vec<u8> = (0..1_000_000).map(|i| (i % 256) as u8).collect();
    
    // Dynamic dispatch
    let compressor = Compressor::new(Box::new(FastCompressor));
    for _ in 0..100 {
        let _ = compressor.compress(&data).unwrap();
    }
    
    // Static dispatch
    let strategy = FastCompressor;
    for _ in 0..100 {
        let _ = compress_with_generic(&strategy, &data).unwrap();
    }
}
```

Compile in release mode: `cargo build --release --test strategy_cache`. Run Cachegrind with `valgrind --tool=cachegrind --branch-sim=yes target/release/deps/strategy_cache-* `. Cachegrind will output instruction reads (Ir), instruction L1 misses (I1mr), and branch mispredictions. Compare the metrics between the dynamic and static dispatch loops. The dynamic dispatch path will typically exhibit higher I1 miss rates due to unpredictable jump targets fragmenting the instruction stream.

To isolate the measurement, modify the test harness to run each dispatch mode in separate binaries and invoke Cachegrind on each independently. This eliminates interference from shared setup code. Alternatively, use `perf stat` for hardware performance counters on real silicon: `perf stat -e L1-icache-load-misses,branch-misses cargo test --release strategy_cache`. The `perf` approach reflects actual hardware behavior, including CPU prefetching and speculative execution, which Cachegrind's simulation does not model.

### Interpreting Results and Pattern Selection Heuristics

If the benchmark reveals less than five percent overhead for dynamic dispatch, the pattern's flexibility justifies the cost for most applications. However, if the tight loop dominates execution time and the benchmark shows ten to twenty percent degradation, prefer static dispatch through generics or enum-based state machines. The decision hinges on the call frequency and the ratio of dispatch overhead to actual work performed. For compression algorithms processing megabytes per invocation, vtable overhead is negligible; for event dispatchers invoking handlers thousands of times per frame, static dispatch is critical.

An alternative pattern is enum dispatch, which replaces trait objects with a `match` statement over an enum of strategy types. This eliminates heap allocation and vtable indirection while preserving runtime selection. Implement an `EnumCompressor` in `src/strategy.rs`:

```rust
pub enum CompressionKind {
    Fast,
    HighRatio,
}

pub struct EnumCompressor {
    kind: CompressionKind,
}

impl EnumCompressor {
    pub fn new(kind: CompressionKind) -> Self {
        Self { kind }
    }

    pub fn compress(&self, input: &[u8]) -> io::Result<Vec<u8>> {
        let mut output = Vec::new();
        match self.kind {
            CompressionKind::Fast => {
                FastCompressor.compress(input, &mut output)?;
            }
            CompressionKind::HighRatio => {
                HighRatioCompressor.compress(input, &mut output)?;
            }
        }
        Ok(output)
    }
}
```

Benchmark this variant and compare. The enum approach often matches static dispatch performance because the compiler can inline through the `match` arms, while avoiding the heap allocation of `Box<dyn Trait>`. This pattern is optimal when the set of strategies is closed and known at compile time, which describes most real-world systems.

## Exercise 2: Observer Pattern – Cache Miss & Throughput Profiling

The Observer pattern decouples event producers from consumers by maintaining a dynamic list of subscribers that receive notifications when state changes occur. Classic implementations use a vector of trait objects or function pointers, iterating through the list to invoke each observer's update method. This design introduces several performance hazards: unpredictable memory access patterns as the iterator chases pointers into disparate heap allocations, cache line contention when multiple observers touch related data, and poor vectorization potential due to type heterogeneity. This exercise implements a GUI event system with multiple observer strategies, profiles cache miss rates and memory bandwidth saturation, and demonstrates how arena allocation and data-oriented design recover performance.

### Implementation: Event System with Dynamic Observers

Create `src/observer.rs` and implement a subject-observer system for a hypothetical GUI framework. The subject maintains a list of observers and notifies them when a button is clicked. We start with the naive implementation using boxed trait objects, then refactor to an arena-allocated design.

```rust
use std::fmt::Debug;

pub trait Observer: Debug {
    fn update(&mut self, event: &ButtonEvent);
}

#[derive(Debug, Clone)]
pub struct ButtonEvent {
    pub button_id: u32,
    pub click_count: u32,
}

#[derive(Debug)]
pub struct LoggingObserver {
    pub name: String,
    pub events_received: usize,
}

impl Observer for LoggingObserver {
    fn update(&mut self, event: &ButtonEvent) {
        self.events_received += 1;
        // Simulate logging overhead
        let _ = format!("{}: Button {} clicked {} times", 
                       self.name, event.button_id, event.click_count);
    }
}

#[derive(Debug)]
pub struct StatisticsObserver {
    pub total_clicks: u64,
    pub button_histogram: Vec<u32>,
}

impl StatisticsObserver {
    pub fn new(num_buttons: usize) -> Self {
        Self {
            total_clicks: 0,
            button_histogram: vec![0; num_buttons],
        }
    }
}

impl Observer for StatisticsObserver {
    fn update(&mut self, event: &ButtonEvent) {
        self.total_clicks += event.click_count as u64;
        if let Some(count) = self.button_histogram.get_mut(event.button_id as usize) {
            *count += event.click_count;
        }
    }
}

pub struct ButtonSubject {
    observers: Vec<Box<dyn Observer>>,
}

impl ButtonSubject {
    pub fn new() -> Self {
        Self {
            observers: Vec::new(),
        }
    }

    pub fn attach(&mut self, observer: Box<dyn Observer>) {
        self.observers.push(observer);
    }

    pub fn notify(&mut self, event: &ButtonEvent) {
        for observer in &mut self.observers {
            observer.update(event);
        }
    }
}
```

Add the module to `src/lib.rs` with `pub mod observer;`. Now create a benchmark that simulates a burst of GUI events. Create `benches/observer_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use design_patterns_lab::observer::*;

fn bench_observer_notify(c: &mut Criterion) {
    let mut group = c.benchmark_group("observer_notify");
    
    for num_observers in [10, 50, 200].iter() {
        group.bench_with_input(
            BenchmarkId::new("boxed_observers", num_observers),
            num_observers,
            |b, &n| {
                let mut subject = ButtonSubject::new();
                for i in 0..n {
                    subject.attach(Box::new(LoggingObserver {
                        name: format!("Logger{}", i),
                        events_received: 0,
                    }));
                }
                subject.attach(Box::new(StatisticsObserver::new(100)));
                
                let event = ButtonEvent {
                    button_id: 42,
                    click_count: 1,
                };
                
                b.iter(|| {
                    subject.notify(black_box(&event));
                });
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, bench_observer_notify);
criterion_main!(benches);
```

Update `Cargo.toml` to register the benchmark. Execute `cargo bench --bench observer_bench` and record the throughput in events per second. With two hundred observers, the iteration loop will traverse two hundred heap allocations scattered across the address space, resulting in high cache miss rates and memory stall cycles.

### Cache Profiling with Perf and Cachegrind

Generate a flamegraph to identify memory stalls: `cargo flamegraph --bench observer_bench --root -- --bench`. The resulting graph should show significant time spent in the `notify` loop and the observer `update` methods. Now use `perf` to measure cache statistics. Execute `perf stat -e cache-misses,cache-references,L1-dcache-load-misses cargo bench --bench observer_bench`. The cache-miss rate (cache-misses / cache-references) will likely exceed ten to twenty percent with scattered allocations, compared to one to five percent for cache-friendly code.

For detailed cache line analysis, run Cachegrind with data cache simulation: `valgrind --tool=cachegrind --cachegrind-out-file=observer.cachegrind target/release/deps/observer_bench-*`. Open the output file with `cg_annotate observer.cachegrind` to view line-by-line cache miss counts. The loop over `self.observers` will exhibit high D1 miss rates as each `Box<dyn Observer>` pointer dereference fetches data from a different cache line.

### Refactoring: Arena Allocation and Type-Erased Storage

To improve cache locality, replace the vector of boxed trait objects with a contiguous arena that stores observers inline. This approach requires type erasure through raw pointers and manual dispatch, but eliminates pointer chasing and coalesces observer data into sequential cache lines. Implement an arena-based observer list in `src/observer.rs`:

```rust
use std::alloc::{alloc, dealloc, Layout};
use std::ptr;

pub struct ArenaObserverList {
    storage: Vec<u8>,
    observers: Vec<(*mut u8, Layout, unsafe fn(*mut u8, &ButtonEvent))>,
}

impl ArenaObserverList {
    pub fn new() -> Self {
        Self {
            storage: Vec::new(),
            observers: Vec::new(),
        }
    }

    pub fn attach<T: Observer + 'static>(&mut self, observer: T) {
        let layout = Layout::new::<T>();
        let ptr = unsafe { alloc(layout) as *mut T };
        unsafe {
            ptr.write(observer);
        }

        let update_fn: unsafe fn(*mut u8, &ButtonEvent) = |ptr, event| unsafe {
            let typed_ptr = ptr as *mut T;
            (*typed_ptr).update(event);
        };

        self.observers.push((ptr as *mut u8, layout, update_fn));
    }

    pub fn notify(&mut self, event: &ButtonEvent) {
        for &(ptr, _, update_fn) in &self.observers {
            unsafe {
                update_fn(ptr, event);
            }
        }
    }
}

impl Drop for ArenaObserverList {
    fn drop(&mut self) {
        for &(ptr, layout, _) in &self.observers {
            unsafe {
                dealloc(ptr, layout);
            }
        }
    }
}

pub struct ArenaButtonSubject {
    observers: ArenaObserverList,
}

impl ArenaButtonSubject {
    pub fn new() -> Self {
        Self {
            observers: ArenaObserverList::new(),
        }
    }

    pub fn attach<T: Observer + 'static>(&mut self, observer: T) {
        self.observers.attach(observer);
    }

    pub fn notify(&mut self, event: &ButtonEvent) {
        self.observers.notify(event);
    }
}
```

Benchmark this implementation by adding a new case to `observer_bench.rs`:

```rust
fn bench_arena_observer_notify(c: &mut Criterion) {
    let mut group = c.benchmark_group("observer_arena_notify");
    
    for num_observers in [10, 50, 200].iter() {
        group.bench_with_input(
            BenchmarkId::new("arena_observers", num_observers),
            num_observers,
            |b, &n| {
                let mut subject = ArenaButtonSubject::new();
                for i in 0..n {
                    subject.attach(LoggingObserver {
                        name: format!("Logger{}", i),
                        events_received: 0,
                    });
                }
                subject.attach(StatisticsObserver::new(100));
                
                let event = ButtonEvent {
                    button_id: 42,
                    click_count: 1,
                };
                
                b.iter(|| {
                    subject.notify(black_box(&event));
                });
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, bench_observer_notify, bench_arena_observer_notify);
```

Rerun the benchmark and compare throughput. The arena implementation should demonstrate thirty to fifty percent higher throughput at scale due to reduced cache misses. Verify this with `perf stat` or Cachegrind, which will show a lower D1 miss rate as the observers are allocated contiguously and iterated in sequential memory order.

### Alternative: Enum-Based Homogeneous Observers

If the set of observer types is statically known and small, replace trait objects with an enum and store observers in a homogeneous `Vec`. This enables vectorization and eliminates indirect calls entirely. Implement `EnumObserver` in `src/observer.rs`:

```rust
#[derive(Debug)]
pub enum EnumObserver {
    Logging(LoggingObserver),
    Statistics(StatisticsObserver),
}

impl EnumObserver {
    fn update(&mut self, event: &ButtonEvent) {
        match self {
            EnumObserver::Logging(obs) => obs.update(event),
            EnumObserver::Statistics(obs) => obs.update(event),
        }
    }
}

pub struct EnumButtonSubject {
    observers: Vec<EnumObserver>,
}

impl EnumButtonSubject {
    pub fn new() -> Self {
        Self {
            observers: Vec::new(),
        }
    }

    pub fn attach(&mut self, observer: EnumObserver) {
        self.observers.push(observer);
    }

    pub fn notify(&mut self, event: &ButtonEvent) {
        for observer in &mut self.observers {
            observer.update(event);
        }
    }
}
```

Benchmark this variant and observe that it achieves the best performance due to optimal cache locality, branch prediction, and potential SIMD autovectorization if the observer bodies are simple. The tradeoff is loss of extensibility: adding a new observer type requires modifying the enum definition and recompiling all dependents.

### Performance Interpretation and Pattern Selection

The observer pattern exhibits superlinear performance degradation with scattered allocations due to memory bandwidth saturation. For latency-critical systems such as game engines or real-time data processing pipelines, arena allocation or enum-based dispatch is mandatory. For configuration-heavy systems where observers are rarely invoked, the boxed trait object approach remains acceptable and preserves modularity. Profile the actual notification frequency and observer count in your target workload before selecting a strategy.

## Exercise 3: Builder Pattern – Data Race Stress Testing & Leak Sanitizer Diagnostics

The Builder pattern separates object construction from its representation, enabling complex initialization sequences with validation, default values, and optional parameters. In concurrent systems, builders often accumulate state across multiple threads before finalizing the object, introducing data race hazards and memory leak risks if ownership is mismanaged. This exercise implements a thread-safe configuration builder for a distributed system, stress-tests it under ThreadSanitizer to detect races, verifies leak-free teardown with LeakSanitizer, and measures the overhead of synchronization primitives using `perf` lock contention profiling.

### Implementation: Thread-Safe Configuration Builder

Create `src/builder.rs` and implement a configuration builder for a hypothetical database connection pool. The builder accumulates connection parameters from multiple threads, validates constraints, and produces an immutable configuration object. We use `Arc<Mutex<BuilderState>>` for thread safety, then refactor to lock-free atomic operations where possible.

```rust
use std::sync::{Arc, Mutex};
use std::time::Duration;

#[derive(Debug, Clone)]
pub struct DatabaseConfig {
    pub host: String,
    pub port: u16,
    pub max_connections: u32,
    pub timeout: Duration,
    pub use_ssl: bool,
}

#[derive(Debug)]
struct BuilderState {
    host: Option<String>,
    port: Option<u16>,
    max_connections: Option<u32>,
    timeout: Option<Duration>,
    use_ssl: bool,
}

impl BuilderState {
    fn new() -> Self {
        Self {
            host: None,
            port: None,
            max_connections: None,
            timeout: None,
            use_ssl: false,
        }
    }

    fn validate(&self) -> Result<(), String> {
        if self.host.is_none() {
            return Err("Host is required".to_string());
        }
        if let Some(max_conn) = self.max_connections {
            if max_conn == 0 || max_conn > 10000 {
                return Err("Max connections must be between 1 and 10000".to_string());
            }
        }
        Ok(())
    }

    fn build(self) -> DatabaseConfig {
        DatabaseConfig {
            host: self.host.unwrap_or_else(|| "localhost".to_string()),
            port: self.port.unwrap_or(5432),
            max_connections: self.max_connections.unwrap_or(100),
            timeout: self.timeout.unwrap_or(Duration::from_secs(30)),
            use_ssl: self.use_ssl,
        }
    }
}

#[derive(Clone)]
pub struct DatabaseConfigBuilder {
    state: Arc<Mutex<BuilderState>>,
}

impl DatabaseConfigBuilder {
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(BuilderState::new())),
        }
    }

    pub fn host(&self, host: String) -> &Self {
        let mut state = self.state.lock().unwrap();
        state.host = Some(host);
        self
    }

    pub fn port(&self, port: u16) -> &Self {
        let mut state = self.state.lock().unwrap();
        state.port = Some(port);
        self
    }

    pub fn max_connections(&self, max_connections: u32) -> &Self {
        let mut state = self.state.lock().unwrap();
        state.max_connections = Some(max_connections);
        self
    }

    pub fn timeout(&self, timeout: Duration) -> &Self {
        let mut state = self.state.lock().unwrap();
        state.timeout = Some(timeout);
        self
    }

    pub fn use_ssl(&self, use_ssl: bool) -> &Self {
        let mut state = self.state.lock().unwrap();
        state.use_ssl = use_ssl;
        self
    }

    pub fn build(&self) -> Result<DatabaseConfig, String> {
        let state = self.state.lock().unwrap();
        state.validate()?;
        let owned_state = BuilderState {
            host: state.host.clone(),
            port: state.port,
            max_connections: state.max_connections,
            timeout: state.timeout,
            use_ssl: state.use_ssl,
        };
        Ok(owned_state.build())
    }
}
```

Add the module to `src/lib.rs` with `pub mod builder;`. Now create a stress test that spawns multiple threads concurrently mutating the builder. Create `tests/builder_stress.rs`:

```rust
use design_patterns_lab::builder::DatabaseConfigBuilder;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

#[test]
fn concurrent_builder_stress_test() {
    let builder = Arc::new(DatabaseConfigBuilder::new());
    let mut handles = vec![];

    for i in 0..10 {
        let b = Arc::clone(&builder);
        let handle = thread::spawn(move || {
            b.host(format!("db{}.example.com", i));
            b.port(5432 + i as u16);
            b.max_connections(50 + i * 10);
            b.timeout(Duration::from_secs(30 + i as u64));
            b.use_ssl(i % 2 == 0);
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let config = builder.build().unwrap();
    println!("Final config: {:?}", config);
}
```

### ThreadSanitizer Stress Testing

Compile and run the stress test with ThreadSanitizer enabled: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu builder_stress`. ThreadSanitizer instruments memory accesses and synchronization operations, reporting data races when unsynchronized conflicting accesses occur. With the Mutex-protected implementation, no races should be detected. The test output will show the final configuration, which may reflect an arbitrary interleaving of updates since threads do not coordinate their write order.

To deliberately introduce a race, create a variant that uses `Arc<UnsafeCell<BuilderState>>` without synchronization. Add to `src/builder.rs`:

```rust
use std::cell::UnsafeCell;

pub struct UnsafeConfigBuilder {
    state: Arc<UnsafeCell<BuilderState>>,
}

unsafe impl Send for UnsafeConfigBuilder {}
unsafe impl Sync for UnsafeConfigBuilder {}

impl UnsafeConfigBuilder {
    pub fn new() -> Self {
        Self {
            state: Arc::new(UnsafeCell::new(BuilderState::new())),
        }
    }

    pub fn host(&self, host: String) -> &Self {
        unsafe {
            (*self.state.get()).host = Some(host);
        }
        self
    }

    pub fn port(&self, port: u16) -> &Self {
        unsafe {
            (*self.state.get()).port = Some(port);
        }
        self
    }

    pub fn build(&self) -> Result<DatabaseConfig, String> {
        unsafe {
            let state = &*self.state.get();
            state.validate()?;
            let owned_state = BuilderState {
                host: state.host.clone(),
                port: state.port,
                max_connections: state.max_connections,
                timeout: state.timeout,
                use_ssl: state.use_ssl,
            };
            Ok(owned_state.build())
        }
    }
}
```

Create a test for this unsafe builder in `tests/builder_stress.rs`:

```rust
#[test]
fn unsafe_concurrent_builder_stress_test() {
    let builder = Arc::new(design_patterns_lab::builder::UnsafeConfigBuilder::new());
    let mut handles = vec![];

    for i in 0..10 {
        let b = Arc::clone(&builder);
        let handle = thread::spawn(move || {
            b.host(format!("db{}.example.com", i));
            b.port(5432 + i as u16);
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let config = builder.build().unwrap();
    println!("Unsafe final config: {:?}", config);
}
```

Run ThreadSanitizer on this test: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu unsafe_concurrent_builder_stress_test`. ThreadSanitizer will report data races on the `host` and `port` fields, pinpointing the exact source lines where unsynchronized writes occur. The output includes stack traces showing the conflicting accesses from different threads, demonstrating that ThreadSanitizer correctly detects the undefined behavior introduced by the unsafe implementation.

### LeakSanitizer and Memory Ownership Verification

LeakSanitizer detects memory leaks by tracking heap allocations and verifying that all allocations are eventually freed. Rust's ownership system prevents most leaks statically, but `Arc` cycles, manual memory management via `Box::into_raw`, and FFI boundaries can introduce leaks. To test for leaks, deliberately create a leak scenario by cloning the builder's internal `Arc` and never dropping it. Add to `src/builder.rs`:

```rust
pub fn leak_builder_state(builder: &DatabaseConfigBuilder) {
    let leaked = Arc::clone(&builder.state);
    std::mem::forget(leaked);
}
```

Create a test in `tests/builder_leak.rs`:

```rust
use design_patterns_lab::builder::{DatabaseConfigBuilder, leak_builder_state};

#[test]
fn test_builder_leak() {
    let builder = DatabaseConfigBuilder::new();
    builder.host("leak.example.com".to_string());
    leak_builder_state(&builder);
    // Builder's Arc is now leaked
}
```

Compile and run with LeakSanitizer: `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu test_builder_leak`. LeakSanitizer will report a memory leak, showing the allocation stack trace where the `Arc` was created. In production code, leaks are often subtler, arising from circular `Arc` references or forgotten `Box::into_raw` calls. LeakSanitizer provides the diagnostic evidence needed to trace and eliminate these issues.

To verify that the normal builder path does not leak, run the original stress test with LeakSanitizer: `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu concurrent_builder_stress_test`. No leaks should be reported, confirming that the builder's lifecycle is correctly managed.

### Lock Contention Profiling with Perf

Mutex contention occurs when threads block waiting to acquire a lock, degrading throughput and introducing latency spikes. Use `perf` to measure lock contention by profiling blocked time. First, create a high-contention benchmark in `benches/builder_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use design_patterns_lab::builder::DatabaseConfigBuilder;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

fn bench_concurrent_builder(c: &mut Criterion) {
    c.bench_function("concurrent_builder_high_contention", |b| {
        b.iter(|| {
            let builder = Arc::new(DatabaseConfigBuilder::new());
            let mut handles = vec![];

            for i in 0..100 {
                let b = Arc::clone(&builder);
                let handle = thread::spawn(move || {
                    for _ in 0..10 {
                        b.host(format!("db{}.example.com", i));
                        b.port(5432);
                        b.max_connections(100);
                    }
                });
                handles.push(handle);
            }

            for handle in handles {
                handle.join().unwrap();
            }

            black_box(builder.build().unwrap());
        });
    });
}

criterion_group!(benches, bench_concurrent_builder);
criterion_main!(benches);
```

Register the benchmark in `Cargo.toml` and compile in release mode: `cargo build --release --bench builder_bench`. Run `perf` with lock profiling: `perf record -e sched:sched_stat_blocked -g -- target/release/deps/builder_bench-* --bench`. This records thread blocking events and call stacks. Generate a flamegraph from the perf data: `perf script | stackcollapse-perf.pl | flamegraph.pl > lock_contention.svg`. The flamegraph will show stack traces where threads spend time blocked on Mutex acquisition, highlighting the `Mutex::lock` calls in the builder methods.

To reduce contention, refactor the builder to use atomic operations for independent fields. Replace the `Mutex<BuilderState>` with separate `AtomicU16` for port and `AtomicBool` for SSL, leaving only the `String` fields under a lock. Implement `AtomicConfigBuilder` in `src/builder.rs`:

```rust
use std::sync::atomic::{AtomicBool, AtomicU16, AtomicU32, Ordering};

pub struct AtomicConfigBuilder {
    host: Arc<Mutex<Option<String>>>,
    port: AtomicU16,
    max_connections: AtomicU32,
    timeout: Arc<Mutex<Option<Duration>>>,
    use_ssl: AtomicBool,
}

impl AtomicConfigBuilder {
    pub fn new() -> Self {
        Self {
            host: Arc::new(Mutex::new(None)),
            port: AtomicU16::new(5432),
            max_connections: AtomicU32::new(100),
            timeout: Arc::new(Mutex::new(None)),
            use_ssl: AtomicBool::new(false),
        }
    }

    pub fn host(&self, host: String) {
        let mut h = self.host.lock().unwrap();
        *h = Some(host);
    }

    pub fn port(&self, port: u16) {
        self.port.store(port, Ordering::Relaxed);
    }

    pub fn max_connections(&self, max_connections: u32) {
        self.max_connections.store(max_connections, Ordering::Relaxed);
    }

    pub fn timeout(&self, timeout: Duration) {
        let mut t = self.timeout.lock().unwrap();
        *t = Some(timeout);
    }

    pub fn use_ssl(&self, use_ssl: bool) {
        self.use_ssl.store(use_ssl, Ordering::Relaxed);
    }

    pub fn build(&self) -> Result<DatabaseConfig, String> {
        let host = self.host.lock().unwrap();
        if host.is_none() {
            return Err("Host is required".to_string());
        }

        let timeout = self.timeout.lock().unwrap();

        Ok(DatabaseConfig {
            host: host.clone().unwrap(),
            port: self.port.load(Ordering::Relaxed),
            max_connections: self.max_connections.load(Ordering::Relaxed),
            timeout: timeout.unwrap_or(Duration::from_secs(30)),
            use_ssl: self.use_ssl.load(Ordering::Relaxed),
        })
    }
}
```

Benchmark this atomic implementation and compare the throughput and lock contention profiles. The atomic approach eliminates contention for numeric fields, reducing blocked time at the cost of weaker ordering guarantees. For configuration builders where field updates are independent, this tradeoff is usually acceptable.

### Miri Undefined Behavior Detection

Miri is an interpreter for Rust's mid-level intermediate representation that detects undefined behavior such as invalid pointer dereferences, use-after-free, and data races not caught by ThreadSanitizer. Run Miri on the unsafe builder test: `cargo +nightly miri test unsafe_concurrent_builder_stress_test`. Miri will report data races with precise stack traces, often catching issues that ThreadSanitizer misses due to timing-dependent detection. Miri's exhaustive checking makes it slower than sanitizers but more reliable for correctness verification.

To test for use-after-free, introduce a deliberate error by leaking a reference and accessing it after the builder is dropped. Add to `tests/builder_uaf.rs`:

```rust
use design_patterns_lab::builder::DatabaseConfigBuilder;

#[test]
fn test_use_after_free() {
    let builder = DatabaseConfigBuilder::new();
    builder.host("uaf.example.com".to_string());
    
    let state_ptr = {
        let state_guard = builder.state.lock().unwrap();
        &*state_guard as *const _
    };
    
    drop(builder);
    
    // Accessing state_ptr here is use-after-free
    unsafe {
        let _ = (*state_ptr).host.clone();
    }
}
```

Run this test under Miri: `cargo +nightly miri test test_use_after_free`. Miri will report a use-after-free error, identifying the exact line where the dangling pointer is dereferenced. In real systems, such errors often arise from FFI boundaries or manual lifetime management in unsafe code blocks.

## Developer Cheat Sheet & Toolchain Checklist

This checklist consolidates the essential commands, tooling workflows, and diagnostic procedures covered in the exercises. Use this as a reference for integrating pattern verification into your daily development cycle.

### Environment Setup and Verification

Install Rust toolchain: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
Install nightly toolchain: `rustup toolchain install nightly`
Add Miri component: `rustup +nightly component add miri`
Install LLVM tools: `sudo apt install clang-18 llvm-18 lld-18 lldb-18`
Install performance profiling: `sudo apt install linux-tools-generic valgrind`
Install Rust profiling extensions: `cargo install flamegraph cargo-bloat`
Verify sanitizer support: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu`

### Compilation and Inspection

Emit LLVM IR: `cargo rustc --release --lib -- --emit=llvm-ir`
Locate IR output: `target/release/deps/<crate>-*.ll`
Disassemble release binary: `objdump -d -C target/release/lib<crate>.so > output.asm`
Analyze binary size by symbol: `cargo bloat --release -n 50`
Check for monomorphization bloat: `cargo bloat --release --crates`

### Performance Benchmarking

Run Criterion benchmarks: `cargo bench --bench <name>`
View HTML reports: `open target/criterion/report/index.html`
Generate flamegraph with perf: `cargo flamegraph --bench <name> --root -- --bench`
Measure hardware counters: `perf stat -e cycles,instructions,cache-misses,branch-misses cargo bench --bench <name>`

### Cache Profiling

Run Cachegrind simulation: `valgrind --tool=cachegrind --cachegrind-out-file=out.cachegrind target/release/<binary>`
Annotate cache misses: `cg_annotate out.cachegrind`
Measure L1 data cache misses: `perf stat -e L1-dcache-load-misses,L1-dcache-loads cargo test --release`
Measure L1 instruction cache misses: `perf stat -e L1-icache-load-misses,L1-icache-loads cargo test --release`

### Concurrency Verification

Run ThreadSanitizer: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu`
Run AddressSanitizer: `RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu`
Run LeakSanitizer: `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly test --target x86_64-unknown-linux-gnu`
Run Miri for undefined behavior: `cargo +nightly miri test`

### Lock Contention Analysis

Profile lock blocking events: `perf record -e sched:sched_stat_blocked -g -- target/release/<binary>`
Generate contention flamegraph: `perf script | stackcollapse-perf.pl | flamegraph.pl > contention.svg`
Measure futex system call overhead: `perf stat -e syscalls:sys_enter_futex cargo bench --bench <name>`

### Debugging and Inspection

Attach LLDB to running process: `lldb target/release/<binary>`
Set breakpoint on function: `(lldb) breakpoint set --name function_name`
Inspect Rust variables: `(lldb) frame variable -D`
Run GDB with Rust pretty-printers: `rust-gdb target/release/<binary>`

### Continuous Integration Integration

Add sanitizer job to CI: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --all-targets --target x86_64-unknown-linux-gnu`
Run Miri in CI: `cargo +nightly miri test --all-features`
Benchmark regression detection: `cargo bench -- --save-baseline main` then `cargo bench -- --baseline main`
Cache profile regression: Store Cachegrind outputs and compare `cg_diff baseline.cachegrind current.cachegrind`

### Pattern-Specific Verification Strategies

Strategy pattern dispatch cost: Benchmark trait objects vs generics vs enum dispatch, measure with `perf stat` branch-misses and L1-icache-misses.
Observer pattern cache locality: Profile with Cachegrind D1 miss rates, refactor to arena allocation or enum dispatch for hot paths.
Builder pattern thread safety: Verify with ThreadSanitizer and Miri, profile lock contention with `perf record sched:sched_stat_blocked`, consider atomic operations for independent fields.
Singleton pattern lazy initialization: Verify thread-safe initialization with ThreadSanitizer, measure initialization overhead with `perf`, consider `OnceCell` or `LazyLock` for zero-overhead after first access.

### Memory Ordering and Atomics

For lock-free patterns using atomics, verify ordering constraints: `Relaxed` for independent operations, `Acquire`/`Release` for synchronization, `SeqCst` for total order. Run Miri to detect ordering violations: `cargo +nightly miri test`. Profile atomic contention with `perf c2c` (cache-to-cache) analysis on x86: `perf c2c record -- target/release/<binary>` then `perf c2c report`.

### Final Verification Workflow

Before committing pattern implementations, execute the following sequence: first, run all tests with sanitizers enabled to detect memory errors and data races; second, benchmark against baseline to verify performance invariants; third, profile cache behavior with Cachegrind to identify regressions; fourth, generate flamegraphs to confirm no unexpected hot spots; fifth, run Miri for exhaustive undefined behavior detection; finally, verify that release builds strip debug symbols and achieve expected binary size with `cargo bloat`. This workflow ensures that pattern abstractions maintain both correctness and performance properties across the full stack from high-level design to machine code.
