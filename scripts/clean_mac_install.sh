#!/usr/bin/env bash

echo "=================================================="
echo " 🧹 SYNAPSE WORKBENCH (macOS) CLEANUP UTILITY"
echo "=================================================="
echo ""
echo "This utility will completely remove Synapse Workbench and all its data"
echo "from your Mac, providing a clean slate for a fresh installation."
echo ""
echo "WARNING: This will delete your local learning history (data/synapse.db)"
echo "and downloaded topics in your personal library."
echo ""
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 1
fi

echo "[*] Quitting Synapse Workbench processes..."
pkill -f "Synapse Workbench" || true
pkill -f "synapse serve" || true

echo "[*] Removing /Applications/Synapse Workbench.app..."
rm -rf "/Applications/Synapse Workbench.app"

echo "[*] Removing ~/Library/Application Support/Synapse Workbench..."
rm -rf "$HOME/Library/Application Support/Synapse Workbench"

echo "[*] Removing ~/Library/Caches/com.synapse.workbench..."
rm -rf "$HOME/Library/Caches/com.synapse.workbench"
rm -rf "$HOME/Library/Caches/com.synapse.workbench.ShipIt"

echo "[*] Removing ~/Library/Preferences/com.synapse.workbench.plist..."
rm -f "$HOME/Library/Preferences/com.synapse.workbench.plist"

echo "[*] Removing ~/Library/Saved Application State/com.synapse.workbench.savedState..."
rm -rf "$HOME/Library/Saved Application State/com.synapse.workbench.savedState"

echo ""
echo "[✔] Cleanup complete! You can now install the latest version from the .dmg."
