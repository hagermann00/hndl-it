# Hndl-it: Local-First Agentic Workspace

> *Say it, and consider it handled.*

**Hndl-it** is a consolidated, local-first agent orchestration system for Windows. It decouples the "Brain" (Orchestrator) from the "Hands" (Specialized Agents), allowing for robust, low-latency control of your digital environment.

## 🏗️ Architecture (v5.0+)

```
┌─────────────────────────────────────────────────────────┐
│                    SUPERVISOR.PY                        │
│              (Singleton Process Manager)                │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   LAUNCH_SUITE.PY                       │
│            (Unified Icon + UI Manager)                  │
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ hndl-it │ │ read-it │ │ todo-it │ │voice-it │       │
│  │  Icon   │ │  Icon   │ │  Icon   │ │  Icon   │       │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
└───────┼──────────┼──────────┼──────────┼───────────────┘
        │          │          │          │
        └──────────┴────┬─────┴──────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    ORCHESTRATOR                         │
│              (Semantic Command Router)                  │
│                                                         │
│    Regex Fast-Path (0ms) → Router LLM (Gemma 2B)       │
└─────────────────┬───────────────────────────────────────┘
                  │ IPC (File-based)
┌─────────────────▼───────────────────────────────────────┐
│                      AGENTS                             │
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Browser │ │ Desktop │ │  Read   │ │Research │       │
│  │  (CDP)  │ │(pyauto) │ │  (TTS)  │ │(memory) │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Start the suite
python supervisor.py

# 2. Click icons to interact
# 3. Use voice: Ctrl+Shift+Win to toggle
```

## 📦 Modules

### 1. hndl-it (Main Router)

- **Click**: Opens command input bar
- **Input**: Type natural language commands
- **Orchestrator**: Routes commands via Gemma 2B

### 2. read-it (TTS Reader)

- **Click**: Opens reader panel
- **Highlight text**: Popup appears with "Play" / "Summarize"
- **TTS**: Edge-quality speech synthesis

### 3. todo-it (Task Manager)

- **Click**: Opens todo panel
- **Voice**: "Add [task]" or "Todo [item]"
- **Persistence**: Saves to JSON automatically

### 4. voice-it (Voice Input)

- **Click**: Toggle microphone
- **Hotkey**: `Ctrl+Shift+Win`
- **Routes**: Commands to Orchestrator

## 🎯 Command Examples

| Command | Target | Action |
|---------|--------|--------|
| "Go to reddit.com" | Browser | Navigate |
| "Search cheap GPUs on ebay" | Browser | Search |
| "Add buy milk" | Todo | Add task |
| "Read this to me" | Read | TTS |
| "Type hello world" | Desktop | Keyboard |
| "Click submit button" | Desktop | Click |
| "What did I do yesterday?" | Retrieval | Airweave |
| "Research AI trends" | Research | NotebookLM |

## 🧠 LLM Configuration

Located in `shared/llm_config.py`:

| Role | Model | VRAM | Purpose |
|------|-------|------|---------|
| Router | gemma2:2b | 1.6 GB | Fast intent classification |
| Brain | qwen2.5:3b | 2.0 GB | Complex reasoning |
| Vision | moondream | 1.7 GB | Image understanding |

**Total VRAM Budget**: ~5.3 GB (safe on 12GB card)

## 📁 Project Structure

```
hndl-it/
├── supervisor.py          # Singleton launcher
├── launch_suite.py        # Unified icon manager
├── shared/
│   ├── orchestrator.py    # Semantic router (Gemma 2B)
│   ├── ipc.py             # File-based IPC
│   ├── llm_config.py      # Model configuration
│   ├── voice_input.py     # Voice capture
│   └── voice_router.py    # Keyword routing
├── floater/               # Main UI module
├── read-it/               # TTS reader module
├── todo-it/               # Task manager module
├── agents/
│   ├── browser/           # Chrome CDP controller
│   ├── desktop/           # pyautogui automation
│   └── vision/            # Image analysis (moondream)
└── docs/                  # Documentation
```

## 🔧 Configuration

Settings stored in `settings.json`:

```json
{
  "ollama_url": "http://localhost:11434",
  "model": "gemma2:2b"
}
```

## 🛣️ Roadmap

- [x] Unified launcher (v5.0)
- [x] Orchestrator with semantic routing (v5.0)
- [x] VRAM optimization (Qwen 3B brain)
- [x] Singleton protection
- [x] Right-click context menus
- [ ] Airweave integration (memory retrieval)
- [ ] NotebookLM integration (research)
- [ ] Multi-step workflow execution
- [ ] Visual MCP integration

---

*Consider it handled.*
