# Lesson 2: Process Control, Job Management, Signals

## 1. First-Principles Intuition & Invariants

The Unix philosophy rests on a deceptively simple foundation: processes are isolated execution contexts, and the shell is itself a process orchestrator. To understand process control in Bash is to understand how the operating system mediates creation, lifecycle, and termination of concurrent work units. This lesson explores the mechanisms that make multitasking tractable and examines why signal handling—far from being a peripheral concern—is the central nervous system of robust shell programming.

At the core lies a fundamental architectural invariant: every process occupies a unique position within a tree rooted at the kernel's init process (PID 1). When you invoke a command in your shell, the kernel does not magically spawn a new interpreter instance. Instead, the shell process (your login shell, typically PID around 1000–2000) calls the `fork()` system call, which duplicates its own memory image—copying the process descriptor, page tables, file descriptor table, and signal handlers—into a new child process. This child inherits an almost identical state to its parent, with one critical exception: the return value of `fork()` itself differs. In the parent, `fork()` returns the child's process ID (PID); in the child, it returns zero. This single datum allows the two processes to diverge: the parent can await the child's termination via `wait()`, while the child typically invokes `exec()` to replace its own memory image with a new program.

This fork-exec model, standardized across all Unix systems, creates a profound separation of concerns. The shell does not need to understand or parse the internal structure of every possible command it might execute. Instead, it delegates responsibility to the program image itself, loaded by the kernel's ELF loader and initialized by libc. The shell's role is purely coordinative: create a process, set up its environment (working directory, file descriptors, signal masks), then either wait for completion or return control to the terminal.

Why must this be explicit? Why not have the shell simply call the command as a function? The answer is process isolation and resource management. Each process has its own virtual address space, protected by the Memory Management Unit (MMU) and enforced by page tables. When a process crashes—whether due to a segmentation fault, division by zero, or an infinite loop consuming memory—that failure cannot propagate to the shell itself. The process is quarantined. Furthermore, modern operating systems measure resource consumption per process: CPU time, memory footprint, number of open file descriptors, maximum file size. A runaway child cannot steal all the system's memory and bring down the shell. This isolation is not merely a convenience; it is a cornerstone of system stability.

The shell's job control system extends this isolation into a model of foreground and background execution. When you type a command and press Enter, that process ordinarily runs in the foreground: its standard input is connected to your terminal, its output appears on your screen, and the shell blocks (suspends itself) awaiting the process's exit. If you append an ampersand (`&`), the shell instead launches the process in the background: the child runs concurrently, and the shell immediately returns a prompt, ready for your next command. This shift from synchronous to asynchronous execution enables pipeline parallelism, allows long-running tasks to proceed while you continue interactive work, and forms the basis for sophisticated workflow management.

Yet background processes introduce complexity. How does the shell track multiple children? What happens when a child exits while the shell is busy servicing a new foreground command? The kernel sends a `SIGCHLD` signal to the parent, notifying it that a child's state has changed. The shell's signal handler intercepts this notification, calls `waitpid()` to reap the child's exit status, and updates its internal job table. This asynchronous notification mechanism is essential: without it, the shell would need to poll repeatedly or block indefinitely. Instead, the kernel guarantees that the parent is notified the moment a child exits, allowing near-real-time synchronization.

Signals themselves deserve careful study. A signal is a software interrupt—a lightweight form of asynchronous notification delivered by the kernel to a process. When you press Ctrl+C at the terminal, the terminal driver sends a `SIGINT` signal to the foreground process group. This signal, by default, terminates the process. But the process can install a custom signal handler, allowing it to catch `SIGINT`, log diagnostics, perform cleanup, and then exit gracefully. Some signals cannot be caught (`SIGKILL`, `SIGSTOP`) because the kernel must guarantee the ability to forcibly terminate or suspend a process. Others are informational (`SIGUSR1`, `SIGUSR2`) and are typically ignored unless the program explicitly handles them. The signal model is a contract between kernel and process: the kernel promises to deliver signals reliably, and the process promises to handle them within bounded time.

