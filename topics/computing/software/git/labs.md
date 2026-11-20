# Operational Verification Labs: Git

## Objective & Toolchain Setup

Git operates as a content-addressable filesystem with a directed acyclic graph (DAG) of immutable commit objects, each cryptographically identified by a SHA-1 (transitioning to SHA-256) hash of its content, parent lineage, and metadata. Understanding Git's internal object model, ref resolution, and pack file compression is essential for diagnosing performance bottlenecks, repository corruption, and merge conflict resolution failures in large-scale collaborative environments. This laboratory sequence treats Git not as a black-box version control tool, but as a production distributed system with measurable performance characteristics, debuggable internal state, and verifiable data integrity guarantees.

The verification methodology employed here borrows directly from systems programming practice: we will instrument Git operations with performance profilers, analyze its I/O patterns with filesystem tracing tools, stress-test concurrent operations to expose race conditions in ref updates, and dissect the internal object storage layer to understand zlib compression overhead and delta chain traversal costs. These exercises assume a Unix-like environment with a complete systems toolchain installed: Git 2.40 or later compiled with debug symbols, a working Rust toolchain via rustup for building custom Git plumbing tools, LLVM's perf profiler or Linux perf for sampling CPU cycles, and strace or dtrace for system call tracing.

Begin by ensuring your Git binary includes debug symbols. On Debian-based systems, install the `git-dbgsym` package; on macOS with Homebrew, reinstall Git with `brew install git --build-from-source` and modify the formula to include `-g` in CFLAGS. Verify debug symbol presence by running `gdb $(which git)` and checking that `info functions` returns rich symbol names rather than stripped addresses. Install the Rust toolchain with `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`, then add the nightly channel for experimental profiling tools: `rustup toolchain install nightly`. Install cargo-flamegraph for flame graph generation: `cargo install flamegraph`. On Linux, ensure kernel perf events are accessible by adding your user to the `perf_event_paranoid` group or temporarily reducing restrictions with `sudo sysctl kernel.perf_event_paranoid=1`. Install Valgrind for memory leak detection: on Debian, `apt install valgrind`; on macOS, use Homebrew with `brew install valgrind`, though note macOS support is limited and Linux is preferred for Exercise 3.

Create a dedicated laboratory directory with `mkdir -p ~/git-labs && cd ~/git-labs`. Clone a moderately-sized open-source repository for realistic profiling; the Rust compiler repository works well due to its large commit history and substantial binary objects: `git clone https://github.com/rust-lang/rust.git rust-clone-lab`. This clone will serve as the corpus for cache profiling and object traversal analysis. Additionally, initialize a scratch repository for controlled experiments: `git init scratch-repo && cd scratch-repo`. Configure Git to emit verbose diagnostic output during these labs by setting `export GIT_TRACE=1 GIT_TRACE_PERFORMANCE=1 GIT_TRACE_PACK_ACCESS=1` in your shell session. These environment variables cause Git to log internal operation timings, pack file accesses, and ref resolution paths to stderr, providing immediate visibility into execution flow without requiring debugger attachment.

Understanding Git's internal architecture begins with the object database. Git stores four fundamental object types—blobs (file contents), trees (directory listings), commits (snapshots with metadata), and annotated tags—in `.git/objects/`, either as loose objects (individually zlib-compressed and SHA-1 named) or packed objects (delta-compressed and bundled into `.git/objects/pack/*.pack` files with corresponding `.idx` index files). Each object is immutable and content-addressed: modifying a single byte in a file generates an entirely new blob object with a different SHA-1 hash, which cascades into new tree and commit objects referencing that blob. This Merkle tree structure provides cryptographic integrity guarantees but imposes I/O amplification during operations that traverse deep commit histories or resolve delta chains. The exercises below quantify this amplification and explore strategies to mitigate it.

## Exercise 1: Object Storage Dissection & SHA-1 Collision Analysis

This exercise constructs Git objects manually using low-level plumbing commands to expose the internal object format, hash computation, and ref storage mechanisms. You will create blobs, trees, and commits from first principles, compute their SHA-1 digests by hand, verify Git's internal storage layout, and analyze the performance implications of loose objects versus packed objects. Finally, you will explore Git's transition to SHA-256 by enabling the experimental SHA-256 object format and measuring the computational overhead of the stronger hash function.

