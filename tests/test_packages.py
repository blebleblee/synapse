import io
import json
import pytest
import tarfile
from pathlib import Path
from learning_engine.packages import (
    export_topic_pack,
    install_topic_pack,
    list_installed_packs,
    uninstall_topic_pack,
    get_domain_pack_info
)
from learning_engine.security import TOPICS_DIR
from learning_engine.database import get_db_connection

def test_export_and_install_topic_pack(tmp_path):
    # Test exporting arts domain
    pack = export_topic_pack("arts", output_dir=tmp_path)
    assert pack.exists()
    assert pack.suffix == ".synpack"
    assert pack.stat().st_size > 0

    # Verify tar contents
    with tarfile.open(pack, "r:gz") as tar:
        names = tar.getnames()
        assert "manifest.json" in names
        assert any(n.startswith("topics/arts") for n in names)

    # Test installing package
    result = install_topic_pack(pack)
    assert result["status"] == "installed"
    assert result["domain"] == "arts"

    # Test listing packages
    installed = list_installed_packs()
    assert any(p["domain"] == "arts" for p in installed)

def test_install_pack_file_not_found(tmp_path):
    """Attempting to install a non-existent pack must raise FileNotFoundError."""
    missing = tmp_path / "does_not_exist.synpack"
    with pytest.raises(FileNotFoundError, match="not found"):
        install_topic_pack(missing)

def test_install_pack_corrupted_archive_rejected(tmp_path):
    """Attempting to install an uncompressed or corrupted file must raise tarfile.ReadError."""
    corrupt_pack = tmp_path / "corrupt.synpack"
    corrupt_pack.write_bytes(b"THIS_IS_NOT_A_VALID_GZIP_OR_TAR_ARCHIVE_DATA")

    with pytest.raises(tarfile.ReadError):
        install_topic_pack(corrupt_pack)

def test_install_pack_path_traversal_rejected(tmp_path):
    """
    A malicious package containing relative or absolute path traversal members
    must be immediately rejected with ValueError before any extraction occurs.
    """
    malicious_pack = tmp_path / "malicious.synpack"
    traversal_target = tmp_path / "should_not_exist.txt"

    with tarfile.open(malicious_pack, "w:gz") as tar:
        payload = b"pwned content"
        ti = tarfile.TarInfo(name="../should_not_exist.txt")
        ti.size = len(payload)
        tar.addfile(ti, io.BytesIO(payload))

    with pytest.raises(ValueError, match="Malicious package detected with path traversal"):
        install_topic_pack(malicious_pack)

    assert not traversal_target.exists()

def test_package_uninstall_and_reinstall_roundtrip(tmp_path):
    """
    Comprehensive round-trip test:
    1. Authored content in a domain.
    2. Export to .synpack.
    3. Uninstall domain: verifies directory is deleted and DB mastery cleaned up.
    4. Reinstall from .synpack: verifies directory and files are completely restored.
    """
    crafts_dir = TOPICS_DIR / "crafts"
    course_dir = crafts_dir / "woodworking" / "joinery"
    course_dir.mkdir(parents=True, exist_ok=True)

    (crafts_dir / "SYLLABUS.md").write_text("# Crafts Syllabus\n\n- **Joinery** (`woodworking/joinery/`)\n", encoding="utf-8")
    (course_dir / "lesson_01.md").write_text("# Mortise and Tenon\nFoundational wood joinery mechanics.\n", encoding="utf-8")
    (course_dir / "labs.md").write_text("# Hands-on Lab\nCut a through-tenon joint.\n", encoding="utf-8")

    # Record mastery progress in DB
    with get_db_connection() as conn:
        conn.execute("INSERT INTO mastery (path, state, completed_lessons) VALUES (?, ?, ?)",
                     ("crafts/woodworking/joinery", "studying", json.dumps(["lesson_01"])))

    # Verify pack info
    info = get_domain_pack_info("crafts")
    assert info["lesson_count"] >= 1
    assert info["lab_count"] >= 1

    # Export domain
    pack_path = export_topic_pack("crafts", output_dir=tmp_path)
    assert pack_path.exists()

    # Uninstall domain
    uninst = uninstall_topic_pack("crafts")
    assert uninst["status"] == "uninstalled"
    assert not crafts_dir.exists()

    # Verify DB mastery cleaned up
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM mastery WHERE path LIKE 'crafts/%'").fetchone()
        assert row is None

    # Reinstall from exported .synpack
    res = install_topic_pack(pack_path)
    assert res["status"] == "installed"
    assert res["domain"] == "crafts"
    assert crafts_dir.exists()
    assert (course_dir / "lesson_01.md").exists()
    assert (course_dir / "labs.md").exists()
    assert "Mortise and Tenon" in (course_dir / "lesson_01.md").read_text(encoding="utf-8")

