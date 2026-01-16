"""
Test Orchestrator Retrieval Store
Simulates a user command "store this important info" to verify Airweave storing.
"""
import sys
import os
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Mock ollama before importing orchestrator
from unittest.mock import MagicMock
sys.modules["ollama"] = MagicMock()

from shared.orchestrator import Orchestrator
import shared.airweave_client

class MockAirweaveClient:
    def __init__(self):
        self.stored_content = []

    def search(self, query, limit=5, **kwargs):
        return []

    def to_a2ui(self, results):
        return {}

    def store(self, content, metadata=None):
        self.stored_content.append(content)
        return True

# Replace the real client with our mock
mock_client = MockAirweaveClient()
shared.airweave_client.get_airweave_client = lambda: mock_client

class TestRetrievalStore(unittest.TestCase):
    def test_store_command(self):
        orch = Orchestrator()

        # Test "store" triggering (avoid "save this" which hits context regex)
        # Regex: (r"^(save|store|remember this) (.+)", "retrieval", "store")
        cmd = "store verify retrieval store works"
        result = orch.process(cmd)

        print(f"Command: {cmd}")
        print(f"Result Target: {result['target']}")
        print(f"Result Action: {result['action']}")
        if result['action'] == 'error':
            print(f"Error Params: {result.get('params')}")

        self.assertEqual(result['target'], 'floater')
        self.assertEqual(result['action'], 'confirm')
        self.assertIn("verify retrieval store works", mock_client.stored_content[0])
        print("✅ SUCCESS: Store command routed correctly and content stored!")

if __name__ == "__main__":
    unittest.main()
