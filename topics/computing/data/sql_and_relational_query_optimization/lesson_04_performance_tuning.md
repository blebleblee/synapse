# Lesson 4: Performance Tuning

## 1. First-Principles Intuition & Invariants

### Tuning Is Not Query Optimization

Lessons 2 and 3 were about making one query cheaper: better plans, better indexes, better SQL. This lesson is about the server that runs *all* the queries at once. A database can have nothing but well-planned queries and still be slow, because they compete for the same five resources:

1. **Memory** for cached pages and for sorts and hashes,
2. **Disk I/O** for reading pages that are not cached and for writing the write-ahead log (WAL),
3. **CPU** for executing plans,
4. **Locks** that make one transaction wait for another,
5. **Connections**, each a separate operating-system process in PostgreSQL.

The examples use PostgreSQL, as in the course labs. The principles carry over to MySQL/InnoDB and SQL Server; the setting names do not.

### Invariant 1: Measure Where the Time Goes Before Changing Anything

Every tuning change trades something. A bigger `work_mem` speeds up sorts and risks running out of memory; looser durability speeds up commits and risks losing them. Without a measurement you cannot tell whether a change helped, and you cannot undo the ones that hurt. So the workflow is always the same: **find the top consumer, form a hypothesis, change one thing, measure again.**

### Invariant 2: The Database Is a Cache in Front of a Disk

PostgreSQL reads and writes 8 KB pages. A page is served from its own buffer cache (`shared_buffers`), from the operating system's page cache, or from disk, at costs that differ by orders of magnitude. Most server tuning is about keeping the working set (the pages the workload actually touches) in memory, and making the unavoidable writes sequential and spread out.

### Invariant 3: MVCC Turns Updates Into Garbage

PostgreSQL implements isolation with multi-version concurrency control. An `UPDATE` does not overwrite a row; it writes a new version and marks the old one dead once no transaction can see it. `DELETE` only marks. Dead versions stay in the table and its indexes until `VACUUM` removes them. A write-heavy table therefore always carries some garbage, and tuning vacuum is as much a part of performance as tuning memory.

---

## 2. Core Architecture & Mechanics

### 2.1 Finding the Top Consumers: `pg_stat_statements`

Enable the extension once (it needs a restart because it must be preloaded):

```ini
# postgresql.conf
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = top
```

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

It aggregates statistics per normalized statement (literals replaced by `$1`, `$2`…). The question to ask is not "which query is slowest?" but "which query uses the most total time?":

```sql
SELECT left(query, 80)                     AS query,
       calls,
       round(total_exec_time::numeric, 0)  AS total_ms,
       round(mean_exec_time::numeric, 2)   AS mean_ms,
       round(100 * total_exec_time / sum(total_exec_time) OVER (), 1) AS pct,
       shared_blks_hit,
       shared_blks_read,
       temp_blks_written
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

A 2-ms query called 3 million times an hour (6,000 seconds of work) matters far more than a 40-second report that runs once a night. The extra columns point at the cause:

- `shared_blks_read` high relative to `shared_blks_hit`: the query reads from outside the buffer cache (section 2.3).
- `temp_blks_written` above zero: sorts or hashes spill to disk (section 2.4).
- `calls` very high and `mean_ms` tiny: an application issuing one query per row (the "N+1" pattern), solved in the application, not the server.

(Column names: PostgreSQL 13 renamed `total_time` and `mean_time` to `total_exec_time` and `mean_exec_time`. Use the old names on 12 and earlier.)

Reset the statistics with `SELECT pg_stat_statements_reset();` before a measurement, so before and after numbers cover comparable periods.

### 2.2 What Sessions Are Waiting For: Wait Events

`pg_stat_statements` says where time went in the past; `pg_stat_activity` says what is happening now. Each active backend reports what it is waiting on:

```sql
SELECT wait_event_type, wait_event, state, count(*)
FROM pg_stat_activity
WHERE backend_type = 'client backend'
GROUP BY 1, 2, 3
ORDER BY count(*) DESC;
```

Sample it every second for a minute during the slow period and the picture becomes clear:

| Dominant wait | Meaning | Look at |
|---|---|---|
| none, state `active` | On CPU | Plans (Lessons 2–3), parallelism, CPU count |
| `IO` / `DataFileRead` | Reading pages from disk | Cache size, missing indexes, sequential scans |
| `IO` / `WALSync`, `WALWrite` | Waiting for commits to reach disk | WAL disk latency, commit rate (section 2.5) |
| `Lock` / `transactionid`, `tuple` | Row-level conflicts between transactions | Hot rows, transaction length (section 3.3) |
| `LWLock` / various | Contention on internal structures | Often too many active connections (section 2.7) |
| `Client` / `ClientRead` | Waiting for the application to send the next statement | The application, or an idle-in-transaction session |

### 2.3 Memory: `shared_buffers` and `effective_cache_size`

`shared_buffers` is PostgreSQL's own page cache, allocated at start-up. The default (128 MB) is a placeholder for tiny machines. A common starting point on a dedicated server is **about 25% of RAM**, leaving the rest to the operating system's page cache, which PostgreSQL also benefits from. Much larger values rarely help, because the same pages then sit in both caches.

Check the hit ratio per table rather than one global number, which hides the tables that matter:

```sql
SELECT relname,
       heap_blks_read,
       heap_blks_hit,
       round(100.0 * heap_blks_hit / nullif(heap_blks_hit + heap_blks_read, 0), 1) AS hit_pct
