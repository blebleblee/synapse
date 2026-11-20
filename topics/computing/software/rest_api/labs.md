# Operational Verification Labs: Rest Api

## Objective & Toolchain Setup

Modern REST API implementations present a deceptively complex systems programming challenge that extends far beyond surface-level HTTP routing. At the boundary between application logic and network transport, REST endpoints become high-frequency execution paths where memory allocation patterns, concurrent access to shared state, JSON serialization overhead, and TCP socket management directly determine throughput, latency distribution, and failure modes under production load. This laboratory guide transforms REST API development from ad-hoc scripting into rigorous systems verification by instrumenting the full stack—from application-level request handlers down through runtime allocators, thread schedulers, and kernel network buffers—using compiler introspection, dynamic sanitizers, and performance profilers native to modern systems toolchains.

The verification workflow established here treats REST APIs as distributed systems components requiring three-dimensional analysis: structural correctness of compiled artifacts (AST and intermediate representation analysis), runtime performance characteristics under realistic concurrency and payload distributions (cache profiling and throughput measurement), and memory safety guarantees across concurrent request lifecycles (race detection and leak analysis). Each exercise builds a concrete diagnostic capability that translates directly to production troubleshooting: identifying hot allocation paths that fragment heap memory, detecting data races in request-scoped middleware, quantifying cache miss rates in JSON serialization routines, and validating cleanup of connection state after socket closure.

The primary implementation language is Rust, leveraging the Actix-web framework for its zero-copy HTTP parsing and lock-free routing table, with comparative examples in Go using the standard `net/http` package and C++ using Boost.Beast for protocol-level control. The Rust toolchain provides LLVM-based sanitizers (AddressSanitizer, ThreadSanitizer, LeakSanitizer) through direct Cargo integration, while performance profiling employs `perf` for CPU event sampling, `cargo-flamegraph` for stack trace aggregation, and `valgrind --tool=cachegrind` for cache simulation. All exercises execute against localhost endpoints with controlled request distributions to isolate behavior from network variance, establishing repeatable baselines for commit-to-commit performance regression detection.

Begin by installing the complete systems verification toolchain. On Debian-based Linux distributions, install the LLVM infrastructure and GNU debugging utilities with `apt install -y clang llvm lld gdb valgrind linux-tools-generic`. The `linux-tools-generic` package provides the `perf` system profiler which requires kernel symbol access; verify availability with `perf --version` and ensure `/proc/sys/kernel/perf_event_paranoid` is set to 1 or lower for non-root profiling. Install the Rust toolchain using the official `rustup` installer: execute `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` and select the stable channel. After installation, add Cargo's binary directory to your shell path with `source $HOME/.cargo/env`. Verify the installation by running `rustc --version` and `cargo --version`; the output should indicate Rust version 1.83 or newer for compatibility with the latest LLVM sanitizer integrations.

Install the flame graph generation toolkit with `cargo install flamegraph` and the criterion benchmarking harness with `cargo install cargo-criterion`. The `flamegraph` tool wraps `perf record` and processes the resulting profile data into interactive SVG visualizations showing aggregate stack traces weighted by sample frequency. To enable debug symbols in release builds—critical for meaningful stack traces in profiling—create a global Cargo configuration at `~/.cargo/config.toml` with the following content:

```toml
[profile.release]
debug = true
strip = false
lto = "thin"
codegen-units = 16

[profile.bench]
debug = true
inherits = "release"
```

This configuration preserves DWARF debug information while maintaining release-mode optimizations, enables thin link-time optimization to eliminate dead code across compilation units, and sets 16 codegen units to balance parallel compilation speed with runtime performance. The `inherits` directive ensures benchmark profiles receive the same optimization and debug settings as release builds.

For Go-based comparative exercises, install the official Go toolchain version 1.22 or newer from the distribution repository or download directly from `go.dev`. Go's native profiling tools `pprof` and `trace` integrate directly with the standard library's `net/http/pprof` package, exposing runtime profiles through HTTP endpoints. For C++ examples using Boost.Beast, install the development headers with `apt install -y libboost-all-dev` and ensure CMake version 3.20 or newer is available for build configuration.

Create a dedicated workspace directory for all laboratory exercises with `mkdir -p ~/rest-api-labs && cd ~/rest-api-labs`. Initialize a new Rust project with `cargo new --lib rest-bench && cd rest-bench`, which creates a library crate suitable for housing both application code and integrated benchmark suites. Open `Cargo.toml` and replace its contents with the following dependency specification:

```toml
[package]
name = "rest-bench"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4.5"
actix-rt = "2.9"
tokio = { version = "1.36", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
env_logger = "0.11"
log = "0.4"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
reqwest = { version = "0.11", features = ["json", "blocking"] }

[[bench]]
name = "api_throughput"
harness = false

[profile.release]
debug = true
lto = "thin"
```

The dependency manifest establishes Actix-web as the primary HTTP server framework, Tokio as the underlying async runtime, and Serde for zero-copy JSON serialization through derive macros. The `criterion` benchmark harness provides statistical rigor with outlier detection and baseline comparison. The `reqwest` HTTP client enables load generation from within benchmark code, using blocking mode to avoid async runtime nesting complexity during profiling.

With the toolchain installed and workspace configured, each subsequent exercise follows a diagnostic cycle: implement a representative API endpoint exhibiting specific behavior (allocation patterns, concurrency patterns, or computational hotspots), compile with targeted instrumentation flags, execute under controlled load, capture profiling artifacts, interpret the diagnostic output to identify bottlenecks or defects, and apply targeted optimizations. This methodology mirrors production incident response workflows where engineers instrument live services, capture profiles during anomalous behavior, and validate fixes through before-and-after performance comparison.

## Exercise 1: AST, IR & Disassembly Analysis

The first verification exercise establishes structural inspection capabilities by analyzing the compilation pipeline artifacts generated from a minimal REST API endpoint. While high-level source code expresses programmer intent, the actual runtime behavior emerges from machine code generated through multiple intermediate transformations: lexical analysis and parsing into an abstract syntax tree, type inference and borrow checking, translation to LLVM intermediate representation, target-specific instruction selection, register allocation, and final assembly emission. Each transformation stage introduces optimization opportunities and potential failure modes invisible at the source level. By inspecting AST structure, IR optimization passes, and disassembled machine code, engineers gain ground truth about what instructions actually execute, how data structures map to memory, and which compiler assumptions hold under specific usage patterns.

Create a new source file at `src/lib.rs` containing a deliberately simple REST endpoint that accepts JSON payloads and returns computed responses. This baseline implementation will serve as the subject for all compilation stage analyses:

```rust
use actix_web::{web, App, HttpServer, HttpResponse, Result};
use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

#[derive(Deserialize)]
pub struct ComputeRequest {
    pub values: Vec<f64>,
    pub iterations: u32,
}

#[derive(Serialize)]
pub struct ComputeResponse {
    pub result: f64,
    pub request_id: u64,
    pub allocations: usize,
}

pub struct AppState {
    pub request_counter: AtomicU64,
}

pub async fn compute_handler(
    req: web::Json<ComputeRequest>,
    state: web::Data<Arc<AppState>>,
) -> Result<HttpResponse> {
    let request_id = state.request_counter.fetch_add(1, Ordering::Relaxed);
    
    let mut accumulator = 0.0f64;
    for _ in 0..req.iterations {
        for &value in &req.values {
            accumulator += value.sqrt().sin().cos();
        }
    }
    
    let allocations = req.values.capacity();
    
    Ok(HttpResponse::Ok().json(ComputeResponse {
        result: accumulator,
        request_id,
        allocations,
    }))
}

pub fn create_app(state: Arc<AppState>) -> App<
    impl actix_web::dev::ServiceFactory<
        actix_web::dev::ServiceRequest,
        Config = (),
        Response = actix_web::dev::ServiceResponse,
        Error = actix_web::Error,
        InitError = (),
    >,
> {
    App::new()
        .app_data(web::Data::new(state))
        .route("/compute", web::post().to(compute_handler))
}

#[cfg(test)]
mod tests {
    use super::*;
    use actix_web::{test, web};

    #[actix_rt::test]
    async fn test_compute_endpoint() {
        let state = Arc::new(AppState {
            request_counter: AtomicU64::new(0),
        });
        let app = test::init_service(create_app(state)).await;
        
        let req = test::TestRequest::post()
            .uri("/compute")
            .set_json(ComputeRequest {
                values: vec![1.0, 2.0, 3.0, 4.0],
                iterations: 100,
            })
            .to_request();
        
        let resp: ComputeResponse = test::call_and_read_body_json(&app, req).await;
        assert_eq!(resp.request_id, 0);
        assert!(resp.result.is_finite());
    }
}
```

This endpoint implements a compute-bound operation that performs transcendental math functions (`sqrt`, `sin`, `cos`) across a variable-length vector for a configurable iteration count, modeling CPU-intensive API workloads like numerical optimization, data transformation, or cryptographic operations. The `AppState` structure holds an atomic counter tracking total requests processed, demonstrating shared mutable state management across concurrent handlers. The response includes the vector's heap capacity to expose allocation behavior during deserialization.

Before analyzing compilation artifacts, verify the implementation builds and passes tests with `cargo test`. The output should indicate successful compilation and test execution, confirming the code is syntactically and semantically valid. Now begin the inspection workflow by examining the compiler's abstract syntax tree representation. Rust's compiler (`rustc`) exposes internal data structures through the `-Z` unstable feature flags, requiring nightly toolchain installation. Install the nightly channel with `rustup install nightly` and set it as the active toolchain for this project with `rustup override set nightly`.

Generate the AST dump with `cargo rustc -- -Z unpretty=ast-tree > ast_dump.txt`. The resulting file contains a hierarchical tree representation of the source code after macro expansion and syntactic desugaring. Open `ast_dump.txt` and locate the `compute_handler` function node. The AST reveals how Rust's syntax sugar expands: the `async fn` keyword desugars into a state machine generator that implements the `Future` trait, `web::Json<ComputeRequest>` expands into an extractor that deserializes HTTP body bytes through Serde, and the `for` loop over `&req.values` becomes an iterator protocol invocation calling `IntoIterator::into_iter` followed by repeated `Iterator::next` calls. This structural visibility is critical when debugging macro-heavy code where source-level line numbers no longer correspond to actual execution paths.

Proceed to the intermediate representation level by generating LLVM IR, the compiler's platform-independent optimization target. Compile the library with IR emission enabled using `cargo rustc --release -- --emit=llvm-ir`. This creates a `.ll` file in the `target/release/deps/` directory with a name matching the crate and hash identifier. Locate the file with `find target/release/deps -name "*.ll"` and examine it with a text editor. Search for the `compute_handler` function by looking for a mangled symbol containing `compute_handler` in its name—Rust uses name mangling to encode type information into symbols for linking.

The LLVM IR representation exposes optimization transformations invisible at the source level. Locate the inner computation loop performing `sqrt`, `sin`, and `cos` operations. In optimized IR, these high-level operations become calls to LLVM intrinsics like `@llvm.sqrt.f64`, `@llvm.sin.f64`, and `@llvm.cos.f64`, which the backend lowers to target-specific vector instructions when available. Examine the loop structure: the optimizer may have unrolled the iteration over `req.values`, creating multiple sequential operations per loop iteration to improve instruction-level parallelism. Look for `phi` nodes representing loop-carried dependencies—these SSA (static single assignment) constructs track how the `accumulator` variable evolves across iterations.

Note the absence of bounds checking in the optimized IR. Rust's iterator protocol guarantees that `for &value in &req.values` cannot exceed the slice bounds, allowing the compiler to eliminate the range check that would be present in manual indexing code like `req.values[i]`. This zero-cost abstraction demonstrates how high-level constructs can produce machine code equivalent to or better than hand-written low-level operations. Record the number of basic blocks in the loop body by counting labels; fewer blocks indicate more aggressive inlining and branch elimination.

Descend to the final assembly representation with `cargo rustc --release -- --emit=asm`. Similar to IR emission, this creates a `.s` file in the dependency output directory. Locate it with `find target/release/deps -name "*.s"` and open the assembly file. Search again for the mangled `compute_handler` symbol. The assembly listing shows the actual machine instructions that execute on the target CPU, including x86-64 specific details like register allocation, calling conventions, and instruction selection.

Examine the loop body's assembly instructions. Modern x86-64 CPUs provide vector floating-point instructions in the SSE and AVX instruction sets; look for instructions like `vsqrtsd`, `vsinsd`, and `vcossd` operating on XMM or YMM registers. These single-instruction operations replace the software transcendental function implementations that would be required on architectures lacking hardware support. Identify the loop counter and accumulator registers: the counter likely resides in a general-purpose register like `rcx` or `r12`, while the accumulator uses a vector register like `xmm0`. Count the instructions per loop iteration; fewer instructions indicate better optimization.

