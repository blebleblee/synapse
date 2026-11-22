# Changelog

All notable changes to the **Synapse AI-Native Learning Workbench** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed
- **Terminal:** no longer retries every 2.5 seconds before you log in; it shows "Login required" and connects after login. The server now closes unauthenticated terminal connections with code 1008, which browsers can see.
- **First-run setup:** keyboard shortcuts such as ⌘K no longer open search behind the setup wizard or the login screen.
- **CLI:** added `synapse pack export <domain…|all>`, which the docs and the post-generation pipeline already used. The pipeline now also builds the complete pack and runs the release guard.
- **macOS build:** corrected misspelled hidden imports (`uvicorn.lifespan`) in `synapse.spec`.
- **Bulk generator (`scripts/generate_all.py`):** no longer commits or runs `git push origin main` on its own. Pass `--commit` to commit each finished topic locally; it only commits core domains and never pushes. Fixed a crash in the old retry loop (`time` was not imported), and importing the script no longer redirects output into `generator.log`.

### Documentation
- README and installation guide: version-free download instructions, a "Stopping Synapse" section, using Synapse as an installed web app, and current security behaviour. The release runbook now describes the real build and publish steps.

## [1.2.1] - 2026-11-21

### Security
- **Localhost-only by default:** without `SYNAPSE_PASSWORD`, the server only answers requests addressed to `localhost`, which blocks other machines and DNS-rebinding attacks. Use `SYNAPSE_ALLOWED_HOSTS` to allow more hosts.
- **Terminal WebSocket:** checks the `Origin` header (blocks cross-site WebSocket hijacking) and uses single-use 30-second tickets instead of `?token=` in the URL.
- **Settings API** never returns secrets or the token-signing key; API keys come back redacted.
- **Rendered lessons and chat** are sanitized (DOMPurify), and Mermaid runs in strict mode.
- **Hardened paths and requests:** topic rename and delete paths are validated, uploads are capped at 500 MB, the login rate limit no longer grows without bound, and `SYNAPSE_TRUST_PROXY` handles reverse proxies.
- **Docker:** the image runs as a non-root user, `--privileged` sandboxes are gone, and the build context excludes private and local files.

### Privacy
- **Packs and builds contain only the 12 core domains.** Chat sessions, blueprints and git-ignored tracks are never included. A release guard (`scripts/check_release_packs.py`) blocks uploads that would publish anything else. Installers for 1.1.0–1.2.0 have been withdrawn; please use 1.2.1.

### Fixed
- **Lesson rewrites no longer truncate lessons.** Review auto-fix and the generator's refine step now work section by section, and a rewrite is accepted only if every heading and code block survives and the length doesn't shrink. An unparseable review is reported as failed instead of "verified".
- **Claude:** retired model IDs are replaced (the cloud fallback works again); `temperature` is no longer sent, since current models reject it; Haiku is no longer silently mapped to Fable; refusals surface as errors; keys entered in Settings are used; requests identify as `Synapse-Workbench/<version>`.
- **Search** uses a self-updating SQLite FTS5 index: about 0.2 s per query instead of seconds, and it no longer blocks the server. Stale responses no longer overwrite newer results.
- **macOS Desktop**: Fixed an issue where the background proxy service remained running in the background after the UI window was closed.
- **UI Navigation**: Lesson titles in the sidebar now gracefully truncate (ellipsis) instead of overflowing into multiline blocks, reducing clutter.
- **Settings & Addons**: Added clear documentation within the Addons pane regarding how uninstalled core modules are generated or fetched.
- **Status Reporting**: Dynamic translation model attribution now correctly reflects the active model (this was fixed in the codebase but previously unreleased in macOS DMG).

## [1.2.0] - 2026-11-20

### Summary
Feature and resilience release introducing section-by-section markdown translation chunking with code/formula preservation, native Windows ConPTY terminal support via `pywinpty`, database WAL maintenance with automatic checkpointing, an overhaul of the macOS packaging pipeline with version-aware cache busting, and code-fence normalization across the 12 core domains, with the content linter now reporting no errors.

