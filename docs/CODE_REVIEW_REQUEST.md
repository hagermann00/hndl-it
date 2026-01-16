# hndl-it Code Review Request

## Repository

**GitHub:** <https://github.com/hagermann00/hndl-it>

## Project Overview

**hndl-it** is a local-first, Windows-native AI agent orchestration system. It serves as "Local Hands" for cloud-based AI assistants, enabling them to control the desktop, browser, and local applications.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 ORCHESTRATOR LAYER                  │
│     (launch_suite.py / supervisor.py)               │
└─────────────────────┬───────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    ▼                 ▼                 ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│ BROWSER │     │ DESKTOP │     │ VISION  │
│  AGENT  │     │  AGENT  │     │  AGENT  │
│ :8766   │     │ :8767   │     │ :8768   │
└─────────┘     └─────────┘     └─────────┘
    │                 │               │
    └─────────────────┴───────────────┘
              Pure CDP / Ollama / IPC
```

## Key Components

1. **Floater UI** (`floater/`) - Minimal overlay for voice/text input
2. **Browser Agent** (`agents/browser/`) - Chrome automation via CDP
3. **Desktop Agent** (`agents/desktop/`) - Windows automation
4. **Vision Agent** (`agents/vision/`) - Screen analysis via Moondream
5. **GPU Monitor** (`gpu_monitor.py`) - System resource widget
6. **MCP Servers** (`mcp-servers/`) - Model Context Protocol integrations

## Tech Stack

- Python 3.13+
- PyQt6 (UI)
- Pure CDP (Chrome DevTools Protocol)
- Ollama (Local LLMs)
- WebSockets / IPC

## Stats

- ~1,663 Python files
- ~20 MB codebase
- Latest: v5.5+ with MCP integration

## Review Questions

1. **Architecture:** Is the 3-agent split (Browser/Desktop/Vision) the right approach?
2. **Code Quality:** What patterns need cleanup or refactoring?
3. **MCP Integration:** Is wrapping browser automation in MCP the best way to access web-based LLMs without API fees?
4. **Performance:** Any obvious bottlenecks or resource concerns?
5. **Security:** Are there risks in the CDP/browser automation approach?

## Files to Focus On

- `launch_suite.py` - Main orchestrator
- `agents/browser/browser_controller.py` - CDP implementation
- `floater/main.py` - UI entry
- `mcp-servers/browser_llm_server.py` - New LLM browser MCP

Please provide candid feedback on architecture, code quality, and potential improvements.
