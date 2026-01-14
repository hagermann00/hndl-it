"""
TTS Hotkeys - Middle-click and Ctrl+Alt+Win to speak selected text
Integrates with Windows native TTS via clipboard capture.
"""
import keyboard
import mouse
import pyperclip
import time
import threading
import logging

logger = logging.getLogger("hndl-it.tts-hotkeys")

# Import local TTS (pyttsx3)
try:
    from shared.voice_output import speak as local_speak
    LOCAL_TTS = True
except ImportError:
    LOCAL_TTS = False
    logger.warning("Local TTS (pyttsx3) not available, using Windows native only")


def get_selected_text() -> str:
    """Copy selected text to clipboard and return it."""
    # Save current clipboard
    old_clipboard = ""
    try:
        old_clipboard = pyperclip.paste()
    except:
        pass
    
    # Send Ctrl+C to copy selection
    keyboard.send("ctrl+c")
    time.sleep(0.1)  # Brief delay for clipboard
    
    # Get new clipboard content
    try:
        text = pyperclip.paste()
        if text == old_clipboard:
            return ""  # Nothing new selected
        return text.strip()
    except:
        return ""
    finally:
        # Optionally restore clipboard (commented out as it may interfere)
        # pyperclip.copy(old_clipboard)
        pass


def speak_selected():
    """Speak the currently selected text."""
    text = get_selected_text()
    if text:
        logger.info(f"🔊 Speaking: {text[:50]}...")
        if LOCAL_TTS:
            local_speak(text)
        else:
            # Fallback: Use Windows SAPI via PowerShell
            import subprocess
            safe_text = text.replace('"', "'").replace('\n', ' ')
            subprocess.Popen(
                ["powershell", "-Command", f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_text}")'],
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
    else:
        logger.debug("No text selected")


def on_middle_click():
    """Handle middle mouse click - speak selected text."""
    # Use threading to avoid blocking mouse events
    threading.Thread(target=speak_selected, daemon=True).start()


def register_tts_hotkeys():
    """Register all TTS hotkeys."""
    try:
        # Middle mouse click to speak selected text
        mouse.on_middle_click(on_middle_click)
        logger.info("✅ Middle-click TTS registered")
        
        # Ctrl+Alt+Win to speak selected text (in addition to Win+H passthrough)
        # Note: This supplements the existing Win+H passthrough in launch_suite.py
        keyboard.add_hotkey("ctrl+alt+windows", speak_selected)
        logger.info("✅ Ctrl+Alt+Win TTS registered")
        
        return True
    except Exception as e:
        logger.error(f"Failed to register TTS hotkeys: {e}")
        return False


def unregister_tts_hotkeys():
    """Cleanup hotkeys."""
    try:
        mouse.unhook_all()
        keyboard.remove_hotkey("ctrl+alt+windows")
    except:
        pass


if __name__ == "__main__":
    # Standalone test
    logging.basicConfig(level=logging.INFO)
    print("TTS Hotkeys Active:")
    print("  • Middle-click: Speak selected text")
    print("  • Ctrl+Alt+Win: Speak selected text")
    print("\nPress Ctrl+C to exit...")
    
    register_tts_hotkeys()
    
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nExiting...")
        unregister_tts_hotkeys()
