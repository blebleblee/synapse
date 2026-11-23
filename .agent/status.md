# Milestone Status Report: Autonomous Maintenance & Verification

- **Batch 16 (2026-11-23):** per-topic Clear conversation (FIND-65, checked in the app); four units rewritten in-session under the owner's exception (Grafana lesson 4, monitoring labs, SQL lesson 4, Adobe CC lab; `5914b21`); `curriculum` release updated on both hosts (arts, computing, complete packs; complete pack downloaded back from GitHub: 12 core domains, 2,969 lessons = git, guard passes); release scripts no longer publish on `--help`/unknown flags (FIND-67, `5fa2293`). Private: 1,302 lessons retitled in addons (local commit `4b437507`, amended), synced; **addons push to origin awaits the owner**.
- **Batch 17 (2026-11-23):** Stop interrupts in-flight Ollama calls (FIND-68, 4 s in the app); `think: false` on short Ollama calls (FIND-69); "Generate missing files" reuses a saved course plan (FIND-70); language/tool courses no longer get compiler labs (FIND-71); deck script ready (`scripts/generate_flashcard_decks.py`); `synapse review --provider anthropic`. Addons pushed to origin (owner). **Waiting for the API proxy:** flashcard decks (539, ~$15) and the review pilot (computing). Still needs a Google `AIza` key: live Gemini check of the app's provider.
- **API proxy: do not use** (owner, 2026-11-23). `/v1/messages` returns 403 "用户额度不足" (wallet −$0.000962) for both keys although the dashboard shows ~$215. Hallucination-audit pilot (computing, `claude-sonnet-4-6`; the proxy has no Sonnet 5.5) waits until the owner says the proxy works. Then use it for every remaining API task without asking again (owner); a Gemini key on the same proxy (same empty wallet) can serve as the different-family reviewer.

## 1. Saved Checkpoint & Synchronization State

