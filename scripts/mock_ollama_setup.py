
import sys
from unittest.mock import MagicMock
import time
import asyncio

# Mock ollama module
mock_ollama = MagicMock()

class MockClient:
    def __init__(self, host=None, timeout=None):
        pass

    def generate(self, model, prompt, stream=False, options=None):
        # Simulate network latency
        time.sleep(0.1)
        return {"response": '{"target": "browser", "action": "navigate", "params": {"url": "http://example.com"}}'}

class MockAsyncClient:
    def __init__(self, host=None, timeout=None):
        pass

    async def generate(self, model, prompt, stream=False, options=None):
        # Simulate network latency
        await asyncio.sleep(0.1)
        return {"response": '{"target": "browser", "action": "navigate", "params": {"url": "http://example.com"}}'}

mock_ollama.Client = MockClient
mock_ollama.AsyncClient = MockAsyncClient

sys.modules["ollama"] = mock_ollama
