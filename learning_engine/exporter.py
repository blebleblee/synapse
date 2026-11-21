"""
Curriculum Book & Handbook Exporter
Stitches canonical masterclass topics and lessons into unified printable handbooks.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from .security import WORKSPACE_ROOT, TOPICS_DIR, get_workspace_root
from .topic_manager import get_topic_tree, get_unit_lessons

def get_exports_dir() -> Path:
    return get_workspace_root() / "exports"

EXPORTS_DIR = get_exports_dir()

def export_handbook(domain: str, level: Optional[str] = None) -> Path:
    """
    Compiles an entire curriculum domain into a cohesive, textbook-grade Markdown handbook.
    """
    out_dir = get_exports_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    domain_dir = TOPICS_DIR / domain
    if not domain_dir.exists():
        raise ValueError(f"Domain '{domain}' does not exist.")

    domain_title = domain.replace('_', ' ').title()
    book_title = f"Synapse Masterclass: {domain_title}"
    output_path = out_dir / f"{domain}_handbook.md"

    lines = [
        f"# {domain_title}: Comprehensive Engineering & Socratic Handbook\n",
        "**Standard:** Canonical 3-Level Masterclass Taxonomy",
        "**Curriculum Repository:** `ai/synapse`\n",
        "## Table of Contents\n"
    ]

    # Collect topics
    tree = get_topic_tree()
    domain_data = tree.get(domain, {"categories": {}})

    toc_entries = []
    chapter_content = []

    for cat_slug, subtopics in domain_data.get("categories", {}).items():
        cat_title = cat_slug.replace("_", " ").title()
        toc_entries.append(f"- **{cat_title}**")

        for sub_slug, sdata in subtopics.items():
            sub_title = sdata.get("display_name", sub_slug.replace("_", " ").title())
            anchor = sub_slug.replace("_", "-")
            toc_entries.append(f"  - [{sub_title}](#{anchor})")

            sub_path = Path(sdata["full_path"])
            chapter_content.append(f"\n---\n\n<a id='{anchor}'></a>\n# {sub_title} ({cat_title})\n")

            # 1. Summary if present
            for sum_name in ["SUMMARY.md", "summary.md"]:
                sum_path = sub_path / sum_name
                if sum_path.exists():
                    chapter_content.append("### Executive Summary\n")
                    chapter_content.append(sum_path.read_text(encoding="utf-8").strip())
                    chapter_content.append("\n\n")
                    break

            # 2. Sequential Masterclass Lessons
            lessons = get_unit_lessons(sub_path)
            for l in lessons:
                p = Path(l["path"])
                if p.exists():
                    chapter_content.append(f"### {l['title']}\n")
                    chapter_content.append(p.read_text(encoding="utf-8").strip())
                    chapter_content.append("\n\n")

            # 3. Operational Labs
            for lab_name in ["labs.md", "LABS.md"]:
                lab_path = sub_path / lab_name
                if lab_path.exists():
                    chapter_content.append("### Operational Verification Labs\n")
                    chapter_content.append(lab_path.read_text(encoding="utf-8").strip())
                    chapter_content.append("\n\n")
                    break

    full_text = "\n".join(lines) + "\n" + "\n".join(toc_entries) + "\n\n" + "\n".join(chapter_content)
    output_path.write_text(full_text, encoding="utf-8")
    return output_path
