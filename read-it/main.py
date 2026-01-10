"""
read-it: Standalone Document Reader Module
Part of the hndl-it ecosystem - Windows Native (PyQt6)

Features:
- 60x60 floating icon (matches hndl-it)
- Click: Expand to reader
- Hold & Drag: Move
- TTS read-aloud
"""

import sys
import os
import re
import pyttsx3
import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QSlider, QComboBox, QProgressBar,
    QFrame, QSystemTrayIcon, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QFont, QPainterPath

# === COLORS (hndl-it lime theme) ===
COLORS = {
    'lime_primary': '#a3ff00',
    'lime_dim': '#7acc00',
    'bg_dark': '#1a1a1a',
    'bg_panel': '#252525',
    'bg_input': '#2a2a2a',
    'text_primary': '#e0e0e0',
    'text_secondary': '#888888',
    'border': '#333333',
}


# ============================================================================
# TTS WORKER THREAD
# ============================================================================
class TTSWorker(QThread):
    """Background TTS thread"""
    progress_updated = pyqtSignal(int, int)
    chunk_started = pyqtSignal(int)
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
            
            self.chunk_started.emit(self.current_chunk)
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
# FLOATING ICON (60x60, matches hndl-it)
# ============================================================================
class FloatingIcon(QWidget):
    """60x60 floating icon - click to expand, drag to move"""
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
        
        # Gradient background
        gradient = QRadialGradient(self.rect().center(), self.width() / 2)
        gradient.setColorAt(0, QColor(COLORS['bg_panel']))
        gradient.setColorAt(1, QColor(COLORS['bg_dark']))
        
        painter.setBrush(QBrush(gradient))
        
        # Lime border
        pen = QPen(QColor(COLORS['lime_primary']))
        pen.setWidth(3)
        painter.setPen(pen)
        
        rect = QRectF(3, 3, self.width()-6, self.height()-6)
        painter.drawEllipse(rect)
        
        # "R" for read-it
        painter.setPen(QColor(COLORS['lime_primary']))
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
            # It was a click, not a drag
            self.clicked.emit()
        self._dragging = False


# ============================================================================
# READER PANEL (Expanded View)
# ============================================================================
class ReaderPanel(QWidget):
    """Expanded reader panel with TTS controls"""
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
        
        self.document_text = ""
        self._drag_pos = QPoint()
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        self.setFixedSize(400, 500)
        
        # Main container
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setGeometry(0, 0, 400, 500)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title bar
        title_bar = QHBoxLayout()
        title = QLabel("read-it")
        title.setStyleSheet(f"color: {COLORS['lime_primary']}; font-size: 16px; font-weight: bold;")
        title_bar.addWidget(title)
        title_bar.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.collapse)
        title_bar.addWidget(close_btn)
        layout.addLayout(title_bar)
        
        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste or drop text here...")
        layout.addWidget(self.text_edit, 1)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)
        
        # Controls
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⬛")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.clicked.connect(self.stop_reading)
        controls.addWidget(self.stop_btn)
        
        controls.addStretch()
        
        # Speed slider
        speed_label = QLabel("Speed:")
        controls.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(100, 300)
        self.speed_slider.setValue(175)
        self.speed_slider.setFixedWidth(100)
        self.speed_slider.valueChanged.connect(lambda v: self.tts.set_rate(v))
        controls.addWidget(self.speed_slider)
        
        layout.addLayout(controls)
        
        # Voice selector
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        voice_layout.addWidget(voice_label)
        
        self.voice_combo = QComboBox()
        self.load_voices()
        self.voice_combo.currentIndexChanged.connect(self.change_voice)
        voice_layout.addWidget(self.voice_combo, 1)
        
        layout.addLayout(voice_layout)
        
        # Bottom buttons
        bottom = QHBoxLayout()
        
        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self.open_file)
        bottom.addWidget(open_btn)
        
        paste_btn = QPushButton("📋 Paste")
        paste_btn.clicked.connect(self.paste_clipboard)
        bottom.addWidget(paste_btn)
        
        layout.addLayout(bottom)
    
    def apply_styles(self):
        self.container.setStyleSheet(f"""
            QFrame#container {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['lime_primary']};
                border-radius: 12px;
            }}
            QLabel {{ color: {COLORS['text_primary']}; }}
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['lime_primary']};
                border: 1px solid {COLORS['lime_dim']};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['lime_dim']};
                color: {COLORS['bg_dark']};
            }}
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['lime_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            QSlider::groove:horizontal {{
                background: {COLORS['border']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['lime_primary']};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QProgressBar {{
                background: {COLORS['border']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['lime_primary']};
                border-radius: 3px;
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
        
        self.document_text = text
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
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.text_edit.setText(f.read())
    
    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        self.text_edit.setText(clipboard.text())
    
    def collapse(self):
        self.hide()
        self.closed.emit()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
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
    """read-it application controller"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Floating icon
        self.icon = FloatingIcon()
        self.icon.clicked.connect(self.toggle_panel)
        
        # Reader panel
        self.panel = ReaderPanel()
        self.panel.closed.connect(lambda: self.icon.show())
        
        # Position icon bottom-right
        screen = self.app.primaryScreen().availableGeometry()
        self.icon.move(screen.width() - 100, screen.height() - 100)
    
    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide()
            self.icon.show()
        else:
            # Position panel near icon
            icon_pos = self.icon.pos()
            self.panel.move(icon_pos.x() - 350, icon_pos.y() - 450)
            self.panel.show()
            self.icon.hide()
    
    def run(self):
        self.icon.show()
        return self.app.exec()


def main():
    app = ReadItApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
