# Lesson 1: Foundations & Kernel/System Invariants

## Curriculum Roadmap

This lesson establishes the theoretical foundation for distributed systems, kernel boundaries, and non-negotiable system invariants. It provides a comprehensive understanding of the problem space, execution boundaries, and fundamental system guarantees that underpin modern distributed systems.

## 1. First-Principles Problem Space & Execution Boundaries

Distributed systems are complex, dynamic, and inherently concurrent. At their core, they consist of multiple, autonomous components that interact through communication protocols, data exchange, and synchronization mechanisms. To understand the intricacies of distributed systems, it is essential to grasp the fundamental problem space and execution boundaries.

In a distributed system, each component, or node, operates within its own execution context, which includes the kernel, user space, and application code. The kernel, in particular, plays a critical role in managing system resources, enforcing security policies, and providing a stable execution environment for applications.

The problem space of distributed systems can be characterized by the following key aspects:

* **Scalability**: Distributed systems must be designed to scale horizontally, allowing for the addition of new nodes and resources as demand increases.
* **Fault Tolerance**: Distributed systems must be able to withstand node failures, network partitions, and other forms of hardware or software faults.
* **Consistency**: Distributed systems must ensure data consistency across nodes, despite the presence of concurrent updates and network latency.
* **Performance**: Distributed systems must optimize performance, balancing the trade-offs between scalability, fault tolerance, and consistency.

To address these challenges, distributed systems employ a range of mechanisms, including:

* **Consensus protocols**: Such as Raft, Paxos, and Byzantine Fault Tolerance (BFT), which ensure agreement among nodes on system state and decisions.
* **Replication**: Data is duplicated across multiple nodes to ensure availability and consistency.
* **Synchronization**: Mechanisms, such as locks and semaphores, are used to coordinate access to shared resources and prevent data corruption.

## 2. Fundamental System Guarantees & Non-Negotiable Invariants

Distributed systems rely on a set of fundamental system guarantees and non-negotiable invariants to ensure correctness, consistency, and reliability. These invariants include:

* **Atomicity**: Operations must be executed as a single, indivisible unit, ensuring that either all or none of the effects are visible.
* **Consistency**: System state must be consistent across nodes, despite concurrent updates and network latency.
* **Isolation**: Nodes must be isolated from each other, preventing interference and ensuring that each node operates independently.
* **Durability**: System state must be persisted across node failures and network partitions.

These invariants are non-negotiable, meaning that distributed systems must be designed to enforce them at all costs. Failure to do so can result in data corruption, system crashes, and other catastrophic consequences.

## 3. High-Level Process & Subsystem Architecture

A high-level process and subsystem architecture for distributed systems can be represented as follows:

```mermaid
graph LR
    A[Application] -->|API|> B[Service]
    B -->|RPC|> C[Node]
    C -->|Consensus|> D[Cluster]
    D -->|Storage|> E[Database]
```

In this architecture, applications interact with services through APIs, which are implemented using RPC (Remote Procedure Call) protocols. Nodes within the cluster communicate with each other using consensus protocols, ensuring agreement on system state and decisions. Finally, the cluster interacts with a database, which provides persistent storage for system state.

This architecture provides a foundation for understanding the high-level structure and interactions within distributed systems. It highlights the importance of consensus protocols, replication, and synchronization mechanisms in ensuring correctness, consistency, and reliability.

### Exercises

1. Implement a simple consensus protocol (e.g., Raft) using a programming language of your choice.
2. Design a distributed system architecture for a scalable, fault-tolerant, and consistent database.
3. Analyze the trade-offs between scalability, fault tolerance, and consistency in a distributed system.

### References

* [1] O. Shalev and U. Vishkin. "Lock-free data structures." Journal of the ACM, 54(6), 2007.
* [2] M. J. Fischer, N. A. Lynch, and M. S. Paterson. "Impossibility of distributed consensus with one faulty process." Journal of the ACM, 32(2), 1985.
* [3] D. B. Terry, V. J. Kumar, V. Lehman, and S. Seshan. "Statemanagement in a wide-area network." ACM Transactions on Computer Systems, 22(2), 2004.

### Code

```c
#include <stdio.h>
#include <stdlib.h>

// Simple consensus protocol (Raft)
int leader = 0;
int candidates = 0;

void election() {
    // Simulate election process
    if (leader == 0) {
        leader = 1;
        candidates = 1;
    } else {
        candidates++;
    }
}

void heartbeat() {
    // Simulate heartbeat process
    if (leader == 1) {
        printf("Leader: %d\n", leader);
    } else {
        printf("Candidate: %d\n", candidates);
    }
}

int main() {
    election();
    heartbeat();
    return 0;
}
```

Note: The code above is a simplified example of a consensus protocol (Raft) and is not intended for production use.
