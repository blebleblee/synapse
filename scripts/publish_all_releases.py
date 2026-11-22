#!/usr/bin/env python3
"""
Publishes Synapse releases on Gitea and GitHub.

    publish_all_releases.py               app release v<VERSION>: installers,
                                          portable builds, Python packages
    publish_all_releases.py --curriculum  the `curriculum` release: the 13
                                          core-domain packs

App releases no longer carry curriculum packs. The `curriculum` release is
updated in place: packs are exported fresh, checked by the release guard, and
only packs whose content changed (by `pack_content_digest`) are replaced.
`curriculum.json` on the release records each pack's digest.
"""

import os
import sys
import re
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

def extract_changelog_notes(ver: str) -> str:
    """Extracts the exact release section for `[ver]` from CHANGELOG.md."""
    changelog_path = WORKSPACE_ROOT / "CHANGELOG.md"
    if not changelog_path.exists():
        return ""
    content = changelog_path.read_text(encoding="utf-8")
    pattern = rf"##\s+\[{re.escape(ver)}\][^\n]*\n([\s\S]*?)(?=\n##\s+\[|\Z)"
    match = re.search(pattern, content)
    if match:
        return match.group(1).strip()
    return ""

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
    f"Synapse-Workbench-{VER}-arm64.dmg": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-{VER}-arm64.dmg",
    f"Synapse-Workbench-{VER}-arm64.zip": WORKSPACE_ROOT / f"dist/desktop/Synapse-Workbench-{VER}-arm64.zip",
    f"synapse-{VER}-py3-none-any.whl": WORKSPACE_ROOT / f"dist/python/synapse-{VER}-py3-none-any.whl",
    f"synapse-{VER}.tar.gz": WORKSPACE_ROOT / f"dist/python/synapse-{VER}.tar.gz",
}

# Packs on the curriculum release (strictly the public core domains)
CORE_SYNPACKS = {
    "synapse_complete_curriculum.synpack",
    "computing.synpack", "arts.synpack", "crafts.synpack", "business.synpack",
    "engineering.synpack", "motorsports.synpack", "formal_sciences.synpack",
    "humanities.synpack", "languages.synpack", "economics.synpack",
    "natural_sciences.synpack", "health_sciences.synpack"
}
CURRICULUM_TAG = "curriculum"
CURRICULUM_INDEX = "curriculum.json"

def release_title() -> str:
    """Plain version title; the notes say what changed."""
    return f"Synapse {TAG}"


def generate_release_body(endpoint_url: str = "", repo_name: str = "", is_github: bool = False,
                          has_installers: bool = True) -> str:
    """Release notes from CHANGELOG.md plus short install guidance.

    Files are not listed or linked here: the release page already shows every
    attached file, and hand-written tables go stale or point at missing files.
    """
    notes = extract_changelog_notes(VER) or "See CHANGELOG.md for details."
    notes = notes.rstrip().removesuffix("---").rstrip()  # sections end with their own divider
    if not has_installers:
        return f"""{notes}

---

### Installing
The desktop installers and portable builds for this version have been withdrawn. Please install the latest release instead. The Python package and the curriculum packs attached here are still available.
"""
    return f"""{notes}

---

### Installing
- **macOS (Apple Silicon):** download the `.dmg` from the files below.
- **Windows:** use the installer, or the portable build if you can't install software.
- **Python:** `pip install` the wheel, then run `synapse serve`.

Curriculum packs (`.synpack`) are on the separate **curriculum** release. The app installs them for you (**Settings ⚙ → Curriculum Store & Addons**).
"""


def _has_installers(assets) -> bool:
    return any(a["name"].endswith((".dmg", ".exe", "-mac.zip", "-arm64.zip", "-win-x64.zip")) for a in assets)


def update_release_text(title, body_for=None) -> bool:
    """Rewrites the notes (and, if `title` is given, the title) of the TAG release
    on Gitea and GitHub. Notes are generated per host, so they mention installers
    only where that host still has them. A host without the release is skipped."""
    body_for = body_for or (lambda has_installers: generate_release_body(has_installers=has_installers))
    ok = True
    gitea_api = f"{GITEA_URL.rstrip('/')}/api/v1/repos/{GITEA_REPO}/releases"
    gh_api = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    gitea_auth = (GITEA_USER, GITEA_PASS)
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json",
                  "X-GitHub-Api-Version": "2022-11-28"}
    for host, api, kw in (("Gitea", gitea_api, {"auth": gitea_auth}), ("GitHub", gh_api, {"headers": gh_headers})):
        got = requests.get(f"{api}/tags/{TAG}", **kw)
        if got.status_code == 404:
            print(f"[-] {host}: no {TAG} release, skipped")
            continue
        if not got.ok:
            print(f"[✘] {host}: HTTP {got.status_code} reading {TAG}")
            ok = False
            continue
        rel = got.json()
        payload = {"body": body_for(_has_installers(rel.get("assets", [])))}
        if title:
            payload["name"] = title
        r = requests.patch(f"{api}/{rel['id']}", json=payload, **kw)
        print(f"[{'✔' if r.ok else '✘'}] {host} {TAG} notes updated: HTTP {r.status_code}")
        ok &= r.ok
    return ok


