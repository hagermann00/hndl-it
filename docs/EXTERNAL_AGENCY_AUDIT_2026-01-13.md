# External Agency & Extension Audit (2026-01-13)

**Usage:** Use this document to review and annotate the external connections in your ecosystem.
**Action:** Add your directives in the **"USER NOTES / ACTION"** column (e.g., *Approve*, *Disable*, *Investigate*, *Switch Profile*).

---

## 1. Hndl-it Agents & MCP Connections

| Resource ID | Connection Type | Identity Used | Access Scope (Us → Them) | Data Exposure (Them → Us) | Risk Level | USER NOTES / ACTION |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hndl-it Browser Agent** | CDP (Remote Debug) | **ISOLATED Profile** (`chrome_profile`) | Current Window Only | Screen Pixels & DOM | **SAFE** | |
| **Claude Web MCP** | Playwright | **🔴 MAIN Personal Profile** | Full History & Settings | Everything in Main Chrome | **HIGH** | |
| **NotebookLM MCP** | CDP | **ISOLATED Profile** | Specific Notebooks | Notebook Content | **SAFE** | |
| **Brain Agent** | Local API | **Local** (Qwen) | Prompt Text Only | None (Offline) | **SAFE** | |
| **Claude Code CLI** | API / Terminal | **Local Token** (`brihag8`) | Current Project Context | Code Edits & Terminal | **MODERATE** | |
| **Gemini CLI** | API | **Unknown / Pending** | Unknown | Unknown | **PENDING** | |
| **Database MCP** | Local File | **Local** (SQLite) | Structured Data | Query Results | **SAFE** | |

---

## 2. VS Code Extensions (External Context)

| Extension ID | Name | Connects To | Context Access | Risk Level | USER NOTES / ACTION |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **anthropic.claude-code** | Claude Code | **Anthropic API** | Deep Project Context | **HIGH (Auth)** | |
| **github.copilot** | GitHub Copilot | **Microsoft / OpenAI** | Real-Time Cursor & Files | **HIGH (Auth)** | |
| **github.copilot-chat** | Copilot Chat | **Microsoft / OpenAI** | Chat & Selection | **HIGH (Auth)** | |
| **ritwickdey.liveserver** | Live Server | **Localhost Only** | Files Served | **LOW** | |
| **tomoki1207.pdf** | PDF Viewer | **None (Local Viewer)** | PDF Content | **LOW** | |

---

## 3. General Notes & Directives

*Space for broader notes on policy (e.g., "Never allow main profile access without Red Override").*

-
-
-
