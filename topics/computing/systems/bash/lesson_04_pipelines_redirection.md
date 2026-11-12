# Lesson 4: Pipelines and Stream Redirection

## 1. First-Principles Intuition & Invariants

Every Unix process is born into a world shaped by three invisible threads connecting it to the system: standard input on file descriptor zero, standard output on file descriptor one, and standard error on file descriptor two. These are not abstractions layered over some other mechanism — they are concrete entries in the per-process file descriptor table, integer indices into a kernel-managed array of `struct file *` pointers that the process inherits from its parent at the moment `fork()` returns. This inheritance model is not incidental; it is the architectural foundation upon which the entire Unix philosophy of composable tools was deliberately built.

Ken Thompson and Dennis Ritchie were not thinking about shells when they designed file descriptors. They were solving a deeper problem: how do you give a process a uniform interface to things as dissimilar as a terminal, a tape drive, a network socket, and an in-memory buffer? The answer was to abstract everything behind an integer handle and let the kernel manage the indirection. The shell then discovered — and this is the genuinely elegant insight — that if you can close file descriptor one and reopen it pointing at a file or a pipe before `execve()` runs, the child process never knows the difference. Its source code never changes. The composition happens entirely in the machinery surrounding the process boundary, not inside it.

A pipe, at the kernel level, is a bounded ring buffer residing in kernel memory. On Linux, `pipe(2)` allocates this buffer — historically 4096 bytes, expanded to 65536 bytes (sixteen 4 KiB pages) in kernel 2.6.11 — and returns two file descriptors: a read end and a write end. The fundamental invariant of a pipe is that writes block when the buffer is full and reads block when the buffer is empty, and both blocking operations release the CPU back to the scheduler. This is not a software-level sleep mechanism; it is a kernel wait queue operation. The writing process's task struct is placed on the pipe's internal `wait_queue_head_t`, its state is set to `TASK_INTERRUPTIBLE`, and `schedule()` is called. When the reading process drains enough data to drop the buffer below capacity, the kernel wakes the writer via `wake_up_interruptible()`. The pipe is therefore not merely a data conduit — it is a synchronization primitive, implementing a classic producer-consumer relationship with the kernel as the monitor.

Understanding this blocking behavior is essential because it determines the throughput characteristics of an entire pipeline. If you chain `producer | transformer | consumer`, the entire pipeline runs only as fast as the slowest stage. The kernel is enforcing backpressure automatically. When the consumer falls behind, its read end's buffer fills, the transformer blocks on write, and consequently the producer blocks on its own write to the previous stage. This cascade is the mechanical meaning of "pipe backpressure," and it is why adding CPU cores does not linearly accelerate a pipeline dominated by a single slow stage — the bottleneck stage serializes the entire chain through the kernel's wait queues.

