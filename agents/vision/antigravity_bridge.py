"""
Antigravity Vision Bridge v5
Resizes image to fit in VRAM
"""

import pyautogui
import time
import os
import base64
import requests
import glob
import io
from pathlib import Path
from PIL import Image

SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"
OUTPUT_FILE = Path("C:/IIWII_DB/hndl-it/vision_result.txt")

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def get_latest_screenshot():
    pattern = str(SCREENSHOTS_DIR / "*.png")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def take_and_resize_screenshot():
    """Take screenshot and resize for VRAM efficiency"""
    log("Taking screenshot with Win+PrtSc...")
    
    before = set(glob.glob(str(SCREENSHOTS_DIR / "*.png")))
    pyautogui.hotkey('win', 'printscreen')
    time.sleep(2)
    after = set(glob.glob(str(SCREENSHOTS_DIR / "*.png")))
    new_files = after - before
    
    screenshot_path = list(new_files)[0] if new_files else get_latest_screenshot()
    
    if not screenshot_path:
        return None
        
    log(f"Screenshot: {screenshot_path}")
    
    # Open and resize to fit in VRAM (max 1024x768)
    img = Image.open(screenshot_path)
    original_size = img.size
    
    # Resize to max 512px width for VRAM (model uses ~6GB, image processing needs room)
    max_width = 512
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    log(f"Original: {original_size}, Resized: {img.size}")
    
    # Convert to grayscale (much smaller, still readable)
    img = img.convert('L')
    log("Converted to grayscale")
    
    # Convert to base64 (PNG)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    log(f"Encoded size: {len(img_base64):,} chars (vs 1.8M before)")
    
    return img_base64

def analyze_with_ollama(image_base64, prompt):
    log("Sending to LLaVA...")
    
    payload = {
        "model": "llava-llama3",
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
            timeout=300
        )
        
        elapsed = time.time() - start
        log(f"Response in {elapsed:.1f}s, status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json().get("response", "No response")
        else:
            err = response.json().get("error", response.text[:200])
            return f"Error: {err}"
                
    except Exception as e:
        return f"Error: {e}"

def main():
    OUTPUT_FILE.write_text("ANTIGRAVITY VISION BRIDGE\n" + "="*50 + "\n", encoding='utf-8')
    
    log("Cloud AI + Local Vision = $0 API Cost")
    log("="*50)
    
    # Take and resize screenshot
    image_base64 = take_and_resize_screenshot()
    
    if not image_base64:
        log("Failed to capture screenshot")
        return
    
    prompt = """Look at this Windows desktop screenshot.
List every desktop icon you can see.
For each: state the icon name and what application it represents."""

    result = analyze_with_ollama(image_base64, prompt)
    
    log("\n" + "="*50)
    log("DESKTOP ICONS I SEE:")
    log("="*50)
    log(result)
    log("="*50)
    log("$0 cloud API cost - 100% local vision!")

if __name__ == "__main__":
    main()
