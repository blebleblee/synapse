# Operational Verification Labs: Core

## Objective & Lab Setup

These labs are designed to transform your theoretical understanding of Bash's internals into hands-on, empirically verified knowledge. You will not merely *run* commands — you will instrument them, stress them, break them deliberately, and measure their behavior against the kernel primitives that underpin them. By the end of this guide, you will have a working mental model of process trees, file descriptor inheritance, signal delivery, job control, and exit code propagation grounded in observable, reproducible evidence.

The lab environment targets a modern Linux system (Ubuntu 22.04 LTS or Debian 12 is recommended) with Bash 5.1+ installed. All exercises are self-contained and require no elevated privileges unless explicitly noted. Before beginning, install the following diagnostic tools and verify their availability.

```bash
# Update package index and install all required tooling
sudo apt-get update && sudo apt-get install -y \
    procps \
    lsof \
    strace \
    ltrace \
    pstree \
    sysstat \
    bc \
    time \
    jq \
    gawk \
    coreutils \
    util-linux \
    inotify-tools
```

```bash
# Verify Bash version — must be 5.1 or higher for all exercises
bash --version

# Verify strace is functional
strace -e trace=none echo "strace operational" 2>/dev/null && echo "strace OK"

# Verify /proc filesystem is mounted (required for process introspection)
mountpoint -q /proc && echo "/proc OK" || echo "/proc NOT MOUNTED"

# Create a persistent lab working directory
export LAB_ROOT="${HOME}/bash_core_labs"
mkdir -p "${LAB_ROOT}"/{ex1,ex2,ex3,artifacts}
cd "${LAB_ROOT}"
echo "Lab root: ${LAB_ROOT}"
```

The `/proc` filesystem is not merely a convenient diagnostic interface — it is the kernel's own structured exposition of its internal state, made readable as a virtual file hierarchy. When you read `/proc/$$/status`, you are reading data that the kernel assembles on demand directly from task structs in kernel memory. This direct coupling between the shell process and its kernel representation is the epistemological foundation of everything that follows.

---

## Exercise 1: Foundational Practical Implementation

### The Process Tree, File Descriptor Table, and Subshell Mechanics

This exercise dissects what actually happens inside the kernel when Bash forks a subshell, executes a pipeline, or runs a command substitution. The goal is to make visible the normally invisible: the process hierarchy, the inherited file descriptor table, and the relationship between the shell's environment and its children's environment.

**Step 1 — Observe the shell's own kernel identity**

```bash
cd "${LAB_ROOT}/ex1"

# Capture a comprehensive snapshot of the current shell's kernel state
{
    echo "=== Shell Process Identity ==="
    echo "Shell PID:       $$"
    echo "Shell PPID:      ${PPID}"
    echo "Shell PGID:      $(ps -o pgid= -p $$)"
    echo "Shell SID:       $(ps -o sid= -p $$)"
    echo "Shell binary:    $(readlink -f /proc/$$/exe)"
    echo ""
    echo "=== Memory Map Summary ==="
    awk '/^VmRSS/ || /^VmSize/ || /^Threads/' /proc/$$/status
    echo ""
    echo "=== Open File Descriptors ==="
    ls -la /proc/$$/fd
    echo ""
    echo "=== Current Limits (ulimit) ==="
    ulimit -a
} | tee "${LAB_ROOT}/artifacts/ex1_shell_identity.txt"
```

```bash
# Examine the shell's full environment as the kernel sees it
# /proc/$$/environ stores the environment with NUL-delimited entries
tr '\0' '\n'  /dev/null' 2>&1 | tee "${LAB_ROOT}/artifacts/ex1_fork_exec_trace.txt"

echo ""
echo "--- Annotated syscall sequence above ---"
echo "Look for: clone() -> execve('/usr/bin/ls') in the child PID"
```

```bash
# Now compare: a builtin requires NO fork/exec — observe the absence
strace -f -e trace=clone,execve,fork,wait4,exit_group \
    bash -c 'pwd' 2>&1 | tee "${LAB_ROOT}/artifacts/ex1_builtin_trace.txt"

echo ""
echo "Builtin syscall count:"
wc -l "${LAB_ROOT}/artifacts/ex1_builtin_trace.txt"
echo "External command syscall count:"
wc -l "${LAB_ROOT}/artifacts/ex1_fork_exec_trace.txt"
```