def _gitea_release(api_base, auth, tag, title):
    res = requests.get(f"{api_base}/repos/{GITEA_REPO}/releases/tags/{tag}", auth=auth)
    if res.status_code == 404:
        print(f"[*] Creating release {tag} on Gitea...")
        res = requests.post(f"{api_base}/repos/{GITEA_REPO}/releases", auth=auth, json={
            "tag_name": tag, "target_commitish": "main", "name": title or release_title(),
            "body": f"Synapse {tag}.", "draft": False, "prerelease": False})
        if res.status_code not in [200, 201]:
            print(f"[✘] Failed to create release {tag} on Gitea: {res.status_code} {res.text[:200]}")
            return None
    elif res.status_code != 200:
        print(f"[✘] Failed to fetch release {tag} on Gitea: {res.status_code}")
        return None
    rel = res.json()
    print(f"[✔] Gitea release ID {rel['id']}: {rel.get('name')}")
    return rel


def publish_gitea(tag=None, title=None, assets=None, body=None, replace=False):
    """Creates or updates release `tag` on Gitea. With `replace`, every listed
    asset is re-uploaded; otherwise an existing one of the same size is kept."""
    tag = tag or TAG
    assets = ASSETS_TO_PUBLISH if assets is None else assets
    print("\n" + "=" * 60)
    print(f"🚀 PUBLISHING TO GITEA ({GITEA_URL} / {GITEA_REPO}) -> {tag}")
    print("=" * 60)

    auth = (GITEA_USER, GITEA_PASS)
    api_base = f"{GITEA_URL.rstrip('/')}/api/v1"
    rel_data = _gitea_release(api_base, auth, tag, title)
    if rel_data is None:
        return False
    rel_id = rel_data["id"]
    assets_url = f"{api_base}/repos/{GITEA_REPO}/releases/{rel_id}/assets"
    existing = {a["name"]: a for a in rel_data.get("assets", [])}
    ok = True

    for name, path in assets.items():
        if not path.exists():
            continue
        sz_bytes = path.stat().st_size
        sz_mb = sz_bytes / (1024 * 1024)
        if name in existing:
            if not replace and existing[name]["size"] == sz_bytes:
                print(f"[✔] Gitea asset '{name}' ({sz_mb:.2f} MB) already up to date. Skipping.")
                continue
            print(f"[*] Replacing Gitea asset '{name}'...", end="", flush=True)
            del_res = requests.delete(f"{assets_url}/{existing[name]['id']}", auth=auth)
            print(" [✔ Deleted]" if del_res.status_code in [200, 204] else f" [✘ Failed: {del_res.status_code}]")

        print(f"[*] Uploading '{name}' ({sz_mb:.2f} MB) to Gitea...", end="", flush=True)
        if upload_via_curl(assets_url, path, auth=auth, form_field="attachment"):
            print(" [✔ Done]")
        else:
            print(" [✘ Upload Failed]")
            ok = False

    payload = {"body": body if body is not None else generate_release_body(GITEA_URL, GITEA_REPO, is_github=False)}
    if title:
        payload["name"] = title
    patch_res = requests.patch(f"{api_base}/repos/{GITEA_REPO}/releases/{rel_id}", auth=auth, json=payload)
    if patch_res.status_code == 200:
        print("[✔] Gitea release notes updated.")
    else:
        print(f"[✘] Failed to update Gitea release body: {patch_res.status_code}")
        ok = False
    return ok


def _github_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def _github_release(tag, title):
    headers = _github_headers()
    res = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}", headers=headers)
    if res.status_code == 404:
        print(f"[*] Creating release {tag} on GitHub...")
        res = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/releases", headers=headers, json={
            "tag_name": tag, "target_commitish": "main", "name": title or release_title(),
            "body": f"Synapse {tag}.", "draft": False, "prerelease": False,
            # "Latest release" must stay the app, never the curriculum.
            "make_latest": "false" if tag == CURRICULUM_TAG else "true"})
        if res.status_code not in [200, 201]:
            print(f"[✘] Failed to create release {tag} on GitHub: {res.status_code} {res.text[:200]}")
            return None
    elif res.status_code != 200:
        print(f"[✘] Failed to fetch release {tag} on GitHub: {res.status_code}")
        return None
    rel = res.json()
    print(f"[✔] GitHub release ID {rel['id']}: {rel.get('name')}")
    return rel


