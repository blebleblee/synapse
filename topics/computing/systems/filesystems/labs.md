# Operational Verification Labs: Filesystems

## Objective & Toolchain Setup

Filesystems represent the most heavily engineered persistence abstraction in modern operating systems, mediating every interaction between volatile DRAM and durable block storage through a sophisticated layering of directory hierarchies, inode metadata structures, block allocators, and page cache coherency protocols. This laboratory sequence develops operational verification competency across the entire filesystem stack, from user-space system call invocation through VFS dispatch layers down to physical block device I/O scheduling. You will instrument filesystem operations using compiler intermediate representations, CPU performance monitoring counters, memory sanitizers, and race detectors to validate correctness, diagnose performance pathologies, and expose concurrency hazards in production-grade filesystem implementations.

The modern filesystem stack operates as a multi-layer state machine. At the top, POSIX system calls (`open`, `read`, `write`, `fsync`, `rename`) present a unified interface that the Virtual Filesystem Switch (VFS) multiplexes across heterogeneous concrete implementations—ext4 journaling filesystems, copy-on-write Btrfs B-trees, distributed network filesystems, in-memory tmpfs ramdisks. Below the VFS, the page cache absorbs read and write pressure through a write-back buffer pool managed by kernel threads (`kworker/flush`), converting small random accesses into large sequential block I/O operations. At the bottom, block layer schedulers (mq-deadline, BFQ, Kyber) reorder and coalesce I/O requests before submitting them to device drivers, which translate logical block addresses into physical sector locations through LBA-to-PBA mapping tables in SSDs or cylinder-head-sector geometries in spinning disks.

Your verification workflow operates at three distinct abstraction layers. At the compiler layer, you examine LLVM intermediate representation (IR) and assembly disassembly to validate that the compiler correctly lowers high-level filesystem operations into optimized instruction sequences, inlines critical paths, and eliminates redundant synchronization primitives. At the runtime layer, you deploy CPU performance counters to measure cache miss rates, TLB shootdowns, and stalled cycles attributable to I/O wait states, correlating microarchitectural bottlenecks with filesystem design decisions around block alignment, read-ahead heuristics, and dirty page writeback policies. At the memory safety layer, you activate AddressSanitizer shadow memory tracking and ThreadSanitizer happens-before graphs to detect use-after-free violations, data races on inode metadata, and lock ordering inversions that trigger deadlocks under concurrent workload stress.

### Environment Preparation

Install the complete systems programming toolchain with compiler infrastructure, debuggers, and dynamic analysis instrumentation. On Linux distributions, acquire the LLVM toolchain for IR inspection, GDB and LLDB for interactive debugging, Valgrind for heap and cache profiling, and Cargo for Rust-native tooling. Execute the following sequence to establish a reproducible verification environment:

```bash
# Install Rust toolchain with nightly channel for unstable sanitizer flags
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup install nightly
rustup default nightly

# Install LLVM utilities for IR and disassembly inspection
sudo apt-get update
sudo apt-get install -y llvm clang lldb lld

# Install Valgrind suite for cache and heap profiling
sudo apt-get install -y valgrind

# Install perf for hardware performance counter access
sudo apt-get install -y linux-tools-common linux-tools-generic linux-tools-$(uname -r)

# Install cargo extensions for flamegraph generation
cargo install flamegraph

# Verify installation
rustc --version
clang --version
lldb --version
valgrind --version
perf --version
```

Configure kernel parameters to permit unprivileged access to performance monitoring counters, enabling non-root userspace processes to sample CPU events without requiring elevated privileges. Write the paranoid level override to the sysctl interface:

```bash
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid
echo 0 | sudo tee /proc/sys/kernel/kptr_restrict
```

Create a dedicated workspace directory for filesystem verification artifacts, isolating compiled binaries, profiling data, and sanitizer reports from system directories:

```bash
mkdir -p ~/fslab/{src,build,profiles,sanitizer-logs}
cd ~/fslab
```

### Verification Target Architecture

Construct a multi-threaded filesystem benchmark suite that exercises the complete I/O path: directory traversal through `openat` system calls, metadata querying via `fstatat`, sequential and random read patterns, write-heavy workloads with explicit `fsync` barriers, and concurrent writers racing on shared directories. The implementation must expose measurable performance characteristics—instruction cache misses from indirect VFS function pointers, L3 cache thrashing from scattered inode allocations, TLB shootdowns from memory-mapped file extensions—while remaining amenable to compiler analysis and sanitizer instrumentation.

The reference implementation deploys Rust's type system to enforce filesystem invariants at compile time: borrowed paths prevent use-after-close errors, `Send` trait bounds guarantee thread-safe handle sharing, and Result types force explicit error handling of `ENOSPC`, `EROFS`, and `EIO` conditions. The core workload generator spawns a configurable number of worker threads, each executing a parameterized mix of read, write, and sync operations against a target directory tree. A centralized coordinator thread aggregates throughput metrics and latency histograms, reporting percentile distributions that reveal tail latencies attributable to journal commits, extent tree splits, or background checkpoint operations.

## Exercise 1: AST, IR & Disassembly Analysis

Compiler intermediate representations expose the semantic transformations applied during translation from high-level language constructs to machine code, revealing optimization decisions that profoundly impact filesystem I/O performance. LLVM IR operates at a level above assembly but below language syntax, representing programs as control flow graphs of typed instructions in Static Single Assignment (SSA) form, where every variable receives exactly one definition and phi nodes merge values at control flow join points. By inspecting IR, you validate that the compiler correctly devirtualizes VFS dispatch through profile-guided optimization, inlines critical filesystem primitives like buffer cache lookups, and hoists invariant metadata loads out of hot loops. Disassembly further exposes microarchitectural artifacts: alignment of hot functions to cache line boundaries, use of vector instructions for bulk memory copying, and placement of branch hints to guide CPU frontend fetch and decode pipelines.

