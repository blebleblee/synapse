# Operational Verification Labs: Core

## Objective & Lab Setup

This laboratory sequence builds foundational competence in Unix shell scripting by grounding practice in the concrete mechanics of process execution, file descriptor manipulation, signal handling, and pipeline composition. Rather than treating Bash as a mere command launcher, we approach it as a programming environment with precise semantics around variable expansion, command substitution, redirection operators, and subprocess lifecycle management.

The exercises progress from basic shell execution models through empirical parameter studies to fault injection scenarios that expose error-handling boundaries. By the end of this sequence, you will have internalized the shell's process creation model via `fork()`/`exec()` system call semantics, understood how file descriptors `0`, `1`, and `2` (stdin, stdout, stderr) are duplicated and redirected across process boundaries, and gained hands-on experience with signal-driven process control.

**Required Environment:**

You need a Unix-like operating system with Bash 4.0 or later. Linux distributions (Ubuntu, Fedora, Arch) or macOS provide suitable environments. Windows users should install Windows Subsystem for Linux (WSL2) to obtain a genuine Linux kernel and userspace.

**Essential Packages:**

Install the following tools to support measurement, tracing, and analysis:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y bash coreutils strace time procps bc gnuplot

# Fedora/RHEL
sudo dnf install -y bash coreutils strace time procps-ng bc gnuplot

# macOS (via Homebrew)
brew install bash coreutils gnu-time strace gnuplot
```

Verify your Bash version and core utilities:

```bash
bash --version | head -1
echo $BASH_VERSION
which strace time bc gnuplot
```

Create a dedicated laboratory workspace to isolate experimental artifacts:

```bash
mkdir -p ~/bash-lab/{ex1,ex2,ex3,data,logs}
cd ~/bash-lab
```

Throughout these exercises, we will trace system calls with `strace`, measure execution timing with `/usr/bin/time`, and generate performance graphs with `gnuplot`. Each exercise includes verification steps that confirm correct behavior through observable system-level effects rather than relying solely on program output.

---

## Exercise 1: Foundational Practical Implementation

**Objective:** Construct a complete shell script demonstrating variable expansion, command substitution, pipeline construction, and redirection while observing the underlying system calls that implement these abstractions.

Modern shell scripting hinges on understanding how the shell interprets metacharacters and when it forks subprocesses. When you write `ls | grep txt`, the shell creates two child processes connected by a pipe, a kernel buffer with read and write file descriptors. The left-hand command writes to the pipe's write end (replaces stdout), and the right-hand command reads from the pipe's read end (replaces stdin). This exercise makes those mechanics explicit.

**Step 1: Create the baseline script**

Navigate to the first exercise directory and create a script that processes a directory listing through a multi-stage pipeline:

```bash
cd ~/bash-lab/ex1
cat > process_files.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Configuration variables
TARGET_DIR="${1:-.}"
EXTENSION="${2:-txt}"
OUTPUT_FILE="filtered_files.log"
ERROR_FILE="errors.log"

# Function: count files with given extension
count_files() {
    local dir="$1"
    local ext="$2"
    find "$dir" -type f -name "*.$ext" 2>/dev/null | wc -l
}

# Function: generate detailed file report
generate_report() {
    local dir="$1"
    local ext="$2"
    
    echo "=== File Analysis Report ===" >&2
    echo "Directory: $dir" >&2
    echo "Extension filter: .$ext" >&2
    echo "Timestamp: $(date -Iseconds)" >&2
    echo "" >&2
    
    # Pipeline: find files, extract names, sort, annotate with size
    find "$dir" -type f -name "*.$ext" -print0 2>"$ERROR_FILE" \
        | xargs -0 ls -lh \
        | awk '{print $9, "(" $5 ")"}' \
        | sort \
        | tee "$OUTPUT_FILE" \
        | nl -w3 -s': '
}

