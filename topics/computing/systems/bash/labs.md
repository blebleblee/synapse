# Operational Verification Labs: Core

## Objective & Lab Setup

This laboratory sequence operationalizes the foundational mechanics of the Bash shell through empirical measurement, fault injection, and behavioral verification. You will interrogate process spawning semantics, file descriptor lifecycle, pipeline buffer saturation, signal propagation, exit code chaining, and subprocess resource isolation. Each exercise produces measurable state transitions observable through `/proc` filesystem introspection, `strace` system call tracing, and timing analysis.

The Bash shell operates as a user-space orchestrator that translates command syntax into kernel system calls: `fork()` creates child processes, `execve()` replaces process images, `pipe()` establishes inter-process communication channels with fixed kernel buffer capacity (typically 64 KiB on Linux), `dup2()` remaps file descriptors, and `waitpid()` harvests exit codes. Understanding these primitives grounds every script you write in the actual state machine executed by the operating system.

**Required Environment:**

Provision a Linux system (bare-metal, VM, or WSL2) with kernel 5.10 or later. Install the following packages:

```bash
sudo apt-get update
sudo apt-get install -y \
  bash \
  coreutils \
  strace \
  time \
  procps \
  util-linux \
  stress-ng \
  bc \
  gnuplot
```

Verify your Bash version supports process substitution and coprocesses:

```bash
bash --version  # Ensure >= 5.0
```

Create a dedicated working directory with sufficient disk quota for log file generation:

```bash
mkdir -p ~/bash-labs/core
cd ~/bash-labs/core
```

Set resource limits to prevent accidental system exhaustion during fault injection:

```bash
ulimit -u 4096      # Max user processes
ulimit -n 4096      # Max open files
ulimit -f 1048576   # Max file size (1 GiB blocks)
```

All exercises assume you execute commands within this prepared environment. Commands prefixed with `$` indicate standard user shell prompts; output examples appear without prefixes.

---

## Exercise 1: Foundational Practical Implementation

This exercise dissects the shell's process lifecycle, pipeline construction, and exit code propagation through direct observation of kernel state. You will spawn subprocesses, trace their system calls, measure pipeline buffer behavior, and verify exit code semantics under command substitution and pipeline chaining.

### Part A: Process Spawning and Fork-Exec Lifecycle

Every command execution in Bash triggers a `fork()` system call that duplicates the current process, creating a child with an identical address space (copy-on-write semantics). The child then invokes `execve()` to replace its process image with the target program. Observe this sequence by tracing a simple command:

```bash
strace -f -e trace=fork,clone,execve bash -c 'ls /tmp' 2>&1 | grep -E 'fork|clone|execve'
```

You will observe `clone()` (the modern `fork()` implementation) creating the child process, followed by `execve("/bin/ls", ...)` replacing the child's address space. The parent Bash process blocks in `waitpid()` until the child terminates, harvesting its exit code.

Create a script that demonstrates subshell isolation and environment inheritance:

```bash
cat > subshell_test.sh <<'EOF'
#!/bin/bash
export PARENT_VAR="parent_value"
echo "Parent PID: $$"
echo "Parent VAR: $PARENT_VAR"

(
  echo "Subshell PID: $$"
  echo "Inherited VAR: $PARENT_VAR"
  PARENT_VAR="modified_in_subshell"
  echo "Modified VAR: $PARENT_VAR"
)

echo "After subshell VAR: $PARENT_VAR"
EOF

chmod +x subshell_test.sh
./subshell_test.sh
```

Expected output demonstrates that the subshell (created via `fork()`) inherits the environment but modifications remain isolated due to copy-on-write semantics. The parent process retains the original `PARENT_VAR` value after the subshell exits.

Verify process isolation by examining `/proc` filesystem entries:

```bash
cat > proc_inspect.sh <<'EOF'
#!/bin/bash
echo "Main shell PID: $$"
(
  echo "Subshell PID: $$"
  sleep 30 &
  BGPID=$!
  echo "Background job PID: $BGPID"
  echo "Listing /proc/$BGPID/status:"
  grep -E 'Pid|PPid|Name' /proc/$BGPID/status
  wait $BGPID
)
EOF

chmod +x proc_inspect.sh
./proc_inspect.sh
```

The background `sleep` process shows `PPid` (parent PID) matching the subshell PID, confirming the process tree hierarchy.

### Part B: Pipeline Buffer Saturation and Blocking Behavior

