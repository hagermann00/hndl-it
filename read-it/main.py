import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QClipboard
from PyQt6.QtCore import pyqtSignal, QObject

class ClipboardMonitor(QObject):
    text_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.clipboard.changed.connect(self.on_clipboard_change)
        self.last_clipboard = ""

    def on_clipboard_change(self, mode):
        if mode == QClipboard.Mode.Clipboard:
            self.check_clipboard()

    def check_clipboard(self):
        try:
            text = self.clipboard.text()
            if text and text != self.last_clipboard and len(text.strip()) > 3:
                self.last_clipboard = text
                self.text_selected.emit(text)
        except Exception:
            pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Read-it (Optimized)")
        self.resize(300, 200)

        self.label = QLabel("Monitoring clipboard (Event-driven)...")
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.monitor = ClipboardMonitor()
        self.monitor.text_selected.connect(self.on_text_selected)

    def on_text_selected(self, text):
        self.label.setText(f"Detected: {text[:20]}...")
        print(f"DEBUG: Selected text: {text[:50]}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