# Main execution block
main() {
    local file_count
    file_count=$(count_files "$TARGET_DIR" "$EXTENSION")
    
    echo "Found $file_count files with .$EXTENSION extension" >&2
    
    if [[ $file_count -gt 0 ]]; then
        generate_report "$TARGET_DIR" "$EXTENSION"
        echo "" >&2
        echo "Report written to: $OUTPUT_FILE" >&2
    else
        echo "No files found matching criteria" >&2
        exit 1
    fi
}

# Execute main with all arguments
main "$@"
EOF

chmod +x process_files.sh
```

**Step 2: Create test data hierarchy**

Generate a structured test environment with files of varying types:

```bash
mkdir -p test_data/{docs,scripts,config}

# Create text files with content
for i in {1..5}; do
    echo "Document $i: $(date)" > "test_data/docs/file$i.txt"
done

# Create shell scripts
for i in {1..3}; do
    echo "#!/bin/bash" > "test_data/scripts/script$i.sh"
    echo "echo 'Script $i'" >> "test_data/scripts/script$i.sh"
    chmod +x "test_data/scripts/script$i.sh"
done

# Create configuration files
echo "key=value" > test_data/config/app.conf
echo "setting=true" > test_data/config/db.conf

# Create markdown file
echo "# README" > test_data/README.md
```

**Step 3: Execute with system call tracing**

Run the script under `strace` to observe how the shell invokes `fork()`, `execve()`, `pipe()`, and `dup2()` system calls:

```bash
strace -f -e trace=fork,clone,execve,pipe,dup2,openat -o syscall_trace.log \
    ./process_files.sh test_data txt 2>&1
```

The output shows file enumeration, sorting, and formatted display. Now examine the system call trace:

```bash
grep -E "(pipe|dup2|execve)" syscall_trace.log | head -20
```

You will see sequences like:

```
pipe([3, 4])                            = 0
dup2(4, 1)                              = 1
execve("/usr/bin/find", ["find", "test_data", "-type", "f", "-name", "*.txt"], ...)
```

This confirms that the shell creates a pipe (returns two file descriptors), duplicates the write end to stdout (fd 1), then replaces the current process image with `find`. Each stage of the pipeline follows this pattern.

**Step 4: Verify redirection correctness**

Check that stdout and stderr are properly separated:

```bash
# Standard output contains the numbered file list
cat filtered_files.log

# Standard error contains diagnostic messages
cat errors.log

# Confirm file descriptor usage
ls -l /proc/$$/fd
```

**Step 5: Measure execution timing breakdown**

Use `/usr/bin/time` with verbose output to capture resource usage:

```bash
/usr/bin/time -v ./process_files.sh test_data txt > /dev/null 2> timing_report.txt
cat timing_report.txt
```

Key metrics include:

- **User time:** CPU time spent in user-mode code
- **System time:** CPU time spent in kernel-mode system calls
- **Maximum resident set size:** Peak memory usage
- **Voluntary context switches:** Times the process yielded CPU
- **Involuntary context switches:** Times the kernel preempted the process

**Step 6: Variable expansion verification**

Demonstrate the distinction between single quotes (literal), double quotes (expansion), and unquoted (word splitting):

```bash
cd ~/bash-lab/ex1
cat > expansion_test.sh << 'EOF'
#!/usr/bin/env bash

VAR="hello world"

echo "--- Single quotes (no expansion) ---"
echo 'Value: $VAR'

echo -e "\n--- Double quotes (expansion, no splitting) ---"
echo "Value: $VAR"

echo -e "\n--- Unquoted (expansion with word splitting) ---"
echo Value: $VAR

echo -e "\n--- Command substitution in double quotes ---"
echo "Current directory: $(pwd)"

echo -e "\n--- Arithmetic expansion ---"
echo "Result: $((5 * 8 + 3))"

echo -e "\n--- Parameter expansion with default ---"
echo "Config: ${CONFIG_FILE:-/etc/default.conf}"
EOF

