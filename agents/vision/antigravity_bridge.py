"""
Antigravity Vision Bridge v6 - THE KILLER FIX
Handles: DPI Trap + Bandwidth Trap + Coordinate Math
"""

import ctypes
import pyautogui
import time
import os
import base64
import requests
import glob
import io
from pathlib import Path
from PIL import Image, ImageGrab

# === 1. THE DPI FIX (Crucial for Windows) ===
try:
    ctypes.windll.user32.SetProcessDPIAware()
    print("✅ DPI Awareness enabled")
except Exception:
    pass

# === 2. THE COORDINATE SYSTEM ===
REAL_WIDTH, REAL_HEIGHT = pyautogui.size()
AI_VIEW_WIDTH = 1024
AI_VIEW_HEIGHT = 768

print(f"🖥️  Real Screen: {REAL_WIDTH}x{REAL_HEIGHT}")
print(f"👁️  AI View: {AI_VIEW_WIDTH}x{AI_VIEW_HEIGHT}")

SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"
OUTPUT_FILE = Path("C:/IIWII_DB/hndl-it/logs/vision_result.txt")

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def take_screenshot_fixed():
    """Take DPI-aware screenshot and compress for AI"""
    log("📸 Taking DPI-aware screenshot...")
    
    # Capture full REAL screen (DPI fix is already applied)
    screenshot = ImageGrab.grab(all_screens=False)
    original_size = screenshot.size
    log(f"   Original: {original_size}")
    
    # Resize for AI (fixed size that works well)
    screenshot = screenshot.resize((AI_VIEW_WIDTH, AI_VIEW_HEIGHT))
    log(f"   Resized: {screenshot.size}")
    
    # Convert to RGB and compress as JPEG (quality=60 = ~50KB)
    buffered = io.BytesIO()
    screenshot.convert("RGB").save(buffered, format="JPEG", quality=60)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    log(f"   Compressed: {len(img_base64):,} chars (~{len(img_base64)//1024}KB)")
    
    return img_base64

def analyze_with_ollama(image_base64, prompt):
    """Send to local LLaVA"""
    log("🧠 Sending to LLaVA...")
    
    payload = {
        "model": "moondream",  # Smaller, more stable vision model
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "options": {"num_predict": 500}
    }
    
    start = time.time()
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=180
        )
        
        elapsed = time.time() - start
        log(f"   Response in {elapsed:.1f}s, status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"   Full response keys: {data.keys()}")
            result = data.get("response", "")
            if not result:
                log(f"   DEBUG: {str(data)[:500]}")
            return result if result else "No text in response"
        else:
            err = response.json().get("error", response.text[:300])
            return f"Error: {err}"
                
    except Exception as e:
        return f"Error: {e}"

def main():
    OUTPUT_FILE.write_text("ANTIGRAVITY VISION BRIDGE v6\n" + "="*50 + "\n", encoding='utf-8')
    
    log("Cloud AI + Local Vision = $0 API Cost")
    log("="*50)
    
    # Take DPI-fixed, compressed screenshot
    image_base64 = take_screenshot_fixed()
    
    # Test "Execution" capability - getting coordinates
    prompt = "point to the grok browser tab"
    log(f"Prompt: {prompt}")

    result = analyze_with_ollama(image_base64, prompt)
    
    log("\n" + "="*50)
    log("DESKTOP ICONS I SEE:")
    log("="*50)
    log(result)
    log("="*50)
    log("$0 cloud API cost - 100% local vision!")

if __name__ == "__main__":
    main()
