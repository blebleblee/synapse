#!/usr/bin/env python3
"""Keep the private curriculum checkout and synapse's working tree in step.

Private domains live in a separate repository and are copied into
synapse's `topics/` so the app can use them. Until now that copy was made by
hand, edits made in synapse never went back, and a fresh copy would have
overwritten them. This script compares both sides and copies in one
direction:

    python scripts/sync_addons.py --addons ../synapse-addons            # report only
    python scripts/sync_addons.py --addons ../synapse-addons --pull     # addons -> synapse
    python scripts/sync_addons.py --addons ../synapse-addons --push     # synapse -> addons

Rules:
- Only files git ignores in synapse take part (never anything synapse
  tracks, never a new public file that isn't committed yet).
- A file is copied when the target is missing, or when the source is newer
  and differs. A newer target is left alone unless --force is given.
- Nothing is deleted; files present on one side only are reported.
- Chat sessions, caches and leftovers from removed features are never copied.
- The script never runs git add, commit or push. Review and commit yourself.
"""
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {"sessions", "__pycache__", ".git", "node_modules", ".regen"}
EXCLUDED_FILES = {"active_session.md", "chat_history.json", ".DS_Store", "MASTERED_GUIDE.md", "SUMMARY.md"}


def is_excluded(rel: str) -> bool:
    parts = rel.split("/")
    return any(p in EXCLUDED_DIRS for p in parts[:-1]) or parts[-1] in EXCLUDED_FILES


def walk(topics: Path) -> set[str]:
    out = set()
    if not topics.is_dir():
        return out
    for root, dirs, files in os.walk(topics):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in files:
            rel = (Path(root) / name).relative_to(topics).as_posix()
            if not is_excluded(rel):
                out.add(rel)
    return out


@dataclass
class Plan:
    copy: list[str] = field(default_factory=list)
    target_newer: list[str] = field(default_factory=list)
    only_in_target: list[str] = field(default_factory=list)
    same: int = 0


def make_plan(src: Path, dst: Path, allowed: Callable[[str], bool], force: bool = False) -> Plan:
    plan = Plan()
    src_files = {r for r in walk(src) if allowed(r)}
    dst_files = {r for r in walk(dst) if allowed(r)}
    for rel in sorted(src_files):
        s, d = src / rel, dst / rel
        if not d.exists():
            plan.copy.append(rel)
        elif filecmp.cmp(s, d, shallow=False):
            plan.same += 1
        elif force or s.stat().st_mtime > d.stat().st_mtime:
            plan.copy.append(rel)
        else:
            plan.target_newer.append(rel)
    plan.only_in_target = sorted(dst_files - src_files)
    return plan


def apply_plan(plan: Plan, src: Path, dst: Path) -> None:
    for rel in plan.copy:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, target)


def synapse_ignored(paths: Iterable[str]) -> set[str]:
    """Return the subset of topic-relative paths that git ignores in synapse."""
    paths = list(paths)
    if not paths:
        return set()
    res = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        cwd=ROOT, input="\n".join(f"topics/{p}" for p in paths), capture_output=True, text=True,
    )
    if res.returncode not in (0, 1):
        sys.exit(f"git check-ignore failed: {res.stderr.strip()}")
    tracked = set(subprocess.run(["git", "ls-files", "topics"], cwd=ROOT, capture_output=True,
                                 text=True, check=True).stdout.splitlines())
    return filter_ignored(res.stdout.splitlines(), tracked)


def filter_ignored(check_ignore_lines: Iterable[str], tracked: set[str]) -> set[str]:
    """Paths git reported as ignored, minus anything synapse tracks anyway."""
    return {line.removeprefix("topics/") for line in check_ignore_lines
            if line and line not in tracked}


def summarize(plan: Plan) -> dict[str, list[int]]:
    rows: dict[str, list[int]] = {}
    for idx, items in enumerate((plan.copy, plan.target_newer, plan.only_in_target)):
        for rel in items:
            rows.setdefault(rel.split("/")[0], [0, 0, 0])[idx] += 1
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--addons", required=True, type=Path, help="path to the private curriculum checkout")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--pull", action="store_true", help="copy addons -> synapse")
    mode.add_argument("--push", action="store_true", help="copy synapse -> addons")
    ap.add_argument("--force", action="store_true", help="also overwrite targets that are newer")
    ap.add_argument("--list", action="store_true", help="print every path, not just totals")
    ap.add_argument("--only", action="append", metavar="DOMAIN", help="limit to this top-level folder (repeatable)")
    args = ap.parse_args()

    addons_topics = args.addons.resolve() / "topics"
    synapse_topics = ROOT / "topics"
    if not addons_topics.is_dir():
        sys.exit(f"{addons_topics} does not exist")

    candidates = walk(addons_topics) | walk(synapse_topics)
    allowed_set = synapse_ignored(candidates)
    only = set(args.only or [])
    allowed = (lambda rel: rel in allowed_set and (not only or rel.split("/")[0] in only))

    src, dst = (synapse_topics, addons_topics) if args.push else (addons_topics, synapse_topics)
    plan = make_plan(src, dst, allowed, force=args.force)
    direction = "synapse -> addons" if args.push else "addons -> synapse"
    print(f"Direction {direction}: {len(plan.copy)} to copy, {len(plan.target_newer)} newer in target (kept), "
          f"{len(plan.only_in_target)} only in target, {plan.same} identical")
    for top, (c, n, o) in sorted(summarize(plan).items()):
        print(f"  {top}: copy={c} target-newer={n} only-in-target={o}")
    if args.list:
        for label, items in (("copy", plan.copy), ("target-newer", plan.target_newer), ("only-in-target", plan.only_in_target)):
            for rel in items:
                print(f"{label}\t{rel}")
    if args.pull or args.push:
        apply_plan(plan, src, dst)
        print(f"Copied {len(plan.copy)} files. Nothing was committed.")
    else:
        print("Report only. Use --pull or --push to copy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
