"""Shipped flashcard decks (scripts/generate_flashcard_decks.py). Fake provider only."""
import csv
import importlib.util
import json
from pathlib import Path

import pytest

import learning_engine.security as sec
from learning_engine.flashcards import generate_flashcards

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("decks", ROOT / "scripts" / "generate_flashcard_decks.py")
decks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decks)


class FakeProvider:
    def __init__(self, n=12, fail=False):
        self.n, self.fail, self.prompts = n, fail, []

    def generate(self, prompt, system_instruction="", **kw):
        self.prompts.append(prompt)
        if self.fail:
            raise RuntimeError("quota")
        return json.dumps([{"front": f"Q{i}?", "back": f"A{i}"} for i in range(self.n)])


@pytest.fixture
def course():
    u = Path(sec.TOPICS_DIR) / "computing" / "deck_cat" / "deck_topic"
    u.mkdir(parents=True, exist_ok=True)
    for i in range(1, 7):
        (u / f"lesson_{i:02d}_part.md").write_text(f"# Lesson {i}: Part\n\nMARKER{i} " + "x " * 300, encoding="utf-8")
    (u / "labs.md").write_text("# Labs\n\nLABMARKER\n", encoding="utf-8")
    return u


def test_deck_budget_covers_every_lesson_and_asks_for_more_cards(course):
    p = FakeProvider()
    out = generate_flashcards("computing/deck_cat/deck_topic", provider=p, **decks.DECK_BUDGET)
    prompt = p.prompts[0]
    assert "generate 12 high-impact" in prompt
    assert all(f"MARKER{i}" in prompt for i in range(1, 7)) and "LABMARKER" in prompt
    rows = [r for r in csv.reader(out.read_text(encoding="utf-8").splitlines()) if r and not r[0].startswith("#")]
    assert len(rows) == 12


def test_app_default_budget_is_unchanged(course):
    p = FakeProvider(n=8)
    generate_flashcards("computing/deck_cat/deck_topic", provider=p)
    prompt = p.prompts[0]
    assert "generate 8 high-impact" in prompt
    assert "MARKER4" in prompt and "MARKER5" not in prompt


FILES = [
    "topics/arts/visual_arts/drawing/lesson_01_line.md",
    "topics/arts/visual_arts/drawing/labs.md",
    "topics/computing/systems/bash/lesson_01_shell.md",
    "topics/otherdomain/cat/course/lesson_01_x.md",   # not a public domain
    "topics/computing/systems/README.md",
    "topics/computing/systems/bash/sessions/lesson_01_x.md",
]


def test_public_courses_lists_only_public_courses_with_lessons():
    assert decks.public_courses(files=FILES) == ["arts/visual_arts/drawing", "computing/systems/bash"]
    assert decks.public_courses("arts", files=FILES) == ["arts/visual_arts/drawing"]


def test_existing_decks_are_skipped(course):
    rel = "computing/deck_cat/deck_topic"
    assert decks.missing_decks([rel], Path(sec.TOPICS_DIR)) == [rel]
    (course / "flashcards.csv").write_text("#separator:Comma\nq,a\n", encoding="utf-8")
    assert decks.missing_decks([rel], Path(sec.TOPICS_DIR)) == []


def test_failures_are_reported_and_write_no_deck(course):
    done, failed = decks.run(["computing/deck_cat/deck_topic"], FakeProvider(fail=True), generate_flashcards)
    assert done == [] and failed[0][0] == "computing/deck_cat/deck_topic"
    assert not (course / "flashcards.csv").exists()


def test_dry_run_calls_no_model(capsys, monkeypatch):
    monkeypatch.setattr("learning_engine.models.get_provider", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no model")))
    assert decks.main(["--dry-run"], files=FILES) == 0
    assert "without a deck" in capsys.readouterr().out
