"""
HNDL-IT Smart Backup Daemon
- Only syncs when files actually change  
- Logs to D: drive (not C:)
- Archives to Google Drive
- Runs headless in background
"""

import subprocess
import time
import datetime
import os
import hashlib
import sys
from pathlib import Path

# === PATHS (D: drive for logs, Google Drive for archive) ===
SOURCE = Path(r"C:\IIWII_DB\hndl-it")
DEST_LOCAL = Path(r"D:\IIWII_DB\hndl-it")
DEST_GDRIVE = Path(r"H:\My Drive\IIWII_ARCHIVE\hndl-it")
LOG_FILE = Path(r"D:\IIWII_DB\logs\backup_daemon.log")

# === TIMING ===
CHECK_INTERVAL = 300  # Check for changes every 5 minutes
SYNC_COOLDOWN = 900   # Don't sync more than once per 15 minutes

# === EXCLUSIONS ===
EXCLUDE_DIRS = {'.git', '__pycache__', 'chrome_profile', 'node_modules', '.venv', 'venv', '.system'}
EXCLUDE_EXTS = {'.log', '.tmp', '.pyc'}

last_hash = None
last_sync = 0
file_count = 0
changed_files = []

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def get_folder_state():
    """Get folder state - returns hash and list of recently changed files"""
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
                
                if now - stat.st_mtime < 300:
                    rel_path = fpath.relative_to(SOURCE)
                    changed_files.append(str(rel_path))
            except:
                pass
    
    return hasher.hexdigest()

def sync_to(dest, name):
    """Sync to a destination"""
    cmd = [
        'robocopy', str(SOURCE), str(dest),
        '/MIR',
        '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv', '.venv', 'logs',
        '/XF', '*.log', '*.tmp',
        '/NP', '/NFL', '/NDL', '/NJH', '/NJS',
        '/R:1', '/W:1'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode <= 7:
        log(f"  → {name}: OK")
    else:
        log(f"  → {name}: ERROR ({result.returncode})")

def sync():
    """Sync to D: drive and Google Drive"""
    log(f"SYNC STARTED - {file_count} files")
    if changed_files:
        log(f"  Changed: {', '.join(changed_files[:5])}" + 
            (f" (+{len(changed_files)-5} more)" if len(changed_files) > 5 else ""))
    
    sync_to(DEST_LOCAL, "D: drive")
    sync_to(DEST_GDRIVE, "Google Drive")
    
    log("SYNC COMPLETE")

def run():
    global last_hash, last_sync
    
    log("=" * 50)
    log("BACKUP DAEMON STARTED")
    log(f"Source: {SOURCE}")
    log(f"Dest 1: {DEST_LOCAL}")
    log(f"Dest 2: {DEST_GDRIVE}")
    log(f"Check: {CHECK_INTERVAL//60} min | Cooldown: {SYNC_COOLDOWN//60} min")
    log("=" * 50)
    
    last_hash = get_folder_state()
    log(f"Initial: {file_count} files")
    sync()
    last_sync = time.time()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        current_hash = get_folder_state()
        time_since_sync = time.time() - last_sync
        
        if current_hash != last_hash:
            log(f"CHANGES: {len(changed_files)} files modified")
            if time_since_sync >= SYNC_COOLDOWN:
                sync()
                last_hash = current_hash
                last_sync = time.time()
            else:
                remaining = int((SYNC_COOLDOWN - time_since_sync) / 60)
                log(f"Cooldown: {remaining} min remaining")
        else:
            log(f"No changes ({file_count} files)")

if __name__ == "__main__":
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    run()
