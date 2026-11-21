"""
Cross-Model Independent Quality & Hallucination Reviewer
Performs blind, adversarial peer review of generated units using an independent model family
(e.g., deepseek-r1:32b or Gemini) to detect hallucinations, factual errors, and weak explanations.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from .models import get_provider, LLMProvider
from .topic_manager import resolve_subtopic, get_domain_persona
from .security import get_workspace_root
from .rewrite_safety import (
    split_markdown_chunks,
    check_rewrite,
    clean_model_markdown,
    parse_json_object,
    DEFAULT_CHUNK_CHARS,
)

WORKSPACE_ROOT = get_workspace_root()

DEFAULT_REVIEWER_MODEL = "deepseek-r1:32b"

AUDIT_SYSTEM_PROMPT = """You are a Ruthless Technical Auditor & Peer Reviewer.
Your task is to independently audit technical curriculum content for:
1. Hallucinations & Fabrications: Non-existent kernel flags, fictional APIs, fake registers, or wrong protocol states.
2. Mathematical & Logical Correctness: Incorrect formulas, broken derivations, or faulty proofs.
3. Completeness & Laziness: Placeholders (// TODO, ..., TBD), truncated code, or superficial handwaving.
4. Operational Integrity: Are commands, configurations, and manifests syntactically valid and runnable?

Be extremely strict. You have no prior relationship to the authoring model.

Return strictly a valid JSON object with this exact structure:
{
  "verdict": "VERIFIED" | "NEEDS_REVISION" | "REJECTED",
  "score": 0-100,
  "hallucinations": ["List of specific fabricated facts or false claims found, if any"],
  "factual_errors": ["List of factual or syntax errors, if any"],
  "critique": "2-3 sentences evaluating the technical depth and rigor"
}

Output valid JSON only with no markdown wrapping or preamble."""

# Verdict used when the reviewer's reply could not be parsed. It is never
# counted as verified and never triggers an automatic rewrite.
REVIEW_FAILED = "REVIEW_FAILED"
_VERDICT_RANK = {"VERIFIED": 0, "NEEDS_REVISION": 1, "REJECTED": 2}


def _audit_chunk(provider: LLMProvider, file_name: str, chunk: str, index: int, total: int) -> Dict[str, Any]:
    part_note = f" (part {index + 1} of {total}; audit only this part)" if total > 1 else ""
    prompt = f"""Audit the following technical curriculum text from '{file_name}'{part_note}:

\"\"\"
{chunk}
\"\"\"

Output valid JSON only."""
    try:
        raw = provider.generate(prompt, system_instruction=AUDIT_SYSTEM_PROMPT)
    except Exception as e:
        return {"verdict": REVIEW_FAILED, "error": f"reviewer call failed: {e}"}

    report = parse_json_object(raw)
    if not report or report.get("verdict") not in _VERDICT_RANK:
        return {"verdict": REVIEW_FAILED, "error": "reviewer reply was not a valid audit JSON object"}
    return report


def _merge_reports(parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combines per-chunk reports: worst verdict, lowest score, all findings."""
    failed = [i for i, r in enumerate(parts) if r.get("verdict") == REVIEW_FAILED]
    ok = [r for r in parts if r.get("verdict") != REVIEW_FAILED]
    merged: Dict[str, Any] = {
        "hallucinations": [h for r in ok for h in (r.get("hallucinations") or [])],
        "factual_errors": [e for r in ok for e in (r.get("factual_errors") or [])],
        "critique": " ".join(str(r.get("critique", "")).strip() for r in ok if r.get("critique")).strip(),
        "parts": parts,
    }
    if failed:
        merged["verdict"] = REVIEW_FAILED
        merged["score"] = None
        merged["error"] = f"{len(failed)} of {len(parts)} part(s) could not be reviewed: " + "; ".join(
            str(parts[i].get("error")) for i in failed[:3]
        )
    else:
        merged["verdict"] = max((r["verdict"] for r in ok), key=lambda v: _VERDICT_RANK[v])
        scores = [r.get("score") for r in ok if isinstance(r.get("score"), (int, float))]
        merged["score"] = min(scores) if scores else None
    return merged


def audit_content(
    file_path: Path,
    reviewer_provider: Optional[str] = None,
    reviewer_model: Optional[str] = None,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
) -> Dict[str, Any]:
    """
    Audits the whole document. Long documents are split at headings and each
    part is audited separately, so nothing beyond a fixed prefix goes unreviewed.
    An unparseable reviewer reply yields REVIEW_FAILED, never VERIFIED.
    """
    if not file_path.exists():
        return {"error": f"File {file_path} not found", "verdict": REVIEW_FAILED}

    content = file_path.read_text(encoding="utf-8")
    if len(content.strip()) < 100:
        return {
            "verdict": "REJECTED",
            "score": 10,
            "hallucinations": ["File is empty or truncated"],
            "factual_errors": ["Insufficient content"],
            "critique": "File is virtually empty.",
            "file": str(file_path.relative_to(WORKSPACE_ROOT)),
        }

    provider = get_provider(
        provider_type=reviewer_provider,
        model=reviewer_model or DEFAULT_REVIEWER_MODEL
    )

    chunks = split_markdown_chunks(content, chunk_chars)
    parts = [_audit_chunk(provider, file_path.name, c, i, len(chunks)) for i, c in enumerate(chunks)]
    report = _merge_reports(parts)
    report["chunks"] = chunks
    report["file"] = str(file_path.relative_to(WORKSPACE_ROOT))
    return report


def _fix_chunk(provider: LLMProvider, chunk: str, findings: Dict[str, Any], index: int, total: int) -> Tuple[Optional[str], str]:
    part_note = (
        f"This is part {index + 1} of {total} of a longer document. Rewrite ONLY this part; "
        "keep every heading exactly as written and in the same order.\n"
        if total > 1 else
        "Keep every heading exactly as written and in the same order.\n"
    )
    fix_prompt = f"""You are correcting a technical curriculum document that failed peer review.
Issues Found:
- Hallucinations: {findings.get('hallucinations')}
- Factual Errors: {findings.get('factual_errors')}
- Critique: {findings.get('critique')}

{part_note}
Original Text:
\"\"\"
{chunk}
\"\"\"

Rewrite this text in full, correcting the factual inaccuracies listed above and eliminating placeholders.
Do not shorten or summarize it. Output clean Markdown only."""
    try:
        fixed = clean_model_markdown(provider.generate(fix_prompt))
    except Exception as e:
        return None, f"rewrite call failed: {e}"
    ok, reason = check_rewrite(chunk, fixed)
    if not ok:
        return None, reason
    # Preserve the chunk's trailing whitespace so chunks rejoin cleanly.
    trailing = chunk[len(chunk.rstrip()):]
    return fixed.rstrip() + (trailing or "\n"), "ok"


def review_and_fix_unit(
    unit_dir: Path,
    reviewer_provider: Optional[str] = None,
    reviewer_model: Optional[str] = None,
    auto_fix: bool = False
) -> Dict[str, Any]:
    """
    Reviews every lesson in a unit. With auto_fix, only the parts that failed
    review are rewritten, each rewrite must pass check_rewrite, and parts that
    fail it keep their original text. The file is rewritten only if at least
    one part was successfully corrected.
    """
    unit_reports = []
    has_issues = False
    review_failed = False

    target_files = list(unit_dir.rglob("*.md"))
    for md_file in target_files:
        if md_file.name in ["SUMMARY.md", "README.md"]:
            continue
        report = audit_content(md_file, reviewer_provider, reviewer_model)
        chunks = report.pop("chunks", None)
        parts = report.get("parts") or []
        unit_reports.append(report)

        verdict = report.get("verdict")
        if verdict == REVIEW_FAILED:
            review_failed = True
            continue
        if verdict not in ("NEEDS_REVISION", "REJECTED"):
            continue

        has_issues = True
        if not auto_fix or not chunks or len(chunks) != len(parts):
            continue

        print(f"[!] Auto-fixing {md_file.relative_to(WORKSPACE_ROOT)} based on audit critique...")
        provider = get_provider(provider_type=reviewer_provider, model=reviewer_model or DEFAULT_REVIEWER_MODEL)
        new_chunks = list(chunks)
        fixed_parts, rejected = 0, []
        for i, (chunk, part) in enumerate(zip(chunks, parts)):
            if part.get("verdict") not in ("NEEDS_REVISION", "REJECTED"):
                continue
            replacement, reason = _fix_chunk(provider, chunk, part, i, len(chunks))
            if replacement is None:
                rejected.append(f"part {i + 1}: {reason}")
            else:
                new_chunks[i] = replacement
                fixed_parts += 1

        if fixed_parts:
            md_file.write_text("".join(new_chunks), encoding="utf-8")
        report["fixed"] = fixed_parts > 0
        report["fixed_parts"] = fixed_parts
        if rejected:
            report["rejected_rewrites"] = rejected

    return {
        "unit": str(unit_dir.relative_to(WORKSPACE_ROOT)),
        "reports": unit_reports,
        "has_issues": has_issues,
        "review_failed": review_failed,
    }
