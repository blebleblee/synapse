# Lesson 3: Interprocess Communication and I/O

## 1. First-Principles Intuition & Invariants

Modern operating systems exist to mediate access to shared hardware resources among competing processes. When Dennis Ritchie and Ken Thompson designed Unix at Bell Labs in the early 1970s, they established a foundational abstraction that has endured for five decades: **everything is a file**. This deceptively simple principle means that whether a process reads from disk, writes to a network socket, communicates with another process through a pipe, or manipulates a device driver, the same fundamental system call interface applies. The `read()` and `write()` system calls operate uniformly across terminals, disk files, sockets, and inter-process pipes, creating a compositional architecture where data flows through uniform channels regardless of the underlying transport mechanism.

At the heart of this abstraction lies the **file descriptor**, an integer handle returned by the kernel that represents an open file description in the process's file descriptor table. When a process starts, it inherits three standard descriptors: `0` for standard input, `1` for standard output, and `2` for standard error. These descriptors are not mere conventions but concrete entries in the kernel's per-process file descriptor array, each pointing to a file description structure in kernel memory that tracks the current file offset, access mode flags, and a reference to the underlying file object. This indirection through multiple layers—file descriptor to file description to inode or socket structure—enables the kernel to implement sophisticated resource sharing, redirection, and duplication semantics.

The genius of Unix I/O architecture emerges when we recognize that interprocess communication (IPC) mechanisms are not bolted onto the system as afterthoughts but are natural extensions of the file descriptor abstraction. A pipe is simply a kernel buffer with two file descriptors attached: one for reading and one for writing. A Unix domain socket extends this concept with bidirectional communication and credential passing. Network sockets map TCP streams and UDP datagrams onto the same file descriptor interface, allowing the same `read()`, `write()`, and `select()` calls to work seamlessly whether data arrives from a local pipe or a remote TCP connection spanning continents.

The fundamental invariant governing all I/O operations is **atomicity at the system call boundary**. When a process invokes `read()` or `write()`, the kernel guarantees that the operation either completes in its entirety or returns an error without partial state corruption. For pipes and sockets, writes smaller than `PIPE_BUF` bytes (typically 4096 bytes on Linux) are atomic, meaning concurrent writers cannot interleave their data within a single logical message. This atomicity guarantee is not a performance optimization but a correctness requirement: without it, shell pipelines like `ps aux | grep ssh | awk '{print $2}'` would produce corrupted output as multiple processes race to write into the same pipe.

The second invariant concerns **blocking semantics**. By default, I/O operations on file descriptors exhibit blocking behavior: a `read()` call on an empty pipe or socket suspends the calling process until data arrives, and a `write()` to a full pipe blocks until buffer space becomes available. This synchronous model simplifies programming by making I/O appear sequential, but it introduces a fundamental tension: a process blocked on one file descriptor cannot simultaneously service other descriptors, creating the need for multiplexing mechanisms that allow a single thread to monitor multiple I/O sources concurrently.

The third invariant addresses **signal-driven asynchrony**. Signals are software interrupts that the kernel delivers to processes, allowing asynchronous notification of events ranging from timer expirations (`SIGALRM`) to child process termination (`SIGCHLD`) to I/O readiness (`SIGIO`). Signals interrupt the normal flow of execution, potentially arriving while a system call is in progress, and this asynchronous nature introduces profound complexity: signal handlers execute in an arbitrary context with minimal kernel state, must be reentrant, and can only safely invoke a restricted set of async-signal-safe functions. The interaction between signals and blocking I/O creates one of systems programming's classic race conditions: a signal can arrive after a process checks a condition but before it blocks on I/O, causing the process to sleep indefinitely despite the signal having already been delivered.

Understanding I/O multiplexing requires grasping why the original blocking model breaks down at scale. Consider a network server handling thousands of concurrent clients. A naive approach spawning one thread per connection quickly exhausts system resources, as each thread consumes kernel stack space (typically 8 KB) and scheduler state. The alternative—non-blocking I/O combined with polling—allows a single thread to service many connections but introduces a new problem: how does the thread efficiently determine which file descriptors are ready for I/O without busy-waiting and burning CPU cycles? The answer lies in kernel-provided event notification mechanisms that allow processes to register interest in I/O events and block until one or more descriptors become ready.

The evolution from `select()` to `poll()` to `epoll()` reflects a progression toward scalability. The `select()` system call, inherited from BSD Unix, operates on fixed-size bitmaps of file descriptors and requires the kernel to scan all registered descriptors on every invocation—an **O(n)** operation that becomes prohibitively expensive as the descriptor count grows. The `poll()` interface improves upon this by using a variable-length array of `pollfd` structures, removing the fixed descriptor limit, but still requires **O(n)** kernel-side scanning. Linux's `epoll` subsystem, introduced in kernel 2.5.44, solves this scalability problem through an event-driven architecture where the kernel maintains a red-black tree of registered descriptors and delivers only those descriptors that have become ready, achieving **O(1)** event delivery per ready descriptor.

The transition from blocking to non-blocking I/O fundamentally changes the programming model. In blocking mode, I/O operations appear synchronous and sequential: the thread of control naturally waits at each I/O point until completion. Non-blocking I/O inverts this relationship, making I/O operations return immediately with either success, partial completion, or an `EAGAIN` error indicating that the operation would block. This inversion forces applications to maintain explicit state machines, tracking which I/O operations are in progress and what logical state each connection occupies. The reward for this complexity is scalability: a single-threaded event loop can efficiently multiplex thousands of I/O sources, yielding the architecture powering high-performance servers like nginx, Redis, and Node.js.

## 2. Core Architecture & Mechanics

### Pipe Internals and Anonymous Communication

A pipe represents the simplest form of unidirectional IPC, implemented in the kernel as a circular buffer with separate read and write pointers. When a process calls `pipe(int pipefd[2])`, the kernel allocates a new pipe buffer (typically 16 pages or 64 KB on Linux), creates two file descriptions—one configured for reading and one for writing—and assigns them to the lowest available file descriptor numbers in the calling process's descriptor table. The returned `pipefd[0]` is the read end, and `pipefd[1]` is the write end.

