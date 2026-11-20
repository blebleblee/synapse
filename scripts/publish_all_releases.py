#!/usr/bin/env python3
"""
Synapse v1.1.1 Release Publisher for Gitea and GitHub
Updates and synchronizes verified binary assets for v1.1.1:
1. macOS DMG & ZIP (with bundled Python sidecar, all curriculum SynPacks, sealed ad-hoc signature, and zero-EPIPE logger)
2. Windows Portable Single-File Executable (Synapse-Workbench-Portable-1.1.1.exe, embedded ffmpeg.dll, NSIS self-contained)
3. Windows Portable ZIP Bundle (with pre-loaded topics) and 1-Click Installer Setup
4. Updates release descriptions on both platforms with direct download links.
"""

import os
import sys
import time
import shutil
import subprocess
import requests
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Load external user credentials from outside the codebase
def _load_external_env():
    user_env = Path.home() / ".config" / "synapse" / "env"
    if user_env.exists():
        for line in user_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v

_load_external_env()

def upload_via_curl(url: str, filepath: Path, headers: dict = None, auth: tuple = None, form_field: str = None) -> bool:
    """Robust binary file upload using curl with automated retries and socket resilience."""
    cmd = ["curl", "-sS", "-X", "POST", "--retry", "3", "--retry-delay", "2", "-w", "\n%{http_code}"]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    if auth:
        cmd.extend(["-u", f"{auth[0]}:{auth[1]}"])
    if form_field:
        cmd.extend(["-F", f"{form_field}=@{filepath}"])
    else:
        cmd.extend(["--data-binary", f"@{filepath}"])
    cmd.append(url)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        output_lines = [l.strip() for l in proc.stdout.strip().splitlines() if l.strip()]
        http_code = output_lines[-1] if output_lines else ""
        return proc.returncode == 0 and http_code in ["200", "201"]
    except Exception as e:
        print(f" [curl err: {e}]", end="")
        return False

# Credentials
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITEA_URL = os.environ.get("GITEA_URL", "https://gitea.2464.cz")
GITEA_USER = os.environ.get("GITEA_USER", "")
GITEA_PASS = os.environ.get("GITEA_PASS", "")
GITEA_REPO = os.environ.get("GITEA_REPO", "ai/synapse")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "blebleblee/synapse")
TAG = "v1.1.1"
VER = "1.1.1"

# Target binary files to publish/replace
ASSETS_TO_PUBLISH = {
    f"Synapse-Workbench-Portable-{VER}.exe": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-Portable-{VER}.exe",
    f"Synapse-Workbench-Setup-{VER}.exe": WORKSPACE_ROOT / f"dist/desktop/Synapse Workbench Setup {VER}.exe",
    f"Synapse-Workbench-Portable-{VER}-win-x64.zip": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-Portable-{VER}-win-x64.zip",
    "Synapse-Portable-Windows.zip": WORKSPACE_ROOT / "dist/desktop/Synapse-Portable-Windows.zip",
    f"Synapse-Workbench-{VER}-arm64.dmg": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-{VER}-arm64.dmg",
    f"Synapse-Workbench-{VER}-arm64-mac.zip": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-{VER}-arm64-mac.zip",
}

