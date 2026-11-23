# Milestone Status Report: Autonomous Maintenance & Verification

## 1. Saved Checkpoint & Synchronization State

- **Released:** v1.3.0 (2026-11-23) from `7239c83`, `main` pushed to `gitea` and `github` (owner approved "when you have solid material for release push to gitea and github"). 7 assets on both hosts (Windows setup/portable .exe and win-x64 zip, macOS dmg/zip, wheel, sdist); GitHub sizes match the local builds. Checks: `check_release_packs.py` passed on the 13 packs; the macOS app bundles only those 13 packs; the Windows bundle's `topics/` is 2,969 files, all git-tracked, 12 core domains only; wheel/sdist carry no curriculum. `curriculum` release updated the same night: 10 of 13 packs changed (Mermaid, titles, arts GEMINI.md) and were replaced on both hosts after the guard passed. GitHub "latest" = v1.3.0. Earlier: v1.2.2 (2026-11-22), v1.2.1 (2026-11-21); installers for v1.1.0–v1.2.0 were withdrawn for private content.
- **CI (green since run #15):** `.gitea/workflows/ci.yml` runs `verify_all.sh`, builds and checks release packs, and runs gitleaks on pushed commits. The runner is a Xeon E3-1265L v2 (x86-64-v2, no AVX2), so CI uses the image's python3 (setup-python's build needs v3) and Rolldown's WebAssembly binding (`NAPI_RS_FORCE_WASI` when the CPU lacks v3). `@rolldown/binding-wasm32-wasi` must match Rolldown's version; CI says so if it drifts. Check runs with `scripts/ci_status.py --wait` / `--log <job>`.
- **Tests are isolated from the host:** `tests/conftest.py` clears provider keys and hosts (`ANTHROPIC_API_KEY*`, `VNAIPRO_*`, `GEMINI_*`, `OLLAMA_HOSTS`, …); app shutdown waits for the start-up warm-up threads. Both hid failures until CI ran.
- **Decisions taken:** keep Electron; leave git history as is; no Gitea password rotation (server is local-only); agent notes live in `.agent/`; pushes to GitHub only with owner approval per push.
- **Curriculum release (2026-11-22, `606f85e`):** packs live on the `curriculum` release on both hosts, published with `scripts/publish_all_releases.py --curriculum`; only packs whose content digest changed are replaced (`curriculum.json` on the release). The app downloads from `curriculum` first, then v<version>/v1.2.0. App releases carry no packs and no longer the duplicate `Synapse-Portable-Windows.zip` (owner decision; the win-x64 zip, the macOS .zip and the 13 packs bundled in installers were kept on purpose). Gitea has no "not latest" flag, so its UI may show `curriculum` as the newest release; nothing in the app relies on "latest".
- **Verification:** `./scripts/verify_all.sh`, all 6 phases (2026-11-23 ~05:15: 304 backend, 49 frontend unit, 15 E2E, oxlint 0 warnings, repo audit clean). Latest checkpoint: `6a896c3` pushed to `gitea/main`. `github/main` is at the v1.3.0 release commit `7239c83`; the commits after it are on gitea only (GitHub push needs owner approval).
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
- **Needs owner decision:** see "Needs Decision" in `backlog.md` (chat "Clear conversation" scope, absolute paths in `/api/tree`).
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