### Implementation: Filesystem I/O Microbenchmark

Construct a minimal filesystem workload generator that performs sequential writes to a temporary file, explicitly invoking `fsync` after each write to force immediate disk persistence and bypass the kernel page cache. This pattern stresses the journaling layer in filesystems like ext4, where each sync operation triggers a transaction commit that writes metadata updates to the journal before updating in-place file blocks. The implementation uses raw file descriptors rather than buffered I/O streams, eliminating userspace buffering layers that obscure kernel behavior.

Create the source file `~/fslab/src/sync_write.rs`:

```rust
use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::os::unix::io::AsRawFd;
use std::path::Path;
use std::time::Instant;

const BLOCK_SIZE: usize = 4096;
const WRITE_COUNT: usize = 1000;

fn sync_write_benchmark<P: AsRef<Path>>(path: P) -> io::Result<f64> {
    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;

    let buffer = vec![0xAA_u8; BLOCK_SIZE];
    let start = Instant::now();

    for i in 0..WRITE_COUNT {
        file.write_all(&buffer)?;
        
        unsafe {
            libc::fsync(file.as_raw_fd());
        }

        if i % 100 == 0 {
            eprintln!("Completed {} syncs", i);
        }
    }

    let elapsed = start.elapsed();
    let throughput_mbps = (BLOCK_SIZE * WRITE_COUNT) as f64 
        / elapsed.as_secs_f64() 
        / 1_048_576.0;

    Ok(throughput_mbps)
}

fn main() -> io::Result<()> {
    let tmpfile = "/tmp/fslab_sync_test.bin";
    
    println!("Starting sync-write benchmark...");
    println!("Block size: {} bytes", BLOCK_SIZE);
    println!("Write count: {}", WRITE_COUNT);
    
    match sync_write_benchmark(tmpfile) {
        Ok(throughput) => {
            println!("\nBenchmark complete!");
            println!("Throughput: {:.2} MB/s", throughput);
        }
        Err(e) => {
            eprintln!("Benchmark failed: {}", e);
            return Err(e);
        }
    }

    std::fs::remove_file(tmpfile)?;
    Ok(())
}
```

Initialize the Rust project structure and declare dependencies for low-level system call access:

```bash
cd ~/fslab
cargo init --name fslab
cp src/sync_write.rs src/main.rs
```

Edit `Cargo.toml` to specify optimization flags and declare the libc dependency:

```toml
[package]
name = "fslab"
version = "0.1.0"
edition = "2021"

[dependencies]
libc = "0.2"

[profile.release]
opt-level = 3
lto = "fat"
codegen-units = 1
```

### IR Generation and Analysis

Compile the benchmark with LLVM IR emission enabled, producing a human-readable `.ll` file that represents the optimized SSA form before final code generation. The IR reveals how Rust's `Write` trait dispatches through virtual function tables, how loop unrolling interacts with branch predictors, and whether the `fsync` system call wrapper inlines or remains an indirect call through the PLT (Procedure Linkage Table).

Generate optimized LLVM IR:

```bash
cargo rustc --release -- --emit=llvm-ir
```

Locate the generated IR file, typically placed in the target build directory with a hashed name. Copy it to the profiles directory for inspection:

```bash
find target/release -name "*.ll" -exec cp {} ~/fslab/profiles/sync_write.ll \;
```

Open `~/fslab/profiles/sync_write.ll` in a text editor and search for the function containing the benchmark loop. The IR will contain a structure resembling:

```llvm
define internal fastcc { i64, i64 } @sync_write_benchmark(
    %Path* nocapture readonly align 8 %path
) unnamed_addr #3 personality i32 (...)* @rust_eh_personality {
start:
  ; ... file opening logic ...
  br label %bb10

bb10:                                             ; preds = %bb15, %start
  %iter.0 = phi i64 [ 0, %start ], [ %1, %bb15 ]
  %cmp = icmp ult i64 %iter.0, 1000
  br i1 %cmp, label %bb11, label %bb20

bb11:                                             ; preds = %bb10
  ; Write buffer to file descriptor
  call void @llvm.memcpy.p0i8.p0i8.i64(
      i8* align 1 %dest, 
      i8* align 1 %src, 
      i64 4096, 
      i1 false
  )
  
  ; System call: fsync(fd)
  %fd = call i32 @"std::os::unix::io::AsRawFd::as_raw_fd"(...)
  %sync_result = call i32 @fsync(i32 %fd)
  
  ; Loop increment
  %1 = add nuw nsw i64 %iter.0, 1
  br label %bb15

bb15:                                             ; preds = %bb11
  ; Conditional modulo check for progress reporting
  %mod = urem i64 %1, 100
  %is_milestone = icmp eq i64 %mod, 0
  br i1 %is_milestone, label %bb16, label %bb10

bb16:                                             ; preds = %bb15
  ; Call eprintln! for progress update
  call void @report_progress(i64 %1)
  br label %bb10

bb20:                                             ; preds = %bb10
  ; Compute and return throughput
  ret { i64, i64 } %result
}
```

Analyze the IR structure to validate optimization correctness. First, verify that the loop induction variable (`%iter.0`) uses a phi node that correctly merges the initial zero value with the incremented value from each iteration. Second, confirm that the `memcpy` intrinsic replaces the manual buffer copy with a bulk memory operation that the backend can lower to vector instructions (SSE `movdqa`, AVX `vmovdqa`). Third, check whether the `fsync` call remains indirect through a function pointer or whether Link-Time Optimization (LTO) successfully devirtualized it into a direct system call invocation.

The `fastcc` calling convention annotation indicates that LLVM selected the fast calling convention, passing arguments through registers rather than the stack for improved call/return latency. The `nocapture` attribute on the path parameter signals that the function does not store the pointer for later use, enabling alias analysis to prove that writes through the file descriptor do not alias with the path string, permitting aggressive reordering of load and store operations.

### Disassembly Inspection