Navigate to the scratch repository created during setup: `cd ~/git-labs/scratch-repo`. Begin by creating a blob object directly from a string without using `git add`. Write a simple text file: `echo "Git stores this as a blob object" > sample.txt`. Compute the SHA-1 hash that Git will assign to this blob by manually constructing the object format. Git prepends a header to the content: the ASCII string `"blob "`, followed by the byte length in decimal, a null byte, and then the raw content. Compute this with: `printf "blob %s\0" $(wc -c < sample.txt) | cat - sample.txt | sha1sum`. This produces a 40-character hex digest. Now create the blob using `git hash-object -w sample.txt`, which writes the object to `.git/objects/`. The output hash should match your manual computation. Verify the object's physical storage: the first two characters of the hash form a subdirectory, and the remaining 38 characters name the file. Decompress and inspect it with `printf "\x1f\x8b\x08\x00\x00\x00\x00\x00" | cat - .git/objects/$(git hash-object sample.txt | cut -c1-2)/$(git hash-object sample.txt | cut -c3-) | zlib-flate -uncompress`, though this requires the `qpdf` package for `zlib-flate`. Alternatively, use `git cat-file -p $(git hash-object sample.txt)` to view the decompressed content through Git's API.

Construct a tree object manually. A tree maps filenames to blob or subtree SHA-1 hashes with associated file modes. Create two blobs: `echo "First file content" | git hash-object -w --stdin` and `echo "Second file content" | git hash-object -w --stdin`. Record their hashes. Write a tree index entry manually using the low-level `git mktree` command. Prepare input in the format `<mode> <type> <hash>\t<name>` for each entry. For regular files, the mode is `100644`; for executable files, `100755`; for symbolic links, `120000`; for subdirectories (subtrees), `040000`. Create a tree with two files: `printf "100644 blob %s\tfile1.txt\n100644 blob %s\tfile2.txt\n" $(echo "First file content" | git hash-object -w --stdin) $(echo "Second file content" | git hash-object -w --stdin) | git mktree`. Git outputs the tree's SHA-1 hash. Inspect the tree structure with `git cat-file -p <tree-hash>`, which displays the mode, type, hash, and name for each entry.

Create a commit object that references the tree. A commit object contains the tree hash, optional parent commit hash(es), author and committer identity with timestamps, and a commit message. Use `git commit-tree` to construct this manually: `echo "Manual commit message" | git commit-tree <tree-hash> -p $(git rev-parse HEAD 2>/dev/null || echo "")`. The `-p` flag specifies the parent commit; omit it for the initial commit. Git returns the commit's SHA-1 hash. Inspect the commit object with `git cat-file -p <commit-hash>` to see the tree reference, parent, author, committer, and message. Update the branch ref to point to this commit: `git update-ref refs/heads/master <commit-hash>`. Verify with `git log --oneline`, which now shows your manually constructed commit.

Measure the storage and decompression overhead of loose objects. Create 1000 small blob objects, each containing a unique integer: `for i in $(seq 1 1000); do echo "Blob content $i" | git hash-object -w --stdin; done`. Check the loose object count with `find .git/objects -type f | wc -l`. Measure total disk usage: `du -sh .git/objects`. Now pack these objects into a single pack file using `git repack -ad`, which aggregates loose objects into a pack file and applies delta compression. The `-a` flag processes all objects, and `-d` removes the loose objects after packing. Re-measure disk usage: `du -sh .git/objects`. The pack file should be significantly smaller due to delta compression. Inspect the pack file structure with `git verify-pack -v .git/objects/pack/*.idx | head -n 20`. The output shows each object's hash, type, size, compressed size, and delta base if applicable. Objects stored as deltas reference a base object and store only the difference, drastically reducing redundant storage for similar files across commits.

Quantify delta chain traversal cost. Clone a repository with deep history: `git clone --bare https://github.com/torvalds/linux.git linux-bare.git`. Checkout a specific file's history: `git --git-dir=linux-bare.git log --pretty=format:"%H" --follow -- Makefile | head -n 100 > makefile-commits.txt`. For each commit, measure the time to retrieve the Makefile blob: `while read commit; do /usr/bin/time -f "%e" git --git-dir=linux-bare.git show $commit:Makefile > /dev/null 2>&1; done < makefile-commits.txt`. Early commits in a deep delta chain require Git to apply a sequence of deltas, causing logarithmic or linear time growth in the worst case. Git mitigates this with delta chain length limits (default 50) and occasional re-packing to rebase deltas, but pathological cases still occur in repositories with aggressive compression settings.

Transition to SHA-256 and benchmark the performance difference. Initialize a new repository with SHA-256 object format (Git 2.29+): `git init --object-format=sha256 sha256-repo && cd sha256-repo`. Create a moderately large blob: `dd if=/dev/urandom bs=1M count=10 | git hash-object -w --stdin`. Measure the hashing time by wrapping the operation in a profiler. First, install `hyperfine` for statistical benchmarking: `cargo install hyperfine`. Benchmark SHA-1 hashing (in the original scratch-repo): `cd ~/git-labs/scratch-repo && hyperfine 'dd if=/dev/urandom bs=1M count=10 | git hash-object --stdin'`. Now benchmark SHA-256 hashing: `cd ~/git-labs/sha256-repo && hyperfine 'dd if=/dev/urandom bs=1M count=10 | git hash-object --stdin'`. SHA-256 typically incurs a 20-40% CPU overhead compared to SHA-1 due to its larger block size (512 bits vs. 512 bits, but more rounds: 64 vs. 80) and stronger avalanche properties. However, modern CPUs with SHA extensions (Intel SHA-NI, ARM Cryptography Extensions) reduce this gap significantly. Verify your CPU's support with `lscpu | grep sha` on Linux or `sysctl hw.optional.arm.FEAT_SHA256` on ARM macOS. If SHA extensions are present, the performance difference narrows to under 10%.

