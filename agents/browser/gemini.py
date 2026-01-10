"""
hndl-it Browser Agent - Gemini Client
Interfaces with Gemini 2.5 Computer Use API
"""

import json
import logging
import os
import asyncio
import base64
from typing import Optional, Any

import google.generativeai as genai

logger = logging.getLogger('hndl-it.gemini')

# System prompt for browser control
SYSTEM_PROMPT = """You are a browser automation assistant. You analyze screenshots of web pages and determine what actions to take based on user commands.

When given a user command and a screenshot, respond with a JSON action object.

Available action types:
1. navigate - Go to a URL
   {"type": "navigate", "url": "https://example.com", "description": "Navigating to example.com"}

2. click - Click an element
   {"type": "click", "text": "Submit", "description": "Clicking the Submit button"}
   {"type": "click", "selector": "#login-btn", "description": "Clicking login button"}
   {"type": "click", "coordinates": {"x": 100, "y": 200}, "description": "Clicking at coordinates"}

3. type - Type text into a field
   {"type": "type", "selector": "input[name='email']", "text": "user@example.com", "description": "Entering email"}
   {"type": "type", "text": "search query", "description": "Typing into focused field"}

4. scroll - Scroll the page
   {"type": "scroll", "direction": "down", "amount": 500, "description": "Scrolling down"}

5. read - Read content from page
   {"type": "read", "selector": "main", "description": "Reading main content"}

6. response - Just respond to user (no browser action needed)
   {"type": "response", "response": "The page shows...", "description": "Describing what I see"}

Rules:
- Always respond with valid JSON
- Include a helpful "description" field
- For clicks, prefer "text" over coordinates when possible
- If you can't determine the action, use response type to ask for clarification
- Be concise in descriptions

Respond ONLY with the JSON action object, no other text."""


class GeminiComputerUse:
    """Client for Gemini 2.5 Computer Use API with key rotation"""
    
    def __init__(self):
        self.model_name = os.getenv("HNDL_MODEL", "gemini-2.0-flash-exp")
        self.api_keys = []
        self.current_key_index = 0
        self._load_api_keys()
        self._configure_api()
        self.model = None
        self._init_model()
    
    def _load_api_keys(self):
        """Load API key hierarchy from shared config"""
        # Path to shared/config.json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "shared", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    # Check for gemini keys in config
                    gemini_config = config.get("gemini", {})
                    key_configs = gemini_config.get("api_keys", [])
                    
                    # If config has keys, load them
                    for key_config in key_configs:
                        env_var = key_config.get("env")
                        if env_var:
                            key = os.getenv(env_var)
                            if key:
                                self.api_keys.append({
                                    "key": key,
                                    "name": key_config.get("name", env_var),
                                    "env": env_var
                                })
            except Exception as e:
                logger.warning(f"Failed to load API keys from config: {e}")
        
        # Fallback: try environment variables directly if no keys loaded from config
        if not self.api_keys:
            for env_var in ["GOOGLE_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEY_2"]:
                key = os.getenv(env_var)
                if key:
                    self.api_keys.append({"key": key, "name": env_var, "env": env_var})
                    logger.info(f"Loaded API key from env: {env_var}")
        
        logger.info(f"Total API keys loaded: {len(self.api_keys)}")
    
    def _configure_api(self):
        """Configure Gemini API with current key"""
        if not self.api_keys:
            logger.warning("No API keys available!")
            return
        
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key["key"])
        logger.info(f"Gemini API configured with: {current_key['name']}")
    
    def _rotate_key(self) -> bool:
        """Rotate to next API key. Returns True if rotation successful."""
        if len(self.api_keys) <= 1:
            logger.warning("No backup API keys available for rotation")
            return False
        
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        new_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=new_key["key"])
        logger.info(f"Rotated API key: {self.api_keys[old_index]['name']} -> {new_key['name']}")
        
        # Re-initialize model with new key
        self._init_model()
        return True
    
    def _init_model(self):
        """Initialize the Gemini model"""
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT
            )
            logger.info(f"Initialized Gemini model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None
    
    async def interpret_command(self, command: str, screenshot_base64: str) -> Optional[dict]:
        """
        Send command and screenshot to Gemini, get action back
        
        Args:
            command: User's natural language command
            screenshot_base64: Base64 encoded PNG screenshot
            
        Returns:
            Action dictionary or None
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return None
        
        try:
            # Decode base64 to bytes for proper image handling
            # model.generate_content accepts base64 string in inline_data, so no need to decode to bytes unless using PIL
            
            # Create image part using genai format
            image_part = {
                "mime_type": "image/png",
                "data": screenshot_base64
            }
            
            # Create prompt
            prompt = f"User command: {command}\n\nAnalyze the screenshot and determine what action to take."
            
            # Call Gemini - wrap sync call in executor for async compatibility
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content([prompt, image_part])
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                return None
            
            # Parse JSON response
            response_text = response.text.strip()
            logger.info(f"Gemini raw response: {response_text[:200]}...")
            
            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines (```json and ```)
                response_text = "\n".join(lines[1:-1])
            
            try:
                action = json.loads(response_text)
                logger.info(f"Gemini action: {action.get('description', action.get('type'))}")
                return action
            except json.JSONDecodeError:
                 # Try to clean up json if it has trailing characters
                 import re
                 json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                 if json_match:
                     action = json.loads(json_match.group(0))
                     return action
                 else:
                     raise

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Try rotation if it's a quote error? (Simplified for now)
            return None
    
    async def describe_page(self, screenshot_base64: str) -> str:
        """Get a description of what's on the page"""
        if not self.model:
            return "Model not available"
        
        try:
            image_part = {
                "mime_type": "image/png",
                "data": screenshot_base64
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content([
                    "Briefly describe what you see on this web page. Focus on the main content and interactive elements.",
                    image_part
                ])
            )
            
            return response.text if response else "Could not describe page"
        
        except Exception as e:
            logger.error(f"Page description failed: {e}")
            return f"Error: {e}"