FROM pg_statio_user_tables
ORDER BY heap_blks_read DESC
LIMIT 10;
```

A "read" here means "not in `shared_buffers`"; the page may still have come from the OS cache. So a low ratio is a prompt to look further, not proof of disk reads. The `pg_buffercache` extension shows exactly which relations occupy the buffer cache.

`effective_cache_size` allocates nothing. It tells the planner how much memory (`shared_buffers` plus the OS cache) is likely available for caching, which makes index scans look cheaper when the index probably fits. Set it to roughly 50–75% of RAM on a dedicated server.

On SSDs, also lower `random_page_cost` from its default of 4.0 (a spinning-disk assumption) to about 1.1. Otherwise the planner overestimates the cost of index access and prefers sequential scans.

### 2.4 Memory per Operation: `work_mem`

`work_mem` (default 4 MB) is the memory **each sort or hash operation in each plan node** may use before spilling to temporary files. It is not per connection. One query with three hash joins and a sort, running with two parallel workers, can use around 12 × `work_mem` (each worker gets its own allowance). Hash operations may use `work_mem × hash_mem_multiplier` (the multiplier was added in PostgreSQL 13; its default is 2.0 since PostgreSQL 15).

Find spills in three ways:

```sql
-- 1. Per statement, from pg_stat_statements
SELECT left(query, 60), temp_blks_written FROM pg_stat_statements
WHERE temp_blks_written > 0 ORDER BY temp_blks_written DESC LIMIT 5;
```

```ini
# 2. In the log: one line for every temporary file over the size given (0 = all)
log_temp_files = 0
```

```sql
-- 3. In one plan
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
--   Sort Method: external merge  Disk: 152 MB     <- spilled
--   Sort Method: quicksort  Memory: 3 MB          <- fitted
```

Raise `work_mem` where the spill happens, not globally. A reporting role or a single session can get more:

```sql
ALTER ROLE reporting SET work_mem = '256MB';
-- or, for one transaction:
BEGIN; SET LOCAL work_mem = '512MB'; SELECT ...; COMMIT;
```

Raising it to 256 MB for 400 connections is how servers get killed by the out-of-memory killer during a busy hour.

`maintenance_work_mem` (default 64 MB) is the equivalent for `VACUUM`, `CREATE INDEX` and adding foreign keys. Raising it to 1 GB or more speeds up index builds considerably; autovacuum workers use it too unless `autovacuum_work_mem` is set.

### 2.5 Writes: WAL and Checkpoints

Every change is first written to the WAL, which is flushed to disk at commit. Data pages are written later, in the background, and a **checkpoint** guarantees that all changes up to a point are in the data files, so older WAL can be recycled.

Two settings decide how often checkpoints happen:

- `checkpoint_timeout` (default 5 min): a checkpoint at least this often,
- `max_wal_size` (default 1 GB): a checkpoint sooner if this much WAL accumulates.

Checkpoints that are too frequent cause two costs. Each one writes every dirty page. And the first change to each page after a checkpoint writes the *whole page* into the WAL (full-page writes protect against torn pages), so frequent checkpoints multiply WAL volume. Check whether checkpoints are triggered by time (good) or by WAL volume (too small a `max_wal_size`):

```sql
-- PostgreSQL 16 and earlier
SELECT checkpoints_timed, checkpoints_req FROM pg_stat_bgwriter;
-- PostgreSQL 17 and later
SELECT num_timed, num_requested FROM pg_stat_checkpointer;
```

If requested checkpoints are a large share, raise `max_wal_size` (several GB is normal on busy servers) and consider `checkpoint_timeout = 15min`. Keep `checkpoint_completion_target = 0.9` (the default since PostgreSQL 14) so each checkpoint's writes are spread over most of the interval instead of arriving as a burst. Longer intervals have one cost: crash recovery replays more WAL.

**Commit latency.** If `WALSync` waits dominate, each commit waits for the WAL disk's flush. Options in order of preference:

1. Put the WAL on low-latency storage.
2. Batch work into fewer, larger transactions where the application allows it.
3. Set `synchronous_commit = off` **for data you can afford to lose**, per session or per transaction. A crash can then lose the last few hundred milliseconds of commits, but never corrupts the database. Never turn off `fsync`, which does risk corruption.

### 2.6 Vacuum, Bloat and HOT Updates

Autovacuum starts on a table when its dead rows exceed `autovacuum_vacuum_threshold + autovacuum_vacuum_scale_factor × rows` (defaults 50 and 0.2). For a 200-million-row table that is 40 million dead rows before anything happens, too late for a hot table. Set the factor per table:

```sql
ALTER TABLE orders SET (autovacuum_vacuum_scale_factor = 0.01,
                        autovacuum_vacuum_threshold   = 10000);
