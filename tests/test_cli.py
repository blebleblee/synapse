"""
CLI behavior (bin/synapse -> learning_engine.cli.main): program name, clean
errors instead of tracebacks, non-zero exit codes on failure, and a full-
curriculum review that stops when no reviewer model is reachable.
"""
import sys

import pytest

from learning_engine import cli


def run_cli(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["synapse", *argv])
    with pytest.raises(SystemExit) as exc:
        cli.main()
        raise SystemExit(0)
    return exc.value.code


def test_help_uses_the_synapse_program_name(monkeypatch, capsys):
    assert run_cli(monkeypatch, "--help") == 0
    assert capsys.readouterr().out.startswith("usage: synapse")


def test_command_error_is_one_line_and_exits_non_zero(monkeypatch, capsys):
    def broken(*a, **k):
        raise RuntimeError("Google GenAI client not initialized.")

    monkeypatch.setattr(cli, "generate_flashcards", broken)
    assert run_cli(monkeypatch, "flashcards", "computing/infrastructure/kubernetes") == 1
    err = capsys.readouterr().err
    assert "synapse flashcards failed: Google GenAI client not initialized." in err
    assert "Traceback" not in err


def test_full_review_stops_when_reviewer_is_unreachable(monkeypatch, capsys):
    calls = []

    def failing_review(path, **kwargs):
        calls.append(path)
        return {"has_issues": False, "review_failed": True,
                "reports": [{"verdict": "REVIEW_FAILED", "error": "reviewer call failed: connection refused"}]}

    tree = {"computing": {"disciplines": {"systems": {"courses": {
        f"c{i}": {"units": {"core": {"rel_path": f"computing/systems/c{i}", "full_path": f"/tmp/c{i}",
                                       "status": {"complete": True}}}}
        for i in range(10)
    }}}}}
    monkeypatch.setattr(cli, "review_and_fix_unit", failing_review)
    monkeypatch.setattr(cli, "get_topic_tree", lambda: tree)

    assert run_cli(monkeypatch, "review") == 1
    out = capsys.readouterr()
    assert len(calls) == 3
    assert "connection refused" in out.out + out.err


def test_clean_db_vacuums_for_real(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(cli, "vacuum_database", lambda: called.append(1))
    assert run_cli(monkeypatch, "clean", "--db") == 0
    assert called == [1]
    assert "Database optimization complete" in capsys.readouterr().out


def test_no_ai_available_error_names_the_real_cause(monkeypatch):
    """With Ollama down and no cloud key, the error used to ask only for a
    Gemini key, which misleads users who run local models."""
    from learning_engine import models
    for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(models.OllamaCluster, "get_cluster_status",
                        lambda self: {"http://127.0.0.1:11434": {"online": False, "models": []}})
    provider = models.get_provider()
    # generate() itself is blocked by conftest; check the error it would raise.
    assert provider.client is None
    assert "No AI model is reachable" in provider.unavailable_reason
    assert "127.0.0.1:11434" in provider.unavailable_reason


def test_pack_uninstall_reports_success(monkeypatch, capsys):
    """It removed the domain, then printed "Uninstall failed: 'message'" and
    exited 1, because the result has no "message" key."""
    import learning_engine.packages as packages
    (packages.TOPICS_DIR / "cli_probe").mkdir()
    assert run_cli(monkeypatch, "pack", "uninstall", "cli_probe") == 0
    out = capsys.readouterr().out
    assert "[+] Uninstalled: cli_probe" in out and "failed" not in out
    assert not (packages.TOPICS_DIR / "cli_probe").exists()


def test_pack_uninstall_dot_is_refused(monkeypatch, capsys):
    import learning_engine.packages as packages
    before = sorted(p.name for p in packages.TOPICS_DIR.iterdir())
    assert run_cli(monkeypatch, "pack", "uninstall", ".") == 1
    assert sorted(p.name for p in packages.TOPICS_DIR.iterdir()) == before