chmod +x expansion_test.sh
bash -x expansion_test.sh
```

The `-x` flag enables execution tracing, showing exactly how the shell expands each line before execution.

---

## Exercise 2: Parameter Variation & Empirical Analysis

**Objective:** Conduct empirical measurements of pipeline performance as a function of data volume and pipeline complexity, then visualize the relationship between input size and execution time.

Unix pipelines achieve concurrency by running multiple processes simultaneously, with the kernel managing buffer flow between them. As data volume increases, we expect execution time to scale linearly for I/O-bound workloads, but CPU-bound transformations may exhibit different scaling characteristics. This exercise quantifies those relationships through controlled parameter sweeps.

**Step 1: Generate test datasets of varying sizes**

Create a script that produces text files ranging from 1 KB to 100 MB:

```bash
cd ~/bash-lab/ex2
cat > generate_datasets.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="datasets"
mkdir -p "$OUTPUT_DIR"

# Generate files with exponentially increasing sizes
for exp in {10..26}; do
    size=$((2 ** exp))
    filename="$OUTPUT_DIR/data_${size}.txt"
    
    # Generate random words to create realistic text
    head -c "$size" /dev/urandom \
        | base64 \
        | tr -d '\n' \
        | fold -w 80 \
        > "$filename"
    
    actual_size=$(stat -c%s "$filename" 2>/dev/null || stat -f%z "$filename")
    echo "Generated: $filename ($actual_size bytes)"
done
EOF

chmod +x generate_datasets.sh
./generate_datasets.sh
```

**Step 2: Construct pipeline benchmark suite**

Create a script that runs identical processing logic on each dataset while measuring execution time:

```bash
cat > benchmark_pipelines.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

RESULTS_FILE="../data/pipeline_results.csv"
echo "file_size_bytes,wall_time_sec,user_time_sec,sys_time_sec,pipeline_stages" > "$RESULTS_FILE"

# Define pipeline complexity levels
run_simple_pipeline() {
    cat "$1" | wc -l > /dev/null
}

run_medium_pipeline() {
    cat "$1" | grep -E '[0-9]+' | cut -d' ' -f1 | sort | uniq -c > /dev/null
}

run_complex_pipeline() {
    cat "$1" \
        | tr '[:upper:]' '[:lower:]' \
        | grep -oE '\w+' \
        | sort \
        | uniq -c \
        | sort -rn \
        | head -100 \
        > /dev/null
}

# Benchmark each dataset with each pipeline
for datafile in datasets/data_*.txt; do
    size=$(stat -c%s "$datafile" 2>/dev/null || stat -f%z "$datafile")
    
    for pipeline_type in simple medium complex; do
        echo "Benchmarking $datafile with $pipeline_type pipeline..."
        
        # Run with time measurement (3 iterations, take median)
        times=()
        for run in {1..3}; do
            output=$( { /usr/bin/time -f "%e %U %S" \
                bash -c "case $pipeline_type in
                    simple) run_simple_pipeline '$datafile' ;;
                    medium) run_medium_pipeline '$datafile' ;;
                    complex) run_complex_pipeline '$datafile' ;;
                esac" ; } 2>&1 )
            times+=("$output")
        done
        
        # Extract median timing
        median_time=$(echo "${times[1]}")
        wall=$(echo "$median_time" | awk '{print $1}')
        user=$(echo "$median_time" | awk '{print $2}')
        sys=$(echo "$median_time" | awk '{print $3}')
        
        echo "$size,$wall,$user,$sys,$pipeline_type" >> "$RESULTS_FILE"
    done
done

echo "Results written to: $RESULTS_FILE"
EOF

chmod +x benchmark_pipelines.sh

# Source the pipeline functions for use in subshells
cat >> benchmark_pipelines.sh << 'EOF'

export -f run_simple_pipeline
export -f run_medium_pipeline
export -f run_complex_pipeline
EOF

./benchmark_pipelines.sh
```

**Step 3: Statistical analysis and visualization**

Process the CSV results and generate comparative plots:

```bash
cat > analyze_results.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

RESULTS="../data/pipeline_results.csv"
PLOT_SCRIPT="../data/plot_performance.gp"

