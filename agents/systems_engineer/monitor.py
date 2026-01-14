"""
Systems Engineer Agent - 24/7 Health & Performance Monitor
Part of hndl-it Antigravity ecosystem

Responsibilities:
1. Periodic health checks of all agents (every 5 mins)
2. Resource usage monitoring (CPU, RAM, VRAM)
3. Log analysis for error patterns ("Archive Worm" logic)
4. Auto-optimization suggestions
5. ZOMBIE HUNTER: Detects and kills runaway processes

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
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from shared.ipc import send_command, broadcast

# Configuration
CHECK_INTERVAL_SECONDS = 60  # Check every 1 minute now for faster response
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
INTERVENTION_LOG = os.path.join(LOG_DIR, "interventions.log")

# Zombie Hunter Config
MAX_CPU_PERCENT = 90.0
MAX_DURATION_HIGH_CPU = 300  # 5 minutes (300s) of continuous high CPU
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
        
        # TODO: GPU VRAM check if `nvidia-smi` is available
        gpu_info = "N/A"
        try:
            # Simple nvidia-smi check
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                gpu_info = result.stdout.strip()
        except:
            pass

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
        
        # Iterate all PIDs
        for pid in psutil.pids():
            try:
                # Use cached process object if possible to keep CPU stats
                if pid in self.process_cache:
                    proc = self.process_cache[pid]
                else:
                    proc = psutil.Process(pid)
                    self.process_cache[pid] = proc

                # Check if process is still alive
                if not proc.is_running():
                    del self.process_cache[pid]
                    continue

                # Filter for only relevant processes (Python)
                try:
                    name = proc.name()
                    cmdline = proc.cmdline()
                    cmd_str = ' '.join(cmdline)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

                current_pids.add(pid)

                # 1. Identify key processes
                for kp in key_processes:
                    if kp in cmd_str:
                        found.append({
                            "name": kp,
                            "pid": pid,
                            "status": proc.status()
                        })

                # 2. Zombie Hunting (Python processes only)
                if "python" in name.lower():
                    # Call cpu_percent.
                    # First call on new object = 0.0.
                    # Second call (next loop) = meaningful.
                    cpu = proc.cpu_percent(interval=None)

                    if cpu > MAX_CPU_PERCENT:
                        # Start tracking if not already
                        if pid not in self.high_cpu_tracker:
                            self.high_cpu_tracker[pid] = time.time()
                            logger.info(f"detected potential zombie {pid} with {cpu}% cpu")
                        else:
                            # Check duration
                            duration = time.time() - self.high_cpu_tracker[pid]
                            logger.info(f"tracking zombie {pid}: {duration:.1f}s > {MAX_DURATION_HIGH_CPU}s @ {cpu}%")
                            if duration > MAX_DURATION_HIGH_CPU:
                                self._kill_zombie(proc, cmd_str, duration, cpu)
                    else:
                        # Cooled down, remove from tracker
                        if pid in self.high_cpu_tracker:
                            del self.high_cpu_tracker[pid]

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                if pid in self.process_cache:
                    del self.process_cache[pid]
                continue

        # Cleanup cache for dead processes
        for cached_pid in list(self.process_cache.keys()):
            if cached_pid not in current_pids:
                del self.process_cache[cached_pid]

        # Cleanup tracker for dead processes
        for tracked_pid in list(self.high_cpu_tracker.keys()):
            if tracked_pid not in current_pids:
                del self.high_cpu_tracker[tracked_pid]
                
        return found

    def _kill_zombie(self, proc, cmd_name, duration, cpu):
        """Terminate a runaway process."""
        # Safety Check: Don't kill protected processes
        for safe in PROTECTED_PROCESSES:
            if safe in cmd_name:
                logger.warning(f"⚠️ Cannot kill protected process {safe} (PID {proc.pid}) despite high load.")
                return

        logger.info(f"🧟 KILLING ZOMBIE: PID {proc.pid} ({cmd_name}) - {duration:.0f}s @ {cpu}% CPU")

        try:
            proc.terminate()
            time.sleep(1)
            if proc.is_running():
                proc.kill()

            self._log_intervention(proc.pid, cmd_name, f"High CPU ({cpu}%) for {duration:.0f}s")

            # Notify user
            send_command("floater", "display", {
                "type": "success",
                "message": f"🛡️ Auto-Fixed: Killed stuck process (PID {proc.pid})"
            })

        except Exception as e:
            logger.error(f"Failed to kill zombie {proc.pid}: {e}")

    def _log_intervention(self, pid, name, reason):
        """Log the intervention for the user to see 'what works'."""
        entry = f"{datetime.now().isoformat()} | KILL | PID: {pid} | Name: {name} | Reason: {reason}\n"
        try:
            with open(INTERVENTION_LOG, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as e:
            logger.error(f"Failed to write intervention log: {e}")

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
