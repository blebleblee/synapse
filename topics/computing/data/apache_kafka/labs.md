# Operational Verification Labs: Core

## Objective & Database Environment Setup

This lab guide is designed for database practitioners and DBAs who seek to deepen their understanding of core database internals through hands-on verification of storage structures, concurrency models, and crash recovery mechanisms. The exercises are grounded in the behavior of a modern relational database engine, with a focus on inspecting internal data structures, analyzing transactional behavior, and validating system resilience under failure conditions.

The environment required for these labs includes a PostgreSQL 15+ instance, a client CLI tool (`psql`), and a set of utilities for memory and page-level inspection. The database engine must be configured with `fsync = on`, `full_page_writes = on`, and `wal_level = logical` to ensure that all write-ahead log (WAL) operations and page-level consistency are preserved for analysis.

### Required Tools and Configuration

- **PostgreSQL 15+** with `fsync = on`, `full_page_writes = on`, `wal_level = logical`
- **psql** – PostgreSQL interactive terminal
- **pg_controldata** – Inspects control file contents
- **pg_waldump** – Parses WAL records
- **pg_filedump** – Analyzes raw page content
- **pg_buffercache** extension – Inspects buffer pool contents
- **pg_stat_statements** extension – Tracks query execution statistics

### Environment Setup

1. **Install PostgreSQL 15+**:
   ```bash
   sudo apt install postgresql-15 postgresql-contrib-15
   ```

2. **Configure `postgresql.conf`**:
   ```conf
   fsync = on
   full_page_writes = on
   wal_level = logical
   ```

