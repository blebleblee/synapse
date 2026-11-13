# Lesson 2: Core Architecture & Memory/Execution Models

## 1. Process, Threading, and Execution Lifecycles

The Linux kernel's process and threading model is built upon the concept of a process, which is a collection of system resources allocated to a program. A process is created when a new program is executed, and it is terminated when the program completes its execution or encounters an error. The kernel manages processes through a hierarchical structure, with each process having a unique process ID (PID).

The kernel's threading model is based on the concept of a thread, which is a lightweight process that shares the same memory space as its parent process. Threads are created and managed by the kernel, and they are used to improve system responsiveness and scalability. The kernel's threading model is based on the Completely Fair Scheduler (CFS), which is a priority-based scheduling algorithm that ensures each thread receives a fair share of CPU time.

The execution lifecycle of a process or thread begins when the kernel receives a system call to create a new process or thread. The kernel then allocates system resources, such as memory and file descriptors, to the new process or thread. The kernel also sets up the process or thread's execution context, including its program counter, stack, and registers.

Once the process or thread is created, it begins executing its program. The kernel's execution model is based on the concept of a task, which is a unit of execution that is scheduled by the kernel. Tasks are created and managed by the kernel, and they are used to improve system responsiveness and scalability.

The kernel's task model is based on the concept of a `task_struct`, which is a data structure that represents a task. The `task_struct` contains information about the task, such as its PID, program counter, stack, and registers. The kernel uses the `task_struct` to manage tasks and to schedule them for execution.

### Creating a New Process

```c
#include <linux/sched.h>
#include <linux/mm.h>

int do_fork(struct task_struct *tsk)
{
    struct task_struct *new_tsk;
    struct mm_struct *mm;

    new_tsk = kmem_cache_alloc(task_struct_cachep, GFP_KERNEL);
    if (!new_tsk)
        return -ENOMEM;

    mm = mm_alloc(mm, GFP_KERNEL);
    if (!mm)
        goto free_new_tsk;

    new_tsk->mm = mm;
    new_tsk->pid = get_pid();
    new_tsk->state = TASK_NEW;

    // Set up new task's execution context
    new_tsk->stack = (void *)new_tsk->stack_start;
    new_tsk->sp = (void *)new_tsk->sp_start;
    new_tsk->pc = (void *)new_tsk->pc_start;

    // Copy parent's registers
    copy_thread_regs(new_tsk, tsk);

    // Schedule new task for execution
    schedule();

    return 0;

free_new_tsk:
    kmem_cache_free(task_struct_cachep, new_tsk);
    return -ENOMEM;
}
```

## 2. Memory Subsystems and Buffer Management

The Linux kernel's memory subsystem is responsible for managing the system's physical memory. The kernel uses a hierarchical memory management structure, with each level of the hierarchy representing a different type of memory allocation.

The kernel's memory management structure is based on the concept of a memory region, which is a contiguous block of physical memory. Memory regions are created and managed by the kernel, and they are used to allocate memory to processes and threads.

The kernel's buffer management system is responsible for managing the system's buffer cache, which is a cache of frequently accessed data. The buffer cache is used to improve system performance by reducing the number of disk accesses.

The kernel's buffer management system is based on the concept of a `buffer_head`, which is a data structure that represents a buffer. `Buffer_heads` contain information about the buffer, such as its size, offset, and flags.

### Allocating Memory

```c
#include <linux/mm.h>

struct page *alloc_page(gfp_t gfp_mask)
{
    struct page *page;

    page = get_page_from_freelist(gfp_mask);
    if (!page)
        return NULL;

    page->flags = 0;
    page->mapping = NULL;
    page->index = 0;

    return page;
}
```

## 3. Data Structures and On-Disk/In-Kernel Binary Layouts

The Linux kernel uses a variety of data structures to manage system resources and to implement kernel functionality. Some of the most important data structures used by the kernel include:

*   `task_struct`: represents a task (process or thread)
*   `mm_struct`: represents a memory map
*   `page_struct`: represents a page of memory
*   `buffer_head`: represents a buffer

The kernel's on-disk and in-kernel binary layouts are based on the concept of a file system, which is a hierarchical structure that represents a file system's directory tree. The kernel's file system is based on the concept of an inode, which is a data structure that represents a file system object.

### Reading an Inode

```c
#include <linux/fs.h>

struct inode *inode_read(struct super_block *sb, unsigned long ino)
{
    struct inode *inode;

    inode = iget(sb, ino);
    if (!inode)
        return NULL;

    return inode;
}
```

## 4. The Critical Execution Lifecycle

The critical execution lifecycle of a process or thread is the sequence of events that occurs when the kernel receives a system call to execute a new process or thread. The critical execution lifecycle includes the following steps:

1.  The kernel receives a system call to create a new process or thread.
2.  The kernel allocates system resources, such as memory and file descriptors, to the new process or thread.
3.  The kernel sets up the process or thread's execution context, including its program counter, stack, and registers.
4.  The kernel schedules the new process or thread for execution.
5.  The kernel executes the new process or thread.

The critical execution lifecycle is a critical component of the Linux kernel's process and threading model, and it is responsible for managing the execution of processes and threads.

### Scheduling a Task

```c
#include <linux/sched.h>

void schedule(void)
{
    struct task_struct *tsk;

    tsk = pick_next_task();
    if (!tsk)
        return;

    tsk->state = TASK_RUNNING;
    tsk->pc = (void *)tsk->pc_start;
    tsk->sp = (void *)tsk->sp_start;

    switch_to(tsk);
}
```

This concludes Lesson 2: Core Architecture & Memory/Execution Models. The next lesson will cover advanced topics in Linux kernel development, including device drivers and network protocols.
