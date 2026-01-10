Here is the suggestion file for the **hndl-it** repository, formatted as requested.

```markdown
docs/suggestions/gemini.md

```

---

# Gemini Suggestions for hndl-it

## Date: 2026-01-10

### Priority 1: Architecture - The "Hub & Spoke" Event Bus

To manage the floating modules without creating a tangled dependency web (e.g., `read-it` crashing `hndl-it`), I recommend a strictly decoupled **Event Bus architecture**.

**The Strategy:**
Treat `hndl-it` (the main router) as the "Hub" and all other agents (`read-it`, `browser`, `todo-it`) as "Spokes".

* **Tech Stack:** Use **ZeroMQ (ZMQ)** (PUB/SUB pattern) or a local **FastAPI + WebSocket** server. ZMQ is preferred for low latency in a local-first environment.
* **Data Flow:** `Voice/Input` -> `Router (LLM Intent)` -> `Publish Event (e.g., "cmd.browser.search")` -> `Subscriber (Browser Agent)` handles it.
* **Benefit:** This allows you to restart individual modules (like the heavy Browser Agent) without killing the main voice listener.

### Priority 2: Local LLM Strategy (12GB VRAM Optimization)

With an RTX 2060 (12GB) and an i7-8700, you are in the "Goldilocks" zone for high-performance 8B models, but you must balance VRAM against the Context Window and Vision model.

**The Recommendation:**

* **Model:** **Llama-3.1-8B-Instruct** (Quantized to **Q6_K** or **Q8_0** via Ollama).
* *Why:* The 8B size at Q6 fits in ~6.5GB VRAM. This leaves ~5.5GB for the KV Cache (context), `Moondream` (Vision), and Windows display overhead.

* **Context Management:** Implement a **"Rolling Summary"** buffer. Do not feed the entire history. Keep the last 10 turns raw, and compress older interactions into a system prompt update ("User is currently working on X").
* **Vision Fallback:** If `Moondream` + `Llama` causes OOM, unload `Moondream` immediately after inference. Do not keep it loaded.

### Priority 3: Voice Integration - "Semantic" Silence Detection

Standard VAD (Voice Activity Detection) often cuts users off while they are thinking.

**The Strategy:**

1. **VAD:** Use **Silero VAD** for low-latency initial detection.
2. **Semantic Buffer:** When silence > 1.0s is detected, do not cut immediately. Run a quick check on the transcripts:

* *Does the sentence end in a conjunction (and, but, so)?* -> **Keep Listening.**
* *Is the intent incomplete?* -> **Keep Listening.**

1. **Wake Word:** Offload `openWakeWord` to the **CPU** (i7-8700) to save GPU VRAM for the LLM.

### Priority 4: UI/UX - PySide6 Radial Overlays

For Windows-native "shaped" windows (floating icons), **PySide6 (Qt)** is superior to Tkinter for handling transparency and anti-aliasing.

**The Design:**

* **Progress Ring:** Use a `QPainter` overlay to draw an arc around the icon.
* *Blue Pulse:* Listening.
* *Gold Spin:* Processing.
* *Green Flash:* Done.

* **Control Overlay:** Implement a **Radial Menu** (Pie Menu) that fades in *around* the icon on hover. It is faster for mouse movement than a list.

### Priority 5: Monetization - The Y-IT "Content Factory"

To hit $1,500/mo, `y-it` needs to move from a "helper" to a "producer."

**The Strategy:**

* **Trend Arbitrage:** Automate the pipeline.

1. **Input:** Browser Agent scrapes trending Tech/AI news (Hacker News/X).
2. **Persona:** LLM rewrites it as a "Cynical Sysadmin" or "Hype-allergic Dev."
3. **Production:** Generate a static reaction image (using Vision/PIL) + TTS.
4. **Output:** 5-10 YouTube Shorts/TikToks per day.

* *Note:* Satire protects you from hallucination risks—accuracy isn't the goal, humor is.

### Code Snippets

**Architecture: Simple ZMQ Publisher (The Router)**

```python
import zmq
import json

def start_router():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    
    print("Router started. Waiting for commands...")
    
    # Mock dispatch function
    def dispatch(intent, payload):
        # Topic: "module.action" -> e.g., "todo.add"
        topic = f"{intent['module']}.{intent['action']}"
        message = json.dumps({'topic': topic, 'data': payload})
        socket.send_string(f"{topic} {message}")
        print(f"Dispatched: {topic}")

    return dispatch

```

**UI: PySide6 Circular Progress Ring (Concept)**

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0  # 0 to 100
        # Pass clicks through to the icon underneath
        self.setAttribute(Qt.WA_TransparentForMouseEvents) 
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Ring
        pen = QPen(QColor("#00FF00")) # Neon Green
        pen.setWidth(4)
        painter.setPen(pen)
        
        # Calculate arc (16 steps per degree)
        span_angle = int(-360 * 16 * (self.progress / 100))
        rect = QRectF(2, 2, self.width()-4, self.height()-4)
        painter.drawArc(rect, 90 * 16, span_angle)

```

### Questions for the User

1. **VRAM Budget:** Do you plan to keep the `Browser Agent` (Chrome) open constantly? Chrome eats system RAM, but GPU acceleration might steal VRAM. Have you disabled hardware acceleration in your browser automation profile?
2. **Voice Trigger:** Do you prefer a "Push-to-Talk" global hotkey (easier to code, zero false positives) or "Always Listening" (requires `openWakeWord` running constantly)?
3. **Y-IT Tone:** Is the satirical content meant to be educational (explaining tech via humor) or purely entertainment? This dictates whether we need FFmpeg automation or just Browser automation.