def test_install_pack_corrupted_manifest_fallback(tmp_path):
    """
    If manifest.json is corrupted or not valid JSON, install_topic_pack
    should gracefully recover the domain name from the package filename.
    """
    pack_path = tmp_path / "woodcraft.synpack"
    with tarfile.open(pack_path, "w:gz") as tar:
        # Malformed manifest
        bad_json = b"{ domain: 'unquoted_broken_json'"
        ti = tarfile.TarInfo(name="manifest.json")
        ti.size = len(bad_json)
        tar.addfile(ti, io.BytesIO(bad_json))

        # Valid topic file
        content = b"# Woodcraft Overview\n"
        ti2 = tarfile.TarInfo(name="topics/woodcraft/SYLLABUS.md")
        ti2.size = len(content)
        tar.addfile(ti2, io.BytesIO(content))

    res = install_topic_pack(pack_path)
    assert res["status"] == "installed"
    assert res["domain"] == "woodcraft"
    assert (TOPICS_DIR / "woodcraft" / "SYLLABUS.md").exists()

def test_install_pack_symlink_rejected(tmp_path):
    """Packages containing symbolic links must be rejected as unsafe members."""
    pack_path = tmp_path / "symlink_attack.synpack"
    with tarfile.open(pack_path, "w:gz") as tar:
        ti = tarfile.TarInfo(name="topics/attack/evil_symlink")
        ti.type = tarfile.SYMTYPE
        ti.linkname = "/etc/passwd"
        tar.addfile(ti)

    with pytest.raises(ValueError, match="unsafe link or device member"):
        install_topic_pack(pack_path)

def test_install_pack_hardlink_rejected(tmp_path):
    """Packages containing hard links must be rejected as unsafe members."""
    pack_path = tmp_path / "hardlink_attack.synpack"
    with tarfile.open(pack_path, "w:gz") as tar:
        ti = tarfile.TarInfo(name="topics/attack/evil_hardlink")
        ti.type = tarfile.LNKTYPE
        ti.linkname = "/etc/shadow"
        tar.addfile(ti)

    with pytest.raises(ValueError, match="unsafe link or device member"):
        install_topic_pack(pack_path)

def test_install_pack_unexpected_manifest_json_type(tmp_path):
    """
    If manifest.json contains valid JSON that is not an object (e.g. array or string),
    it must not crash with AttributeError and must fall back to the package filename.
    """
    pack_path = tmp_path / "safe_array_domain.synpack"
    with tarfile.open(pack_path, "w:gz") as tar:
        array_json = b'["not", "a", "dict"]'
        ti = tarfile.TarInfo(name="manifest.json")
        ti.size = len(array_json)
        tar.addfile(ti, io.BytesIO(array_json))

        content = b"# Safe Array Domain\n"
        ti2 = tarfile.TarInfo(name="topics/safe_array_domain/SYLLABUS.md")
        ti2.size = len(content)
        tar.addfile(ti2, io.BytesIO(content))

    res = install_topic_pack(pack_path)
    assert res["status"] == "installed"
    assert res["domain"] == "safe_array_domain"
    assert (TOPICS_DIR / "safe_array_domain" / "SYLLABUS.md").exists()

def test_install_pack_malicious_domain_name_rejected(tmp_path):
    """
    A manifest containing directory traversal or slashes in its domain field
    must be rejected with ValueError before any backup or directory operations.
    """
    pack_path = tmp_path / "malicious_domain.synpack"
    with tarfile.open(pack_path, "w:gz") as tar:
        bad_manifest = json.dumps({"domain": "../traversal_domain"}).encode("utf-8")
        ti = tarfile.TarInfo(name="manifest.json")
        ti.size = len(bad_manifest)
        tar.addfile(ti, io.BytesIO(bad_manifest))

    with pytest.raises(ValueError, match="Invalid domain identifier"):
        install_topic_pack(pack_path)

def test_install_pack_filename_domain_traversal_rejected(tmp_path):
    """
    When manifest is absent, a filename with path traversal characters
    must be rejected with ValueError.
    """
    pack_path = tmp_path / "..traversal_filename.synpack"
    with tarfile.open(pack_path, "w:gz") as tar:
        content = b"# Dummy\n"
        ti = tarfile.TarInfo(name="topics/dummy/SYLLABUS.md")
        ti.size = len(content)
        tar.addfile(ti, io.BytesIO(content))

    with pytest.raises(ValueError, match="Invalid domain identifier"):
        install_topic_pack(pack_path)




