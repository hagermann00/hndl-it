# Memory & Research Integration Strategy

**Status**: Planned / Stubs Created in Orchestrator
**Date**: 2026-01-10

## Overview

To move beyond simple automation ("Click this") to true agency ("Research this"), hndl-it integrates two powerful memory systems via the Orchestrator.

## 1. Retrieval (Long Term Memory) -> Airweave

**Role**: Remember the user's files, past chats, and personal data.
**Integration**:

- **AgentType**: `RETRIEVAL`
- **Mechanism**: MCP Bridge (Airweave Server) or Direct API.
- **Trigger**: "Recall", "Remember", "What did I do..."
- **Orchestrator Logic**:

  ```python
  if intent.target == "retrieval":
      results = airweave_mcp.search(intent.params["query"])
      return summarize(results)
  ```

## 2. Research (Deep Analysis) -> NotebookLM

**Role**: Analyst for heavy documents (PDFs, Transcripts).
**Integration**:

- **AgentType**: `RESEARCH`
- **Mechanism**: Google NotebookLM API (or MCP Wrapper).
- **Trigger**: "Analyze this PDF", "Deep dive on this Guru".
- **Orchestrator Logic**:

  ```python
  if intent.target == "research":
      source_id = notebooklm.upload(intent.params["file"])
      insight = notebooklm.query(source_id, "Extract key claims")
      return insight
  ```

## Why This Matters (The "Y-IT" Pipeline)

For the Satire Content Factory:

1. **Browser Agent** scrapes Guru Tweets -> `guru_tweets.txt`
2. **Orchestrator** sends `guru_tweets.txt` to **NotebookLM**.
3. **NotebookLM** extracts "Claims".
4. **Orchestrator** sends Claims to **Brain (Qwen 7B)** to write Satire.

This separation keeps the "Thinking" local (Qwen) but the "Heavy Reading" specialized (NotebookLM).
