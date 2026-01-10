# Hndl-it Multi-LLM Synthesis Scratchpad

Started: 2026-01-10
Objective: Synthesize 8 LLM perspectives into a Unified Strategic Roadmap.

## Framework

- **Hardware**: RTX 2060 (12GB VRAM), 48GB System RAM.
- **Goal**: Local-First, Windows Native, "Turbo Mode" development.
- **Current State**: Supervisor Architecture, Independent Processes, IPC Voice Routing.

## Batch 1 Summary (Gemini, DeepThink, DeepSeek)

- **Arch**: Event Bus / Shared State.
- **Models**: "Two-Gear" (Tiny Router + Big Brain).
- **Voice**: Silero VAD + Semantic Buffer.
- **UI**: Magnetic Snapping / Radial Menus.
- **Money**: Y-IT Automated Satire Pipeline.

## Batch 2 Summary (Grok, ChatGPT4, Perplexity Local)

- **Arch**: Hybrid Local/Cloud. Central Brain Routing.
- **Models**: GPT4 suggests **Qwen 2.5 3B (Coordinator)** + Qwen 2.5 7B (Reasoning).
- **Voice**: Vosk vs Whisper.cpp.
- **Money**: "Hybrid Freemium" vs "Dogfood Y-IT".

## Batch 3 Analysis (Claude, Perplexity Suggestion)

**Architecture**:

- **Claude**: "Wire up what you have". Codebase is "80% scaffold, 20% connected". Wants `shared/orchestrator.py` NOW.
- **Perplexity**: "Integration Gap" is the main blocker. Recommends `Orchestrator` pattern identical to Claude.
- *Synthesis*: The "Orchestrator" is the missing link. All top-tier models (Claude, Perplexity) focus here.

**Models**:

- **Claude**: Confirms Llama 3.2 3B + Qwen 2.5 7B Hybrid.
- **Perplexity**: Qwen 2.5 7B + Llama 3.2 3B.
- *Synthesis*: Strong consensus on the 3B/7B split.

**Voice**:

- **Claude**: "Don't build STT, use Whisper.cpp".
- **Perplexity**: Whisper.cpp + `webrtcvad`.
- *Synthesis*: Whisper.cpp is the clear winner for local accuracy/speed.

**UI/UX**:

- **Claude**: Progress Ring (Code provided).
- **Perplexity**: Progress Ring + Responsive Positioning (Percentage based).

## MAJOR CONFLICTS & RESOLUTIONS

1. **Architecture: Bus vs. Brain**
    - *Conflict*: **Gemini/DeepThink** want a tech-heavy "Event Bus" (ZeroMQ/Redis) to decouple everything. **Claude/Perplexity** want a logic-heavy "Orchestrator Class" to centralize intelligence.
    - *Resolution*: **The Orchestrator**. We are in Python. A central Brain Class is easier to debug and manage "Intent" than a stateless Message Bus right now. We can add existing IPC to it.

2. **Voice Stack: Old vs. New**
    - *Conflict*: **Grok/GPT4** suggest "Vosk" (Fast, Old, Reliable). **DeepSeek/Claude** suggest "Whisper.cpp" (New, Smart, slightly heavier).
    - *Resolution*: **Whisper.cpp**. The "Premium" feel requires high-accuracy transcription (Vosk often fails accents/context). We have the VRAM (just barely) or CPU headroom.

3. **Monetization: Service vs. Product**
    - *Conflict*: **GPT4** says "Sell Services" (Manual/Agency work). **DeepSeek** says "Sell Software" (Tiered License).
    - *Resolution*: **Dogfooding (Y-IT)**. We build the "Content Factory" for *ourselves* first (Service model for us), then package it as the "Pro Tier" functionality (Product model).
