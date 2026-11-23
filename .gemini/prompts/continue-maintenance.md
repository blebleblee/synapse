# Start a maintenance batch

Run one bounded maintenance batch exactly as described in `AGENTS.md`
(section 3 for the workflow, sections 2 and 4 for the rules). Begin by reading
`.agent/status.md` and `.agent/backlog.md` and reconciling them with the
real git state, then check CI with `scripts/ci_status.py`: a red latest run
is the first thing to fix. Never assume interrupted work passed; re-run
verification. Commit only after `./scripts/verify_all.sh` passes all 6
phases. Work on a branch, `git push gitea HEAD`, then land it with
`scripts/gitea_pr.py "<title>"`
(main is protected; the PR merges only on green CI). Do not bump the
version or release while CI is red.

When the batch ends, report: completed tasks with commit hashes, the
verification command and its exact result, blocked items and `NEEDS DECISION`
items, and the final `git status --short` and `git diff --stat`.
