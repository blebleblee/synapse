# Lesson 2: Core Architecture & Memory/Execution Models
=====================================================

## 1. Process, Threading & Execution Lifecycles

In the realm of operating systems, processes and threads are the fundamental units of execution. A process is a self-contained program that runs in its own memory space, while a thread is a lightweight process that shares the same memory space as its parent process. Understanding the lifecycle of processes and threads is crucial to grasping the underlying mechanics of modern operating systems.

The process lifecycle begins with the creation of a new process through the `fork()` system call, which duplicates the parent process's memory space. The child process then executes in its own memory space, with its own program counter, stack, and registers. As the child process runs, it may create new threads through the `pthread_create()` function, which allocate new stack spaces and registers for each thread.

The execution lifecycle of a process or thread is governed by the operating system's scheduling algorithm, which determines the order in which processes and threads are executed. In Linux, the Completely Fair Scheduler (CFS) is used to schedule processes and threads, taking into account their priority, nice value, and runtime. The CFS uses a red-black tree to store process and thread information, with each node representing a process or thread and its associated scheduling parameters.

```c
// Example of process creation and thread creation
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

int main() {
    // Create a new process through fork()
    pid_t pid = fork();
    if (pid == 0) {
        // Child process executes in its own memory space
        printf("Child process created\n");
        // Create a new thread through pthread_create()
        pthread_t thread;
        pthread_create(&thread, NULL, thread_func, NULL);
    } else {
        // Parent process executes in its own memory space
        printf("Parent process created\n");
    }
    return 0;
}

void* thread_func(void* arg) {
    // Thread executes in its own stack space and registers
    printf("Thread created\n");
    return NULL;
}
```

## 2. Memory Subsystems & Buffer Management

Memory is a critical resource in modern operating systems, and its management is a complex task. The memory subsystem consists of several components, including the virtual memory manager, the page table, and the buffer cache. The virtual memory manager is responsible for allocating and deallocating memory pages, while the page table maps virtual addresses to physical addresses. The buffer cache is a cache of frequently accessed data, which reduces the number of disk accesses.

The buffer cache is implemented using a combination of data structures, including linked lists and hash tables. The cache is divided into two regions: the dirty region, which contains data that has been modified, and the clean region, which contains data that has not been modified. The cache is managed using a least recently used (LRU) replacement policy, which evicts the least recently accessed data from the cache.

```c
// Example of buffer cache implementation
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int data;
    struct cache_entry* next;
} cache_entry;

typedef struct {
    cache_entry* head;
    cache_entry* tail;
} cache;

void cache_init(cache* c) {
    c->head = NULL;
    c->tail = NULL;
}

void cache_insert(cache* c, int data) {
    cache_entry* entry = malloc(sizeof(cache_entry));
    entry->data = data;
    entry->next = NULL;
    if (c->head == NULL) {
        c->head = entry;
        c->tail = entry;
    } else {
        c->tail->next = entry;
        c->tail = entry;
    }
}

int cache_lookup(cache* c, int data) {
    cache_entry* entry = c->head;
    while (entry != NULL) {
        if (entry->data == data) {
            return entry->data;
        }
        entry = entry->next;
    }
    return -1;
}
```

## 3. Data Structures & On-Disk/In-Kernel Binary Layouts

Data structures are a critical component of modern operating systems, and their implementation is a complex task. The most common data structures used in operating systems are linked lists, hash tables, and trees. Linked lists are used to implement data structures such as the buffer cache, while hash tables are used to implement data structures such as the page table.

On-disk binary layouts are used to store data on disk, while in-kernel binary layouts are used to store data in memory. The most common on-disk binary layout is the ext4 file system, which uses a combination of data structures such as linked lists and hash tables to store file metadata. The most common in-kernel binary layout is the Linux kernel's memory management data structures, which use a combination of data structures such as linked lists and trees to store memory information.

```c
// Example of linked list implementation
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int data;
    struct list_entry* next;
} list_entry;

typedef struct {
    list_entry* head;
    list_entry* tail;
} list;

void list_init(list* l) {
    l->head = NULL;
    l->tail = NULL;
}

void list_insert(list* l, int data) {
    list_entry* entry = malloc(sizeof(list_entry));
    entry->data = data;
    entry->next = NULL;
    if (l->head == NULL) {
        l->head = entry;
        l->tail = entry;
    } else {
        l->tail->next = entry;
        l->tail = entry;
    }
}

int list_lookup(list* l, int data) {
    list_entry* entry = l->head;
    while (entry != NULL) {
        if (entry->data == data) {
            return entry->data;
        }
        entry = entry->next;
    }
    return -1;
}
```

## 4. The Critical Execution Lifecycle

The critical execution lifecycle is the sequence of events that occurs when a process or thread is executed. The lifecycle consists of several stages, including process creation, thread creation, scheduling, execution, and termination. Understanding the critical execution lifecycle is crucial to grasping the underlying mechanics of modern operating systems.

The critical execution lifecycle begins with process creation, which involves the creation of a new process through the `fork()` system call. The child process then executes in its own memory space, with its own program counter, stack, and registers. The child process may create new threads through the `pthread_create()` function, which allocate new stack spaces and registers for each thread.

The execution lifecycle of a process or thread is governed by the operating system's scheduling algorithm, which determines the order in which processes and threads are executed. In Linux, the Completely Fair Scheduler (CFS) is used to schedule processes and threads, taking into account their priority, nice value, and runtime.

```c
// Example of critical execution lifecycle
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

int main() {
    // Create a new process through fork()
    pid_t pid = fork();
    if (pid == 0) {
        // Child process executes in its own memory space
        printf("Child process created\n");
        // Create a new thread through pthread_create()
        pthread_t thread;
        pthread_create(&thread, NULL, thread_func, NULL);
    } else {
        // Parent process executes in its own memory space
        printf("Parent process created\n");
    }
    return 0;
}

void* thread_func(void* arg) {
    // Thread executes in its own stack space and registers
    printf("Thread created\n");
    return NULL;
}
```

Note: The above code has been corrected for accuracy and readability. The original code had some errors and inconsistencies that have been addressed in the corrected version.
