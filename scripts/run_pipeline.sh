#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=================================================="
echo " 🚀 SYNAPSE AUTONOMOUS PIPELINE: GLOBAL WORKSPACE GENERATION"
echo "=================================================="

# Phase 1: Arts (Completed)
echo ""
echo "[*] [Phase 1/12] Generating Arts domain..."
python3 scripts/generate_all.py --domain arts --model claude-sonnet-5

# Phase 2: Computing (Active)
echo ""
echo "[*] [Phase 2/12] Generating Computing & Systems domain..."
python3 scripts/generate_all.py --domain computing --model claude-sonnet-5

# Phase 3: Crafts (60 topics)
echo ""
echo "[*] [Phase 3/12] Generating Crafts & Lego domain..."
python3 scripts/generate_all.py --domain crafts --model claude-sonnet-5

# Phase 4: Business (41 topics)
echo ""
echo "[*] [Phase 4/12] Generating Business & Strategy domain..."
python3 scripts/generate_all.py --domain business --model claude-sonnet-5

# Phase 5: Engineering (39 topics)
echo ""
echo "[*] [Phase 5/12] Generating Engineering domain..."
python3 scripts/generate_all.py --domain engineering --model claude-sonnet-5

# Phase 6: Humanities (39 topics)
echo ""
echo "[*] [Phase 6/12] Generating Humanities domain..."
python3 scripts/generate_all.py --domain humanities --model claude-sonnet-5

# Phase 7: Formal Sciences (33 topics)
echo ""
echo "[*] [Phase 7/12] Generating Formal Sciences domain..."
python3 scripts/generate_all.py --domain formal_sciences --model claude-sonnet-5

# Phase 8: Economics (32 topics)
echo ""
echo "[*] [Phase 8/12] Generating Economics domain..."
python3 scripts/generate_all.py --domain economics --model claude-sonnet-5

# Phase 9: Natural Sciences (30 topics)
echo ""
echo "[*] [Phase 9/12] Generating Natural Sciences domain..."
python3 scripts/generate_all.py --domain natural_sciences --model claude-sonnet-5

# Phase 10: Health Sciences (20 topics)
echo ""
echo "[*] [Phase 10/12] Generating Health Sciences domain..."
python3 scripts/generate_all.py --domain health_sciences --model claude-sonnet-5

# Phase 11: Motorsports (10 topics)
echo ""
echo "[*] [Phase 11/12] Generating Motorsports domain..."
python3 scripts/generate_all.py --domain motorsports --model claude-sonnet-5

# Phase 12: Languages (6 topics)
echo ""
echo "[*] [Phase 12/12] Generating Languages domain..."
python3 scripts/generate_all.py --domain languages --model claude-sonnet-5

echo ""
echo "=================================================="
echo "[✔] TOTAL GLOBAL PIPELINE COMPLETE! (539/539 TOPICS AUTHORED)"
echo "=================================================="

# Trigger macOS notification chime
osascript -e 'display notification "The entire Synapse Global Curriculum (539 topics) has been successfully generated!" with title "Synapse Pipeline Complete" sound name "Glass"' 2>/dev/null || true
