Set WshShell = CreateObject("WScript.Shell")
' Run python run.py --with-vision in hidden mode (0), false means don't wait for return
WshShell.Run "python run.py --with-vision", 0, False
