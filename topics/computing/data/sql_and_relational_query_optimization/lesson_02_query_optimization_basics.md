# SQL and Relational Query Optimization

## 1. First-Principles Intuition & Invariants

### The Fundamental Problem

A SQL query is a *declarative* specification: it describes *what* data to retrieve, not *how* to retrieve it. The query optimizer's job is to bridge that gap — to translate a declarative intent into an imperative execution strategy. This is not a lookup problem; it is a combinatorial search over a space of equivalent execution plans, where "equivalent" means semantically identical results but with potentially orders-of-magnitude differences in cost.

The core difficulty is that the search space is superexponential. For a query joining *n* tables, the number of distinct left-deep join trees alone is *n!*, and when bushy trees and commutativity are included the count grows to the Catalan number C(n) multiplied by per-node algorithm choices. PostgreSQL's planner switches from exhaustive dynamic programming to a Genetic Algorithm (GEQO) at `join_collapse_limit` (default 8) precisely because the DP cost becomes prohibitive.

### Relational Algebra as the Optimization Language

The optimizer does not work directly on SQL text. It first translates SQL into *relational algebra* — a closed, composable set of operators over relations (sets of tuples). The key operators are:

- **σ (Selection)**: filters rows by predicate.
- **π (Projection)**: retains a subset of columns.
- **⨝ (Join)**: combines tuples from two relations.
- **γ (Aggregation / Group-by)**
- **δ (Duplicate elimination)**
- **ρ (Rename)**
- **∪, ∩, − (Set operations)**

Relational algebra is *referentially transparent*: any sub-expression can be replaced by an equivalent expression without changing the result. This algebraic closure is what makes systematic query rewriting possible and correct.

### Semantic Invariants the Optimizer Must Uphold

**Invariant 1 — Semantic equivalence.** Every transformation must produce a plan whose result set is identical to the original query under all valid database states. This is non-trivial with NULLs (three-valued logic), `DISTINCT`, `LIMIT`/`OFFSET`, and non-deterministic functions like `random()`.

**Invariant 2 — Cost monotonicity.** Under the standard cost model, adding more operators to a plan cannot reduce its cost. This property allows dynamic programming to prune suboptimal partial plans early (the "principle of optimality").

**Invariant 3 — Statistics consistency.** The optimizer's cardinality estimates must be derived from a consistent snapshot of catalog statistics. Mid-query statistics changes (e.g., `ANALYZE` running concurrently) do not affect an already-compiled plan.

**Invariant 4 — Isolation from side effects.** A plan transformation may not change the *order* in which side-effecting expressions (functions with `VOLATILE` classification in PostgreSQL) are evaluated. This prevents incorrect reorderings of calls like `nextval()` or `now()`.

### Why Data Distribution Dominates Cardinality Estimation

The optimizer reduces the problem of "how much data flows through each operator?" to cardinality estimation. A naive independence assumption (that predicate selectivities multiply) produces:

```
sel(A AND B) ≈ sel(A) × sel(B)
```

This is accurate only when A and B are statistically independent. Real data is riddled with correlations — ZIP codes correlate with cities, age correlates with salary, product categories correlate with return rates. When the independence assumption breaks down, estimated cardinality can be off by orders of magnitude, forcing the optimizer into catastrophically wrong join orders.

Modern systems address this with:

