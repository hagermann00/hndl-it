"""
read-it: Standalone Document Reader Module
Part of the hndl-it ecosystem - Windows Native (PyQt6)

Features:
- 60x60 floating icon (matches hndl-it size)
- Click: Expand to reader
- Hold & Drag: Move
- TTS read-aloud
- Different color scheme (cyan/teal)
- SELECTION POPUP: Shows pill near cursor when text copied
"""

import sys
import os
import re
import pyttsx3
import ctypes
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QSlider, QComboBox, QProgressBar,
    QFrame, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QRectF, QTimer
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QCursor

# Windows API for mouse state
user32 = ctypes.windll.user32
GetAsyncKeyState = user32.GetAsyncKeyState
VK_LBUTTON = 0x01

# === COLORS (Cyan/Teal theme - distinct from hndl-it lime) ===
COLORS = {
    'primary': '#00d4ff',      # Cyan
    'primary_dim': '#00a0cc',
    'accent': '#00ffcc',       # Teal accent
    'bg_dark': '#1a1a2e',      # Dark blue-black
    'bg_panel': '#252540',
    'bg_input': '#2a2a45',
    'text_primary': '#e0e8ff',
    'text_secondary': '#8888aa',
    'border': '#333355',
}


# ============================================================================
# TTS WORKER THREAD
# ============================================================================
class TTSWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    finished_speaking = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()
        self.chunks = []
        self.current_chunk = 0
        self.is_playing = False
        self.is_paused = False
        self._stop_flag = False
    
    def set_text(self, text: str):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        self.chunks = [s.strip() for s in sentences if s.strip()]
        self.current_chunk = 0
    
    def set_rate(self, rate: int):
        self.engine.setProperty('rate', rate)
    
    def set_voice(self, voice_id: str):
        self.engine.setProperty('voice', voice_id)
    
    def get_voices(self):
        return self.engine.getProperty('voices')
    
    def run(self):
        self._stop_flag = False
        self.is_playing = True
        
        while self.current_chunk < len(self.chunks) and not self._stop_flag:
            if self.is_paused:
                self.msleep(100)
                continue
            
            self.progress_updated.emit(self.current_chunk + 1, len(self.chunks))
            self.engine.say(self.chunks[self.current_chunk])
            self.engine.runAndWait()
            self.current_chunk += 1
        
        self.is_playing = False
        self.finished_speaking.emit()
    
    def stop(self):
        self._stop_flag = True
        self.engine.stop()
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False


# ============================================================================
# SELECTION MONITOR - Detects text highlight (mouse release after drag)
# ============================================================================
class SelectionMonitor(QThread):
    """Monitors for text selection by watching mouse state."""
    text_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._running = True
        self._was_pressed = False
        self._press_pos = None
    
    def run(self):
        import pyautogui
        
        while self._running:
            # Check if left mouse button is pressed
            is_pressed = GetAsyncKeyState(VK_LBUTTON) & 0x8000
            
            if is_pressed and not self._was_pressed:
                # Mouse just pressed - record position
                self._press_pos = pyautogui.position()
                
            elif not is_pressed and self._was_pressed:
                # Mouse just released - check if it was a drag
                if self._press_pos:
                    current_pos = pyautogui.position()
                    distance = abs(current_pos[0] - self._press_pos[0]) + abs(current_pos[1] - self._press_pos[1])
                    
                    # If dragged more than 20 pixels, might be a selection
                    if distance > 20:
                        # Small delay to let selection complete
                        time.sleep(0.1)
                        
                        # Try to copy selection via Ctrl+C
                        import pyperclip
                        old_clipboard = pyperclip.paste()
                        
                        pyautogui.hotkey('ctrl', 'c', interval=0.05)
                        time.sleep(0.15)
                        
                        new_clipboard = pyperclip.paste()
                        
                        # If clipboard changed and has content, emit signal
                        if new_clipboard and new_clipboard != old_clipboard and len(new_clipboard.strip()) > 3:
                            self.text_selected.emit(new_clipboard)
            
            self._was_pressed = is_pressed
            self.msleep(50)  # Check every 50ms
    
    def stop(self):
        self._running = False


