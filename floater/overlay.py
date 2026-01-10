import logging
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QCursor

logger = logging.getLogger("hndl-it.floater.overlay")

class OverlayWidget(QWidget):
    """
    A persistent, always-on-top floating icon.
    - Click: Toggle input
    - Double Click: Toggle Logs/Console
    - Drag: Move
    """
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
        
        self.size_val = 60
        self.setFixedSize(self.size_val, self.size_val)
        
        # State
        self._drag_pos = QPoint()
        self._dragging = False
        
        # Initial Position (Bottom Rightish)
        # We can't easily guess screen geometry here easily without app ref, 
        # so let main set logic or default to 100,100
        self.move(100, 100) 
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Try to load icon (Prefer jpg, then png)
        import os
        from PyQt6.QtGui import QPixmap, QPainterPath
        
        icon_path = ""
        possible_icons = ["icon.jpg", "icon.png"]
        for fname in possible_icons:
            path = os.path.join(os.path.dirname(__file__), "assets", fname)
            if os.path.exists(path):
                icon_path = path
                break
        
        if icon_path:
            pixmap = QPixmap(icon_path)
            
            # Draw Circular Clipped Icon
            path = QPainterPath()
            path.addEllipse(0, 0, self.width(), self.height())
            painter.setClipPath(path)
            
            # Draw user image
            painter.drawPixmap(self.rect(), pixmap)
            
            # Draw border over it again for crispness
            painter.setClipping(False) # Turn off clipping for border
            pen = QPen(QColor("#007acc"))
            pen.setWidth(3)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawEllipse(3, 3, self.width()-6, self.height()-6)
            
        else:
            # Fallback to Gradient Circle
            gradient = QRadialGradient(self.rect().center(), self.width() / 2)
            gradient.setColorAt(0, QColor("#333333"))
            gradient.setColorAt(1, QColor("#111111"))
            
            painter.setBrush(QBrush(gradient))
            
            # Border
            pen = QPen(QColor("#007acc")) # Blue accent
            pen.setWidth(3)
            painter.setPen(pen)
            
            # Draw Circle
            rect = QRectF(3, 3, self.width()-6, self.height()-6)
            painter.drawEllipse(rect)
            
            # Draw "H"
            painter.setPen(QColor("#ffffff"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "H")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        was_drag = False
        if self._dragging:
            # Check if mouse actually moved (drag vs click)
            current_pos = event.globalPosition().toPoint()
            start_pos = self.frameGeometry().topLeft() + self._drag_pos
            if (current_pos - start_pos).manhattanLength() > 5:
                was_drag = True
            self._dragging = False
        
        # Only emit clicked if it wasn't a drag
        if not was_drag:
            self.clicked.emit()

    def mouseDoubleClickEvent(self, event):
        # Override the single click? 
        self.double_clicked.emit()
