from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QBrush, QColor
import sys

class TestFloater(QWidget):
    def __init__(self, color, transparent, y_pos):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        if transparent:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setGeometry(1700, y_pos, 100, 100)
        self.color = color
        self.transparent = transparent
        
        lbl = QLabel("TRANS" if transparent else "SOLID", self)
        lbl.move(10, 40)
        lbl.setStyleSheet("color: white; font-weight: bold;")

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.transparent:
            # Draw circle
            painter.setBrush(QBrush(QColor(self.color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, 100, 100)
        else:
            # Draw solid rect
            painter.fillRect(self.rect(), QColor(self.color))

app = QApplication(sys.argv)

# 1. Translucent Green Circle
w1 = TestFloater("#00ff00", True, 300)
w1.show()

# 2. Solid Red Square
w2 = TestFloater("#ff0000", False, 500)
w2.show()

# 3. Translucent Blue at Calculated Pos (1840)
w3 = TestFloater("#0000ff", True, 700)
w3.move(1840, 700)
w3.show()

print("Launching 3 test windows...")
sys.exit(app.exec())
