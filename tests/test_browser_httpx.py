
import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.browser.browser_controller import BrowserController

class TestBrowserHttpx(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch httpx.AsyncClient
        self.httpx_patcher = patch('httpx.AsyncClient')
        self.MockHttpxClient = self.httpx_patcher.start()

        # Setup mock client instance
        self.mock_client = AsyncMock()
        self.MockHttpxClient.return_value.__aenter__.return_value = self.mock_client
        self.MockHttpxClient.return_value.__aexit__.return_value = None

        self.controller = BrowserController()

    async def asyncTearDown(self):
        self.httpx_patcher.stop()

    async def test_get_debug_url_success(self):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "type": "page",
                "title": "Test Page",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/123"
            }
        ]
        self.mock_client.get.return_value = mock_response

        url = await self.controller._get_debug_url()

        self.mock_client.get.assert_called_with("http://localhost:9222/json")
        self.assertEqual(url, "ws://localhost:9222/devtools/page/123")

    async def test_get_debug_url_fail(self):
        # Mock failure response
        mock_response = MagicMock()
        mock_response.status_code = 500
        self.mock_client.get.return_value = mock_response

        url = await self.controller._get_debug_url()

        self.assertIsNone(url)

    async def test_get_tabs(self):
        # Mock response with mixed targets
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"type": "page", "title": "Page 1"},
            {"type": "background_page", "title": "Extension"},
            {"type": "page", "title": "Page 2"}
        ]
        self.mock_client.get.return_value = mock_response

        tabs = await self.controller.get_tabs()

        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0]['title'], "Page 1")
        self.assertEqual(tabs[1]['title'], "Page 2")

if __name__ == "__main__":
    unittest.main()
