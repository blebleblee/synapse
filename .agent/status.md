# Milestone Status Report: Autonomous Maintenance & Verification

## 1. Saved Checkpoint & Synchronization State

- **Released:** v1.2.2 (2026-11-22) from `8670418`, `main` pushed to `gitea` and `github` (owner approved; `.gitea/` is on GitHub too, inert there). Packs passed `check_release_packs.py`; the macOS app bundles no curriculum, the Windows bundle only git-tracked core-domain files (checked). Earlier: v1.2.1 (2026-11-21); installers for v1.1.0–v1.2.0 were withdrawn for private content.
- **CI (green since run #15):** `.gitea/workflows/ci.yml` runs `verify_all.sh`, builds and checks release packs, and runs gitleaks on pushed commits. The runner is a Xeon E3-1265L v2 (x86-64-v2, no AVX2), so CI uses the image's python3 (setup-python's build needs v3) and Rolldown's WebAssembly binding (`NAPI_RS_FORCE_WASI` when the CPU lacks v3). `@rolldown/binding-wasm32-wasi` must match Rolldown's version; CI says so if it drifts. Check runs with `scripts/ci_status.py --wait` / `--log <job>`.
- **Tests are isolated from the host:** `tests/conftest.py` clears provider keys and hosts (`ANTHROPIC_API_KEY*`, `VNAIPRO_*`, `GEMINI_*`, `OLLAMA_HOSTS`, …); app shutdown waits for the start-up warm-up threads. Both hid failures until CI ran.
- **Decisions taken:** keep Electron; leave git history as is; no Gitea password rotation (server is local-only); agent notes live in `.agent/`; pushes to GitHub only with owner approval per push.
- **Curriculum release (2026-11-22, `606f85e`):** packs live on the `curriculum` release on both hosts, published with `scripts/publish_all_releases.py --curriculum`; only packs whose content digest changed are replaced (`curriculum.json` on the release). The app downloads from `curriculum` first, then v<version>/v1.2.0. App releases carry no packs and no longer the duplicate `Synapse-Portable-Windows.zip` (owner decision; the win-x64 zip, the macOS .zip and the 13 packs bundled in installers were kept on purpose). Gitea has no "not latest" flag, so its UI may show `curriculum` as the newest release; nothing in the app relies on "latest".
- **Verification:** `./scripts/verify_all.sh`, all 5 phases (2026-11-22: 228 backend, 22 frontend unit, 10 E2E, oxlint clean 0 warnings). Latest checkpoint: `54e87e9` pushed to `gitea/main`, CI run #33 green.
- **Security finding (2026-11-21):** the Gitea password was hard-coded in `scripts/upload_gitea_release.py` in commits `b99e525`..`b1fd437`, public on GitHub. No rotation (local-only server). Never print it.
- **Pending owner actions:** top up proxy credit; send the Safari diagram case.
- **Improvement ideas:** clear mentor provider errors and model indicator; send only the current lesson section to the mentor (faster local models); search highlighting, domain filter and jump-to-section; first-run health check; menu-bar Quit or idle shutdown for `synapse serve`; spaced-repetition review queue; pre-commit secret and private-path hook; release from CI; protected `main` with PR-only changes.

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

## 3. Unverified Behavior (Not Confirmed Defects) & Deferred Decisions

This verification suite asserts explicit paths, but does not provide complete coverage over all operational mechanics. These are **unverified behaviors** or deferred design decisions, not confirmed bugs:

1. **Package Content Injection (Decision Needed):**
   - The extraction process validates paths, but writes directly into `TOPICS_DIR` sequentially. If a package is rejected mid-extraction due to an unexpected file type, previously extracted files remain on disk. It is deferred whether to extract into a temporary directory and atomically rename upon complete success.
2. **Terminal PTY Concurrency & Race Conditions:**
   - Auth rejection is tested, but real PTY allocation, buffer clearing, process group signaling, and high-volume stream backpressure are entirely mocked out in the test environment.
3. **Frontend Mentor Streaming Reconnection:**
   - The test suite verifies backend SSE error frames, but frontend handling of abrupt TCP drops during streaming is not fully verified in automated headless browsers.

---

## 4. Verification Command and Results

```bash
./scripts/verify_all.sh
```

```text
==================================================
 🔍 RUNNING COMPLETE SYNAPSE VERIFICATION SUITE   
==================================================

[*] [1/5] Running frontend unit tests...
✔ 16 tests passed in 141.4ms (0 failed)

[*] [2/5] Running frontend linter...
oxlint: 0 errors, 25 non-blocking warnings

[*] [3/5] Building frontend production bundle...
tsc -b && vite build: 3646 modules transformed in 370ms (0 errors)

[*] [4/5] Running backend test suite...
pytest tests/: 108 passed in 58.73s (0 failed)

[*] [5/5] Running Chromium E2E browser tests...
pytest e2e/test_learner_journey.py: 8 passed in 40.57s (0 failed)

==================================================
 [✔] ALL 5 VERIFICATION PHASES PASSED             
==================================================
```