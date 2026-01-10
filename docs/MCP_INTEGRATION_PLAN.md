# Y-IT Research MCP Integration Plan

## Modular MCP Server Architecture for Agentic Research

**Version**: 1.0  
**Date**: 2026-01-10  
**Status**: PLANNING

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ANTIGRAVITY / HNDL-IT                        │
│                         (Orchestrator Layer)                        │
└─────────────────┬───────────────────────────────────────────────────┘
                  │ MCP Protocol (JSON-RPC 2.0)
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP SERVER CONSTELLATION                       │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────┤
│  AIRWEAVE   │ NOTEBOOKLM  │   GEMINI    │  PERPLEXITY │   FUTURE   │
│  (Memory)   │ (Research)  │  (Vision)   │  (Search)   │   (...)    │
├─────────────┼─────────────┼─────────────┼─────────────┼────────────┤
│ Port: 8000  │ Port: 8010  │ Port: 8020  │ Port: 8030  │ Port: 80XX │
│ Docker      │ Standalone  │ Standalone  │ Standalone  │ Modular    │
└─────────────┴─────────────┴─────────────┴─────────────┴────────────┘
```

---

## 2. MCP Server Registry

### 2.1 Existing Servers

| Server | Purpose | Status | Port | Location |
|--------|---------|--------|------|----------|
| **Airweave** | Context retrieval, semantic memory | ✅ DEPLOYED | 8000 | Docker |
| **Browser Agent** | Web automation via CDP | ✅ ACTIVE | 8766 | hndl-it/agents |
| **Desktop Agent** | Windows automation | ✅ ACTIVE | 8767 | hndl-it/agents |
| **Vision Agent** | Screenshot analysis | ✅ ACTIVE | 8768 | hndl-it/agents |

### 2.2 Planned MCP Servers (Y-IT Research Stack)

| Server | Purpose | Status | Port | Notes |
|--------|---------|--------|------|-------|
| **NotebookLM MCP** | Source ingestion, audio overview | 🔲 PLANNED | 8010 | Core research |
| **Gemini MCP** | Deep research, grounding | 🔲 PLANNED | 8020 | API integration |
| **Perplexity MCP** | Real-time search | 🔲 PLANNED | 8030 | Live data |
| **Claude MCP** | Complex reasoning | 🔲 PLANNED | 8040 | Anthropic API |
| **Local LLM MCP** | Ollama models | 🔲 PLANNED | 8050 | Privacy/speed |

---

## 3. NotebookLM MCP Server Specification

### 3.1 Tools (Exposed Capabilities)

```yaml
tools:
  - name: create_notebook
    description: Create a new NotebookLM notebook
    params:
      - title: string
      - sources: list[url | file_path]
  
  - name: add_source
    description: Add source to existing notebook
    params:
      - notebook_id: string
      - source: url | file_path | text
  
  - name: query_notebook
    description: Ask a question across all sources
    params:
      - notebook_id: string
      - query: string
      - mode: "quick" | "deep" | "citations"
  
  - name: generate_audio_overview
    description: Create podcast-style audio summary
    params:
      - notebook_id: string
      - focus_topics: list[string]
  
  - name: extract_structured_data
    description: Extract data into structured format
    params:
      - notebook_id: string
      - schema: json_schema
      - query: string
  
  - name: list_notebooks
    description: List all user notebooks
  
  - name: get_source_citations
    description: Get citations for a claim
    params:
      - notebook_id: string
      - claim: string
