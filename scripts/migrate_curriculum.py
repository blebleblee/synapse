import os
import shutil
import re
from pathlib import Path

TOPICS_DIR = Path("topics")

def migrate_curriculum():
    print("[*] Starting curriculum flattening migration...")
    
    # 1. Map for renaming legacy filenames
    rename_map = {
        "FOUNDATION.md": "lesson_01_foundations.md",
        "LESSON.md": "lesson_02_mechanics.md",
        "LABS.md": "labs.md",
        "SUMMARY.md": "summary.md"
    }

    # Walk through all directories
    for unit_dir in TOPICS_DIR.rglob("*"):
        if not unit_dir.is_dir():
            continue
            
        # Ignore hidden/system dirs
        if unit_dir.name.startswith("."):
            continue

        # Migrate files found in this directory
        for f in unit_dir.iterdir():
            if f.is_file() and f.name.upper() in rename_map:
                new_name = rename_map[f.name.upper()]
                target = unit_dir / new_name
                # If target doesn't exist, rename
                if not target.exists():
                    f.rename(target)
                    print(f"  [Renamed] {f} -> {target}")
                else:
                    # If target exists (e.g. lesson_01 exists), delete legacy
                    f.unlink()
                    print(f"  [Deleted] {f} (redundant)")

        # Move files from subdirectories to unit root (flattening)
        # e.g., topics/computing/.../advanced/LESSON.md -> topics/computing/.../lesson_03_advanced.md
        if unit_dir.name in ["beginner", "intermediate", "advanced"]:
            parent = unit_dir.parent
            for f in unit_dir.iterdir():
                if f.is_file():
                    # Map leveled dir to lesson suffix
                    suffix = unit_dir.name
                    new_name = f"lesson_{suffix}.md"
                    target = parent / new_name
                    
                    if not target.exists():
                        f.rename(target)
                        print(f"  [Flattened] {f} -> {target}")
                    else:
                        f.unlink()
                        print(f"  [Deleted] {f} (redundant)")
            
            # Remove leveled dir if empty
            if not any(unit_dir.iterdir()):
                unit_dir.rmdir()
                print(f"  [Removed Dir] {unit_dir}")

    # Remove numbered subdirectories (01_*, etc)
    for unit_dir in TOPICS_DIR.rglob("*"):
        if unit_dir.is_dir() and re.match(r"^\d{2}_", unit_dir.name):
            # Move contents to parent
            parent = unit_dir.parent
            for f in unit_dir.iterdir():
                shutil.move(str(f), str(parent / f.name))
            shutil.rmtree(unit_dir)
            print(f"  [Flattened Dir] {unit_dir} -> {parent}")

    print("[✔] Curriculum flattening complete.")

if __name__ == "__main__":
    migrate_curriculum()
