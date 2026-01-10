import subprocess
import sys
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supervisor")

def run_module(name, script, start_y, extra_args=[]):
    logger.info(f"🚀 Launching {name}...")
    cmd = [sys.executable, script, f"--y={start_y}"] + extra_args
    # Detached creation flags?
    # For now standard Popen
    return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configuration
    START_Y = 290
    SPACING = 80
    
    modules = [
        ("hndl-it", os.path.join(base_dir, "floater", "main.py"), START_Y),
        ("read-it", os.path.join(base_dir, "read-it", "main.py"), START_Y + SPACING),
        ("todo-it", os.path.join(base_dir, "todo-it", "main.py"), START_Y + SPACING * 2),
        ("voice-it", os.path.join(base_dir, "voice_entry.py"), START_Y + SPACING * 3)
    ]
    
    procs = []
    for name, script, y in modules:
        p = run_module(name, script, y)
        procs.append(p)
        time.sleep(0.5) # Stagger slightly
        
    print("✅ All modules launched as independent processes.")
    print("Each module manages its own Icon and Lifecycle.")
    print("Voice routing handled via IPC in 'ipc/' folder.")
    
    try:
        while True:
            time.sleep(5)
            # Monitoring loop - could auto-restart here if desired
    except KeyboardInterrupt:
        print("Stopping all modules...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()
