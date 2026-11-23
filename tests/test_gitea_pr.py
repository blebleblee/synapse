"""scripts/gitea_pr.py decisions. No network and no real git: both are stubbed."""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "gitea_pr", Path(__file__).resolve().parents[1] / "scripts" / "gitea_pr.py")
gitea_pr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gitea_pr)
cs = gitea_pr.ci_status


class FakeClient:
    def __init__(self, *a, conclusion="success"):
        self.conclusion, self.sent, self.auth, self.secrets, self.base = conclusion, [], None, [], "x"

    def get(self, path, raw=False):
        return [{"number": 7, "head": {"ref": "fix-x"}}] if path.startswith("/pulls") else []

    def runs(self, limit=10):
        return [{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": self.conclusion}]

    def jobs(self, run_id):
        return []


@pytest.fixture
def env(monkeypatch):
    calls = {"run": []}
    state = {"branch": "fix-x", "dirty": "", "client": FakeClient(), "remote_sha": "abc123"}
    answers = {("rev-parse", "--abbrev-ref", "HEAD"): lambda: state["branch"],
               ("rev-parse", "HEAD"): lambda: "abc123",
               ("remote", "get-url", "gitea"): lambda: "https://u:p@git.example.test/o/r.git",
               ("ls-remote", "gitea", "refs/heads/fix-x"): lambda: state["remote_sha"] + "\trefs/heads/fix-x"}
    monkeypatch.setattr(cs, "git", lambda *a: state["dirty"] if a[0] == "status" else answers[a]())
    monkeypatch.setattr(cs, "Client", lambda *a: state["client"])
    monkeypatch.setattr(gitea_pr.subprocess, "run", lambda cmd, check=False: calls["run"].append(cmd))
    monkeypatch.setattr(gitea_pr, "send", lambda c, m, p, payload: c.sent.append((m, p, payload)) or {"number": 7})
    return state, calls


def test_refuses_to_run_on_main(env):
    state, calls = env
    state["branch"] = "main"
    assert gitea_pr.main(["t"]) == 2 and calls["run"] == []


def test_refuses_uncommitted_changes(env):
    state, calls = env
    state["dirty"] = " M app.py"
    assert gitea_pr.main(["t"]) == 2 and calls["run"] == []


def test_red_ci_is_never_merged(env):
    state, _ = env
    state["client"] = FakeClient(conclusion="failure")
    assert gitea_pr.main(["t"]) == 1
    assert not any(p.endswith("/merge") for _, p, _ in state["client"].sent)


def test_green_ci_merges_the_tested_commit_and_reuses_the_open_pr(env):
    state, calls = env
    assert gitea_pr.main(["t"]) == 0
    sent = state["client"].sent
    assert [p for _, p, _ in sent] == ["/pulls/7/merge"]  # no second PR created
    assert sent[0][2]["head_commit_id"] == "abc123"
    assert not any("--force" in c or "-f" in c for c in calls["run"])


def test_unpushed_branch_is_refused(env):
    state, calls = env
    state["remote_sha"] = "0ld5ha"
    assert gitea_pr.main(["t"]) == 2 and state["client"].sent == []
