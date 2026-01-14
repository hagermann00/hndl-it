from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QPixmap, QPainterPath

class AntigravityFloater(QWidget):
    """
    IMMUTABLE REFERENCE for Antigravity Floating Icons.
    
    STANDARD V2 (2026):
    - Size: 70x70 pixels
    - Shape: Circular
    - Border: 3px Solid
    - Behavior: Draggable, Always On Top
    """
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    
    def __init__(self, icon_path: str = None, fallback_letter: str = "?", border_color: str = "#e67e22"):
        super().__init__()
        
        # Standard Window Flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # STANDARD SIZE: 70px
        self.size_val = 70
        self.setFixedSize(self.size_val, self.size_val)
        
        self.icon_path = icon_path
        self.fallback_letter = fallback_letter
        self.border_color = border_color
        
        self._drag_pos = QPoint()
        self._dragging = False
        self._drag_started = False
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.icon_path and self._icon_exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            
            # Draw circular clipped icon
            path = QPainterPath()
            path.addEllipse(0.0, 0.0, float(self.width()), float(self.height()))
            painter.setClipPath(path)
            painter.drawPixmap(self.rect(), pixmap)
            
            # Draw border
            painter.setClipping(False)
            pen = QPen(QColor(self.border_color))
            pen.setWidth(3)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawEllipse(3, 3, self.width()-6, self.height()-6)
        else:
            # Fallback gradient circle
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            gradient = QRadialGradient(cx, cy, self.width() / 2.0)
            gradient.setColorAt(0, QColor("#1a1a2e"))
            gradient.setColorAt(1, QColor("#0a0a1a"))
            
            painter.setBrush(QBrush(gradient))
            pen = QPen(QColor(self.border_color))
            pen.setWidth(3)
            painter.setPen(pen)
            
            rect = QRectF(3, 3, self.width()-6, self.height()-6)
            painter.drawEllipse(rect)
            
            painter.setPen(QColor("#ffffff"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(20) # Slightly larger font for 70px
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.fallback_letter)
            
    def _icon_exists(self, path):
        import os
        if not path: return False
        return os.path.exists(path)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True
            self._drag_started = False
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._drag_started = True
    
    def mouseReleaseEvent(self, event):
        if self._dragging and not self._drag_started:
            self.clicked.emit()
        self._dragging = False
    
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
