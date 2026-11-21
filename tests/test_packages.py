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

