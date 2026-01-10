import subprocess
import sys
import time
import os
import signal
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run Hndl-it System")
    parser.add_argument("--with-vision", action="store_true", help="Start the optional Vision Agent")
    args = parser.parse_args()

    print("🚀 Starting hndl-it System...")
    
    processes = []
    
    try:
        # 1. Start Browser Agent
        print("Starting Browser Agent (Port 8766)...")
        browser_process = subprocess.Popen(
            [sys.executable, "agents/browser/server.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            shell=False
        )
        processes.append(browser_process)
        time.sleep(2) # Wait for server to start
        
        # 2. Start Desktop Agent (Files)
        print("Starting Desktop Agent (Port 8767)...")
        desktop_process = subprocess.Popen(
            [sys.executable, "agents/desktop/server.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            shell=False
        )
        processes.append(desktop_process)
        time.sleep(1)

        # 3. Start Vision Agent (Optional)
        if args.with_vision:
            print("Starting Vision Agent (Port 8768)...")
            vision_process = subprocess.Popen(
                [sys.executable, "agents/vision/server.py"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                shell=False
            )
            processes.append(vision_process)
            time.sleep(1)

        # 4. Start Floater UI
        print("Starting Floater UI...")
        floater_process = subprocess.Popen(
            [sys.executable, "floater/main.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            shell=False
        )
        processes.append(floater_process)
        
        print("\n✅ System Running.")
        print("Press Ctrl+C to stop all services.")
        
        floater_process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        print("Terminating processes...")
        for p in processes:
            if p.poll() is None:
                p.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
