# Lesson 3: Advanced Internal Mechanics & Reliability

## 1. Concurrency Control, Lock Scheduling & Conflict Graphs

In the realm of distributed databases and concurrent systems, ensuring data consistency and integrity is paramount. Concurrency control mechanisms are employed to manage simultaneous access to shared resources, preventing data corruption and ensuring that transactions are executed reliably. At the heart of concurrency control lies the concept of locks, which are used to synchronize access to critical sections of code.

### Lock Scheduling

Lock scheduling algorithms determine the order in which locks are acquired and released. Two primary approaches exist: optimistic and pessimistic locking. Optimistic locking assumes that concurrent transactions will not conflict, and if a conflict arises, it is resolved through retry or abort. Pessimistic locking, on the other hand, assumes that conflicts are inevitable and uses locks to prevent concurrent access.

### Multi-Version Concurrency Control

Multi-version concurrency control (MVCC) is a technique that allows multiple versions of a data item to coexist. Each transaction sees a consistent view of the data, and changes are made by creating new versions of the data item. This approach eliminates the need for locks, as transactions can operate on different versions of the data.

### Conflict Graphs

Conflict graphs are used to detect and resolve conflicts between concurrent transactions. A conflict graph represents the relationships between transactions, with edges indicating potential conflicts. By analyzing the conflict graph, the system can determine which transactions can be executed concurrently and which require serialization.

## 2. Write-Ahead Logging & Crash Recovery State Machines

Write-ahead logging (WAL) is a technique used to ensure data durability in the presence of crashes or failures. WAL involves writing all changes to a log before applying them to the main data store. In the event of a crash, the system can recover by replaying the log entries.

### Recovery Protocols

Recovery protocols are used to ensure that the system can recover from crashes or failures. Two primary approaches exist: checkpointing and redo/undo logging. Checkpointing involves periodically saving the state of the system, allowing for quick recovery in the event of a crash. Redo/undo logging involves maintaining a log of changes, which can be used to recover the system.

### Checkpointing Invariants

Checkpointing invariants are used to ensure that the system can recover from crashes or failures. A checkpointing invariant is a property that must be maintained throughout the checkpointing process. By ensuring that the checkpointing invariant is maintained, the system can recover from crashes or failures.

## 3. Compaction, Eviction & Garbage Collection Engines

Compaction, eviction, and garbage collection are used to manage memory and prevent memory bloat. Compaction involves reorganizing the memory to eliminate free space, while eviction involves removing unused data from memory. Garbage collection involves identifying and reclaiming memory occupied by unused data.

### Tuples Freezing

Tuples freezing is a technique used to prevent memory bloat. When a tuple is frozen, it is marked as immutable, preventing further modifications. This approach eliminates the need for garbage collection, as frozen tuples are not subject to modification.

### Background Worker Loops

Background worker loops are used to perform tasks such as garbage collection and compaction. These loops run in the background, ensuring that memory is managed efficiently and preventing memory bloat.

## 4. Failure Domains & Byzantine Edge Cases

Failure domains and Byzantine edge cases are used to identify and mitigate potential failures. Failure domains are regions of the system that are prone to failure, while Byzantine edge cases are scenarios that can cause the system to fail.

### Disk Corruption

Disk corruption can occur due to hardware failures or software bugs. To mitigate disk corruption, systems use techniques such as checksums and redundancy.

### Partial Writes

Partial writes can occur due to hardware failures or software bugs. To mitigate partial writes, systems use techniques such as atomic writes and transactional memory.

### Network Partitions

Network partitions can occur due to hardware failures or software bugs. To mitigate network partitions, systems use techniques such as distributed consensus and fault-tolerant protocols.

### Mitigations

Mitigations are used to prevent or recover from failures. Techniques such as redundancy, checksums, and distributed consensus are used to mitigate failures and ensure system reliability.