The shell operationalizes this kernel mechanism through a precise sequence of syscalls. When bash encounters `cmd1 | cmd2`, it calls `pipe(pipefd)` to create the channel, then forks twice. In the first child, it closes `pipefd[0]` (the read end it doesn't need), duplicates `pipefd[1]` onto file descriptor one using `dup2(pipefd[1], STDOUT_FILENO)`, closes the now-redundant `pipefd[1]`, and executes `cmd1`. In the second child, the symmetric operation occurs: `pipefd[1]` is closed, `pipefd[0]` is duplicated onto file descriptor zero, and `cmd2` executes. The parent closes both ends of `pipefd` — critically important, because if any process holds the write end open, the reader will never see EOF. This is a frequent source of pipelines that hang: a pipe write end inadvertently left open in the parent or in a background process prevents the downstream reader from ever terminating.

The formal invariant governing EOF on a pipe reads simply: the read end receives EOF when all file descriptors referencing the write end have been closed. The word "all" carries enormous weight. Each `fork()` duplicates the entire file descriptor table, so every child inherits every open file descriptor. If you open a pipe, fork ten children, and forget to close the write end in nine of them, the tenth child — your intended reader — will block forever waiting for data that never arrives. The shell handles this automatically within a simple pipeline, but once you introduce process substitution, coprocesses, or background jobs, the bookkeeping becomes your responsibility.

## 2. Core Architecture & Mechanics

### The File Descriptor Table and Redirection Mechanics

The kernel represents each process's open files as a three-level structure. The process has a `files_struct` containing an `fdtable`, which is an array of `struct file *` pointers indexed by file descriptor number. Each `struct file` holds a reference to a `struct inode` (the actual filesystem object), a current file offset, the open flags, and a `file_operations` vtable. When you redirect output with `> file`, the shell calls `open(file, O_WRONLY|O_CREAT|O_TRUNC, 0666)` which returns some file descriptor `n`, then calls `dup2(n, 1)` which atomically copies the `struct file *` at slot `n` into slot `1`, incrementing the `f_count` reference on the underlying file object, then closes `n`. After `dup2`, file descriptor one points at the new file. The old `struct file` backing the terminal's stdout is dereferenced; if no other fd points to it, its reference count drops to zero and the kernel closes it.

This mechanical understanding clarifies several behaviors that trip up even experienced engineers. The append redirect `>>` differs from `>` only in the `O_APPEND` flag passed to `open`. With `O_APPEND`, every `write(2)` syscall atomically seeks to the current end-of-file before writing. This is a POSIX guarantee: even with multiple concurrent processes appending to the same file, individual writes up to `PIPE_BUF` bytes (4096 bytes on Linux) are atomic at the kernel level. The `2>&1` construction, meanwhile, does not "merge" streams in some abstract sense — it executes `dup2(1, 2)`, making file descriptor two point to the same `struct file` as file descriptor one at that precise moment. Order matters profoundly: `cmd > file 2>&1` first redirects fd 1 to `file`, then copies fd 1 (now `file`) into fd 2. The result is both stdout and stderr going to `file`. But `cmd 2>&1 > file` first copies the current fd 1 (the terminal) into fd 2, then redirects fd 1 to `file`. Stderr still goes to the terminal. The shell processes redirections left to right, and each redirect operates on the file descriptor table as it exists at that exact point in evaluation.

```
Before:  fd 0 → terminal    fd 1 → terminal    fd 2 → terminal

After `> file`:
         fd 0 → terminal    fd 1 → file         fd 2 → terminal

After `2>&1` (applied after `> file`):
         fd 0 → terminal    fd 1 → file         fd 2 → file   ✓

--- contrast ---

After `2>&1` (applied first):
         fd 0 → terminal    fd 1 → terminal    fd 2 → terminal

After `> file` (applied second):
         fd 0 → terminal    fd 1 → file         fd 2 → terminal  ✗
```

### Pipeline Execution Flow

The internal execution model of a multi-stage pipeline can be represented as a directed acyclic graph of kernel objects connected by pipe buffers. Consider a three-stage pipeline `A | B | C`:

```
┌─────────────────────────────────────────────────────────────┐
│                        SHELL (parent)                        │
│  pipe(p1)  pipe(p2)  fork→A  fork→B  fork→C                 │
│  wait(A) wait(B) wait(C)   ← collects exit statuses         │
└─────────────────────────────────────────────────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ Process A │      │ Process B │      │ Process C │
   │ fd1→p1[1] │─p1──▶│ fd0→p1[0] │─p2──▶│ fd0→p2[0] │
   │           │      │ fd1→p2[1] │      │ fd1→tty   │
   └──────────┘      └──────────┘      └──────────┘
        │                                     │
   stdin=tty                             stdout=tty

   ┌────────────┐    ┌────────────┐
   │  Pipe p1   │    │  Pipe p2   │
   │ [kernel    │    │ [kernel    │
   │  ring buf] │    │  ring buf] │
   └────────────┘    └────────────┘
```

The shell forks all pipeline children before waiting on any of them. This is a crucial design point: `A`, `B`, and `C` run concurrently. The pipeline does not execute sequentially — stage `B` begins consuming output from `A` as soon as `A` starts producing it, and `C` simultaneously begins consuming output from `B`. The kernel's pipe buffer acts as an elastic decoupler, allowing brief bursts from any stage to proceed without blocking as long as the downstream buffer has capacity.

### Here-Documents and Here-Strings

A here-document is deceptively simple at the surface level and genuinely interesting at the implementation level. When bash encounters:

```bash
cat (cmd)` is the symmetric case: `cmd1 > >(cmd2)` redirects `cmd1`'s stdout into a FIFO whose read end is connected to `cmd2`'s stdin. This is subtly different from `cmd1 | cmd2` in one important respect: `cmd2` runs as a child of the shell, not as part of the same pipeline wait group. The shell does not wait for `cmd2` to finish when the pipeline exits. If `cmd2` is performing buffered I/O — say, writing to a file via `tee` — there is a race condition: the shell may proceed to the next command before `cmd2` has flushed its buffers. The correct mitigation is to explicitly wait: `wait` with no arguments waits for all background jobs, or you can capture the PID of the process substitution with `$!` immediately after launching it.

### Subshells vs. Command Grouping

The difference between `(cmd1; cmd2)` and `{ cmd1; cmd2; }` is the difference between forking and not forking, and this distinction has profound implications for variable visibility, working directory scope, and exit status propagation.

A subshell `(...)` calls `fork()`. The child process gets a copy of the parent shell's entire environment — variables, functions, aliases, options, and the current working directory — but changes made inside the subshell are invisible to the parent after the subshell exits. This copy-on-write fork is relatively cheap on Linux due to the kernel's CoW page-mapping, but it is not free: each forked subshell allocates kernel task structures, copies the file descriptor table, and eventually requires `waitpid()` cleanup. The practical consequence is that variable assignments made inside `(...)` evaporate when the subshell exits, which is simultaneously a safety feature (isolation) and a trap (data loss).

Command grouping `{ ...; }` runs in the current shell process. There is no fork, no isolation, and no overhead beyond the commands themselves. Variable assignments persist. The working directory changes persist. This makes `{ ...; }` the correct choice when you want to group commands for redirection purposes without paying the fork cost or losing state:

```bash
{ 
    echo "header"
    generate_data
    echo "footer"
} > output.txt
```

This redirects the collective output of all three commands to `output.txt` in a single shell process, without forking. If you wrote `( echo "header"; generate_data; echo "footer" ) > output.txt`, the behavior is identical for simple output redirection, but any variables set inside by `generate_data` would vanish on subshell exit.

### Background Processes and Coprocesses

Appending `&` to a command causes the shell to fork the command and return immediately without waiting for it. The child's PID is recorded in `$!`. The child is placed in its own process group by the shell's job control machinery (`setpgid(child_pid, child_pid)`), which prevents keyboard signals like `SIGINT` from automatically propagating to it. Critically, a background process inherits the shell's file descriptors. If its stdin remains connected to the terminal, any attempt to read will cause it to receive `SIGTTIN`, which suspends it — a common source of mysteriously stopped background jobs. The correct practice is to redirect stdin from `/dev/null` for background processes that do not require input: `long_running_job &"${MY_PROC[1]}"
read -r response &2
    exit 1
fi
if [[ ${pipe_statuses[1]} -ne 0 ]]; then
    echo "ERROR: transform failed with exit ${pipe_statuses[1]}" >&2
    exit 1
fi
```

One subtlety: `${PIPESTATUS[@]}` is overwritten by the next pipeline execution, including the assignment `pipe_statuses=("${PIPESTATUS[@]}")` itself if it is not careful. The array copy must happen in the same compound command or on the immediately following line before any other command executes.

### Buffering, Throughput, and `splice(2)`

The throughput of a pipeline is governed not just by the processing speed of its stages but by the interaction between userspace buffering and kernel pipe capacity. The GNU C library's `stdio` layer buffers writes in userspace: when stdout is not a terminal, it switches from line-buffering to full block-buffering, accumulating up to 8 KiB before calling `write(2)`. This is a performance optimization in isolation — fewer syscalls mean less kernel crossing overhead — but in a pipeline context it creates latency. A transformer stage processing a stream of events may buffer 8 KiB before the downstream consumer sees any data, introducing up to 8 KiB of pipeline latency per stage. For streaming analytics or interactive pipelines, this is unacceptable. The `stdbuf` utility from GNU coreutils wraps a process with an `LD_PRELOAD` shim that patches `setvbuf` to change the buffering mode without modifying the program's source.

Linux's `splice(2)` syscall represents the ceiling of pipeline performance. Rather than copying data from a pipe buffer into userspace and back into another pipe buffer, `splice` moves pages between kernel objects by updating page table mappings. The data never crosses the kernel-userspace boundary at all. Tools like `pv` (pipe viewer) use `splice` internally to achieve near-wire-speed data movement through monitoring pipelines. When you observe that `cat large_file | pv | sink` throughputs near your storage device's sequential read speed, you are witnessing `splice` operating at its theoretical limit — the kernel shuffling page references between the read buffer of the file and the write buffer of the pipe with no memory copying.

The practical implication for high-throughput pipeline design is that inserting a tool that cannot use `splice` — such as any AWK or sed invocation that must decode characters — breaks the zero-copy chain. Each such tool reintroduces two copies: one from pipe to userspace on read, and one from userspace back to pipe on write. For pipelines processing hundreds of megabytes per second, the difference between a `splice`-capable and a `splice`-incapable stage can represent the entire available memory bandwidth.

### Named Pipes, Fan-Out, and the FIFO Race

When a single data stream must be consumed by multiple independent processes, the naive approach of running the producer multiple times is wasteful. The idiomatic solution is `tee`, which reads stdin and writes identical data to both stdout and any number of additional file arguments:

```bash
generate_data | tee >(stage_A) >(stage_B) | stage_C
```

Here, process substitution creates two FIFOs. `tee` writes each chunk of data three times: once to its stdout (feeding `stage_C`) and once to each FIFO (feeding `stage_A` and `stage_B`). The kernel must copy the data once per output, so total kernel-side memory traffic is proportional to the fan-out factor. For extreme fan-out, a named pipe (created with `mkfifo`) can be a preferable architecture because it allows multiple readers to coordinate more explicitly:

```bash
mkfifo /tmp/data_pipe
generate_data > /tmp/data_pipe &
producer_pid=$!
stage_A < /tmp/data_pipe &
stage_B < /tmp/data_pipe &
wait $producer_pid
```

However, this introduces a subtle hazard: a FIFO with multiple readers is not broadcast — it is a multiplexed queue. The kernel delivers each chunk of data to exactly one reader, whichever process wins the `read(2)` race. If the intent is to give each of `stage_A` and `stage_B` the complete data stream, a single named pipe cannot achieve this. You need either `tee` with process substitution (which writes separate copies) or a true publish-subscribe mechanism outside the shell.

### Signal Delivery and Broken Pipes

When a pipeline's reader exits before the writer has finished writing, the kernel delivers `SIGPIPE` to the writer on its next `write(2)` call. The default disposition of `SIGPIPE` is to terminate the process immediately. This is correct behavior for tools like `head`, which intentionally read a fixed number of lines and then exit, cleanly terminating the upstream `cat` or generator. It becomes problematic when you have a writer that has installed a `SIGPIPE` handler (or masked the signal with `SIG_IGN`) or when the writer is a shell script that you expect to clean up after itself.

In bash scripts, `SIGPIPE` is delivered to child processes but is typically masked in the interactive shell itself to prevent accidental termination. When you write a producer that must perform cleanup on termination — removing temporary files, flushing a journal, releasing a lock — you must trap `SIGPIPE` explicitly and perform that cleanup in the signal handler:

```bash
cleanup() {
    rm -f /tmp/work_dir_$$
    exit 130
}
trap cleanup SIGPIPE SIGTERM SIGINT

produce_data_stream | head -n 1000
```

The exit code 130 is conventional for SIGINT-terminated processes (128 + signal number 2); for SIGPIPE the convention is 141 (128 + 13). Respecting these conventions matters for downstream pipefail detection and for shell scripts that inspect exit codes to distinguish normal completion from signal termination.

### Subshell Overhead and Fork Avoidance

In a tight loop calling a command substitution — `result=$(cmd)` — each invocation forks a subshell, executes `cmd` via `execve`, reads its output through a pipe, and then `waitpid`s. On a Linux system with no special optimizations, a fork-exec-wait cycle costs roughly 1 to 5 milliseconds depending on process image size and kernel state. A loop that runs ten thousand iterations will therefore spend 10 to 50 seconds on process overhead alone, entirely independent of what `cmd` actually does. This is why replacing `$(cat file)` with `$(<file)` matters: bash implements `$(<file)` as a special built-in optimization that reads the file directly in the current shell process without forking, reducing the cost from a fork-exec-wait cycle to a single `open`-`read`-`close` sequence.

More broadly, the discipline of fork-avoidance in bash scripting means preferring built-in string operations (`${var#prefix}`, `${var//pattern/replacement}`, `${#var}`) over `sed`, `awk`, or `cut` subshells for small transformations, using `mapfile` or `readarray` to load file content into arrays without spawning subshells, and reserving subshells and pipelines for the genuinely large-data transformations where their I/O advantages outweigh their process creation costs. The mental model is straightforward: every `$(...)` is a fork; every `|` is a fork plus a pipe; every explicit subshell `(...)` is a fork. Count your forks in hot paths. Eliminate the ones whose output could be computed with a parameter expansion.

The architectural conclusion this lesson arrives at is that bash pipelines are not a scripting convenience layered on top of some deeper mechanism — they are the mechanism. The file descriptor table, the fork-exec model, the kernel pipe buffer, and the POSIX signal model are the substrate, and the shell's pipeline syntax is a thin, beautifully ergonomic interface over that substrate. Writing pipelines fluently means understanding that substrate deeply enough to know when the abstraction is working in your favor and when it is working against you.
