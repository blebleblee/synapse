# Lesson 2: Core Architecture & Memory/Execution Models

## 1. Process, Threading & Execution Lifecycles

In modern operating systems, the process model is a fundamental abstraction that enables efficient resource sharing and isolation. At its core, a process is a sequence of instructions executed by the CPU, with its own virtual address space, open file descriptors, and process ID. However, beneath this high-level abstraction lies a complex interplay of threads, scheduling, and execution lifecycles.

To understand the process model, we must first delve into the threading mechanism. In Linux, for example, threads are created using the `clone` system call, which duplicates the current process's memory and registers, creating a new thread with its own stack and program counter. This new thread is then scheduled by the kernel's scheduler, which assigns it a unique thread ID and schedules it for execution.

The execution lifecycle of a process is a critical aspect of understanding how the operating system manages resources. When a process is created, it is assigned a unique process ID (PID) and is scheduled for execution by the kernel's scheduler. As the process executes, it may create new threads, open files, and allocate memory. However, when the process terminates, its resources are released back to the system, and its memory is deallocated.

To illustrate this process, consider the following sequence of events:

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

void* thread_func(void* arg) {
    printf("Hello from thread %d!\n", pthread_self());
    return NULL;
}

int main() {
    pthread_t thread;
    pthread_create(&thread, NULL, thread_func, NULL);
    pthread_join(thread, NULL);
    return 0;
}
```

In this example, we create a new thread using `pthread_create`, which duplicates the current process's memory and registers, creating a new thread with its own stack and program counter. We then schedule the new thread for execution using `pthread_join`, which waits for the thread to complete before returning control to the main process.

## 2. Memory Subsystems & Buffer Management

Memory management is a critical aspect of operating system design, as it enables efficient allocation and deallocation of memory for processes. In modern operating systems, memory management is typically handled by a combination of hardware and software components.

At the hardware level, memory is organized into a hierarchical structure of caches, with the CPU's Level 1 (L1) cache providing the fastest access to memory. The Level 2 (L2) cache provides a slower, but still fast, access to memory, while the Level 3 (L3) cache provides a slower, but still relatively fast, access to memory.

At the software level, memory management is typically handled by a combination of the operating system's memory manager and the process's memory allocator. The memory manager is responsible for allocating and deallocating memory for processes, while the memory allocator is responsible for allocating and deallocating memory within a process.

To illustrate this process, consider the following sequence of events:

```c
#include <stdio.h>
#include <stdlib.h>

int main() {
    int* ptr = malloc(1024);
    printf("Allocated memory at address 0x%x\n", (unsigned int)ptr);
    free(ptr);
    return 0;
}
```

In this example, we allocate 1024 bytes of memory using `malloc`, which returns a pointer to the allocated memory. We then print the address of the allocated memory using `printf`. Finally, we deallocate the memory using `free`, which releases the memory back to the system.

## 3. Data Structures & On-Disk/In-Kernel Binary Layouts

Data structures are a critical aspect of operating system design, as they enable efficient storage and retrieval of data. In modern operating systems, data structures are typically implemented using a combination of arrays, linked lists, and trees.

At the on-disk level, data structures are typically stored in a binary format, with each field represented by a specific byte or set of bytes. For example, a 32-bit integer might be represented by four consecutive bytes, with each byte representing a specific bit of the integer.

At the in-kernel level, data structures are typically implemented using a combination of arrays and linked lists. For example, a kernel's process table might be implemented as an array of process structures, with each process structure containing a set of fields representing the process's state.

To illustrate this process, consider the following sequence of events:

```c
#include <stdio.h>
#include <stdlib.h>

struct process {
    int pid;
    char name[16];
    int status;
};

int main() {
    struct process proc;
    proc.pid = 1234;
    strcpy(proc.name, "example");
    proc.status = 0;
    printf("Process %d: %s, status 0x%x\n", proc.pid, proc.name, proc.status);
    return 0;
}
```

In this example, we define a `process` structure containing a `pid`, `name`, and `status` field. We then create a `process` structure and initialize its fields using assignment. Finally, we print the process's fields using `printf`.

## 4. The Critical Execution Lifecycle

The critical execution lifecycle is a critical aspect of operating system design, as it enables efficient execution of processes. At its core, the critical execution lifecycle consists of a sequence of events, including:

1. Process creation: The process is created using a system call, such as `fork` or `exec`.
2. Memory allocation: The process is allocated memory using a memory allocator, such as `malloc`.
3. Instruction execution: The process executes instructions using the CPU.
4. Interrupt handling: The process handles interrupts, such as page faults or signals.
5. Process termination: The process terminates using a system call, such as `exit`.

To illustrate this process, consider the following sequence of events:

```c
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

void sigint_handler(int sig) {
    printf("Received signal %d\n", sig);
    exit(0);
}

int main() {
    signal(SIGINT, sigint_handler);
    while (1) {
        printf("Hello from process %d!\n", getpid());
        sleep(1);
    }
    return 0;
}
```

In this example, we define a `sigint_handler` function that handles the `SIGINT` signal. We then register the `sigint_handler` function using `signal`. Finally, we enter an infinite loop, printing a message to the console and sleeping for one second.

This concludes Lesson 2: Core Architecture & Memory/Execution Models. In this lesson, we have explored the process model, memory management, data structures, and the critical execution lifecycle. We have also provided examples of code that illustrate these concepts. In the next lesson, we will explore the network stack and how it enables communication between processes.
