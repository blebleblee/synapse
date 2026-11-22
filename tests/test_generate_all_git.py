"""scripts/generate_all.py must not push, and commits only when asked."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "generate_all.py"


@pytest.fixture
def gen():
    stdout_before = sys.stdout
    spec = importlib.util.spec_from_file_location("generate_all_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Importing must not hijack stdout or start logging to a file.
    assert sys.stdout is stdout_before
    return module


def _git_calls(mock_run):
    return [c.args[0] for c in mock_run.call_args_list if c.args and c.args[0][:1] == ["git"]]


def test_no_git_writes_by_default(gen, tmp_path):
    with patch.object(gen.subprocess, "run") as mock_run:
        gen.commit_topic(tmp_path / "x", "computing", "x", "gen", enabled=False)
    assert _git_calls(mock_run) == []


def test_commit_is_local_and_never_pushes(gen, tmp_path):
    with patch.object(gen.subprocess, "run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 0, "", "")
        gen.commit_topic(tmp_path / "x", "computing", "my_topic", "enhance", enabled=True)
    calls = _git_calls(mock_run)
    assert calls, "expected git add/commit when committing is enabled"
    assert all(c[1] != "push" for c in calls)
    assert any(c[1] == "commit" and "enhance(my_topic): masterclass curriculum" in c for c in calls)
    assert ["git", "add", "--", str(tmp_path / "x")] in calls


def test_commit_refuses_non_core_domain(gen, tmp_path):
    with patch.object(gen.subprocess, "run") as mock_run:
        gen.commit_topic(tmp_path / "x", "not_a_core_domain", "x", "gen", enabled=True)
    assert _git_calls(mock_run) == []


def test_commit_refuses_unsafe_subtopic_id(gen, tmp_path):
    with patch.object(gen.subprocess, "run") as mock_run:
        gen.commit_topic(tmp_path / "x", "computing", "bad id; rm", "gen", enabled=True)
    assert _git_calls(mock_run) == []


def test_source_has_no_push():
    assert '"push"' not in SCRIPT.read_text(encoding="utf-8")
