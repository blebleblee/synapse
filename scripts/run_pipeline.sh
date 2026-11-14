#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=================================================="
echo " 🚀 SYNAPSE IDEMPOTENT PIPELINE: ARTS EXPAND -> FRONTIER COMPUTING"
echo "=================================================="

# Phase 1: Generate Unwritten Arts Topics (strictly missing courses only)
echo ""
echo "[*] [Phase 1/2] Generating unwritten Arts topics (Blender, DaVinci, Drawing, Sound Design)..."
python3 scripts/generate_all.py --domain arts --model claude-sonnet-5

echo ""
echo "[✔] Phase 1 Complete: All Arts topics authored and published!"

# Phase 2: Frontier Computing Generation (strictly missing courses only)
echo ""
echo "[*] [Phase 2/2] Generating Frontier & Software Computing topics (Cilium, ArgoCD, Swarms, Web3)..."
python3 scripts/generate_all.py --domain computing --model claude-sonnet-5

echo ""
echo "=================================================="
echo "[✔] ALL PIPELINE PHASES COMPLETE!"
echo "=================================================="

# Trigger macOS notification chime
osascript -e 'display notification "All Arts and Frontier Computing topics generated successfully!" with title "Synapse Pipeline" sound name "Glass"' 2>/dev/null || true