The difference in line count is not merely quantitative — it represents the entire process lifecycle overhead that the kernel must perform for every external command invocation. This is precisely why experienced shell scripters prefer builtins (`[[ ]]` over `/usr/bin/[`, `printf` over `/usr/bin/printf`) in tight loops.

**Step 3 — Visualize the subshell's isolated environment**

```bash
# Define a variable and function in the parent shell
PARENT_VAR="I exist in the parent"
parent_function() { echo "parent function called"; }
export EXPORTED_VAR="I am exported"

# Demonstrate the three scoping contexts
echo "--- Test 1: Subshell ( ) inherits but cannot modify parent ---"
(
    echo "Inside subshell: PARENT_VAR='${PARENT_VAR}'"
    echo "Inside subshell: EXPORTED_VAR='${EXPORTED_VAR}'"
    PARENT_VAR="modified in subshell"
    echo "Inside subshell after modification: PARENT_VAR='${PARENT_VAR}'"
)
echo "Back in parent: PARENT_VAR='${PARENT_VAR}'"  # unchanged

echo ""
echo "--- Test 2: Child process inherits only exported vars ---"
bash -c 'echo "Child sees PARENT_VAR='"'"'${PARENT_VAR}'"'"'"; echo "Child sees EXPORTED_VAR='"'"'${EXPORTED_VAR}'"'"'"'

echo ""
echo "--- Test 3: Functions are NOT inherited by child processes ---"
bash -c 'type parent_function 2>&1 || echo "parent_function not found in child"'

echo ""
echo "--- Test 4: Exported functions ARE inherited (Bash-specific behavior) ---"
export -f parent_function
bash -c 'parent_function'
```

**Step 4 — Instrument a pipeline and observe the process tree in real time**

```bash
# Write a pipeline where each stage sleeps to give us time to observe
cat > "${LAB_ROOT}/ex1/pipeline_observer.sh" /dev/null || ps --forest -o pid,ppid,pgid,sid,comm -g $$

wait ${PIPELINE_BGPID}
echo ""
echo "Pipeline complete."
SCRIPT
chmod +x "${LAB_ROOT}/ex1/pipeline_observer.sh"
bash "${LAB_ROOT}/ex1/pipeline_observer.sh" 2>&1 | tee "${LAB_ROOT}/artifacts/ex1_pipeline_tree.txt"
```

```bash
# Confirm that all pipeline stages share the same process group (PGID)
# This is how job control works — the terminal sends signals to the entire PGID
bash -c '
    ps -o pid,ppid,pgid,comm -p $$ &&
    sleep 10 | sleep 10 | sleep 10 &
    BGPID=$!
    sleep 0.1
    echo "--- Pipeline process group ---"
    ps -o pid,ppid,pgid,comm $(pgrep -g $(ps -o pgid= -p $BGPID | tr -d " ") 2>/dev/null) 2>/dev/null || \
        ps -o pid,ppid,pgid,comm -C sleep
    kill -- -$(ps -o pgid= -p $BGPID | tr -d " ") 2>/dev/null
    wait $BGPID 2>/dev/null
    echo "Pipeline killed via PGID signal"
'
```

**Step 5 — File descriptor inheritance and redirection mechanics**

```bash
# Demonstrate that child processes inherit the parent's FD table
# and that redirections modify that table BEFORE exec()
cat > "${LAB_ROOT}/ex1/fd_inheritance.sh"  "${LAB_ROOT}/artifacts/ex1_fd5_output.txt"
echo "This line goes to FD 5" >&5
ls -la /proc/$$/fd | grep "fd/5"

echo ""
echo "=== Child inherits FD 5 ==="
bash -c 'ls -la /proc/$$/fd | grep "fd/5" && echo "Child has FD 5" >&5'
cat "${LAB_ROOT}/artifacts/ex1_fd5_output.txt"

echo ""
echo "=== Closing FD 5 ==="
exec 5>&-
ls -la /proc/$$/fd | grep "fd/5" 2>/dev/null || echo "FD 5 is now closed"

echo ""
echo "=== Here-document FD mechanics (traced) ==="
# A here-doc creates a temporary file or pipe — strace reveals which
strace -e trace=open,openat,pipe2,read,write,unlink -o /tmp/heredoc_trace.txt \
    bash -c 'cat &1 | head -1

# Establish the minimum measurable overhead — timing a no-op
for i in 1 2 3 4 5; do
    /usr/bin/time -f "wall=%e user=%U sys=%S" bash -c ':' 2>&1
done
```