# Create gnuplot script for multi-series line plot
cat > "$PLOT_SCRIPT" << 'GPEOF'
set terminal png size 1200,800 font "Arial,12"
set output '../data/pipeline_performance.png'

set title "Pipeline Execution Time vs. Data Size" font "Arial,16"
set xlabel "File Size (bytes, log scale)"
set ylabel "Wall Time (seconds)"
set logscale x
set grid

set key left top
set datafile separator ","

plot '../data/pipeline_results.csv' using 1:2 every ::1 \
     title "Simple" with linespoints linewidth 2 pointtype 7, \
     '' using 1:2 every ::1 \
     title "Medium" with linespoints linewidth 2 pointtype 9, \
     '' using 1:2 every ::1 \
     title "Complex" with linespoints linewidth 2 pointtype 11
GPEOF

gnuplot "$PLOT_SCRIPT"

echo "Performance plot generated: ../data/pipeline_performance.png"

# Compute scaling coefficients
echo -e "\n=== Scaling Analysis ==="
for pipeline in simple medium complex; do
    echo -e "\n$pipeline pipeline:"
    grep "$pipeline" "$RESULTS" \
        | awk -F',' '
            NR==1 {x1=$1; y1=$2}
            END {
                x2=$1; y2=$2;
                if (x1 > 0 && y1 > 0) {
                    slope = (log(y2) - log(y1)) / (log(x2) - log(x1))
                    printf "  Scaling exponent: %.3f\n", slope
                    printf "  First point: %d bytes in %.4f sec\n", x1, y1
                    printf "  Last point: %d bytes in %.4f sec\n", x2, y2
                }
            }'
done
EOF

chmod +x analyze_results.sh
./analyze_results.sh
```

**Step 4: Verify theoretical predictions**

For I/O-bound pipelines like the simple case, we expect near-linear scaling (exponent ≈ 1.0) since the kernel's pipe buffer size (default 64 KB) forces synchronization. CPU-bound transformations like the complex pipeline may show slightly worse than linear scaling due to cache effects at large sizes.

Display the generated plot:

```bash
# On Linux with X11
display ../data/pipeline_performance.png

# On macOS
open ../data/pipeline_performance.png

# Or copy to a location accessible from your browser
```

**Step 5: Memory pressure analysis**

Measure peak memory usage as a function of pipeline complexity:

```bash
cat > memory_benchmark.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

LARGE_FILE="datasets/data_67108864.txt"  # 64 MB file

echo "=== Memory Usage Analysis ==="

for pipeline_type in simple medium complex; do
    echo -e "\nTesting $pipeline_type pipeline..."
    
    /usr/bin/time -v bash -c "
        case $pipeline_type in
            simple) cat '$LARGE_FILE' | wc -l ;;
            medium) cat '$LARGE_FILE' | grep -E '[0-9]+' | cut -d' ' -f1 | sort | uniq -c ;;
            complex) cat '$LARGE_FILE' | tr '[:upper:]' '[:lower:]' | grep -oE '\w+' | sort | uniq -c | sort -rn | head -100 ;;
        esac > /dev/null
    " 2>&1 | grep -E "(Maximum resident|Major|Minor|Voluntary|Involuntary)"
done
EOF

chmod +x memory_benchmark.sh
./memory_benchmark.sh
```

The simple pipeline shows minimal memory usage since data streams through without buffering. The medium pipeline's `sort` stage requires buffering the entire input, dramatically increasing resident set size. The complex pipeline demonstrates that combining multiple buffering stages (two `sort` invocations) compounds memory pressure.

---

## Exercise 3: Fault Injection & Stress Testing

**Objective:** Systematically inject failures into shell scripts—missing files, full disks, killed processes, signal interruptions—and verify that error handling mechanisms respond correctly. This exercise operationalizes defensive programming principles by observing how scripts behave under adverse conditions.

Production shell scripts must handle partial failures gracefully. A pipeline that processes thousands of files should not silently skip errors or leave the system in an inconsistent state. The `set -e` option (exit on error) and explicit signal traps provide foundational resilience, but their behavior under stress reveals design weaknesses.

**Step 1: Create a fault-tolerant processing script**

Build a script that processes multiple files with explicit error handling at each stage:

```bash
cd ~/bash-lab/ex3
cat > robust_processor.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Global state tracking
declare -i FILES_PROCESSED=0
declare -i FILES_FAILED=0
LOCKFILE="/tmp/processor_$$.lock"
STATUS_FILE="processing_status.log"

