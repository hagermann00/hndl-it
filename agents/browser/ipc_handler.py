"""
Browser Agent IPC Handler
Listens for IPC commands and executes browser actions.
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.ipc import check_mailbox
from agents.browser.browser_controller import BrowserController

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hndl-it.browser.handler")


def main():
    """Run browser agent IPC handler."""
    logger.info("🌐 Browser Agent Handler starting...")
    
    controller = None
    
    try:
        while True:
            # Check for commands
            action, payload = check_mailbox("browser")
            
            if action:
                logger.info(f"📥 Received: {action} - {payload}")
                
                try:
                    # Lazy init controller
                    if controller is None:
                        controller = BrowserController()
                        controller.navigate("about:blank")
                    
                    # Handle actions
                    if action == "navigate":
                        url = payload.get("subject") or payload.get("url") or payload.get("input", "")
                        # Clean URL
                        if not url.startswith(("http://", "https://")):
                            url = "https://" + url
                        controller.navigate(url)
                        logger.info(f"✅ Navigated to {url}")
                        
                    elif action == "search":
                        query = payload.get("subject") or payload.get("query") or payload.get("input", "")
                        site = payload.get("modifier") or payload.get("site", "")
                        
                        if site:
                            url = f"https://www.google.com/search?q=site:{site}+{query}"
                        else:
                            url = f"https://www.google.com/search?q={query}"
                        controller.navigate(url)
                        logger.info(f"✅ Searched: {query}")
                        
                    elif action == "search_site":
                        query = payload.get("subject", "")
                        site = payload.get("modifier", "")
                        url = f"https://www.google.com/search?q=site:{site}+{query}"
                        controller.navigate(url)
                    
                    elif action == "query":
                        # Generic query - search Google
                        query = payload.get("key") or payload.get("query") or payload.get("subject") or payload.get("input", "")
                        url = f"https://www.google.com/search?q={query}"
                        controller.navigate(url)
                        logger.info(f"✅ Queried: {query}")
                        
                    elif action == "close":
                        if controller:
                            controller.quit()
                            controller = None
                        logger.info("✅ Browser closed")
                        
                    elif action == "quit":
                        logger.info("Shutting down...")
                        break
                        
                    else:
                        logger.warning(f"Unknown action: {action}")
                        
                except Exception as e:
                    logger.error(f"Error executing {action}: {e}")
            
            time.sleep(0.5)  # Poll interval
            
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        if controller:
            controller.quit()
        logger.info("Browser Handler stopped")


if __name__ == "__main__":
    main()
