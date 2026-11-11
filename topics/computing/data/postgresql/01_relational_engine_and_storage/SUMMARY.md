# Executive Curriculum Summary: PostgreSQL Relational Engine & Storage

## 1. High-Level Invariants & System Guarantees

1. **Process Isolation Over Threads:** PostgreSQL's multi-process model isolates memory heaps per connection, guaranteeing that a memory violation or segfault in a client worker does not corrupt sibling backends.
2. **Double Buffering:** Reading from PostgreSQL utilizes both the kernel page cache and PostgreSQL's internal `shared_buffers` (8KB pages managed by a lockless Clock Sweep circular algorithm).
3. **The WAL Invariant:** No dirty 8KB shared buffer page may ever be flushed to persistent disk storage until all preceding WAL records up to `page.pd_lsn` have been fsynced.
4. **Lock-Free Concurrency (MVCC):** Snapshot isolation guarantees that readers inspect tuple visibility bounds (`xmin`, `xmax`, `t_infomask`) without waiting for locks, meaning readers never block writers and writers never block readers.
5. **The Wraparound Horizon:** To prevent transaction ID modular wraparound past the $2^{31}$ horizon, Autovacuum aggressively freezes ancient tuples with `HEAP_XMIN_FROZEN`.
6. **Lehman-Yao B-Trees:** Index concurrent access uses high keys and right-link pointers to allow node splits without parent locking, enabling high write concurrency.
7. **Production HA Stack:** Physical WAL streaming replication with slots, paired with Patroni (etcd Raft consensus) and PgBouncer in transaction-pooling mode.

---

## 2. Key Operational Metrics & Thresholds

| Component | Default | Recommended Production Value | Operational Impact |
| :--- | :--- | :--- | :--- |
| `shared_buffers` | `128MB` | `25%`–`40%` of Host RAM | Primary buffer pool size |
| `random_page_cost` | `4.0` | `1.1`–`1.5` (NVMe SSD) | Allows CBO to choose index scans over sequential scans |
| `checkpoint_timeout`| `5min` | `15min`–`30min` | Smoothes disk write amplification spikes |
| `max_wal_size` | `1GB` | `16GB`–`64GB` | Prevents premature checkpoint bursts during bulk writes |
| `autovacuum_freeze_max_age` | `200M` | `200M` | Hard emergency limit before database refuses writes |
| `synchronous_commit` | `on` | `on` (or `remote_apply` for HA)| Sets ACID durability vs. network roundtrip latency |
