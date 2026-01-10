"""
AI Cluster Monitor v4.0 - Full System Dashboard
Compact widget + Expanded full monitor
"""

import sys
import psutil
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont, QPainterPath, QPen

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except:
    GPU_AVAILABLE = False

# Colors
CYAN = "#0ddff2"
ORANGE = "#f97316"
GREEN = "#22c55e"
GRAY = "#3f3f46"
BG_DARK = "#0a1214"
BORDER = "#0ddff2"
TOTAL_VRAM = 12.0


class DualLineGraph(QFrame):
    """Dual-line graph: GPU (cyan) + CPU (green)."""
    def __init__(self, height=80):
        super().__init__()
        self.setFixedHeight(height)
        self.gpu_history = [0] * 30
        self.cpu_history = [0] * 30
        self.setStyleSheet("background: transparent;")
    
    def add_values(self, gpu_val, cpu_val):
        self.gpu_history.append(gpu_val)
        self.gpu_history = self.gpu_history[-30:]
        self.cpu_history.append(cpu_val)
        self.cpu_history = self.cpu_history[-30:]
        self.update()
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Grid
        p.setPen(QPen(QColor(255, 255, 255, 15), 1))
        for i in range(1, 3):
            y = int(h * i / 3)
            p.drawLine(0, y, w, y)
        
        # Draw GPU line (cyan)
        self._draw_line(p, self.gpu_history, CYAN, w, h)
        
        # Draw CPU line (green)
        self._draw_line(p, self.cpu_history, GREEN, w, h)
        
        p.end()
    
    def _draw_line(self, p, history, color, w, h):
        points = []
        for i, v in enumerate(history):
            x = int(i * w / (len(history) - 1)) if len(history) > 1 else 0
            y = int(h - (v / 100) * h * 0.9)
            points.append((x, y))
        
        p.setPen(QPen(QColor(color), 1.5))
        for i in range(len(points) - 1):
            p.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])


class StackedVRAM(QLabel):
    """Giant VRAM text with stacked gradient."""
    def __init__(self, text="0.0", font_size=48):
        super().__init__(text)
        self.font_size = font_size
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        rect = self.rect()
        text = self.text()
        font = QFont("Space Grotesk", self.font_size)
        font.setBold(True)
        p.setFont(font)
        
        fm = p.fontMetrics()
        x = 8
        y = (rect.height() + fm.ascent() - fm.descent()) // 2
        
        path = QPainterPath()
        path.addText(x, y, font, text)
        
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0.0, QColor(CYAN))
        grad.setColorAt(0.5, QColor(CYAN))
        grad.setColorAt(0.5, QColor(GREEN))
        grad.setColorAt(1.0, QColor(GREEN))
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawPath(path)
        p.end()