# Cleanup handler
cleanup() {
    local exit_code=$?
    echo "=== Cleanup Handler Triggered ===" >&2
    echo "Exit code: $exit_code" >&2
    echo "Files processed: $FILES_PROCESSED" >&2
    echo "Files failed: $FILES_FAILED" >&2
    
    rm -f "$LOCKFILE"
    
    if [[ $exit_code -ne 0 ]]; then
        echo "ERROR: Script terminated abnormally" >&2
        echo "Status saved to: $STATUS_FILE" >&2
    fi
    
    exit "$exit_code"
}

# Signal handlers
handle_sigint() {
    echo "SIGINT received - graceful shutdown initiated" >&2
    cleanup
}

handle_sigterm() {
    echo "SIGTERM received - immediate shutdown" >&2
    cleanup
}

# Register traps
trap cleanup EXIT
trap handle_sigint SIGINT
trap handle_sigterm SIGTERM

# Acquire lock to prevent concurrent execution
acquire_lock() {
    if [[ -f "$LOCKFILE" ]]; then
        local lock_pid
        lock_pid=$(cat "$LOCKFILE")
        if kill -0 "$lock_pid" 2>/dev/null; then
            echo "ERROR: Another instance is running (PID: $lock_pid)" >&2
            exit 1
        else
            echo "Stale lock file detected - removing" >&2
            rm -f "$LOCKFILE"
        fi
    fi
    
    echo $$ > "$LOCKFILE"
}

# Process single file with error handling
process_file() {
    local filepath="$1"
    local filename
    filename=$(basename "$filepath")
    
    echo "Processing: $filename" >&2
    
    # Simulate processing with random failure injection
    if [[ -r "$filepath" ]]; then
        local line_count
        if line_count=$(wc -l < "$filepath" 2>/dev/null); then
            echo "  Lines: $line_count" >&2
            
            # Simulate work
            sleep 0.1
            
            FILES_PROCESSED=$((FILES_PROCESSED + 1))
            echo "SUCCESS: $filename" >> "$STATUS_FILE"
            return 0
        else
            echo "  ERROR: Failed to read file" >&2
            FILES_FAILED=$((FILES_FAILED + 1))
            echo "FAILED: $filename (read error)" >> "$STATUS_FILE"
            return 1
        fi
    else
        echo "  ERROR: File not readable" >&2
        FILES_FAILED=$((FILES_FAILED + 1))
        echo "FAILED: $filename (permission denied)" >> "$STATUS_FILE"
        return 1
    fi
}

# Main processing loop
main() {
    local target_dir="${1:-.}"
    
    acquire_lock
    
    echo "=== Starting Batch Processing ===" >&2
    echo "Target directory: $target_dir" >&2
    echo "PID: $$" >&2
    echo "Timestamp: $(date -Iseconds)" >&2
    
    # Clear previous status
    > "$STATUS_FILE"
    
    # Process all .txt files
    local file_count=0
    while IFS= read -r -d '' filepath; do
        file_count=$((file_count + 1))
        
        # Continue on individual file failures
        if ! process_file "$filepath"; then
            echo "  Continuing despite failure..." >&2
        fi
        
        # Progress indicator every 10 files
        if (( file_count % 10 == 0 )); then
            echo "Progress: $file_count files examined" >&2
        fi
    done < <(find "$target_dir" -type f -name "*.txt" -print0 2>/dev/null)
    
    echo "=== Processing Complete ===" >&2
    echo "Total files: $file_count" >&2
    echo "Successfully processed: $FILES_PROCESSED" >&2
    echo "Failed: $FILES_FAILED" >&2
}

