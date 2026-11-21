# Custom Domains, Data Persistence & Curriculum Packaging Guide

## Architecture Overview

Synapse is designed with an **offline-first, local-persistence architecture**. All user modifications, custom curricula, mentor interactions, and generated lessons are stored permanently on your local file system and are **never overwritten** when upgrading the Synapse desktop application (`.dmg` or portable bundle).

---

## 1. Storage Layout & Data Persistence

Your workspace separates application code from persistent user data:

| Content Type | Location | Persistence Behavior |
| :--- | :--- | :--- |
| **Curriculum Topics** | `topics/{domain}/{discipline}/{subtopic}/` | Markdown lesson files (`lesson_*.md`) and operational labs (`labs.md`). Fully version-controlled and preserved across app updates. |
| **SQLite Database** | `data/synapse.db` | Contains user authentication hashes, mastery status, and cluster ping records. Preserved across updates. |
| **User Configuration** | `~/.config/synapse/env` | Contains cluster endpoints, host pins, and encrypted API keys. Never touched by app installers. |
| **Audio & Translation Cache** | `.cache/` or `data/audio_cache/` | Ephemeral caching for neural TTS voice synthesis and bilingual translations. Can be safely vacuumed in Settings. |
| **Packaged Archives** | `exports/packages/*.synpack` | Self-contained, portable knowledge packages. |

---

## 2. Creating a Custom Domain via CLI

You can create an entirely custom domain (e.g. `robotics`, `astronomy`, `quantum_computing`) and author or AI-synthesize its entire curriculum from the terminal.

### Step 1: Add a New Topic to the Hierarchy
Run the `synapse` CLI executable from the project root:

```bash
# Syntax: bin/synapse add <domain> <discipline> <topic_slug> --title "Display Title"
bin/synapse add robotics autonomous_systems slam_navigation --title "Simultaneous Localization and Mapping (SLAM)"
```

This automatically:
1. Creates the canonical directory structure: `topics/robotics/autonomous_systems/slam_navigation/`
2. Registers the entry into `topics/robotics/SYLLABUS.md`.
3. Re-indexes the workspace topic tree for the UI.

### Step 2: Generate the Masterclass Curriculum with AI
Instruct your local or cluster LLM to generate the full set of numbered lessons and operational labs:

```bash
# Generate using your primary local Ollama model
bin/synapse generate robotics autonomous_systems slam_navigation

# Or specify a particular model and provider
bin/synapse generate robotics autonomous_systems slam_navigation --provider ollama --model qwen2.5-coder:32b --force
```

This produces:
- `lesson_01_foundations_and_invariants.md`
- `lesson_02_architecture_and_mechanics.md`
- `lesson_03_deep_dive_and_concurrency.md`
- `lesson_04_performance_monitoring_and_tuning.md`
- `labs.md` (executable drills and operational scenarios)

---

## 3. Packaging & Exporting Custom Domains (`.synpack`)

To backup your custom domain or share it with other users, bundle it into an optimized `.synpack` archive.

```bash
# Package the custom domain into exports/packages/robotics.synpack
bin/synapse pack robotics
```

The resulting `.synpack` contains:
- Complete markdown curriculum files for all disciplines and topics.
- Domain `SYLLABUS.md` and domain instructions (`GEMINI.md`).
- Integrity SHA-256 manifest and taxonomy metadata.

---

## 4. Restoring & Installing a `.synpack`

On a new computer, reinstalled operating system, or clean Synapse instance:

### Option A: Via the Desktop UI
1. Open **Settings** (gear icon in sidebar).
2. Navigate to the **Storage & Addons** tab.
3. In the **Import Knowledge Package** section, click **Select `.synpack` File** and choose your archive.
4. Synapse extracts the curriculum into your `topics/` directory and immediately updates the Topic Tree.

### Option B: Via the Terminal
```bash
# Install any .synpack archive directly into the local workspace
bin/synapse install /path/to/robotics.synpack
```

---

## 5. Clean App Upgrades Guarantee

When you download a new version of the macOS DMG (`Synapse-Workbench-1.2.x-arm64.dmg`):
1. Dragging the new `Synapse Workbench.app` to `/Applications` replaces the Electron shell and Python runtime.
2. Your user directory (`~/Library/Application Support/Synapse Workbench/` and `~/.config/synapse/`) and workspace repository (`topics/` and `data/synapse.db`) remain untouched.
3. All custom topics, mentor notes, progress, and mastery ratings are automatically preserved.