```

Check whether vacuum is keeping up:

```sql
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;
```

Autovacuum is deliberately throttled (`autovacuum_vacuum_cost_limit` / `vacuum_cost_limit`, default 200, and `autovacuum_vacuum_cost_delay`, default 2 ms since PostgreSQL 12). On fast storage, raising the cost limit (to 1,000–2,000) lets it finish before the next wave of updates.

**HOT updates.** If an update changes no indexed column *and* the new version fits on the same page, PostgreSQL makes a heap-only tuple (HOT) update: no index entries are written, and the old version can be cleaned up without a full vacuum. Two levers increase the HOT ratio:

- Do not index columns that change constantly (a `last_seen_at` timestamp updated on every request).
- Leave free space on each page with a lower fillfactor for update-heavy tables:

```sql
ALTER TABLE sessions SET (fillfactor = 80);   -- applies to newly written pages
SELECT relname, n_tup_upd, n_tup_hot_upd,
       round(100.0 * n_tup_hot_upd / nullif(n_tup_upd, 0), 1) AS hot_pct
FROM pg_stat_user_tables ORDER BY n_tup_upd DESC LIMIT 10;
```

### 2.7 Connections and Pooling

Each PostgreSQL connection is a separate process with its own memory. Hundreds of mostly idle connections cost memory, and hundreds of *active* ones contend for locks and CPU caches. Throughput typically peaks at a small multiple of the CPU core count of active connections and falls beyond it. Raising `max_connections` to 2,000 because the application ran out of connections makes the database slower, not faster.

Put a pooler such as PgBouncer between the application and the database:

```ini
; pgbouncer.ini
[databases]
app = host=127.0.0.1 port=5432 dbname=app

[pgbouncer]
pool_mode = transaction
max_client_conn = 2000
default_pool_size = 20
```

In **transaction pooling**, a server connection is lent to a client only for the duration of one transaction, so 2,000 clients share 20 server connections. The price is that nothing may depend on session state between transactions: `SET` without `LOCAL`, session-level advisory locks, `LISTEN`, temporary tables kept across transactions, and (in PgBouncer versions before 1.21, or without `max_prepared_statements` set) protocol-level prepared statements. Check the application and its driver before switching modes.

Two settings protect the pool from misbehaving clients:

```ini
idle_in_transaction_session_timeout = '60s'   # kill sessions that opened a transaction and went quiet
statement_timeout = '30s'                     # per role or per application, not globally for batch jobs
```

---

## 3. High-Performance Optimization & Failure Modes

### 3.1 A Tuning Session, Start to Finish

A web application slows down every weekday at 10:00. A disciplined session:

1. **Baseline.** Reset `pg_stat_statements` at 09:45, snapshot it at 10:30.
2. **Top consumer.** One statement, `UPDATE carts SET updated_at = now(), ... WHERE id = $1`, uses 38% of total time; mean 9 ms, normally 0.4 ms.
3. **Wait events.** Sampling shows `Lock / tuple` and `Lock / transactionid` waits: sessions are queuing for the same rows.
4. **Cause.** A promotion job updates a "featured" cart row for every request, and its transactions stay open while calling an external service.
5. **Change one thing.** Move the external call outside the transaction.
6. **Measure.** Mean time back to 0.5 ms, lock waits gone. Only now look at the next item on the list.

No server parameter was touched. That is common: the top consumer is often an application pattern, and the statistics views are how you find it.

### 3.2 Bloat and the Long-Running Transaction

**Symptom:** a table grows steadily although its row count is flat; queries on it slow down; `n_dead_tup` stays high even right after autovacuum runs.

**Cause:** vacuum can remove a dead version only when no transaction could still see it. One session that has been `idle in transaction` for six hours, an abandoned replication slot, or a long analytics query on a standby with `hot_standby_feedback = on` holds back the oldest visible transaction ID (the *xmin horizon*) for the whole cluster.

```sql
SELECT pid, state, xact_start, now() - xact_start AS age, left(query, 60)
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start
LIMIT 5;

