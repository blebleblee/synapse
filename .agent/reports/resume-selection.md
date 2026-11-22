# Specification: Restore Selected Topic and Lesson After Browser Reload

## 1. Problem and Root Cause

### Current Behavior & Root Cause
- When a learner selects a topic and lesson in the sidebar or reader, the selection previously existed only in transient React component state (`selectedPath`, `activeLessonId`, and `topicDetails` in `App.tsx`).
- Upon browser reload, tab close, or desktop app restart, component state reset to `null`.
- On component mount (`initApp`), `App.tsx` verified authentication and fetched the topic tree, but did not check for or restore any previously active topic or lesson.
- The reader displayed the blank placeholder state (`.viewer-empty`: *"Select a topic from the left sidebar to begin studying..."*), requiring manual re-navigation from scratch.

### Relevant File Paths
- **`app/frontend/src/App.tsx`**:
  - `loadTopic(query, preserveTab, lessonId, isRestore)` — fetches `/api/topic`, saves valid selections, clears storage on definitive 404, and resolves request sequence races.
  - `initApp()` — authenticates, fetches tree, and triggers restoration if no user interaction has occurred.
  - `handleUnauthorized()` — cancels in-flight requests and clears protected UI state, while preserving the user's saved selection in `localStorage`.
  - `handleLogout()` — explicitly clears saved selection and resets all active state.
  - `handleLoginSuccess()` — restores saved selection upon successful authentication.
- **`app/frontend/src/utils/selectionStorage.ts`**:
  - Safe parsing, schema validation, reading, saving, and clearing of `'synapse_active_selection'` in `localStorage`.
- **`app/frontend/src/utils/selectionStorage.test.ts`**:
  - Unit tests covering schema validation, malformed JSON resilience, round-trip storage, and invalid type rejection.
- **`e2e/test_learner_journey.py`**:
  - Automated browser integration test suite verifying automatic reload-and-resume, stale ID fallbacks, 404 error handling, race conditions, and unauthorized (401) handling.

---

## 2. Implemented Architecture & Error Handling

1. **Selection Persistence:** Whenever a topic and lesson are successfully loaded in the reader (via topic selection, lesson navigation, or keyboard shortcuts), their identifiers are persisted under the key `'synapse_active_selection'`:
   ```json
   {
     "path": "computing/data/postgresql",
     "lessonId": "lesson_01_foundations"
   }
   ```
2. **"All Lessons" Preservation:** When the learner selects the complete guide view (`lessonId === 'all'`), `"lessonId": "all"` is saved and restored upon reload.
3. **Restoration Lifecycle:** In `App.tsx`'s `initApp()`:
   - Performs `checkAuth()`. If unauthenticated or authentication is required, restoration is skipped.
   - Once authenticated and `fetchTree()` completes, reads `'synapse_active_selection'` from storage.
   - If present and the user has not interacted with the UI, invokes `loadTopic(saved.path, false, saved.lessonId, true)`.
4. **401 Unauthorized vs Explicit Logout Handling:**
   - In `handleUnauthorized()`: An unexpected 401 response invalidates in-flight requests (`loadRequestIdRef.current += 1`), resets active state (`selectedPath = null`, `topicDetails = null`), and requires login (`authRequired = true`, `isAuthenticated = false`). It does **not** clear `'synapse_active_selection'`, preserving the learner's place for when they log back in.
   - In `handleLogout()`: An explicit user logout clears `'synapse_active_selection'`, removes the auth token, and wipes all active selection state.
   - In `handleLoginSuccess()`: When the user successfully unlocks the app, `handleLoginSuccess()` checks for the saved selection and automatically restores the active topic and lesson.
5. **Definitive 404 vs Network Errors:**
   - When `/api/topic` returns 404 (topic deleted or uninstalled), `clearStoredSelection()` removes the stale entry and displays `.viewer-empty`.
   - Network errors, 500-level server errors, and 401 unauthorized responses do **not** clear stored selection.
6. **Stale Lesson Fallback:** If the topic exists but the saved lesson was deleted, the backend falls back to the topic's first lesson (`data.active_lesson_id`). The frontend displays this lesson and updates `localStorage` with the actual valid lesson ID.
7. **Race Handling:**
   - Every `loadTopic` call increments `loadRequestIdRef.current`. Responses whose request ID does not match the latest request ID are immediately discarded.
   - Explicit user selection sets `userInteractedRef.current = true`, immediately superseding any in-flight restore.
   - Protected reader content is guarded with `topic={authRequired && !isAuthenticated ? null : topicDetails}`, preventing content leakage while the login screen is displayed.