```c
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    int pipefd[2];
    pid_t child_pid;
    char write_msg[] = "Message from parent process";
    char read_buf[128];
    
    if (pipe(pipefd) == -1) {
        perror("pipe");
        exit(EXIT_FAILURE);
    }
    
    child_pid = fork();
    if (child_pid == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    }
    
    if (child_pid == 0) {
        /* Child process: reader */
        close(pipefd[1]);  /* Close unused write end */
        
        ssize_t nbytes = read(pipefd[0], read_buf, sizeof(read_buf) - 1);
        if (nbytes == -1) {
            perror("read");
            exit(EXIT_FAILURE);
        }
        
        read_buf[nbytes] = '\0';
        printf("Child received: %s\n", read_buf);
        close(pipefd[0]);
        exit(EXIT_SUCCESS);
    } else {
        /* Parent process: writer */
        close(pipefd[0]);  /* Close unused read end */
        
        if (write(pipefd[1], write_msg, strlen(write_msg)) == -1) {
            perror("write");
            exit(EXIT_FAILURE);
        }
        
        close(pipefd[1]);
        wait(NULL);  /* Wait for child to complete */
    }
    
    return 0;
}
```

The critical detail in this code is the explicit closure of unused pipe ends in each process. After `fork()`, both parent and child possess copies of both file descriptors, but standard practice dictates that the writer closes the read end and the reader closes the write end. This discipline is not merely stylistic—it ensures proper end-of-file semantics. A `read()` on a pipe returns zero (EOF) only when all write ends are closed. If the reader retains an open write descriptor, it prevents itself from ever receiving EOF, creating a deadlock where the reader blocks indefinitely waiting for data that will never arrive.

The kernel's pipe implementation employs a lock-free ring buffer structure for efficiency. The write pointer advances as data is written, and the read pointer advances as data is consumed, with the buffer wrapping around circularly. When the buffer fills completely, subsequent `write()` calls block (or return `EAGAIN` in non-blocking mode) until the reader consumes enough data to free space. Conversely, when the buffer is empty, `read()` calls block until a writer produces data. The kernel tracks the number of bytes available using atomic operations, avoiding the need for heavyweight locking in the common case of a single reader and single writer.

The atomic write guarantee for `PIPE_BUF`-sized writes is implemented through a size check in the kernel's pipe write path. If the write size exceeds `PIPE_BUF`, the kernel may break the write into multiple chunks, allowing other writers to interleave their data. This creates a correctness hazard for applications that require message boundaries, necessitating either explicit message framing (length prefixes or delimiters) or restriction to writes smaller than `PIPE_BUF`.

### Unix Domain Sockets and Credential Passing

While pipes provide unidirectional byte streams, Unix domain sockets generalize IPC to support bidirectional communication, datagram semantics, and ancillary data transfer including file descriptors and process credentials. Unix domain sockets use filesystem paths as addresses, creating a namespace that filesystem permissions naturally govern. The kernel implements Unix sockets through dedicated socket buffers rather than shared file buffers, providing higher performance than network sockets for local communication by avoiding the TCP/IP stack overhead.

```c
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SOCKET_PATH "/tmp/demo_socket"

void run_server(void) {
    int listen_fd, conn_fd;
    struct sockaddr_un server_addr, client_addr;
    socklen_t client_len;
    char buffer[256];
    
    listen_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    unlink(SOCKET_PATH);  /* Remove any existing socket file */
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, SOCKET_PATH, sizeof(server_addr.sun_path) - 1);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    
    if (listen(listen_fd, 5) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on %s\n", SOCKET_PATH);
    
    client_len = sizeof(client_addr);
    conn_fd = accept(listen_fd, (struct sockaddr *)&client_addr, &client_len);
    if (conn_fd == -1) {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    
    ssize_t nread = read(conn_fd, buffer, sizeof(buffer) - 1);
    if (nread > 0) {
        buffer[nread] = '\0';
        printf("Server received: %s\n", buffer);
    }
    
    close(conn_fd);
    close(listen_fd);
    unlink(SOCKET_PATH);
}

void run_client(void) {
    int sock_fd;
    struct sockaddr_un server_addr;
    char message[] = "Hello from client";
    
    sock_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, SOCKET_PATH, sizeof(server_addr.sun_path) - 1);
    
    if (connect(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("connect");
        exit(EXIT_FAILURE);
    }
    
    if (write(sock_fd, message, strlen(message)) == -1) {
        perror("write");
        exit(EXIT_FAILURE);
    }
    
    close(sock_fd);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s [server|client]\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    if (strcmp(argv[1], "server") == 0) {
        run_server();
    } else if (strcmp(argv[1], "client") == 0) {
        sleep(1);  /* Give server time to start */
        run_client();
    } else {
        fprintf(stderr, "Invalid argument: %s\n", argv[1]);
        exit(EXIT_FAILURE);
    }
    
    return 0;
}
```

The power of Unix domain sockets extends beyond simple data transfer to **file descriptor passing**, a mechanism where one process can transfer an open file descriptor to another process through an ancillary message carried alongside regular socket data. This enables sophisticated privilege separation architectures where a privileged parent opens restricted resources (raw sockets, device files) and passes the descriptors to unprivileged children that perform actual I/O without holding dangerous capabilities.

```c
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>

void send_fd(int socket, int fd_to_send) {
    struct msghdr msg = {0};
    struct cmsghdr *cmsg;
    char buf[CMSG_SPACE(sizeof(int))];
    char dummy = 'X';
    struct iovec io = {
        .iov_base = &dummy,
        .iov_len = 1
    };
    
    msg.msg_iov = &io;
    msg.msg_iovlen = 1;
    msg.msg_control = buf;
    msg.msg_controllen = sizeof(buf);
    
    cmsg = CMSG_FIRSTHDR(&msg);
    cmsg->cmsg_level = SOL_SOCKET;
    cmsg->cmsg_type = SCM_RIGHTS;
    cmsg->cmsg_len = CMSG_LEN(sizeof(int));
    
    memcpy(CMSG_DATA(cmsg), &fd_to_send, sizeof(int));
    
    if (sendmsg(socket, &msg, 0) == -1) {
        perror("sendmsg");
        exit(EXIT_FAILURE);
    }
}

int recv_fd(int socket) {
    struct msghdr msg = {0};
    struct cmsghdr *cmsg;
    char buf[CMSG_SPACE(sizeof(int))];
    char dummy;
    struct iovec io = {
        .iov_base = &dummy,
        .iov_len = 1
    };
    int received_fd;
    
    msg.msg_iov = &io;
    msg.msg_iovlen = 1;
    msg.msg_control = buf;
    msg.msg_controllen = sizeof(buf);
    
    if (recvmsg(socket, &msg, 0) == -1) {
        perror("recvmsg");
        exit(EXIT_FAILURE);
    }
    
    cmsg = CMSG_FIRSTHDR(&msg);
    if (cmsg == NULL || cmsg->cmsg_type != SCM_RIGHTS) {
        fprintf(stderr, "Failed to receive file descriptor\n");
        exit(EXIT_FAILURE);
    }
    
    memcpy(&received_fd, CMSG_DATA(cmsg), sizeof(int));
    return received_fd;
}
```

