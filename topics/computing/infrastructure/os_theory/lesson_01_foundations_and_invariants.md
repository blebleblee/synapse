# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap

This lesson establishes the theoretical groundwork for understanding operating system theory, kernel design, and system invariants. It provides a foundation for subsequent lessons, which will delve into specific topics such as distributed systems, container runtimes, and software exploitation.

## 1. First-Principles Problem Space & Execution Boundaries

The operating system (OS) is a software layer that abstracts hardware resources, providing a platform for running applications and managing system resources. To understand the OS, it is essential to grasp the first-principles problem space and execution boundaries.

The problem space of an OS can be decomposed into three primary components:

1.  **Hardware Abstraction Layer (HAL)**: The HAL provides a software interface to the underlying hardware, abstracting away low-level details such as memory management, I/O operations, and interrupt handling.
2.  **Kernel**: The kernel is the core component of the OS, responsible for managing system resources, scheduling processes, and providing a platform for device drivers.
3.  **User Space**: User space refers to the applications and libraries that run on top of the OS, utilizing the services provided by the kernel and HAL.

Execution boundaries are critical to understanding how the OS manages system resources. The primary execution boundaries are:

*   **Process Boundaries**: Each process has its own memory space, and the OS ensures that processes do not interfere with each other's memory.
*   **Thread Boundaries**: Threads share the same memory space as their parent process, and the OS ensures that threads do not interfere with each other's execution.
*   **System Call Boundaries**: System calls provide a mechanism for user space applications to interact with the kernel, and the OS ensures that system calls are properly validated and executed.

## 2. Fundamental System Guarantees & Non-Negotiable Invariants

The OS provides several fundamental system guarantees, which are non-negotiable invariants that ensure system correctness and reliability. These guarantees include:

*   **Memory Safety**: The OS ensures that memory accesses are valid and do not result in memory corruption or data loss.
*   **Data Integrity**: The OS ensures that data is properly validated and stored, preventing data corruption or loss.
*   **Process Isolation**: The OS ensures that processes do not interfere with each other's execution or memory.
*   **System Call Validation**: The OS ensures that system calls are properly validated and executed, preventing security vulnerabilities.

These guarantees are achieved through a combination of hardware and software mechanisms, including:

*   **Memory Management Units (MMUs)**: MMUs provide a hardware-based mechanism for memory protection and validation.
*   **Page Tables**: Page tables provide a software-based mechanism for memory protection and validation.
*   **System Call Handlers**: System call handlers provide a software-based mechanism for validating and executing system calls.

## 3. High-Level Process & Subsystem Architecture

The following Mermaid diagram illustrates the high-level process and subsystem architecture of a typical OS:
```mermaid
graph LR
    A[HAL] -->|provides hardware abstraction|> B[Kernel]
    B -->|manages system resources|> C[Process Manager]
    C -->|schedules processes|> D[Scheduler]
    D -->|executes processes|> E[Process Execution]
    E -->|interacts with user space|> F[System Call Interface]
    F -->|provides system call services|> G[User Space]
```
This diagram illustrates the relationships between the HAL, kernel, process manager, scheduler, and user space, highlighting the key components and interactions that comprise the OS.

### Exercises

1.  Describe the role of the HAL in providing hardware abstraction.
2.  Explain the difference between process and thread boundaries.
3.  Discuss the importance of memory safety and data integrity in the OS.
4.  Describe the system call validation mechanism and its role in preventing security vulnerabilities.

### References

*   [1] Tanenbaum, A. S. (2001). Modern Operating Systems. Prentice Hall.
*   [2] Bach, M. J. (2006). The Design of the Unix Operating System. Prentice Hall.
*   [3] Bovet, D. P., & Cesati, M. (2005). Understanding the Linux Kernel. O'Reilly Media.
