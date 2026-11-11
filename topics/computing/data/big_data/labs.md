# Operational Verification Labs: Core

## Objective & Database Environment Setup

### Objective
The objective of this laboratory is to provide hands-on experience with operational verification of database systems. This includes understanding storage page layouts, concurrency control mechanisms, and crash recovery processes. The exercises will use real database clients, page analyzers, and benchmark suites to ensure practical applicability.

### Database Environment Setup
For this lab, we will use PostgreSQL, a powerful, open-source object-relational database system. We will also use `pg_stat_statements` for query performance analysis, `pg_buffercache` for buffer pool inspection, and `pg_locks` for concurrency control analysis.

#### Required Database Engines
- **PostgreSQL 13 or later**

#### Client CLI Tools
- **psql**: The PostgreSQL interactive terminal.
- **pgbench**: A benchmarking tool for PostgreSQL.

#### Inspection Utilities
- **pg_stat_statements**: A PostgreSQL extension for tracking execution statistics of all SQL statements executed by a server.
- **pg_buffercache**: A PostgreSQL extension for displaying the contents of the buffer cache.
- **pg_locks**: A PostgreSQL system view for displaying information about locks held by active processes.

### Installation Steps
1. **Install PostgreSQL**:
   ```bash
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib
   ```

2. **Enable and start the PostgreSQL service**:
   ```bash
   sudo systemctl enable postgresql
   sudo systemctl start postgresql
   ```

3. **Install `pg_stat_statements` and `pg_buffercache`**:
   ```bash
   sudo -u postgres psql -c "CREATE EXTENSION pg_stat_statements;"
   sudo -u postgres psql -c "CREATE EXTENSION pg_buffercache;"
   ```

4. **Install `pgbench`**:
   ```bash
   sudo apt-get install postgresql-contrib
   ```

## Exercise 1: Storage Page & Internal Memory Inspection

### Objective
Inspect the internal storage pages and buffer pool states of a PostgreSQL database.

### Steps

1. **Create a test database and table**:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE testdb;"
   sudo -u postgres psql -d testdb -c "CREATE TABLE test_table (id SERIAL PRIMARY KEY, data TEXT);"
   ```

2. **Insert sample data**:
   ```bash
   sudo -u postgres psql -d testdb -c "INSERT INTO test_table (data) SELECT 'Sample data ' || generate_series(1, 1000);"
   ```

3. **Inspect the buffer cache**:
   ```bash
   sudo -u postgres psql -d testdb -c "SELECT * FROM pg_buffercache;"
   ```

4. **Inspect the storage pages**:
   - Use the `pageinspect` extension to inspect the internal structure of pages.
   ```bash
   sudo -u postgres psql -d testdb -c "CREATE EXTENSION pageinspect;"
   sudo -u postgres psql -d testdb -c "SELECT * FROM heap_page_items(get_raw_page('test_table', 0));"
   ```

## Exercise 2: Concurrency Contention & Lock Graph Analysis

### Objective
Simulate concurrent transactions, observe lock conflicts, and analyze wait graphs.

### Steps

1. **Create a test table with some data**:
   ```bash
   sudo -u postgres psql -d testdb -c "CREATE TABLE concurrent_table (id SERIAL PRIMARY KEY, value INT);"
   sudo -u postgres psql -d testdb -c "INSERT INTO concurrent_table (value) VALUES (100);"
   ```

2. **Open two `psql` sessions**:
   - **Session 1**:
     ```bash
     sudo -u postgres psql -d testdb
     BEGIN;
     UPDATE concurrent_table SET value = value + 1 WHERE id = 1;
     ```
   - **Session 2**:
     ```bash
     sudo -u postgres psql -d testdb
     BEGIN;
     UPDATE concurrent_table SET value = value + 1 WHERE id = 1;
     ```

3. **Observe the lock graph**:
   - In a third `psql` session, run:
     ```bash
     sudo -u postgres psql -d testdb -c "SELECT * FROM pg_locks;"
     ```

4. **Analyze the wait graph**:
   - Use the `pg_blocking_pids` function to identify blocking processes.
   ```bash
   sudo -u postgres psql -d testdb -c "SELECT * FROM pg_blocking_pids();"
   ```

5. **Resolve the deadlock**:
   - In one of the sessions, commit or rollback the transaction to resolve the deadlock.
   ```bash
   COMMIT;
   ```

## Exercise 3: Crash Simulation & WAL Recovery Replay

### Objective
Simulate a sudden termination of the database server, inspect the Write-Ahead Log (WAL) records, and validate database consistency after recovery.

### Steps

1. **Enable WAL archiving**:
   - Edit the `postgresql.conf` file to enable WAL archiving.
   ```bash
   sudo nano /etc/postgresql/13/main/postgresql.conf
   ```
   - Add or modify the following lines:
     ```plaintext
     wal_level = replica
     archive_mode = on
     archive_command = 'cp %p /var/lib/postgresql/13/main/archive/%f'
     ```
   - Restart the PostgreSQL service:
     ```bash
     sudo systemctl restart postgresql
     ```

2. **Insert data to generate WAL records**:
   ```bash
   sudo -u postgres psql -d testdb -c "INSERT INTO test_table (data) SELECT 'Crash test data ' || generate_series(1, 100);"
   ```

3. **Simulate a crash**:
   - Stop the PostgreSQL service abruptly.
   ```bash
   sudo systemctl stop postgresql
   ```

4. **Inspect WAL records**:
   - Check the contents of the WAL archive directory.
   ```bash
   ls /var/lib/postgresql/13/main/archive/
   ```

5. **Start the PostgreSQL service**:
   - Restart the PostgreSQL service to trigger recovery.
   ```bash
   sudo systemctl start postgresql
   ```

6. **Validate database consistency**:
   - Connect to the database and verify the data.
   ```bash
   sudo -u postgres psql -d testdb -c "SELECT COUNT(*) FROM test_table;"
   ```

## Production Diagnostic Cheat Sheet & Verification Checklist

### Essential SQL Inspection Queries

- **Buffer Cache Inspection**:
  ```sql
  SELECT * FROM pg_buffercache;
  ```

- **Locks and Wait Graph**:
  ```sql
  SELECT * FROM pg_locks;
  SELECT * FROM pg_blocking_pids();
  ```

- **Query Performance**:
  ```sql
  SELECT * FROM pg_stat_statements;
  ```

- **Table and Index Statistics**:
  ```sql
  \dt+
  \di+
  ```

### CLI Flags

- **pgbench**:
  - Run a benchmark with 10 clients, 1000 transactions per client:
    ```bash
    pgbench -i -s 1 testdb
    pgbench -c 10 -t 1000 testdb
    ```

- **psql**:
  - Connect to a database:
    ```bash
    psql -d testdb
    ```

- **pg_stat_statements**:
  - Reset statistics:
    ```sql
    SELECT pg_stat_statements_reset();
    ```

This lab guide provides a comprehensive set of exercises to verify the operational correctness of a PostgreSQL database system. By following these steps, you will gain a deeper understanding of storage page layouts, concurrency control, and crash recovery mechanisms.
