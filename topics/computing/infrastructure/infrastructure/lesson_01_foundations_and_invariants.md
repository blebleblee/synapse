# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap

This lesson establishes the theoretical foundation for the infrastructure curriculum, focusing on kernel and system invariants that underpin modern computing systems. By the end of this lesson, students will have a deep understanding of the fundamental mechanisms and trade-offs that govern system behavior.

## 1. First-Principles Problem Space & Execution Boundaries

To grasp the intricacies of modern computing systems, it is essential to understand the first-principles problem space and execution boundaries. The problem space encompasses the set of all possible system configurations, while execution boundaries define the limits within which the system operates.

A computing system is a complex, dynamic entity that interacts with its environment through a series of abstract interfaces. These interfaces, such as the operating system's process abstraction, define the boundaries within which the system executes. Understanding these boundaries is crucial for designing and optimizing systems that meet the demands of modern applications.

Consider the Linux kernel, for example. The kernel's process abstraction is implemented through the `task_struct` data structure, which provides a fundamental interface for managing process execution. The kernel's process scheduling algorithm, based on the Completely Fair Scheduler (CFS), ensures that processes are executed in a fair and efficient manner.

```markdown
struct task_struct {
    pid_t pid;
    struct mm_struct *mm;
    struct completion *completion;
    // ...
};
```

## 2. Fundamental System Guarantees & Non-Negotiable Invariants

A computing system's behavior is governed by a set of fundamental system guarantees and non-negotiable invariants. These invariants ensure that the system operates within well-defined boundaries, providing a predictable and reliable environment for applications to execute.

Some key invariants include:

Memory safety: The system ensures that memory accesses are valid and do not lead to data corruption or crashes.

Data integrity: The system guarantees that data is not modified or deleted unexpectedly, ensuring that applications can rely on consistent data.

Process isolation: The system ensures that processes do not interfere with each other's execution, preventing unexpected behavior or crashes.

These invariants are non-negotiable because they are essential for ensuring the reliability and predictability of the system. Failure to uphold these invariants can have severe consequences, including data corruption, system crashes, or even security breaches.

## 3. High-Level Process & Subsystem Architecture

To illustrate the high-level process and subsystem architecture, consider the following Mermaid diagram:
```mermaid
graph LR
    subgraph Kernel
        OS["Operating System"]
        Scheduler["Scheduler"]
        Memory Manager["Memory Manager"]
    end

    subgraph Process
        Process["Process"]
        Thread["Thread"]
        Context["Context"]
    end

    OS -->|Process Creation|> Process
    Process -->|Thread Creation|> Thread
    Thread -->|Context Switch|> Context
    Memory Manager -->|Memory Allocation|> Process
    Scheduler -->|Scheduling|> Process
```
This diagram shows the high-level interactions between the kernel and process subsystems, highlighting the key components and interfaces that govern system behavior.

By understanding the fundamental mechanisms and trade-offs that govern system behavior, students will be well-equipped to design and optimize modern computing systems that meet the demands of modern applications.
