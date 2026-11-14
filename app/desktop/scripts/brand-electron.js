const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

if (process.platform !== 'darwin') process.exit(0);

const distDir = path.resolve(__dirname, '../node_modules/electron/dist');
const pathTxt = path.resolve(__dirname, '../node_modules/electron/path.txt');
const oldApp = path.join(distDir, 'Electron.app');
const newApp = path.join(distDir, 'Synapse Workbench.app');

try {
  if (fs.existsSync(oldApp)) {
    fs.renameSync(oldApp, newApp);
    const oldExe = path.join(newApp, 'Contents/MacOS/Electron');
    const newExe = path.join(newApp, 'Contents/MacOS/Synapse Workbench');
    if (fs.existsSync(oldExe)) {
      fs.renameSync(oldExe, newExe);
    }
  }

  if (fs.existsSync(newApp)) {
    const plist = path.join(newApp, 'Contents/Info.plist');
    execSync(`/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable 'Synapse Workbench'" "${plist}" 2>/dev/null || true`);
    execSync(`/usr/libexec/PlistBuddy -c "Set :CFBundleName 'Synapse Workbench'" "${plist}" 2>/dev/null || true`);
    execSync(`/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName 'Synapse Workbench'" "${plist}" 2>/dev/null || true`);
    execSync(`/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier 'com.synapse.workbench'" "${plist}" 2>/dev/null || true`);

    const iconSrc = path.resolve(__dirname, '../assets/icon.icns');
    const iconDst = path.join(newApp, 'Contents/Resources/electron.icns');
    if (fs.existsSync(iconSrc)) {
      fs.copyFileSync(iconSrc, iconDst);
    }

    fs.writeFileSync(pathTxt, 'Synapse Workbench.app/Contents/MacOS/Synapse Workbench');
    execSync(`/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "${newApp}" 2>/dev/null || true`);
  }
} catch (e) {
  // Silent fallback in CI/CD or non-mac environments
}
