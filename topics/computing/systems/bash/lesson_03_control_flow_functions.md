# Lesson 3: Control Flow Structures

## 1. First-Principles Intuition & Invariants

Control flow in Bash emerges from a deceptively simple foundation: every command executed by the shell yields an integer exit status, and this status becomes the sole currency through which programs communicate success, failure, and semantic meaning to their callers. Unlike high-level languages where control flow operates on boolean predicates or rich exception hierarchies, Bash reduces all decision-making to a single question: did the last command exit successfully? This architectural constraint—inherited from the original Bourne shell and preserved for POSIX compatibility—shapes every conditional, loop, and function in the language.

The exit status convention establishes a powerful invariant: zero means success, and any non-zero value signals failure or abnormal termination. This inverted logic, where truth is numerically zero and falsehood is any positive integer, stems from the kernel's process exit semantics. When a process terminates, the kernel stores its 8-bit exit code in the low byte of the wait status word, and by convention, zero indicates clean termination while non-zero values encode error categories. The shell exposes this raw kernel primitive directly, making every command—from simple utilities like `ls` to complex pipelines—a potential predicate in a conditional expression.

This design yields remarkable composability. Because commands, functions, and even compound statements all produce exit statuses through the same mechanism, they can be uniformly tested in conditional contexts. The `if` statement does not evaluate a boolean expression in the traditional sense; rather, it executes a command list and inspects the exit status of the final command. This execution-as-predicate model means that arbitrary programs become first-class conditionals without requiring special syntax or wrapper functions. Testing whether a file exists becomes `if [ -f /etc/passwd ]`, where the `[` command (an alias for `test`) exits with status 0 if the file exists and 1 otherwise. Testing whether a remote host responds becomes `if ping -c 1 10.0.0.1 &>/dev/null`, where the `ping` utility's exit status directly encodes reachability.

The shell's control flow constructs preserve a critical mathematical property: they are compositional and exhibit predictable short-circuit semantics. The logical operators `&&` (AND) and `||` (OR) chain commands with eager left-to-right evaluation, halting execution the moment the truth value is determined. The expression `command1 && command2` executes `command2` only if `command1` exits zero, while `command1 || command2` executes `command2` only if `command1` exits non-zero. These operators obey De Morgan's laws and form a complete Boolean algebra over command exit statuses, enabling engineers to construct complex decision trees from simple building blocks without nested `if` statements.

Loops in Bash operate on a different primitive: the stream. While conditionals test discrete exit statuses, iterative constructs consume sequences—lines of text from files, elements from arrays, ranges of integers, or arbitrary command outputs. The `while` loop repeatedly executes a command list as long as a condition command exits successfully, while `for` loops bind a variable to successive elements of a word list and execute the loop body for each binding. This stream-oriented iteration model reflects Unix's pipe-centric architecture, where programs process data as flows rather than in-memory collections. A `while read` loop, for instance, consumes standard input line-by-line, binding each line to a variable and executing the loop body, until the input stream reaches EOF and the `read` command exits with status 1.

Functions in Bash inherit the same exit-status protocol, but introduce lexical scoping and a rudimentary stack discipline. When a function executes, the shell pushes a new variable scope onto an implicit stack, and variables declared with `local` exist only within that scope, shadowing any global variables of the same name. Functions communicate results through two channels: their exit status, set explicitly via `return` or implicitly via the last command executed, and their standard output, which callers can capture via command substitution. This dual-channel model separates control flow (success/failure) from data flow (produced output), a distinction that proves essential when composing functions into pipelines or using them as predicates in conditionals.

The shell's exception-handling mechanism, embodied in the `trap` builtin, operates at a lower level than structured exception handlers in languages like Python or Java. Traps bind shell code to signals—asynchronous notifications delivered by the kernel—or to special pseudo-signals like `EXIT`, `ERR`, and `DEBUG`. When a signal arrives or a triggering condition occurs, the shell suspends its current execution context, runs the trap handler, and resumes (or terminates) based on the handler's behavior. This signal-driven model reflects the Unix process model, where signals are the kernel's mechanism for delivering asynchronous events like user interrupts (SIGINT), termination requests (SIGTERM), or timer expirations (SIGALRM). Trap handlers enable resource cleanup, graceful shutdown protocols, and defensive error handling in long-running scripts.

