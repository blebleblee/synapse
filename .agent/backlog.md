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
- **Status:** **COMPLETED** (Extracted `lessonId` from `r.file` in `SearchModal.tsx`, wired `handleSelectSubtopic` in `App.tsx`, and verified with `test_search_navigation_to_matched_lesson` in `e2e/test_learner_journey.py`).

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
- **Status:** **COMPLETED** (Forwarded configured `model` and `host` from `App.tsx` to `/api/quiz` and `/api/summary/regenerate`, added `host` support to `get_provider` and `regenerate_summary` in `learning_engine/models.py` and `summary.py`. Verified with tests in `tests/test_api.py`).

---

### FIND-09: Terminal WebSocket Reconnect Loop Floods Endpoint on Auth Rejection
- **User-Visible Impact:** When the backend rejects a WebSocket connection due to missing or invalid authentication (`code=1008`), `TerminalDrawer.tsx` schedules an automatic reconnect every 2.5 seconds indefinitely, flooding the server log with connection rejections.
- **Evidence:**
  - `app/frontend/src/components/TerminalDrawer.tsx:112-118`: `ws.onclose` unconditionally schedules reconnection without inspecting close codes.
  - `app/backend/main.py:1591`: Backend sends `await websocket.close(code=1008, reason="Authentication required")`.
- **Status:** **COMPLETED** (Halted automatic terminal WebSocket reconnection loops on code 1008 Policy Violation / Unauthorized and code 1000 Normal Closure in `TerminalDrawer.tsx` and `app/frontend/src/utils/terminalHelpers.ts`. Reconnects upon `synapse:authenticated` event. Added unit tests in `terminalReconnect.test.ts`).


---

### FIND-10: Corrupted Package Manifest Crashes Installer Instead of Using Filename Fallback
- **User-Visible Impact:** When importing or installing a `.synpack` archive that contains a malformed, truncated, or unparseable `manifest.json`, `install_topic_pack` crashed with an unhandled `json.JSONDecodeError` rather than falling back to the package archive name as intended.
- **Evidence:**
  - `learning_engine/packages.py:121`: `json.loads(manifest_member.read().decode("utf-8"))` caught only `KeyError`, letting `JSONDecodeError` crash execution.
  - `learning_engine/packages.py:124`: `domain = manifest.get("domain") or pack_path.stem.replace(".synpack", "")` fallback was unreachable on malformed JSON.
- **Status:** **COMPLETED** (Caught `(KeyError, json.JSONDecodeError, UnicodeDecodeError)` in `install_topic_pack`, allowing clean fallback to `pack_path.stem`. Verified with `test_install_pack_corrupted_manifest_fallback` in `tests/test_packages.py`).

---

### FIND-11: In-Flight Chat Streams Leak Stale Responses Across Topic Navigation
- **User-Visible Impact:** If the learner asks the mentor a question and immediately navigates to a new topic while the response is streaming, the chunks from the first topic continue to append to the unified chat history of the newly selected topic.
- **Status:** **COMPLETED** (Added `chatRequestIdRef` to `App.tsx` to invalidate chat streams on topic change. Added `test_chat_and_mentor.py` disk persistence tests).

---

### FIND-12: Package Installer Vulnerable to Unsafe Archive Links and Domain Traversal
- **User-Visible Impact:** The package installer did not validate `domain` identifiers against safe slugs, nor did it reject symlinks (`member.issym()`), hardlinks (`member.islnk()`), or device nodes. This allowed malicious `.synpack` archives to potentially escape `TOPICS_DIR`.
- **Status:** **COMPLETED** (Enforced `re.match(r"^[a-zA-Z0-9_-]+$")` on domain identifiers and strictly rejected unsafe archive links before extraction in `packages.py`. Added security acceptance tests in `test_packages.py`).

---