When a file descriptor passes through `sendmsg()` with `SCM_RIGHTS`, the kernel does not simply copy the integer value but performs a deep duplication: it increments the reference count on the underlying file description and allocates a new file descriptor in the recipient's descriptor table that points to the same kernel file structure. The recipient can then use this descriptor as if it had opened the file itself, inheriting the current file offset, access mode, and all other state. This mechanism underpins systemd's socket activation, where systemd opens listening sockets and passes them to service processes, allowing services to run without `CAP_NET_BIND_SERVICE` capabilities.

### Signal Mechanics and Asynchronous Notification

Signals represent the operating system's mechanism for asynchronous event notification, predating threads and providing a lightweight alternative to process creation for handling asynchronous events. When the kernel delivers a signal to a process, it interrupts the process's current execution context, saves the CPU register state onto the stack, and invokes the registered signal handler with a synthetic call frame. After the handler returns, the kernel restores the original register state and resumes execution as if the signal had never occurred—at least in the ideal case.

The complexity of signal handling arises from the asynchronous nature of delivery. A signal can arrive at any moment, including during a system call, and the interaction between signals and blocking operations creates subtle race conditions. Consider a process that installs a `SIGALRM` handler, sets an alarm, then calls `read()` on a pipe. If the alarm fires while the process is blocked in `read()`, the kernel has two choices: allow the signal handler to run and return `EINTR` (interrupted system call) from `read()`, or automatically restart the system call after the handler completes. This behavior is controlled by the `SA_RESTART` flag passed to `sigaction()`, and choosing incorrectly can cause application logic to break.

```c
#include <signal.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

volatile sig_atomic_t alarm_fired = 0;

void alarm_handler(int signum) {
    (void)signum;
    alarm_fired = 1;
}

int main(void) {
    struct sigaction sa;
    char buffer[128];
    ssize_t nread;
    
    /* Install signal handler without SA_RESTART */
    sa.sa_handler = alarm_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;  /* No SA_RESTART: read() will return EINTR */
    
    if (sigaction(SIGALRM, &sa, NULL) == -1) {
        perror("sigaction");
        exit(EXIT_FAILURE);
    }
    
    alarm(2);  /* Fire alarm in 2 seconds */
    
    printf("Reading from stdin (alarm will interrupt after 2s)...\n");
    nread = read(STDIN_FILENO, buffer, sizeof(buffer));
    
    if (nread == -1) {
        if (errno == EINTR) {
            printf("read() interrupted by signal\n");
            if (alarm_fired) {
                printf("SIGALRM was delivered\n");
            }
        } else {
            perror("read");
            exit(EXIT_FAILURE);
        }
    } else {
        buffer[nread] = '\0';
        printf("Read %zd bytes: %s\n", nread, buffer);
    }
    
    return 0;
}
```

The `sig_atomic_t` type used for the `alarm_fired` flag represents the only type that the C standard guarantees can be safely written from a signal handler and read from normal code without data races. On most modern architectures, this corresponds to aligned integer types that the CPU can load and store with single instructions. Any more complex data structure risks corruption if the signal interrupts a multi-instruction update sequence in progress.

The limitation on async-signal-safe functions stems from reentrancy concerns. Functions like `printf()` and `malloc()` maintain internal state protected by locks or data structures that assume non-reentrant access. If a signal interrupts `malloc()` while it is manipulating the heap, and the signal handler calls `malloc()` again, the heap allocator's internal data structures may become corrupted, leading to crashes or silent memory corruption. The POSIX standard defines a small set of functions guaranteed to be async-signal-safe, including `write()`, `_exit()`, and signal manipulation functions, but conspicuously excluding `printf()` and nearly all standard library functions.

Modern signal delivery uses **real-time signal queuing** on Linux through signals `SIGRTMIN` through `SIGRTMAX`. Unlike traditional signals which are binary flags (delivered or not delivered), real-time signals queue multiple deliveries and preserve associated data via `sigqueue()`. This enables applications to use signals as a lightweight message-passing mechanism, though the buffer space for queued signals is limited by the `RLIMIT_SIGPENDING` resource limit.

### File Descriptor Semantics and Duplication

The relationship between file descriptors, file descriptions, and file objects forms a three-level indirection that enables Unix's flexible I/O redirection. A file descriptor is simply an index into a process's file descriptor table, a per-process array of pointers. Each entry points to a file description—a kernel structure that tracks the current file offset, status flags (`O_APPEND`, `O_NONBLOCK`), and a reference to the underlying file object (inode for files, socket structure for sockets). Multiple file descriptors can point to the same file description (via `dup()` or `dup2()`), and multiple file descriptions can reference the same file object (when different processes open the same file).

