# Operational Verification Labs: PostgreSQL Storage & MVCC Internals

This lab provides concrete, hands-on operational commands to inspect physical 8KB heap pages, verify MVCC tuple headers, inspect the shared buffer pool cache, and observe the Write-Ahead Log stream.

---

## Lab 1: Microscopic Inspection of an 8KB Heap Page with `pageinspect`

In this exercise, you will create a table, insert rows, and use the official PostgreSQL `pageinspect` extension to read the raw binary header, line pointers, and tuple headers on disk.

### Step 1.1: Launch PostgreSQL Sandbox Container
```bash
docker run --rm --name pg-lab -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16-alpine
```

### Step 1.2: Initialize Schema and Enable `pageinspect`
Connect via `psql`:
```bash
docker exec -it pg-lab psql -U postgres -d postgres
```

Execute SQL commands:
```sql
CREATE EXTENSION IF NOT EXISTS pageinspect;

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    owner_name VARCHAR(64),
    balance NUMERIC(12, 2)
);

INSERT INTO accounts (owner_name, balance) VALUES 
('Alice', 1000.00),
('Bob', 2500.50),
('Charlie', 50.00);
```

### Step 1.3: Inspect PageHeaderData
Inspect block 0 of the `accounts` relation:
```sql
SELECT lsn, checksum, flags, lower, upper, special, pagesize
FROM page_header(get_raw_page('accounts', 0));
```
*Expected Output:*
- `pagesize`: `8192` (8KB)
- `lower`: Byte offset indicating the end of the line pointers array.
- `upper`: Byte offset indicating the start of the unallocated free space.
- `special`: `8192` (0 bytes of special space for heap tables).

### Step 1.4: Inspect Tuple Headers & Line Pointers
Query the individual tuple headers inside page 0:
```sql
SELECT lp, lp_off, lp_flags, lp_len, t_xmin, t_xmax, t_field3 AS t_cid, t_ctid, t_data
FROM heap_page_items(get_raw_page('accounts', 0));
```
*Verification Checkpoints:*
1. Notice that `t_xmin` matches the transaction ID that executed the `INSERT`.
2. Notice that `t_xmax` is `0`, confirming the row is live and unmodified.
3. Observe `t_ctid = (0, 1)`, `(0, 2)`, `(0, 3)` pointing directly to their own line pointers.

---

## Lab 2: Observing MVCC Updates & Dead Tuple Bloat

### Step 2.1: Execute an In-Place Update
```sql
UPDATE accounts SET balance = 1200.00 WHERE owner_name = 'Alice';
```

Now re-run the page inspection query:
```sql
SELECT lp, lp_flags, t_xmin, t_xmax, t_ctid 
FROM heap_page_items(get_raw_page('accounts', 0));
```
*Key Observations:*
- `lp 1` (Old Alice): `t_xmax` is now set to the transaction ID of your `UPDATE` statement. Its `t_ctid` now points forward to `(0, 4)`.
- `lp 4` (New Alice): A brand new tuple has been appended to the page with `t_xmin` set to the updating transaction, `t_xmax = 0`, and `t_ctid = (0, 4)`.
- The original row at line pointer 1 is now a **dead tuple** awaiting Autovacuum cleanup!

---

## Lab 3: Inspecting Shared Buffers with `pg_buffercache`

### Step 3.1: Enable `pg_buffercache`
```sql
CREATE EXTENSION IF NOT EXISTS pg_buffercache;
```

### Step 3.2: Query Buffer Cache Utilization
Check how many 8KB pages are currently pinned, dirty, or cached in `shared_buffers`:
```sql
SELECT 
    c.relname,
    count(*) AS buffered_pages,
    round(100.0 * count(*) / (SELECT setting FROM pg_settings WHERE name='shared_buffers')::integer, 2) AS buffer_pool_pct,
    round(count(*) * 8192.0 / 1024 / 1024, 2) AS buffered_mb,
    count(*) FILTER (WHERE isdirty) AS dirty_pages
FROM pg_buffercache b
JOIN pg_class c ON b.relfilenode = pg_relation_filenode(c.oid)
JOIN pg_database d ON (b.reldatabase = d.oid AND d.datname = current_database())
GROUP BY c.relname
ORDER BY buffered_pages DESC
LIMIT 10;
```

---

## Lab 4: Dissecting Write-Ahead Logs with `pg_waldump`

Exit `psql` back to host terminal:
```bash
docker exec -it pg-lab bash
```

Run `pg_waldump` on the current active WAL segment in `/var/lib/postgresql/data/pg_wal/`:
```bash
# Locate the newest WAL segment
WAL_FILE=$(ls -t /var/lib/postgresql/data/pg_wal/0* | head -n 1)

# Dump the last 20 WAL resource manager records
pg_waldump -n 20 $WAL_FILE
```
*Expected Record Types:*
- `rmgr: Heap` (`desc: INSERT`, `desc: UPDATE`, `desc: HOT_UPDATE`)
- `rmgr: Transaction` (`desc: COMMIT`)
- `rmgr: Standby` (`desc: RUNNING_XACTS`)

---

## Lab 5: Teardown
```bash
docker stop pg-lab
```
