# Milestone Status Report: Keyboard Navigation & Unified Verification

## 1. Milestone Status: COMPLETED

All requirements for Milestone "Stabilize lesson keyboard navigation and create one repeatable command for checking the app" have been implemented and verified.

---

## 2. Changes Made

### Task 1 — Keyboard Navigation
- **`app/frontend/src/App.tsx`**:
  - Implemented the strict lesson navigation contract for `[` and `]`:
    - **Individual lesson navigation**: `[` moves to the previous lesson, `]` moves to the next.
    - **No wrapping**: At lesson 1, `[` does nothing; at the last lesson, `]` does nothing.
    - **"All lessons" handling**: In "all lessons" view (`activeLessonId === 'all'` or unset), `]` opens the first lesson; `[` does nothing.
    - **"Labs" isolation**: In the "labs" tab (`activeTab === 'labs'`), neither `[` nor `]` changes the view.
    - **Target guards**: Shortcuts are ignored if the active target is inside inputs, textareas, editable content, or terminal elements (`.terminal-drawer`, `.xterm`, `.terminal-body`).
    - **Modifier guards**: Shortcuts are ignored if any modifier (`Ctrl`, `Cmd`, `Alt`, or `Shift`) is held.
    - **Dependency update**: Added `activeTab` to the `useEffect` dependency array to eliminate stale closures.
    - **Persistence**: Keyboard navigation delegates directly to `handleSelectLesson()`, automatically persisting the active selection to `localStorage`.
- **`e2e/test_learner_journey.py`**:
  - Added `test_keyboard_navigation_contract` verifying all 9 contract clauses in live Chromium (all 8 browser tests pass).

### Task 2 — One Verification Command
- **`scripts/verify_all.sh`**:
  - Created executable repository-root verification script with `set -eo pipefail`.
  - Runs all 5 project verification phases sequentially:
    1. Frontend unit tests (`npm run test` in `app/frontend`)
    2. Frontend linter (`npm run lint` in `app/frontend`)
    3. Frontend production build (`npm run build` in `app/frontend`)
    4. Backend test suite (`.venv/bin/python -m pytest tests/`)
    5. Chromium E2E browser tests (`.venv/bin/python -m pytest e2e/test_learner_journey.py`)
  - Halts immediately with a non-zero exit status if any phase fails.
  - Requires no automatic package installations, preserves test isolation, and leaves normal app instances untouched.

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
pytest e2e/test_learner_journey.py: 8 passed in 10.17s

==================================================
 [✔] ALL 5 VERIFICATION PHASES PASSED             
==================================================
```

---

## 4. Remaining Limitations

- **Protected-Mode Cold Startup in E2E Harness**: The automated child test server (`e2e/server_launcher.py`) runs in single-user mode (`SYNAPSE_PASSWORD` unset). While runtime 401 handling, login modal triggering, storage preservation, and explicit logout are exercised via route interception and DOM clicks, launching the child server with `SYNAPSE_PASSWORD` set from initial process spawn is not exercised by this harness.
- **Terminal Isolation**: Keystrokes inside xterm bypass global window shortcuts by design, preventing conflict between shell hotkeys and lesson navigation.

---

## 5. Next Recommended Milestone

- **Release Packaging & Binary Verification**: Exercise `scripts/build_mac_desktop.sh` or portable packagers against the unified verification harness to validate distribution bundles before tagging releases.
