# System Architecture Refinement Plan

## Status: PROPOSED

**Date**: 2026-01-13

## 1. Executive Summary

This plan addresses the "system-wide" architectural refinement requested. The core goal is to unify the disparate routing logic (Voice Router vs. Orchestrator) and ensure the "Native-First" A2UI pipeline is fully operational from input to display.

## 2. Current Architecture & Gaps

### 2.1 The "Two Brains" Problem

Currently, the system has two disconnected routing paths:

1. **Text Input (Floater)**:
    - Inputs in `QuickDialog` emit a signal, but the wiring to `shared/orchestrator.py` appears incomplete in `launch_suite.py`.
2. **Voice Input**:
    - Uses `shared/voice_router.py` (simple Regex) directly in `launch_suite.py`.
    - **Gap**: Voice commands miss out on the advanced Context/Memory/LLM routing capabilities of the central Orchestrator.

### 2.2 The Missing Links

- **Orchestrator (`shared/orchestrator.py`)**: Exists and handles A2UI construction (`render_a2ui`), but:
  - `store` action is unimplemented (`# TODO`).
  - It is not actively invoked by the Floater's text input.
- **Airweave Integration**:
  - `AirweaveClient` is ready.
  - `Orchestrator` calls it for `search`.
  - But `store` (saving memories) is missing.

## 3. Implementation Plan

### Phase 1: Unify Routing (The "One Brain" Policy)

**Goal**: All inputs (Text & Voice) should flow through `Orchestrator.process()`.

1. **Update `launch_suite.py`**:
    - Connect `QuickDialog.command_submitted` -> `Orchestrator.process()`.
    - Modify Voice Handler: If `voice_router` returns `HNDL_IT` (generic), forward to `Orchestrator.process()` instead of just printing it.
2. **Refine `shared/voice_router.py`**:
    - Keep it for *instant* local actions (stop, mute, hard commands).
    - Delegate everything else "up" to the Orchestrator.

### Phase 2: Complete the Memory Cycle

**Goal**: Make "Remember this" actually work.

1. **Implement `Orchestrator` Store Action**:
    - In `shared/orchestrator.py`, fill in the `store` block.
    - Call `AirweaveClient.index()` (needs to be verified/added if missing).
2. **A2UI Feedback**:
    - On successful store, render a small A2UI `Card` confirming the save.

### Phase 3: Visualize the Brain

**Goal**: Users should see *why* an action was taken.

1. **Trace Visualization**:
    - When `Orchestrator` routes a command, send a "Thought Trace" to the `QuickDialog` log (e.g., `[Router] Match: 'search' (Confidence: 0.9)`).
2. **A2UI Rendering**:
    - Verify `Floater` correctly renders the JSON payloads returned by `Orchestrator`.

## 4. Execution Steps (Immediate)

1. **Wire Floater**: Edit `launch_suite.py` to import and usage `get_orchestrator`.
2. **Enable Storage**: Update `orchestrator.py` to handle `store`.
3. **Test**: Verified loop of "Recall X" -> Airweave -> A2UI Card.

## 5. User Decision

- **Option A**: Turbo Mode - Proceed immediately with Phase 1 & 2.
- **Option B**: Review - Discuss specific logic mapping before coding.