---

### Key Features & Enhancements

#### 1. Translation Chunking Engine & Code/Math Preservation
* **Section-by-Section Translation Chunking (`/api/translate`):** Segmented massive markdown documents along section boundaries (`(?=\n#{1,2}\s+)`) before translating. This eliminates context-window and output-token exhaustion on local Ollama models (e.g. Qwen 4B/7B, Llama 3.2), preventing truncated lessons.
* **Code & Formula Masking:** Code blocks, KaTeX formulas (`$$...$$`) and Mermaid diagrams are replaced with placeholder tokens (e.g. `___BLOCK_0___`) before translation and put back unchanged afterwards, so translation never alters code or math.
* **Truncation Fallback Guard:** Added proactive output validation that detects severely abbreviated translations (<20% of original source length) and falls back to original text without corrupting the persistent translation cache.

#### 2. Windows Native ConPTY & Terminal Interactive Line Discipline
* **Native Windows ConPTY Support (`pywinpty`):** Bundled `pywinpty>=2.0.14` in the isolated Windows embedded Python runtime (`dist/python-win`), enabling true pseudo-console allocation for full-screen terminal TUI applications (`vim`, `nano`, `htop`, `fzf`) directly within the embedded terminal drawer.
* **Interactive Backspace & Local Echo Fix:** Completely reworked the cross-platform fallback pipe bridge in `app/backend/main.py`. It now maintains an interactive Python line buffer, intercepts backspace keystrokes (`\x7f`, `\x08`), and transmits `\b \b` visual erasing sequences to `xterm.js`, resolving character deletion failures on Windows.
* **Safe Clean Exit & Zombie Prevention:** Updated Electron desktop lifecycle (`terminateBackend()`) to execute `taskkill /pid ... /T /F` on Windows, ensuring child `python.exe` and `uvicorn` processes are cleanly purged from Task Manager when the app closes.

#### 3. macOS Build Pipeline & Automatic Cache-Busting
* **Automated macOS Assembler (`scripts/build_mac_desktop.sh`):** Created a unified build script that compiles the React SPA, forces a fresh PyInstaller recompilation of `dist/bin/synapse`, verifies CLI health, and packages the Electron DMG and ZIP.
* **Authoritative Frontend Resolution:** Updated `resolve_dist_dir()` in `app/backend/main.py` to prioritize `SYNAPSE_RESOURCES_PATH/frontend/dist` over internal PyInstaller `_MEIPASS` caches, ensuring the Electron app always renders the freshest UI assets.
* **Version-Aware Cache Busting:** Added an automatic cache check in `app/desktop/src/main.js` that triggers `session.defaultSession.clearCache()` whenever an application version upgrade is detected. Added `Cache-Control: no-cache` headers on `index.html` FileResponse.
* **Platform Resource Scoping:** Scoped `extraResources` in `package.json` to exclude Windows Python binaries from macOS packages, reducing macOS DMG and ZIP installer size by over ~100 MB.
* **macOS Full Purge Utility (`scripts/clean_mac_install.sh`):** Added a one-click cleanup script to completely uninstall `Synapse Workbench.app`, terminate background daemons, and purge `~/Library/Application Support/Synapse Workbench`.

#### 4. Database Resilience & Concurrency Hardening
* **FastAPI Lifespan Migration:** Migrated from deprecated `@app.on_event("startup")` to standard FastAPI `lifespan` context managers.
* **Automatic WAL Checkpointing:** Enforced `PRAGMA wal_checkpoint(TRUNCATE);` on backend shutdown and startup to prevent SQLite write-ahead log bloating under high concurrency.
* **Busy-Retry Context Manager (`learning_engine/database.py`):** Upgraded `get_db_connection()` with exponential backoff retries and `PRAGMA busy_timeout=5000;`, eliminating `database is locked` operational errors during concurrent curriculum generation.
* **Database Maintenance CLI:** Added `synapse clean --db` to execute `VACUUM;` and `PRAGMA integrity_check;`.

