import asyncio
import json
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import websockets

logger = logging.getLogger("hndl-it.floater.client")

class MultiAgentClient(QObject):
    """
    Manages connections to multiple agents (Browser, Desktop).
    """
    message_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)  # Aggregate status (legacy)
    agent_status = pyqtSignal(str, bool)  # Per-agent: (agent_name, connected)
    chain_progress = pyqtSignal(int, int, str)  # current, total, status_text
    floater_command = pyqtSignal(str)  # UI control commands

    def __init__(self):
        super().__init__()
        self.running = False
        self._loop = None
        # Registry of active sockets: "browser" -> ws, "desktop" -> ws
        self.sockets = {}
        self.config = {
            "browser": "ws://localhost:8766",
            "desktop": "ws://localhost:8767",
            "vision": "ws://localhost:8768"
        }

    def start_client(self):
        self.running = True
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main_loop())

    async def _connect_agent(self, name, uri):
        """Maintains a persistent connection to a single agent."""
        logger.info(f"[{name}] connecting to {uri}...")
        while self.running:
            try:
                async with websockets.connect(uri) as ws:
                    self.sockets[name] = ws
                    logger.info(f"[{name}] Connected!")
                    self.agent_status.emit(name, True)  # Per-agent status
                    
                    try:
                        async for message in ws:
                            self.message_received.emit(f"[{name}] {message}")
                    except websockets.ConnectionClosed:
                        logger.warning(f"[{name}] Disconnected.")
                    except Exception as e:
                        logger.error(f"[{name}] Error: {e}")
                    finally:
                        if name in self.sockets:
                            del self.sockets[name]
                        self.agent_status.emit(name, False)  # Mark disconnected
            except Exception as e:
                self.agent_status.emit(name, False)  # Offline
                await asyncio.sleep(5)

    async def _main_loop(self):
        # Run connect loops in parallel
        tasks = [
            self._connect_agent("browser", self.config["browser"]),
            self._connect_agent("desktop", self.config["desktop"]),
            self._connect_agent("vision", self.config["vision"])
        ]
        await asyncio.gather(*tasks)

    def send_command(self, text):
        """Parse and send command(s). Supports chaining with 'then' / 'and then'."""
        from .parser import CommandParser
        import re

        if not self._loop:
            return

        # Split on chain separators: "then", "and then", "and", ","
        chain_pattern = r'\s+(?:and\s+)?then\s+|\s+and\s+|\s*,\s*(?=\w)'
        parts = re.split(chain_pattern, text, flags=re.IGNORECASE)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) > 1:
            # It's a chain - execute sequentially
            self._execute_chain(parts)
        else:
            # Single command
            self._send_single_command(text)

    def _send_single_command(self, text):
        """Send a single command."""
        from .parser import CommandParser
        import json

        cmd_data = CommandParser.parse(text)
        
        if cmd_data:
            target = cmd_data.get("target_agent", "browser")
            action = cmd_data.get("action", "")
            
            # Handle floater commands locally (UI control)
            if target == "floater":
                self.floater_command.emit(action)
                self.message_received.emit(f"✓ UI: {action}")
                return
            
            payload = json.dumps(cmd_data)
            
            ws = self.sockets.get(target)
            if ws:
                asyncio.run_coroutine_threadsafe(ws.send(payload), self._loop)
            else:
                logger.warning(f"Cannot send to '{target}': No connection")
                self.message_received.emit(f"⚠ No connection to {target} agent")
        else:
            logger.warning(f"Parse failed: {text}")
            self.message_received.emit(f"❓ Unknown command: {text}")

    def _execute_chain(self, commands: list):
        """Execute a chain of commands sequentially."""
        import json
        from .parser import CommandParser
        
        async def run_chain():
            total = len(commands)
            for i, cmd_text in enumerate(commands, 1):
                # Emit progress
                self.chain_progress.emit(i, total, f"Step {i}/{total}: {cmd_text[:30]}...")
                
                cmd_data = CommandParser.parse(cmd_text)
                if not cmd_data:
                    self.message_received.emit(f"⚠ Skipping unknown: {cmd_text}")
                    continue
                
                target = cmd_data.get("target_agent", "browser")
                ws = self.sockets.get(target)
                
                if ws:
                    payload = json.dumps(cmd_data)
                    await ws.send(payload)
                    
                    # Wait for response (simple timeout approach)
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        self.message_received.emit(f"[{target}] {response}")
                    except asyncio.TimeoutError:
                        self.message_received.emit(f"⚠ Timeout waiting for {target}")
                else:
                    self.message_received.emit(f"⚠ No connection to {target}")
                
                # Small delay between steps
                await asyncio.sleep(0.5)
            
            self.chain_progress.emit(total, total, "Chain complete!")
        
        asyncio.run_coroutine_threadsafe(run_chain(), self._loop)

    def stop(self):
        self.running = False

