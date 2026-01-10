"""
Reading Pill - Always-on-top floating pill that appears on text selection
Part of hndl-it system - Uses local Ollama for summarization, pyttsx3 for TTS

Features:
- Monitors clipboard for text selection anywhere on screen
- Shows compact pill with Play ▶ and Summarize 📝 buttons
- Auto-punctuates text using local LLM
- TTS powered by pyttsx3 (local-first)
- Summarization via Ollama (local-first)
"""

import sys
import os
import re
import pyttsx3
import threading
import requests
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QLabel,
    QPushButton, QSystemTrayIcon, QMenu, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QFont, QColor, QCursor, QAction, QClipboard

# ============================================================================
# BRAND COLORS - 4px Brighter Lime (2026 hndl-it Identity)
# ============================================================================
COLORS = {
    'bg_dark': '#1a1a1a',
    'bg_panel': '#252525',
    'lime_primary': '#84ff00',
    'lime_bright': '#9cff33',
    'lime_dim': '#5cb300',
    'lime_glow': 'rgba(132, 255, 0, 0.4)',
    'text_primary': '#e0e0e0',
    'text_secondary': '#888888',
    'border': '#3a3a3a',
}

# Ollama settings (local-first)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"  # Fast local model


# ============================================================================
# TTS ENGINE (Local)
# ============================================================================
class TTSEngine:
    """Local text-to-speech engine"""
    
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)
        self.is_speaking = False
        self._thread = None
        
    def speak(self, text: str):
        """Speak text in background thread"""
        if self.is_speaking:
            self.stop()
            
        self._thread = threading.Thread(target=self._speak_thread, args=(text,))
        self._thread.daemon = True
        self._thread.start()
        
    def _speak_thread(self, text: str):
        """Background speaking thread"""
        self.is_speaking = True
        self.engine.say(text)
        self.engine.runAndWait()
        self.is_speaking = False
        
    def stop(self):
        """Stop speaking"""
        self.engine.stop()
        self.is_speaking = False
        
    def set_rate(self, rate: int):
        """Set speech rate"""
        self.engine.setProperty('rate', rate)


# ============================================================================
# OLLAMA CLIENT (Local-First)
# ============================================================================
class OllamaClient:
    """Local Ollama client for summarization and punctuation"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def auto_punctuate(text: str) -> str:
        """Add proper punctuation to text using local LLM"""
        if not OllamaClient.is_available():
            return text
            
        prompt = f"""Fix the punctuation and capitalization of this text. 
Only return the corrected text, nothing else:

{text}"""
        
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("response", text).strip()
        except:
            pass
            
        return text
    
    @staticmethod
    def summarize(text: str) -> str:
        """Summarize text using local LLM"""
        if not OllamaClient.is_available():
            # Fallback: extractive summary
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return ' '.join(sentences[:3]) if sentences else text[:200]
            
        prompt = f"""Summarize this text in 2-3 concise sentences:

{text}

