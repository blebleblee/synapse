# Repaired: Path Normalization for Mastery and Lesson Progress

## 1. Problem and Root Cause

### Journey Step Affected
**Mark progress → Reload and resume**

### Root Cause
1. **Frontend Call Contract:** In `LessonViewer.tsx` (line 879), the "Mark Complete" toggle passed `topic.path` to `onToggleLessonCompletion`.
2. **Backend Topic Path Format:** In `app/backend/main.py` (line 1023), `get_topic_details` returned `"path": str(sub_path.relative_to(WORKSPACE_ROOT))`, evaluating to `topics/domain/discipline/topic` with a leading `topics/` directory.
3. **Key Mismatch in SQLite:** `learning_engine/mastery.py` only stripped leading/trailing slashes (`subtopic_path.strip("/")`) and did not strip the `topics/` prefix. Consequently, lesson completion was inserted into the `mastery` table under `topics/domain/discipline/topic`.
4. **Desynchronized Query Lookups:** The sidebar tree (`/api/tree` via `topic_manager.py`, line 150) and topic details (`/api/topic` via `main.py`, line 1026) queried completion records using the canonical 3-segment relative path `domain/discipline/topic` (without `topics/`). The query returned empty results (`[]`), leaving the sidebar progress counter unincremented and reverting the lesson completion button on reload.
5. **Stale Tree Cache:** `app/backend/main.py` did not call `invalidate_topic_tree_cache()` on mastery or lesson completion updates, causing `/api/tree` to serve stale cached counts for up to 60 seconds.
6. **Concurrent Read-Modify-Write Window:** Deferred transactions allowed concurrent updates to read overlapping rows before acquiring a write lock, risking lost updates under simultaneous requests.

---

## 2. Changes Made & Transaction Hardening

1. **Transaction Lifecycle Hardening (`BEGIN IMMEDIATE`):**
   - In `learning_engine/mastery.py`, both `set_subtopic_mastery()` and `toggle_lesson_completion()` now acquire the write transaction **before** reading rows using `conn.execute("BEGIN IMMEDIATE")`.
   - The entire read-modify-write cycle (fetching `c_row` and `l_row`, merging state/lessons, writing canonical row, deleting legacy row) runs within that single transaction.
   - Structured with explicit `conn.commit()` and `conn.rollback()` handling; lock errors and exceptions are raised without being swallowed; connection is closed in `finally`.
2. **Deterministic Coexistence Merging:**
   - Added shared helpers `_fetch_topic_records(conn, canonical_path)` and `resolve_topic_state(canonical_row, legacy_row)`:
     - Canonical state takes precedence when a canonical row exists; otherwise legacy state is used.
     - Completed lessons from both rows are merged without duplicates and sorted.
   - Read operations (`get_subtopic_mastery()`, `get_completed_lessons()`) do not mutate the database.
   - Writes consolidate atomically into the canonical row and delete the legacy prefixed row.
   - `/api/mastery` groups by `normalize_topic_path(row["path"])` and resolves state using `resolve_topic_state`, independent of SQL row order.
3. **Warm-Cache Invalidation:**
   - `/api/mastery` and `/api/mastery/lesson` invoke `invalidate_topic_tree_cache()`, ensuring `/api/tree` reflects updated completion counts immediately.

---

## 3. Existing-Data Behavior & Compatibility

- **Read-time compatibility:** Preexisting rows stored in `mastery` with the `topics/` prefix are found and resolved alongside canonical records without modifying the database.
- **Write-time consolidation:** When progress is updated on a topic that has a legacy prefixed row, completed lessons from both rows are merged into the canonical row (`domain/cat/sub`), and the legacy row is deleted within the atomic `BEGIN IMMEDIATE` transaction.
- **Zero database migrations:** No schema changes or raw SQL migrations are performed on the real database.
- **Limitation:** Raw SQLite databases that are never accessed by application writes will retain their historical prefixed rows until the first write consolidation occurs; however, all read queries dynamically resolve them.

---

## 4. Verification Commands and Results

1. **Targeted Concurrency and Legacy Tests (`tests/test_mastery.py`):**
   ```bash
   .venv/bin/python -m pytest tests/test_mastery.py -k "concurrent or toggle_off or coexist or legacy"
   # Output: 4 PASSED
   ```

2. **Targeted Warm-Cache API Invalidation Test (`tests/test_api.py`):**
   ```bash
   .venv/bin/python -m pytest tests/test_api.py -k "prefixed_and_canonical_sync"
   # Output: 1 PASSED
   ```

3. **Combined Targeted Mastery and API Suites:**
   ```bash
   .venv/bin/python -m pytest tests/test_mastery.py tests/test_api.py
   # Output: 29 PASSED in 12.63s
   ```

4. **Full Backend Test Suite:**
   ```bash
   .venv/bin/python -m pytest
   # Output: 79 PASSED in 33.10s
   ```

5. **Frontend Unit Tests:**
   ```bash
   npm run test  # working directory: app/frontend
   # Output: 7 PASSED in 124ms
   ```

*Note on verification scope: Verification was conducted using automated backend unit, concurrent threading barriers, and in-process HTTP ASGI integration tests. Browser UI behavior was not verified with an automated end-to-end browser runner.*
