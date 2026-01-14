$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\dell3630\Desktop\Antigravity Suite.lnk")
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "c:\iiwii_db\hndl-it\launch_suite.py"
$Shortcut.WorkingDirectory = "c:\iiwii_db\hndl-it"
$Shortcut.IconLocation = "c:\iiwii_db\hndl-it\floater\assets\hndl_it_icon.png"
$Shortcut.Save()
