"""
Systems Engineer Agent - 24/7 Health & Performance Monitor
Part of hndl-it Antigravity ecosystem

Responsibilities:
1. Periodic health checks of all agents (every 5 mins)
2. Resource usage monitoring (CPU, RAM, VRAM)
3. Log analysis for error patterns ("Archive Worm" logic)
4. Auto-optimization suggestions

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
CHECK_INTERVAL_SECONDS = 300  # 5 minutes
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

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
        
        # 2. Process Status
        processes = self._check_processes()
        
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

    def _check_processes(self) -> List[Dict]:
        """Check status of key hndl-it processes."""
        key_processes = ["launch_suite.py", "orchestrator", "monitor.py"]
        found = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmd_str = ' '.join(cmdline)
                    for kp in key_processes:
                        if kp in cmd_str:
                            found.append({
                                "name": kp,
                                "pid": proc.info['pid'],
                                "status": proc.status()
                            })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        return found

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
