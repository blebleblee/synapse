"""Domain profiles: private domains keep their prompt templates (and names) in
their own DOMAIN_PROFILE.json, outside the public code. Made-up domain names
only; tmp workspace via conftest."""
import importlib.util
import io
import contextlib
import json
from pathlib import Path

import pytest

import learning_engine.security as sec
from learning_engine import generator, linter
from learning_engine.domain_profiles import PROFILE_FILENAME, domain_profile, render_profile_template

ROOT = Path(__file__).resolve().parents[1]
OUTLINE = "\n".join(
    f"*   **Lesson {i}: Topic {i} (30 mins)**\n    *   *Focus:* focus {i}\n    *   *Hands-On:* drill {i}\n" for i in range(1, 4))


def _domain(name, profile=None):
    d = Path(sec.TOPICS_DIR) / name
    course = d / "cat_a" / "course_a"
    course.mkdir(parents=True, exist_ok=True)
    if profile is not None:
        (d / PROFILE_FILENAME).write_text(json.dumps(profile), encoding="utf-8")
    return course


def _scope(domain, course, scoper=None):
    with contextlib.redirect_stdout(io.StringIO()):
        return generator.scope_topic_curriculum(domain, "cat_a", "course_a", "Course A",
                                                subtopic_dir=course, scoping_provider=scoper)


def test_missing_invalid_or_unsafe_profiles_are_empty():
    _domain("unlisted_plain")
    assert domain_profile("unlisted_plain") == {}
    bad = Path(sec.TOPICS_DIR) / "unlisted_bad"
    bad.mkdir(parents=True, exist_ok=True)
    (bad / PROFILE_FILENAME).write_text("{not json", encoding="utf-8")
    assert domain_profile("unlisted_bad") == {}
    assert domain_profile("../etc") == {}


def test_profile_is_found_next_to_the_course_outside_topics(tmp_path):
    course = tmp_path / "elsewhere" / "dom" / "cat" / "course"
    course.mkdir(parents=True)
    (tmp_path / "elsewhere" / "dom" / PROFILE_FILENAME).write_text('{"music_style": true}', encoding="utf-8")
    assert domain_profile("dom", course) == {"music_style": True}


def test_render_fills_known_names_only():
    assert render_profile_template("{title} / {other} / {{x}}", {"title": "T"}) == "T / {other} / {{x}}"
    assert render_profile_template(None, {}) == ""


def test_outline_lessons_and_capstone_come_from_the_profile():
    course = _domain("unlisted_outline", {"outline_lesson": {"structure": "STRUCT {title} {hands_on}",
                                                             "relevance": "REL {subtopic_title} {category_title}"},
                                          "outline_capstone": "CAP {cap_title} for {subtopic_title}"})
    (course / "TOPIC_OUTLINE.md").write_text(OUTLINE, encoding="utf-8")
    mods = _scope("unlisted_outline", course)
    assert [m["filename"] for m in mods][:3] == ["lesson_01_topic_1.md", "lesson_02_topic_2.md", "lesson_03_topic_3.md"]
    assert "STRUCT Lesson 1: Topic 1 drill 1" in mods[0]["prompt"]
    assert "REL Course A Cat A" in mods[0]["prompt"]
    assert mods[-1]["filename"] == "labs.md" and mods[-1]["prompt"] == "CAP Course A Capstone Sprint for Course A"


def test_without_a_profile_the_built_in_templates_are_used():
    course = _domain("unlisted_noprofile")
    (course / "TOPIC_OUTLINE.md").write_text(OUTLINE, encoding="utf-8")
    mods = _scope("unlisted_noprofile", course)
    assert "MASTERCLASS CHAPTER BLUEPRINT" in mods[0]["prompt"]
    assert "Practical Capstone Challenge Guide" in mods[-1]["prompt"]


def test_music_style_profile_marks_music_courses():
    course = _domain("unlisted_music", {"music_style": True})
    assert generator._is_music_course("unlisted_music", "cat_a", "course_a", course)
    assert not generator._is_music_course("unlisted_plain2", "cat_a", "course_a")


class Scoper:
    def generate(self, *a, **k):
        return json.dumps({"lessons": [{"filename": "lesson_01_x.md", "title": "Lesson 1: X"},
                                       {"filename": "lesson_02_y.md", "title": "Lesson 2: Y"}]})


def test_scoped_lessons_use_the_profile_structure():
    course = _domain("unlisted_scoped", {"scoped_lesson": {"structure": "SCOPED {title}"}})
    mods = _scope("unlisted_scoped", course, Scoper())
    assert "SCOPED Lesson 1: X" in mods[0]["prompt"]
    plain = _scope("unlisted_scoped_plain", _domain("unlisted_scoped_plain"), Scoper())
    assert "SCOPED" not in plain[0]["prompt"] and "Enterprise Problem" in plain[0]["prompt"]


def test_linter_allows_a_pattern_the_profile_allows():
    allowed = _domain("unlisted_lint_ok", {"linter_allow": ["bpftool"]}) / "lesson_01_a.md"
    denied = _domain("unlisted_lint_no") / "lesson_01_a.md"
    for f in (allowed, denied):
        f.write_text("# Lesson 1: A\n\nRun bpftool prog list.\n", encoding="utf-8")
    codes = lambda f: {i["code"] for i in linter.lint_markdown_file(f)}
    assert "CROSS_DOMAIN_BLEED" not in codes(allowed)
    assert "CROSS_DOMAIN_BLEED" in codes(denied)


def _guard():
    spec = importlib.util.spec_from_file_location("guard", ROOT / "scripts" / "check_staged_content.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_guard_flags_quoted_names_and_topics_paths():
    g = _guard()
    text = 'if domain in ["unlisted_x"]:\n    p = "topics/unlisted_y/a.md"\nok = "unlisted_x" # not-a-domain\nplain word unlisted_x\n'
    assert g.find_private_domain_names(text, ["unlisted_x", "unlisted_y"], set()) == [1, 2]
    # A name that is also a public category is checked as a path only.
    assert g.find_private_domain_names(text, ["unlisted_x", "unlisted_y"], {"unlisted_x"}) == [2]


def test_guard_reads_private_names_from_local_folders(tmp_path, monkeypatch):
    g = _guard()
    (tmp_path / "topics" / "computing").mkdir(parents=True)
    (tmp_path / "topics" / "unlisted_z").mkdir()
    (tmp_path / "addons" / "topics" / "unlisted_w").mkdir(parents=True)
    monkeypatch.setenv("SYNAPSE_ADDONS_DIR", str(tmp_path / "addons"))
    assert g.local_private_domains(tmp_path / "topics") == ["unlisted_w", "unlisted_z"]


def test_lint_works_on_topics_outside_the_workspace(tmp_path, monkeypatch):
    topics = tmp_path / "outside" / "topics"
    f = topics / "unlisted_out" / "cat" / "course" / "lesson_01_a.md"
    f.parent.mkdir(parents=True)
    f.write_text("# Lesson 1: A\n\nText.\n", encoding="utf-8")
    monkeypatch.setattr(linter, "TOPICS_DIR", topics)
    issues = linter.lint_markdown_file(f)
    assert all(i["file"] == "topics/unlisted_out/cat/course/lesson_01_a.md" for i in issues)
    assert linter._display_path(f) == "topics/unlisted_out/cat/course/lesson_01_a.md"
