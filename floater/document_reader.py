"""
Document Reader - Native Windows Float-to-Full Reader with TTS
Part of the hndl-it system - Matches Floater UI design language
"""

import sys
import os
import re
import pyttsx3
import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QSlider, QComboBox, QFileDialog,
    QFrame, QScrollArea, QSystemTrayIcon, QMenu, QProgressBar
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QAction
import markdown


# ============================================================================
# BRAND COLORS - 4px Brighter Lime (2026 hndl-it Identity)
# ============================================================================
COLORS = {
    'bg_dark': '#1a1a1a',
    'bg_panel': '#252525',
    'bg_input': '#2d2d2d',
    'lime_primary': '#84ff00',      # Main lime accent
    'lime_bright': '#9cff33',       # Brighter hover
    'lime_dim': '#5cb300',          # Dimmed state
    'lime_glow': 'rgba(132, 255, 0, 0.3)',
    'text_primary': '#e0e0e0',
    'text_secondary': '#888888',
    'border': '#3a3a3a',
    'success': '#44ff66',
    'warning': '#ffaa00',
    'error': '#ff4444',
}


# ============================================================================
# TTS WORKER THREAD
# ============================================================================
class TTSWorker(QThread):
    """Background thread for text-to-speech"""
    progress_updated = pyqtSignal(int, int)  # current, total
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
        """Split text into speakable chunks"""
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        self.chunks = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) < 300:
                current += sentence + " "
            else:
                if current.strip():
                    self.chunks.append(current.strip())
                current = sentence + " "
        
        if current.strip():
            self.chunks.append(current.strip())
        
        self.current_chunk = 0
        
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self.engine.setProperty('rate', rate)
        
    def set_voice(self, voice_id: str):
        """Set voice by ID"""
        self.engine.setProperty('voice', voice_id)
        
    def get_voices(self):
        """Get available voices"""
        return self.engine.getProperty('voices')
    
    def run(self):
        """Main TTS loop"""
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
        """Stop speaking"""
        self._stop_flag = True
        self.engine.stop()
        self.is_playing = False
        
    def pause(self):
        """Pause speaking"""
        self.is_paused = True
        
    def resume(self):
        """Resume speaking"""
        self.is_paused = False
        
    def skip_forward(self):
        """Skip to next chunk"""
        if self.current_chunk < len(self.chunks) - 1:
            self.current_chunk += 1
            self.engine.stop()
            
    def skip_back(self):
        """Skip to previous chunk"""
        if self.current_chunk > 0:
            self.current_chunk -= 1
            self.engine.stop()


