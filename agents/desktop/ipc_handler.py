"""
Desktop Agent IPC Handler
Listens for IPC commands and executes desktop automation actions.
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from shared.ipc import check_mailbox, get_mailbox_path

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hndl-it.desktop.handler")


def main():
    """Run desktop agent IPC handler."""
    logger.info("🖥️ Desktop Agent Handler starting...")
    
    if not PYAUTOGUI_AVAILABLE:
        logger.error("pyautogui not installed! Run: pip install pyautogui")
        return
    
    # Safety settings
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1  # Small delay between actions
    
    # Setup Watchdog
    process_event = threading.Event()
    desktop_mailbox_path = get_mailbox_path("desktop")
    ipc_dir = os.path.dirname(desktop_mailbox_path)

    class IPCHandler(FileSystemEventHandler):
        def _trigger(self, event_path):
            if event_path.endswith("desktop.json"):
                process_event.set()

        def on_created(self, event):
            self._trigger(event.src_path)

        def on_modified(self, event):
            self._trigger(event.src_path)

        def on_moved(self, event):
            self._trigger(event.dest_path)

    observer = Observer()
    observer.schedule(IPCHandler(), path=ipc_dir, recursive=False)
    observer.start()
    logger.info(f"👀 Watching {ipc_dir} for events...")

    try:
        while True:
            # Check for commands
            action, payload = check_mailbox("desktop")
            
            if action:
                logger.info(f"📥 Received: {action} - {payload}")
                
                try:
                    if action == "type":
                        text = payload.get("subject") or payload.get("text") or payload.get("input", "")
                        pyautogui.typewrite(text, interval=0.02)
                        logger.info(f"✅ Typed: {text[:50]}...")
                        
                    elif action == "click":
                        element = payload.get("subject") or payload.get("element", "")
                        # Simple click at current position or specified coords
                        x = payload.get("x")
                        y = payload.get("y")
                        if x and y:
                            pyautogui.click(x, y)
                        else:
                            pyautogui.click()
                        logger.info(f"✅ Clicked at {pyautogui.position()}")
                        
                    elif action == "screenshot":
                        screenshot = pyautogui.screenshot()
                        path = os.path.join(os.path.dirname(__file__), "screenshot.png")
                        screenshot.save(path)
                        logger.info(f"✅ Screenshot saved to {path}")
                        
                    elif action == "scroll":
                        direction = payload.get("subject") or payload.get("direction", "down")
                        amount = payload.get("amount", 3)
                        if direction.lower() == "up":
                            pyautogui.scroll(amount)
                        else:
                            pyautogui.scroll(-amount)
                        logger.info(f"✅ Scrolled {direction}")
                        
                    elif action == "hotkey":
                        keys = payload.get("keys", [])
                        if keys:
                            pyautogui.hotkey(*keys)
                            logger.info(f"✅ Hotkey: {keys}")
                            
                    elif action == "move":
                        x = payload.get("x", 0)
                        y = payload.get("y", 0)
                        pyautogui.moveTo(x, y)
                        logger.info(f"✅ Moved to ({x}, {y})")
                        
                    elif action == "quit":
                        logger.info("Shutting down...")
                        break
                        
                    else:
                        logger.warning(f"Unknown action: {action}")
                        
                except Exception as e:
                    logger.error(f"Error executing {action}: {e}")

                # Check again immediately if we processed something
                continue
            
            # Wait for event
            process_event.wait(timeout=1.0)
            process_event.clear()
            
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        observer.stop()
        observer.join()
        logger.info("Desktop Handler stopped")


if __name__ == "__main__":
    main()
