# Lesson 3: Advanced Internal Mechanics & Reliability

As we delve deeper into the internal mechanics of databases, we'll explore the intricate mechanisms that ensure data consistency, reliability, and high availability. This lesson will cover the advanced topics of concurrency control, crash recovery, state machines, and high availability.

## 1. Concurrency Control, Lock Scheduling & Conflict Graphs

Concurrency control is the mechanism by which multiple transactions can access shared data without interfering with each other. In this section, we'll examine the following key concepts:

*   **Multi-version concurrency control**: This approach involves maintaining multiple versions of data, allowing transactions to access different versions without conflicts. We'll discuss the implementation of multi-version concurrency control using timestamp ordering and vector clocks.
*   **Lock-free queues**: Lock-free data structures are designed to avoid the use of locks, which can lead to contention and performance issues. We'll explore the implementation of lock-free queues using atomic operations and compare-and-swap instructions.
*   **Latches**: Latches are a type of lock that allows multiple threads to access shared data while preventing concurrent modifications. We'll discuss the implementation of latches using atomic operations and the use of latches in database concurrency control.
*   **Deadlock detection**: Deadlocks occur when two or more transactions are blocked, waiting for each other to release resources. We'll discuss the use of deadlock detection algorithms, such as the Banker's algorithm, to prevent deadlocks in database concurrency control.

## 2. Write-Ahead Logging & Crash Recovery State Machines

Write-ahead logging is a mechanism that ensures data consistency by logging all changes to data before they are committed. In this section, we'll examine the following key concepts:

*   **Recovery protocols**: Recovery protocols are used to restore a database to a consistent state after a crash or failure. We'll discuss the implementation of recovery protocols using write-ahead logging and checkpointing.
*   **Checkpointing invariants**: Checkpointing involves periodically saving the state of a database to a stable storage device. We'll discuss the implementation of checkpointing invariants and their use in crash recovery.
*   **Redo/undo logging mechanics**: Redo logging involves logging all changes to data before they are committed, while undo logging involves logging all changes to data before they are committed. We'll discuss the implementation of redo/undo logging mechanics and their use in crash recovery.

## 3. Compaction, Eviction & Garbage Collection Engines

Compaction, eviction, and garbage collection are mechanisms used to manage memory and prevent memory leaks in databases. In this section, we'll examine the following key concepts:

*   **Tuples freezing**: Tuples freezing involves freezing tuples in memory to prevent them from being garbage collected. We'll discuss the implementation of tuples freezing and its use in database memory management.
*   **Background worker loops**: Background worker loops are used to perform tasks such as compaction and eviction in the background. We'll discuss the implementation of background worker loops and their use in database memory management.
*   **Bloat prevention**: Bloat prevention involves preventing the growth of memory usage in databases. We'll discuss the implementation of bloat prevention mechanisms and their use in database memory management.

## 4. Failure Domains & Byzantine Edge Cases

Failure domains and Byzantine edge cases are scenarios that can occur in databases, such as disk corruption, partial writes, and network partitions. In this section, we'll examine the following key concepts:

*   **Disk corruption**: Disk corruption involves data corruption on a disk device. We'll discuss the implementation of disk corruption detection and recovery mechanisms.
*   **Partial writes**: Partial writes involve writing data to a disk device in a way that is not atomic. We'll discuss the implementation of partial write detection and recovery mechanisms.
*   **Network partitions**: Network partitions involve a network failure that prevents communication between nodes. We'll discuss the implementation of network partition detection and recovery mechanisms.
*   **Mitigations**: Mitigations involve mechanisms used to prevent or recover from failure domains and Byzantine edge cases. We'll discuss the implementation of mitigations and their use in database failure domains and Byzantine edge cases.
