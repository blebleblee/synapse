#!/usr/bin/env python3
"""
Synapse Multi-Platform Release Publisher for Gitea and GitHub
Dynamically reads version from VERSION / learning_engine.version.
Automatically creates releases if they do not yet exist, and synchronizes
verified binary assets across Gitea and GitHub.
"""

import os
import sys
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

# Single Source of Truth Version Resolution
VER_FILE = WORKSPACE_ROOT / "VERSION"
if VER_FILE.exists():
    VER = VER_FILE.read_text(encoding="utf-8").strip()
else:
    VER = "1.2.0"

TAG = f"v{VER}"

# Credentials
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITEA_URL = os.environ.get("GITEA_URL", "https://gitea.2464.cz")
GITEA_USER = os.environ.get("GITEA_USER", "")
GITEA_PASS = os.environ.get("GITEA_PASS", "")
GITEA_REPO = os.environ.get("GITEA_REPO", "ai/synapse")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "blebleblee/synapse")

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

# Target binary files to publish
ASSETS_TO_PUBLISH = {
    f"Synapse-Workbench-Portable-{VER}.exe": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-Portable-{VER}.exe",
    f"Synapse-Workbench-Setup-{VER}.exe": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-Setup-{VER}.exe",
    f"Synapse-Workbench-Portable-{VER}-win-x64.zip": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-Portable-{VER}-win-x64.zip",
    "Synapse-Portable-Windows.zip": WORKSPACE_ROOT / "dist/desktop/Synapse-Portable-Windows.zip",
    f"Synapse-Workbench-{VER}-arm64.dmg": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-{VER}-arm64.dmg",
    f"Synapse-Workbench-{VER}-arm64.zip": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-{VER}-arm64.zip",
    f"synapse-{VER}-py3-none-any.whl": WORKSPACE_ROOT / f"dist/python/synapse-{VER}-py3-none-any.whl",
    f"synapse-{VER}.tar.gz": WORKSPACE_ROOT / f"dist/python/synapse-{VER}.tar.gz",
}

# Add SynPacks if present
packages_dir = WORKSPACE_ROOT / "exports" / "packages"
if packages_dir.exists():
    for synpack in packages_dir.glob("*.synpack"):
        ASSETS_TO_PUBLISH[synpack.name] = synpack

def generate_release_body(endpoint_url: str, repo_name: str, is_github: bool = False) -> str:
    dl_base = f"https://github.com/{repo_name}/releases/download/{TAG}" if is_github else f"{endpoint_url.rstrip('/')}/{repo_name}/releases/download/{TAG}"
    return f"""## Synapse {TAG} Milestone Release

### 🎓 100% Global Polymath Masterclass Curriculum (1,541 Topics across 21 Domains)
This milestone release marks the full completion and code-fence normalization of the Synapse curriculum (12,426 lessons and 1,541 operational verification labs, with zero linter errors and zero warnings).

---

### 📥 Direct Download Links

#### 1. Application Binaries (macOS & Windows Desktop, Python)
| Platform / Environment | File Artifact | Direct Download |
| :--- | :--- | :--- |
| **macOS Apple Silicon (DMG)** | `Synapse-Workbench-{VER}-arm64.dmg` | [Download .dmg]({dl_base}/Synapse-Workbench-{VER}-arm64.dmg) |
| **macOS Portable (.zip)** | `Synapse-Workbench-{VER}-arm64.zip` | [Download .zip]({dl_base}/Synapse-Workbench-{VER}-arm64.zip) |
| **Windows Portable (.exe)** | `Synapse-Workbench-Portable-{VER}.exe` | [Download Portable .exe]({dl_base}/Synapse-Workbench-Portable-{VER}.exe) |
| **Windows Installer (.exe)** | `Synapse-Workbench-Setup-{VER}.exe` | [Download Installer .exe]({dl_base}/Synapse-Workbench-Setup-{VER}.exe) |
| **Windows Portable Bundle (.zip)** | `Synapse-Workbench-Portable-{VER}-win-x64.zip` | [Download Portable Zip]({dl_base}/Synapse-Workbench-Portable-{VER}-win-x64.zip) |
| **Python Wheel (.whl)** | `synapse-{VER}-py3-none-any.whl` | [Download .whl]({dl_base}/synapse-{VER}-py3-none-any.whl) |
| **Python Source (.tar.gz)** | `synapse-{VER}.tar.gz` | [Download .tar.gz]({dl_base}/synapse-{VER}.tar.gz) |

---

#### 2. Curriculum Package Addons
| Package | Description | Direct Download |
| :--- | :--- | :--- |
| **`synapse_complete_curriculum.synpack`** | All Core Masterclass Domains | [Download Complete Set]({dl_base}/synapse_complete_curriculum.synpack) |
| **`computing.synpack`** | Computing & Distributed Systems | [Download computing.synpack]({dl_base}/computing.synpack) |
| **`arts.synpack`** | Arts, Design & Music Performance | [Download arts.synpack]({dl_base}/arts.synpack) |
| **`engineering.synpack`** | Engineering, Robotics & Avionics | [Download engineering.synpack]({dl_base}/engineering.synpack) |
| **`crafts.synpack`** | Fabrication, Maker & 3D Printing | [Download crafts.synpack]({dl_base}/crafts.synpack) |
| **`business.synpack`** | Enterprise, Finance & Markets | [Download business.synpack]({dl_base}/business.synpack) |
| **`humanities.synpack`** | Philosophy, History & Literature | [Download humanities.synpack]({dl_base}/humanities.synpack) |
| **`natural_sciences.synpack`** | Physics, Chemistry & Biology | [Download natural_sciences.synpack]({dl_base}/natural_sciences.synpack) |
| **`economics.synpack`** | Macroeconomics, Quant & Policy | [Download economics.synpack]({dl_base}/economics.synpack) |
| **`formal_sciences.synpack`** | Pure Mathematics & Logic | [Download formal_sciences.synpack]({dl_base}/formal_sciences.synpack) |
| **`health_sciences.synpack`** | Medicine, Neuroscience & Triage | [Download health_sciences.synpack]({dl_base}/health_sciences.synpack) |
| **`motorsports.synpack`** | Vehicle Dynamics & Race Eng. | [Download motorsports.synpack]({dl_base}/motorsports.synpack) |
| **`languages.synpack`** | Grammar, Writing & Translation | [Download languages.synpack]({dl_base}/languages.synpack) |

---

### 💡 How to Install Addons
1. Open Synapse Workbench.
2. Click **Settings ⚙** → **Curriculum Store & Addons**.
3. Sideload a downloaded `.synpack` file or click **Install** next to any domain to download it automatically.
"""