Pipelines connect process standard I/O streams through kernel pipe buffers with fixed capacity. When the buffer fills, the writer blocks until the reader consumes data. Measure this behavior by saturating a pipe:

```bash
cat > pipe_buffer_test.sh <<'EOF'
#!/bin/bash

# Determine kernel pipe buffer size
PIPE_SIZE=$(cat /proc/sys/fs/pipe-max-size)
echo "Kernel max pipe buffer: $PIPE_SIZE bytes"

# Create a writer that generates data faster than reader consumes
echo "Testing pipe buffer saturation..."
(
  # Writer: generate 10 MiB
  dd if=/dev/zero bs=1M count=10 2>/dev/null
) | (
  # Reader: consume slowly (1 byte/sec)
  dd of=/dev/null bs=1 count=100 iflag=fullblock 2>/dev/null &
  READER_PID=$!
  
  # Monitor writer's state
  sleep 2
  WRITER_PID=$(pgrep -P $$ dd | head -1)
  if [ -n "$WRITER_PID" ]; then
    echo "Writer PID $WRITER_PID state:"
    grep State /proc/$WRITER_PID/status
  fi
  
  wait $READER_PID
)
EOF

chmod +x pipe_buffer_test.sh
timeout 10 ./pipe_buffer_test.sh
```

When the writer fills the pipe buffer (typically 64 KiB on Linux kernels), its process state transitions to `S (interruptible sleep)` as it blocks on the `write()` system call. The kernel scheduler resumes the writer only after the reader's `read()` drains buffer space.

Empirically measure pipeline throughput by varying block sizes:

```bash
cat > pipeline_throughput.sh <<'EOF'
#!/bin/bash

echo "Block_Size_KB,Throughput_MBps,Elapsed_Sec" > pipeline_results.csv

for BS in 1 4 16 64 256 1024; do
  START=$(date +%s.%N)
  dd if=/dev/zero bs=${BS}k count=$((10240/BS)) 2>/dev/null | dd of=/dev/null bs=${BS}k 2>/dev/null
  END=$(date +%s.%N)
  ELAPSED=$(echo "$END - $START" | bc)
  THROUGHPUT=$(echo "scale=2; 10 / $ELAPSED" | bc)
  echo "$BS,$THROUGHPUT,$ELAPSED" | tee -a pipeline_results.csv
done
EOF

chmod +x pipeline_throughput.sh
./pipeline_throughput.sh
```

Plot results to observe throughput increasing with block size until reaching the pipe buffer's natural transfer unit (typically optimal at 64 KiB):

```bash
gnuplot <<'EOF'
set terminal dumb
set datafile separator ","
set xlabel "Block Size (KiB)"
set ylabel "Throughput (MiB/s)"
plot 'pipeline_results.csv' using 1:2 with linespoints title "Pipeline Throughput"
EOF
```

### Part C: Exit Code Propagation and PIPESTATUS

Bash captures exit codes from every command in a pipeline through the `PIPESTATUS` array. By default, the pipeline's overall exit code reflects only the rightmost command, but `set -o pipefail` changes this to fail on the first non-zero exit:

```bash
cat > exit_code_test.sh <<'EOF'
#!/bin/bash

echo "=== Default Behavior (rightmost exit code wins) ==="
false | false | true
echo "Pipeline exit code: $?"
echo "PIPESTATUS array: ${PIPESTATUS[@]}"

echo ""
echo "=== With pipefail (fail on first error) ==="
set -o pipefail
false | false | true
echo "Pipeline exit code: $?"
echo "PIPESTATUS array: ${PIPESTATUS[@]}"

set +o pipefail
echo ""
echo "=== Command Substitution Exit Code ==="
OUTPUT=$(false; echo "captured")
echo "Substitution exit code: $?"
echo "Captured output: $OUTPUT"
EOF

chmod +x exit_code_test.sh
./exit_code_test.sh
```

Observe that without `pipefail`, the pipeline succeeds because `true` (the rightmost command) returns zero. The `PIPESTATUS` array preserves all intermediate exit codes for forensic analysis. Command substitution captures the *last* command's exit code, a common source of error-handling bugs in production scripts.

Create a robust error-handling wrapper:

```bash
cat > robust_pipeline.sh <<'EOF'
#!/bin/bash
set -euo pipefail

# Trap handler for debugging
trap 'echo "Error on line $LINENO: exit code $?"' ERR

# Function with intentional failure
fail_in_middle() {
  echo "Stage 1: success" | tee stage1.log
  false  # Intentional failure
  echo "Stage 3: never reached" | tee stage3.log
}

echo "Testing error propagation..."
if fail_in_middle; then
  echo "Pipeline succeeded"
else
  echo "Pipeline failed as expected"
  echo "PIPESTATUS: ${PIPESTATUS[@]}"
fi
EOF

chmod +x robust_pipeline.sh
./robust_pipeline.sh
```

The `set -e` option terminates execution on any non-zero exit code, while `set -u` treats unset variables as errors, and `set -o pipefail` ensures pipeline failures propagate correctly. This combination forms the foundation of defensive scripting practices.

---

## Exercise 2: Parameter Variation & Empirical Analysis

This exercise quantifies shell performance characteristics through controlled parameter variation. You will measure subprocess spawning overhead, pipeline buffer throughput under different block sizes, file descriptor exhaustion thresholds, and signal delivery latency. Each test produces empirical data for graphical analysis.

### Part A: Subprocess Spawning Overhead and Fork Bomb Dynamics

Subprocess creation carries measurable overhead due to `fork()` and `execve()` system calls. Benchmark the time cost of spawning processes versus invoking shell builtins:

```bash
cat > spawn_overhead.sh <<'EOF'
#!/bin/bash

ITERATIONS=1000

echo "Benchmark,Iterations,Elapsed_Sec,Per_Call_Usec" > spawn_results.csv

# Test 1: Shell builtin (no fork)
START=$(date +%s.%N)
for ((i=0; i<ITERATIONS; i++)); do
  : # Null command (builtin)
done
END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)
PER_CALL=$(echo "scale=2; $ELAPSED * 1000000 / $ITERATIONS" | bc)
echo "Builtin,$ITERATIONS,$ELAPSED,$PER_CALL" | tee -a spawn_results.csv

# Test 2: External command (fork + exec)
START=$(date +%s.%N)
for ((i=0; i<ITERATIONS; i++)); do
  /bin/true
done
END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)
PER_CALL=$(echo "scale=2; $ELAPSED * 1000000 / $ITERATIONS" | bc)
echo "External,$ITERATIONS,$ELAPSED,$PER_CALL" | tee -a spawn_results.csv

# Test 3: Subshell (fork only)
START=$(date +%s.%N)
for ((i=0; i<ITERATIONS; i++)); do
  ( : )
done
END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)
PER_CALL=$(echo "scale=2; $ELAPSED * 1000000 / $ITERATIONS" | bc)
echo "Subshell,$ITERATIONS,$ELAPSED,$PER_CALL" | tee -a spawn_results.csv
EOF

chmod +x spawn_overhead.sh
./spawn_overhead.sh
```

Typical results show builtins execute in under 1 microsecond, subshells require 50–100 microseconds for `fork()`, and external commands add 200–500 microseconds for `execve()` and program loading. This overhead compounds in loops processing large datasets, motivating the use of Bash builtins over external utilities when performance matters.

Measure fork bomb dynamics under controlled resource limits:

```bash
cat > fork_bomb_controlled.sh <<'EOF'
#!/bin/bash

# Set strict limits to prevent system DoS
ulimit -u 256  # Max 256 processes
ulimit -t 10   # Max 10 CPU seconds

echo "Testing controlled fork bomb (limited to 256 processes)..."

fork_bomb() {
  (fork_bomb &) &
}

# Launch and measure until resource exhaustion
START=$(date +%s)
fork_bomb 2>/dev/null
END=$(date +%s)

ELAPSED=$((END - START))
FINAL_PROCS=$(pgrep -u $(whoami) bash | wc -l)

echo "Time to exhaustion: ${ELAPSED} seconds"
echo "Final process count: ${FINAL_PROCS}"
echo "Killing orphaned processes..."
pkill -9 -u $(whoami) bash
EOF

chmod +x fork_bomb_controlled.sh
./fork_bomb_controlled.sh
```

The fork bomb exponentially spawns processes until hitting `ulimit -u` (process limit) or `ulimit -t` (CPU time limit). Observe that process creation accelerates until resource exhaustion, demonstrating why production systems require per-user cgroup limits.

### Part B: Pipeline Buffer Throughput Under Variable Block Sizes

Revisit pipeline throughput with finer granularity, testing block sizes from 512 bytes to 4 MiB and measuring kernel buffer efficiency:

```bash
cat > pipeline_granular.sh <<'EOF'
#!/bin/bash

echo "Block_Size_Bytes,Throughput_MBps,User_Time,Sys_Time" > pipeline_granular.csv

for BS in 512 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288 1048576 2097152 4194304; do
  COUNT=$((1048576 / (BS / 1024)))  # Generate 1 GiB total
  
  TIME_OUTPUT=$( { time -p dd if=/dev/zero bs=$BS count=$COUNT 2>/dev/null | dd of=/dev/null bs=$BS 2>/dev/null ; } 2>&1 )
  
  REAL=$(echo "$TIME_OUTPUT" | awk '/^real/ {print $2}')
  USER=$(echo "$TIME_OUTPUT" | awk '/^user/ {print $2}')
  SYS=$(echo "$TIME_OUTPUT" | awk '/^sys/ {print $2}')
  
  THROUGHPUT=$(echo "scale=2; 1024 / $REAL" | bc)
  
  echo "$BS,$THROUGHPUT,$USER,$SYS" | tee -a pipeline_granular.csv
done
EOF

chmod +x pipeline_granular.sh
./pipeline_granular.sh
```

Generate comparative plots for throughput and CPU time distribution:

```bash
gnuplot <<'EOF'
set terminal dumb size 120,30
set datafile separator ","
set logscale x 2
set xlabel "Block Size (bytes, log scale)"
set ylabel "Throughput (MiB/s)"
set y2label "CPU Time (sec)"
set ytics nomirror
set y2tics
plot 'pipeline_granular.csv' using 1:2 axes x1y1 with linespoints title "Throughput", \
     'pipeline_granular.csv' using 1:4 axes x1y2 with linespoints title "Sys Time"
EOF
```

Observe throughput increasing logarithmically until block size matches the kernel's pipe buffer capacity (64 KiB), after which diminishing returns set in. System time (kernel CPU usage) decreases with larger blocks due to reduced system call frequency.

### Part C: File Descriptor Exhaustion and Leak Detection

Every pipe, redirection, and subprocess consumes file descriptors from a per-process limit (default 1024, tunable via `ulimit -n`). Measure descriptor exhaustion by opening files in a loop:

```bash
cat > fd_exhaustion.sh <<'EOF'
#!/bin/bash

ulimit -n 256  # Reduce to accelerate test

echo "Opening files until descriptor exhaustion..."
COUNT=0

while true; do
  exec {FD}>/dev/null 2>&1 || break
  ((COUNT++))
done

echo "Opened $COUNT file descriptors before exhaustion"

# List open descriptors
echo "Currently open descriptors:"
ls -l /proc/$$/fd | wc -l

# Close all dynamically opened descriptors
for ((i=10; i<260; i++)); do
  eval "exec $i>&-" 2>/dev/null
done

echo "After cleanup:"
ls -l /proc/$$/fd | wc -l
EOF

chmod +x fd_exhaustion.sh
./fd_exhaustion.sh
```

The script opens file descriptors in a loop using Bash's dynamic descriptor allocation syntax (`exec {FD}>file`), stopping when the kernel returns `EMFILE` (too many open files). Inspect `/proc/$$/fd` to enumerate all open descriptors, including stdin (0), stdout (1), stderr (2), and any leaked descriptors from previous commands.

Create a descriptor leak detector:

```bash
cat > fd_leak_detector.sh <<'EOF'
#!/bin/bash

BASELINE=$(ls /proc/$$/fd | wc -l)
echo "Baseline descriptors: $BASELINE"

# Simulate leaky function
leaky_function() {
  for i in {1..10}; do
    exec {FD}>/tmp/leak_$i.txt
    # Intentionally never close $FD
  done
}

leaky_function

AFTER=$(ls /proc/$$/fd | wc -l)
LEAKED=$((AFTER - BASELINE))
echo "Descriptors after leaky function: $AFTER (leaked $LEAKED)"

# Cleanup
rm -f /tmp/leak_*.txt
for ((i=10; i<100; i++)); do
  eval "exec $i>&-" 2>/dev/null
done
EOF

chmod +x fd_leak_detector.sh
./fd_leak_detector.sh
```

Descriptor leaks accumulate silently until processes fail to open files. Production scripts must explicitly close descriptors or use subshells to ensure automatic cleanup.

---

## Exercise 3: Fault Injection & Stress Testing

This exercise induces controlled failure modes to validate error handling, signal propagation, and recovery mechanisms. You will trigger out-of-memory conditions, send asynchronous signals to pipelines, exhaust disk space during I/O operations, and verify atomic file update patterns under interruption.

