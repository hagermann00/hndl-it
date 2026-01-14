
import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.browser.ipc_handler import BrowserAgent

class TestBrowserAgentAsync(unittest.TestCase):
    def setUp(self):
        # Patch BrowserController class
        self.patcher = patch('agents.browser.ipc_handler.BrowserController')
        self.MockController = self.patcher.start()

        # Setup the mock instance
        self.mock_controller_instance = self.MockController.return_value
        self.mock_controller_instance.start = AsyncMock()
        self.mock_controller_instance.navigate = AsyncMock()
        self.mock_controller_instance.close = AsyncMock()

        # Patch asyncio.wait_for to verify timeout
        self.wait_for_patcher = patch('asyncio.wait_for', side_effect=asyncio.wait_for)
        self.mock_wait_for = self.wait_for_patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.wait_for_patcher.stop()
        if hasattr(self, 'agent'):
            self.agent.stop()

    def test_navigate_is_awaited_with_timeout(self):
        print("Initializing BrowserAgent...")
        self.agent = BrowserAgent()

        # Give the loop a moment to start and initialize controller
        import time
        time.sleep(1)

        url = "example.com"
        print(f"Sending navigate action for {url}...")

        # process_action blocks until the async action is complete
        self.agent.process_action("navigate", {"url": url})

        # Verify start was called
        self.mock_controller_instance.start.assert_awaited()

        # Verify navigate was called
        expected_url = "https://" + url
        self.mock_controller_instance.navigate.assert_called_with(expected_url)

        # Verify wait_for was called with timeout=30
        # We need to find the call that wraps our navigate coroutine
        # Since wait_for takes a coroutine as first arg, we can't easily equate equality of coroutines
        # checking one of the calls has timeout=30

        found_timeout = False
        for call in self.mock_wait_for.call_args_list:
            args, kwargs = call
            if kwargs.get('timeout') == 30:
                found_timeout = True
                break

        self.assertTrue(found_timeout, "asyncio.wait_for was not called with timeout=30")
        print("✅ navigate() was awaited with timeout!")

if __name__ == "__main__":
    unittest.main()
