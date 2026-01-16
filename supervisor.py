import subprocess
import sys
import os
import time
import logging
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supervisor")

LOCK_FILE = "supervisor.lock"
SUITE_SCRIPT = "launch_suite.py"

def check_singleton():
    """Ensure only one supervisor runs."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    # Check if it's actually this script
                    cmdline = proc.cmdline()
                    # We look for 'supervisor.py' in the command line
                    if any('supervisor.py' in arg for arg in cmdline):
                        logger.error(f"⛔ Supervisor already running (PID {pid}). Exiting.")
                        print(f"Supervisor is already running (PID {pid}). Please kill it first or just close this window.")
                        sys.exit(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                     pass

                logger.info("Found stale lock file (PID reused or invalid). Overwriting.")
            else:
                logger.info("Found stale lock file. Overwriting.")
        except:
            pass
            
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def get_python_executable(base_dir):
    """Determine the best Python executable to use."""
    # Check for venv in standard locations
    venvs = [
        os.path.join(base_dir, ".venv", "Scripts", "python.exe"), # Windows
        os.path.join(base_dir, ".venv", "bin", "python"),         # Unix
        os.path.join(base_dir, "venv", "Scripts", "python.exe"),
        os.path.join(base_dir, "venv", "bin", "python")
    ]

    for path in venvs:
        if os.path.exists(path):
            return path

    return sys.executable

def main():
    check_singleton()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = get_python_executable(base_dir)
    
    suite_script_path = os.path.join(base_dir, SUITE_SCRIPT)
    if not os.path.exists(suite_script_path):
        logger.error(f"❌ Could not find {SUITE_SCRIPT}")
        sys.exit(1)

    logger.info(f"🚀 Launching Unified Suite using {python_exe}...")
    
    # Launch the Suite
    try:
        suite_process = subprocess.Popen([python_exe, suite_script_path], cwd=base_dir)

        print("✅ Hndl-it Suite Launched.")
        print(f"   PID: {suite_process.pid}")
        print("   Close this window to stop the suite.")

        while True:
            time.sleep(1)
            # Check if suite is still running
            if suite_process.poll() is not None:
                logger.warning("Suite exited. Supervisor shutting down.")
                break

    except KeyboardInterrupt:
        print("\nStopping Suite...")
    except Exception as e:
        logger.error(f"Error running suite: {e}")
    finally:
        # Cleanup
        if 'suite_process' in locals() and suite_process.poll() is None:
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
                suite_process.terminate()
        
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

if __name__ == "__main__":
    main()
