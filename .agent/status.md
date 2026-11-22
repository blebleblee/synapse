# Milestone Status Report: Autonomous Maintenance & Verification

## 1. Saved Checkpoint & Synchronization State

- **Released:** v1.2.2 (2026-11-22) from `8670418`, `main` pushed to `gitea` and `github` (owner approved; `.gitea/` is on GitHub too, inert there). Packs passed `check_release_packs.py`; the macOS app bundles no curriculum, the Windows bundle only git-tracked core-domain files (checked). Earlier: v1.2.1 (2026-11-21); installers for v1.1.0–v1.2.0 were withdrawn for private content.
- **CI (green since run #15):** `.gitea/workflows/ci.yml` runs `verify_all.sh`, builds and checks release packs, and runs gitleaks on pushed commits. The runner is a Xeon E3-1265L v2 (x86-64-v2, no AVX2), so CI uses the image's python3 (setup-python's build needs v3) and Rolldown's WebAssembly binding (`NAPI_RS_FORCE_WASI` when the CPU lacks v3). `@rolldown/binding-wasm32-wasi` must match Rolldown's version; CI says so if it drifts. Check runs with `scripts/ci_status.py --wait` / `--log <job>`.
- **Tests are isolated from the host:** `tests/conftest.py` clears provider keys and hosts (`ANTHROPIC_API_KEY*`, `VNAIPRO_*`, `GEMINI_*`, `OLLAMA_HOSTS`, …); app shutdown waits for the start-up warm-up threads. Both hid failures until CI ran.
- **Decisions taken:** keep Electron; leave git history as is; no Gitea password rotation (server is local-only); agent notes live in `.agent/`; pushes to GitHub only with owner approval per push.
- **Curriculum release (2026-11-22, `606f85e`):** packs live on the `curriculum` release on both hosts, published with `scripts/publish_all_releases.py --curriculum`; only packs whose content digest changed are replaced (`curriculum.json` on the release). The app downloads from `curriculum` first, then v<version>/v1.2.0. App releases carry no packs and no longer the duplicate `Synapse-Portable-Windows.zip` (owner decision; the win-x64 zip, the macOS .zip and the 13 packs bundled in installers were kept on purpose). Gitea has no "not latest" flag, so its UI may show `curriculum` as the newest release; nothing in the app relies on "latest".
- **Verification:** `./scripts/verify_all.sh`, all 6 phases (2026-11-22 evening: 254 backend, 23 frontend unit, 11 E2E, oxlint 0 warnings, repo audit clean). Latest checkpoint: `a0b89d2` pushed to `gitea/main`. `main` is 30+ commits ahead of `github/main` (unreleased; push needs owner approval).
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

Commits (all pushed to `gitea/main`; CI #49–#51 green, #52 pending):
- `997c975` fix(security): cross-origin POST/PUT/DELETE rejected by middleware (no-cors CSRF, e.g. `/api/system/shutdown`); shutdown no longer trusts the `testclient` host. FIND-20.
- `8dbc84d` fix(mentor): UI shows the model that actually answers; fallback marked amber. FIND-21.
- `932a30a` fix(settings): "Clear Transient Cache" deleted all chat sessions; "Vacuum" did nothing but reported success. FIND-22.
- `a0b89d2` fix(sidebar): tree reveals the restored topic after reload; "AI"/"3D" acronyms; "Connecting…" label. FIND-23.

Verification: `./scripts/verify_all.sh` all 6 phases (254 backend, 23 frontend unit, 11 E2E, oxlint 0 warnings, repo audit clean).
