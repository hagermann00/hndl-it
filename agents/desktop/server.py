import asyncio
import json
import logging
import sys
import os
import websockets
from websockets.server import serve
import time

# Sync path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.messages import (
    OpenCommand, ListDirCommand,
    StatusEvent, ResultEvent, ErrorEvent
)
from agents.desktop.file_controller import FileController

HOST = "localhost"
PORT = 8767
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))

# Logging Setup
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "desktop_agent.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DesktopAgentServer")

class DesktopAgentServer:
    def __init__(self):
        self.controller = FileController()

    async def handle_command(self, command_data: dict) -> str: # returns JSON string event
        cmd_id = command_data.get("id", "unknown")
        action = command_data.get("action")
        
        try:
            result_data = {}
            
            if action == "open":
                cmd = OpenCommand(**command_data)
                msg = self.controller.open_path(cmd.path)
                result_data = {"status": "success", "message": msg}
                
            elif action == "list_dir":
                cmd = ListDirCommand(**command_data)
                items = self.controller.list_dir(cmd.path)
                result_data = {"items": items}
            
            elif action == "minimize_all":
                msg = self.controller.minimize_all()
                result_data = {"status": "success", "message": msg}
            
            elif action == "switch_desktop":
                direction = command_data.get("direction", "next")
                msg = self.controller.switch_virtual_desktop(direction)
                result_data = {"status": "success", "message": msg}
            
            elif action == "new_desktop":
                msg = self.controller.new_virtual_desktop()
                result_data = {"status": "success", "message": msg}
            
            # Volume & Media
            elif action == "volume_mute":
                msg = self.controller.volume_mute()
                result_data = {"status": "success", "message": msg}
            elif action == "volume_up":
                msg = self.controller.volume_up()
                result_data = {"status": "success", "message": msg}
            elif action == "volume_down":
                msg = self.controller.volume_down()
                result_data = {"status": "success", "message": msg}
            elif action == "play_pause":
                msg = self.controller.media_play_pause()
                result_data = {"status": "success", "message": msg}
            elif action == "next_track":
                msg = self.controller.media_next()
                result_data = {"status": "success", "message": msg}
            elif action == "prev_track":
                msg = self.controller.media_prev()
                result_data = {"status": "success", "message": msg}
            
            # Screenshots
            elif action == "screenshot":
                msg = self.controller.screenshot()
                result_data = {"status": "success", "message": msg}
            elif action == "snip":
                msg = self.controller.screenshot_snip()
                result_data = {"status": "success", "message": msg}
            
            # System
            elif action == "lock":
                msg = self.controller.lock_computer()
                result_data = {"status": "success", "message": msg}
            elif action == "task_manager":
                msg = self.controller.open_task_manager()
                result_data = {"status": "success", "message": msg}
            elif action == "run_dialog":
                msg = self.controller.open_run_dialog()
                result_data = {"status": "success", "message": msg}
            elif action == "settings":
                msg = self.controller.open_settings()
                result_data = {"status": "success", "message": msg}
            elif action == "file_explorer":
                msg = self.controller.open_file_explorer()
                result_data = {"status": "success", "message": msg}
            elif action == "search":
                msg = self.controller.open_search()
                result_data = {"status": "success", "message": msg}
            
            # Window Management
            elif action == "snap_left":
                msg = self.controller.snap_window_left()
                result_data = {"status": "success", "message": msg}
            elif action == "snap_right":
                msg = self.controller.snap_window_right()
                result_data = {"status": "success", "message": msg}
            elif action == "maximize":
                msg = self.controller.maximize_window()
                result_data = {"status": "success", "message": msg}
            elif action == "minimize":
                msg = self.controller.minimize_window()
                result_data = {"status": "success", "message": msg}
            elif action == "close_window":
                msg = self.controller.close_window()
                result_data = {"status": "success", "message": msg}
            
            # Browser shortcuts
            elif action == "new_tab":
                msg = self.controller.new_tab()
                result_data = {"status": "success", "message": msg}
            elif action == "close_tab":
                msg = self.controller.close_tab()
                result_data = {"status": "success", "message": msg}
            elif action == "refresh":
                msg = self.controller.refresh_page()
                result_data = {"status": "success", "message": msg}
            elif action == "go_back":
                msg = self.controller.go_back()
                result_data = {"status": "success", "message": msg}
            elif action == "go_forward":
                msg = self.controller.go_forward()
                result_data = {"status": "success", "message": msg}
            
            # Apps
            elif action == "launch_app":
                app_name = command_data.get("app_name", "")
                msg = self.controller.launch_app(app_name)
                result_data = {"status": "success", "message": msg}
            
            else:
                return ErrorEvent(command_id=cmd_id, type="error", error_message=f"Unknown desktop action: {action}", timestamp=time.time()).model_dump_json()

            return ResultEvent(command_id=cmd_id, type="result", data=result_data, timestamp=time.time()).model_dump_json()

        except Exception as e:
            logger.error(f"Command failed: {e}")
            return ErrorEvent(command_id=cmd_id, type="error", error_message=str(e), timestamp=time.time()).model_dump_json()


    async def ws_handler(self, websocket):
        logger.info("Client connected to Desktop Agent.")
        try:
            async for message in websocket:
                logger.info(f"Received: {message}")
                
                await websocket.send(StatusEvent(type="status", status="working", timestamp=time.time()).model_dump_json())
                
                try:
                    data = json.loads(message)
                    resp = await self.handle_command(data)
                    await websocket.send(resp)
                except json.JSONDecodeError:
                    pass
                    
                await websocket.send(StatusEvent(type="status", status="idle", timestamp=time.time()).model_dump_json())
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected.")

    async def main(self):
        logger.info(f"Starting Desktop (Files) Agent on ws://{HOST}:{PORT}")
        async with serve(self.ws_handler, HOST, PORT):
            await asyncio.Future()

if __name__ == "__main__":
    server = DesktopAgentServer()
    asyncio.run(server.main())
