"""Pure helpers of scripts/ci_status.py. No network: the Gitea API is never called."""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "ci_status", Path(__file__).resolve().parents[1] / "scripts" / "ci_status.py")
ci_status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ci_status)


def test_parse_remote_with_credentials():
    base, user, password = ci_status.parse_remote("https://bot:s3cr%40t@git.example.test/team/app.git")
    assert base == "https://git.example.test/api/v1/repos/team/app"
    assert (user, password) == ("bot", "s3cr@t")


def test_parse_remote_without_credentials_and_with_port():
    base, user, password = ci_status.parse_remote("http://git.example.test:3000/team/app")
    assert base == "http://git.example.test:3000/api/v1/repos/team/app"
    assert user is None and password is None


@pytest.mark.parametrize("url", ["git@git.example.test:team/app.git", "https://git.example.test/app.git"])
def test_parse_remote_rejects_unusable_urls(url):
    with pytest.raises(ci_status.CIError):
        ci_status.parse_remote(url)


def test_client_scrubs_password_and_basic_auth_from_logs():
    client = ci_status.Client("https://git.example.test/api/v1/repos/team/app", "bot", "hunter2pass")
    raw = ("2026-11-22T07:00:00.123Z cloning https://bot:hunter2pass@git.example.test/team/app\n"
           f"2026-11-22T07:00:01Z header {client.auth}\n"
           "2026-11-22T07:00:02Z ok\n")
    cleaned = ci_status.clean_log(raw, client.secrets)
    assert "hunter2pass" not in cleaned
    assert client.auth.split(" ", 1)[1] not in cleaned
    assert cleaned.splitlines()[2] == "ok"  # timestamps stripped


def test_redact_hides_secret_assignments():
    out = ci_status.redact("Authorization: Basic abc123xyz\nGITEA_TOKEN=abcdef\nfine", [])
    assert "abc123xyz" not in out and "abcdef" not in out
    assert out.endswith("fine")


def test_format_run_marks_failed_steps():
    text = ci_status.format_run(
        {"run_number": 12, "head_sha": "fa5e70cabc", "status": "completed", "conclusion": "failure",
         "display_title": "ci: something"},
        [{"name": "verify", "conclusion": "failure",
          "steps": [{"name": "Build", "conclusion": "failure"}, {"name": "Test", "conclusion": "skipped"}]}],
    )
    assert "run #12 fa5e70c completed failure" in text
    assert "[FAILED] Build" in text and "[skip] Test" in text
