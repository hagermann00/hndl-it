"""
IPC - Inter-Process Communication for hndl-it suite.
Uses file-based messaging for reliable cross-process communication.

Each target module has a mailbox file (ipc/<target>.json).
Messages are atomic-write and consumed on read.
"""

import json
import os
import time
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Define IPC Directory relative to this file
IPC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ipc")

# Ensure it exists
if not os.path.exists(IPC_DIR):
    os.makedirs(IPC_DIR, exist_ok=True)

logger = logging.getLogger("hndl-it.ipc")


def get_mailbox_path(target: str) -> str:
    """Returns the absolute path for a target's mailbox."""
    return os.path.join(IPC_DIR, f"{target}.json")


def send_command(target: str, action: str, payload: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send command to a target module.
    
    Args:
        target: Module name (e.g. 'todo', 'read', 'browser', 'desktop')
        action: Action to perform (e.g. 'add', 'search', 'speak')
        payload: Optional parameters for the action
        
    Returns:
        True if sent successfully, False otherwise
    """
    fpath = get_mailbox_path(target)
    
    data = {
        "action": action,
        "payload": payload or {},
        "timestamp": time.time(),
        "sent_at": datetime.now().isoformat()
    }
    
    try:
        # Atomic write: write to temp file then rename
        # We use a temp file in the SAME directory to ensure atomic rename works
        fd, tmp_path = tempfile.mkstemp(dir=IPC_DIR, suffix=".tmp")

        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        # Atomic replacement
        os.replace(tmp_path, fpath)

        logger.debug(f"📤 IPC -> {target}: {action}")
        return True

    except Exception as e:
        logger.error(f"❌ IPC send failed ({target}): {e}")
        # Try to clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        return False


def check_mailbox(target: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Check if there is a message for target.
    Consumes the message (deletes the file after reading).
    
    Args:
        target: Module name to check
        
    Returns:
        Tuple of (action, payload) or (None, None) if no message
    """
    fpath = get_mailbox_path(target)
    
    if not os.path.exists(fpath):
        return None, None
    
    try:
        # Read first
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Then delete (Consume)
        try:
            os.remove(fpath)
        except FileNotFoundError:
            # Another process might have grabbed it? Unlikely in this architecture
            pass
        
        action = data.get("action")
        payload = data.get("payload", {})
        
        logger.debug(f"📥 IPC <- {target}: {action}")
        return action, payload
        
    except json.JSONDecodeError:
        logger.warning(f"⚠️ Malformed IPC message for {target}. Deleting.")
        _safe_remove(fpath)
        return None, None
    except Exception as e:
        logger.error(f"❌ IPC read failed ({target}): {e}")
        return None, None


def peek_mailbox(target: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Peek at a message without consuming it.
    Useful for checking if work is pending.
    """
    fpath = get_mailbox_path(target)
    
    if not os.path.exists(fpath):
        return None, None
    
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("action"), data.get("payload", {})
    except:
        return None, None


def broadcast(action: str, payload: Optional[Dict[str, Any]] = None,
              targets: Optional[List[str]] = None) -> int:
    """
    Broadcast a command to multiple targets.
    """
    if targets is None:
        # Auto-discover targets based on running agents (could be enhanced)
        targets = ["floater", "todo", "read", "browser", "desktop", "voice", "brain"]
    
    success_count = 0
    for target in targets:
        if send_command(target, action, payload):
            success_count += 1
    return success_count


def clear_all():
    """Clear all pending IPC messages."""
    if not os.path.exists(IPC_DIR):
        return
    
    count = 0
    for f in os.listdir(IPC_DIR):
        if f.endswith('.json') or f.endswith('.tmp'):
            _safe_remove(os.path.join(IPC_DIR, f))
            count += 1
    
    logger.info(f"🧹 IPC cleared ({count} files removed)")


def _safe_remove(path: str):
    """Safely remove a file, ignoring errors."""
    try:
        os.remove(path)
    except:
        pass


def _handle_system_command(action: str, params: Dict) -> bool:
    """Handle system-level commands."""
    logger.info(f"🔧 System command: {action}")

    if action == "quit":
        broadcast("quit")
        return True
    elif action == "restart":
        broadcast("restart")
        return True
    elif action == "status":
        send_command("floater", "show_status", params)
        return True

    return False

# Route intent from Orchestrator to appropriate module
def route_intent(intent: Dict[str, Any]) -> bool:
    """
    Route a structured intent from the Orchestrator to the appropriate module.
    """
    target = intent.get("target", "floater")
    action = intent.get("action", "unknown")
    params = intent.get("params", {})
    
    # Special handling for system commands
    if target == "system":
        return _handle_system_command(action, params)
    
    # Special handling for A2UI render
    if target == "floater" and action == "render_a2ui":
        return send_command("floater", "render_a2ui", params)
    
    # Route to module
    return send_command(target, action, params)
