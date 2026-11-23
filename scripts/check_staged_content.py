#!/usr/bin/env python3
"""
Pre-commit and CI Security Guard.
Scans staged or tracked files to prevent committing:
1. Private curriculum domains and sideloaded files (per AGENTS.md § 2).
2. Secret API keys and credentials (Anthropic, Gemini, OpenAI, Gitea tokens).

Usage:
    python3 scripts/check_staged_content.py [--staged] [--audit-tracked] [file1 file2 ...]
"""

import sys
import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

CORE_DOMAINS = {
    "arts", "business", "computing", "crafts", "economics", "engineering",
    "formal_sciences", "health_sciences", "humanities", "languages",
    "motorsports", "natural_sciences",
}

PRIVATE_FILE_PATTERNS = [
    re.compile(r"^topics/languages/(?:czech|english|german)/", re.IGNORECASE),
    re.compile(r"(?:^|/)sessions/", re.IGNORECASE),
    re.compile(r"(?:^|/)active_session\.md$", re.IGNORECASE),
    re.compile(r"(?:^|/)chat_history\.json$", re.IGNORECASE),
    re.compile(r"(?:^|/)CURRICULUM_BLUEPRINT\.md$", re.IGNORECASE),
    # Written by the app from the learner's chat sessions.
    re.compile(r"(?:^|/)MASTERED_GUIDE\.md$", re.IGNORECASE),
    re.compile(r"^topics/.*/SUMMARY\.md$", re.IGNORECASE),
]

SECRET_PATTERNS = [
    (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}"), "Anthropic API Key"),
    (re.compile(r"AIzaSy[a-zA-Z0-9_\-]{33}"), "Google/Gemini API Key"),
    (re.compile(r"sk-(?!ant-)(?:proj-)?[a-zA-Z0-9_\-]{20,}"), "OpenAI API Key"),
    (re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}"), "GitHub Token"),
]

# Patterns that indicate safe placeholder values in tests or examples
SAFE_PLACEHOLDER_REGEX = re.compile(
    r"(?:dummy|test|fake|mock|example|placeholder|your[-_]api[-_]key|<[^>]+>)",
    re.IGNORECASE
)


def is_private_path(rel_path: str) -> Tuple[bool, str]:
    norm = rel_path.replace("\\", "/").strip().lstrip("/")
    
    # 1. Check topics/ domain whitelist
    if norm.startswith("topics/"):
        parts = norm.split("/")
        if len(parts) >= 2:
            domain = parts[1]
            if domain not in CORE_DOMAINS:
                return True, f"Non-core private domain '{domain}'"

    # 2. Check forbidden file and folder patterns
    for pat in PRIVATE_FILE_PATTERNS:
        if pat.search(norm):
            return True, f"Matches private pattern '{pat.pattern}'"

    return False, ""


def find_secrets_in_text(text: str, filename: str) -> List[Tuple[int, str, str]]:
    issues = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, 1):
        # Skip commented test explanations or documentation of key patterns
        if "re.compile(" in line or "SECRET_PATTERNS" in line:
            continue
        for pat, desc in SECRET_PATTERNS:
            match = pat.search(line)
            if match:
                token = match.group(0)
                if not SAFE_PLACEHOLDER_REGEX.search(token):
                    issues.append((idx, desc, token[:6] + "..." + token[-4:]))
    return issues


def local_private_domains(topics_dir: Path = REPO_ROOT / "topics") -> List[str]:
    """Private domain folders present on this machine: the synced copies here,
    plus the private repository itself when SYNAPSE_ADDONS_DIR points to it
    (some private domains are never synced). Their names are never stored in
    this repository; CI has none, so there the check finds nothing to compare."""
    import os
    dirs = [topics_dir]
    if os.environ.get("SYNAPSE_ADDONS_DIR"):
        dirs.append(Path(os.environ["SYNAPSE_ADDONS_DIR"]) / "topics")
    names = set()
    for base in dirs:
        try:
            names.update(d.name for d in base.iterdir()
                         if d.is_dir() and not d.name.startswith((".", "_")) and d.name not in CORE_DOMAINS)
        except OSError:
            pass
    return sorted(names)


