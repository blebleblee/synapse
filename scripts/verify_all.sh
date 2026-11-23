#!/usr/bin/env bash
#
# Unified verification script for Synapse Workbench.
# Runs all 5 required verification phases in sequence:
# 1. Frontend unit tests (node --test)
# 2. Frontend linter (oxlint)
# 3. Frontend production build (tsc & vite build)
# 4. Backend test suite (pytest tests/)
# 5. Chromium E2E browser tests (pytest e2e/test_learner_journey.py)
#
# Fails immediately with nonzero exit status if any check fails.
#

set -eo pipefail

# Ensure execution from project root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

if [ ! -x "${VENV_PYTHON}" ]; then
    echo "[✘] Error: Virtual environment python not found at ${VENV_PYTHON}" >&2
    exit 1
fi

echo "=================================================="
echo " 🔍 RUNNING COMPLETE SYNAPSE VERIFICATION SUITE   "
echo "=================================================="

# Phase 1: Frontend Unit Tests
echo ""
echo "[*] [1/5] Running frontend unit tests..."
(cd app/frontend && npm run test)

# Phase 2: Frontend Linter
echo ""
echo "[*] [2/5] Running frontend linter..."
(cd app/frontend && npm run lint)

# Phase 3: Frontend Production Build
echo ""
echo "[*] [3/5] Building frontend production bundle..."
# On CPUs without x86-64-v3 (the CI runner) the bundler runs as WebAssembly,
# which now and then panics ("Parking not supported on this platform", a
# Rolldown bug, CI run #83). Retry once for that panic only; any other build
# failure still fails here.
build_log=$(mktemp)
if ! (cd app/frontend && npm run build) 2>&1 | tee "$build_log"; then
  if grep -q "Rolldown panicked" "$build_log"; then
    echo "[!] Rolldown (WebAssembly) panicked; retrying the build once."
    (cd app/frontend && npm run build)
  else
    rm -f "$build_log"
    exit 1
  fi
fi
rm -f "$build_log"

# Phase 4: Backend Test Suite
echo ""
echo "[*] [4/5] Running backend test suite..."
"${VENV_PYTHON}" -m pytest tests/

# Phase 5: Chromium E2E Browser Journey Tests
echo ""
echo "[*] [5/6] Running Chromium E2E browser tests..."
"${VENV_PYTHON}" -m pytest e2e/test_learner_journey.py

# Phase 6: Repository Security & Privacy Audit
echo ""
echo "[*] [6/6] Auditing tracked repository files for private content and secrets..."
"${VENV_PYTHON}" scripts/check_staged_content.py --audit-tracked

echo ""
echo "=================================================="
echo " [✔] ALL 6 VERIFICATION PHASES PASSED             "
echo "=================================================="
