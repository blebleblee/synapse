# Synapse Workbench Actionable Audit Backlog

This backlog documents prioritized, actionable findings from the user-facing functionality audit across curriculum management, lesson rendering, generation, chat, settings, packages, terminal, and mastery tracking.

---

## Verified Working Behavior Summary

- **Lesson Reading & Markdown Rendering:** KaTeX mathematical typesetting, Mermaid diagram rendering, and synthesized terminal commands operate cleanly without errors.
- **Topic & Lesson Reload Persistence:** Active topic and specific lesson selection (including "all lessons" view) persist across browser reloads via `localStorage` with sequence race protection.
- **Keyboard Navigation Contract:** `[` and `]` navigate between lessons, ignore modifiers and inputs/terminal, do not wrap at bounds, and preserve persistence.
- **Socratic Mentor Chat:** Streams responses, contextualizes active lesson content and recent terminal buffer, and handles disconnects gracefully.
- **Settings & Cluster Discovery:** Probes configured Ollama nodes, lists available models, and saves preferences to SQLite and localStorage.
- **Single-User / Protected Mode Transitions:** Protected mode triggers login modal, clears sensitive reader content, and requires authentication before restoring topic views.

---

## Prioritized Actionable Findings

### FIND-01: Curriculum Generation Fails with HTTP 422 Due to Request Schema Mismatch
- **User-Visible Impact:** Clicking "Generate Masterclass Curriculum Units" or "Regenerate Content" fails immediately with HTTP 422 Unprocessable Entity. The learner cannot generate or regenerate curriculum content from the UI.
- **Evidence:**
  - `app/frontend/src/App.tsx:280`: Frontend sends `body: JSON.stringify({ query, force })`.
  - `app/backend/main.py:251-255`: `GenerateRequest` requires `domain: str`, `category: str`, `subtopic: str` as mandatory fields.
  - `app/backend/main.py:1057`: `generate_topic` endpoint accesses `req.query`, `req.provider`, `req.model`, which do not exist on `GenerateRequest`.
- **Status:** **COMPLETED** (Replaced `domain`, `category`, `subtopic` with `query`, `provider`, `model`, `force` in `GenerateRequest`, and added `/api/generate` regression test).

---

### FIND-02: Unconstrained `git add -A` and Remote Push on Topic Delete, Compile, and Summary
- **User-Visible Impact:** Deleting a topic, compiling a guide, or generating a summary triggers unconstrained Git commands that stage all files across `WORKSPACE_ROOT` (`git add -A`) and attempt to push to `origin main`. If a user or developer has untracked files, `.env` configs, or private notes in the workspace, they risk being committed and pushed unexpectedly. If offline, the UI hangs while waiting for Git network timeouts.
- **Evidence:**
  - `learning_engine/topic_manager.py:363-366`: `delete_subtopic` runs `git add -A`, `git commit`, and `git push origin main`.
  - `app/backend/main.py:1570-1574`: `compile_guide` runs `git add`, `git commit`, and `git push origin main`.
  - `learning_engine/summary.py:120-123`: `regenerate_summary` runs `git add`, `git commit`, and `git push origin main`.
- **Status:** **COMPLETED** (Removed automatic `git add/commit/push` side effects from `topic_manager.py`, `summary.py`, and `main.py`, and added `tests/test_git_isolation.py`).

---

### FIND-03: Single-Lesson Topics Cannot Be Marked Complete from Reader or Sidebar
- **User-Visible Impact:** When a topic contains only one lesson (`lessons.length === 1`), `LessonViewer.tsx` completely suppresses the bottom navigation bar containing the "Mark Complete" toggle button. Simultaneously, `TopicTree.tsx` does not render a completion checkbox for single-lesson units. The learner has no UI mechanism to track progress or mark single-lesson courses as completed.
- **Evidence:**
  - `app/frontend/src/components/LessonViewer.tsx:878`: `{topic.lessons && topic.lessons.length > 1 && activeLessonId !== 'all' ? (` restricts bottom bar to multi-lesson topics.
  - `app/frontend/src/components/TopicTree.tsx:507`: `const hasMultiLessons = Boolean(singleUnit.lessons && singleUnit.lessons.length > 1);` hides lesson checkboxes for single-lesson units.
- **Status:** **COMPLETED** (Updated conditionals to `length >= 1` in `LessonViewer.tsx` and `TopicTree.tsx`).

---

### FIND-04: Failed Translations Are Permanently Cached as Valid Content
- **User-Visible Impact:** If Ollama or the AI provider fails, times out, or is offline during translation, `translate_chunk()` catches the exception and returns the source English text as a fallback. The endpoint then writes this untranslated English text to the disk translation cache (`cache_file.write_text(final_translation)`). Future requests return this cached file, permanently locking the user into English even after the AI service is restored.
- **Evidence:**
  - `app/backend/main.py:791-794`: Exception in translation returns original English chunk text.
  - `app/backend/main.py:803`: `cache_file.write_text(final_translation + "\n", encoding="utf-8")` unconditionally caches the result.
