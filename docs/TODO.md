# hndl-it & read-it TODO List

## Session: 2026-01-10

---

## 🚀 NEXT MODULE: todo-it

**The next icon** - A TODO input/interface that needs future-proofing:

- [x] **todo-it module** - Standalone TODO input + management (main.py done)
- [x] **Speech input** that connects to both todo-it AND hndl-it (shared/voice_input.py + voice_router.py)
- [ ] **Voice input button** for all qualifying modules THAT IT MAKES SENSE FOR
- [ ] ALL MODULES NEED GFUTIURE PRROFFNG FOR TWO AS END THINGS DATAA OUTPUT DOCKING AMND I THINKG VISUALL Y TO OPITOONALLY EKEP EM INTERLLCIOKED AND LOFITICLY STANBLER
- [ ] Future-proof interface design

---

## 🔴 HIGH PRIORITY

### Orchestrator & Agent Verification (2026-01-10)

- [x] **Todo-it persistence** - Save tasks to disk, reload on startup ✅ Already implemented!
- [x] **Verify floater input is connected to agents** - Route commands through Orchestrator ✅ v5.2
- [ ] **Test multi-step command execution** - Simple but chained operations
- [x] **Clean shutdown** - Supervisor kills entire process tree with psutil ✅ v5.1

### Headless Execution

- [ ] **read-it and hndl-it should NOT open terminal windows** ALL SHOURLRF BUT I GET IT DIURIGNM DEVELOPMENT
- [ ] Use pythonw or subprocess flags to run completely headless
- [ ] Closing terminal should NOT kill the app

### UI Overhaul - Progress Ring Standard

- [ ] **Bright blue ring around icons** - Acts as progress bar (animated during execution)
- [ ] **Both read-it and hndl-it** should have this ring

### read-it Enhancements

- [ ] **Control buttons overlayed on icon** during playback (not a separate overlay widget)
- [ ] **Standard execution field on top** with 3-4 buttons
- [ ] **TTS Pause/Resume not working properly** - needs fix
- [ ] **Paste function** - verify it works

### hndl-it UI Redesign  

- [ ] ** MIUNI MIJNIMAL VISUAL OPTION JUS BARE INPUT BASICALLYE EXTREDN OUT FREOIEMN THE ICON ON LEFT SOIDE IT JSURT RETARACT ON ESC OR ENTR - no close or title bar
- [ ] **Type and enter** OR **Speak and enter(EXTEND SILEBNCE)**
- [ ] **Verbal input button** on all qualifying modules FROM A  SINGULR ICONM IN LINE ON TH RIGHT COLUM OR ON TEH MOUNTING BAR  THEOREHTICALL

### 🎤 Voice Input System (NEXT UP)

- [x] **Speech-to-text for hndl-it** - Direct audio input to router (voice_input.py)
- [x] **Custom hotkey** Win+Alt routes to hndl-it voice input
- [x] **Keep Windows Win+H** for native dictation (Win+Alt used instead)
- [ ] **Extended silence detection** = end of input, auto-submit
- [ ] **Visual indicator** when listening (pulsing ring?)
- [ ] **Works globally** - any app, routes to hndl-it

### Cross-Module Standard

---

## 🟡 MEDIUM PRIORITY

### read-it

- [ ] **Summary uses local LLM** instead of first 200 chars  (???????? )
- [ ] **Back button** - go back actual 10 seconds (not just 2 sentences)
- [ ] **Speed dropdown** - verify it changes TTS rate properly

### Browser Agent

- [x] Multi-tab support added
- [x] Hardened Chrome (dark mode, isolated profile)
- [x] MORE DELIBERATE ACTION/STREPS TO CLOSE BECASUE APPARENTLY ITS CAN ONLY IUSER TAT ONE
- [ ] Test multi-tab execution
- [ ]   FTURE WORK LOCATIONS NEED TO NOT BE INPIXELS MUST BE PERCENTAGE OD PIXXELS I BELEEED WEIUTH IN CRRAS IN ASOZE WSITH SCREEM  
- [ ]

---

## 🟢 COMPLETED TODAY

- [x] read-it icon using iiwii book image
- [x] Icon positions finalized (hndl-it Y=170, read-it Y=300)
- [x] Clipboard popup pill (Play + Summary buttons)
- [x] Selection monitor - triggers on HIGHLIGHT not copy
- [x] Playback overlay with controls (pause, back, speed)
- [x] Summary auto-plays TTS
- [x] Panel stays compact, text scrollable
- [x] Right-click menu with Restart/Quit
- [x] Restart button fixed with absolute path
- [x] hndl-it popup lowered 200px
- [x] Browser agent multi-tab + hardened Chrome
- [ ] y-it inter conmnection and exeuviton game plan analusis
- [ ] to do 9input and liwsting

## 💡 NOTES

- Current screen: 1920x1080
- read-it at Y=300, hndl-it at Y=170
- Use `pythonw` for headless execution
- pyautogui + pyperclip for selection monitoring