### Part A: Signal Propagation Through Pipelines

Signals sent to a pipeline must propagate correctly to all constituent processes. Test SIGINT (Ctrl+C) and SIGTERM handling:

```bash
cat > signal_pipeline.sh <<'EOF'
#!/bin/bash

cleanup() {
  echo "Caught signal in main script, cleaning up..."
  jobs -p | xargs -r kill 2>/dev/null
  exit 130
}

trap cleanup SIGINT SIGTERM

echo "Starting pipeline (PID $$). Press Ctrl+C to interrupt..."

# Create a long-running pipeline
(
  trap 'echo "Stage 1 interrupted"; exit 130' SIGINT SIGTERM
  while true; do
    echo "Stage 1 running..."
    sleep 2
  done
) | (
  trap 'echo "Stage 2 interrupted"; exit 130' SIGINT SIGTERM
  while read line; do
    echo "Stage 2 processing: $line"
    sleep 1
  done
) &

PIPELINE_PID=$!
wait $PIPELINE_PID
echo "Pipeline exit code: $?"
EOF

chmod +x signal_pipeline.sh
timeout 10 ./signal_pipeline.sh
```

When you send SIGINT (via `timeout` or Ctrl+C), observe that each stage's trap handler executes, allowing graceful cleanup. Without explicit traps, processes receive default signal behavior (often termination without cleanup).

Test signal masking and delivery timing:

```bash
cat > signal_race.sh <<'EOF'
#!/bin/bash

SIGNAL_COUNT=0

count_signal() {
  ((SIGNAL_COUNT++))
  echo "Received signal #$SIGNAL_COUNT"
}

trap count_signal SIGUSR1

echo "Main PID: $$"
echo "Sending 100 rapid SIGUSR1 signals..."

for i in {1..100}; do
  kill -SIGUSR1 $$ &
done

wait
sleep 1
echo "Total signals caught: $SIGNAL_COUNT"
EOF

chmod +x signal_race.sh
./signal_race.sh
```

Signal delivery is asynchronous and non-queuing: multiple signals of the same type coalesce if delivered before the handler completes. You will observe fewer than 100 signals caught, demonstrating why critical sections require signal masking (`trap '' SIGUSR1` to block).

### Part B: Disk Space Exhaustion and Atomic File Updates

Simulate disk exhaustion during file writes and verify atomic update patterns that prevent data corruption:

```bash
cat > disk_exhaustion.sh <<'EOF'
#!/bin/bash

# Create a small disk image
dd if=/dev/zero of=testfs.img bs=1M count=10 2>/dev/null
mkfs.ext4 -F testfs.img >/dev/null 2>&1
mkdir -p testmount
sudo mount -o loop testfs.img testmount
sudo chown $(whoami) testmount

cd testmount

echo "Writing until disk full..."
dd if=/dev/zero of=bigfile bs=1M 2>&1 | grep -i 'no space'

# Test non-atomic write (direct overwrite)
echo "original content" > target.txt
echo "Attempting non-atomic overwrite..."
if echo "new content that will fail" > target.txt 2>/dev/null; then
  echo "Write succeeded (unexpected)"
else
  echo "Write failed. File content:"
  cat target.txt 2>/dev/null || echo "(file corrupted or missing)"
fi

# Test atomic write (write-then-rename)
echo "Attempting atomic update via temp file..."
if echo "new content via atomic pattern" > target.txt.tmp 2>/dev/null && mv target.txt.tmp target.txt 2>/dev/null; then
  echo "Atomic update succeeded (unexpected)"
else
  echo "Atomic update failed. Original file intact:"
  cat target.txt 2>/dev/null || echo "(file corrupted or missing)"
fi

cd ..
sudo umount testmount
rm -rf testmount testfs.img
EOF

chmod +x disk_exhaustion.sh
./disk_exhaustion.sh
```

Direct overwrites (`>` redirection) truncate the target file *before* writing, causing data loss on failure. The atomic pattern (write to `.tmp`, then `mv`) leverages rename's atomicity guarantee: the `mv` operation either fully succeeds or leaves the original file untouched, preventing partial updates.

### Part C: Out-of-Memory Conditions and Process Killing

Trigger the Linux OOM (Out-Of-Memory) killer by allocating memory faster than the kernel can reclaim:

```bash
cat > oom_test.sh <<'EOF'
#!/bin/bash

# Set memory limit to 512 MiB for this process group
ulimit -v 524288

oom_bomb() {
  echo "Allocating memory until OOM..."
  
  ARRAY=()
  COUNT=0
  
  while true; do
    # Allocate 10 MiB strings
    ARRAY[$COUNT]=$(head -c 10485760 /dev/zero | tr '\0' 'A')
    ((COUNT++))
    
    if ((COUNT % 10 == 0)); then
      echo "Allocated $((COUNT * 10)) MiB"
    fi
  done
}

# Run in subshell to isolate
(
  trap 'echo "OOM bomb terminated"; exit 137' SIGKILL
  oom_bomb
) &

BOMB_PID=$!
wait $BOMB_PID
EXIT_CODE=$?

echo "Process exit code: $EXIT_CODE"
if ((EXIT_CODE == 137)); then
  echo "Process killed by SIGKILL (likely OOM killer)"
fi
EOF

chmod +x oom_test.sh
./oom_test.sh
```

When virtual memory limit (`ulimit -v`) is exceeded, the kernel sends SIGKILL to the process. Exit code 137 (128 + 9) confirms SIGKILL delivery. On systems without `ulimit -v` enforcement, the kernel OOM killer selects the highest-memory process for termination, logged in `dmesg`.

Create a memory pressure test with graceful degradation:

```bash
cat > memory_pressure.sh <<'EOF'
#!/bin/bash

ulimit -v 524288  # 512 MiB limit

allocate_with_fallback() {
  SIZE_MB=$1
  
  if BUFFER=$(head -c $((SIZE_MB * 1048576)) /dev/zero 2>/dev/null | tr '\0' 'A' 2>/dev/null); then
    echo "Successfully allocated ${SIZE_MB} MiB"
    return 0
  else
    echo "Failed to allocate ${SIZE_MB} MiB (reducing to half)"
    allocate_with_fallback $((SIZE_MB / 2))
    return $?
  fi
}

echo "Testing graceful degradation under memory pressure..."

for SIZE in 256 128 64 32 16 8 4 2 1; do
  if allocate_with_fallback $SIZE; then
    break
  fi
done

echo "Minimum successful allocation: $SIZE MiB"
EOF

chmod +x memory_pressure.sh
./memory_pressure.sh
```

This pattern demonstrates binary search allocation: when large requests fail, halve the request size until succeeding, allowing scripts to adapt to available resources rather than failing catastrophically.

### Part D: Pipeline Interruption and Partial Data Handling

Test pipeline behavior when the reader terminates early, generating SIGPIPE for the writer:

```bash
cat > sigpipe_test.sh <<'EOF'
#!/bin/bash

echo "Testing SIGPIPE behavior..."

# Writer that generates infinite data
(
  trap 'echo "Writer caught SIGPIPE"; exit 141' SIGPIPE
  
  while true; do
    echo "data line"
  done
) | (
  # Reader that exits after 10 lines
  head -10 >/dev/null
)

PIPE_EXIT=${PIPESTATUS[0]}
echo "Writer exit code: $PIPE_EXIT"

if ((PIPE_EXIT == 141)); then
  echo "Writer terminated by SIGPIPE (128 + 13 = 141)"
fi

echo ""
echo "Testing SIGPIPE with error handling..."

(
  # Ignore SIGPIPE and check write() errors
  trap '' SIGPIPE
  
  COUNT=0
  while true; do
    echo "data line" || {
      echo "Write failed after $COUNT lines"
      exit 1
    }
    ((COUNT++))
  done
) | head -10 >/dev/null

echo "Writer exit code: ${PIPESTATUS[0]}"
EOF

chmod +x sigpipe_test.sh
./sigpipe_test.sh
```

When the pipeline reader closes its input (via `head -10`), subsequent writes by the writer fail with EPIPE (broken pipe). The kernel delivers SIGPIPE to the writer, terminating it unless trapped. Production scripts handling large datasets must either trap SIGPIPE or check write errors explicitly to detect premature reader termination.

---

## Practical Cheat Sheet & Quick Reference

The following table consolidates essential Bash commands, parameter expansions, and verification techniques for operational troubleshooting and script debugging.

