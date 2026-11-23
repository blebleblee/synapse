"""
Packs must never contain private or personal content:
- chat sessions and private blueprints are excluded from every pack;
- git-ignored (private sideloaded) tracks inside core domains are excluded;
- the complete pack contains and names only the 12 core domains;
- private domains still export for local use.
"""
import json
import sys
import tarfile
from pathlib import Path

import learning_engine.packages as packages
import learning_engine.security as sec

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_release_packs  # noqa: E402


def _write(path: Path, text: str = "content\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _members(pack: Path):
    with tarfile.open(pack) as t:
        names = [m.name for m in t.getmembers() if m.isfile()]
        manifest = json.load(t.extractfile("manifest.json"))
    return names, manifest


def _seed(monkeypatch):
    topics = Path(sec.TOPICS_DIR)
    public = _write(topics / "languages" / "linguistics" / "phonology" / "lesson_01.md")
    _write(topics / "languages" / "linguistics" / "phonology" / "labs.md")
    private_track = _write(topics / "languages" / "secret_track" / "unit" / "lesson_01.md")
    _write(topics / "languages" / "linguistics" / "phonology" / "sessions" / "active_session.md", "my chat\n")
    _write(topics / "languages" / "linguistics" / "phonology" / "sessions" / "chat_history.json", "[]\n")
    _write(topics / "languages" / "CURRICULUM_BLUEPRINT.md", "plan\n")
    _write(topics / ".workspace_sessions" / "active_session.md", "chat\n")
    private_domain = _write(topics / "private_music" / "theory" / "harmony" / "lesson_01.md")
    _write(topics / "private_music" / "theory" / "harmony" / "sessions" / "active_session.md")
    # Simulate .gitignore declaring the private track inside a core domain.
    monkeypatch.setattr(packages, "_git_ignored", lambda paths: {p for p in paths if "secret_track" in str(p)})
    return public, private_track, private_domain


def test_domain_pack_excludes_sessions_blueprints_and_ignored_tracks(monkeypatch, tmp_path):
    _seed(monkeypatch)
    names, manifest = _members(packages.export_topic_pack("languages", output_dir=tmp_path))
    assert "topics/languages/linguistics/phonology/lesson_01.md" in names
    assert "topics/languages/linguistics/phonology/labs.md" in names
    assert not any("secret_track" in n for n in names)
    assert not any("/sessions/" in n for n in names)
    assert not any(n.endswith("CURRICULUM_BLUEPRINT.md") for n in names)
    assert manifest["lesson_count"] == 1 and manifest["lab_count"] == 1


def test_complete_pack_contains_and_names_only_core_domains(monkeypatch, tmp_path):
    _seed(monkeypatch)
    names, manifest = _members(packages.export_topic_pack("all", output_dir=tmp_path))
    assert not any(n.startswith("topics/private_music/") for n in names)
    assert not any(".workspace_sessions" in n or "/sessions/" in n for n in names)
    assert not any("secret_track" in n for n in names)
    assert set(manifest["domains"]) <= set(packages.CORE_DOMAINS)
    assert "private_music" not in json.dumps(manifest)


def test_private_domain_still_exports_for_local_use(monkeypatch, tmp_path):
    _seed(monkeypatch)
    names, manifest = _members(packages.export_topic_pack("private_music", output_dir=tmp_path))
    assert "topics/private_music/theory/harmony/lesson_01.md" in names
    assert not any("/sessions/" in n for n in names)
    assert manifest["domain"] == "private_music"


def test_release_guard_rejects_untracked_and_private_content(monkeypatch, tmp_path):
    _seed(monkeypatch)
    monkeypatch.setattr(packages, "_git_ignored", lambda paths: set())  # pretend no git: track leaks in
    pack = packages.export_topic_pack("languages", output_dir=tmp_path)
    tracked = {"topics/languages/linguistics/phonology/lesson_01.md",
               "topics/languages/linguistics/phonology/labs.md"}
    problems = check_release_packs.check_pack(pack, tracked)
    assert any("not tracked" in p for p in problems)

    private = packages.export_topic_pack("private_music", output_dir=tmp_path)
    problems = check_release_packs.check_pack(private, tracked)
    assert any("outside the core domains" in p for p in problems)
    assert any("non-core domain" in p for p in problems)


def test_release_guard_accepts_clean_pack(monkeypatch, tmp_path):
    _seed(monkeypatch)
    pack = packages.export_topic_pack("languages", output_dir=tmp_path)
    topics = Path(sec.TOPICS_DIR)
    tracked = {f"topics/{f.relative_to(topics).as_posix()}" for f in packages.iter_pack_files("languages")}
    assert check_release_packs.check_pack(pack, tracked) == []


def test_cli_pack_export(tmp_path, monkeypatch):
    """`synapse pack export` exists (runbook, pipeline and release guard rely on it)."""
    import sys
    from learning_engine import cli
    monkeypatch.setattr(sys, "argv", ["synapse", "pack", "export", "computing", "-o", str(tmp_path)])
    cli.main()
    assert (tmp_path / "computing.synpack").exists()


def test_mastered_field_guide_is_never_packed(monkeypatch, tmp_path):
    """The removed "Mastered Field Guide" wrote artifacts/MASTERED_GUIDE.md into the
    course folder, synthesized from the learner's chat sessions. It was not
    git-ignored, so exporting the domain to share it included it."""
    _seed(monkeypatch)
    _write(Path(sec.TOPICS_DIR) / "languages" / "linguistics" / "phonology" / "artifacts" / "MASTERED_GUIDE.md", "my notes\n")
    names, _ = _members(packages.export_topic_pack("languages", output_dir=tmp_path))
    assert not any(n.endswith("MASTERED_GUIDE.md") for n in names)
    assert "topics/languages/linguistics/phonology/lesson_01.md" in names


def test_course_summary_is_never_packed(monkeypatch, tmp_path):
    """The removed "Regenerate summary" wrote <course>/SUMMARY.md with a
    "Discussion Insights" section taken from the learner's chat sessions."""
    _seed(monkeypatch)
    _write(Path(sec.TOPICS_DIR) / "languages" / "linguistics" / "phonology" / "SUMMARY.md", "what I asked the tutor\n")
    names, _ = _members(packages.export_topic_pack("languages", output_dir=tmp_path))
    assert not any(n.lower().endswith("summary.md") for n in names)
    assert "topics/languages/linguistics/phonology/lesson_01.md" in names