Build a custom Rust tool to compute Git object hashes and compare with Git's internal implementation. Create a new Rust project: `cargo new --bin git-hash-tool && cd git-hash-tool`. Add dependencies in `Cargo.toml`:

```toml
[dependencies]
sha1 = "0.10"
sha2 = "0.10"
```

Write the hash computation logic in `src/main.rs`:

```rust
use sha1::{Sha1, Digest as Sha1Digest};
use sha2::{Sha256, Digest as Sha256Digest};
use std::io::{self, Read};

fn main() -> io::Result<()> {
    let mut input = Vec::new();
    io::stdin().read_to_end(&mut input)?;
    
    let content_len = input.len();
    let header = format!("blob {}\0", content_len);
    
    let mut sha1_hasher = Sha1::new();
    sha1_hasher.update(header.as_bytes());
    sha1_hasher.update(&input);
    let sha1_result = sha1_hasher.finalize();
    
    let mut sha256_hasher = Sha256::new();
    sha256_hasher.update(header.as_bytes());
    sha256_hasher.update(&input);
    let sha256_result = sha256_hasher.finalize();
    
    println!("SHA-1:   {:x}", sha1_result);
    println!("SHA-256: {:x}", sha256_result);
    
    Ok(())
}
```

Build the tool with `cargo build --release`. Verify correctness against Git's output: `echo "Test content" | ./target/release/git-hash-tool` and compare the SHA-1 output with `echo "Test content" | git hash-object --stdin`. The hashes must match exactly. Now benchmark the Rust implementation against Git's internal hashing using `hyperfine`: `hyperfine 'dd if=/dev/urandom bs=1M count=10 | ./target/release/git-hash-tool' 'dd if=/dev/urandom bs=1M count=10 | git hash-object --stdin'`. The Rust tool should perform comparably or slightly faster for pure hashing since it lacks Git's I/O layer and object database locking overhead.

Explore SHA-1 collision resistance by generating a hash collision using the SHAttered attack's publicly available colliding PDFs. Download the collision files: `wget https://shattered.io/static/shattered-1.pdf && wget https://shattered.io/static/shattered-2.pdf`. Compute their SHA-1 hashes: `sha1sum shattered-1.pdf shattered-2.pdf`. Both files produce the same SHA-1 hash (`38762cf7f55934b34d179ae6a4c80cadccbb7f0a`) despite having different content. Attempt to add both to a Git repository: `git hash-object -w shattered-1.pdf` and `git hash-object -w shattered-2.pdf`. Git assigns the same object ID to both, causing the second write to silently fail since the object already exists. Retrieve the object with `git cat-file -p 38762cf7f55934b34d179ae6a4c80cadccbb7f0a > retrieved.pdf` and compare with the original files: `cmp retrieved.pdf shattered-1.pdf` and `cmp retrieved.pdf shattered-2.pdf`. Only the first file is retrievable; the second is lost due to the collision. This demonstrates why Git is transitioning to SHA-256, which has no known collision attacks and a security margin of 2^128 operations compared to SHA-1's broken 2^63 threshold.

## Exercise 2: Cache Miss & Throughput Profiling

Git's performance on large repositories is dominated by three factors: pack file I/O bandwidth, delta decompression CPU cost, and ref resolution cache locality. This exercise profiles Git operations under realistic workloads using Linux perf, flame graphs, and I/O tracing to identify bottlenecks in common workflows like `git log`, `git blame`, and `git grep`. You will measure CPU cache miss rates during object traversal, quantify the impact of pack file fragmentation, and optimize repository structure for better cache utilization.

Navigate to the Rust clone created during setup: `cd ~/git-labs/rust-clone-lab`. This repository contains over 100,000 commits and gigabytes of history, making it suitable for realistic profiling. Ensure the repository is fully packed by running `git repack -ad --depth=250 --window=250`, which creates a single pack file with aggressive delta compression. The `--depth` parameter controls the maximum delta chain length, and `--window` controls how many objects Git considers for delta base candidates. Larger values improve compression at the cost of CPU time during packing.

