# Voice Input Architecture for hndl-it Ecosystem

## Hotkey Layout

| Hotkey | Function | Destination |
|--------|----------|-------------|
| **Win+H** | Windows native dictation | System (keep as-is) |
| **Ctrl+Shift+H** | hndl-it voice input | Routes to hndl-it router |
| **Ctrl+Shift+R** | read-it voice command | "Read this", "Summarize" |
| **Ctrl+Shift+T** | todo-it voice input | "Remember", "Todo", "Remind me" |

---

## Voice Router Flow

```
[Microphone] 
     ↓
[Global Hotkey Listener] (Ctrl+Shift+H)
     ↓
[Speech Recognition] (local, no cloud)
     ↓
[hndl-it Voice Router]
     ↓
┌────────────────────────────────────────┐
│  Intent Classification (keyword-based) │
│                                        │
│  "read" / "summarize" → read-it        │
│  "todo" / "remember" → todo-it         │
│  "open" / "go to" → browser-agent      │
│  "file" / "folder" → desktop-agent     │
│  else → show in hndl-it input          │
└────────────────────────────────────────┘
```

---

## Button Input Layout (Right Column)

All floating icons get a **mic button** on right side:

```
┌──────────────────────────────────┐
│  [H icon] ────────── [🎤]       │  hndl-it
│                                  │
│  [📖 icon] ─────────── [🎤]     │  read-it  
│                                  │
│  [📝 icon] ─────────── [🎤]     │  todo-it (new)
└──────────────────────────────────┘
```

OR: Single mic icon on mounting bar that routes intelligently.

---

## Implementation Steps

### Phase 1: Global Hotkey + Speech Recognition

1. [ ] Install `keyboard` library for global hotkeys
2. [ ] Install `SpeechRecognition` + `pyaudio` for mic input
3. [ ] Create `shared/voice_input.py` module
4. [ ] Hotkey triggers listening → transcribes → routes to hndl-it

### Phase 2: Visual Feedback

1. [ ] Pulsing ring on icon when listening
2. [ ] Text appears in input field as transcribed
3. [ ] Auto-submit after 2 sec silence

### Phase 3: Intent Router

1. [ ] Keyword-based routing (no LLM needed initially)
2. [ ] "read", "summarize" → read-it
3. [ ] "todo", "remember", "remind" → todo-it
4. [ ] "open", "go to", "navigate" → browser-agent

### Phase 4: todo-it Module

1. [ ] New floating icon (📝)
2. [ ] Voice input → creates TODO item
3. [ ] List view with checkboxes
4. [ ] Persists to local file/database

---

## Libraries Needed

```bash
pip install SpeechRecognition pyaudio keyboard
```

---

## Files to Create/Modify

| File | Purpose |
|------|---------|
| `shared/voice_input.py` | Global hotkey + speech recognition |
| `floater/main.py` | Register global hotkey |
| `floater/overlay.py` | Pulsing ring animation |
| `todo-it/main.py` | New todo module |
| `shared/voice_router.py` | Intent classification |

---

*Created: 2026-01-10*