def _write_pack(pack_path, manifest, members):
    with tarfile.open(pack_path, "w:gz") as tar:
        if manifest is not None:
            data = json.dumps(manifest).encode("utf-8")
            ti = tarfile.TarInfo(name="manifest.json")
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))
        for name, payload in members.items():
            ti = tarfile.TarInfo(name=name)
            ti.size = len(payload)
            tar.addfile(ti, io.BytesIO(payload))


def test_install_domain_pack_cannot_write_into_other_domain(tmp_path):
    """A domain pack may only write inside its own domain folder."""
    pack_path = tmp_path / "arts.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "arts"}, {
        "topics/arts/ok/course/labs.md": b"# ok\n",
        "topics/crafts/injected.md": b"# injected\n",
    })

    with pytest.raises(ValueError, match="outside its domain"):
        install_topic_pack(pack_path)

    assert not (TOPICS_DIR / "crafts" / "injected.md").exists()
    assert not (TOPICS_DIR / "arts" / "ok" / "course" / "labs.md").exists()


def test_install_domain_pack_cannot_write_topics_root(tmp_path):
    pack_path = tmp_path / "arts.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "arts"}, {
        "topics/stray.md": b"# stray\n",
    })

    with pytest.raises(ValueError, match="outside its domain"):
        install_topic_pack(pack_path)

    assert not (TOPICS_DIR / "stray.md").exists()


def test_install_complete_pack_limited_to_listed_domains(tmp_path):
    pack_path = tmp_path / "synapse_complete_curriculum.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "complete", "domains": ["arts"]}, {
        "topics/arts/a/b/labs.md": b"# a\n",
        "topics/unlisted/x.md": b"# x\n",
    })

    with pytest.raises(ValueError, match="outside its domain"):
        install_topic_pack(pack_path)

    assert not (TOPICS_DIR / "unlisted").exists()


def test_install_complete_pack_writes_listed_domains(tmp_path):
    pack_path = tmp_path / "synapse_complete_curriculum.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "complete", "domains": ["arts", "crafts"]}, {
        "topics/arts/p/q/labs.md": b"# arts\n",
        "topics/crafts/p/q/labs.md": b"# crafts\n",
    })

    res = install_topic_pack(pack_path)
    assert res["domain"] == "complete"
    assert (TOPICS_DIR / "arts" / "p" / "q" / "labs.md").read_bytes() == b"# arts\n"
    assert (TOPICS_DIR / "crafts" / "p" / "q" / "labs.md").read_bytes() == b"# crafts\n"


def test_exported_complete_pack_installs(tmp_path):
    """The complete pack built by export_topic_pack passes the domain check."""
    pack = export_topic_pack("complete", output_dir=tmp_path)
    res = install_topic_pack(pack)
    assert res["domain"] == "complete"


def test_install_complete_pack_backs_up_each_listed_domain(tmp_path):
    """Installing the complete pack saves a copy of every domain it replaces."""
    from learning_engine.packages import WORKSPACE_ROOT as PKG_WS
    existing = TOPICS_DIR / "arts" / "local" / "edit" / "labs.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("# my local edit\n")

    pack_path = tmp_path / "synapse_complete_curriculum.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "complete", "domains": ["arts", "crafts"]}, {
        "topics/arts/p/q/labs.md": b"# arts\n",
        "topics/crafts/p/q/labs.md": b"# crafts\n",
    })
    install_topic_pack(pack_path)

    backups = PKG_WS / "exports" / "backups"
    arts_backups = sorted(backups.glob("arts_backup_*"))
    assert arts_backups, "arts was replaced without a backup"
    assert (arts_backups[-1] / "local" / "edit" / "labs.md").read_text() == "# my local edit\n"


def test_pack_content_digest_ignores_timestamps_but_not_content(tmp_path):
    """Re-exporting unchanged content must give the same digest, so the curriculum
    release only re-uploads packs whose lessons actually changed."""
    import os
    import time
    from learning_engine.packages import pack_content_digest

    def make(path, body, mtime):
        src = tmp_path / f"src-{mtime}"
        f = src / "topics" / "arts" / "x" / "y" / "lesson_1.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
        os.utime(f, (mtime, mtime))
        with tarfile.open(path, "w:gz") as tar:
            tar.add(f, arcname="topics/arts/x/y/lesson_1.md")
        return path

    a = make(tmp_path / "a.synpack", "# Lesson\n", 1_000_000)
    time.sleep(1.1)  # gzip header carries the write time
    b = make(tmp_path / "b.synpack", "# Lesson\n", 2_000_000)
    c = make(tmp_path / "c.synpack", "# Lesson changed\n", 1_000_000)
    assert a.read_bytes() != b.read_bytes()
    assert pack_content_digest(a) == pack_content_digest(b)
    assert pack_content_digest(a) != pack_content_digest(c)