class ExpandedMonitor(QWidget):
    """Full AI Cluster Monitor panel."""
    
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self.setWindowTitle("AI Cluster Monitor")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 700)
        self._drag_pos = None
        self._click_pos = None
        
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.update_stats()
    
    def init_ui(self):
        c = QFrame(self)
        c.setGeometry(0, 0, 320, 700)
        c.setObjectName("main")
        c.setStyleSheet(f"""
            QFrame#main {{
                background: {BG_DARK};
                border: 1px solid {CYAN};
            }}
            QLabel {{ background: transparent; color: white; font-family: 'Space Grotesk'; }}
            QProgressBar {{
                background: rgba(255,255,255,0.1);
                border: none;
                height: 4px;
            }}
            QProgressBar::chunk {{ background: {CYAN}; }}
        """)
        
        layout = QVBoxLayout(c)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ===== HEADER =====
        header = QFrame()
        header.setStyleSheet(f"background: rgba(0,0,0,0.3);")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)
        
        icon = QLabel("⬛")
        icon.setStyleSheet(f"color: {CYAN}; font-size: 14px;")
        h_layout.addWidget(icon)
        
        title = QLabel("AI CLUSTER MONITOR V4.0")
        title.setStyleSheet("font-size: 11px; font-weight: bold; letter-spacing: 2px;")
        h_layout.addWidget(title)
        
        h_layout.addStretch()
        
        status = QLabel("⊞⊞⊞")
        status.setStyleSheet(f"color: {CYAN}; font-size: 10px;")
        h_layout.addWidget(status)
        
        layout.addWidget(header)
        
        # ===== GPU SECTION =====
        gpu_section = QFrame()
        gpu_section.setStyleSheet(f"background: rgba(13,223,242,0.05); border: 1px solid rgba(13,223,242,0.2); margin: 8px;")
        gpu_layout = QVBoxLayout(gpu_section)
        gpu_layout.setContentsMargins(12, 8, 12, 8)
        gpu_layout.setSpacing(4)
        
        gpu_header = QHBoxLayout()
        gpu_title = QLabel("GPU ARCHITECTURE / CUDA 12.1")
        gpu_title.setStyleSheet(f"color: {CYAN}; font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        gpu_header.addWidget(gpu_title)
        gpu_header.addStretch()
        self.gpu_status = QLabel("STABLE")
        self.gpu_status.setStyleSheet(f"color: {GREEN}; font-size: 9px; font-weight: bold;")
        gpu_header.addWidget(self.gpu_status)
        gpu_layout.addLayout(gpu_header)
        
        # VRAM display
        vram_row = QHBoxLayout()
        self.vram_value = StackedVRAM("0.0", 42)
        self.vram_value.setFixedHeight(55)
        vram_row.addWidget(self.vram_value)
        gb_lbl = QLabel("GB")
        gb_lbl.setStyleSheet(f"color: {GRAY}; font-size: 14px; font-weight: bold;")
        vram_row.addWidget(gb_lbl, alignment=Qt.AlignmentFlag.AlignBottom)
        vram_row.addStretch()
        gpu_layout.addLayout(vram_row)
        
        # Legend
        legend = QHBoxLayout()
        for name, color in [("ROUTER", CYAN), ("BRAIN", ORANGE), ("VISION", GREEN), ("IDLE", GRAY)]:
            dot = QLabel("■")
            dot.setStyleSheet(f"color: {color}; font-size: 8px;")
            legend.addWidget(dot)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color: rgba(255,255,255,0.5); font-size: 8px;")
            legend.addWidget(lbl)
            legend.addSpacing(8)
        legend.addStretch()
        gpu_layout.addLayout(legend)
        
        layout.addWidget(gpu_section)
        
        # ===== WAVEFORM =====
        self.waveform = DualLineGraph(70)
        layout.addWidget(self.waveform)
        
        # ===== CPU MATRIX =====
        cpu_section = QFrame()
        cpu_section.setStyleSheet("margin: 8px;")
        cpu_layout = QVBoxLayout(cpu_section)
        cpu_layout.setContentsMargins(8, 0, 8, 0)
        cpu_layout.setSpacing(4)
        
        cpu_header = QHBoxLayout()
        cpu_title = QLabel("CPU COMPUTE MATRIX")
        cpu_title.setStyleSheet("font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        cpu_header.addWidget(cpu_title)
        cpu_header.addStretch()
        self.cpu_avg = QLabel("AVG 0°C")
        self.cpu_avg.setStyleSheet(f"color: {CYAN}; font-size: 9px;")
        cpu_header.addWidget(self.cpu_avg)
        cpu_layout.addLayout(cpu_header)
        
        # CPU cores grid
        self.cpu_grid = QGridLayout()
        self.cpu_grid.setSpacing(4)
        self.cpu_bars = []
        for i in range(8):
            box = QFrame()
            box.setStyleSheet(f"background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1);")
            box.setFixedHeight(32)
            box_layout = QHBoxLayout(box)
            box_layout.setContentsMargins(6, 2, 6, 2)
            
            core_lbl = QLabel(f"C0{i+1}")
            core_lbl.setStyleSheet("font-size: 8px; color: rgba(255,255,255,0.4);")
            box_layout.addWidget(core_lbl)
            
            pct = QLabel("0%")
            pct.setObjectName(f"cpu_{i}")
            pct.setStyleSheet(f"color: {CYAN}; font-size: 10px; font-weight: bold;")
            box_layout.addWidget(pct)
            self.cpu_bars.append(pct)
            
            self.cpu_grid.addWidget(box, i // 4, i % 4)
        
        cpu_layout.addLayout(self.cpu_grid)
        layout.addWidget(cpu_section)
        
        # ===== STORAGE HUB =====
        storage = QFrame()
        storage.setStyleSheet(f"margin: 8px; background: rgba(0,0,0,0.2); border-left: 2px solid {CYAN};")
        storage_layout = QVBoxLayout(storage)
        storage_layout.setContentsMargins(12, 8, 12, 8)
        storage_layout.setSpacing(6)
        
        storage_title = QLabel("STORAGE HUB")
        storage_title.setStyleSheet("font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        storage_layout.addWidget(storage_title)
        
        self.disk_bars = []
        for name in ["NVMe_01 / DATA", "NVMe_02 / MODELS", "SATA_01 / COLD"]:
            row = QHBoxLayout()
            lbl = QLabel(name)
            lbl.setStyleSheet("font-size: 9px; color: rgba(255,255,255,0.6);")
            lbl.setFixedWidth(120)
            row.addWidget(lbl)
            
            bar = QProgressBar()
            bar.setFixedHeight(6)
            bar.setRange(0, 100)
            row.addWidget(bar)
            
            size_lbl = QLabel("-- / --")
            size_lbl.setStyleSheet(f"color: {CYAN}; font-size: 8px;")
            size_lbl.setFixedWidth(70)
            size_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(size_lbl)
            self.disk_bars.append((bar, size_lbl))
            
            storage_layout.addLayout(row)
        
        layout.addWidget(storage)
        
        # ===== AI MODELS =====
        models = QFrame()
        models.setStyleSheet("margin: 8px;")
        models_layout = QVBoxLayout(models)
        models_layout.setContentsMargins(8, 0, 8, 0)
        models_layout.setSpacing(4)
        
        models_title = QLabel("AI LATENCY & MODELS")
        models_title.setStyleSheet("font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        models_layout.addWidget(models_title)
        
        for name, color in [("Router-8b", CYAN), ("Brain-MoE", ORANGE), ("Vision-v4", GREEN)]:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 8px;")
            row.addWidget(dot)
            lbl = QLabel(name)
            lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
            row.addWidget(lbl)
            row.addStretch()
            latency = QLabel("--ms")
            latency.setStyleSheet("font-size: 9px; color: rgba(255,255,255,0.5);")
            row.addWidget(latency)
            tps = QLabel("-- t/s")
            tps.setStyleSheet(f"color: {CYAN}; font-size: 9px; font-weight: bold;")
            row.addWidget(tps)
            models_layout.addLayout(row)
        
        layout.addWidget(models)
        
        layout.addStretch()
        
        # ===== BOTTOM NAV =====
        nav = QFrame()
        nav.setStyleSheet(f"background: rgba(0,0,0,0.4); border-top: 1px solid rgba(13,223,242,0.2);")
        nav.setFixedHeight(40)
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(20, 0, 20, 0)
        
        for icon in ["⊞", "⬛", "⚙", "🔔"]:
            btn = QLabel(icon)
            btn.setStyleSheet(f"color: {CYAN}; font-size: 16px;")
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nav_layout.addWidget(btn)
        
        layout.addWidget(nav)
    
    def update_stats(self):
        try:
            # GPU
            if GPU_AVAILABLE:
                h = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                used = mem.used / (1024**3)
                self.vram_value.setText(f"{used:.1f}")
            
            # CPU
            cpu_pcts = psutil.cpu_percent(percpu=True)
            self.waveform.add_values(cpu_pcts)
            
            for i, pct in enumerate(cpu_pcts[:8]):
                self.cpu_bars[i].setText(f"{int(pct)}%")
            
            # Disk
            partitions = psutil.disk_partitions()
            for i, (bar, lbl) in enumerate(self.disk_bars):
                if i < len(partitions):
                    try:
                        usage = psutil.disk_usage(partitions[i].mountpoint)
                        bar.setValue(int(usage.percent))
                        used_gb = usage.used / (1024**3)
                        total_gb = usage.total / (1024**3)
                        lbl.setText(f"{used_gb:.0f} / {total_gb:.0f} GB")
                    except:
                        pass
                        
        except Exception as e:
            pass
    
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._click_pos = e.globalPosition().toPoint()
    
    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, e):
        if self._click_pos:
            delta = (e.globalPosition().toPoint() - self._click_pos).manhattanLength()
            if delta < 5:
                self.hide()
                self.app_ref.show_compact(self.pos())
        self._drag_pos = None
        self._click_pos = None


class CompactMonitor(QWidget):
    """Mini version - scaled down industrial widget."""
    
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self.setWindowTitle("GPU")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(70, 130)
        self._drag_pos = None
        self._click_pos = None
        
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.update_stats()
    
    def init_ui(self):
        c = QFrame(self)
        c.setGeometry(0, 0, 70, 130)
        c.setObjectName("main")
        c.setStyleSheet(f"""
            QFrame#main {{ background: {BG_DARK}; border: 1px solid {CYAN}; }}
            QLabel {{ background: transparent; color: white; }}
        """)
        
        layout = QVBoxLayout(c)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet(f"background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(13,223,242,0.2);")
        header.setFixedHeight(16)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(4, 0, 4, 0)
        title = QLabel("⬛")
        title.setStyleSheet(f"color: {CYAN}; font-size: 8px;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {GREEN}; font-size: 4px;")
        h_layout.addWidget(dot)
        layout.addWidget(header)
        
        # VRAM (GB number)
        self.vram_value = StackedVRAM("0.0", 22)
        self.vram_value.setFixedHeight(28)
        layout.addWidget(self.vram_value)
        
        # Dual-line graph: GPU (cyan) + CPU (green)
        self.dual_graph = DualLineGraph(28)
        layout.addWidget(self.dual_graph)
        
        # Stats row: GPU% | CPU% | RAM%
        stats = QFrame()
        stats.setStyleSheet("background: rgba(0,0,0,0.2);")
        stats_layout = QHBoxLayout(stats)
        stats_layout.setContentsMargins(3, 2, 3, 2)
        stats_layout.setSpacing(2)
        
        # GPU %
        self.gpu_pct = QLabel("0")
        self.gpu_pct.setStyleSheet(f"color: {CYAN}; font-size: 9px; font-weight: bold;")
        stats_layout.addWidget(self.gpu_pct)
        
        stats_layout.addWidget(QLabel("|"))
        
        # CPU %
        self.cpu_pct = QLabel("0")
        self.cpu_pct.setStyleSheet(f"color: {GREEN}; font-size: 9px; font-weight: bold;")
        stats_layout.addWidget(self.cpu_pct)
        
        stats_layout.addWidget(QLabel("|"))
        
        # RAM %
        self.ram_pct = QLabel("0")
        self.ram_pct.setStyleSheet(f"color: {ORANGE}; font-size: 9px; font-weight: bold;")
        stats_layout.addWidget(self.ram_pct)
        
        layout.addWidget(stats)
        
        # Footer with temp
        footer = QFrame()
        footer.setStyleSheet(f"background: rgba(0,0,0,0.3); border-top: 1px solid rgba(13,223,242,0.2);")
        footer.setFixedHeight(12)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(4, 0, 4, 0)
        self.temp_lbl = QLabel("--°")
        self.temp_lbl.setStyleSheet(f"color: rgba(13,223,242,0.4); font-size: 7px;")
        f_layout.addWidget(self.temp_lbl)
        f_layout.addStretch()
        layout.addWidget(footer)
    
    def update_stats(self):
        try:
            gpu_util = 0
            cpu_util = 0
            
            if GPU_AVAILABLE:
                h = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                used = mem.used / (1024**3)
                self.vram_value.setText(f"{used:.1f}")
                
                util = pynvml.nvmlDeviceGetUtilizationRates(h)
                gpu_util = util.gpu
                self.gpu_pct.setText(f"{gpu_util}")
                
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
                    self.temp_lbl.setText(f"{temp}°")
                except: pass
            
            # CPU
            cpu_util = psutil.cpu_percent()
            self.cpu_pct.setText(f"{int(cpu_util)}")
            
            # RAM
            ram = psutil.virtual_memory()
            self.ram_pct.setText(f"{int(ram.percent)}")
            
            # Update dual graph
            self.dual_graph.add_values(gpu_util, cpu_util)
        except:
            pass
    
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._click_pos = e.globalPosition().toPoint()
    
    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, e):
        if self._click_pos:
            delta = (e.globalPosition().toPoint() - self._click_pos).manhattanLength()
            if delta < 5:
                self.hide()
                self.app_ref.show_expanded(self.pos())
        self._drag_pos = None
        self._click_pos = None


class GPUApp:
    def __init__(self):
        self.compact = CompactMonitor(self)
        self.expanded = ExpandedMonitor(self)
    
    def show_compact(self, pos=None):
        if pos:
            self.compact.move(pos.x() + 250, pos.y())
        self.compact.show()
    
    def show_expanded(self, pos=None):
        if pos:
            self.expanded.move(pos.x() - 250, pos.y())
        self.expanded.show()
    
    def start(self):
        s = QApplication.primaryScreen().availableGeometry()
        self.compact.move(s.width() - self.compact.width() - 12, 400)
        self.compact.show()


def main():
    app = QApplication(sys.argv)
    gpu_app = GPUApp()
    gpu_app.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