#### 5. Curriculum Code-Fence Normalization
* **Heuristic Normalizer (`scripts/normalize_code_fences.py`):** Tags previously untagged code blocks in the 12 core domains with a language (`bash`, `yaml`, `json`, `sql`, `python`, `c`, `text`), so they get correct syntax highlighting.
* **Content Linting:** `bin/synapse lint` reports no errors or warnings for the core domains.
* **100% Masterclass Status:** Standardized operational lab naming, bringing canonical curriculum status to 539 / 539 masterclasses (100.0%).

#### 6. Socratic Mentor Generation Expansion
* **Expanded Output Horizon:** Increased streaming Socratic Chat token limit from 250 to 2048 tokens in `app/backend/main.py`, enabling complete, comprehensive pedagogical explanations and multi-file code blocks without mid-sentence truncation.

---

## [1.1.1] - 2026-11-19

### Summary
Maintenance and security release introducing instance-level password protection for cloud/VPS web deployments, non-blocking asynchronous terminal streaming on Windows, integrated multi-language toolbar flag toggling, and private SynPack curriculum distribution support.

---

### Key Features & Enhancements

#### 1. Hosted Instance Protection & Authentication
* **Zero-Dependency Instance Auth (`learning_engine/auth.py`):** Added optional instance password protection via `SYNAPSE_PASSWORD` (or `SYNAPSE_AUTH_PASSWORD`). When unset, Synapse operates in open single-user mode for seamless local development and desktop use.
* **Persistent Signed HMAC Tokens:** Implemented 30-day signed bearer tokens stored in browser `localStorage` and verified against a persistent SQLite secret.
* **Secured Terminal & APIs:** Integrated FastAPI HTTP middleware blocking unauthenticated `/api/*` endpoints with `401 Unauthorized`, and secured the `/ws/terminal` PTY WebSocket with connection-time token validation.
* **Brute-Force Rate Limiting:** Enforced IP-based rate limiting (5 failed attempts per 60 seconds) with constant-time password comparison (`hmac.compare_digest`).
* **Sleek React Login Modal:** Built an in-app authentication card (`LoginModal.tsx`) with automatic 401 interception and instant unlock/lock mechanics.

#### 2. Terminal Independence & Windows PTY Starvation Fix
* **Async Queue Streaming:** Refactored LLM chunk streaming in `/api/chat` and `/api/translate` to execute through a background thread queue (`asyncio.Queue` + `asyncio.to_thread`).
* **Zero Event Loop Blocking:** Completely unblocked the FastAPI asyncio event loop during model generation, resolving shell input lag and keystroke freezes on Windows.

#### 3. Translation UI & External Endpoint Routing
* **Reader Toolbar Language Switcher:** Added a one-click Quick Language Switcher to the `LessonViewer` toolbar (`🌐 EN ▾` with 🇬🇧 English, 🇨🇿 Čeština, 🇩🇪 Deutsch, 🇪🇸 Español).
* **Unified AI & Content Shift:** Toggling flags immediately updates both the active lesson translation and the Socratic Mentor conversational prompt language.
* **Cloud API Key Persistence:** Updated `SettingsModal` (`POST /api/settings`) and `models.py` to persist and prioritize Anthropic Claude and Gemini API keys and custom gateway URLs directly in SQLite.

#### 4. Private SynPacks & Addon Workflows
* **CLI Package Subsystem:** Added the `synapse pack` CLI command suite (`install`, `list`, `uninstall`) for air-gapped and headless package management.
* **Private Gitea Registry Support:** Enabled downloading `.synpack` archives from custom endpoints via `SYNAPSE_PACKAGE_REGISTRY` with optional bearer token authorization (`SYNAPSE_PACKAGE_TOKEN`).
* **Non-Destructive Backups:** Automated pre-extraction backups into `exports/backups/<domain>_<timestamp>` when installing an updated package over an existing domain directory.
* **Unified Cross-Runtime Workspace:** Aligned `learning_engine/security.py` to default safely to `~/.synapse` for all desktop, standalone binary, and web server runtimes, ensuring shared curriculum sources and mastery progress out of the box.

