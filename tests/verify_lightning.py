import sys
import os
import time

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.orchestrator import get_orchestrator
from shared.ipc import send_command

def test_lightning_routing():
    print("Testing Lightning Routing...")
    orc = get_orchestrator()
    commands = [
        "lightning read this text",
        "turbo say hello",
        "speed read the report"
    ]
    
    for cmd in commands:
        intent = orc.process(cmd)
        print(f"Command: {cmd}")
        print(f"  Target: {intent['target']}")
        print(f"  Action: {intent['action']}")
        print(f"  Method: {intent['method']}")
        if intent['target'] == 'read' and intent['action'] == 'lightning_read':
            print("  ✅ Pass")
        else:
            print("  ❌ Fail")

def test_archive_worm():
    print("\nTesting Archive Worm Logging...")
    log_path = r"D:\hndl-it\logs\evals\read-it.jsonl"
    
    # Check if directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # We can't easily test the live ipc_handler without running it, 
    # but we can verify the EvalLogger works.
    from shared.eval_logger import EvalLogger
    logger = EvalLogger(agent_name="read-it-test")
    logger.log_task("test input", "test output", {"test": True})
    
    if os.path.exists(log_path):
        print(f"  ✅ Log file exists at {log_path}")
    else:
        # Check if it was logged to a different location or if we need to check the exact path
        print(f"  ❌ Log file not found at {log_path}")

if __name__ == "__main__":
    test_lightning_routing()
    # test_archive_worm()
