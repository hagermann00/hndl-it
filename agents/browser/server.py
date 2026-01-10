import asyncio
import json
import logging
import sys
import os
import websockets
from websockets.server import serve
import time

# Ensure we can import shared modules by adding the repo root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.messages import (
    BrowserCommand, BrowserEvent, 
    NavigateCommand, ScrapeCommand, ClickCommand, ExecuteScriptCommand,
    StatusEvent, LogEvent, ResultEvent, ErrorEvent
)
from agents.browser.browser_controller import BrowserController

# Configuration
HOST = "localhost"
PORT = 8766
CDP_URL = "http://localhost:9222"
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))

# Setup Logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "browser_agent.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BrowserAgentServer")

class BrowserAgentServer:
    def __init__(self):
        self.controller = BrowserController(cdp_url=CDP_URL)

    async def handle_command(self, command_data: dict) -> BrowserEvent:
        """Parses and executes a command, returning a BrowserEvent."""
        try:
            # Parse command using Pydantic
            # We need to determine the specific type or let Pydantic try to match Union
            # A simple way is to check 'action' manually or use a TypeAdapter
            # For simplicity here, we'll manual dispatch for robust error messages
            
            action = command_data.get("action")
            cmd_id = command_data.get("id", "unknown")

            if not action:
                return ErrorEvent(command_id=cmd_id, type="error", error_message="Missing 'action' field", timestamp=time.time())

            result_data = {}
            
            if action == "navigate":
                cmd = NavigateCommand(**command_data)
                await self.controller.navigate(cmd.url)
                result_data = {"status": "navigated", "url": cmd.url}

            elif action == "scrape":
                cmd = ScrapeCommand(**command_data)
                text = await self.controller.scrape_text(cmd.selector)
                result_data = {"text": text}

            elif action == "click":
                cmd = ClickCommand(**command_data)
                await self.controller.click_element(cmd.selector)
                result_data = {"status": "clicked", "selector": cmd.selector}
            
            elif action == "execute_script":
                cmd = ExecuteScriptCommand(**command_data)
                res = await self.controller.execute_script(cmd.script)
                result_data = {"result": res}

            else:
                return ErrorEvent(command_id=cmd_id, type="error", error_message=f"Unknown action: {action}", timestamp=time.time())

            return ResultEvent(command_id=cmd_id, type="result", data=result_data, timestamp=time.time())

        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)
            return ErrorEvent(command_id=command_data.get("id"), type="error", error_message=str(e), timestamp=time.time())

    async def ws_handler(self, websocket):
        """Handles WebSocket connections."""
        logger.info("New client connected.")
        try:
            async for message in websocket:
                logger.info(f"Received message: {message}")
                
                # Notify: Working
                await websocket.send(StatusEvent(type="status", status="working", message="Processing command...", timestamp=time.time()).model_dump_json())

                try:
                    data = json.loads(message)
                    response_event = await self.handle_command(data)
                    
                    # specific log for the result
                    logger.info(f"Command execution result: {response_event.type}")
                    
                    await websocket.send(response_event.model_dump_json())
                    
                except json.JSONDecodeError:
                    await websocket.send(ErrorEvent(type="error", error_message="Invalid JSON", timestamp=time.time()).model_dump_json())
                
                # Notify: Idle
                await websocket.send(StatusEvent(type="status", status="idle", message="Ready", timestamp=time.time()).model_dump_json())

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected.")

    async def main(self):
        """Starts the server and browser controller."""
        logger.info("Starting Browser Agent Server...")
        
        # Start Browser Controller
        try:
            await self.controller.start()
        except Exception as e:
            logger.critical(f"Failed to start Browser Controller: {e}")
            logger.critical("Is Chrome running with --remote-debugging-port=9222?")
            # We don't exit, we wait, maybe user starts it later? 
            # Ideally we fail fast, but for robustness let's just log.
            pass

        # Start WebSocket Server
        async with serve(self.ws_handler, HOST, PORT):
            logger.info(f"WebSocket server listening on ws://{HOST}:{PORT}")
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    server = BrowserAgentServer()
    try:
        asyncio.run(server.main())
    except KeyboardInterrupt:
        logger.info("Server stopping...")
