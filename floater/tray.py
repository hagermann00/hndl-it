import os
import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread

from floater.quick_dialog import QuickDialog
from floater.client import MultiAgentClient # Changed

from floater.settings import SettingsDialog

logger = logging.getLogger("hndl-it.floater.tray")

class FloaterTray(QSystemTrayIcon):
    def __init__(self, app):
        super().__init__()
        self.app = app
        
        # Settings UI
        self.settings_dialog = SettingsDialog()
        
        # Load Icon
        icon_path = ""
        possible_icons = ["icon.jpg", "icon.png"]
        for fname in possible_icons:
            path = os.path.join(os.path.dirname(__file__), "assets", fname)
            if os.path.exists(path):
                icon_path = path
                break
                
        if icon_path:
            self.setIcon(QIcon(icon_path))
        else:
            logger.warning(f"Icon not found at {os.path.join(os.path.dirname(__file__), 'assets')}")
            
        self.setToolTip("hndl-it (Disconnected)")
        
        # UI Components
        self.quick_dialog = QuickDialog()
        self.quick_dialog.command_submitted.connect(self.on_command)
        
        # Network Client
        self.client_thread = QThread()
        self.client = MultiAgentClient() # Changed
        self.client.moveToThread(self.client_thread)
        self.client_thread.started.connect(self.client.start_client)
        
        # Connect signals
        self.client.message_received.connect(self.on_message)
        self.client.connection_status.connect(self.on_connection_status)
        self.client.agent_status.connect(self.on_agent_status)
        self.client.chain_progress.connect(self.on_chain_progress)
        self.client.floater_command.connect(self.on_floater_command)
        
        self.client_thread.start()
        
        # Menu
        self.menu = QMenu()
        
        self.action_show = QAction("Show Console", self)
        self.action_show.triggered.connect(self.on_show_console)
        self.menu.addAction(self.action_show)
        
        self.action_settings = QAction("Settings...", self)
        self.action_settings.triggered.connect(self.settings_dialog.show)
        self.menu.addAction(self.action_settings)
        
        self.menu.addSeparator()
        
        self.action_exit = QAction("Exit", self)
        self.action_exit.triggered.connect(self.app.quit)
        self.menu.addAction(self.action_exit)
        
        self.setContextMenu(self.menu)
        
        # Events
        self.activated.connect(self.on_activated)
        
        self.show()
        
        # Force show dialog on startup so user knows it's running
        # Use a timer to allow loop to start first
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, lambda: self.on_activated(QSystemTrayIcon.ActivationReason.Trigger))
        
        # IPC Response Listener - polls for responses from agents
        self.ipc_timer = QTimer()
        self.ipc_timer.timeout.connect(self.check_ipc_responses)
        self.ipc_timer.start(500)  # Check every 500ms
        
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single Click - Toggle Quick Dialog
            if self.quick_dialog.isVisible():
                self.quick_dialog.hide()
            else:
                self.quick_dialog.show()
                
                # Robust Positioning Logic
                from PyQt6.QtGui import QCursor
                screen = self.app.primaryScreen()
                avail_geo = screen.availableGeometry()
                cursor_pos = QCursor.pos()
                
                # Get window size (ensure it's realized)
                width = self.quick_dialog.width()
                height = self.quick_dialog.height()
                
                # Calculate Target X (Default: Centered on cursor, or Left-aligned if space permits?)
                # Strategy: Anchor Bottom-Right to Cursor, then shift if needed.
                # Actually, standard tray behavior is usually centered horizontally on icon, above icon.
                
                # X: Center on cursor
                target_x = cursor_pos.x() - (width // 2)
                
                # Clamp X
                if target_x < avail_geo.left():
                    target_x = avail_geo.left() + 5
                elif target_x + width > avail_geo.right():
                    target_x = avail_geo.right() - width - 5
                    
                # Y: Default to ABOVE cursor (assuming bottom tray)
                target_y = cursor_pos.y() - height - 10
                
                # If that pushes it off top, put it BELOW cursor
                if target_y < avail_geo.top():
                    target_y = cursor_pos.y() + 20 # Below cursor
                
                # Clamp Y High (Bottom edge check)
                if target_y + height > avail_geo.bottom():
                    target_y = avail_geo.bottom() - height - 5

                self.quick_dialog.move(target_x, target_y)
                
                self.quick_dialog.activateWindow()
                self.quick_dialog.raise_()
                self.quick_dialog.input.setFocus()
                
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double Click - Show Console (Stub)
            logger.info("Tray Double Click - Show Console")
            self.on_show_console()
            
    def on_show_console(self):
        logger.info("Show Console Requested")
        if hasattr(self, 'console_window'):
            self.console_window.show()
            self.console_window.raise_()
            self.console_window.activateWindow()

    def on_command(self, text):
        logger.info(f"Command: {text}")
        
        # Check for Saved Task Match first
        from floater.config import ConfigManager
        config = ConfigManager()
        tasks = config.get_tasks()
        
        # Case-insensitive match?
        matching_task = next((t for t in tasks if t["name"].lower() == text.strip().lower()), None)
        
        if matching_task:
            self.quick_dialog.add_log(f"⚡ Executing Task: {matching_task['name']}")
            for cmd in matching_task["commands"]:
                self.client.send_command(cmd)
        else:
            # Route through Orchestrator for semantic parsing
            try:
                from shared.orchestrator import get_orchestrator
                from shared.ipc import route_intent
                
                orchestrator = get_orchestrator()
                intent = orchestrator.process(text)
                
                # Log the intent
                target = intent.get("target", "unknown")
                action = intent.get("action", "unknown")
                confidence = intent.get("confidence", 0)
                method = intent.get("method", "unknown")
                
                self.quick_dialog.add_log(f"🎯 {target}/{action} (conf: {confidence:.0%}, via: {method})")
                
                # Route to appropriate module
                if route_intent(intent):
                    self.quick_dialog.add_log(f"✅ Routed to {target}")
                else:
                    self.quick_dialog.add_log(f"⚠️ Failed to route to {target}")
                    
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                self.quick_dialog.add_log(f"❌ Error: {e}")
                # Fallback to old behavior
                self.client.send_command(text)
        
    def on_message(self, message):
        logger.info(f"Received: {message}")
        try:
            data = json.loads(message)
            content = data.get("content", "")
            msg_type = data.get("type", "")
            
            if msg_type == "pong":
                return
                
            self.quick_dialog.add_log(f"[{msg_type}] {content}")
        except:
            self.quick_dialog.add_log(f"? {message}")
            
    def on_connection_status(self, connected):
        status = "Connected" if connected else "Disconnected"
        self.setToolTip(f"hndl-it ({status})")
        if connected:
            self.quick_dialog.add_log("✓ Connected to Agent")
        else:
            self.quick_dialog.add_log("⚠ Disconnected from Agent")

    def on_chain_progress(self, current, total, status_text):
        """Handle chain progress updates."""
        self.quick_dialog.set_working(True)
        self.quick_dialog.set_progress(current, total, status_text)
        
        if current >= total:
            self.quick_dialog.set_working(False)

    def on_floater_command(self, action):
        """Handle UI control commands."""
        if action == "toggle_ghost":
            self.quick_dialog.toggle_ghost_mode()
        else:
            logger.warning(f"Unknown floater action: {action}")

    def on_agent_status(self, agent_name, connected):
        """Handle per-agent connection status updates."""
        self.quick_dialog.set_agent_status(agent_name, connected)

    def check_ipc_responses(self):
        """Poll for IPC responses from agents (like Brain answers)."""
        try:
            from shared.ipc import check_mailbox
            
            action, payload = check_mailbox("floater")
            
            if action and payload:
                if action == "display":
                    msg_type = payload.get("type", "info")
                    
                    if msg_type == "answer":
                        question = payload.get("question", "")
                        answer = payload.get("answer", "")
                        self.quick_dialog.add_log(f"❓ {question}")
                        self.quick_dialog.add_log(f"💡 {answer}")
                        
                    elif msg_type == "error":
                        message = payload.get("message", "Unknown error")
                        self.quick_dialog.add_log(f"❌ {message}")
                        
                    else:
                        self.quick_dialog.add_log(f"📨 {payload}")
                        
        except Exception as e:
            logger.debug(f"IPC check error: {e}")
