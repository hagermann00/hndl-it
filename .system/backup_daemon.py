"""
HNDL-IT Complete Backup & Logging System
=========================================
- Live log flow → Google Drive
- D: drive = Real-time working clone
- Periodic versioning with timestamps
- Log rotation and compression
- Best practice folder structure
"""

import subprocess
import time
import datetime
import os
import hashlib
import sys
import gzip
import shutil
from pathlib import Path

# === FOLDER STRUCTURE (Best Practices) ===
#
# D:\IIWII_DB\
# ├── hndl-it\              ← Real-time clone (can run if C: dies)
# └── intermediate\         ← Temp files, overflow from C:
#
# H:\My Drive\IIWII_ARCHIVE\
# ├── hndl-it\              ← Current code archive
# ├── logs\
# │   ├── live\             ← Live log stream
# │   └── archive\          ← Compressed old logs
# └── versions\
#     └── YYYY-MM-DD_HH\    ← Periodic snapshots

# === PATHS ===
SOURCE = Path(r"C:\IIWII_DB\hndl-it")
CLONE_D = Path(r"D:\IIWII_DB\hndl-it")
INTERMEDIATE_D = Path(r"D:\IIWII_DB\intermediate")

# Inbox Paths
INBOX_SOURCE = Path(r"D:\Antigravity_Inbox")
INBOX_ARCHIVE = Path(r"H:\My Drive\Antigravity_Inbox_Backup")

GDRIVE_BASE = Path(r"H:\My Drive\IIWII_ARCHIVE")
ARCHIVE_CODE = GDRIVE_BASE / "hndl-it"
LOGS_LIVE = GDRIVE_BASE / "logs" / "live"
LOGS_ARCHIVE = GDRIVE_BASE / "logs" / "archive"
VERSIONS_DIR = GDRIVE_BASE / "versions"

LOG_FILE = LOGS_LIVE / "backup.log"

# === TIMING ===
CLONE_INTERVAL = 60       # D: clone every 1 minute
LOG_ROTATE_DAYS = 7       # Compress logs older than 7 days
VERSION_INTERVAL = 3600   # Create version snapshot every 1 hour

last_clone_hash = None
last_version_time = 0

def setup_folders():
    """Create folder structure"""
    for folder in [CLONE_D, INTERMEDIATE_D, ARCHIVE_CODE, LOGS_LIVE, LOGS_ARCHIVE, VERSIONS_DIR, INBOX_ARCHIVE]:
        folder.mkdir(parents=True, exist_ok=True)

def log(msg):
    """Live log to Google Drive"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def get_hash():
    hasher = hashlib.md5()
    count = 0
    for root, dirs, files in os.walk(SOURCE):
        dirs[:] = [d for d in dirs if d not in {'chrome_profile', '__pycache__', '.git', 'node_modules', '.venv'}]
        for fname in sorted(files):
            if not fname.endswith(('.tmp', '.pyc')):
                fpath = Path(root) / fname
                try:
                    stat = fpath.stat()
                    count += 1
                    hasher.update(f"{fpath}:{stat.st_mtime}:{stat.st_size}".encode())
                except:
                    pass
    return hasher.hexdigest(), count

def sync_clone():
    """Real-time sync to D: drive"""
    cmd = ['robocopy', str(SOURCE), str(CLONE_D), '/MIR',
           '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv', '.venv',
           '/XF', '*.tmp', '*.pyc', '/NP', '/NFL', '/NDL', '/NJH', '/NJS', '/R:1', '/W:1']
    return subprocess.run(cmd, capture_output=True).returncode <= 7

def sync_archive():
    """Sync current state to Google Drive archive"""
    # 1. Sync Code
    cmd_code = ['robocopy', str(SOURCE), str(ARCHIVE_CODE), '/MIR',
           '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv', '.venv',
           '/XF', '*.tmp', '*.pyc', '/NP', '/NFL', '/NDL', '/NJH', '/NJS', '/R:1', '/W:1']
    res_code = subprocess.run(cmd_code, capture_output=True).returncode <= 7

    # 2. Sync Inbox (Antigravity Push)
    if INBOX_SOURCE.exists():
        cmd_inbox = ['robocopy', str(INBOX_SOURCE), str(INBOX_ARCHIVE), '/MIR',
                     '/XF', '*.tmp', '/NP', '/NFL', '/NDL', '/NJH', '/NJS', '/R:1', '/W:1']
        res_inbox = subprocess.run(cmd_inbox, capture_output=True).returncode <= 7
    else:
        res_inbox = True # Skip if source doesn't exist

    return res_code and res_inbox

def create_version_snapshot():
    """Create timestamped version snapshot"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H")
    version_dir = VERSIONS_DIR / timestamp
    
    if version_dir.exists():
        return  # Already have this hour's snapshot
    
    log(f"VERSION SNAPSHOT → {timestamp}")
    cmd = ['robocopy', str(SOURCE), str(version_dir), '/MIR',
           '/XD', 'chrome_profile', '__pycache__', '.git', 'node_modules', 'venv', '.venv',
           '/XF', '*.tmp', '*.pyc', '/NP', '/NFL', '/NDL', '/NJH', '/NJS', '/R:1', '/W:1']
    subprocess.run(cmd, capture_output=True)

def rotate_logs():
    """Compress old logs, clean very old ones"""
    now = datetime.datetime.now()
    
    for log_file in LOGS_LIVE.glob("*.log"):
        if log_file == LOG_FILE:
            continue
        
        mtime = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
        age_days = (now - mtime).days
        
        if age_days > LOG_ROTATE_DAYS:
            # Compress to archive
            gz_path = LOGS_ARCHIVE / f"{log_file.stem}_{mtime.strftime('%Y%m%d')}.log.gz"
            with open(log_file, 'rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            log_file.unlink()
            log(f"ROTATED: {log_file.name} → {gz_path.name}")

def run():
    global last_clone_hash, last_version_time
    
    setup_folders()
    
    log("=" * 60)
    log("BACKUP SYSTEM STARTED")
    log(f"Source: {SOURCE}")
    log(f"Clone (D:): {CLONE_D}")
    log(f"Archive: {ARCHIVE_CODE}")
    log(f"Logs: {LOGS_LIVE}")
    log(f"Versions: {VERSIONS_DIR}")
    log("=" * 60)
    
    current_hash, count = get_hash()
    last_clone_hash = current_hash
    last_version_time = time.time()
    
    log(f"Initial: {count} files")
    sync_clone()
    sync_archive()
    create_version_snapshot()
    
    while True:
        time.sleep(CLONE_INTERVAL)
        
        current_hash, count = get_hash()
        now = time.time()
        
        # D: CLONE - Real-time
        if current_hash != last_clone_hash:
            if sync_clone():
                log(f"CLONE → D: ({count} files)")
                last_clone_hash = current_hash
        
        # VERSION SNAPSHOT - Hourly
        if now - last_version_time >= VERSION_INTERVAL:
            create_version_snapshot()
            sync_archive()
            rotate_logs()
            last_version_time = now

if __name__ == "__main__":
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    run()