---

## [1.1.0] - 2026-11-16

### Summary
Milestone release marking the full 100.0% completion of the **Synapse Global Masterclass Curriculum** (539 topics across 12 domains, comprising 2,945 lessons and operational verification labs). This release packages the complete master curriculum into a unified 33.5 MB distribution (`synapse_complete_curriculum.synpack`), upgrades over 3,100 diagrams to vector Mermaid.js flowcharts, adds official KaTeX `mhchem` chemical formula rendering, and prepares the repository for public release on GitHub.

---

### Key Features & Enhancements

#### 1. Complete Global Polymath Curriculum (539 / 539 Topics)
* **100% Taxonomical Coverage:** All 12 domains fully authored and verified:
  * **Computing & Systems:** 162 topics (10.6 MB)
  * **Arts & Music:** 67 topics (3.4 MB)
  * **Crafts & Fabrication:** 60 topics (2.7 MB)
  * **Business & Strategy:** 41 topics (2.5 MB)
  * **Engineering:** 39 topics (2.8 MB)
  * **Humanities:** 39 topics (2.5 MB)
  * **Formal Sciences:** 33 topics (2.2 MB)
  * **Economics:** 32 topics (2.3 MB)
  * **Natural Sciences:** 30 topics (2.3 MB)
  * **Health Sciences:** 20 topics (1.0 MB)
  * **Motorsports:** 10 topics (0.7 MB)
  * **Languages:** 6 topics (0.5 MB)
* **Master Unified Addon:** Introduced `synapse_complete_curriculum.synpack` (33.5 MB), enabling 1-click installation of all 539 topics and 2,945 lessons/labs at once.

#### 2. Vector Graphics & Mathematical Rendering Engine
* **Vector Mermaid.js Upgrades:** Converted over 900 legacy ASCII box diagrams into modern, vector Mermaid.js flowcharts (` ```mermaid flowchart TD ... ``` `). Over 50% of all curriculum units (1,484 files) now feature vector Mermaid diagrams (3,172 total diagrams across the workspace).
* **High-Contrast Dark Mode Rendering:** Automated luminance-based text contrast enforcement for Mermaid nodes in dark mode.
* **KaTeX Chemical Equations (`mhchem`):** Integrated official `katex/contrib/mhchem` extension into both the React desktop renderer and headless validation suite for native chemical formula rendering (e.g. `\ce{C4H10 -> 2 C2H5}`).
* **HTML Comparison Escaping:** Fixed bare less-than numerical comparisons (`< 0.2s`, `< 10%`) to prevent browser HTML parsers from mistaking comparisons for invalid HTML tags.

#### 3. Desktop UI & Onboarding Polish
* **Helpful Empty State:** Added an intuitive Empty State to the sidebar when no topics are installed, with an embedded one-click **`[ Open Curriculum Store ]`** button.
* **Visual Documentation:** Added a comprehensive visual guide in `README.md` explaining the App Shell + Modular SynPack architecture and 4 distinct installation paths.

#### 4. Infrastructure & Verification
* **Content Linter:** All 2,945 curriculum files pass the linter (complete final sentences, required sections, balanced code blocks).
* **Headless Render Validation:** Verified 133,544 KaTeX math formulas and 3,172 Mermaid diagrams through headless browser parsers (`validate_render.mjs`).
* **Automated Test Suite:** 59 / 59 Pytest tests passing (100%).

---

## [1.0.0] - 2026-11-13