Process substitution introduces another dimension. When you write `<(command)`, the shell creates a named pipe (FIFO) and launches the command in a subshell, redirecting its output to that pipe. From the perspective of the calling command, the FIFO appears as a file path; internally, it is a kernel buffer mediating communication between processes. This mechanism allows arbitrary commands to participate in streams that might otherwise require complex temporary files or shell control structures, exemplifying how the shell extends the Unix toolkit beyond the original fork-exec-wait trilogy.

The mathematical invariant underlying all of this is elegant: the process tree is a forest of directed acyclic graphs (DAGs), each with a single root (init or a session leader), and each non-root node has exactly one parent. Parent-child relationships are immutable during a process's lifetime. When a child exits but its parent has not yet called `wait()`, the child becomes a zombie—its process descriptor remains in the kernel's process table, holding its exit status for the parent to retrieve. The system has a finite pool of process table slots; zombie processes consume them. If a parent never calls `wait()` (or never sets up a `SIGCHLD` handler), zombies accumulate until the process table fills and the system can no longer create new processes. This is not a theoretical edge case; it is a real failure mode that has crashed production systems.

## 2. Core Architecture & Mechanics

### 2.1 The Fork-Exec Model in Depth

The fork-exec sequence is the heartbeat of process creation in Unix. When you type `ls -la /tmp` and press Enter, the following sequence occurs:

First, the shell receives the command line from the terminal driver and parses it into tokens: `ls`, `-la`, and `/tmp`. It searches for the executable `ls` by iterating through directories in the `PATH` environment variable, eventually locating `/bin/ls`. The shell then calls `fork()`, which creates an identical copy of the shell process. At this point, two processes exist: the original shell and its child. The kernel returns a unique PID to each. The parent receives the child's PID as the return value of `fork()`; the child receives zero.

The child process, now running a copy of the shell code, detects that `fork()` returned zero and knows it is the child. It performs any necessary setup: redirecting file descriptors, setting the working directory, clearing or installing signal handlers, and adjusting resource limits. Then it calls `exec()` (typically via `execvp()` in C, which searches `PATH`). The `exec()` call is remarkable: it does not create a new process. Instead, it replaces the calling process's memory image—its code, data, heap, and stack—with the contents of the executable file. The process ID remains unchanged; the parent-child relationship is preserved. Only the program being executed changes.

The parent shell, which also received the return value from `fork()`, now knows the child's PID. In a foreground context, the parent calls `waitpid(child_pid, &status, 0)`, blocking until the child terminates. When `ls` completes and exits, the kernel transitions the child process to a zombie state (technically, the `TASK_ZOMBIE` state in the kernel's process descriptor) and sends a `SIGCHLD` signal to the parent. The blocked `waitpid()` call returns, providing the child's exit status in the `status` variable. The parent reads this status, updates its job table, prints a new prompt, and is ready for the next command.

This sequence relies on several invariants:

The child's virtual address space is initially identical to the parent's. This is cheap to implement because modern Unix systems use copy-on-write (COW) semantics: the kernel does not physically copy all memory pages. Instead, it creates new page table entries pointing to the same physical pages, marking them read-only. Only when the child (or parent) modifies a page does the kernel trigger a page fault, allocate a new physical page, copy the contents, and update the page tables. For short-lived processes that immediately call `exec()`, the child never modifies its inherited memory, so no copying occurs.

File descriptors are inherited by the child, with the exception of those marked with the `FD_CLOEXEC` flag. This allows the parent to set up redirections (e.g., connecting `stdout` to a pipe or file) before calling `exec()`. The child's `exec()` call replaces the program image but preserves the file descriptors, so the new program inherits the redirections automatically.

Signal handlers are reset to their default disposition in the child, while signal masks are inherited. This prevents the child from accidentally triggering the parent's signal handlers; it forces the child to opt into custom signal handling if needed.

### 2.2 Job Control and Process Groups

Foreground and background processes are managed through job control, a mechanism that groups processes into units that can be suspended, resumed, or terminated as a single entity. The kernel maintains a process group ID (PGID) for each process. All processes in the same process group receive the same signals (e.g., `SIGINT` from Ctrl+C) when the signal is sent to the process group rather than a single process.

