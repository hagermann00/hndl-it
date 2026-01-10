"""
todo-it Overlay Widget
Floating icon for todo-it module, similar to hndl-it overlay.
"""

import sys
import os
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen

# Colors matching hndl-it theme
COLORS = {
    'bg_dark': '#1a1a2e',
    'primary': '#e67e22',  # Orange
    'secondary': '#00d4ff',  # Cyan
    'accent': '#00ff88',  # Green
}

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')


class TodoOverlay(QWidget):
    """Floating todo-it icon widget."""
    
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(60, 60)
        
        self._dragging = False
        self._drag_start = QPoint()
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Try to load icon
        icon_path = os.path.join(ASSETS_DIR, 'todo_it_icon.png')
        if os.path.exists(icon_path):
            self.icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.icon_label)
        else:
            # Fallback text
            self.icon_label = QLabel("📝")
            self.icon_label.setStyleSheet(f"font-size: 32px; color: {COLORS['primary']};")
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.icon_label)
    
    def paintEvent(self, event):
        """Draw border ring."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Outer ring
        pen = QPen(QColor(COLORS['primary']))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(2, 2, 56, 56)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_start)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                # Check if it was a click (minimal movement)
                if (event.globalPosition().toPoint() - self._drag_start - self.pos()).manhattanLength() < 5:
                    self.clicked.emit()
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu, QApplication
        from PyQt6.QtGui import QAction
        menu = QMenu(self)
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(close_action)
        
        menu.exec(event.globalPos())


# Standalone launcher
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = TodoOverlay()
    overlay.show()
    overlay.move(1820, 240)  # Below hndl-it
    
    # Import and connect to panel
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from main import TodoItApp
    
    todo_app = TodoItApp()
    
    overlay.clicked.connect(lambda: todo_app.panel.show() or todo_app.panel.raise_())
    overlay.double_clicked.connect(lambda: todo_app.show_quick_input(overlay.x() - 310, overlay.y()))
    
    sys.exit(app.exec())