Understanding Bash control flow requires internalizing a fundamental cognitive inversion: the shell does not evaluate expressions to produce boolean values that control execution. Instead, it executes commands and uses their exit statuses as the sole decision-making primitive. This execution-centric model, combined with the shell's fork-exec process model and its text-stream orientation, creates a control flow paradigm that is simultaneously more primitive and more composable than conventional imperative languages. Mastering this paradigm means thinking in terms of command pipelines, exit codes, and signal-driven state machines rather than boolean logic and exception hierarchies.

## 2. Core Architecture & Mechanics

The shell's conditional execution machinery operates through a three-layer evaluation model: syntactic parsing of control structures, semantic evaluation of test expressions, and dynamic dispatch based on exit statuses. At the syntactic level, the shell recognizes control keywords like `if`, `while`, `case`, and `for` as compound commands, parsing them into abstract syntax tree nodes that encapsulate their condition clauses, body statements, and continuation logic. These compound commands are first-class syntactic entities, meaning they can be nested arbitrarily, used as function bodies, or placed in pipelines.

The `if` statement exemplifies the execution-as-predicate model. Its syntax consists of four clauses: the condition command list (`if`), the then branch, optional `elif` clauses (each with its own condition), and an optional `else` branch. When the shell encounters an `if` statement, it evaluates the condition command list—which can be a single command, a pipeline, or a compound statement—and captures the exit status of the final command in that list. If the status is zero, the shell executes the then branch. Otherwise, it evaluates each `elif` condition in sequence, executing the first branch whose condition succeeds, or falling through to the `else` branch if no condition matches. This sequential evaluation ensures deterministic short-circuiting: once a condition succeeds, no subsequent conditions are tested.

```bash
# Condition command list can be arbitrary complexity
if command1 | command2 && command3; then
    # Executes if command3 exits 0
    action1
elif [ -f "$CONFIG_FILE" ] && validate_config "$CONFIG_FILE"; then
    # Executes if file exists AND validate_config exits 0
    action2
else
    # Executes if all prior conditions failed
    action3
fi
```

The test command, invoked as `[` or `test`, provides file attribute testing, string comparison, and integer arithmetic comparisons, but it is merely a utility program that exits 0 or 1 based on its operands. The shell's extended test construct `[[ ... ]]`, by contrast, is a shell keyword that implements the same semantics internally without forking a subprocess. This distinction has performance implications: the `[[` construct avoids a fork-exec cycle, evaluates operands without word splitting or globbing, and supports pattern matching on the right-hand side of `==` and `!=` operators. For file tests, string comparisons, and pattern matching, `[[` is strictly superior, but it sacrifices POSIX portability since it is a Bash extension.

```bash
# Legacy test command (forks subprocess)
if [ -f "$file" ]; then
    process_file "$file"
fi

# Bash extended test (no fork, safer quoting)
if [[ -f $file ]]; then
    process_file "$file"
fi

# Pattern matching only available in [[
if [[ $hostname == web-*.example.com ]]; then
    configure_webserver
fi
```

The file test operators expose kernel-level metadata through stat system calls. Testing `-f` checks the file type field in the inode's `st_mode` bitfield to determine if the target is a regular file, while `-d` tests for directories, `-L` for symbolic links, and `-e` for any existing filesystem object. The permission tests `-r`, `-w`, and `-x` evaluate effective permissions based on the process's UID, GID, and supplementary group list, consulting the file's mode bits and any filesystem ACLs. Integer comparisons like `-eq`, `-ne`, `-lt`, `-le`, `-gt`, and `-ge` perform arithmetic evaluation on their operands before comparing, meaning they interpret strings as integers or exit with an error if the operands are non-numeric.

The `case` statement implements pattern-based dispatch, analogous to a switch statement but operating on shell glob patterns rather than integer constants. The shell evaluates the word operand, then sequentially matches it against each pattern (which may contain wildcards, character classes, or alternation operators). Upon finding the first match, it executes the corresponding command list and exits the `case` statement—no fallthrough occurs unless explicitly coded with loops or conditionals. This pattern-driven dispatch proves invaluable for parsing command-line arguments, routing based on filename extensions, or implementing finite-state machines.