main "$@"
EOF

chmod +x robust_processor.sh
```

**Step 2: Create test environment with fault injection points**

Generate a dataset that includes files with various failure modes:

```bash
mkdir -p fault_test/{normal,unreadable,large,empty}

# Normal files
for i in {1..20}; do
    echo "Line $i: $(date +%s%N)" > "fault_test/normal/file$i.txt"
done

# Unreadable files (permission denied)
for i in {1..5}; do
    echo "Secret data" > "fault_test/unreadable/secret$i.txt"
    chmod 000 "fault_test/unreadable/secret$i.txt"
done

# Large files that may trigger buffering issues
for i in {1..3}; do
    seq 1 100000 > "fault_test/large/big$i.txt"
done

# Empty files
for i in {1..3}; do
    touch "fault_test/empty/empty$i.txt"
done

# Symlink to nonexistent target
ln -s /nonexistent/path fault_test/broken_link.txt
```

**Step 3: Baseline execution with fault injection**

Run the script and verify that it continues processing despite individual file failures:

```bash
./robust_processor.sh fault_test 2>&1 | tee execution.log

# Verify status tracking
echo -e "\n=== Status File Contents ==="
cat processing_status.log | sort | uniq -c
```

Expected output shows successful processing of accessible files and logged failures for permission-denied cases.

**Step 4: Signal interruption testing**

Test graceful shutdown on SIGINT (Ctrl+C):

```bash
# Run script in background
./robust_processor.sh fault_test &
PROCESSOR_PID=$!

# Allow some processing to occur
sleep 2

# Send SIGINT
echo "Sending SIGINT to PID $PROCESSOR_PID"
kill -SIGINT "$PROCESSOR_PID"

# Wait for cleanup
wait "$PROCESSOR_PID"
echo "Exit code: $?"

# Verify cleanup occurred
ls -l /tmp/processor_*.lock 2>&1 | grep "No such file"
```

The cleanup handler executes, logs partial progress, and removes the lock file.

**Step 5: Resource exhaustion simulation**

Test behavior when output disk is full:

```bash
# Create a small filesystem for testing
dd if=/dev/zero of=small_fs.img bs=1M count=10
mkfs.ext4 -F small_fs.img
mkdir -p mount_point
sudo mount -o loop small_fs.img mount_point

# Create test data that will overflow the filesystem
mkdir -p mount_point/overflow_test
for i in {1..5}; do
    seq 1 50000 > "mount_point/overflow_test/file$i.txt"
done

# Modify script to write large output to the small filesystem
cat > disk_full_test.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="mount_point/overflow_test/output"
mkdir -p "$OUTPUT_DIR"

for i in {1..100}; do
    if ! cat "mount_point/overflow_test/file1.txt" >> "$OUTPUT_DIR/accumulated.txt" 2>/dev/null; then
        echo "ERROR: Write failed at iteration $i" >&2
        echo "Likely cause: No space left on device" >&2
        df -h mount_point
        exit 1
    fi
done
EOF

chmod +x disk_full_test.sh
./disk_full_test.sh

# Cleanup
sudo umount mount_point
rm -f small_fs.img
```

The script detects write failures and exits with a diagnostic message rather than silently producing truncated output.

**Step 6: Concurrent execution conflict testing**

Verify that the lock mechanism prevents concurrent execution:

```bash
# Start first instance
./robust_processor.sh fault_test &
PID1=$!

# Attempt second instance immediately
sleep 0.5
./robust_processor.sh fault_test 2>&1 | tee concurrent_test.log &
PID2=$!

# Wait for both
wait "$PID1"
wait "$PID2"

# Verify second instance detected lock
grep "Another instance is running" concurrent_test.log
```

The second instance exits immediately after detecting the active lock.

**Step 7: Subprocess failure propagation**

Test that pipeline failures propagate correctly with `set -o pipefail`:

```bash
cat > pipeline_failure_test.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "=== Test 1: Failure in middle of pipeline ==="
if cat /nonexistent/file | grep "pattern" | wc -l; then
    echo "Pipeline succeeded (UNEXPECTED)"
