"""
hndl-it Suite Launcher
Launches all floating module icons in a vertical dock on the right side.
Refactored for modularity and plug-and-play architecture.
"""

import sys
import os
import logging
import subprocess
import atexit
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
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
# CONFIGURATION
# ============================================================================
LOCK_FILE = os.path.join(PROJECT_ROOT, "launch_suite.lock")

# ============================================================================
# UTILITIES
# ============================================================================
def check_singleton() -> bool:
    """Fail-safe singleton check."""
    try:
        import psutil
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                     # Check command line to be sure
                    try:
                        proc = psutil.Process(pid)
                        if 'launch_suite' in ' '.join(proc.cmdline()):
                            logger.error(f"⛔ Suite already running (PID {pid}).")
                            return False
                    except:
                        pass
            except:
                pass
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.warning(f"Singleton check warning: {e}")
        return True

def cleanup_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

def get_python_exe():
    """Get the best available python executable."""
    venvs = [
        os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe"),
        os.path.join(PROJECT_ROOT, ".venv", "bin", "python"),
    ]
    for path in venvs:
        if os.path.exists(path):
            return path
    return sys.executable

# ============================================================================
# UI COMPONENTS
# ============================================================================
class ModuleIcon(QWidget):
    """Generic floating icon for any module."""
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    
    def __init__(self, icon_name: str, fallback_letter: str = "?", border_color: str = "#e67e22"):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.size_val = 70
        self.setFixedSize(self.size_val, self.size_val)
        
        self.icon_path = os.path.join(PROJECT_ROOT, 'floater', 'assets', icon_name)
        self.fallback_letter = fallback_letter
        self.border_color = border_color
        
        self._drag_pos = QPoint()
        self._dragging = False
        self._drag_started = False
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Icon if exists
        if os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            if not pixmap.isNull():
                path = QPainterPath()
                path.addEllipse(0.0, 0.0, float(self.width()), float(self.height()))
                painter.setClipPath(path)
                painter.drawPixmap(self.rect(), pixmap)
                
                painter.setClipping(False)
                pen = QPen(QColor(self.border_color))
                pen.setWidth(3)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(pen)
                painter.drawEllipse(3, 3, self.width()-6, self.height()-6)
                return

        # Fallback
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

def add_context_menu(icon, name, app, hide_callback=None):
    icon.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    def show(pos):
        menu = QMenu()
        if hide_callback:
            menu.addAction(f"👁️ Hide {name}", hide_callback)
            menu.addSeparator()

        menu.addAction("♻️ Restart Suite", lambda: os.execl(sys.executable, sys.executable, *sys.argv))
        menu.addAction("❌ Close Suite", app.quit)
        menu.exec(icon.mapToGlobal(pos))
    icon.customContextMenuRequested.connect(show)


# ============================================================================
# MODULE INITIALIZERS
# ============================================================================
def init_hndl_it(app, icon):
    from floater.tray import FloaterTray
    from floater.console import ConsoleWindow
    
    console = ConsoleWindow()
    tray = FloaterTray(app)
    tray.console_window = console
    
    add_context_menu(icon, "hndl-it", app, lambda: tray.quick_dialog.hide())
    
    def toggle():
        if tray.quick_dialog.isVisible():
            tray.quick_dialog.hide()
        else:
            geo = icon.geometry()
            tray.quick_dialog.move(
                geo.left() - tray.quick_dialog.width(),
                geo.center().y() - (tray.quick_dialog.height() // 2)
            )
            tray.quick_dialog.show()
            tray.quick_dialog.activateWindow()
            tray.quick_dialog.input.setFocus()

    icon.clicked.connect(toggle)
    icon.double_clicked.connect(lambda: console.show() or console.raise_())
    return tray # Return main obj if needed

def init_read_it(app, icon):
    sys.path.insert(0, PROJECT_ROOT)
    from reading_pill import ReadingPill
    pill = ReadingPill()
    add_context_menu(icon, "read-it", app, lambda: pill.hide())
    icon.clicked.connect(lambda: pill.hide() if pill.isVisible() else pill.show())

def init_todo_it(app, icon):
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'todo-it'))
    from main import TodoItApp
    todo = TodoItApp()
    add_context_menu(icon, "todo-it", app, lambda: todo.panel.hide())
    
    def toggle():
        if todo.panel.isVisible():
            todo.panel.hide()
        else:
            todo.panel.move(icon.x() - todo.panel.width() - 10, icon.y())
            todo.panel.show_animated()
    icon.clicked.connect(toggle)
    return todo

def init_capture_it(app, icon):
    from floater.capture_tool import CapturePanel
    panel = CapturePanel(icon)
    add_context_menu(icon, "capture-it", app, lambda: panel.hide())
    
    def toggle():
        if panel.isVisible():
            panel.hide()
        else:
            panel.move(icon.x() - panel.width() - 10, icon.y())
            panel.show()
    icon.clicked.connect(toggle)

