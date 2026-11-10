# AI Learning Workspace

Welcome to your AI-native learning repository. This workspace uses the filesystem as a database for learning topics, utilizing dynamic AI personas based on the directory you are working in.

## Structure

- `/topics`: The root of your learning modules.
  - `/topics/business_and_economics`: Micro/macroeconomics, corporate finance, market trading, and wealth management (Persona: Senior Economist & Quantitative Financial Analyst).
  - `/topics/computing_and_engineering`: Software engineering, infrastructure/cloud, hardware circuits, AI, cybersecurity, and robotics (Persona: Principal Systems Architect and Senior Staff Engineer).
  - `/topics/formal_sciences`: Pure mathematics, applied mathematics, logic, and discrete structures (Persona: Professor of Mathematics and Formal Logic).
  - `/topics/natural_sciences`: Physics, chemistry, and biological sciences (Persona: Research Scientist and Natural Philosophy Scholar).
  - `/topics/arts_and_humanities`: Music theory & performance, visual arts, global history, and philosophy (Persona: Polymath Scholar, Master Musician, and Humanities Mentor).
  - `/topics/hobbies_and_crafts`: LEGO engineering, fine woodworking, and 3D printing (Persona: Master Builder, Woodworker, and Fabrication Craftsman).
- `/scripts`: Utility scripts for managing the workspace and automated curriculum generation.

## Learning Engine CLI (`bin/learning`)

The workspace includes a command-line interface for managing topics, generating lessons, and starting tutor sessions:

```bash
# Launch the Interactive Web Workbench (UI + AI Chat + PTY Terminal on http://127.0.0.1:8000)
bin/learning serve

# Check completion stats across all domains and active LLM engines
bin/learning status

# View the hierarchical curriculum tree with status badges ([FLB])
bin/learning tree
bin/learning tree --domain computing_and_engineering

# Add a new topic or subtopic (automatically updates SYLLABUS.md)
bin/learning add computing_and_engineering infrastructure_and_ops ebpf --title "Extended Berkeley Packet Filter (eBPF)"

# Generate Foundation, Lesson, and Labs for any subtopic (uses local Ollama or Gemini)
bin/learning generate ebpf
bin/learning generate game_theory --model qwen3:4b

# Start an interactive terminal Socratic session with domain persona and context loaded
bin/learning chat ebpf
```

### Interactive Web Workbench (`bin/learning serve`)

Running `bin/learning serve` boots the unified engineering dashboard at `http://127.0.0.1:8000`:
- **Topic Explorer (Left Pane):** Real-time search, category breakdown, status indicators (`[FLB]`), and a "+ New Topic" modal.
- **Lesson & Knowledge Viewer (Center Pane):** Tabbed reader switching between `Foundation`, `Technical Lesson`, and `Operational Labs` with live one-click "Generate" capability.
- **Socratic AI Tutor Chat (Right Pane):** Dynamically mounts the active directory's `GEMINI.md` persona and subtopic lesson context into Ollama or Gemini for deep interactive dialogue.
- **Integrated Terminal (Bottom Drawer):** Full interactive PTY shell (`bash`/`zsh` via WebSockets and `@xterm/xterm`) for running lab commands directly in the workspace.

### Module Content Structure

Each subtopic module follows a 3-tier learning model:
- `FOUNDATION.md`: Core mental models, intuition, essential terminology, visual architecture diagrams, and common misconceptions.
- `LESSON.md`: In-depth theoretical mechanics, equations/formulas, production-grade manifests or code, and failure domains.
- `LABS.md`: Step-by-step hands-on operational lab with concrete verification commands and debugging scenarios.

## Workflow

1. **Start a Session:** Navigate to a topic folder in your terminal (or tell the AI to look there).
2. **Learn & Experiment:** Discuss the topic. The AI will write files (manifests, sheet music) directly to the repository and execute commands to demonstrate concepts.
3. **Save Session:** When finished, ask the AI to summarize the discussion and save it in the `sessions/` folder of that topic.
4. **Compile Artifacts:** When a topic is mastered, the session histories can be compiled into a final markdown guide in the `artifacts/` folder.
