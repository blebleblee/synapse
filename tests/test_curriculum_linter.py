"""synapse lint catches what reached public lessons unnoticed.

Three lessons started with "Here is the fully corrected, publication-grade,
raw Markdown:" (shown as the lesson's title), a lab had no "# " title, and a
course had two lessons titled with the course name. `synapse lint` passed
all of them. Generated files also kept bare ``` fences, so every new course
produced UNTAGGED_CODE_BLOCK warnings."""
from learning_engine import linter
from learning_engine.code_fences import tag_untagged_fences

BODY = "\n\n## Core Ideas\n\n" + ("Real lesson content with enough words to look complete. " * 80) + "\n"


def _course(name="demo_course"):
    d = linter.TOPICS_DIR / "computing" / "software" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _codes(path):
    return {i.get("code") for i in linter.lint_markdown_file(path)}


def test_lint_flags_model_preamble(tmp_path):
    f = _course() / "lesson_01_intro.md"
    f.write_text("Here is the fully corrected, publication-grade, raw Markdown:\n\n# Lesson 1: Intro" + BODY, encoding="utf-8")
    assert "MODEL_PREAMBLE" in _codes(f)


def test_lint_flags_missing_title(tmp_path):
    f = _course() / "labs.md"
    f.write_text("Operational Labs: Demo\n=====\n" + BODY, encoding="utf-8")
    assert "MISSING_TITLE" in _codes(f)


def test_lint_accepts_a_normal_lesson(tmp_path):
    f = _course() / "lesson_01_intro.md"
    f.write_text("# Lesson 1: Intro" + BODY, encoding="utf-8")
    assert not {"MODEL_PREAMBLE", "MISSING_TITLE"} & _codes(f)


def test_lint_flags_duplicate_lesson_titles(tmp_path):
    d = _course("dup_course")
    (d / "lesson_01_a.md").write_text("# SQL and Relational Query Optimization" + BODY, encoding="utf-8")
    (d / "lesson_02_b.md").write_text("# SQL and Relational Query Optimization" + BODY, encoding="utf-8")
    (d / "labs.md").write_text("# Labs" + BODY, encoding="utf-8")
    report = linter.lint_curriculum("computing")
    assert any(i.get("code") == "DUPLICATE_LESSON_TITLE" and "dup_course" in i["file"] for i in report["issues"])


def test_bare_fences_get_a_language_and_labelled_ones_are_kept():
    text = "# T\n\n```\nkubectl get pods\n```\n\n```python\nx = 1\n```\n\n```\nplain output\n```"
    out, n = tag_untagged_fences(text)
    assert n == 2
    assert "```bash\nkubectl" in out and "```python\nx = 1" in out and "```text\nplain output" in out
    assert tag_untagged_fences(out) == (out, 0)
