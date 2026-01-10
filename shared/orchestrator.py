import json
import requests
import re
from typing import Dict, Any, Optional
from shared.llm_config import ACTIVE_ROLES

class Orchestrator:
    """
    The Nervous System of hndl-it.
    Translates Natural Language -> Structured IPC Commands.
    Uses 'Router' model (Gemma 2:2B) for fast intent classification.
    """
    
    def __init__(self):
        self.router_model = ACTIVE_ROLES["router"]  # gemma2:2b
        self.brain_model = ACTIVE_ROLES["brain"]    # gemma:7b
        self.api_url = "http://localhost:11434/api/generate"
        
        # Regex heuristics for instant routing (fast-path)
        self.cheat_sheet = {
            r"^(go to|open|browse) (.+)": "browser",
            r"^(read|say|speak) (.+)": "read",
            r"^(add|remind|todo) (.+)": "todo",
            r"^(search|find|look for) (.+)": "browser",
            r"^(research|analyze|deep dive) (.+)": "research", # NotebookLM
            r"^(recall|remember|what did i) (.+)": "retrieval", # Airweave
        }

    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Main entry point.
        1. Try Regex (0ms latency).
        2. If regex fails, call Gemma 2:2B Router (Low latency).
        3. Return structured Intent.
        """
        clean_input = user_input.strip().lower()

        # 1. Fast Path: Regex Heuristics
        for pattern, target in self.cheat_sheet.items():
            if re.match(pattern, clean_input):
                return self._construct_intent(target, "default", {"input": user_input})

        # 2. Smart Path: LLM Routing
        return self._ask_the_router(user_input)

    def _ask_the_router(self, user_input: str) -> Dict[str, Any]:
        """
        Asks Gemma 2:2B to classify the intent into JSON.
        """
        prompt = f"""
        You are the Router for a Windows Agent.
        Analyze the user command: "{user_input}"
        
        Return JSON ONLY. No markdown. No thinking.
        Format: {{ "target": "browser|todo|read|desktop|research|retrieval", "action": "string", "params": {{ "key": "value" }} }}
        
        Example: "Find cheap GPUs on ebay" -> {{ "target": "browser", "action": "search", "params": {{ "query": "cheap GPUs", "site": "ebay.com" }} }}
        Example: "Add buy milk" -> {{ "target": "todo", "action": "add", "params": {{ "item": "buy milk" }} }}
        Example: "Analyze this PDF" -> {{ "target": "research", "action": "notebooklm_upload", "params": {{ "file": "this PDF" }} }}
        Example: "What did I do yesterday?" -> {{ "target": "retrieval", "action": "airweave_search", "params": {{ "query": "yesterday" }} }}
        """

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.router_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": 256} # Fast, deterministic
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result_text = response.json().get("response", "")
                return self._extract_json(result_text)
            
        except Exception as e:
            print(f"Router Error: {e}")
        
        # Fallback
        return {"target": "floater", "action": "error", "params": {"msg": "Router unreachable"}}

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extracts JSON from LLM output."""
        try:
            # Try finding { ... }
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        return {"target": "floater", "action": "unknown", "params": {"raw": text}}

    def _construct_intent(self, target, action, params):
        return {"target": target, "action": action, "params": params}