# ============================================================================
# DOCUMENT READER WIDGET
# ============================================================================
class DocumentReader(QWidget):
    """Native Windows Document Reader with TTS - Float-to-Full Pattern"""
    
    def __init__(self):
        super().__init__()
        self.is_expanded = False
        self.document_text = ""
        self.drag_position = None
        
        # TTS
        self.tts_worker = TTSWorker()
        self.tts_worker.progress_updated.connect(self.update_progress)
        self.tts_worker.chunk_started.connect(self.highlight_chunk)
        self.tts_worker.finished_speaking.connect(self.on_finished)
        
        self.init_ui()
        self.setup_tray()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Window setup - frameless
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main container
        self.container = QFrame(self)
        self.container.setObjectName("container")
        
        # Layouts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 8, 12, 12)
        container_layout.setSpacing(8)
        
        # Title bar
        title_bar = self.create_title_bar()
        container_layout.addLayout(title_bar)
        
        # Mini controls (visible when collapsed)
        self.mini_controls = self.create_mini_controls()
        container_layout.addLayout(self.mini_controls)
        
        # Expanded content (hidden when collapsed)
        self.expanded_frame = QFrame()
        self.expanded_frame.setVisible(False)
        expanded_layout = QVBoxLayout(self.expanded_frame)
        expanded_layout.setContentsMargins(0, 0, 0, 0)
        expanded_layout.setSpacing(8)
        
        # Full controls
        full_controls = self.create_full_controls()
        expanded_layout.addLayout(full_controls)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setTextVisible(False)
        expanded_layout.addWidget(self.progress_bar)
        
        # Document area
        self.doc_area = QTextEdit()
        self.doc_area.setReadOnly(True)
        self.doc_area.setPlaceholderText("📄 Load a document or drag & drop a .md/.txt file...")
        expanded_layout.addWidget(self.doc_area)
        
        # Bottom actions
        bottom = self.create_bottom_actions()
        expanded_layout.addLayout(bottom)
        
        container_layout.addWidget(self.expanded_frame)
        
        # Apply styles
        self.apply_styles()
        
        # Initial size
        self.update_size()
        
        # Position bottom-right
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 80)
        
        # Accept drops
        self.setAcceptDrops(True)
        
    def create_title_bar(self):
        """Create the title bar"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        
        # Status dot
        self.status_dot = QLabel("●")
        self.status_dot.setFixedSize(14, 14)
        self.status_dot.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        layout.addWidget(self.status_dot)
        
        # Title
        self.title_label = QLabel("📄 Doc Reader")
        self.title_label.setStyleSheet(f"color: {COLORS['lime_primary']}; font-weight: bold;")
        layout.addWidget(self.title_label, 1)
        
        # Expand button
        self.expand_btn = QPushButton("⬆")
        self.expand_btn.setFixedSize(28, 28)
        self.expand_btn.clicked.connect(self.toggle_expand)
        self.expand_btn.setToolTip("Expand/Collapse")
        layout.addWidget(self.expand_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.hide)
        close_btn.setToolTip("Hide to tray")
        layout.addWidget(close_btn)
        
        return layout
        
    def create_mini_controls(self):
        """Create mini controls for collapsed mode"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        self.mini_play_btn = QPushButton("▶")
        self.mini_play_btn.setFixedSize(32, 32)
        self.mini_play_btn.clicked.connect(self.toggle_play)
        layout.addWidget(self.mini_play_btn)
        
        back_btn = QPushButton("⏪")
        back_btn.setFixedSize(32, 32)
        back_btn.clicked.connect(self.skip_back)
        layout.addWidget(back_btn)
        
        fwd_btn = QPushButton("⏩")
        fwd_btn.setFixedSize(32, 32)
        fwd_btn.clicked.connect(self.skip_forward)
        layout.addWidget(fwd_btn)
        
        layout.addStretch()
        
        return layout
        
    def create_full_controls(self):
        """Create full controls for expanded mode"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Row 1: Play controls
        row1 = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        row1.addWidget(self.play_btn)
        
        back_btn = QPushButton("⏪ -10s")
        back_btn.clicked.connect(self.skip_back)
        row1.addWidget(back_btn)
        
        fwd_btn = QPushButton("⏩ +10s")
        fwd_btn.clicked.connect(self.skip_forward)
        row1.addWidget(fwd_btn)
        
        stop_btn = QPushButton("⏹️")
        stop_btn.clicked.connect(self.stop_reading)
        row1.addWidget(stop_btn)
        
        layout.addLayout(row1)
        
        # Row 2: Voice selection
        row2 = QHBoxLayout()
        
        row2.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.load_voices()
        row2.addWidget(self.voice_combo, 1)
        
        layout.addLayout(row2)
        
        # Row 3: Speed
        row3 = QHBoxLayout()
        
        row3.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(300)
        self.speed_slider.setValue(175)
        self.speed_slider.valueChanged.connect(self.update_speed)
        row3.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1.0x")
        self.speed_label.setMinimumWidth(40)
        row3.addWidget(self.speed_label)
        
        load_btn = QPushButton("📁 Load")
        load_btn.clicked.connect(self.load_file)
        row3.addWidget(load_btn)
        
        layout.addLayout(row3)
        
        return layout
        
    def create_bottom_actions(self):
        """Create bottom action buttons"""
        layout = QHBoxLayout()
        
        summarize_btn = QPushButton("📝 Summarize")
        summarize_btn.clicked.connect(self.summarize)
        layout.addWidget(summarize_btn)
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self.copy_all)
        layout.addWidget(copy_btn)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_doc)
        layout.addWidget(export_btn)
        
        return layout
        
    def load_voices(self):
        """Load available TTS voices"""
        voices = self.tts_worker.get_voices()
        for voice in voices:
            name = voice.name.replace("Microsoft ", "")[:30]
            self.voice_combo.addItem(name, voice.id)
            
    def apply_styles(self):
        """Apply the hndl-it lime theme"""
        self.setStyleSheet(f"""
            QFrame#container {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['lime_primary']};
                border-radius: 12px;
            }}
            
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 12px;
            }}
            
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
                border-color: {COLORS['lime_primary']};
            }}
            
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                line-height: 1.6;
            }}
            
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['lime_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px 10px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QSlider::groove:horizontal {{
                background: {COLORS['border']};
                height: 6px;
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background: {COLORS['lime_primary']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            
            QProgressBar {{
                background: {COLORS['border']};
                border: none;
                border-radius: 2px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['lime_dim']}, stop:1 {COLORS['lime_primary']});
                border-radius: 2px;
            }}
        """)
        
    def update_size(self):
        """Update window size based on state"""
        if self.is_expanded:
            self.setFixedSize(500, 550)
        else:
            self.setFixedSize(220, 100)
            
    def toggle_expand(self):
        """Toggle between collapsed and expanded"""
        self.is_expanded = not self.is_expanded
        self.expanded_frame.setVisible(self.is_expanded)
        self.expand_btn.setText("⬇" if self.is_expanded else "⬆")
        self.update_size()
        
    def setup_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create icon (lime colored document)
        icon = QIcon()
        # Use a default icon for now
        self.tray_icon.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_FileDialogContentsView))
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction("📄 Show Reader", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("❌ Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_activated)
        self.tray_icon.show()
        
    def tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                
    # ========================================================================
    # TTS CONTROLS
    # ========================================================================
    
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.document_text:
            self.title_label.setText("📄 Load a document first!")
            return
            
        if self.tts_worker.is_playing:
            if self.tts_worker.is_paused:
                self.tts_worker.resume()
                self.update_play_buttons(True)
            else:
                self.tts_worker.pause()
                self.update_play_buttons(False, paused=True)
        else:
            self.start_reading()
            
    def start_reading(self):
        """Start reading the document"""
        self.tts_worker.set_text(self.document_text)
        self.tts_worker.set_rate(self.speed_slider.value())
        
        voice_id = self.voice_combo.currentData()
        if voice_id:
            self.tts_worker.set_voice(voice_id)
            
        self.update_play_buttons(True)
        self.status_dot.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px;")
        self.tts_worker.start()
        
    def stop_reading(self):
        """Stop reading"""
        self.tts_worker.stop()
        self.update_play_buttons(False)
        self.status_dot.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        self.progress_bar.setValue(0)
        
    def skip_forward(self):
        """Skip forward"""
        self.tts_worker.skip_forward()
        
    def skip_back(self):
        """Skip back"""
        self.tts_worker.skip_back()
        
    def update_play_buttons(self, playing: bool, paused: bool = False):
        """Update play button states"""
        if playing and not paused:
            self.play_btn.setText("⏸️ Pause")
            self.mini_play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶️ Play")
            self.mini_play_btn.setText("▶")
            
    def update_speed(self, value):
        """Update speed display"""
        rate = value / 175.0
        self.speed_label.setText(f"{rate:.1f}x")
        self.tts_worker.set_rate(value)
        
    def update_progress(self, current, total):
        """Update progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.title_label.setText(f"📄 {current}/{total}")
        
    def highlight_chunk(self, index):
        """Highlight current chunk being read"""
        # Could implement text highlighting here
        pass
        
    def on_finished(self):
        """Called when TTS finishes"""
        self.update_play_buttons(False)
        self.status_dot.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        self.title_label.setText("📄 Doc Reader")
        
    # ========================================================================
    # DOCUMENT HANDLING
    # ========================================================================
    
    def load_file(self):
        """Load a document file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "",
            "Text Files (*.md *.txt *.markdown);;All Files (*)"
        )
        
        if file_path:
            self.load_document(file_path)
            
    def load_document(self, file_path: str):
        """Load document from path"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.document_text = content
            
            # Convert markdown to HTML for display
            if file_path.endswith(('.md', '.markdown')):
                html = markdown.markdown(content)
                self.doc_area.setHtml(html)
            else:
                self.doc_area.setPlainText(content)
                
            # Update title
            name = Path(file_path).name[:20]
            self.title_label.setText(f"📄 {name}")
            
            # Auto-expand
            if not self.is_expanded:
                self.toggle_expand()
                
        except Exception as e:
            self.doc_area.setPlainText(f"Error loading file: {e}")
            
    def summarize(self):
        """Generate a simple summary"""
        if not self.document_text:
            return
            
        # Simple extractive summary - first 3 sentences
        sentences = re.split(r'(?<=[.!?])\s+', self.document_text)
        summary = ' '.join(sentences[:3])
        
        self.doc_area.setPlainText(f"📝 SUMMARY:\n\n{summary}\n\n---\n\n{self.document_text}")
        
    def copy_all(self):
        """Copy document to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.document_text or self.doc_area.toPlainText())
        self.title_label.setText("📋 Copied!")
        QTimer.singleShot(2000, lambda: self.title_label.setText("📄 Doc Reader"))
        
    def export_doc(self):
        """Export document"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Document", "exported_document.md",
            "Markdown (*.md);;Text (*.txt)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.document_text or self.doc_area.toPlainText())
            self.title_label.setText("📤 Exported!")
            QTimer.singleShot(2000, lambda: self.title_label.setText("📄 Doc Reader"))
            
    # ========================================================================
    # DRAG & DROP
    # ========================================================================
    
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handle file drop"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(('.md', '.txt', '.markdown')):
                self.load_document(file_path)
                break
                
    # ========================================================================
    # WINDOW DRAGGING
    # ========================================================================
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)


# ============================================================================
# MAIN ENTRY
# ============================================================================
def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    reader = DocumentReader()
    reader.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
