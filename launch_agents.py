"""
Agent Service Launcher
Starts all IPC-based agent handlers as background processes.
"""

import subprocess
import sys
import os
import time
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hndl-it.agents")

# Agent definitions: (name, script_path, enabled_by_default)
AGENTS = [
    ("browser", "agents/browser/ipc_handler.py", False),  # Off by default - heavy
    ("desktop", "agents/desktop/ipc_handler.py", False),  # Off by default - needs approval
    ("read", "read-it/ipc_handler.py", True),             # On - TTS is lightweight
]


def launch_agents(agents_to_start=None):
    """
    Launch specified agent handlers.
    
    Args:
        agents_to_start: List of agent names, or None for all enabled
    """
    processes = []
    
    for name, script, enabled in AGENTS:
        if agents_to_start and name not in agents_to_start:
            continue
        if not agents_to_start and not enabled:
            continue
            
        script_path = os.path.join(PROJECT_ROOT, script)
        
        if not os.path.exists(script_path):
            logger.warning(f"⚠️ Script not found: {script_path}")
            continue
        
        try:
            # Start as background process
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            processes.append((name, proc))
            logger.info(f"✅ Started {name} agent (PID: {proc.pid})")
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
    
    return processes


def stop_agents(processes):
    """Stop all running agent processes."""
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            logger.info(f"⏹️ Stopped {name}")
        except:
            proc.kill()
            logger.warning(f"🔪 Force killed {name}")


def main():
    """Run all enabled agents until interrupted."""
    logger.info("🚀 Starting Agent Services...")
    
    processes = launch_agents()
    
    if not processes:
        logger.warning("No agents started!")
        return
    
    logger.info(f"Running {len(processes)} agent(s). Press Ctrl+C to stop.")
    
    try:
        while True:
            # Check for dead processes
            for name, proc in processes:
                if proc.poll() is not None:
                    logger.warning(f"⚠️ {name} exited unexpectedly")
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        stop_agents(processes)
        logger.info("All agents stopped.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch hndl-it agent handlers")
    parser.add_argument("--all", action="store_true", help="Start all agents (not just enabled)")
    parser.add_argument("--agents", nargs="+", help="Specific agents to start (e.g., browser desktop)")
    
    args = parser.parse_args()
    
    if args.all:
        launch_agents([name for name, _, _ in AGENTS])
    elif args.agents:
        launch_agents(args.agents)
    else:
        main()