3. **Enable required extensions**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_buffercache;
   CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
   ```

4. **Start PostgreSQL service**:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

5. **Connect to PostgreSQL as superuser**:
   ```bash
   sudo -u postgres psql
   ```

---

## Exercise 1: Storage Page & Internal Memory Inspection

In this exercise, we will inspect the internal structure of a PostgreSQL table by examining slotted pages, buffer pool contents, and index trees. This provides insight into how data is laid out on disk and how the system manages memory for efficient access.

### Step 1: Create a Test Table with Known Structure

```sql
CREATE TABLE test_page_inspection (
    id SERIAL PRIMARY KEY,
    name TEXT,
    value INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO test_page_inspection (name, value) VALUES
('Alice', 100),
('Bob', 200),
('Charlie', 300);
```

### Step 2: Identify the Table's OID and Page Number

We will use `pg_relation_filepath()` to determine the file path of the table and `pgstattuple` to inspect page-level details.

```sql
SELECT pg_relation_filepath('test_page_inspection') AS table_path;
```

### Step 3: Inspect Raw Page Content Using `pg_filedump`

Assuming the table is stored in `/var/lib/postgresql/15/main/base/16384/16385`, we can dump the first page:

```bash
pg_filedump -p 1 /var/lib/postgresql/15/main/base/16384/16385
```

This command outputs the raw page header and slotted page layout, including:
- Page type (heap, index, etc.)
- Free space map
- Tuple pointers and offsets
- Tuple data layout

### Step 4: Analyze Buffer Pool Contents

Use the `pg_buffercache` extension to inspect which pages are currently in memory:

```sql
SELECT
    relfilenode,
    pg_size_pretty(pg_relation_size(relfilenode)) AS size,
    count(*) AS buffer_count
FROM pg_buffercache bc
JOIN pg_class c ON bc.relfilenode = c.relfilenode
WHERE c.relname = 'test_page_inspection'
GROUP BY relfilenode, pg_relation_size(relfilenode);
```

This query reveals how many pages of the table are cached in memory and how much space they occupy.

### Step 5: Inspect Index Tree Structure

If an index exists, we can inspect its internal structure using `pgstattuple`:

```sql
SELECT * FROM pgstattuple('test_page_inspection_pkey');
```

This returns:
- Number of live tuples
- Number of dead tuples
- Free space
- Page header information

---

## Exercise 2: Concurrency Contention & Lock Graph Analysis

In this exercise, we simulate concurrent transactions and analyze lock contention using PostgreSQL's lock monitoring system. This is crucial for understanding how the system handles concurrent access and resolves conflicts.

### Step 1: Begin Two Concurrent Transactions

Open two separate `psql` sessions and execute the following:

**Session 1:**
```sql
BEGIN;
UPDATE test_page_inspection SET value = 999 WHERE id = 1;
-- Do not commit yet
```

**Session 2:**
```sql
BEGIN;
UPDATE test_page_inspection SET value = 888 WHERE id = 1;
-- This will block until Session 1 commits or rolls back
```

### Step 2: Monitor Locks and Wait Graphs

In a third session, query the current locks and wait graph:

```sql
SELECT
    pid,
    locktype,
    database,
    relation::regclass,
    mode,
    granted
FROM pg_locks
WHERE relation = 'test_page_inspection'::regclass;
```

This reveals which processes are holding or waiting for locks on the table.

### Step 3: Analyze Wait Graphs Using `pg_stat_activity`

```sql
SELECT
    pid,
    query,
    wait_event_type,
    wait_event,
    state
FROM pg_stat_activity
WHERE state = 'active';
```

This shows which queries are currently blocked and what event they are waiting on.

### Step 4: Simulate Deadlock

To simulate a deadlock, we can create a scenario where two transactions are waiting on each other:

**Session 1:**
```sql
BEGIN;
UPDATE test_page_inspection SET value = 111 WHERE id = 1;
-- Do not commit yet
```

**Session 2:**
```sql
BEGIN;
UPDATE test_page_inspection SET value = 222 WHERE id = 2;
-- Do not commit yet
```

**Session 3:**
```sql
BEGIN;
UPDATE test_page_inspection SET value = 333 WHERE id = 1;
-- This will cause a deadlock with Session 1
```

Check for deadlocks:

```sql
SELECT
    pid,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE state = 'active' AND wait_event_type = 'Lock';
```

PostgreSQL will automatically abort one of the transactions to resolve the deadlock.

---

## Exercise 3: Crash Simulation & WAL Recovery Replay

In this exercise, we simulate a system crash and verify that PostgreSQL's write-ahead logging (WAL) ensures data consistency upon restart.

### Step 1: Start a Long-Running Transaction

```sql
BEGIN;
INSERT INTO test_page_inspection (name, value) VALUES ('Crash Test', 500);
-- Do not commit
```

### Step 2: Simulate a Crash

Stop the PostgreSQL service to simulate a crash:

```bash
sudo systemctl stop postgresql
```

### Step 3: Inspect WAL Records

After stopping PostgreSQL, we can inspect the WAL using `pg_waldump`:

```bash
pg_waldump /var/lib/postgresql/15/main/pg_wal/000000010000000000000001
```

This shows the sequence of WAL records, including:
- `XLOG_INSERT` for new tuples
- `XLOG_UPDATE` for modified tuples
- `XLOG_COMMIT` for transaction commits

### Step 4: Restart PostgreSQL and Verify Recovery

Start PostgreSQL again:

```bash
sudo systemctl start postgresql
```

Check that the transaction was rolled back:

```sql
SELECT * FROM test_page_inspection WHERE name = 'Crash Test';
```

If the transaction was not committed, it will not appear in the table, confirming that PostgreSQL's crash recovery mechanism correctly rolled back uncommitted transactions.

### Step 5: Inspect WAL Replay Logs

Check PostgreSQL logs for recovery messages:

```bash
tail -f /var/log/postgresql/postgresql-15-main.log
```

Look for lines like:
```
LOG: redo starts at ...
LOG: consistent recovery state reached at ...
LOG: database system is ready to accept connections
```

These confirm that the system successfully replayed WAL records and reached a consistent state.

---

## Production Diagnostic Cheat Sheet & Verification Checklist

| Task | SQL Query or CLI Command | Purpose |
|------|--------------------------|---------|
| Inspect table page layout | `pgstattuple('table_name')` | Analyze heap page structure |
| Check buffer pool usage | `SELECT * FROM pg_buffercache` | Monitor memory usage |
| View active locks | `SELECT * FROM pg_locks` | Identify lock contention |
| Monitor wait events | `SELECT * FROM pg_stat_activity` | Detect blocking queries |
| Inspect WAL records | `pg_waldump` | Analyze transaction logs |
| Check control file | `pg_controldata` | Verify system state |
| Analyze query performance | `SELECT * FROM pg_stat_statements` | Identify slow queries |
| Validate recovery | `tail -f postgresql.log` | Confirm crash recovery |

This checklist provides a quick reference for diagnosing common issues in a PostgreSQL database environment, ensuring that both operational and diagnostic tasks are covered.
