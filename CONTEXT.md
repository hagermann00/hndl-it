# hndl-it Context Document

## Version 5.6 | January 2026

---

## 🎯 What is hndl-it?

**hndl-it** is a local-first, Windows-native agentic system that lets you control your computer through natural language. It uses local LLMs (via Ollama) for semantic understanding and routes commands to specialized agents.

> *"Say it, and consider it handled."*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SUPERVISOR.PY                          │
│                (Singleton Process Manager)                   │
│            - PID lock file prevents duplicates               │
│            - Tree-kill ensures clean shutdown                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     LAUNCH_SUITE.PY                          │
│               (Unified UI + Agent Launcher)                  │
│                                                              │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐               │
│   │hndl-it │ │read-it │ │todo-it │ │voice-it│               │
│   │  🎯    │ │  📖    │ │  ✅    │ │  🎤    │               │
│   └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘               │
│       │          │          │          │                     │
│       └──────────┴────┬─────┴──────────┘                     │
│                       │                                      │
└───────────────────────┼──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                    ORCHESTRATOR                               │
│              (shared/orchestrator.py)                         │
│                                                               │
│   Tier 1: Regex Fast-Path (0ms)                              │
│           └─ Pattern matching for common commands             │
│                                                               │
│   Tier 2: LLM Router (Gemma 2B, ~200ms)                      │
│           └─ Semantic classification for ambiguous input      │
│                                                               │
│   Output: Structured Intent → IPC                            │
└───────────────────────┬──────────────────────────────────────┘
                        │ File-based IPC (ipc/*.json)
┌───────────────────────▼──────────────────────────────────────┐
│                       AGENTS                                  │
│                                                               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│   │ Browser  │ │ Desktop  │ │   Read   │ │  Vision  │       │
│   │   🌐     │ │   🖥️     │ │   🔊     │ │   👁️     │       │
│   │   CDP    │ │ pyauto   │ │   TTS    │ │ moondream │       │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧠 LLM Configuration

Located in `shared/llm_config.py`. Using "Two-Gear" strategy:

| Role | Model | VRAM | Purpose |
|------|-------|------|---------|
| **Router** | gemma2:2b | ~1.6 GB | Fast intent classification (always resident) |
| **Brain** | qwen2.5:3b | ~2.0 GB | Complex reasoning (on-demand) |
| **Vision** | moondream | ~1.7 GB | Image understanding (on-demand) |

**Total VRAM**: ~5.3 GB base, ~7.5 GB with overhead  
**Hardware**: RTX 2060 12GB → 4.5 GB headroom ✅

---

## 📁 Project Structure

```
hndl-it/
├── supervisor.py          # Singleton launcher with process tree management
├── launch_suite.py        # Unified icon manager + agent starter
├── warm_models.py         # Force-load LLMs into VRAM
├── launch_agents.py       # Standalone agent launcher
│
├── shared/
│   ├── orchestrator.py    # Semantic command router (Gemma 2B)
│   ├── ipc.py             # File-based inter-process communication
│   ├── llm_config.py      # Model configuration + VRAM validation
│   ├── voice_input.py     # Global hotkey + speech recognition
│   └── voice_router.py    # Keyword-based voice routing
│
├── floater/               # Main UI module
│   ├── tray.py            # System tray + command handling
│   ├── quick_dialog.py    # Command input bar (multiple modes)
│   ├── console.py         # Log console window
│   └── assets/            # Icons
│
├── read-it/               # TTS reader module
│   ├── main.py            # Reader panel + selection pill
│   └── ipc_handler.py     # TTS IPC listener
│
├── todo-it/               # Task manager module
│   ├── main.py            # Todo panel with persistence
│   └── todos.json         # Saved tasks (auto-persisted)
│
├── agents/
│   ├── browser/
│   │   ├── server.py          # WebSocket server (port 8766)
│   │   ├── browser_controller.py  # Chrome CDP automation
│   │   └── ipc_handler.py     # IPC-based browser control
│   ├── desktop/
│   │   ├── server.py          # WebSocket server (port 8767)
│   │   └── ipc_handler.py     # pyautogui automation
│   └── vision/                # Moondream image analysis (scaffold)
│
├── tests/
│   └── test_orchestrator.py   # Routing validation (13.5/14 pass)
│
└── docs/
    ├── MASTER_SYNTHESIS.md    # Multi-LLM strategic roadmap
    ├── MEM_RESEARCH_INTEGRATION.md  # Airweave + NotebookLM plans
    └── TODO.md                # Development backlog
```

---

## 🎮 Command Examples

### Regex Fast-Path (0ms)

| Command | Target | Action |
|---------|--------|--------|
| `go to reddit.com` | browser | navigate |
| `search cheap GPUs on ebay` | browser | search_site |
| `add buy milk` | todo | add |
| `read this to me` | read | speak |
| `type hello world` | desktop | type |
| `screenshot` | desktop | screenshot |

### LLM Router (Gemma 2B, ~200ms)

| Command | Target | Action |
|---------|--------|--------|
| `find the cheapest flight to Paris` | browser | search |
| `what did I work on yesterday?` | retrieval | search |
| `analyze this PDF` | research | upload |

---

## 🔌 Communication

### IPC (Inter-Process Communication)

File-based messaging in `ipc/` directory:

```python
from shared.ipc import send_command, check_mailbox

# Send command to agent
send_command("browser", "navigate", {"url": "https://reddit.com"})

# Agent checks for commands
action, payload = check_mailbox("browser")
```

### WebSocket (Legacy)

Original agent servers on dedicated ports:

- Browser: `ws://localhost:8766`
- Desktop: `ws://localhost:8767`
- Vision: `ws://localhost:8768`

---

## 🚀 Quick Start

```powershell
# 1. Warm up LLMs (first run or after reboot)
python warm_models.py

# 2. Launch the suite
python supervisor.py

# 3. Interact
# - Click icons to toggle panels
# - Type commands in input bar
# - Ctrl+Shift+Win for voice input
# - Right-click any icon for context menu
```

---

## 🎯 Voice Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+Win` | Toggle voice input (start/stop) |
| `Ctrl+Win+Alt` | Windows native dictation (Win+H) |

---

## 📊 Status Indicators

The 3 dots in the input bar show agent status:

- ⚫ Gray = Offline
- 🟢 Green = Connected + Idle
- 💚 Pulsing = Working
- 🟡 Yellow = Trouble
- 🔴 Red = Error

---

## 🔮 Roadmap

### Completed (v5.0-5.6)

- [x] Unified launcher (singleton protection)
- [x] Orchestrator with regex + LLM routing
- [x] VRAM optimization (Qwen 3B brain)
- [x] Clean shutdown (process tree kill)
- [x] Right-click context menus on all icons
- [x] Auto-start agent handlers
- [x] Todo-it persistence
- [x] Test suite (13.5/14 pass)

### Next Up

- [ ] Auto-update status dots based on agent heartbeat
- [ ] Airweave integration (memory retrieval)
- [ ] NotebookLM integration (research)
- [ ] Multi-step workflow execution
- [ ] Visual MCP integration

---

## 🛠️ Configuration

### settings.json

```json
{
  "ollama_url": "http://localhost:11434",
  "model": "gemma2:2b"
}
```

### Model Warmup

```powershell
python warm_models.py
# Loads gemma2:2b, qwen2.5:3b, moondream with keep_alive=-1
```

---

## 📝 Key Design Decisions

1. **Regex-First Routing**: 95% of commands hit regex patterns (0ms latency)
2. **Two-Gear LLM Strategy**: Light router always resident, heavy brain on-demand
3. **File-Based IPC**: Simple, debuggable, no socket complexity
4. **Singleton Protection**: Lock files prevent zombie processes
5. **Local-First**: All processing happens on-device, no cloud dependencies

---

*Consider it handled.* 🎯