Disassemble the compiled binary to examine the final machine code layout, validating that the compiler correctly aligned hot loops to cache line boundaries, selected efficient instruction encodings, and placed system call invocations in a manner that minimizes instruction cache misses during the critical I/O path.

Disassemble the optimized binary using `objdump`:

```bash
objdump -d -M intel target/release/fslab > ~/fslab/profiles/sync_write.asm
```

Open `~/fslab/profiles/sync_write.asm` and locate the benchmark function by searching for the mangled symbol name containing `sync_write_benchmark`. The disassembly will reveal a structure resembling:

```asm
0000000000004a80 <_ZN5fslab19sync_write_benchmark17h...>:
    4a80:  push   rbp
    4a81:  mov    rbp, rsp
    4a84:  push   r15
    4a86:  push   r14
    4a88:  push   r13
    4a8a:  push   r12
    4a8c:  push   rbx
    4a8d:  sub    rsp, 0x48
    
    ; Loop entry point (aligned to 16-byte boundary)
    4ab0:  xor    r12d, r12d              ; i = 0
    
    4ab3:  align  16                      ; Force cache line alignment
    4ab4:  cmp    r12, 0x3e8              ; i < 1000?
    4abb:  jae    4b60                    ; Exit if i >= 1000
    
    ; Write operation
    4abd:  mov    rdi, r15                ; fd
    4ac0:  mov    rsi, rbx                ; buffer
    4ac3:  mov    edx, 0x1000             ; count = 4096
    4ac8:  call   4200 <write@plt>
    
    ; fsync system call
    4acd:  mov    edi, r15d               ; fd
    4ad0:  call   4140 <fsync@plt>
    
    ; Progress reporting (modulo check)
    4ad5:  mov    rax, r12
    4ad8:  xor    edx, edx
    4ada:  mov    ecx, 0x64               ; divisor = 100
    4adf:  div    rcx                     ; rdx = i % 100
    4ae2:  test   rdx, rdx
    4ae5:  jnz    4af0                    ; Skip report if rdx != 0
    
    4ae7:  mov    rdi, r12
    4aea:  call   5200 <report_progress>
    
    ; Loop increment
    4af0:  inc    r12                     ; i++
    4af3:  jmp    4ab4                    ; Continue loop
    
    ; Epilogue
    4b60:  add    rsp, 0x48
    4b64:  pop    rbx
    4b65:  pop    r12
    4b67:  pop    r13
    4b69:  pop    r14
    4b6b:  pop    r15
    4b6d:  pop    rbp
    4b6e:  ret
```

Examine the disassembly for performance-critical characteristics. The `align 16` directive forces the loop entry point to reside at a 16-byte boundary, ensuring that the instruction fetch unit can load the entire loop header in a single cache line access. The `xor r12d, r12d` idiom zeros the loop counter using an XOR operation, which modern CPUs recognize as a zeroing idiom and execute without consuming execution unit bandwidth. The `call` instructions to `write` and `fsync` route through the Procedure Linkage Table (PLT), indicating dynamic linking; in a static binary, these would appear as direct `syscall` instructions with the appropriate system call numbers loaded into `rax`.

The modulo operation for progress reporting uses hardware division (`div rcx`), which consumes approximately 40-80 cycles on modern x86 CPUs. If profiling reveals this as a bottleneck, you would replace it with a bitwise AND against a power-of-two constant (e.g., `i & 127 == 0` instead of `i % 100 == 0`), trading mathematical precision for a single-cycle bitwise operation. However, since this code executes only once per hundred iterations, the division latency likely resides outside the critical path.

### Validation Workflow

Execute the benchmark and correlate runtime behavior with IR and assembly predictions. Run the compiled binary and observe throughput metrics:

```bash
cargo build --release
time ./target/release/fslab
```

Expected output structure:

```text
Starting sync-write benchmark...
Block size: 4096 bytes
Write count: 1000
Completed 0 syncs
Completed 100 syncs
Completed 200 syncs
...
Completed 900 syncs

Benchmark complete!
Throughput: 8.45 MB/s

real    0m29.384s
user    0m0.012s
sys     0m0.156s
```

The dramatically higher system time relative to user time confirms that the workload spends the majority of its execution inside the kernel, servicing `write` and `fsync` system calls. The low throughput (typically 5-15 MB/s depending on storage backend) reflects the synchronous nature of `fsync`, which forces the storage controller to flush its volatile write cache to persistent media on every iteration.

Compare the disassembly with actual CPU behavior using `perf stat` to measure instruction and cycle counts:

```bash
perf stat -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \
    ./target/release/fslab
```

Output example:

```text
Performance counter stats for './target/release/fslab':

    87,459,234,891      cycles
     1,284,567,234      instructions              #    0.01  insn per cycle
       234,123,456      branches
         1,234,567      branch-misses             #    0.53% of all branches
        12,345,678      cache-references
         3,456,789      cache-misses              #   28.01% of all cache refs

      29.384721945 seconds time elapsed
```

The extremely low instructions-per-cycle (IPC) ratio of approximately 0.01 confirms that the CPU spends the vast majority of its time stalled, waiting for I/O completion rather than executing instructions. This validates that the benchmark successfully bypasses all CPU-side optimizations (prefetching, out-of-order execution, speculative loads) and directly exposes storage backend latency.

## Exercise 2: Cache Miss & Throughput Profiling

CPU cache hierarchies mediate the performance gap between DRAM (50-100 nanosecond latency) and on-die SRAM caches (L1: 1ns, L2: 3ns, L3: 10-20ns), employing spatial and temporal locality heuristics to predict which memory regions will be accessed in the near future. Filesystem operations exhibit complex cache behavior: metadata structures like directory entries and inode tables benefit from temporal locality (the same inodes are repeatedly accessed during directory traversals), while file content exhibits spatial locality (sequential reads stream through contiguous memory regions). Cache miss rates directly determine filesystem throughput—a workload that thrashes the L3 cache by randomly accessing scattered inodes can experience 10-100x throughput degradation compared to a sequential scan that maintains high cache residency.