```bash
# Benchmark: external command vs arithmetic builtin in a tight loop
# This demonstrates the cumulative fork/exec cost at scale
ITERATIONS=1000

echo "=== Benchmark: External /usr/bin/expr (fork+exec per call) ==="
/usr/bin/time -f "wall=%e user=%U sys=%S maxrss=%M KB" \
    bash -c "
        x=0
        for i in \$(seq 1 ${ITERATIONS}); do
            x=\$(/usr/bin/expr \$x + 1)
        done
        echo \"Final x=\$x\"
    " 2>&1

echo ""
echo "=== Benchmark: Bash arithmetic builtin (no fork) ==="
/usr/bin/time -f "wall=%e user=%U sys=%S maxrss=%M KB" \
    bash -c "
        x=0
        for ((i=0; i&1
```

```bash
# Extend the analysis — log results across multiple iteration counts
# to generate data suitable for plotting

cat > "${LAB_ROOT}/ex2/benchmark_sweep.sh"  "${RESULTS}"

for ITERS in 10 50 100 250 500 750 1000; do
    for METHOD in external builtin; do
        if [[ "${METHOD}" == "external" ]]; then
            CMD="x=0; for i in \$(seq 1 ${ITERS}); do x=\$(/usr/bin/expr \$x + 1); done"
        else
            CMD="x=0; for ((i=0; i&1 | tail -1 )
            W=$(echo "${READ}" | awk '{print $1}')
            U=$(echo "${READ}" | awk '{print $2}')
            S=$(echo "${READ}" | awk '{print $3}')
            WALL_SUM=$(echo "${WALL_SUM} + ${W}" | bc -l)
            USER_SUM=$(echo "${USER_SUM} + ${U}" | bc -l)
            SYS_SUM="${S}"  # sys time is dominated by fork count
        done

        WALL_AVG=$(echo "scale=4; ${WALL_SUM} / 3" | bc -l)
        USER_AVG=$(echo "scale=4; ${USER_SUM} / 3" | bc -l)

        echo "${ITERS},${METHOD},${WALL_AVG},${USER_AVG},${SYS_SUM}" | tee -a "${RESULTS}"
    done
done

echo ""
echo "=== Benchmark Results CSV ==="
cat "${RESULTS}"
SCRIPT
chmod +x "${LAB_ROOT}/ex2/benchmark_sweep.sh"
bash "${LAB_ROOT}/ex2/benchmark_sweep.sh"
```

```bash
# Generate a simple ASCII plot from the CSV using awk
awk -F',' '
NR==1 { next }
$2=="external" { ext[$1]=$3 }
$2=="builtin"  { blt[$1]=$3 }
END {
    printf "%-12s %-12s %-12s %-10s\n", "Iterations", "External(s)", "Builtin(s)", "Speedup"
    printf "%-12s %-12s %-12s %-10s\n", "----------", "-----------", "---------", "-------"
    for (k in ext) {
        speedup = (blt[k] > 0) ? ext[k]/blt[k] : 0
        printf "%-12s %-12.4f %-12.4f %-10.1fx\n", k, ext[k], blt[k], speedup
    }
}' "${LAB_ROOT}/artifacts/ex2_benchmark_results.csv" | sort -k1 -n
```

**Step 2 — IFS tokenization parameter sweep**

The Internal Field Separator is one of the most consequential and misunderstood variables in Bash. Its behavior with leading/trailing whitespace differs categorically from its behavior with non-whitespace characters, and word splitting on unquoted variables follows rules that are non-obvious without direct experimentation.

