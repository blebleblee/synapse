"""Choose which part of a lesson the mentor sees with a question.

Lessons run 25-115k characters; the mentor prompt has room for a few
thousand. Instead of always sending the beginning, send the sections that
share the most words with the question (or the section the learner opened),
in lesson order, plus the lesson title.
"""
from __future__ import annotations

import re

DEFAULT_BUDGET = 9000

_HEADING = re.compile(r"^#{1,4}\s", re.M)
_FENCE = re.compile(r"^(```|~~~)", re.M)
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}|[^\sA-Za-z0-9]{2,4}")
_STOP = {
    "the", "and", "for", "with", "what", "why", "how", "does", "this", "that",
    "are", "is", "can", "you", "me", "my", "here", "lesson", "explain", "about",
    "from", "into", "when", "which", "there", "their", "would", "should", "could",
    "give", "some", "more", "than", "then", "them", "they", "have", "has", "was",
}


def _sections(text: str) -> list[str]:
    """Split at headings, ignoring '#' lines inside fenced code blocks."""
    starts = [0]
    in_fence = False
    pos = 0
    for line in text.splitlines(keepends=True):
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and _HEADING.match(line) and pos > 0:
            starts.append(pos)
        pos += len(line)
    starts.append(len(text))
    return [text[a:b] for a, b in zip(starts, starts[1:]) if text[a:b].strip()]


def _terms(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)} - _STOP


def _clip(text: str, budget: int) -> str:
    return text if len(text) <= budget else text[:budget].rsplit("\n", 1)[0]


def lesson_excerpt(text: str, question: str, section_title: str | None = None,
                   budget: int = DEFAULT_BUDGET) -> str:
    text = (text or "").strip()
    sections = _sections(text)
    # The learner asked from a specific section: that section only.
    if section_title:
        wanted = section_title.replace("#", "").strip().lower()
        for sec in sections:
            if sec.lstrip("# ").splitlines()[0].strip().lower() == wanted:
                return _clip(sec.strip(), budget)
    if len(text) <= budget:
        return text

    # The title section (lesson heading + intro) orients the model.
    head = _clip(sections[0].strip(), min(1500, budget // 4))
    q = _terms(question)
    scored = []
    for i, sec in enumerate(sections[1:], start=1):
        words = _terms(sec)
        hits = len(q & words)
        # Headings that mention the question's terms count extra.
        title_hits = len(q & _terms(sec.splitlines()[0]))
        scored.append((hits + 2 * title_hits, -i, i))
    scored.sort(reverse=True)
    # A question that names nothing in the lesson ("give me a scenario"):
    # send the opening, which states the lesson's core ideas.
    if not scored or scored[0][0] == 0:
        return _clip(text, budget)

    picked: dict[int, str] = {}
    used = len(head)
    for score, _, i in scored:
        if score == 0:
            break
        sec = sections[i].strip()
        room = budget - used - 2
        if room < 400:
            break
        if len(sec) > room:
            if picked:
                continue
            sec = _clip(sec, room)
        picked[i] = sec
        used += len(sec) + 2
    if not picked:
        return _clip(text, budget)
    body = [picked[i] for i in sorted(picked)]
    out = "\n\n".join([head, *body])
    return _clip(out, budget)
