"""
Orchestrator - The Nervous System of hndl-it
Translates Natural Language -> Structured IPC Commands.
Uses tiered routing: Regex (0ms) -> Router LLM (fast) -> Brain LLM (complex)
"""

import json
import requests
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from shared.llm_config import ACTIVE_ROLES

logger = logging.getLogger("hndl-it.orchestrator")


class Orchestrator:
    """
    Central command router for the hndl-it agent suite.
    
    Routing Tiers:
    1. Regex Fast-Path (0ms) - Handles common patterns instantly
    2. Router LLM (Gemma 2B) - Handles ambiguous commands quickly
    3. Brain LLM (Qwen 3B) - Handles complex reasoning (future)
    """
    
    def __init__(self):
        self.router_model = ACTIVE_ROLES["router"]  # gemma2:2b
        self.brain_model = ACTIVE_ROLES["brain"]    # qwen2.5:3b
        self.api_url = "http://localhost:11434/api/generate"
        
        # Statistics for monitoring
        self.stats = {"regex_hits": 0, "router_hits": 0, "errors": 0}
        
        # Regex patterns: (pattern, target, action_extractor)
        # Ordered by priority (first match wins)
        self.patterns: List[Tuple[str, str, str]] = [
            # Browser - Navigation
            (r"^(go to|open|browse|visit|navigate to) (.+)", "browser", "navigate"),
            (r"^(search|google|look up|find) (.+)", "browser", "search"),
            (r"^(search|find) (.+) on (.+)", "browser", "search_site"),
            
            # Todo - Task Management  
            (r"^(add|remind|todo|task|note) (.+)", "todo", "add"),
            (r"^(show|list|view) (todos?|tasks?|notes?)", "todo", "list"),
            (r"^(complete|done|finish|check) (.+)", "todo", "complete"),
            
            # Read - TTS
            (r"^(read|say|speak|pronounce) (.+)", "read", "speak"),
            (r"^(summarize|summary of) (.+)", "read", "summarize"),
            
            # Desktop - Windows Control
            (r"^(type|write|input) (.+)", "desktop", "type"),
            (r"^(click|press|tap) (.+)", "desktop", "click"),
            (r"^(screenshot|capture|snap)", "desktop", "screenshot"),
            (r"^(scroll) (up|down)", "desktop", "scroll"),
            
            # Research - NotebookLM Integration
            (r"^(research|analyze|deep dive|study) (.+)", "research", "analyze"),
            (r"^(upload|ingest|add to notebook) (.+)", "research", "upload"),
            
            # Retrieval - Airweave Memory
            (r"^(recall|remember|what did i|history of) (.+)", "retrieval", "search"),
            (r"^(save|store|remember this) (.+)", "retrieval", "store"),
            
            # System Commands
            (r"^(quit|exit|close|shutdown)", "system", "quit"),
            (r"^(restart|reload)", "system", "restart"),
            (r"^(status|health|check)", "system", "status"),
        ]
        
        # Compile patterns for performance
        self._compiled = [(re.compile(p, re.IGNORECASE), t, a) for p, t, a in self.patterns]

    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Main entry point. Returns structured intent.
        
        Returns:
            Dict with keys: target, action, params, confidence
        """
        clean_input = user_input.strip()
        
        if not clean_input:
            return self._error("Empty input")
        
        # 1. Fast Path: Regex Patterns
        for pattern, target, action in self._compiled:
            match = pattern.match(clean_input)
            if match:
                self.stats["regex_hits"] += 1
                logger.debug(f"Regex matched: {target}/{action}")
                return self._construct_intent(
                    target=target,
                    action=action,
                    params=self._extract_params(match, clean_input),
                    confidence=0.95,
                    method="regex"
                )
        
        # 2. Smart Path: LLM Router
        result = self._ask_router(clean_input)
        self.stats["router_hits"] += 1
        return result

    def _ask_router(self, user_input: str) -> Dict[str, Any]:
        """
        Asks Router LLM (Gemma 2B) to classify intent.
        Optimized for speed with low temperature and tiny context.
        """
        prompt = f"""You are an intent classifier. Analyze: "{user_input}"

Return ONLY valid JSON (no markdown, no explanation):
{{"target": "browser|todo|read|desktop|research|retrieval|system", "action": "verb", "params": {{"key": "value"}}}}

Examples:
"Find GPUs on ebay" -> {{"target": "browser", "action": "search", "params": {{"query": "GPUs", "site": "ebay"}}}}
"Add buy milk" -> {{"target": "todo", "action": "add", "params": {{"item": "buy milk"}}}}
"Read this to me" -> {{"target": "read", "action": "speak", "params": {{"text": "this"}}}}
"Click submit button" -> {{"target": "desktop", "action": "click", "params": {{"element": "submit button"}}}}
"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.router_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 256,
                        "num_predict": 100
                    }
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result_text = response.json().get("response", "")
                intent = self._extract_json(result_text)
                intent["confidence"] = 0.8
                intent["method"] = "router"
                return intent
            else:
                logger.warning(f"Router returned {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning("Router timeout")
        except Exception as e:
            logger.error(f"Router error: {e}")
            self.stats["errors"] += 1
        
        return self._error("Router unavailable", user_input)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extracts JSON from LLM output."""
        try:
            # Find JSON object
            match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                # Validate required fields
                if "target" in parsed:
                    return parsed
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        return {"target": "floater", "action": "unknown", "params": {"raw": text}}

    def _extract_params(self, match: re.Match, original: str) -> Dict[str, Any]:
        """Extracts parameters from regex match groups."""
        groups = match.groups()
        params = {"input": original}
        
        if len(groups) >= 2:
            params["verb"] = groups[0]
            params["subject"] = groups[1]
        if len(groups) >= 3:
            params["modifier"] = groups[2]
            
        return params

    def _construct_intent(self, target: str, action: str, params: Dict, 
                          confidence: float = 1.0, method: str = "direct") -> Dict[str, Any]:
        """Builds standardized intent structure."""
        return {
            "target": target,
            "action": action,
            "params": params,
            "confidence": confidence,
            "method": method
        }

    def _error(self, message: str, original_input: str = "") -> Dict[str, Any]:
        """Returns an error intent."""
        self.stats["errors"] += 1
        return {
            "target": "floater",
            "action": "error",
            "params": {"message": message, "input": original_input},
            "confidence": 0,
            "method": "error"
        }

    def get_stats(self) -> Dict[str, int]:
        """Returns routing statistics."""
        return self.stats.copy()


# Singleton instance
_orchestrator: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    """Get or create the global Orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
