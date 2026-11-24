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

## Resolved Decisions (history)


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

### FIND-41: Mentor Prompts and Arts Generator Assumed Engineers / Musicians
- **Status:** **COMPLETED** (batch 4). Suggested prompts depend on the domain (`utils/mentorSuggestions.ts`, tested); `topics/arts/GEMINI.md` scopes the music persona to music courses. Follow-up resolved by FIND-60 (2026-11-23 check: the only remaining "musician" hits are in music_production courses, where they are correct).

### FIND-42: ~100 Formulas Showed as Red Source Text
- **Status:** **COMPLETED** (`301045e`). Test: `app/frontend/src/utils/katexMacros.test.ts`.

### FIND-43: Add Topic Dialog Always Failed
- **Status:** **COMPLETED** (`ae8b7f5`). Test: `toSlug` in `app/frontend/src/utils/text.test.ts`.

### FIND-44: CI Build Flaked on the WebAssembly Bundler
- **Status:** **COMPLETED** (`b7ae6db`).

### FIND-45: Mentor Got the Terminal Twice Under a "MUST Inspect" Rule
- **Status:** **COMPLETED** (`8933d73`). Test: `test_api_chat_sends_terminal_output_to_the_model_once`.

### FIND-46: Course List Order Jumped; Import Not Keyboard-Reachable
- **Status:** **COMPLETED** (`1092748`).

### FIND-47: Pack Uninstall of "" or "." Deleted the Whole Curriculum
- **Status:** **COMPLETED** (`4fe4d9a`). Tests in `tests/test_packages.py`, `tests/test_cli.py`.

### FIND-48: Generation Failed on Ollama/Gemini; CLI chat Crashed; Failures Exited 0
- **Status:** **COMPLETED** (`a6cfa24`). Tests: `tests/test_provider_contract.py`, `tests/test_cli.py`.

### FIND-49: Visual Arts Courses Generated From the Music Blueprint
- **Status:** **GENERATOR FIXED** (`d32f356`). **Content resolved (owner decision 2026-11-23):** 15 labs were music-production exercises; moved to the private addons repo and removed from the public courses. 3 labs (visual_arts/sketching, visual_media/graphic_design, visual_media/photography) are real visual labs and stay (heading fixed). Musician analogies fixed by FIND-60. Open: new labs for the 15 courses whose music labs moved to addons.
- **Related (not fixed):** in the TOPIC_OUTLINE path the capstone lab for every non-maths course is IT-flavoured (CLI, YAML, failure injection). No public course uses TOPIC_OUTLINE.md.

### FIND-50: Mentor Replies Rendered Lists and Code Without Styles
- **Status:** **COMPLETED** (`148d15b`).

### FIND-51: Mastered Field Guide (From Chat Sessions) Could Be Packed
- **Status:** **COMPLETED** (`6a896c3`). Test: `tests/test_pack_privacy.py::test_mastered_field_guide_is_never_packed`.

### FIND-52: Regenerate Deleted the Course (and Chat Sessions); Stop Did Not Stop
- **Status:** **COMPLETED** (`d4fa183`). Tests: `tests/test_regeneration_safety.py`.

### FIND-53: Generation Gave No Feedback; Skipped Files Counted as Failures
- **Status:** **COMPLETED** (`e203fd9`). Tests: `generation.test.ts`, `test_regeneration_safety.py`, `test_cli.py`.

### FIND-54: Quiz Showed a Canned Question When the Model Reply Did Not Parse
- **Status:** **COMPLETED** (`9613e54`). Tests in `tests/test_api.py`.

### FIND-55: One Broken Flashcard Lost the Whole Deck
- **Status:** **COMPLETED** (`425c29d`). Tests: `tests/test_json_salvage.py`, `test_search.py`.

### FIND-56: Course SUMMARY.md (From Chat Sessions) Could Be Packed or Committed
- **Status:** **COMPLETED** (`9bbb200`). Tests: `test_pack_privacy.py::test_course_summary_is_never_packed`, `test_security_hardening.py::test_check_staged_content_blocks_files_written_from_chat_sessions`.

### FIND-57: Host-Shell Paste Could Be Escaped by a Snippet
- **Status:** **COMPLETED** (`2aa0ee6`). Tests: `terminalText.test.ts`.

### FIND-58: Bulk Scoping Script Committed and Pushed
- **Status:** **COMPLETED** (`b67d6f6`). `scripts/scope_domain_curriculum.py` ran `git add`/`commit`/`push` itself. Test: `tests/test_no_auto_push.py` scans scripts, learning_engine, app/backend and bin.

