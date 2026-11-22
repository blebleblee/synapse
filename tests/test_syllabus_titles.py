"""
Course titles come from each public domain's SYLLABUS.md ("- **Title** (`disc/course/`)").
Two courses with the same title in one discipline look like a duplicate entry
in the sidebar and graph (e.g. two "Large Language Models" under AI).
"""
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC_DOMAINS = (
    "arts", "business", "computing", "crafts", "economics", "engineering", "formal_sciences",
    "health_sciences", "humanities", "languages", "motorsports", "natural_sciences",
)
ENTRY = re.compile(r"^-\s+\*\*(.*?)\*\*\s+\(`(.*?)/`\)", re.M)


def test_course_titles_are_unique_within_a_discipline():
    duplicates = []
    for domain in PUBLIC_DOMAINS:
        syllabus = REPO / "topics" / domain / "SYLLABUS.md"
        if not syllabus.exists():
            continue
        courses_by_title = defaultdict(set)
        for title, rel in ENTRY.findall(syllabus.read_text(encoding="utf-8")):
            parts = rel.split("/")
            if len(parts) >= 2:
                courses_by_title[(parts[0], title.strip().lower())].add(parts[1])
        duplicates += [f"{domain}/{disc}: '{t}' -> {sorted(c)}"
                       for (disc, t), c in courses_by_title.items() if len(c) > 1]
    assert duplicates == []
