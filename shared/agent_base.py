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

from shared.ipc import check_mailbox, send_command

class BaseAgent(ABC):
    """
    Abstract Base Class for robust agents.

    Features:
    - Main Loop with configurable polling
    - ThreadPool for non-blocking task execution
    - Graceful Shutdown handling
    - Standardized Logging
    - Error Isolation (one task crash doesn't kill the agent)
    """

    def __init__(self, agent_name: str, poll_interval: float = 0.5, max_workers: int = 3):
        self.agent_name = agent_name
        self.poll_interval = poll_interval
        self.running = True

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

        self.logger.info(f"🚀 {agent_name} initialized (Pool: {max_workers} workers)")

    def _signal_handler(self, sig, frame):
        self.logger.info(f"🛑 Shutdown signal received: {sig}")
        self.stop()

    def stop(self):
        """Signals the agent to stop."""
        self.running = False
        self.executor.shutdown(wait=False)
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

                except Exception as e:
                    self.logger.error(f"⚠️ Loop Error: {e}")
                    time.sleep(1) # Prevent tight loop on error

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            self.stop()
        finally:
            self.logger.info(f"✅ {self.agent_name} shut down.")
