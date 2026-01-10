import asyncio
import logging
import json
import aiohttp
import websockets
from typing import Optional, Dict, Any, List

# Configure Logger
logger = logging.getLogger("BrowserController")
logger.setLevel(logging.INFO)

class BrowserController:
    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_http_url = cdp_url
        self.ws_url: Optional[str] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.msg_id = 0

    async def _get_debug_url(self) -> Optional[str]:
        """Fetches the WebSocket Debugger URL for the active page."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.cdp_http_url}/json") as resp:
                    if resp.status != 200:
                        logger.error(f"CDP Endpoint returned {resp.status}")
                        return None
                    targets = await resp.json()
                    
            # Filter for 'page' type and find valid socket
            # We want a 'page' that is not a background page if possible, or just the first one
            for t in targets:
                if t.get('type') == 'page' and 'webSocketDebuggerUrl' in t:
                    # found a candidate
                    logger.info(f"Target Found: {t.get('title', 'Unknown')} | {t.get('url', 'no-url')}")
                    return t['webSocketDebuggerUrl']
            
            logger.error("No debuggable page target found.")
            return None
        except Exception as e:
            logger.error(f"Failed to query CDP endpoint: {e}")
            return None

    async def start(self):
        """Connects to the Chrome instance."""
        logger.info(f"Scanning for pages at {self.cdp_http_url}...")
        self.ws_url = await self._get_debug_url()
        
        if not self.ws_url:
            logger.info("Chrome not found or not debuggable. Attempting to launch...")
            if self._launch_chrome():
                # Wait for Chrome to start up
                for _ in range(10):
                    await asyncio.sleep(1)
                    self.ws_url = await self._get_debug_url()
                    if self.ws_url:
                        break
            
        if not self.ws_url:
            raise RuntimeError(f"Could not find a valid page at {self.cdp_http_url}. Is Chrome running with --remote-debugging-port=9222?")
            
        logger.info(f"Connecting to Page WS: {self.ws_url}")
        self.websocket = await websockets.connect(self.ws_url)
        logger.info("Connected to Chrome via WebSocket.")

    def _launch_chrome(self) -> bool:
        """Launches Chrome with hndl-it specific profile - visually distinct and isolated."""
        import subprocess
        import os
        
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        chrome_path = None
        for path in candidates:
            if os.path.exists(path):
                chrome_path = path
                break
                
        if not chrome_path:
            logger.error("Could not find chrome.exe in standard locations.")
            return False
        
        # Dedicated hndl-it profile - completely separate from user's Chrome
        user_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../chrome_profile'))
        os.makedirs(user_data_dir, exist_ok=True)
        
        # HNDL-IT CHROME: Distinctive and isolated
        args = [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",              # No user extensions
            "--disable-sync",                     # No sync with user account
            "--disable-background-networking",    # Reduce interference
            "--new-window",                       # Always new window
            "--window-size=1200,800",             # Consistent size
            "--window-position=100,100",          # Known position
            "--force-dark-mode",                  # VISUAL: Dark mode for distinction
            "--enable-features=WebContentsForceDark",  # Force dark on all sites
            "about:blank"
        ]
        
        try:
            logger.info(f"Launching hndl-it Chrome (isolated profile, dark mode)...")
            subprocess.Popen(args, close_fds=True, shell=False, 
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)  # Process isolation
            return True
        except Exception as e:
            logger.error(f"Failed to launch Chrome: {e}")
            return False

    async def _send_cdp(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Sends a raw CDP command and waits for the result."""
        if not self.websocket:
            raise RuntimeError("Not connected")
            
        self.msg_id += 1
        cmd_id = self.msg_id
        message = {
            "id": cmd_id,
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Simple/Naive Loop: Read until we get OUR message ID back
        # In a real rigorous impl, we'd have a listening loop dispatching futures.
        # But for this tailored agent, we await the immediate response.
        # NOTE: This blocks other async events (like logs) which is fine for step-by-step agent.
        
        while True:
            resp_raw = await self.websocket.recv()
            resp = json.loads(resp_raw)
            
            if resp.get("id") == cmd_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP Error: {resp['error']['message']}")
                return resp.get("result", {})

    async def navigate(self, url: str, new_tab: bool = False):
        """Navigates to URL. If new_tab=True, opens in new tab."""
        # Domain Normalization
        if "." not in url and "localhost" not in url:
            url = f"{url}.com"
        if not url.startswith("http"):
            url = f"https://{url}"
        
        if new_tab:
            # Create new tab and switch to it
            await self.open_new_tab(url)
        else:
            logger.info(f"Navigating to {url}...")
            await self._send_cdp("Page.navigate", {"url": url})
            await self._wait_for_load()
    
    async def open_new_tab(self, url: str = "about:blank"):
        """Opens a new tab and switches to it."""
        logger.info(f"Opening new tab: {url}")
        
        # Use Target.createTarget to create new tab
        result = await self._send_cdp("Target.createTarget", {"url": url})
        target_id = result.get("targetId")
        
        if target_id:
            # Get the new tab's websocket URL and connect to it
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.cdp_http_url}/json") as resp:
                    targets = await resp.json()
                    for t in targets:
                        if t.get("id") == target_id:
                            new_ws_url = t.get("webSocketDebuggerUrl")
                            if new_ws_url:
                                # Close old connection, open new
                                if self.websocket:
                                    await self.websocket.close()
                                self.ws_url = new_ws_url
                                self.websocket = await websockets.connect(new_ws_url)
                                logger.info(f"Switched to new tab: {target_id}")
                                await self._wait_for_load()
                                return
        
        logger.warning("Could not switch to new tab")
    
    async def get_tabs(self) -> List[Dict]:
        """Get list of all open tabs."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.cdp_http_url}/json") as resp:
                targets = await resp.json()
                return [t for t in targets if t.get("type") == "page"]

    async def _wait_for_load(self, timeout: int = 10):
        """Polls readyState."""
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            res = await self.execute_script("return document.readyState")
            if res == "complete":
                return
            await asyncio.sleep(0.5)
        logger.warning(f"Timeout waiting for page load.")

    async def scrape_text(self, selector: Optional[str] = None) -> str:
        """Scrapes text using JS."""
        if selector:
            # document.querySelector(selector).innerText
            script = f"""
                (function() {{
                    const el = document.querySelector('{selector}');
                    return el ? el.innerText : '';
                }})()
            """
        else:
            script = "document.body.innerText"
            
        return await self.execute_script(script)

    async def click_element(self, selector: str):
        """Clicks via JS (simulated)."""
        # True CDP click involves Input.dispatchMouseEvent which implies coordinates.
        # The easiest robust way in Pure CDP is JS click() unless we have vision coords.
        script = f"""
            (function() {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.click();
                    return true;
                }}
                return false;
            }})()
        """
        success = await self.execute_script(script)
        if not success:
            raise RuntimeError(f"Element {selector} not found")

    async def execute_script(self, script: str) -> Any:
        """Runtime.evaluate wrapper."""
        # Ensure 'return' is handled if it's a raw expression?
        # CDP expects an expression that evaluates to a value.
        # If user passed "return 1", CDP might fail if not wrapped in function.
        # We'll assume the helper methods wrap commands well, or user sends valid expression.
        
        # If the script contains 'return', it likely needs wrapping in IIFE
        if "return " in script and not script.strip().startswith("(function"):
             script = f"(function(){{ {script} }})()"
             
        res = await self._send_cdp("Runtime.evaluate", {
            "expression": script, 
            "returnByValue": True,
            "awaitPromise": True
        })
        
        val = res.get("result", {}).get("value")
        return val

    async def close(self):
        if self.websocket:
            await self.websocket.close()
