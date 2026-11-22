#!/usr/bin/env python3
"""
Synapse Single Source of Truth Version Bumper
Atomically synchronizes release version across all workspace configuration files:
- VERSION (root truth)
- pyproject.toml
- app/desktop/package.json
- app/frontend/package.json
- app/frontend/src/components/SettingsModal.tsx
- app/desktop/package-lock.json, app/frontend/package-lock.json
"""

import sys
import re
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

def bump_version(new_ver: str):
    new_ver = new_ver.strip().lstrip("v")
    if not re.match(r"^\d+\.\d+\.\d+$", new_ver):
        print(f"[✘] Invalid semantic version format: '{new_ver}'. Expected 'X.Y.Z' (e.g. '1.2.0')")
        sys.exit(1)

    print(f"[*] Bumping Synapse workspace to version: v{new_ver}")

    # 1. Update VERSION file
    ver_file = WORKSPACE_ROOT / "VERSION"
    ver_file.write_text(f"{new_ver}\n", encoding="utf-8")
    print(f" [✔] Updated {ver_file.relative_to(WORKSPACE_ROOT)}")

    # 2. Update pyproject.toml
    pyproject = WORKSPACE_ROOT / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        updated = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_ver}"', content)
        pyproject.write_text(updated, encoding="utf-8")
        print(f" [✔] Updated {pyproject.relative_to(WORKSPACE_ROOT)}")

    # 3. Update app/desktop/package.json
    desktop_pkg = WORKSPACE_ROOT / "app" / "desktop" / "package.json"
    if desktop_pkg.exists():
        data = json.loads(desktop_pkg.read_text(encoding="utf-8"))
        data["version"] = new_ver
        desktop_pkg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f" [✔] Updated {desktop_pkg.relative_to(WORKSPACE_ROOT)}")

    # 4. Update app/frontend/package.json
    frontend_pkg = WORKSPACE_ROOT / "app" / "frontend" / "package.json"
    if frontend_pkg.exists():
        data = json.loads(frontend_pkg.read_text(encoding="utf-8"))
        data["version"] = new_ver
        frontend_pkg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f" [✔] Updated {frontend_pkg.relative_to(WORKSPACE_ROOT)}")

    # 5. Update app/frontend/src/components/SettingsModal.tsx
    settings_modal = WORKSPACE_ROOT / "app" / "frontend" / "src" / "components" / "SettingsModal.tsx"
    if settings_modal.exists():
        content = settings_modal.read_text(encoding="utf-8")
        updated, n = re.subn(r'Synapse v\d+\.\d+\.\d+', f'Synapse v{new_ver}', content)
        if n == 0:
            print(f"[✘] No 'Synapse vX.Y.Z' label found in {settings_modal.relative_to(WORKSPACE_ROOT)}")
            sys.exit(1)
        settings_modal.write_text(updated, encoding="utf-8")
        print(f" [✔] Updated {settings_modal.relative_to(WORKSPACE_ROOT)}")

    # 6. npm lock files carry the package's own version too
    for lock in (WORKSPACE_ROOT / "app" / "desktop" / "package-lock.json",
                 WORKSPACE_ROOT / "app" / "frontend" / "package-lock.json"):
        if lock.exists():
            data = json.loads(lock.read_text(encoding="utf-8"))
            data["version"] = new_ver
            if "" in data.get("packages", {}):
                data["packages"][""]["version"] = new_ver
            lock.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f" [✔] Updated {lock.relative_to(WORKSPACE_ROOT)}")

    print(f"\n[✔] Synapse version successfully synchronized to v{new_ver} across all subsystems!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        ver_file = WORKSPACE_ROOT / "VERSION"
        target = ver_file.read_text(encoding="utf-8").strip() if ver_file.exists() else "1.2.0"
    bump_version(target)
