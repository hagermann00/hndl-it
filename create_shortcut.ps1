$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = $WshShell.SpecialFolders.Item("Desktop")
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "Hndl-it.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
# Pass script as argument to wscript
$ScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "start_silent.vbs"
$Shortcut.Arguments = """$ScriptPath"""
$Shortcut.WorkingDirectory = $PSScriptRoot
# Try to use icon if available
$IconPath = Join-Path -Path $PSScriptRoot -ChildPath "floater\assets\icon.png"
if (-not (Test-Path $IconPath)) {
    $IconPath = Join-Path -Path $PSScriptRoot -ChildPath "floater\assets\icon.jpg"
}

if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
}
$Shortcut.Save()
Write-Host "Shortcut created at $ShortcutPath"