### FIND-59: Env File Overrode Exported Variables
- **Status:** **COMPLETED** (`51e5c14`). `load_env_file()` now lets exported variables win (an empty export counts as unset). Test: `tests/test_env_precedence.py`; documented in `docs/CONFIG_AND_SECURITY.md`.

### FIND-60: Visual Courses in Music-Named Categories Got the Music Blueprint
- **Status:** **COMPLETED** (`2ad7872`). Course-level override in `domain_strategies.py`; the generator passes `subtopic_id` at all three `get_strategy` call sites. Root cause of the musician framing: the arts persona assumed musicians until `c48ab00`; content predates it. Content fixed in `f36f3d4`, `6ab5e64` (15 visual labs, ~400 paragraphs). Guard: `tests/test_visual_arts_audience.py`. FIND-49 is fully resolved.

### FIND-61: Model Preambles and Broken Fence Openers Reached Lessons
- **Status:** **COMPLETED** (`4f7fced`). `clean_model_markdown()` strips "Here is the …:" lines and `` ``markdown `` openers. 4 computing lessons cleaned by hand.

### FIND-62: `/api/tree` Sent Absolute Server Paths
- **Status:** **COMPLETED** (`60b343b`). Every course's `full_path` and every lesson's `path` were absolute; the browser read neither. Dropped from the response only; other GET endpoints probed clean. Test: `test_api.py::test_api_tree_does_not_reveal_server_paths`.

### FIND-63: `synapse lint` Missed Preambles and Titles, Exited 0 on FAILED
- **Status:** **COMPLETED** (`aa17a57`). New checks MODEL_PREAMBLE, MISSING_TITLE, DUPLICATE_LESSON_TITLE; `lint` and `lint --render` exit 1 on errors; CI lints the public curriculum. The generator now labels bare code fences (`learning_engine/code_fences.py`), so new courses no longer come back with UNTAGGED_CODE_BLOCK warnings. Tests: `tests/test_curriculum_linter.py`, `test_cli.py`.

### FIND-64: Mermaid Repair Broke Quoted Labels
- **Status:** **COMPLETED** (`bb354eb`). The node-label regex in `repair_mermaid_diagrams()` rewrote brackets inside quoted labels (`"W[:, 0:d/2]"` → `W[":, 0:d/2"]`); applied to the public curriculum it broke 15 working diagrams. Replaced by a quote-aware scanner (flowcharts only) that also quotes brackets/quotes inside labels. Regression run: 0 render errors over every public diagram; 9 of 11 failing local diagrams repaired automatically. Tests in `tests/test_generation_output.py`.

### FIND-65: Mentor "Clear conversation" Deleted Every Topic's Chats
- **Status:** **COMPLETED** (owner decision 2026-11-23: mentor window clears the open topic, Settings clears everything). New `DELETE /api/chat/session?query=`; Settings → Courses → "Clear all chat history". Checked in the app (isolated server, Playwright). Tests in `tests/test_cleanup.py`.

### FIND-66: Mentor Replies Lost Their Opening Paragraph; `synapse chat` Died on One Error
- **Status:** **COMPLETED** (`05e1923`, `73b6ca8`). Providers ran lesson cleanup on every reply; now only `check_model_reply`. Gemini empty reply raises. Contract tests for `generate_stream` / `generate_cancellable`.

### FIND-67: Release Scripts Published on Any Unknown Flag
- **Status:** **COMPLETED** (2026-11-23). `publish_all_releases.py --help` ran a full v1.3.1 publish to both hosts (every asset skipped as up to date; notes rewritten with the unchanged `[1.3.1]` CHANGELOG text, so nothing visible changed). `update_release_notes.py --help` or a mistyped `--dry-run` would rewrite notes the same way. Both now use argparse; tests in `tests/test_publish_curriculum.py`.

### FIND-68: Stop Waited for Every Model Call in Progress
- **Status:** **COMPLETED** (2026-11-23). Course generation called the uninterruptible `generate()`; Stop took effect only after in-flight calls returned (~4 min on a 32B model). Draft, refine and sequential calls now go through `_call_model`, which uses `OllamaProvider.generate_cancellable` (now with `max_tokens`, and `generate()` fallback on a 404 from servers without the native API). Checked in the app: Stop during a `qwen2.5-coder:32b` draft answered in 4 s, course unchanged, no staging leftovers. Conftest now routes `generate_cancellable` through the blocked `generate` (it streamed from a real Ollama before). Cloud providers still finish their call first.

