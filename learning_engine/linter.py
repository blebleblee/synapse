"""
Curriculum Content Quality & Semantic Relevance Linter
Validates markdown structure, technical depth, placeholder elimination,
Mermaid diagram syntax, and cross-domain tool bleed.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from .security import WORKSPACE_ROOT, TOPICS_DIR

FORBIDDEN_PLACEHOLDERS = [
    r"//\s*TODO",
    r"<!--\s*TODO",
    r"#\s*TODO",
    r"\bTODO\b",
    r"\[TRUNCATED\]",
    r"insert code here",
    r"\[insert\s+",
    r"\bto be determined\b",
    r"\bexercise for the reader\b"
]

CROSS_DOMAIN_BLEED_RULES = [
    {
        "pattern": r"\bbpftool\b",
        "allowed_topics": [
            "ebpf",
            "observability",
            "linux_kernel",
            "device_drivers",
            "linux_device_drivers",
            "linux"
        ],
        "message": "Low-level eBPF inspection utility (bpftool) referenced in an off-topic course"
    },
    {
        "pattern": r"The operational verification lab for the Core domain within",
        "allowed_topics": [],
        "message": "Legacy generic template stub detected; requires topic-specific masterclass rework"
    }
]

def lint_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    issues = []
    file_path = file_path.resolve()
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"file": str(file_path), "severity": "error", "message": f"Read error: {e}"}]

    rel_file = str(file_path.relative_to(WORKSPACE_ROOT))
    parts = file_path.relative_to(TOPICS_DIR).parts if file_path.is_relative_to(TOPICS_DIR) else ()
    subtopic_id = parts[2] if len(parts) >= 3 else ""

    # 1. Outer Code Fence Check (File must not start with ```markdown)
    stripped = content.strip()
    if stripped.startswith("```markdown") or stripped.startswith("```md"):
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "OUTER_CODE_FENCE",
            "message": "File is wrapped in an outer markdown code fence (causes file to render as a code box)"
        })

    # 2. Mermaid Subgraph Syntax Check (subgraph "..." without an ID fails in Mermaid.js)
    invalid_subgraphs = re.findall(r'subgraph\s+"([^"\n]+)"', content)
    if invalid_subgraphs:
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "INVALID_MERMAID_SUBGRAPH",
            "message": f"Found {len(invalid_subgraphs)} Mermaid subgraph(s) without alphanumeric IDs (e.g. 'subgraph \"{invalid_subgraphs[0]}\"'). Must be 'subgraph id [\"Title\"]'."
        })

    # 3. Cross-Domain Bleed & Generic Template Detection
    for rule in CROSS_DOMAIN_BLEED_RULES:
        if subtopic_id not in rule["allowed_topics"]:
            if re.search(rule["pattern"], content, re.IGNORECASE):
                issues.append({
                    "file": rel_file,
                    "severity": "error",
                    "code": "CROSS_DOMAIN_BLEED",
                    "message": rule["message"]
                })

    # 4. File Size & Depth Thresholds
    size_bytes = len(content.encode("utf-8"))
    min_size = 2500 if "lesson_" in file_path.name else 1200
    if size_bytes < min_size:
        issues.append({
            "file": rel_file,
            "severity": "warning",
            "code": "LOW_DEPTH",
            "message": f"File is brief ({size_bytes} bytes, expected > {min_size} bytes for masterclass rigor)"
        })

    # 5. Section Heading Completeness
    headings = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    if len(headings) < 2 and "labs" not in file_path.name.lower():
        issues.append({
            "file": rel_file,
            "severity": "warning",
            "code": "INSUFFICIENT_SECTIONS",
            "message": f"Found only {len(headings)} top-level sections (expected >= 2)"
        })

    # 6. Placeholder Detection
    for pattern in FORBIDDEN_PLACEHOLDERS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append({
                "file": rel_file,
                "severity": "error",
                "code": "FORBIDDEN_PLACEHOLDER",
                "message": f"Contains forbidden placeholder or truncated marker matching '{pattern}'"
            })

    # 7. Untagged Code Blocks
    untagged = re.findall(r"```\s*\n", content)
    if untagged:
        issues.append({
            "file": rel_file,
            "severity": "warning",
            "code": "UNTAGGED_CODE_BLOCK",
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
    clean_files = scanned_files - len({i["file"] for i in all_issues if i["severity"] == "error"})

    return {
        "scanned_files": scanned_files,
        "clean_files": clean_files,
        "error_count": error_count,
        "warning_count": warning_count,
        "passed": error_count == 0,
        "issues": all_issues
    }
