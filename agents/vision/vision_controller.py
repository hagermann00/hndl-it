import os
import time
import logging
import base64
import io
import mss
import mss.tools
import ollama
from PIL import Image

logger = logging.getLogger("VisionController")

class VisionController:
    def __init__(self, model="llava-llama3"):
        self.model = model
        self.sct = mss.mss()
        self.monitors = self.sct.monitors
        # monitor[0] is all, monitor[1] is primary
    
    def check_model_availability(self) -> bool:
        """Checks if the configured model is available in Ollama."""
        try:
            models = ollama.list()
            # Handle both object and dict return types from ollama library
            model_names = []
            if hasattr(models, 'models'): # Object form
                model_names = [m.model for m in models.models]
            elif isinstance(models, dict) and 'models' in models: # Dict form
                model_names = [m['name'] for m in models['models']]
            else:
                 # Fallback/Direct list?
                 model_names = [str(m) for m in models]

            logger.info(f"Available Ollama models: {model_names}")
            
            # loose matching
            is_available = any(self.model in name for name in model_names)
            return is_available
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False

    def capture_screen(self, monitor_idx=1) -> str:
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
                image_b64 = self.capture_screen()
                
            logger.info(f"Sending request to Ollama ({self.model})... Prompt: {prompt}")
            
            # Ollama Python library sync call (blocking), might want to wrap in run_in_executor if heavy
            # For now keeping it simple or using async if library supports it (it handles valid async?)
            # The official python library is synchronous for chat/generate usually, but let's check.
            # We'll run it in a thread to be safe for asyncio loop.
            
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
