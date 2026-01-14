"""
Brain Agent - Answers questions using local LLM
Routes responses back to floater for display.
"""

import sys
import os
from ollama import Client

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.agent_base import BaseAgent
from shared.ipc import send_command
from shared.llm_config import ACTIVE_ROLES, get_ollama_host

class BrainAgent(BaseAgent):
    """
    Uses LLM (e.g. Qwen) to answer questions.
    Inherits robustness from BaseAgent.
    """
    
    def __init__(self):
        super().__init__("brain")
        self.model = ACTIVE_ROLES.get("brain", "qwen2.5:3b")
        host = get_ollama_host()
        self.client = Client(host=host, timeout=30) # Increased timeout for brain
        self.logger.info(f"🧠 Brain Agent initialized (Model: {self.model}, Host: {host})")
    
    def process_action(self, action: str, payload: dict):
        """Handle incoming brain actions."""
        if action in ("answer", "ask", "query", "question"):
            self._handle_answer(payload)
        elif action == "summarize":
            self._handle_summarize(payload)
        elif action == "analyze_image":
            self._handle_image_analysis(payload)
        else:
            self.logger.warning(f"Unknown action: {action}")

    def _handle_answer(self, payload: dict):
        question = payload.get("question") or payload.get("query") or payload.get("input", "")
        if not question:
            return

        self.logger.info(f"🤔 Thinking about: {question}")

        prompt = f"""You are a helpful assistant. Answer this question concisely:

Question: {question}

Answer:"""
        
        answer = self._generate(prompt)

        self.logger.info(f"💡 Answer: {answer[:100]}...")
        send_command("floater", "display", {
            "type": "answer",
            "question": question,
            "answer": answer
        })

    def _handle_summarize(self, payload: dict):
        text = payload.get("text", "")
        if not text:
            return

        self.logger.info(f"📝 Summarizing text ({len(text)} chars)...")
        prompt = f"""Summarize the following text in 3 bullet points:

{text[:2000]}

Summary:"""

        summary = self._generate(prompt)
        send_command("floater", "display", {
            "type": "answer",
            "question": "Summary",
            "answer": summary
        })

    def _handle_image_analysis(self, payload: dict):
        image_b64 = payload.get("image")
        prompt = payload.get("prompt", "Describe this image.")

        if not image_b64:
            self.logger.warning("No image data provided for analysis")
            return

        self.logger.info(f"👁️ Analyzing image... Prompt: {prompt}")

        # Use _generate but with image support
        # We need to make sure _generate supports images or call client directly
        try:
            # Check if model supports vision?
            # Ideally we might swap model to 'llava' or 'llama3.2-vision' if current is text-only
            # For now assuming the user has a multimodal model loaded or the current one works

            # Using client directly to pass images
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                images=[image_b64],
                stream=False
            )
            answer = response.get("response", "").strip()

            self.logger.info(f"💡 Vision Result: {answer[:100]}...")

            send_command("floater", "display", {
                "type": "answer",
                "question": "Vision Analysis",
                "answer": answer
            })

        except Exception as e:
            self.logger.error(f"Vision analysis failed: {e}")
            send_command("floater", "display", {
                "type": "error",
                "message": f"Vision analysis failed: {e}"
            })

    def _generate(self, prompt: str) -> str:
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.7,
                    "num_ctx": 1024,
                    "num_predict": 256
                }
            )
            return response.get("response", "").strip() or "I couldn't generate an answer."
        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            return f"Error: {e}"

if __name__ == "__main__":
    agent = BrainAgent()
    agent.run()
