"""
hndl-it Drive Cleanup & Archive Utility
Handles: Temp cleanup, deduplication, archive structuring
"""
import os
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# Config
C_DRIVE_TARGETS = [
    r"C:\Users\dell3630\AppData\Local\Temp",
    r"C:\Windows\Temp",
    r"C:\Users\dell3630\AppData\Local\Microsoft\Windows\INetCache",
]

ARCHIVE_ROOT = Path(r"D:\Archives")
DEDUP_MIN_SIZE_MB = 1  # Only dedup files > 1MB


def clean_temp_folders():
    """Clean standard temp directories."""
    total_freed = 0
    for target in C_DRIVE_TARGETS:
        if os.path.exists(target):
            try:
                for item in Path(target).iterdir():
                    try:
                        if item.is_file():
                            size = item.stat().st_size
                            item.unlink()
                            total_freed += size
                        elif item.is_dir():
                            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item, ignore_errors=True)
                            total_freed += size
                    except:
                        pass
            except:
                pass
    return total_freed / (1024**3)  # Return GB


def find_duplicates(search_path: str, min_size_mb: float = DEDUP_MIN_SIZE_MB):
    """Find duplicate files by hash."""
    hash_map = defaultdict(list)
    min_size = min_size_mb * 1024 * 1024
    
    for root, dirs, files in os.walk(search_path):
        # Skip hidden/system folders
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for fname in files:
            fpath = Path(root) / fname
            try:
                if fpath.stat().st_size >= min_size:
                    # Quick hash (first 64KB + file size)
                    with open(fpath, 'rb') as f:
                        data = f.read(65536)
                    file_hash = hashlib.md5(data + str(fpath.stat().st_size).encode()).hexdigest()
                    hash_map[file_hash].append(str(fpath))
            except:
                pass
    
    # Return only duplicates
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}


def archive_by_date(source_path: str, archive_name: str = "general"):
    """Move old files to dated archive structure on D: drive."""
    archive_base = ARCHIVE_ROOT / archive_name
    archive_base.mkdir(parents=True, exist_ok=True)
    
    moved = 0
    for root, dirs, files in os.walk(source_path):
        for fname in files:
            fpath = Path(root) / fname
            try:
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
                year_month = mtime.strftime("%Y-%m")
                dest_dir = archive_base / year_month
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(fpath), str(dest_dir / fname))
                moved += 1
            except:
                pass
    return moved


def get_drive_stats():
    """Get C: and D: drive free space."""
    import ctypes
    stats = {}
    for drive in ['C:', 'D:']:
        try:
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive), None, None, ctypes.pointer(free_bytes)
            )
            stats[drive] = round(free_bytes.value / (1024**3), 2)
        except:
            stats[drive] = 0
    return stats


def run_full_cleanup():
    """Run complete cleanup routine."""
    print("=" * 50)
    print("hndl-it Drive Cleanup Utility")
    print("=" * 50)
    
    # 1. Drive stats before
    stats_before = get_drive_stats()
    print(f"\nBefore: C: {stats_before['C:']} GB free | D: {stats_before['D:']} GB free")
    
    # 2. Clean temp
    print("\n[1/3] Cleaning temp folders...")
    freed = clean_temp_folders()
    print(f"  Freed: {freed:.2f} GB")
    
    # 3. Find duplicates (just report for now)
    print("\n[2/3] Scanning for duplicates...")
    dupes = find_duplicates(r"C:\Users\dell3630\Downloads")
    if dupes:
        print(f"  Found {len(dupes)} duplicate sets")
        for h, paths in list(dupes.items())[:3]:
            print(f"    - {Path(paths[0]).name} ({len(paths)} copies)")
    else:
        print("  No duplicates found")
    
    # 4. Drive stats after
    stats_after = get_drive_stats()
    print(f"\nAfter: C: {stats_after['C:']} GB free | D: {stats_after['D:']} GB free")
    print(f"Total freed: {stats_after['C:'] - stats_before['C:']:.2f} GB")
    
    return {
        "freed_gb": stats_after['C:'] - stats_before['C:'],
        "duplicates_found": len(dupes),
        "c_free_gb": stats_after['C:'],
        "d_free_gb": stats_after['D:']
    }


if __name__ == "__main__":
    result = run_full_cleanup()
    print("\n" + json.dumps(result, indent=2))
