# Milestone Status Report: Autonomous Maintenance & Verification

## 1. Saved Checkpoint & Synchronization State

- **Released:** v1.2.2 (2026-11-22) from `8670418`, `main` pushed to `gitea` and `github` (owner approved; `.gitea/` is on GitHub too, inert there). Packs passed `check_release_packs.py`; the macOS app bundles no curriculum, the Windows bundle only git-tracked core-domain files (checked). Earlier: v1.2.1 (2026-11-21); installers for v1.1.0–v1.2.0 were withdrawn for private content.
- **CI (green since run #15):** `.gitea/workflows/ci.yml` runs `verify_all.sh`, builds and checks release packs, and runs gitleaks on pushed commits. The runner is a Xeon E3-1265L v2 (x86-64-v2, no AVX2), so CI uses the image's python3 (setup-python's build needs v3) and Rolldown's WebAssembly binding (`NAPI_RS_FORCE_WASI` when the CPU lacks v3). `@rolldown/binding-wasm32-wasi` must match Rolldown's version; CI says so if it drifts. Check runs with `scripts/ci_status.py --wait` / `--log <job>`.
- **Tests are isolated from the host:** `tests/conftest.py` clears provider keys and hosts (`ANTHROPIC_API_KEY*`, `VNAIPRO_*`, `GEMINI_*`, `OLLAMA_HOSTS`, …); app shutdown waits for the start-up warm-up threads. Both hid failures until CI ran.
- **Decisions taken:** keep Electron; leave git history as is; no Gitea password rotation (server is local-only); agent notes live in `.agent/`; pushes to GitHub only with owner approval per push.
- **Curriculum release (2026-11-22, `606f85e`):** packs live on the `curriculum` release on both hosts, published with `scripts/publish_all_releases.py --curriculum`; only packs whose content digest changed are replaced (`curriculum.json` on the release). The app downloads from `curriculum` first, then v<version>/v1.2.0. App releases carry no packs and no longer the duplicate `Synapse-Portable-Windows.zip` (owner decision; the win-x64 zip, the macOS .zip and the 13 packs bundled in installers were kept on purpose). Gitea has no "not latest" flag, so its UI may show `curriculum` as the newest release; nothing in the app relies on "latest".
- **Verification:** `./scripts/verify_all.sh`, all 6 phases (2026-11-23 night: 279 backend, 41 frontend unit, 15 E2E, oxlint 0 warnings, repo audit clean). Latest checkpoint: `c48ab00` pushed to `gitea/main`. `main` is 30+ commits ahead of `github/main` (unreleased; push needs owner approval).
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
