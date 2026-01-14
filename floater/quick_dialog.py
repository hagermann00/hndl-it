import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, 
    QPushButton, QLabel, QWidget, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QAction, QColor

logger = logging.getLogger("hndl-it.floater.dialog")

class QuickDialog(QDialog):
    command_submitted = pyqtSignal(str)
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("hndl-it")
        # Always on top, frameless, transparent background
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # State
        self.is_collapsed = False
        self.is_paused = False
        self.is_working = False
        self.is_ghost_mode = False  # Ghost mode: transparent + click-through
        self.is_click_through = False
        self.current_step = 0
        self.total_steps = 0
        
        # UI Modes
        self.UI_MODES = ["full", "bar", "pill", "panel", "tray"]
        self.current_mode_index = 0  # Start with full mode
        
        # Dimensions per mode
        self.mode_dimensions = {
            "full": (500, None),   # Full dialog
            "bar": (400, 40),      # Command bar
            "pill": (150, 35),     # Floating pill
            "panel": (180, 400),   # Side panel
            "tray": (500, 35),     # Status tray
        }
        
        # Dimensions
        self.expanded_width = 500
        self.collapsed_width = 200
        self.expanded_height = 300
        self.collapsed_height = 40
        
        self.setFixedWidth(self.expanded_width)
        
        self._setup_styles()
        self._setup_ui()
        
        # Activity pulse timer
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._pulse_activity)
        self.pulse_phase = 0
        
        # Draggable variables
        self._drag_pos = QPoint()
        
        # Apply initial mode
        # Apply initial mode - Start specific
        self.apply_mode("bar")
        self.collapse_to_input()

    def _setup_styles(self):
        # Warm orange/amber theme - NO blue/purple
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(25, 22, 20, 230);
                border: 3px solid rgba(255, 140, 50, 200);
                border-radius: 12px;
            }
            QDialog[collapsed="true"] {
                background-color: rgba(30, 25, 22, 200);
            }
            QLabel#Title {
                color: #ffffff;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#StatusLabel {
                color: rgba(255, 180, 100, 220);
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#ProgressLabel {
                color: #ff9944;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#ActivityDot {
                color: #ffaa44;
                font-size: 16px;
            }
            QLineEdit {
                padding: 10px;
                background-color: rgba(35, 30, 25, 220);
                border: 2px solid rgba(255, 140, 50, 150);
                color: #ffffff;
                border-radius: 6px;
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #ff9944;
                background-color: rgba(45, 38, 30, 240);
            }
            QTextEdit {
                background-color: rgba(30, 26, 22, 200);
                border: 1px solid rgba(255, 140, 50, 80);
                border-radius: 4px;
                color: rgba(255, 220, 180, 230);
                font-family: 'Consolas', monospace;
                font-size: 13px;
            }
            QPushButton#CloseBtn {
                background-color: transparent;
                color: rgba(255, 180, 120, 200);
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton#CloseBtn:hover {
                color: #ff6666;
            }
            QPushButton#PauseBtn {
                background-color: rgba(50, 40, 30, 200);
                color: #ffaa66;
                border: 1px solid rgba(255, 140, 50, 150);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton#PauseBtn:hover {
                background-color: rgba(70, 55, 40, 220);
            }
            QProgressBar {
                border: none;
                background-color: rgba(40, 35, 30, 150);
                height: 4px;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #ff9944;
                border-radius: 2px;
            }
            QPushButton#ModeBtn, QPushButton#ClickThroughBtn, QPushButton#SettingsBtn {
                background-color: rgba(50, 40, 30, 200);
                color: rgba(255, 180, 120, 200);
                border: 1px solid rgba(255, 140, 50, 150);
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton#ModeBtn:hover, QPushButton#ClickThroughBtn:hover, QPushButton#SettingsBtn:hover {
                background-color: rgba(70, 55, 40, 220);
                color: #ffffff;
            }
        """)

    def _setup_ui(self):
        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Title Bar (Always Visible) ---
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet("background-color: rgba(22, 32, 26, 240); border-top-left-radius: 12px; border-top-right-radius: 12px;")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)
        
        # Agent status indicators (3 dots: Browser, Desktop, Vision)
        # Colors: Green=connected+idle, Pulsing=working, Red=offline, Yellow=trouble
        self.agent_dots = {}
        for agent_name, tooltip in [("browser", "Browser"), ("desktop", "Desktop"), ("vision", "Vision")]:
            dot = QLabel("●")
            dot.setObjectName(f"AgentDot_{agent_name}")
            dot.setFixedWidth(16)
            dot.setStyleSheet("color: #666;")  # Offline = gray
            dot.setToolTip(f"{tooltip}: Offline")
            title_layout.addWidget(dot)
            self.agent_dots[agent_name] = {"widget": dot, "connected": False, "working": False}
        
        title_layout.addSpacing(5)
        
        # Title
        self.title_label = QLabel("hndl-it")
        self.title_label.setObjectName("Title")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # Progress label (e.g., "2/5")
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("ProgressLabel")
        title_layout.addWidget(self.progress_label)
        
        # Pause/Resume button
        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setObjectName("PauseBtn")
        self.pause_btn.setFixedSize(30, 20)
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.pause_btn.hide()  # Only show when working
        title_layout.addWidget(self.pause_btn)
        
        # Mode switcher button (protected - always clickable)
        self.mode_btn = QPushButton("◐")
        self.mode_btn.setObjectName("ModeBtn")
        self.mode_btn.setFixedSize(25, 20)
        self.mode_btn.setToolTip("Switch UI mode")
        self.mode_btn.clicked.connect(self.cycle_mode)
        title_layout.addWidget(self.mode_btn)
        
        # Click-through toggle button (protected - always clickable)
        self.clickthrough_btn = QPushButton("👆")
        self.clickthrough_btn.setObjectName("ClickThroughBtn")
        self.clickthrough_btn.setFixedSize(25, 20)
        self.clickthrough_btn.setToolTip("Toggle transparency")
        self.clickthrough_btn.clicked.connect(self.toggle_click_through)
        title_layout.addWidget(self.clickthrough_btn)
        
        # Settings button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setFixedSize(25, 20)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        title_layout.addWidget(self.settings_btn)
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.hide)
        title_layout.addWidget(self.close_btn)
        
        self.main_layout.addWidget(self.title_bar)
        
        # --- Progress Bar (Mini, below title) ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)
        
        # --- Content Area (Collapsible) ---
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(15, 10, 15, 15)
        content_layout.setSpacing(10)
        
        # Status label (natural language)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        content_layout.addWidget(self.status_label)
        
        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command...")
        self.input.returnPressed.connect(self.submit)
        content_layout.addWidget(self.input)
        
        # Log/Output area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(120)  # Reduced to make room for A2UI
        content_layout.addWidget(self.log_area)
        
        # A2UI Render Zone - for rich agent UI output
        from .a2ui_renderer import A2UIRenderer
        self.a2ui_zone = A2UIRenderer()
        self.a2ui_zone.setFixedHeight(150)
        self.a2ui_zone.action_triggered.connect(self._handle_a2ui_action)
        content_layout.addWidget(self.a2ui_zone)
        
        # System Monitor
        from .system_monitor import SystemMonitor
        self.sys_monitor = SystemMonitor()
        content_layout.addWidget(self.sys_monitor)
        
        self.main_layout.addWidget(self.content_widget)
        self.setLayout(self.main_layout)

    def _toggle_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.setText("⏸")
            self.resume_requested.emit()
            self.set_status("Resumed...")
        else:
            self.is_paused = True
            self.pause_btn.setText("▶")
            self.pause_requested.emit()
            self.set_status("Paused - Click ▶ to resume")

    def set_working(self, working: bool):
        """Set working state - shows/hides activity indicators."""
        self.is_working = working
        if working:
            self.pulse_timer.start(300)  # Pulse every 300ms
            self.pause_btn.show()
            self.progress_bar.show()
        else:
            self.pulse_timer.stop()
            self.pause_btn.hide()
            self.progress_bar.hide()
            self.progress_bar.setValue(0)
            self.progress_label.setText("")
            # Reset all working states
            for agent, dot_info in self.agent_dots.items():
                if dot_info["connected"]:
                    dot_info["working"] = False
                    dot_info["widget"].setStyleSheet("color: #44ff66;")

    def set_progress(self, current: int, total: int, status_text: str = None):
        """Update progress display."""
        self.current_step = current
        self.total_steps = total
        
        if total > 0:
            self.progress_label.setText(f"{current}/{total}")
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        
        if status_text:
            self.set_status(status_text)

    def set_status(self, text: str):
        """Set natural language status."""
        self.status_label.setText(text)

    def set_agent_status(self, agent: str, connected: bool, working: bool = False):
        """Update an agent's status indicator.
        
        Colors:
        - Gray (#666): Offline
        - Green (#44ff66): Connected + Idle  
        - Pulsing Orange: Connected + Working
        - Red (#ff4444): Error/Trouble
        """
        if agent not in self.agent_dots:
            return
            
        dot_info = self.agent_dots[agent]
        dot_info["connected"] = connected
        dot_info["working"] = working
        dot = dot_info["widget"]
        
        tooltip_name = agent.capitalize()
        
        if not connected:
            dot.setStyleSheet("color: #666;")
            dot.setToolTip(f"{tooltip_name}: Offline")
        elif working:
            # Will be pulsed by timer
            dot.setToolTip(f"{tooltip_name}: Working...")
        else:
            dot.setStyleSheet("color: #44ff66;")
            dot.setToolTip(f"{tooltip_name}: Connected")

    def _pulse_activity(self):
        """Animate working agent dots with pulsing effect."""
        self.pulse_phase = (self.pulse_phase + 1) % 4
        pulse_colors = ["#ffaa44", "#ff8822", "#ff6600", "#ff8822"]  # Orange pulse
        
        for agent, dot_info in self.agent_dots.items():
            if dot_info["working"] and dot_info["connected"]:
                dot_info["widget"].setStyleSheet(f"color: {pulse_colors[self.pulse_phase]};")


    def toggle_collapsed(self):
        """Toggle between collapsed and expanded mode."""
        if self.is_collapsed:
            # Expand
            self.content_widget.show()
            self.setFixedWidth(self.expanded_width)
            self.setProperty("collapsed", False)
            self.is_collapsed = False
        else:
            # Collapse
            self.content_widget.hide()
            self.setFixedWidth(self.collapsed_width)
            self.setProperty("collapsed", True)
            self.is_collapsed = True
        
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        """Allow dragging from anywhere on the window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Double-click on title bar to toggle collapse
            if self.title_bar.geometry().contains(event.pos()):
                self.toggle_collapsed()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()

    def closeEvent(self, event):
        """Ignore close events (minimize to tray instead)."""
        event.ignore()
        self.hide()

    def showEvent(self, event):
        """Force window to stay on top using Windows API."""
        super().showEvent(event)
        try:
            import ctypes
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE
            )
        except Exception as e:
            logger.warning(f"Could not set topmost: {e}")
        
    def submit(self):
        text = self.input.text()
        if text:
            self.expand_to_log()  # Auto-expand on submit
            self.add_log(f"> {text}")
            self.command_submitted.emit(text)
            self.input.clear()
            
    def add_log(self, message):
        self.log_area.append(message)
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def collapse_to_input(self):
        """Show only input field."""
        self.log_area.hide()
        self.status_label.hide()
        # Keep width, shrink height
        self.setFixedSize(self.width(), 75) 
    
    def expand_to_log(self):
        """Show full log area."""
        self.log_area.show()
        self.status_label.show()
        # Keep width, grow height
        self.setFixedSize(self.width(), 320)

    def toggle_ghost_mode(self):
        """Toggle ghost mode: transparent + click-through vs normal."""
        self.is_ghost_mode = not self.is_ghost_mode
        
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            
            if self.is_ghost_mode:
                # GHOST MODE: Transparent, click-through
                self.setWindowOpacity(0.3)
                
                # Enable click-through
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
                
                self.title_label.setText("hndl-it 👻")
            else:
                # NORMAL MODE: Full opacity, interactive
                self.setWindowOpacity(1.0)
                
                # Disable click-through
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT)
                
                self.title_label.setText("hndl-it")
                
        except Exception as e:
            logger.warning(f"Ghost mode toggle failed: {e}")

    def set_opacity(self, opacity: float):
        """Set window opacity (0.0 to 1.0)."""
        self.setWindowOpacity(max(0.1, min(1.0, opacity)))

    def cycle_mode(self):
        """Cycle through UI modes: full → bar → pill → panel → tray → full"""
        self.current_mode_index = (self.current_mode_index + 1) % len(self.UI_MODES)
        mode = self.UI_MODES[self.current_mode_index]
        self.apply_mode(mode)
        self.add_log(f"Mode: {mode.upper()}")

    def apply_mode(self, mode: str):
        """Apply a specific UI mode."""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        if mode == "full":
            # Full dialog - standard view, centered
            self.content_widget.show()
            self.content_widget.layout().setContentsMargins(15, 10, 15, 15)
            self.setFixedSize(500, 320)
            self.title_label.setText("hndl-it")
            self.input.show()
            self.log_area.show()
            self.status_label.show()
            # Center on screen
            self.move((screen.width() - 500) // 2, (screen.height() - 320) // 2)
            
        elif mode == "bar":
            # Command bar - horizontal with input
            self.content_widget.show()
            self.log_area.hide()
            self.status_label.hide()
            self.input.show()
            self.content_widget.layout().setContentsMargins(5, 2, 5, 5)
            self.setFixedSize(450, 75)  # Taller to fit input properly
            self.title_label.setText("⌨")
            # Move to top center
            self.move((screen.width() - 450) // 2, 10)
            
        elif mode == "pill":
            # Floating pill - small but with input
            self.content_widget.show()
            self.log_area.hide()
            self.status_label.hide()
            self.input.show()
            self.content_widget.layout().setContentsMargins(5, 2, 5, 5)
            self.setFixedSize(250, 75)  # Wider and taller for input
            self.title_label.setText("●")
            # Move to top right
            self.move(screen.width() - 270, 10)
            
        elif mode == "panel":
            # Side panel - vertical, docked right
            self.content_widget.show()
            self.log_area.show()
            self.status_label.show()
            self.input.show()
            self.content_widget.layout().setContentsMargins(8, 5, 8, 8)
            self.setFixedSize(220, 400)
            self.title_label.setText("▌")
            # Dock to right edge
            self.move(screen.width() - 230, (screen.height() - 400) // 2)
            
        elif mode == "tray":
            # Status tray - horizontal bar with input at bottom
            self.content_widget.show()
            self.log_area.hide()
            self.status_label.hide()
            self.input.show()
            self.content_widget.layout().setContentsMargins(5, 2, 5, 5)
            self.setFixedSize(500, 75)
            self.title_label.setText("hndl-it")
            # Move to bottom center
            self.move((screen.width() - 500) // 2, screen.height() - 60)

    def toggle_click_through(self):
        """Toggle transparency mode (keeps buttons clickable)."""
        self.is_click_through = not self.is_click_through
        
        if self.is_click_through:
            # Semi-transparent mode (but still clickable!)
            self.setWindowOpacity(0.3)
            self.clickthrough_btn.setText("👻")
            self.clickthrough_btn.setToolTip("Transparent mode ON")
        else:
            # Normal opacity
            self.setWindowOpacity(1.0)
            self.clickthrough_btn.setText("👆")
            self.clickthrough_btn.setToolTip("Transparent mode OFF")

    def open_settings(self):
        """Open the settings dialog."""
        from .settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.apply_settings)
        dialog.exec()
    
    def apply_settings(self, settings: dict):
        """Apply settings from the settings dialog."""
        # Apply theme (would need to regenerate stylesheet)
        theme = settings.get("theme", "orange")
        self.add_log(f"Theme: {theme} (restart to apply)")
        
        # Apply default mode
        mode = settings.get("default_mode", "full")
        self.apply_mode(mode)
        
        # Store settings for reference
        self.current_settings = settings
        self.add_log("Settings saved!")

    def _handle_a2ui_action(self, action: str, payload: dict):
        """Handle actions triggered from A2UI buttons."""
        logger.info(f"A2UI action: {action} with payload: {payload}")
        self.add_log(f"[A2UI] {action}: {payload}")
        
        # Route common actions
        if action == "expand_result":
            entity_id = payload.get("entity_id", "")
            self.add_log(f"Expanding result: {entity_id}")
            # TODO: Fetch full content from Airweave and display
        elif action == "search_again":
            query = payload.get("query", "")
            if query:
                self.input.setText(query)
                self.submit()
        else:
            # Emit as command for orchestrator to handle
            self.command_submitted.emit(f"a2ui:{action}:{payload}")

    def render_a2ui(self, a2ui_payload: dict):
        """Render an A2UI component tree in the A2UI zone."""
        if hasattr(self, 'a2ui_zone'):
            self.a2ui_zone.render(a2ui_payload)
            self.add_log("[A2UI] Rendered component")
        else:
            logger.warning("A2UI zone not initialized")

    def clear_a2ui(self):
        """Clear the A2UI render zone."""
        if hasattr(self, 'a2ui_zone'):
            self.a2ui_zone.clear()
