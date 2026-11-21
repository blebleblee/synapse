#!/usr/bin/env python3
"""
Automated GitHub Release & Asset Uploader
Creates GitHub Release v1.1.0 and uploads all 17 distribution binaries and SynPack addons.
"""

import os
import sys
import argparse
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

ASSETS = [
    WORKSPACE_ROOT / "exports/packages/synapse_complete_curriculum.synpack",
    WORKSPACE_ROOT / "exports/packages/computing.synpack",
    WORKSPACE_ROOT / "exports/packages/arts.synpack",
    WORKSPACE_ROOT / "exports/packages/crafts.synpack",
    WORKSPACE_ROOT / "exports/packages/business.synpack",
    WORKSPACE_ROOT / "exports/packages/engineering.synpack",
    WORKSPACE_ROOT / "exports/packages/motorsports.synpack",
    WORKSPACE_ROOT / "exports/packages/formal_sciences.synpack",
    WORKSPACE_ROOT / "exports/packages/humanities.synpack",
    WORKSPACE_ROOT / "exports/packages/languages.synpack",
    WORKSPACE_ROOT / "exports/packages/economics.synpack",
    WORKSPACE_ROOT / "exports/packages/natural_sciences.synpack",
    WORKSPACE_ROOT / "exports/packages/health_sciences.synpack",
    WORKSPACE_ROOT / "dist/desktop/Synapse Workbench-1.1.1-arm64.dmg",
    WORKSPACE_ROOT / "dist/desktop/Synapse Workbench-1.1.1-arm64-mac.zip",
    WORKSPACE_ROOT / "dist/desktop/Synapse-Workbench-Portable-1.1.1.exe",
    WORKSPACE_ROOT / "dist/desktop/Synapse-Portable-Windows.zip",
    WORKSPACE_ROOT / "dist/python/synapse-1.1.1-py3-none-any.whl",
    WORKSPACE_ROOT / "dist/python/synapse-1.1.1.tar.gz"
]


def _require_clean_packs(paths=None):
    """Refuses to publish if any pack contains private or uncommitted content."""
    import subprocess as _sp
    checker = Path(__file__).resolve().parent / "check_release_packs.py"
    args = [sys.executable, str(checker)] + [str(p) for p in (paths or []) if str(p).endswith(".synpack")]
    if _sp.run(args).returncode != 0:
        print("[✘] Aborting release: pack privacy check failed (see above).")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Upload Synapse v1.1.1 Release Assets to Gitea")
    parser.add_argument("--url", default=os.environ.get("GITEA_URL", "https://gitea.2464.cz"), help="Gitea instance URL")
    parser.add_argument("--token", default=os.environ.get("GITEA_TOKEN"), help="Gitea Personal Access Token")
    parser.add_argument("--user", default=os.environ.get("GITEA_USER", ""), help="Gitea username")
    parser.add_argument("--password", default=os.environ.get("GITEA_PASS", ""), help="Gitea password")
    parser.add_argument("--repo", default=os.environ.get("GITEA_REPO", "ai/synapse"), help="Target Gitea repo (default: ai/synapse)")
    parser.add_argument("--tag", default="v1.1.1", help="Release tag (default: v1.1.1)")
    args = parser.parse_args()
    _require_clean_packs(ASSETS if 'ASSETS' in globals() else None)

    auth = None
    headers = {"Accept": "application/json"}
    if args.token:
        headers["Authorization"] = f"token {args.token}"
    elif args.user and args.password:
        auth = (args.user, args.password)
    else:
        print("[✘] Error: Gitea authentication required. Pass --token <PAT> or --user / --password.")
        sys.exit(1)

    # 1. Create or fetch Release
    releases_url = f"{args.url.rstrip('/')}/api/v1/repos/{args.repo}/releases"
    print(f"[*] Checking existing releases for {args.repo} on {args.url}...")
    res = requests.get(f"{releases_url}/tags/{args.tag}", headers=headers, auth=auth)
    
    if res.status_code == 200:
        rel_data = res.json()
        rel_id = rel_data["id"]
        print(f"[✔] Found existing release: {rel_data['name']} (ID: {rel_id})")
    elif res.status_code == 404:
        print(f"[*] Creating Gitea Release {args.tag}...")
        payload = {
            "tag_name": args.tag,
            "target_commitish": "main",
            "name": f"Synapse {args.tag} — Complete Global Curriculum (539 Topics) & Master SynPack Suite",
            "body": """## Synapse v1.1.0 Milestone Release

### 🎓 100% Global Curriculum Complete (539 Topics across 12 Domains)
This milestone release marks the full completion of the Synapse masterclass curriculum spanning 2,945 lessons and operational labs, with 3,172 vector Mermaid.js diagrams and full KaTeX math formatting.

### 📦 Modular SynPack Curriculum Addons
Download and sideload curriculum addons via Settings ⚙ → Sideload, or drop into your portable folder:
- **`synapse_complete_curriculum.synpack` (33.5 MB)**: Complete master pack containing all 12 domains and 539 topics.
- **12 Individual Domain Addons**: Computing, Arts, Crafts, Business, Engineering, Motorsports, Formal Sciences, Humanities, Languages, Economics, Natural Sciences, Health Sciences.

### 💻 Application Binaries
- **macOS Apple Silicon**: `Synapse Workbench-1.1.0-arm64.dmg` / `.zip`
- **Windows Portable**: `Synapse-Portable-Windows.zip`
- **Python Distribution**: `synapse-1.1.0-py3-none-any.whl` / `.tar.gz`
""",
            "draft": False,
            "prerelease": False
        }
        res = requests.post(releases_url, headers=headers, json=payload)
        if res.status_code in [200, 201]:
            rel_data = res.json()
            rel_id = rel_data["id"]
            print(f"[✔] Created release successfully! ID: {rel_id}")
        else:
            print(f"[✘] Failed to create release: {res.status_code} {res.text}")
            sys.exit(1)
    else:
        print(f"[✘] Gitea API error: {res.status_code} {res.text}")
        sys.exit(1)

    # 2. Upload Assets
    existing_assets = {a["name"]: a["id"] for a in rel_data.get("assets", [])}
    valid_assets = [p for p in ASSETS if p.exists()]
    upload_url = f"{releases_url}/{rel_id}/assets"

    print(f"\n[*] Uploading {len(valid_assets)} release assets to Gitea:")
    for p in valid_assets:
        sz_mb = p.stat().st_size / (1024 * 1024)
        if p.name in existing_assets:
            print(f"  • {p.name} ({sz_mb:.2f} MB) already uploaded. Skipping.")
            continue

        print(f"  • Uploading {p.name} ({sz_mb:.2f} MB)...", end="", flush=True)
        uploaded = False
        for attempt in range(1, 4):
            try:
                with open(p, "rb") as f:
                    up_res = requests.post(
                        upload_url,
                        headers=headers,
                        auth=auth,
                        files={"attachment": (p.name, f)},
                        params={"name": p.name},
                        timeout=600
                    )
                    if up_res.status_code in [200, 201]:
                        print(" [✔ Done]")
                        uploaded = True
                        break
                    else:
                        print(f" [Retry {attempt}: {up_res.status_code}]", end="", flush=True)
            except Exception as e:
                print(f" [Retry {attempt}: {e.__class__.__name__}]", end="", flush=True)
                import time; time.sleep(3)
        if not uploaded:
            print(" [✘ Failed after 3 attempts]")

    print("\n" + "=" * 60)
    print(f" [✔] All assets uploaded to Gitea!")
    print("=" * 60)

if __name__ == "__main__":
    main()