When the shell creates a new job, it assigns the child process (and any processes it spawns via pipes) to a new process group. For a simple command like `ls -la /tmp`, the shell creates a single process in a new process group, waits for it to complete, and returns. For a pipeline like `cat file.txt | grep pattern | wc -l`, the shell creates three processes—one for each command—and places them all in the same process group. When any of these processes terminates naturally, the shell reaps it via `waitpid()`. If the user presses Ctrl+C, the terminal driver sends `SIGINT` to the entire process group, and all three processes receive the signal simultaneously (unless they have custom handlers). This ensures that pipelines terminate cohesively.

Background jobs are handled similarly, except the shell does not call `waitpid()` immediately. Instead, it registers the job in an internal table, prints a job number and PID, and returns the prompt. The shell's main loop now handles two types of events: user input from the terminal, and `SIGCHLD` signals from background children. When `SIGCHLD` arrives, the shell's signal handler calls `waitpid(-1, &status, WNOHANG)`, which reaps all terminated children without blocking. The `-1` means "any child process," and `WNOHANG` means "do not block if no children have terminated." The shell updates its job table, marking the job as done or stopped.

The `jobs` builtin command lists all known jobs, and the `fg` and `bg` builtins move jobs between foreground and background. When you type `fg %1`, the shell sends `SIGCONT` to the process group associated with job 1, resuming it if it was stopped, and then calls `waitpid()` to block until it completes. When you type `bg %1`, the shell sends `SIGCONT` to resume the job but does not block; the job continues in the background.

### 2.3 Signals: The Nervous System

Signals are the kernel's primary mechanism for asynchronous communication with processes. A process receives a signal while executing arbitrary code; the kernel interrupts execution, delivers the signal, and—depending on the signal's disposition—either terminates the process, stops it, continues it, or invokes a custom handler. This model is elegant but requires care: signal handlers must be short, reentrant (safe to call while the main program is in any state), and use only async-signal-safe functions.

The standard signals most relevant to shell programming are:

`SIGTERM` (15): A request to terminate. This is the default signal sent by `kill pid`. A process should handle this gracefully by cleaning up resources and exiting.

`SIGKILL` (9): An unconditional termination order. This signal cannot be caught, blocked, or ignored. The kernel terminates the process immediately. Use this only when `SIGTERM` is ineffective.

`SIGINT` (2): Interrupt from the terminal, typically triggered by Ctrl+C. The default action is to terminate the process. Custom handlers can use this to trigger cleanup routines before exit.

`SIGSTOP` (19): An unconditional stop order. This signal cannot be caught or ignored. The kernel suspends the process. The process resumes when it receives `SIGCONT`.

`SIGCONT` (18): Continue a stopped process. If a process is not stopped, this signal is ignored.

`SIGCHLD` (17): Notification that a child process has changed state (exited, stopped, or continued). The default action is to ignore this signal, but interactive shells install a custom handler to reap child processes.

`SIGUSR1` (10) and `SIGUSR2` (12): User-defined signals. These are application-specific and are typically ignored unless the program installs a handler.

`SIGHUP` (1): Hang-up signal, traditionally sent when a terminal connection is lost. Interactive shells interpret this as a request to exit, while daemon processes might use it to signal a configuration reload.

The behavior of a signal is determined by its disposition, which can be set via the `signal()` or `sigaction()` system call. Each process maintains a signal disposition table (part of its process descriptor) and a signal mask—a set of signals currently blocked. When a signal is generated, the kernel checks if the signal is in the mask; if so, the signal is queued (pending) and not delivered until the mask is cleared. If not masked, the kernel suspends the process, saves its current state, and invokes the signal handler (if one is installed) or performs the default action (usually termination).

In Bash, the builtin command `trap` installs custom signal handlers. The syntax `trap 'command' SIGNAL` registers `command` to be executed whenever `SIGNAL` is delivered to the shell. For example:

```bash
trap 'echo "Caught SIGINT"; exit 1' SIGINT
```

This handler catches `SIGINT` (Ctrl+C), prints a message, and exits with status 1. The handler is executed by the shell's main loop after the signal is received; it is not invoked from arbitrary code, so it can safely call any Bash builtin or command.

### 2.4 Process Substitution and FIFOs

