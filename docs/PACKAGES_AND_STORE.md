# SynPack Curriculum Distributions & Addon Store

Synapse curriculum topics are fully modular and distributable as standalone, compressed `.synpack` archives. This allows learners and institutions to export authored masterclasses, share them offline, and sideload them on any Synapse instance across **macOS**, **Windows**, and **Linux**.

---

## 1. What is a `.synpack`?

A `.synpack` is a gzip-compressed archive (`.tar.gz`) containing:
1. **`manifest.json`**: An integrity descriptor documenting the domain, discipline, topic title, lesson count, lab count, and export timestamp.
2. **`topics/`**: The complete canonical markdown masterclasses (`lesson_01_*.md` ... `labs.md`).

Because `.synpack` files adhere strictly to the 3-level taxonomy (`topics/{domain}/{discipline}/{topic}/`), they unpack safely into the root workspace without overwriting unrelated courses.

---

## 2. Managing Packages via the Workbench UI

Open **Settings ⚙ → Curriculum Store & Addons** (or click the `<Package />` icon in the sidebar header):

* **Export Any Domain:** Click **Export** on any domain card to compile and download its `.synpack` file immediately.
* **1-Click Install / Register:** Click **Install** on an available domain to activate and register it in local topics.
* **1-Click Uninstall:** Click **Uninstall** to unregister the domain package from your local catalog.
* **Sideload Custom Package:** Drag and drop or click **Sideload .synpack** to upload and extract an external topic pack into your workspace.

---

## 3. Package Management via CLI

You can also manage `.synpack` bundles directly via Python:

```python
from learning_engine.packages import export_topic_pack, install_topic_pack, list_installed_packs

# Export a domain into exports/packages/{domain}.synpack
pack_path = export_topic_pack("computing")

# Install / sideload a .synpack bundle
result = install_topic_pack(pack_path)

# List all installed packages
installed = list_installed_packs()
```
