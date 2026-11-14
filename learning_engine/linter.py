"""
Curriculum Content Quality & Semantic Relevance Linter
Validates markdown structure, technical depth, placeholder elimination,
Mermaid diagram syntax, code fence integrity, and cross-domain tool bleed.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from .security import WORKSPACE_ROOT, TOPICS_DIR

FORBIDDEN_TEXT_PLACEHOLDERS = [
    r"//\s*TODO",
    r"<!--\s*TODO",
    r"#\s*TODO",
    r"\bTODO:\s*",
    r"\bFIXME:\s*",
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
            "linux",
            "cilium",
            "cni"
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

    # 1. Outer Code Fence Check (File must not start with ```markdown or ```md)
    stripped = content.strip()
    if stripped.startswith("```markdown") or stripped.startswith("```md"):
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "OUTER_CODE_FENCE",
            "message": "File is wrapped in an outer markdown code fence (causes file to render as a code box)"
        })

    # 2. Unclosed Code Fence Check (Odd number of code fences breaks document formatting)
    code_fences = re.findall(r"^```", content, re.MULTILINE)
    if len(code_fences) % 2 != 0:
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "UNCLOSED_CODE_FENCE",
            "message": f"Found an odd number ({len(code_fences)}) of code fence markers (```). An unclosed fence corrupts markdown parsing."
        })

    # 3. Mermaid Subgraph Syntax Check (subgraph "..." without an ID fails in Mermaid.js)
    invalid_subgraphs = re.findall(r'subgraph\s+"([^"\n]+)"', content)
    if invalid_subgraphs:
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "INVALID_MERMAID_SUBGRAPH",
            "message": f"Found {len(invalid_subgraphs)} Mermaid subgraph(s) without alphanumeric IDs (e.g. 'subgraph \"{invalid_subgraphs[0]}\"'). Must be 'subgraph id [\"Title\"]'."
        })

    # 4. Cross-Domain Bleed & Generic Template Detection
    for rule in CROSS_DOMAIN_BLEED_RULES:
        if subtopic_id not in rule["allowed_topics"]:
            if re.search(rule["pattern"], content, re.IGNORECASE):
                issues.append({
                    "file": rel_file,
                    "severity": "error",
                    "code": "CROSS_DOMAIN_BLEED",
                    "message": rule["message"]
                })

    # 5. File Size & Truncation Checks
    size_bytes = len(content.encode("utf-8"))
    if size_bytes < 500:
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "CORRUPTED_FILE",
            "message": f"File is severely truncated or empty ({size_bytes} bytes). Expected complete masterclass content."
        })
    else:
        min_size = 2500 if "lesson_" in file_path.name else 1200
        if size_bytes < min_size:
            issues.append({
                "file": rel_file,
                "severity": "warning",
                "code": "LOW_DEPTH",
                "message": f"File is brief ({size_bytes} bytes, expected > {min_size} bytes for masterclass rigor)"
            })

    # 6. Section Heading Completeness
    headings = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    if len(headings) < 2 and "labs" not in file_path.name.lower():
        issues.append({
            "file": rel_file,
            "severity": "warning",
            "code": "INSUFFICIENT_SECTIONS",
            "message": f"Found only {len(headings)} top-level sections (expected >= 2)"
        })

    # 7. Context-Aware Placeholder Detection (Extract text outside code blocks)
    # Remove code blocks so programming keywords (like Rust's todo!() or regex patterns) don't trigger false positives
    text_outside_code = re.sub(r"```[\s\S]*?```", "", content)
    for pattern in FORBIDDEN_TEXT_PLACEHOLDERS:
        if re.search(pattern, text_outside_code, re.IGNORECASE):
            issues.append({
                "file": rel_file,
                "severity": "error",
                "code": "FORBIDDEN_PLACEHOLDER",
                "message": f"Contains unfulfilled author placeholder matching '{pattern}' in lesson prose"
            })

    # 8. Untagged Code Blocks
    untagged = re.findall(r"```\s*\n", content)
    if untagged:
        issues.append({
            "file": rel_file,
            "severity": "warning",
            "code": "UNTAGGED_CODE_BLOCK",
            "message": f"Found {len(untagged)} code block(s) without language identifier"
        })

    # 9. Operational Labs Integrity Check
    if file_path.name == "labs.md":
        has_exercises = bool(re.search(r"##\s+(?:Exercise|Lab|Scenario|Mission|\d+\.)", content, re.IGNORECASE))
        if not has_exercises and len(headings) < 2:
            issues.append({
                "file": rel_file,
                "severity": "warning",
                "code": "INCOMPLETE_LABS",
                "message": "Labs file does not appear to contain structured hands-on exercises or operational scenarios"
            })

    return issues

def lint_curriculum(domain_filter: str = "") -> Dict[str, Any]:
    all_issues = []
    scanned_files = 0

    target_dir = TOPICS_DIR / domain_filter if domain_filter else TOPICS_DIR

    for md_file in target_dir.glob("**/*.md"):
        # Ignore hidden folders like .workspace_sessions, .git, .cache, and topic chat sessions
        if any(part.startswith(".") for part in md_file.parts) or "sessions" in md_file.parts:
            continue
        # Ignore metadata and blueprint documents
        if md_file.name in ["GEMINI.md", "SYLLABUS.md", "README.md", "TOPIC_OUTLINE.md", "CURRICULUM_BLUEPRINT.md"]:
            continue

        scanned_files += 1
        issues = lint_markdown_file(md_file)
        all_issues.extend(issues)

    # Topic-level architectural and sequence validations
    scanned_topics = set()
    for md_file in target_dir.glob("**/lesson_*.md"):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        topic_dir = md_file.parent
        if topic_dir in scanned_topics:
            continue
        scanned_topics.add(topic_dir)

        lesson_files = sorted(list(topic_dir.glob("lesson_*.md")))
        numbers = []
        num_counts = {}
        for f in lesson_files:
            m = re.match(r"^lesson_(\d+)_", f.name)
            if m:
                n = int(m.group(1))
                numbers.append(n)
                num_counts[n] = num_counts.get(n, 0) + 1

        rel_dir = str(topic_dir.relative_to(WORKSPACE_ROOT))

        # Check for duplicate lesson numbers
        duplicates = [n for n, c in num_counts.items() if c > 1]
        if duplicates:
            all_issues.append({
                "file": rel_dir,
                "severity": "error",
                "code": "DUPLICATE_LESSON_NUMBER",
                "message": f"Topic has duplicate lesson numbers: {duplicates}"
            })

        # Check for sequence numbering gaps (e.g. 1, 2, 4 missing 3)
        if numbers:
            expected = set(range(1, max(numbers) + 1))
            missing = expected - set(numbers)
            if missing:
                all_issues.append({
                    "file": rel_dir,
                    "severity": "error",
                    "code": "MISSING_LESSON_IN_SEQUENCE",
                    "message": f"Topic directory has missing lesson number(s) in sequence: {sorted(list(missing))}"
                })

        # Check for labs.md presence in active topics
        labs_file = topic_dir / "labs.md"
        if not labs_file.exists():
            all_issues.append({
                "file": rel_dir,
                "severity": "error",
                "code": "MISSING_LABS",
                "message": "Topic is missing operational labs.md file"
            })

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
