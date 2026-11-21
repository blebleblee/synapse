#!/usr/bin/env bash
#
# scripts/continue.sh
# Resumes the latest Gemini session with the autonomous maintenance prompt
# in interactive mode, or launches a fresh interactive session if no prior
# session exists.
#

set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# 1. Verify Gemini CLI binary is available
if ! command -v gemini >/dev/null 2>&1; then
    echo "[✘] Error: 'gemini' CLI is not found in PATH." >&2
    echo "    Please ensure Gemini CLI is installed and available in your environment." >&2
    exit 1
fi

PROMPT_FILE="${REPO_ROOT}/.gemini/prompts/continue-maintenance.md"
if [ ! -f "${PROMPT_FILE}" ]; then
    echo "[✘] Error: Prompt file not found at ${PROMPT_FILE}" >&2
    exit 1
fi

PROMPT_CONTENT="$(cat "${PROMPT_FILE}")"

# 2. Check whether previous sessions exist for this workspace
HAS_SESSIONS=false
SESSIONS_OUTPUT="$(gemini --list-sessions 2>&1 || true)"
if echo "${SESSIONS_OUTPUT}" | grep -q "Available sessions for this project ([1-9]"; then
    HAS_SESSIONS=true
fi

# 3. Launch Gemini CLI in interactive mode with prompt
if [ "${HAS_SESSIONS}" = true ]; then
    echo "[*] Resuming latest session for Synapse with maintenance prompt..."
    exec gemini --resume latest --prompt-interactive "${PROMPT_CONTENT}"
else
    echo "[*] No previous session found. Starting fresh interactive session with maintenance prompt..."
    exec gemini --prompt-interactive "${PROMPT_CONTENT}"
fi