Process substitution, a Bash extension, allows you to use command output as a file. The syntax `<(command)` creates a named pipe (FIFO) and spawns `command` in a subshell, redirecting its output to the FIFO. The shell expands `<(command)` to the path of the FIFO (e.g., `/dev/fd/63`), which you can pass to any command expecting a file path.

Consider this example:

```bash
diff <(sort file1.txt) <(sort file2.txt)
```

The shell creates two FIFOs and spawns two subshells: one sorts `file1.txt` and writes to the first FIFO, the other sorts `file2.txt` and writes to the second FIFO. The `diff` command receives the paths to these FIFOs and reads from them as if they were regular files. When `diff` closes a FIFO, the corresponding subshell's output end also closes, causing the subshell to terminate. When both subshells are done, the FIFOs are cleaned up.

This mechanism avoids the need for temporary files and allows natural composition of commands that do not support pipes natively. For instance, `diff` expects two file paths; without process substitution, you would need to write the output of each sort to a temporary file, invoke `diff`, and then clean up the temporary files. Process substitution handles all of this transparently.

Internally, a FIFO is a kernel buffer that mediates communication between a writer and readers. Unlike regular pipes, which are created on demand and exist only during the lifetime of the processes using them, FIFOs persist in the file system (until explicitly deleted with `rm`) and can be opened by unrelated processes. However, Bash's process substitution uses the `/dev/fd` pseudo-filesystem, which provides dynamically created file descriptors as paths; these FIFOs are automatically cleaned up when the processes exit.

### 2.5 Process State Transitions

A process transitions through several states during its lifetime:

```
Running -> Blocked (waiting for I/O or a system call)
Blocked -> Running (I/O completes or system call returns)
Running -> Stopped (receives SIGSTOP or is traced)
Stopped -> Running (receives SIGCONT)
Running -> Zombie (process exits; parent has not yet called wait)
Zombie -> Reaped (parent calls waitpid)
```

When a process exits (or is terminated by a signal), it transitions to the zombie state. The kernel keeps the process descriptor in memory, storing the exit status and resource usage, until the parent calls `waitpid()` to retrieve this information. If the parent dies before calling `waitpid()`, the process is adopted by init, which periodically reaps all orphaned children. A process in the zombie state consumes minimal resources (just the kernel memory for its descriptor), but accumulation of many zombies can prevent new process creation.

The `ps` command displays process state using single-letter codes: `R` for running, `S` for sleeping (blocked on I/O), `T` for stopped, `Z` for zombie, and `D` for disk sleep (blocked on uninterruptible I/O, typically disk operations). Observing these states helps diagnose process management issues.

## 3. Practical Patterns and Idioms

### 3.1 Waiting for Multiple Background Jobs

A common pattern is launching multiple background jobs and waiting for all to complete:

```bash
#!/bin/bash
# Download multiple files in parallel
for url in https://example.com/file1 https://example.com/file2 https://example.com/file3; do
    curl -O "$url" &
done

# Wait for all background jobs to complete
wait
```

The `wait` builtin, called without arguments, blocks until all background children have exited. The shell's `SIGCHLD` handler reaps each child as it terminates, and `wait` returns once the last one is reaped. This is simpler than manually tracking PIDs or invoking `waitpid()` in a loop.

If you need to capture the exit status of individual jobs, you can collect PIDs and wait for each explicitly:

```bash
#!/bin/bash
pids=()
for url in https://example.com/file1 https://example.com/file2 https://example.com/file3; do
    curl -O "$url" &
    pids+=($!)
done

# Wait for each job and check its exit status
for pid in "${pids[@]}"; do
    if wait "$pid"; then
        echo "PID $pid succeeded"
    else
        echo "PID $pid failed with status $?"
    fi
done
```

Here, `$!` expands to the PID of the last background job. Each `wait` call blocks until the specified PID terminates and returns the exit status. The `if` statement checks whether the exit status was zero (success) and prints accordingly.

### 3.2 Graceful Shutdown with Signal Handling

Production scripts often need to clean up resources—temporary files, database connections, child processes—when interrupted. A robust pattern is:

