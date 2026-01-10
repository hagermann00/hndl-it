from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

# --- Commands (Floater -> Agent) ---

class BaseCommand(BaseModel):
    id: str = Field(..., description="Unique ID for the command request")
    action: str = Field(..., description="Action type")

class NavigateCommand(BaseCommand):
    action: Literal["navigate"]
    url: str = Field(..., description="Target URL to visit")

class ScrapeCommand(BaseCommand):
    action: Literal["scrape"]
    selector: Optional[str] = Field(None, description="CSS selector to scrape. If None, scrapes full page text.")

class ClickCommand(BaseCommand):
    action: Literal["click"]
    selector: str = Field(..., description="CSS selector to click")

class ExecuteScriptCommand(BaseCommand):
    action: Literal["execute_script"]
    script: str = Field(..., description="JavaScript code to execute")

# Union type for parsing
BrowserCommand = NavigateCommand | ScrapeCommand | ClickCommand | ExecuteScriptCommand


# --- Files Commands (Floater -> Desktop Agent) ---

class OpenCommand(BaseCommand):
    action: Literal["open"]
    path: str = Field(..., description="Path to file or folder to open")

class ListDirCommand(BaseCommand):
    action: Literal["list_dir"]
    path: str = Field(..., description="Directory path")

class FileCommand(BaseCommand):
    # Generic container or Union
    pass

# --- Vision Commands (Floater -> Vision Agent) ---

class AnalyzeCommand(BaseCommand):
    action: Literal["analyze"]
    prompt: str = Field(..., description="Prompt for the vision model")

# Union type for parsing



# --- Events (Agent -> Floater) ---

class BaseEvent(BaseModel):
    command_id: Optional[str] = Field(None, description="ID of the command this event relates to")
    type: str = Field(..., description="Event type")
    timestamp: float = Field(..., description="Unix timestamp of the event")

class StatusEvent(BaseEvent):
    type: Literal["status"]
    status: Literal["idle", "working", "error", "starting"]
    message: Optional[str] = None

class LogEvent(BaseEvent):
    type: Literal["log"]
    level: Literal["info", "warning", "error", "debug"]
    message: str

class ResultEvent(BaseEvent):
    type: Literal["result"]
    data: Dict[str, Any] = Field(..., description="Result data (e.g., scraped text)")

class ErrorEvent(BaseEvent):
    type: Literal["error"]
    error_message: str

# Union type for parsing
BrowserEvent = StatusEvent | LogEvent | ResultEvent | ErrorEvent
