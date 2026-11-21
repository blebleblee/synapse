#!/usr/bin/env python3
"""
Rewrites the title and notes of an existing release on Gitea and GitHub from
CHANGELOG.md, without touching its files.

Usage:
  python scripts/update_release_notes.py            # current VERSION
  python scripts/update_release_notes.py 1.2.1 --dry-run
  python scripts/update_release_notes.py 1.1.0 --keep-title   # older release: notes only
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("publish", ROOT / "scripts" / "publish_all_releases.py")
publish = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publish)


def main(argv):
    dry = "--dry-run" in argv
    keep_title = "--keep-title" in argv
    args = [a for a in argv if not a.startswith("--")]
    if args:
        publish.VER = args[0].lstrip("v")
        publish.TAG = f"v{publish.VER}"
    title = None if keep_title else publish.release_title()
    print(f"[*] {publish.TAG}: title {'unchanged' if keep_title else repr(title)}")
    if dry:
        print(publish.generate_release_body(has_installers=True))
        return 0
    return 0 if publish.update_release_text(title) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
