# Curriculum Generation, Models & Live Monitoring Guide

Synapse features an autonomous, multi-tier curriculum generation and enhancement engine designed to author textbook-grade technical masterclasses without hallucination or conversational fluff.

---

## 1. Generation Pipeline Architecture

The generation engine operates through two distinct modes:

### A. Autonomous Drafting Mode (New Topics)
When drafting an unwritten syllabus node, the engine executes a multi-stage sequential pipeline:
1. **Dynamic Curriculum Scoping:** Queries the LLM with the canonical 3-level taxonomy context (`domain/discipline/topic`) to determine the exact number of sequential lessons (typically 4–6) and custom descriptive titles.
2. **Parallel Module Drafting:** Concurrently drafts all lessons and operational labs (`labs.md`) using a `ThreadPoolExecutor` (3 concurrent workers for Claude or distributed across all online Ollama cluster nodes).
3. **Adversarial Peer Review:** Passes the drafted markdown to an independent reviewer model (e.g. `deepseek-r1:32b`, `qwen2.5-coder:32b`, or Claude Opus) to fact-check APIs, verify invariants, and refine prose.
4. **Mermaid Diagram Normalization:** Automatically runs all generated code through `repair_mermaid_diagrams()` to ensure strict `subgraph sub_id ["Title"]` and quoted label compliance before disk writes.
5. **Git Versioning & Remote Push:** Commits the completed topic directory (`gen(<topic_id>): masterclass curriculum`) and automatically pushes to the remote repository in real time.

### B. Deep Enhancement Mode (`--enhance`)
Enhancement mode audits and upgrades existing curriculum units:
- Feeds each existing lesson/lab to **Claude Opus 5.5** under an elite staff-engineer / MIT-Press author persona.
- Expands theoretical rigor, adds robust Mermaid architecture diagrams, inserts production-grade code (C, Rust, Go, Python, SQL), and eliminates conversational filler.
- Enforces defensive outer code fence stripping so markdown files never render as raw code boxes.
- Commits as `enhance(<topic_id>): masterclass curriculum` and syncs with origin.

---

## 2. CLI Execution & Flags

All generation workflows are orchestrated through `scripts/generate_all.py`:

```bash
# Enhance all existing topics in the computing domain
python3 scripts/generate_all.py --domain computing --enhance

# Draft all missing topics across all 12 domains using Claude Opus 5.5
python3 scripts/generate_all.py --provider anthropic

# Override specific model target
python3 scripts/generate_all.py --provider anthropic --model claude-sonnet-5

# Use local multi-node Ollama cluster
python3 scripts/generate_all.py --provider ollama

# Target a specific domain (e.g., formal_sciences)
python3 scripts/generate_all.py --domain formal_sciences --provider auto
```

---

## 3. Real-Time Generation Monitoring

Synapse provides three complementary methods to monitor active background generation:

### Option A: Live Terminal Dashboard (`monitor.py --watch`)
```bash
python3 scripts/monitor.py --watch
```
Renders an auto-updating visual dashboard:
* **Engine Status & PID:** Displays active process and worker thread count.
* **Progress Bar:** Real-time course completion counter (`X/45` courses, `%`).
* **Active In-Flight Changes:** Real-time git insertion/deletion counters (e.g. `+3,322 lines` added).
* **Live Engine Output:** Tails the last 8 lines emitted from the generator.
* **Recent Commits Stream:** Timestamped list of published and pushed masterclasses.

### Option B: Raw Engine Log Stream (`tail -f`)
```bash
tail -f generator.log
```
Every token stream dispatch, worker thread completion, elapsed second, and git push event is mirrored with line buffering to `generator.log`.

### Option C: Snapshot Query
```bash
python3 scripts/monitor.py
```
Outputs a one-time terminal snapshot of active workers and recent commits.

---

## 4. Supported Models & Gateways

| Provider / Model | Latency | Primary Role | Configuration Key |
| :--- | :--- | :--- | :--- |
| **`claude-opus-5-5`** | **~3.1s** | **Primary Author & Reviewer** (MIT Press standard) | `ANTHROPIC_MODEL=claude-opus-5-5` |
| **`claude-sonnet-5`** | **~5.1s** | High-throughput drafting & code blocks | `ANTHROPIC_MODEL=claude-sonnet-5` |
| **`qwen2.5-coder:32b`** | Local / Metal | High-precision local code & lab authoring | Pinned in `.synapse_node_pins.json` |
| **`deepseek-r1:32b`** | Local / CUDA | Adversarial peer reviewer & logic auditor | Pinned in `.synapse_node_pins.json` |
| **`qwen2.5-coder:7b`** | Local / Laptop | Fast Socratic Mentor conversational chat | Default local fallback |