```bash
case "$1" in
    start|run)
        # Alternation: matches either "start" or "run"
        start_service
        ;;
    stop|halt|shutdown)
        stop_service
        ;;
    status)
        check_service_status
        ;;
    --config=*)
        # Parameter extraction via pattern matching
        CONFIG_FILE="${1#--config=}"
        load_config "$CONFIG_FILE"
        ;;
    *)
        # Default case, catches all unmatched patterns
        echo "Usage: $0 {start|stop|status|--config=FILE}" >&2
        exit 1
        ;;
esac
```

Loop constructs provide three core iteration primitives, each suited to different data sources. The `for` loop binds a variable to successive elements of a word list, where the word list can be an explicit sequence, a brace expansion, a glob pattern, or an array expansion. The shell performs word splitting on the list (unless it is an array expansion), then iterates over each resulting word, binding it to the loop variable and executing the body. This model integrates naturally with filename globbing: `for file in *.txt` iterates over all `.txt` files in the current directory, with the glob expanded before the loop executes.

```bash
# Iterating over a static word list
for env in dev staging prod; do
    deploy_to_environment "$env"
done

# Iterating over command output (word splitting applies)
for pid in $(pgrep nginx); do
    analyze_process "$pid"
done

# Iterating over array elements (no word splitting)
servers=(web1 web2 db1 db2)
for host in "${servers[@]}"; do
    ssh "$host" 'systemctl status nginx'
done

# C-style arithmetic for loop
for ((i = 0; i &2
        exit 1
    fi
    echo "Attempt $attempt failed, retrying in ${delay}s..."
    sleep "$delay"
    ((delay *= 2))
done
```

The `until` loop inverts `while` semantics, executing the body repeatedly as long as the condition command exits non-zero. This construct is less common but useful for implementing wait-until-ready patterns, such as blocking until a file appears or a network port becomes available. The loop `until [ -f /var/run/ready.flag ]; do sleep 1; done` polls for the existence of a flag file, pausing one second between checks.

Loop control flow can be altered mid-iteration via `break` and `continue`. The `break` statement exits the innermost enclosing loop immediately, skipping all remaining iterations, while `continue` aborts the current iteration and advances to the next. Both accept an optional integer argument specifying how many enclosing loops to break or continue, enabling early exit from nested loops. The statement `break 2` exits both the innermost and its enclosing loop, useful when an inner condition invalidates the outer iteration context.

Functions encapsulate reusable command sequences and introduce lexical scoping discipline. The shell provides two syntactic forms for function definition: the traditional form `function name { ... }` and the POSIX-compatible form `name() { ... }`. Both forms are semantically identical in Bash, creating a named compound command that can be invoked like any other command. Functions receive positional parameters through the special variables `$1`, `$2`, etc., mirroring the script's own argument protocol. The special variables `$@` and `$*` expand to all positional parameters, with `"$@"` preserving word boundaries while `"$*"` joins arguments into a single word.

```bash
# POSIX-compatible function definition
deploy() {
    local environment="$1"
    local version="$2"
    
    if [[ -z $environment || -z $version ]]; then
        echo "Usage: deploy ENVIRONMENT VERSION" >&2
        return 1
    fi
    
    echo "Deploying version $version to $environment"
    # Deployment logic here
}

# Bash-specific function definition (identical behavior)
function validate_config {
    local config_file="$1"
    
    if [[ ! -f $config_file ]]; then
        echo "Config file not found: $config_file" >&2
        return 2
    fi
    
    if ! jq empty "$config_file" 2>/dev/null; then
        echo "Invalid JSON in config file: $config_file" >&2
        return 3
    fi
    
    return 0
}
```

Variable scope within functions follows a stack-based discipline. By default, variables assigned in functions are global, persisting after the function returns and potentially shadowing or modifying caller variables. The `local` keyword restricts a variable's lifetime to the function's execution, automatically discarding it upon return. Local variables shadow global variables of the same name, but the global remains unmodified. This scoping mechanism enables safe encapsulation: functions can use temporary variables without polluting the global namespace or interfering with caller state.

```bash
COUNTER=0  # Global variable

increment_counter() {
    local delta="${1:-1}"
    ((COUNTER += delta))
    echo "Counter incremented by $delta, now $COUNTER"
}

compute_checksum() {
    local file="$1"
    local checksum  # Declare before assignment to trap errors
    
    checksum=$(sha256sum "$file" | awk '{print $1}')
    echo "$checksum"
}

# After calling increment_counter, COUNTER is modified globally
# After calling compute_checksum, checksum variable does not persist
```

