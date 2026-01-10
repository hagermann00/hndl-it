# MCP Servers for Y-IT Research Pipeline

Standalone MCP servers for agentic research integration.

## Servers

| Server | Port | Status | Description |
|--------|------|--------|-------------|
| `notebooklm/` | 8010 | 🔲 Planned | Google NotebookLM integration |
| `gemini/` | 8020 | 🔲 Planned | Gemini Deep Research |
| `perplexity/` | 8030 | 🔲 Planned | Real-time search |
| `local_llm/` | 8050 | 🔲 Planned | Ollama bridge |

## Quick Start

```bash
# Install dependencies
pip install fastmcp

# Run a server
cd notebooklm && python server.py
```

## Architecture

These servers follow MCP (Model Context Protocol) standard and integrate with:

- **hndl-it** (local orchestrator)
- **Antigravity** (development agent)
- **Airweave** (context retrieval)

See `../docs/MCP_INTEGRATION_PLAN.md` for full architecture.
