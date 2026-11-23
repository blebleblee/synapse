"""No code in the repository pushes to a git remote by itself.

scripts/scope_domain_curriculum.py used to `git add topics/`, commit and
`git push origin main` after writing outlines, in whatever repository held
the topics folder (synapse's own main included). Pushing is the maintainer's
decision (AGENTS.md section 4)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUSH = re.compile(r"""["']git["']\s*,\s*["']push["']|\bgit push\b""")


def test_no_python_code_pushes_to_a_remote():
    offenders = []
    for folder in ("scripts", "learning_engine", "app/backend", "bin"):
        for path in (ROOT / folder).rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
            if PUSH.search(code):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
