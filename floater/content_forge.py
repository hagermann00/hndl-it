import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QWidget, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QIcon, QColor

logger = logging.getLogger("hndl-it.floater.content_forge")

class ContentForge(QDialog):
    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("A-G Content Forge")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.expanded_width = 800
        self.expanded_height = 600
        self.setFixedSize(self.expanded_width, self.expanded_height)
        
        self._setup_styles()
        self._setup_ui()
        
        self._drag_pos = QPoint()

    def _setup_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(20, 20, 20, 240);
                border: 2px solid #ff9944;
                border-radius: 12px;
            }
            QLabel#Title {
                color: #ff9944;
                font-weight: bold;
                font-size: 18px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTextEdit {
                background-color: rgba(30, 30, 30, 200);
                border: 1px solid rgba(255, 153, 68, 100);
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-family: 'Consolas', monospace;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 1px solid #ff9944;
            }
            QPushButton {
                background-color: rgba(255, 153, 68, 40);
                color: #ff9944;
                border: 1px solid #ff9944;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 153, 68, 80);
                color: #ffffff;
            }
            #LogArea {
                font-size: 12px;
                color: #aaaaaa;
            }
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)
        
        # Title Bar
        title_layout = QHBoxLayout()
        self.title_label = QLabel("⚒ A-G CONTENT FORGE")
        self.title_label.setObjectName("Title")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30,30)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)
        layout.addLayout(title_layout)
        
        # Main Prompt Area
        layout.addWidget(QLabel("LONG-FORM PROMPT / CONTENT SPEC"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your intensive long-form content instructions here...")
        layout.addWidget(self.prompt_input)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_research = QPushButton("🌐 RESEARCH")
        self.btn_distill = QPushButton("🧠 DISTILL")
        self.btn_forge = QPushButton("🔥 FORGE CONTENT")
        self.btn_narrate = QPushButton("🔊 NARRATE")
        
        btn_layout.addWidget(self.btn_research)
        btn_layout.addWidget(self.btn_distill)
        btn_layout.addWidget(self.btn_forge)
        btn_layout.addWidget(self.btn_narrate)
        layout.addLayout(btn_layout)
        
        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setObjectName("LogArea")
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(150)
        layout.addWidget(self.log_area)
        
        # Connect signals
        self.btn_forge.clicked.connect(self.submit_prompt)

    def submit_prompt(self):
        prompt = self.prompt_input.toPlainText()
        if prompt:
            self.add_log(f"⚡ Forging sequence initiated for {len(prompt)} chars...")
            self.command_submitted.emit(prompt)
            # self.prompt_input.clear()

    def add_log(self, message):
        self.log_area.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

from datetime import datetime
