# Lesson 2: Core Architecture & Memory/Execution Models

## Process, Threading, and Execution Lifecycles

In the eBPF ecosystem, a process is a fundamental unit of execution, encapsulating a program's memory, resources, and state. At its core, a process is a thread of execution, managed by the Linux kernel's scheduler. Understanding the process lifecycle is crucial to grasping eBPF's behavior and performance.

A process is created when a new thread of execution is spawned, typically through the `clone` system call. The `clone` call creates a new process by duplicating the current process's memory, resources, and state. The new process inherits the parent's memory map, including the eBPF program's memory allocation. This memory allocation is managed by the kernel's slab allocator, which provides a pool of pre-allocated memory blocks for efficient allocation and deallocation.

The process lifecycle consists of several stages:

1.  **Creation**: A new process is created through the `clone` system call, which duplicates the parent's memory, resources, and state.
2.  **Initialization**: The new process initializes its memory, including the eBPF program's memory allocation, through the `do_execve` function.
3.  **Execution**: The new process executes the eBPF program, which is loaded into memory through the `bpf_load_program` function.
4.  **Termination**: The process terminates when the eBPF program completes execution, at which point the kernel's scheduler frees the process's resources.

## Memory Subsystems and Buffer Management

eBPF relies heavily on the Linux kernel's memory management subsystems, including the slab allocator and the page cache. Understanding these subsystems is essential to grasping eBPF's memory behavior and performance.

The slab allocator provides a pool of pre-allocated memory blocks for efficient allocation and deallocation. The slab allocator is responsible for managing the kernel's memory, including the eBPF program's memory allocation. The slab allocator uses a combination of LRU (Least Recently Used) and LFU (Least Frequently Used) eviction policies to manage memory allocation and deallocation.

The page cache is a critical component of the Linux kernel's memory management subsystem. The page cache provides a cache of disk blocks, allowing the kernel to efficiently access and manage disk storage. The page cache is used by eBPF to store and manage disk blocks, including the eBPF program's memory allocation.

## Data Structures and On-Disk/In-Kernel Binary Layouts

eBPF relies heavily on a variety of data structures, including linked lists, trees, and hash tables. Understanding these data structures is essential to grasping eBPF's behavior and performance.

The eBPF program's memory allocation is stored in a linked list, managed by the kernel's slab allocator. The linked list is used to efficiently manage memory allocation and deallocation.

The eBPF program's binary layout is stored on disk in a variety of formats, including ELF (Executable and Linkable Format) and BPF (Berkeley Packet Filter) formats. The binary layout is used to store the eBPF program's code, data, and metadata.

## The Critical Execution Lifecycle

The critical execution lifecycle of an eBPF program consists of several stages:

1.  **Load**: The eBPF program is loaded into memory through the `bpf_load_program` function.
2.  **Attach**: The eBPF program is attached to a specific network interface or socket through the `bpf_attach` function.
3.  **Execution**: The eBPF program executes, processing network packets or socket events.
4.  **Detach**: The eBPF program is detached from the network interface or socket through the `bpf_detach` function.
5.  **Unload**: The eBPF program is unloaded from memory through the `bpf_unload_program` function.

Understanding the critical execution lifecycle is essential to grasping eBPF's behavior and performance.

### Exercises

1.  Write a simple eBPF program that loads and executes a basic function.
2.  Analyze the memory allocation and deallocation behavior of an eBPF program.
3.  Implement a custom eBPF program that uses a linked list to manage memory allocation.

### Code

```c
#include <linux/bpf.h>

struct bpf_map_def SEC("maps") my_map = {
    .type = BPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(__u32),
    .value_size = sizeof(__u32),
    .max_entries = 1,
};

int bpf_load_program(struct bpf_map *map, int fd, __u32 flags) {
    // Load the eBPF program into memory
    return bpf_load_program(fd, flags);
}

int bpf_attach(struct bpf_map *map, int fd, __u32 flags) {
    // Attach the eBPF program to a network interface or socket
    return bpf_attach(fd, flags);
}

int bpf_detach(struct bpf_map *map, int fd, __u32 flags) {
    // Detach the eBPF program from the network interface or socket
    return bpf_detach(fd, flags);
}

int bpf_unload_program(struct bpf_map *map, int fd, __u32 flags) {
    // Unload the eBPF program from memory
    return bpf_unload_program(fd, flags);
}
```

## Memory Allocation and Deallocation

The eBPF program's memory allocation is managed by the kernel's slab allocator, which uses a combination of LRU and LFU eviction policies to manage memory allocation and deallocation.

The slab allocator provides a pool of pre-allocated memory blocks for efficient allocation and deallocation. The slab allocator is responsible for managing the kernel's memory, including the eBPF program's memory allocation.

The page cache is a critical component of the Linux kernel's memory management subsystem, providing a cache of disk blocks to efficiently access and manage disk storage.

The eBPF program's memory allocation is stored in a linked list, managed by the kernel's slab allocator. The linked list is used to efficiently manage memory allocation and deallocation.

## Data Structures

eBPF relies heavily on a variety of data structures, including linked lists, trees, and hash tables. Understanding these data structures is essential to grasping eBPF's behavior and performance.

The eBPF program's binary layout is stored on disk in a variety of formats, including ELF (Executable and Linkable Format) and BPF (Berkeley Packet Filter) formats. The binary layout is used to store the eBPF program's code, data, and metadata.

## Critical Execution Lifecycle

The critical execution lifecycle of an eBPF program consists of several stages:

1.  **Load**: The eBPF program is loaded into memory through the `bpf_load_program` function.
2.  **Attach**: The eBPF program is attached to a specific network interface or socket through the `bpf_attach` function.
3.  **Execution**: The eBPF program executes, processing network packets or socket events.
4.  **Detach**: The eBPF program is detached from the network interface or socket through the `bpf_detach` function.
5.  **Unload**: The eBPF program is unloaded from memory through the `bpf_unload_program` function.

Understanding the critical execution lifecycle is essential to grasping eBPF's behavior and performance.