Profile a `git log` traversal across the entire history. Start with a cold cache by clearing the kernel's page cache: `sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'`. This requires root privileges and clears cached file pages, dentries, and inodes, forcing Git to perform physical I/O. Record a perf profile with cache miss events: `perf record -e cache-misses,cache-references -g -- git log --oneline --all > /dev/null`. The `-e` flag specifies hardware performance counters: `cache-misses` counts L3 cache misses, and `cache-references` counts all cache accesses. The `-g` flag enables call graph recording for flame graph generation. After the command completes, analyze the profile: `perf report --stdio | head -n 50`. Look for functions with high cache miss rates relative to cache references. Typical hotspots include `use_pack` (delta base resolution), `unpack_entry_data` (zlib decompression), and `find_pack_entry_one` (binary search in pack index).

Generate a flame graph for visual analysis. Convert the perf data to a format suitable for flame graph generation: `perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl > git-log-flamegraph.svg`. This requires the FlameGraph repository: `git clone https://github.com/brendangregg/FlameGraph.git ~/FlameGraph`. Open `git-log-flamegraph.svg` in a web browser. The flame graph visualizes CPU time spent in each function, with the x-axis representing the total sample width and the y-axis representing stack depth. Wide plateaus indicate functions consuming significant CPU time. In a typical Git log traversal, `inflate` (zlib decompression) and `get_delta_base` (delta chain traversal) dominate. If `find_pack_entry_one` appears prominently, the pack index binary search is cache-inefficient, suggesting the index file is too large or fragmented across memory pages.

Measure the impact of pack file fragmentation. Create an artificially fragmented repository by forcing multiple pack files to coexist. Start with a fresh clone: `cd ~/git-labs && git clone --bare https://github.com/rust-lang/rust.git rust-fragmented.git && cd rust-fragmented.git`. Run `git repack -d` multiple times with small increments: `for i in $(seq 1 10); do git repack -d --max-pack-size=50M; done`. This creates multiple pack files, each limited to 50 MB. List the pack files with `ls -lh objects/pack/*.pack`. Now profile a `git log` traversal: `perf record -e cache-misses,cache-references -g -- git log --oneline --all > /dev/null`. Compare the cache miss rate with the single-pack baseline by examining `perf stat -e cache-misses,cache-references -- git log --oneline --all > /dev/null`. The fragmented repository will exhibit a higher cache miss rate because Git must search multiple pack indexes and switch between pack files, thrashing the CPU cache. Consolidate the pack files with `git repack -ad` and re-run the measurement. The cache miss rate should decrease significantly.

Profile `git blame` to analyze line-by-line attribution cost. This operation traverses the commit history backward, applying reverse diffs to determine the last commit that modified each line. Choose a large file with substantial history: `git blame kernel/sys.c` in the Linux kernel repository or `compiler/rustc/src/lib.rs` in the Rust repository. Profile with perf: `perf record -e cache-misses,cycles -g -- git blame compiler/rustc/src/lib.rs > /dev/null`. Generate a flame graph as before. The hotspot should be `blame_chunk` or `fill_blame_origin`, which repeatedly parses diff hunks and applies reverse patches. The cache miss rate is typically higher than `git log` because blame accesses scattered parts of history rather than sequential traversal.

Optimize blame performance with the commit graph feature, which precomputes reachability and generation numbers for fast traversal. Generate a commit graph for the repository: `git commit-graph write --reachable --changed-paths`. This creates `.git/objects/info/commit-graph`, a binary index that stores topological levels and parent relationships in a cache-friendly format. Re-run the blame profiling: `perf stat -e cache-misses,cycles -- git blame compiler/rustc/src/lib.rs > /dev/null`. The cycle count and cache miss rate should decrease because Git uses the commit graph to skip unreachable commits and prune the search space. Verify the improvement with `git blame --incremental compiler/rustc/src/lib.rs`, which emits partial results as it computes. With the commit graph, early results appear almost instantly compared to the cold cache case.

Profile `git grep` to measure full-text search throughput. This operation scans the working tree or historical snapshots for a regex pattern. First, benchmark working tree search: `hyperfine 'git grep "fn main"'`. Now benchmark historical search across all commits: `hyperfine 'git grep "fn main" $(git rev-list --all)'`. The historical search is orders of magnitude slower because Git must inflate every blob in every commit to apply the regex. Profile with perf: `perf record -e cycles,instructions -g -- git grep "fn main" $(git rev-list --all | head -n 100) > /dev/null`. The flame graph will show `inflate` and `regexec` as the primary hotspots. Git's grep is single-threaded by default; enable parallelism with `git grep --threads=8 "fn main" $(git rev-list --all | head -n 100)`. Re-run the perf profile to verify parallel inflate calls across multiple threads.

Measure the throughput impact of object database locking. In multi-threaded Git operations, the object database is protected by file-level locks in `.git/objects/pack/`. Simulate concurrent access with a simple shell script that runs multiple `git log` commands in parallel: `for i in $(seq 1 8); do git log --oneline --all > /dev/null & done; wait`. Profile with perf and examine lock contention: `perf record -e cycles -g -- bash -c 'for i in $(seq 1 8); do git log --oneline --all > /dev/null & done; wait'`. The flame graph should show significant time in `flock` or `lockfile` calls if contention is high. Git 2.31+ introduces a multi-pack index (MIDX) to reduce lock contention. Generate a MIDX: `git multi-pack-index write`. Re-run the parallel log test and compare the contention. The MIDX consolidates pack index lookups into a single read-only structure, reducing lock acquisition frequency.

