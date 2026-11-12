# Lesson 3: I/O Redirection, File Descriptors, Streams

## 1. First-Principles Intuition & Invariants

When Dennis Ritchie and Ken Thompson designed Unix at Bell Labs in the early 1970s, they made a radical architectural decision that would define systems programming for the next half-century: **everything is a file**. This deceptively simple abstraction unified the interface to hardware devices, network sockets, inter-process communication channels, and regular disk files under a single coherent model. At the heart of this model lies the **file descriptor**—an unsigned integer that serves as an opaque handle into the kernel's per-process open file table.

A file descriptor is not a pointer, not a memory address, and not the file itself. It is an index into a kernel data structure that maintains the true state of the open file: the current seek position, access mode flags, inode reference, and a pointer to the underlying file operations vector table. When a process forks, the child inherits a duplicate set of file descriptors that point to the same open file table entries, sharing seek offsets and status flags. This copy-on-write semantics for file descriptor tables enables the elegant piping model that defines shell programming: the parent shell opens a pipe, forks child processes, and each child inherits one end of the bidirectional channel while closing the other.

Every process launched by the Linux kernel begins life with three pre-opened file descriptors. **File descriptor 0** connects to standard input (stdin), the stream from which the process reads user commands, configuration data, or piped content from a predecessor in a pipeline. **File descriptor 1** routes to standard output (stdout), the primary channel for emitting results, log messages, and structured data intended for human consumption or further processing. **File descriptor 2** is reserved for standard error (stderr), a dedicated stream for diagnostic messages, warnings, and error reports that should remain visible even when stdout is redirected to a file or piped to another process.

The separation of stdout and stderr reflects a foundational principle of Unix design: distinguish between **data** and **metadata**. A well-designed command-line tool emits its primary output—the data you requested—to stdout, while progress indicators, error diagnostics, and debugging traces flow to stderr. This architectural separation allows you to redirect the data stream to a file or pipeline while still observing error messages on the terminal. When you execute `grep pattern largefile.txt > results.txt`, the matching lines flow silently into `results.txt` through stdout, but any error message about the file not existing appears immediately on your terminal through stderr, unaffected by the redirection.

The kernel maintains a global **open file table** shared across all processes, and each entry in this table tracks the current file offset, access mode, and reference count. When you duplicate a file descriptor using `dup2()` or through the implicit duplication that occurs during shell redirection, you create a new file descriptor that points to the same open file table entry. This means that two file descriptors can share a seek position: if you read from one, the offset advances for both. This behavior is subtle but critical when constructing complex redirection chains or debugging why a script behaves unexpectedly after a fork.

The deterministic rule governing file descriptor allocation is fundamental: the kernel always assigns the **lowest-numbered available file descriptor** when you open a new file or duplicate an existing descriptor. If file descriptors 0, 1, and 2 are occupied by the standard streams and you open a file without specifying a target descriptor, the kernel assigns descriptor 3. If you then close descriptor 1 and open another file, the kernel reuses descriptor 1 because it is now the lowest available slot. This predictable allocation policy underpins the shell's redirection operators: when you redirect stdout with `> file`, the shell first closes descriptor 1, then opens the target file, knowing the kernel will assign it descriptor 1 automatically.

Redirection operators in the shell are not commands; they are **metacharacters** interpreted by the shell itself before any command executes. When you type `command > file`, the shell parses the redirection operator, opens `file` for writing, duplicates the resulting file descriptor onto descriptor 1, and then invokes `execve()` to replace the shell's process image with `command`. The command itself never sees the redirection operator—it simply writes to file descriptor 1, unaware that the kernel now routes those bytes to a disk file instead of the terminal. This is the essence of I/O redirection: **transparent interposition** at the file descriptor layer, invisible to the application.

The buffering behavior of I/O streams introduces a performance optimization that can confuse programmers unfamiliar with the stdio library's internals. When a process writes to a file descriptor connected to a terminal, the C standard library employs **line buffering**: output accumulates in a userspace buffer until a newline character appears, at which point the library issues a single `write()` system call to flush the buffer. When writing to a regular file or pipe, the library switches to **full buffering**, accumulating up to 4096 or 8192 bytes before flushing. This amortizes the cost of system calls, which involve context switches and kernel mode transitions. However, full buffering means that if a process crashes before flushing its buffer, the last few kilobytes of output vanish, never reaching the destination file. Explicit calls to `fflush()` or `fsync()` provide control over this tradeoff between performance and durability.

