"""
Read-it IPC Handler
Listens for IPC commands and executes TTS actions.
"""

import sys
import os
import time
import logging

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.ipc import check_mailbox

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hndl-it.read.handler")


class TTSEngine:
    """Simple TTS wrapper."""
    
    def __init__(self):
        self.engine = pyttsx3.init() if TTS_AVAILABLE else None
        if self.engine:
            self.engine.setProperty('rate', 175)  # Words per minute
            voices = self.engine.getProperty('voices')
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
    
    def speak(self, text: str):
        if not self.engine:
            logger.error("TTS engine not available")
            return
        self.engine.say(text)
        self.engine.runAndWait()
    
    def stop(self):
        if self.engine:
            self.engine.stop()


def main():
    """Run read-it IPC handler."""
    logger.info("📖 Read-it Handler starting...")
    
    if not TTS_AVAILABLE:
        logger.error("pyttsx3 not installed! Run: pip install pyttsx3")
        return
    
    tts = TTSEngine()
    
    try:
        while True:
            # Check for commands
            action, payload = check_mailbox("read")
            
            if action:
                logger.info(f"📥 Received: {action} - {payload}")
                
                try:
                    if action in ("speak", "read", "say"):
                        text = payload.get("subject") or payload.get("text") or payload.get("input", "")
                        if text:
                            logger.info(f"🔊 Speaking: {text[:50]}...")
                            tts.speak(text)
                            logger.info("✅ Done speaking")
                        
                    elif action == "summarize":
                        text = payload.get("subject") or payload.get("text") or payload.get("input", "")
                        # Simple summary: first 200 chars
                        summary = text[:200] + "..." if len(text) > 200 else text
                        tts.speak(f"Summary: {summary}")
                        
                    elif action == "stop":
                        tts.stop()
                        logger.info("✅ Stopped speaking")
                        
                    elif action == "quit":
                        logger.info("Shutting down...")
                        break
                        
                    else:
                        logger.warning(f"Unknown action: {action}")
                        
                except Exception as e:
                    logger.error(f"Error executing {action}: {e}")
            
            time.sleep(0.5)  # Poll interval
            
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        logger.info("Read-it Handler stopped")


if __name__ == "__main__":
    main()
