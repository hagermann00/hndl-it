"""
HNDL-IT Smart Backup Daemon
- Only syncs when files actually change
- Runs headless in background
- Logs what it's checking and backing up
"""

import subprocess
import time
import datetime
import os
import hashlib
import sys
from pathlib import Path

# Configuration
SOURCE = Path(r"C:\IIWII_DB\hndl-it")
DEST = Path(r"D:\IIWII_DB\hndl-it")
LOG_FILE = Path(r"D:\IIWII_DB\.backup_log.txt")
CHECK_INTERVAL = 300  # Check for changes every 5 minutes
SYNC_COOLDOWN = 900   # Don't sync more than once per 15 minutes

# Excluded from hash calculation
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
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for fname in sorted(files):
            if any(fname.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            fpath = Path(root) / fname
            try:
                stat = fpath.stat()
                file_count += 1
                hasher.update(f"{fpath}:{stat.st_mtime}:{stat.st_size}".encode())
                
                # Track files modified in last 5 minutes
                if now - stat.st_mtime < 300:
                    rel_path = fpath.relative_to(SOURCE)
                    changed_files.append(str(rel_path))
            except:
                pass
    
    return hasher.hexdigest()

def sync():
    """Efficient sync using robocopy"""
    log(f"SYNC STARTED - {file_count} files tracked")
    if changed_files:
        log(f"Recently changed: {', '.join(changed_files[:10])}" + 
            (f" (+{len(changed_files)-10} more)" if len(changed_files) > 10 else ""))
    
    cmd = [
        'robocopy', str(SOURCE), str(DEST),
        '/MIR',
        '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv', '.venv',
        '/XF', '*.log', '*.tmp',
        '/NP', '/NFL', '/NDL', '/NJH', '/NJS',
        '/R:1', '/W:1'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode <= 7:
        log(f"SYNC COMPLETE - Exit code {result.returncode}")
    else:
        log(f"SYNC ERROR - Exit code {result.returncode}")

def run():
    global last_hash, last_sync
    
    log("=" * 50)
    log("BACKUP DAEMON STARTED")
    log(f"Source: {SOURCE}")
    log(f"Dest: {DEST}")
    log(f"Check interval: {CHECK_INTERVAL}s ({CHECK_INTERVAL//60} min)")
    log(f"Sync cooldown: {SYNC_COOLDOWN}s ({SYNC_COOLDOWN//60} min)")
    log("=" * 50)
    
    # Initial sync
    last_hash = get_folder_state()
    log(f"Initial state: {file_count} files")
    sync()
    last_sync = time.time()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        current_hash = get_folder_state()
        time_since_sync = time.time() - last_sync
        
        if current_hash != last_hash:
            log(f"CHANGES DETECTED - {len(changed_files)} files modified recently")
            if time_since_sync >= SYNC_COOLDOWN:
                sync()
                last_hash = current_hash
                last_sync = time.time()
            else:
                remaining = int(SYNC_COOLDOWN - time_since_sync)
                log(f"Cooldown active - sync in {remaining}s")
        else:
            log(f"No changes - {file_count} files checked")

if __name__ == "__main__":
    # Headless mode - redirect stdout/stderr to null
    if '--headless' in sys.argv or True:  # Always headless
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    run()