def test_pack_download_tries_the_curriculum_release_first(monkeypatch, tmp_path):
    import urllib.request
    import learning_engine.packages as pk

    monkeypatch.setattr(pk, "get_packs_dir", lambda: tmp_path / "packs")
    monkeypatch.setenv("SYNAPSE_RESOURCES_PATH", str(tmp_path / "no-resources"))
    monkeypatch.delenv("SYNAPSE_PACKAGE_REGISTRY", raising=False)
    tried = []
    def fake_urlopen(req, timeout=None):
        tried.append(req.full_url)
        raise OSError("offline")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(FileNotFoundError):
        pk.resolve_or_download_pack("complete")
    assert tried[0] == "https://github.com/blebleblee/synapse/releases/download/curriculum/synapse_complete_curriculum.synpack"
    assert tried[1] == "https://gitea.2464.cz/ai/synapse/releases/download/curriculum/synapse_complete_curriculum.synpack"
    # Older app-release locations stay as fallbacks.
    assert any("/download/v1.2.0/" in u for u in tried[2:])


def test_failed_install_leaves_existing_domain_untouched(tmp_path, monkeypatch):
    """A write failure partway through must not leave a half-updated domain."""
    import shutil as _shutil
    import learning_engine.packages as pk

    lesson = TOPICS_DIR / "arts" / "c" / "t" / "lesson_1.md"
    lesson.parent.mkdir(parents=True, exist_ok=True)
    lesson.write_text("# old lesson\n")
    mine = TOPICS_DIR / "arts" / "c" / "t" / "my_notes.md"
    mine.write_text("# my notes\n")

    pack_path = tmp_path / "arts.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "arts"}, {
        "topics/arts/c/t/lesson_1.md": b"# new lesson\n",
        "topics/arts/c/t/labs.md": b"# new labs\n",
        "topics/arts/c/u/lesson_1.md": b"# another\n",
    })

    real_copy = _shutil.copyfileobj
    calls = {"n": 0}
    def flaky_copy(src, dst, *a, **kw):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        return real_copy(src, dst, *a, **kw)
    monkeypatch.setattr(pk.shutil, "copyfileobj", flaky_copy)

    with pytest.raises(OSError, match="disk full"):
        install_topic_pack(pack_path)

    assert lesson.read_text() == "# old lesson\n"
    assert mine.read_text() == "# my notes\n"
    assert not (TOPICS_DIR / "arts" / "c" / "t" / "labs.md").exists()
    assert not (TOPICS_DIR / "arts" / "c" / "u").exists()
    assert not [p for p in TOPICS_DIR.iterdir() if p.name.startswith(".")], "staging left behind"


def test_install_merges_pack_into_existing_domain(tmp_path):
    """Pack files replace their counterparts; the learner's other files stay."""
    lesson = TOPICS_DIR / "arts" / "c" / "t" / "lesson_1.md"
    lesson.parent.mkdir(parents=True, exist_ok=True)
    lesson.write_text("# old lesson\n")
    mine = TOPICS_DIR / "arts" / "c" / "t" / "my_notes.md"
    mine.write_text("# my notes\n")

    pack_path = tmp_path / "arts.synpack"
    _write_pack(pack_path, {"format": "synpack/v1", "domain": "arts"}, {
        "topics/arts/c/t/lesson_1.md": b"# new lesson\n",
    })
    install_topic_pack(pack_path)

    assert lesson.read_text() == "# new lesson\n"
    assert mine.read_text() == "# my notes\n"
    assert not [p for p in TOPICS_DIR.iterdir() if p.name.startswith(".")]


def test_search_skips_hidden_staging_folders():
    from learning_engine.search import _iter_markdown
    hidden = TOPICS_DIR / ".install-1-1" / "pack" / "arts" / "c" / "t" / "lesson_1.md"
    hidden.parent.mkdir(parents=True, exist_ok=True)
    hidden.write_text("# staged\n")
    visible = TOPICS_DIR / "arts" / "c" / "t" / "lesson_1.md"
    visible.parent.mkdir(parents=True, exist_ok=True)
    visible.write_text("# live\n")
    found = list(_iter_markdown(TOPICS_DIR))
    assert visible in found
    assert hidden not in found