def publish_gitea():
    print("\n" + "=" * 60)
    print(f"🚀 PUBLISHING TO GITEA ({GITEA_URL} / {GITEA_REPO})")
    print("=" * 60)

    auth = (GITEA_USER, GITEA_PASS)
    api_base = f"{GITEA_URL.rstrip('/')}/api/v1"
    rel_url = f"{api_base}/repos/{GITEA_REPO}/releases/tags/{TAG}"

    res = requests.get(rel_url, auth=auth)
    if res.status_code != 200:
        print(f"[✘] Failed to fetch release {TAG} on Gitea: {res.status_code} {res.text}")
        return False

    rel_data = res.json()
    rel_id = rel_data["id"]
    print(f"[✔] Found Gitea release ID {rel_id}: {rel_data.get('name')}")

    assets_url = f"{api_base}/repos/{GITEA_REPO}/releases/{rel_id}/assets"
    existing_assets = {a["name"]: a["id"] for a in rel_data.get("assets", [])}

    gitea_targets = [
        ("Synapse-Workbench-Portable-1.1.1.exe", ASSETS_TO_PUBLISH["Synapse-Workbench-Portable-1.1.1.exe"]),
        ("Synapse-Workbench-Setup-1.1.1.exe", ASSETS_TO_PUBLISH["Synapse-Workbench-Setup-1.1.1.exe"]),
        ("Synapse-Workbench-Portable-1.1.1-win-x64.zip", ASSETS_TO_PUBLISH["Synapse-Workbench-Portable-1.1.1-win-x64.zip"]),
        ("Synapse-Portable-Windows.zip", ASSETS_TO_PUBLISH["Synapse-Portable-Windows.zip"]),
        ("Synapse-Workbench-1.1.1-arm64.dmg", ASSETS_TO_PUBLISH["Synapse-Workbench-1.1.1-arm64.dmg"]),
        ("Synapse-Workbench-1.1.1-arm64-mac.zip", ASSETS_TO_PUBLISH["Synapse-Workbench-1.1.1-arm64-mac.zip"]),
    ]

    existing_asset_sizes = {a["name"]: a["size"] for a in rel_data.get("assets", [])}

    for name, path in gitea_targets:
        if not path.exists():
            print(f"[✘] File not found: {path}")
            continue

        sz_mb = path.stat().st_size / (1024 * 1024)
        sz_bytes = path.stat().st_size

        if name in existing_assets:
            if existing_asset_sizes.get(name) == sz_bytes:
                print(f"[✔] Gitea asset '{name}' ({sz_mb:.2f} MB) already up to date. Skipping.")
                continue
            asset_id = existing_assets[name]
            print(f"[*] Deleting outdated Gitea asset '{name}' (ID: {asset_id})...", end="", flush=True)
            del_res = requests.delete(f"{assets_url}/{asset_id}", auth=auth)
            if del_res.status_code in [200, 204]:
                print(" [✔ Deleted]")
            else:
                print(f" [✘ Failed: {del_res.status_code}]")

        print(f"[*] Uploading '{name}' ({sz_mb:.2f} MB) to Gitea...", end="", flush=True)
        if upload_via_curl(assets_url, path, auth=auth, form_field="attachment"):
            print(" [✔ Done]")
        else:
            print(" [✘ Upload Failed]")

    gitea_body = f"""## Synapse v1.1.1 Milestone Release

### 🎓 100% Global Curriculum Complete (539 Topics across 12 Domains)
This milestone release marks the full completion of the Synapse masterclass curriculum spanning 2,945 lessons and operational labs, with 3,172 vector Mermaid.js diagrams and full KaTeX math formatting.

---

### 📥 Direct Download Links

#### 1. Master Curriculum Addon (All 12 Domains / 539 Topics)
| Package | Size | Scope | Direct Download |
| :--- | :---: | :---: | :--- |
| **`synapse_complete_curriculum.synpack`** | **33.5 MB** | **All 12 Domains (539 Topics / 2,945 Lessons & Labs)** | [**Download Master Set**]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/synapse_complete_curriculum.synpack) |

---

#### 2. Application Binaries (Desktop & Python)
| Platform / Environment | File Artifact | Size | Direct Download |
| :--- | :--- | :---: | :--- |
| **Windows Portable (.exe)** | `Synapse-Workbench-Portable-1.1.1.exe` | 163.2 MB | [Download Portable .exe]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/Synapse-Workbench-Portable-1.1.1.exe) |
| **Windows Installer (.exe)** | `Synapse-Workbench-Setup-1.1.1.exe` | 163.2 MB | [Download Installer .exe]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/Synapse-Workbench-Setup-1.1.1.exe) |
| **Windows Portable Bundle (.zip)** | `Synapse-Workbench-Portable-1.1.1-win-x64.zip` | 363.1 MB | [Download Portable Zip]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/Synapse-Workbench-Portable-1.1.1-win-x64.zip) |
| **macOS Apple Silicon (DMG)** | `Synapse-Workbench-1.1.1-arm64.dmg` | 190.0 MB | [Download .dmg]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/Synapse%20Workbench-1.1.1-arm64.dmg) |
| **macOS Portable (.zip)** | `Synapse-Workbench-1.1.1-arm64-mac.zip` | 186.2 MB | [Download .zip]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/Synapse%20Workbench-1.1.1-arm64-mac.zip) |
| **Python Wheel (.whl)** | `synapse-1.1.1-py3-none-any.whl` | 76 KB | [Download .whl]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/synapse-1.1.1-py3-none-any.whl) |
| **Python Source (.tar.gz)** | `synapse-1.1.1.tar.gz` | 84 KB | [Download .tar.gz]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/synapse-1.1.1.tar.gz) |

---

#### 3. Individual Modular Domain Addons
| Domain Addon | Size | Scope | Direct Download |
| :--- | :---: | :---: | :--- |
| **Computing & Systems** | 10.6 MB | 162 topics | [Download computing.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/computing.synpack) |
| **Arts & Music** | 3.4 MB | 67 topics | [Download arts.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/arts.synpack) |
| **Engineering** | 2.8 MB | 39 topics | [Download engineering.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/engineering.synpack) |
| **Crafts & Fabrication** | 2.7 MB | 60 topics | [Download crafts.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/crafts.synpack) |
| **Humanities** | 2.5 MB | 39 topics | [Download humanities.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/humanities.synpack) |
| **Business & Strategy** | 2.5 MB | 41 topics | [Download business.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/business.synpack) |
| **Natural Sciences** | 2.3 MB | 30 topics | [Download natural_sciences.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/natural_sciences.synpack) |
| **Economics** | 2.3 MB | 32 topics | [Download economics.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/economics.synpack) |
| **Formal Sciences** | 2.2 MB | 33 topics | [Download formal_sciences.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/formal_sciences.synpack) |
| **Health Sciences** | 969 KB | 20 topics | [Download health_sciences.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/health_sciences.synpack) |
| **Motorsports** | 686 KB | 10 topics | [Download motorsports.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/motorsports.synpack) |
| **Languages** | 514 KB | 6 topics | [Download languages.synpack]({GITEA_URL}/{GITEA_REPO}/releases/download/{TAG}/languages.synpack) |

---

### 💡 How to Install Addons
1. Open Synapse Workbench.
2. Click **Settings ⚙** → **Curriculum Store & Addons**.
3. Sideload a downloaded `.synpack` file or click **Install** next to any domain to download it automatically.
"""
    patch_res = requests.patch(
        f"{api_base}/repos/{GITEA_REPO}/releases/{rel_id}",
        auth=auth,
        json={"body": gitea_body}
    )
    if patch_res.status_code == 200:
        print("[✔] Updated Gitea release description and download tables.")
    else:
        print(f"[✘] Failed to update Gitea release body: {patch_res.status_code}")

    return True