Summary:"""
        
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }, timeout=60)
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except:
            pass
            
        # Fallback
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return ' '.join(sentences[:3]) if sentences else text[:200]


# ============================================================================
# READING PILL WIDGET
# ============================================================================
class ReadingPill(QWidget):
    """Compact always-on-top pill that appears on text selection"""
    
    text_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.current_text = ""
        self.last_clipboard = ""
        self.tts = TTSEngine()
        self.drag_position = None
        self.is_processing = False
        
        self.init_ui()
        self.setup_clipboard_monitor()
        self.setup_tray()
        
    def init_ui(self):
        """Initialize the pill UI"""
        # Frameless, always on top, tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Fixed pill size
        self.setFixedSize(180, 44)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        
        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {COLORS['lime_dim']}; font-size: 8px;")
        layout.addWidget(self.status_dot)
        
        # Play button
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 32)
        self.play_btn.setToolTip("Read Aloud")
        self.play_btn.clicked.connect(self.play_text)
        layout.addWidget(self.play_btn)
        
        # Summarize button  
        self.summarize_btn = QPushButton("📝")
        self.summarize_btn.setFixedSize(36, 32)
        self.summarize_btn.setToolTip("Summarize & Read")
        self.summarize_btn.clicked.connect(self.summarize_and_play)
        layout.addWidget(self.summarize_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(36, 32)
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.clicked.connect(self.stop_playback)
        layout.addWidget(self.stop_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setToolTip("Hide")
        close_btn.clicked.connect(self.hide_pill)
        layout.addWidget(close_btn)
        
        # Apply styles
        self.apply_styles()
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Position at top-right
        self.position_pill()
        
    def apply_styles(self):
        """Apply hndl-it lime theme"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['lime_primary']};
                border-radius: 22px;
            }}
            
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['lime_primary']};
                border: 1px solid {COLORS['lime_dim']};
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {COLORS['lime_dim']};
                color: {COLORS['bg_dark']};
            }}
            
            QPushButton:pressed {{
                background-color: {COLORS['lime_primary']};
            }}
        """)
        
    def position_pill(self):
        """Position pill at top-right of screen"""
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = 60  # Below typical taskbar
        self.move(x, y)
        
    def setup_clipboard_monitor(self):
        """Setup clipboard monitoring for text selection"""
        self.clipboard = QApplication.clipboard()
        self.clipboard.changed.connect(self.on_clipboard_change)
        
        # Also poll periodically for selection changes
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_selection)
        self.poll_timer.start(500)  # Check every 500ms
        
    def on_clipboard_change(self, mode):
        """Handle clipboard changes"""
        if mode == QClipboard.Mode.Clipboard:
            self.check_clipboard()
            
    def check_clipboard(self):
        """Check clipboard for new text"""
        text = self.clipboard.text()
        
        if text and text != self.last_clipboard and len(text) > 10:
            self.last_clipboard = text
            self.current_text = text
            self.show_pill()
            
    def check_selection(self):
        """Check for text selection (platform specific)"""
        # On Windows, we mainly rely on clipboard
        # User copies text with Ctrl+C, pill appears
        pass
        
    def show_pill(self):
        """Show the pill with animation"""
        self.status_dot.setStyleSheet(f"color: {COLORS['lime_primary']}; font-size: 8px;")
        self.show()
        self.raise_()
        
        # Auto-hide after 30 seconds if not used
        QTimer.singleShot(30000, self.auto_hide)
        
    def hide_pill(self):
        """Hide the pill"""
        self.status_dot.setStyleSheet(f"color: {COLORS['lime_dim']}; font-size: 8px;")
        self.hide()
        
    def auto_hide(self):
        """Auto-hide if not playing"""
        if not self.tts.is_speaking and not self.is_processing:
            self.hide_pill()
            
    def play_text(self):
        """Play the current text with auto-punctuation"""
        if not self.current_text:
            return
            
        self.status_dot.setStyleSheet(f"color: #44ff66; font-size: 8px;")  # Green = playing
        
        # Auto-punctuate in background then speak
        def process_and_speak():
            text = OllamaClient.auto_punctuate(self.current_text)
            self.tts.speak(text)
            
        thread = threading.Thread(target=process_and_speak)
        thread.daemon = True
        thread.start()
        
    def summarize_and_play(self):
        """Summarize text and play the summary"""
        if not self.current_text:
            return
            
        self.is_processing = True
        self.status_dot.setStyleSheet(f"color: #ffaa00; font-size: 8px;")  # Orange = processing
        self.summarize_btn.setText("⏳")
        
        def process_and_speak():
            summary = OllamaClient.summarize(self.current_text)
            self.tts.speak(f"Summary: {summary}")
            self.is_processing = False
            # Reset button
            QTimer.singleShot(0, lambda: self.summarize_btn.setText("📝"))
            QTimer.singleShot(0, lambda: self.status_dot.setStyleSheet(
                f"color: #44ff66; font-size: 8px;"))
            
        thread = threading.Thread(target=process_and_speak)
        thread.daemon = True
        thread.start()
        
    def stop_playback(self):
        """Stop current playback"""
        self.tts.stop()
        self.status_dot.setStyleSheet(f"color: {COLORS['lime_primary']}; font-size: 8px;")
        
    def setup_tray(self):
        """Setup system tray icon"""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_MediaVolume))
        self.tray.setToolTip("Reading Pill - hndl-it")
        
        menu = QMenu()
        
        show_action = QAction("📖 Show Pill", self)
        show_action.triggered.connect(self.show_pill)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        quit_action = QAction("❌ Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r: self.show_pill() 
            if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()
        
    # ========================================================================
    # DRAGGING
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
# MAIN
# ============================================================================
def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Check Ollama status
    if OllamaClient.is_available():
        print("✅ Ollama available - Full AI features enabled")
    else:
        print("⚠️ Ollama not available - Using fallback mode")
    
    pill = ReadingPill()
    pill.show()
    
    print("📖 Reading Pill active!")
    print("   Copy text (Ctrl+C) anywhere to activate")
    print("   ▶ = Read aloud | 📝 = Summarize & read")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
