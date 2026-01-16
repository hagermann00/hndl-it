"""
Systems Engineer Agent - 24/7 Health & Performance Monitor
Part of hndl-it Antigravity ecosystem

Responsibilities:
1. Periodic health checks of all agents (every 5 mins)
2. Resource usage monitoring (CPU, RAM, VRAM)
3. Log analysis for error patterns ("Archive Worm" logic)
4. Auto-optimization suggestions
5. ZOMBIE HUNTER: Detects runaway processes and summons MEDIC

Usage:
    Run as a background process: python agents/systems_engineer/monitor.py
"""

import sys
import os
import time
import logging
import psutil
import json
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from shared.ipc import send_command, broadcast

# Configuration
CHECK_INTERVAL_SECONDS = 60  # Check every 1 minute now for faster response
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# Zombie Hunter Config
ENABLE_ZOMBIE_HUNTER = False  # Disabled by default, can be enabled by user/config
MAX_CPU_PERCENT = 90.0
MAX_DURATION_HIGH_CPU = 300  # 5 minutes
PROTECTED_PROCESSES = ["supervisor.py", "monitor.py", "launch_suite.py"]

# Setup logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure environment for Windows Unicode support
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "systems_engineer.log"), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("systems_engineer")


class SystemsEngineer:
    def __init__(self):
        self.running = True
        self.last_check = 0
        self.high_cpu_tracker = {}  # {pid: start_time}
        self.process_cache = {} # {pid: psutil.Process}
        self.warnings = []

    def start(self):
        """Start the monitoring loop."""
        logger.info("🛡️ Systems Engineer Agent started")
        send_command("floater", "display", {"type": "info", "content": "🛡️ Systems Engineer active"})
        
        while self.running:
            try:
                self.run_health_check()
                
                # Sleep for remaining time
                time.sleep(CHECK_INTERVAL_SECONDS)
                
            except KeyboardInterrupt:
                logger.info("Stopping Systems Engineer...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait on error

    def run_health_check(self):
        """Perform a comprehensive system health check."""
        logger.info("--- Starting Health Check ---")
        
        # 1. Resource Usage
        resources = self._check_resources()
        logger.info(f"Resources: {resources}")
        
        # 2. Process Status & Zombie Hunting
        processes = self._check_processes_and_hunt_zombies()
        
        # 3. Log Analysis (Archive Worm)
        log_issues = self._scan_logs()
        
        # 4. Report findings
        self._report_status(resources, processes, log_issues)

    def _check_resources(self) -> Dict[str, Any]:
        """Check system resources (CPU, Memory, Disk)."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(PROJECT_ROOT)
        
        gpu_info = "N/A"
        # Check if nvidia-smi is available before trying to run it
        if shutil.which('nvidia-smi'):
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    gpu_info = result.stdout.strip()
            except (subprocess.SubprocessError, OSError) as e:
                logger.warning(f"Failed to query GPU info despite nvidia-smi being available: {e}")

        return {
            "cpu": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "gpu": gpu_info
        }

    def _check_processes_and_hunt_zombies(self) -> List[Dict]:
        """Check status of key hndl-it processes and hunt zombies."""
        key_processes = ["launch_suite.py", "orchestrator", "monitor.py"]
        found = []
        current_pids = set()

        # More efficient process iteration
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pid = proc.pid
                current_pids.add(pid)

                # Ensure process is in cache for CPU tracking.
                if pid not in self.process_cache:
                    self.process_cache[pid] = proc

                cmd_str = ' '.join(proc.cmdline() or [])
                name = proc.name()

                # 1. Identify key processes
                for kp in key_processes:
                    if kp in cmd_str:
                        found.append({
                            "name": kp,
                            "pid": pid,
                            "status": proc.status()
                        })

                # 2. Zombie Hunting (if enabled)
                if ENABLE_ZOMBIE_HUNTER and "python" in name.lower():
                    # Use the cached process object to get meaningful cpu_percent readings
                    cached_proc = self.process_cache[pid]
                    cpu = cached_proc.cpu_percent(interval=None)

                    if cpu > MAX_CPU_PERCENT:
                        # Start tracking if not already
                        if pid not in self.high_cpu_tracker:
                            self.high_cpu_tracker[pid] = time.time()
                            logger.info(f"detected potential zombie {pid} with {cpu:.1f}% cpu")
                        else:
                            # Check duration
                            duration = time.time() - self.high_cpu_tracker[pid]
                            logger.info(f"tracking zombie {pid}: {duration:.1f}s > {MAX_DURATION_HIGH_CPU}s @ {cpu:.1f}%")
                            if duration > MAX_DURATION_HIGH_CPU:
                                self._summon_medic(pid, cmd_str, duration, cpu)
                    else:
                        # Cooled down, remove from tracker
                        if pid in self.high_cpu_tracker:
                            del self.high_cpu_tracker[pid]

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Cleanup cache and tracker for dead processes
        dead_pids = set(self.process_cache.keys()) - current_pids
        for pid in dead_pids:
            if pid in self.process_cache:
                del self.process_cache[pid]
            if pid in self.high_cpu_tracker:
                del self.high_cpu_tracker[pid]
                
        return found

    def _summon_medic(self, pid, cmd_name, duration, cpu):
        """Summon the Medic agent to deal with the zombie."""
        # Safety Check: Don't kill protected processes
        for safe in PROTECTED_PROCESSES:
            if safe in cmd_name:
                logger.warning(f"⚠️ Cannot kill protected process {safe} (PID {pid}) despite high load.")
                return

        logger.info(f"🚑 SUMMONING MEDIC for PID {pid} ({cmd_name}) - {duration:.0f}s @ {cpu}% CPU")

        try:
            medic_script = os.path.join(PROJECT_ROOT, "agents", "medic", "medic_agent.py")
            if not os.path.exists(medic_script):
                logger.error("Medic agent script not found!")
                return

            # Launch Medic as a subprocess
            subprocess.Popen([sys.executable, medic_script, str(pid), cmd_name, str(cpu), str(duration)])

            # Notify user
            send_command("floater", "display", {
                "type": "warning",
                "message": f"🚑 Medic dispatched for stuck process (PID {pid})"
            })

        except Exception as e:
            logger.error(f"Failed to summon medic: {e}")

    def _scan_logs(self) -> List[str]:
        """Scan recent log files for ERROR patterns."""
        issues = []
        patterns = ["ERROR", "CRITICAL", "Exception", "Traceback"]
        
        # Look at last modified log files
        for filename in os.listdir(LOG_DIR):
            if filename.endswith(".log"):
                filepath = os.path.join(LOG_DIR, filename)
                try:
                    # Only read if modified in last 5 mins
                    mtime = os.path.getmtime(filepath)
                    if time.time() - mtime < CHECK_INTERVAL_SECONDS:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            # Read last 50 lines
                            lines = f.readlines()[-50:]
                            for line in lines:
                                if any(p in line for p in patterns):
                                    issues.append(f"[{filename}] {line.strip()[:100]}")
                except Exception as e:
                    logger.warning(f"Could not scan log {filename}: {e}")
                    
        return issues

    def _report_status(self, resources: Dict, processes: List, log_issues: List):
        """Report health status to the floater."""
        status_msg = f"System Health: CPU {resources['cpu']}% | RAM {resources['memory_percent']}%"
        
        # Alert on high usage
        if resources['memory_percent'] > 90:
            send_command("floater", "display", {
                "type": "error", 
                "message": f"⚠️ High Memory Usage: {resources['memory_percent']}%"
            })
            
        # Alert on log issues
        if log_issues:
            count = len(log_issues)
            send_command("floater", "display", {
                "type": "warning",
                "message": f"⚠️ Found {count} recent errors in logs."
            })
            
            # Create an A2UI report for the issues
            a2ui_report = {
                "type": "List",
                "id": "health_report",
                "props": {"title": "🛡️ Systems Engineer Report"},
                "children": [
                    {
                        "type": "Card",
                        "id": "resource_card",
                        "props": {
                            "title": "Resource Usage",
                            "subtitle": f"CPU: {resources['cpu']}% | RAM: {resources['memory_percent']}% | GPU: {resources['gpu']}"
                        },
                        "children": [{"type": "ProgressBar", "id": "ram_bar", "props": {"value": resources['memory_percent'], "max": 100}}]
                    },
                    {
                        "type": "Card",
                        "id": "issues_card",
                        "props": {
                            "title": "Recent Errors",
                            "subtitle": f"{len(log_issues)} issues detected"
                        },
                        "children": [
                            {"type": "Text", "id": f"err_{i}", "props": {"text": issue}} 
                            for i, issue in enumerate(log_issues[:3])
                        ]
                    }
                ]
            }
            send_command("floater", "render_a2ui", {"a2ui": a2ui_report})
        
        logger.info(status_msg)


if __name__ == "__main__":
    agent = SystemsEngineer()
    agent.start()
