"""
"Regenerate with AI" (force) used to delete the course's lesson files and
every subfolder, including the learner's chat sessions, before drafting.
A failed model call, an unreachable model or pressing Stop left the course
empty. Now new files are staged and replace the old ones only when every
file succeeded; subfolders are never touched; Stop publishes nothing.
"""
from pathlib import Path

import pytest

import learning_engine.generator as generator
import learning_engine.security as sec
from learning_engine.models import GenerationStopped, LLMProvider

LESSON = "# Lesson\n\n" + ("Body text with enough words to pass. " * 60) + "\n"


class Node(LLMProvider):
    def __init__(self, fail_on=None):
        self.model = "fake-7b"
        self.fail_on = fail_on

    def generate(self, prompt, system_instruction="", **kwargs):
        if self.fail_on and self.fail_on in prompt:
            raise RuntimeError("model unreachable")
        if "DRAFT TO AUDIT & REFINE" in prompt:
            return prompt.split("DRAFT TO AUDIT & REFINE:\n", 1)[1].split('"""', 2)[1]
        return LESSON


@pytest.fixture
def course(monkeypatch):
    unit = Path(sec.TOPICS_DIR) / "computing" / "regen_cat" / "regen_topic"
    unit.mkdir(parents=True, exist_ok=True)
    (unit / "lesson_01_old.md").write_text("# Old lesson\n", encoding="utf-8")
    (unit / "labs.md").write_text("# Old labs\n", encoding="utf-8")
    (unit / "sessions").mkdir()
    (unit / "sessions" / "active_session.md").write_text("my chat\n", encoding="utf-8")
    monkeypatch.setattr(generator, "scope_topic_curriculum", lambda *a, **kw: [
        {"filename": "lesson_01_new.md", "title": "New", "prompt": "write lesson one"},
        {"filename": "labs.md", "title": "Labs", "prompt": "write labs"},
    ])
    monkeypatch.setattr(generator, "validate_lesson_completeness", lambda c: c)
    monkeypatch.setattr(generator.time, "sleep", lambda s: None)
    return unit


def _workers(node):
    return [("http://node-a:11434", "fake-7b", node), ("http://node-b:11434", "fake-7b", node)]


def test_successful_regeneration_replaces_lessons_and_keeps_sessions(course):
    results = generator.generate_topic_parallel("computing", "regen_cat", "regen_topic", course,
                                                force=True, workers=_workers(Node()))
    assert results == {"lesson_01_new.md": True, "labs.md": True}
    names = sorted(p.name for p in course.iterdir())
    assert names == ["labs.md", "lesson_01_new.md", "sessions"]
    assert (course / "sessions" / "active_session.md").read_text() == "my chat\n"
    assert "Old" not in (course / "labs.md").read_text()


def test_failed_regeneration_keeps_the_old_course(course):
    results = generator.generate_topic_parallel("computing", "regen_cat", "regen_topic", course,
                                                force=True, workers=_workers(Node(fail_on="write labs")))
    assert results["labs.md"] is False
    assert (course / "lesson_01_old.md").read_text() == "# Old lesson\n"
    assert (course / "labs.md").read_text() == "# Old labs\n"
    assert not (course / "lesson_01_new.md").exists()
    assert (course / "sessions" / "active_session.md").exists()
    assert not (course / generator.STAGING_DIRNAME).exists()


def test_stop_publishes_nothing(course):
    with pytest.raises(GenerationStopped):
        generator.generate_topic_parallel("computing", "regen_cat", "regen_topic", course, force=True,
                                          workers=_workers(Node()), should_stop=lambda: True)
    assert sorted(p.name for p in course.iterdir()) == ["labs.md", "lesson_01_old.md", "sessions"]


def test_new_course_keeps_the_lessons_that_succeeded(course):
    for f in course.glob("*.md"):
        f.unlink()
    results = generator.generate_topic_parallel("computing", "regen_cat", "regen_topic", course,
                                                force=True, workers=_workers(Node(fail_on="write labs")))
    assert results == {"lesson_01_new.md": True, "labs.md": False}
    assert sorted(p.name for p in course.iterdir()) == ["lesson_01_new.md", "sessions"]


def test_api_cancel_stops_a_running_generation():
    """Stop in the UI only aborted the browser request; the server kept
    drafting. /api/generate/cancel now reaches the running generation."""
    import threading
    import time as _time
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.backend.main import app

    started = threading.Event()

    def fake_generate(*a, should_stop=None, **kw):
        started.set()
        for _ in range(500):
            if should_stop():
                raise GenerationStopped()
            _time.sleep(0.01)
        return {"lesson_01.md": True}

    client = TestClient(app)
    out = {}
    with patch("app.backend.main.generate_subtopic_content", fake_generate), \
         patch("app.backend.main.get_provider", lambda **k: object()):
        t = threading.Thread(target=lambda: out.update(res=client.post(
            "/api/generate", json={"query": "computing/infrastructure/kubernetes", "force": True})))
        t.start()
        assert started.wait(5)
        busy = client.post("/api/generate", json={"query": "computing/infrastructure/kubernetes"})
        cancel = client.post("/api/generate/cancel", json={"query": "computing/infrastructure/kubernetes"})
        t.join(10)
    assert busy.status_code == 409
    assert cancel.json() == {"cancelled": True}
    assert out["res"].status_code == 409
    assert "not changed" in out["res"].json()["detail"]


def test_files_already_on_disk_are_reported_as_skipped(course):
    (course / "lesson_01_new.md").write_text(LESSON, encoding="utf-8")
    (course / "labs.md").unlink()
    results = generator.generate_topic_parallel("computing", "regen_cat", "regen_topic", course,
                                                force=False, workers=_workers(Node()))
    assert results == {"lesson_01_new.md": False, "labs.md": True}
    assert results.skipped == {"lesson_01_new.md"}


def test_api_generate_lists_skipped_files():
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.backend.main import app

    res_obj = generator.GenerationResults({"lesson_01.md": False, "labs.md": True})
    res_obj.skipped.add("lesson_01.md")
    with patch("app.backend.main.generate_subtopic_content", lambda *a, **k: res_obj), \
         patch("app.backend.main.get_provider", lambda **k: object()):
        res = TestClient(app).post("/api/generate", json={"query": "computing/infrastructure/kubernetes"})
    assert res.status_code == 200
    assert res.json()["skipped"] == ["lesson_01.md"]
    assert res.json()["results"] == {"lesson_01.md": False, "labs.md": True}