```

### 3.2 Implementation Path

```
mcp-servers/
├── notebooklm/
│   ├── server.py          # FastMCP server
│   ├── auth.py            # Google OAuth handling
│   ├── browser_backend.py # Headless Chrome for NotebookLM
│   ├── tools/
│   │   ├── notebook.py
│   │   ├── sources.py
│   │   ├── query.py
│   │   └── audio.py
│   ├── config.yaml
│   └── requirements.txt
```

---

## 4. Y-IT Research Pipeline Integration

### 4.1 Research Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Y-IT RESEARCH PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. DISCOVERY   │────▶│  2. INGESTION   │────▶│  3. ANALYSIS    │
│  Perplexity MCP │     │  NotebookLM MCP │     │  Gemini MCP     │
│  (Find sources) │     │  (Ingest 500+)  │     │  (Deep research)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
     ┌──────────────────────────────────────────────────┘
     ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  4. SYNTHESIS   │────▶│  5. STORAGE     │────▶│  6. OUTPUT      │
│  Local LLM MCP  │     │  Airweave MCP   │     │  hndl-it UI     │
│  (Qwen/Mistral) │     │  (Save to KG)   │     │  (Present)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 4.2 Orchestrator Commands

```python
# Example: Research a Y-IT topic
async def research_topic(topic: str):
    # 1. Discovery - Find sources via Perplexity
    sources = await perplexity_mcp.call("search", {
        "query": f"real income data {topic} side hustle 2025",
        "count": 50
    })
    
    # 2. Ingestion - Add to NotebookLM
    notebook = await notebooklm_mcp.call("create_notebook", {
        "title": f"Y-IT: {topic}",
        "sources": sources
    })
    
    # 3. Analysis - Deep research via Gemini
    analysis = await gemini_mcp.call("deep_research", {
        "notebook_id": notebook.id,
        "queries": CHAPTER_QUERIES,  # From Source Vetting SOP
        "grounding": True
    })
    
    # 4. Synthesis - Local LLM refinement
    synthesis = await local_llm_mcp.call("synthesize", {
        "data": analysis,
        "voice": "Y-IT_SATIRICAL",
        "format": "chapter_outline"
    })
    
    # 5. Storage - Save to Airweave knowledge graph
    await airweave_mcp.call("store", {
        "collection": "y-it-research",
        "document": synthesis,
        "metadata": {"topic": topic}
    })
    
    return synthesis
```

---

## 5. Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Set up `mcp-servers/` directory structure
- [ ] Create FastMCP template server
- [ ] Implement NotebookLM MCP (browser-based)
- [ ] Test with single notebook workflow

### Phase 2: Research Stack (Week 2)

- [ ] Add Gemini MCP server (API-based)
- [ ] Add Perplexity MCP server (API-based)
- [ ] Integrate with hndl-it Orchestrator
- [ ] Test full discovery → ingestion pipeline

### Phase 3: Production (Week 3)

- [ ] Add Local LLM MCP server (Ollama bridge)
- [ ] Implement Airweave integration
- [ ] Create Y-IT research automation workflows
- [ ] Deploy with Docker Compose

### Phase 4: Scale (Week 4+)

- [ ] Add batch source processing
- [ ] Implement rate limiting and queuing
- [ ] Create monitoring dashboard
- [ ] Document API and usage patterns

---

## 6. Configuration

### 6.1 Unified MCP Config (`mcp_servers.yaml`)

```yaml
mcp_servers:
  airweave:
    host: localhost
    port: 8000
    transport: streamable-http
    auth: api_key
    
  notebooklm:
    host: localhost
    port: 8010
    transport: stdio
    auth: google_oauth
    
  gemini:
    host: localhost
    port: 8020
    transport: streamable-http
    auth: api_key
    
  perplexity:
    host: localhost
    port: 8030
    transport: streamable-http
    auth: api_key
    
  local_llm:
    host: localhost
    port: 8050
    transport: streamable-http
    auth: none
    backend: ollama
```

### 6.2 Environment Variables

```env
# mcp-servers/.env
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
GEMINI_API_KEY=...
PERPLEXITY_API_KEY=...
AIRWEAVE_API_KEY=...
OLLAMA_HOST=http://localhost:11434
```

---

## 7. Next Steps

1. **Create `mcp-servers/` directory** in workspace root
2. **Scaffold NotebookLM MCP server** using FastMCP
3. **Test Google OAuth flow** for NotebookLM access
4. **Build first tool**: `create_notebook` with source ingestion
5. **Integrate with hndl-it** via Orchestrator routing

---

## References

- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Airweave Documentation](https://airweave.ai/docs)
- [Y-IT Source Vetting SOP](../knowledge/y_it_production_automation_standard/artifacts/production_pipeline/source_vetting_sop_v2.md)
