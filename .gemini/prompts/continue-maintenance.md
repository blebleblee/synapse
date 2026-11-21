# Autonomous Maintenance Startup Instruction

Continue autonomous maintenance and stabilization of the Synapse repository in accordance with the standing agreement in `GEMINI.md`:

1. **Inspect & Reconcile State First:**
   - Read `docs/status.md` and `docs/backlog.md` before making any modifications.
   - Inspect actual Git state (`git status --short`, `git diff HEAD`, `git log -n 3`) and reconcile it with the recorded handoff in `docs/status.md`.
   - If in-flight, uncommitted, or interrupted work exists from a previous session, evaluate it carefully:
     - Never assume interrupted commands, builds, or test suites passed; re-run verification if uncertain.
     - Safely resume or complete the interrupted task if viable.
     - If the interrupted work is corrupt, preserve clean files and document the state.

2. **Execute Bounded Maintenance Batch:**
   - Work autonomously for a bounded batch of up to **two hours**, monitoring elapsed time between tasks.
   - Select the next prioritized, safe, evidence-backed task from `docs/backlog.md`.
   - Re-check each finding against the codebase before implementing.
   - For each task:
     - Formulate a brief plan in session.
     - Reproduce the defect with an automated regression test where practical.
     - Implement the minimal, surgical change.
     - Self-review the actual diff, including untracked files.
     - Verify with targeted checks and `./scripts/verify_all.sh`.
     - Create a focused local commit (`git commit`) only after verification passes.
     - Push to the development remote strictly according to the authoritative remote policy defined in `GEMINI.md`.
     - Update `docs/status.md` and `docs/backlog.md` after completing or blocking each task before proceeding to the next.

3. **Decision & Escalation Protocol:**
   - Make routine engineering and test decisions autonomously.
   - Stop only for genuine blockers or architectural decisions requiring human clarification; record `NEEDS DECISION` in `docs/status.md` and `docs/backlog.md` and continue with other safe tasks.
   - Follow all strict safety boundaries: push to remotes only as authorized in `GEMINI.md`, no real AI/network calls in tests, strict database and browser test isolation, no dependency changes, no weakening of test assertions.

4. **Batch Handoff Report:**
   - At the conclusion of the batch or if the safe backlog is exhausted, provide a concise summary:
     - Completed tasks and commit hashes.
     - Verification command and exact results.
     - Blocked tasks or deferred decisions.
     - Final `git status --short` and `git diff --stat`.