Build a custom Rust tool to measure Git object traversal cache locality. Create a new project: `cargo new --bin git-cache-profiler && cd git-cache-profiler`. Add dependencies in `Cargo.toml`:

```toml
[dependencies]
git2 = "0.18"
perf-event = "0.4"
```

Write the traversal and profiling logic in `src/main.rs`:

```rust
use git2::{Repository, Oid, ObjectType};
use perf_event::events::Hardware;
use perf_event::Builder;
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <repo-path>", args[0]);
        return Ok(());
    }
    
    let repo = Repository::open(&args[1])?;
    let mut revwalk = repo.revwalk()?;
    revwalk.push_head()?;
    revwalk.set_sorting(git2::Sort::TOPOLOGICAL)?;
    
    let mut cache_miss_counter = Builder::new(Hardware::CACHE_MISSES).build()?;
    let mut cache_ref_counter = Builder::new(Hardware::CACHE_REFERENCES).build()?;
    
    cache_miss_counter.enable()?;
    cache_ref_counter.enable()?;
    
    let mut commit_count = 0;
    for oid_result in revwalk {
        let oid = oid_result?;
        let commit = repo.find_commit(oid)?;
        let tree = commit.tree()?;
        
        tree.walk(git2::TreeWalkMode::PreOrder, |_, entry| {
            if entry.kind() == Some(ObjectType::Blob) {
                let _ = repo.find_blob(entry.id());
            }
            git2::TreeWalkResult::Ok
        })?;
        
        commit_count += 1;
        if commit_count >= 1000 {
            break;
        }
    }
    
    cache_miss_counter.disable()?;
    cache_ref_counter.disable()?;
    
    let cache_misses = cache_miss_counter.read()?;
    let cache_refs = cache_ref_counter.read()?;
    let miss_rate = (cache_misses as f64 / cache_refs as f64) * 100.0;
    
    println!("Traversed {} commits", commit_count);
    println!("Cache references: {}", cache_refs);
    println!("Cache misses: {}", cache_misses);
    println!("Miss rate: {:.2}%", miss_rate);
    
    Ok(())
}
```

Build the profiler with `cargo build --release`. Run it on the Rust repository: `./target/release/git-cache-profiler ~/git-labs/rust-clone-lab`. The tool traverses 1000 commits, reads each tree and blob object, and measures cache miss rates using hardware performance counters. Compare the miss rate before and after running `git repack -ad` to quantify the impact of pack file consolidation. Typical miss rates range from 5-15% for well-packed repositories to 30-50% for fragmented or poorly structured repositories with deep delta chains.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Git's concurrency model relies on file-level locking and atomic ref updates to prevent data races during concurrent operations. However, certain edge cases—such as simultaneous pushes to the same branch, concurrent gc operations, or parallel submodule updates—can expose race conditions that corrupt the object database or leave orphaned objects. This exercise uses ThreadSanitizer to detect data races in Git's C codebase and Valgrind to identify memory leaks during complex multi-threaded operations. You will compile Git from source with sanitizer instrumentation, stress-test concurrent operations, and analyze the resulting reports to understand Git's concurrency guarantees and limitations.

Clone the Git source repository and check out a stable release tag: `cd ~/git-labs && git clone https://github.com/git/git.git git-source && cd git-source && git checkout v2.43.0`. Install build dependencies. On Debian-based systems: `sudo apt install build-essential libcurl4-openssl-dev libssl-dev libexpat1-dev gettext`. On macOS, ensure Xcode Command Line Tools are installed: `xcode-select --install`.

Compile Git with ThreadSanitizer (TSan) instrumentation. TSan detects data races by intercepting memory accesses and tracking happens-before relationships. Add TSan flags to the build: `make CFLAGS="-g -O1 -fsanitize=thread -fPIE" LDFLAGS="-fsanitize=thread -pie" -j$(nproc)`. The `-O1` optimization level is required because `-O0` can cause false positives, and `-O2` may inline too aggressively for accurate race detection. The `-fPIE` and `-pie` flags enable position-independent code, required by TSan. Compilation takes several minutes. After completion, verify the instrumented binary: `./git --version`. The version string should display normally, indicating the binary is functional.

Create a test repository for concurrent operations: `mkdir -p ~/git-labs/race-test && cd ~/git-labs/race-test && ./git init`. Configure Git to use the instrumented binary for this session: `export GIT_EXEC_PATH=~/git-labs/git-source`. Verify with `git --version`, which should now invoke the TSan-instrumented binary.

