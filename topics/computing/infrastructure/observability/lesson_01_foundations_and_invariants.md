# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap

This lesson establishes the theoretical foundation for the Observability masterclass, focusing on kernel and system invariants essential for designing and operating large-scale distributed systems. By the end of this lesson, you will understand the fundamental mechanisms governing system behavior, the boundaries of kernel and user-space interactions, and the non-negotiable invariants that ensure system reliability and performance.

## 1. First-Principles Problem Space & Execution Boundaries

The kernel is the core of the operating system, responsible for managing hardware resources, providing a platform for user-space applications, and enforcing system security policies. To grasp the kernel's role, let's dissect the problem space and execution boundaries.

The kernel's primary function is to abstract hardware resources, allowing user-space applications to interact with the system without directly accessing hardware components. This abstraction is achieved through a set of system calls, which provide a standardized interface for applications to request kernel services. System calls are the primary means of communication between user-space applications and the kernel.

To understand the kernel's execution boundaries, consider the following:

*   **Kernel Space**: The kernel executes in a privileged mode, with direct access to hardware resources. This mode is characterized by a set of kernel-specific registers, such as the Program Counter (PC), Stack Pointer (SP), and Control Registers (CR).
*   **User Space**: User-space applications execute in a non-privileged mode, with restricted access to hardware resources. This mode is characterized by a set of user-space registers, such as the User Program Counter (UPC) and User Stack Pointer (USP).
*   **System Call Interface**: The system call interface is the boundary between kernel and user space. It provides a standardized interface for applications to request kernel services, such as process creation, memory allocation, and I/O operations.

```markdown
Kernel Space (privileged mode)
---------------------------

*   Program Counter (PC)
*   Stack Pointer (SP)
*   Control Registers (CR)

User Space (non-privileged mode)
-------------------------------

*   User Program Counter (UPC)
*   User Stack Pointer (USP)

System Call Interface (boundary between kernel and user space)
---------------------------------------------------------

*   System calls for process creation
*   System calls for memory allocation and deallocation
*   System calls for I/O operations
```

## 2. Fundamental System Guarantees & Non-Negotiable Invariants

To ensure system reliability and performance, the kernel enforces a set of fundamental system guarantees and non-negotiable invariants. These invariants are essential for maintaining system integrity and preventing common pitfalls such as data corruption, resource leaks, and security breaches.

Some of the key system guarantees and invariants include:

*   **Memory Safety**: The kernel ensures memory safety by enforcing bounds checking, preventing buffer overflows, and managing memory allocation and deallocation.
*   **Resource Isolation**: The kernel provides resource isolation, ensuring that applications do not interfere with each other's resources, such as memory, CPU, and I/O devices.
*   **Security Policies**: The kernel enforces security policies, such as access control, authentication, and authorization, to prevent unauthorized access to system resources.

```markdown
System Guarantees
----------------

*   Memory Safety
*   Resource Isolation
*   Security Policies
```

## 3. High-Level Process & Subsystem Architecture

To illustrate the high-level process and subsystem architecture, consider the following Mermaid diagram:

```mermaid
graph LR
    A[Kernel] -->|System Call Interface|> B[User Space]
    B -->|System Call|> C[Kernel]
    C -->|Service|> D[Hardware Resources]
    D -->|Resource|> E[Kernel]
    E -->|Notification|> F[User Space]
```

This diagram illustrates the interaction between kernel and user space, highlighting the system call interface, kernel services, and hardware resource management.

By understanding the kernel's role, execution boundaries, and fundamental system guarantees and invariants, you will be well-equipped to design and operate large-scale distributed systems that are reliable, performant, and secure.

## Exercises

1.  Write a system call to request kernel services for process creation.
2.  Implement a kernel module to manage memory allocation and deallocation.
3.  Design a security policy to enforce access control and authentication.

## References

1.  "The Linux Kernel" by Robert Love
2.  "Operating Systems: Three Easy Pieces" by Remzi Arpaci-Dusseau and Andrea Arpaci-Dusseau
3.  "The Design of the Unix Operating System" by Maurice J. Bach
