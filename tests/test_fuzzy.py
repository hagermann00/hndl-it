import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.orchestrator import Orchestrator

def test_fuzzy_fallback():
    print("Testing Fuzzy Fallback (Simulating LLM Error)...")
    orc = Orchestrator()
    # Force LLM router to fail by giving it a bad URL
    orc.api_url = "http://localhost:9999/bad" 
    
    commands = [
        "please read this article",
        "can you summarize the text?",
        "search for pizza"
    ]
    
    for cmd in commands:
        intent = orc.process(cmd)
        print(f"Command: {cmd}")
        print(f"  Target: {intent['target']}")
        print(f"  Action: {intent['action']}")
        print(f"  Method: {intent['method']}")
        if intent['method'] == "fuzzy":
            print("  ✅ Fuzzy fallthrough active")
        elif intent['method'] == "regex":
            print("  ℹ️ Regex hit (no fallback needed)")
        else:
            print("  ❌ Fail")

if __name__ == "__main__":
    test_fuzzy_fallback()