```bash
# Establish the canonical IFS whitespace-collapse behavior
echo "=== Default IFS (space, tab, newline) — whitespace is collapsed ==="
INPUT="  hello   world   foo  "
IFS_DEFAULT=( ${INPUT} )
echo "Array elements: ${#IFS_DEFAULT[@]}"
printf '  [%s]\n' "${IFS_DEFAULT[@]}"

echo ""
echo "=== IFS=: — colon-delimited, leading/trailing colons produce empty fields ==="
IFS=':'
PATH_LIKE=":/usr/bin:/usr/local/bin:/opt/bin:"
read -ra PARTS  "${LAB_ROOT}/ex2/ifs_matrix.sh"  "${LAB_ROOT}/ex2/glob_timing.sh"  "${LAB_ROOT}/artifacts/ex2_glob_timing.csv"

for COUNT in 100 500 1000 5000 10000; do
    DIR="${GLOB_DIR}/${COUNT}"

    # Time the glob expansion itself using SECONDS and $EPOCHREALTIME
    START="${EPOCHREALTIME}"
    files=( "${DIR}"/*.txt )
    END="${EPOCHREALTIME}"

    ELAPSED=$(echo "${END} - ${START}" | bc -l)
    MATCHED="${#files[@]}"

    printf "%-10s | elapsed=%-12s | matched=%d\n" "${COUNT}" "${ELAPSED}" "${MATCHED}"
    echo "${COUNT},${ELAPSED},${MATCHED}" >> "${LAB_ROOT}/artifacts/ex2_glob_timing.csv"
done

echo ""
echo "=== Raw timing data ==="
cat "${LAB_ROOT}/artifacts/ex2_glob_timing.csv"
SCRIPT
chmod +x "${LAB_ROOT}/ex2/glob_timing.sh"
bash "${LAB_ROOT}/ex2/glob_timing.sh"
```

```bash
# Compare glob vs find vs ls for file enumeration — practical tradeoff analysis
GLOB_DIR="${LAB_ROOT}/ex2/glob_test/5000"

echo "=== Method Comparison for 5000 files ==="

echo "--- Glob expansion (shell, no fork) ---"
/usr/bin/time -f "wall=%e user=%U sys=%S" bash -c \
    'files=( '"${GLOB_DIR}"'/*.txt ); echo "${#files[@]} files"' 2>&1

echo "--- find (fork+exec, single getdents pass) ---"
/usr/bin/time -f "wall=%e user=%U sys=%S" \
    find "${GLOB_DIR}" -maxdepth 1 -name '*.txt' | wc -l 2>&1

echo "--- ls (fork+exec, sorted output) ---"
/usr/bin/time -f "wall=%e user=%U sys=%S" \
    bash -c "ls ${GLOB_DIR}/*.txt | wc -l" 2>&1
```

---

## Exercise 3: Fault Injection & Stress Testing

### Signal Delivery, Exit Code Boundaries, and Shell Error Handling Under Failure

This exercise is designed to push the shell's error handling mechanisms to their boundary conditions. You will inject signals at precise points in script execution, verify that `trap` handlers fire correctly, test `set -euo pipefail` semantics under adversarial conditions, and confirm that the exit status encoding scheme (`128+N`) is internally consistent with what the kernel reports.

**Step 1 — Signal delivery and trap handler verification**

```bash
cd "${LAB_ROOT}/ex3"

# Demonstrate that trap handlers run in the shell's current environment
# and that EXIT traps run even on abnormal termination paths
cat > "${LAB_ROOT}/ex3/trap_verification.sh"  "${TRAP_LOG}"

log() { echo "[$(date +%T.%N)] $*" | tee -a "${TRAP_LOG}"; }

# Register handlers for every commonly deliverable signal
trap 'log "TRAP: EXIT (status=$?)"'                             EXIT
trap 'log "TRAP: ERR  (status=$? lineno=${LINENO})"'            ERR
trap 'log "TRAP: SIGTERM received"'                             TERM
trap 'log "TRAP: SIGINT received — ignoring for this test"'     INT
trap 'log "TRAP: SIGUSR1 received"'                             USR1
trap 'log "TRAP: SIGUSR2 received"'                             USR2
trap 'log "TRAP: SIGCHLD (child state changed)"'                CHLD

log "Script PID: $$"
log "Sending SIGUSR1 to self"
kill -USR1 $$

log "Sending SIGUSR2 to self"
kill -USR2 $$

log "Starting a background child (will trigger SIGCHLD)"
sleep 0.1 &
wait $!

log "Inducing ERR trap via false"
set +e   # temporarily disable errexit so script continues after false
false
set -e

log "All signal tests complete — EXIT trap will fire now"
SCRIPT
chmod +x "${LAB_ROOT}/ex3/trap_verification.sh"
bash "${LAB_ROOT}/ex3/trap_verification.sh"
echo ""
echo "=== Trap log ==="
cat "${LAB_ROOT}/artifacts/ex3_trap_log.txt"
```

**Step 2 — Exit code encoding and signal death verification**