Hardware performance counters expose microarchitectural events invisible to software profilers: L1 data cache misses, L2 instruction cache misses, TLB shootdowns triggered by page table modifications, stalled cycles awaiting memory subsystem responses. Linux `perf` provides a unified interface to these counters, sampling program counter values when specific events occur and attributing costs to source lines through DWARF debug symbols. By correlating cache miss hotspots with filesystem code paths, you identify optimization opportunities: reordering structure fields to improve cache line utilization, prefetching directory entries before traversal loops, or batching metadata queries to amortize TLB miss penalties.

### Implementation: Directory Tree Scanner

Construct a multi-threaded directory traversal benchmark that walks a filesystem hierarchy, collecting metadata statistics (file size, modification time, inode number) for every regular file and directory entry. This workload stresses the VFS dentry cache, inode cache, and page cache coherency protocols, generating measurable cache miss patterns that vary with directory tree depth, fanout, and access ordering (breadth-first versus depth-first traversal).

Create the source file `~/fslab/src/scanner.rs`:

```rust
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::mpsc::{channel, Sender};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Instant;

#[derive(Debug, Clone)]
struct FileStats {
    path: PathBuf,
    size: u64,
    is_dir: bool,
}

struct ScanResult {
    total_files: usize,
    total_dirs: usize,
    total_bytes: u64,
    elapsed_secs: f64,
}

fn scan_directory_recursive(
    root: &Path,
    stats_tx: &Sender<FileStats>,
) -> io::Result<()> {
    let entries = fs::read_dir(root)?;

    for entry_result in entries {
        let entry = entry_result?;
        let metadata = entry.metadata()?;
        let path = entry.path();

        let stat = FileStats {
            path: path.clone(),
            size: metadata.len(),
            is_dir: metadata.is_dir(),
        };

        stats_tx.send(stat.clone()).unwrap();

        if metadata.is_dir() {
            scan_directory_recursive(&path, stats_tx)?;
        }
    }

    Ok(())
}

fn parallel_scan<P: AsRef<Path>>(
    roots: &[P],
    num_threads: usize,
) -> io::Result<ScanResult> {
    let start = Instant::now();
    let (stats_tx, stats_rx) = channel();

    let work_queue = Arc::new(Mutex::new(
        roots.iter().map(|p| p.as_ref().to_path_buf()).collect::<Vec<_>>()
    ));

    let mut handles = Vec::new();

    for _ in 0..num_threads {
        let queue = Arc::clone(&work_queue);
        let tx = stats_tx.clone();

        let handle = thread::spawn(move || {
            loop {
                let next_root = {
                    let mut q = queue.lock().unwrap();
                    q.pop()
                };

                match next_root {
                    Some(root) => {
                        if let Err(e) = scan_directory_recursive(&root, &tx) {
                            eprintln!("Scan error on {:?}: {}", root, e);
                        }
                    }
                    None => break,
                }
            }
        });

        handles.push(handle);
    }

    drop(stats_tx);

    let mut total_files = 0_usize;
    let mut total_dirs = 0_usize;
    let mut total_bytes = 0_u64;

    for stat in stats_rx {
        if stat.is_dir {
            total_dirs += 1;
        } else {
            total_files += 1;
        }
        total_bytes += stat.size;
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let elapsed = start.elapsed();

    Ok(ScanResult {
        total_files,
        total_dirs,
        total_bytes,
        elapsed_secs: elapsed.as_secs_f64(),
    })
}

fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <directory> [num_threads]", args[0]);
        std::process::exit(1);
    }

    let scan_root = &args[1];
    let num_threads = args.get(2)
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(4);

    println!("Scanning directory: {}", scan_root);
    println!("Worker threads: {}", num_threads);
    println!();

    let result = parallel_scan(&[scan_root], num_threads)?;

    println!("Scan complete!");
    println!("  Files: {}", result.total_files);
    println!("  Directories: {}", result.total_dirs);
    println!("  Total size: {:.2} MB", result.total_bytes as f64 / 1_048_576.0);
    println!("  Elapsed: {:.3} seconds", result.elapsed_secs);
    println!("  Throughput: {:.0} entries/sec", 
        (result.total_files + result.total_dirs) as f64 / result.elapsed_secs);

    Ok(())
}
```

Replace the previous `src/main.rs` with this implementation:

```bash
cp ~/fslab/src/scanner.rs ~/fslab/src/main.rs
```

Compile the scanner with debug symbols enabled to support source-level profiling attribution:

```bash
cargo build --release
```

### Cache Profiling with Valgrind Cachegrind

Valgrind's Cachegrind tool simulates a three-level cache hierarchy, tracking every memory access and attributing cache hits and misses to individual source lines. Unlike hardware performance counters, Cachegrind provides deterministic, reproducible measurements independent of system noise, making it ideal for comparing algorithmic variants and validating optimization hypotheses.

Execute the scanner under Cachegrind instrumentation, targeting a directory tree with measurable depth and breadth. The `/usr` directory typically contains tens of thousands of files organized in a multi-level hierarchy, providing sufficient complexity to generate meaningful cache statistics:

```bash
valgrind --tool=cachegrind \
    --cache-sim=yes \
    --branch-sim=yes \
    ./target/release/fslab /usr 1
```

Cachegrind emits a summary report to stderr and writes detailed per-function statistics to a file named `cachegrind.out.<pid>`. The summary resembles:

```text
==12345== Cachegrind, a cache and branch-prediction profiler
==12345== Copyright (C) 2002-2017, and GNU GPL'd, by Nicholas Nethercote et al.
==12345== Using Valgrind-3.18.1 and LibVEX; rerun with -h for copyright info
==12345== Command: ./target/release/fslab /usr 1
==12345== 
Scanning directory: /usr
Worker threads: 1

Scan complete!
  Files: 42387
  Directories: 4892
  Total size: 8473.45 MB
  Elapsed: 8.234 seconds
  Throughput: 5743 entries/sec
==12345== 
==12345== I   refs:      1,847,294,561
==12345== I1  misses:        1,234,567
==12345== LLi misses:          234,567
==12345== I1  miss rate:          0.07%
==12345== LLi miss rate:          0.01%
==12345== 
==12345== D   refs:        734,582,394  (523,847,392 rd + 210,734,002 wr)
==12345== D1  misses:       12,345,678  ( 10,234,567 rd +   2,111,111 wr)
==12345== LLd misses:        3,456,789  (  2,345,678 rd +   1,111,111 wr)
==12345== D1  miss rate:           1.7% (        2.0%   +         1.0%  )
==12345== LLd miss rate:           0.5% (        0.4%   +         0.5%  )
==12345== 
==12345== LL refs:          13,580,245  ( 11,469,134 rd +   2,111,111 wr)
==12345== LL misses:         3,691,356  (  2,580,245 rd +   1,111,111 wr)
==12345== LL miss rate:            0.1% (        0.1%   +         0.5%  )
```

Interpret the cache hierarchy statistics. The L1 instruction cache miss rate of 0.07% indicates high code locality—the scanner's hot loop fits within the 32KB L1i cache, avoiding frontend stalls from instruction fetch latency. The L1 data cache miss rate of 1.7% reflects the random access pattern of directory traversal; each `read_dir` system call returns a batch of directory entries whose metadata resides in scattered memory locations, defeating spatial prefetching. The last-level cache (LLC, typically L3) miss rate of 0.5% for data accesses represents the true memory bandwidth demand—these misses must be serviced by DRAM, incurring 100+ cycle latencies.

Annotate the source code with line-level cache miss attribution using the `cg_annotate` tool:

```bash
cg_annotate cachegrind.out.12345 > ~/fslab/profiles/cachegrind_annotated.txt
```

Open `~/fslab/profiles/cachegrind_annotated.txt` and locate the `scan_directory_recursive` function. The annotation displays instruction fetch (Ir), L1 data read (Dr), L1 data write (Dw), and corresponding miss counts alongside each source line:

```text
--------------------------------------------------------------------------------
-- User-annotated source: src/main.rs
--------------------------------------------------------------------------------
Ir          Dr          Dw          I1mr  D1mr  D1mw  ILmr DLmr DLmw  

            .           .           .     .     .     .    .    .     fn scan_directory_recursive(
            .           .           .     .     .     .    .    .         root: &Path,
            .           .           .     .     .     .    .    .         stats_tx: &Sender<FileStats>,
            .           .           .     .     .     .    .    .     ) -> io::Result<()> {
45,892,341  23,456,789  8,234,567   12,345 8,901 1,234 567  234  112      let entries = fs::read_dir(root)?;
            .           .           .     .     .     .    .    .     
98,234,567  67,890,123  12,345,678  23,456 45,678 2,345 1,234 3,456 567      for entry_result in entries {
12,345,678  8,901,234   3,456,789   2,345 5,678 890   123  456  78           let entry = entry_result?;
67,890,123  45,678,901  9,876,543   15,678 23,456 3,456 2,345 4,567 789      let metadata = entry.metadata()?;
```

The `fs::read_dir` call exhibits the highest L1 data miss count, confirming that kernel-returned directory entry structures bypass userspace caches. The `metadata()` call similarly generates substantial misses, as each invocation triggers a new `fstatat` system call that fetches inode metadata from the kernel's inode cache, which resides in unmapped kernel memory.

### Hardware Counter Profiling with Perf

Hardware performance counters provide cycle-accurate measurements of cache behavior in production environments, capturing the actual cache miss costs rather than Cachegrind's simulated estimates. Modern Intel and AMD CPUs expose hundreds of performance events through Model-Specific Registers (MSRs), accessible through the `perf_event_open` system call that Linux `perf` abstracts.

Profile the scanner using CPU performance counters to measure L1, L2, and L3 cache miss rates:

```bash
perf stat -e cycles,instructions,L1-dcache-loads,L1-dcache-load-misses,\
LLC-loads,LLC-load-misses,dTLB-loads,dTLB-load-misses \
    ./target/release/fslab /usr 4
```

Expected output structure:

```text
Scanning directory: /usr
Worker threads: 4

Scan complete!
  Files: 42387
  Directories: 4892
  Total size: 8473.45 MB
  Elapsed: 2.384 seconds
  Throughput: 19842 entries/sec

Performance counter stats for './target/release/fslab /usr 4':

    18,473,294,891      cycles
     4,284,567,234      instructions              #    0.23  insn per cycle
     1,847,329,458      L1-dcache-loads
        34,582,394      L1-dcache-load-misses     #    1.87% of all L1-dcache accesses
        34,582,394      LLC-loads
         8,234,567      LLC-load-misses           #   23.82% of all LL-cache accesses
     1,234,567,890      dTLB-loads
         2,345,678      dTLB-load-misses          #    0.19% of all dTLB cache accesses

       2.384721945 seconds time elapsed
      0.456789012 seconds user
      1.928012345 seconds sys
```

Analyze the counter relationships. The L1 data cache miss rate of 1.87% aligns with Cachegrind's simulation, validating the model. The LLC (L3) load miss rate of 23.82% indicates that approximately one-quarter of L3 accesses miss, requiring DRAM fetches—this high rate stems from the random memory access pattern of directory traversal across a large inode table that exceeds L3 capacity (typically 16-32MB on server CPUs). The data TLB miss rate of 0.19% remains low because the kernel maps directory entry buffers using huge pages (2MB pages instead of 4KB), reducing TLB pressure.

Generate a flamegraph to visualize the call stack attribution of CPU cycles:

