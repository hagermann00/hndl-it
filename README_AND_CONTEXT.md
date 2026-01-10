# Hndl-it: Local-First Agentic Workspace

> *Say it, and consider it handled.*

**Hndl-it** is a consolidated, local-first agent orchestration system for Windows. It decouples the "Brain" (Floater UI) from the "Hands" (Specialized Agents), allowing for robust, low-latency control of your digital environment.

## 🚀 Current Capabilities

### 1. The Interface

- **The Dock (Overlay)**: A always-on-top, draggable circular widget.
  - **Click**: Opens the dark-themed Command Input.
  - **Double-Click**: Opens the Status Console.
  - **Drag**: Move it anywhere; it remembers its place.
- **System Tray**:
  - Right-click for **Settings**, **Console**, or **Exit**.
  - Persistent background operation (minimizing Input window hides it to tray).
- **Settings UI**:
  - Configure your Local LLM (Ollama) URL and Model.
  - Manage **"Memory"**: Create, Edit, and Delete multi-step workflows (Saved Tasks).

### 2. The Agents

- **Browser Agent** (`Port 8766`):
  - Pure CDP (Chrome DevTools Protocol) control.
  - Auto-launches Chrome with remote debugging if needed.
  - **Commands**: `open <url>`, `click <selector>`, `scrape`, `scroll`.
- **Desktop Agent** (`Port 8767`):
  - Fast file system operations.
  - **Commands**: `list <path>`, `open <file>`.

### 3. The "Memory"

- Define tasks like "Daily Login" or "Check Server".
- Execute them instantly by typing their name in the Input box.

---

## 🛠️ Setup & Usage

### First Run

1. **Install Dependencies**: `pip install -r requirements.txt` (if not done).
2. **Create Shortcut**: Run `powershell .\create_shortcut.ps1`.
3. **Launch**: Double-click **Hndl-it** on your Desktop.

### Configuration

1. Right-click the **Tray Icon** -> **Settings**.
2. **General Tab**:
    - Enter your Ollama URL (e.g., `http://localhost:11434`).
    - Click **Refresh Models** and select your preferred model (e.g., `llama3`).
3. **Memory Tab**:
    - Create new workflows. Example:
        - **Name**: `Search YouTube`
        - **Commands**:

            ```
            open youtube.com
            click #search-input
            ```

---

## 🔮 Future Possibilities & Recommendations (The Roadmap)

### 1. "True" Agentic Parsing

* **Current State**: The `parser.py` uses Regex heuristics (deterministic/safe).
- **Future**: Connect the `parser.py` to the **Ollama Model** configured in Settings.
  - *Prompt*: "Translate user request '{input}' into JSON command format."
  - *Benefit*: Handle complex requests like "Find the latest PDF in downloads and open it."

### 2. Vision Agent Integration

* **Current State**: `agents/vision` is a scaffold listening on Port 8768.
- **Future**: Implement a Snapshot loop.
  - Allow the user to say "Click the red checkout button" (where no selector exists).
  - Send screenshots to `llava` or `moondream` via Ollama for coordinate extraction.

### 3. Voice Command "Whisperer"

* **Recommendation**: Add a global hotkey (e.g., `Ctrl+Space`) to record audio.
- **Pipeline**: Audio -> Local Whisper -> Text -> Hndl-it Input.
- *Result*: Zero-friction voice control of your PC.

### 4. Semantic Memory / RAG

* **Current State**: "Memory" is a static list of explicit commands.
- **Future**: Store execution logs and "Successful" patterns in a vector database (e.g., using `chromadb`).
- *Benefit*: The agent "remembers" how it solved a problem last week without you manually saving a task.

### 5. Multi-Bodal "Hands"

* **Recommendation**: Expand Desktop Agent to handle OS-level UI automation (via `pywinauto` or `uiautomation`) for controlling non-web apps like Spotify, VS Code, or Explorer windows beyond simple file listing.

---

## 📝 Developer Context

- **Architecture**: `Floater` (PyQt6 Client) <-> `WebSockets` <-> `Agents` (Servers).
- **Communication**: Pydantic models in `shared/messages.py`.
- **Logs**: `floater/console.py` receives filtered logs from `GuiLogHandler`.
- **Config**: `settings.json` is managed by `floater/config.py`.

*Consider it handled.*
