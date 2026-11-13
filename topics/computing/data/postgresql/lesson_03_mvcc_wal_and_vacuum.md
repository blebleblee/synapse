```markdown
# Lesson 3: Multiversion Concurrency Control (MVCC), WAL & Vacuum Engine

## 1. Physical Heap Page Layout & The Anatomy of a Tuple

PostgreSQL stores every relation—tables, sequences, TOAST tables, and certain index types—as a collection of fixed-size 8 KB pages on the filesystem at `$PGDATA/base/<db_oid>/<relfilenode>`. When a relation exceeds 1 GB, PostgreSQL transparently creates additional segment files named `<relfilenode>.1`, `<relfilenode>.2`, and so on (the 1 GB boundary is set at compile time via `BLCKSZ` and `DEFAULT_RELSEG_SIZE`, but 8 KB / 1 GB are universal defaults). The page format is defined in `src/include/storage/bufpage.h` and has remained structurally stable across all major PostgreSQL versions.

To understand lock-free concurrency and mutation semantics at their root, one must first understand the anatomy of a single 8 KB heap page.

```
+------------------------------------------------------------------------+
| PageHeaderData (24 bytes)                                              |
|  pd_lsn        (8 bytes)  — LSN of last WAL record touching this page |
|  pd_checksum   (2 bytes)  — optional CRC-16 of page content           |
|  pd_flags      (2 bytes)  — PD_HAS_FREE_LINES, PD_PAGE_FULL, etc.    |
|  pd_lower      (2 bytes)  — byte offset to start of free space        |
|  pd_upper      (2 bytes)  — byte offset to end of free space          |
|  pd_special    (2 bytes)  — byte offset to start of special space     |
|  pd_pagesize_version      — encoded page size + layout version        |
|  pd_prune_xid  (4 bytes)  — oldest deletable t_xmax on page (hint)   |
+------------------------------------------------------------------------+
| ItemIdData Array (line pointers, 4 bytes each, grows toward pd_lower) |
|  [lp_1: lp_off=15 bits, lp_flags=2 bits, lp_len=15 bits]             |
|  [lp_2] [lp_3] ...                                                    |
+------------------------------------------------------------------------+
|                                                                        |
|                      F R E E   S P A C E                              |
|            (pd_lower ———————————————————> pd_upper)                   |
|                                                                        |
+------------------------------------------------------------------------+
| HeapTupleData payloads (grow upward from page bottom toward pd_upper) |
|  [Tuple N: HeapTupleHeaderData (23 bytes) + null bitmap + columns]    |
|  ...                                                                   |
|  [Tuple 2: HeapTupleHeaderData + null bitmap + columns]               |
|  [Tuple 1: HeapTupleHeaderData + null bitmap + columns]               |
+------------------------------------------------------------------------+
| Special Space (index-type metadata; 0 bytes for heap tables)          |
+------------------------------------------------------------------------+
```

The key invariant is that `pd_lower` grows downward as line pointers are appended, and `pd_upper` grows upward as tuple payloads are prepended. Free space is the gap between them: `free = pd_upper - pd_lower`. The `pd_prune_xid` field is a performance hint that allows page-level pruning to be skipped if no dead tuples could possibly be older than the current global `OldestXmin`.

### 1.1. The `ItemIdData` Line Pointer

Each line pointer is exactly 4 bytes encoding three fields:

| Field | Bits | Purpose |
|---|---|---|
| `lp_off` | 15 | Byte offset of tuple from page start |
| `lp_flags` | 2 | `LP_UNUSED` (0), `LP_NORMAL` (1), `LP_REDIRECT` (2), `LP_DEAD` (3) |
| `lp_len` | 15 | Length of tuple in bytes |

`LP_REDIRECT` is the cornerstone of the **HOT chain** mechanism (Section 4.1). `LP_DEAD` signals to index scans that this pointer is immediately recyclable without a heap fetch, enabling index-only vacuum optimizations.

### 1.2. The 23-Byte `HeapTupleHeaderData` Structure

Every row version on disk is prefixed by this C structure (defined in `src/include/access/htup_details.h`):

```c
typedef struct HeapTupleFields {
    TransactionId t_xmin;    /* 4 bytes: inserting transaction ID     */
    TransactionId t_xmax;    /* 4 bytes: deleting/locking xact ID     */
    union {
        CommandId   t_cid;   /* 4 bytes: insert/delete command ID     */
        TransactionId t_xvac;/* used by VACUUM FULL during page moves */
    } t_field3;
} HeapTupleFields;

