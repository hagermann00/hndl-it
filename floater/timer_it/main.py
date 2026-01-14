"""
timer-it: Focus Timer & Pomodoro Module
Plug-and-play module for hndl-it suite.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QTime
from PyQt6.QtGui import QColor, QFont

# Colors
COLORS = {
    'bg': '#1e1e1e',
    'accent': '#ffaa00',  # Orange/Gold
    'text': '#ffffff',
    'dim': '#888888',
    'danger': '#ff4444'
}

class TimerPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 200)

        self.total_time = 25 * 60  # 25 minutes default
        self.time_left = self.total_time
        self.running = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title = QLabel("⏱️ Focus Timer")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(title)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("border: none; color: #888; font-size: 16px;")
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Display
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Consolas", 48, QFont.Weight.Bold))
        layout.addWidget(self.time_label)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, self.total_time)
        self.progress.setValue(self.total_time)
        layout.addWidget(self.progress)

        # Controls
        controls = QHBoxLayout()

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.toggle_timer)
        controls.addWidget(self.start_btn)

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.clicked.connect(self.reset_timer)
        controls.addWidget(self.reset_btn)

        layout.addLayout(controls)

        # Modes
        modes = QHBoxLayout()
        btn_25 = QPushButton("25m")
        btn_25.clicked.connect(lambda: self.set_duration(25))
        modes.addWidget(btn_25)

        btn_5 = QPushButton("5m")
        btn_5.clicked.connect(lambda: self.set_duration(5))
        modes.addWidget(btn_5)

        btn_15 = QPushButton("15m")
        btn_15.clicked.connect(lambda: self.set_duration(15))
        modes.addWidget(btn_15)

        layout.addLayout(modes)

    def apply_styles(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg']};
                border: 2px solid {COLORS['accent']};
                border-radius: 15px;
                color: {COLORS['text']};
            }}
            QLabel {{ color: {COLORS['text']}; }}
            QPushButton {{
                background-color: #333;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }}
            QPushButton:hover {{ background-color: #444; }}
            QProgressBar {{
                border: none;
                background-color: #333;
                height: 4px;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 2px;
            }}
        """)

    def set_duration(self, minutes):
        self.total_time = minutes * 60
        self.reset_timer()

    def reset_timer(self):
        self.running = False
        self.timer.stop()
        self.time_left = self.total_time
        self.update_display()
        self.start_btn.setText("▶ Start")
        self.progress.setValue(self.total_time)
        self.progress.setRange(0, self.total_time)

    def toggle_timer(self):
        if self.running:
            self.running = False
            self.timer.stop()
            self.start_btn.setText("▶ Resume")
        else:
            self.running = True
            self.timer.start(1000)
            self.start_btn.setText("⏸ Pause")

    def tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            self.progress.setValue(self.time_left)
        else:
            self.timer.stop()
            self.running = False
            self.start_btn.setText("▶ Start")
            self.flash_alert()

    def update_display(self):
        m = self.time_left // 60
        s = self.time_left % 60
        self.time_label.setText(f"{m:02}:{s:02}")

    def flash_alert(self):
        # Simple visual alert
        self.setStyleSheet(f"background-color: {COLORS['accent']}; color: black;")
        QTimer.singleShot(500, self.apply_styles)
        QTimer.singleShot(1000, lambda: self.setStyleSheet(f"background-color: {COLORS['accent']}; color: black;"))
        QTimer.singleShot(1500, self.apply_styles)


class TimerApp:
    def __init__(self):
        self.panel = TimerPanel()

    def show(self):
        self.panel.show()

    def hide(self):
        self.panel.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    timer = TimerApp()
    timer.show()
    sys.exit(app.exec())