The kernel encodes a child process's termination status in a 16-bit integer. The low 8 bits encode the signal number if the process was killed by a signal; the high 8 bits encode the exit code if the process called `_exit()`. Bash re-encodes signal-killed exits as `128 + signal_number`. Here you will verify this encoding empirically.

```bash
# Map signal numbers to Bash exit codes
echo "=== Signal Number to Bash Exit Code Mapping ==="
echo "signal_name,signal_num,bash_exit_code,expected_128+N,match" > \
    "${LAB_ROOT}/artifacts/ex3_exit_code_map.csv"

for SIG_INFO in "HUP:1" "INT:2" "QUIT:3" "KILL:9" "TERM:15" "USR1:10" "USR2:12" "PIPE:13"; do
    SIGNAME="${SIG_INFO%%:*}"
    SIGNUM="${SIG_INFO##*:}"
    EXPECTED=$(( 128 + SIGNUM ))

    # Launch a sleep, kill it with the target signal, capture exit code
    bash -c "sleep 60 & PID=\$!; sleep 0.05; kill -${SIGNAME} \$PID; wait \$PID" 2>/dev/null
    ACTUAL_EXIT=$?

    MATCH="YES"
    [[ "${ACTUAL_EXIT}" -ne "${EXPECTED}" ]] && MATCH="NO — got ${ACTUAL_EXIT}"

    printf "SIG%-6s (#%2d) | exit=%-4d | expected=%-4d | %s\n" \
        "${SIGNAME}" "${SIGNUM}" "${ACTUAL_EXIT}" "${EXPECTED}" "${MATCH}"

    echo "SIG${SIGNAME},${SIGNUM},${ACTUAL_EXIT},${EXPECTED},${MATCH}" >> \
        "${LAB_ROOT}/artifacts/ex3_exit_code_map.csv"
done
```

```bash
# Verify the kernel-level wait status encoding using a C helper via bash/proc
# /proc//stat field 52 (exit_signal) is set after process termination
# Instead, we use strace on wait4() to observe the raw wstatus integer

strace -e trace=wait4 bash -c '
    sleep 60 &
    PID=$!
    sleep 0.1
    kill -KILL $PID
    wait $PID
' 2>&1 | grep wait4 | tail -3
# The wstatus value will show: signal bits (low byte) set to 9 for SIGKILL
# e.g., wstatus=[{WIFSIGNALED(s) && WTERMSIG(s) == SIGKILL}]
```

**Step 3 — `set -euo pipefail` fault injection matrix**

The `errexit` (`-e`) option is profoundly misunderstood. It does not simply "exit on error" — it has specific carve-outs for commands in `if` conditions, `while`/`until` test expressions, the left-hand side of `&&` and `||` chains, negated commands (`!`), and the last command in a pipeline unless `pipefail` is also set. This step maps every exception through direct fault injection.

```bash
cat > "${LAB_ROOT}/ex3/errexit_matrix.sh" /dev/null || actual_exit=$?

    if [[ "${actual_exit}" -eq "${expected_exit}" ]]; then
        printf "PASS | %-55s | exit=%d\n" "${label}" "${actual_exit}"
        (( PASS++ )) || true
    else
        printf "FAIL | %-55s | expected=%d got=%d\n" "${label}" "${expected_exit}" "${actual_exit}"
        (( FAIL++ )) || true
    fi
}

echo "=== set -e exception carve-outs ==="
echo ""

# Case 1: false in if-condition — errexit does NOT fire
check "false in if-condition (should exit 0)" 0 \
    "bash -c 'set -e; if false; then echo yes; fi; echo survived'"

# Case 2: false in while-condition — errexit does NOT fire
check "false in while-condition (should exit 0)" 0 \
    "bash -c 'set -e; while false; do echo loop; done; echo survived'"

# Case 3: false after || — errexit does NOT fire
check "false after || (should exit 0)" 0 \
    "bash -c 'set -e; false || true; echo survived'"

# Case 4: false after && — errexit DOES fire for the right-hand side failure
check "false in && chain RHS (should exit 1)" 1 \
    "bash -c 'set -e; true && false; echo survived'"

# Case 5: negated false — errexit does NOT fire
check "negated false (should exit 0)" 0 \
    "bash -c 'set -e; ! false; echo survived'"

# Case 6: pipeline without pipefail — only last exit matters
check "pipeline no pipefail: false|true (should exit 0)" 0 \
    "bash -c 'set -e; false | true; echo survived'"

# Case 7: pipeline WITH pipefail — first failure propagates
check "pipeline with pipefail: false|true (should exit 1)" 1 \
    "bash -c 'set -eo pipefail; false | true; echo survived'"

# Case 8: unset variable without -u
check "unset var without -u (should exit 0)" 0 \
    "bash -c 'set -e; echo \${DEFINITELY_UNSET_VAR}; echo survived'"

# Case 9: unset variable WITH -u
check "unset var with -u (should exit 1)" 1 \
    "bash -c 'set -eu; echo \${DEFINITELY_UNSET_VAR}; echo survived'"

# Case 10: command substitution failure without -e propagation
check "cmd sub failure propagates with -e" 1 \
    "bash -c 'set -e; x=\$(false); echo survived'"

echo ""
printf "Results: %d PASS, %d FAIL\n" "${PASS}" "${FAIL}"
SCRIPT
chmod +x "${LAB_ROOT}/ex3/errexit_matrix.sh"
bash "${LAB_ROOT}/ex3/errexit_matrix.sh" | tee "${LAB_ROOT}/artifacts/ex3_errexit_matrix.txt"
```

