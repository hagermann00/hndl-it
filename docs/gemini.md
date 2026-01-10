```markdown
# Gemini Suggestions for hndl-it
## Date: 2026-01-10

---

## TL;DR

You have excellent components ("Hands" and "Eyes") but lack a unified "Nervous System." While Claude suggested an Orchestrator (a central router), I recommend a **Shared State Bus** architecture. This allows `hndl-it` to know what `read-it` is reading and `todo-it` to know what the browser is looking at. For monetization, prioritize the **Y-IT Content Factory**—it's your fastest path to revenue using your existing tech stack.

---

## Priority 1: Architecture - The "Synapse" Shared State

**Current State:** Modules are isolated islands. `client.py` sends fire-and-forget commands.
**Problem:** If I say "Add *this* to my todo list", `hndl-it` doesn't know what "this" is (e.g., the URL in Browser Agent or the text in read-it).

**Suggestion:** Implement a lightweight **State Bus** (using `multiprocessing.managers.SyncManager` or a simple JSON-RPC state server) that acts as the "Short Term Memory."

All agents publish updates to the Bus:
* **Browser Agent:** Publishes `current_url`, `page_title` (on navigation).
* **read-it:** Publishes `current_text_snippet`, `status` (playing/paused).
* **Vision Agent:** Publishes `last_seen_description`.

**Why:** This enables "Context-Aware" commands.
* User: "Summarize this."
* Parser checks Bus: Is `read-it` active? No. Is `browser` active? Yes. -> Route to Browser Agent.

---

## Priority 2: UI/UX - "Magnetic" Modular Docking

**User Concern:** "Future proofing... visually optionally keep em interlocked."

**Suggestion:** Implement **Magnetic Window Snapping** in PyQt.
Instead of a rigid bar, allow the floating icons (`hndl-it`, `read-it`, `todo-it`) to "snap" to each other when dragged close, forming a dynamic toolbar.

**Logic:**
1. On `moveEvent`, calculate distance to other active module windows.
2. If distance < 20px, snap coordinates to align edges.
3. If snapped, moving the "parent" (hndl-it) moves the "children" (read-it/todo-it).

This solves the "screen clutter" problem while keeping modules independent.

---

## Priority 3: Monetization - The Y-IT "Content Factory"

**Target:** $1,500/mo ASAP.
**Strategy:** Automation of the "boring stuff" for your satire brand.

**Pipeline Suggestion:**
Build a specific `y-it` script that utilizes your existing agents to generate rough drafts 10x faster.

**Workflow:**
1. **Trigger:** "Research [Guru Name]" in `hndl-it`.
2. **Browser Agent:** - Searches [Guru] on YouTube/Twitter.
   - Scrapes top 5 video transcripts/tweets.
3. **Local LLM (Brain):** - Extracts "Claims".
   - Applies "Satire Persona" (Prompt: "Rewrite these claims as if you are a cynical raccoon...").
4. **Desktop Agent:** - Saves `[Guru]_Draft.md` to your Obsidian/Drive folder.

**Result:** You skip the research/drafting phase and go straight to polishing. This increases your content output velocity immediately.

---

## Priority 4: Local LLM - Dynamic Model Loading (The "Gear Shift")

**Hardware:** RTX 2060 (12GB VRAM). 
**Constraint:** Moondream (1.7GB) is always on.

**Suggestion:** Use a **Two-Gear System**.
1. **Low Gear (Always On):** `Qwen2.5-0.5B` or `Danube-1.8B`. 
   - *Cost:* ~1GB VRAM.
   - *Job:* Intent classification ("Is this a browser command?"), simple chat, formatting.
   - *Speed:* Instant.
2. **High Gear (On Demand):** `Mistral-Nemo-12B` (Quantized Q4_K_M) or `Qwen2.5-14B`.
   - *Cost:* ~8-10GB VRAM (Fits in remaining 12GB - 1.7GB - 1GB = 9.3GB).
   - *Job:* Summarization, Y-IT Satire generation, complex reasoning.
   - *Trigger:* Only loaded when "Low Gear" detects a complex intent.

**Why:** Keeps the system snappy for 90% of commands (Music, App Launching) without choking VRAM.

---

## Code Snippets

### Magnetic Docking Logic (PyQt6)

```python
# In your FloatingIcon class (shared/ui_base.py suggested)

def moveEvent(self, event):
    # Snap to other known windows (passed in or found via QApplication)
    SNAP_DIST = 25
    my_pos = self.pos()
    
    for other_window in known_modules:
        if other_window == self or not other_window.isVisible(): continue
        
        other_pos = other_window.pos()
        
        # Simple Vertical Snap (Snap bottom of this to top of other)
        dist_y = abs((my_pos.y() + self.height()) - other_pos.y())
        dist_x = abs(my_pos.x() - other_pos.x())
        
        if dist_y < SNAP_DIST and dist_x < SNAP_DIST:
            # Snap!
            self.move(other_pos.x(), other_pos.y() - self.height() - 5)
            # (Optional) Draw visual connector line
            return
            
    super().moveEvent(event)

```

### VAD-Gated Voice Input (Preventing False Triggers)

```python
# shared/voice.py integration with Silero VAD (Lightweight)
import torch

class VoiceGate:
    def __init__(self):
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                           model='silero_vad',
                                           force_reload=False)
        self.get_speech_timestamps, _, _, _, _ = utils

    def is_speech(self, audio_chunk):
        # Only send to Whisper if VAD says it's speech
        # Saves massive processing power/latency
        timestamps = self.get_speech_timestamps(audio_chunk, self.model)
        return len(timestamps) > 0

```

---

## Questions for User

1. **Y-IT Specifics:** Do you have a specific "Persona Prompt" for Y-IT already, or should the `hndl-it` Brain help generate one?
2. **Data Persistence:** Do you prefer a simple JSON file for the "Shared State" (easiest to debug) or a Python memory object (fastest)?
3. **Voice Hardware:** Are you using a dedicated mic (good quality) or laptop mic? (Affects VAD sensitivity settings).

```

```