Locate the stack frame setup prologue and epilogue at the function entry and exit. The prologue typically saves callee-saved registers and allocates local stack space, while the epilogue restores registers and deallocates the frame. Measure the stack frame size by examining the `sub rsp, <immediate>` instruction in the prologue—the immediate value indicates total bytes allocated. A large frame suggests many spilled registers or stack-allocated local variables, potentially impacting cache utilization. Compare the frame size against the source-level variable count: if the source declares four local variables but the frame allocates 128 bytes, the compiler is spilling intermediate values during register allocation.

To validate the absence of unnecessary runtime checks, search the assembly for `ud2` instructions, which Rust inserts at unreachable code paths to trigger CPU exceptions if executed. The presence of `ud2` in reachable code indicates potential panic paths from unwrap operations, array bounds violations, or integer overflows in debug mode. In release mode with overflow checks disabled, these should not appear in hot paths.

Switch back to the stable toolchain with `rustup override set stable` to restore normal development workflow. The nightly-only AST and IR inspection tools are diagnostic aids, not daily-use requirements. Create a shell script to automate artifact generation for future analyses. Write the following to `scripts/inspect_compilation.sh`:

```bash
#!/bin/bash
set -e

echo "Building release binary with debug symbols..."
cargo build --release

echo "Generating LLVM IR..."
cargo rustc --release -- --emit=llvm-ir
IR_FILE=$(find target/release/deps -name "*.ll" -type f | head -n 1)
echo "IR written to: $IR_FILE"

echo "Generating assembly..."
cargo rustc --release -- --emit=asm
ASM_FILE=$(find target/release/deps -name "*.s" -type f | head -n 1)
echo "Assembly written to: $ASM_FILE"

echo "Disassembling compute_handler function..."
BINARY=$(find target/release/deps -name "librest_bench-*.so" -type f | head -n 1)
if [ -n "$BINARY" ]; then
    objdump -d -C --section=.text "$BINARY" | grep -A 100 "compute_handler" > disasm_handler.txt
    echo "Disassembly written to: disasm_handler.txt"
fi

echo "Compilation artifacts generated successfully."
```

Make the script executable with `chmod +x scripts/inspect_compilation.sh` and run it with `./scripts/inspect_compilation.sh`. This automated workflow generates all three artifact types in a single invocation, establishing a repeatable baseline for comparing optimization changes across code revisions.

The disassembly inspection using `objdump` provides an alternative view to raw assembly files, showing the final linked code with resolved symbols and memory addresses. The `-C` flag demangles Rust symbols into human-readable names, while `--section=.text` restricts output to the executable code section. The `grep -A 100` command extracts 100 lines following the function entry point, capturing the complete implementation for moderately sized functions.

Extend the analysis by examining the symbol table to identify which functions the linker retained and which were eliminated through dead code analysis. Run `nm --demangle --defined-only target/release/deps/librest_bench-*.so | grep compute` to list all defined symbols containing "compute" in their demangled names. The output reveals whether the compiler inlined helper functions or retained them as separate call targets. If `compute_handler` appears but no other compute-related symbols exist, all helpers were successfully inlined. Conversely, retained symbols indicate separate functions that may benefit from manual inlining via the `#[inline]` attribute.

Compare symbol visibility across optimization levels by building in debug mode with `cargo build` and extracting symbols from `target/debug/deps/librest_bench-*.so`. Debug builds retain many more symbols due to disabled inlining, including monomorphized generic functions and trait method implementations. Count the total symbol count in each build with `nm --defined-only <binary> | wc -l`: debug builds often contain 5-10x more symbols than release builds, quantifying the optimization impact.

This exercise establishes the foundation for performance optimization by making compiler decisions observable. When profiling later identifies a hot function, return to these artifacts to understand what machine code actually executes, whether bounds checks remain, if loops vectorized, and how much stack space allocates. The inspection workflow transforms optimization from trial-and-error into hypothesis-driven engineering: propose a change, predict its IR or assembly transformation, verify through artifact inspection, and measure runtime impact.

## Exercise 2: Cache Miss & Throughput Profiling

The second exercise shifts from static compilation analysis to dynamic runtime profiling, instrumenting the REST API under realistic concurrent load to quantify memory hierarchy performance and request processing throughput. Modern CPU performance is dominated by the memory subsystem: while arithmetic operations complete in 1-4 cycles, cache misses to DRAM cost 200+ cycles, and each cache miss directly translates to idle CPU cycles waiting for data. REST APIs present particularly challenging cache behavior because request payloads, deserialized data structures, and response buffers continuously stream through memory without temporal reuse, defeating CPU cache prediction. Profiling cache miss rates and memory bandwidth utilization exposes optimization opportunities that source-level inspection cannot reveal: data structure layout changes to improve spatial locality, buffer reuse strategies, and algorithmic modifications to reduce working set size.

Begin by implementing a standalone HTTP server binary that runs the REST endpoint under controlled load. Create `src/main.rs` with the following server implementation:

```rust
use actix_web::{middleware, web, App, HttpServer};
use rest_bench::{create_app, AppState};
use std::sync::atomic::AtomicU64;
use std::sync::Arc;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    
    let state = Arc::new(AppState {
        request_counter: AtomicU64::new(0),
    });
    
    log::info!("Starting REST API server on http://127.0.0.1:8080");
    
    HttpServer::new(move || {
        create_app(state.clone())
            .wrap(middleware::Logger::default())
    })
    .bind("127.0.0.1:8080")?
    .workers(4)
    .run()
    .await
}
```

This server configuration uses four worker threads to handle concurrent requests, matching typical deployment configurations on quad-core development machines. The middleware logger emits request timing information for basic latency visibility. Build the server binary with `cargo build --release` and verify it starts successfully with `cargo run --release`. In a separate terminal, test the endpoint with `curl -X POST http://127.0.0.1:8080/compute -H "Content-Type: application/json" -d '{"values":[1.0,2.0,3.0],"iterations":100}'`. The response should return a JSON object with computed results.

Establish baseline throughput measurement using `wrk`, a modern HTTP load generator that reports latency distribution and request throughput. Install `wrk` from source since distribution packages are often outdated: clone the repository with `git clone https://github.com/wg/wrk.git && cd wrk` and compile with `make`. Copy the resulting binary to your local bin directory with `sudo cp wrk /usr/local/bin/`. Verify installation with `wrk --version`.

Create a load test script that exercises the compute endpoint with varying payload sizes. Write the following to `load_test.lua`:

```lua
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"

local payload_sizes = {10, 100, 1000}
local current_size = 1

request = function()
    local size = payload_sizes[current_size]
    current_size = current_size % #payload_sizes + 1
    
    local values = {}
    for i = 1, size do
        values[i] = tostring(math.random())
    end
    
    local body = string.format(
        '{"values":[%s],"iterations":1000}',
        table.concat(values, ",")
    )
    
    return wrk.format(nil, "/compute", nil, body)
end
```