**Step 4 — Race condition and signal delivery timing stress test**

```bash
cat > "${LAB_ROOT}/ex3/signal_race_stress.sh"  "${RACE_LOG}"

SUCCESSES=0
FAILURES=0
UNEXPECTED=0

echo "Running ${STRESS_ITERS} iterations of signal-during-sleep race..."

for ((i=1; i "${TMPF}"; exit 0' TERM INT EXIT
            echo "RUNNING" > "${TMPF}"
            sleep 10 &
            BGPID=$!
            # Simulate work that gets interrupted
            kill -TERM $BGPID 2>/dev/null
            wait $BGPID 2>/dev/null
            echo "COMPLETED" > "${TMPF}"
INNER
        cat "${TMPF}"
    )

    case "${result}" in
        "COMPLETED") (( SUCCESSES++ )) || true ;;
        "CLEANED")   (( FAILURES++ ))  || true ;;   # signal interrupted before completion
        *)           (( UNEXPECTED++ )) || true; echo "iter ${i}: unexpected='${result}'" >> "${RACE_LOG}" ;;
    esac

    rm -f "${TMPFILE}"
done

echo "Results over ${STRESS_ITERS} iterations:"
echo "  Normal completions:  ${SUCCESSES}"
echo "  Signal interrupts:   ${FAILURES}"
echo "  Unexpected states:   ${UNEXPECTED}"

(( UNEXPECTED == 0 )) && echo "PASS: No unexpected states detected" || \
    echo "FAIL: Unexpected states found — see ${RACE_LOG}"
SCRIPT
chmod +x "${LAB_ROOT}/ex3/signal_race_stress.sh"
bash "${LAB_ROOT}/ex3/signal_race_stress.sh"
```

**Step 5 — Verify cleanup under all abnormal termination paths**

```bash
cat > "${LAB_ROOT}/ex3/cleanup_audit.sh"  "${AUDIT_LOG}"

run_and_check() {
    local scenario="$1"
    local script="$2"
    local sentinel="${LAB_ROOT}/artifacts/sentinel_${RANDOM}.flag"

    rm -f "${sentinel}"

    eval "${script}" "\"${sentinel}\"" 2>/dev/null || true

    if [[ -f "${sentinel}" ]]; then
        printf "PASS | %-40s | sentinel created\n" "${scenario}" | tee -a "${AUDIT_LOG}"
    else
        printf "FAIL | %-40s | sentinel NOT created\n" "${scenario}" | tee -a "${AUDIT_LOG}"
    fi
    rm -f "${sentinel}"
}

echo "=== Cleanup Sentinel Audit ==="
echo ""

# Scenario A: Normal exit
run_and_check "normal exit" \
    "bash -c 'trap \"touch \$1\" EXIT; exit 0'"

# Scenario B: Errexit triggers
run_and_check "errexit (set -e + false)" \
    "bash -c 'trap \"touch \$1\" EXIT; set -e; false'"

# Scenario C: SIGTERM
run_and_check "SIGTERM delivery" \
    "bash -c 'trap \"touch \$1\" EXIT; sleep 10 & PID=\$!; kill -TERM \$\$' "

# Scenario D: Explicit exit with non-zero code
run_and_check "exit 42" \
    "bash -c 'trap \"touch \$1\" EXIT; exit 42'"

# Scenario E: Unbound variable with set -u
run_and_check "unbound variable (set -u)" \
    "bash -c 'trap \"touch \$1\" EXIT; set -eu; echo \${UNDEFINED_XYZ123}'"

echo ""
echo "Full audit log: ${AUDIT_LOG}"
SCRIPT
chmod +x "${LAB_ROOT}/ex3/cleanup_audit.sh"
bash "${LAB_ROOT}/ex3/cleanup_audit.sh"
```