def public_slugs(tracked: List[str]) -> set:
    """Category and course folder names of the public domains."""
    out = set()
    for f in tracked:
        parts = f.split("/")
        if len(parts) >= 4 and parts[0] == "topics" and parts[1] in CORE_DOMAINS:
            out.update(parts[2:4])
    return out


def find_private_domain_names(text: str, names: List[str], ambiguous: set) -> List[int]:
    """Line numbers where code names a private domain: as a quoted string
    ("name") or a topics path (topics/name/). Names that are also public
    category or course names (physics) are checked as paths only; lines
    marked "not-a-domain" are skipped."""
    pats = []
    for n in names:
        e = re.escape(n)
        pats.append(rf"topics/{e}/")
        if n not in ambiguous:
            pats.append(rf"[\"']{e}[\"']")
    if not pats:
        return []
    rx = re.compile("|".join(pats), re.IGNORECASE)
    # A line marked "not-a-domain" uses the word itself (e.g. "daw" as a term).
    return [i for i, line in enumerate(text.splitlines(), 1) if rx.search(line) and "not-a-domain" not in line]


def scan_file(path: Path, rel_str: str, private_names=None, ambiguous=frozenset()) -> List[str]:
    errors = []

    # 1. Path privacy check
    private, reason = is_private_path(rel_str)
    if private:
        errors.append(f"[✘] Private Content Violation: '{rel_str}' ({reason})")

    # 2. Content secret check (skip binary or non-text files)
    if not path.is_file() or path.stat().st_size > 2_000_000:
        return errors

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return errors

    secret_hits = find_secrets_in_text(content, rel_str)
    for line_num, secret_type, redacted in secret_hits:
        errors.append(f"[✘] Secret Leak Warning: '{rel_str}:{line_num}' contains {secret_type} ({redacted})")

    # 3. Public files must not name private domains (AGENTS.md section 2).
    if private_names and not rel_str.startswith("topics/"):
        for line_num in find_private_domain_names(content, private_names, ambiguous):
            errors.append(f"[✘] Private Domain Name: '{rel_str}:{line_num}' names a private domain "
                          "(move it to that domain's DOMAIN_PROFILE.json or use a made-up name in tests)")

    return errors


def get_staged_files() -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=str(REPO_ROOT),
            text=True
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def get_tracked_files() -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            text=True
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Scan staged or tracked files for private content or secrets.")
    parser.add_argument("--staged", action="store_true", help="Scan git staged files (default for pre-commit)")
    parser.add_argument("--audit-tracked", action="store_true", help="Scan all git tracked files in repository")
    parser.add_argument("files", nargs="*", help="Specific files to scan")
    args = parser.parse_args()

    files_to_scan = []
    if args.files:
        files_to_scan = args.files
    elif args.audit_tracked:
        files_to_scan = get_tracked_files()
    else:
        files_to_scan = get_staged_files()

    if not files_to_scan:
        print("[✔] No files to scan.")
        sys.exit(0)

    private_names = local_private_domains()
    ambiguous = public_slugs(get_tracked_files()) if private_names else set()
    all_errors = []
    for f in files_to_scan:
        full_path = REPO_ROOT / f
        errors = scan_file(full_path, f, private_names, ambiguous)
        all_errors.extend(errors)

    if all_errors:
        print("==================================================")
        print(" 🚨 PRE-COMMIT SECURITY SCAN FAILED               ")
        print("==================================================")
        for err in all_errors:
            print(f" {err}")
        print("==================================================")
        print(" Commit blocked to protect private data & secrets.")
        sys.exit(1)

    print(f"[✔] Security scan clean ({len(files_to_scan)} files inspected; 0 private paths, 0 secrets).")
    sys.exit(0)


if __name__ == "__main__":
    main()