This script cycles through three payload sizes—10, 100, and 1000 floating-point values—generating random input data for each request. The iteration count remains constant at 1000 to maintain consistent computational work per request. Launch the load test with `wrk -t4 -c100 -d60s --latency -s load_test.lua http://127.0.0.1:8080`. The flags configure 4 threads, 100 concurrent connections, a 60-second test duration, and latency histogram reporting.

Record the baseline results, focusing on three metrics: total requests per second (throughput), mean latency, and 99th percentile tail latency. Typical results on a 4-core system might show 8,000-12,000 req/s with mean latency around 8-10ms and p99 latency of 15-25ms. These numbers establish the performance envelope before optimization and provide the comparison baseline for cache-aware improvements.

Now instrument the server with CPU performance counters to capture cache miss rates during load. The Linux `perf` profiler directly accesses hardware performance monitoring units (PMUs) to count cache events without instrumentation overhead. Stop the running server and restart it under `perf` with `perf stat -e cache-references,cache-misses,cycles,instructions cargo run --release`. This command configures `perf` to count four hardware events: total cache accesses, cache misses, CPU cycles consumed, and instructions retired. The ratio of cache misses to cache references yields the miss rate percentage.

In the second terminal, run the same `wrk` load test. Allow it to complete the full 60-second duration to accumulate statistically significant event counts. When the load test finishes, stop the server with Ctrl+C. The `perf stat` output displays event counts and computed ratios:

```text
 Performance counter stats for 'cargo run --release':

    45,234,891,234      cache-references
     8,921,456,789      cache-misses              #   19.71% of all cache refs
   189,456,123,456      cycles
   234,567,890,123      instructions              #    1.24  insn per cycle

      60.234567890 seconds time elapsed
```

The cache miss rate of 19.71% indicates that nearly one in five cache accesses missed all levels and fetched from DRAM. This rate is typical for workloads with streaming data access patterns and indicates significant optimization potential. Calculate the average cycles per request by dividing total cycles by requests processed (visible in the `wrk` output): if the test completed 720,000 requests, each request consumed approximately 263,000 cycles. At a 3.0 GHz CPU frequency, this translates to 87 microseconds of CPU time per request, though much of this time is spent waiting on memory.

Profile cache behavior at a finer granularity using `perf record` to sample stack traces correlated with cache miss events. Stop the server and restart it with sampling enabled: `perf record -e cache-misses -c 10000 -g --call-graph dwarf cargo run --release`. The `-c 10000` flag samples one stack trace for every 10,000 cache miss events, balancing overhead against statistical accuracy. The `--call-graph dwarf` option uses DWARF debug information to unwind stack frames, providing complete call stacks even in optimized code.

Run the `wrk` load test again, allow it to complete, then stop the server. The `perf record` command writes profile data to `perf.data` in the current directory. Analyze the profile with `perf report --stdio` to generate a text-based report sorted by cache miss frequency. The output shows a hierarchical tree of functions ordered by sample count:

```bash
# Overhead  Command     Shared Object       Symbol
# ........  ..........  ..................  .................................
#
    23.45%  rest-bench  rest-bench          [.] rest_bench::compute_handler
                |
                ---rest_bench::compute_handler
                   actix_web::handler::Handler::call
                   actix_web::service::ServiceRequest::into_response
    
    18.32%  rest-bench  libc.so.6           [.] __sin_fma
    15.67%  rest-bench  libc.so.6           [.] __cos_fma
    12.89%  rest-bench  rest-bench          [.] serde_json::de::read::Read::parse_whitespace
     8.21%  rest-bench  rest-bench          [.] alloc::vec::Vec<T>::extend_from_slice
```

The report reveals that `compute_handler` itself accounts for 23.45% of cache misses, followed by the transcendental math library functions (`sin`, `cos`) and the JSON parser's whitespace handling. The `Vec::extend_from_slice` entry indicates allocation activity during vector deserialization, likely from resizing the backing buffer as the parser reads array elements.

Generate a visual flame graph to explore the cache miss call paths interactively. Install the flame graph toolkit with `git clone https://github.com/brendangregg/FlameGraph.git`. Convert the `perf.data` profile to the format expected by the flame graph scripts: `perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl --title="Cache Miss Flame Graph" > cache_misses.svg`. Open `cache_misses.svg` in a web browser. The flame graph visualizes stack traces as horizontal bars, with width proportional to sample frequency. Functions at the bottom of the stack are callers; functions at the top are callees. Click any bar to zoom into that subtree.

Identify the widest bars corresponding to the highest cache miss rates. The `compute_handler` bar should dominate the middle of the graph, with children representing the math operations and iterator traversal. The JSON deserialization path likely appears as a separate tower on the left, indicating distinct allocation and parsing overhead. Measure the relative width of the allocation path versus the computation path: if allocation consumes more than 20% of total samples, vector resizing during deserialization is a significant bottleneck.

Optimize the cache miss behavior by preallocating the input vector to eliminate reallocation during deserialization. Serde's deserializer implementation for `Vec<T>` calls `Vec::with_capacity` using a hint from the JSON array length, but this hint may be inaccurate for large payloads. Modify the `ComputeRequest` type to enforce a maximum size and preallocate accordingly. Update `src/lib.rs`:

```rust
#[derive(Deserialize)]
pub struct ComputeRequest {
    #[serde(deserialize_with = "deserialize_bounded_vec")]
    pub values: Vec<f64>,
    pub iterations: u32,
}

fn deserialize_bounded_vec<'de, D>(deserializer: D) -> Result<Vec<f64>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    use serde::de::{SeqAccess, Visitor};
    use std::fmt;

    struct BoundedVecVisitor;

    impl<'de> Visitor<'de> for BoundedVecVisitor {
        type Value = Vec<f64>;

        fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
            formatter.write_str("a sequence of f64 values")
        }

        fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            let capacity = seq.size_hint().unwrap_or(0).min(2048);
            let mut vec = Vec::with_capacity(capacity);
            
            while let Some(value) = seq.next_element()? {
                if vec.len() >= 2048 {
                    return Err(serde::de::Error::custom("array too large"));
                }
                vec.push(value);
            }
            
            Ok(vec)
        }
    }

    deserializer.deserialize_seq(BoundedVecVisitor)
}
```

This custom deserializer caps vector capacity at 2048 elements and rejects arrays exceeding this limit, preventing unbounded memory allocation from untrusted payloads. The preallocated capacity eliminates incremental resizing, reducing allocation system calls and improving cache behavior through contiguous storage.

