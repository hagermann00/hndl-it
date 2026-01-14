import subprocess
import sys
import os
import time
import logging
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supervisor")

LOCK_FILE = "supervisor.lock"

def check_singleton():
    """Ensure only one supervisor runs."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                logger.error(f"⛔ Supervisor already running (PID {pid}). Exiting.")
                print(f"Supervisor is already running (PID {pid}). Please kill it first or just close this window.")
                sys.exit(1)
            else:
                logger.info("Found stale lock file. Overwriting.")
        except:
            pass
            
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def main():
    check_singleton()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # We now use the Unified Suite Launcher
    # This prevents "3 instances of every icon"
    # Determine which Python to use (prefer the .venv)
    venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    
    logger.info(f"🚀 Launching Unified Suite using {python_exe}...")
    
    # Launch the Suite
    suite_process = subprocess.Popen([python_exe, suite_script], cwd=base_dir)

    
    print("✅ Hndl-it Suite Launched.")
    print(f"   PID: {suite_process.pid}")
    print("   Close this window to stop the suite.")
    
    try:
        while True:
            time.sleep(1)
            # Check if suite is still running
            if suite_process.poll() is not None:
                logger.warning("Suite exited. Supervisor shutting down.")
                break
    except KeyboardInterrupt:
        print("\nStopping Suite...")
        try:
            parent = psutil.Process(suite_process.pid)
            for child in parent.children(recursive=True):
                try:
                    child.terminate()
                except:
                    pass
            parent.terminate()
        except Exception as e:
            logger.error(f"Error killing process tree: {e}")
            # Fallback
            suite_process.terminate()
        
    # Cleanup lock
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

if __name__ == "__main__":
    main()
