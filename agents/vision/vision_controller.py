import os
import time
import logging
import base64
import io
import mss
import mss.tools
import ollama
import ctypes
import pyautogui
from PIL import Image

logger = logging.getLogger("VisionController")

# === DPI AWARENESS ===
# Crucial for Windows to ensure coordinates match reality
try:
    if os.name == 'nt':
        ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

class VisionController:
    """
    Unified Vision Controller
    Consolidates functionality from:
    1. VisionController (mss, ollama)
    2. VisualBridge (DPI fix, Coordinate Scaling, Actions)
    3. AntigravityBridge (ImageGrab, requests)
    """

    def __init__(self, model="llava-llama3"):
        self.model = model
        self.sct = mss.mss()
        self.monitors = self.sct.monitors
        # monitor[0] is all, monitor[1] is primary

        # Coordinate Mapping
        self.real_width, self.real_height = pyautogui.size()
        self.ai_view_width = 1024
        self.ai_view_height = 768
        self.scale_x = self.real_width / self.ai_view_width
        self.scale_y = self.real_height / self.ai_view_height

        logger.info(f"Vision initialized. Screen: {self.real_width}x{self.real_height}, AI View: {self.ai_view_width}x{self.ai_view_height}")

    def check_model_availability(self) -> bool:
        """Checks if the configured model is available in Ollama."""
        try:
            models = ollama.list()
            model_names = []
            if hasattr(models, 'models'): # Object form
                model_names = [m.model for m in models.models]
            elif isinstance(models, dict) and 'models' in models: # Dict form
                model_names = [m['name'] for m in models['models']]
            else:
                 model_names = [str(m) for m in models]

            logger.info(f"Available Ollama models: {model_names}")
            is_available = any(self.model in name for name in model_names)
            return is_available
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False

    def capture_screen(self, monitor_idx=1, resize_for_ai=False) -> str:
        """
        Captures screenshot of specified monitor and returns base64 encoded string.
        """
        try:
            if monitor_idx >= len(self.monitors):
                logger.warning(f"Monitor index {monitor_idx} out of range, using primary (1)")
                monitor_idx = 1
                
            screenshot = self.sct.grab(self.monitors[monitor_idx])
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            if resize_for_ai:
                img = img.resize((self.ai_view_width, self.ai_view_height))

            # Save to buffer
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            
            # Encode
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return img_str
            
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            raise

    async def analyze_image(self, prompt: str, image_b64: str = None) -> str:
        """
        Analyzes the image using Ollama. If no image provided, captures screen.
        """
        try:
            if not image_b64:
                logger.info("No image provided, capturing screen...")
                image_b64 = self.capture_screen(resize_for_ai=True)
                
            logger.info(f"Sending request to Ollama ({self.model})... Prompt: {prompt}")
            
            import asyncio
            loop = asyncio.get_running_loop()
            
            response = await loop.run_in_executor(
                None, 
                lambda: ollama.generate(
                    model=self.model, 
                    prompt=prompt, 
                    images=[image_b64]
                )
            )
            
            result = response.get('response', '')
            logger.info("Ollama response received.")
            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return f"Error analyzing image: {e}"

    def execute_click(self, ai_x: int, ai_y: int, button="left", double=False) -> str:
        """Executes a click based on AI coordinates (0-1024 space)."""
        real_x = int(ai_x * self.scale_x)
        real_y = int(ai_y * self.scale_y)

        logger.info(f"Clicking at AI({ai_x},{ai_y}) -> REAL({real_x},{real_y})")

        pyautogui.moveTo(real_x, real_y, duration=0.2)

        if double:
            pyautogui.doubleClick(button=button)
        else:
            pyautogui.click(button=button)

        return f"Clicked at real coords ({real_x}, {real_y})"