---

## 3. Handling for Stale Topic and Stale Lesson Identifiers

| Scenario | Condition | System Action | Resulting UI State |
| :--- | :--- | :--- | :--- |
| **Valid Topic & Lesson** | Topic exists on disk, lesson ID exists in topic | Fetch 200; set `topicDetails` and `activeLessonId` | Reader displays saved lesson; sidebar highlights unit |
| **"All Lessons" View** | Topic exists, `lessonId === "all"` | Fetch 200; set `activeLessonId = 'all'` | Reader displays complete concatenated guide |
| **Stale Lesson ID** | Topic exists, but saved lesson was deleted/renamed | Backend falls back to first lesson (`lessons_list[0]`); returns 200 | Reader opens topic's first lesson; updates stored `lessonId` in `localStorage` |
| **Stale Topic Path** | Topic was deleted, uninstalled, or corrupted | Backend `/api/topic` returns 404; `loadTopic` catches failure | Clears `localStorage['synapse_active_selection']`; shows normal `.viewer-empty` |
| **Unauthorized (401)** | Token expired or 401 response | `handleUnauthorized` clears UI, invalidates requests, preserves storage | Shows `LoginModal`; saved selection restored upon `handleLoginSuccess` |
| **Explicit Logout** | User clicks Lock / Logout button | `handleLogout` clears `localStorage`, invalidates requests, resets state | Shows `LoginModal`; storage is empty |
| **User Interrupted** | User clicked sidebar item before restore finished | Request ID check and `userInteractedRef` discard restore | User's explicit click takes precedence; saved state overwritten with new selection |

---

## 4. Verification Commands and Results

1. **Frontend Unit Tests:**
   ```bash
   npm run test  # working directory: app/frontend
   # Output: 13 passed in 134ms (including selectionStorage parsing, validation, and storage round-trip)
   ```

2. **Frontend Linter:**
   ```bash
   npm run lint  # working directory: app/frontend
   # Output: 0 errors, 25 non-blocking warnings
   ```

3. **Frontend Production Build:**
   ```bash
   npm run build  # working directory: app/frontend
   # Output: Built client environment in 381ms (3,645 modules transformed, 0 type errors)
   ```

4. **End-to-End Browser Journey & Resume Tests (Playwright Chromium):**
   ```bash
   .venv/bin/python -m pytest e2e/test_learner_journey.py
   # Output: 7 passed in 7.45s
   ```
   - `test_learner_core_journey_with_automatic_resume`: Verified that on browser reload, topic, lesson, and completed/incomplete states are automatically restored without manual reselection.
   - `test_resume_different_lesson_and_all_lessons_view`: Verified that selecting Lesson 2 and selecting Complete Guide ("all") are restored on reload.
   - `test_resume_malformed_and_missing_topic_error_handling`: Verified that malformed JSON and 404 missing topics do not break startup and clear stale storage.
   - `test_resume_stale_lesson_id_fallback`: Verified that missing lesson IDs fall back to the first lesson and replace the stale ID in storage.
   - `test_late_restore_superseded_by_user_selection`: Verified that delayed restore responses are discarded when a user makes a newer selection.
   - `test_unauthorized_response_clears_content_but_preserves_saved_selection`: Verified that receiving a controlled 401 response clears protected reader content, requires login, and preserves the saved selection in `localStorage`.
   - `test_explicit_logout_clears_saved_selection`: Verified that explicit user logout clears the saved selection from `localStorage` and requires login.

5. **Existing Backend Suite:**
   ```bash
   .venv/bin/python -m pytest tests/
   # Output: 79 passed, 0 failed in 31.67s
   ```

---

## 5. Unverified Test Scenarios

- **Full Protected-Mode Startup Awaiting Password Submission:**
  - In `App.tsx`, `initApp()` guards restoration with `checkAuth()`, and `handleLoginSuccess()` restores saved selections after password verification.
  - In our automated E2E test harness (`e2e/server_launcher.py`), the test server executes in single-user loopback mode (`SYNAPSE_PASSWORD` unset). While 401 handling, login modal triggering, storage preservation, and explicit logout were exercised via live browser routing and UI clicks, launching the child server with `SYNAPSE_PASSWORD` set from cold startup was not run in this harness and remains an unverified automated test scenario.
