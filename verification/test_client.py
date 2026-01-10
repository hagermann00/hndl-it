import asyncio
import websockets
import json
import uuid
import sys

async def test_browser_agent():
    uri = "ws://localhost:8766"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # 1. Test Navigation
            cmd_id = str(uuid.uuid4())
            nav_cmd = {
                "id": cmd_id,
                "action": "navigate",
                "url": "example.com"
            }
            print(f"Sending Navigate: {nav_cmd}")
            await websocket.send(json.dumps(nav_cmd))
            
            # Loop to receive responses until we get the result
            async for message in websocket:
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data.get("type") == "result" and data.get("command_id") == cmd_id:
                    print("Navigation Success!")
                    break
                if data.get("type") == "error":
                    print(f"Error: {data}")
                    break

            # 2. Test Scraping
            cmd_id = str(uuid.uuid4())
            scrape_cmd = {
                "id": cmd_id,
                "action": "scrape"
            }
            print(f"Sending Scrape: {scrape_cmd}")
            await websocket.send(json.dumps(scrape_cmd))
            
            async for message in websocket:
                data = json.loads(message)
                # print(f"Received: {data}") # noisy
                
                if data.get("type") == "result" and data.get("command_id") == cmd_id:
                    text_len = len(data["data"].get("text", ""))
                    print(f"Scrape Success! Got {text_len} chars.")
                    break
                
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_browser_agent())
    except KeyboardInterrupt:
        pass
