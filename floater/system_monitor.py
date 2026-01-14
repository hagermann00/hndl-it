"""
System Monitor Widget for hndl-it Floater Arsenal
Revamped Form: Compact, elegant, real-time GPU/CPU/RAM display.
"""
import logging
import psutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen

logger = logging.getLogger("hndl-it.floater.sysmon")

# Try to import pynvml for GPU stats
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False

class SystemMonitor(QWidget):
    """
    Compact System Monitor Widget.
    Shows CPU, RAM, and GPU (if available) in a sleek, minimal design.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SystemMonitor")
        self.setFixedHeight(100)
        
        self._setup_styles()
        self._setup_ui()
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(2000)  # Refresh every 2 seconds
        
        self._refresh()

    def _setup_styles(self):
        self.setStyleSheet("""
            QWidget#SystemMonitor {
                background-color: rgba(20, 25, 30, 220);
                border: 1px solid rgba(100, 200, 255, 80);
                border-radius: 8px;
            }
            QLabel.metric-label {
                color: #888888;
                font-size: 10px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel.metric-value {
                color: #00ffff;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Consolas', monospace;
            }
            QProgressBar {
                border: none;
                background-color: rgba(40, 50, 60, 150);
                height: 6px;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00aaff, stop:1 #00ffff);
                border-radius: 3px;
            }
        """)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(15)
        
        # CPU
        cpu_box = self._create_metric_box("CPU", "cpu")
        layout.addWidget(cpu_box)
        
        # RAM
        ram_box = self._create_metric_box("RAM", "ram")
        layout.addWidget(ram_box)
        
        # GPU (if available)
        if GPU_AVAILABLE:
            gpu_box = self._create_metric_box("GPU", "gpu")
            layout.addWidget(gpu_box)

    def _create_metric_box(self, label: str, metric_id: str) -> QWidget:
        box = QFrame()
        box.setStyleSheet("background: transparent; border: none;")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(2)
        
        # Label
        lbl = QLabel(label)
        lbl.setProperty("class", "metric-label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(lbl)
        
        # Value
        val = QLabel("--")
        val.setObjectName(f"{metric_id}_value")
        val.setProperty("class", "metric-value")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(val)
        
        # Progress bar
        bar = QProgressBar()
        bar.setObjectName(f"{metric_id}_bar")
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setMaximum(100)
        bar.setValue(0)
        box_layout.addWidget(bar)
        
        return box

    def _refresh(self):
        # CPU
        cpu_pct = psutil.cpu_percent(interval=None)
        self._update_metric("cpu", f"{cpu_pct:.0f}%", int(cpu_pct))
        
        # RAM
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        self._update_metric("ram", f"{ram_pct:.0f}%", int(ram_pct))
        
        # GPU
        if GPU_AVAILABLE:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_pct = util.gpu
                self._update_metric("gpu", f"{gpu_pct}%", gpu_pct)
            except Exception as e:
                self._update_metric("gpu", "N/A", 0)

    def _update_metric(self, metric_id: str, text: str, value: int):
        val_label = self.findChild(QLabel, f"{metric_id}_value")
        bar = self.findChild(QProgressBar, f"{metric_id}_bar")
        
        if val_label:
            val_label.setText(text)
        if bar:
            bar.setValue(value)
            # Color coding
            if value > 80:
                bar.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; border-radius: 3px; }")
            elif value > 60:
                bar.setStyleSheet("QProgressBar::chunk { background-color: #ffaa44; border-radius: 3px; }")
            else:
                bar.setStyleSheet("QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00aaff, stop:1 #00ffff); border-radius: 3px; }")

    def stop(self):
        self.timer.stop()
