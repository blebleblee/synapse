#!/usr/bin/env bash
set -e

# Change to project root
cd "$(dirname "$0")/.."

echo "=================================================="
echo " 🍏 SYNAPSE MACOS DESKTOP BUNDLE ASSEMBLER       "
echo "=================================================="

# 1. Compile fresh React Frontend SPA
echo ""
echo "[*] [Step 1/3] Compiling production React frontend SPA..."
cd app/frontend
npm run build
cd ../..

# 2. Compile standalone PyInstaller backend binary (dist/bin/synapse)
echo ""
echo "[*] [Step 2/3] Compiling standalone backend binary via PyInstaller..."
rm -rf build/ dist/bin/
.venv/bin/pyinstaller synapse.spec --distpath dist/bin --clean -y

echo "[*] Verifying compiled backend binary..."
if [ ! -f "dist/bin/synapse" ]; then
    echo "[✘] Error: dist/bin/synapse was not generated."
    exit 1
fi
chmod +x dist/bin/synapse
dist/bin/synapse --help | grep -q "pack"
if [ $? -eq 0 ]; then
    echo "[✔] Verified: Standalone binary is healthy and up-to-date."
else
    echo "[✘] Error: Standalone binary appears to be stale or corrupt."
    exit 1
fi

# 3. Package macOS Electron App (DMG & ZIP)
echo ""
echo "[*] [Step 3/3] Packaging macOS Apple Silicon desktop app (DMG & Zip)..."
cd app/desktop
npm run build:mac
cd ../..

echo ""
echo "[✔] macOS Build Complete!"
echo "    Artifacts located in: dist/desktop/"
ls -lh dist/desktop/*.dmg dist/desktop/*-mac.zip 2>/dev/null || true