```bash
#!/bin/bash
set -o pipefail

# Array to track background PIDs
child_pids=()

cleanup() {
    echo "Shutting down gracefully..."
    for pid in "${child_pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Terminating PID $pid..."
            kill -TERM "$pid"
        fi
    done
    
    # Wait for children to exit, with a timeout
    for i in {1..30}; do
        remaining=0
        for pid in "${child_pids[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                remaining=$((remaining + 1))
            fi
        done
        if [ $remaining -eq 0 ]; then
            break
        fi
        sleep 0.1
    done
    
    # Force-kill any stragglers
    for pid in "${child_pids[@]}"; do
        kill -9 "$pid" 2>/dev/null || true
    done
    
    exit 0
}

trap cleanup SIGTERM SIGINT

# Launch background jobs
for i in {1..5}; do
    sleep 1000 &
    child_pids+=($!)
done

# Wait for all jobs (this blocks until interrupted)
wait
```

This script installs a `cleanup` handler for both `SIGTERM` and `SIGINT`. When the user presses Ctrl+C or the script receives `SIGTERM`, the handler is invoked. It sends `SIGTERM` to all known children, waits up to 3 seconds for them to exit, and then force-kills any stragglers with `SIGKILL`. Finally, it exits with status 0. This ensures that the script never leaves zombie children or orphaned processes.

The `kill -0 $pid` test checks whether a process still exists without sending a signal; if the process is gone, `kill` returns a non-zero exit code.

### 3.3 Monitoring Process State with ps and Jobs

Understanding the current state of processes is essential for debugging. The `ps` command displays a snapshot of process information. Common invocations include:

```bash
ps aux
```

This shows all processes on the system with detailed information: user, PID, CPU usage, memory usage, state, and command line. The output is typically piped to `grep` to filter for specific processes:

```bash
ps aux | grep nginx
```

For a more compact view of running jobs in the current shell:

```bash
jobs -l
```

This lists all known background jobs with their job numbers, PIDs, states (Running, Stopped, Done), and commands. The `-l` flag includes the PID. If a job has terminated, `jobs` marks it as Done but does not remove it until the next command prompt; this allows you to inspect its exit status. To clean up completed jobs:

```bash
jobs -r
```

This lists only running jobs. Completed jobs can be removed with:

```bash
jobs -c
```