- **Status:** **COMPLETED** (Prevented failed chunks, empty translations, and source-identical fallbacks from writing to disk cache in `app/backend/main.py`. Added regression tests in `tests/test_api.py`).

---

### FIND-05: Search Result Click Navigates to Lesson 1 Instead of the Matched Lesson
- **User-Visible Impact:** Search results display specific matching section titles and content snippets from deeper lessons (e.g. Lesson 3), but clicking the search result card only navigates to the parent course path (`r.path`), always opening Lesson 1. The learner must manually hunt for the lesson containing the snippet.
- **Evidence:**
  - `app/frontend/src/components/SearchModal.tsx:111`: `onSelectTopic(r.path)` passes only the course path, omitting the lesson identifier.
  - `learning_engine/search.py:73`: `search_curriculum` returns `"file": md_path.name` (e.g. `lesson_02_indexing.md`), which contains the exact lesson identifier.
- **Status:** **COMPLETED** (Extracted `lessonId` from `r.file` in `SearchModal.tsx` and updated `onSelectTopic`).

---

### FIND-06: Topic Deletion Does Not Clear Active Selection in Memory or LocalStorage
- **User-Visible Impact:** Deleting an active topic from the sidebar deletes the files on disk, but `handleDeleteTopic` in `App.tsx` does not clear `synapse_active_selection` from `localStorage` or reset `activeLessonId`. On the next browser reload, `initApp()` attempts to restore the deleted topic, causing an unnecessary 404 request. If backend deletion fails, the UI provides no error feedback.
- **Evidence:**
  - `app/frontend/src/App.tsx:321-325`: `handleDeleteTopic` clears `selectedPath` and `topicDetails` but omits `clearStoredSelection()`, `setActiveLessonId(null)`, and error notification on `!res.ok`.
- **Status:** **COMPLETED** (Updated `handleDeleteTopic` to invoke `clearStoredSelection()`, `setActiveLessonId(null)`, and `window.alert` on backend failure).

---

### FIND-07: Manual Mastery Level Update Does Not Refresh Sidebar Progress
- **User-Visible Impact:** When a learner updates the mastery level dropdown in the reader header (e.g., from Novice to Proficient), the course badge in the reader updates, but `fetchTree()` is not invoked. As a result, the sidebar tree's mastery color indicators remain stale until page reload.
- **Evidence:**
  - `app/frontend/src/App.tsx:708-713`: `handleUpdateMastery` updates `topicDetails.mastery` in state but omits `fetchTree()`.
  - Contrast with `handleToggleLessonCompletion` at `App.tsx:378`, which correctly calls `await fetchTree()`.
- **Status:** **COMPLETED** (Added `await fetchTree()` and `await fetchStatus()` inside `handleUpdateMastery`).

---

### FIND-08: Quiz and Summary Generation Ignore Configured Primary/Mentor AI Model
- **User-Visible Impact:** When a user configures a specific model (e.g. `qwen2.5-coder:32b`) or cluster host in Settings, clicking "Generate Knowledge Quiz" or "Regenerate Summary" sends only `{ query }`, ignoring the configured preferred model and host. The backend defaults to whatever cloud or local provider it discovers first.
- **Evidence:**
  - `app/frontend/src/App.tsx:675`: `body: JSON.stringify({ query: selectedPath })`.
  - `app/frontend/src/App.tsx:738`: `body: JSON.stringify({ query: selectedPath })`.
  - `app/backend/main.py:1411-1420`: `QuizRequest` accepts `provider` and `model`, but receives none from the frontend.
- **Status:** Confirmed by code.
- **Proposed Acceptance Criteria:** `handleRefreshQuiz` and `handleRegenerateSummary` forward `model` and `provider` parameters matching the user's active preferences.
- **Small Proposed Repair Task:** Include `model: settings.mentorModel || settings.primaryModel` and `host: settings.ollamaHost` in the POST bodies for `/api/quiz` and `/api/summary/regenerate`.

---

### FIND-09: Terminal WebSocket Reconnect Loop Floods Endpoint on Auth Rejection
- **User-Visible Impact:** When the backend rejects a WebSocket connection due to missing or invalid authentication (`code=1008`), `TerminalDrawer.tsx` schedules an automatic reconnect every 2.5 seconds indefinitely, flooding the server log with connection rejections.
- **Evidence:**
  - `app/frontend/src/components/TerminalDrawer.tsx:112-118`: `ws.onclose` unconditionally schedules reconnection without inspecting close codes.
  - `app/backend/main.py:1591`: Backend sends `await websocket.close(code=1008, reason="Authentication required")`.
- **Status:** Confirmed by code.
- **Proposed Acceptance Criteria:** `ws.onclose` does not schedule an automatic reconnection if the close code indicates authentication failure (`event.code === 1008`) or deliberate closure (`event.code === 1000`).
- **Small Proposed Repair Task:** In `TerminalDrawer.tsx`, check `if (event.code !== 1008 && event.code !== 1000)` before scheduling `reconnectTimerRef.current`.
