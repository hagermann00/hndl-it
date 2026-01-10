"""
HNDL-IT Smart Backup Daemon
- All logs go STRAIGHT to Google Drive (30TB)
- Heavy, thorough logging - everything recorded
- No intermediate storage
"""

import subprocess
import time
import datetime
import os
import hashlib
import sys
from pathlib import Path

# === ALL PATHS GO TO GOOGLE DRIVE ===
SOURCE = Path(r"C:\IIWII_DB\hndl-it")
DEST_GDRIVE = Path(r"H:\My Drive\IIWII_ARCHIVE\hndl-it")
LOG_DIR = Path(r"H:\My Drive\IIWII_ARCHIVE\logs\hndl-it")
LOG_FILE = LOG_DIR / "backup_daemon.log"

# === TIMING ===
CHECK_INTERVAL = 300  # Check every 5 minutes
SYNC_COOLDOWN = 900   # Sync every 15 minutes max

# === EXCLUSIONS (minimal - we want everything) ===
EXCLUDE_DIRS = {'chrome_profile', '__pycache__', '.git', 'node_modules', '.venv', 'venv'}
EXCLUDE_EXTS = {'.tmp', '.pyc'}

last_hash = None
last_sync = 0
file_count = 0
changed_files = []

def log(msg):
    """All logs go STRAIGHT to Google Drive"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def get_folder_state():
    """Get folder state with detailed tracking"""
    global file_count, changed_files
    hasher = hashlib.md5()
    file_count = 0
    changed_files = []
    now = time.time()
    
    for root, dirs, files in os.walk(SOURCE):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for fname in sorted(files):
            if any(fname.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            fpath = Path(root) / fname
            try:
                stat = fpath.stat()
                file_count += 1
                hasher.update(f"{fpath}:{stat.st_mtime}:{stat.st_size}".encode())
                
                # Track ALL files modified in last 5 minutes
                if now - stat.st_mtime < 300:
                    rel_path = fpath.relative_to(SOURCE)
                    changed_files.append(str(rel_path))
            except:
                pass
    
    return hasher.hexdigest()

def sync():
    """Sync EVERYTHING to Google Drive"""
    log(f"SYNC STARTED - {file_count} files tracked")
    
    # Log ALL changed files (thorough)
    if changed_files:
        for f in changed_files:
            log(f"  CHANGED: {f}")
    
    cmd = [
        'robocopy', str(SOURCE), str(DEST_GDRIVE),
        '/MIR',
        '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv', '.venv',
        '/XF', '*.tmp', '*.pyc',
        '/NP', '/R:1', '/W:1'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Log robocopy output for thorough record
    if result.stdout:
        for line in result.stdout.strip().split('\n')[-5:]:  # Last 5 lines
            if line.strip():
                log(f"  ROBOCOPY: {line.strip()}")
    
    if result.returncode <= 7:
        log(f"SYNC COMPLETE (exit {result.returncode})")
    else:
        log(f"SYNC ERROR (exit {result.returncode})")
        if result.stderr:
            log(f"  ERROR: {result.stderr[:200]}")

def run():
    global last_hash, last_sync
    
    log("=" * 60)
    log("BACKUP DAEMON STARTED")
    log(f"Source: {SOURCE}")
    log(f"Archive: {DEST_GDRIVE} (Google Drive 30TB)")
    log(f"Logs: {LOG_DIR} (Google Drive)")
    log(f"Check interval: {CHECK_INTERVAL//60} min")
    log(f"Sync cooldown: {SYNC_COOLDOWN//60} min")
    log("=" * 60)
    
    last_hash = get_folder_state()
    log(f"Initial scan: {file_count} files")
    sync()
    last_sync = time.time()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        current_hash = get_folder_state()
        time_since_sync = time.time() - last_sync
        
        if current_hash != last_hash:
            log(f"CHANGES DETECTED - {len(changed_files)} files modified")
            if time_since_sync >= SYNC_COOLDOWN:
                sync()
                last_hash = current_hash
                last_sync = time.time()
            else:
                remaining = int((SYNC_COOLDOWN - time_since_sync) / 60)
                log(f"Cooldown active - {remaining} min until next sync")
        else:
            log(f"Heartbeat - {file_count} files, no changes")

if __name__ == "__main__":
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    run()