Stress-test concurrent ref updates by simulating multiple writers updating the same branch. This scenario commonly occurs in continuous integration systems where multiple jobs push to the same branch simultaneously. Create a shell script `concurrent-push.sh`:

```bash
#!/bin/bash
set -e

REPO_DIR=~/git-labs/race-test
cd $REPO_DIR

for i in $(seq 1 20); do
    echo "Commit $i" > file$i.txt
    git add file$i.txt
    git commit -m "Commit $i"
done

for i in $(seq 1 10); do
    (
        git checkout -b branch-$i
        echo "Branch $i content" > branch-$i.txt
        git add branch-$i.txt
        git commit -m "Branch $i commit"
        git checkout master
        git merge --no-ff branch-$i -m "Merge branch $i"
    ) &
done

wait
```

Make the script executable: `chmod +x concurrent-push.sh`. Run it and observe TSan output: `./concurrent-push.sh 2>&1 | tee tsan-output.txt`. TSan reports data races with detailed stack traces showing the conflicting accesses. Look for warnings like "WARNING: ThreadSanitizer: data race (pid=12345)". Each race report includes two stack traces: the write operation and the conflicting read or write. Common race locations in Git include `refs/files-backend.c` (ref transaction logic) and `lockfile.c` (file locking primitives). These races are typically benign due to Git's file-level locking, but TSan correctly identifies them as potential issues.

Analyze a specific race report from the output. TSan reports include the memory address of the conflicting access, the operation type (read or write), and the call stack. For example:

```text
WARNING: ThreadSanitizer: data race
  Write of size 8 at 0x7f1234567890 by thread T2:
    #0 write_in_full refs.c:123
    #1 commit_ref_update refs/files-backend.c:456
  Previous read of size 8 at 0x7f1234567890 by thread T1:
    #0 read_in_full refs.c:789
    #1 read_ref refs/files-backend.c:321
```

This indicates two threads accessed the same memory location (an in-memory ref cache) without synchronization. Verify whether Git's file locks prevent actual corruption by checking repository integrity: `git fsck --full`. If fsck reports no errors, the race is benign and protected by filesystem atomicity guarantees.

Compile Git with AddressSanitizer (ASan) to detect memory errors during concurrent operations. ASan detects buffer overflows, use-after-free, and double-free bugs. Rebuild Git with ASan: `make clean && make CFLAGS="-g -O1 -fsanitize=address -fno-omit-frame-pointer" LDFLAGS="-fsanitize=address" -j$(nproc)`. Run the concurrent push test again: `./concurrent-push.sh 2>&1 | tee asan-output.txt`. ASan reports memory errors with precise allocation and deallocation stack traces. Common issues in Git's C codebase include improper `free()` calls in error paths and buffer overruns in string formatting functions.

Stress-test Git's garbage collection (gc) with concurrent modifications. Git gc runs multiple phases: loose object pruning, pack file creation, ref packing, and reachability analysis. Concurrent modifications during gc can leave orphaned objects or corrupt pack files. Create a script `concurrent-gc.sh`:

```bash
#!/bin/bash
set -e

REPO_DIR=~/git-labs/race-test
cd $REPO_DIR

git gc --auto &
GC_PID=$!

for i in $(seq 1 50); do
    echo "Concurrent commit $i" > gc-test-$i.txt
    git add gc-test-$i.txt
    git commit -m "Concurrent commit during gc $i"
    sleep 0.1
done

wait $GC_PID
```

Make it executable: `chmod +x concurrent-gc.sh`. Run with TSan: `./concurrent-gc.sh 2>&1 | tee gc-tsan-output.txt`. TSan may report races in `builtin/gc.c` or `builtin/repack.c`. Check repository integrity after gc completes: `git fsck --full --unreachable`. Any unreachable objects indicate orphaned data that gc failed to collect due to race conditions.

Profile memory leaks with Valgrind's Memcheck tool. Valgrind is more heavyweight than ASan but provides comprehensive leak detection, including reachable but not-freed allocations. Compile Git without sanitizers for Valgrind: `make clean && make CFLAGS="-g -O0" -j$(nproc)`. Run a simple Git command under Valgrind: `valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./git log --oneline -n 10`. Valgrind's output reports memory leaks categorized as "definitely lost," "indirectly lost," "possibly lost," and "still reachable." "Definitely lost" indicates memory allocated but never freed with no remaining pointers. "Still reachable" indicates memory held by global variables at program exit, which is not a true leak. Examine the leak stack traces to identify allocation sites. Common leak sources in Git include error paths that exit early without freeing temporary buffers.

