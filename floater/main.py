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
    overlay.move(screen_geo.width() - 100, 100)
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
            y = geo.top()
            
            # Clamp logic (simple)
            if x < 0: x = geo.right() + 10
            
            tray.quick_dialog.move(x, y)
            tray.quick_dialog.show()
            tray.quick_dialog.activateWindow()
            tray.quick_dialog.raise_()
            tray.quick_dialog.input.setFocus()
            
    overlay.clicked.connect(toggle_input)
    overlay.double_clicked.connect(lambda: console.show() or console.raise_() or console.activateWindow())
    
    logger.info("Floater UI initialized. Overlay and Tray active.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
