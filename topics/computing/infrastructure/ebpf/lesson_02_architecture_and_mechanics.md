# Lesson 2: Core Architecture & Memory/Execution Models

## 1. Process, Threading & Execution Lifecycles

In the realm of infrastructure and extended Berkeley Packet Filter (eBPF) programming, understanding the process, threading, and execution lifecycles is paramount. These lifecycles are the backbone of how systems manage resources, schedule tasks, and execute code efficiently. At the heart of this lies the Linux kernel, which provides the necessary abstractions and mechanisms to orchestrate these processes.

### Scheduling Mechanics

The Linux kernel employs a sophisticated scheduling mechanism known as the Completely Fair Scheduler (CFS). CFS is designed to provide fairness among all runnable tasks, ensuring that no single process monopolizes CPU resources. At its core, CFS uses a red-black tree data structure to maintain a balanced tree of tasks, each associated with a virtual runtime (`vruntime`). The task with the smallest `vruntime` is selected for execution, ensuring that tasks that have been waiting longer receive more CPU time. This mechanism is crucial for maintaining system responsiveness and fairness, especially in multi-threaded and multi-process environments.

### Ring Buffers

Ring buffers are a fundamental data structure used in various parts of the Linux kernel, including eBPF. They are circular buffers that allow efficient and lockless data exchange between kernel and user space. In the context of eBPF, ring buffers are used to collect and transmit data from eBPF programs to user-space applications. The lockless nature of ring buffers is achieved through atomic operations and careful management of buffer pointers, ensuring that data can be written and read concurrently without contention.

### eBPF Bytecode Execution

eBPF programs are executed in a virtual machine (VM) that is embedded within the Linux kernel. This VM is designed to execute eBPF bytecode efficiently and safely. The eBPF VM operates on a 64-bit RISC architecture, featuring 11 general-purpose registers (`R0`–`R10`). The static DAG verifier in the kernel ensures that eBPF programs are safe to execute by pruning state space and enforcing bounded loops. This verification process is critical for maintaining system security, as it prevents eBPF programs from executing arbitrary code or accessing unauthorized memory.

### Control Loops

Control loops are a fundamental concept in systems programming, particularly in the context of distributed systems and eBPF. In distributed systems, control loops are used to reconcile the desired state of the system with its actual state. This is achieved through continuous level-triggered reconciliation loops, where the system continuously monitors its state and applies corrective actions to bring it in line with the desired configuration. In the context of eBPF, control loops can be used to monitor and manage network traffic, system performance, and other critical metrics.

## 2. Memory Subsystems & Buffer Management

Memory management is a critical aspect of any operating system, and Linux is no exception. The Linux kernel employs a sophisticated memory management subsystem that includes virtual memory, page tables, and various buffer management mechanisms. Understanding these subsystems is essential for systems programmers working with eBPF and other low-level kernel technologies.

### Page Layouts

Virtual memory in Linux is managed through multi-level page tables, which map virtual addresses to physical addresses. The page table hierarchy consists of several levels, including the Page Global Directory (PGD), Page Upper Directory (PUD), Page Middle Directory (PMD), and Page Table (PT). Each level of the page table contains entries that point to the next level, ultimately leading to the physical frame that contains the data. This hierarchical structure allows the kernel to efficiently manage large address spaces and provide fine-grained control over memory access.

### Socket Buffers

Socket buffers are used in the Linux networking subsystem to manage data packets as they are transmitted and received. These buffers are implemented as circular buffers that allow efficient and lockless data exchange between network drivers and the kernel. Socket buffers are crucial for maintaining high network throughput and low latency, as they allow data to be processed in a continuous stream without the need for frequent memory allocations and deallocations.

### Shared Memory

Shared memory is a mechanism that allows multiple processes to access a common block of memory. In Linux, shared memory is managed through the `shmget`, `shmat`, and `shmdt` system calls. Shared memory is particularly useful in distributed systems and eBPF programming, as it allows data to be shared between kernel and user-space applications without the need for frequent data copying. This can significantly improve performance and reduce memory overhead.

### CRD Reconciliation Cache

In the context of Kubernetes and other distributed systems, Custom Resource Definitions (CRDs) are used to define custom resources that can be managed by the system. The reconciliation cache is a mechanism used to store and manage the state of these resources. The cache is implemented as a key-value store that allows the system to efficiently track the desired state of each resource and apply corrective actions to bring it in line with the actual state. The reconciliation cache is a critical component of the continuous level-triggered reconciliation loops used in distributed systems.

## 3. Data Structures & On-Disk/In-Kernel Binary Layouts