```bash
perf record -F 999 -g -- ./target/release/fslab /usr 4
perf script | stackcollapse-perf.pl | flamegraph.pl > ~/fslab/profiles/scanner_flamegraph.svg
```

Open `~/fslab/profiles/scanner_flamegraph.svg` in a web browser. The flamegraph displays a hierarchical visualization where the x-axis represents the total sample count (proportional to CPU time) and the y-axis represents call stack depth. Wide boxes indicate hot functions; tall stacks indicate deep call chains. For the directory scanner, expect to see:

- A wide base representing `main` and `parallel_scan`
- Narrower but still prominent boxes for `scan_directory_recursive`
- Tall, narrow stacks descending through `fs::read_dir` into kernel functions like `vfs_readdir`, `ext4_readdir`, and `__getdents64`
- Separate stacks for `metadata()` calls descending through `fstatat` into `vfs_getattr` and filesystem-specific attribute functions

The flamegraph confirms that the majority of CPU time resides in kernel space, servicing system calls rather than executing userspace logic, consistent with filesystem I/O workloads.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrent filesystem operations expose race conditions invisible to sequential testing: simultaneous directory modifications can corrupt the dentry cache, parallel writes to overlapping file regions can interleave data inconsistently, and reference counting bugs in file descriptor management can leak kernel memory. ThreadSanitizer (TSan) instruments memory accesses with shadow state tracking, constructing a dynamic happens-before graph that detects data races—concurrent accesses to the same memory location where at least one is a write and no synchronization orders the accesses. AddressSanitizer (ASan) instruments heap allocations with poisoned redzones, detecting use-after-free bugs, buffer overflows, and memory leaks through shadow memory metadata that encodes allocation liveness and bounds information.

### Implementation: Concurrent Directory Mutation Workload

Construct a stress test that spawns multiple threads simultaneously creating, renaming, and deleting files in a shared temporary directory. This workload deliberately races filesystem metadata operations, exposing potential race conditions in inode allocation, directory entry insertion, and orphan cleanup logic.

Create the source file `~/fslab/src/race_test.rs`:

```rust
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Barrier};
use std::thread;
use std::time::Duration;

const NUM_THREADS: usize = 8;
const OPS_PER_THREAD: usize = 500;

#[derive(Clone)]
struct TestConfig {
    base_dir: PathBuf,
}

fn worker_thread(
    thread_id: usize,
    config: Arc<TestConfig>,
    start_barrier: Arc<Barrier>,
) -> io::Result<()> {
    start_barrier.wait();

    for i in 0..OPS_PER_THREAD {
        let file_path = config.base_dir.join(format!("thread{}_file{}.tmp", thread_id, i));

        let mut file = File::create(&file_path)?;
        file.write_all(b"test data")?;
        file.sync_all()?;
        drop(file);

        let rename_path = config.base_dir.join(format!("thread{}_renamed{}.tmp", thread_id, i));
        fs::rename(&file_path, &rename_path)?;

        thread::sleep(Duration::from_micros(10));

        fs::remove_file(&rename_path)?;

        if i % 100 == 0 {
            let remaining = OPS_PER_THREAD - i;
            if remaining > 0 {
                eprintln!("Thread {}: {} ops remaining", thread_id, remaining);
            }
        }
    }

    Ok(())
}

fn run_race_test<P: AsRef<Path>>(base_dir: P) -> io::Result<()> {
    let base_path = base_dir.as_ref();
    fs::create_dir_all(base_path)?;

    let config = Arc::new(TestConfig {
        base_dir: base_path.to_path_buf(),
    });

    let start_barrier = Arc::new(Barrier::new(NUM_THREADS));
    let mut handles = Vec::new();

    println!("Spawning {} worker threads...", NUM_THREADS);
    println!("Each thread will perform {} operations", OPS_PER_THREAD);
    println!();

    for thread_id in 0..NUM_THREADS {
        let cfg = Arc::clone(&config);
        let barrier = Arc::clone(&start_barrier);

        let handle = thread::spawn(move || {
            worker_thread(thread_id, cfg, barrier)
        });

        handles.push(handle);
    }

    let mut success_count = 0;
    let mut error_count = 0;

    for (thread_id, handle) in handles.into_iter().enumerate() {
        match handle.join() {
            Ok(Ok(())) => {
                success_count += 1;
                eprintln!("Thread {} completed successfully", thread_id);
            }
            Ok(Err(e)) => {
                error_count += 1;
                eprintln!("Thread {} failed: {}", thread_id, e);
            }
            Err(_) => {
                error_count += 1;
                eprintln!("Thread {} panicked", thread_id);
            }
        }
    }

    println!();
    println!("Race test complete!");
    println!("  Successful threads: {}/{}", success_count, NUM_THREADS);
    println!("  Failed threads: {}/{}", error_count, NUM_THREADS);

    fs::remove_dir_all(base_path)?;
    Ok(())
}

fn main() -> io::Result<()> {
    let test_dir = "/tmp/fslab_race_test";
    
    println!("Starting filesystem race condition stress test");
    println!("Test directory: {}", test_dir);
    println!();

    run_race_test(test_dir)?;
    Ok(())
}
```

Replace the existing main source:

```bash
cp ~/fslab/src/race_test.rs ~/fslab/src/main.rs
```

### ThreadSanitizer Data Race Detection

ThreadSanitizer instruments all memory accesses with shadow state that tracks the set of threads that have accessed each memory location and the synchronization operations that order those accesses. When two threads access the same location concurrently without intervening synchronization, TSan reports a data race with full stack traces for both racing accesses.