The `/dev/fd/` directory exposes the kernel's file descriptor table as a synthetic filesystem, allowing you to reference open file descriptors by number as if they were regular files. On modern Linux systems, `/dev/fd/` is typically a symbolic link to `/proc/self/fd/`, which dynamically generates directory entries for each open descriptor in the current process. This abstraction enables powerful constructions: you can pass `/dev/fd/3` as a filename argument to a program that expects a path, and the program will read from or write to file descriptor 3 without knowing it is not accessing a real file. Similarly, `/dev/stdin`, `/dev/stdout`, and `/dev/stderr` are symbolic links to `/dev/fd/0`, `/dev/fd/1`, and `/dev/fd/2`, providing mnemonic aliases for scripts that need to explicitly reference the standard streams.

Pipelines represent the canonical form of inter-process communication in Unix. When the shell encounters the pipe operator `|`, it creates an anonymous pipe—a unidirectional byte stream with a read end and a write end—then forks two child processes. The shell duplicates the write end of the pipe onto file descriptor 1 of the left-hand process, so its stdout flows into the pipe. Simultaneously, the shell duplicates the read end onto file descriptor 0 of the right-hand process, so its stdin receives bytes from the pipe. Both child processes close the opposite ends of the pipe: the left process closes the read end, and the right process closes the write end. When the left process exits or closes its write end, the pipe reaches EOF, signaling the right process to terminate its input loop. This coordinated file descriptor manipulation, performed by the shell before either command executes, transforms two independent programs into a synchronized data processing chain.

## 2. Core System Calls & Their Semantics

The foundation of file descriptor manipulation rests on four essential system calls: `open()`, `close()`, `dup2()`, and `pipe()`. Understanding their precise behavior, including edge cases and kernel guarantees, is prerequisite to competent systems programming.

### open()

The `open()` system call creates or opens a file and returns a file descriptor:

```c
int open(const char *pathname, int flags);
int open(const char *pathname, int flags, mode_t mode);
```

The `flags` argument controls the behavior of the operation. The access mode—one of `O_RDONLY`, `O_WRONLY`, or `O_RDWR`—determines whether the file is opened for reading, writing, or both. Creation and truncation flags modify this behavior: `O_CREAT` instructs the kernel to create the file if it does not exist, using the `mode` argument to set initial permissions; `O_EXCL`, combined with `O_CREAT`, causes the call to fail if the file already exists, providing atomic creation semantics; `O_TRUNC` truncates an existing file to zero bytes, destructively clearing its content.

The `mode` argument specifies the file permission bits when creating a new file. The kernel applies the process umask to these bits: if the umask is 0022 and you specify mode 0666, the resulting file receives permissions 0644 (rw-r--r--). The umask is a per-process value that you can read and modify with the `umask()` call, though this is rarely necessary in practice.

When `open()` succeeds, it returns a non-negative file descriptor. The kernel invokes the lowest-numbered available descriptor algorithm, so if descriptors 0, 1, and 2 are in use, `open()` returns 3 for the first newly opened file. If `open()` fails—because the file does not exist and `O_CREAT` was not set, or because permission is denied—it returns -1 and sets the global `errno` variable to indicate the cause.

One subtle but critical behavior: if you open a file with `O_WRONLY` and the file exists, subsequent writes append to the file's end only if you also specified `O_APPEND`. Without this flag, the file pointer starts at position 0, and your first write truncates the file to zero bytes before writing. This is why accidentally redirecting to an existing file with `>` in the shell truncates it: the shell uses `open()` without `O_APPEND`. To append without truncating, use `O_WRONLY | O_APPEND`.

### close()

The `close()` system call closes a file descriptor and releases the kernel's resources associated with it:

```c
int close(int fd);
```

After `close()` succeeds, the file descriptor is no longer valid. Any subsequent attempt to use it—in `read()`, `write()`, or another system call—returns EBADF (bad file descriptor). The kernel decrements the reference count on the open file table entry; if the reference count reaches zero and the file has been deleted, the kernel frees the inode and data blocks.

A critical invariant: `close()` does not flush buffered I/O from userspace libraries like stdio. If you have called `printf()` or `fprintf()`, the bytes may still reside in a userspace buffer, not yet written to the kernel. Calling `close()` on the underlying file descriptor causes those buffered bytes to be lost. Always call `fflush()` on a FILE stream before closing its file descriptor, or use `fclose()`, which flushes before closing.

