"""
Worker Agent - Heavy Lifter for hndl-it
Handles long-running tasks like file processing, conversions, or complex analysis
off the main UI thread.
"""

import sys
import os
import time
import threading

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.agent_base import BaseAgent
from shared.ipc import send_command

class WorkerAgent(BaseAgent):
    def __init__(self):
        super().__init__("worker", max_workers=2)
        self.logger.info("👷 Worker Agent ready for heavy lifting.")

    def process_action(self, action: str, payload: dict):
        """Handle worker tasks."""
        if action == "process_file":
            self._process_file(payload)
        elif action == "sleep":
            # Test task
            duration = payload.get("duration", 5)
            self.logger.info(f"Sleeping for {duration}s...")
            time.sleep(duration)
            self.logger.info("Woke up!")
            send_command("floater", "notify", {"message": "Task complete: Sleep"})
        else:
            self.logger.warning(f"Unknown job: {action}")

    def _process_file(self, payload: dict):
        filepath = payload.get("filepath")
        if not filepath or not os.path.exists(filepath):
            self.logger.error(f"File not found: {filepath}")
            return

        self.logger.info(f"Processing {filepath}...")
        # Simulate heavy work
        file_size = os.path.getsize(filepath)
        chunks = range(0, 101, 10)

        for p in chunks:
            time.sleep(0.2) # Simulating work
            # Report progress?
            if p % 50 == 0:
                self.logger.info(f"Progress: {p}%")

        self.logger.info(f"Done processing {filepath}")
        send_command("floater", "notify", {"message": f"Processed {os.path.basename(filepath)}"})

if __name__ == "__main__":
    agent = WorkerAgent()
    agent.run()
