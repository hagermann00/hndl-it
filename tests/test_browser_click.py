
import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.browser.ipc_handler import BrowserAgent

class TestBrowserAgentClick(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('agents.browser.ipc_handler.BrowserController')
        self.MockController = self.patcher.start()

        self.mock_controller_instance = self.MockController.return_value
        self.mock_controller_instance.start = AsyncMock()
        self.mock_controller_instance.click_element = AsyncMock()
        self.mock_controller_instance.close = AsyncMock()

    def tearDown(self):
        self.patcher.stop()
        if hasattr(self, 'agent'):
            self.agent.stop()

    def test_click_action_calls_controller(self):
        self.agent = BrowserAgent()
        import time
        time.sleep(1)

        selector = "#my-button"
        self.agent.process_action("click", {"selector": selector})

        self.mock_controller_instance.click_element.assert_called_with(selector)

    def test_click_action_handles_missing_selector(self):
        self.agent = BrowserAgent()
        import time
        time.sleep(1)

        with self.assertLogs('BrowserAgent', level='ERROR') as cm:
            self.agent.process_action("click", {})
            self.assertIn("requires a 'selector' or 'subject' in payload", cm.output[0])

        self.mock_controller_instance.click_element.assert_not_called()

if __name__ == "__main__":
    unittest.main()
