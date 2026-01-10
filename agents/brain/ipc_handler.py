"""
Brain Agent - Answers questions using local LLM
Routes responses back to floater for display.
"""

import sys
import os
import time
import logging
import requests

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.ipc import check_mailbox, send_command
from shared.llm_config import ACTIVE_ROLES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("hndl-it.brain")


class BrainAgent:
    """Uses Qwen 3B to answer questions."""
    
    def __init__(self):
        self.model = ACTIVE_ROLES.get("brain", "qwen2.5:3b")
        self.api_url = "http://localhost:11434/api/generate"
        logger.info(f"Brain Agent initialized with model: {self.model}")
    
    def answer(self, question: str) -> str:
        """Generate an answer to a question."""
        prompt = f"""You are a helpful assistant. Answer this question concisely:

Question: {question}

Answer:"""
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 512,
                        "num_predict": 150
                    }
                },
                timeout=15
            )
            
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                return answer if answer else "I couldn't generate an answer."
            else:
                return f"LLM error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Request timed out. Try a simpler question."
        except Exception as e:
            logger.error(f"Brain error: {e}")
            return f"Error: {e}"


def main():
    """Run brain agent IPC handler."""
    logger.info("🧠 Brain Agent starting...")
    
    brain = BrainAgent()
    
    try:
        while True:
            # Check for questions
            action, payload = check_mailbox("brain")
            
            if action:
                logger.info(f"📥 Received: {action} - {payload}")
                
                try:
                    if action in ("answer", "ask", "query", "question"):
                        question = payload.get("question") or payload.get("query") or payload.get("input", "")
                        
                        if question:
                            logger.info(f"🤔 Thinking about: {question}")
                            answer = brain.answer(question)
                            logger.info(f"💡 Answer: {answer[:100]}...")
                            
                            # Send response back to floater
                            send_command("floater", "display", {
                                "type": "answer",
                                "question": question,
                                "answer": answer
                            })
                        
                    elif action == "quit":
                        logger.info("Shutting down...")
                        break
                        
                    else:
                        logger.warning(f"Unknown action: {action}")
                        
                except Exception as e:
                    logger.error(f"Error: {e}")
                    send_command("floater", "display", {
                        "type": "error",
                        "message": str(e)
                    })
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        logger.info("Brain Agent stopped")


if __name__ == "__main__":
    main()
