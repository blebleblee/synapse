# SynPack Curriculum Distributions, Addon Store & Private Packages

Synapse curriculum topics are fully modular and distributable as standalone, compressed `.synpack` archives. This allows learners, engineering teams, and institutions to author private masterclasses, distribute them offline, and install them into any Synapse instance across **macOS**, **Windows**, and **Linux**.

---

## 1. What is a `.synpack`?

A `.synpack` archive is a gzip-compressed tarball (`.tar.gz`) containing:
1. **`manifest.json`**: An integrity descriptor documenting the domain, discipline, topic title, lesson count, lab count, and export timestamp.
2. **`topics/`**: Canonical Markdown masterclasses organized strictly by the 3-level taxonomy (`topics/{domain}/{discipline}/{topic}/` containing `lesson_01_*.md` ... `labs.md`).

Because `.synpack` packages adhere to this taxonomy, they unpack safely into the curriculum workspace without overwriting unrelated courses or corrupting other domains.

```text
my_private_domain.synpack (tar.gz)
├── manifest.json
└── topics/
    └── my_private_domain/
        ├── GEMINI.md
        ├── SYLLABUS.md
        └── discipline_a/
            └── topic_1/
                ├── lesson_01_foundation.md
                └── labs.md
```

---

## 2. Creating Private SynPacks

You can compile any domain folder into a `.synpack` archive, including your own private domains. The complete pack (`synapse_complete_curriculum.synpack`) contains only the 12 core domains. Packs never include chat sessions, `CURRICULUM_BLUEPRINT.md` files, or tracks that git ignores.

### Via Workbench UI
1. Navigate to **Settings ⚙ → Curriculum Store & Addons** (or the `<Package />` icon).
2. Click **Export** on any domain card.
3. The browser will download `{domain}.synpack`.

### Via Python API
```python
from learning_engine.packages import export_topic_pack

# Export an individual domain to exports/packages/{domain}.synpack
pack_path = export_topic_pack("computing")

# Export the 12 core domains as one bundle:
# exports/packages/synapse_complete_curriculum.synpack
global_pack = export_topic_pack("all")
```

### Via the command line
```bash
bin/synapse pack export computing              # one domain
bin/synapse pack export my_private_domain      # works for private domains too
bin/synapse pack export all -o /tmp/packs      # complete core pack, custom folder
```

> **Publishing:** private packs are for your own use or a private registry (`SYNAPSE_PACKAGE_REGISTRY`). The project's release scripts run `scripts/check_release_packs.py`, which refuses any pack that contains non-core domains or files not committed to git.

---

## 3. Installing Private SynPacks

Synapse supports multiple installation methods depending on your environment:

### Method A: Workbench UI Sideloading (Recommended for Desktop / WebUI)
1. Open **Settings ⚙ → Storage & Addons**.
2. Locate the **Sideload / Upload Package** zone.
3. Select or drag-and-drop your private `.synpack` file.
4. The backend verifies the archive, extracts files into `TOPICS_DIR`, and registers the package in the local SQLite database (`synapse.db`).

### Method B: Python Engine
```python
from pathlib import Path
from learning_engine.packages import install_topic_pack

pack_path = Path("/path/to/my_private_domain.synpack")
result = install_topic_pack(pack_path)
print(result) # {'status': 'installed', 'domain': 'my_private_domain', 'manifest': {...}}
```

### Method C: Direct Filesystem Drop-in (Air-Gapped / Portable)
Because Synapse reads curriculum directly from the `topics/` directory on disk, you can extract the archive manually:
```bash
# Extract topics directory directly into your active topics location
tar -xzf my_private_domain.synpack -C /path/to/active/topics/ --strip-components=1 topics
```
Synapse will dynamically scan and index the new domain on next reload or via `GET /api/tree`.

---

## 4. Runtime Data Paths: WebUI vs. Local Binary vs. Desktop App

A critical question when using private packages is whether the **WebUI (`synapse serve`)**, **Electron Desktop App**, and **standalone local binaries** share the same data.

### Default Path Resolution Hierarchy

The active directories are determined at runtime by `learning_engine/security.py` and `app/desktop/src/main.js`:

| Runtime Mode | Default Workspace Root (`WORKSPACE_ROOT`) | Default Topics Directory (`TOPICS_DIR`) | Database Location (`DB_PATH`) |
| :--- | :--- | :--- | :--- |
| **CLI / WebUI** (`synapse serve` inside repo) | Repository root (`./`) | `<repo>/topics` | `<repo>/data/synapse.db` |
| **CLI / WebUI** (`synapse serve` outside repo) | `~/.synapse` | `~/.synapse/topics` | `~/.synapse/data/synapse.db` |
| **Packaged Desktop App (macOS)** | `~/Library/Application Support/Synapse` | `~/Library/Application Support/Synapse/topics` | `~/Library/Application Support/Synapse/data/synapse.db` |
| **Packaged Desktop App (Linux)** | `~/.config/Synapse` | `~/.config/Synapse/topics` | `~/.config/Synapse/data/synapse.db` |
| **Packaged Desktop App (Windows Installed)** | `%APPDATA%\Synapse` | `%APPDATA%\Synapse\topics` | `%APPDATA%\Synapse\data\synapse.db` |
| **Portable Windows App (`.exe`)** | Directory containing the `.exe` (if `topics/` or portable env exists) | `<portable_dir>\topics` | `<portable_dir>\data\synapse.db` |
| **Standalone PyInstaller Binary** | Sibling directory containing `topics/`, else `cwd`, else `~/.synapse` | `<detected_root>/topics` | `<detected_root>/data/synapse.db` |

> **Key Takeaway:** By default, running `synapse serve` from source uses the repo directory, whereas running the installed Desktop application uses the operating system's `userData` folder. **They will not automatically share installed private packages or mastery records unless configured to point to a shared location.**

---

## 5. Unifying Data Across All Runtimes (WebUI, Desktop & Binaries)

To ensure that any package installed in the WebUI is instantly visible in the Desktop app and standalone CLI (and that lesson completion/mastery stays in sync), bind all runtimes to a single shared directory using environment variables.

### Priority Resolution Order
1. **`SYNAPSE_WORKSPACE`**: Overrides the base workspace path where `data/synapse.db`, `.cache/`, and `exports/` live.
2. **`SYNAPSE_TOPICS_DIR`**: Overrides the curriculum directory where markdown masterclasses live (defaults to `$SYNAPSE_WORKSPACE/topics`).

### Option 1: System-Wide Environment File (`~/.config/synapse/env`)
Synapse automatically loads `~/.config/synapse/env` on startup across all runtimes:
```bash
mkdir -p ~/.config/synapse
cat << 'EOF' >> ~/.config/synapse/env
SYNAPSE_WORKSPACE=/Users/shared/synapse_data
SYNAPSE_TOPICS_DIR=/Users/shared/synapse_data/topics
EOF
chmod 600 ~/.config/synapse/env
```

### Option 2: Environment Variables in Shell Profile
Add the following to your `~/.zshrc`, `~/.bashrc`, or Windows System Environment Variables:
```bash
export SYNAPSE_WORKSPACE="$HOME/.synapse"
export SYNAPSE_TOPICS_DIR="$HOME/.synapse/topics"
```

Once configured, installing a private SynPack through the WebUI, Desktop app, or terminal will write to the unified `~/.synapse/topics` and `~/.synapse/data/synapse.db`, giving all interfaces access to the exact same content.

---

## 6. Package Database Registration & Metadata

When a `.synpack` is installed via `install_topic_pack()` or the UI upload API (`/api/packages/install`):
1. Files are extracted to `$SYNAPSE_TOPICS_DIR/<domain>/...`.
2. Package metadata from `manifest.json` is registered in `synapse.db` under the `settings` table with key `pack:<domain>`.
3. The UI queries `GET /api/packages` to verify which packages are active and list their topic and lesson counts.

### Listing Installed Packages
To check active packages programmatically:
```python
from learning_engine.packages import list_installed_packs

packs = list_installed_packs()
for p in packs:
    print(f"Domain: {p.get('domain')} | Title: {p.get('title')} | Lessons: {p.get('lesson_count')}")
```