```c
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    int fd1, fd2, fd3;
    off_t offset;
    char write_buf[] = "Hello";
    char read_buf[16];
    
    /* Open file and get first descriptor */
    fd1 = open("test.txt", O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd1 == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }
    
    /* Duplicate fd1 to fd2 - both share the same file description */
    fd2 = dup(fd1);
    if (fd2 == -1) {
        perror("dup");
        exit(EXIT_FAILURE);
    }
    
    /* Open the same file again - separate file description */
    fd3 = open("test.txt", O_RDWR);
    if (fd3 == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }
    
    /* Write through fd1 */
    write(fd1, write_buf, strlen(write_buf));
    
    /* Check offset on fd2 - should be advanced because fd1 and fd2 share file description */
    offset = lseek(fd2, 0, SEEK_CUR);
    printf("Offset via fd2 (dup'd from fd1): %ld\n", (long)offset);
    
    /* Check offset on fd3 - should still be 0 because it's a separate file description */
    offset = lseek(fd3, 0, SEEK_CUR);
    printf("Offset via fd3 (separate open): %ld\n", (long)offset);
    
    /* Read from fd3 to verify file content */
    lseek(fd3, 0, SEEK_SET);
    ssize_t nread = read(fd3, read_buf, sizeof(read_buf) - 1);
    read_buf[nread] = '\0';
    printf("Content read via fd3: %s\n", read_buf);
    
    close(fd1);
    close(fd2);
    close(fd3);
    unlink("test.txt");
    
    return 0;
}
```

The distinction between `dup()` and separate `open()` calls determines whether file offset changes are visible across descriptors. When `dup()` or `dup2()` creates a new descriptor, both descriptors point to the same file description, so operations like `lseek()` or `write()` that modify the file offset affect both descriptors. In contrast, separate `open()` calls create independent file descriptions with their own file offsets, allowing concurrent access without interference. This semantic difference is crucial for shell redirection: when a shell sets up a pipeline like `cmd1 | cmd2`, it uses `dup2()` to redirect standard output of `cmd1` and standard input of `cmd2` to the pipe, preserving the shared offset semantics needed for sequential data flow.

The `dup2()` call provides atomic replacement of a target descriptor, closing the old descriptor if it exists and atomically assigning the new descriptor to the specified number. This atomicity is essential for thread-safe I/O redirection, avoiding race conditions where another thread might allocate the target descriptor number between a close and a subsequent dup operation.

### Blocking, Non-Blocking, and Asynchronous I/O

Every file descriptor carries status flags that control its blocking behavior, settable through `fcntl(fd, F_SETFL, O_NONBLOCK)`. In blocking mode (the default), I/O operations suspend the calling thread until they can complete or an error occurs. A `read()` on an empty socket blocks until data arrives, and a `write()` to a full socket buffer blocks until space becomes available. The kernel places the thread on a wait queue associated with the file object and marks the thread as sleeping, allowing other runnable threads to execute.

Non-blocking mode inverts this behavior: I/O operations return immediately with either success or `EAGAIN`/`EWOULDBLOCK` if the operation cannot complete without blocking. This mode requires applications to explicitly retry failed operations, typically within an event loop that uses multiplexing to wait for I/O readiness. The kernel maintains readiness state for each file description, tracking whether the receive buffer contains data (`POLLIN`) or the send buffer has space (`POLLOUT`), and the multiplexing system calls query this state efficiently.

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) {
        perror("fcntl F_GETFL");
        return -1;
    }
    if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
        perror("fcntl F_SETFL");
        return -1;
    }
    return 0;
}

int main(void) {
    int listen_fd, conn_fd;
    struct sockaddr_in server_addr;
    char buffer[4096];
    ssize_t total_read = 0;
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(8080);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    
    if (listen(listen_fd, 10) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port 8080\n");
    
    conn_fd = accept(listen_fd, NULL, NULL);
    if (conn_fd == -1) {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    
    if (set_nonblocking(conn_fd) == -1) {
        exit(EXIT_FAILURE);
    }
    
    printf("Connection accepted, reading in non-blocking mode\n");
    
    /* Read loop with explicit EAGAIN handling */
    while (1) {
        ssize_t nread = read(conn_fd, buffer, sizeof(buffer));
        
        if (nread > 0) {
            total_read += nread;
            printf("Read %zd bytes (total: %zd)\n", nread, total_read);
        } else if (nread == 0) {
            printf("Connection closed by client\n");
            break;
        } else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                printf("No data available, would block\n");
                usleep(100000);  /* Sleep 100ms before retry */
                continue;
            } else {
                perror("read");
                break;
            }
        }
    }
    
    close(conn_fd);
    close(listen_fd);
    
    return 0;
}
```

The busy-wait loop in this example illustrates the inefficiency of pure non-blocking I/O without multiplexing: the process repeatedly calls `read()` and sleeps, wasting CPU cycles checking for readiness. Production systems eliminate this waste by using multiplexing primitives that leverage kernel-side readiness tracking, allowing threads to sleep until the kernel notifies them that I/O operations can proceed without blocking.

True asynchronous I/O, as provided by POSIX AIO and Linux's `io_uring` interface, goes beyond non-blocking semantics by allowing I/O operations to complete entirely in the background. Rather than returning `EAGAIN` when an operation would block, asynchronous I/O accepts the operation and returns control immediately, later delivering completion notifications through signals, callbacks, or completion queue polling. The `io_uring` interface introduced in Linux 5.1 provides a high-performance asynchronous I/O framework using shared memory ring buffers for submission and completion queues, eliminating system call overhead for the common path.

```c
#include <liburing.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define QUEUE_DEPTH 32
#define BLOCK_SIZE 4096

