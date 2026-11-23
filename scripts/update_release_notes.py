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
    import argparse
    # Explicit parsing: an unknown flag (--help, a typo of --dry-run) must not
    # fall through to rewriting the notes on both hosts.
    parser = argparse.ArgumentParser(description="Rewrite a release's title and notes on Gitea and GitHub from CHANGELOG.md.")
    parser.add_argument("version", nargs="?", help="release version (default: VERSION)")
    parser.add_argument("--dry-run", action="store_true", help="print the notes, change nothing")
    parser.add_argument("--keep-title", action="store_true", help="rewrite the notes only")
    opts = parser.parse_args(argv)
    dry, keep_title = opts.dry_run, opts.keep_title
    if opts.version:
        publish.VER = opts.version.lstrip("v")
        publish.TAG = f"v{publish.VER}"
    title = None if keep_title else publish.release_title()
    print(f"[*] {publish.TAG}: title {'unchanged' if keep_title else repr(title)}")
    if dry:
        print(publish.generate_release_body(has_installers=True))
        return 0
    return 0 if publish.update_release_text(title) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
