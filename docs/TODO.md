# hndl-it & read-it TODO List

## Session: 2026-01-10

---

## 🔴 HIGH PRIORITY

### UI Overhaul - Progress Ring Standard

- [ ] **Bright blue ring around icons** - Acts as progress bar (animated during execution)
- [ ] **Both read-it and hndl-it** should have this ring

### read-it Enhancements

- [ ] **Control buttons overlayed on icon** during playback (not a separate overlay widget)
- [ ] **Standard execution field on top** with 3-4 buttons
- [ ] **TTS Pause/Resume not working properly** - needs fix
- [ ] **Paste function** - verify it works

### hndl-it UI Redesign  

- [ ] **All input box** - no close or title bar
- [ ] **Type and enter** OR **Speak and enter**
- [ ] **Verbal input button** on all qualifying modules

### Cross-Module Standard

- [ ] **Voice input button** on all modules that support it (prep for next module)

---

## 🟡 MEDIUM PRIORITY

### read-it

- [ ] **Summary uses local LLM** instead of first 200 chars
- [ ] **Back button** - go back actual 10 seconds (not just 2 sentences)
- [ ] **Speed dropdown** - verify it changes TTS rate properly

### Browser Agent

- [x] Multi-tab support added
- [x] Hardened Chrome (dark mode, isolated profile)
- [ ] Test multi-tab execution

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

---

## 💡 NOTES

- Current screen: 1920x1080
- read-it at Y=300, hndl-it at Y=170
- Use `pythonw` for headless execution
- pyautogui + pyperclip for selection monitoring