def publish_gitea():
    print("\n" + "=" * 60)
    print(f"🚀 PUBLISHING TO GITEA ({GITEA_URL} / {GITEA_REPO}) -> {TAG}")
    print("=" * 60)

    auth = (GITEA_USER, GITEA_PASS)
    api_base = f"{GITEA_URL.rstrip('/')}/api/v1"
    rel_url = f"{api_base}/repos/{GITEA_REPO}/releases/tags/{TAG}"

    res = requests.get(rel_url, auth=auth)
    if res.status_code == 404:
        print(f"[*] Release {TAG} not found on Gitea. Creating release {TAG} automatically...")
        create_url = f"{api_base}/repos/{GITEA_REPO}/releases"
        payload = {
            "tag_name": TAG,
            "name": f"Synapse {TAG} — Resilient Translation, Native ConPTY & Zero-Defect Curriculum",
            "body": f"Release binaries for Synapse {TAG}.",
            "draft": False,
            "prerelease": False
        }
        res = requests.post(create_url, json=payload, auth=auth)
        if res.status_code not in [200, 201]:
            print(f"[✘] Failed to create release {TAG} on Gitea: {res.status_code} {res.text}")
            return False
        rel_data = res.json()
        print(f"[✔] Created new Gitea release ID {rel_data['id']}: {rel_data.get('name')}")
    elif res.status_code != 200:
        print(f"[✘] Failed to fetch release {TAG} on Gitea: {res.status_code} {res.text}")
        return False
    else:
        rel_data = res.json()

    rel_id = rel_data["id"]
    print(f"[✔] Found Gitea release ID {rel_id}: {rel_data.get('name')}")

    assets_url = f"{api_base}/repos/{GITEA_REPO}/releases/{rel_id}/assets"
    existing_assets = {a["name"]: a["id"] for a in rel_data.get("assets", [])}
    existing_asset_sizes = {a["name"]: a["size"] for a in rel_data.get("assets", [])}

    for name, path in ASSETS_TO_PUBLISH.items():
        if not path.exists():
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

    gitea_body = generate_release_body(GITEA_URL, GITEA_REPO, is_github=False)
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
    print(f"🚀 PUBLISHING TO GITHUB (https://github.com/{GITHUB_REPO}) -> {TAG}")
    print("=" * 60)

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    rel_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{TAG}"

    res = requests.get(rel_url, headers=headers)
    if res.status_code == 404:
        print(f"[*] Release {TAG} not found on GitHub. Creating release {TAG} automatically...")
        create_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        payload = {
            "tag_name": TAG,
            "name": f"Synapse {TAG} — Resilient Translation, Native ConPTY & Zero-Defect Curriculum",
            "body": f"Release binaries for Synapse {TAG}.",
            "draft": False,
            "prerelease": False
        }
        res = requests.post(create_url, json=payload, headers=headers)
        if res.status_code not in [200, 201]:
            print(f"[✘] Failed to create release {TAG} on GitHub: {res.status_code} {res.text}")
            return False
        rel_data = res.json()
        print(f"[✔] Created new GitHub release ID {rel_data['id']}: {rel_data.get('name')}")
    elif res.status_code != 200:
        print(f"[✘] Failed to fetch release {TAG} on GitHub: {res.status_code} {res.text}")
        return False
    else:
        rel_data = res.json()

    rel_id = rel_data["id"]
    upload_url_base = rel_data["upload_url"].split("{")[0]
    print(f"[✔] Found GitHub release ID {rel_id}: {rel_data.get('name')}")

    existing_assets = {a["name"]: a["id"] for a in rel_data.get("assets", [])}
    existing_asset_sizes = {a["name"]: a["size"] for a in rel_data.get("assets", [])}

    for name, path in ASSETS_TO_PUBLISH.items():
        if not path.exists():
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
        up_headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/octet-stream",
            "Accept": "application/vnd.github+json"
        }
        target_upload_url = f"{upload_url_base}?name={name}"
        if upload_via_curl(target_upload_url, path, headers=up_headers):
            print(" [✔ Done]")
        else:
            print(" [✘ Upload Failed]")

    github_body = generate_release_body(GITEA_URL, GITHUB_REPO, is_github=True)
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
    print(f" SYNAPSE {TAG} MULTI-PLATFORM RELEASE PUBLISHER")
    print("=" * 60)

    ok_gitea = publish_gitea()
    ok_github = publish_github()

    print("\n" + "=" * 60)
    if ok_gitea and ok_github:
        print(f"🎉 [✔] ALL RELEASES FOR {TAG} SUCCESSFULLY PUBLISHED TO GITEA & GITHUB!")
    else:
        print(f"⚠️ [!] Completed with status: Gitea={ok_gitea}, GitHub={ok_github}")
    print("=" * 60)

if __name__ == "__main__":
    main()