### FIND-13: Mentor Routing Silently Falls Back to Cloud on Local Cluster Outage
- **User-Visible Impact:** If a user explicitly configured a Local AI model for the Socratic Mentor (e.g. `custom-chat-model:14b`), but the Ollama cluster was offline, the router silently fell back to Anthropic Claude (if keys were present in the environment), ignoring the user`s preference and potentially transmitting local curriculum context to cloud servers.
- **Status:** **COMPLETED** (Refactored `get_chat_provider()` in `models.py` to respect explicit user model selections and raise connection errors rather than silently fallback to cloud. Verified with mock cluster tests in `test_settings_consumers.py`).

---

### FIND-14: Bulk Generator Auto-Commits and Pushes
- **Impact:** `scripts/generate_all.py` committed every generated topic, including topics in non-core domains, and ran `git push origin main`. The retry loop called `time.sleep` without importing `time`, and importing the script redirected stdout.
- **Status:** **COMPLETED** (2026-11-22). No git writes by default. `--commit` makes local commits for core domains only and never pushes. Test: `tests/test_generate_all_git.py`.

---

### FIND-15: Packs Could Write Outside Their Declared Domain
- **Impact:** `install_topic_pack` checked paths for traversal but not which domain they belong to. A pack declaring `arts` could add or overwrite files in any other domain or in the `topics/` root, and only the declared domain was backed up first.
- **Status:** **COMPLETED** (2026-11-22, `4e598ee`). Every member is checked before backup and extraction. Tests: `tests/test_packages.py`.

---

### FIND-16: Mentor Times Out While a Translation Runs
- **User-Visible Impact:** "Unable to connect" from the mentor during a translation, although it showed online; local Ollama serves one request at a time.
- **Status:** **COMPLETED** (`1f2ca86`): mentor requests pause the translation, which retries its section afterwards. Test: `tests/test_translation_jobs.py`.

---

### FIND-17: Tests Depended on the Developer's Shell and Leaked Threads
- **User-Visible Impact:** none for users; CI failed where local runs passed. A "provider fails" test only passed with a real API key (`ANTHROPIC_API_KEY_2`) in the shell; start-up warm-up threads wrote into the next test's database.
- **Status:** **COMPLETED** (`499138c`): conftest clears provider keys and hosts; shutdown joins the warm-up threads; `/api/translate` returns 503 without a provider.

---

### FIND-18: Settings Showed a Running Local Ollama as "Offline"
- **User-Visible Impact:** Ollama nodes were probed from the browser, which Ollama's CORS rules reject, and statuses were looked up under a different host spelling.
- **Status:** **COMPLETED** (`222b287`): `/api/settings/cluster-status?hosts=` probes from the backend, in parallel, under the names as typed.

---

### FIND-19: `bump_version.py` Silently Skipped the Settings Version Label
- **Status:** **COMPLETED** (`8670418`): matches `Synapse vX.Y.Z`, fails when absent, and updates the npm lock files.

---

### FIND-20: Websites Could Trigger State Changes on a Password-less Instance (CSRF)
- **Impact:** a no-cors POST from any site reached e.g. `/api/system/shutdown` (valid localhost Host, loopback IP). CORS does not stop simple requests.
- **Status:** **COMPLETED** (`997c975`): middleware rejects non-GET/HEAD/OPTIONS with a foreign `Origin`. Tests: `tests/test_security_hardening.py`.

### FIND-21: Mentor Status Named a Model That Was Not Answering
- **Impact:** with the configured model missing, the chat fell back to another local model while the UI kept showing the configured one.
- **Status:** **COMPLETED** (`8dbc84d`): connectivity check returns the resolved model; chat sends `X-Synapse-Model`; UI marks fallback. Tests: `tests/test_chat_and_mentor.py`.

### FIND-22: Settings Maintenance Buttons Did the Wrong Thing
- **Impact:** "Clear Transient Cache" deleted every saved chat session and no cache; "Vacuum SQLite Database" was a no-op that reported success; Shut Down reported success on 403.
- **Status:** **COMPLETED** (`932a30a`). Tests: `tests/test_cleanup.py`.

### FIND-23: Sidebar Collapsed After Reload
- **Impact:** the restored lesson was hidden in a collapsed tree.
- **Status:** **COMPLETED** (`a0b89d2`). E2E: `test_sidebar_reveals_restored_topic_after_reload`.

---

## Needs Decision

- **Chat "Clear conversation" deletes saved sessions of every topic** (`TutorChat.tsx` sends `sessions: true`, which removes all `sessions/` dirs). The chat history is shared across topics in the UI, so this may be intended. Options: keep; or clear only the active topic's session.
- **`/api/tree` returns absolute `full_path`s** (server home directory) to the browser. Harmless on localhost; with a password and remote access it reveals the server layout. Check whether the frontend needs it before removing.

### FIND-24: Locked First Run Showed Wizard and Login Together, Polled 401s
- **Status:** **COMPLETED** (`35b0705`). E2E: `test_locked_first_run_shows_only_login_and_stays_quiet`.

### FIND-25: Flashcards Silent for ~46 s, Failures Blamed on Lessons; Start-up Before Server
- **Status:** **COMPLETED** (`59c4e86`). Tests: `tests/test_api.py` deck tests; E2E `test_startup_waits_for_backend`.

### FIND-26: No Escape-to-Close; Dead Learning-Pathway Link
- **Status:** **COMPLETED** (`5576c11`). Tests: `tests/test_learning_pathways.py`; E2E `test_escape_closes_dialogs`.

### FIND-27: Terminal Closed the PTY Slave fd Twice
- **Impact:** the second close hit whatever socket had reused the fd number, breaking the reconnecting terminal or an HTTP request.
- **Status:** **COMPLETED** (`771c769`). Test: `test_terminal_closes_each_pty_fd_exactly_once`.

### FIND-28: Course-Path Links Repeated the Course Name
- **Status:** **COMPLETED** (`b14085c`). Test: `test_node_labels_do_not_repeat_the_course_name`.

### FIND-29: Anki Export Regenerated Decks; Placeholder Decks Cached; Bad Anki Header
- **Status:** **COMPLETED** (`7ff4d93`). Tests in `tests/test_search.py`. The only shipped deck was a leaked test mock and was removed.

### FIND-30: CLI Tracebacks, Exit Codes, Endless Review
- **Status:** **COMPLETED** (`149820c`). Tests: `tests/test_cli.py`.

### FIND-31: Math Rendered in Two Domains Only; "<" Escaped Inside Code
- **Status:** **COMPLETED** (`01855bc`). Tests: `app/frontend/src/utils/mathSpans.test.ts`.

### FIND-32: Duplicate Course Titles in the Sidebar
- **Status:** **COMPLETED** (`7f65a0c`). Test: `tests/test_syllabus_titles.py`.

### FIND-33: Mermaid Repair Corrupted Quoted Labels
- **Status:** **COMPLETED** (`496bc60`, `103c111`, `417c42a`). Tests: `app/frontend/src/utils/mermaidRepair.test.ts`.

### FIND-34: Mentor Model Shown Twice (User Request)
- **Status:** **COMPLETED** (`a1cbac2`).

### FIND-35: 47 Broken Diagrams and a Runaway Code Block in Public Lessons
- **Status:** **COMPLETED** (`1f8dad2`). `scripts/validate_render.mjs` reports 0 broken Mermaid diagrams in tracked public lessons.

### FIND-36: Listen Gave No Feedback and Could Play a Lesson Already Left
- **Status:** **COMPLETED** (`fd5ea6d`). Test: `app/frontend/src/utils/speech.test.ts`.

### FIND-37: Mentor Showed the Folder Name in Lowercase
- **Status:** **COMPLETED** (`98d1cfd`).

### FIND-38: "Sandbox" Terminal Fell Back to a Host Shell; Run Executed Snippets on the Host
- **Status:** **COMPLETED** (`540c518`). Test: `tests/test_security_hardening.py::test_unreachable_sandbox_does_not_fall_back_to_a_host_shell`.

### FIND-39: Settings Hard to Read; Main Window Crowded (User Request)
- **Status:** **COMPLETED** (`ce3c065`). The `reviewerModel` setting is no longer shown (unused by the app); the field stays in `settingsDefaults.ts` for stored settings.

### FIND-40: Mentor Failed on Long Lessons and Saw Only Their Start
- **Status:** **COMPLETED** (`1dec52e`). Tests: `tests/test_lesson_context.py`, `tests/test_generation_output.py`.

## Next Candidates (not yet verified)

- **Curriculum hallucinations (owner question, proposal):** (1) `synapse review` with a reviewer from a different model family than the generator; (2) run lesson/lab code blocks in the sandbox in CI and flag failures; (3) extract checkable claims (versions, defaults, flags, API names) and verify against docs or installed tools; (4) a "Report a mistake" button in the reader feeding a review queue. (1) and (2) are cheapest. NEEDS DECISION on which to build.
- **Run buttons:** shown on every bash block, including illustrations like `cmd > file`. Consider showing Run only in labs or on blocks marked runnable (product decision).
- **Mentor:** terminal buffer and last command are injected twice (system instruction and prompt) under a "you MUST inspect" directive, even for unrelated questions; consider once, and only when relevant. Lesson-generation cleanup (`validate_generation_output`) still runs on chat replies; a chat-specific path would be cleaner.
- **Listen privacy:** narration sends the lesson text to Microsoft's Edge TTS service (`edge_tts`); say so in the UI or docs.

- **Curriculum:** ~100 KaTeX errors now visible to learners (95 formal/natural sciences, 5 business/economics). Run `node scripts/validate_render.mjs topics/<domain>` per public domain and filter to `git ls-files topics`.

- **UI not yet exercised in this pass:** Listen (TTS), lesson translation (EN ▾), Add Topic, rename/delete unit, Curriculum Store. (Quiz, Labs, Export checked: quiz generation works, ~2 min with a local model.)
- **CLI:** checked in batch 2 (FIND-30). Not yet exercised: `add`, `generate`, `chat`, `pack install/uninstall` (they write or need a model).
- No course ships `flashcards.csv` (the one that did was a test artifact); every deck is generated on first open (tens of seconds). Consider shipping decks or pre-generating in the curriculum pipeline (product decision).

---

## Deferred Decisions & Unverified Behavior

- **Package Content Injection:** **COMPLETED** (`2779454`, `4e598ee`): extraction stages into `.install-{stamp}-{pid}`, validates all members, merges safely, and atomically swaps via `os.replace` with automatic rollback.
- **Terminal PTY Concurrency:** Real PTY process allocation and signaling remain mocked in the test environment to prevent host shell execution.
- **Complete Pack Backup:** **COMPLETED** (`2779454`): every domain a pack writes into is backed up first.
