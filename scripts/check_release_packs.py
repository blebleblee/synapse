#!/usr/bin/env python3
"""
Release guard: verifies that public .synpack files contain only content that is
committed to this repository.

Private sideloaded domains and tracks live in a separate repository. They work
in the app locally, but must never be named in or bundled into a public pack.
This check fails (exit 1) if any pack:
  - contains a file outside topics/<core domain>/ (other than manifest.json),
  - contains a file that is not tracked by git (private tracks, chat sessions,
    blueprints, local edits that were never committed),
  - names a non-core domain in its manifest.

Usage:
  python scripts/check_release_packs.py                 # checks exports/packages/*.synpack
  python scripts/check_release_packs.py a.synpack b.synpack
"""

import json
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from learning_engine.packages import CORE_DOMAINS  # noqa: E402


def tracked_topic_files() -> set:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "topics"],
        capture_output=True, text=True, check=True,
    ).stdout
    return {p for p in out.split("\0") if p}


def check_pack(pack: Path, tracked: set) -> list:
    problems = []
    try:
        with tarfile.open(pack) as tar:
            members = tar.getmembers()
            manifest = {}
            if "manifest.json" in tar.getnames():
                manifest = json.load(tar.extractfile("manifest.json"))
    except (tarfile.TarError, OSError, json.JSONDecodeError) as e:
        return [f"unreadable: {e}"]

    untracked = outside = 0
    for m in members:
        if not m.isfile() or m.name == "manifest.json":
            continue
        parts = m.name.split("/")
        if len(parts) < 3 or parts[0] != "topics" or parts[1] not in CORE_DOMAINS:
            outside += 1
        elif m.name not in tracked:
            untracked += 1
    if outside:
        problems.append(f"{outside} file(s) outside the core domains")
    if untracked:
        problems.append(f"{untracked} file(s) not tracked in git (private, session or uncommitted content)")

    named = manifest.get("domains") or []
    if manifest.get("domain") not in (None, "complete") and manifest.get("domain") not in CORE_DOMAINS:
        named = list(named) + [manifest.get("domain")]
    private_named = [d for d in named if d not in CORE_DOMAINS]
    if private_named:
        problems.append(f"manifest names {len(private_named)} non-core domain(s)")
    return problems


def main(argv: list) -> int:
    packs = [Path(a) for a in argv] or sorted((REPO_ROOT / "exports" / "packages").glob("*.synpack"))
    if not packs:
        print("[!] No .synpack files to check.")
        return 1
    tracked = tracked_topic_files()
    failed = 0
    for pack in packs:
        problems = check_pack(pack, tracked)
        if problems:
            failed += 1
            print(f"[✘] {pack.name}: " + "; ".join(problems))
        else:
            print(f"[✔] {pack.name}")
    if failed:
        print(f"\n[✘] {failed} pack(s) would publish private or uncommitted content. "
              "Rebuild them with `synapse pack export <domain>` from a clean checkout.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