Understanding the binary layouts of data structures is essential for systems programmers working with low-level kernel technologies such as eBPF. These layouts define how data is stored and accessed in memory, and they play a critical role in the performance and correctness of the system.

### Detailed ASCII Layouts and Bitwise Field Explanations

#### Page Table Entry (PTE)

A Page Table Entry (PTE) is a data structure used in the Linux page table hierarchy to map virtual addresses to physical addresses. The PTE contains several fields that define the attributes of the mapped page, including the physical frame number, access permissions, and caching attributes. The following ASCII layout shows the structure of a PTE in a 64-bit Linux system:

```
  63  62  61  60  59  58  57  56  55  54  53  52  51  50  49  48  47  46  45  44  43  42  41  40  39  38  37  36  35  34  33  32
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  31  30  29  28  27  26  25  24  23  22  21  20  19  18  17  16  15  14  13  12  11  10   9   8   7   6   5   4   3   2   1   0
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
```

The fields in the PTE are defined as follows:

- **Bits 63-55**: Reserved for future use.
- **Bits 54-52**: Page protection key.
- **Bit 51**: Dirty bit.
- **Bit 50**: Accessed bit.
- **Bit 49**: Page global bit.
- **Bit 48**: Custom page table bit.
- **Bits 47-12**: Physical frame number.
- **Bit 11**: Custom page table bit.
- **Bit 10**: Page attribute table bit.
- **Bit 9**: Custom page table bit.
- **Bit 8**: Custom page table bit.
- **Bit 7**: Custom page table bit.
- **Bit 6**: Custom page table bit.
- **Bit 5**: Custom page table bit.
- **Bit 4**: Custom page table bit.
- **Bit 3**: Custom page table bit.
- **Bit 2**: Custom page table bit.
- **Bit 1**: Custom page table bit.
- **Bit 0**: Present bit.

#### eBPF Instruction

An eBPF instruction is a 64-bit RISC instruction that is executed by the eBPF virtual machine. The instruction format is defined as follows:

```
  63  62  61  60  59  58  57  56  55  54  53  52  51  50  49  48  47  46  45  44  43  42  41  40  39  38  37  36  35  34  33  32
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  31  30  29  28  27  26  25  24  23  22  21  20  19  18  17  16  15  14  13  12  11  10   9   8   7   6   5   4   3   2   1   0
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
```

The fields in the eBPF instruction are defined as follows:

- **Bits 63-59**: Opcode.
- **Bits 58-55**: Source register.
- **Bits 54-51**: Destination register.
- **Bits 50-32**: Immediate value.
- **Bits 31-0**: Offset.

## 4. The Critical Execution Lifecycle

Understanding the critical execution lifecycle is essential for systems programmers working with eBPF and other low-level kernel technologies. This lifecycle encompasses the end-to-end trace of a request, packet, or state transition through the system, from its initial entry to its final exit.

### End-to-End Trace of a Request

When a request enters the system, it is first processed by the network stack, where it is parsed and validated. The request is then passed to the appropriate kernel subsystem, which processes the request and generates a response. In the context of eBPF, this process can be enhanced by attaching eBPF programs to various hooks in the kernel, such as network packets, system calls, and tracepoints. These eBPF programs can be used to monitor and modify the request as it is processed, providing powerful insights into system behavior.

### End-to-End Trace of a Packet

When a packet enters the system, it is first processed by the network interface card (NIC), where it is received and passed to the network stack. The network stack parses the packet and determines its destination, which can be another process on the same machine or a remote machine. The packet is then passed to the appropriate protocol handler, which processes the packet and generates a response. In the context of eBPF, this process can be enhanced by attaching eBPF programs to various hooks in the network stack, such as socket buffers, packet filters, and tracepoints. These eBPF programs can be used to monitor and modify the packet as it is processed, providing powerful insights into network behavior.

### End-to-End Trace of a State Transition

When a state transition occurs in the system, it is typically triggered by an event, such as a system call, timer expiration, or interrupt. The event is processed by the kernel, which updates the system state and generates any necessary responses. In the context of eBPF, this process can be enhanced by attaching eBPF programs to various hooks in the kernel, such as tracepoints, kprobes, and uprobes. These eBPF programs can be used to monitor and modify the state transition as it occurs, providing powerful insights into system behavior.

In conclusion, understanding the core architecture and memory/execution models is essential for systems programmers working with eBPF and other low-level kernel technologies. By delving into the scheduling mechanics, memory subsystems, data structures, and critical execution lifecycle, we gain a deep understanding of how these systems operate and how we can optimize and enhance their performance. This knowledge is crucial for building robust, efficient, and secure systems in the modern infrastructure landscape.
