#!/usr/bin/env python3
"""Land the current branch on `main` through a Gitea pull request.

    (push the branch to gitea first)
    scripts/gitea_pr.py "fix(x): title"      open (or reuse) the PR, wait for
                                              its CI, merge when green
    scripts/gitea_pr.py --no-merge "title"   stop after CI reports

`main` is protected: direct pushes are refused and a PR merges only when the
CI checks on its head commit passed. The script does not push (pushing stays
the maintainer's explicit step; see tests/test_no_auto_push.py): it refuses
to run until the branch on `gitea` is at the local HEAD. It never merges a red
or unfinished run. Credentials come from the `gitea` remote URL
and are scrubbed from everything printed (see ci_status.py).
Exit codes: 0 merged (or green with --no-merge), 1 CI failed, 2 usage or API
error, 3 timed out.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

_spec = importlib.util.spec_from_file_location("ci_status", Path(__file__).with_name("ci_status.py"))
ci_status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ci_status)

BASE_BRANCH = "main"


def send(client, method: str, path: str, payload: Dict) -> Dict:
    req = urllib.request.Request(client.base + path, data=json.dumps(payload).encode(), method=method,
                                 headers={"Content-Type": "application/json"})
    if client.auth:
        req.add_header("Authorization", client.auth)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = ci_status.redact(e.read().decode("utf-8", "replace")[:300], client.secrets)
        raise ci_status.CIError(f"Gitea API {method} {path}: HTTP {e.code} {detail}") from None
    return json.loads(body) if body.strip() else {}


def find_open_pr(client, branch: str) -> Optional[Dict]:
    for pr in client.get("/pulls?state=open&limit=50"):
        if (pr.get("head") or {}).get("ref") == branch:
            return pr
    return None


def wait_for_run(client, sha: str, timeout: int) -> Optional[Dict]:
    """The completed CI run of `sha` (any event), or None on timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        run = ci_status.find_run(client, None, sha)
        if run and run.get("status") == "completed":
            return run
        time.sleep(15)
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Land the current branch on main through a Gitea PR.")
    ap.add_argument("title", help="pull request title (usually the main commit's subject)")
    ap.add_argument("--no-merge", action="store_true", help="report CI but do not merge")
    ap.add_argument("--timeout", type=int, default=45 * 60, help="seconds to wait for CI (default 2700)")
    args = ap.parse_args(argv)
    git = ci_status.git
    try:
        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        if branch in (BASE_BRANCH, "HEAD"):
            raise ci_status.CIError(f"work on a branch, not {branch}: git switch -c <name>")
        if git("status", "--porcelain", "--untracked-files=no"):
            raise ci_status.CIError("uncommitted changes to tracked files; commit them first")
        client = ci_status.Client(*ci_status.parse_remote(git("remote", "get-url", ci_status.REMOTE)))
        sha = git("rev-parse", "HEAD")
        remote = git("ls-remote", ci_status.REMOTE, f"refs/heads/{branch}").split("\t")[0]
        if remote != sha:
            raise ci_status.CIError(f"gitea's {branch} is not at HEAD {sha[:7]}: push the branch to gitea first")

        pr = find_open_pr(client, branch) or send(client, "POST", "/pulls",
                                                  {"head": branch, "base": BASE_BRANCH, "title": args.title})
        print(f"PR #{pr['number']}: {pr.get('html_url', '')}")

        run = wait_for_run(client, sha, args.timeout)
        if not run:
            print(f"timed out waiting for the CI run of {sha[:7]}", file=sys.stderr)
            return 3
        print(ci_status.format_run(run, client.jobs(run["id"])))
        if run.get("conclusion") != "success":
            print("CI failed: not merging. See scripts/ci_status.py --log <job>.", file=sys.stderr)
            return 1
        if args.no_merge:
            return 0

        send(client, "POST", f"/pulls/{pr['number']}/merge",
             {"Do": "merge", "head_commit_id": sha})
        print(f"merged PR #{pr['number']} into {BASE_BRANCH}")
        subprocess.run(["git", "fetch", "-q", ci_status.REMOTE, BASE_BRANCH], check=True)
        subprocess.run(["git", "switch", "-q", BASE_BRANCH], check=True)
        subprocess.run(["git", "merge", "-q", "--ff-only", f"{ci_status.REMOTE}/{BASE_BRANCH}"], check=True)
        subprocess.run(["git", "branch", "-q", "-d", branch], check=False)
        return 0
    except ci_status.CIError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"error: {' '.join(e.cmd[:3])} failed (exit {e.returncode})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
