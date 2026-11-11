# Lesson 3: Advanced Internal Mechanics & Reliability

In this lesson, we'll delve into the intricate mechanisms that underlie the reliability and performance of distributed systems. We'll explore concurrency control, crash recovery, state machines, and high availability, providing a deep understanding of the internal mechanics that enable scalable and fault-tolerant systems.

## 1. Concurrency Control, Lock Scheduling & Conflict Graphs

Concurrency control is a critical aspect of distributed systems, ensuring that multiple transactions or operations can execute simultaneously without interfering with each other. There are several techniques for concurrency control, including:

* **Multi-version concurrency control (MVCC)**: This approach maintains multiple versions of data, allowing transactions to read from previous versions while other transactions are writing to the current version. MVCC is particularly useful in systems with high contention or frequent concurrent updates.
* **Lock-free queues**: These data structures use atomic operations to update shared state, eliminating the need for locks and reducing contention. Lock-free queues are essential in high-performance systems where concurrent access is critical.
* **Latches**: A latch is a lightweight lock that allows multiple threads to access shared data while minimizing contention. Latches are often used in conjunction with lock-free queues to ensure efficient concurrency control.
* **Deadlock detection**: Deadlocks occur when two or more threads are blocked, waiting for each other to release resources. Deadlock detection algorithms, such as the Banker's algorithm, can identify potential deadlocks and prevent them from occurring.

## 2. Write-Ahead Logging & Crash Recovery State Machines

Write-ahead logging (WAL) is a technique used to ensure data consistency in the presence of crashes or failures. WAL involves writing a log of all changes to the database before applying them to the main data structures. This log can be used to recover the database to a consistent state in the event of a failure.

* **Recovery protocols**: Recovery protocols, such as the ARIES (Algorithms for Recovery and Isolation Exploiting Semantics) protocol, use the WAL to recover the database to a consistent state. These protocols involve reading the log, applying the changes, and checking for consistency.
* **Checkpointing invariants**: Checkpointing involves periodically saving the state of the database to a stable storage. Checkpointing invariants ensure that the database can be recovered to a consistent state using the checkpoint and the WAL.
* **Redo/undo logging mechanics**: Redo logging involves writing the changes to the database to a log, while undo logging involves writing the changes to a separate log. Redo/undo logging mechanics ensure that the database can be recovered to a consistent state using the WAL.

## 3. Compaction, Eviction & Garbage Collection Engines

As data is inserted, updated, and deleted, the database can become bloated with unused or redundant data. Compaction, eviction, and garbage collection engines are used to remove this bloat and maintain the performance of the database.

* **Tuples freezing**: Tuples freezing involves temporarily freezing the state of the database to prevent changes while compaction or eviction is occurring.
* **Background worker loops**: Background worker loops are used to perform compaction, eviction, and garbage collection in the background, minimizing the impact on the main database operations.
* **Bloat prevention**: Bloat prevention involves using techniques such as tuple reordering, compression, and deletion to prevent the database from becoming bloated.

## 4. Failure Domains & Byzantine Edge Cases

Failure domains and Byzantine edge cases refer to the potential failures that can occur in a distributed system. These failures can be caused by a variety of factors, including disk corruption, partial writes, network partitions, and malicious actors.

* **Disk corruption**: Disk corruption can occur due to hardware failures, software bugs, or other factors. Disk corruption can be mitigated using techniques such as checksums, redundancy, and error correction.
* **Partial writes**: Partial writes can occur when a write operation is interrupted or fails. Partial writes can be mitigated using techniques such as atomic operations and write-ahead logging.
* **Network partitions**: Network partitions can occur when a network connection is lost or interrupted. Network partitions can be mitigated using techniques such as replication, redundancy, and failover.
* **Mitigations**: Mitigations involve using techniques such as redundancy, replication, and failover to ensure that the system remains available and consistent in the presence of failures.