Compile the stress test with ThreadSanitizer instrumentation enabled:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
```

Execute the instrumented binary:

```bash
./target/x86_64-unknown-linux-gnu/debug/fslab 2>&1 | tee ~/fslab/sanitizer-logs/tsan_output.txt
```

If the workload contains data races (unlikely in this carefully synchronized example), TSan will emit reports resembling:

```text
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7f8a4c001000 by thread T2:
    #0 std::fs::rename src/fs.rs:1234
    #1 race_test::worker_thread src/main.rs:42
    #2 std::thread::spawn::thread_start <null>

  Previous write of size 8 at 0x7f8a4c001000 by thread T5:
    #0 std::fs::create_dir_all src/fs.rs:567
    #1 race_test::worker_thread src/main.rs:38
    #2 std::thread::spawn::thread_start <null>

  Location is heap block of size 4096 at 0x7f8a4c001000 allocated by main thread:
    #0 malloc <null>
    #1 alloc::alloc::alloc src/alloc.rs:89
    #2 race_test::run_race_test src/main.rs:65

  Thread T2 (tid=12347) created by main thread at:
    #0 pthread_create <null>
    #1 std::thread::spawn src/thread.rs:456

  Thread T5 (tid=12350) created by main thread at:
    #0 pthread_create <null>
    #1 std::thread::spawn src/thread.rs:456

SUMMARY: ThreadSanitizer: data race src/main.rs:42 in race_test::worker_thread
==================
```

Analyze race reports by identifying the conflicting operations (both writes in this example), the memory location, and the synchronization gap. The stack traces pinpoint the exact source lines where the race occurred. In filesystem workloads, common race patterns include:

- **Metadata races**: Two threads simultaneously calling `fs::metadata()` on the same file, racing on the kernel's inode cache entry
- **Directory entry races**: Concurrent `create` and `remove` operations on files in the same directory, racing on the dentry cache
- **Reference count races**: File descriptor duplication and closure racing on the kernel's `struct file` reference count

Note that TSan introduces significant overhead (5-15x slowdown and 5-10x memory inflation), making it unsuitable for production deployment but acceptable for development-time verification.

### AddressSanitizer Memory Leak Detection

AddressSanitizer instruments heap allocations by wrapping `malloc` and `free`, maintaining shadow memory that tracks which memory regions are allocated, freed, or poisoned (redzones). At program termination, ASan scans the shadow state for allocated blocks not reachable from the stack or global variables, reporting them as memory leaks with allocation stack traces.

Compile the stress test with AddressSanitizer enabled:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
```

Execute the instrumented binary with leak checking enabled:

```bash
ASAN_OPTIONS=detect_leaks=1:log_path=~/fslab/sanitizer-logs/asan.log \
    ./target/x86_64-unknown-linux-gnu/debug/fslab
```

ASan writes leak reports to the specified log file. Examine `~/fslab/sanitizer-logs/asan.log.*`:

```text
=================================================================
==12345==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 4096 byte(s) in 1 object(s) allocated from:
    #0 0x7f8a4d001234 in malloc (/lib/x86_64-linux-gnu/libasan.so.6+0x001234)
    #1 0x5643a8002345 in alloc::alloc::alloc src/alloc.rs:89
    #2 0x5643a8003456 in std::fs::File::create src/fs.rs:345
    #3 0x5643a8004567 in race_test::worker_thread src/main.rs:32
    #4 0x5643a8005678 in std::thread::spawn::thread_start src/thread.rs:456

Direct leak of 128 byte(s) in 1 object(s) allocated from:
    #0 0x7f8a4d001234 in malloc (/lib/x86_64-linux-gnu/libasan.so.6+0x001234)
    #1 0x5643a8006789 in alloc::alloc::alloc src/alloc.rs:89
    #2 0x5643a800789a in std::path::PathBuf::new src/path.rs:123
    #3 0x5643a80089ab in race_test::worker_thread src/main.rs:28

SUMMARY: AddressSanitizer: 4224 byte(s) leaked in 2 allocation(s).
```

Interpret leak reports by examining the allocation stack trace to identify the code responsible for the leak. In this example, a `File` handle and a `PathBuf` were allocated but never explicitly freed. In Rust, this typically indicates that a value was moved into a `thread::spawn` closure but the thread panicked before reaching the implicit drop, or that a `std::mem::forget` call deliberately prevented the destructor from running.

Common filesystem-related leak patterns include:

- **Unclosed file descriptors**: Opening files without ensuring `Drop` semantics execute (via panic or `forget`)
- **Orphaned directory handles**: `read_dir` iterators abandoned mid-iteration
- **Temporary file leaks**: Files created in `/tmp` without cleanup on error paths

### Validation Workflow

Execute the instrumented stress test and confirm absence of races and leaks:

```bash
# Clean build with ThreadSanitizer
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/fslab

# Clean build with AddressSanitizer
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
ASAN_OPTIONS=detect_leaks=1 ./target/x86_64-unknown-linux-gnu/debug/fslab
```

Expected output for a race-free, leak-free implementation:

```text
Starting filesystem race condition stress test
Test directory: /tmp/fslab_race_test

Spawning 8 worker threads...
Each thread will perform 500 operations

Thread 0: 400 ops remaining
Thread 1: 400 ops remaining
...
Thread 7 completed successfully
Thread 6 completed successfully
Thread 5 completed successfully
Thread 4 completed successfully
Thread 3 completed successfully
Thread 2 completed successfully
Thread 1 completed successfully
Thread 0 completed successfully

Race test complete!
  Successful threads: 8/8
  Failed threads: 0/8
```

No TSan warnings should appear during execution. The ASan log file should contain only the final summary line indicating zero leaks. If any leaks are detected, trace the allocation stack to the source line, inspect the surrounding control flow for early return or panic paths, and ensure that RAII destructors execute on all code paths.

## Developer Cheat Sheet & Toolchain Checklist

Filesystem verification demands a multi-layered diagnostic approach, combining compiler analysis, microarchitectural profiling, and runtime sanitization. This reference synthesizes the critical commands and interpretation heuristics for rapid debugging and optimization cycles.

### Compiler Intermediate Representation Analysis

Emit LLVM IR to validate optimization decisions (inlining, devirtualization, loop unrolling):

