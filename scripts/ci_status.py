#!/usr/bin/env python3
"""Show Gitea Actions CI results for this repository.

    scripts/ci_status.py                 latest run: each job and step
    scripts/ci_status.py --wait          wait for the run of the current HEAD
    scripts/ci_status.py --log verify    log of the job named "verify"
    scripts/ci_status.py --run 12 ...    a specific run instead of the latest

Credentials come from the `gitea` remote URL. They are sent only in the
request's Authorization header and are scrubbed from everything printed.

Exit codes: 0 success, 1 the run failed, 2 usage or API error, 3 timed out.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

REMOTE = "gitea"
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z ")
SECRET_LINE_RE = re.compile(r"(authorization|password|token|extraheader)\S*\s*[:=]\s*(?:(?:basic|bearer|token)\s+)?\S+", re.IGNORECASE)


class CIError(Exception):
    pass


def parse_remote(url: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Return (api_base, user, password) for an https remote URL."""
    parts = urllib.parse.urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise CIError(f"remote '{REMOTE}' is not an http(s) URL")
    path = parts.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if path.count("/") != 1:
        raise CIError(f"cannot read owner/repo from the '{REMOTE}' remote")
    host = parts.hostname + (f":{parts.port}" if parts.port else "")
    user = urllib.parse.unquote(parts.username) if parts.username else None
    password = urllib.parse.unquote(parts.password) if parts.password else None
    return f"{parts.scheme}://{host}/api/v1/repos/{path}", user, password


def redact(text: str, secrets: List[Optional[str]]) -> str:
    for s in secrets:
        if s and len(s) >= 4:
            text = text.replace(s, "***")
            text = text.replace(urllib.parse.quote(s, safe=""), "***")
    return SECRET_LINE_RE.sub(lambda m: f"{m.group(1)}: ***", text)


def clean_log(raw: str, secrets: List[Optional[str]]) -> str:
    lines = (TIMESTAMP_RE.sub("", line) for line in raw.splitlines())
    return redact("\n".join(lines), secrets)


def format_run(run: Dict, jobs: List[Dict]) -> str:
    out = [f"run #{run.get('run_number', run.get('id'))} {str(run.get('head_sha', ''))[:7]} "
           f"{run.get('status')} {run.get('conclusion') or ''}".rstrip()
           + f"  {str(run.get('display_title', ''))[:60]}"]
    for job in jobs:
        out.append(f"  {job.get('name')}: {job.get('conclusion') or job.get('status')}")
        for step in job.get("steps") or []:
            state = step.get("conclusion") or step.get("status")
            mark = {"success": "ok", "failure": "FAILED", "skipped": "skip"}.get(state, state)
            out.append(f"      [{mark}] {step.get('name')}")
    return "\n".join(out)


class Client:
    def __init__(self, base: str, user: Optional[str], password: Optional[str]):
        self.base = base
        self.secrets = [password, f"{user}:{password}" if user and password else None]
        self.auth = None
        if user and password:
            self.auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
            self.secrets.append(self.auth.split(" ", 1)[1])

    def get(self, path: str, raw: bool = False):
        req = urllib.request.Request(self.base + path)
        if self.auth:
            req.add_header("Authorization", self.auth)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            raise CIError(f"Gitea API {path}: HTTP {e.code}") from None
        except urllib.error.URLError as e:
            raise CIError(f"Gitea API unreachable: {redact(str(e.reason), self.secrets)}") from None
        return body if raw else json.loads(body)

    def runs(self, limit: int = 10) -> List[Dict]:
        return self.get(f"/actions/runs?limit={limit}").get("workflow_runs") or []

    def run(self, run_id: int) -> Dict:
        return self.get(f"/actions/runs/{run_id}")

    def jobs(self, run_id: int) -> List[Dict]:
        return self.get(f"/actions/runs/{run_id}/jobs").get("jobs") or []

    def log(self, job_id: int) -> str:
        return clean_log(self.get(f"/actions/jobs/{job_id}/logs", raw=True), self.secrets)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def find_run(client: Client, run_id: Optional[int], sha: Optional[str]) -> Optional[Dict]:
    if run_id:
        return client.run(run_id)
    for run in client.runs():
        if not sha or str(run.get("head_sha", "")).startswith(sha):
            return run
    return None


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Gitea Actions CI status for this repository.")
    ap.add_argument("--run", type=int, help="run id (default: the latest run)")
    ap.add_argument("--wait", action="store_true", help="wait until the run of the current HEAD finishes")
    ap.add_argument("--timeout", type=int, default=45 * 60, help="seconds to wait (default 2700)")
    ap.add_argument("--log", metavar="JOB", help="print the log of the job with this name")
    args = ap.parse_args(argv)

    try:
        client = Client(*parse_remote(git("remote", "get-url", REMOTE)))
        sha = git("rev-parse", "HEAD") if args.wait and not args.run else None
        deadline = time.time() + args.timeout
        while True:
            run = find_run(client, args.run, sha)
            if run and run.get("status") == "completed" or not args.wait:
                break
            if time.time() > deadline:
                print(f"timed out waiting for the CI run of {sha[:7] if sha else args.run}", file=sys.stderr)
                return 3
            time.sleep(15)
        if not run:
            raise CIError("no CI run found")
        jobs = client.jobs(run["id"])
        if args.log:
            job = next((j for j in jobs if j.get("name") == args.log), None)
            if not job:
                raise CIError(f"no job named '{args.log}' (jobs: {', '.join(j.get('name', '?') for j in jobs)})")
            print(client.log(job["id"]))
        else:
            print(format_run(run, jobs))
        if run.get("status") == "completed" and run.get("conclusion") not in ("success", "skipped"):
            return 1
        return 0
    except (CIError, subprocess.CalledProcessError) as e:
        print(f"ci_status: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
