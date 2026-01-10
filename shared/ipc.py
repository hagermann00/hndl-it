import json
import os
import logging

IPC_DIR = r"C:\iiwii_db\hndl-it\ipc"
logger = logging.getLogger("hndl-it.ipc")

def send_command(target, action, payload=None):
    """
    Send command to a target module (e.g. 'todo', 'read').
    Writes to ipc/<target>.json
    """
    if not os.path.exists(IPC_DIR):
        os.makedirs(IPC_DIR)
        
    fpath = os.path.join(IPC_DIR, f"{target}.json")
    data = {
        "action": action,
        "payload": payload or {},
        "timestamp": os.path.getmtime(fpath) if os.path.exists(fpath) else 0 # simple versioning
    }
    
    try:
        # Write atomic-ish
        tmp = fpath + ".tmp"
        with open(tmp, 'w') as f:
            json.dump(data, f)
        os.replace(tmp, fpath)
        logger.info(f"IPC sent to {target}: {action}")
    except Exception as e:
        logger.error(f"IPC send failed: {e}")

def check_mailbox(target):
    """
    Check if there is a message for target.
    Returns (action, payload) or (None, None).
    Consumes the message file (deletes it).
    """
    fpath = os.path.join(IPC_DIR, f"{target}.json")
    if not os.path.exists(fpath):
        return None, None
        
    try:
        with open(fpath, 'r') as f:
            data = json.load(f)
        
        # Consume it
        try:
            os.remove(fpath)
        except:
            pass
            
        return data.get("action"), data.get("payload")
    except Exception as e:
        logger.error(f"IPC read failed: {e}")
        return None, None
