# Claude Suggestions for hndl-it

## Date: 2026-01-10

---

## TL;DR

Your codebase is **80% scaffolded, 20% connected**. The agents work independently but the orchestration layer is missing. Before adding todo-it or voice, **wire up what you have**. The model selection synthesis from earlier stands—Llama 3.2:3B + Qwen2.5:7B hybrid is correct for your hardware.

---

## Priority 1: Architecture - The Missing Orchestrator

**Problem I See In Code:**

Your `floater/parser.py` exists but `run.py` just launches processes independently. There's no central brain routing commands between agents.

```
Current State:
run.py → spawns processes → they sit waiting
floater/main.py → sends to... nothing? 

What's Missing:
floater → ORCHESTRATOR → routes to correct agent → returns result
```

**Suggestion:**

Create `shared/orchestrator.py`:

```python
# shared/orchestrator.py
class Orchestrator:
    def __init__(self):
        self.agents = {
            "browser": "ws://localhost:8766",
            "desktop": "ws://localhost:8767",
            "vision": "ws://localhost:8768"
        }
        self.brain = None  # Local LLM connection
    
    async def route(self, user_input: str) -> str:
        # Step 1: Classify intent (simple rules first, LLM later)
        intent = self.classify(user_input)
        
        # Step 2: Route to agent
        if intent.agent == "browser":
            return await self.send_to_browser(intent.command)
        # ... etc
```

**Why This Matters:**
- Without this, adding todo-it or voice just creates more disconnected modules
- The orchestrator IS the product—agents are just hands

---

## Priority 2: UI/UX - Progress Ring Implementation

**From your TODO.md:** You want a progress ring around icons.

**Code Location:** `floater/overlay.py` - currently just a static circle

**Suggestion:**

```python
# In floater/overlay.py - Add animated ring
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0  # 0-100
        self._animation = None
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw arc based on self.progress
        rect = self.rect().adjusted(2, 2, -2, -2)
        span = int(self.progress * 3.6 * 16)  # Qt uses 1/16th degrees
        painter.setPen(QPen(QColor("#3498db"), 3))  # Blue ring
        painter.drawArc(rect, 90 * 16, -span)
    
    def set_progress(self, value: int):
        self.progress = value
        self.update()
```

**Integration Point:** `floater/tray.py` line 99 - the icon widget

---

## Priority 3: Voice Integration - Don't Build STT, Use Whisper.cpp

**Your VOICE_INPUT_ARCHITECTURE.md** mentions SpeechRecognition library.

**Problem:** Python SpeechRecognition is slow and requires internet for good accuracy.

**Better Path:**

1. Use `whisper.cpp` (C++ port) - runs locally, fast
2. Install via: `pip install pywhispercpp`
3. Uses ~1GB VRAM (fits with Moondream + Brain)

```python
# shared/voice_input.py
from pywhispercpp.model import Model

class VoiceInput:
    def __init__(self):
        self.model = Model('base.en')  # 140MB, English only
    
    def transcribe(self, audio_path: str) -> str:
        segments = self.model.transcribe(audio_path)
        return ' '.join([s.text for s in segments])
```

**Silence Detection:** Use `webrtcvad` library - lightweight, works great for end-of-speech detection.

---

## Priority 4: Local LLM - Wire Ollama Into Parser

**Your `floater/parser.py` exists but doesn't call Ollama.**

Looking at line 1-50 of parser.py - it's all regex heuristics.

**The Bridge:**

```python
# In floater/parser.py - Add LLM fallback
import requests

def parse_with_llm(user_input: str) -> dict:
    """When regex fails, ask the brain"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": f"""Convert this to JSON command:
Input: "{user_input}"
Output format: {{"agent": "browser|desktop|vision", "action": "...", "params": {{}}}}
JSON:""",
            "stream": False
        }
    )
    return json.loads(response.json()["response"])
```

**Decision Tree:**
1. Try regex first (instant, free)
2. If confidence < 0.7 → call LLM
3. If LLM fails → ask user to clarify

---

## Priority 5: Monetization - Y-IT Pipeline Integration

**This is where previous synthesis applies directly.**

Your hndl-it should **dogfood Y-IT production** before selling to others.

**Concrete Integration:**

| hndl-it Agent | Y-IT Use Case |
|---------------|---------------|
| Browser Agent | Scrape guru claims from 3 sites |
| Vision Agent | Extract text from screenshots of paywalled content |
| Desktop Agent | Organize scraped files to Google Drive |
| Orchestrator | Chain: scrape → extract → dedupe → package for Claude |

**File to Create:** `y-it/pipeline.py`

