"""
Unified Browser LLM MCP Server
Uses Chrome CDP to access all LLMs via your logged-in browser.
No API keys needed.
"""
from fastmcp import FastMCP
import asyncio
import sys
import os

# Add hndl-it to path
HNDL_IT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, HNDL_IT_PATH)

from agents.browser.browser_controller import BrowserController
from mcp_servers.llm_registry import LLM_REGISTRY

mcp = FastMCP("browser-llm")


@mcp.tool()
async def ask_llm(llm: str, prompt: str) -> str:
    """
    Send a prompt to any LLM via browser automation.
    
    Args:
        llm: One of: gemini, deepseek, grok, claude, chatgpt, manus, abacus
        prompt: The message to send
    
    Returns:
        The LLM's response text
    """
    llm = llm.lower()
    if llm not in LLM_REGISTRY:
        return f"Unknown LLM: {llm}. Available: {list(LLM_REGISTRY.keys())}"
    
    config = LLM_REGISTRY[llm]
    bc = BrowserController()
    
    try:
        await bc.start()
        await bc.navigate(config["url"])
        
        # Wait for input to be ready
        await asyncio.sleep(2)
        
        # Type the prompt
        script = f"""
        (function() {{
            const input = document.querySelector('{config["input_selector"]}');
            if (input) {{
                input.focus();
                input.innerText = `{prompt.replace('`', '\\`')}`;
                return true;
            }}
            return false;
        }})()
        """
        success = await bc.execute_script(script)
        if not success:
            return f"Could not find input field for {llm}"
        
        # Submit
        await bc.execute_script("document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}))")
        
        # Wait for response
        await asyncio.sleep(5)
        
        # Scrape response
        response = await bc.scrape_text(config.get("response_selector"))
        return response or "No response captured"
        
    except Exception as e:
        return f"Error: {e}"
    finally:
        await bc.close()


@mcp.tool()
async def list_llms() -> str:
    """List all available LLMs."""
    return str(list(LLM_REGISTRY.keys()))


@mcp.tool()
async def open_llm(llm: str) -> str:
    """Open an LLM in the browser without sending a prompt."""
    llm = llm.lower()
    if llm not in LLM_REGISTRY:
        return f"Unknown LLM: {llm}"
    
    bc = BrowserController()
    try:
        await bc.start()
        await bc.navigate(LLM_REGISTRY[llm]["url"])
        return f"Opened {llm}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
