"""
hndl-it Browser Agent - Controller
CDP/Playwright browser control
"""

import asyncio
import base64
import logging
from typing import Optional

try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

import aiohttp

logger = logging.getLogger("hndl-it.browser")


class BrowserController:
    """Controls Chrome browser via CDP"""
    
    def __init__(self, debug_port: int = 9223):
        self.debug_port = debug_port
        self.cdp_url = f"http://localhost:{debug_port}"
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self.is_connected = False
    
    async def connect(self) -> bool:
        """Connect to Chrome debugging port"""
        try:
            if not HAS_PLAYWRIGHT:
                logger.error("Playwright not installed")
                return False
            
            # Verify Chrome is running with debug port
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.cdp_url}/json/version", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        logger.error(f"Chrome not responding on port {self.debug_port}")
                        return False
                    data = await resp.json()
                    logger.info(f"Chrome: {data.get('Browser', 'Unknown')}")
                
                # List tabs
                async with session.get(f"{self.cdp_url}/json") as resp:
                    tabs = await resp.json()
                    logger.info(f"Found {len(tabs)} Chrome tabs")
            
            # Connect via Playwright CDP
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.debug_port}"
            )
            
            # Get existing page or create one
            contexts = self._browser.contexts
            if contexts and contexts[0].pages:
                self._page = contexts[0].pages[0]
                logger.info(f"Using existing tab: {self._page.url[:50]}")
            else:
                ctx = contexts[0] if contexts else await self._browser.new_context()
                self._page = await ctx.new_page()
                await self._page.goto("about:blank")
                logger.info("Created new tab")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Clean disconnect"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self.is_connected = False
        logger.info("Disconnected from Chrome")
    
    async def get_current_url(self) -> str:
        """Get current page URL"""
        if self._page:
            return self._page.url
        return ""
    
    async def take_screenshot(self, timeout: int = 5000) -> Optional[str]:
        """Take screenshot, return base64"""
        try:
            if not self._page:
                return None
            screenshot = await self._page.screenshot(type="png", timeout=timeout)
            return base64.b64encode(screenshot).decode("utf-8")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None
    
    async def execute(self, action: dict) -> dict:
        """Execute a browser action"""
        action_type = action.get("type", "").lower()
        
        try:
            if action_type == "navigate":
                return await self._navigate(action)
            elif action_type == "click":
                return await self._click(action)
            elif action_type == "type":
                return await self._type(action)
            elif action_type == "scroll":
                return await self._scroll(action)
            elif action_type == "scrape":
                return await self._scrape(action)
            elif action_type == "back":
                await self._page.go_back()
                return {"success": True, "message": "Went back"}
            elif action_type == "forward":
                await self._page.go_forward()
                return {"success": True, "message": "Went forward"}
            elif action_type == "refresh":
                await self._page.reload()
                return {"success": True, "message": "Refreshed"}
            else:
                return {"success": False, "error": f"Unknown action: {action_type}"}
        except Exception as e:
            logger.error(f"Action failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _navigate(self, action: dict) -> dict:
        """Navigate to URL"""
        url = action.get("target") or action.get("url", "")
        if not url:
            return {"success": False, "error": "No URL"}
        
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        if self._page:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return {"success": True, "message": f"Navigated to {url}"}
        return {"success": False, "error": "No page"}
    
    async def _click(self, action: dict) -> dict:
        """Click element"""
        if not self._page:
            return {"success": False, "error": "No page"}
        
        selector = action.get("target") or action.get("selector")
        text = action.get("text")
        coords = action.get("coordinates")
        
        if coords:
            await self._page.mouse.click(coords.get("x", 0), coords.get("y", 0))
            return {"success": True, "message": f"Clicked at {coords}"}
        if selector:
            await self._page.click(selector, timeout=5000)
            return {"success": True, "message": f"Clicked {selector}"}
        if text:
            await self._page.click(f"text={text}", timeout=5000)
            return {"success": True, "message": f"Clicked '{text}'"}
        
        return {"success": False, "error": "No target for click"}
    
    async def _type(self, action: dict) -> dict:
        """Type text"""
        if not self._page:
            return {"success": False, "error": "No page"}
        
        text = action.get("value") or action.get("text", "")
        selector = action.get("target") or action.get("selector")
        
        if selector:
            await self._page.fill(selector, text)
        else:
            await self._page.keyboard.type(text)
        
        return {"success": True, "message": f"Typed: {text[:20]}..."}
    
    async def _scroll(self, action: dict) -> dict:
        """Scroll page"""
        if not self._page:
            return {"success": False, "error": "No page"}
        
        direction = action.get("direction", "down").lower()
        amount = action.get("amount", 500)
        
        delta = amount if direction == "down" else -amount
        await self._page.mouse.wheel(0, delta)
        
        return {"success": True, "message": f"Scrolled {direction}"}
    
    async def _scrape(self, action: dict) -> dict:
        """Scrape page content"""
        if not self._page:
            return {"success": False, "error": "No page"}
        
        selector = action.get("target") or action.get("selector") or "body"
        
        try:
            # Get text content
            content = await self._page.inner_text(selector)
            
            # Also get title and URL
            title = await self._page.title()
            url = self._page.url
            
            # Truncate if too long
            if len(content) > 10000:
                content = content[:10000] + "\n...[truncated]"
            
            return {
                "success": True,
                "message": f"Scraped {len(content)} chars from {title}",
                "data": {
                    "title": title,
                    "url": url,
                    "content": content
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Scrape failed: {e}"}
