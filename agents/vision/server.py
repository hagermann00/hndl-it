import asyncio
import logging
import sys
import os
import json
import websockets
from websockets.server import serve
import time

# Sync path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.messages import (
    StatusEvent, ErrorEvent, ResultEvent, AnalyzeCommand
)
from agents.vision.vision_controller import VisionController

HOST = "localhost"
PORT = 8768
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))

# Logging Setup
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "vision_agent.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VisionAgentServer")

class VisionAgentServer:
    def __init__(self):
        # Initialize controller (which loads mss, but model inference is per-request or lazy?)
        # For Ollama, it's just REST calls usually, so cheap init.
        self.controller = VisionController(model="llava-llama3")
        
        # Check model
        if not self.controller.check_model_availability():
            logger.warning(f"Model '{self.controller.model}' not found in Ollama! please run 'ollama pull {self.controller.model}'")
        else:
            logger.info(f"Model '{self.controller.model}' verified.")

    async def handle_command(self, command_data: dict) -> str:
        cmd_id = command_data.get("id", "unknown")
        action = command_data.get("action")
        
        try:
            if action == "analyze":
                # We need to ensure we validate via Pydantic but handle errors gracefully
                # Manually constructing command object
                cmd = AnalyzeCommand(**command_data)
                
                # Report "Working" state separately or just let the caller handle? 
                # The ws_handler handles the status events.
                
                result = await self.controller.analyze_image(cmd.prompt)
                
                return ResultEvent(
                    command_id=cmd_id, 
                    type="result", 
                    data={"text": result}, 
                    timestamp=time.time()
                ).model_dump_json()

            else:
                return ErrorEvent(
                    command_id=cmd_id, 
                    type="error", 
                    error_message=f"Unknown vision action: {action}", 
                    timestamp=time.time()
                ).model_dump_json()

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return ErrorEvent(
                command_id=cmd_id, 
                type="error", 
                error_message=str(e), 
                timestamp=time.time()
            ).model_dump_json()

    async def ws_handler(self, websocket):
        logger.info("Client connected to Vision Agent.")
        try:
            async for message in websocket:
                logger.info(f"Received: {message}")
                
                # Notify: Working
                await websocket.send(StatusEvent(type="status", status="working", message="Analyzing...", timestamp=time.time()).model_dump_json())
                
                try:
                    data = json.loads(message)
                    response = await self.handle_command(data)
                    await websocket.send(response)
                    
                except json.JSONDecodeError:
                    await websocket.send(ErrorEvent(type="error", error_message="Invalid JSON", timestamp=time.time()).model_dump_json())
                
                # Notify: Idle
                await websocket.send(StatusEvent(type="status", status="idle", message="Vision Agent idle.", timestamp=time.time()).model_dump_json())

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected.")

    async def main(self):
        logger.info(f"Starting Vision Agent on ws://{HOST}:{PORT} (Model: {self.controller.model})")
        async with serve(self.ws_handler, HOST, PORT):
            await asyncio.Future()

if __name__ == "__main__":
    server = VisionAgentServer()
    try:
        asyncio.run(server.main())
    except KeyboardInterrupt:
        logger.info("Vision Agent stopping...")