```python
# y-it/pipeline.py
class YITPipeline:
    async def research_guru(self, guru_name: str):
        # 1. Browser scrapes
        claims = await self.browser.scrape_guru_site(guru_name)
        
        # 2. Vision extracts from images
        image_claims = await self.vision.extract_text_from_screenshots()
        
        # 3. Dedupe & package
        bundle = self.package_for_claude(claims + image_claims)
        
        # 4. Save to G-Drive
        await self.desktop.save_to_drive(bundle, f"y-it/research/{guru_name}")
        
        return bundle
```

---

## Code Snippets: Quick Wins

### 1. Fix Headless Execution (from TODO.md)

In `run.py` line 45:

```python
# BEFORE:
floater_process = subprocess.Popen(
    [sys.executable, "floater/main.py"],
    ...
)

# AFTER (headless):
if sys.platform == 'win32':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
floater_process = subprocess.Popen(
    [sys.executable, "floater/main.py"],
    startupinfo=startupinfo if sys.platform == 'win32' else None,
    ...
)
```

### 2. Fix Browser Agent Tab Isolation

In `agents/browser/browser_controller.py` line 89:

Your comment says "MORE DELIBERATE ACTION/STEPS TO CLOSE" - the issue is `_launch_chrome` creates one profile. If user has personal Chrome open, CDP might attach to wrong window.

**Fix:** Add process ID tracking

```python
# In browser_controller.py
def _launch_chrome(self) -> bool:
    # ... existing code ...
    
    proc = subprocess.Popen(args, ...)
    self.chrome_pid = proc.pid  # Track it
    
    # Later, to close ONLY hndl-it Chrome:
    # os.kill(self.chrome_pid, signal.SIGTERM)
```

### 3. Percentage-Based Positioning (from TODO.md)

In `floater/overlay.py`:

```python
# BEFORE (pixel-based):
self.move(50, 170)

# AFTER (percentage-based):
screen = QApplication.primaryScreen().geometry()
x = int(screen.width() * 0.03)  # 3% from left
y = int(screen.height() * 0.16) # 16% from top
self.move(x, y)
```

---

## Questions for Clarification

1. **Parser priority:** Should LLM parsing be opt-in (user enables in settings) or automatic fallback?

2. **Voice scope:** Global hotkey everywhere, or only when hndl-it window is focused?

3. **Y-IT integration timing:** Build as hndl-it module, or separate repo that imports hndl-it?

4. **Moondream concurrent:** Currently vision agent loads LLaVA-Llama3 (crashes per your note). Should I provide Moondream-specific integration code?

---

## Marching Orders (Prioritized)

| Priority | Task | Time Est |
|----------|------|----------|
| **1** | Create `shared/orchestrator.py` skeleton | 2 hours |
| **2** | Wire floater → orchestrator → browser agent | 3 hours |
| **3** | Test end-to-end: "go to reddit" works | 1 hour |
| **4** | Add Ollama call to parser.py as fallback | 2 hours |
| **5** | Create `y-it/pipeline.py` with first scrape target | 4 hours |
| **6** | Progress ring on icons | 2 hours |
| **7** | Voice input module (whisper.cpp) | 4 hours |
| **8** | todo-it module | 4 hours |

**Total to MVP:** ~22 hours focused work = ~1 week at 25-min sprints

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                                │
│            (keyboard / voice / clipboard)                    │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  FLOATER UI                                  │
│              (PyQt6 overlay)                                 │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   PARSER                                     │
│         (regex first → LLM fallback)                        │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               ORCHESTRATOR  ◄──────────────────────────────┐│
│    (routes commands, manages state, handles errors)        ││
└──────┬──────────────┬──────────────┬──────────────────────┘│
       ▼              ▼              ▼                        │
┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│ BROWSER  │   │ DESKTOP  │   │  VISION  │                   │
│  AGENT   │   │  AGENT   │   │  AGENT   │                   │
│ (CDP)    │   │ (PyAuto) │   │(Moondream)│                   │
└────┬─────┘   └────┬─────┘   └────┬─────┘                   │
     │              │              │                          │
     └──────────────┴──────────────┴──────────────────────────┘
                           ▼
              ┌─────────────────────┐
              │   LOCAL LLM BRAIN   │
              │  (Qwen2.5:7b via    │
              │      Ollama)        │
              └─────────────────────┘
```

---

## Bottom Line

The scaffolding is solid. Now connect the pieces. Don't add more modules until Browser → Desktop → Vision chain works end-to-end through the orchestrator.

---

*Generated by Claude Opus 4.5 via claude.ai*
*For: hndl-it project by hagermann00*