#!/usr/bin/env bash
# =============================================================================
# SYNAPSE MASTER POST-GENERATION PIPELINE
# Executes Quality Remediation, Linter & Render Validation, Test Suite,
# Desktop Binary Rebuild, and SynPack Addon Export for all 12 domains.
# =============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "================================================================="
echo " 🚀 SYNAPSE POST-GENERATION QUALITY & RELEASE PIPELINE"
echo "================================================================="

# -----------------------------------------------------------------------------
# STEP 1: Truncation Remediation & Conclusion
# -----------------------------------------------------------------------------
echo ""
echo "[*] [Step 1/5] Running automated parallel truncation remediation..."
python3 scripts/remediate_truncations.py

# -----------------------------------------------------------------------------
# STEP 2: Comprehensive Linter & Headless Render Validation
# -----------------------------------------------------------------------------
echo ""
echo "[*] [Step 2/5] Running curriculum content quality linter..."
python3 -m learning_engine.cli lint

echo ""
echo "[*] [Step 2b/5] Running headless KaTeX and Mermaid render validation..."
python3 -m learning_engine.cli lint --render

# -----------------------------------------------------------------------------
# STEP 3: Automated Test Suite
# -----------------------------------------------------------------------------
echo ""
echo "[*] [Step 3/5] Executing automated pytest suite..."
.venv/bin/python -m pytest

# -----------------------------------------------------------------------------
# STEP 4: Rebuilding Production Application Binaries
# -----------------------------------------------------------------------------
echo ""
echo "[*] [Step 4/5] Running macOS Desktop Build Pipeline (Frontend + PyInstaller + Electron)..."
bash scripts/build_mac_desktop.sh

echo ""
echo "[*] [Step 4b/5] Building Python distribution wheel and source tarball..."
.venv/bin/python -m build --outdir dist/python

# -----------------------------------------------------------------------------
# STEP 5: Exporting Modular SynPack Addons for All 12 Domains
# -----------------------------------------------------------------------------
echo ""
echo "[*] [Step 5/5] Exporting modular .synpack curriculum addons..."
mkdir -p exports/packages

DOMAINS=(
    "computing"
    "arts"
    "crafts"
    "business"
    "engineering"
    "motorsports"
    "formal_sciences"
    "humanities"
    "languages"
    "economics"
    "natural_sciences"
    "health_sciences"
)

for dom in "${DOMAINS[@]}"; do
    echo "  • Exporting $dom.synpack..."
    python3 -m learning_engine.cli pack export "$dom"
done
echo "  • Exporting synapse_complete_curriculum.synpack (all core domains)..."
python3 -m learning_engine.cli pack export all
echo "  • Checking packs for private or uncommitted content..."
python3 scripts/check_release_packs.py

echo ""
echo "================================================================="
echo " [✔] SYNAPSE GLOBAL RELEASE PIPELINE COMPLETED SUCCESSFULLY!"
echo "================================================================="
echo " Release Artifacts Ready:"
echo "   • Desktop DMG: dist/desktop/Synapse Workbench-1.0.0-arm64.dmg"
echo "   • Desktop Zip: dist/desktop/Synapse Workbench-1.0.0-arm64-mac.zip"
echo "   • Python Wheel: dist/python/synapse-1.0.0-py3-none-any.whl"
echo "   • SynPacks:     exports/*.synpack (All 12 domains)"
echo "================================================================="

osascript -e 'display notification "Synapse post-generation release pipeline completed successfully!" with title "Synapse Release Ready" sound name "Glass"' 2>/dev/null || true
