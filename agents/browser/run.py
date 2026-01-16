"""
hndl-it Browser Agent - Launch Script
"""

import subprocess
import sys
import os

# Get paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "Scripts", "python.exe")
SERVER_PATH = os.path.join(SCRIPT_DIR, "server.py")

def main():
    # Check if venv exists
    if not os.path.exists(VENV_PYTHON):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", os.path.join(SCRIPT_DIR, ".venv")])
        
        print("Installing dependencies (lightweight CDP only)...")
        subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-q", 
                       "websockets", "httpx", "requests"])
    
    # Run server
    print("Starting Browser Agent...")
    subprocess.run([VENV_PYTHON, SERVER_PATH])

if __name__ == "__main__":
    main()
