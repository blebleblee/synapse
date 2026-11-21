# Milestone Status Report: Keyboard Navigation, Unified Verification & Functionality Audit

## 1. Saved Checkpoint

- **Commit Hash:** `323a087` (`fix: stabilize lesson shortcuts and add unified verification`)
- **Self-Review:** Verified strict adherence to the keyboard navigation contract (`[` and `]` navigation, no boundary wrapping, "all lessons" default, "labs" isolation, modifier/target guards, and selection persistence).
- **Verification Script:** Verified `scripts/verify_all.sh` runs reliably from root, halts on failure via `set -eo pipefail`, and passes all 5 verification phases.

---

## 2. Audit Summary

A systematic audit of user-facing workbench functionality was conducted across 8 core areas:
1. **Curriculum Selection & Navigation:** Selection and reload-and-resume work reliably. However, search result cards navigate only to Lesson 1 instead of the matched lesson (`FIND-05`), and deleting an active topic leaves stale state in memory/localStorage (`FIND-06`).
2. **Lesson Rendering & Reader Controls:** KaTeX math, Mermaid diagrams, and code fences render cleanly. However, topics with only 1 lesson suppress the entire bottom navigation bar, preventing learners from marking single-lesson courses as complete (`FIND-03`).
3. **Curriculum Generation:** **Critically broken.** Clicking "Generate Masterclass Curriculum Units" or "Regenerate Content" fails with HTTP 422 Unprocessable Entity due to a mismatch between frontend JSON (`query`, `force`) and backend `GenerateRequest` (`domain`, `category`, `subtopic`) (`FIND-01`).
4. **Mentor Chat:** Fully functional; streams responses with active lesson and terminal buffer context.
5. **Settings & Provider Configuration:** Hardware discovery, Ollama node probing, and SQLite settings persistence operate reliably. However, quiz and summary generation ignore configured preferred models (`FIND-08`).
6. **Package Import/Export:** Package listing, `.synpack` export, and installation operate as expected.
7. **Terminal Controls:** WebSocket PTY bridge works for interactive shell commands. However, WebSocket reconnection loops endlessly on HTTP 1008 auth rejection (`FIND-09`).
8. **Progress / Mastery Controls:** Lesson completion toggling and tree progress badges operate reliably. However, manual mastery level updates in the reader header omit `fetchTree()`, leaving sidebar progress badges stale until reload (`FIND-07`).
9. **Data Integrity & Operations:** Topic deletion, guide compilation, and summary generation invoke unconstrained `git add -A` across `WORKSPACE_ROOT` and attempt `git push origin main`, risking accidental commit of private or uncommitted workspace files (`FIND-02`).
10. **Translation Caching:** Failed translations cache fallback English text permanently, locking users out of future translations (`FIND-04`).

Detailed findings, evidence, status, and acceptance criteria are documented in `docs/backlog.md`.

---

## 3. Exact Verification Command and Results

### Command
```bash
./scripts/verify_all.sh
```

### Results
```text
==================================================
 🔍 RUNNING COMPLETE SYNAPSE VERIFICATION SUITE   
==================================================

[*] [1/5] Running frontend unit tests...
✔ 13 tests passed in 137.9ms (0 failed)

[*] [2/5] Running frontend linter...
oxlint: 0 errors, 25 non-blocking warnings

[*] [3/5] Building frontend production bundle...
tsc -b && vite build: 3645 modules transformed in 369ms (0 errors)

[*] [4/5] Running backend test suite...
pytest tests/: 79 passed in 32.18s

[*] [5/5] Running Chromium E2E browser tests...
pytest e2e/test_learner_journey.py: 8 passed in 11.19s

==================================================
 [✔] ALL 5 VERIFICATION PHASES PASSED             
==================================================
```

---

## 4. Single Highest-Priority Recommended Next Milestone

**Milestone: Restore Curriculum Generation & Sanitize Git Workspace Side-Effects (FIND-01 & FIND-02)**

- **Objective:** Fix the HTTP 422 schema mismatch in `/api/generate` so learners can generate and regenerate curriculum units from the UI, and eliminate unconstrained `git add -A` and automatic `git push origin main` from topic deletion, summary regeneration, and guide compilation.
- **Scope:**
  1. Align `GenerateRequest` in `app/backend/main.py` with the frontend `{ query, force, provider?, model? }` payload and resolve path components dynamically.
  2. Add unit and integration tests for `/api/generate` with mocked provider.
  3. Replace `git add -A` with targeted file staging (or disable automatic git mutations) in `learning_engine/topic_manager.py`, `learning_engine/summary.py`, and `app/backend/main.py`.
