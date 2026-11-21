# Start a maintenance batch

Run one bounded maintenance batch exactly as described in `AGENTS.md`
(section 3 for the workflow, sections 2 and 4 for the rules). Begin by reading
`docs/agent/status.md` and `docs/agent/backlog.md` and reconciling them with the
real git state. Never assume interrupted work passed; re-run verification.

When the batch ends, report: completed tasks with commit hashes, the
verification command and its exact result, blocked items and `NEEDS DECISION`
items, and the final `git status --short` and `git diff --stat`.