int main(int argc, char *argv[]) {
    struct io_uring ring;
    struct io_uring_sqe *sqe;
    struct io_uring_cqe *cqe;
    int fd;
    char *buffer;
    int ret;
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    /* Initialize io_uring with queue depth */
    ret = io_uring_queue_init(QUEUE_DEPTH, &ring, 0);
    if (ret < 0) {
        fprintf(stderr, "io_uring_queue_init: %s\n", strerror(-ret));
        exit(EXIT_FAILURE);
    }
    
    fd = open(argv[1], O_RDONLY);
    if (fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }
    
    buffer = malloc(BLOCK_SIZE);
    if (!buffer) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    
    /* Get submission queue entry */
    sqe = io_uring_get_sqe(&ring);
    if (!sqe) {
        fprintf(stderr, "Failed to get SQE\n");
        exit(EXIT_FAILURE);
    }
    
    /* Prepare read operation */
    io_uring_prep_read(sqe, fd, buffer, BLOCK_SIZE, 0);
    io_uring_sqe_set_data(sqe, buffer);  /* Associate buffer with request */
    
    /* Submit the operation */
    ret = io_uring_submit(&ring);
    if (ret < 0) {
        fprintf(stderr, "io_uring_submit: %s\n", strerror(-ret));
        exit(EXIT_FAILURE);
    }
    
    /* Wait for completion */
    ret = io_uring_wait_cqe(&ring, &cqe);
    if (ret < 0) {
        fprintf(stderr, "io_uring_wait_cqe: %s\n", strerror(-ret));
        exit(EXIT_FAILURE);
    }
    
    if (cqe->res < 0) {
        fprintf(stderr, "Async read failed: %s\n", strerror(-cqe->res));
    } else {
        printf("Read %d bytes asynchronously\n", cqe->res);
        buffer[cqe->res] = '\0';
        printf("Content: %s\n", buffer);
    }
    
    io_uring_cqe_seen(&ring, cqe);
    
    free(buffer);
    close(fd);
    io_uring_queue_exit(&ring);
    
    return 0;
}
```

The `io_uring` model eliminates the context switching overhead of traditional blocking I/O and the system call overhead of non-blocking polling loops by allowing applications to batch multiple I/O operations in a single submission and receive multiple completions without repeated system calls. The shared memory ring buffers enable the kernel and application to communicate without crossing the user-kernel boundary, and the support for operation chaining (where one operation can automatically trigger another upon completion) enables complex I/O patterns with minimal overhead.

### I/O Multiplexing: select, poll, and epoll

The `select()` system call, inherited from 4.2BSD, provides the foundational API for I/O multiplexing. It accepts three file descriptor sets (readable, writable, exceptional conditions), a timeout, and blocks until at least one descriptor becomes ready or the timeout expires. The descriptor sets are bitmaps with each bit representing one file descriptor, limiting `select()` to monitoring at most `FD_SETSIZE` descriptors (typically 1024).

```c
#include <sys/select.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#define MAX_CLIENTS 10
#define PORT 8080

int main(void) {
    int listen_fd, max_fd;
    int client_fds[MAX_CLIENTS];
    fd_set read_fds, master_fds;
    struct sockaddr_in server_addr;
    char buffer[1024];
    
    /* Initialize client fd array */
    for (int i = 0; i < MAX_CLIENTS; i++) {
        client_fds[i] = -1;
    }
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    
    if (listen(listen_fd, 10) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d\n", PORT);
    
    FD_ZERO(&master_fds);
    FD_SET(listen_fd, &master_fds);
    max_fd = listen_fd;
    
    while (1) {
        read_fds = master_fds;
        
        if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) == -1) {
            perror("select");
            exit(EXIT_FAILURE);
        }
        
        /* Check listening socket for new connections */
        if (FD_ISSET(listen_fd, &read_fds)) {
            int new_fd = accept(listen_fd, NULL, NULL);
            if (new_fd == -1) {
                perror("accept");
                continue;
            }
            
            int slot = -1;
            for (int i = 0; i < MAX_CLIENTS; i++) {
                if (client_fds[i] == -1) {
                    client_fds[i] = new_fd;
                    slot = i;
                    break;
                }
            }
            
            if (slot == -1) {
                printf("Maximum clients reached, closing connection\n");
                close(new_fd);
            } else {
                FD_SET(new_fd, &master_fds);
                if (new_fd > max_fd) {
                    max_fd = new_fd;
                }
                printf("New client connected on fd %d\n", new_fd);
            }
        }
        
        /* Check client sockets for data */
        for (int i = 0; i < MAX_CLIENTS; i++) {
            int fd = client_fds[i];
            if (fd == -1) continue;
            
            if (FD_ISSET(fd, &read_fds)) {
                ssize_t nread = read(fd, buffer, sizeof(buffer) - 1);
                if (nread > 0) {
                    buffer[nread] = '\0';
                    printf("Client fd %d: %s\n", fd, buffer);
                } else {
                    if (nread == 0) {
                        printf("Client fd %d disconnected\n", fd);
                    } else {
                        perror("read");
                    }
                    close(fd);
                    FD_CLR(fd, &master_fds);
                    client_fds[i] = -1;
                }
            }
        }
    }
    
    close(listen_fd);
    return 0;
}
```

The `select()` implementation suffers from two fundamental performance problems. First, the descriptor sets must be copied from user space to kernel space on every call, an **O(n)** operation where **n** is the value of the highest descriptor plus one. Second, the kernel must scan all descriptors in the sets to determine which are ready, another **O(n)** operation. For a server handling thousands of connections where only a few become ready each iteration, `select()` wastes massive CPU time scanning dormant descriptors.

The `poll()` system call addresses `select()`'s fixed size limit by accepting a variable-length array of `pollfd` structures, each specifying a descriptor and the events of interest (readable, writable, error). The kernel populates a `revents` field in each structure indicating which events actually occurred. While `poll()` removes the descriptor count limit, it still requires **O(n)** kernel-side scanning on each call, failing to solve the fundamental scalability problem.

```c
#include <poll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_CLIENTS 1000
#define PORT 8080

