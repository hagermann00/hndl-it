import sys
import os
import logging
from PyQt6.QtWidgets import QApplication

# Add parent dir to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from floater.tray import FloaterTray
from floater.overlay import OverlayWidget
from floater.console import ConsoleWindow
from PyQt6.QtGui import QScreen

# Voice and routing imports
try:
    from shared.voice_input import init_voice_input, VoiceInput, VOICE_AVAILABLE
    from shared.voice_router import parse_voice_command, VoiceTarget
except ImportError:
    VOICE_AVAILABLE = False
    print("Voice modules not available")

# Todo-it import
try:
    from importlib import import_module
    TODO_AVAILABLE = True
except:
    TODO_AVAILABLE = False

# Logging Setup
# Custom Handler to route logs to ConsoleWindow
class GuiLogHandler(logging.Handler):
    def __init__(self, console_window):
        super().__init__()
        self.console = console_window
        
    def emit(self, record):
        msg = self.format(record)
        # Thread safety in Qt? logging is thread-safe, but UI updates must be main thread.
        # For simplicity in this specific setup (logging from main thread mostly), we'll direct call.
        # ideally use signals.
        from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
        QMetaObject.invokeMethod(self.console.text_edit, "append", Qt.ConnectionType.QueuedConnection, Q_ARG(str, msg))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hndl-it.floater")

def main():
    logger.info("Starting hndl-it Floater UI...")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Important for tray apps
    
    # Console
    console = ConsoleWindow()
    
    # Add Console Handler
    gui_handler = GuiLogHandler(console)
    gui_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(gui_handler)
    
    # 1. Tray Icon (Logic Hub + Backup UI)
    tray = FloaterTray(app)
    # Give tray access to console for its menu
    tray.console_window = console
    
    # 2. Overlay Widget (The "Dock")
    overlay = OverlayWidget()
    
    # Initial Position: Top-Rightish
    screen_geo = app.primaryScreen().availableGeometry()
    overlay.move(screen_geo.width() - 100, 170)
    overlay.show()
    
    # Wiring
    def toggle_input():
        if tray.quick_dialog.isVisible():
            tray.quick_dialog.hide()
        else:
            # Position near overlay
            geo = overlay.geometry()
            # Place to left of overlay
            x = geo.left() - tray.quick_dialog.width() - 10
            y = geo.top() + 200
            
            # Clamp logic (simple)
            if x < 0: x = geo.right() + 10
            
            tray.quick_dialog.move(x, y)
            tray.quick_dialog.show()
            tray.quick_dialog.activateWindow()
            tray.quick_dialog.raise_()
            tray.quick_dialog.input.setFocus()
            
    overlay.clicked.connect(toggle_input)
    overlay.double_clicked.connect(lambda: console.show() or console.raise_() or console.activateWindow())
    
    # 3. Voice Input System (Win+Alt hotkey)
    todo_app = None
    
    def handle_voice_result(text: str):
        """Route voice command to appropriate module."""
        nonlocal todo_app
        logger.info(f"Voice input: {text}")
        
        if VOICE_AVAILABLE:
            result = parse_voice_command(text)
            target = result["target"]
            
            if target == VoiceTarget.TODO_IT:
                # Route to todo-it
                logger.info(f"Routing to todo-it: {result.get('todo_text', text)}")
                if todo_app is None:
                    try:
                        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'todo-it'))
                        from main import TodoItApp
                        todo_app = TodoItApp()
                    except Exception as e:
                        logger.error(f"Failed to load todo-it: {e}")
                
                if todo_app:
                    todo_app.panel.add_todo(result.get('todo_text', text))
                    todo_app.panel.show()
                    
            elif target == VoiceTarget.READ_IT:
                # Route to read-it (future)
                logger.info(f"Would route to read-it: {result['command']}")
                
            elif target == VoiceTarget.BROWSER:
                # Route to browser agent
                logger.info(f"Would route to browser: {result['command']}")
                tray.quick_dialog.input.setText(result['command'])
                toggle_input()
                
            else:
                # Default: show in hndl-it input
                tray.quick_dialog.input.setText(text)
                toggle_input()
        else:
            # No routing, just put in input
            tray.quick_dialog.input.setText(text)
            toggle_input()
    
    def handle_listening_state(is_listening: bool):
        """Update UI when listening state changes."""
        if is_listening:
            logger.info("🎤 Listening...")
            # Could add visual feedback on overlay here
        else:
            logger.info("🔇 Stopped listening")
    
    # Initialize voice input
    if VOICE_AVAILABLE:
        try:
            voice = init_voice_input(handle_voice_result, handle_listening_state)
            logger.info("Voice input ready. Press WIN+ALT to speak.")
        except Exception as e:
            logger.warning(f"Voice input failed to initialize: {e}")
    
    logger.info("Floater UI initialized. Overlay and Tray active.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