Functions communicate results through two orthogonal channels. The primary channel is the exit status, set via the `return` builtin or implicitly by the last command executed. The exit status signals success or failure and integrates seamlessly with conditionals: `if validate_config "$file"; then` executes the then branch only if `validate_config` returns 0. The secondary channel is standard output, captured via command substitution. A function like `get_hostname() { hostname; }` produces its result by printing to stdout, and callers capture it with `host=$(get_hostname)`. This dual-channel model separates control flow (did the operation succeed?) from data flow (what value was produced?), a critical distinction for composable shell functions.

The shell's exception-handling primitive, the `trap` builtin, binds shell code to signals or pseudo-signals. The syntax `trap 'command_list' SIGNAL...` registers a handler that executes when the specified signals are delivered. Signals like SIGINT (interrupt, typically Ctrl+C), SIGTERM (termination request), and SIGHUP (hangup) are delivered asynchronously by the kernel, while pseudo-signals like `EXIT`, `ERR`, and `DEBUG` are shell-specific constructs triggered by process termination, command failure, and command execution respectively. Trap handlers enable resource cleanup (closing file descriptors, deleting temporary files), graceful shutdown (flushing buffers, saving state), and error recovery (logging failures, retrying operations).

```bash
# Cleanup trap ensures temporary files are deleted on script exit
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Error trap logs failures and exits
trap 'echo "Command failed at line $LINENO" >&2; exit 1' ERR

# Signal trap handles graceful shutdown
SHUTTING_DOWN=0
trap 'SHUTTING_DOWN=1; echo "Shutdown signal received"' SIGTERM SIGINT

while [[ $SHUTTING_DOWN -eq 0 ]]; do
    process_next_job
done

echo "Shutdown complete"
```

The `EXIT` trap executes when the shell process terminates, regardless of exit status or cause. This trap provides a guaranteed cleanup hook, analogous to a finally block in exception-handling languages. The `ERR` trap executes when a command exits with non-zero status, but only if the shell is in error-checking mode (`set -e`). The `DEBUG` trap executes before every simple command, enabling tracing and debugging instrumentation. Traps can be cleared with `trap - SIGNAL`, restoring default signal handling, or queried with `trap -p SIGNAL`, printing the current handler.

The interaction between traps and subshells requires careful attention. When a subshell is created (via command substitution, pipeline, or explicit parentheses), it inherits the parent's trap handlers but operates in an independent execution context. Modifications to traps in the subshell do not affect the parent, and the subshell's `EXIT` trap fires when the subshell terminates, not when the parent terminates. This isolation ensures that pipeline stages and background jobs can install their own cleanup handlers without interfering with the main script's error handling.

## 3. High-Performance Optimization & Failure Modes

Control flow performance in Bash degrades rapidly with subprocess creation, dynamic string evaluation, and inefficient loop patterns. Every invocation of an external command incurs a fork-exec cycle, consuming milliseconds of latency and requiring kernel-level process creation, memory mapping, and ELF loader invocation. Scripts that invoke commands in tight loops can spend orders of magnitude more time in kernel process management than in productive computation. The canonical antipattern is invoking `grep` or `sed` once per loop iteration when a single invocation outside the loop would suffice.

```bash
# Antipattern: subprocess per iteration (extremely slow for large arrays)
for file in "${files[@]}"; do
    if grep -q "pattern" "$file"; then
        matching_files+=("$file")
    fi
done

# Optimized: single subprocess with all files
matching_files=($(grep -l "pattern" "${files[@]}"))

# Even better: use shell built-in pattern matching when possible
for file in "${files[@]}"; do
    if [[ $(&2
    exit 1
fi
```

The `set -u` option (`nounset`) causes the shell to exit when referencing undefined variables, catching typos and logic errors that would otherwise silently evaluate to empty strings. Combining `set -e`, `set -u`, and `set -o pipefail` (which propagates pipeline component failures) creates a strict error-checking mode suitable for production scripts, but requires careful handling of intentional failures and optional variables. The idiom `${VAR:-default}` provides default values for potentially undefined variables, satisfying `set -u` while maintaining flexibility.

```bash
#!/bin/bash
set -euo pipefail

# Safe handling of optional variables
CONFIG_FILE="${CONFIG_FILE:-/etc/default/config.conf}"

# Intentional failure handling without triggering errexit
if some_command_that_might_fail; then
    echo "Command succeeded"
else
    echo "Command failed (expected)" >&2
fi

# Pipeline failure propagation
cat /nonexistent/file | sort  # Exits due to pipefail, despite sort success
```

