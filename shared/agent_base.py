"""
Base Agent - Foundation for all hndl-it backend agents.
Provides robust IPC loop, error handling, thread pooling, and standardized logging.
"""

import sys
import os
import time
import logging
import signal
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Any

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.ipc import check_mailbox, send_command, IPC_DIR

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

class BaseAgent(ABC):
    """
    Abstract Base Class for robust agents.

    Features:
    - Main Loop with configurable polling (or file system events)
    - ThreadPool for non-blocking task execution
    - Graceful Shutdown handling
    - Standardized Logging
    - Error Isolation (one task crash doesn't kill the agent)
    """

    def __init__(self, agent_name: str, poll_interval: float = 0.5, max_workers: int = 3):
        self.agent_name = agent_name
        self.poll_interval = poll_interval
        self.running = True
        self.ipc_event = threading.Event()
        self.observer = None

        # Setup Logger
        logging.basicConfig(
            level=logging.INFO,
            format=f"%(asctime)s - {agent_name} - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(f"hndl-it.{agent_name}")

        # Thread Pool for parallel tasks
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=agent_name)

        # Signal Handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Setup Watchdog if available
        if WATCHDOG_AVAILABLE:
            self._setup_watchdog()

        self.logger.info(f"🚀 {agent_name} initialized (Pool: {max_workers} workers)")

    def _setup_watchdog(self):
        """Configures file system watcher for IPC."""
        try:
            target_file = f"{self.agent_name}.json"
            event_trigger = self.ipc_event

            class IPCEventHandler(FileSystemEventHandler):
                def _trigger(self, event_path):
                    if os.path.basename(event_path) == target_file:
                        event_trigger.set()

                def on_created(self, event):
                    self._trigger(event.src_path)

                def on_modified(self, event):
                    self._trigger(event.src_path)

                def on_moved(self, event):
                    self._trigger(event.dest_path)

            self.observer = Observer()
            self.observer.schedule(IPCEventHandler(), path=IPC_DIR, recursive=False)
            self.observer.start()
            self.logger.info("👀 Watchdog enabled for IPC.")
        except Exception as e:
            self.logger.warning(f"⚠️ Watchdog setup failed: {e}")
            self.observer = None

    def _signal_handler(self, sig, frame):
        self.logger.info(f"🛑 Shutdown signal received: {sig}")
        self.stop()

    def stop(self):
        """Signals the agent to stop."""
        self.running = False
        self.executor.shutdown(wait=False)
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.ipc_event.set() # Wake up loop
        self.logger.info("👋 Agent stopping...")

    @abstractmethod
    def process_action(self, action: str, payload: Dict[str, Any]):
        """
        Implement this to handle specific actions.
        This method runs in a separate thread.
        """
        pass

    def _safe_process(self, action: str, payload: Dict[str, Any]):
        """Wrapper to catch exceptions in worker threads."""
        try:
            self.logger.info(f"🔧 Processing: {action}")
            self.process_action(action, payload)
        except Exception as e:
            self.logger.error(f"❌ Error processing {action}: {e}", exc_info=True)
            # Optional: Send error back to UI
            send_command("floater", "display", {
                "type": "error",
                "message": f"{self.agent_name} error: {str(e)}"
            })

    def run(self):
        """Starts the main IPC loop."""
        self.logger.info(f"🏃 {self.agent_name} loop started.")

        try:
            while self.running:
                try:
                    # Check for messages
                    action, payload = check_mailbox(self.agent_name)

                    if action:
                        self.logger.info(f"📥 Received: {action}")

                        if action == "quit":
                            self.stop()
                            break

                        elif action == "ping":
                            send_command("floater", "pong", {"agent": self.agent_name})

                        else:
                            # Submit to thread pool
                            self.executor.submit(self._safe_process, action, payload)

                        # Loop immediately if we found work, to drain queue
                        continue

                except Exception as e:
                    self.logger.error(f"⚠️ Loop Error: {e}")
                    time.sleep(1) # Prevent tight loop on error

                # Wait for event or timeout (poll interval)
                self.ipc_event.wait(timeout=self.poll_interval)
                self.ipc_event.clear()

        except KeyboardInterrupt:
            self.stop()
        finally:
            self.logger.info(f"✅ {self.agent_name} shut down.")
