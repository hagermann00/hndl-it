import time
import threading
from unittest.mock import MagicMock

# Mock Orchestrator
class MockOrchestrator:
    def process(self, text):
        time.sleep(2)
        return {"target": "mock", "action": "test", "params": {}}

# Mock send_command
def mock_send_command(target, action, params):
    print(f"Sent: {target}/{action}")

# Original Logic (Sync)
def process_voice_command_sync(text, orchestrator, send_command_func):
    print(f"🎤 Voice Process: '{text}'")
    try:
        intent = orchestrator.process(text)
        target = intent.get("target")
        action = intent.get("action")
        params = intent.get("params", {})

        if target and target != "floater":
            send_command_func(target, action, params)
        elif target == "floater":
            send_command_func("hndl", "input", {"text": text, "response": params.get("response")})
    except Exception as e:
        print(f"❌ Error: {e}")

# Optimized Logic (Async)
def process_voice_command_async(text, orchestrator, send_command_func):
    def _worker():
        print(f"🎤 Voice Process (Async): '{text}'")
        try:
            intent = orchestrator.process(text)
            target = intent.get("target")
            action = intent.get("action")
            params = intent.get("params", {})

            if target and target != "floater":
                send_command_func(target, action, params)
            elif target == "floater":
                send_command_func("hndl", "input", {"text": text, "response": params.get("response")})
        except Exception as e:
            print(f"❌ Error: {e}")

    threading.Thread(target=_worker).start()

if __name__ == "__main__":
    orchestrator = MockOrchestrator()

    # Test Sync
    print("Testing Synchronous...")
    start = time.time()
    process_voice_command_sync("test sync", orchestrator, mock_send_command)
    duration_sync = time.time() - start
    print(f"Sync Duration: {duration_sync:.4f}s")

    # Test Async
    print("\nTesting Asynchronous...")
    start = time.time()
    process_voice_command_async("test async", orchestrator, mock_send_command)
    duration_async = time.time() - start
    print(f"Async Duration: {duration_async:.4f}s")

    # Wait for async to finish printing
    time.sleep(2.1)

    if duration_sync > 1.5 and duration_async < 0.1:
        print("\n✅ PASS: Async implementation unblocked main thread.")
    else:
        print("\n❌ FAIL: Performance requirements not met.")
        exit(1)