Stress-test submodule operations, which involve concurrent fetches and checkouts across nested repositories. Initialize a parent repository with submodules: `cd ~/git-labs && mkdir submodule-stress && cd submodule-stress && git init && git submodule add https://github.com/git/git.git module1 && git submodule add https://github.com/torvalds/linux.git module2 && git commit -m "Add submodules"`. Run concurrent submodule updates: `git submodule update --init --recursive --jobs=4`. Profile with TSan by setting `GIT_EXEC_PATH` to the instrumented binary and re-running the update. TSan may report races in `builtin/submodule--helper.c` related to shared ref caches across parallel submodule operations.

Build a custom Rust fuzzer to detect ref update races. Create a new project: `cargo new --bin git-ref-fuzzer && cd git-ref-fuzzer`. Add dependencies:

```toml
[dependencies]
git2 = "0.18"
rand = "0.8"
crossbeam = "0.8"
```

Write the fuzzing logic in `src/main.rs`:

```rust
use git2::{Repository, Signature};
use crossbeam::thread;
use rand::Rng;
use std::env;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <repo-path>", args[0]);
        return Ok(());
    }
    
    let repo_path = Path::new(&args[1]);
    let num_threads = 8;
    let commits_per_thread = 50;
    
    thread::scope(|s| {
        for thread_id in 0..num_threads {
            s.spawn(move |_| {
                let repo = Repository::open(repo_path).unwrap();
                let sig = Signature::now("Fuzzer", "fuzzer@example.com").unwrap();
                let mut rng = rand::thread_rng();
                
                for i in 0..commits_per_thread {
                    let branch_name = format!("fuzz-thread-{}-{}", thread_id, i);
                    let head = repo.head().unwrap();
                    let head_commit = head.peel_to_commit().unwrap();
                    
                    let tree_id = head_commit.tree_id();
                    let tree = repo.find_tree(tree_id).unwrap();
                    
                    let commit_id = repo.commit(
                        Some(&format!("refs/heads/{}", branch_name)),
                        &sig,
                        &sig,
                        &format!("Fuzzer commit {} from thread {}", i, thread_id),
                        &tree,
                        &[&head_commit],
                    ).unwrap();
                    
                    if rng.gen_bool(0.5) {
                        let _ = repo.find_reference(&format!("refs/heads/{}", branch_name))
                            .and_then(|mut r| r.delete());
                    }
                }
            });
        }
    }).unwrap();
    
    println!("Fuzzing complete. Checking repository integrity...");
    let repo = Repository::open(repo_path)?;
    let references = repo.references()?;
    let ref_count = references.count();
    println!("Final reference count: {}", ref_count);
    
    Ok(())
}
```

Build the fuzzer: `cargo build --release`. Run it on a test repository: `./target/release/git-ref-fuzzer ~/git-labs/race-test`. The fuzzer creates and deletes branches concurrently across multiple threads. After completion, check repository integrity with `git fsck` inside the test repository. Any corruption indicates insufficient locking in Git's ref transaction logic.

Combine TSan and ASan by compiling with both sanitizers (supported in Clang): `cd ~/git-labs/git-source && make clean && make CC=clang CFLAGS="-g -O1 -fsanitize=thread,address -fPIE" LDFLAGS="-fsanitize=thread,address -pie" -j$(nproc)`. Run the concurrent push and gc tests again. The combined sanitizers provide comprehensive detection of both race conditions and memory errors, though with higher runtime overhead (10-50x slowdown).

Analyze false positives in sanitizer reports. TSan may report races in intentionally lock-free data structures (e.g., atomic counters in `progress.c`) or benign races where correctness is guaranteed by external synchronization (e.g., filesystem locks). To suppress false positives, create a TSan suppression file `tsan-suppressions.txt`:

```text
race:progress.c
race:lockfile.c
```

Run Git with the suppression file: `TSAN_OPTIONS="suppressions=tsan-suppressions.txt" ./git log --oneline -n 10`. TSan will ignore races in the specified files. Use suppressions judiciously; overly broad suppressions can mask real bugs.

## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the essential commands, profiling workflows, and debugging strategies covered in the exercises into a reference guide for daily use. The cheat sheet assumes the Git source is compiled with debug symbols and the Rust toolchain is installed.

**Object Database Inspection:**
- Compute SHA-1 hash manually: `printf "blob %s\0" $(wc -c < file.txt) | cat - file.txt | sha1sum`
- Decompress loose object: `git cat-file -p <hash>`
- Inspect tree object: `git cat-file -p <tree-hash>`
- Inspect commit object: `git cat-file -p <commit-hash>`
- Verify pack file integrity: `git verify-pack -v .git/objects/pack/*.idx`
- Generate commit graph: `git commit-graph write --reachable --changed-paths`
- Generate multi-pack index: `git multi-pack-index write`

**Performance Profiling:**
- Clear kernel page cache (requires root): `sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'`
- Record perf profile with cache events: `perf record -e cache-misses,cache-references -g -- git log --oneline --all`
- Generate flame graph: `perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl > output.svg`
- Benchmark with hyperfine: `hyperfine 'git log --oneline --all'`
- Enable Git trace logging: `export GIT_TRACE=1 GIT_TRACE_PERFORMANCE=1 GIT_TRACE_PACK_ACCESS=1`
- Profile multi-threaded grep: `perf record -e cycles -g -- git grep --threads=8 "pattern"`

