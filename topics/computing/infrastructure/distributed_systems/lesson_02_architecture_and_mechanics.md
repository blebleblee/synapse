# Lesson 2: Core Architecture & Memory/Execution Models

## 1. Process, Threading & Execution Lifecycles

In modern operating systems, the process model is a fundamental abstraction that enables concurrent execution, resource sharing, and isolation. A process is a self-contained program in execution, with its own virtual address space, open files, and process ID. The process model is built upon the concept of threads, which are lightweight processes that share the same memory space and resources.

The execution lifecycle of a process begins with creation, where the kernel allocates a new process descriptor and initializes the process's virtual address space. The process then enters the running state, where it executes instructions and interacts with the kernel and other processes. When the process terminates, the kernel reclaims its resources and deallocates its process descriptor.

The threading model is an essential component of the process model, enabling concurrent execution and improving system responsiveness. Threads are scheduled by the kernel using various scheduling algorithms, such as the Completely Fair Scheduler (CFS) in Linux. The CFS uses a red-black tree to manage thread priorities and schedules threads based on their priority and runtime.

```markdown
// Example of a simple process creation in Linux
#include <linux/sched.h>
#include <linux/mm.h>

int main() {
    // Create a new process descriptor
    struct task_struct *task = kmalloc(sizeof(struct task_struct), GFP_KERNEL);
    if (!task) {
        // Handle allocation failure
        return -ENOMEM;
    }

    // Initialize the process's virtual address space
    task->mm = mm_init();
    if (!task->mm) {
        // Handle initialization failure
        kfree(task);
        return -ENOMEM;
    }

    // Set the process's execution context
    task->state = TASK_RUNNING;
    task->pid = get_pid();

    // Schedule the process
    schedule();

    // Execute the process
    while (1) {
        // Execute instructions and interact with the kernel
    }

    // Terminate the process
    exit();
}
```

## 2. Memory Subsystems & Buffer Management

Memory is a critical resource in modern computing systems, and the memory subsystem plays a vital role in managing memory allocation, deallocation, and access. The memory subsystem consists of several components, including the page table, the page cache, and the buffer cache.

The page table is a data structure that maps virtual addresses to physical addresses, enabling the kernel to manage memory allocation and deallocation. The page cache is a cache of recently accessed pages, which improves memory access performance by reducing the number of page faults. The buffer cache is a cache of recently accessed data, which improves I/O performance by reducing the number of disk accesses.

Buffer management is a critical component of the memory subsystem, enabling the kernel to manage buffer allocation, deallocation, and access. Buffers are used to store data temporarily while it is being transferred between devices, and buffer management ensures that buffers are allocated and deallocated efficiently.

```markdown
// Example of a simple buffer allocation in Linux
#include <linux/mm.h>

int main() {
    // Allocate a new buffer
    struct buffer_head *bh = kmalloc(sizeof(struct buffer_head), GFP_KERNEL);
    if (!bh) {
        // Handle allocation failure
        return -ENOMEM;
    }

    // Initialize the buffer's metadata
    bh->b_size = 4096;
    bh->b_dev = get_dev();
    bh->b_blocknr = get_blocknr();

    // Schedule the buffer
    schedule();

    // Execute the buffer
    while (1) {
        // Execute instructions and interact with the kernel
    }

    // Deallocate the buffer
    kfree(bh);
}
```

## 3. Data Structures & On-Disk/In-Kernel Binary Layouts

Data structures are a critical component of modern computing systems, enabling the kernel to manage data efficiently and effectively. The kernel uses various data structures, including arrays, linked lists, trees, and graphs, to manage data such as process descriptors, memory allocation, and I/O operations.

On-disk and in-kernel binary layouts are critical components of the kernel, enabling the kernel to store and retrieve data efficiently. The kernel uses various binary formats, including ELF, a.out, and COFF, to store executable code and data. The kernel also uses various on-disk formats, including ext2, ext3, and ext4, to store file system metadata.

