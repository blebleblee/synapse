"""
The Knowledge Graph's curated learning pathways (GraphModal.tsx) link to
courses by path. Every link must open a course that exists in the public
curriculum; a dead link shows "Topic not found" when the learner clicks it.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRAPH = REPO / "app" / "frontend" / "src" / "components" / "GraphModal.tsx"
# The public domains (AGENTS.md); pathways must not point anywhere else.
PUBLIC_DOMAINS = {
    "arts", "business", "computing", "crafts", "economics", "engineering", "formal_sciences",
    "health_sciences", "humanities", "languages", "motorsports", "natural_sciences",
}


def _is_public_course(course: str) -> bool:
    if course.split("/")[0] not in PUBLIC_DOMAINS:
        return False
    course_dir = REPO / "topics" / course
    return course_dir.is_dir() and any(course_dir.glob("lesson_*.md"))


def test_every_pathway_step_opens_a_public_course():
    paths = re.findall(r"path:\s*'([^']+)'", GRAPH.read_text(encoding="utf-8"))
    assert paths, "no pathway paths found; did the GraphModal format change?"
    missing = sorted({p for p in paths if not _is_public_course("/".join(p.split("/")[:3]))})
    assert missing == [], f"pathway steps pointing at missing courses: {missing}"
