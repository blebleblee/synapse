"""
Full-Text Search Engine
Indexes and searches across all generated curriculum markdown units.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from .security import WORKSPACE_ROOT, TOPICS_DIR

def clean_snippet(text: str, match_pos: int, snippet_len: int = 160) -> str:
    start = max(0, match_pos - snippet_len // 2)
    end = min(len(text), match_pos + snippet_len // 2)
    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet

def search_curriculum(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    if not query or len(query.strip()) < 2:
        return []

    tokens = [re.escape(t.strip()) for t in query.strip().split() if t.strip()]
    if not tokens:
        return []

    regex_pattern = re.compile("|".join(tokens), re.IGNORECASE)
    results = []

    for md_path in TOPICS_DIR.glob("**/*.md"):
        if md_path.name in ["GEMINI.md", "SYLLABUS.md"]:
            continue

        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception:
            continue

        matches = list(regex_pattern.finditer(content))
        if not matches:
            continue

        # Deduce hierarchy (domain / discipline / topic / file.md)
        rel_parts = md_path.relative_to(TOPICS_DIR).parts
        if len(rel_parts) >= 3:
            domain = rel_parts[0]
            category = rel_parts[1]
            subtopic = rel_parts[2]
        else:
            domain = rel_parts[0] if len(rel_parts) > 0 else ""
            category = rel_parts[1] if len(rel_parts) > 1 else ""
            subtopic = md_path.stem

        # Extract first match snippet
        first_match = matches[0]
        snippet = clean_snippet(content, first_match.start())

        # Find closest section header
        prev_headers = re.findall(r"^#{1,3}\s+(.+)$", content[:first_match.start()], re.MULTILINE)
        section = prev_headers[-1] if prev_headers else "Introduction"

        score = len(matches) * 10
        if query.lower() in subtopic.lower():
            score += 50
        if query.lower() in content.lower():
            score += 20

        results.append({
            "domain": domain,
            "category": category,
            "subtopic": subtopic,
            "level": "masterclass",
            "file": md_path.name,
            "path": f"{domain}/{category}/{subtopic}",
            "section": section,
            "snippet": snippet,
            "match_count": len(matches),
            "score": score
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]
