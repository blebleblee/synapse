# Synapse Pipeline & Release Operational Runbook

This runbook documents the exact procedures to monitor, restart, remediate, validate, and release the Synapse Global Curriculum (539 topics across 12 domains) and the desktop application binaries.

---

## 1. Quick Status & Live Monitoring

To check live pipeline progress, worker drafting jobs, and recent Git commits at any time:

```bash
# Snapshot dashboard
python3 scripts/monitor.py

# Live streaming watcher (updates in real time)
python3 scripts/monitor.py --watch

# Raw engine log tail
tail -f generator.log

# Raw pipeline execution log
tail -f pipeline.log
```

---

## 2. How to Restart the Generation Pipeline

If the machine reboots or the pipeline process stops, restart it in the background with `caffeinate` (preventing macOS sleep):

```bash
cd "$(git rev-parse --show-toplevel || echo .)"

# 1. Kill any stale or dangling worker processes
pkill -f "run_pipeline.sh" || true
pkill -f "generate_all.py" || true

# 2. Launch autonomous pipeline in detached session
caffeinate -dimsu ./scripts/run_pipeline.sh >> pipeline.log 2>&1 &

# 3. Verify it is running
python3 scripts/monitor.py
```

*Note on Credentials:* The engine is permanently configured to use **VNAIPRO** (`https://apikey.vnaipro.app`) stored in `~/.config/synapse/env`. AIAPIFLOW is blacklisted.

---

## 3. Post-Generation Quality Remediation (Run After 539/539 Topics)

When the 539th topic finishes generating (Health Sciences completes), execute the remediation pass to conclude any lessons that reached the 8,192 token limit and add complete Summary & Verification Matrices:

```bash
# Concurrently conclude all truncated lessons and add summary matrices (uses 4 parallel workers)
python3 scripts/remediate_truncations.py
```

---

## 4. Full Quality & Render Verification

Ensure 100% compliance across all ~2,700 Markdown files before packaging:

```bash
# 1. Static AST Linter (Must report 0 Errors)
bin/synapse lint

# 2. Headless KaTeX Math & Mermaid.js Render Validation
bin/synapse lint --render

# 3. Full Automated Pytest Suite (59/59 must pass)
.venv/bin/python -m pytest
```

---

## 5. Building and Publishing a Release

Run these from a clean checkout of `main` after `./scripts/verify_all.sh` passes. Bump `VERSION` first (`python scripts/bump_version.py`) and add a `## [x.y.z]` section to `CHANGELOG.md`: the release notes are taken from it.

Curriculum packs are not part of app releases. They live on the separate `curriculum` release (see below). The installers still bundle the packs, so export them first:

```bash
# 1. Curriculum packs for the installers (core domains only; private and session files are excluded)
bin/synapse pack export arts business computing crafts economics engineering \
  formal_sciences health_sciences humanities languages motorsports natural_sciences all
python scripts/check_release_packs.py        # must pass: blocks private/uncommitted content

# 2. macOS app (React build, PyInstaller backend, Electron DMG + ZIP)
bash scripts/build_mac_desktop.sh            # -> dist/desktop/Synapse-Workbench-<ver>-arm64.{dmg,zip}

# 3. Windows apps (embedded Python with current code, then installer, portable .exe, portable .zip)
.venv/bin/python scripts/build_windows_python_env.py
.venv/bin/python scripts/build_windows_portable.py

# 4. Python wheel and source package
.venv/bin/python -m build --outdir dist/python

# 5. Publish to Gitea and GitHub (push main to both remotes first, so the tag points at this code)
git push gitea main && git push github main
.venv/bin/python scripts/publish_all_releases.py
```

`publish_all_releases.py` first checks that the working tree is committed, `HEAD` is `gitea/main`, and CI passed on that commit; otherwise it publishes nothing. It then creates the `v<ver>` release on both hosts, uploads the installers, portable builds and Python packages, and sets the notes from `CHANGELOG.md`. It exits non-zero if any upload fails.

### Curriculum release

When lessons change, publish the packs (independent of app releases):

```bash
.venv/bin/python scripts/publish_all_releases.py --curriculum
```

It exports the 12 core domains and the complete pack into a temporary folder, runs the release guard on them, and compares each pack's content digest (file names and contents, not timestamps) with `curriculum.json` on the `curriculum` release. Only changed packs are replaced; `curriculum.json` and the notes table are always refreshed. The release is never marked "Latest" on GitHub. The app downloads packs from `curriculum` first, then from older app releases.

To fix the notes of an existing app release later, edit `CHANGELOG.md` and run:

```bash
.venv/bin/python scripts/update_release_notes.py 1.2.1                # title + notes
.venv/bin/python scripts/update_release_notes.py 1.1.0 --keep-title   # notes only
```

If you're updating a local macOS install, run `bash scripts/clean_mac_install.sh` first to clear cached app state.

---

## 6. One-Click Automated Post-Generation Pipeline

To run Steps 3, 4, and 5 automatically in sequence, simply execute:

```bash
bash scripts/post_generation_pipeline.sh
```