### Summary
Initial production release of **Synapse** — the AI-native engineering and polymath learning workbench. Synapse combines textbook-depth masterclass curricula with an interactive Socratic AI Mentor, an embedded PTY terminal with host and sandbox execution modes, a responsive Cytoscape knowledge graph, and distributed multi-node inference clustering.

Curriculum domains are distributed modularly via the Synapse Package Manager (`synpack/v1`), shipping with the complete core Computing masterclass suite and enabling additional domain and localized language bundles as modular add-ons.

---

### Key Features & Architectural Highlights

#### 1. Socratic Workbench & Desktop Shell
* **Native Desktop Shell (macOS arm64):** Production Electron shell orchestrating native window lifecycle, menu bar controls, and automatic FastAPI backend sidecar management.
* **Interactive Terminal Drawer:**
  * Dual-mode terminal supporting both native Host OS execution and isolated Docker sandboxes (`Dockerfile.sandbox`).
  * Resilient PTY line discipline enabling `ICRNL` translation (`\r` $\rightarrow$ `\n`), ensuring instant execution on Enter keystrokes.
  * Real-time ANSI and OSC terminal escape sequence sanitization to prevent prompt redraw loops.
  * Host safety guard intercepting high-risk commands (`rm -rf /`, `mkfs`, fork bombs) until explicit confirmation is provided.
* **Multilingual Socratic AI Mentor:**
  * Context-aware conversational tutor automatically grounded in the active lesson, syllabus invariants, and terminal buffer.
  * Exact command tracking (`LAST_TERMINAL_COMMAND`) to diagnose terminal inputs without confusing commands with output text.
  * Full localization across 5 languages (English, Čeština, Deutsch, Español, Русский) with prompt-level language mandate injection.
* **Theme & Appearance Engine:**
  * 7 curated base themes (Default Dark, Cyberpunk, Forest, Monokai, Nord, Midnight, Paper White).
  * 5 accent color options (Indigo, Amber, Rose, Emerald, Cyan), typography choices (Sans, Serif, Mono), and reader line-height scaling.
  * Redesigned compact domain sort toggle with alphabetical and progress-oriented sorting modes.
* **System & Maintenance Dashboard:**
  * Dedicated System & Maintenance tab in Settings for runtime data cleanup and one-click lesson completion progress reset.

#### 2. Learning Engine & Distributed Inference
* **Multi-Node Cluster & Cloud Gateway:**
  * Seamlessly connects to local Ollama clusters (`127.0.0.1`, LAN nodes) and low-latency cloud gateways routed to Anthropic Claude Sonnet & Opus.
  * Dynamic cluster host normalization and node-specific model pinning saved to `.synapse_node_pins.json`.
* **Parallel Content Enhancement Pipeline (`enhancer.py`):**
  * Concurrent thread pool engine with automated exponential backoff retries and 600-second socket timeouts to handle massive 8,192-token masterclass files.
* **Pre-Commit Gatekeeper & Semantic Linter (`linter.py`):**
  * Pre-save validation stripping outer code fences (` ```markdown `).
  * Automated Mermaid subgraph ID normalization (`subgraph sub_id ["Title"]`).
  * Cross-domain bleed and template stub detection blocking generic boilerplate or misplaced toolchains.

#### 3. Curriculum & Package Store Architecture
* **Computing Masterclass Suite:** 45 complete courses (238 files) at textbook depth, featuring C/Rust kernel diagnostics, distributed Raft consensus, and production Kubernetes manifests.
* **Dedicated Infrastructure Labs:** Custom operational verification labs for Cloud Native (`containerd`, OCI, Envoy), SRE (SLI/SLO error budgets, Prometheus, Chaos Mesh), DevOps (BuildKit, Trivy, Argo CD), and Systems Automation (Ansible, Terraform).
* **Modular Add-On Store (`synpack/v1`):** Complete decoupling of curriculum data from the workbench runtime, enabling curriculum expansion packs and localized translation trees to be packaged, verified, and installed via Synapse Package Manager.

---
