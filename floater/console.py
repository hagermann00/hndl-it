import logging
from PyQt6.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

logger = logging.getLogger("hndl-it.floater.console")

class ConsoleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hndl-it Console")
        self.resize(800, 600)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #ccc; }
            QTextEdit { background-color: #252525; color: #00ff00; font-family: Consolas; font-size: 12px; border: none; }
        """)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.text_edit)
        
        self.setCentralWidget(central)
        
    def log(self, message):
        self.text_edit.append(message)
        # Auto scroll
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())
