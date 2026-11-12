# Synapse Project Backlog & Session State Snapshot
**Date:** November 12, 2026  
**Repository Branch:** `main`  
**Current Git HEAD:** `65bb122` (Local git clean; ready to push to remote when online)

---

## 1. Executive Status

* **Curriculum Taxonomy:** Standardized strictly on 3 levels: `Domain` (L1) -> `Discipline` (L2) -> `Topic` (L3). Exactly 504 clean Level 3 topics across 80 disciplines and 12 domains.
* **Taxonomy Standardization:** All 12 `SYLLABUS.md` files sanitized to 2-segment paths (`discipline/topic/`). All residual numbered directories (`01_*`, `02_*`) flattened into canonical Level 3 topics (`kubernetes`, `bass_guitar`, `drums`, `electric_guitar`, `piano`).
* **Taxonomy Guards:** Hardened `TaxonomyService` (`learning_engine/services.py`) and `scripts/generate_all.py` to enforce strict 3-level depth (`topics/{domain}/{discipline}/{topic}/`) and reject any 4-level or numbered subfolder generation.
* **Database & Persistence:** SQLite WAL mode active in `data/synapse.db` (`settings` & `mastery` tables).
* **CLI Standard:** Single canonical executable: `./bin/synapse`.
* **Test Suite:** 34/34 tests passing (`pytest tests/`).
* **Frontend:** Built and compiled cleanly in `app/frontend/dist` (`npm run build`).

---

## 2. Completed Items (Ready & Verified)

### A. Rendering & Content Integrity
- [x] **Mermaid Re-render Loop Fix:** Converted `renderMermaidDiagramsInElement` to use `mermaid.render()` with `data-rendered="true"` guards and unique IDs. Diagrams no longer re-parse their own SVGs on state change.
- [x] **Mermaid Syntax Sanitizer:** Added `sanitizeAndRepairMermaid()` to auto-strip semicolons, quote multi-word edge labels, and fix malformed arrows.
- [x] **Domain-Specific KaTeX Guard:** KaTeX LaTeX parsing strictly restricted to `formal_sciences` and `natural_sciences`. Disabled for `computing`/`engineering` so shell variables (`$VAR`, `$$`, `$PATH`) are never turned into math spans.
- [x] **DevSecOps Lab Specialization:** Specialized `generator.py` prompt for DevSecOps with real AppSec tools (`trivy`, `semgrep`, `gitleaks`, `cosign`, `syft`, `grype`, `opa`/`conftest`). Regenerated `computing/infrastructure/devsecops`.
- [x] **Bash Masterclass Rework:** Completely purged and regenerated `computing/systems/bash` into 4 clean lessons + labs using Claude 3.5 Sonnet.
- [x] **Kubernetes Masterclass Flattening:** Flattened `computing/infrastructure/kubernetes/01_control_plane_and_etcd` directly into `computing/infrastructure/kubernetes/` (4 lessons + labs).
- [x] **Global Taxonomy Standardization & Flattening:** Ran `scripts/standardize_taxonomy.py` across all 12 domains; converted all `SYLLABUS.md` files to canonical 2-segment relative paths (`discipline/topic/`), flattened all lessons in `bass_guitar`, `drums`, `electric_guitar`, `piano`, and `kubernetes`, and purged all numbered unit subfolders.

### B. UI & Ergonomics Redesign
- [x] **Terminal Header Redesign:** Clean 40px bar; removed redundant "Terminal" text; combined `[ >_ Icon ] [ Status Dot ] [ Environment Dropdown ]`; moved Setup Guide to right action bar.
- [x] **Terminal & AI Status Synchronization:** Lifted `terminalConnected` state into `App.tsx`. AI mentor badge accurately reflects whether terminal is live or offline.
- [x] **Socratic Mentor Header:** Unified into a sleek single card with glowing avatar, domain specialization pill, Terminal Live chip, and Clear Chat action.
- [x] **Settings Window Redesign:** Expanded from narrow vertical scroll to wide **780px tabbed workstation window** (🎨 *Theme & Reader*, ⚡ *Cluster Nodes*, 🧠 *AI Models & API Keys*).
- [x] **Topic Filter Instant Clear Button:** Added one-click `✕` clear button inside search filter in `TopicTree.tsx`.
- [x] **Keyboard Shortcuts:** `Cmd+K` (Search), `Cmd+J`/`Cmd+[` (Next/Prev Lesson), `Cmd+B` (Terminal drawer), `Cmd+1/2/3` (Tabs).
- [x] **Executable Code Blocks:** Added one-click `▶ Run in Sandbox` button for `bash`, `python`, `c`, `rust`, and `sql`.

### C. Security & Robustness
- [x] **SQLite WAL Mode:** Configured `PRAGMA journal_mode=WAL;` and `timeout=10.0` with `get_db_connection()` context manager.
- [x] **ReDoS Bounds:** Bounded API query strings to max 256 characters before regex execution.
- [x] **Terminal Buffer Memory Cap:** Enforced `MAX_LINE_LENGTH = 10_000` (10KB limit per line) in `TerminalRingBuffer`.
- [x] **Path Traversal Guards:** Enforced `validate_workspace_path` on `resolve_subtopic`.
- [x] **Host Privacy:** Sanitized all real hostnames and private URLs in `README.md` to standard RFC placeholders. Documented local SQLite storage for API keys.
- [x] **Resilient Terminal Pipe Bridge:** Added pipe-based interactive shell fallback in `main.py` if host hits macOS `kern.tty.ptmx_max` ceiling.

### D. Packaging & Addons Architecture
- [x] **SynPack Package Engine:** Built `learning_engine/packages.py` (`export_topic_pack`, `install_topic_pack`, `list_installed_packs`, `uninstall_topic_pack`, `get_domain_pack_info`).
- [x] **Package API Endpoints:** Added `GET /api/packages`, `POST /api/packages/export`, `POST /api/packages/install` (multipart file upload + domain param), and `DELETE /api/packages/{domain}`.
- [x] **Curriculum Store UI:** Built dedicated "Curriculum Store & Addons" workstation tab in `SettingsModal.tsx` with 1-click `.synpack` export, install/register, sideloading upload dropzone, and direct sidebar header launch button in `TopicTree.tsx`.
- [x] **Standalone Desktop Shell (Electron):** Built native window wrapper under `app/desktop` (`src/main.js`, `src/preload.js`, `package.json`, `electron-builder`) bundling `app/frontend/dist` and managing the Python FastAPI sidecar. Added canonical `./bin/synapse desktop` CLI launch command. Verified macOS `.app` packaging with `electron-builder`.

---

## 3. Active Operations & Monitoring

### Priority 1: Clustered Curriculum Generation (Active in Background)
- [x] Background curriculum batch running across all 12 domains (PID `2684`) using flagship cluster nodes (`localhost:32b`, `studio:32b`, `ai:30b`) with automated cross-node peer review and Gitea synchronization.
- [ ] Monitor full curriculum generation progress (`tail -f data/generation.log`).

---

## 4. Quick Restart Reference

When you restart the host/services:

```bash
# 1. Activate environment
cd /Users/radovan.varga/repos/synapse
source .venv/bin/activate

# 2. Check status
./bin/synapse status

# 3. Run test suite
pytest tests/

# 4. Launch backend workbench (port 8000)
./bin/synapse serve

# 5. (Optional) Run background curriculum generator
.venv/bin/python scripts/generate_all.py --domain all
```