int main(void) {
    int listen_fd;
    struct pollfd fds[MAX_CLIENTS + 1];
    int nfds = 1;
    struct sockaddr_in server_addr;
    char buffer[1024];
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    
    if (listen(listen_fd, 10) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d using poll()\n", PORT);
    
    fds[0].fd = listen_fd;
    fds[0].events = POLLIN;
    
    while (1) {
        int ret = poll(fds, nfds, -1);
        if (ret == -1) {
            perror("poll");
            exit(EXIT_FAILURE);
        }
        
        /* Check listening socket */
        if (fds[0].revents & POLLIN) {
            int new_fd = accept(listen_fd, NULL, NULL);
            if (new_fd == -1) {
                perror("accept");
                continue;
            }
            
            if (nfds < MAX_CLIENTS + 1) {
                fds[nfds].fd = new_fd;
                fds[nfds].events = POLLIN;
                nfds++;
                printf("Client connected, total clients: %d\n", nfds - 1);
            } else {
                printf("Maximum clients reached\n");
                close(new_fd);
            }
        }
        
        /* Check client sockets */
        for (int i = 1; i < nfds; i++) {
            if (fds[i].revents & POLLIN) {
                ssize_t nread = read(fds[i].fd, buffer, sizeof(buffer) - 1);
                if (nread > 0) {
                    buffer[nread] = '\0';
                    printf("Client fd %d: %s\n", fds[i].fd, buffer);
                } else {
                    if (nread == 0) {
                        printf("Client fd %d disconnected\n", fds[i].fd);
                    } else {
                        perror("read");
                    }
                    close(fds[i].fd);
                    fds[i] = fds[nfds - 1];  /* Swap with last element */
                    nfds--;
                    i--;  /* Recheck this index */
                }
            }
        }
    }
    
    close(listen_fd);
    return 0;
}
```

Linux's `epoll` API, introduced to solve the scalability crisis, fundamentally changes the multiplexing model from stateless to stateful. Instead of passing the entire descriptor set on each call, applications create an `epoll` instance with `epoll_create1()`, register interest in specific descriptors using `epoll_ctl()`, and retrieve ready descriptors with `epoll_wait()`. The kernel maintains a red-black tree of monitored descriptors and uses callback hooks in the socket and file code to efficiently track readiness state. When a descriptor becomes ready, the kernel adds it to a ready list, allowing `epoll_wait()` to return only the ready descriptors in **O(1)** time per ready descriptor, regardless of the total number of monitored descriptors.

```c
#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#define MAX_EVENTS 64
#define PORT 8080

int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int main(void) {
    int listen_fd, epoll_fd;
    struct sockaddr_in server_addr;
    struct epoll_event ev, events[MAX_EVENTS];
    char buffer[1024];
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    
    if (set_nonblocking(listen_fd) == -1) {
        perror("set_nonblocking");
        exit(EXIT_FAILURE);
    }
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    
    if (listen(listen_fd, SOMAXCONN) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) {
        perror("epoll_create1");
        exit(EXIT_FAILURE);
    }
    
    ev.events = EPOLLIN;
    ev.data.fd = listen_fd;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, listen_fd, &ev) == -1) {
        perror("epoll_ctl: listen_fd");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d using epoll\n", PORT);
    
    while (1) {
        int nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);
        if (nfds == -1) {
            perror("epoll_wait");
            exit(EXIT_FAILURE);
        }
        
        for (int i = 0; i < nfds; i++) {
            if (events[i].data.fd == listen_fd) {
                /* Accept new connections */
                while (1) {
                    int conn_fd = accept(listen_fd, NULL, NULL);
                    if (conn_fd == -1) {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) {
                            break;  /* All connections processed */
                        } else {
                            perror("accept");
                            break;
                        }
                    }
                    
                    if (set_nonblocking(conn_fd) == -1) {
                        close(conn_fd);
                        continue;
                    }
                    
                    ev.events = EPOLLIN | EPOLLET;  /* Edge-triggered */
                    ev.data.fd = conn_fd;
                    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, conn_fd, &ev) == -1) {
                        perror("epoll_ctl: conn_fd");
                        close(conn_fd);
                        continue;
                    }
                    
                    printf("New client connected on fd %d\n", conn_fd);
                }
            } else {
                /* Handle client data */
                int fd = events[i].data.fd;
                
                while (1) {
                    ssize_t nread = read(fd, buffer, sizeof(buffer) - 1);
                    if (nread > 0) {
                        buffer[nread] = '\0';
                        printf("Client fd %d: %s\n", fd, buffer);
                    } else if (nread == 0) {
                        printf("Client fd %d disconnected\n", fd);
                        epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL);
                        close(fd);
                        break;
                    } else {
                        if (errno == EAGAIN || errno == EWOULDBLOCK) {
                            break;  /* All data read */
                        } else {
                            perror("read");
                            epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL);
                            close(fd);
                            break;
                        }
                    }
                }
            }
        }
    }
    
    close(listen_fd);
    close(epoll_fd);
    return 0;
}
```

The `EPOLLET` flag in this example enables edge-triggered mode, where `epoll_wait()` reports an event only when a descriptor transitions from not-ready to ready, rather than reporting readiness on every call as in level-triggered mode. Edge-triggered mode requires applications to fully drain each descriptor when notified (reading until `EAGAIN`), but it reduces the number of spurious wakeups and allows more efficient batching of I/O operations. The trade-off is increased application complexity: forgetting to drain a descriptor in edge-triggered mode causes the application to miss data, while level-triggered mode repeatedly notifies about unread data, providing a safety net against incomplete handling.

## 3. High-Performance Optimization & Failure Modes

### Zero-Copy Techniques and Splice

Traditional I/O paths involve multiple data copies: from device to kernel buffer, from kernel buffer to user-space buffer, from user-space buffer back to kernel buffer, and from kernel buffer to device. For applications that merely transfer data between file descriptors without inspecting or modifying it—such as proxies, load balancers, and file servers—these copies waste CPU cycles and memory bandwidth. Linux provides several zero-copy mechanisms that eliminate user-space copies by allowing the kernel to transfer data directly between kernel buffers.

The `sendfile()` system call transfers data from one descriptor to another entirely within kernel space, avoiding the copy to user space. Originally designed for serving static files over sockets, `sendfile()` now works with regular files as source and sockets or pipes as destination. The kernel internally uses page cache references to avoid copying file data, instead incrementing reference counts on page cache pages and adding them to the socket send buffer.

```c
#include <sys/sendfile.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int listen_fd, conn_fd, file_fd;
    struct sockaddr_in server_addr;
    struct stat file_stat;
    off_t offset;
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <file_to_serve>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    file_fd = open(argv[1], O_RDONLY);
    if (file_fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }
    
    if (fstat(file_fd, &file_stat) == -1) {
        perror("fstat");
        exit(EXIT_FAILURE);
    }
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    
    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(9090);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    
    if (listen(listen_fd, 5) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    
    printf("Serving file %s on port 9090\n", argv[1]);
    
    conn_fd = accept(listen_fd, NULL, NULL);
    if (conn_fd == -1) {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    
    offset = 0;
    ssize_t sent = sendfile(conn_fd, file_fd, &offset, file_stat.st_size);
    if (sent == -1) {
        perror("sendfile");
    } else {
        printf("Sent %zd bytes using zero-copy sendfile()\n", sent);
    }
    
    close(conn_fd);
    close(file_fd);
    close(listen_fd);
    
    return 0;
}
```

The `splice()` system call generalizes zero-copy to arbitrary combinations of pipes, sockets, and files, allowing data to move between kernel buffers without entering user space. The mechanism works by manipulating page references in the pipe buffer: when splicing from a file to a pipe, the kernel adds references to the file's page cache pages directly into the pipe buffer; when splicing from a pipe to a socket, the kernel adds the pipe's page references to the socket buffer. This reference-based approach eliminates not only data copying but also context switches, as no user-space code executes during the transfer.

```c
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#define SPLICE_SIZE 65536

int main(int argc, char *argv[]) {
    int input_fd, output_fd;
    int pipe_fds[2];
    ssize_t bytes_spliced;
    
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <input_file> <output_file>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    input_fd = open(argv[1], O_RDONLY);
    if (input_fd == -1) {
        perror("open input");
        exit(EXIT_FAILURE);
    }
    
    output_fd = open(argv[2], O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (output_fd == -1) {
        perror("open output");
        exit(EXIT_FAILURE);
    }
    
    if (pipe(pipe_fds) == -1) {
        perror("pipe");
        exit(EXIT_FAILURE);
    }
    
    ssize_t total_bytes = 0;
    while (1) {
        /* Splice from file to pipe */
        bytes_spliced = splice(input_fd, NULL, pipe_fds[1], NULL, 
                              SPLICE_SIZE, SPLICE_F_MOVE);
        if (bytes_spliced == -1) {
            perror("splice read");
            break;
        }
        if (bytes_spliced == 0) {
            break;  /* EOF */
        }
        
        /* Splice from pipe to output file */
        ssize_t bytes_written = 0;
        while (bytes_written < bytes_spliced) {
            ssize_t written = splice(pipe_fds[0], NULL, output_fd, NULL,
                                    bytes_spliced - bytes_written, SPLICE_F_MOVE);
            if (written == -1) {
                perror("splice write");
                exit(EXIT_FAILURE);
            }
            bytes_written += written;
        }
        
        total_bytes += bytes_spliced;
    }
    
    printf("Copied %zd bytes using zero-copy splice()\n", total_bytes);
    
    close(input_fd);
    close(output_fd);
    close(pipe_fds[0]);
    close(pipe_fds[1]);
    
    return 0;
}
```

### Memory-Mapped I/O

Memory-mapped I/O through `mmap()` provides an alternative to `read()` and `write()` by mapping file contents directly into the process's virtual address space. The kernel establishes page table entries pointing to the file's page cache pages, allowing the process to access file data through ordinary memory loads and stores without explicit system calls. Page faults bring pages into memory on demand, and the kernel's page cache writeback mechanisms handle synchronization to disk. This approach eliminates the explicit copy between kernel and user space but introduces complexity around synchronization, cache coherency, and error handling—I/O errors manifest as segmentation faults rather than system call error returns.

```c
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int fd;
    struct stat sb;
    char *mapped;
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    
    fd = open(argv[1], O_RDWR);
    if (fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }
    
    if (fstat(fd, &sb) == -1) {
        perror("fstat");
        exit(EXIT_FAILURE);
    }
    
    mapped = mmap(NULL, sb.st_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) {
        perror("mmap");
        exit(EXIT_FAILURE);
    }
    
    /* File is now accessible as memory */
    printf("First 100 bytes:\n%.*s\n", 100, mapped);
    
    /* Modify the file through memory writes */
    if (sb.st_size >= 10) {
        memcpy(mapped, "MODIFIED__", 10);
        
        /* Ensure changes are synced to disk */
        if (msync(mapped, sb.st_size, MS_SYNC) == -1) {
            perror("msync");
        }
    }
    
    /* Advise kernel about access pattern */
    madvise(mapped, sb.st_size, MADV_SEQUENTIAL);
    
    munmap(mapped, sb.st_size);
    close(fd);
    
    return 0;
}
```

The `madvise()` call provides hints to the kernel about expected access patterns, enabling optimizations like aggressive readahead for `MADV_SEQUENTIAL` or dropping pages from cache for `MADV_DONTNEED`. These hints do not change program semantics but can dramatically improve performance by aligning kernel heuristics with application behavior.

### Thundering Herd and Load Balancing

The classic thundering herd problem occurs when multiple processes or threads block on `accept()` on the same listening socket. When a connection arrives, the kernel wakes all waiters, but only one successfully accepts the connection while the others return `EAGAIN` and must retry. This creates wasteful context switching and cache pollution. Linux solved this for `accept()` by implementing an exclusive wakeup semantic where only one waiter is awakened per incoming connection. However, the problem persists for epoll: if multiple threads call `epoll_wait()` on the same epoll instance containing a listening socket, connection events can wake multiple threads unnecessarily.

Modern practice for scalable servers uses one of two patterns. The first employs a dedicated acceptor thread that accepts connections and distributes the connected sockets to worker threads, either through work queues or by explicitly passing descriptors via Unix sockets. The second uses `SO_REUSEPORT` socket option, introduced in Linux 3.9, which allows multiple sockets to bind to the same address/port combination and distributes incoming connections among them using a hash of the connection tuple, providing kernel-level load balancing without thundering herd effects.

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_WORKERS 4
#define PORT 8080

void *worker_thread(void *arg) {
    int listen_fd;
    struct sockaddr_in server_addr;
    char buffer[1024];
    long thread_id = (long)arg;
    
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) {
        perror("socket");
        return NULL;
    }
    
    int reuse = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    
    if (bind(listen_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        return NULL;
    }
    
    if (listen(listen_fd, 128) == -1) {
        perror("listen");
        return NULL;
    }
    
    printf("Worker %ld listening with SO_REUSEPORT\n", thread_id);
    
    while (1) {
        int conn_fd = accept(listen_fd, NULL, NULL);
        if (conn_fd == -1) {
            perror("accept");
            continue;
        }
        
        printf("Worker %ld accepted connection on fd %d\n", thread_id, conn_fd);
        
        ssize_t nread = read(conn_fd, buffer, sizeof(buffer) - 1);
        if (nread > 0) {
            buffer[nread] = '\0';
            printf("Worker %ld received: %s\n", thread_id, buffer);
        }
        
        close(conn_fd);
    }
    
    close(listen_fd);
    return NULL;
}

int main(void) {
    pthread_t threads[NUM_WORKERS];
    
    for (long i = 0; i < NUM_WORKERS; i++) {
        if (pthread_create(&threads[i], NULL, worker_thread, (void *)i) != 0) {
            perror("pthread_create");
            exit(EXIT_FAILURE);
        }
    }
    
    for (int i = 0; i < NUM_WORKERS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    return 0;
}
```

### Resource Exhaustion and Descriptor Limits

File descriptor exhaustion represents a critical failure mode that can bring servers to their knees. Each process has a soft and hard limit on open file descriptors, queryable and modifiable through `getrlimit()` and `setrlimit()`. The soft limit defaults to 1024 on many systems, while the hard limit defaults to 4096 or higher. Production servers must explicitly raise these limits, typically to hundreds of thousands of descriptors for high-capacity services. Beyond per-process limits, the kernel imposes a system-wide limit on total open files, configured through `/proc/sys/fs/file-max`.

Exhausting descriptors manifests as `EMFILE` (per-process limit) or `ENFILE` (system-wide limit) errors from `socket()`, `open()`, or `accept()`. Robust servers must handle these errors gracefully, typically by logging the error, closing optional resources like cached connections, and backing off from accepting new connections temporarily. Failing to handle descriptor exhaustion can create cascading failures where error handling itself allocates resources, pushing the system deeper into failure.

```c
#include <sys/resource.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
    struct rlimit limit;
    
    /* Query current limits */
    if (getrlimit(RLIMIT_NOFILE, &limit) == -1) {
        perror("getrlimit");
        exit(EXIT_FAILURE);
    }
    
    printf("Current limits: soft=%ld hard=%ld\n", 
           (long)limit.rlim_cur, (long)limit.rlim_max);
    
    /* Attempt to raise soft limit to hard limit */
    limit.rlim_cur = limit.rlim_max;
    if (setrlimit(RLIMIT_NOFILE, &limit) == -1) {
        perror("setrlimit");
        exit(EXIT_FAILURE);
    }
    
    printf("Raised soft limit to %ld\n", (long)limit.rlim_cur);
    
    /* Attempt to allocate many descriptors */
    int *fds = malloc(limit.rlim_cur * sizeof(int));
    int count = 0;
    
    for (int i = 0; i < limit.rlim_cur; i++) {
        int pipefd[2];
        if (pipe(pipefd) == -1) {
            perror("pipe");
            printf("Allocated %d descriptors before exhaustion\n", count);
            break;
        }
        fds[count++] = pipefd[0];
        fds[count++] = pipefd[1];
    }
    
    /* Clean up */
    for (int i = 0; i < count; i++) {
        close(fds[i]);
    }
    free(fds);
    
    return 0;
}
```

### Signal Safety and Interrupted System Calls

The interaction between signals and blocking I/O creates a persistent source of subtle bugs. When a signal interrupts a blocking system call, the kernel can either return `EINTR` or automatically restart the system call, depending on the `SA_RESTART` flag in the signal handler's configuration. Code that fails to handle `EINTR` may treat legitimate signal deliveries as fatal I/O errors, while code that assumes automatic restart may hang indefinitely if restart is not enabled. The safest approach wraps all blocking I/O operations in loops that retry on `EINTR`, explicitly handling the interruption regardless of the restart configuration.

```c
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

ssize_t read_fully(int fd, void *buf, size_t count) {
    size_t total_read = 0;
    char *ptr = buf;
    
    while (total_read < count) {
        ssize_t nread = read(fd, ptr + total_read, count - total_read);
        if (nread < 0) {
            if (errno == EINTR) {
                continue;  /* Retry after signal interruption */
            }
            return -1;  /* Actual error */
        }
        if (nread == 0) {
            break;  /* EOF */
        }
        total_read += nread;
    }
    
    return total_read;
}

ssize_t write_fully(int fd, const void *buf, size_t count) {
    size_t total_written = 0;
    const char *ptr = buf;
    
    while (total_written < count) {
        ssize_t nwritten = write(fd, ptr + total_written, count - total_written);
        if (nwritten < 0) {
            if (errno == EINTR) {
                continue;  /* Retry after signal interruption */
            }
            return -1;  /* Actual error */
        }
        total_written += nwritten;
    }
    
    return total_written;
}
```

The self-pipe trick provides a robust solution for integrating signals with event loops. The pattern creates a pipe, installs signal handlers that write a byte to the pipe, and includes the pipe's read end in the set of descriptors monitored by `select()` or `epoll()`. When a signal arrives, the write to the pipe causes the multiplexing call to return, allowing the event loop to check for delivered signals without race conditions or complex signal masking. This technique transforms asynchronous signals into synchronous I/O events that fit naturally into event-driven architectures.

```c
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

static int signal_pipe[2];

void signal_handler(int signum) {
    char byte = signum;
    ssize_t unused __attribute__((unused));
    unused = write(signal_pipe[1], &byte, 1);
}

int init_signal_handling(void) {
    if (pipe(signal_pipe) == -1) {
        return -1;
    }
    
    /* Set both ends to non-blocking */
    int flags = fcntl(signal_pipe[0], F_GETFL);
    fcntl(signal_pipe[0], F_SETFL, flags | O_NONBLOCK);
    flags = fcntl(signal_pipe[1], F_GETFL);
    fcntl(signal_pipe[1], F_SETFL, flags | O_NONBLOCK);
    
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    
    return signal_pipe[0];  /* Return read end for event loop */
}

void process_signals(void) {
    char signals[16];
    ssize_t nread;
    
    while ((nread = read(signal_pipe[0], signals, sizeof(signals))) > 0) {
        for (ssize_t i = 0; i < nread; i++) {
            printf("Received signal %d\n", signals[i]);
            if (signals[i] == SIGINT || signals[i] == SIGTERM) {
                printf("Shutdown signal received\n");
                exit(0);
            }
        }
    }
}
```

Interprocess communication and I/O represent the connective tissue of systems programming, transforming isolated processes into cooperating components of larger systems. Mastering these primitives—from the elegance of pipes to the scalability of epoll to the complexity of signal-driven programming—separates capable programmers from systems architects who build infrastructure that scales to millions of users. The progression from blocking I/O to non-blocking to event-driven to asynchronous represents not merely performance optimization but a fundamental shift in how we conceptualize computation itself: not as sequential instruction execution but as asynchronous event processing where the operating system orchestrates vast numbers of concurrent activities, each making incremental progress as resources become available.
