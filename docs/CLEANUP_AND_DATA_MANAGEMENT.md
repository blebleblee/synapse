# Clean Packaging & Workspace Data Management

To ensure Synapse can be shared or shipped as a clean, unpolluted application without accidentally wiping custom content authored by users, Synapse enforces strict separation between **permanent curriculum assets** and **transient runtime state**.

---

## 1. Data Classification Matrix

| Category | Storage Path | Committed to Git? | Cleaned on Reset? | Examples |
| :--- | :--- | :--- | :--- | :--- |
| **Authored Curriculum** | `topics/{domain}/{discipline}/{topic}/*.md` | **Yes** (Tracked) | **NEVER** | Masterclasses, operational labs, syllabi |
| **Interactive Chat Sessions** | `topics/**/sessions/`, `topics/.workspace_sessions/` | **No** (Ignored) | Optional / Yes | Dialogue with Socratic AI mentor |
| **Generated Flashcard Decks** | `topics/**/flashcards.csv` | Optional (Ignored) | Optional | Anki spaced-repetition CSV decks |
| **Exported Handbooks & Packs** | `exports/` | **No** (Ignored) | Yes | Compiled `.pdf` / `.synpack` bundles |
| **Settings & Mastery DB** | `data/synapse.db` | **No** (Ignored) | Safe Reset | Spaced-repetition intervals, theme |

---

## 2. Cleaning Transient Data via CLI

Synapse includes a built-in clean command to clear chat logs, flashcard caches, and export files without touching your authored lessons:

```bash
# Clean all temporary AI chat sessions
./bin/synapse clean --sessions

# Clean exported .synpack packages and handbook markdown exports
./bin/synapse clean --exports

# Clean all transient runtime data (sessions + exports + logs)
./bin/synapse clean --all
```

---

## 3. Shipping / Open-Sourcing Verification

Before creating a release candidate or pushing to a public repository, verify:
1. `git status` shows no untracked `.db`, `.log`, or `sessions/` directories.
2. `tests/test_taxonomy_compliance.py` passes completely with `pytest tests/`.
3. Private API keys and local IPs are stored solely in your private `.env` or local SQLite database, never in source files.
