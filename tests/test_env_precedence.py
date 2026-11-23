"""Variables exported in the shell win over ~/.config/synapse/env.

The file used to overwrite them, so `ANTHROPIC_API_KEY=... synapse ...` was
silently replaced by whatever key the file held. An exported but empty value
does not count: a blank SYNAPSE_PASSWORD in the shell must not cancel the
password set in the file."""
from learning_engine import models


def _write_user_env(tmp_path, monkeypatch, text):
    home = tmp_path / "home"
    (home / ".config" / "synapse").mkdir(parents=True)
    (home / ".config" / "synapse" / "env").write_text(text, encoding="utf-8")
    monkeypatch.setattr(models.Path, "home", classmethod(lambda cls: home))


def test_exported_variable_wins_over_user_env_file(tmp_path, monkeypatch):
    _write_user_env(tmp_path, monkeypatch, "SYNAPSE_TEST_KEY=from-file\nSYNAPSE_TEST_OTHER=file-only\n")
    monkeypatch.setenv("SYNAPSE_TEST_KEY", "from-shell")
    monkeypatch.delenv("SYNAPSE_TEST_OTHER", raising=False)
    models.load_env_file()
    assert models.os.environ["SYNAPSE_TEST_KEY"] == "from-shell"
    assert models.os.environ["SYNAPSE_TEST_OTHER"] == "file-only"
    monkeypatch.delenv("SYNAPSE_TEST_OTHER")


def test_empty_exported_value_does_not_cancel_file_value(tmp_path, monkeypatch):
    _write_user_env(tmp_path, monkeypatch, "SYNAPSE_TEST_PASSWORD=secret\n")
    monkeypatch.setenv("SYNAPSE_TEST_PASSWORD", "")
    models.load_env_file()
    assert models.os.environ["SYNAPSE_TEST_PASSWORD"] == "secret"
