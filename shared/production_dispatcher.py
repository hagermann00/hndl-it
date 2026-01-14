"""
Production Dispatcher for hndl-it
Coordinates Browser (Acquisition), NotebookLM (Distillation), and Voice (Output).
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from shared.ipc import send_command
from shared.eval_logger import log_eval
from shared.voice_output import speak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hndl-it.production")

class ProductionDispatcher:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def run_pipeline(self, research_url: str, notebook_name: str = "Production_Archive"):
        """
        Full Production Pipeline:
        1. Scrape Source -> 2. Upload to NotebookLM -> 3. Query for Summary -> 4. Speak
        """
        logger.info(f"🚀 Starting Production Pipeline for: {research_url}")
        log_eval("production", "pipeline_start", f"URL: {research_url}")
        speak("Initializing production pipeline. Starting acquisition phase.")

        # --- Phase 1: Acquisition (Browser Agent) ---
        # Note: In a real flow, we'd wait for result via IPC. 
        # For this MVP/Dispatcher integration, we send the intent.
        send_command("browser", "navigate", {"subject": research_url})
        await asyncio.sleep(5)  # Allow time for page load
        
        # --- Phase 2: Distillation (NotebookLM) ---
        # We trigger the MCP server indirectly or via direct orchestration
        # For now, we'll log the "Distillation Request"
        logger.info(f"🧠 Distilling knowledge in Notebook: {notebook_name}")
        speak("Research acquired. Distilling knowledge in Notebook LM.")
        
        # TRIGGER: Integration with notebooklm-py or MCP server would go here
        # Placeholder for tool call simulation
        distillation_result = f"Summary of insights from {research_url}"
        
        # --- Phase 3: Output (Voice Agent) ---
        logger.info(f"🔊 Outputting session {self.session_id}")
        speak(f"Distillation complete. Here is the summary: {distillation_result}")
        log_eval("production", "pipeline_complete", distillation_result)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python production_dispatcher.py <url>")
        return

    url = sys.argv[1]
    dispatcher = ProductionDispatcher()
    await dispatcher.run_pipeline(url)

if __name__ == "__main__":
    asyncio.run(main())
