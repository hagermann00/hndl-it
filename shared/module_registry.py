# Module Registry - Where to find data from independent modules
# Orchestrator uses this to locate module output for follow-up actions
# No two-way IPC needed - just read from known locations

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

# =============================================================================
# MODULE CONFIGURATION
# =============================================================================

INBOX_ROOT = Path("D:/Antigravity_Inbox")
TOOLS_ROOT = Path.home() / ".gemini" / "antigravity" / "tools"

# Module definitions: where they live and where they store data
MODULES = {
    "dump-it": {
        "executable": TOOLS_ROOT / "quickdump_floater.py",
        "inbox": INBOX_ROOT / "dump",
        "format": "md",  # Primary format for human reading
        "jsonl": False,  # No JSONL yet
        "description": "Quick text/voice dumps",
    },
    "read-it": {
        "executable": TOOLS_ROOT / "readit_control.py",
        "inbox": INBOX_ROOT / "readit",
        "format": "md",
        "jsonl": False,
        "description": "TTS transcripts and saved readings",
    },
    "capture-it": {
        "executable": None,  # Not built yet
        "inbox": INBOX_ROOT / "capture",
        "format": "files",  # Screenshots, recordings
        "jsonl": False,
        "description": "Screenshots and screen recordings",
    },
    "knowledge": {
        "executable": None,  # Via inbox_module.py
        "inbox": INBOX_ROOT / "knowledge",
        "format": "md",
        "jsonl": True,  # Has JSONL for Airweave sync
        "description": "Saved knowledge from read-it, browser",
    },
    "todo": {
        "executable": None,  # Via todo-it in hndl-it
        "inbox": INBOX_ROOT / "todo",
        "format": "md",
        "jsonl": True,
        "description": "Extracted tasks",
    },
}


# =============================================================================
# DATA ACCESS FUNCTIONS
# =============================================================================

def get_today_file(module: str, ext: str = None) -> Optional[Path]:
    """Get today's data file for a module."""
    if module not in MODULES:
        return None
    
    config = MODULES[module]
    ext = ext or config["format"]
    today = datetime.now().strftime("%Y-%m-%d")
    
    filepath = config["inbox"] / f"{today}.{ext}"
    return filepath if filepath.exists() else None


def get_latest_entries(module: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the most recent entries from a module's inbox.
    Returns list of dicts with: id, timestamp, content, metadata
    """
    if module not in MODULES:
        return []
    
    config = MODULES[module]
    
    # Prefer JSONL if available (machine-readable)
    if config.get("jsonl"):
        jsonl_file = get_today_file(module, "jsonl")
        if jsonl_file and jsonl_file.exists():
            entries = []
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line.strip()))
                    except:
                        continue
            entries.reverse()
            return entries[:limit]
    
    # Fallback: parse markdown (less structured)
    md_file = get_today_file(module, "md")
    if md_file and md_file.exists():
        return _parse_markdown_entries(md_file, limit)
    
    return []


def _parse_markdown_entries(filepath: Path, limit: int) -> List[Dict]:
    """Parse markdown entries (best-effort extraction)."""
    entries = []
    content = filepath.read_text(encoding="utf-8")
    
    # Split on ## headers (entry markers)
    import re
    blocks = re.split(r'\n## ', content)
    
    for block in blocks[1:]:  # Skip header
        lines = block.strip().split('\n')
        if lines:
            header = lines[0]
            body = '\n'.join(lines[1:]).strip().strip('-').strip()
            
            # Extract timestamp from header like "[04:10:54 PM] 105054"
            time_match = re.search(r'\[(\d+:\d+:\d+ [AP]M)\]', header)
            timestamp = time_match.group(1) if time_match else header[:20]
            
            entries.append({
                "timestamp": timestamp,
                "content": body,
                "source": filepath.stem,
                "raw_header": header
            })
    
    entries.reverse()
    return entries[:limit]


def get_reading_context(limit: int = 5) -> Dict[str, Any]:
    """
    Get context from read-it and knowledge modules.
    Useful for follow-up actions like "open the webpage from that reading".
    """
    context = {
        "recent_readings": get_latest_entries("read-it", limit),
        "recent_knowledge": get_latest_entries("knowledge", limit),
    }
    
    # Extract any URLs from recent entries
    urls = []
    for entry in context["recent_knowledge"]:
        url = entry.get("url") or entry.get("metadata", {}).get("url")
        if url:
            urls.append({"url": url, "content_preview": entry.get("content", "")[:100]})
    
    context["urls_found"] = urls
    return context


def get_dump_context(limit: int = 10) -> List[Dict]:
    """Get recent dumps for context."""
    return get_latest_entries("dump-it", limit)


def search_inbox(query: str, module: str = None) -> List[Dict]:
    """
    Simple text search across inbox files.
    For real semantic search, use Airweave.
    """
    results = []
    modules_to_search = [module] if module else list(MODULES.keys())
    
    for mod in modules_to_search:
        if mod not in MODULES:
            continue
        config = MODULES[mod]
        inbox_dir = config["inbox"]
        
        if not inbox_dir.exists():
            continue
        
        for filepath in inbox_dir.glob("*.md"):
            try:
                content = filepath.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    results.append({
                        "module": mod,
                        "file": str(filepath),
                        "date": filepath.stem,
                        "preview": _extract_match_context(content, query)
                    })
            except:
                continue
    
    return results


def _extract_match_context(content: str, query: str, window: int = 100) -> str:
    """Extract text around the match."""
    idx = content.lower().find(query.lower())
    if idx == -1:
        return content[:200]
    
    start = max(0, idx - window)
    end = min(len(content), idx + len(query) + window)
    return f"...{content[start:end]}..."


# =============================================================================
# MODULE EXECUTION (subprocess launch)
# =============================================================================

def get_module_executable(module: str) -> Optional[Path]:
    """Get the executable path for a module."""
    if module in MODULES and MODULES[module].get("executable"):
        exe = MODULES[module]["executable"]
        return exe if exe.exists() else None
    return None


def launch_module(module: str) -> bool:
    """Launch a module as subprocess. Returns True if launched."""
    import subprocess
    import sys
    
    exe = get_module_executable(module)
    if not exe:
        return False
    
    try:
        subprocess.Popen(
            [sys.executable, str(exe)],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return True
    except Exception as e:
        print(f"Failed to launch {module}: {e}")
        return False


# =============================================================================
# QUICK STATUS CHECK
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MODULE REGISTRY - Antigravity Inbox Integration")
    print("=" * 60)
    print(f"\nInbox Root: {INBOX_ROOT}")
    print(f"Tools Root: {TOOLS_ROOT}")
    print("\nModules:")
    for name, config in MODULES.items():
        exe_status = "✓" if config["executable"] and config["executable"].exists() else "✗"
        inbox_status = "✓" if config["inbox"].exists() else "✗"
        print(f"  {name}: exe[{exe_status}] inbox[{inbox_status}] - {config['description']}")
    
    print("\n\nRecent Reading Context:")
    ctx = get_reading_context(3)
    for entry in ctx["recent_knowledge"][:3]:
        print(f"  - {entry.get('timestamp', 'N/A')}: {entry.get('content', '')[:60]}...")
