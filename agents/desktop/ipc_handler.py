"""
Desktop Agent IPC Handler
Listens for IPC commands and executes desktop automation actions.
"""

import sys
import os
import time
import logging
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.ipc import check_mailbox, IPC_DIR

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


class IPCEventHandler(FileSystemEventHandler):
    """Watchdog handler to detect IPC messages."""

    def __init__(self, msg_queue, target_filename):
        self.msg_queue = msg_queue
        self.target_filename = target_filename

    def _process_event(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)
        if filename == self.target_filename:
            self.msg_queue.put(True)

    def on_created(self, event):
        self._process_event(event)

    def on_modified(self, event):
        self._process_event(event)

    def on_moved(self, event):
        if not event.is_directory and os.path.basename(event.dest_path) == self.target_filename:
            self.msg_queue.put(True)


def process_command():
    """Check mailbox and execute command."""
    try:
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
                    return False

                else:
                    logger.warning(f"Unknown action: {action}")

            except Exception as e:
                logger.error(f"Error executing {action}: {e}")

    except Exception as e:
        logger.error(f"Error checking mailbox: {e}")

    return True


def main():
    """Run desktop agent IPC handler."""
    logger.info("🖥️ Desktop Agent Handler starting (Watchdog Enabled)...")
    
    if not PYAUTOGUI_AVAILABLE:
        logger.error("pyautogui not installed! Run: pip install pyautogui")
        return
    
    # Safety settings
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1  # Small delay between actions
    
    # Setup Watchdog
    msg_queue = queue.Queue()
    event_handler = IPCEventHandler(msg_queue, "desktop.json")
    observer = Observer()
    observer.schedule(event_handler, IPC_DIR, recursive=False)
    observer.start()

    # Check initially
    msg_queue.put(True)

    running = True
    try:
        while running:
            try:
                # Block until event (or timeout to check for signals)
                msg_queue.get(timeout=1.0)
                
                # Drain queue (debounce)
                while not msg_queue.empty():
                    try:
                        msg_queue.get_nowait()
                    except queue.Empty:
                        break

                # Process
                running = process_command()

            except queue.Empty:
                continue
            except KeyboardInterrupt:
                logger.info("Interrupted")
                running = False

    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        observer.stop()
        observer.join()
        logger.info("Desktop Handler stopped")


if __name__ == "__main__":
    main()
