# Baseline Verification Report

Conducted on: November 21, 2026
Workspace: `<repo>`

## Summary Table

| Check | Command | Working Directory | Status | Result / Diagnostics |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Tests** | `.venv/bin/python -m pytest` | `<repo>` | **PASS** | 72 tests passed, 0 failed (30.24s) |
| **Frontend Tests** | `npm run test` (`node --test 'src/**/*.test.ts'`) | `<repo>/app/frontend` | **PASS** | 7 tests passed, 0 failed (128ms) |
| **Frontend Lint** | `npm run lint` (`oxlint`) | `<repo>/app/frontend` | **PASS** | 0 errors, 25 warnings |
| **Frontend Build** | `npm run build` (`tsc -b && vite build`) | `<repo>/app/frontend` | **PASS** | 0 errors, built in 408ms (3644 modules) |

---

## Detailed Check Findings

### 1. Backend Tests
- **Status:** **PASS**
- **Command:** `.venv/bin/python -m pytest`
- **Working Directory:** `<repo>`
- **Results:**
  - 72 tests collected, 72 passed, 0 failed, 0 skipped in 30.24s.
  - Test suites executed:
    - `tests/test_api.py` (18 tests) — REST endpoints, graph, tree, mastery persistence, cluster settings, packages endpoints, security sanitizer.
    - `tests/test_auth.py` (3 tests) — Auth disabled mode, auth token verification, rate limiting.
    - `tests/test_chat_and_mentor.py` (5 tests) — Socratic mentor instruction builder, language directives, connectivity check, non-streaming & streaming chat history handling.
    - `tests/test_cluster_pins.py` (3 tests) — Host normalization, node model pinning, settings endpoints.
    - `tests/test_domain_strategies.py` (5 tests) — Domain strategy architecture and lab toolchain blueprints.
    - `tests/test_exporter.py` (1 test) — Real handbook compilation into temporary export directory without mocks.
    - `tests/test_graph.py` (3 tests) — DAG prerequisite graph, node/edge integrity, dependency resolution.
    - `tests/test_isolation_regression.py` (6 tests) — Verification of global path isolation, rejection of unexpected outbound network calls, rejection of unmocked AI generation, rejection of subprocess executions, and rejection of PTY launches.
    - `tests/test_mastery.py` (4 tests) — Mastery competence state transitions, atomic persistence, lesson completion toggling.
    - `tests/test_packages.py` (1 test) — Package export and install lifecycle.
    - `tests/test_search.py` (7 tests) — Keyword search, 2-character queries, search validation, flashcards generation.
    - `tests/test_taxonomy_compliance.py` (8 tests) — Explicit read-only audit of real repository curriculum taxonomy, zero numbered directories, canonical depth, zero duplicate lesson numbers.
    - `tests/test_topic_manager.py` (8 tests) — Topic tree hierarchy, path traversal security, subtopic resolution, persona retrieval.

---

### Review Findings & Acceptance Blocker Repairs

During independent review, two regressions were identified and repaired:

#### Regression 1: Broken `export_handbook()` in `learning_engine/exporter.py`
- **Root Cause:** A previous refactoring left inconsistent variable names (`domain_title` referenced before definition, `out_file` referenced instead of `output_path`) and dropped imports for `get_topic_tree` and `get_unit_lessons`. Calling `export_handbook()` crashed with `NameError`.
- **Repair:**
  - Restored imports `from .topic_manager import get_topic_tree, get_unit_lessons`.
  - Consistently defined `domain_title = domain.replace('_', ' ').title()` and `output_path = out_dir / f"{domain}_handbook.md"`.
  - Ensured content is written directly to `output_path` inside `get_exports_dir()`.
  - Added regression test `tests/test_exporter.py::test_export_handbook_real_execution` executing `export_handbook("computing")` without mocks, verifying file creation inside the temporary export directory, title formatting, and lesson content aggregation. Confirmed empirical test failure prior to fix and clean pass after repair.
- **Verification Command:**
  ```bash
  .venv/bin/python -m pytest tests/test_exporter.py
  # Result: 1 passed in 1.04s
  ```

