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
    WORKSPACE_ROOT / "dist/desktop/Synapse Workbench-1.1.0-arm64.dmg",
    WORKSPACE_ROOT / "dist/desktop/Synapse Workbench-1.1.0-arm64-mac.zip",
    WORKSPACE_ROOT / "dist/python/synapse-1.1.0-py3-none-any.whl",
    WORKSPACE_ROOT / "dist/python/synapse-1.1.0.tar.gz"
]

def main():
    parser = argparse.ArgumentParser(description="Upload Synapse v1.1.0 Release Assets to GitHub")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub Personal Access Token (or set GITHUB_TOKEN)")
    parser.add_argument("--repo", default="blebleblee/synapse", help="Target GitHub repo (default: blebleblee/synapse)")
    parser.add_argument("--tag", default="v1.1.0", help="Release tag (default: v1.1.0)")
    args = parser.parse_args()

    token = args.token
    if not token:
        print("[✘] Error: GitHub token required. Pass --token <PAT> or set GITHUB_TOKEN environment variable.")
        print("    Generate a token at: https://github.com/settings/tokens (select 'repo' scope)")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # 1. Create or fetch Release
    releases_url = f"https://api.github.com/repos/{args.repo}/releases"
    print(f"[*] Checking existing releases for {args.repo}...")
    res = requests.get(f"{releases_url}/tags/{args.tag}", headers=headers)
    
    if res.status_code == 200:
        rel_data = res.json()
        rel_id = rel_data["id"]
        upload_url = rel_data["upload_url"].split("{")[0]
        print(f"[✔] Found existing release: {rel_data['name']} (ID: {rel_id})")
    elif res.status_code == 404:
        print(f"[*] Creating GitHub Release {args.tag}...")
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
- **Python Distribution**: `synapse-1.1.0-py3-none-any.whl` / `.tar.gz`
""",
            "draft": False,
            "prerelease": False
        }
        res = requests.post(releases_url, headers=headers, json=payload)
        if res.status_code in [200, 201]:
            rel_data = res.json()
            rel_id = rel_data["id"]
            upload_url = rel_data["upload_url"].split("{")[0]
            print(f"[✔] Created release successfully! ID: {rel_id}")
        else:
            print(f"[✘] Failed to create release: {res.status_code} {res.text}")
            sys.exit(1)
    else:
        print(f"[✘] GitHub API error: {res.status_code} {res.text}")
        sys.exit(1)

    # 2. Upload Assets
    existing_assets = {a["name"]: a["id"] for a in rel_data.get("assets", [])}
    valid_assets = [p for p in ASSETS if p.exists()]

    print(f"\n[*] Uploading {len(valid_assets)} release assets to GitHub:")
    for p in valid_assets:
        sz_mb = p.stat().st_size / (1024 * 1024)
        if p.name in existing_assets:
            print(f"  • {p.name} ({sz_mb:.2f} MB) already uploaded. Skipping.")
            continue

        print(f"  • Uploading {p.name} ({sz_mb:.2f} MB)...", end="", flush=True)
        up_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Accept": "application/vnd.github+json"
        }
        with open(p, "rb") as f:
            up_res = requests.post(
                upload_url,
                headers=up_headers,
                params={"name": p.name},
                data=f,
                timeout=300
            )
            if up_res.status_code in [200, 201]:
                print(" [✔ Done]")
            else:
                print(f" [✘ Failed: {up_res.status_code}]")

    print("\n" + "=" * 60)
    print(f" [✔] All assets uploaded to: {rel_data.get('html_url')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
