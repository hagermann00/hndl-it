import requests
import json

MODELS_TO_UNLOAD = [
    "gemma:7b",
    "gemma2:2b",
    "moondream",
    "qwen2.5:3b",
    "qwen2.5:7b",
    "llama3.1:8b"
]

print("🧹 Flushing VRAM...")

for model in MODELS_TO_UNLOAD:
    try:
        # keep_alive: 0 means "unload immediately"
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "keep_alive": 0}
        )
        if response.status_code == 200:
            print(f"✅ Unloaded {model}")
        else:
            print(f"⚠️ Failed to unload {model}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error communicating with Ollama for {model}: {e}")

print("✨ VRAM should be clear.")
