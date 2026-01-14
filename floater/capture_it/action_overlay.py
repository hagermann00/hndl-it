from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QBuffer, QByteArray, QIODevice
from PyQt6.QtGui import QPixmap, QIcon, QCursor
import base64
import io

class ActionOverlay(QWidget):
    """
    Floating overlay that appears after a capture.
    Provides options: Analyze, Resale, Save, etc.
    """
    action_selected = pyqtSignal(str, object) # action_type, payload

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Main Frame
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 30, 0.95);
                border: 2px solid #00d4ff;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #2a2a3e;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #00d4ff;
                color: black;
            }
            QLabel {
                color: #aaa;
                font-size: 12px;
                font-weight: bold;
                padding-bottom: 5px;
            }
        """)

        self.frame_layout = QVBoxLayout(self.frame)
        self.layout.addWidget(self.frame)

        # Header
        lbl = QLabel("CAPTURE ACTION")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addWidget(lbl)

        # Buttons
        self.add_btn("🧠 Explain / Analyze", "explain")
        self.add_btn("💰 Resale / Comps", "resale")
        self.add_btn("💾 Save to Inbox", "save")
        self.add_btn("❌ Discard", "discard")

        # Auto-close timer (optional, or close on click)

    def add_btn(self, text, action_code):
        btn = QPushButton(text)
        btn.clicked.connect(lambda: self.handle_click(action_code))
        self.frame_layout.addWidget(btn)

    def handle_click(self, action):
        if action == "discard":
            self.close()
            return

        payload = {}
        if action in ["explain", "resale"]:
            # Convert pixmap to base64 using QBuffer
            ba = QByteArray()
            buff = QBuffer(ba)
            buff.open(QIODevice.OpenModeFlag.WriteOnly)
            self.pixmap.save(buff, "PNG")
            b64_str = base64.b64encode(ba.data()).decode("utf-8")
            payload["image"] = b64_str

        self.action_selected.emit(action, payload)
        self.close()
