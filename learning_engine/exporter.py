"""
Curriculum Book & Handbook Exporter
Stitches topic hierarchies and progressive units into unified printable handbooks.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from .topic_manager import get_topic_tree, get_unit_lessons

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"
EXPORTS_DIR = WORKSPACE_ROOT / "exports"

def export_handbook(domain: str, level: Optional[str] = None) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    domain_dir = TOPICS_DIR / domain
    if not domain_dir.exists():
        raise ValueError(f"Domain '{domain}' does not exist.")

    domain_title = domain.replace("_", " ").title()
    level_suffix = f"_{level.lower()}" if level else ""
    out_file = EXPORTS_DIR / f"{domain}{level_suffix}_handbook.md"

    lines = [
        f"# {domain_title}: Comprehensive Engineering & Socratic Handbook\n",
        f"**Target Difficulty Level:** `{level.upper() if level else 'ALL LEVELS'}`",
        f"**Curriculum Repository:** `ai/learning`\n",
        "## Table of Contents\n"
    ]

    # Collect topics
    tree = get_topic_tree()
    domain_data = tree.get(domain, {"categories": {}})

    toc_entries = []
    chapter_content = []

    for cat_slug, subtopics in domain_data["categories"].items():
        cat_title = cat_slug.replace("_", " ").title()
        toc_entries.append(f"- **{cat_title}**")

        for sub_slug, sdata in subtopics.items():
            sub_title = sdata["display_name"]
            anchor = sub_slug.replace("_", "-")
            toc_entries.append(f"  - [{sub_title}](#{anchor})")

            sub_path = Path(sdata["full_path"])
            chapter_content.append(f"\n---\n\n<a id='{anchor}'></a>\n# {sub_title} ({cat_title})\n")

            # Determine units to stitch
            target_dirs = []
            if level and (sub_path / level.lower()).exists():
                target_dirs.append(sub_path / level.lower())
            else:
                for lvl in ["beginner", "intermediate", "advanced"]:
                    if (sub_path / lvl).exists():
                        target_dirs.append(sub_path / lvl)
                if not target_dirs:
                    target_dirs.append(sub_path)

            for tdir in target_dirs:
                lvl_label = tdir.name.upper() if tdir.name in ["beginner", "intermediate", "advanced"] else "CORE"
                chapter_content.append(f"### Tier: {lvl_label}\n")

                if (tdir / "FOUNDATION.md").exists():
                    chapter_content.append("#### Foundation\n")
                    chapter_content.append((tdir / "FOUNDATION.md").read_text(encoding="utf-8"))
                    chapter_content.append("\n\n")

                for l in get_unit_lessons(tdir):
                    p = Path(l["path"])
                    if p.exists():
                        chapter_content.append(f"#### {l['title']}\n")
                        chapter_content.append(p.read_text(encoding="utf-8"))
                        chapter_content.append("\n\n")

                if (tdir / "LABS.md").exists():
                    chapter_content.append("#### Labs\n")
                    chapter_content.append((tdir / "LABS.md").read_text(encoding="utf-8"))
                    chapter_content.append("\n\n")

                if (tdir / "SUMMARY.md").exists():
                    chapter_content.append("#### Summary\n")
                    chapter_content.append((tdir / "SUMMARY.md").read_text(encoding="utf-8"))
                    chapter_content.append("\n\n")

    full_text = "\n".join(lines) + "\n" + "\n".join(toc_entries) + "\n\n" + "\n".join(chapter_content)
    out_file.write_text(full_text, encoding="utf-8")
    return out_file