SELECT slot_name, active, xmin, catalog_xmin FROM pg_replication_slots;
```

**Fix:** end the transaction (`SELECT pg_terminate_backend(pid);`), drop unused slots, and set `idle_in_transaction_session_timeout`. Space already bloated is reused by later inserts but not returned to the operating system; `VACUUM FULL` returns it at the cost of an exclusive lock for the whole rewrite, and the `pg_repack` extension does the same with only brief locks.

### 3.3 Hot Rows and Lock Queues

**Symptom:** throughput stops rising as clients are added; `Lock` waits dominate; CPU is low.

**Cause:** many transactions update the same row: a global counter, an "inventory" row for a popular product, a status row per tenant. Row locks serialize them, and each waits for the previous commit's WAL flush.

**Fixes, from cheapest:**

- Keep transactions that touch hot rows short, and touch the hot row *last*, so the lock is held only until commit.
- Replace one counter with N sharded counters (`counter_id, shard, value`) and sum them on read.
- Turn updates into inserts (an append-only ledger) aggregated periodically.
- For queues, let workers skip rows that others hold: `SELECT ... FOR UPDATE SKIP LOCKED LIMIT 10`.

Also set `log_lock_waits = on`. Every wait longer than `deadlock_timeout` (default 1 s) is then logged with the blocking process, which turns a vague "it is slow" into a specific pair of statements.

### 3.4 Memory Exhaustion From Good Intentions

**Symptom:** the server is killed by the out-of-memory killer at peak, or swaps heavily. All backends restart because the postmaster resets after a backend is killed.

**Cause:** `work_mem` raised globally, combined with many connections and parallel queries; or `shared_buffers` set to 75% of RAM, leaving too little for everything else.

**Fix:** budget memory explicitly. `shared_buffers`, plus `maintenance_work_mem × autovacuum_max_workers`, plus a realistic `active connections × nodes per query × work_mem` must stay below physical RAM with headroom for the OS cache. On Linux, set `vm.overcommit_memory = 2` on dedicated database hosts, so allocations fail with an error inside one query instead of the kernel killing a process.

### 3.5 Checkpoint Storms

**Symptom:** latency spikes every few minutes; I/O is saturated during them; the log shows `checkpoints are occurring too frequently` (enabled by `checkpoint_warning`, default 30 s).

**Fix:** raise `max_wal_size` until most checkpoints are timed (section 2.5), keep `checkpoint_completion_target = 0.9`, and make sure the WAL and data files are not on a device that is also busy with something else.

### 3.6 Changing Settings Safely

```sql
SHOW work_mem;                                -- current value
SELECT name, setting, unit, source, pending_restart
FROM pg_settings WHERE name IN ('shared_buffers', 'work_mem', 'max_wal_size');

ALTER SYSTEM SET max_wal_size = '8GB';        -- written to postgresql.auto.conf
SELECT pg_reload_conf();                      -- enough for most settings
```

`pending_restart = true` means the setting (such as `shared_buffers` or `max_connections`) needs a restart. Record every change with the date and the measurement that justified it. Six months later, that record is the only way to know which settings still matter.

---

## 4. Summary: The Tuning Contract

- Measure first: `pg_stat_statements` for where time went, wait events for what sessions wait on.
- Rank by total time, not by the slowest single query.
- `shared_buffers` around 25% of RAM; `effective_cache_size` is a hint, not an allocation; lower `random_page_cost` on SSDs.
- `work_mem` is per operation: raise it where spills happen, not globally.
- Most checkpoints should be timed, not requested; spread them with `checkpoint_completion_target`.
- Tune autovacuum per table, and hunt the long transactions that block it.
- Pool connections; keep active connections near the core count.
- Change one thing at a time, and write down why.