#### Regression 2: Diluted Repository Taxonomy Audit Coverage
- **Root Cause:** Global test isolation redirected `TOPICS_DIR` in all modules to a minimal test fixture directory containing only 6 seeded courses. Consequently, `tests/test_taxonomy_compliance.py` was auditing the minimal temporary fixtures instead of verifying the real repository curriculum.
- **Repair:**
  - Decoupled read-only repository audits in `tests/test_taxonomy_compliance.py` from temporary application workspace overrides.
  - Defined `REPO_TOPICS_DIR = (REPO_ROOT / "topics").resolve()`.
  - Updated all taxonomy audit tests to inspect `REPO_TOPICS_DIR` in a strictly read-only manner (no generation, cleanup, or database side effects).
  - Added `test_audit_targets_real_repository_curriculum()` verifying that the audited directory is the real repository path, is not inside temporary folders, and contains full curriculum content across all domains (without hardcoding an exact topic count).
  - Maintained full temporary workspace isolation for all other application test suites (`test_api.py`, `test_packages.py`, etc.).
- **Verification Command:**
  ```bash
  .venv/bin/python -m pytest tests/test_taxonomy_compliance.py
  # Result: 8 passed in 3.70s
  ```

- **Combined Targeted Verification:**
  ```bash
  .venv/bin/python -m pytest tests/test_exporter.py tests/test_taxonomy_compliance.py
  # Result: 9 passed in 3.89s
  ```

---

### Test-Process Isolation Protections & Architecture

- **Early Database Isolation:** A unique temporary run directory is initialized at `conftest.py` load time, unconditionally overriding `SYNAPSE_DB_PATH` before application modules are imported. Each test runs against its own fresh SQLite database in `tmp_path` initialized via `init_db()`.
- **Global Filesystem Isolation:** Application tests run within an isolated temporary workspace (`tmp_path / "workspace"`) and topics directory (`tmp_path / "workspace" / "topics"`), initialized with minimal fixtures. Package deletion tests delete only temporary fixtures; repository curriculum is never mutated.
- **Process & PTY Interception:** `subprocess.run`, `subprocess.Popen`, `subprocess.call`, `asyncio.create_subprocess_*`, and `pty.openpty` / `pty.fork` raise immediate `RuntimeError` exceptions if invoked without an explicit fake.
- **Network Interception:** Outbound connections via `socket.create_connection`, `urllib.request.urlopen`, and `urllib.request.urlretrieve` raise test-protection errors. Unmocked LLM generation paths (Anthropic, Gemini, Ollama) are blocked.
- **In-Process ASGI Preservation:** `TestClient(app)` calls FastAPI endpoints in memory without network sockets.
- **Retroactive Snapshot Monitoring:** Pre- and post-test snapshots of file paths and mtimes in the real repository's `data/` and `topics/` directories confirm that zero repository modifications occurred. Snapshots detect changes retroactively and do not proactively prevent damage in-flight.

---

### Known Limitations & Boundary Conditions

1. **Incomplete Raw-Socket Blocking (Do Not Claim All Network Access Blocked):**
   - Outbound network blocking intercepts `socket.create_connection`, `urllib.request.urlopen`, and `urllib.request.urlretrieve`.
   - Low-level raw socket operations (e.g. instantiating `s = socket.socket()` and invoking `s.connect(...)` directly) are not globally intercepted at the C-socket or kernel level. Code utilizing raw sockets directly or low-level asynchronous network loops would not be prevented from initiating connections unless specifically mocked.
2. **In-Process Scope, Not an OS Sandbox:**
   - Protections are implemented via Python monkeypatches, environment variable overrides, and mock objects. They do not constitute an operating system security sandbox (such as Linux namespaces, cgroups, chroot, or container isolation).
3. **Native & C Extension Boundary:**
   - Any external binary or unmanaged native C extension that bypasses the Python standard library layer would not be constrained by in-process Python hooks.
4. **Live External Services:**
   - Because standard library network calls and AI provider endpoints are blocked by default, tests requiring real remote AI hardware or live daemons must use explicit fakes or purpose-built mock handlers.

---

### 2. Frontend Tests
- **Status:** **PASS**
- **Command:** `npm run test` (executes `node --test 'src/**/*.test.ts'`)
- **Working Directory:** `<repo>/app/frontend`
- **Results:** 7 passed (128ms).

### 3. Frontend Lint
- **Status:** **PASS** (with warnings)
- **Command:** `npm run lint` (executes `oxlint`)
- **Working Directory:** `<repo>/app/frontend`
- **Results:** 0 errors, 25 warnings.

### 4. Frontend Production Build
- **Status:** **PASS**
- **Command:** `npm run build` (executes `tsc -b && vite build`)
- **Working Directory:** `<repo>/app/frontend`
- **Results:** 0 errors, built in 408ms.

---

*Note: These baseline checks verify toolchain execution and isolated units, but do not prove end-to-end runtime functionality.*
