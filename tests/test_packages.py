import pytest
import tarfile
from pathlib import Path
from learning_engine.packages import export_topic_pack, install_topic_pack, list_installed_packs

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
