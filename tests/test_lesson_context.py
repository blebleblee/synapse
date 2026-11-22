"""The mentor sees the part of the lesson the learner is asking about.

It used to get only the first 5,000 characters, so on a typical 25-50k
lesson every question about a later section was answered without the
lesson; and /api/chat rejected lessons over 50,000 characters (422), so
the mentor failed outright on 351 public lessons and labs."""
from fastapi.testclient import TestClient

from app.backend.lesson_context import lesson_excerpt


def _lesson():
    filler = "Background prose about shells and processes. " * 60  # ~2.7k chars
    return (
        "# Lesson 1: Shells\n\nIntro paragraph.\n\n"
        f"## 1. Basics\n{filler}\n\n"
        f"## 2. Parsing\n{filler}\n\n"
        f"## 3. Redirection\n{filler}\n\n"
        "## 4. Compound commands\n### 4.6 Test brackets\n"
        "The [[ ]] keyword does not word-split and supports =~ regex matching.\n"
        f"{filler}\n\n"
        f"## 5. Pipelines\nEach pipeline stage runs in a subshell. {filler}\n"
    )


def test_short_lesson_is_passed_whole():
    text = "# L\n\n## A\nsmall\n"
    assert lesson_excerpt(text, "anything") == text.strip()


def test_question_about_a_late_section_includes_that_section():
    text = _lesson()
    out = lesson_excerpt(text, "What does [[ ]] regex matching do here?", budget=6000)
    assert "=~ regex matching" in out
    assert "# Lesson 1: Shells" in out  # the lesson title stays for orientation
    assert len(out) <= 6000


def test_pipeline_question_picks_pipeline_section():
    out = lesson_excerpt(_lesson(), "why does my pipeline run in a subshell", budget=6000)
    assert "Each pipeline stage runs in a subshell" in out


def test_section_title_wins():
    out = lesson_excerpt(_lesson(), "explain this", section_title="3. Redirection", budget=6000)
    assert out.lstrip().startswith("## 3. Redirection")


def test_chat_accepts_a_long_lesson(monkeypatch):
    import app.backend.main as backend

    seen = {}

    class FakeProvider:
        def generate(self, prompt, system_instruction=None, **kw):
            seen["prompt"] = prompt
            return "ok"

    monkeypatch.setattr(backend, "get_chat_provider", lambda model=None, host=None: (FakeProvider(), "fake"))
    long_lesson = _lesson() + ("x " * 40000)  # > 50,000 chars
    client = TestClient(backend.app)
    res = client.post("/api/chat", json={"message": "What does [[ ]] regex matching do?", "lesson_content": long_lesson})
    assert res.status_code == 200, res.text
    assert "=~ regex matching" in seen["prompt"]


def test_question_naming_nothing_in_the_lesson_gets_the_opening():
    text = _lesson()
    out = lesson_excerpt(text, "give me a scenario", budget=6000)
    assert text.startswith(out[:2000])
    assert out.startswith("# Lesson 1: Shells")
