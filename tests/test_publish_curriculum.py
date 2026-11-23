"""Curriculum release bookkeeping in scripts/publish_all_releases.py. No network."""
import importlib.util
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def publish(monkeypatch, tmp_path):
    # The script loads ~/.config/synapse/env on import: point HOME elsewhere.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    spec = importlib.util.spec_from_file_location("publish_under_test", ROOT / "scripts" / "publish_all_releases.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pack(path: Path, lesson: str, lessons=1) -> Path:
    src = path.parent / (path.stem + "-src")
    f = src / "lesson_1.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(lesson, encoding="utf-8")
    m = src / "manifest.json"
    m.write_text(json.dumps({"lesson_count": lessons, "lab_count": 1}), encoding="utf-8")
    with tarfile.open(path, "w:gz") as tar:
        tar.add(f, arcname="topics/arts/a/b/lesson_1.md")
        tar.add(m, arcname="manifest.json")
    return path


def test_app_release_no_longer_carries_packs_or_the_duplicate_zip(publish):
    names = set(publish.ASSETS_TO_PUBLISH)
    assert not any(n.endswith(".synpack") for n in names)
    assert "Synapse-Portable-Windows.zip" not in names


def test_only_changed_packs_are_uploaded(publish, tmp_path):
    arts = _pack(tmp_path / "arts.synpack", "# A\n")
    crafts = _pack(tmp_path / "crafts.synpack", "# C\n")
    first = publish.curriculum_index({"arts.synpack": arts, "crafts.synpack": crafts}, "aaa1111", {})
    assert publish.changed_packs(first, {}) == ["arts.synpack", "crafts.synpack"]

    # Re-export: crafts unchanged (new archive bytes), arts edited.
    arts2 = _pack(tmp_path / "x" / "arts.synpack", "# A edited\n")
    crafts2 = _pack(tmp_path / "x" / "crafts.synpack", "# C\n")
    second = publish.curriculum_index({"arts.synpack": arts2, "crafts.synpack": crafts2}, "bbb2222", first)
    assert publish.changed_packs(second, first) == ["arts.synpack"]
    assert second["packs"]["crafts.synpack"]["commit"] == "aaa1111"  # unchanged pack keeps its origin
    assert second["packs"]["arts.synpack"]["commit"] == "bbb2222"


def test_curriculum_notes_list_every_pack(publish, tmp_path):
    index = publish.curriculum_index({"arts.synpack": _pack(tmp_path / "arts.synpack", "# A\n", lessons=7)}, "c", {})
    body = publish.curriculum_body(index)
    assert "| Arts | 7 | 1 |" in body
    assert "curriculum.json" in body


@pytest.mark.parametrize("argv", [["--help"], ["--bogus"], ["--curriculm"]])
def test_publisher_unknown_or_help_flag_publishes_nothing(publish, monkeypatch, argv):
    # Before argparse, any flag other than --curriculum fell through to a full
    # app publish on Gitea and GitHub.
    def boom(*a, **k):
        raise AssertionError("must not publish")
    for name in ("publish_gitea", "publish_github", "publish_curriculum"):
        monkeypatch.setattr(publish, name, boom)
    with pytest.raises(SystemExit):
        publish.main(argv)


@pytest.mark.parametrize("argv", [["--help"], ["1.3.1", "--dryrun"]])
def test_update_release_notes_bad_flag_changes_nothing(monkeypatch, tmp_path, argv):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    spec = importlib.util.spec_from_file_location("notes_under_test", ROOT / "scripts" / "update_release_notes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod.publish, "update_release_text", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not update")))
    with pytest.raises(SystemExit):
        mod.main(argv)
