$ErrorActionPreference = 'Stop'

$repoRoot = Get-Location
$exePath = Join-Path $repoRoot 'dist\afterburner.exe'
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath 'afterburner.lnk'

if (-Not (Test-Path $exePath)) {
    Write-Error "Executable not found: $exePath. Build it first."
    exit 1
}

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = Split-Path $exePath
$shortcut.Arguments = ''
$shortcut.Description = 'Launch afterburner.exe to run gcloud commands.'
$shortcut.Save()

Write-Output "Created shortcut: $shortcutPath"
