import sys
import os
import asyncio
import unittest
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBrowserType(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch sys.modules to mock missing dependencies
        # We use patch.dict so it's reversible
        self.modules_patcher = patch.dict('sys.modules', {
            'httpx': MagicMock(),
            'websockets': MagicMock()
        })
        self.modules_patcher.start()

        # Import inside the patched environment
        # We need to ensure we get a fresh import or one that uses our mocks
        if 'agents.browser.browser_controller' in sys.modules:
            del sys.modules['agents.browser.browser_controller']

        from agents.browser.browser_controller import BrowserController
        self.BrowserController = BrowserController

        self.controller = self.BrowserController()
        # Mock _send_cdp
        self.controller._send_cdp = AsyncMock()
        # Mock execute_script
        self.controller.execute_script = AsyncMock()
        self.controller.execute_script.return_value = True

    async def asyncTearDown(self):
        self.modules_patcher.stop()
        # Clean up the module we imported so future imports don't get the mocked version
        if 'agents.browser.browser_controller' in sys.modules:
            del sys.modules['agents.browser.browser_controller']

    async def test_type_text_no_selector(self):
        text = "Hello World"
        await self.controller.type_text(text)

        # Verify execute_script was NOT called (no focus needed)
        self.controller.execute_script.assert_not_called()

        # Verify Input.insertText was called
        self.controller._send_cdp.assert_called_with("Input.insertText", {"text": text})

    async def test_type_text_with_selector(self):
        text = "Hello World"
        selector = "#my-input"

        await self.controller.type_text(text, selector)

        # Verify execute_script WAS called (to focus)
        self.controller.execute_script.assert_called_once()
        args, _ = self.controller.execute_script.call_args

        # Check for safe selector (json encoded)
        # "#my-input" -> "\"#my-input\""
        expected_selector = json.dumps(selector)
        self.assertIn(f"document.querySelector({expected_selector})", args[0])
        self.assertIn("el.focus()", args[0])

        # Verify Input.insertText was called
        self.controller._send_cdp.assert_called_with("Input.insertText", {"text": text})

    async def test_type_text_focus_fails(self):
        text = "Hello World"
        selector = "#missing-input"

        self.controller.execute_script.return_value = False

        with self.assertRaises(RuntimeError):
            await self.controller.type_text(text, selector)

        # Verify Input.insertText was NOT called
        self.controller._send_cdp.assert_not_called()

if __name__ == "__main__":
    unittest.main()
