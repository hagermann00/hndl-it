# hndl-it Storage Architecture Standard

## 3-Tier Drive Strategy

---

## Tier 1: C: Drive (Small SSD - "The Runway")

**Purpose:** OS + Active Apps ONLY. Keep at 20%+ free for performance.

### What Belongs Here

- Windows OS
- Installed programs (Program Files)
- Active Python/Node environments (.venv)
- User profile essentials (AppData\Roaming for active apps)

### What Does NOT Belong Here

- ❌ Downloads (redirect to D:)
- ❌ Documents (redirect to D:)
- ❌ Media files
- ❌ Git repos (except active work)
- ❌ Docker images (move to D:)
- ❌ Ollama models (move to D:)

### Automated Cleanup Targets

```
C:\Users\dell3630\AppData\Local\Temp           # Always safe
C:\Windows\Temp                                 # Always safe
C:\Users\dell3630\AppData\Local\Microsoft\Windows\INetCache
C:\Users\dell3630\AppData\Local\CrashDumps
C:\$Recycle.Bin                                 # Periodic empty
```

### Redirect Strategy

```powershell
# Move Downloads to D:
mklink /J "C:\Users\dell3630\Downloads" "D:\Downloads"

# Move Documents to D:
mklink /J "C:\Users\dell3630\Documents" "D:\Documents"
```

---

## Tier 2: D: Drive (500GB SSD - "The Workshop")

**Purpose:** Active projects, working files, local backups.

### Folder Structure

```
D:\
├── Projects\              # All git repos / active code
│   ├── hndl-it\           # Main agent suite
│   ├── y-it-agents\       # Y-IT automation
│   └── ...
├── Downloads\             # Redirected from C:
├── Documents\             # Redirected from C:
├── Media\                 # Active media files
│   ├── Screenshots\
│   ├── Recordings\
│   └── Assets\
├── Ollama\                # Local LLM models
│   └── models\
├── Docker\                # Docker images/volumes
├── Archives\              # Quarterly rollover staging
│   ├── 2025-Q4\
│   └── 2026-Q1\
└── Backups\               # Local backup before cloud sync
```

### Auto-Archive Rules

- Files older than 90 days in Downloads → Move to Archives
- Media older than 30 days → Move to Archives
- Project branches merged > 60 days → Archive and delete

---

## Tier 3: Google Drive (30TB - "The Vault")

**Purpose:** Long-term archive, off-site backup, cold storage.

### Folder Structure

```
My Drive (brihag8@gmail.com)\
├── 📁 Active\             # Synced folders (sparse)
│   ├── Y-IT Project Files\
│   └── Shared Work\
├── 📦 Archives\           # Cold storage (no sync)
│   ├── 2024\
│   ├── 2025\
│   └── 2026\
├── 💾 Backups\            # System backups
│   ├── hndl-it\
│   ├── ANTI_GRAVITY\
│   └── Full-System-Snapshots\
└── 🗃️ Vault\              # Permanent records
    ├── Legal\
    ├── Financial\
    └── Personal\
```

### Sync Strategy

- **Active:** Full sync (always local)
- **Archives:** Stream-only (no local copy)
- **Backups:** Upload-only (rclone scheduled)

---

## Automated Workflow

### Daily (Cron/Task Scheduler)

1. Clean C:\Temp folders
2. Empty Recycle Bin if C: < 10GB free
3. Log disk stats to D:\Logs\disk_stats.csv

### Weekly

1. Scan for duplicates across D:
2. Archive old Downloads to D:\Archives
3. Sync D:\Backups → Google Drive

### Monthly

1. Full C: drive audit
2. Move D:\Archives\[old quarter] → Google Drive
3. Prune Docker unused images
4. Verify Ollama model integrity

---

## Emergency Protocols

### C: Drive Critical (< 5GB free)

```bash
# Immediate actions
1. Empty Recycle Bin
2. Clear all Temp folders
3. Move largest user files to D:
4. Check for runaway log files
5. Clear browser caches (Chrome, Edge)
```

### D: Drive Critical (< 50GB free)

```bash
# Immediate actions
1. Identify largest folders
2. Archive old projects to Google Drive
3. Delete node_modules / .venv (can recreate)
4. Move cold media to Google Drive
```

---

## Integration with hndl-it

### Voice Commands

- "Clean up drives" → Run full cleanup
- "Archive old downloads" → Move to D:\Archives
- "Sync to cloud" → rclone push to Google Drive
- "Drive status" → Report free space on all tiers

### Agent Capabilities

- Desktop Agent can move files
- Vision Agent can identify large folders in Explorer
- Floater shows drive status in compact mode

---

## Environment Variables

```bash
# Set in system environment
OLLAMA_MODELS=D:\Ollama\models
DOCKER_DATA=D:\Docker
DOWNLOADS=D:\Downloads
PROJECTS=D:\Projects
ARCHIVE_ROOT=D:\Archives
GOOGLE_DRIVE=C:\Users\dell3630\My Drive (brihag8@gmail.com)
```

---

**Last Updated:** 2026-01-10
**Owner:** hndl-it Automation Suite
