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
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

IPC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ipc")
logger = logging.getLogger("hndl-it.ipc")


def send_command(target: str, action: str, payload: Optional[Dict] = None) -> bool:
    """
    Send command to a target module.
    
    Args:
        target: Module name (e.g. 'todo', 'read', 'browser', 'desktop')
        action: Action to perform (e.g. 'add', 'search', 'speak')
        payload: Optional parameters for the action
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not os.path.exists(IPC_DIR):
        os.makedirs(IPC_DIR, exist_ok=True)
    
    fpath = os.path.join(IPC_DIR, f"{target}.json")
    data = {
        "action": action,
        "payload": payload or {},
        "timestamp": time.time(),
        "sent_at": datetime.now().isoformat()
    }
    
    try:
        # Atomic write using temp file
        tmp = fpath + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, fpath)
        logger.info(f"📤 IPC -> {target}: {action}")
        return True
    except Exception as e:
        logger.error(f"❌ IPC send failed: {e}")
        return False


def check_mailbox(target: str) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Check if there is a message for target.
    Consumes the message (deletes the file after reading).
    
    Args:
        target: Module name to check
        
    Returns:
        Tuple of (action, payload) or (None, None) if no message
    """
    fpath = os.path.join(IPC_DIR, f"{target}.json")
    
    if not os.path.exists(fpath):
        return None, None
    
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Consume the message
        try:
            os.remove(fpath)
        except OSError:
            pass
        
        action = data.get("action")
        payload = data.get("payload", {})
        
        logger.debug(f"📥 IPC <- {target}: {action}")
        return action, payload
        
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Malformed IPC message for {target}: {e}")
        _safe_remove(fpath)
        return None, None
    except Exception as e:
        logger.error(f"❌ IPC read failed: {e}")
        return None, None


def peek_mailbox(target: str) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Peek at a message without consuming it.
    Useful for checking if work is pending.
    
    Args:
        target: Module name to check
        
    Returns:
        Tuple of (action, payload) or (None, None) if no message
    """
    fpath = os.path.join(IPC_DIR, f"{target}.json")
    
    if not os.path.exists(fpath):
        return None, None
    
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("action"), data.get("payload", {})
    except:
        return None, None


def broadcast(action: str, payload: Optional[Dict] = None, 
              targets: Optional[list] = None) -> int:
    """
    Broadcast a command to multiple targets.
    
    Args:
        action: Action to perform
        payload: Parameters
        targets: List of targets, or None for all known targets
        
    Returns:
        Number of successful sends
    """
    if targets is None:
        targets = ["floater", "todo", "read", "browser", "desktop", "voice"]
    
    success = 0
    for target in targets:
        if send_command(target, action, payload):
            success += 1
    return success


def clear_all():
    """Clear all pending IPC messages."""
    if not os.path.exists(IPC_DIR):
        return
    
    for f in os.listdir(IPC_DIR):
        if f.endswith('.json'):
            _safe_remove(os.path.join(IPC_DIR, f))
    
    logger.info("🧹 IPC cleared")


def _safe_remove(path: str):
    """Safely remove a file, ignoring errors."""
    try:
        os.remove(path)
    except:
        pass


# Route intent from Orchestrator to appropriate module
def route_intent(intent: Dict[str, Any]) -> bool:
    """
    Route a structured intent from the Orchestrator to the appropriate module.
    
    Args:
        intent: Dict with target, action, params from Orchestrator
        
    Returns:
        True if routed successfully
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


def _handle_system_command(action: str, params: Dict) -> bool:
    """Handle system-level commands."""
    logger.info(f"🔧 System command: {action}")
    
    if action == "quit":
        # Broadcast quit to all modules
        broadcast("quit")
        return True
    elif action == "restart":
        broadcast("restart")
        return True
    elif action == "status":
        # Status is handled by floater
        send_command("floater", "show_status", params)
        return True
    
    return False
