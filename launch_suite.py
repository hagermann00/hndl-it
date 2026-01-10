"""
hndl-it Suite Launcher
Launches all floating module icons in a vertical dock on the right side.

Modules:
- hndl-it (main router)
- read-it (TTS reader)
- todo-it (task manager)
"""

import sys
import os
import logging

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF, QThread
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QPixmap, QPainterPath

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hndl-it.launcher")


# ============================================================================
# GENERIC FLOATING ICON - Reusable for all modules
# ============================================================================
class ModuleIcon(QWidget):
    """Generic floating icon for any module."""
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    
    def __init__(self, icon_path: str = None, fallback_letter: str = "?", border_color: str = "#e67e22"):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.size_val = 60
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
        
        if self.icon_path and os.path.exists(self.icon_path):
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
            font.setPointSize(18)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.fallback_letter)
    
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


def launch_all():
    """Launch all modules with stacked floating icons."""
    logger.info("🚀 Starting hndl-it Suite...")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    screen_geo = app.primaryScreen().availableGeometry()
    RIGHT_X = screen_geo.width() - 80
    START_Y = 290
    SPACING = 80
    
    modules = []
    
    # ========== 1. HNDL-IT (Main Router) ==========
    try:
        from floater.tray import FloaterTray
        from floater.console import ConsoleWindow
        
        console = ConsoleWindow()
        tray = FloaterTray(app)
        tray.console_window = console
        
        hndl_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'hndl_it_icon.png'),
            fallback_letter="H",
            border_color="#00d4ff"  # Cyan
        )
        hndl_icon.move(RIGHT_X, START_Y)
        hndl_icon.show()
        
        # Context Menu for Restart/Close
        hndl_icon.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        def restart_suite():
            logger.info("♻️ Restarting Suite...")
            import sys
            import os
            # Relaunch current script
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        def show_context_menu(pos):
            menu = QMenu()
            
            restart_action = QAction("♻️ Restart Suite", hndl_icon)
            restart_action.triggered.connect(restart_suite)
            
            close_action = QAction("❌ Close Suite", hndl_icon)
            close_action.triggered.connect(app.quit)
            
            menu.addAction(restart_action)
            menu.addSeparator()
            menu.addAction(close_action)
            
            menu.exec(hndl_icon.mapToGlobal(pos))
            
        hndl_icon.customContextMenuRequested.connect(show_context_menu)
        
        def toggle_hndl_input():
            if tray.quick_dialog.isVisible():
                tray.quick_dialog.hide()
            else:
                geo = hndl_icon.geometry()
                x = geo.left() - tray.quick_dialog.width() - 10
                y = geo.top() - 150  # Up and to the left
                
                if x < 0:
                    x = geo.right() + 10
                
                tray.quick_dialog.move(x, y)
                tray.quick_dialog.show()
                tray.quick_dialog.activateWindow()
                tray.quick_dialog.input.setFocus()
        
        hndl_icon.clicked.connect(toggle_hndl_input)
        hndl_icon.double_clicked.connect(lambda: console.show() or console.raise_())
        
        modules.append(("hndl-it", hndl_icon))
        logger.info("✅ hndl-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load hndl-it: {e}")
        import traceback
        traceback.print_exc()
    
    # ========== 2. READ-IT (TTS Reader) ==========
    try:
        # Import components directly, not the app
        sys.path.insert(0, os.path.join(PROJECT_ROOT, 'read-it'))
        
        # Import just what we need
        import importlib.util
        spec = importlib.util.spec_from_file_location("readit", os.path.join(PROJECT_ROOT, 'read-it', 'main.py'))
        readit_module = importlib.util.module_from_spec(spec)
        
        # Don't execute main, just define the classes
        exec(open(os.path.join(PROJECT_ROOT, 'read-it', 'main.py')).read().split('def main():')[0], readit_module.__dict__)
        
        FloatingIcon = readit_module.FloatingIcon
        ReaderPanel = readit_module.ReaderPanel
        PlaybackOverlay = readit_module.PlaybackOverlay
        SelectionPill = readit_module.SelectionPill
        SelectionMonitor = readit_module.SelectionMonitor
        
        read_icon = FloatingIcon()
        read_icon.move(RIGHT_X, START_Y + SPACING)
        read_icon.show()
        
        read_panel = ReaderPanel()
        playback_overlay = PlaybackOverlay(read_icon)
        pill = SelectionPill()
        
        # Selection monitor
        selection_monitor = SelectionMonitor()
        selection_monitor.text_selected.connect(pill.show_at_cursor)
        selection_monitor.start()
        
        def toggle_read_panel():
            if read_panel.isVisible():
                read_panel.hide()
            else:
                read_panel.move(read_icon.x() - read_panel.width() - 10, read_icon.y() - 150)
                read_panel.show()
        
        def read_text(text):
            read_panel.text_edit.setText(text)
            read_panel.start_reading()
            playback_overlay.set_playing(True)
            playback_overlay.show_near_icon()
        
        read_icon.clicked.connect(toggle_read_panel)
        pill.read_requested.connect(read_text)
        pill.summary_requested.connect(lambda t: read_text(f"Summary: {t[:200]}..."))
        
        modules.append(("read-it", read_icon))
        logger.info("✅ read-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load read-it: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback - simple icon
        read_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'read-it', 'assets', 'icon.png'),
            fallback_letter="R",
            border_color="#e67e22"
        )
        read_icon.move(RIGHT_X, START_Y + SPACING)
        read_icon.show()
        modules.append(("read-it (basic)", read_icon))
    
    # ========== 3. TODO-IT (Task Manager) ==========
    try:
        sys.path.insert(0, os.path.join(PROJECT_ROOT, 'todo-it'))
        from main import TodoItApp
        
        todo_app = TodoItApp()
        
        todo_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'todo_it_icon.png'),
            fallback_letter="T",
            border_color="#00ff88"  # Green
        )
        todo_icon.move(RIGHT_X, START_Y + SPACING * 2)
        todo_icon.show()
        
        todo_icon.clicked.connect(lambda: todo_app.panel.show() or todo_app.panel.raise_())
        
        modules.append(("todo-it", todo_icon))
        logger.info("✅ todo-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load todo-it: {e}")
        import traceback
        traceback.print_exc()
    
    # ========== 4. Voice Input (Global Hotkey + Icon) ==========
    try:
        from shared.voice_input import init_voice_input, VOICE_AVAILABLE, get_voice_input
        from shared.voice_router import parse_voice_command, VoiceTarget
        
        # Create Icon First
        voice_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'voice_it_icon.png'),
            fallback_letter="V",
            border_color="#ff00ff"  # Magenta
        )
        voice_icon.move(RIGHT_X, START_Y + SPACING * 3)
        voice_icon.show()
        
        modules.append(("voice-it", voice_icon))
        
        if VOICE_AVAILABLE:
            def handle_voice(text):
                logger.info(f"🎤 Voice: {text}")
                result = parse_voice_command(text)
                
                if result["target"] == VoiceTarget.TODO_IT:
                    try:
                        # todo_app is captured from enclosing scope
                        if todo_app:
                            todo_app.panel.add_todo(result.get('todo_text', text))
                            todo_app.panel.show()
                    except Exception as e:
                        logger.error(f"Failed to route to todo-it: {e}")
                else:
                    try:
                        if tray:
                            tray.quick_dialog.input.setText(text)
                            toggle_hndl_input()
                    except Exception as e:
                        logger.error(f"Failed to route to hndl-it: {e}")
            
            def handle_listening(is_listening):
                logger.info(f"🎤 Listening state: {is_listening}")
                # Visual feedback on icon
                if is_listening:
                    voice_icon.border_color = "#ff0000"  # Red when recording
                    voice_icon.update()
                else:
                    voice_icon.border_color = "#ff00ff"  # Back to Magenta
                    voice_icon.update()
            
            vi = init_voice_input(handle_voice, handle_listening)
            
            # Click to toggle listening
            def toggle_voice():
                if vi.is_listening:
                    vi.cancel_listening()
                else:
                    vi._on_hotkey_pressed()
            
            voice_icon.clicked.connect(toggle_voice)
            
            # --- Bonus Hotkeys ---
            try:
                import keyboard
                # "The other two are for native dictation" -> Simulating Win+H
                keyboard.add_hotkey("ctrl+windows+alt", lambda: keyboard.send("windows+h"))
                logger.info("✅ Native Dictation shortcut (Ctrl+Win+Alt -> Win+H) active")
            except Exception as e:
                logger.warning(f"Failed to register native hotkeys: {e}")

            logger.info("✅ Voice input ready (Ctrl+Shift+Win or Click Icon)")
        else:
            logger.warning("⚠️ Voice input unavailable")
            
    except Exception as e:
        logger.warning(f"⚠️ Voice input setup failed: {e}")
    
    # ========== Summary ==========
    logger.info(f"🎯 Launched {len(modules)} modules:")
    for name, widget in modules:
        logger.info(f"   - {name} at ({widget.x()}, {widget.y()})")
    
    logger.info("=" * 50)
    logger.info("hndl-it Suite Ready!")
    logger.info("  • Click icons to interact")
    logger.info("  • Win+Alt for voice commands")
    logger.info("  • Right-click tray for menu")
    logger.info("=" * 50)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_all()
