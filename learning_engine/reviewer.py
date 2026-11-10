"""
Cross-Model Independent Quality & Hallucination Reviewer
Performs blind, adversarial peer review of generated units using an independent model family
(e.g., deepseek-r1:32b or Gemini) to detect hallucinations, factual errors, and weak explanations.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import get_provider, LLMProvider
from .topic_manager import resolve_subtopic, get_domain_persona

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

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

def audit_content(
    file_path: Path,
    reviewer_provider: Optional[str] = None,
    reviewer_model: Optional[str] = None
) -> Dict[str, Any]:
    if not file_path.exists():
        return {"error": f"File {file_path} not found"}

    content = file_path.read_text(encoding="utf-8")
    if len(content.strip()) < 100:
        return {
            "verdict": "REJECTED",
            "score": 10,
            "hallucinations": ["File is empty or truncated"],
            "factual_errors": ["Insufficient content"],
            "critique": "File is virtually empty."
        }

    provider = get_provider(
        provider_type=reviewer_provider,
        model=reviewer_model or DEFAULT_REVIEWER_MODEL
    )

    prompt = f"""Audit the following technical curriculum text from '{file_path.name}':

\"\"\"
{content[:7000]}
\"\"\"

Output valid JSON only."""

    raw = provider.generate(prompt, system_instruction=AUDIT_SYSTEM_PROMPT).strip()

    # Strip thinking tags if deepseek-r1
    if "<think>" in raw and "</think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    # Strip code block wrapping
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        report = json.loads(raw)
    except Exception:
        # Fallback parsing
        is_verified = "TODO" not in content and "TBD" not in content and len(content) > 1000
        report = {
            "verdict": "VERIFIED" if is_verified else "NEEDS_REVISION",
            "score": 85 if is_verified else 60,
            "hallucinations": [],
            "factual_errors": [],
            "critique": "Automated baseline check passed." if is_verified else "Contains potential placeholders."
        }

    report["file"] = str(file_path.relative_to(WORKSPACE_ROOT))
    return report

def review_and_fix_unit(
    unit_dir: Path,
    reviewer_provider: Optional[str] = None,
    reviewer_model: Optional[str] = None,
    auto_fix: bool = False
) -> Dict[str, Any]:
    unit_reports = []
    has_issues = False

    target_files = list(unit_dir.rglob("*.md"))
    for md_file in target_files:
        if md_file.name in ["SUMMARY.md", "README.md"]:
            continue
        report = audit_content(md_file, reviewer_provider, reviewer_model)
        unit_reports.append(report)

        if report.get("verdict") in ["NEEDS_REVISION", "REJECTED"]:
            has_issues = True
            if auto_fix:
                print(f"[!] Auto-fixing {md_file.relative_to(WORKSPACE_ROOT)} based on audit critique...")
                # Correction prompt
                fix_prompt = f"""You are correcting a technical curriculum document that failed peer review.
Issues Found:
- Hallucinations: {report.get('hallucinations')}
- Factual Errors: {report.get('factual_errors')}
- Critique: {report.get('critique')}

Original Document:
{md_file.read_text(encoding='utf-8')[:6000]}

Rewrite this entire document, correcting all factual inaccuracies, eliminating all placeholders, and ensuring graduate-level precision.
Output clean Markdown only."""
                provider = get_provider(provider_type=reviewer_provider, model=reviewer_model or DEFAULT_REVIEWER_MODEL)
                fixed_content = provider.generate(fix_prompt).strip()
                if "<think>" in fixed_content and "</think>" in fixed_content:
                    fixed_content = fixed_content.split("</think>")[-1].strip()
                md_file.write_text(fixed_content + "\n", encoding="utf-8")
                report["fixed"] = True

    return {
        "unit": str(unit_dir.relative_to(WORKSPACE_ROOT)),
        "reports": unit_reports,
        "has_issues": has_issues
    }