- **Released:** v1.3.1 (2026-11-23) from `05c4f22`, `main` pushed to `gitea` and `github` (owner: "if it makes sense to release 1.3.1 with fixes then do it"). 7 assets on both hosts (Windows setup/portable .exe and win-x64 zip, macOS dmg/zip, wheel, sdist); GitHub sizes match the local builds; GitHub "latest" = v1.3.1. Checks: `check_release_packs.py` passed on the 13 packs; the complete pack holds only the 12 core domains; the macOS app bundles only those 13 packs; the Windows bundle's `topics/` is 2,954 files, all git-tracked, 12 core domains only; wheel/sdist carry no curriculum. `curriculum` release updated the same morning: 6 of 13 packs changed (formula fixes, arts labs) and were replaced on both hosts. Earlier: v1.3.0 (2026-11-23, `7239c83`), v1.2.2, v1.2.1; installers for v1.1.0–v1.2.0 were withdrawn for private content.
- **CI (green since run #15):** `.gitea/workflows/ci.yml` runs `verify_all.sh`, builds and checks release packs, and runs gitleaks on pushed commits. The runner is a Xeon E3-1265L v2 (x86-64-v2, no AVX2), so CI uses the image's python3 (setup-python's build needs v3) and Rolldown's WebAssembly binding (`NAPI_RS_FORCE_WASI` when the CPU lacks v3). `@rolldown/binding-wasm32-wasi` must match Rolldown's version; CI says so if it drifts. Check runs with `scripts/ci_status.py --wait` / `--log <job>`.
- **Tests are isolated from the host:** `tests/conftest.py` clears provider keys and hosts (`ANTHROPIC_API_KEY*`, `VNAIPRO_*`, `GEMINI_*`, `OLLAMA_HOSTS`, …); app shutdown waits for the start-up warm-up threads. Both hid failures until CI ran.
- **Decisions taken:** keep Electron; leave git history as is; no Gitea password rotation (server is local-only); agent notes live in `.agent/`; pushes to GitHub only with owner approval per push.
- **Curriculum release (2026-11-22, `606f85e`):** packs live on the `curriculum` release on both hosts, published with `scripts/publish_all_releases.py --curriculum`; only packs whose content digest changed are replaced (`curriculum.json` on the release). The app downloads from `curriculum` first, then v<version>/v1.2.0. App releases carry no packs and no longer the duplicate `Synapse-Portable-Windows.zip` (owner decision; the win-x64 zip, the macOS .zip and the 13 packs bundled in installers were kept on purpose). Gitea has no "not latest" flag, so its UI may show `curriculum` as the newest release; nothing in the app relies on "latest".
- **Verification:** `./scripts/verify_all.sh`, all 6 phases (2026-11-23 ~09:00: 325 backend, 56 frontend unit, 15 E2E, oxlint 0 warnings, repo audit clean). Release checkpoint: `05c4f22` on `gitea/main` and `github/main` (CI #113 green). Handoff commits after it are on gitea only.
- **Security finding (2026-11-21):** the Gitea password was hard-coded in `scripts/upload_gitea_release.py` in commits `b99e525`..`b1fd437`, public on GitHub. No rotation (local-only server). Never print it.
- **Pending owner actions:** top up proxy credit; send the Safari diagram case.
- **Improvement ideas (completed 1–7):** release from CI; protected `main` with PR-only changes.

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

## 3. Open Items

- **Terminal PTY:** real PTY allocation, signaling and backpressure are only exercised with mocks (tests never spawn host shells). A bounded real-PTY test in `tmp_path` was proposed; awaiting owner answer.
- **Frontend mentor streaming reconnection:** abrupt TCP drops during streaming are not covered by E2E.
- **Needs owner decision:** see "Needs Decision" in `backlog.md` (chat "Clear conversation" scope).
- **Pending owner questions (asked 2026-11-22):** scope of unattended runs once the backlog is empty; ship the unreleased commits as v1.3.0; delete the merged `security/audit-hardening` branch. Until answered: no GitHub push, no release, no branch deletion.

---

## 4. Latest Batch (2026-11-22 evening, 24 h owner-requested loop)

Owner asked for a continuous loop: UI bugs first (verified in the real app with Playwright), then old items, new features, CLI checks and curriculum.

UI testing setup (not committed): isolated server on 127.0.0.1:8765 with `env -i`, `HOME`, `SYNAPSE_WORKSPACE`, `SYNAPSE_TOPICS_DIR` and `SYNAPSE_DB_PATH` in the session scratchpad, topics from `git archive` of three public domains. Note: the variable is `SYNAPSE_WORKSPACE`, not `SYNAPSE_WORKSPACE_ROOT`. Playwright MCP snapshots land in `.playwright-mcp/` (now git-ignored).

Commits (all pushed to `gitea/main`; CI #49–#56 green, #57+ queued at handoff (slow runner)):
- `997c975` cross-origin POST/PUT/DELETE rejected (no-cors CSRF). FIND-20.
- `8dbc84d` UI shows the model that actually answers; fallback marked amber. FIND-21.
- `932a30a` "Clear Transient Cache" deleted all chats; "Vacuum" was a no-op. FIND-22.
- `a0b89d2` sidebar reveals restored topic; "AI"/"3D" acronyms; "Connecting…". FIND-23.
- `35b0705` locked first run: only the login card; no 401 polling before login. FIND-24.
- `59c4e86` flashcards: generation hint, 503 on failure, real title; start-up waits for the server. FIND-25.
- `5576c11` Escape closes Search/Settings/Graph/Flashcards; dead "Propositional Logic" pathway link. FIND-26.
- `771c769` terminal PTY slave fd closed twice → killed unrelated sockets ("Invalid frame header"). FIND-27.
- `b14085c` course-path links read "Kubernetes: Kubernetes" (301 doubled graph labels). FIND-28.
- `7ff4d93` Anki export regenerated/overwrote decks; placeholder decks cached; Anki headers on one row; leaked test deck removed from kubernetes. FIND-29.

### Batch 15 (2026-11-23, 09:45–12:30): visual labs, root-cause fixes, review

Owner: labs for the 15 arts courses and music analogies fixed (API key for generation only, until its credit ran out: it did, twice); then "review the code and topics again". All commits on `gitea/main`, not on GitHub.
- Content: `f36f3d4`, `6ab5e64` (15 visual labs, music framing removed), `05143f4` (fence labels).
- Fixes: FIND-58…64 in `backlog.md` (auto-push script, env precedence, blueprint mapping, preamble cleaner, `/api/tree` paths, linter checks + exit code + CI step, Mermaid repair).
- `scripts/sync_addons.py` (`8a34d59`) copies the private curriculum both ways (git-ignored files only, never deletes, newest wins).
- Verify: 348 backend, 15 E2E, all 6 phases (12:20). CI was queued behind the slow runner (#121–#124 at handoff; #120 green).
- Owner approved a curriculum release after the content work; not yet published (packs to rebuild and check first).
- In progress locally: UX paragraph rewrites (Gemma), then course retitling for private tracks and the Adobe lab.

### Batch 14 (2026-11-23, 09:00–09:45): content move, v1.3.1, loop end

- `853fc8f`: FIND-49 resolved per owner: 15 labs moved to the private addons repo, removed here; 3 real visual labs kept (heading fixed). The 15 courses show "Labs not yet generated".
- `becebff` CHANGELOG; `05c4f22` **v1.3.1 released** (see Saved Checkpoint) and the `curriculum` release updated.
- The 24h maintenance loop ended here at the owner's request ("continue with remaining planned work until you have everything done. save everything then and exit").
- **Open for the next session (backlog):** labs for the 15 arts courses; music analogies in 42 visual-arts files; hallucination approach (owner asked for the list again: cross-family reviewer, run code blocks in the sandbox in CI, verify extracted claims, "Report a mistake"); Stop latency during drafting; contract tests for `generate_stream`/`generate_cancellable`; TOPIC_OUTLINE capstone is IT-flavoured; mentor replies still go through lesson cleanup.

### Batch 13 (2026-11-23, 08:30–09:00): owner decisions

- `04a85ad` (CI #107): owner: the field guide and the course summary are leftovers of an earlier design. Both features removed (UI items, `/api/artifacts/compile`, `/api/summary/regenerate`, `learning_engine/summary.py`, SUMMARY.md in the topic payload and handbook). Privacy guards kept for old copies on disk. Earlier batch work on them (`8041726`, `5285157`) is superseded.
- Owner: Run buttons make sense only on runnable code, which cannot be told reliably, so rename. Done: "⇥ Send to terminal" (+ wrapper in brackets); behaviour unchanged.
- FIND-49 (owner decision): of the 18 suspect arts labs, 15 are music-production exercises; they moved to the private addons repo (commit there `272000d3`) and were removed from the public courses, which now have no labs. The other 3 (sketching, graphic_design, photography) are real visual labs; their "DAW / Studio Setup" heading was fixed, their music analogies remain (see the analogies item).
- `becebff`: CHANGELOG `[Unreleased]` now covers everything since v1.3.0 (ready for a v1.3.1 if the owner wants one; GitHub push/release needs approval).

### Batch 12 (2026-11-23, 07:38–08:05): privacy, summary, terminal

- `9bbb200` privacy: `<course>/SUMMARY.md` ("Regenerate summary") is written partly from the learner's chat sessions and was neither git-ignored nor excluded from packs. Now both, listed private in AGENTS.md; the pre-commit guard blocks it and `MASTERED_GUIDE.md` (missed in FIND-51). FIND-56.
- `5285157` (CI #104): summary regeneration reports model errors (502) and never replaces SUMMARY.md with an empty reply. Not clicked in the app (button only shows once a summary exists; error path uses the existing notice).
- `2aa0ee6` (CI #105) **security:** Run on Host Shell sends a bracketed paste; snippet text was not cleaned, so an `ESC[201~` in an imported (untrusted) pack's code block could end the paste and run the rest without review. Control characters are now stripped. Checked in the app: a six-line lab command is typed into zsh, not run. FIND-57.
- Translation failure handling reviewed (already guarded: errors and truncation keep the English section).

### Batch 11 (2026-11-23, 06:26–07:15): AI feedback, quiz, flashcards

- `e203fd9` (CI #100): the UI ignored `/api/generate` results, so a run where every file failed (no model) just reloaded silently; it now says what was generated/failed and whether the old lessons were kept. Skipped files (already on disk) are `results.skipped`, not failures: the CLI prints "Kept N existing file(s)" and exits 0; the API returns `skipped`. After a generation finished, reloading the course fired the stale cancel handler ("Generation stopped" notice + a server cancel); only the Stop button stops the server now. FIND-53.
- `9613e54` (CI #101): **the quiz showed a hard-coded question** ("what is the primary architectural trade-off?", generic options) whenever the model's reply did not parse; now a 502 with a clear message. Cause in practice: qwen2.5-coder:32b put unescaped quotes in one question, invalidating the whole array; questions are now parsed one by one and malformed ones dropped. Checked in the app: the Bash quiz shows 2 real questions. FIND-54.
- `425c29d` (CI #102): flashcards had the same all-or-nothing parse; shared helper `learning_engine/json_salvage.py`. Checked in the app: Bash deck, 8 cards. FIND-55.
- Note for UI checks: the UI sends the Ollama host from Settings, so the scratch server reaches the local Ollama even when started with an unreachable `OLLAMA_HOSTS`.

### Batch 10 (2026-11-23, 05:26–06:00): Export, Regenerate/Stop

- `8041726`: Export → field guide now downloads `<course>_field_guide.md` (it only saved into the course folder after minutes of AI work); label "My Field Guide (.md, AI)". Checked in the app with the endpoint mocked.
- `d4fa183` (CI #98 green) **data loss:** "Regenerate with AI…" deleted the course's lessons and every subfolder (the learner's `sessions/` too) before drafting; Stop only aborted the browser request and the server kept drafting. Found in the app: Stop left the scratch Bash course an empty folder. Now staged (old lessons replaced only when every file succeeds; subfolders untouched; a new course keeps what succeeded), `POST /api/generate/cancel`, and a second generation of the same course is refused (409). FIND-52.
- Live check of Stop on qwen2.5-coder:32b (scratch workspace): the one draft already in flight finished (~4 min), the rest were skipped, nothing was published; the course incl. `sessions/` was byte-identical afterwards and no staging folder was left. Layout at 1024/1280 px has no horizontal overflow.

### Batch 9 (2026-11-23, 04:48–05:15): UI sweep, privacy

- Curriculum scan: the arts music-template mix-up (FIND-49) is the only cross-discipline template problem in public content (IT/lab-science headings checked).
- `148d15b`: mentor replies had no Markdown styles (bullets outside the text column, code blocks without background); checked in the app. FIND-50.
- `6a896c3` **privacy:** "Mastered Field Guide" writes `<course>/artifacts/MASTERED_GUIDE.md` from the learner's chat sessions; it was neither git-ignored nor excluded from packs. Now both, and listed as private in AGENTS.md. FIND-51.
- Progress select (Not Started / Studying / Lab Verified / Mastered) persists across reload. Export menu items checked.
- Note: while checking the ignore rule I created and removed `topics/computing/systems/bash/artifacts/` in the real tree without first checking whether it existed. No `artifacts/` folder or guide exists in any course, so nothing was likely lost, but it cannot be proven. Use `git check-ignore --no-index` on non-existent paths instead.

### Batch 8 (2026-11-23, 04:15–04:50): arts generator, curriculum audit

- App "Generate Learning Units Now" checked end to end on qwen2.5-coder:32b after `a6cfa24`: 3 lessons + labs, readable, 0 render errors.
- `427af10` (CI #91 green): Gemini mentor streaming (base `generate_stream`).
- `d32f356`: **every arts course used the music blueprint**, so visual lessons address "composers/audio engineers" and 18 non-music labs are music-production exercises (3d_graphics/3d_animation, 3d_graphics/3d_rendering, 3d_graphics/blender, 3d_graphics/maya, design/interior_design, design/ux_design, design/web_design, visual_arts/2d_animation, visual_arts/art_history, visual_arts/color_theory, visual_arts/composition, visual_arts/sculpture, visual_arts/sketching, visual_media/content_creation, visual_media/davinci_resolve, visual_media/graphic_design, visual_media/photography, visual_media/video_production). New `ArtsVisualStrategy` for visual_arts/visual_media/design/3d_graphics; the TOPIC_OUTLINE path no longer gives non-music courses the music chapter template. New generation only; existing content NEEDS DECISION. FIND-49.

### Batch 7 (2026-11-23, 03:27–03:50): content generation, CLI

- `a6cfa24`: **lesson generation failed with every provider except Anthropic** — the generator passes `max_tokens=8192`, which Ollama, the Ollama cluster and Gemini did not accept, so all drafts failed ("unexpected keyword argument"), in the CLI and the app's "Generate Learning Units Now". Hidden because the test fakes and conftest's network blocker take `**kwargs`; `tests/test_provider_contract.py` checks the real methods. Also `synapse chat` crashed (missing import) and `add -g`/`generate` exited 0 when every file failed. Checked for real: CLI with qwen2.5-coder:7b wrote 3 lessons + labs (0 render errors); the app button on qwen2.5-coder:32b drafts lessons (~3–4 min each). FIND-48.
- CLI `add` (incl. duplicate and bad names) behaves; exit codes correct.

### Batch 6 (2026-11-23, 02:40–03:30): CI flake, mentor context, course packs

- `b7ae6db` (CI #84 green): CI #83 failed because Rolldown's WebAssembly bundler panicked ("Parking not supported on this platform"; first time in 23 runs). `verify_all.sh` retries the build once, only for that panic. FIND-44.
- `8933d73` (CI #85 green): the mentor got the terminal output and last command twice (system instruction + prompt) under a "you MUST inspect" rule; now once, ignored unless the question is about the terminal. Checked in the app with qwen2.5-coder:32b. FIND-45.
- `1092748`: Settings → Courses list is alphabetical (an imported course jumped to the top); "Import .synpack file" is a real button (was a label, unreachable by Tab). Export, import (keyboard), broken-file error checked in the app. FIND-46.
- `4fe4d9a` **safety:** `uninstall_topic_pack("")`/`(".")` resolved to the topics folder and deleted every course (`synapse pack uninstall .`; `DELETE /api/packages/%2E` from a non-browser client). Domain must be one folder name and a direct child. Also a successful CLI uninstall printed "Uninstall failed: 'message'" with exit 1. FIND-47. (`delete_subtopic` already guarded.)

### Batch 5 (2026-11-23): formulas, Add Topic

- `301045e` (CI #81 green): 100 KaTeX errors in 23 public lessons fixed (source typos and braces, `^\circ'`, `\urangle`, unescaped `&`, math nested in `\text{$..$}`); shared `utils/katexMacros.ts` (`\Arg`, `\with`, `\parr`, `\surhd`) used by the reader and `scripts/validate_render.mjs`. Validator: 0 issues in tracked files; six lessons checked in the app. FIND-42.
- `ae8b7f5` (CI #82 queued at handoff): the sidebar "+" Add Topic dialog always failed ("Invalid category 'x/y'"); it now creates `<domain>/<category>/<course>` with slugified names. Create, rename and delete checked in the app. FIND-43.

### Batch 4 (2026-11-23, after midnight): mentor relevance, arts generator, privacy note

- `c48ab00` (CI #76 green): mentor starter prompts depend on the domain (no terminal/debugging prompts on arts, humanities, languages…), checked in the app; `topics/arts/GEMINI.md` persona follows the course (music vs visual); Listen tooltip and `docs/CONFIG_AND_SECURITY.md` §6 say what leaves the computer. FIND-41.
- Lesson translation checked in the app: works with progress and Stop, ~1 min per section on qwen2.5-coder:32b.
- Open: 62 of 134 visual-arts lessons address the reader as a musician (backlog FIND-41 follow-up).

### Batch 3 (2026-11-22 23:00 – 2026-11-23): user feedback on UI, terminal safety, mentor

Commits (pushed to `gitea/main`; CI #65–#68 green, #69 onward queued behind the single runner at handoff):
- `fd5ea6d` Listen shows "Preparing…" (first synthesis takes ~1 min) and can be cancelled; audio for a lesson already left no longer starts later. FIND-36.
- `98d1cfd` mentor panel shows the course name in correct case ("Artificial Intelligence", not "ai foundations"). FIND-37.
- `540c518` **safety:** with Docker or k3s unreachable, "Linux Sandbox"/"Kubernetes Pod" started a host shell under the Sandbox label, so lesson Run buttons ran on the real machine. Now no shell opens; on Host Shell, Run only types the command (no Enter); zsh accepts `#` comments. FIND-38.
- `ce3c065` Settings rebuilt from titled groups with hints and one control size; the unused "Reviewer / Evaluator Model" select removed; 6px gutter between the three panels (user request). FIND-39.
- `1dec52e` mentor: lessons over 50,000 chars got 422 (351 public files); it saw only the first 5,000 chars; replies lost text before a `# comment` in code; "2-4 sentences" cap replaced by right-sized answers with lesson-first grounding and an accuracy rule. FIND-40.

Mentor check (qwen2.5-coder:32b, bash lesson 1, four real questions): all correct and grounded after the fix. Note: the server's own fallback mentor model is qwen2.5-coder:7b when the client sends none; 7b answers more accurately when kept very short. Script: scratchpad only, not committed.

Also deleted the merged `security/audit-hardening` branch on gitea and locally (owner approved; never on GitHub).

### Batch 2 (2026-11-22, ~22:00–22:50): CLI, rendering, curriculum

Commits (pushed to `gitea/main`; CI #60, #61, #63 green; #62 failed only because the runner timed out downloading the Playwright wheel from PyPI, and #63 contains that commit; #64+ queued at handoff):
- `149820c` CLI: one-line errors + exit 1, `prog=synapse`, `review` stops after 3 unreachable-reviewer failures, `clean --db` really vacuums, "no AI model is reachable" message. First CLI tests (`tests/test_cli.py`). FIND-30.
- `01855bc` math rendered only in formal/natural sciences (~440 lessons showed raw LaTeX); now everywhere with Pandoc-style `$` rules (prices stay text). `<digit` was escaped inside code ("IoMem&lt;0x100>"). Validator now imports the reader's own `mathSpans.ts`/`mermaidRepair.ts`. FIND-31.
- `7f65a0c` two courses carried another course's title ("Large Language Models", "Acoustic Guitar"); test keeps titles unique. FIND-32.
- `496bc60`, `103c111`, `417c42a` Mermaid repair: spaced quoted edge labels, sequence `;` (U+037E, since `#59;` truncates labels), no quoting inside quoted labels (the source of the nested-quote corruption), no double quotes on `|x|>`, quoted bracket/space labels on all arrows. FIND-33.
- `a1cbac2` mentor model shown only in the status bar (user request: header looked crowded). FIND-34.
- `1f8dad2` the remaining 47 broken diagrams fixed in 45 public lessons (validator: 0 broken); observability lesson 4 had mis-tagged closing fences that turned most of the lesson into one code block. FIND-35.

Next in line: about 100 KaTeX errors that learners now see (95 in formal/natural sciences, 5 in business/economics; `node scripts/validate_render.mjs topics/<domain>`), then the UI items listed under Next Candidates in the backlog.

False alarm recorded so nobody repeats it: "flashcard keys go to the terminal" only happens with a scripted `.click()`; a real click moves focus to the button. A regression test for the keyboard review flow was kept.

Verification: `./scripts/verify_all.sh` all 6 phases (268 backend, 38 frontend unit, 15 E2E, oxlint 0 warnings, repo audit clean).