### dup2()

The `dup2()` system call duplicates a file descriptor, making the new descriptor reference the same open file table entry:

```c
int dup2(int oldfd, int newfd);
```

`dup2()` closes `newfd` if it is already open, then makes `newfd` refer to the same open file as `oldfd`. Both descriptors share the file pointer, so advancing one advances the other. The operation is atomic: if `oldfd` and `newfd` refer to the same file, `dup2()` closes `newfd` first, then reassigns it, ensuring consistency.

The canonical use of `dup2()` is shell redirection. When you type `command > file`, the shell executes roughly this sequence:

```c
int fd = open("file", O_WRONLY | O_CREAT | O_TRUNC, 0666);
dup2(fd, 1);           // Make fd 1 point to file
close(fd);             // Close the temporary descriptor
execve("command", ...); // Execute command; writes to fd 1 go to file
```

After `dup2(fd, 1)`, both `fd` and `1` reference the same open file. Closing `fd` does not close the file; it merely decrements the reference count. File descriptor 1 remains open and valid, pointing to the file. When `command` writes to stdout (file descriptor 1), the bytes flow into the file.

### pipe()

The `pipe()` system call creates an anonymous, unidirectional pipe and returns two file descriptors:

```c
int pipe(int pipefd[2]);
```

On success, `pipe()` populates the array `pipefd` with two descriptors: `pipefd[0]` is the read end, and `pipefd[1]` is the write end. Bytes written to `pipefd[1]` become available for reading from `pipefd[0]` in FIFO order. A pipe has a fixed kernel buffer, typically 65536 bytes on modern Linux systems. If the write end fills the buffer, subsequent `write()` calls block until the reader consumes bytes. If the reader closes the write end without reading all data, the kernel discards remaining bytes.

When all write ends of a pipe are closed, `read()` returns 0 (EOF). When all read ends are closed, a `write()` to the pipe generates SIGPIPE and returns -1 with EPIPE, signaling a broken pipe. This behavior is essential for constructing pipelines: when the right-hand process in a pipeline exits, the shell closes its end of the pipe, causing the left-hand process to detect EOF and terminate gracefully.

A pipe created with `pipe()` is anonymous and exists only while at least one file descriptor to it remains open. When all descriptors close, the kernel frees the pipe. This differs from named pipes (FIFOs), created with `mkfifo()`, which persist as files in the filesystem until explicitly deleted.

## 3. Shell Redirection in Practice

The shell's redirection operators are syntactic sugar that expand into file descriptor manipulation before any command executes. Understanding the precise mechanics clarifies why certain redirection patterns work and others do not.

### Output Redirection: >

When you type `command > file`, the shell parses the `>` token as an output redirection operator. The shell then:

1. Opens `file` for writing, creating it if necessary and truncating if it exists. This is equivalent to `open(file, O_WRONLY | O_CREAT | O_TRUNC, 0666)`.
2. Duplicates the resulting file descriptor onto descriptor 1 using `dup2()`.
3. Closes the temporary file descriptor (the one returned by `open()`).
4. Forks a child process and calls `execve()` to execute `command`.

The child process inherits file descriptor 1 pointing to `file`. When `command` writes to stdout, the bytes flow into the file. If the file already exists, `>` truncates it to zero bytes; the previous content is lost. This is a frequent source of accidental data loss: a mistyped redirection overwrites an existing file without warning.

### Append Redirection: >>

The `>>` operator appends to a file instead of truncating it. The shell opens the file with `O_WRONLY | O_CREAT | O_APPEND`. With `O_APPEND` set, every write operation automatically seeks to the end of the file before writing, regardless of the current file pointer. This guarantees that multiple processes writing to the same file with `>>` do not overwrite each other's data, provided the underlying filesystem supports atomic append operations (most modern filesystems do).

### Input Redirection: <

The `<` operator redirects stdin. When you type `command < file`, the shell opens `file` for reading and duplicates the descriptor onto file descriptor 0. The command then reads from `file` instead of the terminal.

### Error Redirection: 2>

The `2>` operator redirects stderr. When you type `command 2> errlog`, the shell opens `errlog` for writing and duplicates the descriptor onto file descriptor 2. Error messages from `command` flow into `errlog` instead of the terminal.

### Combining Output and Error: &>

