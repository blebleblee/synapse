"""
Safe LLM rewriting of curriculum documents.

Lessons average ~35k characters, far more than a local model's default context
window or a single response can reliably carry. Sending a truncated prefix and
writing the reply over the whole file silently destroys content. This module
provides the pieces that make rewrites safe:

- split_markdown_chunks: split a document at heading boundaries (never inside
  a code fence) into chunks small enough for any model; "".join(chunks) == text.
- check_rewrite: accept a rewritten chunk only if it is plausibly complete
  (keeps every heading in order, balanced code fences, no large length loss).
- clean_model_markdown: strip reasoning tags and a wrapping ``` fence without
  dropping legitimate content.
- parse_json_object: extract a JSON object from a model reply that may contain
  reasoning tags, code fences or prose.
"""

import json
import re
from typing import List, Optional, Tuple

DEFAULT_CHUNK_CHARS = 12_000
MIN_REWRITE_RATIO = 0.7

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _iter_lines_with_fence_state(text: str):
    """Yields (line_with_newline, inside_fence_before_line)."""
    in_fence = False
    for line in text.splitlines(keepends=True):
        yield line, in_fence
        if _FENCE_RE.match(line):
            in_fence = not in_fence


def extract_headings(text: str) -> List[str]:
    """Markdown headings outside code fences, normalized for comparison."""
    headings = []
    for line, in_fence in _iter_lines_with_fence_state(text):
        if in_fence or _FENCE_RE.match(line):
            continue
        m = _HEADING_RE.match(line.rstrip("\n"))
        if m:
            title = re.sub(r"[*_`]", "", m.group(2)).strip().lower()
            headings.append(f"{len(m.group(1))}:{title}")
    return headings


def count_fences(text: str) -> int:
    return sum(1 for line in text.splitlines() if _FENCE_RE.match(line))


def _split_at(text: str, is_boundary) -> List[str]:
    """Splits text before lines where is_boundary(line) holds (outside fences)."""
    parts: List[str] = []
    current: List[str] = []
    for line, in_fence in _iter_lines_with_fence_state(text):
        if not in_fence and current and is_boundary(line):
            parts.append("".join(current))
            current = []
        current.append(line)
    if current:
        parts.append("".join(current))
    return parts


def split_markdown_chunks(text: str, max_chars: int = DEFAULT_CHUNK_CHARS) -> List[str]:
    """
    Splits markdown into chunks of at most ~max_chars, cutting only before
    headings (or, for an oversized section, before blank lines) and never inside
    a fenced code block. A single block larger than max_chars stays whole.
    Invariant: "".join(result) == text.
    """
    if len(text) <= max_chars:
        return [text] if text else []

    sections = _split_at(text, lambda l: bool(_HEADING_RE.match(l.rstrip("\n"))))

    pieces: List[str] = []
    for sec in sections:
        if len(sec) <= max_chars:
            pieces.append(sec)
        else:
            pieces.extend(_split_at(sec, lambda l: l.strip() == ""))

    chunks: List[str] = []
    current = ""
    for piece in pieces:
        if current and len(current) + len(piece) > max_chars:
            chunks.append(current)
            current = ""
        current += piece
    if current:
        chunks.append(current)
    return chunks


def clean_model_markdown(raw: str) -> str:
    """Strips reasoning tags and a single wrapping code fence from a model reply."""
    text = (raw or "").strip()
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    m = re.match(r"^```(?:markdown|md)?[ \t]*\n(.*)\n```\s*$", text, re.DOTALL)
    if m and count_fences(m.group(1)) % 2 == 0:
        text = m.group(1).strip()
    return text


def check_rewrite(original: str, rewritten: str, min_ratio: float = MIN_REWRITE_RATIO) -> Tuple[bool, str]:
    """
    Decides whether a rewrite may replace the original. Rejects rewrites that
    are empty, much shorter, drop or reorder headings, or leave a code fence open.
    """
    orig = original.strip()
    new = (rewritten or "").strip()
    if not new:
        return False, "empty rewrite"
    if orig and len(new) < min_ratio * len(orig):
        return False, f"rewrite is {len(new)} chars vs {len(orig)} original (< {int(min_ratio * 100)}%)"
    if count_fences(new) % 2 != 0:
        return False, "rewrite leaves a code fence unclosed"
    orig_headings = extract_headings(orig)
    new_headings = extract_headings(new)
    it = iter(new_headings)
    if not all(h in it for h in orig_headings):
        missing = [h.split(":", 1)[1] for h in orig_headings if h not in new_headings]
        detail = f"missing {missing[:3]}" if missing else "headings reordered"
        return False, f"rewrite does not preserve section headings ({detail})"
    return True, "ok"


def parse_json_object(raw: str) -> Optional[dict]:
    """Returns the first JSON object found in a model reply, or None."""
    text = (raw or "").strip()
    if "</think>" in text:
        text = text.split("</think>")[-1]
    decoder = json.JSONDecoder()
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text, m.start())
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return None
