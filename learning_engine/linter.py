"""
Curriculum Content Quality & Semantic Relevance Linter
Validates markdown structure, technical depth, placeholder elimination,
Mermaid diagram syntax, code fence integrity, and cross-domain tool bleed.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from .security import WORKSPACE_ROOT, TOPICS_DIR
from .domain_profiles import domain_profile

FORBIDDEN_TEXT_PLACEHOLDERS = [
    r"//\s*TODO",
    r"<!--\s*TODO",
    r"#\s*TODO",
    r"\bTODO:\s*",
    r"\bFIXME:\s*",
    r"insert code here",
    r"\[insert\s+(?:code|text|here|your|content|summary|data|claim|value|description|step)",
    r"\[to be determined\]",
    r"\bTBD\b",
    r"(?i)\b(?:status|date|author|version):\s*to be determined\b",
    r"\bexercise for the reader\b"
]

CROSS_DOMAIN_BLEED_RULES = [
    {
        "id": "bpftool",
        "pattern": r"\bbpftool\b",
        # Other domains allow it in their DOMAIN_PROFILE.json ("linter_allow").
        "allowed_domains": ["computing"],
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
        "message": "Low-level Linux kernel eBPF utility (bpftool) referenced in an off-topic non-computing domain"
    },
    {
        "pattern": r"The operational verification lab for the Core domain within",
        "allowed_topics": [],
        "message": "Legacy generic template stub detected; requires topic-specific masterclass rework"
    }
]

def _display_path(path: Path) -> str:
    """Path for reports: relative to the workspace, or to the topics folder's
    parent when SYNAPSE_TOPICS_DIR points outside the workspace."""
    for base in (WORKSPACE_ROOT, Path(TOPICS_DIR).parent):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def lint_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    issues = []
    file_path = file_path.resolve()
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"file": str(file_path), "severity": "error", "message": f"Read error: {e}"}]

    rel_file = _display_path(file_path)
    parts = file_path.relative_to(TOPICS_DIR).parts if file_path.is_relative_to(TOPICS_DIR) else ()
    domain = parts[0] if len(parts) >= 1 else ""
    category = parts[1] if len(parts) >= 2 else ""
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
        allowed_domains = rule.get("allowed_domains", [])
        allowed_topics = rule.get("allowed_topics", [])
        is_allowed = ((domain in allowed_domains) or (subtopic_id in allowed_topics)
                      or (rule.get("id") and rule["id"] in domain_profile(domain).get("linter_allow", [])))
        if not is_allowed:
            if re.search(rule["pattern"], content, re.IGNORECASE):
                issues.append({
                    "file": rel_file,
                    "severity": "error",
                    "code": "CROSS_DOMAIN_BLEED",
                    "message": rule["message"]
                })

    # 5. File Size & Truncation Checks
    size_bytes = len(content.encode("utf-8"))
    min_size = 2500 if "lesson_" in file_path.name else 1200
    if size_bytes < min_size:
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "TRUNCATED_OR_INCOMPLETE",
            "message": f"File is truncated or brief ({size_bytes} bytes, expected >= {min_size} bytes for masterclass completeness)"
        })

    # 5b. LLM Refusal & Upstream API Failure Stub Detection
    refusal_patterns = [
        r"\bI can't write (?:this|code|about|essays? for you|that|such content)\b",
        r"\bI cannot write (?:this|code|about|essays? for you|that|such content)\b",
        r"\bI cannot fulfill this request\b",
        r"\bI cannot assist with this\b",
        r"\bI won't write this\b",
        r"\bI'm not going to write this\b",
        r"\bI'll decline regardless\b",
        r"\bUpstream service temporarily unavailable\b"
    ]
    for rpat in refusal_patterns:
        if re.search(rpat, content, re.IGNORECASE):
            issues.append({
                "file": rel_file,
                "severity": "error",
                "code": "LLM_REFUSAL_STUB",
                "message": f"File contains an unresolved LLM refusal or API failure stub matching '{rpat}'"
            })
            break

    # 5b2. Chat preamble before the content, and a missing "# " title. The
    # sidebar takes a lesson's title from its first "# " line, so a reply that
    # starts "Here is the fully corrected Markdown:" shows that as the title.
    first_line = next((l.strip() for l in content.splitlines() if l.strip()), "")
    if re.match(r"^(here is|here's|here are|sure|certainly|of course|absolutely|below is)\b.{0,200}:$", first_line, re.IGNORECASE):
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "MODEL_PREAMBLE",
            "message": f"File starts with a model preamble instead of content: '{first_line[:80]}'"
        })
    elif (file_path.name.startswith("lesson_") or file_path.name == "labs.md") and not first_line.startswith("# "):
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "MISSING_TITLE",
            "message": "File does not start with a '# ' title line"
        })

    # 5c. Prompt / Context Echo Leak Detection
    context_leak_patterns = [
        r"--- Newly Discovered Project Context ---",
        r"--- End of Context from:",
        r"--- End Project Context ---"
    ]
    for cpat in context_leak_patterns:
        if re.search(cpat, content):
            issues.append({
                "file": rel_file,
                "severity": "error",
                "code": "CONTEXT_LEAK_CORRUPTION",
                "message": f"File is corrupted by leaked system prompt context matching '{cpat}'"
            })
            break

    # 6. Section Heading Completeness
    headings = re.findall(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
    if len(headings) < 2 and "labs" not in file_path.name.lower():
        issues.append({
            "file": rel_file,
            "severity": "error",
            "code": "INCOMPLETE_SECTIONS",
            "message": f"Lesson has only {len(headings)} section(s) (expected >= 2, likely truncated early)"
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

    # 8. Untagged Code Blocks (State-aware: inspect opening fences only)
    untagged_count = 0
    in_code_block = False
    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("```"):
            if not in_code_block:
                lang = trimmed[3:].strip()
                if not lang:
                    untagged_count += 1
                in_code_block = True
            else:
                in_code_block = False

    if untagged_count > 0:
        issues.append({
            "file": rel_file,
            "severity": "warning",
            "code": "UNTAGGED_CODE_BLOCK",
            "message": f"Found {untagged_count} opening code block(s) without language identifier"
        })

    # 9. Operational Labs Integrity Check
    if file_path.name == "labs.md":
        has_exercises = bool(re.search(r"##\s+(?:Exercise|Lab|Scenario|Mission|Part|Drill|Project|Phase|Milestone|Track|Workflow|Profiling|\d+\.)", content, re.IGNORECASE))
        if not has_exercises and len(headings) < 3:
            issues.append({
                "file": rel_file,
                "severity": "error",
                "code": "INCOMPLETE_LABS",
                "message": "Labs file does not appear to contain structured hands-on exercises or operational scenarios"
            })

    # 10. Abrupt Sentence / File Truncation Check
    clean_lines = [l.strip() for l in content.splitlines() if l.strip()]
    if clean_lines:
        last_line = clean_lines[-1]
        valid_terminators = ('.', '!', '?', '"', "'", "```", "-->", "$$", "]", "}", ")", ">", ":", ";", "|", "*", "_", "~", "-")
        if not (last_line == "---" or any(last_line.endswith(c) for c in valid_terminators)):
            issues.append({
                "file": rel_file,
                "severity": "error",
                "code": "ABRUPT_TRUNCATION",
                "message": f"File appears cut off mid-sentence or mid-word (ends with '{last_line[-40:]}')"
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

        rel_dir = _display_path(topic_dir)

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

        # Two lessons with the same title look like one lesson listed twice.
        titles = {}
        for f in lesson_files:
            try:
                head = f.read_text(encoding="utf-8").lstrip().split("\n", 1)[0]
            except OSError:
                continue
            if head.startswith("# "):
                key = re.sub(r"^#\s+Lesson\s+\d+\s*:\s*", "", head).strip().lower()
                titles.setdefault(key, []).append(f.name)
        for title, names in titles.items():
            if len(names) > 1:
                all_issues.append({
                    "file": rel_dir,
                    "severity": "error",
                    "code": "DUPLICATE_LESSON_TITLE",
                    "message": f"Lessons {', '.join(sorted(names))} share the title '{title}'"
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
