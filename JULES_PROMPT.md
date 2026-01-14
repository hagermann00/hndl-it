<instruction>You are an expert software engineer. You are working on a WIP branch. Please run `git status` and `git diff` to understand the changes and the current state of the code. Analyze the workspace context and complete the mission brief.</instruction>
<workspace_context>
<artifacts>
--- CURRENT TASK CHECKLIST ---

# Hndl-it Consolidation Tasks

- [x] Analyze current directory structure and file contents <!-- id: 0 -->
- [x] Verify `floater/client.py` and UI implementation <!-- id: 1 -->
- [x] Verify `agents/browser` implementation <!-- id: 2 -->
- [x] Verify `agents/desktop` and `agents/vision` implementation <!-- id: 3 -->
- [x] Create or update `run.py` orchestration script <!-- id: 4 -->
- [x] Unify dependency management (`requirements.txt`) <!-- id: 5 -->
- [x] Verify communication protocols (WebSockets) <!-- id: 6 -->
- [x] Test end-to-end flow <!-- id: 7 -->
- [x] Fix Floater UI off-screen positioning bug <!-- id: 8 -->
- [x] Implement auto-launch for Chrome in Browser Agent <!-- id: 9 -->
- [x] Fix Floater UI visibility (force show on startup) <!-- id: 10 -->
- [x] Re-skin UI and make persistent (minimize to tray) <!-- id: 11 -->
- [x] Create silent startup script (`start_silent.vbs`) <!-- id: 12 -->
- [x] Implement Floating Overlay Widget (Draggable "Dock") <!-- id: 13 -->
- [x] Create Desktop Shortcut (`create_shortcut.ps1`) <!-- id: 14 -->
- [x] Update Icon to user-provided Hand Logo (Circular Clip) <!-- id: 15 -->
- [x] Create `ConfigManager` for persistent settings <!-- id: 16 -->
- [x] Implement `SettingsDialog` (Ollama Model Selection & API URL) <!-- id: 17 -->
- [x] Implement "Memory Cache" (Saved Workflows) Manager in UI <!-- id: 18 -->
- [x] Integrate Task Execution in `Tray` (Route task names to command sequences) <!-- id: 19 -->

--- IMPLEMENTATION PLAN ---

# Hndl-it Overlay & Routing Plan

## Goal Description

Transform the interaction model from "Tray-only" to a "Floating Overlay Widget" (Draggable Icon) that stays on top of other windows.

1. **Overlay Widget**: A permanent, draggable circle/icon on screen.
    - **Click**: Toggles the Quick Input Dialog.
    - **Double Click**: Opens the Full Console (Log Viewer).
    - **Drag**: Moves the icon.
2. **Routing**: Verify and ensure natural language commands route efficiently to Browser vs. Desktop agents.
3. **Desktop Shortcut**: Create a convenient launcher on the User's Desktop.

## User Review Required
>
> [!NOTE]
> The System Tray icon will remain as a fallback for "Exit", but the primary interaction will be the new on-screen Floating Button.

## Proposed Changes

### UI Components

#### [NEW] [floater/overlay.py](file:///C:/IIWII_DB/hndl-it/floater/overlay.py)

- **Class**: `OverlayWidget` (PyQt6).
- **Style**: Circular/Rounded, high-tech "Dock" aesthetic (Dark/Blue accent). Always on top.
- **Events**:
  - `mousePress/Move/Release`: Handle dragging.
  - `mouseRelease` (if not dragged): Signal click.
  - `mouseDoubleClick`: Signal double-click.

#### [MODIFY] [floater/main.py](file:///C:/IIWII_DB/hndl-it/floater/main.py)

- Instantiate `OverlayWidget`.
- Connect Overlay signals to `QuickDialog` (toggle) and a new `ConsoleWindow` (show).

#### [MODIFY] [floater/quick_dialog.py](file:///C:/IIWII_DB/hndl-it/floater/quick_dialog.py)

- Ensure it positions itself relative to the *Overlay Widget* instead of the cursor/tray when toggled.

### Command Routing

#### [MODIFY] [floater/parser.py](file:///C:/IIWII_DB/hndl-it/floater/parser.py)

- Enhance `CommandParser` to better detect "file/desktop" intent vs "browser" intent.
- Ensure "open [path]" routes to Desktop if it looks like a file path, or Browser if it takes a URL.

### Deployment

#### [NEW] [create_shortcut.ps1](file:///C:/IIWII_DB/hndl-it/create_shortcut.ps1)

- PowerShell script to create a `.lnk` on the Desktop pointing to `start_silent.vbs` with the correct icon.

## Verification Plan

### Manual Verification

1. Run `create_shortcut.ps1`.
2. Launch via the new Desktop Shortcut.
3. **Verify Overlay**: A widget appears on screen.
4. **Verify Drag**: Click and drag the widget around.
5. **Verify Click**: Single click opens the Input Dialog next to the widget.
6. **Verify Routing**:
    - Type `list .` -> Check Desktop Agent logs.
    - Type `open google.com` -> Check Browser Agent logs.
</artifacts>

</workspace_context>
<mission_brief>[I need a cpom[lp;ete trighten or bnreaking uip or restructuireion or somethign tha trewiall make this not fucntionlike shit]]</mission_brief>
