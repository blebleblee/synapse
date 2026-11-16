#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=================================================="
echo " 🚀 SYNAPSE AUTONOMOUS PIPELINE: GLOBAL WORKSPACE GENERATION"
echo "=================================================="

# Completed Domains (Skips automatically in seconds)
echo ""
echo "[*] [Audited Phase] Arts domain (67/67 Complete)..."
python3 scripts/generate_all.py --domain arts --model claude-sonnet-5

echo ""
echo "[*] [Audited Phase] Computing & Systems domain (162/162 Complete)..."
python3 scripts/generate_all.py --domain computing --model claude-sonnet-5

echo ""
echo "[*] [Audited Phase] Crafts & Lego domain (60/60 Complete)..."
python3 scripts/generate_all.py --domain crafts --model claude-sonnet-5

echo ""
echo "[*] [Audited Phase] Business & Strategy domain (41/41 Complete)..."
python3 scripts/generate_all.py --domain business --model claude-sonnet-5

echo ""
echo "[*] [Audited Phase] Engineering domain (39/39 Complete)..."
python3 scripts/generate_all.py --domain engineering --model claude-sonnet-5

echo ""
echo "[*] [Audited Phase] Languages domain (6/6 Complete)..."
python3 scripts/generate_all.py --domain languages --model claude-sonnet-5

# -----------------------------------------------------------------------------
# ACTIVE PIPELINE SCHEDULE:
# 1. Motorsports (10 topics)
# 2. Humanities (22 topics remaining, resuming at medieval_history)
# 3. Formal Sciences (33 topics)
# 4. Economics (32 topics)
# 5. Natural Sciences (30 topics)
# 6. Health Sciences (20 topics)
# -----------------------------------------------------------------------------

echo ""
echo "[*] [Active Phase] Generating Motorsports domain (10 topics)..."
python3 scripts/generate_all.py --domain motorsports --model claude-sonnet-5

echo ""
echo "[*] [Active Phase] Resuming Humanities domain..."
python3 scripts/generate_all.py --domain humanities --model claude-sonnet-5

echo ""
echo "[*] [Active Phase] Generating Formal Sciences domain (33 topics)..."
python3 scripts/generate_all.py --domain formal_sciences --model claude-sonnet-5

echo ""
echo "[*] [Active Phase] Generating Economics domain (32 topics)..."
python3 scripts/generate_all.py --domain economics --model claude-sonnet-5

echo ""
echo "[*] [Active Phase] Generating Natural Sciences domain (30 topics)..."
python3 scripts/generate_all.py --domain natural_sciences --model claude-sonnet-5

echo ""
echo "[*] [Active Phase] Generating Health Sciences domain (20 topics)..."
python3 scripts/generate_all.py --domain health_sciences --model claude-sonnet-5

echo ""
echo "=================================================="
echo "[✔] TOTAL GLOBAL PIPELINE COMPLETE! (539/539 TOPICS AUTHORED)"
echo "=================================================="

# Trigger macOS notification chime
osascript -e 'display notification "The entire Synapse Global Curriculum (539 topics) has been successfully generated!" with title "Synapse Pipeline Complete" sound name "Glass"' 2>/dev/null || true
