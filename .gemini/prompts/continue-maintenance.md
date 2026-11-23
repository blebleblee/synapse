# Start a maintenance batch

Run one bounded maintenance batch exactly as described in `AGENTS.md`
(section 3 for the workflow, sections 2 and 4 for the rules). Begin by reading
`.agent/status.md` and `.agent/backlog.md` and reconciling them with the
real git state, then check CI with `scripts/ci_status.py`: a red latest run
is the first thing to fix. Never assume interrupted work passed; re-run
verification. Commit only after `./scripts/verify_all.sh` passes all 6
phases; after each push run `scripts/ci_status.py --wait` and do not commit,
push, bump the version or release again until that run is green.

When the batch ends, report: completed tasks with commit hashes, the
verification command and its exact result, blocked items and `NEEDS DECISION`
items, and the final `git status --short` and `git diff --stat`.
