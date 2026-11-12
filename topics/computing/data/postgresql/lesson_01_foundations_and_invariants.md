# Lesson 1: Foundations & Storage Invariants

Welcome to the PostgreSQL Relational Engine & Systems Engineering Curriculum. This course is constructed for systems engineers, database administrators, and infrastructure architects who need first-principles mastery of PostgreSQL internals.

PostgreSQL does not treat the relational database as an opaque black box. Its process model, shared memory architecture, heap page layout, and write-ahead logging (WAL) are directly anchored in POSIX kernel primitives and classical systems architecture. To reason about database performance, concurrency contention, and recovery state machines, one must understand the foundational invariants that govern how data transitions from client processes into volatile shared memory and persistent disk storage.

---

## 1. The Relational Contract & First-Principles Systems Philosophy

A relational database engine exists to solve a fundamental physical tension: persistent storage media (NVMe drives, SSDs, spinning magnetic rust) have high latency and block-oriented access patterns, while client applications require microsecond transaction isolation, arbitrary predicate queries, and strict serializability guarantees.

PostgreSQL balances these trade-offs by operating essentially as an operating system within an operating system:

```mermaid
graph TD
    Client[Client Application] -->|"TCP Connection / TLS"| PM[Postmaster Daemon - PID 1]
    PM -->|"fork & exec"| BE[Dedicated Backend Worker Process]
    BE <-->|"Direct Read / Write via Latches"| SHM[\"(Shared Memory Segments: Buffer Pool, WAL, Locks)\"]
    SHM <-->|"Block-Level Asynchronous Flush"| Storage[\"(Persistent Storage: 8KB Slotted Heap Pages & WAL Segments)\"]
    BGW[Background Auxiliary Daemons: Checkpointer, BgWriter, WalWriter, Autovacuum] <--> SHM
```

Unlike modern database engines that utilize multi-threaded architectures (such as MySQL InnoDB or Microsoft SQL Server), PostgreSQL maintains a strict **process-per-connection** execution model inherited from its UC Berkeley POSTGRES heritage:

1. **Process Memory Isolation:** Every connected client session is serviced by an independent OS backend process spawned via `fork()`. A memory corruption, segmentation fault, or catastrophic buffer overrun in one connection terminates only that backend process without directly corrupting the memory space of sibling clients.
2. **Coordinated Shared State:** Inter-process coordination is achieved not through thread-level shared memory heaps, but via a dedicated POSIX/System V shared memory segment mapped uniformly into the virtual address space of every backend.
3. **No Hidden State:** The kernel is treated as an active partner. PostgreSQL relies heavily on kernel page caches, raw POSIX synchronous write primitives (`fdatasync`, `O_DIRECT`), and UNIX domain sockets for maximum IPC throughput.

---

## 2. Slotted-Page Binary Format & Physical Heap Layout

At the lowest physical storage layer, tables and indexes in PostgreSQL are stored on disk as collections of fixed-size **8 Kilobyte (8192-byte) disk pages** (often referred to as *blocks*). An individual table relation is broken into 1GB segment files (`relfilenode`, `relfilenode.1`, etc.) within the database directory hierarchy.

To efficiently accommodate variable-length rows, updates, and deletes without requiring constant defragmentation, PostgreSQL uses a classical **Slotted Page** architecture:

```text
+-----------------------------------------------------------------------+
| PageHeaderData (24 bytes)                                             |
|   pd_lsn (8 bytes)       : LSN of last WAL byte that modified page   |
|   pd_checksum (2 bytes)  : Page CRC checksum                          |
|   pd_flags (2 bytes)     : Allocation and visibility flags            |
|   pd_lower (2 bytes)     : Byte offset to end of line pointers        |
|   pd_upper (2 bytes)     : Byte offset to start of lowest raw tuple   |
|   pd_special (2 bytes)   : Offset to special page trailer (indexes)   |
+-----------------------------------------------------------------------+
| ItemIdData Array (Line Pointers, 4 bytes each)                        |
|   [Item 1: offset, flags, len] -> points to Tuple 1                   |
|   [Item 2: offset, flags, len] -> points to Tuple 2                   |
|   [Item 3: offset, flags, len] (pd_lower marks boundary)              |
|                     |                                                 |
|                     v  (Grows Downwards)                              |
+-----------------------------------------------------------------------+
|                       UNALLOCATED FREE SPACE                          |
|                     ^  (Grows Upwards)                                |
|                     |                                                 |
+-----------------------------------------------------------------------+
| HeapTupleData (Raw Tuples, allocated from bottom up)                  |
|   Tuple 2 (HeapTupleHeaderData + Null Bitmap + User Attributes)       |
|   Tuple 1 (HeapTupleHeaderData + Null Bitmap + User Attributes)       |
|   (pd_upper marks boundary)                                           |
+-----------------------------------------------------------------------+
| Special Space (Index-specific trailing metadata, 0 bytes on heap)    |
+-----------------------------------------------------------------------+
```

### The Two-Way Growth Invariant