The `&>` operator is shorthand for redirecting both stdout and stderr to the same file. `command &> file` is equivalent to `command > file 2>&1`. The `2>&1` syntax deserves careful explanation: it is a redirection of descriptor 2 (stderr) to descriptor 1 (stdout). At the point this redirection is processed, descriptor 1 already points to `file` (from the `> file` part), so descriptor 2 is duplicated to reference the same file. Both stdout and stderr now flow into `file`.

The order of redirection operators matters. Consider the difference between `command > file 2>&1` and `command 2>&1 > file`. In the first case, stdout is redirected to `file`, then stderr is redirected to follow stdout, so both go to `file`. In the second case, stderr is redirected to stdout (which still points to the terminal at that moment), then stdout is redirected to `file`. The result: stdout goes to `file`, but stderr still goes to the terminal. Careful attention to redirection order prevents subtle debugging puzzles.

### Here-Documents: <<

A here-document provides inline input to a command without creating a temporary file. The syntax `command << EOF` instructs the shell to read lines until it encounters a line containing only `EOF`, then feed those lines to `command`'s stdin. The shell creates a temporary pipe, writes the here-document content to the write end, duplicates the read end onto file descriptor 0 of the command, and executes the command.

```bash
cat << EOF
This is a here-document.
Multiple lines are allowed.
EOF
```

The shell writes the two content lines to a temporary pipe, then runs `cat` with stdin connected to that pipe. `cat` reads until EOF and prints the content.

## 4. File Descriptor Inheritance & Process Family Trees

When a process forks, the child inherits a copy of the parent's file descriptor table. Each entry in the child's table initially points to the same open file table entry as the parent's. This inheritance is the mechanism that enables shell pipelines and redirection.

Consider a simple pipeline: `producer | consumer`. The shell forks a child for `producer` and another for `consumer`. Before executing each command, the shell manipulates file descriptors:

```
Parent shell:
  pipe(pipefd)  // pipefd[0] = read end, pipefd[1] = write end

fork() for producer:
  child inherits pipefd[0] and pipefd[1]
  dup2(pipefd[1], 1)   // stdout -> write end
  close(pipefd[0])     // close read end
  close(pipefd[1])     // close duplicate
  execve("producer")

fork() for consumer:
  child inherits pipefd[0] and pipefd[1]
  dup2(pipefd[0], 0)   // stdin -> read end
  close(pipefd[1])     // close write end
  close(pipefd[0])     // close duplicate
  execve("consumer")

Parent shell:
  close(pipefd[0])     // close both ends in parent
  close(pipefd[1])
  wait()
```

After the shell closes both ends of the pipe, only the child processes hold open descriptors to it. When `producer` writes to stdout (descriptor 1), the bytes flow into the pipe. `consumer` reads from stdin (descriptor 0), receiving those bytes. When `producer` exits and closes descriptor 1, the pipe reaches EOF, signaling `consumer` to terminate its input loop.

