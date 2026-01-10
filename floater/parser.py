"""
Natural Language Command Parser for hndl-it.
Uses keyword extraction and fuzzy intent matching for robust parsing.
"""
import re
import uuid
from typing import Dict, Any, Optional, List, Tuple

class CommandParser:
    """
    Intelligent natural language parser that extracts intent and entities.
    """
    
    # Keywords mapped to actions
    INTENT_PATTERNS = {
        # Volume
        "volume_up": {
            "keywords": ["volume", "louder", "loud"],
            "modifiers": ["up", "increase", "raise", "higher", "more"],
            "action": "volume_up",
            "agent": "desktop"
        },
        "volume_down": {
            "keywords": ["volume", "quieter", "quiet"],
            "modifiers": ["down", "decrease", "lower", "less", "reduce"],
            "action": "volume_down", 
            "agent": "desktop"
        },
        "mute": {
            "keywords": ["mute", "unmute", "silence"],
            "modifiers": [],
            "action": "volume_mute",
            "agent": "desktop"
        },
        
        # Media
        "play_pause": {
            "keywords": ["play", "pause", "music", "media"],
            "modifiers": ["toggle"],
            "action": "play_pause",
            "agent": "desktop"
        },
        "next_track": {
            "keywords": ["next", "skip"],
            "modifiers": ["track", "song", "music"],
            "action": "next_track",
            "agent": "desktop"
        },
        "prev_track": {
            "keywords": ["previous", "prev", "last", "back"],
            "modifiers": ["track", "song", "music"],
            "action": "prev_track",
            "agent": "desktop"
        },
        
        # Screenshots
        "screenshot": {
            "keywords": ["screenshot", "screen", "capture", "snap", "print"],
            "modifiers": ["take", "grab", "get", "desktop"],
            "action": "screenshot",
            "agent": "desktop"
        },
        "snip": {
            "keywords": ["snip", "snipping", "crop", "select", "partial"],
            "modifiers": ["tool", "area", "region"],
            "action": "snip",
            "agent": "desktop"
        },
        
        # System
        "lock": {
            "keywords": ["lock"],
            "modifiers": ["computer", "pc", "screen", "desktop"],
            "action": "lock",
            "agent": "desktop"
        },
        "minimize_all": {
            "keywords": ["minimize", "hide"],
            "modifiers": ["all", "windows", "everything"],
            "action": "minimize_all",
            "agent": "desktop"
        },
        "show_desktop": {
            "keywords": ["show", "clear"],
            "modifiers": ["desktop"],
            "action": "minimize_all",
            "agent": "desktop"
        },
        "task_manager": {
            "keywords": ["task", "processes"],
            "modifiers": ["manager", "kill"],
            "action": "task_manager",
            "agent": "desktop"
        },
        "settings": {
            "keywords": ["settings", "preferences", "config"],
            "modifiers": ["windows", "system", "open"],
            "action": "settings",
            "agent": "desktop"
        },
        "search": {
            "keywords": ["search", "find"],
            "modifiers": ["windows", "start"],
            "action": "search",
            "agent": "desktop"
        },
        "explorer": {
            "keywords": ["explorer", "files", "folders"],
            "modifiers": ["file", "open"],
            "action": "file_explorer",
            "agent": "desktop"
        },
        
        # Window Management
        "snap_left": {
            "keywords": ["snap", "move", "window"],
            "modifiers": ["left", "half"],
            "action": "snap_left",
            "agent": "desktop"
        },
        "snap_right": {
            "keywords": ["snap", "move", "window"],
            "modifiers": ["right"],
            "action": "snap_right",
            "agent": "desktop"
        },
        "maximize": {
            "keywords": ["maximize", "fullscreen", "full"],
            "modifiers": ["window", "screen"],
            "action": "maximize",
            "agent": "desktop"
        },
        "minimize": {
            "keywords": ["minimize"],
            "modifiers": ["window", "this"],
            "action": "minimize",
            "agent": "desktop"
        },
        "close_window": {
            "keywords": ["close", "exit", "quit"],
            "modifiers": ["window", "this", "app"],
            "action": "close_window",
            "agent": "desktop"
        },
        
        # Virtual Desktops
        "next_desktop": {
            "keywords": ["next", "switch"],
            "modifiers": ["desktop", "virtual"],
            "action": "switch_desktop",
            "agent": "desktop",
            "params": {"direction": "next"}
        },
        "prev_desktop": {
            "keywords": ["previous", "prev", "last"],
            "modifiers": ["desktop", "virtual"],
            "action": "switch_desktop",
            "agent": "desktop",
            "params": {"direction": "previous"}
        },
        "new_desktop": {
            "keywords": ["new", "create", "add"],
            "modifiers": ["desktop", "virtual"],
            "action": "new_desktop",
            "agent": "desktop"
        },
        
        # Browser Controls
        "new_tab": {
            "keywords": ["new", "open"],
            "modifiers": ["tab"],
            "action": "new_tab",
            "agent": "desktop"
        },
        "close_tab": {
            "keywords": ["close"],
            "modifiers": ["tab"],
            "action": "close_tab",
            "agent": "desktop"
        },
        "refresh": {
            "keywords": ["refresh", "reload"],
            "modifiers": ["page", "browser"],
            "action": "refresh",
            "agent": "desktop"
        },
        "go_back": {
            "keywords": ["back", "previous"],
            "modifiers": ["page", "browser", "go"],
            "action": "go_back",
            "agent": "desktop"
        },
        "go_forward": {
            "keywords": ["forward", "next"],
            "modifiers": ["page", "browser", "go"],
            "action": "go_forward",
            "agent": "desktop"
        },
    }
    
    # Apps that can be launched
    LAUNCHABLE_APPS = [
        "notepad", "calculator", "calc", "paint", "chrome", "firefox", 
        "edge", "terminal", "cmd", "powershell", "spotify", "vscode", 
        "code", "word", "excel", "outlook", "slack", "discord", "zoom",
        "teams", "skype", "vlc", "steam", "obs"
    ]
    
    # Special folder names
    SPECIAL_FOLDERS = {
        "downloads": "~/Downloads",
        "documents": "~/Documents",
        "desktop": "~/Desktop",
        "home": "~",
        "pictures": "~/Pictures",
        "music": "~/Music",
        "videos": "~/Videos",
    }
    
    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text: lowercase, remove extra spaces, strip articles."""
        text = text.lower().strip()
        # Remove common filler words
        text = re.sub(r'\b(the|a|an|my|please|can you|could you|would you|i want to|i want|let\'s|lets)\b', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    @staticmethod
    def _extract_words(text: str) -> List[str]:
        """Extract meaningful words from text."""
        return re.findall(r'\b\w+\b', text.lower())
    
    @classmethod
    def _match_intent(cls, text: str) -> Optional[Tuple[str, Dict]]:
        """Try to match text to an intent using keyword matching."""
        words = set(cls._extract_words(text))
        normalized = cls._normalize(text)
        
        best_match = None
        best_score = 0
        
        for intent_name, config in cls.INTENT_PATTERNS.items():
            keywords = set(config["keywords"])
            modifiers = set(config.get("modifiers", []))
            
            # Calculate match score
            keyword_matches = len(words & keywords)
            modifier_matches = len(words & modifiers)
            
            # Keywords are more important than modifiers
            score = (keyword_matches * 2) + modifier_matches
            
            # Require at least one keyword match
            if keyword_matches > 0 and score > best_score:
                best_score = score
                best_match = (intent_name, config)
        
        return best_match if best_score >= 2 else None
    
    @classmethod
    def parse(cls, text: str) -> Optional[Dict[str, Any]]:
        """Parse natural language command into structured command."""
        original_text = text
        text = text.strip().lower()
        cmd_id = str(uuid.uuid4())
        normalized = cls._normalize(text)
        words = cls._extract_words(text)
        
        # 1. Try direct file path detection first
        # Pattern: "open X" where X looks like a path
        open_match = re.match(r"(?:go\s+to|open|visit|start|launch)\s+(.+)", text)
        if open_match:
            target = open_match.group(1).strip()
            
            # Check for Windows paths
            is_file_path = (
                "\\" in target or
                re.match(r"^[a-z]:", target) or
                target.startswith("/") or
                target.startswith(".") or
                target.startswith("~")
            )
            
            if is_file_path:
                import os
                return {
                    "id": cmd_id,
                    "target_agent": "desktop",
                    "action": "open",
                    "path": os.path.expanduser(target) if target.startswith("~") else target
                }
            
            # Check for special folders (natural language)
            folder_words = target.replace("folder", "").replace("directory", "").strip()
            if folder_words in cls.SPECIAL_FOLDERS:
                import os
                return {
                    "id": cmd_id,
                    "target_agent": "desktop",
                    "action": "open",
                    "path": os.path.expanduser(cls.SPECIAL_FOLDERS[folder_words])
                }
            
            # Check for launchable apps
            for app in cls.LAUNCHABLE_APPS:
                if app in target:
                    return {
                        "id": cmd_id,
                        "target_agent": "desktop",
                        "action": "launch_app",
                        "app_name": app
                    }
            
            # Default: treat as URL/browser navigation
            url = target
            if not url.startswith(("http://", "https://")):
                if "." in url and " " not in url:
                    url = "https://" + url
            
            return {
                "id": cmd_id,
                "target_agent": "browser",
                "action": "navigate",
                "url": url
            }
        
        # 2. Try intent matching
        match = cls._match_intent(text)
        if match:
            intent_name, config = match
            result = {
                "id": cmd_id,
                "target_agent": config["agent"],
                "action": config["action"]
            }
            # Add any extra params
            if "params" in config:
                result.update(config["params"])
            return result
        
        # 3. Specific pattern matches for complex commands
        
        # Scrape patterns
        if re.search(r'\b(scrape|read|get)\s*(page|text|content)?\b', text):
            selector_match = re.search(r'scrape\s+(.+)', text)
            return {
                "id": cmd_id,
                "target_agent": "browser",
                "action": "scrape",
                "selector": selector_match.group(1).strip() if selector_match else None
            }
        
        # Click patterns
        click_match = re.match(r'click\s+(?:on\s+)?(.+)', text)
        if click_match:
            return {
                "id": cmd_id,
                "target_agent": "browser",
                "action": "click",
                "selector": click_match.group(1).strip()
            }
        
        # List directory
        list_match = re.match(r'(?:list|ls|dir)\s+(.+)', text)
        if list_match:
            return {
                "id": cmd_id,
                "target_agent": "desktop",
                "action": "list_dir",
                "path": list_match.group(1).strip()
            }
        
        # Vision/analyze
        vision_match = re.match(r'(?:look|see|vision|analyze|describe|what\'?s?)\s*(.*)', text)
        if vision_match:
            prompt = vision_match.group(1).strip()
            if not prompt or prompt in ["at", "on", "screen", "this", "here"]:
                prompt = "Describe what you see on the screen."
            return {
                "id": cmd_id,
                "target_agent": "vision",
                "action": "analyze",
                "prompt": prompt
            }
        
        # 4. Fallback: try to guess intent from keywords
        
        # Volume keywords anywhere
        if any(w in words for w in ["volume", "loud", "quiet", "sound"]):
            if any(w in words for w in ["up", "increase", "raise", "higher", "louder", "more"]):
                return {"id": cmd_id, "target_agent": "desktop", "action": "volume_up"}
            if any(w in words for w in ["down", "decrease", "lower", "less", "quieter", "reduce"]):
                return {"id": cmd_id, "target_agent": "desktop", "action": "volume_down"}
            if "mute" in words:
                return {"id": cmd_id, "target_agent": "desktop", "action": "volume_mute"}
        
        # Screenshot keywords
        if any(w in words for w in ["screenshot", "capture", "screen"]) and any(w in words for w in ["take", "grab", "get", "screenshot"]):
            return {"id": cmd_id, "target_agent": "desktop", "action": "screenshot"}
        
        # UI Control commands (handled by floater itself)
        if text in ["ghost", "ghost mode", "go ghost", "transparent", "fade", "solid", "unghost", "opaque", "visible"]:
            return {"id": cmd_id, "target_agent": "floater", "action": "toggle_ghost"}
        
        # If nothing matched
        return None
