# Operational Verification Labs: Core

## Objective & Database Environment Setup

The objective of this laboratory is to provide hands-on experience with operational verification of a relational database system. We will use PostgreSQL as the primary database engine due to its robust feature set and comprehensive documentation. The lab will cover storage page inspection, concurrency contention analysis, and crash simulation with Write-Ahead Logging (WAL) recovery. 

### Required Database Engines, Client CLI Tools, and Inspection Utilities

- **Database Engine:** PostgreSQL 13.5
- **Client CLI Tools:** `psql` (PostgreSQL interactive terminal)
- **Inspection Utilities:** `pg_controldata`, `pg_stat_statements`, `pg_buffercache`, `pg_locks`, `pg_walinspect`

#### Installation Steps

1. **Install PostgreSQL:**

   On Debian-based systems:
   ```bash
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   ```

   On Red Hat-based systems:
   ```bash
   sudo yum install postgresql-server postgresql-contrib
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Install Additional Utilities:**

   Ensure the `pg_buffercache` and `pg_stat_statements` extensions are available:
   ```bash
   sudo apt-get install postgresql-contrib
   ```

3. **Enable Extensions:**

   Connect to the PostgreSQL database and enable the required extensions:
   ```bash
   sudo -u postgres psql
   ```

   Inside the `psql` shell:
   ```sql
   CREATE EXTENSION pg_buffercache;
   CREATE EXTENSION pg_stat_statements;
   ```

4. **Install `pg_walinspect`:**

   `pg_walinspect` is a utility for inspecting WAL files. It can be installed from the PostgreSQL source code or via package managers:

   On Debian-based systems:
   ```bash
   sudo apt-get install postgresql-walinspect
   ```

   On Red Hat-based systems:
   ```bash
   sudo yum install postgresql-walinspect
   ```

## Exercise 1: Storage Page & Internal Memory Inspection

In this exercise, we will inspect the storage pages and the buffer pool state of a PostgreSQL database.

### Inspect Slotted Pages

1. **Create a Test Table:**

   ```sql
   CREATE TABLE test_table (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100),
       value INT
   );

   INSERT INTO test_table (name, value) VALUES ('Alice', 100);
   INSERT INTO test_table (name, value) VALUES ('Bob', 200);
   ```

2. **Identify the Physical Location of the Table:**

   ```sql
   SELECT relfilenode FROM pg_class WHERE relname = 'test_table';
   ```

   Note the `relfilenode` value, which is the physical file identifier for the table.

3. **Inspect the Slotted Pages:**

   Use the `pg_filedump` utility to inspect the slotted pages. First, find the data directory:

   ```bash
   sudo -u postgres pg_controldata /var/lib/postgresql/13/main | grep "Data directory"
   ```

   Navigate to the data directory and use `pg_filedump`:

   ```bash
   cd /var/lib/postgresql/13/main/base/12345  # Replace 12345 with the relfilenode value
   sudo -u postgres pg_filedump -p test_table.1
   ```

### Inspect Buffer Pool State

1. **Query the Buffer Cache:**

   ```sql
   SELECT * FROM pg_buffercache;
   ```

   This query will show the current state of the buffer pool, including the file identifiers, block numbers, and usage statistics.

## Exercise 2: Concurrency Contention & Lock Graph Analysis

In this exercise, we will simulate concurrent transactions and analyze lock contention.

### Simulate Concurrent Transactions

1. **Open Two `psql` Sessions:**

   Open two terminal windows and connect to the PostgreSQL database in each session.

2. **Session 1: Begin a Transaction and Lock a Row:**

   ```sql
   BEGIN;
   SELECT * FROM test_table WHERE id = 1 FOR UPDATE;
   ```

3. **Session 2: Attempt to Update the Same Row:**

   ```sql
   BEGIN;
   UPDATE test_table SET value = 300 WHERE id = 1;
   ```

   This will block because the row is locked by Session 1.

4. **Analyze Locks:**

   In a third `psql` session, query the lock status:

   ```sql
   SELECT * FROM pg_locks;
   ```

   This will show the lock conflicts and wait graphs.

### Analyze Wait Graphs

1. **Query the Locks and Wait Events:**

   ```sql
   SELECT
       l1.pid AS waiting_pid,
       a1.query AS waiting_query,
       l2.pid AS blocking_pid,
       a2.query AS blocking_query
   FROM pg_locks l1
   JOIN pg_stat_activity a1 ON l1.pid = a1.pid
   JOIN pg_locks l2 ON l1.locktype = l2.locktype
       AND l1.database = l2.database
       AND l1.relation = l2.relation
       AND l1.page = l2.page
       AND l1.tuple = l2.tuple
       AND l1.virtualxid = l2.virtualxid
       AND l1.transactionid = l2.transactionid
       AND l1.classid = l2.classid
       AND l1.objid = l2.objid
       AND l1.objsubid = l2.objsubid
       AND l1.pid != l2.pid
   JOIN pg_stat_activity a2 ON l2.pid = a2.pid
   WHERE NOT l1.granted;
   ```

   This query will show the wait graphs and identify which transactions are blocking others.

## Exercise 3: Crash Simulation & WAL Recovery Replay

In this exercise, we will simulate a crash and inspect the WAL records to ensure data consistency.

### Simulate a Crash

1. **Insert Data and Simulate a Crash:**

   ```sql
   INSERT INTO test_table (name, value) VALUES ('Charlie', 300);
   ```

   In another terminal, simulate a crash by stopping the PostgreSQL service:

   ```bash
   sudo systemctl stop postgresql
   ```

2. **Inspect WAL Records:**

   Navigate to the WAL directory:

   ```bash
   cd /var/lib/postgresql/13/main/pg_wal
   ```

   Use `pg_walinspect` to inspect the WAL files:

   ```bash
   sudo -u postgres pg_walinspect 000000010000000000000001
   ```

   Replace `000000010000000000000001` with the appropriate WAL segment file name.

3. **Restart PostgreSQL and Verify Data Consistency:**

   ```bash
   sudo systemctl start postgresql
   ```

   Connect to the database and verify the data:

   ```sql
   SELECT * FROM test_table;
   ```

   The data should be consistent and include the row inserted before the crash.

## Production Diagnostic Cheat Sheet & Verification Checklist

### Essential SQL Inspection Queries

1. **Buffer Cache State:**

   ```sql
   SELECT * FROM pg_buffercache;
   ```

2. **Locks and Wait Events:**

   ```sql
   SELECT * FROM pg_locks;
   ```

3. **Transaction Statistics:**

   ```sql
   SELECT * FROM pg_stat_activity;
   ```

4. **Table Statistics:**

   ```sql
   SELECT * FROM pg_stat_user_tables;
   ```

5. **Index Statistics:**

   ```sql
   SELECT * FROM pg_stat_user_indexes;
   ```

### Essential CLI Flags

1. **Inspect Database Control Data:**

   ```bash
   sudo -u postgres pg_controldata /var/lib/postgresql/13/main
   ```

2. **Inspect WAL Files:**

   ```bash
   sudo -u postgres pg_walinspect <wal_segment_file>
   ```

3. **Inspect Slotted Pages:**

   ```bash
   sudo -u postgres pg_filedump -p <table_file>
   ```

By completing these exercises, you will gain a deeper understanding of the operational aspects of a relational database system, including storage page inspection, concurrency management, and crash recovery mechanisms.
