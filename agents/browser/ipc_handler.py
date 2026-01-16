"""
Browser Agent - Controls Chrome via CDP.
Inherits from BaseAgent for robust IPC, uses asyncio for BrowserController.
"""

import sys
import os
import asyncio
import threading
from concurrent.futures import Future

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.agent_base import BaseAgent
from agents.browser.browser_controller import BrowserController
from shared.voice_output import speak

class BrowserAgent(BaseAgent):
    def __init__(self):
        # Initialize BaseAgent with 1 worker to ensure serial execution of browser commands
        # (Browsers are stateful and serial by nature for a single view)
        super().__init__("browser", max_workers=1)

        self.controller = BrowserController()
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()

        # Initialize the controller on the loop
        future = asyncio.run_coroutine_threadsafe(self.controller.start(), self.loop)
        try:
            future.result(timeout=10)
            self.logger.info("🌐 Browser Controller connected.")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to browser: {e}")

    def _run_event_loop(self):
        """Runs the asyncio loop in a dedicated thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def process_action(self, action: str, payload: dict):
        """
        Receives synchronous calls from BaseAgent's thread pool.
        Proxies them to the async loop.
        """
        # Create a future to wait for the async result
        coro = self._route_action(action, payload)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)

        try:
            # Wait for result (blocks this worker thread, but not the IPC loop)
            future.result(timeout=30)
        except Exception as e:
            self.logger.error(f"Action {action} timed out or failed: {e}")
            raise e

    async def _route_action(self, action: str, payload: dict):
        """Async router running on the loop."""
        if action == "navigate":
            url = payload.get("subject") or payload.get("url") or payload.get("input", "")
            if not url.startswith(("http://", "https://", "about:")):
                url = "https://" + url
            # Add timeout to prevent hanging
            try:
                await asyncio.wait_for(self.controller.navigate(url), timeout=30)
                self.logger.info(f"✅ Navigated to {url}")
            except asyncio.TimeoutError:
                self.logger.error(f"❌ Navigation to {url} timed out after 30s")

        elif action == "search":
            query = payload.get("subject") or payload.get("query") or payload.get("input", "")
            site = payload.get("modifier") or payload.get("site", "")
            if site:
                url = f"https://www.google.com/search?q=site:{site}+{query}"
            else:
                url = f"https://www.google.com/search?q={query}"
            # Add timeout to prevent hanging
            try:
                await asyncio.wait_for(self.controller.navigate(url), timeout=30)
                self.logger.info(f"✅ Searched: {query}")
            except asyncio.TimeoutError:
                self.logger.error(f"❌ Search for {query} timed out after 30s")
            
        elif action == "type":
            text = payload.get("text", "") or payload.get("input", "")
            selector = payload.get("selector") or payload.get("subject")
            await self.controller.type_text(text, selector)
            self.logger.info(f"✅ Typed '{text}'")
            
        elif action == "click":
            selector = payload.get("selector") or payload.get("subject")
            if selector:
                try:
                    await asyncio.wait_for(self.controller.click_element(selector), timeout=10)
                    self.logger.info(f"✅ Clicked element '{selector}'")
                except asyncio.TimeoutError:
                    self.logger.error(f"❌ Clicking element '{selector}' timed out.")
                except Exception as e:
                    self.logger.error(f"❌ Failed to click element '{selector}': {e}")
            else:
                self.logger.error("❌ 'click' action requires a 'selector' or 'subject' in payload.")

        elif action == "close":
            await self.controller.close()
            
        else:
            self.logger.warning(f"Unknown action: {action}")

    def stop(self):
        """Override stop to close loop."""
        super().stop()
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join(timeout=1)


if __name__ == "__main__":
    agent = BrowserAgent()
    agent.run()
