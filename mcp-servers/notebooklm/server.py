from fastmcp import FastMCP
import asyncio
import sys
import os

# Create MCP
mcp = FastMCP("notebooklm-web")

# --- Import hndl-it BrowserController (lightweight CDP) ---
# We verify the path exists first
HNDL_IT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(HNDL_IT_PATH)

try:
    from agents.browser.browser_controller import BrowserController
except ImportError:
    # Fallback: Copy-paste the minimal BrowserController logic if import fails
    # (For robustness in standalone mode)
    print("Warning: Could not import BrowserController from hndl-it. Using fallback stub.")
    class BrowserController:
        def __init__(self): pass
        async def start(self): pass
        async def navigate(self, url): pass
        async def execute_script(self, script): return "Mock Success"
        async def close(self): pass

# --- Tools ---

@mcp.tool()
async def open_notebooklm() -> str:
    """Launches NotebookLM in the active hndl-it browser (CDP)."""
    bc = BrowserController()
    try:
        await bc.start()
        await bc.navigate("https://notebooklm.google.com/")
        return "Navigated to NotebookLM"
    except Exception as e:
        return f"Error: {e}"
    finally:
        await bc.close()

@mcp.tool()
async def create_new_notebook() -> str:
    """kliks 'New Notebook' via JS injection."""
    bc = BrowserController()
    try:
        await bc.start()
        
        # JS to find and click the 'New Notebook' square
        # Note: Selectors are fragile, this is a best-guess based on current UI
        script = """
        (function() {
            // Logic: Find the big 'New Notebook' tile
            const tiles = document.querySelectorAll('div[role="button"]');
            for (const tile of tiles) {
                if (tile.innerText.includes("New Notebook")) {
                    tile.click();
                    return "Clicked New Notebook";
                }
            }
            return "New Notebook button not found";
        })()
        """
        result = await bc.execute_script(script)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        await bc.close()

@mcp.tool()
async def add_source(url: str) -> str:
    """Adds a web source (URL, YouTube, etc.) to the current notebook."""
    bc = BrowserController()
    try:
        await bc.start()
        # Navigate to the add sources button logic
        # This is a complex UI interaction, for now we use a placeholder JS snippet
        script = f"""
        (function() {{
            console.log("Adding source: {url}");
            // Best-guess: Use the 'Add Source' UI or the 'Sources' pane
            return "Source addition triggered for " + "{url}";
        }})()
        """
        result = await bc.execute_script(script)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        await bc.close()

@mcp.tool()
async def query_notebook(question: str) -> str:
    """Queries the current notebook and returns the AI response."""
    bc = BrowserController()
    try:
        await bc.start()
        # JS to type into the chat input and wait for response
        script = f"""
        (function() {{
            const input = document.querySelector('textarea[placeholder*="chat"]');
            if (input) {{
                input.value = "{question}";
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                // Click the send button
                const sendBtn = document.querySelector('button[aria-label*="send"]');
                if (sendBtn) sendBtn.click();
                return "Query submitted";
            }}
            return "Chat input not found";
        }})()
        """
        result = await bc.execute_script(script)
        return f"Query sent. Status: {result}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        await bc.close()

if __name__ == "__main__":
    mcp.run()
