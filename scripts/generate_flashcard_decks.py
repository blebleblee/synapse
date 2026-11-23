#!/usr/bin/env python3
"""
Generates flashcards.csv for public courses that have none, so decks ship
with the curriculum instead of being generated (tens of seconds, with a
small local model) the first time a learner opens them.

Only git-tracked courses in the 12 public domains are considered. Courses
that already have a deck are skipped; delete a deck to regenerate it.

    python scripts/generate_flashcard_decks.py --dry-run           # what would run
    python scripts/generate_flashcard_decks.py --only computing --limit 5
    python scripts/generate_flashcard_decks.py                     # every missing deck

Needs an Anthropic-compatible API: ANTHROPIC_API_KEY (or VNAIPRO_API_KEY with
VNAIPRO_BASE_URL). The model defaults to claude-sonnet-4-6.
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PUBLIC_DOMAINS = ("arts", "business", "computing", "crafts", "economics", "engineering", "formal_sciences",
                  "health_sciences", "humanities", "languages", "motorsports", "natural_sciences")
# Shipped decks: a stronger model and more of the course than the app's
# on-demand default (8 cards from 4 lessons, 6,000 characters).
DECK_BUDGET = dict(cards=12, max_lessons=12, per_file_chars=3000, context_chars=30000)


def public_courses(only=None, files=None):
    """Courses with git-tracked lessons in the public domains (`files`: paths
    as `git ls-files topics` prints them; read from git when omitted)."""
    if files is None:
        files = subprocess.run(["git", "ls-files", "topics"], cwd=ROOT, capture_output=True, text=True,
                               check=True).stdout.split()
    courses = set()
    for f in files:
        parts = Path(f).parts
        if len(parts) == 5 and parts[1] in PUBLIC_DOMAINS and parts[4].startswith("lesson_") and parts[4].endswith(".md"):
            if only is None or parts[1] == only:
                courses.add("/".join(parts[1:4]))
    return sorted(courses)


def missing_decks(courses, topics_dir: Path):
    return [c for c in courses if not (topics_dir / c / "flashcards.csv").exists()]


def run(courses, provider, generate):
    done, failed = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(generate, c, provider=provider, **DECK_BUDGET): c for c in courses}
        for fut in as_completed(futures):
            c = futures[fut]
            try:
                fut.result()
                done.append(c)
                print(f"[✔] {c}", flush=True)
            except Exception as e:
                failed.append((c, str(e)[:200]))
                print(f"[✘] {c}: {str(e)[:200]}", flush=True)
    return done, failed


def main(argv=None, files=None):
    ap = argparse.ArgumentParser(description="Generate missing flashcard decks for the public courses.")
    ap.add_argument("--only", choices=PUBLIC_DOMAINS, help="one domain")
    ap.add_argument("--limit", type=int, help="at most this many decks")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--dry-run", action="store_true", help="list the courses, call no model")
    args = ap.parse_args(argv)

    from learning_engine import topic_manager
    todo = missing_decks(public_courses(args.only, files=files), Path(topic_manager.TOPICS_DIR))
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(todo)} course(s) without a deck" + (f" in {args.only}" if args.only else ""))
    if args.dry_run or not todo:
        for c in todo[:20]:
            print(f"  {c}")
        return 0

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY")):
        print("[✘] No API key: set ANTHROPIC_API_KEY or VNAIPRO_API_KEY (and VNAIPRO_BASE_URL).")
        return 2
    from learning_engine.models import get_provider
    from learning_engine.flashcards import generate_flashcards
    provider = get_provider(provider_type="anthropic", model=args.model)
    done, failed = run(todo, provider, generate_flashcards)
    print(f"\n{len(done)} deck(s) written, {len(failed)} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
