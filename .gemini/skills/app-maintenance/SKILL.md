---
name: app-maintenance
description: Use when maintaining, auditing, stabilizing, or continuing development of an existing application through bounded autonomous repair batches.
---

# Application Maintenance & Stabilization

This skill provides procedural guidance for conducting disciplined, bounded autonomous maintenance, bug fixing, and stabilization batches. Permanent safety boundaries are governed by root `GEMINI.md`.

## Core Procedure

Execute autonomous maintenance using this iterative 9-step cycle:

1. **Reconcile Workspace State:**
   - Review `docs/status.md` and `docs/backlog.md` before editing.
   - Inspect actual Git state (`git status --short`, `git diff HEAD`, `git log -n 3`) and reconcile discrepancies.
   - For interrupted work: verify whether previous tests passed; never assume unverified steps succeeded.
2. **Select & Validate Prioritized Tasks:**
   - Choose candidate items from `docs/backlog.md` based on impact (data loss, crashes, unsafe side effects first).
   - Re-check code before editing; do not assume backlog diagnoses are automatically correct.
   - If an item requires ambiguous architectural choices, record `NEEDS DECISION` in `docs/status.md` and continue with other safe tasks.
3. **Define Task Scope & Acceptance Criteria:**
   - Narrow each task to a single verifiable defect or gap.
   - Define observable acceptance criteria before touching code.
4. **Reproduce Failure:**
   - Write a reproduction script or automated regression test demonstrating the defect before applying changes.
   - Test boundary cases, empty states, and legacy data structures where relevant.
5. **Apply Minimal Coherent Repair:**
   - Make surgical edits strictly addressing the defect.
   - Avoid unrelated refactoring or scope creep.
6. **Self-Review Diffs:**
   - Review `git diff` and untracked files thoroughly.
   - Distinguish explicit self-review from independent review (never claim external/independent review occurred).
7. **Execute Verification Commands:**
   - Run targeted test suites first.
   - Run the project's unified verification script:
     ```bash
     ./scripts/verify_all.sh
     ```
   - Maintain the hierarchy of verification:
     - **Unit tests:** Fast structural logic verification.
     - **API tests:** Request/response schemas, error status codes, and path traversal guards.
     - **Browser/E2E tests:** Interactive DOM state, rendering, and cross-tab/reload persistence.
     - **Mock vs. Real Providers:** Keep automated tests strictly deterministic using mocks. Honestly report real-provider execution as unverified when mocks are used.
8. **Create Local Checkpoint & Synchronize:**
   - Stage explicit modified files only (`git add <file>...`).
   - Create a focused local commit (`git commit -m "..."`).
   - Push to the development remote strictly according to the authoritative remote policy defined in root `GEMINI.md`.
9. **Update Handoff & Monitor Batch Limits:**
   - Update `docs/status.md` and `docs/backlog.md` with the new commit hash and remaining tasks.
   - Track elapsed time against the two-hour batch budget.
   - Allow a maximum of two corrective cycles per task; if still blocked, document findings and proceed or conclude the batch.
