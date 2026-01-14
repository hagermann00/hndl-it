"""
Voice Output (TTS) Utility for hndl-it
Uses pyttsx3 for offline, low-latency text-to-speech.
"""
import pyttsx3
import threading
import queue
import logging

logger = logging.getLogger("hndl-it.voice-output")

class VoiceOutput:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)  # Speed
        self.engine.setProperty('volume', 0.9)  # Volume
        
        # Set a clear, natural-sounding voice if available
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "Zira" in voice.name or "Hazel" in voice.name:  # Preferred voices
                self.engine.setProperty('voice', voice.id)
                break
        
        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        """Background worker to process speech requests without blocking UI."""
        while not self._stop_event.is_set():
            try:
                text = self.queue.get(timeout=1)
                if text:
                    self.engine.say(text)
                    self.engine.runAndWait()
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS Error: {e}")

    def speak(self, text: str):
        """Add text to the speech queue."""
        if text:
            self.queue.put(text)

    def stop(self):
        """Stop TTS and cleanup."""
        self._stop_event.set()
        self.engine.stop()

# Singleton instance
_instance = None

def get_speaker() -> VoiceOutput:
    global _instance
    if _instance is None:
        _instance = VoiceOutput()
    return _instance

def speak(text: str):
    get_speaker().speak(text)

if __name__ == "__main__":
    # Test
    import time
    speak("This is Hndl-it voice output test. System online.")
    time.sleep(5)
