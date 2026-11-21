# Milestone Status Report: Autonomous Maintenance & Verification

## 1. Saved Checkpoint & Synchronization State

- **Branch:** `security/audit-hardening` (PR #1 on Gitea, not merged into `main` yet).
- **Work on the branch (2026-11-21):** security hardening (host/origin checks, localhost-only default, WebSocket tickets, settings redaction, HTML sanitization, non-root Docker); safe chunked lesson rewriting in review and refine; private domains kept out of packs, Docker and portable builds, with a release guard (`scripts/check_release_packs.py`); current Claude model IDs and no sampling parameters; an indexed full-text search (SQLite FTS5); agent rules consolidated into `AGENTS.md`.
- **Verification:** `./scripts/verify_all.sh`. All 5 phases must pass before merging.
- **NEEDS DECISION:**
  - Chat-session files are still in git history, which is public on GitHub. Removing them requires rewriting history and force-pushing.
  - Whether to replace Electron (Tauri v2, or a browser/PWA launcher).
- **Next Milestone:** Real-use Manual Acceptance Testing (see `docs/manual-acceptance.md`).

---

## 2. Evidence-Gap Acceptance Audit Summary

A targeted acceptance audit was performed to close critical evidence gaps in previously unverified boundaries. 

### A. Mentor Behavior & Chat Context (Priority 1)
- **Verified Scenarios (`tests/test_chat_and_mentor.py`):**
  - **Disk Fallback:** Reads lesson markdown from disk if `lesson_content` is missing from the payload.
  - **Workspace Mode:** Resolves to neutral workspace instruction when no topic query is provided.
  - **Streaming Failure:** Yields an SSE error frame (`done: True`) without crashing the connection when the model fails mid-stream.
  - **Disk Persistence:** `save_chat_session` successfully persists `active_session.md` and `chat_history.json` into the topic workspace.
- **Repaired Defects:**
  - Prevented in-flight chat streams from leaking stale responses into unrelated topics after navigation by adding `chatRequestIdRef` cancellation (`198d6e8`).
  - Restored real disk persistence in testing by removing the redundant `save_chat_session` monkeypatch in `conftest.py` (`198d6e8`).

### B. Package Extraction Boundaries & Security (Priority 2)
- **Verified Scenarios (`tests/test_packages.py`):**
  - Missing file handling, corrupted archive rejection (`tarfile.ReadError`), and full lifecycle roundtrips.
  - Path traversal injection rejection (`ValueError`).
  - Graceful fallback on corrupted `manifest.json`.
- **Repaired Defects:**
  - Expanded package rejection to block absolute paths, traversal (`..`), symbolic links (`issym()`), hard links (`islnk()`), and device nodes (`isdev()`) before extraction. Validated both manifest-provided and filename-derived domain identifiers against a strict slug regex to prevent directory traversal in backups (`69a2f89`).

### C. Settings Persistence & Consumer Routing (Priority 3)
- **Verified Scenarios (`tests/test_settings_consumers.py`):**
  - `auth_password` enables backend authentication without environment variables.
  - `cluster_hosts` and `node_pins` correctly propagate to dynamic consumers.
- **Repaired Defects:**
  - `get_chat_provider` silently routed to Anthropic Claude when a local AI model was explicitly configured but the cluster was offline. Repaired to strictly respect user-configured primary/mentor models and raise an error rather than silently fallback to cloud (`5ce7d46`).

---

## 3. Unverified Behavior (Not Confirmed Defects) & Deferred Decisions

This verification suite asserts explicit paths, but does not provide complete coverage over all operational mechanics. These are **unverified behaviors** or deferred design decisions, not confirmed bugs:

1. **Package Content Injection (Decision Needed):**
   - The extraction process validates paths, but writes directly into `TOPICS_DIR` sequentially. If a package is rejected mid-extraction due to an unexpected file type, previously extracted files remain on disk. It is deferred whether to extract into a temporary directory and atomically rename upon complete success.
2. **Terminal PTY Concurrency & Race Conditions:**
   - Auth rejection is tested, but real PTY allocation, buffer clearing, process group signaling, and high-volume stream backpressure are entirely mocked out in the test environment.
3. **Frontend Mentor Streaming Reconnection:**
   - The test suite verifies backend SSE error frames, but frontend handling of abrupt TCP drops during streaming is not fully verified in automated headless browsers.

---

## 4. Verification Command and Results

```bash
./scripts/verify_all.sh
```

```text
==================================================
 🔍 RUNNING COMPLETE SYNAPSE VERIFICATION SUITE   
==================================================

[*] [1/5] Running frontend unit tests...
✔ 16 tests passed in 141.4ms (0 failed)

[*] [2/5] Running frontend linter...
oxlint: 0 errors, 25 non-blocking warnings

[*] [3/5] Building frontend production bundle...
tsc -b && vite build: 3646 modules transformed in 370ms (0 errors)

[*] [4/5] Running backend test suite...
pytest tests/: 108 passed in 58.73s (0 failed)

[*] [5/5] Running Chromium E2E browser tests...
pytest e2e/test_learner_journey.py: 8 passed in 40.57s (0 failed)

==================================================
 [✔] ALL 5 VERIFICATION PHASES PASSED             
==================================================
```