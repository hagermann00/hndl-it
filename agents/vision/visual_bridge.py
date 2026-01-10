"""
Antigravity Visual MCP Bridge
Architecture: Local Eyes (Moondream) -> Cloud Brain (Antigravity) -> Local Hands (Python)

This module provides the "Eyes" and "Hands" for the cloud agent.
"""

import ctypes
import pyautogui
import time
import base64
import os
import requests
import io
import json
from pathlib import Path
from PIL import Image, ImageGrab

# === CONFIGURATION ===
OLLAMA_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "moondream"  # Eye
AI_VIEW_WIDTH = 1024        # Resolution Cloud Brain expects
AI_VIEW_HEIGHT = 768

# === 1. DPI AWARENESS (The "Killer" Fix) ===
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# === 2. REALITY MAPPING ===
REAL_WIDTH, REAL_HEIGHT = pyautogui.size()
SCALE_X = REAL_WIDTH / AI_VIEW_WIDTH
SCALE_Y = REAL_HEIGHT / AI_VIEW_HEIGHT

class VisualBridge:
    """The local bridge that gives the Cloud Agent sight and action."""
    
    @staticmethod
    def get_sight():
        """
        Captures reality, compresses it, and asks Local Vision (Moondream) 
        to describe it for the Cloud Brain.
        """
        # 1. Capture
        screenshot = ImageGrab.grab(all_screens=False)
        
        # 2. Resize/Compress for Local Vision Model
        ai_view = screenshot.resize((AI_VIEW_WIDTH, AI_VIEW_HEIGHT))
        
        buffered = io.BytesIO()
        ai_view.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 3. Ask Moondream to process (Heavy lifting on Local GPU)
        prompt = "Describe this screen. List active windows, icons, and text."
        description = VisualBridge._query_ollama(img_base64, prompt)
        
        return {
            "vision_summary": description,
            "real_resolution": f"{REAL_WIDTH}x{REAL_HEIGHT}",
            "ai_resolution": f"{AI_VIEW_WIDTH}x{AI_VIEW_HEIGHT}"
        }

    @staticmethod
    def _query_ollama(image_base64, prompt):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": VISION_MODEL,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False,
                    "options": {"num_predict": 300} # Fast responses
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            return f"Error: Vision Blind (Status {response.status_code})"
        except Exception as e:
            return f"Error: Vision Blind ({str(e)})"

    @staticmethod
    def execute_click(ai_x, ai_y, button="left", double=False):
        """Executes a click based on AI coordinates (0-1024 space)."""
        real_x = int(ai_x * SCALE_X)
        real_y = int(ai_y * SCALE_Y)
        
        pyautogui.moveTo(real_x, real_y, duration=0.2)
        
        if double:
            pyautogui.doubleClick(button=button)
        else:
            pyautogui.click(button=button)
            
        return f"Clicked at real coords ({real_x}, {real_y})"

# === TEST HARNESS ===
def test():
    print("=== VISUAL BRIDGE DIAGNOSTICS ===")
    print(f"Monitor: {REAL_WIDTH}x{REAL_HEIGHT}")
    print(f"Scale: {SCALE_X:.2f}, {SCALE_Y:.2f}")
    
    print("\n1. Testing Sight (Moondream)...")
    sight = VisualBridge.get_sight()
    print(f"   Vision: {sight['vision_summary']}")

if __name__ == "__main__":
    test()
