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

from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF, QThread
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QPixmap, QPainterPath, QAction

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hndl-it.launcher")

# ============================================================================
# SINGLETON CHECK - Prevent multiple instances
# ============================================================================
LOCK_FILE = os.path.join(PROJECT_ROOT, "launch_suite.lock")

def check_singleton():
    """Fail-safe singleton check. Returns True if we can proceed, False if already running."""
    try:
        import psutil
        
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.read().strip())
                
                if psutil.pid_exists(pid):
                    # Check if it's actually a Python process running launch_suite
                    try:
                        proc = psutil.Process(pid)
                        cmdline = ' '.join(proc.cmdline())
                        if 'launch_suite' in cmdline:
                            logger.error(f"⛔ Suite already running (PID {pid}). Exiting.")
                            return False
                    except:
                        pass  # Process exists but we can't read it, assume stale
            except:
                pass  # Stale or corrupt lock file
        
        # Write our PID
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        return True
        
    except Exception as e:
        logger.warning(f"Singleton check failed (proceeding anyway): {e}")
        return True  # Fail-safe: if check fails, allow launch

def cleanup_lock():
    """Remove lock file on exit."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


# ============================================================================
# CONTEXT MENU HELPER - Adds right-click menu to any icon
# ============================================================================
def add_icon_context_menu(icon, module_name, app, hide_callback=None):
    """
    Add right-click context menu to an icon with:
    - Hide [Module] (if hide_callback provided)
    - Restart Suite
    - Close Suite
    """
    icon.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    
    def show_menu(pos):
        menu = QMenu()
        
        # Hide option (if callback provided)
        if hide_callback:
            hide_action = QAction(f"👁️ Hide {module_name}", icon)
            hide_action.triggered.connect(hide_callback)
            menu.addAction(hide_action)
            menu.addSeparator()
        
        # Restart Suite
        restart_action = QAction("♻️ Restart Suite", icon)
        restart_action.triggered.connect(lambda: os.execl(sys.executable, sys.executable, *sys.argv))
        menu.addAction(restart_action)
        
        # Close Suite
        close_action = QAction("❌ Close Suite", icon)
        close_action.triggered.connect(app.quit)
        menu.addAction(close_action)
        
        menu.exec(icon.mapToGlobal(pos))
    
    icon.customContextMenuRequested.connect(show_menu)


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
        
        if self.icon_path and os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            
            if not pixmap.isNull():
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
                return

        # Fallback gradient circle (if path missing or image invalid)
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
    
    # Singleton check - prevent duplicate instances
    if not check_singleton():
        logger.error("Aborting: Another instance is already running.")
        sys.exit(1)
    
    logger.info("🚀 Starting hndl-it Suite...")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Register cleanup on exit
    import atexit
    atexit.register(cleanup_lock)
    
    screen_geo = app.primaryScreen().availableGeometry()
    RIGHT_X = screen_geo.width() - 80
    START_Y = 290
    SPACING = 90
    
    modules = []
    
    # ========== 1. HNDL-IT (Main Router) ==========
    try:
        from floater.tray import FloaterTray
        from floater.console import ConsoleWindow
        from floater.capture_tool import CapturePanel
        
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
        add_icon_context_menu(hndl_icon, "hndl-it", app, hide_callback=lambda: tray.quick_dialog.hide())
        
        def toggle_hndl_input():
            if tray.quick_dialog.isVisible():
                tray.quick_dialog.hide()
            else:
                geo = hndl_icon.geometry()
                dialog_w = tray.quick_dialog.width()
                dialog_h = tray.quick_dialog.height()
                
                # Magnetic attachment: Right edge of dialog touches Left edge of icon
                x = geo.left() - dialog_w
                # Center vertically relative to icon
                y = geo.center().y() - (dialog_h // 2)
                
                # Debug logging
                logger.info(f"📍 Input Bar Positioning:")
                logger.info(f"   Icon geometry: {geo.x()}, {geo.y()}, {geo.width()}x{geo.height()}")
                logger.info(f"   Dialog size: {dialog_w}x{dialog_h}")
                logger.info(f"   Calculated position: ({x}, {y})")
                
                if x < 0:
                    x = geo.right() + 10
                    logger.info(f"   Adjusted X (off-screen fix): {x}")
                
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
        sys.path.insert(0, PROJECT_ROOT)
        from reading_pill import ReadingPill
        
        pill = ReadingPill()
        
        read_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'read_it_icon.png'),
            fallback_letter="R",
            border_color="#00d4ff" # Cyan
        )
        # Position at Slot 5 (0=Hndl, 1=Shed, 2=Todo, 3=Capture, 4=Voice, 5=Read)
        read_icon.move(RIGHT_X, START_Y + SPACING * 5)
        read_icon.show()
        
        def toggle_read():
            if pill.isVisible():
                pill.hide()
            else:
                pill.show()
                
        read_icon.clicked.connect(toggle_read)
        
        add_icon_context_menu(read_icon, "read-it", app, hide_callback=lambda: pill.hide())
        modules.append(("read-it", read_icon))
        logger.info("✅ read-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load read-it: {e}")
        import traceback
        traceback.print_exc()
    
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
        
        # TOGGLE LOGIC (Click to open/minimize)
        def toggle_todo():
            if todo_app.panel.isVisible():
                todo_app.panel.hide()
            else:
                todo_app.panel.move(todo_icon.x() - todo_app.panel.width() - 10, todo_icon.y())
                todo_app.panel.show_animated()
                
        todo_icon.clicked.connect(toggle_todo)
        
        # Context Menu
        add_icon_context_menu(todo_icon, "todo-it", app, hide_callback=lambda: todo_app.panel.hide())
        
        modules.append(("todo-it", todo_icon))
        logger.info("✅ todo-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load todo-it: {e}")
        import traceback
        traceback.print_exc()

    # ========== 3.5 CAPTURE-IT (Vision Tool) ==========
    try:
        capture_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'capture_it_icon.png'),
            fallback_letter="📷", 
            border_color="#ff0000"  # Red
        )
        capture_icon.move(RIGHT_X, START_Y + SPACING * 3)
        capture_icon.show()
        
        capture_panel = CapturePanel(capture_icon)
        
        def toggle_capture():
            if capture_panel.isVisible():
                capture_panel.hide()
            else:
                capture_panel.move(capture_icon.x() - capture_panel.width() - 10, capture_icon.y())
                capture_panel.show()
                
        capture_icon.clicked.connect(toggle_capture)
        add_icon_context_menu(capture_icon, "capture-it", app, hide_callback=lambda: capture_panel.hide())
        
        modules.append(("capture-it", capture_icon))
        logger.info("✅ capture-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load capture-it: {e}")
    
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
        # Create Icon First
        voice_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'voice_it_icon.png'),
            fallback_letter="V",
            border_color="#ff00ff"  # Magenta
        )
        voice_icon.move(RIGHT_X, START_Y + SPACING * 4)
        voice_icon.show()
        
        modules.append(("voice-it", voice_icon))
        
        # Context Menu (no hide_callback for voice - it's always visible)
        add_icon_context_menu(voice_icon, "voice-it", app)
        
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
                
                elif result["target"] == VoiceTarget.READ_IT:
                    try:
                        cmd = result["command"]
                        # Call global speak or read_it component
                        from shared.voice_output import speak
                        speak(cmd)
                        logger.info(f"🔊 Speaking: {cmd}")
                    except Exception as e:
                        logger.error(f"Failed to speak: {e}")

                elif "clean" in text.lower() or "storage" in text.lower():
                    try:
                        logger.info("🧹 Triggering Drive Cleanup...")
                        script = os.path.join(PROJECT_ROOT, "scripts", "drive_cleanup.py")
                        subprocess.Popen([sys.executable, script])
                        from shared.voice_output import speak
                        speak("Starting drive cleanup protocol")
                    except Exception as e:
                        logger.error(f"Failed to start cleanup: {e}")

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
            
            # Click to toggle listening (Click = Submit if running)
            def toggle_voice():
                if vi.is_listening:
                    # User requested 'Click should submit'
                    # Assuming vi has stop_listening() which processes buffer
                    if hasattr(vi, 'stop_listening'):
                        vi.stop_listening()
                    else:
                        vi.cancel_listening() # Fallback
                else:
                    vi._on_hotkey_pressed()
            
            voice_icon.clicked.connect(toggle_voice)
            
            # Double Click to Cancel
            voice_icon.double_clicked.connect(lambda: vi.cancel_listening() if vi.is_listening else None)
            
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
    
    # ========== 5. SHED-IT (The Repository) ==========
    try:
        sys.path.insert(0, os.path.join(PROJECT_ROOT, 'floater', 'shed_it'))
        from main import ShedItApp
        
        shed_app = ShedItApp()
        
        shed_icon = ModuleIcon(
            icon_path=os.path.join(PROJECT_ROOT, 'floater', 'assets', 'shed_it_icon.png'),
            fallback_letter="S",
            border_color="#8888aa"  # Grey/Silver
        )
        shed_icon.move(RIGHT_X, START_Y + SPACING * 1)
        shed_icon.show()
        
        shed_icon.clicked.connect(lambda: shed_app.show() or shed_app.raise_())
        
        # Context Menu
        add_icon_context_menu(shed_icon, "shed-it", app, hide_callback=lambda: shed_app.hide())
        
        modules.append(("shed-it", shed_icon))
        logger.info("✅ shed-it loaded")
        
    except Exception as e:
        logger.error(f"❌ Failed to load shed-it: {e}")
        import traceback
        traceback.print_exc()
    
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
    
    # ========== Start Agent Handlers ==========
    import subprocess
    agent_processes = []
    
    agent_scripts = [
        ("read", os.path.join(PROJECT_ROOT, "read-it", "ipc_handler.py")),
        ("browser", os.path.join(PROJECT_ROOT, "agents", "browser", "ipc_handler.py")),
        ("brain", os.path.join(PROJECT_ROOT, "agents", "brain", "ipc_handler.py")),
        ("systems_engineer", os.path.join(PROJECT_ROOT, "agents", "systems_engineer", "monitor.py")),
        ("dump-it", r"D:\iiWiiOperate-it_System\dump-it.py"),
        # ("desktop", os.path.join(PROJECT_ROOT, "agents", "desktop", "ipc_handler.py")),  # Needs pyautogui
    ]
    
    # Determine which Python to use (prefer the .venv)
    venv_python = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    
    for name, script in agent_scripts:
        if os.path.exists(script):
            try:
                proc = subprocess.Popen(
                    [python_exe, script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                agent_processes.append((name, proc))
                logger.info(f"✅ Started {name} agent (PID: {proc.pid}) using {python_exe}")

            except Exception as e:
                logger.warning(f"⚠️ Failed to start {name} agent: {e}")
    
    # Cleanup agents on exit
    import atexit
    def cleanup_agents():
        for name, proc in agent_processes:
            try:
                proc.terminate()
            except:
                pass
    atexit.register(cleanup_agents)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_all()