**Sanitizer Compilation:**
- Compile with ThreadSanitizer: `make CFLAGS="-g -O1 -fsanitize=thread -fPIE" LDFLAGS="-fsanitize=thread -pie" -j$(nproc)`
- Compile with AddressSanitizer: `make CFLAGS="-g -O1 -fsanitize=address -fno-omit-frame-pointer" LDFLAGS="-fsanitize=address" -j$(nproc)`
- Compile with both (Clang only): `make CC=clang CFLAGS="-g -O1 -fsanitize=thread,address -fPIE" LDFLAGS="-fsanitize=thread,address -pie" -j$(nproc)`
- Run with TSan suppressions: `TSAN_OPTIONS="suppressions=tsan-suppressions.txt" ./git <command>`

**Concurrency Stress Testing:**
- Concurrent branch creation: `for i in $(seq 1 10); do git checkout -b branch-$i && git commit --allow-empty -m "Branch $i" & done; wait`
- Concurrent gc: `git gc --auto & for i in $(seq 1 50); do git commit --allow-empty -m "Commit $i"; done; wait`
- Parallel submodule update: `git submodule update --init --recursive --jobs=8`

**Memory Leak Detection:**
- Run Valgrind with full leak check: `valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes git <command>`
- Filter Valgrind output to show only leaks: `valgrind --leak-check=full git <command> 2>&1 | grep "definitely lost"`

**Repository Integrity:**
- Full fsck with unreachable objects: `git fsck --full --unreachable`
- Verify ref integrity: `git for-each-ref --format='%(refname) %(objectname)'`
- Check for corrupted objects: `git cat-file --batch-check --batch-all-objects < /dev/null`

**Pack File Optimization:**
- Aggressive repack: `git repack -ad --depth=250 --window=250`
- Repack with max pack size: `git repack -ad --max-pack-size=100M`
- Prune unreachable objects: `git prune --expire=now`
- Clean up reflog: `git reflog expire --expire=now --all && git gc --prune=now`

**Toolchain Verification Checklist:**
- Git with debug symbols: `gdb $(which git)` then `info functions` should show rich symbol names
- Rust toolchain: `rustc --version && cargo --version`
- Perf availability (Linux): `perf --version`
- Flame graph scripts: `ls ~/FlameGraph/stackcollapse-perf.pl ~/FlameGraph/flamegraph.pl`
- Hyperfine installed: `hyperfine --version`
- Valgrind installed: `valgrind --version`
- libgit2 Rust bindings: `cargo tree | grep git2` in a Rust project using git2

**Common Performance Pitfalls:**
- Deep delta chains: limit with `git config pack.depth 50`
- Large pack files: split with `--max-pack-size` during repack
- Missing commit graph: run `git commit-graph write` after large fetches
- Fragmented pack files: consolidate with `git repack -ad`
- Cold cache: warm with `git log --all --oneline > /dev/null` before profiling
- Single-threaded operations: enable parallelism with `--threads` or `--jobs` flags

**Race Condition Investigation Workflow:**
1. Compile Git with TSan: `make CFLAGS="-g -O1 -fsanitize=thread -fPIE" LDFLAGS="-fsanitize=thread -pie"`
2. Run concurrent operation: `./concurrent-push.sh 2>&1 | tee tsan-output.txt`
3. Analyze race reports: examine stack traces for conflicting accesses
4. Check repository integrity: `git fsck --full`
5. If corruption detected, bisect Git source to find regression: `git bisect start && git bisect bad HEAD && git bisect good v2.40.0`
6. Report issue with minimal reproduction case and TSan output

**Memory Error Investigation Workflow:**
1. Compile Git with ASan: `make CFLAGS="-g -O1 -fsanitize=address" LDFLAGS="-fsanitize=address"`
2. Run operation: `./git <command> 2>&1 | tee asan-output.txt`
3. Analyze error report: identify allocation and access stack traces
4. Reproduce with GDB: `gdb --args ./git <command>` and set breakpoint at error site
5. Examine memory state: `x/32x <address>` to dump memory contents
6. Verify fix with ASan re-run: errors should disappear

This laboratory sequence has dissected Git's internal architecture from the object database through to concurrent operation safety guarantees, grounding each exercise in measurable performance characteristics and verifiable correctness properties. The profiling and sanitizer workflows demonstrated here generalize to any production distributed system: instrument the critical path, measure cache locality and lock contention, stress-test concurrent operations, and verify integrity under adversarial conditions. Mastery of these techniques transforms Git from an opaque version control tool into a transparent, auditable, and optimizable component of the software development infrastructure.