else
    echo "Pipeline failed as expected (exit code: $?)"
fi

echo -e "\n=== Test 2: Failure in first stage ==="
set -o pipefail
if false | true | true; then
    echo "Pipeline succeeded (UNEXPECTED)"
else
    echo "Pipeline failed due to first stage (exit code: $?)"
fi

echo -e "\n=== Test 3: Success propagates ==="
if echo "test" | grep "test" | wc -l > /dev/null; then
    echo "Pipeline succeeded as expected"
else
    echo "Pipeline failed (UNEXPECTED)"
fi
EOF

chmod +x pipeline_failure_test.sh
./pipeline_failure_test.sh
```

With `pipefail` enabled, the exit status reflects any failure in the pipeline rather than only the final command.

**Step 8: Memory limit stress testing**

Use `ulimit` to constrain memory and observe behavior:

```bash
cat > memory_limit_test.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Set virtual memory limit to 100 MB
ulimit -v 102400

echo "Memory limit set to: $(ulimit -v) KB"

# Attempt to load large file into memory
if CONTENT=$(cat fault_test/large/big1.txt 2>&1); then
    echo "File loaded successfully (${#CONTENT} bytes)"
else
    echo "Failed to load file due to memory constraints"
fi

# Attempt memory-intensive sort operation
echo -e "\nAttempting memory-intensive sort..."
if seq 1 10000000 | sort > /dev/null 2>&1; then
    echo "Sort succeeded"
else
    echo "Sort failed due to memory limit"
fi
EOF