Rebuild the server with `cargo build --release` and repeat the profiling workflow: run `wrk` under `perf record`, collect cache miss samples, and regenerate the flame graph. Compare the new flame graph against the baseline: the allocation path should shrink significantly, with more samples concentrated in the computation loop. Quantify the improvement by comparing miss rates from `perf stat` runs before and after optimization. A successful optimization reduces the miss rate by 3-5 percentage points and increases throughput by 10-15%.

Profile memory bandwidth utilization using `perf stat` with memory controller events. These events are architecture-specific; on Intel systems, use `perf stat -e uncore_imc/data_reads/,uncore_imc/data_writes/ cargo run --release`. On AMD systems, substitute `amd_df` events. Run the load test and examine memory traffic: data reads measure bytes transferred from DRAM to CPU, while data writes measure bytes written from CPU to DRAM. Divide these values by test duration to compute average bandwidth in GB/s.

Compare memory bandwidth against theoretical peak for your system. Most dual-channel DDR4-3200 configurations provide approximately 50 GB/s peak bandwidth. If profiling shows 15-20 GB/s sustained during load, the application is memory-bound and will not benefit from additional CPU cores. Conversely, bandwidth below 5 GB/s with high CPU utilization indicates a compute-bound workload where algorithmic improvements or vectorization provide greater benefit than cache optimization.

Create a benchmark suite using the Criterion framework to establish automated regression detection. Create `benches/api_throughput.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId, Throughput};
use rest_bench::{ComputeRequest, compute_handler, AppState};
use actix_web::{web, test, App};
use std::sync::Arc;
use std::sync::atomic::AtomicU64;

async fn benchmark_handler(values: Vec<f64>, iterations: u32) {
    let state = Arc::new(AppState {
        request_counter: AtomicU64::new(0),
    });
    
    let req = web::Json(ComputeRequest { values, iterations });
    let state_data = web::Data::new(state);
    
    let _ = compute_handler(req, state_data).await.unwrap();
}

fn throughput_benchmark(c: &mut Criterion) {
    let mut group = c.benchmark_group("compute_handler");
    
    for size in [10, 100, 1000].iter() {
        group.throughput(Throughput::Elements(*size as u64));
        group.bench_with_input(
            BenchmarkId::new("size", size),
            size,
            |b, &size| {
                let values: Vec<f64> = (0..size).map(|i| i as f64).collect();
                let rt = actix_rt::Runtime::new().unwrap();
                b.iter(|| {
                    rt.block_on(benchmark_handler(
                        black_box(values.clone()),
                        black_box(1000),
                    ))
                });
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, throughput_benchmark);
criterion_main!(benches);
```

This benchmark exercises the handler with three input sizes, measuring throughput in elements processed per second. The `black_box` calls prevent the compiler from optimizing away unused computations. Run the benchmark suite with `cargo bench` and observe the output:

```text
compute_handler/size/10   time:   [1.2345 ms 1.2389 ms 1.2435 ms]
                          thrpt:  [8.0420 Kelem/s 8.0717 Kelem/s 8.1008 Kelem/s]
compute_handler/size/100  time:   [11.234 ms 11.289 ms 11.347 ms]
                          thrpt:  [8.8134 Kelem/s 8.8591 Kelem/s 8.9025 Kelem/s]
compute_handler/size/1000 time:   [112.45 ms 113.21 ms 114.02 ms]
                          thrpt:  [8.7711 Kelem/s 8.8325 Kelem/s 8.8952 Kelem/s]
```

The benchmark reports reveal near-linear scaling of execution time with input size, confirming O(n) computational complexity. Throughput in elements per second remains relatively constant across sizes, indicating cache effects are minimal compared to computation cost. Store baseline results with `cargo bench -- --save-baseline initial` and compare future changes against this baseline with `cargo bench -- --baseline initial`.

Profile individual benchmark runs with `perf` by recording criterion's test harness execution. Modify the benchmark temporarily to run a single size configuration, then execute `perf record -g --call-graph dwarf cargo bench`. This captures fine-grained profiles of the benchmark iteration loop, isolating cache behavior from HTTP framework overhead. The resulting flame graph focuses exclusively on the handler logic, revealing optimization opportunities invisible during full server profiling where network and serialization dominate samples.

This exercise establishes the complete workflow for performance measurement and optimization: profile cache behavior under realistic load, identify bottlenecks through hierarchical stack sampling, apply targeted optimizations, verify improvements through automated benchmarks, and detect regressions in continuous integration through baseline comparison. The methodology extends to any performance-critical system component by substituting appropriate load generators and adjusting event counters to target-specific hardware resources.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

The final exercise addresses concurrent correctness and resource lifecycle management through dynamic sanitizer instrumentation. REST API servers inherently execute request handlers across multiple threads, sharing connection state, request counters, caches, and database connection pools. The Rust type system prevents most data races at compile time through the `Send` and `Sync` trait contracts, but unsafe code, incorrect synchronization primitives, and misuse of interior mutability can introduce races invisible to static analysis. Similarly, while Rust's ownership model eliminates many memory leaks, reference cycles involving `Rc<RefCell<T>>`, leaked threads, and incorrect manual memory management in unsafe blocks create persistent allocations. The ThreadSanitizer (TSAN) and LeakSanitizer (LSAN) dynamic analysis tools detect these runtime defects by instrumenting every memory access and allocation, reporting violations with precise stack traces identifying the conflicting operations.

Begin by implementing a deliberately flawed API endpoint that exhibits both data race and memory leak conditions. The endpoint maintains a request cache using shared mutable state with incorrect synchronization, and allocates resources during request processing without proper cleanup. Create `src/unsafe_endpoint.rs`:

```rust
use actix_web::{web, HttpResponse, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::RwLock;
use std::sync::Arc;
use std::cell::UnsafeCell;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CachedRequest {
    pub key: String,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone, Serialize)]
pub struct CacheResponse {
    pub hit: bool,
    pub data: Option<Vec<u8>>,
}

pub struct UnsafeCache {
    inner: UnsafeCell<HashMap<String, Vec<u8>>>,
}

unsafe impl Sync for UnsafeCache {}

impl UnsafeCache {
    pub fn new() -> Self {
        Self {
            inner: UnsafeCell::new(HashMap::new()),
        }
    }
    
    pub fn get(&self, key: &str) -> Option<Vec<u8>> {
        let map = unsafe { &*self.inner.get() };
        map.get(key).cloned()
    }
    
    pub fn insert(&self, key: String, value: Vec<u8>) {
        let map = unsafe { &mut *self.inner.get() };
        map.insert(key, value);
    }
}

pub struct LeakyState {
    pub cache: Arc<UnsafeCache>,
    pub leaked_allocations: Arc<RwLock<Vec<Box<[u8; 1024]>>>>,
}

pub async fn unsafe_cache_handler(
    req: web::Json<CachedRequest>,
    state: web::Data<Arc<LeakyState>>,
) -> Result<HttpResponse> {
    if let Some(data) = state.cache.get(&req.key) {
        return Ok(HttpResponse::Ok().json(CacheResponse {
            hit: true,
            data: Some(data),
        }));
    }
    
    state.cache.insert(req.key.clone(), req.data.clone());
    
    let leaked_box = Box::new([0u8; 1024]);
    if let Ok(mut leaks) = state.leaked_allocations.write() {
        leaks.push(leaked_box);
    }
    
    Ok(HttpResponse::Ok().json(CacheResponse {
        hit: false,
        data: Some(req.data.clone()),
    }))
}

pub fn create_unsafe_app(state: Arc<LeakyState>) -> actix_web::App<
    impl actix_web::dev::ServiceFactory<
        actix_web::dev::ServiceRequest,
        Config = (),
        Response = actix_web::dev::ServiceResponse,
        Error = actix_web::Error,
        InitError = (),
    >,
> {
    actix_web::App::new()
        .app_data(web::Data::new(state))
        .route("/unsafe_cache", web::post().to(unsafe_cache_handler))
}
```

This implementation contains multiple defects. The `UnsafeCache` type wraps a `HashMap` in `UnsafeCell`, implementing `Sync` manually to allow shared access across threads. However, the `get` and `insert` methods access the underlying `HashMap` without any synchronization, creating a data race: concurrent `insert` calls can corrupt the hash table structure, leading to use-after-free bugs, infinite loops during iteration, or incorrect lookup results. The `leaked_allocations` vector accumulates 1KB allocations on every cache miss, simulating a resource leak where memory allocated during request processing is never freed.

Update `src/lib.rs` to expose the unsafe endpoint module by adding `pub mod unsafe_endpoint;` at the top of the file. Create a test server that exercises the unsafe endpoint concurrently. Write `src/bin/unsafe_server.rs`:

```rust
use actix_web::{web, App, HttpServer};
use rest_bench::unsafe_endpoint::{create_unsafe_app, LeakyState, UnsafeCache};
use std::sync::Arc;
use std::sync::RwLock;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("info"));
    
    let state = Arc::new(LeakyState {
        cache: Arc::new(UnsafeCache::new()),
        leaked_allocations: Arc::new(RwLock::new(Vec::new())),
    });
    
    log::info!("Starting unsafe server on http://127.0.0.1:8081");
    
    HttpServer::new(move || {
        create_unsafe_app(state.clone())
    })
    .bind("127.0.0.1:8081")?
    .workers(4)
    .run()
    .await
}
```

Before running sanitizers, verify the endpoint compiles and responds to requests. Build with `cargo build --bin unsafe_server --release` and start the server with `cargo run --bin unsafe_server --release`. Test with `curl -X POST http://127.0.0.1:8081/unsafe_cache -H "Content-Type: application/json" -d '{"key":"test","data":[1,2,3,4]}'`. The initial request returns a cache miss; repeating the identical request returns a cache hit. Stop the server after verifying functionality.

Compile the server with ThreadSanitizer instrumentation to detect data races. TSAN requires rebuilding the entire dependency tree with instrumentation, which significantly increases compilation time. Set the target-specific rustflags in a local configuration file by creating `.cargo/config.toml`:

```toml
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=thread"]

[build]
target = "x86_64-unknown-linux-gnu"
```

Ensure the nightly toolchain is active with `rustup override set nightly` since sanitizers require unstable compiler features. Rebuild the unsafe server with `cargo clean && cargo build --bin unsafe_server`. The clean step is essential because mixing instrumented and non-instrumented object files causes linking failures.

Start the instrumented server with `TSAN_OPTIONS="halt_on_error=1 history_size=7" cargo run --bin unsafe_server`. The `TSAN_OPTIONS` environment variable configures sanitizer behavior: `halt_on_error=1` terminates immediately upon detecting the first race, preventing log spam from cascading failures, while `history_size=7` tracks the seven most recent memory accesses per thread for race reporting. In a second terminal, generate concurrent load with `wrk -t4 -c20 -d10s -s load_test.lua http://127.0.0.1:8081/unsafe_cache` (adjust the Lua script to use the `/unsafe_cache` path).

Within seconds, ThreadSanitizer detects the data race and terminates the server with a detailed report printed to stderr:

```text
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7f8a4c001a80 by thread T2:
    #0 hashbrown::raw::RawTable<K,V>::insert rest_bench/src/unsafe_endpoint.rs:35
    #1 std::collections::HashMap::insert hashmap.rs:1024
    #2 rest_bench::unsafe_endpoint::UnsafeCache::insert rest_bench/src/unsafe_endpoint.rs:35
    #3 rest_bench::unsafe_endpoint::unsafe_cache_handler rest_bench/src/unsafe_endpoint.rs:58
    #4 actix_web::handler::Handler::call handler.rs:89

  Previous read of size 8 at 0x7f8a4c001a80 by thread T4:
    #0 hashbrown::raw::RawTable<K,V>::find rest_bench/src/unsafe_endpoint.rs:28
    #1 std::collections::HashMap::get hashmap.rs:892
    #2 rest_bench::unsafe_endpoint::UnsafeCache::get rest_bench/src/unsafe_endpoint.rs:28
    #3 rest_bench::unsafe_endpoint::unsafe_cache_handler rest_bench/src/unsafe_endpoint.rs:53
    #4 actix_web::handler::Handler::call handler.rs:89

  Location is heap block of size 65536 allocated by main thread:
    #0 malloc tsan_interceptors.cc:123
    #1 alloc::alloc::alloc alloc.rs:98
    #2 hashbrown::raw::RawTable::new_uninitialized raw.rs:234

  Thread T2 (tid=12347) created by main thread
  Thread T4 (tid=12349) created by main thread
```

The report identifies the conflicting operations: thread T2 executed a write (insert) at line 35 while thread T4 executed a read (get) at line 28, both accessing the same memory location `0x7f8a4c001a80` within the `HashMap` backing buffer. The stack traces show the complete call chain from the HTTP handler through the cache methods into the standard library hash table implementation. The "Location" section indicates the memory was allocated as part of the hash table creation during server initialization.

Fix the data race by replacing `UnsafeCell` with proper synchronization. Modify `src/unsafe_endpoint.rs` to use `RwLock`:

```rust
use std::sync::RwLock;

pub struct UnsafeCache {
    inner: RwLock<HashMap<String, Vec<u8>>>,
}

impl UnsafeCache {
    pub fn new() -> Self {
        Self {
            inner: RwLock::new(HashMap::new()),
        }
    }
    
    pub fn get(&self, key: &str) -> Option<Vec<u8>> {
        self.inner.read().ok()?.get(key).cloned()
    }
    
    pub fn insert(&self, key: String, value: Vec<u8>) {
        if let Ok(mut map) = self.inner.write() {
            map.insert(key, value);
        }
    }
}
```

Remove the unsafe `Sync` implementation—`RwLock<T>` automatically implements `Sync` when `T: Send`. Rebuild with `cargo build --bin unsafe_server` and run under TSAN again. Generate load with `wrk`. This time, the server runs to completion without sanitizer violations, confirming the race is eliminated.

Now address the memory leak using LeakSanitizer. LSAN integrates with AddressSanitizer, sharing infrastructure for allocation tracking. Update `.cargo/config.toml` to enable address sanitization:

```toml
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=address"]

[build]
target = "x86_64-unknown-linux-gnu"
```

Clean and rebuild with `cargo clean && cargo build --bin unsafe_server`. Start the server with `ASAN_OPTIONS="detect_leaks=1" cargo run --bin unsafe_server`. Generate substantial load to accumulate leaked allocations: `wrk -t4 -c20 -d30s -s load_test.lua http://127.0.0.1:8081/unsafe_cache`. Stop the server with Ctrl+C after the load test completes.

Upon termination, LeakSanitizer performs a final sweep of allocated memory, identifying blocks without remaining references:

```text
=================================================================
==23456==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 524288 byte(s) in 512 object(s) allocated from:
    #0 malloc asan_malloc_linux.cc:145
    #1 alloc::alloc::alloc alloc.rs:98
    #2 alloc::alloc::box::Box::new boxed.rs:214
    #3 rest_bench::unsafe_endpoint::unsafe_cache_handler rest_bench/src/unsafe_endpoint.rs:60
    #4 actix_web::handler::Handler::call handler.rs:89

SUMMARY: AddressSanitizer: 524288 byte(s) leaked in 512 allocation(s).
```

The report identifies 512 leaked allocations totaling 512KB, matching the 1KB box allocated per cache miss. The stack trace points directly to line 60 in the handler where `Box::new([0u8; 1024])` executes. While the boxes are pushed into the `leaked_allocations` vector and thus technically remain reachable, they serve no purpose and accumulate unbounded, constituting a resource leak.

Fix the leak by removing the accumulation vector entirely—in a real application, this would involve ensuring proper cleanup of per-request resources. Modify the handler to eliminate the leak:

```rust
pub async fn unsafe_cache_handler(
    req: web::Json<CachedRequest>,
    state: web::Data<Arc<LeakyState>>,
) -> Result<HttpResponse> {
    if let Some(data) = state.cache.get(&req.key) {
        return Ok(HttpResponse::Ok().json(CacheResponse {
            hit: true,
            data: Some(data),
        }));
    }
    
    state.cache.insert(req.key.clone(), req.data.clone());
    
    Ok(HttpResponse::Ok().json(CacheResponse {
        hit: false,
        data: Some(req.data.clone()),
    }))
}
```

Rebuild and run under ASAN. After load testing and server termination, LSAN reports no leaks, confirming the fix.

Extend race detection to cover the original compute endpoint by testing under extreme concurrency. Switch back to the safe server binary and enable ThreadSanitizer. Update `.cargo/config.toml` to instrument the main binary:

```toml
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=thread"]
```

Rebuild the original server with `cargo clean && cargo build --release --bin rest-bench`. Run under TSAN with increased worker threads to amplify race potential: modify `src/main.rs` to set `.workers(16)`, then start with `cargo run --release`. Generate high concurrency load: `wrk -t16 -c500 -d60s -s load_test.lua http://127.0.0.1:8080`. TSAN should report no violations, validating that the atomic counter and immutable request data structures avoid races despite concurrent access.

Test for leaks in the safe endpoint by running under ASAN after a long-duration load test. Switch to address sanitization in `.cargo/config.toml`, rebuild, start the server, run a 5-minute load test, then stop the server and examine LSAN output. No leaks should appear, confirming that Actix-web's request lifecycle correctly deallocates buffers, parsed JSON structures, and response bodies.

Create an integration test that deliberately triggers sanitizer violations to validate CI detection. Write `tests/sanitizer_integration.rs`:

```rust
#[cfg(test)]
mod tests {
    use std::sync::Arc;
    use std::thread;
    use std::sync::atomic::{AtomicU64, Ordering};

    #[test]
    #[ignore]
    fn test_data_race_detection() {
        let counter = Arc::new(AtomicU64::new(0));
        let mut handles = vec![];
        
        for _ in 0..10 {
            let counter_clone = counter.clone();
            let handle = thread::spawn(move || {
                for _ in 0..1000 {
                    let val = counter_clone.load(Ordering::Relaxed);
                    counter_clone.store(val + 1, Ordering::Relaxed);
                }
            });
            handles.push(handle);
        }
        
        for handle in handles {
            handle.join().unwrap();
        }
        
        assert!(counter.load(Ordering::Relaxed) <= 10000);
    }
}
```

This test contains a race: the load-store sequence is not atomic, allowing lost updates. Run with `cargo test --test sanitizer_integration -- --ignored` under TSAN to verify detection. The test should fail with sanitizer violations reported.

Switch back to stable toolchain for daily development with `rustup override set stable`. Document the sanitizer workflow in a script. Write `scripts/run_sanitizers.sh`:

```bash
#!/bin/bash
set -e

echo "Running ThreadSanitizer..."
rustup override set nightly
cargo clean
cat > .cargo/config.toml << 'EOF'
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=thread"]
[build]
target = "x86_64-unknown-linux-gnu"
EOF

cargo build --bin unsafe_server
TSAN_OPTIONS="halt_on_error=1" cargo run --bin unsafe_server &
SERVER_PID=$!
sleep 2

echo "Generating load..."
wrk -t4 -c20 -d10s http://127.0.0.1:8081/compute
kill $SERVER_PID

echo "Running AddressSanitizer..."
cargo clean
cat > .cargo/config.toml << 'EOF'
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=address"]
[build]
target = "x86_64-unknown-linux-gnu"
EOF

cargo build --bin unsafe_server
ASAN_OPTIONS="detect_leaks=1" cargo run --bin unsafe_server &
SERVER_PID=$!
sleep 2

wrk -t4 -c20 -d10s http://127.0.0.1:8081/compute
kill $SERVER_PID
sleep 1

rm .cargo/config.toml
rustup override set stable
echo "Sanitizer checks complete."
```