# ============================================================================
# SELECTION PILL - Appears near cursor when text copied
# ============================================================================
class SelectionPill(QWidget):
    read_requested = pyqtSignal(str)  # Emits the text to read
    summary_requested = pyqtSignal(str)  # Emits text for summary
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.setFixedSize(160, 36)
        self.pending_text = ""
        
        self.init_ui()
        self.apply_styles()
        
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
    
    def init_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("pill")
        self.container.setGeometry(0, 0, 160, 36)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Play button
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.on_play_click)
        layout.addWidget(self.play_btn)
        
        # Summary button
        self.summary_btn = QPushButton("📝 Sum")
        self.summary_btn.clicked.connect(self.on_summary_click)
        layout.addWidget(self.summary_btn)
    
    def apply_styles(self):
        self.container.setStyleSheet(f"""
            QFrame#pill {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['primary']};
                border-radius: 18px;
            }}
            QPushButton {{
                background-color: transparent;
                color: {COLORS['primary']};
                border: none;
                font-weight: bold;
                font-size: 11px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                color: {COLORS['accent']};
            }}
        """)
    
    def show_at_cursor(self, text: str):
        self.pending_text = text
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 10, cursor_pos.y() + 20)
        self.show()
        self.raise_()
        self.hide_timer.start(5000)
    
    def on_play_click(self):
        self.hide_timer.stop()
        self.hide()
        if self.pending_text:
            self.read_requested.emit(self.pending_text)
    
    def on_summary_click(self):
        self.hide_timer.stop()
        self.hide()
        if self.pending_text:
            self.summary_requested.emit(self.pending_text)


# ============================================================================
# PLAYBACK OVERLAY - Controls that appear on the icon when playing
# ============================================================================
class PlaybackOverlay(QWidget):
    play_pause_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    speed_changed = pyqtSignal(int)
    
    def __init__(self, parent_icon):
        super().__init__()
        self.parent_icon = parent_icon
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(140, 40)
        self.is_playing = False
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("overlay")
        self.container.setGeometry(0, 0, 140, 40)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)
        
        # Back 10 sec
        self.back_btn = QPushButton("⏪")
        self.back_btn.setFixedSize(28, 28)
        self.back_btn.setToolTip("Back 10 sec")
        self.back_btn.clicked.connect(lambda: self.back_clicked.emit())
        layout.addWidget(self.back_btn)
        
        # Play/Pause
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_btn)
        
        # Speed selector
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.75x", "1x", "1.25x", "1.5x", "2x"])
        self.speed_combo.setCurrentIndex(1)
        self.speed_combo.setFixedWidth(50)
        self.speed_combo.currentIndexChanged.connect(self.on_speed_change)
        layout.addWidget(self.speed_combo)
    
    def apply_styles(self):
        self.container.setStyleSheet(f"""
            QFrame#overlay {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['primary']};
                border-radius: 20px;
            }}
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['primary_dim']};
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dim']};
            }}
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 2px;
                font-size: 10px;
            }}
        """)
    
    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_btn.setText("▶" if not self.is_playing else "⏸")
        self.play_pause_clicked.emit()
    
    def on_speed_change(self, index):
        speeds = [75, 100, 125, 150, 200]
        self.speed_changed.emit(speeds[index])
    
    def show_near_icon(self):
        icon_pos = self.parent_icon.pos()
        self.move(icon_pos.x() - 80, icon_pos.y() + 65)
        self.show()
        self.raise_()
    
    def set_playing(self, playing: bool):
        self.is_playing = playing
        self.play_btn.setText("⏸" if playing else "▶")


