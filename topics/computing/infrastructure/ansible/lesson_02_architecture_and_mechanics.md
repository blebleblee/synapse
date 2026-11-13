# Lesson 2: Core Architecture & Memory/Execution Models

## 1. Process, Threading, and Execution Lifecycles

Understanding the process, threading, and execution lifecycles is crucial for grasping the intricacies of infrastructure automation in Ansible. A process is an instance of a program in execution, with its own virtual address space, open file descriptors, and process ID. Modern operating systems, such as Linux, schedule processes using various algorithms, including the Completely Fair Scheduler (CFS).

The process lifecycle begins with creation, where a new process is spawned from a parent process using the `fork()` system call. The child process inherits the parent's address space, open file descriptors, and process ID. The child process then executes the `exec()` system call, which replaces the child's address space with a new one containing the executable file's binary code. This process is repeated recursively, allowing for the creation of multiple processes from a single parent.

Threading is a mechanism for concurrent execution within a single process. Threads share the same virtual address space and open file descriptors as their parent process, but each thread has its own stack and program counter. Threads are scheduled by the kernel using the same scheduling algorithms as processes. In Ansible, threading is used to execute multiple tasks concurrently, improving overall system performance.

The execution lifecycle of a process or thread is governed by the kernel's scheduling policies. The kernel maintains a data structure known as the Process Control Block (PCB), which contains information about the process or thread, such as its state, priority, and scheduling parameters. The kernel uses this information to schedule processes and threads, ensuring that each process or thread receives a fair share of CPU time.

### Exercise 1: Process Creation and Execution

Create a new process using the `fork()` system call and execute a simple program using the `exec()` system call. Use the `ps` command to verify the creation of the new process.

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main() {
    pid_t pid = fork();
    if (pid == 0) {
        // Child process
        execl("/bin/ls", "ls", NULL);
    } else {
        // Parent process
        printf("Child process created with PID %d\n", pid);
    }
    return 0;
}
```

Compile and run the program using the following commands:

```bash
gcc -o process_example process_example.c
./process_example
```

Verify the creation of the new process using the `ps` command:

```bash
ps -ef | grep process_example
```

## 2. Memory Subsystems and Buffer Management

In the context of Ansible, memory subsystems and buffer management are critical components of infrastructure automation. The memory subsystem is responsible for managing the allocation and deallocation of memory blocks for processes and threads. The kernel maintains a data structure known as the Page Table, which maps virtual addresses to physical addresses in memory.

The kernel uses a technique known as virtual memory to manage memory allocation. Virtual memory is a combination of physical RAM and disk storage, where pages of memory are swapped in and out of physical RAM as needed. The kernel uses a data structure known as the Page Table to manage virtual memory, mapping virtual addresses to physical addresses in memory.

Buffer management is a critical component of memory subsystems, as it ensures that data is properly buffered and transmitted between processes and threads. The kernel maintains a data structure known as the Buffer Cache, which stores frequently accessed data in memory. The Buffer Cache is used to improve system performance by reducing the number of disk I/O operations.

### Exercise 2: Memory Allocation and Deallocation

Use the `malloc()` and `free()` functions to allocate and deallocate memory blocks. Use the `valgrind` tool to verify memory leaks.

```c
#include <stdio.h>
#include <stdlib.h>

int main() {
    int* ptr = malloc(10 * sizeof(int));
    if (ptr == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }
    printf("Memory allocated successfully\n");
    free(ptr);
    return 0;
}
```

Compile and run the program using the following commands:

```bash
gcc -o memory_example memory_example.c
valgrind ./memory_example
```

Verify the memory allocation and deallocation using the `valgrind` tool:

```bash
valgrind --leak-check=full ./memory_example
```

## 3. Data Structures and On-Disk/In-Kernel Binary Layouts

In the context of Ansible, data structures and on-disk/in-kernel binary layouts are critical components of infrastructure automation. Data structures are used to represent complex data in a compact and efficient manner. The kernel uses various data structures, such as linked lists, trees, and graphs, to manage system resources and data.

On-disk binary layouts refer to the format in which data is stored on disk. The kernel uses various formats, such as the ext4 file system, to store data on disk. The ext4 file system uses a data structure known as the Inode Table to manage file metadata.

In-kernel binary layouts refer to the format in which data is stored in kernel memory. The kernel uses various formats, such as the Page Table, to store data in kernel memory. The Page Table is used to manage virtual memory and map virtual addresses to physical addresses in memory.

### Exercise 3: Data Structure Implementation

Implement a simple linked list data structure using C. Use the `malloc()` and `free()` functions to allocate and deallocate memory blocks.

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node* next;
} Node;

void add_node(Node** head, int data) {
    Node* new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = *head;
    *head = new_node;
}

void print_list(Node* head) {
    while (head != NULL) {
        printf("%d -> ", head->data);
        head = head->next;
    }
    printf("NULL\n");
}

int main() {
    Node* head = NULL;
    add_node(&head, 10);
    add_node(&head, 20);
    add_node(&head, 30);
    print_list(head);
    return 0;
}
```

Compile and run the program using the following commands:

```bash
gcc -o linked_list_example linked_list_example.c
./linked_list_example
```

Verify the linked list implementation using the `print_list()` function:

```bash
./linked_list_example
```

## 4. The Critical Execution Lifecycle

The critical execution lifecycle refers to the sequence of events that occur when a process or thread is executed by the kernel. The critical execution lifecycle includes the following stages:

1. Process creation: The kernel creates a new process or thread using the `fork()` or `clone()` system call.
2. Memory allocation: The kernel allocates memory blocks for the process or thread using the `malloc()` or `sbrk()` system call.
3. Thread scheduling: The kernel schedules the process or thread using the same scheduling algorithms as processes.
4. Execution: The kernel executes the process or thread, transferring control to the process or thread's program counter.
5. Termination: The kernel terminates the process or thread, releasing any allocated resources.

The critical execution lifecycle is a critical component of infrastructure automation in Ansible, as it ensures that processes and threads are executed efficiently and effectively.
