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


def test_chat_loads_the_course_and_answers(monkeypatch, capsys):
    """`synapse chat` crashed at once: get_unit_lessons was never imported."""
    seen = {}

    class Fake:
        model = "fake"

        def generate(self, prompt, system_instruction=""):
            seen["system"] = system_instruction
            return "Pods are scheduled by the scheduler."

    answers = iter(["What schedules pods?", "exit"])
    monkeypatch.setattr(cli, "get_provider", lambda **k: Fake())
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    assert run_cli(monkeypatch, "chat", "computing/infrastructure/kubernetes") == 0
    out = capsys.readouterr().out
    assert "Tutor > Pods are scheduled by the scheduler." in out
    assert "--- lesson_" in seen["system"]


@pytest.mark.parametrize("argv", [
    ["add", "computing", "infrastructure", "cli_gen_probe", "-g"],
    ["generate", "computing/infrastructure/kubernetes"],
])
def test_generation_failure_is_reported_and_exits_non_zero(monkeypatch, capsys, argv):
    """Every file failed, yet `add -g` printed the raw result dict and `generate`
    said "Learning modules updated", both with exit code 0."""
    monkeypatch.setattr(cli, "get_provider", lambda **k: object())
    monkeypatch.setattr(cli, "generate_subtopic_content",
                        lambda *a, **k: {"lesson_01_x.md": True, "labs.md": False})
    assert run_cli(monkeypatch, *argv) == 1
    out = capsys.readouterr().out
    assert "1 file(s) could not be generated: labs.md" in out
    assert "Wrote 1 file(s)" in out


def test_files_already_on_disk_are_kept_not_failed(monkeypatch, capsys):
    """`generate` without --force on a partly built course exited 1 and called
    the lessons it left alone "could not be generated"."""
    from learning_engine.generator import GenerationResults
    res = GenerationResults({"lesson_01_x.md": False, "lesson_02_y.md": True})
    res.skipped.add("lesson_01_x.md")
    monkeypatch.setattr(cli, "get_provider", lambda **k: object())
    monkeypatch.setattr(cli, "generate_subtopic_content", lambda *a, **k: res)
    assert run_cli(monkeypatch, "generate", "computing/infrastructure/kubernetes") == 0
    out = capsys.readouterr().out
    assert "Wrote 1 file(s)" in out
    assert "Kept 1 existing file(s)" in out and "lesson_01_x.md" in out
    assert "could not be generated" not in out


def test_lint_exits_non_zero_when_it_finds_errors(monkeypatch, capsys):
    """`synapse lint` printed "FAILED" but exited 0, so no script or CI step
    could use it as a gate."""
    monkeypatch.setattr(cli, "lint_curriculum", lambda domain_filter="": {
        "scanned_files": 1, "error_count": 1, "warning_count": 0, "passed": False,
        "issues": [{"file": "topics/x/y/z/lesson_01_a.md", "severity": "error", "message": "bad"}]})
    assert run_cli(monkeypatch, "lint") == 1
    monkeypatch.setattr(cli, "lint_curriculum", lambda domain_filter="": {
        "scanned_files": 1, "error_count": 0, "warning_count": 2, "passed": True, "issues": []})
    assert run_cli(monkeypatch, "lint") == 0


def test_chat_survives_a_failed_model_call(monkeypatch, capsys):
    """One timeout or empty reply ended the whole `synapse chat` session (and
    its history). The turn now reports the error and the session goes on."""
    calls = iter([RuntimeError("timed out"), "A Service gives pods a stable address."])

    class Flaky:
        model = "fake"

        def generate(self, prompt, system_instruction=""):
            r = next(calls)
            if isinstance(r, Exception):
                raise r
            return r

    answers = iter(["What is a Service?", "What is a Service?", "exit"])
    monkeypatch.setattr(cli, "get_provider", lambda **k: Flaky())
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    assert run_cli(monkeypatch, "chat", "computing/infrastructure/kubernetes") == 0
    out = capsys.readouterr().out
    assert "timed out" in out
    assert "Tutor > A Service gives pods a stable address." in out