def publish_github(tag=None, title=None, assets=None, body=None, replace=False):
    """Creates or updates release `tag` on GitHub; see publish_gitea."""
    tag = tag or TAG
    assets = ASSETS_TO_PUBLISH if assets is None else assets
    print("\n" + "=" * 60)
    print(f"🚀 PUBLISHING TO GITHUB (https://github.com/{GITHUB_REPO}) -> {tag}")
    print("=" * 60)

    headers = _github_headers()
    rel_data = _github_release(tag, title)
    if rel_data is None:
        return False
    rel_id = rel_data["id"]
    upload_url_base = rel_data["upload_url"].split("{")[0]
    existing = {a["name"]: a for a in rel_data.get("assets", [])}
    ok = True

    for name, path in assets.items():
        if not path.exists():
            continue
        sz_bytes = path.stat().st_size
        sz_mb = sz_bytes / (1024 * 1024)
        if name in existing:
            if not replace and existing[name]["size"] == sz_bytes:
                print(f"[✔] GitHub asset '{name}' ({sz_mb:.2f} MB) already up to date. Skipping.")
                continue
            print(f"[*] Replacing GitHub asset '{name}'...", end="", flush=True)
            del_res = requests.delete(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{existing[name]['id']}", headers=headers)
            print(" [✔ Deleted]" if del_res.status_code in [200, 204] else f" [✘ Failed: {del_res.status_code}]")

        print(f"[*] Uploading '{name}' ({sz_mb:.2f} MB) to GitHub...", end="", flush=True)
        # Prefer gh release upload if available for large files, otherwise curl
        if shutil.which("gh") and GITHUB_TOKEN:
            env = os.environ.copy()
            env["GH_TOKEN"] = GITHUB_TOKEN
            proc = subprocess.run(["gh", "release", "upload", tag, str(path), "--repo", GITHUB_REPO, "--clobber"],
                                  env=env, capture_output=True, text=True, timeout=1200)
            if proc.returncode == 0:
                print(" [✔ Done (gh)]")
                continue
            print(f" [gh fallback: {proc.stderr.strip()[:60]}...]", end="", flush=True)
        up_headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/octet-stream",
                      "Accept": "application/vnd.github+json"}
        if upload_via_curl(f"{upload_url_base}?name={name}", path, headers=up_headers):
            print(" [✔ Done (curl)]")
        else:
            print(" [✘ Upload Failed]")
            ok = False

    payload = {"body": body if body is not None else generate_release_body(GITEA_URL, GITHUB_REPO, is_github=True)}
    if title:
        payload["name"] = title
    patch_res = requests.patch(f"https://api.github.com/repos/{GITHUB_REPO}/releases/{rel_id}",
                               headers=headers, json=payload)
    if patch_res.status_code == 200:
        print("[✔] GitHub release notes updated.")
    else:
        print(f"[✘] Failed to update GitHub release body: {patch_res.status_code}")
        ok = False
    return ok


# ---------------------------------------------------------------------------
# Curriculum release

def export_curriculum_packs(out_dir: Path) -> dict:
    """Exports the 12 core domains and the complete pack into `out_dir`."""
    sys.path.insert(0, str(WORKSPACE_ROOT))
    from learning_engine.packages import CORE_DOMAINS, TOPICS_DIR, export_topic_pack
    out_dir.mkdir(parents=True, exist_ok=True)
    packs = {}
    for d in CORE_DOMAINS:
        if (TOPICS_DIR / d).is_dir():
            p = export_topic_pack(d, output_dir=out_dir)
            packs[p.name] = p
    p = export_topic_pack("complete", output_dir=out_dir)
    packs[p.name] = p
    unknown = set(packs) - CORE_SYNPACKS
    if unknown:
        raise SystemExit(f"[✘] Unexpected pack names: {sorted(unknown)}")
    return packs


def curriculum_index(packs: dict, commit: str, previous: dict) -> dict:
    """The curriculum.json written to the release. A pack keeps its previous
    `updated` date unless its content digest changed."""
    sys.path.insert(0, str(WORKSPACE_ROOT))
    import json
    import tarfile
    from datetime import date
    from learning_engine.packages import pack_content_digest
    today = date.today().isoformat()
    prev = (previous or {}).get("packs", {})
    entries = {}
    for name, path in sorted(packs.items()):
        digest = pack_content_digest(path)
        with tarfile.open(path, "r:gz") as tar:
            manifest = json.load(tar.extractfile("manifest.json"))
        old = prev.get(name, {})
        changed = old.get("content_sha256") != digest
        entries[name] = {
            "content_sha256": digest,
            "size": path.stat().st_size,
            "lessons": manifest.get("lesson_count"),
            "labs": manifest.get("lab_count"),
            "updated": today if changed else old.get("updated", today),
            "commit": commit if changed else old.get("commit", commit),
        }
    return {"format": "synapse-curriculum/v1", "packs": entries}


