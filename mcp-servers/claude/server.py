from fastmcp import FastMCP
from playwright.sync_api import sync_playwright
import os
import time

mcp = FastMCP("claude-web")

# Config
USER_DATA_DIR = r"C:\Users\dell3630\AppData\Local\Google\Chrome\User Data"
HEADLESS = False  # Set to False so you can see it working initially

@mcp.tool()
def ask_claude_web(prompt: str, context_files: list[str] = None) -> str:
    """
    Ask Claude.ai a question using the user's existing logic/browser session.
    No API key required. Uses web automation.
    """
    with sync_playwright() as p:
        # Connect to browser with user profile (requires closing main Chrome first usually, 
        # or we use a separate profile/debugging port)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=HEADLESS,
            args=["--remote-debugging-port=9222"] 
        )
        
        page = browser.new_page()
        page.goto("https://claude.ai/new")
        
        # Wait for input box
        # Note: Selectors change, this is a best-guess stable selector strategy
        page.wait_for_selector("div[contenteditable='true']")
        
        # Attach files if needed (stub)
        if context_files:
            pass 

        # Type prompt
        page.fill("div[contenteditable='true']", prompt)
        page.keyboard.press("Enter")
        
        # Wait for response (look for "Copy" button or cessation of streaming)
        # This is the tricky part in web auto - simplified wait here
        page.wait_for_timeout(5000) 
        
        # Scrape last message
        # Adding simple scraping logic here
        
        # browser.close() # Keep open?
        return "Command sent to Claude.ai (Web Automation)"

if __name__ == "__main__":
    mcp.run()