A critical detail: if the parent shell did not close both ends of the pipe, the pipe would never reach EOF. `consumer` would block indefinitely waiting for data, because from its perspective, the pipe has at least one write end still open (in the parent shell's file descriptor table). This is a common source of subtle hangs in shell scripts that spawn background processes without carefully managing file descriptors.

File descriptors are inherited across `execve()` calls by default. When you call `execve()`, the kernel replaces the process image but preserves the file descriptor table. Any open descriptors remain open in the new process. This allows the shell to set up redirection before executing a command, and the command sees the redirected descriptors without explicitly requesting them. The close-on-exec flag, set with `fcntl(fd, F_SETFD, FD_CLOEXEC)`, changes this behavior: descriptors with this flag are automatically closed when `execve()` is called. This is useful for temporary descriptors that should not leak into child processes.

## 5. Advanced Redirection Patterns

### Process Substitution

Some shells (bash, zsh) support process substitution, a mechanism that treats the output of a command as a file. The syntax `<(command)` creates a temporary named pipe (FIFO), runs `command` with stdout connected to that pipe, and substitutes the pipe path into the command line. This allows programs that expect filenames to work with command output.

```bash
diff <(sort file1) <(sort file2)
```

This executes `sort file1` and `sort file2` with their outputs connected to temporary FIFOs, then passes those FIFO paths to `diff`. `diff` sees two filenames and opens them like regular files, unaware that it is reading from command output.

The shell creates the FIFOs in `/dev/fd/` (or a temporary directory on systems that do not support `/dev/fd/`), which means they are anonymous to the user and cleaned up automatically when no longer needed.

### File Descriptor Cloning

In some cases, you need to preserve the current value of a file descriptor before redirecting it, so you can restore it later. Duplicating the descriptor to a high-numbered slot preserves its state:

```bash
exec 3>&1        # Save stdout to fd 3
exec 1> /tmp/log # Redirect stdout to /tmp/log
command          # Writes to /tmp/log
exec 1>&3        # Restore stdout from fd 3
exec 3>&-        # Close fd 3
```

This pattern uses the shell's `exec` builtin to perform redirection in the current shell process (rather than in a subshell created for a command). After saving stdout to descriptor 3, subsequent commands see the redirected stdout. After restoring from descriptor 3, stdout flows back to the terminal.

### Multiplexing Output

To redirect a command's output to both a file and the terminal simultaneously, use the `tee` utility:

```bash
command | tee output.log
```

`tee` reads from stdin, writes each line to stdout and to the specified file. This allows you to see the output in real-time while also capturing it for later review.

## 6. Buffering & Synchronization

Buffering introduces a layer of indirection between your program's output and the actual disk or terminal. Understanding buffering modes and their implications is essential for writing correct programs.

### Buffering Modes in stdio

The C stdio library supports three buffering modes:

1. **Unbuffered**: Each `putchar()`, `printf()`, or `fputc()` call issues a system call immediately. No data accumulates in userspace. This guarantees that output appears on the destination immediately but incurs the performance cost of frequent context switches.

2. **Line buffered**: The library accumulates output in a userspace buffer until a newline character is encountered. When a newline appears, the library flushes the buffer with a single `write()` system call. This is the default for stdout when connected to a terminal. Line buffering balances performance (fewer system calls than unbuffered) with responsiveness (output appears after each line, making the program seem interactive).

3. **Fully buffered**: The library accumulates output until the buffer fills (typically 4096 or 8192 bytes) or the program explicitly flushes. This is the default for stdout when redirected to a file or pipe, and for all FILE streams opened to regular files. Full buffering minimizes system calls but delays output, which can be problematic for long-running programs or those that crash unexpectedly.

You can change the buffering mode of a FILE stream with `setvbuf()`:

```c
setvbuf(stream, NULL, _IOLBF, 0);   // Line buffering
setvbuf(stream, NULL, _IOFBF, 0);   // Full buffering
setvbuf(stream, NULL, _IONBF, 0);   // Unbuffered
```

The third parameter specifies the buffer size; passing 0 causes the library to allocate a default buffer.

### Flushing & Durability

Calling `fflush(stream)` forces the stdio library to write all buffered data to the underlying file descriptor with a `write()` system call. However, `fflush()` does not guarantee that data reaches the disk. The kernel may still buffer the data in the page cache, and a system crash before the page cache is written to disk will lose the data.

To guarantee durability, call `fsync(fd)` after `fflush()`. `fsync()` instructs the kernel to write all pending data for the file to the physical disk and wait for the operation to complete. This is more expensive than `fflush()` but guarantees that subsequent system crashes will not lose the data.

```c
fprintf(stream, "Critical data\n");
fflush(stream);
fsync(fileno(stream));  // Ensure data reaches disk
```

For performance-critical applications that do not require absolute durability, `fflush()` alone is sufficient. For applications handling important data, `fsync()` is worth the performance cost.

### Blocking & Non-Blocking I/O

By default, `read()` and `write()` on regular files and pipes are **blocking**: if no data is available to read, `read()` suspends the process until data arrives or the stream reaches EOF; if the write buffer is full, `write()` suspends until space becomes available. This blocking behavior simplifies programming but can cause unexpected delays.

For network sockets and other special files, you can set non-blocking mode with `fcntl()`:

```c
int flags = fcntl(fd, F_GETFL);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);
```

In non-blocking mode, `read()` returns immediately with 0 bytes if no data is available (returning 0 without setting errno), and `write()` returns immediately if the buffer is full, with the number of bytes actually written (which may be less than requested). This allows a program to multiplex I/O across multiple descriptors without blocking on any single one, though it complicates error handling and requires careful management of partial operations.

## 7. Practical Examples

### Example 1: Redirecting Errors to a Log File

A common pattern in shell scripts is to run a command, capture errors separately from normal output, and continue execution even if the command fails:

```bash
#!/bin/bash
command arg1 arg2 2> errors.log
if [ $? -ne 0 ]; then
  echo "Command failed. Errors logged to errors.log"
  cat errors.log
fi
```

The `2> errors.log` redirection sends stderr to a file while stdout remains on the terminal. The `$?` variable contains the exit status of the last command. If non-zero, the command failed, and we print an explanation and the error log.

### Example 2: Duplicating Output to Multiple Destinations

To send output to both a file and the terminal, use `tee`:

```bash
make 2>&1 | tee build.log | grep -i error
```

This runs `make`, combines stdout and stderr with `2>&1`, pipes to `tee`, which writes all data to both `build.log` and its own stdout, and finally pipes to `grep` to highlight errors. You see errors on the terminal and have a complete log in `build.log`.

### Example 3: Using /dev/null

The special file `/dev/null` is a read source of EOF and a write sink that discards all input. Redirecting stderr to `/dev/null` silences error messages:

```bash
command 2> /dev/null
```

Similarly, redirecting stdout to `/dev/null` discards output while allowing errors to flow to the terminal.

### Example 4: Closing Descriptors

To explicitly close a file descriptor in a shell, use `exec` with the close syntax:

```bash
exec 3>&-    # Close file descriptor 3
exec 1>&-    # Close stdout (rarely useful)
```

Closing a descriptor prevents the file from receiving any further input from the current shell or its children. This is useful for cleanup but rarely necessary in practice.

### Example 5: Parallel Redirection in C

A C program can coordinate redirection of multiple child processes:

```c
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>

int main() {
    int pipefd[2];
    pipe(pipefd);
    
    pid_t pid = fork();
    if (pid == 0) {
        // Child: producer
        close(pipefd[0]);           // Close read end
        dup2(pipefd[1], STDOUT_FILENO);
        close(pipefd[1]);
        execlp("echo", "echo", "Hello from producer", NULL);
    } else {
        // Parent: consumer
        close(pipefd[1]);           // Close write end
        dup2(pipefd[0], STDIN_FILENO);
        close(pipefd[0]);
        execlp("cat", "cat", NULL);
    }
    
    return 0;
}
```

This program forks two processes connected by a pipe. The parent and child swap roles after `fork()`: the child becomes the producer (using `execlp()` to run `echo`), and the parent becomes the consumer (using `execlp()` to run `cat`). Both close their unused ends of the pipe before calling `execlp()`, which replaces their process images. The result: `cat` reads the output of `echo` through the pipe.

## 8. Debugging & Troubleshooting

### Inspecting Open File Descriptors

On Linux, `/proc/self/fd/` contains symbolic links to all open file descriptors of the current process:

```bash
ls -l /proc/self/fd/
```

Each symlink shows the file or device that the descriptor references. For a running process, replace `self` with the process ID:

```bash
ls -l /proc/1234/fd/
```

This reveals which files a process has open, their modes, and their current seek positions (displayed as part of the symlink target on some systems).

The `lsof` utility provides a more user-friendly view:

```bash
lsof -p 1234
```

This lists all open files (including sockets and pipes) for process 1234, along with file descriptors, access modes, and seek positions.

### Strace for I/O System Calls

The `strace` utility traces system calls and their arguments:

```bash
strace -e openat,read,write,dup2,pipe command arg
```

This restricts output to I/O-related system calls, showing exactly when a command opens files, reads, writes, or duplicates descriptors. The `-o` flag writes output to a file for later analysis.

### Identifying Broken Pipes

A program that writes to a closed pipe receives SIGPIPE and terminates. To handle this gracefully, catch SIGPIPE:

```c
#include <signal.h>

signal(SIGPIPE, SIG_IGN);
```

Ignoring SIGPIPE allows the program to continue after a `write()` to a closed pipe returns -1 with EPIPE. This is useful for programs like `grep` or `head` that may exit early, breaking pipes downstream.

### Testing Buffering Behavior

To observe buffering behavior, run a long-lived command and redirect its output:

```bash
(yes "line"; sleep 10) > output.txt &
tail -f output.txt
```

The `yes` command loops indefinitely, printing a line on each iteration. With line buffering, each line appears in `output.txt` immediately. If buffering changes, output may accumulate and appear in chunks.

---

This chapter has surveyed the mechanisms of I/O redirection, file descriptors, and streams from first principles through practical application. The Unix design philosophy of treating everything as a file, combined with the elegant file descriptor abstraction, enables programs to compose seamlessly through pipes and redirection. Mastery of these concepts is foundational to proficient systems programming and shell scripting.
