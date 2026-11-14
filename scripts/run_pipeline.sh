#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=================================================="
echo " 🚀 SYNAPSE TRIPLE PIPELINE: ARTS ENHANCE -> ARTS EXPAND -> FRONTIER COMPUTING"
echo "=================================================="

# Phase 1A: Arts Masterclass Enhancement (33 existing music topics)
echo ""
echo "[*] [Phase 1A/3] Enhancing Arts domain (33 topics) with Claude Sonnet 5..."
python3 scripts/generate_all.py --domain arts --enhance --model claude-sonnet-5

echo ""
echo "[✔] Phase 1A Complete: All 33 music topics enhanced and published to Gitea!"

# Phase 1B: Generate Unwritten Arts Topics (34 missing visual arts, 3D graphics, and modular audio topics)
echo ""
echo "[*] [Phase 1B/3] Generating unwritten Arts topics (34 courses: Blender, DaVinci, Modular Synthesis, ZBrush)..."
python3 scripts/generate_all.py --domain arts --model claude-sonnet-5

echo ""
echo "[✔] Phase 1B Complete: All 34 missing Arts topics generated and published!"

# Phase 2: Frontier Computing Generation (117 unwritten topics)
echo ""
echo "[*] [Phase 2/3] Generating Frontier & Software Computing topics (117 courses: Quantum, Swarms, Web3, Cilium, ArgoCD)..."
python3 scripts/generate_all.py --domain computing --model claude-sonnet-5

echo ""
echo "=================================================="
echo "[✔] ALL PIPELINE PHASES COMPLETE!"
echo "=================================================="

# Trigger macOS notification chime
osascript -e 'display notification "All Arts and Frontier Computing topics generated successfully!" with title "Synapse Pipeline" sound name "Glass"' 2>/dev/null || true
