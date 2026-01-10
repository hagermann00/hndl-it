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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--y", type=int, default=170)
    args, _ = parser.parse_known_args()

    logger.info("Starting hndl-it Floater UI...")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Console
    console = ConsoleWindow()
    
    # Add Console Handler
    gui_handler = GuiLogHandler(console)
    gui_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(gui_handler)
    
    # 1. Tray Icon
    tray = FloaterTray(app)
    tray.console_window = console
    
    # 2. Overlay Widget
    overlay = OverlayWidget()
    
    # Position
    screen_geo = app.primaryScreen().availableGeometry()
    overlay.move(screen_geo.width() - 80, args.y)
    overlay.show()
    
    # Wiring
    def toggle_input():
        if tray.quick_dialog.isVisible():
            tray.quick_dialog.hide()
        else:
            geo = overlay.geometry()
            # Up and to the left
            x = geo.left() - tray.quick_dialog.width() - 10
            y = geo.top() - 150
            
            if x < 0: x = geo.right() + 10
            
            tray.quick_dialog.move(x, y)
            tray.quick_dialog.show()
            tray.quick_dialog.activateWindow()
            tray.quick_dialog.raise_()
            tray.quick_dialog.input.setFocus()
            
    overlay.clicked.connect(toggle_input)
    overlay.double_clicked.connect(lambda: console.show() or console.raise_() or console.activateWindow())
    
    # IPC Listener
    from PyQt6.QtCore import QTimer
    ipc_timer = QTimer()
    
    def check_ipc_handler():
        try:
            from shared.ipc import check_mailbox
            action, payload = check_mailbox("hndl")
            if action:
                if action == "input":
                    text = payload.get("text")
                    # Set text and show
                    tray.quick_dialog.input.setText(text)
                    if not tray.quick_dialog.isVisible():
                         toggle_input()
        except Exception:
            pass

    ipc_timer.timeout.connect(check_ipc_handler)
    ipc_timer.start(1000)
    
    logger.info("Floater UI initialized. Listening on IPC 'hndl'.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