def changed_packs(index: dict, previous: dict) -> list:
    prev = (previous or {}).get("packs", {})
    return [n for n, e in index["packs"].items() if prev.get(n, {}).get("content_sha256") != e["content_sha256"]]


def curriculum_body(index: dict) -> str:
    rows = []
    for name, e in index["packs"].items():
        label = "Complete curriculum (all 12 domains)" if name == "synapse_complete_curriculum.synpack" \
            else name.removesuffix(".synpack").replace("_", " ").title()
        rows.append(f"| {label} | {e['lessons']} | {e['labs']} | {e['updated']} |")
    return "\n".join([
        "Curriculum packs for Synapse: the 12 public domains, one pack each, plus the complete curriculum.",
        "",
        "The app installs them for you (**Settings ⚙ → Curriculum Store & Addons**). This release is updated "
        "in place when lessons change; a pack is only replaced when its content changed. App releases are "
        "published separately.",
        "",
        "| Pack | Lessons | Labs | Updated |",
        "|---|---:|---:|---|",
        *rows,
        "",
        "`curriculum.json` lists each pack's content digest and the commit it was built from.",
    ])


def fetch_previous_index() -> dict:
    """curriculum.json from the GitHub curriculum release (public), else Gitea, else {}."""
    import json
    rel = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{CURRICULUM_TAG}",
                       headers=_github_headers())
    sources = []
    if rel.ok:
        sources += [a["browser_download_url"] for a in rel.json().get("assets", []) if a["name"] == CURRICULUM_INDEX]
    g = requests.get(f"{GITEA_URL.rstrip('/')}/api/v1/repos/{GITEA_REPO}/releases/tags/{CURRICULUM_TAG}",
                     auth=(GITEA_USER, GITEA_PASS))
    if g.ok:
        sources += [a["browser_download_url"] for a in g.json().get("assets", []) if a["name"] == CURRICULUM_INDEX]
    for url in sources:
        r = requests.get(url, auth=(GITEA_USER, GITEA_PASS) if "github.com" not in url else None)
        if r.ok:
            try:
                return json.loads(r.text)
            except ValueError:
                pass
    return {}


def publish_curriculum():
    import json
    import tempfile
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=WORKSPACE_ROOT,
                            capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="synapse-curriculum-") as tmp:
        out = Path(tmp)
        packs = export_curriculum_packs(out)
        _require_clean_packs(list(packs.values()))
        previous = fetch_previous_index()
        index = curriculum_index(packs, commit, previous)
        changed = changed_packs(index, previous)
        print(f"[*] {len(changed)} of {len(packs)} packs changed: {', '.join(changed) or 'none'}")
        index_path = out / CURRICULUM_INDEX
        index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        assets = {n: packs[n] for n in changed}
        assets[CURRICULUM_INDEX] = index_path
        title = "Curriculum packs"
        body = curriculum_body(index)
        ok_gitea = publish_gitea(CURRICULUM_TAG, title, assets, body, replace=True)
        ok_github = publish_github(CURRICULUM_TAG, title, assets, body, replace=True)
    print("\n" + "=" * 60)
    print("🎉 [✔] Curriculum release published." if ok_gitea and ok_github
          else f"⚠️ [!] Completed with status: Gitea={ok_gitea}, GitHub={ok_github}")
    print("=" * 60)
    return ok_gitea and ok_github


def _require_clean_packs(paths=None):
    """Refuses to publish if any pack contains private or uncommitted content."""
    import subprocess as _sp
    checker = Path(__file__).resolve().parent / "check_release_packs.py"
    args = [sys.executable, str(checker)] + [str(p) for p in (paths or []) if str(p).endswith(".synpack")]
    if _sp.run(args).returncode != 0:
        print("[✘] Aborting release: pack privacy check failed (see above).")
        sys.exit(1)

def main():
    if "--curriculum" in sys.argv[1:]:
        sys.exit(0 if publish_curriculum() else 1)
    print("=" * 60)
    print(f" SYNAPSE {TAG} MULTI-PLATFORM RELEASE PUBLISHER")
    print("=" * 60)

    ok_gitea = publish_gitea()
    ok_github = publish_github()
    if not (ok_gitea and ok_github):
        print("\n" + "=" * 60)
        print(f"⚠️ [!] Completed with status: Gitea={ok_gitea}, GitHub={ok_github}")
        print("=" * 60)
        sys.exit(1)

    print("\n" + "=" * 60)
    if ok_gitea and ok_github:
        print(f"🎉 [✔] ALL RELEASES FOR {TAG} SUCCESSFULLY PUBLISHED TO GITEA & GITHUB!")
    else:
        print(f"⚠️ [!] Completed with status: Gitea={ok_gitea}, GitHub={ok_github}")
    print("=" * 60)

if __name__ == "__main__":
    main()