---

## Practical Cheat Sheet & Quick Reference

### Process & Shell Introspection

| Command / Expression | What It Reveals |
|---|---|
| `echo $$` | PID of the current shell |
| `echo $PPID` | PID of the parent process |
| `echo $BASHPID` | PID of the **current** subshell (differs from `$$` inside subshells) |
| `echo $BASH_SUBSHELL` | Subshell nesting depth (0 = top-level) |
| `ps -o pid,ppid,pgid,sid,comm -p $$` | Full process group/session context |
| `pstree -p $$` | ASCII process tree rooted at current shell |
| `cat /proc/$$/status` | Full kernel task struct fields (VmRSS, Threads, State) |
| `ls -la /proc/$$/fd` | Current open file descriptor table |
| `tr '\0' '\n' ` overwriting existing files |
| `set -b` | `notify` | Report background job status immediately |

### Trap Signal Reference

| Pseudo-signal / Signal | Fires When |
|---|---|
| `EXIT` | Shell exits for any reason (always fires) |
| `ERR` | A command returns non-zero (requires `set -e` context awareness) |
| `DEBUG` | Before each command (used by debuggers like `bashdb`) |
| `RETURN` | When a function or sourced script returns |
| `SIGINT` (2) | Ctrl+C received |
| `SIGTERM` (15) | `kill` default signal |
| `SIGCHLD` | Any child process changes state |
| `SIGHUP` (1) | Terminal hangup or session leader exit |
| `SIGPIPE` (13) | Write to pipe with no readers |

### IFS Tokenization Rules

| Condition | Behavior |
|---|---|
| `IFS` is default (`$' \t\n'`) | Leading/trailing whitespace stripped; runs of whitespace = single split |
| `IFS` is non-whitespace char (e.g., `:`) | Each occurrence creates a field split; runs do NOT collapse (double `:` = empty field) |
| `IFS=''` (empty string) | No word splitting occurs regardless of variable content |
| `IFS` unset | Behaves identically to default whitespace IFS |
| Mixed `IFS` (e.g., `: `) | Whitespace chars still collapse when adjacent to delimiter chars |

### File Descriptor Operations

| Syntax | Operation |
|---|---|
| `cmd > file` | Redirect stdout to file (truncate) |
| `cmd >> file` | Redirect stdout to file (append) |
| `cmd 2> file` | Redirect stderr to file |
| `cmd 2>&1` | Redirect stderr to current stdout destination |
| `cmd &> file` | Redirect both stdout and stderr to file |
| `cmd 1>&2` | Redirect stdout to stderr |
| `exec N> file` | Open file descriptor N for writing (persistent) |
| `exec N&-` | Close file descriptor N |
| `cmd {varname}> file` | Assign next available FD to variable (Bash 4.1+) |
| `cmd  >(consumer)` | Process substitution: consumer receives cmd's stdout |

### Performance Diagnostic Commands

| Command | Purpose |
|---|---|
| `/usr/bin/time -f "%e %U %S" cmd` | Wall, user, and system CPU time for `cmd` |
| `strace -c cmd` | Syscall count and time summary for `cmd` |
| `strace -f -e trace=clone,execve cmd` | Trace fork/exec calls including children |
| `lsof -p $$` | All open files and sockets for current shell |
| `cat /proc/$$/maps` | Virtual memory map (segments, libraries, stack, heap) |
| `awk '/VmPeak|VmRSS|VmStk/' /proc/$$/status` | Peak, resident, and stack memory |
| `bash -c 'time for ...'` | Bash builtin timer (less precise than `/usr/bin/time`) |
| `TIMEFORMAT='%R %U %S' ; time { ... }` | Custom format for Bash's builtin `time` |