```bash
cargo rustc --release -- --emit=llvm-ir
find target/release -name "*.ll" -exec less {} \;
```

Key IR patterns to validate:
- `fastcc` calling convention on hot functions (reduces register spill/restore overhead)
- `@llvm.memcpy` intrinsics replacing manual buffer copies (enables vector lowering)
- Direct function calls instead of indirect `call` instructions (confirms devirtualization)
- `phi` nodes at loop headers correctly merging induction variables

Disassemble to machine code for cache alignment and instruction selection analysis:

```bash
objdump -d -M intel target/release/fslab | less
```

Critical assembly characteristics:
- Loop entry points aligned to 16-byte boundaries (`.align 16` directives)
- System calls via direct `syscall` instructions (static linking) or PLT stubs (dynamic linking)
- Efficient zeroing idioms (`xor reg, reg` instead of `mov reg, 0`)
- Branch prediction hints on hot conditional jumps

### Hardware Performance Counter Profiling

Measure cache miss rates and memory bandwidth consumption:

```bash
perf stat -e cycles,instructions,L1-dcache-load-misses,LLC-load-misses,dTLB-load-misses \
    ./target/release/fslab <args>
```

Interpret key metrics:
- **Instructions per cycle (IPC) < 0.5**: CPU is memory-bound; optimize for cache locality
- **L1 miss rate > 5%**: Poor spatial locality; consider structure-of-arrays layout or prefetching
- **LLC miss rate > 10%**: Working set exceeds cache capacity; batch operations or use streaming access
- **dTLB miss rate > 1%**: Excessive page table walks; increase huge page usage or reduce virtual address space fragmentation

Generate flamegraphs for call stack attribution:

```bash
perf record -F 999 -g -- ./target/release/fslab <args>
perf script | stackcollapse-perf.pl | flamegraph.pl > profile.svg
```

Flamegraph interpretation:
- Wide boxes at base indicate time-dominant functions
- Tall stacks suggest deep call chains or recursion
- Kernel symbols (`[kernel.kallsyms]`) indicate time spent in system calls

### Cache Simulation with Valgrind

Deterministic cache miss profiling independent of hardware:

```bash
valgrind --tool=cachegrind --cache-sim=yes ./target/release/fslab <args>
cg_annotate cachegrind.out.<pid> > annotated_source.txt
```

Cachegrind report interpretation:
- **I1 miss rate > 1%**: Instruction cache thrashing; reduce code size or improve locality
- **D1 miss rate > 3%**: Data cache thrashing; reorder structure fields or batch memory accesses
- **LL miss rate > 0.5%**: Memory bandwidth bottleneck; optimize algorithmic complexity

### ThreadSanitizer Race Detection

Instrument for data race detection with 5-15x overhead:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/fslab
```

Race report triage workflow:
1. Identify conflicting operations (read-write or write-write)
2. Determine synchronization gap (missing lock acquisition, barrier, or atomic operation)
3. Add appropriate synchronization or refactor to eliminate shared mutable state
4. Rerun TSan to confirm fix

### AddressSanitizer Memory Safety Validation

Instrument for use-after-free, buffer overflow, and leak detection:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 ./target/x86_64-unknown-linux-gnu/debug/fslab
```

Leak report triage workflow:
1. Examine allocation stack trace to identify leaking code path
2. Check for panic or early return before destructor execution
3. Verify RAII pattern compliance (resources owned by stack-allocated guards)
4. Run under ASan again to confirm zero leaks

### Filesystem-Specific Diagnostic Commands

Measure actual disk I/O operations bypassing page cache:

```bash
iostat -x 1
```

Key `iostat` metrics:
- **r/s, w/s**: Read/write operations per second
- **rkB/s, wkB/s**: Read/write throughput in kilobytes per second
- **await**: Average I/O request latency including queue time
- **%util**: Percentage of time the device had I/O requests in flight

Trace system calls issued by the benchmark:

```bash
strace -c ./target/release/fslab <args>
```

The `-c` flag emits a summary table of system call counts and cumulative time. Filesystem workloads typically exhibit dominance of `openat`, `read`, `write`, `fstatat`, `fsync`, and `close` calls.

### Complete Verification Sequence

Execute this command sequence to perform comprehensive filesystem verification:

```bash
# Build release binary with debug symbols
cargo build --release

# IR and disassembly analysis
cargo rustc --release -- --emit=llvm-ir
find target/release -name "*.ll" -exec cp {} ~/fslab/profiles/optimized.ll \;
objdump -d -M intel target/release/fslab > ~/fslab/profiles/disassembly.asm

# Hardware performance counter profiling
perf stat -d ./target/release/fslab /usr 4
perf record -F 999 -g -- ./target/release/fslab /usr 4
perf script | stackcollapse-perf.pl | flamegraph.pl > ~/fslab/profiles/flamegraph.svg

# Cache simulation
valgrind --tool=cachegrind --cache-sim=yes ./target/release/fslab /usr 1
cg_annotate cachegrind.out.* > ~/fslab/profiles/cache_annotated.txt

# ThreadSanitizer race detection
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/fslab 2>&1 | tee ~/fslab/sanitizer-logs/tsan.log

# AddressSanitizer leak detection
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
ASAN_OPTIONS=detect_leaks=1:log_path=~/fslab/sanitizer-logs/asan.log \
    ./target/x86_64-unknown-linux-gnu/debug/fslab

# System call trace
strace -c ./target/release/fslab /usr 4 2>&1 | tee ~/fslab/profiles/syscall_summary.txt

# I/O statistics monitoring (run in separate terminal during benchmark)
iostat -x 1 30 > ~/fslab/profiles/iostat.log
```

This sequence produces a complete verification artifact set in `~/fslab/profiles/` and `~/fslab/sanitizer-logs/`, enabling systematic optimization and correctness validation. Iterate through this workflow after each code modification, comparing metrics against baseline measurements to quantify performance impact and confirm absence of regressions.
