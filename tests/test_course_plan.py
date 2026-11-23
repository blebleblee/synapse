"""Filling in missing files reuses the course's plan.

Before: a run without --force asked the AI for a new plan, whose file names
differed from the existing lessons, so "Generate missing files" (and the UI's
"Run it again to generate the missing files") added duplicate lessons.
"""
import json
import tarfile
from pathlib import Path

import pytest

import learning_engine.generator as generator
import learning_engine.packages as packages
import learning_engine.security as sec
from learning_engine.models import LLMProvider

LESSON = "# Lesson\n\n" + ("Body text with enough words to pass. " * 60) + "\n"


class Node(LLMProvider):
    def __init__(self, fail_on=None):
        self.model = "fake-7b"
        self.fail_on = fail_on
        self.prompts = []

    def generate(self, prompt, system_instruction="", **kwargs):
        self.prompts.append(prompt)
        if self.fail_on and self.fail_on in prompt:
            raise RuntimeError("model unreachable")
        if "DRAFT TO AUDIT & REFINE" in prompt:
            return prompt.split("DRAFT TO AUDIT & REFINE:\n", 1)[1].split('"""', 2)[1]
        return LESSON


def _workers(node):
    return [("http://node-a:11434", "fake-7b", node)]


@pytest.fixture
def unit(monkeypatch):
    u = Path(sec.TOPICS_DIR) / "computing" / "plan_cat" / "plan_topic"
    u.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(generator, "validate_lesson_completeness", lambda c: c)
    monkeypatch.setattr(generator.time, "sleep", lambda s: None)
    return u


def _scoping_returns(monkeypatch, names):
    calls = []

    def scope(*a, **kw):
        calls.append(1)
        return [{"filename": n, "title": n, "prompt": f"write {n}"} for n in names]
    monkeypatch.setattr(generator, "scope_topic_curriculum", scope)
    return calls


def _gen(unit, node, force=False):
    return generator.generate_topic_parallel("computing", "plan_cat", "plan_topic", unit,
                                             force=force, workers=_workers(node))


def lessons(unit):
    return sorted(p.name for p in unit.glob("lesson_*.md"))


def test_rerun_fills_in_the_failed_lesson_under_its_planned_name(unit, monkeypatch):
    _scoping_returns(monkeypatch, ["lesson_01_alpha.md", "lesson_02_beta.md", "labs.md"])
    first = _gen(unit, Node(fail_on="write lesson_02_beta.md"))
    assert first["lesson_02_beta.md"] is False
    assert lessons(unit) == ["lesson_01_alpha.md"]

    # A second scoping call would name the lessons differently.
    calls = _scoping_returns(monkeypatch, ["lesson_01_other.md", "lesson_02_names.md", "labs.md"])
    node = Node()
    second = _gen(unit, node)
    assert calls == [], "the saved plan is reused; no new scoping"
    assert second["lesson_02_beta.md"] is True
    assert lessons(unit) == ["lesson_01_alpha.md", "lesson_02_beta.md"]
    drafts = [p for p in node.prompts if "DRAFT TO AUDIT & REFINE" not in p]
    assert drafts == ["write lesson_02_beta.md"]


def test_lessons_without_a_saved_plan_get_only_fixed_files(unit, monkeypatch):
    (unit / "lesson_01_existing.md").write_text(LESSON, encoding="utf-8")
    calls = _scoping_returns(monkeypatch, ["lesson_01_fresh.md", "labs.md"])
    results = _gen(unit, Node())
    assert calls == []
    assert results == {"labs.md": True}
    assert lessons(unit) == ["lesson_01_existing.md"]
    assert (unit / "labs.md").exists()


def test_nothing_missing_generates_nothing(unit, monkeypatch):
    _scoping_returns(monkeypatch, ["lesson_01_alpha.md", "labs.md"])
    _gen(unit, Node())
    node = Node()
    results = _gen(unit, node)
    assert node.prompts == [] and not any(results.values())
    assert results.skipped == {"lesson_01_alpha.md", "labs.md"}


@pytest.mark.parametrize("bad", [
    "not json",
    json.dumps({"modules": [{"filename": "../../escape.md", "prompt": "x"}]}),
    json.dumps({"modules": [{"filename": "lesson_01_a.md"}]}),
    json.dumps({"modules": []}),
])
def test_unusable_plan_is_ignored(unit, monkeypatch, bad):
    (unit / generator.PLAN_FILENAME).write_text(bad, encoding="utf-8")
    calls = _scoping_returns(monkeypatch, ["lesson_01_alpha.md", "labs.md"])
    _gen(unit, Node())
    assert calls == [1]
    assert lessons(unit) == ["lesson_01_alpha.md"]
    assert not (unit.parent.parent / "escape.md").exists()


def test_regeneration_saves_its_plan_only_when_it_replaces_the_course(unit, monkeypatch):
    (unit / "lesson_01_old.md").write_text(LESSON, encoding="utf-8")
    _scoping_returns(monkeypatch, ["lesson_01_new.md", "labs.md"])
    _gen(unit, Node(fail_on="write labs.md"), force=True)
    assert not (unit / generator.PLAN_FILENAME).exists()
    _gen(unit, Node(), force=True)
    saved = json.loads((unit / generator.PLAN_FILENAME).read_text())
    assert [m["filename"] for m in saved["modules"]] == ["lesson_01_new.md", "labs.md"]


def test_outline_courses_do_not_save_a_plan(unit, monkeypatch):
    (unit / "TOPIC_OUTLINE.md").write_text("# Outline\n", encoding="utf-8")
    calls = _scoping_returns(monkeypatch, ["lesson_01_alpha.md", "labs.md"])
    _gen(unit, Node())
    assert calls == [1]
    assert not (unit / generator.PLAN_FILENAME).exists()


def test_plan_file_is_not_packed(unit, monkeypatch):
    _scoping_returns(monkeypatch, ["lesson_01_alpha.md", "labs.md"])
    _gen(unit, Node())
    assert (unit / generator.PLAN_FILENAME).exists()
    assert not any(f.name == generator.PLAN_FILENAME for f in packages.iter_pack_files("computing"))
