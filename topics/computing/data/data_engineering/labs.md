# Operational Verification Labs: Core

## Objective & Database Environment Setup

The objective of this laboratory is to provide hands-on experience with operational verification of a database system. This includes understanding storage page layouts, concurrency control mechanisms, and crash recovery processes. We will use PostgreSQL as the primary database engine, along with several client CLI tools and inspection utilities.

### Required Database Engines, Client CLI Tools, and Inspection Utilities

- **Database Engine:** PostgreSQL 13.5
- **Client CLI Tools:** `psql`, `pgbench`
- **Inspection Utilities:** `pg_controldata`, `pg_stat_activity`, `pg_locks`, `pg_waldump`

### Installation Steps

1. **Install PostgreSQL:**

   ```bash
   sudo apt-get update
   sudo apt-get install postgresql-13
   ```

2. **Install `pgbench`:**

   ```bash
   sudo apt-get install postgresql-contrib-13
   ```

3. **Install `pg_controldata`:**

   This utility is included with PostgreSQL, so no additional installation is required.

4. **Install `pg_stat_activity` and `pg_locks`:**

   These are built-in views in PostgreSQL, so no additional installation is required.

5. **Install `pg_waldump`:**

   This utility is included with PostgreSQL, so no additional installation is required.

## Exercise 1: Storage Page & Internal Memory Inspection

In this exercise, we will inspect the storage pages and internal memory structures of PostgreSQL.

### Inspecting Slotted Pages

PostgreSQL uses slotted pages to store data. Each page is 8KB in size and contains a header, item pointers, and the actual data.

1. **Connect to the PostgreSQL Database:**

   ```bash
   psql -U postgres
   ```

2. **Create a Test Table:**

   ```sql
   CREATE TABLE test_table (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100)
   );
   ```

3. **Insert Sample Data:**

   ```sql
   INSERT INTO test_table (name) VALUES ('Alice'), ('Bob'), ('Charlie');
   ```

4. **Inspect the Page Structure:**

   To inspect the page structure, we can use the `pageinspect` extension.

   ```sql
   CREATE EXTENSION pageinspect;
   ```

5. **Get the Page ID of the Test Table:**

   ```sql
   SELECT pg_relation_filenode('test_table');
   ```

   Assume the output is `12345`.

6. **Inspect the Page:**

   ```sql
   SELECT * FROM heap_page_items(get_raw_page('test_table', 0));
   ```

### Inspecting Buffer Pool States

The buffer pool is an in-memory cache of database pages. We can inspect the buffer pool state using the `pg_buffercache` extension.

1. **Install the `pg_buffercache` Extension:**

   ```sql
   CREATE EXTENSION pg_buffercache;
   ```

2. **Inspect the Buffer Pool:**

   ```sql
   SELECT * FROM pg_buffercache;
   ```

### Inspecting Index Trees

Indexes are critical for query performance. We can inspect the structure of an index using the `pageinspect` extension.

1. **Create an Index on the Test Table:**

   ```sql
   CREATE INDEX idx_test_table_name ON test_table(name);
   ```

2. **Get the Page ID of the Index:**

   ```sql
   SELECT pg_relation_filenode('idx_test_table_name');
   ```

   Assume the output is `12346`.

3. **Inspect the Index Page:**

   ```sql
   SELECT * FROM bt_metap('idx_test_table_name');
   ```

## Exercise 2: Concurrency Contention & Lock Graph Analysis

In this exercise, we will simulate concurrent transactions and analyze lock contention and wait graphs.

### Simulating Concurrent Transactions

1. **Open Two Terminal Windows:**

   In each terminal, connect to the PostgreSQL database.

   ```bash
   psql -U postgres
   ```

2. **Start a Transaction in Terminal 1:**

   ```sql
   BEGIN;
   UPDATE test_table SET name = 'Alice Updated' WHERE id = 1;
   ```

3. **Attempt to Update the Same Row in Terminal 2:**

   ```sql
   BEGIN;
   UPDATE test_table SET name = 'Alice Updated Again' WHERE id = 1;
   ```

   This will block Terminal 2, waiting for Terminal 1 to commit or roll back.

### Analyzing Lock Conflicts

1. **Inspect Locks in Terminal 1:**

   ```sql
   SELECT * FROM pg_locks WHERE locktype = 'relation';
   ```

2. **Inspect Locks in Terminal 2:**

   ```sql
   SELECT * FROM pg_locks WHERE locktype = 'relation';
   ```

3. **Inspect Wait Graph:**

   ```sql
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

   This will show the active transactions and their states.

### Resolving Locks

1. **Commit the Transaction in Terminal 1:**

   ```sql
   COMMIT;
   ```

2. **Check Terminal 2:**

   The update should now proceed.

## Exercise 3: Crash Simulation & WAL Recovery Replay

In this exercise, we will simulate a crash and inspect the Write-Ahead Log (WAL) records to ensure data consistency.

### Simulating a Crash

1. **Insert More Data:**

   ```sql
   INSERT INTO test_table (name) VALUES ('David'), ('Eve');
   ```

2. **Simulate a Crash:**

   ```bash
   sudo systemctl stop postgresql
   ```

3. **Inspect WAL Records:**

   ```bash
   pg_waldump -p /var/lib/postgresql/13/main/pg_wal/000000010000000000000001
   ```

   Replace the WAL file path with the appropriate file from your PostgreSQL data directory.

### Validating Consistency

1. **Restart PostgreSQL:**

   ```bash
   sudo systemctl start postgresql
   ```

2. **Verify Data Consistency:**

   ```sql
   SELECT * FROM test_table;
   ```

   The data should be consistent and include all inserted records.

## Production Diagnostic Cheat Sheet & Verification Checklist

### Essential SQL Inspection Queries

- **Inspect Buffer Pool:**

  ```sql
  SELECT * FROM pg_buffercache;
  ```

- **Inspect Locks:**

  ```sql
  SELECT * FROM pg_locks;
  ```

- **Inspect WAL:**

  ```bash
  pg_waldump -p /var/lib/postgresql/13/main/pg_wal/000000010000000000000001
  ```

- **Inspect Active Transactions:**

  ```sql
  SELECT * FROM pg_stat_activity;
  ```

### CLI Flags

- **Start PostgreSQL:**

  ```bash
  sudo systemctl start postgresql
  ```

- **Stop PostgreSQL:**

  ```bash
  sudo systemctl stop postgresql
  ```

- **Inspect Database Control Data:**

  ```bash
  pg_controldata /var/lib/postgresql/13/main
  ```

This lab guide provides a comprehensive set of exercises to verify the operational correctness of a PostgreSQL database system. By understanding storage page layouts, concurrency control mechanisms, and crash recovery processes, you will gain a deeper insight into the inner workings of a database management system.
