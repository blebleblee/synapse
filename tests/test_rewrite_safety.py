"""
Regression tests for safe LLM rewriting of lessons.

Before the fix:
- reviewer auto-fix sent only the first 6,000 chars and overwrote the whole file;
- the generator's refine step sent only the first 7,000 chars of each draft and
  published the reply as the full chapter;
- an unparseable reviewer reply was reported as VERIFIED (score 85).
"""
import json
import re
from pathlib import Path

import pytest

import learning_engine.security as sec
import learning_engine.reviewer as reviewer
import learning_engine.generator as generator
from learning_engine.models import LLMProvider
from learning_engine.rewrite_safety import (
    split_markdown_chunks,
    check_rewrite,
    clean_model_markdown,
    parse_json_object,
    extract_headings,
    count_fences,
)


def make_long_lesson(sections: int = 12, para_repeat: int = 50) -> str:
    """~35-40k char lesson with headings, code blocks (incl. '#' comments) and lists."""
    out = ["# Masterclass: Storage Engines\n\nIntro paragraph about lorem storage.\n\n"]
    for i in range(1, sections + 1):
        out.append(f"## Section {i}: Topic {i}\n\n")
        out.append(("Section %d body lorem ipsum explains invariants in depth. " % i) * para_repeat + "\n\n")
        out.append("```bash\n# not a heading inside a fence\nls -la /var/lib\n\n# still code\n```\n\n")
        out.append(f"- point A{i}\n- point B{i}\n\n")
    return "".join(out)


# --- splitting ---------------------------------------------------------------

def test_split_roundtrips_exactly_and_respects_size():
    text = make_long_lesson()
    assert len(text) > 30_000
    chunks = split_markdown_chunks(text, 6_000)
    assert "".join(chunks) == text
    assert len(chunks) > 1
    assert all(len(c) <= 6_000 for c in chunks)


def test_split_never_cuts_inside_code_fence():
    text = make_long_lesson()
    for c in split_markdown_chunks(text, 3_000):
        assert count_fences(c) % 2 == 0, "chunk boundary fell inside a code fence"


def test_split_keeps_oversized_block_whole():
    code = "```python\n" + "x = 1\n" * 5_000 + "```\n"
    text = "## Big\n\n" + code + "## After\n\ntext\n"
    chunks = split_markdown_chunks(text, 2_000)
    assert "".join(chunks) == text
    assert any(code in c for c in chunks)


def test_headings_inside_fences_are_ignored():
    assert extract_headings("## Real\n```\n# comment\n```\n### **Also** real\n") == ["2:real", "3:also real"]


# --- rewrite acceptance --------------------------------------------------------