| **Category** | **Command / Syntax** | **Description** | **Example** |
|--------------|---------------------|-----------------|-------------|
| **Process Introspection** | `echo $$` | Current shell PID | `echo "Shell PID: $$"` |
| | `echo $PPID` | Parent process PID | `ps -p $PPID` |
| | `echo $BASHPID` | PID of current Bash instance (differs in subshells) | `(echo $BASHPID)` |
| | `/proc/$$/status` | Process state details | `grep State /proc/$$/status` |
| | `/proc/$$/fd` | Open file descriptors | `ls -l /proc/$$/fd` |
| | `pstree -p $$` | Process tree from current shell | `pstree -p $$` |
| **Exit Codes** | `$?` | Last command exit code | `ls /nonexistent; echo $?` |
| | `${PIPESTATUS[@]}` | Exit codes of all pipeline commands | `false | true; echo ${PIPESTATUS[@]}` |
| | `set -e` | Exit on any non-zero exit | `set -e; false; echo "never printed"` |
| | `set -o pipefail` | Fail pipeline on first error | `set -o pipefail; false | true; echo $?` |
| | `trap 'echo "Error on line $LINENO"' ERR` | Debug trap on command failure | `trap 'echo "Failed: $LINENO"' ERR` |
| **File Descriptors** | `exec 3<file` | Open file on descriptor 3 for reading | `exec 3</etc/hosts; cat <&3` |
| | `exec 4>file` | Open file on descriptor 4 for writing | `exec 4>/tmp/out.txt; echo "data" >&4` |
| | `exec {fd}<file` | Dynamically allocate descriptor | `exec {myfd}</etc/hosts; cat <&$myfd` |
| | `exec 3>&-` | Close file descriptor 3 | `exec 3>&-` |
| | `lsof -p $$` | List open files for current process | `lsof -p $$ | grep REG` |
| **Redirection** | `cmd >file 2>&1` | Redirect stdout and stderr to file | `ls /tmp /nonexistent >log 2>&1` |
| | `cmd 2>&1 | tee log` | Merge stderr to stdout, tee to file | `make 2>&1 | tee build.log` |
| | `cmd < <(other)` | Process substitution as input | `diff <(ls /tmp) <(ls /var/tmp)` |
| | `cmd > >(other)` | Process substitution as output | `ls | tee >(wc -l) >(sort)` |
| | `exec > >(tee -a script.log)` | Log all script output | `exec > >(tee -a full.log)` |
| **Pipelines** | `cmd1 | cmd2` | Pipe stdout of cmd1 to stdin of cmd2 | `cat file | grep pattern` |
| | `cmd1 |& cmd2` | Pipe stdout and stderr to cmd2 | `make |& tee build.log` |
| | `cat /proc/sys/fs/pipe-max-size` | Kernel pipe buffer size | `cat /proc/sys/fs/pipe-max-size` |
| **Subshells & Jobs** | `(cmd)` | Run cmd in subshell | `(cd /tmp; ls)` |
| | `{ cmd; }` | Run cmd in current shell | `{ cd /tmp; ls; }` |
| | `cmd &` | Background job | `sleep 100 & echo $!` |
| | `jobs` | List background jobs | `jobs -l` |
| | `fg %1` | Bring job 1 to foreground | `fg %1` |
| | `wait $PID` | Wait for process PID | `sleep 10 & wait $!` |
| | `wait` | Wait for all background jobs | `job1 & job2 & wait` |
| **Signals** | `trap 'cmd' SIGINT` | Catch SIGINT (Ctrl+C) | `trap 'echo "Interrupted"' SIGINT` |
| | `trap 'cmd' EXIT` | Execute cmd on script exit | `trap 'rm -f /tmp/lock' EXIT` |
| | `kill -TERM $PID` | Send SIGTERM to process | `kill -TERM $!` |
| | `kill -0 $PID` | Test if process exists | `kill -0 $PID && echo "alive"` |
| | `pkill -TERM -P $$` | Kill all children of current shell | `pkill -TERM -P $$` |
| **Resource Limits** | `ulimit -a` | Display all limits | `ulimit -a` |
| | `ulimit -u 256` | Max 256 processes | `ulimit -u 256` |
| | `ulimit -n 1024` | Max 1024 open files | `ulimit -n 1024` |
| | `ulimit -v 524288` | Max 512 MiB virtual memory (KiB units) | `ulimit -v 524288` |
| | `ulimit -t 10` | Max 10 CPU seconds | `ulimit -t 10` |
| **Debugging** | `bash -x script.sh` | Trace script execution | `bash -x script.sh` |
| | `set -x` / `set +x` | Enable/disable tracing | `set -x; ls; set +x` |
| | `set -v` | Print input lines as read | `set -v` |
| | `strace -f -e trace=open,read,write cmd` | Trace system calls | `strace -f ls /tmp` |
| | `time cmd` | Measure execution time | `time sleep 2` |
| | `/usr/bin/time -v cmd` | Detailed resource usage | `/usr/bin/time -v ls /` |
| **Variables** | `${VAR:-default}` | Use default if VAR unset | `echo ${MISSING:-fallback}` |
| | `${VAR:?error}` | Exit with error if VAR unset | `echo ${REQUIRED:?Missing var}` |
| | `${#VAR}` | Length of VAR | `echo ${#PATH}` |
| | `${VAR#pattern}` | Remove shortest prefix matching pattern | `FILE=/path/to/file.txt; echo ${FILE#*/}` |
| | `${VAR##pattern}` | Remove longest prefix | `echo ${FILE##*/}` (basename) |
| | `${VAR%pattern}` | Remove shortest suffix | `echo ${FILE%.txt}` |
| | `${VAR%%pattern}` | Remove longest suffix | `echo ${FILE%%/*}` |
| **Arrays** | `ARR=(one two three)` | Declare array | `ARR=(a b c)` |
| | `${ARR[0]}` | First element (zero-indexed) | `echo ${ARR[0]}` |
| | `${ARR[@]}` | All elements as separate words | `for i in "${ARR[@]}"; do echo $i; done` |
| | `${#ARR[@]}` | Array length | `echo "Count: ${#ARR[@]}"` |
| | `ARR+=(four)` | Append element | `ARR+=(d)` |

