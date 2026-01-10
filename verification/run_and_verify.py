import subprocess
import sys
import time
import os
import signal

def main():
    print("🧪 Starting Automated Verification...")
    
    # 1. Start System
    print("   Starting run.py...")
    # Use python executable to run run.py
    # Pass --with-vision to test everything
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    process = subprocess.Popen(
        [sys.executable, "run.py", "--with-vision"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=env
    )
    
    # Complete silence from run.py is suspicious, but let's wait
    print("   Waiting 5 seconds for subsystems to initialize...")
    time.sleep(5)
    
    # 2. Run Verification
    print("   Running test_system.py...")
    test_result = subprocess.run(
        [sys.executable, "verification/test_system.py", "--with-vision"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        capture_output=True,
        text=True,
        env=env,
        encoding='utf-8' # Force encoding for read
    )
    
    print("\n   --- Verification Output ---")
    print(test_result.stdout)
    if test_result.stderr:
        print("   --- Verification Errors ---")
        print(test_result.stderr)
    
    # Write to log file for debugging
    with open("verification.log", "w", encoding="utf-8") as f:
        f.write(test_result.stdout)
        if test_result.stderr:
            f.write("\nERROR:\n")
            f.write(test_result.stderr)

    print("   ---------------------------\n")
    
    # 3. Cleanup
    print("   Terminating system...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        
    if test_result.returncode == 0:
        print("✅ SUCCESS: System verification passed.")
        sys.exit(0)
    else:
        print("❌ FAILURE: System verification failed. Check verification.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
