"""
HNDL-IT Auto-Backup Failsafe
Mirrors C:\IIWII_DB\hndl-it to D:\IIWII_DB\hndl-it every 20 minutes
Only syncs changed files (incremental)
"""

import subprocess
import time
import datetime
import os
from pathlib import Path

# Configuration
SOURCE = r"C:\IIWII_DB\hndl-it"
DEST = r"D:\IIWII_DB\hndl-it"
INTERVAL_MINUTES = 20
LOG_FILE = r"D:\IIWII_DB\backup_log.txt"

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def sync():
    """Use robocopy for efficient incremental sync"""
    log("Starting sync...")
    
    # Robocopy flags:
    # /MIR = Mirror (sync deletions too)
    # /XD = Exclude directories (chrome_profile, __pycache__, .git)
    # /XF = Exclude files
    # /NP = No progress (cleaner output)
    # /NFL = No file list
    # /NDL = No directory list
    # /R:1 = Retry once
    # /W:1 = Wait 1 second between retries
    
    cmd = [
        'robocopy', SOURCE, DEST,
        '/MIR',
        '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv',
        '/XF', '*.log', '*.tmp',
        '/NP', '/R:1', '/W:1'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Robocopy exit codes: 0-7 = success, 8+ = error
    if result.returncode <= 7:
        log(f"Sync complete. Exit code: {result.returncode}")
    else:
        log(f"Sync error! Exit code: {result.returncode}")
        log(f"stderr: {result.stderr[:500] if result.stderr else 'None'}")

def main():
    log("="*50)
    log("HNDL-IT Backup Failsafe Started")
    log(f"Source: {SOURCE}")
    log(f"Destination: {DEST}")
    log(f"Interval: {INTERVAL_MINUTES} minutes")
    log("="*50)
    
    # Initial sync
    sync()
    
    # Loop forever
    while True:
        log(f"Sleeping {INTERVAL_MINUTES} minutes...")
        time.sleep(INTERVAL_MINUTES * 60)
        sync()

if __name__ == "__main__":
    main()
