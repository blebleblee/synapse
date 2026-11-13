# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap

This lesson establishes the theoretical foundation for the Devsecops masterclass, focusing on the kernel and system invariants that underpin modern computing infrastructure. By the end of this lesson, students will have a deep understanding of the fundamental mechanisms and trade-offs that govern system behavior, enabling them to design and deploy secure, scalable, and efficient infrastructure.

## 1. First-Principles Problem Space & Execution Boundaries

At its core, computing is about executing a sequence of instructions on a machine. The problem space consists of the input data, the program, and the machine itself. To understand the behavior of a system, we must consider the execution boundaries that govern how these components interact.

The machine is comprised of a CPU, memory, and I/O devices. The CPU executes instructions, which are stored in memory. I/O devices provide input/output operations, such as reading from a disk or sending data over a network. The program, written in a high-level language, is compiled into machine code that the CPU can execute.

The execution boundary between the program and the machine is defined by the operating system (OS). The OS provides a layer of abstraction between the program and the hardware, managing resources such as memory, CPU time, and I/O devices. The OS also enforces security policies, ensuring that programs do not access sensitive data or perform unauthorized actions.

```markdown
// Example of a simple program that prints "Hello, World!"
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
```

This program, written in C, is compiled into machine code that the CPU can execute. The OS loads the program into memory, allocates resources as needed, and executes the instructions.

## 2. Fundamental System Guarantees & Non-Negotiable Invariants

A system's behavior is governed by a set of fundamental guarantees and non-negotiable invariants. These invariants ensure that the system behaves predictably and reliably, even in the presence of faults or errors.

One such invariant is the memory safety guarantee, which ensures that programs do not access memory outside their allocated bounds. This is achieved through mechanisms such as memory protection, bounds checking, and garbage collection.

Another invariant is the data integrity guarantee, which ensures that data is not corrupted or tampered with during transmission or storage. This is achieved through mechanisms such as checksums, digital signatures, and encryption.

```markdown
Memory Safety ⇒ No memory access outside allocated bounds
Data Integrity ⇒ Data is not corrupted or tampered with
```

These invariants are non-negotiable, meaning that they must be enforced at all times to ensure the system's reliability and security.

## 3. High-Level Process & Subsystem Architecture

A high-level process and subsystem architecture is essential for understanding how systems interact and how they can be designed and deployed securely.

The following Mermaid diagram illustrates a high-level view of a system's architecture:
```mermaid
graph LR
    A[User] -->|Request|> B[Web Server]
    B -->|Response|> C[Database]
    C -->|Data|> D[Cache]
    D -->|Cache Hit|> E[Web Server]
    E -->|Response|> A
```

This diagram shows how a user requests data from a web server, which retrieves the data from a database and stores it in a cache. The web server then returns the response to the user.

By understanding the fundamental mechanisms and trade-offs that govern system behavior, students will be able to design and deploy secure, scalable, and efficient infrastructure that meets the needs of modern computing applications.

## Exercises

1. Write a program that demonstrates the memory safety guarantee by attempting to access memory outside the allocated bounds.
2. Implement a simple checksum algorithm to ensure data integrity during transmission or storage.
3. Design a high-level process and subsystem architecture for a web application, considering the interactions between the user, web server, database, and cache.

## References

* [1] Tanenbaum, A. S., & Woodhull, A. S. (2018). Operating Systems: Design and Implementation. Prentice Hall.
* [2] Stevens, W. R. (1998). Advanced Programming in the UNIX Environment. Addison-Wesley.
* [3] Lea, D. (2000). Java Concurrency in Practice. Addison-Wesley.
