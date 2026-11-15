# Operational Verification Labs: Sed

## Objective & Toolchain Setup

This guide treats `sed` not as a black box you invoke and forget, but as a live system you instrument, disassemble, profile, and stress-test. The labs are structured to build genuine mechanical intuition about how a stream editor executes at the instruction level, how its memory access patterns interact with CPU cache hierarchy, and how concurrent invocations can expose race conditions or leak memory under sanitizer scrutiny. By the end of these exercises you will be able to reason about `sed` performance from first principles, verify its correctness guarantees under hostile input, and apply the same verification workflow to any C runtime tool in your systems programming arsenal.

The labs below use two implementation targets in parallel. The first is GNU `sed` itself, compiled from source so you have debug symbols and can attach GDB or Valgrind. The second is a minimal `sed`-like stream processor written in Rust and C++ that you will build incrementally, giving the sanitizer and profiler toolchains something to sink their teeth into. All commands assume a Linux x86-64 host, though the Rust path is portable.

**Toolchain installation.** Start by installing the full chain. On a Debian or Ubuntu base:

```bash
sudo apt-get update
sudo apt-get install -y build-essential clang lldb valgrind \
    linux-perf git curl binutils
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
source "$HOME/.cargo/env"
rustup toolchain install nightly
rustup component add rust-src llvm-tools-preview
cargo install cargo-flamegraph cargo-criterion flamegraph
```

Compile GNU `sed` from source with debug symbols intact so that GDB and Valgrind resolve function names cleanly:

```bash
wget https://ftp.gnu.org/gnu/sed/sed-4.9.tar.xz
tar -xf sed-4.9.tar.xz
cd sed-4.9
./configure CFLAGS="-O1 -g3 -fno-omit-frame-pointer" --prefix="$HOME/.local"
make -j$(nproc)
make install
export PATH="$HOME/.local/bin:$PATH"
which sed   # should resolve to ~/.local/bin/sed
```

The `-O1` flag preserves enough optimization for realistic execution without collapsing the call graph into a wall of inlined no-ops that GDB cannot navigate. `-fno-omit-frame-pointer` is critical: it keeps `rbp` as a real frame pointer so that `perf record` can walk the stack without resorting to DWARF unwinding, which costs cycles and distorts profiler samples.

Create the workspace that all three labs share:

```bash
mkdir -p ~/sed-labs/{corpus,rust-sed,cpp-sed,results}
cd ~/sed-labs
# Generate a 50 MB synthetic corpus: mixed ASCII lines with numeric fields
python3 -c "
import random, string
for i in range(1_000_000):
    words = ' '.join(''.join(random.choices(string.ascii_lowercase, k=random.randint(3,12)))
                     for _ in range(random.randint(4,10)))
    print(f'{i:08d} {words}')
" > corpus/lines.txt
wc -l corpus/lines.txt   # 1 000 000 lines
du -sh corpus/lines.txt  # ~65 MB
```

---

## Exercise 1: AST, IR & Disassembly Analysis

### 1.1 — What sed compiles a script into

Before instrumenting anything, you need a mental model of what `sed` actually does with a script string. GNU `sed` is a single-pass, address-driven state machine. When you write `sed '10,20s/foo/bar/g'`, the runtime parses that into an internal command list that is effectively a hand-compiled IR: each node holds an address predicate (line range, regex anchor, `$`, or none), an opcode, and opcode-specific operands. There is no JIT, no bytecode interpreter loop in the LLVM sense — but the command list is a linear array of function pointers and compiled regex objects, and understanding that structure tells you exactly what GDB will show you on the hot path.

