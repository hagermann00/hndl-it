# Grok Suggestions for hndl-it

## Date: 2026-01-10

### Priority 1: Local LLM Integration

For the RTX 2060 12GB VRAM constraint while running concurrently with Moondream (~1.7GB), the strongest local brain model in early 2026 is **Qwen3-14B-Instruct** at Q5_K_M quantization (or Q4_K_M if VRAM is tight). It dominates agentic benchmarks for structured JSON output, reliable tool/function calling, intent classification, multi-step reasoning, and context management across modules.

Key strengths for hndl-it:

- Excellent intent parsing from floater natural language commands
- Robust summary generation for read-it document processing
- Strong context tracking for multi-turn interactions across browser/desktop agents
- Native tool-calling support simplifies routing to specialized agents

Performance: ~18-28 tokens/second on your hardware — responsive enough for real-time command routing. Run brain and Moondream on separate Ollama instances (different ports) for true concurrency.

For CPU-only fallback (to support broader consumer hardware), use **Qwen3-8B-Instruct** or **Phi-4 Mini** — slower but fully offline-capable.

**Implementation tip**: Use strict JSON schemas in prompts with ReAct-style reasoning chains. Validate outputs before routing to agents.

### Priority 2: Architecture

Go with a **hybrid local-first architecture with automatic cloud escalation** to maximize offline privacy while enabling mass-market reach on non-GPU machines.

- **Core pattern**: Single central brain (local Ollama) receives commands from floater, classifies intent, and routes structured JSON commands to modular agents via a lightweight shared queue (e.g., multiprocessing Queue or Redis if scaling).
- **Data flow**: Floater → brain (intent + context) → agent execution → observation → brain (next step or completion) → floater feedback.
- **Future-proofing**: Abstract agent interfaces with a base class (execute, observe, reset). Use config-driven module registration so todo-it and y-it can plug in seamlessly.
- **Escalation**: Auto-detect GPU → local brain; else prompt for user API key (prefer Grok API for agentic strength and vision; fallbacks: Claude 4, GPT-4o-mini). Client handles all actions locally — cloud only gets reasoning prompts and screenshots when needed.

This keeps the system zero-server for launch while scaling effortlessly.

### Priority 3: UI/UX

Focus on subtle, professional floating icons that feel native and non-intrusive.

- **Progress ring**: Animated circular progress around icons using PyQt6 QProgressBar with custom styling.
- **Control overlays**: Semi-transparent close/minimize/settings buttons on hover.
- **Minimal input bar**: Optional always-visible slim bar at screen bottom (toggle via hotkey), with command history and autocomplete.
- **Responsive positioning**: Store positions as screen percentage (via QScreen.availableGeometry()) for multi-monitor and resolution resilience.

**Code Snippet** (animated progress ring):

```python
from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtGui import QConicalGradient, QPalette, QColor
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve

def create_animated_progress_ring(parent, size=60):
    progress = QProgressBar(parent)
    progress.setRange(0, 100)
    progress.setValue(0)
    progress.setTextVisible(False)
    progress.setFixedSize(size, size)
    
    # Conical gradient for ring effect
    gradient = QConicalGradient(size/2, size/2, 90)
    gradient.setColorAt(0.0, QColor("#00ff88"))
    gradient.setColorAt(0.5, QColor("#0088ff"))
    gradient.setColorAt(1.0, QColor("#00ff88"))
    
    palette = progress.palette()
    palette.setBrush(QPalette.ColorRole.Highlight, Qt.BrushStyle.Dense4Pattern)  # Will style via CSS
    progress.setPalette(palette)
    
    progress.setStyleSheet("""
        QProgressBar {
            background: transparent;
            border: 3px solid #333333;
            border-radius: %dpx;
            text-align: center;
        }
        QProgressBar::chunk {
            background: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:0 #00ff88, stop:1 #0088ff);
            border-radius: %dpx;
        }
    """ % (size//2, size//2))
    
    # Animation
    anim = QPropertyAnimation(progress, b"value")
    anim.setDuration(1000)
    anim.setStartValue(0)
    anim.setEndValue(100)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    anim.setLoopCount(-1)
    anim.start()
    
    return progress
```

### Priority 4: Voice Integration

Use **Vosk** for lightweight, fully offline STT — excellent accuracy on Windows, small footprint, and real-time streaming.

- Route via keyword triggers ("hndl-it", "read-it", "todo-it", "remember") to activate listening.
- Extended silence detection (adjustable 1-2 seconds) to end input automatically.
- Pipe transcribed text directly to floater/brain for intent processing.

Alternative: whisper.cpp (GGUF) for higher accuracy if CPU can handle it.

For cloud boost: Optional escalation to Grok voice mode or Whisper API when local fails.

### Priority 5: Monetization Path

To hit $1,500/mo survival quickly, launch a **hybrid freemium model**:

- **Local Pro** ($49 one-time or $12/mo): Full offline capability for GPU users — target privacy-focused pros (freelancers, traders, researchers) via Reddit, X, and indie forums.
- **Cloud Lite** ($9/mo): User-provided API keys for non-GPU users — seamless escalation, broader reach.
- **Y-IT Premium** ($19/mo add-on): Automated satirical content pipeline (script gen → editing → posting) as high-value upsell for creators.
- Distribution: Gumroad/itch.io for fast one-time sales; later Stripe subscription with serverless proxy.

Launch paid local beta within days — existing GPU owners are ready to buy polished local agents now.

### Questions for the User

1. What specific steps in the y-it satirical content pipeline need the most automation priority (e.g., idea generation, script writing, video assembly, posting)?
2. Any preference for STT library (Vosk vs whisper.cpp) or constraints on binary dependencies?
3. For cloud escalation, which providers should be supported first (Grok API priority, or others like Claude/OpenAI)?
