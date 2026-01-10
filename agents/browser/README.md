# hndl-it Browser Agent

Standalone browser automation agent.

## Quick Start

```powershell
# Start Chrome with debug port first
chrome --remote-debugging-port=9223 --user-data-dir="C:\Users\dell3630\AppData\Local\Google\Chrome\User Data\hndl-it"

# Then run the agent
python run.py
```

## Commands Supported

| Command | Example |
|---------|---------|
| Navigate | `go to google`, `open reddit` |
| Scroll | `scroll down`, `scroll up` |
| Back/Forward | `back`, `forward` |
| Refresh | `refresh` |
| Scrape | `scrape this page` |

## API

- **WebSocket**: `ws://localhost:8766/`
- **Health**: `GET http://localhost:8766/health`

## Message Format

```json
{"type": "command", "content": "go to google"}
```

Response:
```json
{"type": "action", "content": "✓ Navigated to google.com"}
```
