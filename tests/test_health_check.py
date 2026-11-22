"""
Unit tests for scripts/health_check.py diagnostic utility.
"""

import sys
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.health_check import (
    check_python_environment,
    check_database,
    check_frontend_assets,
    check_curriculum,
    check_local_ai,
    run_all_checks,
)


def test_health_check_python_environment():
    report = check_python_environment()
    assert report["ok"] is True
    assert report["valid_version"] is True
    assert len(report["missing_dependencies"]) == 0


def test_health_check_database(tmp_path, monkeypatch):
    from learning_engine.database import init_db, DB_PATH
    report = check_database()
    assert report["ok"] is True
    assert report["integrity"] == "ok"
    assert report["has_mastery"] is True
    assert report["has_settings"] is True


def test_health_check_frontend_assets():
    report = check_frontend_assets()
    assert report["ok"] is True
    assert report["built_bundle_present"] is True
    assert report["fonts_present"] is True
    assert report["powerline_font"] is True
    assert report["nerd_font"] is True


def test_health_check_curriculum():
    report = check_curriculum()
    assert report["ok"] is True
    assert report["total_present"] > 0
    assert "computing" in report["core_domains_present"]


def test_health_check_local_ai(monkeypatch):
    from learning_engine.models import OllamaCluster
    monkeypatch.setattr(
        OllamaCluster,
        "get_cluster_status",
        lambda self: {"http://127.0.0.1:11434": {"online": True, "models": ["qwen2.5-coder:32b"]}}
    )
    report = check_local_ai()
    assert report["ok"] is True
    assert report["is_online"] is True
    assert "qwen2.5-coder:32b" in report["models_available"]


def test_health_check_run_all_checks():
    report = run_all_checks()
    assert report["status"] == "pass"
    assert report["python"]["ok"] is True
    assert report["database"]["ok"] is True
    assert report["frontend"]["ok"] is True
