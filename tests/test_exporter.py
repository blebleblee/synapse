"""
Regression test for learning_engine.exporter.export_handbook.
Verifies real handbook compilation into the isolated temporary exports directory.
"""

from pathlib import Path
from learning_engine.exporter import export_handbook, get_exports_dir


def test_export_handbook_real_execution():
    """
    Calls the real export_handbook() without mocking it.
    Verifies that the compiled handbook is written into the temporary exports directory
    and contains the expected title and lesson text.
    """
    output_path = export_handbook("computing")

    assert output_path.exists()
    assert output_path.parent == get_exports_dir()
    assert output_path.suffix == ".md"

    content = output_path.read_text(encoding="utf-8")
    assert "Computing" in content
    assert "Comprehensive Engineering & Socratic Handbook" in content
    assert len(content) > 100