def init_voice_it(app, icon):
    from shared.voice_input import init_voice_input, VOICE_AVAILABLE
    from shared.voice_router import parse_voice_command, VoiceTarget
    
    add_context_menu(icon, "voice-it", app)
    
    if not VOICE_AVAILABLE:
        logger.warning("Voice unavailable")
        return

    # Helper to route voice commands (needs access to other modules instances effectively)
    # Ideally, this should use IPC broadcast, but for now we hook locally if possible
    # or rely on IPC handlers in other processes.
    
    def handle_voice(text):
        logger.info(f"🎤 Voice: {text}")
        result = parse_voice_command(text)
        # For now, just logging or basic IPC could go here.
        # The previous implementation had direct object references.
        # We will use IPC for robustness.
        from shared.ipc import route_intent
        # Mock intent
        route_intent({"target": result["target"], "action": "voice_command", "params": result})
        
    def handle_state(listening):
        icon.border_color = "#ff0000" if listening else "#ff00ff"
        icon.update()
        
    vi = init_voice_input(handle_voice, handle_state)
    
    icon.clicked.connect(lambda: vi.stop_listening() if vi.is_listening else vi._on_hotkey_pressed())
    icon.double_clicked.connect(lambda: vi.cancel_listening() if vi.is_listening else None)

def init_shed_it(app, icon):
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'floater', 'shed_it'))
    from main import ShedItApp
    shed = ShedItApp()
    add_context_menu(icon, "shed-it", app, lambda: shed.hide())
    icon.clicked.connect(lambda: shed.show() or shed.raise_())

def init_timer_it(app, icon):
    # Dynamic load for new module
    try:
        sys.path.insert(0, os.path.join(PROJECT_ROOT, 'floater', 'timer_it'))
        from main import TimerApp
        timer = TimerApp()
        add_context_menu(icon, "timer-it", app, lambda: timer.hide())
        
        def toggle():
            if timer.panel.isVisible():
                timer.panel.hide()
            else:
                timer.panel.move(icon.x() - timer.panel.width() - 10, icon.y())
                timer.panel.show()
        icon.clicked.connect(toggle)
    except ImportError:
        logger.warning("timer-it not found yet")


# ============================================================================
# MAIN LAUNCHER
# ============================================================================
def launch_all():
    if not check_singleton():
        sys.exit(1)
    
    atexit.register(cleanup_lock)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    screen = app.primaryScreen().availableGeometry()
    RIGHT_X = screen.width() - 80
    START_Y = 200
    SPACING = 90
    
    # MODULE REGISTRY
    MODULES = [
        {"id": "hndl-it", "icon": "hndl_it_icon.png", "l": "H", "c": "#00d4ff", "init": init_hndl_it},
        {"id": "shed-it", "icon": "shed_it_icon.png", "l": "S", "c": "#8888aa", "init": init_shed_it},
        {"id": "todo-it", "icon": "todo_it_icon.png", "l": "T", "c": "#00ff88", "init": init_todo_it},
        {"id": "capture", "icon": "capture_it_icon.png", "l": "📷", "c": "#ff0000", "init": init_capture_it},
        {"id": "voice",   "icon": "voice_it_icon.png", "l": "V", "c": "#ff00ff", "init": init_voice_it},
        {"id": "read-it", "icon": "read_it_icon.png", "l": "R", "c": "#00d4ff", "init": init_read_it},
        {"id": "timer",   "icon": "timer_it_icon.png", "l": "⏱️", "c": "#ffaa00", "init": init_timer_it},
    ]
    
    launched_widgets = []
    
    for i, mod in enumerate(MODULES):
        try:
            icon = ModuleIcon(mod["icon"], mod["l"], mod["c"])
            icon.move(RIGHT_X, START_Y + (SPACING * i))
            icon.show()

            # Initialize module logic
            if mod["init"]:
                mod["init"](app, icon)

            launched_widgets.append(icon) # Keep ref
            logger.info(f"✅ Loaded {mod['id']}")

        except Exception as e:
            logger.error(f"❌ Failed to load {mod['id']}: {e}")

    # BACKGROUND AGENTS
    agent_scripts = [
        ("read", os.path.join(PROJECT_ROOT, "read-it", "ipc_handler.py")),
        ("browser", os.path.join(PROJECT_ROOT, "agents", "browser", "ipc_handler.py")),
        ("brain", os.path.join(PROJECT_ROOT, "agents", "brain", "ipc_handler.py")),
        ("worker", os.path.join(PROJECT_ROOT, "agents", "worker", "ipc_handler.py")),
        ("systems", os.path.join(PROJECT_ROOT, "agents", "systems_engineer", "monitor.py")),
    ]
    
    # Check for local dump-it if exists
    local_dump = os.path.join(PROJECT_ROOT, "floater", "dump_it", "dump_agent.py")
    if os.path.exists(local_dump):
        agent_scripts.append(("dump-it", local_dump))

    python_exe = get_python_exe()
    agent_procs = []
    
    for name, script in agent_scripts:
        if os.path.exists(script):
            try:
                # Platform specific creation flags for hidden window
                flags = 0
                if sys.platform == "win32":
                    flags = subprocess.CREATE_NO_WINDOW

                p = subprocess.Popen([python_exe, script],
                                   creationflags=flags,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                agent_procs.append(p)
                logger.info(f"🤖 Agent started: {name}")
            except Exception as e:
                logger.error(f"⚠️ Agent failed: {name} - {e}")

    def kill_agents():
        for p in agent_procs:
            try:
                p.terminate()
            except:
                pass
    atexit.register(kill_agents)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_all()
