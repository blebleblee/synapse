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
(cd app/frontend && npm run build)

# Phase 4: Backend Test Suite
echo ""
echo "[*] [4/5] Running backend test suite..."
"${VENV_PYTHON}" -m pytest tests/

# Phase 5: Chromium E2E Browser Journey Tests
echo ""
echo "[*] [5/5] Running Chromium E2E browser tests..."
"${VENV_PYTHON}" -m pytest e2e/test_learner_journey.py

echo ""
echo "=================================================="
echo " [✔] ALL 5 VERIFICATION PHASES PASSED             "
echo "=================================================="
