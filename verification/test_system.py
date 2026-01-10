import asyncio
import websockets
import sys

async def test_agent(name, port):
    uri = f"ws://localhost:{port}"
    print(f"Testing {name} at {uri}...", end=" ")
    try:
        async with websockets.connect(uri) as websocket:
            # Wait for initial status/handshake
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"[OK] Connected. Received: {msg[:50]}...")
                return True
            except asyncio.TimeoutError:
                print(f"[WARN] Connected, but no initial message received.")
                return True
    except ConnectionRefusedError:
        print(f"[FAIL] Connection Refused (Is it running?)")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

async def main():
    print("[INFO] Hndl-it System Verification")
    print("-----------------------------")
    
    results = []
    results.append(await test_agent("Browser Agent", 8766))
    results.append(await test_agent("Desktop Agent", 8767))
    
    # Check vision only if passed arg (simple check)
    if "--with-vision" in sys.argv:
        results.append(await test_agent("Vision Agent", 8768))
    
    print("-----------------------------")
    if all(results):
        print("[SUCCESS] All checked systems are operational.")
        sys.exit(0)
    else:
        print("[FAILURE] Some systems failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
