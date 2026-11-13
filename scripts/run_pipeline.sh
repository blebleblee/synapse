#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=================================================="
echo " 🚀 SYNAPSE DUAL PIPELINE: ARTS -> FRONTIER COMPUTING"
echo "=================================================="

# Phase 1: Arts Masterclass Enhancement (33 topics)
echo ""
echo "[*] [Phase 1/2] Enhancing Arts domain (33 topics) with Claude Opus 5.5..."
python3 scripts/generate_all.py --domain arts --enhance

echo ""
echo "[✔] Phase 1 Complete: All Arts topics enhanced and published to Gitea!"

# Phase 2: Frontier Computing Generation (94 unwritten topics)
echo ""
echo "[*] [Phase 2/2] Generating Frontier & Software Computing topics (94 topics)..."
python3 scripts/generate_all.py --domain computing

echo ""
echo "=================================================="
echo "[✔] ALL PIPELINE PHASES COMPLETE!"
echo "=================================================="

# Trigger macOS notification chime
osascript -e 'display notification "Arts enhancement and Frontier Computing generation complete!" with title "Synapse Pipeline" sound name "Glass"' 2>/dev/null || true