```markdown
// Example of a simple data structure in Linux
#include <linux/mm.h>

struct process_descriptor {
    struct task_struct *task;
    struct mm_struct *mm;
    struct file *file;
};

int main() {
    // Create a new process descriptor
    struct process_descriptor *pd = kmalloc(sizeof(struct process_descriptor), GFP_KERNEL);
    if (!pd) {
        // Handle allocation failure
        return -ENOMEM;
    }

    // Initialize the process descriptor's metadata
    pd->task = kmalloc(sizeof(struct task_struct), GFP_KERNEL);
    pd->mm = mm_init();
    pd->file = get_file();

    // Schedule the process descriptor
    schedule();

    // Execute the process descriptor
    while (1) {
        // Execute instructions and interact with the kernel
    }

    // Deallocate the process descriptor
    kfree(pd);
}
```

## 4. The Critical Execution Lifecycle

The critical execution lifecycle is the sequence of events that occurs when a process executes instructions and interacts with the kernel. The critical execution lifecycle consists of several stages, including process creation, thread scheduling, memory allocation, I/O operations, and process termination.

The critical execution lifecycle is a critical component of modern computing systems, enabling the kernel to manage process execution efficiently and effectively. The kernel uses various mechanisms, including scheduling algorithms, memory allocation, and I/O operations, to manage the critical execution lifecycle.

```markdown
// Example of a simple critical execution lifecycle in Linux
#include <linux/sched.h>
#include <linux/mm.h>

int main() {
    // Create a new process descriptor
    struct process_descriptor *pd = kmalloc(sizeof(struct process_descriptor), GFP_KERNEL);
    if (!pd) {
        // Handle allocation failure
        return -ENOMEM;
    }

    // Initialize the process descriptor's metadata
    pd->task = kmalloc(sizeof(struct task_struct), GFP_KERNEL);
    pd->mm = mm_init();
    pd->file = get_file();

    // Schedule the process descriptor
    schedule();

    // Execute the process descriptor
    while (1) {
        // Execute instructions and interact with the kernel
    }

    // Terminate the process descriptor
    exit();
}
```

### Process Creation

The process creation stage involves allocating a new process descriptor and initializing the process's virtual address space.

```markdown
graph TD;
    A[Process Creation] -->| "Allocate process descriptor" | B[Process Descriptor];
    B -->| "Initialize virtual address space" | C[Virtual Address Space];
    C -->| "Schedule process" | D[Process Scheduler];
    D -->| "Execute process" | E[Process Execution];
```

### Thread Scheduling

The thread scheduling stage involves scheduling threads based on their priority and runtime.

```markdown
graph TD;
    A[Thread Scheduling] -->| "Schedule threads" | B[Thread Scheduler];
    B -->| "Manage thread priorities" | C[Thread Priorities];
    C -->| "Schedule threads based on priority and runtime" | D[Thread Scheduling];
```

### Memory Allocation

The memory allocation stage involves allocating memory for the process and managing memory deallocation.

```markdown
graph TD;
    A[Memory Allocation] -->| "Allocate memory" | B[Memory Allocator];
    B -->| "Manage memory deallocation" | C[Memory Deallocator];
    C -->| "Free memory" | D[Memory Free];
```

### I/O Operations

The I/O operations stage involves managing I/O operations, including reading and writing data to devices.

```markdown
graph TD;
    A[I/O Operations] -->| "Manage I/O operations" | B[I/O Manager];
    B -->| "Read data from devices" | C[Read Data];
    C -->| "Write data to devices" | D[Write Data];
```

### Process Termination

The process termination stage involves terminating the process and deallocating its resources.

```markdown
graph TD;
    A[Process Termination] -->| "Terminate process" | B[Process Termination];
    B -->| "Deallocate resources" | C[Resource Deallocator];
    C -->| "Free process descriptor" | D[Process Descriptor Free];
```

This concludes Lesson 2: Core Architecture & Memory/Execution Models. The lesson has covered the process model, memory subsystem, data structures, and critical execution lifecycle, providing a deep understanding of the fundamental mechanisms and trade-offs in modern computing systems.
