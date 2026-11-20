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

## 5. Rebuilding Desktop Binaries & Exporting SynPack Addons

Once verification passes cleanly, compile fresh binaries and export the modular curriculum addons:

```bash
# 1. Rebuild React Frontend SPA, PyInstaller Sidecar & macOS Desktop Installer
bash scripts/build_mac_desktop.sh
# Artifacts created in: dist/desktop/
# - dist/desktop/Synapse-Workbench-1.1.1-arm64.dmg
# - dist/desktop/Synapse-Workbench-1.1.1-arm64-mac.zip

# Note on macOS App Updates & Cleanup:
# If you are updating a local installation, macOS caches Chromium app state.
# Run `bash scripts/clean_mac_install.sh` to purge old app caches before installing the new DMG.

# 2. Rebuild Python Wheel and Source Distribution
.venv/bin/python -m build --outdir dist/python
# Artifacts created in: dist/python/
# - dist/python/synapse-1.0.0-py3-none-any.whl (~74 KB)
# - dist/python/synapse-1.0.0.tar.gz (~81 KB)

# 4. Export Modular .synpack Addons for All 12 Domains
mkdir -p exports/packages
bin/synapse pack export computing
bin/synapse pack export arts
bin/synapse pack export crafts
bin/synapse pack export business
bin/synapse pack export engineering
bin/synapse pack export motorsports
bin/synapse pack export formal_sciences
bin/synapse pack export humanities
bin/synapse pack export languages
bin/synapse pack export economics
bin/synapse pack export natural_sciences
bin/synapse pack export health_sciences
```

---

## 6. One-Click Automated Post-Generation Pipeline

To run Steps 3, 4, and 5 automatically in sequence, simply execute:

```bash
bash scripts/post_generation_pipeline.sh
```