1. **Item Pointers Grow Downward:** The `ItemIdData` array (line pointers) starts immediately after the 24-byte header and grows downward toward higher memory offsets. Each item pointer occupies 4 bytes and stores:
   * `lp_off`: The physical byte offset from the start of the page to the tuple data.
   * `lp_flags`: Pointer state (`LP_NORMAL` for valid tuples, `LP_REDIRECT` for HOT chains, `LP_DEAD` for vacuum-eligible dead slots).
   * `lp_len`: Exact physical byte length of the tuple.
2. **Tuples Grow Upward:** Actual row payloads (heap tuples) are inserted starting from the very bottom of the page and grow upward toward lower memory offsets.
3. **The Free Space Hole:** The remaining usable space on the page is strictly defined as `pd_upper - pd_lower`. When this difference is less than `sizeof(ItemIdData) + tuple_length`, the page is considered full and cannot accommodate a new insert.

### Heap Tuple Header Structure (`HeapTupleHeaderData`)

Every individual row on a page carries a mandatory 23-byte header preceding user data:
* `t_xmin`: The Transaction ID (XID) of the inserting transaction.
* `t_xmax`: The Transaction ID of the deleting or updating transaction (0 if live and unmodified).
* `t_cid`: The Command Identifier within the transaction that created or deleted the row.
* `t_infomask` / `t_infomask2`: Bitwise flags storing visibility state (e.g., `HEAP_XMIN_COMMITTED`, `HEAP_XMIN_INVALID`, `HEAP_XMAX_COMMITTED`, `HEAP_HOT_UPDATED`).
* `t_hoff`: Offset to user data, accommodating optional Null Bitmaps and Object Identifiers (OIDs).

---

## 3. The Four Non-Negotiable Storage Invariants

All relational correctness, concurrency, and durability in PostgreSQL depend on four immutable systems invariants:

### Invariant 1: The Write-Ahead Logging (WAL) Contract
$$\text{WAL Flush LSN} \ge \text{Page } pd\_lsn$$
* **The Rule:** A dirty 8KB shared buffer page may **never** be written to persistent storage by a backend, BgWriter, or Checkpointer until all WAL records describing modifications to that page have been completely fsynced to disk up to the page's current `pd_lsn`.
* **Mechanical Rationale:** If a power failure occurs while flushing a dirty data page whose corresponding WAL log was still in volatile RAM, the database on-disk state is hopelessly corrupted and unrecoverable. Adhering to the WAL invariant guarantees that crash recovery (via `REDO` replay) can always reconstruct consistency.

### Invariant 2: Reader-Writer Non-Blocking Concurrency (MVCC)
* **The Rule:** Readers never block writers, and writers never block readers.
* **Mechanical Rationale:** Rather than acquiring read shared locks on table rows (which would serialize concurrent transactions), PostgreSQL evaluates tuple visibility using snapshot horizons. When a row is updated, PostgreSQL does not overwrite the existing bytes; it writes a brand new version of the row (*tuple*) to the page, sets the old row's `t_xmax` to the current transaction ID, and sets the new row's `t_xmin`.

### Invariant 3: Single-Writer Heap Page Latching
* **The Rule:** Modifying an 8KB buffer page requires an **Exclusive Buffer Latch**, while reading requires a **Shared Buffer Latch**.
* **Mechanical Rationale:** Latches are lightweight, short-lived spinlocks/semaphores internal to the PostgreSQL server. While transactions do not lock rows during read queries, the engine must still guarantee memory safety so that concurrent backends do not read half-written binary bytes while another backend splits or compacts line pointers.

### Invariant 4: Transaction ID Modular Horizon & Freeze Boundary
$$\text{Current XID} - t\_xmin < 2^{31}$$
* **The Rule:** No tuple in any table may have an un-frozen `t_xmin` older than $2^{31} - 1$ transactions before the current cluster transaction counter.
* **Mechanical Rationale:** PostgreSQL uses 32-bit transaction IDs, meaning XIDs wrap around cyclically modulo $2^{32}$. To distinguish whether a transaction ID happened in the past or in the future, PostgreSQL uses modular arithmetic: if $XID_A < XID_B$ within a $2^{31}$ window, it is considered past. If unmanaged, old data would suddenly appear to have been created in the future and vanish from query results. Autovacuum enforces this invariant by "freezing" ancient tuples (`HEAP_XMIN_FROZEN`).

---

## 4. Key Takeaways & Architecture Summary

| Architectural Subsystem | Design Implementation | Systems Rationale |
| :--- | :--- | :--- |
| **Concurrency Architecture** | Multi-process (`fork`) | Memory fault isolation and crash containment |
| **Page Granularity** | Fixed 8192-byte slotted pages | Aligns with OS memory pages and disk block I/O |
| **Row Insertion Geometry** | Pointers downward, rows upward | Minimizes fragmentation; dynamic variable-width rows |
| **Crash Recovery** | ARIES-style Write-Ahead Logging | Guarantees atomic replay after sudden power cutoff |
| **Visibility Model** | Append-only tuple versioning (`xmin`/`xmax`) | Zero-lock read concurrency for high throughput |
