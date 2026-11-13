# Socratic Workbench & UI Architecture Guide

The Synapse Socratic Workbench is an interactive, distraction-free environment for polymath study, practical terminal verification, and AI-assisted inquiry.

---

## 1. Architectural Components

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  TOPBAR: Topic Breadcrumbs ── Level Selector ── Search (⌘K) ── Settings ⚙    │
├─────────────────┬───────────────────────────────────────────┬────────────────┤
│ TOPIC TREE      │ LESSON VIEWER                             │ SOCRATIC CHAT  │
│ 12 Domains      │ • Multi-Stage Reader (KaTeX, Mermaid)     │ • Active Lesson│
│ 80 Disciplines  │ • Code Blocks + Smart Command Synthesizer │   Grounding    │
│ • Sort (A-Z/%)  │ • Bilingual Polyglot Side-by-Side         │ • Terminal Log │
│ • Multi-Lesson  │ • Interactive Socratic Quiz & Flashcards  │   Diagnosis    │
│   Expansion     │ • Zoomable Architecture Diagrams          │ • Multilingual │
├─────────────────┴───────────────────────────────────────────┴────────────────┤
│ INTEGRATED PTY TERMINAL DRAWER (Host Shell / Docker Sandbox / Kubernetes Pod) │
│ In-Stream Safety Guard ── Auto-Reconnect ── Resilient Dimension Caching      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Smart Terminal Command Synthesizer

Rather than forcing users to blindly copy-paste complex multi-line snippets into their terminal, the **Smart Command Synthesizer** (`commandSynthesizer.ts`) inspects the syntax of code blocks and automatically produces self-contained, safe executions:

| Language | Raw Snippet | Synthesized Execution Wrap | Button Label |
| :--- | :--- | :--- | :--- |
| **SQL** | `SELECT * FROM pg_stat_activity;` | Wraps in `psql -c "..."` or `sqlite3` temporary file runner | `▶ Execute SQL` |
| **Kubernetes YAML** | `apiVersion: apps/v1\nkind: Deployment...` | Writes to `/tmp/synapse_manifest.yaml` and executes `kubectl apply -f /tmp/synapse_manifest.yaml` | `▶ Apply Manifest` |
| **Python** | `import torch\nprint(torch.cuda.is_available())` | Executes via active virtual environment `.venv/bin/python3 -c "..."` | `▶ Run Python` |
| **C / C++** | `#include <stdio.h>\nint main()...` | Saves to `/tmp/synapse_prog.c`, compiles with `gcc -O2`, and executes `/tmp/synapse_prog` | `▶ Compile & Run` |
| **Rust** | `fn main() { println!("ok"); }` | Saves to `/tmp/synapse_prog.rs`, compiles with `rustc -O`, and runs | `▶ Compile & Run` |
| **JSON** | `{"cluster": {"nodes": 3}}` | Writes to `/tmp/synapse_data.json` and pretty-prints with `jq .` | `▶ Inspect JSON` |
| **Bash / Shell** | `docker ps -a` | Executes directly in active terminal PTY session | `▶ Run in Terminal` |

---

## 3. Socratic AI Mentor & Multilingual Engine

### A. Context Grounding
When you submit an inquiry to the AI Mentor, the backend automatically extracts:
1. **Active Curriculum Context:** Up to 8,000 characters of the lesson or lab currently visible on your screen.
2. **Student's Last Executed Command (`LAST_TERMINAL_COMMAND`):** The exact command you entered into the terminal before pressing Enter.
3. **Live Terminal Console Output:** The last 40 lines of console output, filtered to strip OSC escape sequences and resolved for backspaces.

### B. Multilingual i18n
Synapse includes a polyglot dictionary (`i18n.ts`) supporting **English, Čeština, Deutsch, Español, and Русский**.
When a language is selected in **Settings → Theme & Appearance**:
1. All UI labels, tabs, headers, modal instructions, search placeholders, and buttons immediately translate.
2. An explicit language directive is injected into the AI Mentor's prompt:
   ```text
   MANDATORY LANGUAGE DIRECTIVE: The student has selected Czech (Čeština). You MUST converse, mentor, and formulate all responses strictly in natural, fluent Czech. Preserve exact technical keywords, CLI flags, and code syntax, but formulate all explanations, questions, and guidance in Czech.
   ```
   The mentor converses fluently in your language while preserving exact command flags and syntax.

---

## 4. Deep Theme & Appearance Engine

Customization is powered by scoped CSS Custom Properties applied directly to `document.documentElement`:

* **Color Scheme Palettes (`data-theme`):**
  * `studio` — Studio Obsidian (Deep OLED Carbon & Gold)
  * `github_dimmed` — GitHub Dimmed (Slate Navy & High Contrast)
  * `nordic` — Nordic Frost (Polar Night & Arctic Cyan)
  * `monokai` — Monokai Pro (Toasted Espresso & Neon Pastels)
  * `dracula` — Dracula Noir (Deep Violet Indigo & Pink)
  * `solarized` — Solarized Dark (Teal Oceanic & Warm Amber)
  * `titanium` — Titanium Daybreak (Clean High-Contrast Light Mode)
* **Accent Highlights (`data-accent`):** Amber Gold, Electric Cyan, Matrix Emerald, Royal Amethyst, Crimson Rose.
* **Reader Typography (`data-fontfamily`):** Modern Sans (Inter), Academic Serif (Charter/Merriweather), Technical Mono (JetBrains Mono).
* **Reader Line Spacing (`data-lineheight`):** Compact (1.45), Balanced (1.68), Relaxed (1.92).

---

## 5. Visual DAG Knowledge Graph

Accessible via the toolbar or pressing **⌘G**:
* **Visual DAG Pipeline View:** Color-coded stages representing domain clusters, interactive cytoscape nodes, prerequisite dependency arrows, and direct study jumps.
* **Timeline Step View:** Linear, ordered progression for sequential learners.
