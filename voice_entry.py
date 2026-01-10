import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QPixmap
from PyQt6.QtCore import Qt, QRect

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from shared.voice_input import init_voice_input, VOICE_AVAILABLE
from shared.voice_router import parse_voice_command, VoiceTarget
from shared.ipc import send_command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-it")

class VoiceIcon(QWidget):
    def __init__(self, icon_path):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(60, 60)
        self.icon_path = icon_path
        self.border_color = "#ff00ff"
        self._drag_pos = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Circle bg
        painter.setBrush(QBrush(QColor(20, 20, 20, 240)))
        painter.setPen(QPen(QColor(self.border_color), 2))
        painter.drawEllipse(2, 2, 56, 56)
        
        # Icon
        if os.path.exists(self.icon_path):
            target = QRect(10, 10, 40, 40)
            painter.drawPixmap(target, QPixmap(self.icon_path))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'on_click') and self._drag_pos:
             # Simple click detection (if didn't move much?)
             # For now just trigger
             self.on_click()
        self._drag_pos = None

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--y", type=int, default=530)
    args, _ = parser.parse_known_args()
    
    app = QApplication(sys.argv)
    
    # Locate icon
    icon_path = os.path.join(PROJECT_ROOT, "floater", "assets", "voice_it_icon.png")
    icon = VoiceIcon(icon_path)
    
    screen = app.primaryScreen().availableGeometry()
    
    # Position
    icon.move(screen.width() - 80, args.y)
    icon.show()
    
    # Voice Logic
    if VOICE_AVAILABLE:
        def handle_voice(text):
            logger.info(f"🎤 Voice: {text}")
            result = parse_voice_command(text)
            target = result["target"]
            
            logger.info(f"Routing to: {target}")
            
            if target == VoiceTarget.TODO_IT:
                send_command("todo", "add_todo", {"text": result.get("todo_text", text)})
            elif target == VoiceTarget.READ_IT:
                # Send to read-it
                send_command("read", "read_text", {"text": text}) # Simplified
            else:
                 # Route to hndl-it
                 send_command("hndl", "input", {"text": text})

        def handle_listening(is_listening):
            icon.border_color = "#ff0000" if is_listening else "#ff00ff"
            icon.update()
            
        vi = init_voice_input(handle_voice, handle_listening)
        
        # Link click
        icon.on_click = lambda: vi.cancel_listening() if vi.is_listening else vi._on_hotkey_pressed()
        
        # Native Hotkey Logic (Ctrl+Win+Alt -> Win+H)
        try:
            import keyboard
            keyboard.add_hotkey("ctrl+windows+alt", lambda: keyboard.send("windows+h"))
        except: pass
        
    else:
        logger.warning("Voice unavailable")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
