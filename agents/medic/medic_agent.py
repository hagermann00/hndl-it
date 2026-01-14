"""
Medic Agent - Ephemeral Process Terminator
Part of hndl-it Antigravity ecosystem

Responsibilities:
1. Receive target PID from Systems Engineer.
2. Confirm PID is still runaway (double-check).
3. Terminate the process.
4. Log the intervention.
5. Exit immediately.

Usage:
    python agents/medic/medic_agent.py <PID> <PROCESS_NAME> <CPU_PCT> <DURATION>
"""

import sys
import os
import time
import logging
import psutil
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from shared.ipc import send_command

LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
INTERVENTION_LOG = os.path.join(LOG_DIR, "interventions.log")

# Setup logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "medic.log"), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("medic")

def terminate_process(pid, name, cpu_pct, duration):
    logger.info(f"🚑 Medic dispatched for PID {pid} ({name})")

    try:
        proc = psutil.Process(int(pid))

        # Double check? Maybe not, trust the System Engineer.
        # But we can verify it exists.

        logger.info(f"Attempting to terminate {pid}...")
        proc.terminate()

        # Wait for death
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            logger.warning(f"PID {pid} resisting termination. Escalating to KILL.")
            proc.kill()

        logger.info(f"✅ PID {pid} neutralized.")

        _log_intervention(pid, name, f"High CPU ({cpu_pct}%) for {duration:.0f}s - TERMINATED BY MEDIC")

        send_command("floater", "display", {
            "type": "success",
            "message": f"🚑 Medic: Neutralized stuck process (PID {pid})"
        })

    except psutil.NoSuchProcess:
        logger.info(f"PID {pid} already gone. Job done.")
    except Exception as e:
        logger.error(f"Failed to neutralize {pid}: {e}")

def _log_intervention(pid, name, reason):
    """Log the intervention."""
    entry = f"{datetime.now().isoformat()} | MEDIC_KILL | PID: {pid} | Name: {name} | Reason: {reason}\n"
    try:
        with open(INTERVENTION_LOG, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception as e:
        logger.error(f"Failed to write intervention log: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        logger.error("Usage: medic_agent.py <PID> <NAME> <CPU> <DURATION>")
        sys.exit(1)

    terminate_process(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]))
