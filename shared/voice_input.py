"""
Voice Input Module for hndl-it
Global hotkey (Win+Alt) triggers speech-to-text, routes to hndl-it.
"""

import threading
import time
import queue
from typing import Callable, Optional

try:
    import keyboard
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("Voice dependencies not installed. Run: pip install SpeechRecognition pyaudio keyboard")


class VoiceInput:
    """Global voice input handler with hotkey trigger."""
    
    HOTKEY = "win+alt"  # hndl-it voice trigger
    SILENCE_TIMEOUT = 2.0  # seconds of silence to auto-submit
    PHRASE_TIMEOUT = 10.0  # max recording time
    
    def __init__(self, on_result: Callable[[str], None], on_listening: Callable[[bool], None] = None):
        """
        Args:
            on_result: Callback with transcribed text
            on_listening: Callback when listening state changes (for UI feedback)
        """
        self.on_result = on_result
        self.on_listening = on_listening or (lambda x: None)
        self.recognizer = sr.Recognizer() if VOICE_AVAILABLE else None
        self.microphone = None
        self.is_listening = False
        self._stop_event = threading.Event()
        self._hotkey_registered = False
        
        # Adjust for ambient noise on init
        if self.recognizer:
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = self.SILENCE_TIMEOUT
    
    def start(self):
        """Register global hotkey and start listening for triggers."""
        if not VOICE_AVAILABLE:
            print("Voice input not available - dependencies missing")
            return False
        
        if self._hotkey_registered:
            return True
            
        try:
            keyboard.add_hotkey(self.HOTKEY, self._on_hotkey_pressed)
            self._hotkey_registered = True
            print(f"Voice input ready. Press {self.HOTKEY.upper()} to speak.")
            return True
        except Exception as e:
            print(f"Failed to register hotkey: {e}")
            return False
    
    def stop(self):
        """Unregister hotkey and cleanup."""
        if self._hotkey_registered:
            try:
                keyboard.remove_hotkey(self.HOTKEY)
            except:
                pass
            self._hotkey_registered = False
        self._stop_event.set()
    
    def _on_hotkey_pressed(self):
        """Hotkey triggered - start listening in background thread."""
        if self.is_listening:
            return  # Already listening
        
        thread = threading.Thread(target=self._listen_and_transcribe, daemon=True)
        thread.start()
    
    def _listen_and_transcribe(self):
        """Capture audio and transcribe."""
        if not VOICE_AVAILABLE:
            return
            
        self.is_listening = True
        self.on_listening(True)
        
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                
                # Quick ambient adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                # Listen with timeout
                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=5,  # Wait up to 5s for speech to start
                        phrase_time_limit=self.PHRASE_TIMEOUT
                    )
                except sr.WaitTimeoutError:
                    print("No speech detected")
                    return
                
                print("Processing...")
                
                # Try offline recognition first (Sphinx), fallback to Google
                try:
                    # Sphinx (offline) - faster but less accurate
                    text = self.recognizer.recognize_sphinx(audio)
                except (sr.UnknownValueError, sr.RequestError):
                    try:
                        # Google (online) - more accurate
                        text = self.recognizer.recognize_google(audio)
                    except sr.UnknownValueError:
                        print("Could not understand audio")
                        return
                    except sr.RequestError as e:
                        print(f"Recognition error: {e}")
                        return
                
                if text:
                    print(f"Heard: {text}")
                    self.on_result(text)
                    
        except Exception as e:
            print(f"Voice input error: {e}")
        finally:
            self.is_listening = False
            self.on_listening(False)
    
    def listen_once(self) -> Optional[str]:
        """Synchronous single listen (for testing)."""
        if not VOICE_AVAILABLE:
            return None
            
        with sr.Microphone() as source:
            print("🎤 Listening (sync)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
            
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio)
                return text
            except:
                return None


# Singleton instance for global access
_voice_input: Optional[VoiceInput] = None


def init_voice_input(on_result: Callable[[str], None], on_listening: Callable[[bool], None] = None) -> VoiceInput:
    """Initialize global voice input."""
    global _voice_input
    _voice_input = VoiceInput(on_result, on_listening)
    _voice_input.start()
    return _voice_input


def get_voice_input() -> Optional[VoiceInput]:
    """Get global voice input instance."""
    return _voice_input


# Test
if __name__ == "__main__":
    def on_text(text):
        print(f"RECEIVED: {text}")
    
    def on_listening(is_listening):
        print(f"Listening: {is_listening}")
    
    vi = init_voice_input(on_text, on_listening)
    print("Press Win+Alt to speak, Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        vi.stop()
        print("Stopped")