typedef struct HeapTupleHeaderData {
    union {
        HeapTupleFields t_heap;
        DatumTupleFields t_datum; /* used for composite type datums    */
    } t_choice;

    ItemPointerData t_ctid;  /* 6 bytes: TID of current row version   */
    uint16          t_infomask2; /* 2 bytes: attribute count + flags  */
    uint16          t_infomask;  /* 2 bytes: visibility hint flags    */
    uint8           t_hoff;      /* 1 byte: offset to user data       */
    /* BITMAPSET of null attributes follows if HEAP_HASNULL is set    */
    /* Then column data aligned per attalign requirements             */
} HeapTupleHeaderData;
```

The fields carry precise semantic meaning in the MVCC protocol:

**`t_xmin` (TransactionId, 4 bytes):** The transaction that created (INSERTed) this tuple version. A tuple is only potentially visible if its `t_xmin` has committed. Readers check `pg_xact` (the commit log, formerly `pg_clog`) or the cached hint bits to determine this.

**`t_xmax` (TransactionId, 4 bytes):** The transaction that deleted or superseded this tuple version. A value of `InvalidTransactionId` (0) means no delete has been executed. For a row locked in `FOR UPDATE`/`FOR SHARE` mode without deletion, `t_xmax` is set to the locker's XID but the `HEAP_XMAX_IS_EXCL_LOCKED` or `HEAP_XMAX_KEYSHR_LOCK` hint bits in `t_infomask` distinguish a lock from a delete.

**`t_cid` (CommandId, 4 bytes):** A within-transaction statement counter. This ensures that if a transaction executes `UPDATE t SET v=2` and then `SELECT * FROM t` as its second statement, the second statement does not see the row it just updated as both old and new—the `CommandId` monotonically orders intra-transaction visibility.

**`t_ctid` (ItemPointerData, 6 bytes):** A physical self-pointer `(block_number, offset_number)`. For a live, unupdated tuple, `t_ctid` points to itself. When an `UPDATE` creates a new tuple version, the old tuple's `t_ctid` is updated to point to the new tuple's location, forming a **forward update chain**. This chain is the structural backbone of HOT pruning.

**`t_infomask` and `t_infomask2` (4 bytes combined):** These bit fields are **visibility hint bits**—a critical performance optimization. Rather than consulting `pg_xact` (a random I/O) on every tuple access, once a backend confirms that `t_xmin` has committed, it sets `HEAP_XMIN_COMMITTED` in `t_infomask` as a hint. Subsequent readers short-circuit the `pg_xact` lookup. These bits are set lazily (not WAL-logged in older versions, though PostgreSQL 9.3+ hint bit WAL logging can be enabled) and serve as a cache. Key flags:

| Flag | Meaning |
|---|---|
| `HEAP_XMIN_COMMITTED` | `t_xmin` is known committed |
| `HEAP_XMIN_INVALID` | `t_xmin` is known aborted or invalid |
| `HEAP_XMAX_COMMITTED` | `t_xmax` is known committed (tuple is dead) |
| `HEAP_XMAX_INVALID` | `t_xmax` is invalid (tuple is live) |
| `HEAP_XMAX_IS_EXCL_LOCKED` | `t_xmax` holds an exclusive row lock, not a delete |
| `HEAP_XMIN_FROZEN` | Tuple has been frozen; visible to all transactions |
| `HEAP_HASVARWIDTH` | Row contains variable-length attributes |
| `HEAP_HASNULL` | Null bitmap follows the header |

```mermaid
graph TD
    subgraph "8 KB Heap Page (block N)"
        PH["PageHeaderData\npd_lsn=0/4A1C3F20\npd_lower=96, pd_upper=6240"]
        LP1["lp_1: off=8128, flags=LP_NORMAL, len=52"]
        LP2["lp_2: off=8072, flags=LP_REDIRECT → lp_3"]
        LP3["lp_3: off=7996, flags=LP_NORMAL, len=76"]
        FS["FREE SPACE (6240 - 96 = 6144 bytes)"]
        T3["Tuple at off=7996\nt_xmin=502, t_xmax=0\nt_ctid=(N,3
