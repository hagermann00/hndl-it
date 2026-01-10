@echo off
echo 🚀 Launching Chrome for Hndl-it (Port 9222)...

:: Standard Paths
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else (
    echo ❌ Chrome not found in standard locations!
    echo Please launch Chrome manually with: --remote-debugging-port=9222
    pause
    exit /b
)

:: Launch
echo Found Chrome at: "%CHROME_PATH%"
start "" "%CHROME_PATH%" --remote-debugging-port=9222
echo ✅ Chrome launched. You can now run 'run_browser_agent.bat' or 'run.py'.
pause
