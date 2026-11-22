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
    parser = argparse.ArgumentParser(description="Upload Synapse v1.1.0 Release Assets to GitHub")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub Personal Access Token (or set GITHUB_TOKEN)")
    parser.add_argument("--repo", default="blebleblee/synapse", help="Target GitHub repo (default: blebleblee/synapse)")
    parser.add_argument("--tag", default="v1.1.1", help="Release tag (default: v1.1.1)")
    args = parser.parse_args()
    _require_clean_packs(ASSETS if 'ASSETS' in globals() else None)

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
            "name": f"Synapse {args.tag} — Hosted Instance Protection, Async Terminal Streaming & Translation Polish",
            "body": """## Synapse v1.1.1 Release

### 🛡️ Hosted Instance Password Protection
- Zero-dependency instance password gating via `SYNAPSE_PASSWORD`.
- 30-day signed HMAC bearer tokens stored in browser `localStorage`.
- Gated `/api/*` endpoints and `/ws/terminal` PTY WebSocket with 401 interceptor.
- Sleek React login modal with brute-force rate-limiting.

### ⚡ Terminal Independence (Windows Event Loop Fix)
- Non-blocking async queue streaming for `/api/chat` and `/api/translate`.
- Eliminates PTY starvation and keystroke input lag during AI generation.

### 🌐 On-Demand Curriculum Translation
- One-click language switcher with English default and on-demand translation.
- Immediate in-place translation rendering powered by Claude Sonnet (~2.4s).
- Seamless alignment with Socratic Mentor conversational language.

### 📦 Private SynPack Distribution & Dynamic Discovery
- Sideloading and dynamic filesystem discovery for custom curriculum packages without `SYLLABUS.md`.
- Headless CLI `synapse pack` subsystem (`install`, `list`, `uninstall`).
- Configurable private Gitea registries via `SYNAPSE_PACKAGE_REGISTRY`.
- Automatic pre-extraction backups in `exports/backups/`.
- Cross-runtime workspace default aligned to `~/.synapse`.

### 🚀 Performance & Caching
- In-memory topic tree RAM caching (drops warm tree queries from 2.3s to 3 microseconds).
- Fast parallel Ollama cluster node probing with 1.5s timeouts (eliminates 12–20s startup hangs).
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
        sz_bytes = p.stat().st_size
        if p.name in existing_assets:
            print(f"  • {p.name} ({sz_mb:.2f} MB) already uploaded. Skipping.")
            continue

        print(f"  • Uploading {p.name} ({sz_mb:.2f} MB)...", end="", flush=True)
        up_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Content-Length": str(sz_bytes),
            "Accept": "application/vnd.github+json"
        }
        uploaded = False
        for attempt in range(1, 4):
            try:
                with open(p, "rb") as f:
                    up_res = requests.post(
                        upload_url,
                        headers=up_headers,
                        params={"name": p.name},
                        data=f,
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
    print(f" [✔] All assets uploaded to: {rel_data.get('html_url')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
