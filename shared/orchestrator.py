"""
Orchestrator - The Nervous System of hndl-it
Translates Natural Language -> Structured IPC Commands.
Uses tiered routing: Regex (0ms) -> Router LLM (fast) -> Brain LLM (complex)
"""

import json
import re
import logging
from ollama import AsyncClient
from typing import Dict, Any, Optional, List, Tuple
from shared.llm_config import ACTIVE_ROLES

# Module registry for context-aware commands (reading from independent tools)
try:
    from shared.module_registry import get_reading_context, get_dump_context, search_inbox
    MODULE_REGISTRY_AVAILABLE = True
except ImportError:
    MODULE_REGISTRY_AVAILABLE = False
    def get_reading_context(*args, **kwargs): return {}
    def get_dump_context(*args, **kwargs): return []
    def search_inbox(*args, **kwargs): return []

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
        self.client = AsyncClient(host='http://localhost:11434', timeout=5)
        
        # Statistics for monitoring
        self.stats = {"regex_hits": 0, "router_hits": 0, "errors": 0}
        
        # Regex patterns: (pattern, target, action_extractor)
        # Ordered by priority (first match wins)
        self.patterns: List[Tuple[str, str, str]] = [
            # Context-Aware FIRST: Reference recent data from independent modules
            # These must come before generic patterns to catch "that/the" references
            # "go to that website" / "open that page" / "visit the link from reading"
            (r"^(go to|open|visit) (that|the) (website|page|link|url|site)", "context", "open_reading_url"),
            # "summarize that reading" / "what was that about"
            (r"^(summarize|what was) (that|the|my) (reading|article|page)", "context", "summarize_reading"),
            # "what did I dump" / "show my dumps"
            (r"^(what did i|show my|list my) (dump|dumps|notes)", "context", "list_dumps"),
            # "go back to that" / "open the last thing"
            (r"^(go back to|open the last|reopen) (that|it|thing)", "context", "open_last"),
            # "email that to X" / "send that reading to X"
            (r"^(email|send) (that|this|the reading) to (.+)", "context", "email_reading"),
            # "save that for later" / "bookmark that"
            (r"^(save|bookmark|keep) (that|this|it) (for later|aside)?", "context", "save_for_later"),
            
            # Passthrough to independent modules (hndl-it writes directly to their inbox)
            # "dump: some idea" / "dump this thought"  
            (r"^dump[:\s]+(.+)", "passthrough", "dump"),
            # "capture: screenshot of settings"
            (r"^capture[:\s]+(.+)", "passthrough", "capture"),
            # Intelligent routing: thoughts/ideas → dump (before todo patterns)
            # "I had an idea about X" / "thought: maybe we should..." / "consider this..."
            (r"^(i have an?|i had an?|here'?s an?) (idea|thought)[:\s]*(.+)", "passthrough", "dump"),
            (r"^(thought|idea|concept|notion)[:\s]+(.+)", "passthrough", "dump"),
            (r"^(maybe|perhaps|consider|what if|wondering)[:\s]+(.+)", "passthrough", "dump"),
            
            # Browser - Navigation (generic - after context patterns)
            (r"^(go to|open|browse|visit|navigate to) (.+)", "browser", "navigate"),
            (r"^(search|google|look up|find) (.+)", "browser", "search"),
            (r"^(search|find) (.+) on (.+)", "browser", "search_site"),
            
            # Todo - Task Management (actionable items)
            (r"^(add|remind|todo|task|note) (.+)", "todo", "add"),
            (r"^(show|list|view) (todos?|tasks?|notes?)", "todo", "list"),
            (r"^(complete|done|finish|check) (.+)", "todo", "complete"),
            
            # Read - TTS
            (r"^(v2|hustle|lightning|turbo) (read|say|speak)", "read", "v2_read"),
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
            
            # Brain - Questions that need LLM answers
            (r"^(what is|what's|whats) (.+)", "brain", "answer"),
            (r"^(who is|who's|whos) (.+)", "brain", "answer"),
            (r"^(why|how|when|where) (.+)", "brain", "answer"),
            (r"^(explain|tell me about|describe) (.+)", "brain", "answer"),
            
            # System Commands
            (r"^(quit|exit|close|shutdown)", "system", "quit"),
            (r"^(restart|reload)", "system", "restart"),
            (r"^(status|health|check)", "system", "status"),
        ]
        
        # Compile patterns for performance
        self._compiled = [(re.compile(p, re.IGNORECASE), t, a) for p, t, a in self.patterns]

    async def process(self, user_input: str) -> Dict[str, Any]:
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
                
                # Context-aware commands need resolution from module registry
                if target == "context":
                    resolved = self._resolve_context(action)
                    if resolved:
                        return resolved
                    # Fallback if no context found
                    return self._error("No recent context found to reference", clean_input)
                
                # Passthrough: Write directly to module inbox
                if target == "passthrough":
                    result = self._passthrough_to_inbox(action, match, clean_input)
                    if result:
                        return result
                    return self._error(f"Failed to passthrough to {action}", clean_input)

                # Retrieval: Execute Airweave search immediately and route result to A2UI
                if target == "retrieval":
                    from shared.airweave_client import get_airweave_client
                    client = get_airweave_client()
                    params = self._extract_params(match, clean_input)
                    
                    if action == "search":
                        query = params.get("subject", clean_input)
                        results = client.search(query, limit=5)
                        a2ui_payload = client.to_a2ui(results)
                        
                        # Return an intent that renders this A2UI payload on the floater
                        return self._construct_intent(
                            target="floater",
                            action="render_a2ui",
                            params={"a2ui": a2ui_payload},
                            confidence=1.0,
                            method="airweave_direct"
                        )
                    elif action == "store":
                        content = params.get("subject", clean_input)
                        success = client.store(content)

                        if success:
                            return self._construct_intent(
                                target="floater",
                                action="confirm",
                                params={"message": f"✓ Stored in Memory: {content[:50]}...", "source": "airweave"},
                                confidence=1.0,
                                method="airweave_direct"
                            )
                        else:
                            return self._error("Failed to store in Airweave", clean_input)
                
                return self._construct_intent(
                    target=target,
                    action=action,
                    params=self._extract_params(match, clean_input),
                    confidence=0.95,
                    method="regex"
                )
        
        # 2. Smart Path: LLM Router
        try:
            result = await self._ask_router(clean_input)
            self.stats["router_hits"] += 1
            return result
        except Exception as e:
            logger.warning(f"Router failed, attempting fuzzy fallback: {e}")
            return self._fuzzy_fallback(clean_input)

    async def _ask_router(self, user_input: str) -> Dict[str, Any]:
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
            response = await self.client.generate(
                model=self.router_model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.1,
                    "num_ctx": 256,
                    "num_predict": 100
                }
            )
            
            result_text = response.get("response", "")
            intent = self._extract_json(result_text)
            intent["confidence"] = 0.8
            intent["method"] = "router"
            return intent
                
        except Exception as e:
            logger.error(f"Router error: {e}")
            self.stats["errors"] += 1
        
        return self._fuzzy_fallback(user_input)

    def _fuzzy_fallback(self, user_input: str) -> Dict[str, Any]:
        """
        Dumb keyword-based fallback for when LLM is down.
        FAIL-SAFE: If nothing matches, dump it (never lose input).
        """
        text = user_input.lower()
        
        # Simple keyword mapping
        if any(w in text for w in ["read", "say", "speak", "voice", "summarize"]):
            action = "summarize" if "summarize" in text else "speak"
            return self._construct_intent("read", action, {"text": user_input}, 0.6, "fuzzy")
            
        if any(w in text for w in ["google", "search", "open", "browser", "http"]):
            return self._construct_intent("browser", "search", {"query": user_input}, 0.6, "fuzzy")
            
        if any(w in text for w in ["task", "todo", "list", "remind"]):
            return self._construct_intent("todo", "add", {"text": user_input}, 0.6, "fuzzy")
        
        # FAIL-SAFE: Can't route? Dump it. Never lose user input.
        logger.info(f"Fail-safe dump: {user_input[:50]}...")
        return self._construct_intent("passthrough", "dump", {"content": user_input, "reason": "fail-safe"}, 0.5, "fail-safe")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extracts JSON from LLM output. Prevents catastrophic backtracking."""
        if not text:
            return {"target": "floater", "action": "unknown", "params": {}}
            
        # Limit text size to prevent excessive processing
        text_limit = 2000
        safe_text = text[:text_limit]
        
        try:
            # Linear search for the first '{' and last '}'
            start = safe_text.find('{')
            end = safe_text.rfind('}')
            
            if start != -1 and end != -1 and end > start:
                json_candidate = safe_text[start:end+1]
                parsed = json.loads(json_candidate)
                # Validate required fields
                if "target" in parsed:
                    return parsed
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        return {"target": "floater", "action": "unknown", "params": {"raw": safe_text}}

        
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

    def _passthrough_to_inbox(self, module: str, match: re.Match, original: str) -> Optional[Dict[str, Any]]:
        """
        Write content directly to a module's inbox.
        hndl-it acts as a passthrough - doesn't need the module running.
        """
        try:
            from shared.module_registry import INBOX_ROOT, add_to_inbox_simple
        except ImportError:
            # Fallback: write directly to inbox
            from pathlib import Path
            from datetime import datetime
            
            INBOX_ROOT = Path("D:/Antigravity_Inbox")
            
            def add_to_inbox_simple(inbox_type: str, content: str) -> bool:
                """Simple inbox write fallback."""
                inbox_dir = INBOX_ROOT / inbox_type
                inbox_dir.mkdir(parents=True, exist_ok=True)
                
                today = datetime.now().strftime("%Y-%m-%d")
                timestamp = datetime.now().strftime("%I:%M:%S %p")
                
                filepath = inbox_dir / f"{today}.md"
                
                # Header if new file
                if not filepath.exists():
                    filepath.write_text(f"# {inbox_type.upper()} - {today}\n\n---\n\n", encoding="utf-8")
                
                entry = f"\n## [{timestamp}] via hndl-it\n\n{content}\n\n---\n"
                
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(entry)
                
                return True
        
        # Extract the content from the match
        groups = match.groups()
        content = groups[0] if groups else original
        
        try:
            if module == "dump":
                success = add_to_inbox_simple("dump", content)
                if success:
                    logger.info(f"Passthrough dump: {content[:50]}...")
                    return self._construct_intent(
                        target="floater",
                        action="confirm",
                        params={"message": f"✓ Dumped: {content[:50]}...", "source": "passthrough"},
                        confidence=1.0,
                        method="passthrough"
                    )
                    
            elif module == "capture":
                # For capture, we just log the request - actual capture needs desktop agent
                logger.info(f"Capture request: {content}")
                return self._construct_intent(
                    target="desktop",
                    action="screenshot",
                    params={"note": content, "source": "passthrough"},
                    confidence=0.9,
                    method="passthrough"
                )
                
        except Exception as e:
            logger.error(f"Passthrough failed: {e}")
            
        return None

    def _resolve_context(self, action: str) -> Optional[Dict[str, Any]]:
        """
        Resolve context-aware commands by looking up data from independent modules.
        Converts abstract references like "that website" into concrete URLs/content.
        """
        if not MODULE_REGISTRY_AVAILABLE:
            logger.warning("Module registry not available for context resolution")
            return None
        
        try:
            if action == "open_reading_url":
                # Find the most recent URL from read-it/knowledge inbox
                ctx = get_reading_context(limit=5)
                urls = ctx.get("urls_found", [])
                if urls:
                    url = urls[0]["url"]
                    logger.info(f"Context resolved: opening URL from reading: {url}")
                    return self._construct_intent(
                        target="browser",
                        action="navigate",
                        params={"url": url, "source": "reading_context"},
                        confidence=0.9,
                        method="context"
                    )
                # Try to find URL in recent knowledge entries
                for entry in ctx.get("recent_knowledge", []):
                    url = entry.get("url") or entry.get("metadata", {}).get("url")
                    if url:
                        return self._construct_intent(
                            target="browser",
                            action="navigate", 
                            params={"url": url, "source": "knowledge_context"},
                            confidence=0.85,
                            method="context"
                        )
                        
            elif action == "summarize_reading":
                # Get recent reading content for summarization
                ctx = get_reading_context(limit=3)
                readings = ctx.get("recent_readings", []) + ctx.get("recent_knowledge", [])
                if readings:
                    content = readings[0].get("content", "")[:2000]  # Limit size
                    return self._construct_intent(
                        target="brain",
                        action="summarize",
                        params={"text": content, "source": "recent_reading"},
                        confidence=0.9,
                        method="context"
                    )
                    
            elif action == "list_dumps":
                # Get recent dumps and format for display
                dumps = get_dump_context(limit=10)
                if dumps:
                    formatted = "\n".join([
                        f"• [{d.get('timestamp', 'N/A')}] {d.get('content', '')[:80]}..."
                        for d in dumps
                    ])
                    return self._construct_intent(
                        target="floater",
                        action="display",
                        params={"text": f"Recent dumps:\n{formatted}", "source": "dump_context"},
                        confidence=1.0,
                        method="context"
                    )
                    
            elif action == "open_last":
                # Try to find the most recent actionable item (URL or file)
                ctx = get_reading_context(limit=3)
                urls = ctx.get("urls_found", [])
                if urls:
                    return self._construct_intent(
                        target="browser",
                        action="navigate",
                        params={"url": urls[0]["url"], "source": "last_context"},
                        confidence=0.85,
                        method="context"
                    )
            
            elif action == "email_reading":
                # Get recent reading content for email
                ctx = get_reading_context(limit=1)
                readings = ctx.get("recent_knowledge", [])
                if readings:
                    content = readings[0].get("content", "")[:1000]
                    url = readings[0].get("url", "")
                    return self._construct_intent(
                        target="email",  # Future: email agent
                        action="compose",
                        params={"body": content, "url": url, "source": "reading_context"},
                        confidence=0.9,
                        method="context"
                    )
            
            elif action == "save_for_later":
                # Save current context reference to todo/bookmark
                ctx = get_reading_context(limit=1)
                readings = ctx.get("recent_knowledge", [])
                if readings:
                    content = readings[0].get("content", "")[:200]
                    url = readings[0].get("url", "")
                    return self._construct_intent(
                        target="todo",
                        action="add",
                        params={"text": f"Review: {content}...", "url": url, "source": "save_for_later"},
                        confidence=0.9,
                        method="context"
                    )
                    
        except Exception as e:
            logger.error(f"Context resolution failed: {e}")
            
        return None

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
