"""
Curriculum Content Quality Linter
Validates markdown structure, technical depth, section completeness, and placeholder elimination.
"""

import re
from pathlib import Path
from typing import Dict, List, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"

FORBIDDEN_PLACEHOLDERS = [
    r"//\s*TODO",
    r"<!--\s*TODO",
    r"#\s*TODO",
    r"\[TRUNCATED\]",
    r"insert code here",
    r"placeholder",
    r"to be determined",
    r"exercise for the reader"
]

def lint_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    issues = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"file": str(file_path), "severity": "error", "message": f"Read error: {e}"}]

    # 1. File Size & Depth Thresholds
    size_bytes = len(content.encode("utf-8"))
    min_size = 3000 if "LESSON" in file_path.name else 1500
    if size_bytes < min_size:
        issues.append({
            "file": str(file_path.relative_to(WORKSPACE_ROOT)),
            "severity": "warning",
            "message": f"File is short ({size_bytes} bytes, expected > {min_size} bytes for depth)"
        })

    # 2. Section Heading Completeness
    headings = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    if len(headings) < 3:
        issues.append({
            "file": str(file_path.relative_to(WORKSPACE_ROOT)),
            "severity": "error",
            "message": f"Insufficient section structure (found only {len(headings)} sections, expected >= 3)"
        })

    # 3. Placeholder Detection
    for pattern in FORBIDDEN_PLACEHOLDERS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append({
                "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                "severity": "error",
                "message": f"Contains forbidden placeholder or truncated marker matching '{pattern}'"
            })

    # 4. Untagged Code Blocks
    untagged = re.findall(r"```\s*\n", content)
    if untagged:
        issues.append({
            "file": str(file_path.relative_to(WORKSPACE_ROOT)),
            "severity": "warning",
            "message": f"Found {len(untagged)} code block(s) without language identifier"
        })

    return issues

def lint_curriculum(domain_filter: str = "") -> Dict[str, Any]:
    all_issues = []
    scanned_files = 0

    target_dir = TOPICS_DIR / domain_filter if domain_filter else TOPICS_DIR

    for md_file in target_dir.glob("**/*.md"):
        if md_file.name in ["GEMINI.md", "SYLLABUS.md"]:
            continue

        scanned_files += 1
        issues = lint_markdown_file(md_file)
        all_issues.extend(issues)

    error_count = sum(1 for i in all_issues if i["severity"] == "error")
    warning_count = sum(1 for i in all_issues if i["severity"] == "warning")

    return {
        "scanned_files": scanned_files,
        "error_count": error_count,
        "warning_count": warning_count,
        "passed": error_count == 0,
        "issues": all_issues
    }