### FIND-69: Thinking Models Returned Empty Replies on Short Budgets
- **Status:** **COMPLETED** (owner chose `think: false` for short calls, 2026-11-23). Ollama counts thinking against `num_predict`: `gemma4:26b` with 10 tokens replied "" (all thinking). `OllamaProvider` now sends `think: false` when the budget is ≤ `SHORT_REPLY_TOKENS` (2,048: mentor chat, short probes); unbounded calls (quiz, flashcards) and 8,192-token drafts keep the model's default. Plain models accept the flag (`qwen2.5:3b`, Ollama 0.40.17). Mentor chat with gemma4:26b checked on the isolated server. Tests: `tests/test_ollama_think.py`.

### FIND-70: Filling In Missing Files Added Duplicate Lessons
- **Status:** **COMPLETED** (2026-11-23). Without `--force` the generator re-planned the course with AI, so new names sat next to old lessons. The plan is saved (`.generation_plan.json`, git-ignored, not packed) and reused; lessons without a plan get only `labs.md`. Course menu: "Generate missing files". Checked in the app. Tests: `tests/test_course_plan.py`.

### FIND-71: Language and Tool Courses Got Compiler Labs
- **Status:** **COMPLETED** (2026-11-23). Found while checking FIND-70: a Bash lab came out as a C++ AST/IR exercise. `software`/`systems`/unmatched computing categories used the compiler blueprint. New `GeneralSoftwareStrategy`; four low-level courses keep the old one. Existing labs unaffected (checked: Bash's lab is on-topic). Tests: `tests/test_computing_blueprints.py`.

### FIND-72: Gemini Did Not Work for New Accounts; Short Replies Cut Off
- **Status:** **COMPLETED** (2026-11-23, live key from the owner). (1) Default `gemini-2.5-flash` (and 2.5-pro) answer 404 "no longer available to new users": default now `gemini-3.8-flash`, model list 3.8-flash / 3.5-flash / 3.5-flash-lite. (2) Gemini 3 thinking counts against `max_output_tokens`: a 200-token reply was "`set -"; short calls (≤ `SHORT_REPLY_TOKENS`) send `thinking_budget=0`, retried without it on 400 (3.5-flash-lite rejects it). (3) Mentor chat now really streams (`generate_content_stream`). Checked live: all three models; mentor chat in the app, streamed and not. Tests: `tests/test_gemini_provider.py`.

### FIND-76: FIND-75 Refactor Broke Outline Lesson Names; CI Red, v1.3.2 Released on Red
- **Status:** **COMPLETED** (2026-11-23, `11300a1`). `\**` in the TOPIC_OUTLINE.md regex made outline courses produce `lesson_01_.md`; CI red runs #153–#158, v1.3.2 tagged from `94148e4` (red). The same refactor made `get_chat_provider` probe the cluster before a cloud mentor and swap models on an unreachable host; restored (`85f2e3b`, `tests/test_chat_provider_routing.py`). `/api/topic` before/after compared on 14 public courses: identical. AGENTS.md §3 now requires green verify + CI before commit/push/release (`46d606a`).

### FIND-77: Gateways Got the Wrong Model
- **Status:** **COMPLETED** (2026-11-23, `85f2e3b`, `19c2fed`). On a non-Anthropic base URL every model became one fixed name per family (`claude-sonnet-5`, which the new gateway lacks: 404), and `gpt-5.5` became Claude. Exact IDs now pass through. App env switched to `aeroai.aerolink.ink`, `claude-sonnet-5-5` (checked live).

### FIND-78: Translation State Was Invisible
- **Status:** **COMPLETED** (2026-11-23, PR #5). Each lesson opened in English; a queued or finished translation showed only after re-picking the language, and the owner could not tell whether revisiting lost it (it did not: submit reuses the active job, the cache keeps results; a server restart drops queued jobs). Now: `GET /api/translate/status`, remembered reading language, auto-open of cached/queued lessons, Translate button otherwise, sidebar markers. Tests: `tests/test_translation_jobs.py`, E2E `test_translations_are_visible_per_lesson_in_the_remembered_language`.

### FIND-79: Status Bar Split App Status From the Running Translation
- **Status:** **COMPLETED** (2026-11-23, PR #4). E2E `test_status_bar_during_background_translation` uses the app while a translation runs.

### FIND-80: A Model Dropped by the Gateway Retried ~40 s, Then Showed Raw JSON
- **Status:** **COMPLETED** (2026-11-24). aerolink removed `claude-sonnet-5-5` overnight; the mentor and translation retried 5 times and then showed the gateway's JSON. Now a 404 naming the model raises `ModelUnavailableError` at once: "<host> does not offer the model 'X'. It offers: ... Pick another model in Settings or set ANTHROPIC_MODEL." (list from `/v1/models`, omitted when unavailable). Tests: `tests/test_claude_provider.py`.

### FIND-81: 67 Broken or Mislabelled Python Blocks in Public Lessons
- **Status:** **COMPLETED** (2026-11-24, owner: "continue with all remaining tasks"). Found free by `synapse lint` (`PYTHON_SYNTAX_ERROR` / `MISSING_IMPORT`). 37 missing imports added; 23 shell / SQL+dbt / k6 / gyp / pseudocode / query blocks retagged from `python`; 4 one-line bugs (`min(...)` generator, `from sklearn.set_config`, `MetricUnit.None`, `ATT&CK_STAGE_MAP`); Ignition `runScript` rewritten (it takes a library function name, not inline code); a timeout function ignored its `normal_percentile` argument. Public lint: 0 code warnings. Private: 9 fixed in the addons repo (`e7f0b87f`).
- **Open:** 7 public lessons were cut off mid-code by generation (the repair step closed the fence, so `ABRUPT_TRUNCATION` missed them). Their code blocks are now complete, but any sections planned after that point are missing: ai_safety_and_alignment lesson 3, chatgpt_and_openai_apis labs, tensorflow lesson 3, vibe_coding lesson 4, devsecops lessons 5 and 6, linux_device_drivers lesson 4. Regenerate their endings when credit allows.

### Curriculum review (focused): IN PROGRESS
- Method, cost and the first 26 courses (329 findings): `.agent/reports/review_focused_2026-11-23.md`. Owner 2026-11-24: continue on aerolink `claude-opus-5-5` until its credit ($150) runs out; public courses first. Reports only; **fixing needs the owner** (each fix costs credit). Free first step: the lint warnings `PYTHON_SYNTAX_ERROR` / `MISSING_IMPORT`.
- Thin public decks (under 6 cards): regenerated 2026-11-24 (2 courses, 12 cards each).

### Queued translations are lost on server restart
- Candidate (not verified as a problem for the owner yet): the queue lives in memory. Persisting pending jobs would make restarts safe.

## Next Candidates (not yet verified)

- **Curriculum hallucinations:** see "Curriculum review (focused)" above (cross-family full review measured: too costly, ~45% nitpicks).
- **UI:** all main flows exercised in batches 1–6. (Listen, translation, Add Topic, rename/delete checked in batches 4–5.) (Quiz, Labs, Export checked: quiz generation works, ~2 min with a local model.)
- **CLI:** checked in batch 2 (FIND-30). `pack list/install/uninstall` checked in batch 6. `add`, `generate`, `chat` checked in batch 7.
- **Ship flashcard decks:** **COMPLETED** (2026-11-23). Scripts updated to support local Ollama generation without API credit. Final 29 decks generated and committed (`977e16a`). 100% of 539 public courses now have offline flashcard decks.

---

## Deferred Decisions & Unverified Behavior

- **Package Content Injection:** **COMPLETED** (`2779454`, `4e598ee`): extraction stages into `.install-{stamp}-{pid}`, validates all members, merges safely, and atomically swaps via `os.replace` with automatic rollback.
- **Terminal PTY Concurrency:** Real PTY process allocation and signaling remain mocked in the test environment to prevent host shell execution.
- **Complete Pack Backup:** **COMPLETED** (`2779454`): every domain a pack writes into is backed up first.

- **FIND-73** Private domain names in public code (generator branches, linter list, test fixtures, scope script). **Status:** **COMPLETED** (batch 18): moved to per-domain DOMAIN_PROFILE.json; guard added.
- **FIND-74** `synapse lint` failed on topics outside the workspace (`relative_to(WORKSPACE_ROOT)` in linter.py). **Status:** **COMPLETED** (batch 19): report paths fall back to the topics folder's parent.
- **FEAT** `synapse review --workers N --domain D`: bounded parallel full review; a unit whose review raises counts as "could not be reviewed" instead of aborting the run. **Status:** **COMPLETED** (batch 19).

- **Curriculum review:** superseded; running as the focused review (owner 2026-11-23/24). The saved rag_systems findings are unapplied.
- **Flashcard decks:** **COMPLETED** (All 539 shipped, final 29 generated via local Ollama in `977e16a`).

- **FIND-75 Refactor branch-heavy code (owner, 2026-11-23).** Status: **COMPLETED** (`8901d75`). Decomposed `get_topic_details` into 4 helpers, `scope_topic_curriculum` prompt generation into 4 template builders, and `get_chat_provider` into a strategy resolution pattern. Guarded by full backend test suites.