- **Multi-column statistics** (PostgreSQL `CREATE STATISTICS`, SQL Server's column statistics on computed expressions).
- **Histograms** (equi-width, equi-depth, compressed) to represent non-uniform distributions.
- **Most-Common Values (MCVs)** for highly skewed columns.
- **Machine-learned cardinality estimators** (e.g., Naru, NeuroCard) that model joint distributions using deep generative models.

The following diagram shows the data flow from a SQL query through the optimizer pipeline to execution:

```mermaid
flowchart TD
    SQL["SQL Text"] --> Parser["Parser\n(AST)"]
    Parser --> Analyzer["Semantic Analyzer\n(Name resolution, type checking)"]
    Analyzer --> LogicalPlan["Logical Query Plan\n(Relational Algebra Tree)"]
    LogicalPlan --> Rewriter["Query Rewriter\n(View expansion, macro substitution)"]
    Rewriter --> Optimizer["Query Optimizer"]

    subgraph Optimizer["Query Optimizer"]
        direction TB
        RulePhase["Rule-Based Rewriting\n(Predicate pushdown, join reorder,\nsubquery unnesting)"]
        CostPhase["Cost-Based Search\n(DP / GEQO over plan space)"]
        RulePhase --> CostPhase
    end

    Catalog["Catalog & Statistics\n(Histograms, MCVs, NDV)"] --> CostPhase
    CostPhase --> PhysicalPlan["Physical Query Plan\n(Operators + Algorithms)"]
    PhysicalPlan --> Executor["Execution Engine\n(Volcano / Vectorized / JIT)"]
    Executor --> Result["Result Set"]
```

---

## 2. Core Architecture & Mechanics

### The Query Optimizer: Three Architectural Phases

Modern optimizers (PostgreSQL, SQL Server, Oracle, DB2) operate in three broadly defined phases, though implementations overlap them:

#### Phase 1 — Logical Rewriting (Rule-Based)

A set of algebraic equivalence rules is applied exhaustively or heuristically to transform the logical plan into a canonical, more-efficient form before cost estimation begins. These rules are provably correct and applied regardless of statistics.

Key rules:

**Predicate Pushdown**: Move `σ` operators as far down the tree as possible, reducing the cardinality of intermediate results.

```
σ_p(R ⨝ S)  →  (σ_p(R)) ⨝ S,   if p references only R
```

**Projection Pushdown**: Drop columns not needed by upstream operators early to reduce tuple width.

**Join Commutativity and Associativity**:
```
R ⨝ S  ≡  S ⨝ R
(R ⨝ S) ⨝ T  ≡  R ⨝ (S ⨝ T)
```
These two rules together are what enable join reordering.

**Subquery Unnesting / Decorrelation**: Correlated subqueries (which execute once per outer row) are transformed into joins. This is the single most important rewrite for OLTP queries.

```sql
-- Correlated subquery: O(n) executions of inner query
SELECT e.name FROM employees e
WHERE e.salary > (SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id);

-- Unnested form: single scan + join
SELECT e.name
FROM employees e
JOIN (SELECT dept_id, AVG(salary) AS avg_sal FROM employees GROUP BY dept_id) d
  ON e.dept_id = d.dept_id
WHERE e.salary > d.avg_sal;
```

#### Phase 2 — Cost-Based Plan Enumeration

The optimizer enumerates alternative physical implementations for each logical operator and selects the global minimum-cost plan using dynamic programming (Selinger's algorithm, 1979 — still the foundation of every major RDBMS optimizer).

The DP algorithm builds a table of optimal plans bottom-up:

1. Find optimal single-table access plans (seq scan vs. index scan).
2. For each pair of relations, find the optimal two-way join using the best single-table plans.
3. For each triple, find the optimal three-way join using the best two-way plans.
4. Continue until all relations are joined.

The key insight is that an optimal plan for a subset of relations can be reused in any superset plan — the optimal substructure property.

```mermaid
flowchart LR
    subgraph DP["DP Table (n=4 tables: A,B,C,D)"]
        S1["Level 1\n{A},{B},{C},{D}"]
        S2["Level 2\n{A,B},{A,C},{A,D}\n{B,C},{B,D},{C,D}"]
        S3["Level 3\n{A,B,C},{A,B,D}\n{A,C,D},{B,C,D}"]
        S4["Level 4\n{A,B,C,D}"]
    end
    S1 --> S2
    S2 --> S3
    S3 --> S4
```

#### Phase 3 — Physical Operator Selection

For each logical operator, the optimizer selects a physical implementation:

| Logical Operator | Physical Implementations |
|---|---|
| Join | Nested Loop Join, Hash Join, Merge Join, Index Nested Loop |
| Sort | External Merge Sort, In-memory Quicksort |
| Aggregation | Hash Aggregate, Sort-then-Stream Aggregate |
| Table Scan | Sequential Scan, Index Scan, Index-Only Scan, Bitmap Heap Scan |

The choice depends on estimated cardinalities, available memory (`work_mem` in PostgreSQL), sort order requirements of upstream operators, and index availability.

### The Cost Model

The cost model assigns a numeric cost to each operator. PostgreSQL's cost model is representative:

```
cost = cpu_cost + io_cost

io_cost  = pages_read × seq_page_cost      (sequential I/O)
         + random_pages × random_page_cost  (random I/O)

cpu_cost = tuples_processed × cpu_tuple_cost
         + tuples_qualified × cpu_operator_cost
```

The key parameters (`seq_page_cost`, `random_page_cost`, `cpu_tuple_cost`) are user-tunable and must reflect actual hardware. On modern NVMe SSDs, `random_page_cost` should be set near 1.1 (vs. the default 4.0 designed for spinning disks). Miscalibration here is one of the most common causes of bad plan choices in production.

**Hash Join cost model example:**

```
Build phase:  cost = N_inner × cpu_tuple_cost + N_inner/B × seq_page_cost
Probe phase:  cost = N_outer × cpu_tuple_cost + N_outer/B × seq_page_cost
Total memory: work_mem ≥ N_inner × avg_tuple_width  (to avoid batch spill)
```

Where *B* is the buffer pool size in pages. If `work_mem` is too small, the hash join spills to disk in multiple batches, dramatically increasing I/O cost.

### Index Architecture: B-Tree Internals

The B+ tree is the dominant index structure in relational databases (PostgreSQL, MySQL InnoDB, SQL Server, Oracle). Understanding its internals is essential for predicting when an index will be used.

```mermaid
flowchart TD
    Root["Root Node\n[30 | 60]"]
    IL["Internal Node\n[10 | 20]"]
    IR["Internal Node\n[40 | 50]"]
    IR2["Internal Node\n[70 | 80]"]

    L1["Leaf: 1,5,9"]
    L2["Leaf: 10,15,19"]
    L3["Leaf: 20,25,29"]
    L4["Leaf: 30,35,39"]
    L5["Leaf: 40,45,49"]
    L6["Leaf: 50,55,59"]
    L7["Leaf: 60,65,69"]
    L8["Leaf: 70,75,79"]
    L9["Leaf: 80,85,99"]

    Root --> IL
    Root --> IR
    Root --> IR2
    IL --> L1
    IL --> L2
    IL --> L3
    IR --> L4
    IR --> L5
    IR --> L6
    IR2 --> L7
    IR2 --> L8
    IR2 --> L9

    L1 -. "linked list" .-> L2
    L2 -. "linked list" .-> L3
    L3 -. "linked list" .-> L4
    L4 -. "linked list" .-> L5
    L5 -. "linked list" .-> L6
    L6 -. "linked list" .-> L7
    L7 -. "linked list" .-> L8
    L8 -. "linked list" .-> L9
```

A B+ tree of height *h* with branching factor *b* can index *b^h* entries. For a typical branching factor of 200 and height 3, this covers 8 million entries in 3 I/Os. All data lives in the leaf layer; internal nodes are purely routing. Leaves are linked in sorted order, enabling efficient range scans by following the leaf chain without re-traversing internal nodes.

**When the optimizer chooses NOT to use an index:**

The optimizer performs a break-even analysis. An index scan on a heap table incurs a *random* I/O per qualifying row (each row may be in a different page). If selectivity is low enough that most pages will be visited anyway, a sequential scan is cheaper:

```
Use index if: selectivity × table_pages > index_scan_break_even
```

For a typical spinning disk with `random_page_cost = 4`, the break-even is around 5–10% selectivity. For NVMe with `random_page_cost = 1.1`, it extends to 40–50% selectivity. This is why correctly setting `random_page_cost` matters enormously.

**Bitmap Index Scan** (PostgreSQL) is a hybrid: the index is first scanned to build an in-memory bitmap of matching TIDs (Tuple IDs), then the heap is accessed in physical page order (sequential), and finally a recheck filters out false positives. This amortizes the random-I/O penalty and is the preferred mode when selectivity is moderate.

### Statistics: Histograms and MCVs

PostgreSQL's `pg_statistic` table stores per-column statistics collected by `ANALYZE`:

- **`stadistinct`**: Number of distinct values (NDV), or negative fraction if estimated as a fraction of total rows.
- **`stanumbers` / `stavalues` (slot kind 1 — MCVs)**: The most-common values and their frequencies.
- **`stanumbers` / `stavalues` (slot kind 2 — histogram)**: Equi-depth histogram bucket boundaries.
- **`stanumbers` (slot kind 3 — correlation)**: Physical-to-logical order correlation (1.0 = perfectly sorted, relevant for index scan cost).

Cardinality estimation for a range predicate on a histogram:

```python
def estimate_range_selectivity(histogram_bounds, lo, hi):
    """
    Equi-depth histogram: each bucket covers equal fraction 1/num_buckets.
    Partial bucket interpolation for the boundary buckets.
    """
    n = len(histogram_bounds) - 1  # number of buckets
    bucket_sel = 1.0 / n

    lo_bucket = bisect.bisect_right(histogram_bounds, lo) - 1
    hi_bucket = bisect.bisect_left(histogram_bounds, hi) - 1

    lo_bucket = max(0, min(lo_bucket, n - 1))
    hi_bucket = max(0, min(hi_bucket, n - 1))

    if lo_bucket == hi_bucket:
        # Both endpoints in the same bucket — interpolate
        blo = histogram_bounds[lo_bucket]
        bhi = histogram_bounds[lo_bucket + 1]
        if bhi == blo:
            return 0.0
        return bucket_sel * (hi - lo) / (bhi - blo)

    # Partial contribution of first and last buckets + full middle buckets
    blo_hi = histogram_bounds[lo_bucket + 1]
    blo_lo = histogram_bounds[lo_bucket]
    left_frac = (blo_hi - lo) / (blo_hi - blo_lo) if blo_hi != blo_lo else 1.0

    bhi_hi = histogram_bounds[hi_bucket + 1]
    bhi_lo = histogram_bounds[hi_bucket]
    right_frac = (hi - bhi_lo) / (bhi_hi - bhi_lo) if bhi_hi != bhi_lo else 1.0

    full_buckets = hi_bucket - lo_bucket - 1
    return bucket_sel * (left_frac + full_buckets + right_frac)
```

This is the essential logic behind PostgreSQL's `ineq_histogram_selectivity`. When the actual data has multi-modal distributions or strong correlations, this linear interpolation produces significant errors, motivating extended statistics.

---

## 3. Physical Join Algorithms: Deep Mechanics

### Nested Loop Join (NLJ)

```
for each outer_tuple in R:
    for each inner_tuple in S where join_predicate(outer_tuple, inner_tuple):
        emit(outer_tuple, inner_tuple)
```

**Cost**: O(|R| × |S|) in the worst case. With an index on S, the inner loop becomes O(log|S|) per outer row: total O(|R| × log|S|).

**Optimal when**: |R| is small (driving table fits in L3 cache), or an index on the inner table reduces inner loop cost drastically. This is the dominant join algorithm in OLTP workloads where queries touch a small number of rows.

**Block Nested Loop (BNL)** is the disk-aware variant: load a block of outer tuples into memory, scan the inner table once against all buffered outer tuples. Reduces inner table scans from |R| to ⌈|R| / buffer_size⌉.

### Hash Join

```
-- Build phase
for each inner_tuple in S:
    h = hash(inner_tuple[join_key])
    HT[h].append(inner_tuple)

-- Probe phase
for each outer_tuple in R:
    h = hash(outer_tuple[join_key])
    for each candidate in HT[h]:
        if join_predicate(outer_tuple, candidate):
            emit(outer_tuple, candidate)
```

**Cost**: O(|R| + |S|) CPU time. Memory requirement: O(|S|) — the entire inner (build-side) relation must fit in `work_mem`. When it does not, a *Grace Hash Join* partitions both R and S into *k* partitions using a first hash function, then independently hash-joins matching partition pairs. The number of passes required is ⌈log_{work_mem/B}(|S|/work_mem)⌉ where *B* is the number of partitions.

**Optimal when**: large equi-joins with no useful sort order, inner relation fits in memory. Not applicable for non-equi-join predicates.

### Sort-Merge Join (SMJ)

```
sort R on join key
sort S on join key

i, j = 0, 0
while i < len(R) and j < len(S):
    if R[i].key < S[j].key:   i++
    elif R[i].key > S[j].key: j++
    else:
        # emit all matching pairs (handle duplicates carefully)
        mark = j
        while j < len(S) and S[j].key == R[i].key:
            emit(R[i], S[j]); j++
        i++
        if i < len(R) and R[i].key == S[mark].key:
            j = mark  # backtrack for many-to-many
```

**Cost**: O(|R| log|R| + |S| log|S|) for sorting, then O(|R| + |S|) for the merge. If both inputs are already sorted (from an index scan or prior sort), the sort phase is eliminated — this is the primary reason SMJ appears in plans involving `ORDER BY` or `GROUP BY` on join keys.

**Optimal when**: both inputs already arrive in sorted order, or when a downstream `ORDER BY` / `GROUP BY` can consume the sorted output (eliminating a later sort).

```mermaid
sequenceDiagram
    participant QO as Query Optimizer
    participant SE as Statistics Engine
    participant DP as DP Planner
    participant Exec as Executor

    QO->>SE: Request cardinality estimates for join predicates
    SE-->>QO: Histogram + MCV estimates per column
    QO->>DP: Enumerate join orders and algorithms
    DP->>DP: Build DP table (bottom-up over subsets)
    DP-->>QO: Optimal plan tree with cost annotations
    QO->>Exec: Dispatch physical plan
    Exec->>Exec: Execute (Volcano pull model or push/vectorized)
    Exec-->>QO: Result rows + runtime statistics
    Note over QO,Exec: Adaptive re-optimization may feed\nruntime stats back for mid-query correction
```

---

## 4. High-Performance Optimization Techniques

### Predicate Pushdown: A Concrete Example

Consider the following query on a 100M-row `orders` table and a 10M-row `customers` table:

```sql
SELECT c.name, o.total
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'shipped'
  AND c.country = 'DE';
```

Without pushdown, the join processes 100M × 10M combinations before filtering. With pushdown:

1. `σ_{status='shipped'}` applied to `orders` before the join — reduces to ~10M rows (assuming 10% selectivity).
2. `σ_{country='DE'}` applied to `customers` before the join — reduces to ~500K rows.
3. Join operates on 10M × 500K — vastly cheaper.

The transformation is legal because both predicates reference a single table (they are "local predicates"). A predicate referencing both tables (e.g., `o.total > c.credit_limit`) cannot be pushed below the join.

### Join Reordering and the Importance of Cardinality

The query optimizer's most impactful decision for multi-table queries is join order. Consider joining three tables: `orders` (100M rows), `customers` (1M rows), `order_items` (500M rows).

The optimal strategy is to perform the most selective joins first to minimize intermediate result sizes:

```
-- Bad order: orders ⨝ order_items → 500M intermediate → ⨝ customers
-- Good order: orders ⨝ customers → 1M intermediate → ⨝ order_items
```

A systematic way to understand the optimizer's choice is to compute the *join selectivity*:

```
|R ⨝ S| ≈ |R| × |S| × selectivity(join_predicate)
```

For a foreign key join (every FK value exists in PK), selectivity ≈ 1/|S|, giving |R ⨝ S| ≈ |R|. When the optimizer has correct cardinality estimates, it naturally gravitates toward FK-driven joins from largest to smallest dimension table.

### Subquery Unnesting / Decorrelation

Correlated subqueries are the single most common source of accidental O(n²) behavior in SQL:

```sql
-- Anti-pattern: correlated EXISTS subquery (executes once per orders row)
SELECT o.id
FROM orders o
WHERE EXISTS (
    SELECT 1 FROM blacklist b WHERE b.customer_id = o.customer_id
);

-- Equivalent semi-join (single scan of blacklist):
SELECT DISTINCT o.id
FROM orders o
JOIN blacklist b ON b.customer_id = o.customer_id;

-- Or: Hash anti-join (for NOT EXISTS)
SELECT o.id
FROM orders o
WHERE o.customer_id NOT IN (SELECT customer_id FROM blacklist);
-- Note: NOT IN has NULL-safety issues; prefer NOT EXISTS or LEFT JOIN / IS NULL
```

Modern optimizers (PostgreSQL ≥ 7.4, SQL Server, Oracle) automatically decorrelate most `EXISTS`/`IN` subqueries into semi-joins or anti-joins. However, complex correlated subqueries in `SELECT` lists or with aggregation may still be executed as nested loops.

### Partition Pruning

For partitioned tables, the optimizer evaluates partition constraints against query predicates at plan time (static pruning) or at execution time (dynamic pruning for parameterized queries).

```sql
-- Table partitioned by order_date RANGE (monthly)
CREATE TABLE orders (
    id          BIGINT,
    order_date  DATE,
    customer_id INT,
    total       NUMERIC
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_01 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- ... additional partitions ...

-- This query touches only one partition (Jan 2024):
EXPLAIN SELECT * FROM orders WHERE order_date BETWEEN '2024-01-10' AND '2024-01-20';
```

The `EXPLAIN` output will show only `orders_2024_01` in the scan list — the other 11+ partitions are pruned without being read. This is a form of *constraint exclusion* — the planner uses `CHECK` constraints embedded in partition definitions.

### Materialized CTEs vs. Inline CTEs

A common misconception: CTEs are **not** always optimization fences. PostgreSQL ≤ 11 always materialized CTEs (computed once, result stored). PostgreSQL ≥ 12 uses a cost-based decision:

- CTEs referenced once and without side effects are **inlined** by default (treated as subqueries, allowing predicate pushdown across the CTE boundary).
- CTEs with `MATERIALIZED` keyword are always computed once.
- CTEs with side effects (`UPDATE`, `INSERT`, `DELETE ... RETURNING`) are always materialized.

```sql
-- PostgreSQL 12+: this CTE is inlined; the predicate on status pushes through
WITH recent_orders AS (
    SELECT * FROM orders WHERE order_date > CURRENT_DATE - INTERVAL '30 days'
)
SELECT * FROM recent_orders WHERE status = 'pending';

-- Force materialization (optimization fence):
WITH recent_orders AS MATERIALIZED (
    SELECT * FROM orders WHERE order_date > CURRENT_DATE - INTERVAL '30 days'
)
SELECT * FROM recent_orders WHERE status = 'pending';
```

### Covering Indexes and Index-Only Scans

An index covers a query when all columns referenced (both in predicates and in the `SELECT` list) are present in the index. The executor can then return results directly from the index without touching the heap at all.

```sql
-- Query:
SELECT customer_id, total FROM orders WHERE status = 'shipped' AND order_date > '2024-01-01';

-- A covering index:
CREATE INDEX idx_orders_covering ON orders (status, order_date) INCLUDE (customer_id, total);
-- (status, order_date) are search/filter keys; (customer_id, total) are payload columns
```

In PostgreSQL, the `INCLUDE` clause (available since v11) adds non-key columns to the leaf level of the B+ tree without participating in the sort order, avoiding index bloat while enabling index-only scans.

**Visibility map caveat**: PostgreSQL's index-only scans must consult the *visibility map* to determine whether the index-returned tuple is visible to the current transaction. Pages not yet set as all-visible in the visibility map require a heap fetch to check. Immediately after a large `VACUUM`, index-only scan performance improves dramatically.

### Vectorized Execution and SIMD

The classic Volcano/Iterator model (each operator calls `next()` on its child one tuple at a time) incurs enormous function-call overhead per row. Vectorized execution (pioneered by VectorWise / MonetDB, now implemented in DuckDB, ClickHouse, Snowflake, and partially in PostgreSQL via JIT) processes batches of 1,000–10,000 rows per call, enabling:

1. **SIMD utilization**: batch operations on column arrays map directly to AVX-512 instructions.
2. **Cache efficiency**: a column array fits in L1/L2 cache; accessing it repeatedly for different operations avoids cache thrashing.
3. **Branch prediction improvement**: tight loops over homogeneous data are highly predictable.

```c
/* Simplified vectorized filter — SIMD AVX2 for int32 comparison */
#include <immintrin.h>
#include <stdint.h>

void filter_eq_i32(const int32_t *col, int32_t val,
                   uint8_t *out_bitmap, int n) {
    __m256i vval = _mm256_set1_epi32(val);
    int i = 0;
    for (; i <= n - 8; i += 8) {
        __m256i vcol = _mm256_loadu_si256((const __m256i *)(col + i));
        __m256i vcmp = _mm256_cmpeq_epi32(vcol, vval);
        int mask = _mm256_movemask_ps((__m256)vcmp);
        /* pack 8 comparison bits into the bitmap */
        out_bitmap[i / 8] = (uint8_t)mask;
    }
    /* scalar tail */
    for (; i < n; i++) {
        int byte = i / 8, bit = i % 8;
        if (col[i] == val)
            out_bitmap[byte] |= (1u << bit);
    }
}
```

### JIT Compilation

PostgreSQL 11+ optionally JIT-compiles expression evaluation and tuple deforming using LLVM. The JIT compiler generates native code for specific expressions (e.g., `WHERE salary * 1.1 > 50000`), eliminating interpreter dispatch overhead. JIT is most beneficial for CPU-bound queries over large scans; for small queries, JIT compilation overhead exceeds the savings.

JIT control:
```sql
SET jit = on;                      -- enable JIT (default on in PG 15+)
SET jit_above_cost = 100000;       -- JIT query plans above this cost
SET jit_inline_above_cost = 500000; -- inline functions above this cost
SET jit_optimize_above_cost = 500000; -- run LLVM optimization passes
```

---

## 5. Reading and Interpreting EXPLAIN ANALYZE

`EXPLAIN ANALYZE` executes the query and annotates the plan with actual runtime statistics. Understanding this output is the primary tool for diagnosing optimizer failures.

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT c.name, SUM(o.total) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date >= '2024-01-01'
GROUP BY c.name
ORDER BY revenue DESC
LIMIT 10;
```

Annotated output interpretation:

```
HashAggregate  (cost=184321.00..184331.00 rows=1000 width=48)
               (actual time=2341.221..2342.108 rows=987 loops=1)
  --  ^^^^^ estimated cost / rows vs. actual time (ms) / rows
  Buffers: shared hit=12043 read=8721
  --  ^^^^^ cache hits vs. disk reads — high read count means poor caching
  ->  Hash Join  (cost=25000.00..181821.00 rows=500000 width=24)
                 (actual time=312.445..2201.333 rows=502341 loops=1)
        Hash Cond: (o.customer_id = c.id)
        Buffers: shared hit=10231 read=8721
        ->  Seq Scan on orders  (cost=0.00..155000.00 rows=500000 width=16)
                                (actual time=0.021..1842.331 rows=502341 loops=1)
              Filter: (order_date >= '2024-01-01'::date)
              Rows Removed by Filter: 497659         <-- 50% of table scanned and discarded
              Buffers: shared hit=8900 read=8721
        ->  Hash  (cost=15000.00..15000.00 rows=1000000 width=20)
                  (actual time=308.112..308.112 rows=1000000 loops=1)
              Buckets: 131072  Batches: 8  Memory Usage: 24576kB
              --  ^^^^^ Batches > 1 means hash spilled to disk — increase work_mem
```

**Key diagnostic signals:**

| Signal | Diagnosis |
|---|---|
| Estimated rows ≪ actual rows | Underestimated cardinality → run `ANALYZE`, consider extended statistics |
| `Batches > 1` in Hash Join/Aggregate | `work_mem` too small — increase or force merge join |
| High `Rows Removed by Filter` on a Seq Scan | Missing index on filter column |
| `loops` > 1 on inner side of Nested Loop | NLJ on large inner table — consider Hash Join via `enable_nestloop=off` |
| `Buffers: read` >> `Buffers: hit` | Working set exceeds `shared_buffers` — increase or use prefetching |

---

## 6. Failure Modes and Mitigations

### Cardinality Estimation Failure

The most common root cause of bad plans. Symptoms: plan uses NLJ where HJ is optimal, or chooses a small table as the driving side of a large cross-join.

**Diagnosis:**
```sql
-- Find tables with stale statistics
SELECT schemaname, tablename, last_analyze, last_autoanalyze, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
WHERE last_analyze < NOW() - INTERVAL '1 day'
   OR last_analyze IS NULL
ORDER BY n_live_tup DESC;

-- Check if estimates are far from actuals
EXPLAIN (ANALYZE, FORMAT JSON) <your query>;
-- Compare 'Plan Rows' vs 'Actual Rows' at each node
```

**Mitigations:**
1. `ANALYZE <table>` — refresh statistics.
2. Increase `default_statistics_target` (default 100; increase to 500 for heavily skewed columns).
3. Create multi-column statistics for correlated columns:
   ```sql
   CREATE STATISTICS orders_stats (dependencies, ndistinct, mcv)
       ON status, order_date FROM orders;
   ANALYZE orders;
   ```
4. Use query hints (`pg_hint_plan` extension) as a last resort.

### Parameter Sniffing / Plan Cache Instability

Prepared statements and stored procedures compile a plan against the first set of parameter values. If the data distribution changes significantly (e.g., querying for a rare vs. common status value), a cached plan may be catastrophically suboptimal for different parameters.

```sql
-- PostgreSQL uses generic plans after 5 executions by default
-- Force custom plan per-execution:
SET plan_cache_mode = force_custom_plan;  -- disable plan caching entirely
-- Or selectively, in connection strings or session config
```

SQL Server's equivalent is `OPTION (RECOMPILE)` or `OPTIMIZE FOR UNKNOWN`. Oracle uses bind variable peeking with adaptive cursor sharing.

### Join Order Explosion with GEQO

For queries with more than `join_collapse_limit` (default 8) tables, PostgreSQL's GEQO genetic algorithm may produce non-reproducible, suboptimal plans. The randomized nature of GEQO means the same query can get different plans across runs.

**Mitigation**: Increase `join_collapse_limit` to allow exhaustive DP for queries you control, or rewrite the query to explicitly specify join order using subqueries with `OFFSET 0` as a materialization barrier.

### Work Memory Pressure and Spill-to-Disk

Hash joins and hash aggregations both require memory for hash tables. When `work_mem` is insufficient, they spill to disk using multiple passes. A single query can open multiple sort/hash operations simultaneously; total memory consumption is `work_mem × number_of_operators`.

**Rule of thumb for setting `work_mem`:**
```
work_mem = (available_RAM × 0.25) / (max_concurrent_queries × avg_operators_per_query)
```

For an OLTP server with 64GB RAM, 100 concurrent connections, and ~3 operators per query:
```
work_mem ≈ (64GB × 0.25) / (100 × 3) ≈ 53MB
```

This is the per-operator allocation, so set it conservatively and increase for specific analytical sessions.

### Stale Visibility Map and Index Bloat

Dead tuples accumulate after `UPDATE`/`DELETE` and are only reclaimed by `VACUUM`. Excessive dead tuples:
1. Force index scans to visit heap pages for visibility checks (defeating index-only scans).
2. Inflate table size, increasing seq scan cost.
3. Cause histogram buckets to reflect deleted data.

Monitor and automate:
```sql
-- Tables with significant bloat
SELECT relname,
       pg_size_pretty(pg_total_relation_size(oid)) AS total_size,
       n_dead_tup,
       n_live_tup,
       round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY dead_pct DESC;
```

---

## 7. Adaptive Query Optimization

Static query optimization makes all decisions before execution begins. This is fundamentally limited: estimates computed at plan time can be wrong by orders of magnitude for complex multi-join queries because estimation errors *compound* (multiply) at each join.

### Re-Optimization Strategies

**Eddies** (Avnur & Hellerstein, 2000): a theoretical model where tuples are routed dynamically through operators based on observed selectivity, with no fixed join order.

**Mid-Query Re-Optimization** (SQL Server 2017+ "Adaptive Joins", Oracle's "Adaptive Plans"): the executor monitors actual row counts at key points. If the count deviates significantly from the estimate, it switches to an alternative pre-compiled plan fragment at a designated "switch point."

```sql
-- SQL Server: Adaptive Join will choose between NLJ and Hash Join at runtime
-- based on actual rows flowing into the join
SELECT *
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending'
OPTION (USE HINT ('ENABLE_PARALLEL_PLAN_PREFERENCE'));
```

**PostgreSQL Adaptive Execution**: as of PostgreSQL 16, there is no built-in mid-query re-optimization, but `pg_hint_plan` and the `auto_explain` extension with `log_min_duration` provide post-hoc correction capabilities.

**Learned Query Optimizers**: recent research systems (Bao, Neo, HybridQO) use reinforcement learning or tree-structured neural networks to predict plan quality, feeding runtime feedback into future optimization decisions. These are not yet production-standard in mainstream RDBMS but are deployed in specialized analytical systems.

---

## 8. Production Optimization Workflow

A systematic, repeatable approach to diagnosing and fixing slow queries:

```mermaid
flowchart TD
    A["Identify slow query\n(pg_stat_statements, slow query log)"]
    B["EXPLAIN ANALYZE BUFFERS\n(capture actual vs. estimated rows)"]
    C{"Large estimate/\nactual divergence?"}
    D["Statistics fix:\nANALYZE, increase target,\ncreate extended stats"]
    E{"Index missing\nor unused?"}
    F["Add covering index\nor rewrite to be SARGable"]
    G{"Memory spill\nor batch > 1?"}
    H["Increase work_mem\nor force merge join"]
    I{"Query logic\nsuboptimal?"}
    J["Rewrite: decorrelate,\npush predicates, unnest CTEs"]
    K["Deploy fix, monitor\npg_stat_statements regression"]

    A --> B
    B --> C
    C -- Yes --> D
    D --> B
    C -- No --> E
    E -- Yes --> F
    F --> B
    E -- No --> G
    G -- Yes --> H
    H --> B
    G -- No --> I
    I -- Yes --> J
    J --> B
    I -- No --> K
```

### SARGability: Writing Index-Friendly Predicates

A predicate is *SARGable* (Search ARGument Able) if the query engine can use an index to satisfy it without evaluating a function over every row.

```sql
-- NOT SARGable: function applied to indexed column, disables index
WHERE YEAR(order_date) = 2024
WHERE UPPER(email) = 'USER@EXAMPLE.COM'
WHERE customer_id + 1 = 1001

-- SARGable equivalents:
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
WHERE email = lower('USER@EXAMPLE.COM')   -- or use a functional index
WHERE customer_id = 1000

-- Functional index to handle case-insensitive email lookups:
CREATE INDEX idx_customers_email_lower ON customers (lower(email));
-- Now this IS SARGable with the functional index:
WHERE lower(email) = 'user@example.com'
```

### Common Table Expression Optimization Patterns

```sql
-- Pattern: recursive CTE for hierarchical data (org chart, BOM)
WITH RECURSIVE org_tree AS (
    -- Base case: root nodes
    SELECT id, name, manager_id, 0 AS depth, ARRAY[id] AS path
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: children
    SELECT e.id, e.name, e.manager_id, ot.depth + 1, ot.path || e.id
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
    WHERE NOT e.id = ANY(ot.path)  -- cycle detection
)
SELECT id, name, depth, path
FROM org_tree
ORDER BY path;
```

Recursive CTEs use a *working table* (the recursive term's result set) that is re-evaluated each iteration. The optimizer cannot apply normal transformations across the recursion boundary — the `UNION ALL` is always materialized. Indexing the join column (`manager_id`) is essential for performance.

---

## 9. Benchmark: Demonstrating Optimization Impact

The following Go benchmark demonstrates the query planning and execution latency difference between an unoptimized and optimized query path, using `pgx` against a local PostgreSQL instance:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func runQuery(ctx context.Context, pool *pgxpool.Pool, query string, args ...any) (int, time.Duration) {
	start := time.Now()
	rows, err := pool.Query(ctx, query, args...)
	if err != nil {
		log.Fatalf("query error: %v", err)
	}
	defer rows.Close()
	count := 0
	for rows.Next() {
		count++
	}
	if err := rows.Err(); err != nil {
		log.Fatalf("row iteration error: %v", err)
	}
	return count, time.Since(start)
}

func main() {
	ctx := context.Background()

	pool, err := pgxpool.New(ctx, "postgres://user:pass@localhost:5432/benchdb")
	if err != nil {
		log.Fatalf("connection pool error: %v", err)
	}
	defer pool.Close()

	// Unoptimized: correlated subquery, non-SARGable predicate
	unoptimized := `
		SELECT o.id, o.total
		FROM orders o
		WHERE EXTRACT(YEAR FROM o.order_date) = 2024
		  AND o.customer_id IN (
		      SELECT id FROM customers WHERE UPPER(country) = 'DE'
		  )`

	// Optimized: SARGable range, decorrelated with JOIN, covering index assumed
	optimized := `
		SELECT o.id, o.total
		FROM orders o
		JOIN customers c ON o.customer_id = c.id
		WHERE o.order_date >= '2024-01-01' AND o.order_date < '2025-01-01'
		  AND c.country = 'DE'`

	const iterations = 5

	fmt.Println("=== Query Optimization Benchmark ===")
	var totalUnopt, totalOpt time.Duration

	for i := range iterations {
		rows, dur := runQuery(ctx, pool, unoptimized)
		fmt.Printf("[unoptimized] run %d: %d rows in %v\n", i+1, rows, dur)
		totalUnopt += dur
	}

	for i := range iterations {
		rows, dur := runQuery(ctx, pool, optimized)
		fmt.Printf("[optimized]   run %d: %d rows in %v\n", i+1, rows, dur)
		totalOpt += dur
	}

	fmt.Printf("\nAvg unoptimized: %v\n", totalUnopt/iterations)
	fmt.Printf("Avg optimized:   %v\n", totalOpt/iterations)
	fmt.Printf("Speedup factor:  %.1fx\n", float64(totalUnopt)/float64(totalOpt))
}
```

---

## Summary of Key Mental Models

**Cardinality is king.** Every poor plan ultimately traces back to a cardinality estimate error. When a plan is bad, check estimated vs. actual row counts at each node before anything else.

**Cost model calibration matters.** The optimizer is only as good as its cost model's calibration to actual hardware. `random_page_cost`, `seq_page_cost`, and `cpu_tuple_cost` must reflect the storage substrate (NVMe vs. HDD vs. cloud object storage).

**Transformations are algebraic, not heuristic.** Rule-based rewrites (predicate pushdown, subquery unnesting) are correct by construction. Cost-based decisions (join order, algorithm choice) are estimates and can be wrong. Knowing which category a decision falls into determines how to debug it.

**The optimizer is a search problem.** For large join counts, exhaustive search is intractable. GEQO and similar heuristics trade optimality for tractability. Explicitly structuring complex queries (CTEs, subquery ordering) can guide the search toward better plans.

**Memory sizing determines algorithm choice.** `work_mem` directly determines whether hash join and hash aggregation operate in-memory (fast) or spill to disk (slow). Matching `work_mem` to the working set size of the dominant operators is the highest-leverage per-query tuning action available.