# ============================================================================
# FLOATING ICON (60x60)
# ============================================================================
class FloatingIcon(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.size_val = 60
        self.setFixedSize(self.size_val, self.size_val)
        
        self._drag_pos = QPoint()
        self._dragging = False
        self._drag_started = False
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        from PyQt6.QtGui import QPixmap, QPainterPath
        
        # Try to load custom icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            
            # Draw circular clipped icon
            path = QPainterPath()
            path.addEllipse(0.0, 0.0, float(self.width()), float(self.height()))
            painter.setClipPath(path)
            
            # Scale and draw
            painter.drawPixmap(self.rect(), pixmap)
            
            # Draw border
            painter.setClipping(False)
            pen = QPen(QColor(COLORS['primary']))
            pen.setWidth(3)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawEllipse(3, 3, self.width()-6, self.height()-6)
        else:
            # Fallback gradient
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            gradient = QRadialGradient(cx, cy, self.width() / 2.0)
            gradient.setColorAt(0, QColor(COLORS['bg_panel']))
            gradient.setColorAt(1, QColor(COLORS['bg_dark']))
            
            painter.setBrush(QBrush(gradient))
            pen = QPen(QColor(COLORS['primary']))
            pen.setWidth(3)
            painter.setPen(pen)
            
            rect = QRectF(3, 3, self.width()-6, self.height()-6)
            painter.drawEllipse(rect)
            
            painter.setPen(QColor(COLORS['primary']))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(18)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "R")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = True
            self._drag_started = False
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self._drag_started = True
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if self._dragging and not self._drag_started:
            self.clicked.emit()
        self._dragging = False
    
    def contextMenuEvent(self, event):
        """Right-click menu with Restart/Quit options."""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary_dim']};
            }}
        """)
        
        restart_action = menu.addAction("🔄 Restart")
        menu.addSeparator()
        quit_action = menu.addAction("❌ Quit")
        
        action = menu.exec(event.globalPos())
        
        if action == restart_action:
            import subprocess
            subprocess.Popen([sys.executable, __file__])
            QApplication.quit()
        elif action == quit_action:
            QApplication.quit()


# ============================================================================
# READER PANEL (Expanded View)
# ============================================================================
class ReaderPanel(QWidget):
    closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        
        self.tts = TTSWorker()
        self.tts.finished_speaking.connect(self.on_finished)
        self.tts.progress_updated.connect(self.update_progress)
        
        self.is_expanded = False
        self._drag_pos = QPoint()
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        self.setFixedSize(600, 400)  # Larger panel for big text
        
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setGeometry(0, 0, 600, 400)
        
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)
        
        # Title bar
        title_bar = QHBoxLayout()
        title = QLabel("read-it")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-size: 14px; font-weight: bold;")
        title_bar.addWidget(title)
        title_bar.addStretch()
        
        # Expand toggle
        self.expand_btn = QPushButton("◀")
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.clicked.connect(self.toggle_expand)
        title_bar.addWidget(self.expand_btn)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.collapse)
        title_bar.addWidget(close_btn)
        self.layout.addLayout(title_bar)
        
        # Text area (scrollable, no limit)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste or drop text here...")
        self.text_edit.setMinimumHeight(200)
        self.layout.addWidget(self.text_edit)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(4)
        self.layout.addWidget(self.progress)
        
        # MINIMAL CONTROLS (always visible)
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⬛")
        self.stop_btn.setFixedSize(36, 36)
        self.stop_btn.clicked.connect(self.stop_reading)
        controls.addWidget(self.stop_btn)
        
        controls.addStretch()
        
        # Speed (compact)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(100, 300)
        self.speed_slider.setValue(175)
        self.speed_slider.setFixedWidth(80)
        self.speed_slider.valueChanged.connect(lambda v: self.tts.set_rate(v))
        controls.addWidget(self.speed_slider)
        
        self.layout.addLayout(controls)
        
        # EXPANDED CONTROLS (hidden by default)
        self.expanded_frame = QFrame()
        self.expanded_frame.hide()
        exp_layout = QVBoxLayout(self.expanded_frame)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        exp_layout.setSpacing(6)
        
        # Voice selector
        voice_row = QHBoxLayout()
        voice_label = QLabel("Voice:")
        voice_row.addWidget(voice_label)
        self.voice_combo = QComboBox()
        self.load_voices()
        self.voice_combo.currentIndexChanged.connect(self.change_voice)
        voice_row.addWidget(self.voice_combo, 1)
        exp_layout.addLayout(voice_row)
        
        # Open/Paste buttons
        btn_row = QHBoxLayout()
        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self.open_file)
        btn_row.addWidget(open_btn)
        
        paste_btn = QPushButton("📋 Paste")
        paste_btn.clicked.connect(self.paste_clipboard)
        btn_row.addWidget(paste_btn)
        exp_layout.addLayout(btn_row)
        
        self.layout.addWidget(self.expanded_frame)
    
    def toggle_expand(self):
        if self.is_expanded:
            self.expanded_frame.hide()
            self.setFixedSize(600, 400)
            self.container.setGeometry(0, 0, 600, 400)
            self.expand_btn.setText("◀")
            self.is_expanded = False
        else:
            self.expanded_frame.show()
            self.setFixedSize(600, 500)
            self.container.setGeometry(0, 0, 600, 500)
            self.expand_btn.setText("▼")
            self.is_expanded = True
    
    def apply_styles(self):
        self.container.setStyleSheet(f"""
            QFrame#container {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['primary']};
                border-radius: 12px;
            }}
            QLabel {{ color: {COLORS['text_primary']}; }}
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['primary_dim']};
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dim']};
                color: {COLORS['bg_dark']};
            }}
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px;
            }}
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 4px;
            }}
            QSlider::groove:horizontal {{
                background: {COLORS['border']};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['primary']};
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QProgressBar {{
                background: {COLORS['border']};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 2px;
            }}
        """)
    
    def load_voices(self):
        voices = self.tts.get_voices()
        for voice in voices:
            self.voice_combo.addItem(voice.name, voice.id)
    
    def change_voice(self, index):
        voice_id = self.voice_combo.itemData(index)
        if voice_id:
            self.tts.set_voice(voice_id)
    
    def toggle_play(self):
        if self.tts.is_playing:
            if self.tts.is_paused:
                self.tts.resume()
                self.play_btn.setText("⏸")
            else:
                self.tts.pause()
                self.play_btn.setText("▶")
        else:
            self.start_reading()
    
    def start_reading(self):
        text = self.text_edit.toPlainText()
        if not text.strip():
            return
        
        self.tts.set_text(text)
        self.tts.set_rate(self.speed_slider.value())
        self.play_btn.setText("⏸")
        self.tts.start()
    
    def stop_reading(self):
        self.tts.stop()
        self.play_btn.setText("▶")
        self.progress.setValue(0)
    
    def on_finished(self):
        self.play_btn.setText("▶")
        self.progress.setValue(100)
    
    def update_progress(self, current, total):
        if total > 0:
            self.progress.setValue(int((current / total) * 100))
    
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "Text (*.txt);;All (*)")
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.text_edit.setText(f.read())
    
    def paste_clipboard(self):
        self.text_edit.setText(QApplication.clipboard().text())
    
    def collapse(self):
        self.hide()
        self.closed.emit()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self.text_edit.setText(f.read())
                    break
        elif event.mimeData().hasText():
            self.text_edit.setText(event.mimeData().text())


# ============================================================================
# MAIN APP
# ============================================================================
class ReadItApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Main icon (always visible)
        self.icon = FloatingIcon()
        self.icon.clicked.connect(self.toggle_panel)
        
        # Reader panel
        self.panel = ReaderPanel()
        self.panel.tts.finished_speaking.connect(self.on_playback_finished)
        
        # Playback overlay (controls near icon)
        self.playback_overlay = PlaybackOverlay(self.icon)
        self.playback_overlay.play_pause_clicked.connect(self.toggle_playback)
        self.playback_overlay.back_clicked.connect(self.back_10_sec)
        self.playback_overlay.speed_changed.connect(self.change_speed)
        
        # Selection pill (popup on highlight)
        self.pill = SelectionPill()
        self.pill.read_requested.connect(self.read_text)
        self.pill.summary_requested.connect(self.summarize_text)
        
        # Selection monitor - detects text highlight (NOT copy)
        self.selection_monitor = SelectionMonitor()
        self.selection_monitor.text_selected.connect(self.on_text_selected)
        self.selection_monitor.start()
        
        # Position icon
        screen = self.app.primaryScreen().availableGeometry()
        self.icon.move(screen.width() - 100, screen.height() - 780)
    
    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide()
        else:
            icon_pos = self.icon.pos()
            panel_x = icon_pos.x() - 70 - self.panel.width()
            self.panel.move(panel_x, icon_pos.y() - 150)
            self.panel.show()
    
    def on_text_selected(self, text: str):
        """Called when text is highlighted anywhere."""
        self.pill.show_at_cursor(text)
    
    def read_text(self, text: str):
        """Read text and show playback overlay."""
        self.panel.text_edit.setText(text)
        self.panel.start_reading()
        self.playback_overlay.set_playing(True)
        self.playback_overlay.show_near_icon()
    
    def summarize_text(self, text: str):
        """Summarize text (placeholder - will use local LLM later)."""
        # For now, just show first 200 chars as summary
        summary = text[:200] + "..." if len(text) > 200 else text
        self.panel.text_edit.setText(f"📝 Summary:\n\n{summary}")
        icon_pos = self.icon.pos()
        panel_x = icon_pos.x() - 70 - self.panel.width()
        self.panel.move(panel_x, icon_pos.y() - 150)
        self.panel.show()
    
    def toggle_playback(self):
        if self.panel.tts.is_playing:
            if self.panel.tts.is_paused:
                self.panel.tts.resume()
            else:
                self.panel.tts.pause()
        else:
            self.panel.start_reading()
    
    def back_10_sec(self):
        """Go back ~10 sentences (approximation)."""
        if self.panel.tts.current_chunk > 2:
            self.panel.tts.current_chunk -= 2
    
    def change_speed(self, rate: int):
        """Change TTS speed."""
        actual_rate = int(175 * rate / 100)
        self.panel.tts.set_rate(actual_rate)
    
    def on_playback_finished(self):
        self.playback_overlay.set_playing(False)
        self.playback_overlay.hide()
    
    def run(self):
        self.icon.show()
        return self.app.exec()


def main():
    app = ReadItApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
