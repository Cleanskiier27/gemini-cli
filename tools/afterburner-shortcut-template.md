# Afterburner Desktop Shortcut Template

Use this template to build `afterburner.exe` and create a desktop shortcut on Windows.

## 1. Build the executable

From the repository root:

```powershell
# If you have Node.js installed and pkg available:
npx pkg tools/afterburner-launcher.js --target node18-win-x64 --output dist/afterburner.exe
```

If Node is not on PATH, use the portable Node runtime extracted in this repository:

```powershell
.\node-portable\node-v26.4.0-win-x64\node.exe .\tmp-pkg\node_modules\pkg\lib-es5\bin.js tools/afterburner-launcher.js --target node18-win-x64 --output dist/afterburner.exe
```

> The current built executable path is `dist/afterburner.exe`.

## 2. Create a desktop shortcut

Run the helper script from the repository root:

```powershell
.\tools\create-afterburner-shortcut.ps1
```

This creates a shortcut named `afterburner.lnk` on your Windows desktop that launches `dist/afterburner.exe`.

## 3. Use the shortcut

Double-click `afterburner.lnk` on your desktop, then pass your `gcloud` arguments:

```powershell
afterburner.exe auth list
```

> If you want the desktop shortcut to use a different target path or name, edit `tools/create-afterburner-shortcut.ps1`.