def test_check_rewrite_rejects_truncation():
    chunk = split_markdown_chunks(make_long_lesson(), 6_000)[1]
    ok, reason = check_rewrite(chunk, chunk[: len(chunk) // 3])
    assert not ok


def test_check_rewrite_rejects_dropped_heading_and_open_fence():
    orig = "## A\n\n" + "text " * 100 + "\n\n## B\n\n" + "more " * 100
    ok, reason = check_rewrite(orig, "## A\n\n" + "text " * 220)
    assert not ok and "heading" in reason
    ok, reason = check_rewrite(orig, orig + "\n```bash\nunclosed")
    assert not ok and "fence" in reason


def test_check_rewrite_accepts_expanded_rewrite():
    orig = "## A\n\nshort text here.\n\n## B\n\nmore text.\n"
    new = "## A\n\nA much longer and better explanation.\n\n## B\n\nMore text, expanded with detail.\n"
    assert check_rewrite(orig, new) == (True, "ok")


def test_clean_model_markdown_keeps_trailing_code_block():
    body = "## A\n\ntext\n\n```bash\nls\n```"
    assert clean_model_markdown(body) == body
    assert clean_model_markdown("```markdown\n" + body + "\n```") == body
    assert clean_model_markdown("<think>plan</think>\n" + body) == body


@pytest.mark.parametrize("raw", [
    '{"verdict": "VERIFIED", "score": 90}',
    '<think>let me {think}</think>```json\n{"verdict": "VERIFIED", "score": 90}\n```',
    'Here is my audit:\n{"verdict": "VERIFIED", "score": 90}\nThanks.',
])
def test_parse_json_object_variants(raw):
    assert parse_json_object(raw)["verdict"] == "VERIFIED"


def test_parse_json_object_garbage():
    assert parse_json_object("The document looks fine overall.") is None


# --- reviewer ------------------------------------------------------------------

class ScriptedReviewer(LLMProvider):
    """Audits: part containing a marker NEEDS_REVISION, others VERIFIED. Fixes: per `fix_mode`."""

    def __init__(self, revise_marker=None, fix_mode="good", audit_garbage=False):
        self.model = "fake-reviewer"
        self.revise_marker = revise_marker
        self.fix_mode = fix_mode
        self.audit_garbage = audit_garbage
        self.audit_calls = 0
        self.fix_calls = 0

    @staticmethod
    def _quoted(prompt):
        return prompt.split('"""', 2)[1].strip("\n")

    def generate(self, prompt, system_instruction="", **kwargs):
        if "Output valid JSON only" in prompt:
            self.audit_calls += 1
            if self.audit_garbage:
                return "<think>hmm</think> The text seems broadly fine to me."
            part = self._quoted(prompt)
            bad = self.revise_marker and self.revise_marker in part
            return json.dumps({
                "verdict": "NEEDS_REVISION" if bad else "VERIFIED",
                "score": 55 if bad else 92,
                "hallucinations": ["fake flag"] if bad else [],
                "factual_errors": [],
                "critique": "needs work" if bad else "fine",
            })
        self.fix_calls += 1
        part = self._quoted(prompt)
        if self.fix_mode == "truncate":
            return part[: len(part) // 4]
        return part.replace("lorem", "CORRECTED")


def _unit_with_lesson(text: str) -> Path:
    unit = Path(sec.TOPICS_DIR) / "computing" / "rw_cat" / "rw_topic"
    unit.mkdir(parents=True, exist_ok=True)
    (unit / "lesson_01.md").write_text(text, encoding="utf-8")
    return unit


def test_unparseable_review_is_not_verified_and_never_rewrites(monkeypatch):
    text = make_long_lesson()
    unit = _unit_with_lesson(text)
    fake = ScriptedReviewer(audit_garbage=True)
    monkeypatch.setattr(reviewer, "get_provider", lambda **kw: fake)

    res = reviewer.review_and_fix_unit(unit, auto_fix=True)
    report = res["reports"][0]
    assert report["verdict"] == reviewer.REVIEW_FAILED
    assert report["score"] is None
    assert res["review_failed"] is True
    assert res["has_issues"] is False
    assert fake.fix_calls == 0
    assert (unit / "lesson_01.md").read_text(encoding="utf-8") == text


def test_audit_covers_whole_document(monkeypatch):
    text = make_long_lesson()
    unit = _unit_with_lesson(text)
    # Problem planted only at the end, far past the old 7,000-char audit window.
    fake = ScriptedReviewer(revise_marker="Section 12 body")
    monkeypatch.setattr(reviewer, "get_provider", lambda **kw: fake)

    report = reviewer.audit_content(unit / "lesson_01.md")
    assert fake.audit_calls > 1
    assert report["verdict"] == "NEEDS_REVISION"
    assert report["score"] == 55
    assert "".join(report["chunks"]) == text


def test_auto_fix_rewrites_only_flagged_part_and_keeps_rest(monkeypatch):
    text = make_long_lesson()
    unit = _unit_with_lesson(text)
    fake = ScriptedReviewer(revise_marker="Section 12 body", fix_mode="good")
    monkeypatch.setattr(reviewer, "get_provider", lambda **kw: fake)

    res = reviewer.review_and_fix_unit(unit, auto_fix=True)
    new = (unit / "lesson_01.md").read_text(encoding="utf-8")
    report = res["reports"][0]
    assert report["fixed"] is True and report["fixed_parts"] == 1
    assert extract_headings(new) == extract_headings(text)
    assert "Section 12 body CORRECTED" in new
    assert "Section 1 body lorem" in new  # untouched parts keep original text
    assert abs(len(new) - len(text)) < 0.1 * len(text)


def test_auto_fix_rejects_truncated_rewrite(monkeypatch):
    text = make_long_lesson()
    unit = _unit_with_lesson(text)
    fake = ScriptedReviewer(revise_marker="Section 12 body", fix_mode="truncate")
    monkeypatch.setattr(reviewer, "get_provider", lambda **kw: fake)

    res = reviewer.review_and_fix_unit(unit, auto_fix=True)
    report = res["reports"][0]
    assert report["fixed"] is False
    assert report["rejected_rewrites"]
    assert (unit / "lesson_01.md").read_text(encoding="utf-8") == text


# --- generator refine step -----------------------------------------------------

class ClusterNode(LLMProvider):
    """Drafts return a long lesson; refines either improve or truncate a part."""

    def __init__(self, draft: str, truncate_marker: str):
        self.model = "fake-32b"
        self.draft = draft
        self.truncate_marker = truncate_marker
        self.refine_prompts = []

    def generate(self, prompt, system_instruction="", **kwargs):
        if "DRAFT TO AUDIT & REFINE" not in prompt:
            return self.draft
        self.refine_prompts.append(prompt)
        part = prompt.split("DRAFT TO AUDIT & REFINE:\n", 1)[1].split('"""', 2)[1].strip("\n")
        if self.truncate_marker in part:
            return part[: len(part) // 5]
        return part.replace("lorem", "REFINED")


def test_refine_step_processes_full_draft_and_keeps_rejected_parts(monkeypatch):
    draft = make_long_lesson()
    node = ClusterNode(draft, truncate_marker="Section 6 body")
    workers = [("http://node-a:11434", "fake-32b", node), ("http://node-b:11434", "fake-32b", node)]

    monkeypatch.setattr(generator, "scope_topic_curriculum",
                        lambda *a, **kw: [{"filename": "lesson_01.md", "title": "Storage", "prompt": "write"}])
    monkeypatch.setattr(generator, "validate_lesson_completeness", lambda c: c)

    unit = Path(sec.TOPICS_DIR) / "computing" / "gen_cat" / "gen_topic"
    unit.mkdir(parents=True, exist_ok=True)
    results = generator.generate_topic_parallel("computing", "gen_cat", "gen_topic", unit, force=True, workers=workers)
    assert results.get("lesson_01.md") is True

    out = (unit / "lesson_01.md").read_text(encoding="utf-8")
    assert len(node.refine_prompts) > 1, "long drafts must be refined in parts"
    assert extract_headings(out) == extract_headings(draft)
    for i in range(1, 13):
        assert f"Section {i}" in out
    assert "Section 12 body REFINED" in out          # content past 7,000 chars was refined
    assert "Section 6 body lorem" in out             # truncated refinement rejected, draft kept
    assert len(out) > 0.9 * len(draft)
    assert count_fences(out) % 2 == 0


@pytest.mark.parametrize("raw", [
    "Here is the fully corrected, publication-grade, raw Markdown:\n\n# Lesson 1: X\n\n## A\n\ntext",
    "Sure! Here's the lesson:\n# Lesson 1: X\n\n## A\n\ntext",
    "Here is the fully corrected, publication-grade, raw Markdown:\n\n```markdown\n# Lesson 1: X\n\n## A\n\ntext\n```",
    "``markdown\n# Lesson 1: X\n\n## A\n\ntext",
])
def test_clean_model_markdown_drops_chat_preambles_and_broken_openers(raw):
    """Three public lessons began with "Here is the fully corrected, publication-grade,
    raw Markdown:" and one with a stray "``markdown" line, because the cleaner only
    removed a fence that wrapped the whole reply."""
    assert clean_model_markdown(raw) == "# Lesson 1: X\n\n## A\n\ntext"


def test_clean_model_markdown_keeps_real_opening_prose():
    body = "Here is a question every painter faces: where does the light come from?\n\n## A\n\ntext"
    assert clean_model_markdown(body) == body