chmod +x memory_limit_test.sh
./memory_limit_test.sh
```

The script demonstrates that operations exceeding the memory limit fail predictably rather than causing system-wide instability.

---

## Practical Cheat Sheet & Quick Reference

### Essential Bash Options

| Option | Effect |
|--------|--------|
| `set -e` | Exit immediately if any command returns non-zero |
| `set -u` | Treat unset variables as errors |
| `set -o pipefail` | Pipeline fails if any stage fails |
| `set -x` | Print each command before execution (debugging) |
| `shopt -s nullglob` | Glob patterns that match nothing expand to empty string |
| `shopt -s extglob` | Enable extended pattern matching |

### File Descriptor Redirection

| Syntax | Meaning |
|--------|---------|
| `> file` | Redirect stdout to file (overwrite) |
| `>> file` | Redirect stdout to file (append) |
| `2> file` | Redirect stderr to file |
| `&> file` | Redirect both stdout and stderr |
| `2>&1` | Redirect stderr to wherever stdout points |
| `< file` | Redirect stdin from file |
| `<< EOF` | Here-document (stdin from literal text) |
| `<<< "text"` | Here-string (single line to stdin) |
| `exec 3< file` | Open file on fd 3 for reading |
| `exec 4> file` | Open file on fd 4 for writing |

### Variable Expansion Patterns

| Syntax | Behavior |
|--------|----------|
| `$VAR` or `${VAR}` | Basic expansion |
| `${VAR:-default}` | Use default if unset |
| `${VAR:=default}` | Assign default if unset |
| `${VAR:?error_msg}` | Exit with error if unset |
| `${VAR:+alternate}` | Use alternate if set |
| `${#VAR}` | Length of string |
| `${VAR#pattern}` | Remove shortest match from beginning |
| `${VAR##pattern}` | Remove longest match from beginning |
| `${VAR%pattern}` | Remove shortest match from end |
| `${VAR%%pattern}` | Remove longest match from end |
| `${VAR/pattern/replacement}` | Replace first match |
| `${VAR//pattern/replacement}` | Replace all matches |

### Command Substitution & Process Substitution

| Syntax | Meaning |
|--------|---------|
| `$(command)` | Command substitution (preferred) |
| `` `command` `` | Command substitution (legacy) |
| `<(command)` | Process substitution (creates temp file with output) |
| `>(command)` | Process substitution (creates temp file as input) |

### Array Operations

| Syntax | Effect |
|--------|--------|
| `arr=(val1 val2 val3)` | Define array |
| `${arr[0]}` | Access first element |
| `${arr[@]}` | Expand all elements as separate words |
| `${arr[*]}` | Expand all elements as single word |
| `${#arr[@]}` | Array length |
| `arr+=(val4)` | Append element |
| `unset arr[2]` | Delete element |
| `"${arr[@]:1:3}"` | Slice (offset 1, length 3) |

### Signal Handling

| Signal | Typical Use |
|--------|------------|
| `SIGINT (2)` | User interrupt (Ctrl+C) |
| `SIGTERM (15)` | Graceful termination request |
| `SIGKILL (9)` | Forced kill (cannot be caught) |
| `SIGHUP (1)` | Terminal closed |
| `SIGUSR1 (10)` | User-defined signal 1 |
| `SIGUSR2 (12)` | User-defined signal 2 |

**Trap Syntax:**
```bash
trap 'cleanup_function' EXIT
trap 'handle_interrupt' SIGINT SIGTERM
trap - SIGINT  # Remove trap
```

### Pipeline Performance Verification

```bash
# Measure pipeline throughput
pv input.txt | processing_command | output_command

# Profile CPU usage per pipeline stage
ps -eo pid,cmd,%cpu | grep pipeline_stage

# Monitor pipe buffer usage (Linux)
cat /proc/sys/fs/pipe-max-size

# Trace system calls in pipeline
strace -f -e trace=pipe,read,write,dup2 -o trace.log command

# Measure memory peak for command
/usr/bin/time -v command 2>&1 | grep "Maximum resident"
```

### Error Handling Patterns

```bash
# Explicit error handling
if ! command; then
    echo "Command failed" >&2
    exit 1
fi

# Short-circuit with ||
command || { echo "Failed" >&2; exit 1; }

# Store exit code
command
exit_code=$?
if [[ $exit_code -ne 0 ]]; then
    handle_error "$exit_code"
fi

# Subshell failure isolation
(risky_command) || echo "Subshell failed but main script continues"

# Disable exit-on-error temporarily
set +e
command_that_may_fail
set -e
```

### Quick Diagnostic Commands

| Command | Purpose |
|---------|---------|
| `type command` | Show if command is alias, function, or binary |
| `declare -f function_name` | Print function definition |
| `declare -p VAR` | Print variable attributes and value |
| `set -o` | Show all shell options |
| `echo $-` | Show active options (compact) |
| `trap -p` | Show active traps |
| `jobs -l` | List background jobs with PIDs |
| `ps -p $$` | Show current shell process |
| `lsof -p $$` | Show open file descriptors |
| `strace -p PID` | Attach to running process |

### Verification Checklist

Before deploying any shell script to production:

1. **Shebang line present:** `#!/usr/bin/env bash` (portable) or `#!/bin/bash`
2. **Error handling enabled:** `set -euo pipefail` in non-interactive scripts
3. **Variable quoting:** All variable references in `"${VAR}"` form to prevent word splitting
4. **Signal traps registered:** At minimum, trap EXIT for cleanup
5. **Lock files for serialization:** Prevent concurrent execution of non-reentrant scripts
6. **Explicit logging:** Diagnostic messages to stderr, data to stdout
7. **Input validation:** Check argument count and types before processing
8. **Resource limits:** Use `ulimit` to constrain memory and CPU time
9. **Timeout enforcement:** Use `timeout` command for operations that may hang
10. **Static analysis:** Run `shellcheck` to detect common errors

**ShellCheck Example:**
```bash
shellcheck -x -s bash script.sh
```

This verification framework provides the empirical foundation for writing shell scripts that behave predictably under both normal operation and fault conditions. The exercises demonstrate that defensive programming is not about avoiding action but about making system behavior observable and failures recoverable.