Make the script executable with `chmod +x scripts/run_sanitizers.sh`. This automated workflow integrates into continuous integration pipelines, failing builds that introduce races or leaks.

This exercise completes the verification workflow by establishing dynamic correctness checks that complement static type system guarantees. Together with compilation artifact inspection and performance profiling, the sanitizer toolkit provides comprehensive visibility into REST API behavior across structural, performance, and correctness dimensions, enabling confident evolution of production systems under the pressures of scale and concurrency.

## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the essential commands, configuration patterns, and diagnostic workflows established throughout the laboratory exercises into a rapid-reference format optimized for operational use. The cheat sheet assumes the complete toolchain installation described in the setup section and provides copy-paste-ready invocations for common verification tasks.

**Compilation Artifact Inspection**

Generate LLVM IR for optimization analysis:
```bash
cargo rustc --release -- --emit=llvm-ir
find target/release/deps -name "*.ll" | head -n 1 | xargs less
```

Generate assembly listing with demangled symbols:
```bash
cargo rustc --release -- --emit=asm
find target/release/deps -name "*.s" | head -n 1 | xargs less
```

Disassemble specific function from compiled binary:
```bash
objdump -d -C --section=.text target/release/rest-bench | grep -A 50 "compute_handler"
```

Extract symbol table showing retained functions:
```bash
nm --demangle --defined-only target/release/librest_bench.so | grep -v " U "
```

**Cache and Performance Profiling**

Profile cache miss rate during load test:
```bash
perf stat -e cache-references,cache-misses,cycles,instructions cargo run --release
```

Sample cache miss call stacks:
```bash
perf record -e cache-misses -c 10000 -g --call-graph dwarf cargo run --release
perf report --stdio
```

Generate cache miss flame graph:
```bash
perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl > cache.svg
```

Measure memory bandwidth utilization (Intel):
```bash
perf stat -e uncore_imc/data_reads/,uncore_imc/data_writes/ cargo run --release
```

Profile individual benchmark with perf:
```bash
perf record -g --call-graph dwarf cargo bench --bench api_throughput
perf report --stdio
```

**Sanitizer Execution**

Configure and run ThreadSanitizer:
```bash
rustup override set nightly
cat > .cargo/config.toml << 'EOF'
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=thread"]
EOF
cargo clean && cargo build
TSAN_OPTIONS="halt_on_error=1 history_size=7" cargo run
```

Configure and run AddressSanitizer with leak detection:
```bash
cat > .cargo/config.toml << 'EOF'
[target.x86_64-unknown-linux-gnu]
rustflags = ["-Zsanitizer=address"]
EOF
cargo clean && cargo build
ASAN_OPTIONS="detect_leaks=1" cargo run
```

Run tests under ThreadSanitizer:
```bash
RUSTFLAGS="-Zsanitizer=thread" cargo test
```

**Load Generation and Throughput Measurement**

Basic throughput test with latency distribution:
```bash
wrk -t4 -c100 -d60s --latency http://127.0.0.1:8080/compute
```

Load test with custom Lua script:
```bash
wrk -t4 -c100 -d60s --latency -s load_test.lua http://127.0.0.1:8080
```

Generate sustained high-concurrency load:
```bash
wrk -t16 -c500 -d300s http://127.0.0.1:8080/compute
```

**Benchmark Execution and Regression Detection**

Run all benchmarks and save baseline:
```bash
cargo bench -- --save-baseline initial
```

Compare current performance against baseline:
```bash
cargo bench -- --baseline initial
```

Run benchmarks with CSV output for plotting:
```bash
cargo bench -- --output-format bencher | tee bench_results.txt
```

**Common Configuration Patterns**

Cargo.toml profile for profiling-friendly release builds:
```toml
[profile.release]
debug = true
strip = false
lto = "thin"
codegen-units = 16
```

Cargo.toml dependencies for REST API development:
```toml
[dependencies]
actix-web = "4.5"
tokio = { version = "1.36", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
reqwest = { version = "0.11", features = ["json", "blocking"] }
```

**Diagnostic Workflow Decision Tree**

For throughput degradation: profile with `perf record`, generate flame graph, identify hot functions, inspect disassembly, optimize allocation patterns or algorithmic complexity.

For latency spikes: capture `wrk` latency histogram, correlate with `perf` samples during spike interval, examine kernel scheduler events with `perf sched record`.

For suspected data race: rebuild with ThreadSanitizer, reproduce under high concurrency load, examine race report for conflicting access locations.

For memory growth: rebuild with AddressSanitizer, run until memory exceeds baseline, trigger leak check on shutdown, trace allocation sources from LSAN report.

For unexplained behavior: compile with IR and assembly emission, manually trace execution through disassembly, insert strategic `println!` logging, use `gdb` to set breakpoints and inspect runtime state.

**Critical Environment Variables**

`RUSTFLAGS`: pass flags directly to `rustc` for sanitizer instrumentation or specific optimizations.

`TSAN_OPTIONS`: control ThreadSanitizer behavior including `halt_on_error`, `history_size`, `report_bugs`.

`ASAN_OPTIONS`: control AddressSanitizer including `detect_leaks`, `abort_on_error`, `allocator_may_return_null`.

`CARGO_PROFILE_RELEASE_DEBUG`: override debug symbol generation in release builds without modifying Cargo.toml.

**Toolchain Version Requirements**

Minimum Rust version: 1.83 for latest sanitizer integrations and async runtime support.

Minimum LLVM version: 15 for complete sanitizer coverage and optimization passes.

Minimum Linux kernel: 5.10 for full `perf` event support and eBPF capabilities.

Required system packages: `clang`, `llvm`, `lld`, `gdb`, `valgrind`, `linux-tools-generic`.

**Integration into CI/CD Pipelines**

Add sanitizer checks to GitHub Actions workflow:
```yaml
- name: ThreadSanitizer
  run: |
    rustup override set nightly
    RUSTFLAGS="-Zsanitizer=thread" cargo test
    
- name: AddressSanitizer
  run: |
    RUSTFLAGS="-Zsanitizer=address" ASAN_OPTIONS="detect_leaks=1" cargo test
```

Add benchmark regression checks:
```yaml
- name: Benchmark
  run: |
    cargo bench -- --save-baseline pr-${{ github.event.pull_request.number }}
    cargo bench -- --baseline main
```

This cheat sheet completes the operational verification laboratory guide by providing instant access to the diagnostic commands and configuration patterns that transform REST API development from exploratory coding into disciplined systems engineering. Regular application of these techniques during development catches defects early, establishes performance baselines, and builds institutional knowledge about system behavior under production-representative conditions.
