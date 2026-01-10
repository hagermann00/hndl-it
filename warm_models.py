"""
Model Warmer for hndl-it
Force-loads the required models into VRAM to ensure readiness.
"""

import threading
import time
import requests
import json
from shared.llm_config import ACTIVE_ROLES

OLLAMA_API = "http://localhost:11434/api/generate"

def warm_model(role, model_name):
    print(f"🔥 Warming up {role.upper()} ({model_name})...")
    try:
        response = requests.post(OLLAMA_API, json={
            "model": model_name,
            "prompt": "Hello",
            "stream": False,
            "keep_alive": -1 # Keep loaded indefinitely
        })
        if response.status_code == 200:
            print(f"✅ {model_name} loaded!")
        else:
            print(f"❌ Failed to load {model_name}: {response.text}")
    except Exception as e:
        print(f"❌ Error connecting to Ollama for {model_name}: {e}")

def main():
    print("🚀 Initializing hndl-it Brain Trust...")
    print(f"Targeting: {', '.join(ACTIVE_ROLES.values())}")
    
    threads = []
    for role, model in ACTIVE_ROLES.items():
        t = threading.Thread(target=warm_model, args=(role, model))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
        
    print("✨ All models warmed and resident in VRAM.")

if __name__ == "__main__":
    main()