The substitution opcode compiles your regex once at startup using the POSIX `regcomp` family (or GNU's internal `re_compile_pattern` on glibc systems), producing a DFA/NFA hybrid representation. Every subsequent line feeds that pre-compiled automaton, so the per-line cost is `re_search` or `re_exec`, not `regcomp`. This distinction matters enormously for throughput: a script with one substitution applied to one million lines pays `regcomp` exactly once.

### 1.2 — Disassembling the hot path with GDB and objdump

Launch GDB against your debug build and set a breakpoint on `do_subst`, the function that executes a substitution command against a single line:

```bash
gdb -q "$HOME/.local/bin/sed"
(gdb) break do_subst
(gdb) run -n 's/[0-9]\{8\}/NUM/g' corpus/lines.txt > /dev/null
(gdb) disassemble /m do_subst
```

The `/m` flag interleaves source lines with assembly. You will see that the core loop — the one that calls `re_search`, copies unmatched spans with `memmove`, and advances the scan pointer — compiles to a tight block of roughly 60–90 x86-64 instructions. Pay attention to the memory reference patterns: `sed` maintains a `struct output_buf` that grows by `realloc` when a substituted line exceeds the original, so you should see a conditional `call realloc` guarded by a size comparison.

Dump the full disassembly to a file for annotation:

```bash
objdump -d -M intel --source "$HOME/.local/bin/sed" \
    > ~/sed-labs/results/sed_disasm.txt
grep -n "do_subst\|execute_command\|regex_compile" \
    ~/sed-labs/results/sed_disasm.txt | head -40
```

Identify the loop structure in `do_subst`: the outer while loop advances `start` through the input line, and the inner body copies a matched replacement then advances past the match. This is a classic copy-on-match loop. Note the `lea` instructions computing replacement string lengths — these are where SIMD-free `strlen` calls appear on older glibc versions.

### 1.3 — Build and inspect the Rust sed implementation

Now build the companion Rust implementation. This is a minimal but complete `sed s///g` processor that you will carry through all three exercises:

```toml
# ~/sed-labs/rust-sed/Cargo.toml
[package]
name = "rust-sed"
version = "0.1.0"
edition = "2021"

[dependencies]
regex = "1.10"
memmap2 = "0.9"

[profile.release]
opt-level = 3
debug = true
codegen-units = 1
lto = "fat"

[profile.release-asan]
inherits = "release"
opt-level = 1
debug = true
sanitize = ["address"]
```

```rust
// ~/sed-labs/rust-sed/src/main.rs
use memmap2::Mmap;
use regex::bytes::Regex;
use std::fs::File;
use std::io::{self, BufWriter, Write};

fn process_stream(
    input: &[u8],
    pattern: &Regex,
    replacement: &[u8],
    output: &mut dyn Write,
) -> io::Result<()> {
    // Process the input byte slice line by line using manual scanning
    // so we avoid allocating a Vec<u8> per line.
    let mut pos = 0usize;
    let len = input.len();

    while pos < len {
        // Find the next newline boundary.
        let end = memchr(b'\n', &input[pos..])
            .map(|rel| pos + rel + 1)
            .unwrap_or(len);

        let line = &input[pos..end];
        // Perform global substitution using the regex replace_all.
        // regex::bytes::Regex::replace_all returns a Cow<[u8]>, so when
        // there is no match it borrows the original slice with zero copy.
        let replaced = pattern.replace_all(line, replacement);
        output.write_all(&replaced)?;

        pos = end;
    }

    Ok(())
}

/// Minimal memchr using the standard library's position search.
#[inline(always)]
fn memchr(byte: u8, haystack: &[u8]) -> Option<usize> {
    haystack.iter().position(|&b| b == byte)
}

fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 {
        eprintln!("Usage: {} <pattern> <replacement> <file>", args[0]);
        std::process::exit(1);
    }

    let pattern_str = &args[1];
    let replacement = args[2].as_bytes().to_vec();
    let path = &args[3];

    let pattern = Regex::new(pattern_str)
        .unwrap_or_else(|e| { eprintln!("Invalid regex: {e}"); std::process::exit(1); });

    let file = File::open(path)?;
    // Memory-map the input file for zero-copy sequential reads.
    let mmap = unsafe { Mmap::map(&file)? };

    let stdout = io::stdout();
    let mut writer = BufWriter::with_capacity(1 << 20, stdout.lock());

    process_stream(&mmap[..], &pattern, &replacement, &mut writer)?;
    writer.flush()?;
    Ok(())
}
```

Build and inspect the LLVM IR:

```bash
cd ~/sed-labs/rust-sed
cargo build --release 2>&1 | tail -5

# Emit LLVM IR for the process_stream function
RUSTFLAGS="--emit=llvm-ir" cargo build --release 2>&1 | grep -v "^$"
# IR files land in target/release/deps/
find target/release/deps -name "*.ll" | head -3
grep -A 40 "define.*process_stream" \
    target/release/deps/rust_sed*.ll | head -60
```

In the IR you will observe that `replace_all` on a `Cow::Borrowed` path compiles to a straight pointer pass-through — the substitution only materializes a new allocation on the `Cow::Owned` branch. This is the structural zero-copy guarantee Rust's type system enforces that C's `sed` achieves only by convention.

Emit the final x86-64 assembly:

```bash
RUSTFLAGS="--emit=asm" cargo build --release 2>&1 | grep -v "^$"
find target/release/deps -name "*.s" | xargs grep -l "process_stream" | head -1 \
    | xargs grep -A 80 "process_stream:"
```

Compare the generated `memchr` loop against glibc's AVX2 implementation. Your scalar Rust version will show a byte-at-a-time `cmp` loop; in Exercise 2 you will replace it with `memchr = "2"` to pull in the SIMD-accelerated crate and measure the throughput delta.

### 1.4 — C++ companion implementation for Clang/LLDB analysis

```cpp
// ~/sed-labs/cpp-sed/sed_replace.cpp
// Compile: clang++ -std=c++20 -O2 -g -fno-omit-frame-pointer \
//          -fsanitize=address,undefined \
//          -o sed_replace sed_replace.cpp

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <regex>
#include <string_view>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static void process(const char* data, std::size_t size,
                    const std::regex& pat, const std::string& repl) {
    const char* pos  = data;
    const char* end  = data + size;

    // Use a fixed 4 MB output buffer; flush when 75% full.
    constexpr std::size_t BUF = 4u << 20u;
    char* out_buf = static_cast<char*>(std::malloc(BUF));
    if (!out_buf) { std::perror("malloc"); std::exit(1); }
    std::size_t out_pos = 0;

    auto flush = [&]() {
        std::size_t written = 0;
        while (written < out_pos) {
            ssize_t n = ::write(STDOUT_FILENO, out_buf + written, out_pos - written);
            if (n < 0) { std::perror("write"); std::exit(1); }
            written += static_cast<std::size_t>(n);
        }
        out_pos = 0;
    };

    while (pos < end) {
        const char* nl = static_cast<const char*>(
            std::memchr(pos, '\n', static_cast<std::size_t>(end - pos)));
        const char* line_end = nl ? nl + 1 : end;
        std::string_view line(pos, static_cast<std::size_t>(line_end - pos));

        std::string result = std::regex_replace(
            std::string(line), pat, repl);

        if (out_pos + result.size() > BUF * 3 / 4) flush();

        std::memcpy(out_buf + out_pos, result.data(), result.size());
        out_pos += result.size();
        pos = line_end;
    }
    flush();
    std::free(out_buf);
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::fprintf(stderr, "Usage: %s <pattern> <replacement> <file>\n", argv[0]);
        return 1;
    }

    std::regex pat(argv[1], std::regex::ECMAScript | std::regex::optimize);
    std::string repl(argv[2]);

    int fd = ::open(argv[3], O_RDONLY);
    if (fd < 0) { std::perror("open"); return 1; }

    struct stat st{};
    if (::fstat(fd, &st) < 0) { std::perror("fstat"); return 1; }
    std::size_t sz = static_cast<std::size_t>(st.st_size);

    void* mem = ::mmap(nullptr, sz, PROT_READ, MAP_PRIVATE, fd, 0);
    if (mem == MAP_FAILED) { std::perror("mmap"); return 1; }
    ::close(fd);

    process(static_cast<const char*>(mem), sz, pat, repl);

    ::munmap(mem, sz);
    return 0;
}
```

```bash
cd ~/sed-labs/cpp-sed
clang++ -std=c++20 -O2 -g -fno-omit-frame-pointer \
    -o sed_replace sed_replace.cpp

# Inspect LLVM IR
clang++ -std=c++20 -O2 -S -emit-llvm \
    -o sed_replace.ll sed_replace.cpp
grep -A 30 "define.*process" sed_replace.ll | head -50

# Attach LLDB and inspect the regex hot path
lldb ./sed_replace
(lldb) breakpoint set --name "std::regex_replace"
(lldb) process launch -- '[0-9]{8}' 'NUM' ../corpus/lines.txt
(lldb) thread backtrace
(lldb) register read
(lldb) disassemble --frame --count 40
(lldb) continue
```

The LLDB session reveals the C++ `std::regex` overhead: each `std::regex_replace` call constructs a temporary `std::string` from `string_view`, then allocates the result string. The allocator traffic is visible in the frame addresses — you will see `operator new` frames between every regex engine call, which is precisely what the Rust `Cow` path avoids.

---

## Exercise 2: Cache Miss & Throughput Profiling

### 2.1 — Establishing the memory access model

`sed` is an I/O-bound workload for small regexes and a compute-bound workload for complex ones. The transition point is determined by the ratio of regex automaton steps per byte of input to the bytes-per-cycle the LLC can deliver. On a modern x86-64 machine with a 20–40 MB L3 cache, a 65 MB corpus that does not fit in cache puts significant pressure on DRAM bandwidth. The memory-mapped I/O path your Rust and C++ implementations use means the kernel brings pages into the page cache on demand; first-pass throughput is DRAM-bound. Second and subsequent passes over the same file are L3-bound because Linux keeps hot pages in the page cache until memory pressure evicts them.

Understanding this two-regime behavior is essential. If your profiler shows high `LLC-load-misses` on the first run and low misses on the second, you are seeing page-cache warming, not a code-level problem. The fix for first-pass latency is `madvise(MADV_SEQUENTIAL)`, which triggers read-ahead; the fix for sustained throughput is ensuring your processing loop does not stall the pipeline with dependent memory loads.

### 2.2 — Profiling GNU sed with perf

```bash
# Drop page cache to get cold-start numbers
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Record with hardware performance counters
sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
LLC-loads,LLC-load-misses,branch-misses \
    sed 's/[0-9]\{8\}/NUM/g' ~/sed-labs/corpus/lines.txt > /dev/null

# Second run (warm cache)
sudo perf stat -e cycles,instructions,cache-references,cache-misses,\
LLC-loads,LLC-load-misses,branch-misses \
    sed 's/[0-9]\{8\}/NUM/g' ~/sed-labs/corpus/lines.txt > /dev/null
```

Record a flame graph for the full execution:

```bash
sudo perf record -F 999 -g --call-graph fp \
    sed 's/[0-9]\{8\}/NUM/g' ~/sed-labs/corpus/lines.txt > /dev/null

sudo perf script | \
    stackcollapse-perf.pl > ~/sed-labs/results/sed_collapsed.txt 2>/dev/null \
    || (git clone https://github.com/brendangregg/FlameGraph /tmp/flamegraph &&
        sudo perf script | \
        /tmp/flamegraph/stackcollapse-perf.pl > ~/sed-labs/results/sed_collapsed.txt)

/tmp/flamegraph/flamegraph.pl ~/sed-labs/results/sed_collapsed.txt \
    > ~/sed-labs/results/sed_flame.svg
```

Open `sed_flame.svg` in a browser. The widest tower will be `re_search` or `re_execute` depending on your glibc version, with `memmove` and `memcpy` occupying the next widest bands. This confirms that substitution is dominated by the DFA scan and the subsequent output copy, not by syscall overhead.

### 2.3 — Rust implementation: Criterion microbenchmark and flamegraph

Add a benchmark target to the Rust workspace:

```toml
# Append to ~/sed-labs/rust-sed/Cargo.toml
[[bench]]
name = "throughput"
harness = false

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
```

```rust
// ~/sed-labs/rust-sed/benches/throughput.rs
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use regex::bytes::Regex;
use std::fs;

fn bench_process(c: &mut Criterion) {
    // Load the corpus once; Criterion will drive repeated iterations.
    let data = fs::read("../corpus/lines.txt")
        .expect("corpus/lines.txt not found; run from ~/sed-labs/rust-sed");

    let cases: &[(&str, &[u8])] = &[
        (r"[0-9]{8}", b"NUM"),
        (r"\b\w{10}\b", b"LONG"),
        (r"a[a-z]{3}e", b"VOWEL"),
    ];

    let mut group = c.benchmark_group("sed_replace");
    group.throughput(Throughput::Bytes(data.len() as u64));

    for (pat_str, repl) in cases {
        let pat = Regex::new(pat_str).unwrap();
        let repl_owned: Vec<u8> = repl.to_vec();

        group.bench_with_input(
            BenchmarkId::new("pattern", pat_str),
            &(&data[..], &pat, &repl_owned[..]),
            |b, (data, pat, repl)| {
                b.iter(|| {
                    let mut sink = Vec::with_capacity(data.len() + data.len() / 10);
                    rust_sed::process_stream_pub(data, pat, repl, &mut sink)
                        .expect("process failed");
                    criterion::black_box(sink.len())
                });
            },
        );
    }
    group.finish();
}

criterion_group!(benches, bench_process);
criterion_main!(benches);
```

Expose `process_stream` as a public function in `lib.rs` so the bench can call it:

```rust
// ~/sed-labs/rust-sed/src/lib.rs
use regex::bytes::Regex;
use std::io::{self, Write};

#[inline(always)]
fn memchr_scalar(byte: u8, haystack: &[u8]) -> Option<usize> {
    haystack.iter().position(|&b| b == byte)
}

pub fn process_stream_pub(
    input: &[u8],
    pattern: &Regex,
    replacement: &[u8],
    output: &mut dyn Write,
) -> io::Result<()> {
    let mut pos = 0usize;
    let len = input.len();
    while pos < len {
        let end = memchr_scalar(b'\n', &input[pos..])
            .map(|rel| pos + rel + 1)
            .unwrap_or(len);
        let line = &input[pos..end];
        let replaced = pattern.replace_all(line, replacement);
        output.write_all(&replaced)?;
        pos = end;
    }
    Ok(())
}
```

Run the benchmark and generate the flamegraph:

```bash
cd ~/sed-labs/rust-sed
cargo bench --bench throughput 2>&1 | tee ~/sed-labs/results/criterion_output.txt

# Flamegraph (requires perf and cargo-flamegraph)
sudo cargo flamegraph --bench throughput -- \
    --bench --profile-time 15 \
    2>&1 | tail -10
# Output: flamegraph.svg in the current directory
mv flamegraph.svg ~/sed-labs/results/rust_sed_flame.svg
```

Compare `criterion_output.txt` throughput numbers against GNU `sed`. On a typical Skylake machine you should see the Rust implementation achieving 350–600 MB/s for the numeric digit pattern, while GNU `sed` lands in the 200–400 MB/s range for the same substitution. The gap arises primarily from two sources: the Rust `regex` crate uses a lazy DFA with SIMD-accelerated literal search via its internal `aho-corasick` and `memchr` crates, and the `Cow` path avoids allocations entirely on non-matching lines.

### 2.4 — Identifying and fixing the cache-hostile memchr

The scalar `memchr_scalar` function above is intentionally naive. Add the `memchr` crate and measure the difference:

```toml
# Add to [dependencies] in Cargo.toml
memchr = "2.7"
```

```rust
// Update process_stream_pub in src/lib.rs to use the SIMD version:
use memchr::memchr as simd_memchr;

pub fn process_stream_pub(
    input: &[u8],
    pattern: &Regex,
    replacement: &[u8],
    output: &mut dyn Write,
) -> io::Result<()> {
    let mut pos = 0usize;
    let len = input.len();
    while pos < len {
        let end = simd_memchr(b'\n', &input[pos..])
            .map(|rel| pos + rel + 1)
            .unwrap_or(len);
        let line = &input[pos..end];
        let replaced = pattern.replace_all(line, replacement);
        output.write_all(&replaced)?;
        pos = end;
    }
    Ok(())
}
```

```bash
cargo bench --bench throughput 2>&1 | grep -E "time:|thrpt:"
```

The SIMD `memchr` crate dispatches at runtime to AVX2 `vpcmpeqb`/`vpmovmskb` intrinsics on capable CPUs, scanning 32 bytes per cycle instead of 1. For a corpus where 90% of bytes are not newlines, this reduces line-finding overhead from roughly 15% of total runtime to under 2%, shifting the bottleneck entirely into the regex engine.

### 2.5 — perf annotate: seeing the cache miss at the instruction level

```bash
cd ~/sed-labs/rust-sed
# Build with frame pointer for perf
RUSTFLAGS="-C force-frame-pointers=yes" cargo build --release

sudo perf record -F 999 -g --call-graph fp \
    target/release/rust-sed '[0-9]{8}' NUM ../corpus/lines.txt > /dev/null

sudo perf report --stdio --no-children \
    -s symbol --percent-limit 1 \
    > ~/sed-labs/results/perf_report.txt 2>&1

head -60 ~/sed-labs/results/perf_report.txt
```

Then use `perf annotate` to see which instructions account for the most samples inside the hot loop:

```bash
sudo perf annotate --stdio -s "process_stream_pub" \
    > ~/sed-labs/results/perf_annotate.txt 2>&1
head -100 ~/sed-labs/results/perf_annotate.txt
```

The annotation output maps sample percentages to individual assembly instructions. High percentages on `vmovdqu` or `vpcmpeqb` lines confirm that the SIMD path is active. High percentages on `mov [rsp+offset]` or `push` instructions suggest spill-induced cache pressure from a large stack frame, which can appear if the regex engine holds too many live variables simultaneously.

---

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

### 3.1 — Why sed's shared state matters

GNU `sed` is single-threaded by design, but modern deployment patterns run many `sed` processes in parallel (GNU Parallel, `xargs -P`, shell job control, container sidecars). The correctness question shifts from intra-process thread safety to inter-process resource sharing: temporary files, `--in-place` file locking, and signal handling. Your Rust and C++ implementations, however, may be extended to process files concurrently using threads, and that is where TSan becomes essential.

The more immediately valuable sanitizer for `sed`-like tools is AddressSanitizer (ASan) combined with LeakSanitizer (LSan). The C++ `std::regex` implementation allocates heavily per line, and any exception path that bypasses `std::free` will show up as a leak. GNU `sed`'s output buffer reallocation chain has historically had double-free bugs under pathological backreference patterns.

### 3.2 — GNU sed under Valgrind Memcheck

```bash
# Full Memcheck run with leak detection
valgrind --tool=memcheck \
    --leak-check=full \
    --show-leak-kinds=all \
    --track-origins=yes \
    --error-exitcode=1 \
    --xml=yes \
    --xml-file=~/sed-labs/results/valgrind_sed.xml \
    sed 's/\(.\{4\}\)\(.\{4\}\)/\2\1/g' \
    ~/sed-labs/corpus/lines.txt > /dev/null

# Parse the XML for definite leaks
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('results/valgrind_sed.xml')
root = tree.getroot()
errors = root.findall('.//error')
print(f'Total errors: {len(errors)}')
for e in errors[:10]:
    kind = e.findtext('kind', 'unknown')
    desc = e.findtext('.//text', 'no description')
    print(f'  [{kind}] {desc[:120]}')
"
```

The backreference swap pattern `\(.\{4\}\)\(.\{4\}\)/\2\1/g` forces `sed` to maintain two capture groups and copy them in reversed order into the output buffer, stressing the buffer growth code path. Any `realloc` that moves the buffer while a dangling pointer to the old location exists will be caught immediately by Memcheck's shadow memory tracking.

### 3.3 — ASan + LSan on the C++ implementation

```bash
cd ~/sed-labs/cpp-sed

clang++ -std=c++20 -O1 -g -fno-omit-frame-pointer \
    -fsanitize=address,undefined,leak \
    -fno-sanitize-recover=all \
    -o sed_replace_asan sed_replace.cpp

ASAN_OPTIONS="detect_leaks=1:check_initialization_order=1:\
abort_on_error=0:print_stats=1:atexit=1" \
LSAN_OPTIONS="report_objects=1:max_leaks=20" \
    ./sed_replace_asan '[0-9]{8}' NUM \
    ~/sed-labs/corpus/lines.txt > /dev/null 2>&1 | \
    tee ~/sed-labs/results/asan_cpp.txt

tail -40 ~/sed-labs/results/asan_cpp.txt
```

The `detect_leaks=1` option activates LeakSanitizer at process exit. Because your C++ implementation deliberately uses `std::malloc`/`std::free` for the output buffer, any exception thrown by `std::regex_replace` (say, a `std::regex_error` on a degenerate input) that bypasses the `free` call will be reported with a full stack trace. To stress the exception path:

```bash
# Inject a deliberately complex, potentially catastrophic backtracking pattern
# Note: std::regex will throw std::regex_error on some compilers for this, 
# but on others it hangs. We test the behavior:
echo "aaaaaaaaaaaaaaaaaaaab" | \
    timeout 5 ./sed_replace_asan '(a+)+b' 'X' /dev/stdin || \
    echo "Process timed out or errored (expected for catastrophic backtracking)"
```

Catastrophic backtracking is an exponential blowup in NFA-based engines where the alternation `(a+)+` applied to a string of `a`s with no terminating `b` explores an exponentially large match space. GNU `sed` and `std::regex` both use NFA engines that are vulnerable to this. The Rust `regex` crate uses a linear-time DFA and is immune; you can verify:

```bash
cd ~/sed-labs/rust-sed
echo "aaaaaaaaaaaaaaaaaaaab" | \
    time target/release/rust-sed '(a+)+b' 'X' /dev/stdin
# Should complete in < 1ms
```

### 3.4 — ThreadSanitizer: parallel sed processing in Rust

Extend the Rust implementation with a Rayon-based parallel processing mode and stress it with TSan:

```toml
# Add to [dependencies] in Cargo.toml
rayon = "1.10"
```

```rust
// ~/sed-labs/rust-sed/src/parallel.rs
use memchr::memchr;
use rayon::prelude::*;
use regex::bytes::Regex;

/// Split `input` into chunks at newline boundaries, process each chunk
/// in parallel, then collect results in order.
pub fn process_parallel(
    input: &[u8],
    pattern: &Regex,
    replacement: &[u8],
    num_threads: usize,
) -> Vec<u8> {
    // Build a list of (start, end) byte ranges, one per chunk.
    // Each chunk boundary falls exactly on a newline so lines are never split.
    let len = input.len();
    let raw_chunk = (len / num_threads).max(1);

    let mut boundaries: Vec<usize> = vec![0];
    let mut pos = 0;
    while pos < len {
        pos = (pos + raw_chunk).min(len);
        // Advance pos forward until we hit a newline or end of input.
        if pos < len {
            if let Some(rel) = memchr(b'\n', &input[pos..]) {
                pos += rel + 1;
            } else {
                pos = len;
            }
        }
        boundaries.push(pos);
    }
    boundaries.dedup();
    if *boundaries.last().unwrap() != len {
        boundaries.push(len);
    }

    // Build (start, end) pairs from the boundary list.
    let chunks: Vec<(usize, usize)> = boundaries
        .windows(2)
        .map(|w| (w[0], w[1]))
        .collect();

    // Process chunks in parallel; each chunk produces an independent Vec<u8>.
    let processed: Vec<Vec<u8>> = chunks
        .par_iter()
        .map(|&(start, end)| {
            let mut out = Vec::with_capacity(end - start + 128);
            crate::process_stream_pub(&input[start..end], pattern, replacement, &mut out)
                .expect("chunk processing failed");
            out
        })
        .collect();

    // Concatenate in order.
    let total: usize = processed.iter().map(|v| v.len()).sum();
    let mut result = Vec::with_capacity(total);
    for chunk in processed {
        result.extend_from_slice(&chunk);
    }
    result
}
```

```rust
// Add to src/main.rs after the existing imports:
mod parallel;
```

Build and run under TSan (requires the nightly toolchain because TSan in Rust requires `-Z sanitizer=thread`):

```bash
cd ~/sed-labs/rust-sed
RUSTFLAGS="-Z sanitizer=thread" \
    cargo +nightly build --target x86_64-unknown-linux-gnu 2>&1 | tail -10

# Write a stress binary that intentionally creates a shared Regex and clones
# it across threads, verifying Send safety:
cat > /tmp/tsan_stress.rs << 'EOF'
// Compile: rustc -Z sanitizer=thread -g -o /tmp/tsan_stress /tmp/tsan_stress.rs
// This should produce ZERO TSan reports because regex::Regex is Send+Sync.
use std::sync::Arc;
use std::thread;
use regex::bytes::Regex;

fn main() {
    let pat = Arc::new(Regex::new(r"[0-9]{8}").unwrap());
    let data = b"12345678 hello world\n98765432 another line\n".repeat(50_000);
    let data = Arc::new(data);

    let handles: Vec<_> = (0..8).map(|_| {
        let pat = Arc::clone(&pat);
        let data = Arc::clone(&data);
        thread::spawn(move || {
            let result = pat.replace_all(&data[..], b"NUM".as_ref());
            assert!(!result.is_empty());
        })
    }).collect();

    for h in handles { h.join().unwrap(); }
    println!("No data races detected.");
}
EOF

rustc +nightly -Z sanitizer=thread -g \
    --edition 2021 \
    -L "$HOME/.cargo/registry/src" \
    -o /tmp/tsan_stress /tmp/tsan_stress.rs 2>/dev/null || \
    echo "Standalone rustc compile needs Cargo; use the following instead:"

# Use Cargo to run the TSan test properly
cargo +nightly test --target x86_64-unknown-linux-gnu \
    -Z build-std \
    -- --nocapture 2>&1 | grep -E "WARN|ERROR|data race|No data" | head -20
```

If TSan fires on the parallel implementation, the report will show two threads accessing the same memory address with conflicting read/write operations and no intervening synchronization. The correct fix is always to ensure each thread operates on a fully independent slice of input and writes to an independent output buffer — which the `par_iter().map(...)` structure above guarantees by construction, since `rayon` does not share `out` buffers between closures.

### 3.5 — LeakSanitizer on Rust: catching raw pointer leaks in unsafe blocks

Introduce a deliberate leak in an `unsafe` block to verify LSan catches it, then fix it:

```rust
// ~/sed-labs/rust-sed/src/leak_demo.rs
// This module deliberately leaks memory to demonstrate LSan detection.
// It is gated behind a feature flag so it never ships.

#[cfg(feature = "leak-demo")]
pub fn leaky_buffer(size: usize) -> *mut u8 {
    // Allocate via the global allocator, then deliberately forget the Box.
    // LSan will report this as a definite leak at process exit.
    let mut v: Vec<u8> = vec![0xAB; size];
    let ptr = v.as_mut_ptr();
    std::mem::forget(v);  // intentional leak
    ptr
}

#[cfg(feature = "leak-demo")]
pub fn fixed_buffer(size: usize) -> Vec<u8> {
    // Correct version: Vec is returned and its drop runs normally.
    vec![0xAB; size]
}
```

```bash
# Build with the leak-demo feature and LSan
RUSTFLAGS="-Z sanitizer=leak" \
    cargo +nightly build --target x86_64-unknown-linux-gnu \
    --features leak-demo 2>&1 | tail -5

# Run a small harness that calls leaky_buffer
LSAN_OPTIONS="report_objects=1" \
    target/x86_64-unknown-linux-gnu/debug/rust-sed \
    '[0-9]' 'N' /dev/null 2>&1 | grep -E "LEAK|leaked|bytes" | head -20
```

LSan will print a report identifying the allocation site in `leaky_buffer` with a full Rust symbolized stack trace. Switching to `fixed_buffer` eliminates the report entirely. This workflow — intentional leak injection, LSan detection, fix, verification — is the standard protocol for auditing `unsafe` code that deals with raw allocations, FFI buffers, or memory-mapped regions that are conditionally unmapped.

---

## Developer Cheat Sheet & Toolchain Checklist

The table below consolidates every command used across the three exercises into a single reference. Each row maps a diagnostic goal to its exact invocation so you can drop it directly into a Makefile, CI step, or shell alias.

| Goal | Command |
|------|---------|
| Build GNU sed with debug symbols | `./configure CFLAGS="-O1 -g3 -fno-omit-frame-pointer" && make -j$(nproc)` |
| Disassemble hot function in GDB | `gdb sed`, then `break do_subst`, `run`, `disassemble /m do_subst` |
| Dump full binary disassembly | `objdump -d -M intel --source ./sed > disasm.txt` |
| Emit Rust LLVM IR | `RUSTFLAGS="--emit=llvm-ir" cargo build --release` |
| Emit Rust x86-64 assembly | `RUSTFLAGS="--emit=asm" cargo build --release` |
| Emit C++ LLVM IR | `clang++ -O2 -S -emit-llvm -o out.ll file.cpp` |
| Cold-cache perf stat | `echo 3 \| sudo tee /proc/sys/vm/drop_caches && sudo perf stat -e cycles,cache-misses,LLC-load-misses ./sed ...` |
| Record perf flame graph | `sudo perf record -F 999 -g --call-graph fp ./binary ... && sudo perf script \| stackcollapse-perf.pl \| flamegraph.pl > out.svg` |
| Cargo flamegraph | `sudo cargo flamegraph --bench throughput -- --bench --profile-time 15` |
| Criterion throughput bench | `cargo bench --bench throughput 2>&1 \| grep -E "time:\|thrpt:"` |
| perf annotate hot function | `sudo perf annotate --stdio -s "function_name"` |
| Valgrind Memcheck full | `valgrind --tool=memcheck --leak-check=full --track-origins=yes --error-exitcode=1 ./binary` |
| Clang ASan + LSan + UBSan | `clang++ -fsanitize=address,undefined,leak -fno-sanitize-recover=all -O1 -g` |
| ASan runtime options | `ASAN_OPTIONS="detect_leaks=1:print_stats=1:atexit=1"` |
| Rust TSan (nightly) | `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly build --target x86_64-unknown-linux-gnu` |
| Rust LSan (nightly) | `RUSTFLAGS="-Z sanitizer=leak" cargo +nightly build --target x86_64-unknown-linux-gnu` |
| LLDB attach to running process | `lldb -p $(pgrep sed)` |
| LLDB set breakpoint by name | `(lldb) breakpoint set --name "std::regex_replace"` |
| Verify no sanitizer errors in CI | `cargo test 2>&1 \| grep -E "ERROR\|WARN\|leak" \| wc -l` (expect 0) |
| Check binary frame pointer | `readelf -s ./binary \| grep -i "frame"` or `objdump -d ./binary \| grep "push.*rbp"` |
| madvise sequential hint | `madvise(ptr, size, MADV_SEQUENTIAL)` before the processing loop |

**Toolchain version pinning checklist.** Lock your environment to avoid silent behavior changes between lab runs. Record these versions in a `TOOLCHAIN.lock` file at the workspace root:

```bash
cat > ~/sed-labs/TOOLCHAIN.lock << EOF
rustc: $(rustc --version)
cargo: $(cargo --version)
clang: $(clang --version | head -1)
lldb: $(lldb --version | head -1)
valgrind: $(valgrind --version)
perf: $(perf --version)
kernel: $(uname -r)
sed: $(sed --version | head -1)
EOF
cat ~/sed-labs/TOOLCHAIN.lock
```

**Sanitizer compatibility matrix.** ASan and TSan cannot be linked into the same binary because they both intercept `malloc`; run them in separate build targets. LSan is a subset of ASan when `detect_leaks=1` is set, so you get leak detection for free in an ASan build without a separate LSan binary. UBSan is composable with both and should always be included in debug builds. For Rust, the nightly `-Z sanitizer=` flag maps directly to the same LLVM instrumentation passes that Clang uses, so the semantics are identical at the machine level even though the invocation syntax differs.

**Performance baseline cadence.** Run `perf stat` with the hardware counter set above before and after any implementation change that touches the hot path. Keep a `results/baselines.csv` with columns `date, impl, pattern, file_size_mb, throughput_mb_s, LLC_miss_rate, branch_miss_rate`. A throughput regression of more than 5% or an LLC miss rate increase of more than 2 percentage points warrants investigation before merging. Criterion's regression detection handles microbenchmark drift automatically; `perf stat` handles the system-level counters that Criterion cannot see.