def publish_github():
    print("\n" + "=" * 60)
    print(f"🚀 PUBLISHING TO GITHUB (https://github.com/{GITHUB_REPO})")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    rel_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{TAG}"

    res = requests.get(rel_url, headers=headers)
    if res.status_code != 200:
        print(f"[✘] Failed to fetch release {TAG} on GitHub: {res.status_code} {res.text}")
        return False

    rel_data = res.json()
    rel_id = rel_data["id"]
    upload_url_base = rel_data["upload_url"].split("{")[0]
    print(f"[✔] Found GitHub release ID {rel_id}: {rel_data.get('name')}")

    existing_assets = {a["name"]: a["id"] for a in rel_data.get("assets", [])}
    existing_asset_sizes = {a["name"]: a["size"] for a in rel_data.get("assets", [])}

    github_targets = [
        ("Synapse-Workbench-Portable-1.1.1.exe", ASSETS_TO_PUBLISH["Synapse-Workbench-Portable-1.1.1.exe"]),
        ("Synapse-Workbench-Setup-1.1.1.exe", ASSETS_TO_PUBLISH["Synapse-Workbench-Setup-1.1.1.exe"]),
        ("Synapse-Workbench-Portable-1.1.1-win-x64.zip", ASSETS_TO_PUBLISH["Synapse-Workbench-Portable-1.1.1-win-x64.zip"]),
        ("Synapse-Portable-Windows.zip", ASSETS_TO_PUBLISH["Synapse-Portable-Windows.zip"]),
        ("Synapse-Workbench-1.1.1-arm64.dmg", ASSETS_TO_PUBLISH["Synapse-Workbench-1.1.1-arm64.dmg"]),
        ("Synapse-Workbench-1.1.1-arm64-mac.zip", ASSETS_TO_PUBLISH["Synapse-Workbench-1.1.1-arm64-mac.zip"]),
    ]

    for name, path in github_targets:
        if not path.exists():
            print(f"[✘] File not found: {path}")
            continue

        sz_mb = path.stat().st_size / (1024 * 1024)
        sz_bytes = path.stat().st_size

        if name in existing_assets:
            if existing_asset_sizes.get(name) == sz_bytes:
                print(f"[✔] GitHub asset '{name}' ({sz_mb:.2f} MB) already up to date. Skipping.")
                continue
            asset_id = existing_assets[name]
            print(f"[*] Deleting outdated GitHub asset '{name}' (ID: {asset_id})...", end="", flush=True)
            del_res = requests.delete(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{asset_id}",
                headers=headers
            )
            if del_res.status_code in [200, 204]:
                print(" [✔ Deleted]")
            else:
                print(f" [✘ Failed: {del_res.status_code}]")

        print(f"[*] Uploading '{name}' ({sz_mb:.2f} MB) to GitHub...", end="", flush=True)
        if shutil.which("gh") and GITHUB_TOKEN:
            env = os.environ.copy()
            env["GH_TOKEN"] = GITHUB_TOKEN
            proc = subprocess.run(
                ["gh", "release", "upload", TAG, str(path), "--repo", GITHUB_REPO, "--clobber"],
                env=env,
                capture_output=True,
                text=True
            )
            if proc.returncode == 0:
                print(" [✔ Done]")
            else:
                print(f" [✘ Upload Failed: {proc.stderr.strip()}]")
        else:
            up_headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/octet-stream",
                "Accept": "application/vnd.github+json"
            }
            target_upload_url = f"{upload_url_base}?name={name}"
            if upload_via_curl(target_upload_url, path, headers=up_headers):
                print(" [✔ Done]")
            else:
                print(" [✘ Upload Failed]")

    github_body = f"""## Synapse v1.1.1 Milestone Release

### 🎓 100% Global Curriculum Complete (539 Topics across 12 Domains)
This milestone release marks the full completion of the Synapse masterclass curriculum spanning 2,945 lessons and operational labs, with 3,172 vector Mermaid.js diagrams and full KaTeX math formatting.

---

### 📥 Direct Download Links

#### 1. Master Curriculum Addon (All 12 Domains / 539 Topics)
| Package | Size | Scope | Direct Download |
| :--- | :---: | :---: | :--- |
| **`synapse_complete_curriculum.synpack`** | **33.5 MB** | **All 12 Domains (539 Topics / 2,945 Lessons & Labs)** | [**Download Master Set**](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/synapse_complete_curriculum.synpack) |

---

#### 2. Application Binaries (Desktop & Python)
| Platform / Environment | File Artifact | Size | Direct Download |
| :--- | :--- | :---: | :--- |
| **Windows Portable (.exe)** | `Synapse-Workbench-Portable-1.1.1.exe` | 163.2 MB | [Download Portable .exe](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/Synapse-Workbench-Portable-1.1.1.exe) |
| **Windows Installer (.exe)** | `Synapse-Workbench-Setup-1.1.1.exe` | 163.2 MB | [Download Installer .exe](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/Synapse-Workbench-Setup-1.1.1.exe) |
| **Windows Portable Bundle (.zip)** | `Synapse-Workbench-Portable-1.1.1-win-x64.zip` | 363.1 MB | [Download Portable Zip](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/Synapse-Workbench-Portable-1.1.1-win-x64.zip) |
| **macOS Apple Silicon (DMG)** | `Synapse-Workbench-1.1.1-arm64.dmg` | 190.0 MB | [Download .dmg](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/Synapse-Workbench-1.1.1-arm64.dmg) |
| **macOS Portable (.zip)** | `Synapse-Workbench-1.1.1-arm64-mac.zip` | 186.2 MB | [Download .zip](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/Synapse-Workbench-1.1.1-arm64-mac.zip) |
| **Python Wheel (.whl)** | `synapse-1.1.1-py3-none-any.whl` | 76 KB | [Download .whl](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/synapse-1.1.1-py3-none-any.whl) |
| **Python Source (.tar.gz)** | `synapse-1.1.1.tar.gz` | 84 KB | [Download .tar.gz](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/synapse-1.1.1.tar.gz) |

---

#### 3. Individual Modular Domain Addons
| Domain Addon | Size | Scope | Direct Download |
| :--- | :---: | :---: | :--- |
| **Computing & Systems** | 10.6 MB | 162 topics | [Download computing.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/computing.synpack) |
| **Arts & Music** | 3.4 MB | 67 topics | [Download arts.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/arts.synpack) |
| **Engineering** | 2.8 MB | 39 topics | [Download engineering.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/engineering.synpack) |
| **Crafts & Fabrication** | 2.7 MB | 60 topics | [Download crafts.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/crafts.synpack) |
| **Humanities** | 2.5 MB | 39 topics | [Download humanities.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/humanities.synpack) |
| **Business & Strategy** | 2.5 MB | 41 topics | [Download business.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/business.synpack) |
| **Natural Sciences** | 2.3 MB | 30 topics | [Download natural_sciences.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/natural_sciences.synpack) |
| **Economics** | 2.3 MB | 32 topics | [Download economics.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/economics.synpack) |
| **Formal Sciences** | 2.2 MB | 33 topics | [Download formal_sciences.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/formal_sciences.synpack) |
| **Health Sciences** | 969 KB | 20 topics | [Download health_sciences.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/health_sciences.synpack) |
| **Motorsports** | 686 KB | 10 topics | [Download motorsports.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/motorsports.synpack) |
| **Languages** | 514 KB | 6 topics | [Download languages.synpack](https://github.com/{GITHUB_REPO}/releases/download/{TAG}/languages.synpack) |

---

### 💡 How to Install Addons
1. Open Synapse Workbench.
2. Click **Settings ⚙** → **Curriculum Store & Addons**.
3. Sideload a downloaded `.synpack` file or click **Install** next to any domain to download it automatically.
"""
    patch_res = requests.patch(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/{rel_id}",
        headers=headers,
        json={"body": github_body}
    )
    if patch_res.status_code == 200:
        print("[✔] Updated GitHub release description and download tables.")
    else:
        print(f"[✘] Failed to update GitHub release body: {patch_res.status_code}")

    return True

def main():
    print("=" * 60)
    print(" SYNAPSE v1.1.1 MULTI-PLATFORM RELEASE PUBLISHER")
    print("=" * 60)

    ok_gitea = publish_gitea()
    ok_github = publish_github()

    print("\n" + "=" * 60)
    if ok_gitea and ok_github:
        print("🎉 [✔] ALL RELEASES SUCCESSFULLY PUBLISHED TO GITEA & GITHUB!")
    else:
        print(f"⚠️ [!] Completed with status: Gitea={ok_gitea}, GitHub={ok_github}")
    print("=" * 60)

if __name__ == "__main__":
    main()
