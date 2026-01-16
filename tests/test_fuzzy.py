import sys
import os
import asyncio

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    import ollama
except ImportError:
    import scripts.mock_ollama_setup

from shared.orchestrator import Orchestrator

async def test_fuzzy_fallback_async():
def test_fuzzy_fallback():
    import asyncio
    print("Testing Fuzzy Fallback (Simulating LLM Error)...")
    orc = Orchestrator()
    # Force LLM router to fail (Gemma 2B) by pointing to bad host
    orc.ollama_host = 'http://localhost:9999'
    
    commands = [
        "please read this article",
        "can you summarize the text?",
        "search for pizza"
    ]
    
    for cmd in commands:
        intent = await orc.process(cmd)
        intent = asyncio.run(orc.process(cmd))
        print(f"Command: {cmd}")
        print(f"  Target: {intent['target']}")
        print(f"  Action: {intent['action']}")
        print(f"  Method: {intent['method']}")
        if intent['method'] == "fuzzy":
            print("  ✅ Fuzzy fallthrough active")
        elif intent['method'] == "regex":
            print("  ℹ️ Regex hit (no fallback needed)")
        else:
            print("  ❌ Fail (Got method: {intent['method']})")

def test_fuzzy_fallback():
    asyncio.run(test_fuzzy_fallback_async())

if __name__ == "__main__":
    test_fuzzy_fallback()
