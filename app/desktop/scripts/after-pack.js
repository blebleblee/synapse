const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

exports.default = async function (context) {
  if (context.electronPlatformName !== 'darwin') return;

  const appPath = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`);
  console.log(`[AfterPack] Codesigning and sealing macOS application bundle at: ${appPath}`);

  const entitlementsPath = path.join(__dirname, '../build/entitlements.mac.plist');

  try {
    // 1. Sign sidecar binaries in Contents/Resources/bin
    const binDir = path.join(appPath, 'Contents', 'Resources', 'bin');
    if (fs.existsSync(binDir)) {
      for (const item of fs.readdirSync(binDir)) {
        const itemPath = path.join(binDir, item);
        try {
          fs.chmodSync(itemPath, 0o755);
          execSync(`codesign --force --options runtime --entitlements "${entitlementsPath}" --sign - "${itemPath}"`, {
            stdio: 'inherit',
          });
          console.log(`[AfterPack] Signed sidecar binary: ${item}`);
        } catch (e) {
          console.warn(`[AfterPack] Warning signing ${item}:`, e.message);
        }
      }
    }

    // 2. Sign entire .app bundle deeply with runtime entitlements
    execSync(`codesign --force --deep --options runtime --entitlements "${entitlementsPath}" --sign - "${appPath}"`, {
      stdio: 'inherit',
    });
    console.log('[AfterPack] Code signing and sealing succeeded.');

    // 3. Verify sealed signature
    execSync(`codesign -vvv --deep --strict "${appPath}"`, {
      stdio: 'inherit',
    });
    console.log('[AfterPack] Signature verification passed.');
  } catch (err) {
    console.error('[AfterPack] Code signing hook failed:', err);
    throw err;
  }
};