(In some shells, use `disown` to remove a job from the shell's job table without terminating it.)

### 3.4 Process Substitution in Data Processing

Process substitution shines in data processing workflows. Consider comparing the output of two commands:

```bash
diff <(ssh host1 'ps aux') <(ssh host2 'ps aux')
```

Without process substitution, you would need to log into each host, save the output to a file, transfer the files, and then compare them. With process substitution, the shell handles all of this transparently: it spawns two subshells, each executing the SSH command and writing to a FIFO, and `diff` reads from both FIFOs.

Another example: feeding multiple streams into a command that expects files:

```bash
paste <(seq 1 10) <(seq 11 20) <(seq 21 30)
```

The `paste` command merges lines from multiple files. Without process substitution, you would need to generate three temporary files and pass them to `paste`. With process substitution, three subshells generate the sequences and write to FIFOs, and `paste` reads from them as if they were regular files.

### 3.5 Debugging Signal Handling

When a script behaves unexpectedly with respect to signals, debugging can be challenging. The `set -x` option enables tracing, printing each command before execution:

```bash
#!/bin/bash
set -x

trap 'echo "Caught SIGTERM"' SIGTERM
trap 'echo "Caught SIGINT"' SIGINT

sleep 1000
```

When run and interrupted, the output shows whether the trap was installed and invoked. However, `set -x` does not trace signal handlers themselves (they are invoked by the kernel, not by the shell script), so you may not see the handler's commands execute in the trace. Adding explicit logging helps:

```bash
trap 'echo "Handler for SIGTERM invoked at $(date)" >> /tmp/handler.log; exit 1' SIGTERM
```

This writes to a log file, which you can examine post-mortem.

For deeper debugging, the `strace` utility traces system calls, including signal delivery:

```bash
strace -f -e signal bash script.sh
```

The `-f` flag traces child processes, and `-e signal` filters for signal-related system calls. The output shows when signals are delivered and how the process responds.

## 4. Common Pitfalls and Solutions

### 4.1 Zombie Processes

Zombie processes accumulate when a parent never calls `waitpid()` or fails to install a `SIGCHLD` handler. Once accumulated, they remain until the parent exits (at which point init adopts and reaps them) or until the parent explicitly calls `waitpid()`.

To identify zombies:

```bash
ps aux | grep Z
```

Zombies are marked with a `Z` in the STAT column. If a script creates many zombies, the root cause is typically a missing `SIGCHLD` handler or a missing `wait` call at the end of the script.

Solution: Always call `wait` (without arguments) to wait for all background children to complete, or install a `SIGCHLD` handler that calls `waitpid()` with the `WNOHANG` flag.

### 4.2 Signal Handlers Calling Non-Async-Safe Functions

Signal handlers are invoked asynchronously, potentially interrupting the main program at any point. If the main program was in the middle of a library function (e.g., `malloc()`), and the signal handler calls another library function (e.g., `free()`), the result is undefined behavior—the library's internal data structures may be corrupted, leading to crashes or data corruption.

Solution: Signal handlers should call only async-signal-safe functions. These include basic system calls like `write()`, `kill()`, and `exit()`, but not library functions like `printf()` or `malloc()`. In Bash, this is handled transparently; the shell ensures that its signal handlers call only safe functions. In C programs, refer to the `signal-safety(7)` man page for the complete list of safe functions.

If you need to log from a signal handler, write to a file descriptor using `write()` rather than `printf()`:

```c
const char *msg = "Signal received\n";
write(STDOUT_FILENO, msg, strlen(msg));
```

### 4.3 Child Processes Inheriting Unwanted State

When a process calls `fork()`, the child inherits file descriptors, signal handlers, and environment variables. If the parent has open file handles, the child will inherit them; if the parent has ignored `SIGPIPE`, the child will also ignore it. This can lead to subtle bugs.

Solution: In Bash, use `exec` with redirection to manage file descriptors explicitly:

```bash
exec 3< file.txt
# PID $$ has FD 3 open
bash -c 'echo "Child sees FD 3: $(cat <&3)"'
# Child inherits FD 3
```

If you want to isolate a child from the parent's environment, use a subshell with explicit setup:

```bash
(
    # Start a fresh subshell
    unset UNWANTED_VAR
    # Reset signal handlers to defaults
    trap - SIGTERM SIGINT
    # Run the command
    exec command
)
```

The subshell inherits the environment, but you can modify it before exec'ing the command.

### 4.4 Race Conditions in Job Control

Background jobs introduce race conditions. If you launch a background job and immediately query its status, the shell's `SIGCHLD` handler may not have been invoked yet, and the job table may be out of sync.

Solution: Use `wait` to explicitly synchronize with background jobs. After launching background jobs, call `wait` (with or without a PID) to ensure the jobs have completed before proceeding. This blocks the shell until the kernel has notified it of the child's state change.

### 4.5 Process Substitution with Large Data

Process substitution creates FIFOs, which are kernel buffers. If a command writes a large amount of data to a FIFO faster than the reader consumes it, the FIFO buffer fills up, and the writer blocks. If the reader blocks (waiting for input from another source), and the writer is blocked (waiting for the FIFO to drain), a deadlock occurs.

Solution: Use explicit temporary files for large data sets, or redesign the pipeline to avoid deep nesting of process substitutions. For example, instead of:

```bash
diff <(sort <(cat file1.txt | tr a-z A-Z)) <(sort file2.txt)
```

Use:

```bash
cat file1.txt | tr a-z A-Z | sort > /tmp/temp1.txt
sort file2.txt > /tmp/temp2.txt
diff /tmp/temp1.txt /tmp/temp2.txt
rm /tmp/temp1.txt /tmp/temp2.txt
```

This explicitly serializes the pipeline, avoiding potential deadlocks.

## 5. Advanced Patterns

### 5.1 Managing Process Groups and Sessions

A session is a collection of process groups associated with a single terminal. The shell's process group is the session leader. When a user logs in, the login process creates a new session, and the login shell becomes the session leader.

Job control commands (`fg`, `bg`) operate on process groups within the current session. If you need to manage processes across session boundaries (e.g., detaching a process from the terminal), use `nohup` or `disown`:

```bash
nohup long_running_task &
disown %1
```

`nohup` redirects the process's stdin from `/dev/null` and its stdout/stderr to a file (typically `nohup.out`), ensuring the process continues even if the terminal closes. `disown` removes the job from the shell's job table, preventing the shell from sending it a `SIGHUP` signal when the shell exits.

### 5.2 Parallel Process Pools

For tasks that benefit from parallelism but need to limit the number of concurrent processes (to avoid resource exhaustion), a process pool pattern is useful:

```bash
#!/bin/bash
max_parallel=4
active=()

for file in /path/to/files/*; do
    # If we've reached the max, wait for one to finish
    if [ ${#active[@]} -ge $max_parallel ]; then
        wait -n  # Wait for any one child to exit
        active=()  # Reset the array
        for pid in $(jobs -p); do
            active+=($pid)
        done
    fi
    
    # Launch a new job
    process_file "$file" &
    active+=($!)
done

# Wait for all remaining jobs
wait
```

The `wait -n` command blocks until any one child exits, allowing the pool to launch a new job. The `jobs -p` command lists all active job PIDs, which are stored in the `active` array for bookkeeping.

### 5.3 Structured Concurrency with exec

Complex scripts with multiple levels of subshells can become difficult to manage. A structured approach is to use `exec` to redirect file descriptors at the script level, then use process substitution for read-only operations:

```bash
#!/bin/bash
set -o pipefail

# Redirect stdin, stdout, stderr for the entire script
exec 3< input.txt
exec 4> output.txt
exec 5> error.log

# Now process_data reads from FD 3, writes to FD 4, and logs to FD 5
while read -u 3 line; do
    result=$(echo "$line" | process_pipeline)
    echo "$result" >&4
done

# Close the file descriptors
exec 3<&-
exec 4>&-
exec 5>&-
```

This pattern avoids nested subshells and makes resource management explicit.

### 5.4 Process Restart and Monitoring

For long-running services, a supervisor pattern monitors the process and restarts it if it dies:

```bash
#!/bin/bash
service_cmd="$1"
max_retries=5
retry_delay=5
attempt=0

while [ $attempt -lt $max_retries ]; do
    echo "Attempt $((attempt + 1)): Starting $service_cmd"
    
    # Run the command and capture its PID
    $service_cmd &
    pid=$!
    
    # Wait for it to exit
    if wait $pid; then
        echo "Service exited with status 0; assuming normal exit"
        exit 0
    else
        status=$?
        echo "Service exited with status $status; restarting in ${retry_delay}s..."
        sleep $retry_delay
        attempt=$((attempt + 1))
    fi
done

echo "Max retries exceeded; giving up"
exit 1
```

This runs the service in the foreground, waits for it to exit, and restarts it if the exit status is non-zero. After a configurable number of retries, it gives up and exits.

## 6. Summary and Key Takeaways

Process control in Unix and Bash is grounded in a few elegant primitives: `fork()` creates processes, `exec()` replaces their memory image, `wait()` synchronizes on child termination, and signals provide asynchronous notification. The shell orchestrates these primitives to provide job control, background execution, and sophisticated process management.

Understanding the fork-exec-wait model demystifies how commands are launched and how the shell maintains control over multiple children. Signals form the nervous system connecting the kernel to processes, enabling timely response to events. Process substitution extends the shell's ability to compose commands, avoiding temporary files and enabling natural data flow.

Robust shell scripts employ careful signal handling to clean up resources, avoid zombie processes by calling `wait()`, and use process groups and job control to manage related processes cohesively. Debugging process management issues requires understanding process state transitions, recognizing symptoms like zombie accumulation, and using tools like `ps`, `jobs`, and `strace` to diagnose problems.

The patterns and idioms presented here—waiting for multiple jobs, graceful shutdown, monitoring process state, and supervisor loops—form the foundation of production-grade shell scripts. Mastery of these concepts transforms shell programming from a scripting convenience into a powerful tool for systems administration and automation.