Trap handlers must be idempotent and reentrant, as signals can be delivered at arbitrary execution points, including while the trap handler itself is running. A non-reentrant trap handler that modifies global state or invokes non-atomic operations risks corrupting data structures or deadlocking. The standard defensive pattern is to set an atomic flag in the signal handler and check it periodically in the main loop, deferring complex cleanup to the main execution context where it can be performed safely.

```bash
INTERRUPTED=0

# Atomic flag set, no complex operations
trap 'INTERRUPTED=1' SIGTERM SIGINT

# Main loop checks flag and performs cleanup in main context
while [[ $INTERRUPTED -eq 0 ]]; do
    process_job
    
    # Periodic flag check allows controlled shutdown
    if [[ $INTERRUPTED -eq 1 ]]; then
        echo "Interrupt detected, cleaning up..."
        cleanup_jobs
        break
    fi
done
```

Exit trap execution order matters when multiple resources require cleanup. The shell executes the most recently installed EXIT trap, then earlier traps in reverse order of installation. This LIFO (last-in, first-out) semantics mirrors typical resource acquisition patterns: resources acquired later should be released first. A function that opens a file descriptor should install its cleanup trap after the caller's trap, ensuring the descriptor is closed before the caller performs its own cleanup.

Function recursion in Bash is legal but hazardous due to the lack of tail call optimization and limited stack depth. Each recursive call allocates a new variable scope and pushes a stack frame, and deep recursion (thousands of levels) can exhaust the shell's internal stack, causing a crash. Iterative solutions using loops are always preferable, and when recursion is necessary (tree traversal, divide-and-conquer algorithms), depth should be validated or bounded. The shell provides no mechanism to detect or recover from stack exhaustion.

The performance characteristics of case pattern matching depend on the pattern complexity and the position of the matching clause. The shell evaluates case patterns sequentially from top to bottom, executing the first match and exiting. Frequently matched patterns should appear early in the case statement to minimize average evaluation cost. Complex patterns with multiple wildcards or character classes require more evaluation time than simple literal matches or single-wildcard patterns. For dispatching on a large set of simple strings, a case statement outperforms a chain of string comparisons, but for truly large dispatch tables (hundreds or thousands of keys), an associative array lookup is more efficient.

```bash
# Optimized: frequent cases first, simple patterns
case "$request" in
    /health)
        # Most common endpoint, matched first
        health_check
        ;;
    /api/*)
        # Common prefix, matched second
        api_handler "${request#/api/}"
        ;;
    /admin/*)
        # Less common, matched later
        admin_handler "${request#/admin/}"
        ;;
    *)
        # Default case last
        not_found
        ;;
esac

# For large dispatch tables, use associative arrays
declare -A handlers=(
    [/health]=health_check
    [/metrics]=metrics_handler
    [/status]=status_handler
)

handler="${handlers[$request]}"
if [[ -n $handler ]]; then
    "$handler"
else
    not_found
fi
```

The interaction between control flow and job control in scripts managing background processes requires explicit synchronization. A script that spawns background jobs with `&` must wait for them to complete via `wait` before exiting, or the shell will send SIGHUP to all background jobs upon termination. The `wait` builtin blocks until all background jobs complete or a specific job completes, returning the exit status of the waited job. Scripts that parallelize workloads by spawning multiple background processes must collect exit statuses with wait and aggregate them to determine overall success.

```bash
# Spawn parallel jobs
for host in "${hosts[@]}"; do
    deploy_to_host "$host" &
done

# Wait for all jobs, collecting exit statuses
failed=0
for job in $(jobs -p); do
    if ! wait "$job"; then
        echo "Job $job failed" >&2
        ((failed++))
    fi
done

if [[ $failed -gt 0 ]]; then
    echo "$failed jobs failed" >&2
    exit 1
fi
```

Defensive error handling in production scripts mandates explicit checks after critical operations, comprehensive logging of failures, and graceful degradation when external dependencies are unavailable. A robust script validates inputs, checks command exit statuses, logs errors with context, and provides meaningful diagnostics. The pattern `command || { echo "Error context" >&2; exit 1; }` ensures immediate failure with actionable error messages, preventing cascading errors from obscuring root causes.