### Verification Formulas

- **Pipeline Throughput**: $T = \frac{D}{t}$ where $D$ is data size (MiB), $t$ is elapsed time (sec)
- **Process Spawn Overhead**: $O = \frac{t_{\text{total}}}{N}$ where $N$ is iteration count
- **File Descriptor Usage**: $U = \frac{F_{\text{open}}}{F_{\text{limit}}} \times 100\%$ where $F_{\text{open}}$ from `ls /proc/$$/fd | wc -l`, $F_{\text{limit}}$ from `ulimit -n`
- **Memory Allocation Rate**: $R = \frac{M_{\text{allocated}}}{t}$ (MiB/sec)
- **Signal Coalescing Factor**: $C = \frac{N_{\text{sent}}}{N_{\text{caught}}}$ where $C > 1$ indicates coalescing

### Common Exit Codes

| **Code** | **Meaning** | **Source** |
|----------|-------------|------------|
| 0 | Success | Command completed normally |
| 1 | General error | Command failed (syntax, file not found, etc.) |
| 2 | Misuse of shell builtin | Incorrect number of arguments to builtin |
| 126 | Command not executable | Permissions issue or file format error |
| 127 | Command not found | PATH lookup failed |
| 128+N | Fatal signal N | Process killed by signal (N = signal number) |
| 130 | SIGINT (Ctrl+C) | 128 + 2 |
| 137 | SIGKILL | 128 + 9 (OOM killer or explicit kill -9) |
| 141 | SIGPIPE | 128 + 13 (broken pipe) |
| 143 | SIGTERM | 128 + 15 (graceful termination request) |

### Performance Debugging Checklist

1. **Excessive subprocess spawning**: Replace external commands with Bash builtins (e.g., `[[ ]]` instead of `test`, `(( ))` instead of `expr`)
2. **Small pipeline blocks**: Increase block size to 64 KiB to match kernel pipe buffer
3. **Untrapped signals**: Add trap handlers for SIGINT, SIGTERM, and EXIT
4. **Non-atomic file updates**: Use `write-to-temp + rename` pattern for critical data
5. **File descriptor leaks**: Close unused descriptors explicitly or use subshells for automatic cleanup
6. **Unbounded loops**: Add iteration limits or resource checks (`ulimit -t`)
7. **Missing `set -euo pipefail`**: Enable strict error handling in all production scripts
8. **Unchecked exit codes**: Test `$?` or `${PIPESTATUS[@]}` after critical commands
9. **Race conditions in parallel jobs**: Use file locks (`flock`) or atomic operations
10. **Missing cleanup traps**: Always trap EXIT to remove temp files and release resources

This laboratory sequence grounds your Bash scripting practice in the actual kernel mechanisms that execute your commands. Every pipeline, redirection, and subprocess invocation translates to specific system calls with measurable performance characteristics and failure modes. By empirically observing these behaviors and inducing controlled faults, you develop the operational intuition required to write robust, debuggable production scripts.
