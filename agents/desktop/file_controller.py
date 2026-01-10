import os
import logging
from typing import List, Optional

logger = logging.getLogger("FileController")
logger.setLevel(logging.INFO)

class FileController:
    def open_path(self, path: str) -> str:
        """
        Opens a file or directory using the default Windows application.
        Equivalent to double-clicking in Explorer.
        """
        path = os.path.abspath(path)
        if not os.path.exists(path):
            # Try appending c:\ if missing? No, stay strict first.
            raise FileNotFoundError(f"Path not found: {path}")

        logger.info(f"Opening path: {path}")
        try:
            os.startfile(path)
            return f"Opened: {path}"
        except Exception as e:
            logger.error(f"Failed to open {path}: {e}")
            raise

    def list_dir(self, path: str) -> List[str]:
        """Lists directory contents."""
        path = os.path.abspath(path)
        if not os.path.exists(path):
             raise FileNotFoundError(f"Path not found: {path}")
             
        items = os.listdir(path)
        return items

    def minimize_all(self) -> str:
        """Minimizes all windows (Show Desktop)."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            user32.keybd_event(0x5B, 0, 0, 0)  # Win down
            user32.keybd_event(0x44, 0, 0, 0)  # D down
            user32.keybd_event(0x44, 0, 2, 0)  # D up
            user32.keybd_event(0x5B, 0, 2, 0)  # Win up
            return "Minimized all windows"
        except Exception as e:
            logger.error(f"Failed to minimize: {e}")
            raise

    def switch_virtual_desktop(self, direction: str) -> str:
        """Switch to next or previous virtual desktop."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # Win+Ctrl+Left or Win+Ctrl+Right
            VK_LWIN = 0x5B
            VK_LCONTROL = 0xA2
            VK_LEFT = 0x25
            VK_RIGHT = 0x27
            
            arrow_key = VK_RIGHT if direction == "next" else VK_LEFT
            
            user32.keybd_event(VK_LWIN, 0, 0, 0)      # Win down
            user32.keybd_event(VK_LCONTROL, 0, 0, 0)  # Ctrl down
            user32.keybd_event(arrow_key, 0, 0, 0)    # Arrow down
            user32.keybd_event(arrow_key, 0, 2, 0)    # Arrow up
            user32.keybd_event(VK_LCONTROL, 0, 2, 0)  # Ctrl up
            user32.keybd_event(VK_LWIN, 0, 2, 0)      # Win up
            
            return f"Switched to {direction} virtual desktop"
        except Exception as e:
            logger.error(f"Failed to switch desktop: {e}")
            raise

    def new_virtual_desktop(self) -> str:
        """Create a new virtual desktop."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            user32.keybd_event(0x5B, 0, 0, 0)   # Win down
            user32.keybd_event(0xA2, 0, 0, 0)   # Ctrl down
            user32.keybd_event(0x44, 0, 0, 0)   # D down
            user32.keybd_event(0x44, 0, 2, 0)   # D up
            user32.keybd_event(0xA2, 0, 2, 0)   # Ctrl up
            user32.keybd_event(0x5B, 0, 2, 0)   # Win up
            return "Created new virtual desktop"
        except Exception as e:
            logger.error(f"Failed to create desktop: {e}")
            raise

    def _send_key(self, vk_code: int, with_shift: bool = False):
        """Helper to send a single keypress."""
        import ctypes
        user32 = ctypes.windll.user32
        if with_shift:
            user32.keybd_event(0x10, 0, 0, 0)  # Shift down
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, 2, 0)
        if with_shift:
            user32.keybd_event(0x10, 0, 2, 0)  # Shift up

    def _send_hotkey(self, *keys):
        """Send a combination of keys."""
        import ctypes
        user32 = ctypes.windll.user32
        # Press all keys down
        for key in keys:
            user32.keybd_event(key, 0, 0, 0)
        # Release all keys up (reverse order)
        for key in reversed(keys):
            user32.keybd_event(key, 0, 2, 0)

    # --- Volume Control ---
    def volume_mute(self) -> str:
        """Toggle mute."""
        self._send_key(0xAD)  # VK_VOLUME_MUTE
        return "Toggled mute"

    def volume_up(self) -> str:
        """Increase volume."""
        self._send_key(0xAF)  # VK_VOLUME_UP
        return "Volume increased"

    def volume_down(self) -> str:
        """Decrease volume."""
        self._send_key(0xAE)  # VK_VOLUME_DOWN
        return "Volume decreased"

    # --- Media Control ---
    def media_play_pause(self) -> str:
        """Play/pause media."""
        self._send_key(0xB3)  # VK_MEDIA_PLAY_PAUSE
        return "Toggled play/pause"

    def media_next(self) -> str:
        """Next track."""
        self._send_key(0xB0)  # VK_MEDIA_NEXT_TRACK
        return "Next track"

    def media_prev(self) -> str:
        """Previous track."""
        self._send_key(0xB1)  # VK_MEDIA_PREV_TRACK
        return "Previous track"

    # --- Screenshot ---
    def screenshot(self) -> str:
        """Take a full screenshot and save to Pictures/Screenshots."""
        try:
            import mss
            import os
            from datetime import datetime
            
            # Ensure Screenshots folder exists
            pics_folder = os.path.expanduser("~/Pictures/Screenshots")
            os.makedirs(pics_folder, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Screenshot_{timestamp}.png"
            filepath = os.path.join(pics_folder, filename)
            
            # Capture
            with mss.mss() as sct:
                sct.shot(output=filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            return f"Screenshot saved: {filename}"
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            # Fallback to keyboard
            self._send_hotkey(0x5B, 0x2C)
            return "Screenshot taken (keyboard fallback)"

    def screenshot_snip(self) -> str:
        """Open Windows Snip tool."""
        self._send_hotkey(0x5B, 0x10, 0x53)  # Win+Shift+S
        return "Snip tool opened"

    # --- System ---
    def lock_computer(self) -> str:
        """Lock the computer."""
        self._send_hotkey(0x5B, 0x4C)  # Win+L
        return "Computer locked"

    def open_task_manager(self) -> str:
        """Open Task Manager."""
        self._send_hotkey(0xA2, 0x10, 0x1B)  # Ctrl+Shift+Esc
        return "Task Manager opened"

    def open_run_dialog(self) -> str:
        """Open Run dialog."""
        self._send_hotkey(0x5B, 0x52)  # Win+R
        return "Run dialog opened"

    def open_settings(self) -> str:
        """Open Windows Settings."""
        self._send_hotkey(0x5B, 0x49)  # Win+I
        return "Settings opened"

    def open_file_explorer(self) -> str:
        """Open File Explorer."""
        self._send_hotkey(0x5B, 0x45)  # Win+E
        return "File Explorer opened"

    def open_search(self) -> str:
        """Open Windows Search."""
        self._send_hotkey(0x5B, 0x53)  # Win+S
        return "Search opened"

    # --- Window Management ---
    def snap_window_left(self) -> str:
        """Snap current window to left half."""
        self._send_hotkey(0x5B, 0x25)  # Win+Left
        return "Window snapped left"

    def snap_window_right(self) -> str:
        """Snap current window to right half."""
        self._send_hotkey(0x5B, 0x27)  # Win+Right
        return "Window snapped right"

    def maximize_window(self) -> str:
        """Maximize current window."""
        self._send_hotkey(0x5B, 0x26)  # Win+Up
        return "Window maximized"

    def minimize_window(self) -> str:
        """Minimize current window."""
        self._send_hotkey(0x5B, 0x28)  # Win+Down
        return "Window minimized"

    def close_window(self) -> str:
        """Close current window (Alt+F4)."""
        self._send_hotkey(0x12, 0x73)  # Alt+F4
        return "Window closed"

    # --- Browser Tab Control ---
    def new_tab(self) -> str:
        """Open new browser tab."""
        self._send_hotkey(0xA2, 0x54)  # Ctrl+T
        return "New tab opened"

    def close_tab(self) -> str:
        """Close current browser tab."""
        self._send_hotkey(0xA2, 0x57)  # Ctrl+W
        return "Tab closed"

    def refresh_page(self) -> str:
        """Refresh current page."""
        self._send_key(0x74)  # F5
        return "Page refreshed"

    def go_back(self) -> str:
        """Go back in browser."""
        self._send_hotkey(0x12, 0x25)  # Alt+Left
        return "Navigated back"

    def go_forward(self) -> str:
        """Go forward in browser."""
        self._send_hotkey(0x12, 0x27)  # Alt+Right
        return "Navigated forward"

    # --- Apps ---
    def launch_app(self, app_name: str) -> str:
        """Launch an application by name."""
        import subprocess
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "chrome": "chrome",
            "firefox": "firefox",
            "edge": "msedge",
            "terminal": "wt",
            "cmd": "cmd",
            "powershell": "powershell",
            "spotify": "spotify",
            "vscode": "code",
            "word": "winword",
            "excel": "excel",
            "outlook": "outlook",
        }
        
        exe = app_map.get(app_name.lower(), app_name)
        try:
            subprocess.Popen(exe, shell=True)
            return f"Launched {app_name}"
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            raise
