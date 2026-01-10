"""
Voice Router for hndl-it
Keyword-based intent classification to route voice commands to appropriate modules.
"""

from enum import Enum
from typing import Tuple, Optional
import re


class VoiceTarget(Enum):
    """Target modules for voice commands."""
    HNDL_IT = "hndl-it"      # General commands, default
    READ_IT = "read-it"      # Document reading, TTS
    TODO_IT = "todo-it"      # Task management
    BROWSER = "browser"      # Web navigation
    DESKTOP = "desktop"      # File operations


# Keyword mappings - order matters (first match wins)
ROUTING_RULES = [
    # read-it triggers
    (VoiceTarget.READ_IT, [
        r"\bread\b", r"\bsummarize\b", r"\bsummary\b", 
        r"\bspeak\b", r"\bnarrate\b", r"\bout\s*loud\b",
        r"\btts\b", r"\btext.to.speech\b"
    ]),
    
    # todo-it triggers
    (VoiceTarget.TODO_IT, [
        r"\btodo\b", r"\bto.do\b", r"\btask\b",
        r"\bremember\b", r"\bremind\b", r"\breminder\b",
        r"\bnote\b", r"\bjot\b", r"\bwrite\s*down\b",
        r"\badd\s*(to\s*)?(my\s*)?list\b", r"\bdon't\s*forget\b"
    ]),
    
    # browser triggers
    (VoiceTarget.BROWSER, [
        r"\bopen\b.*\b(website|page|site|url)\b",
        r"\bgo\s*to\b", r"\bnavigate\b", r"\bbrowse\b",
        r"\bsearch\b.*\b(google|web|online)\b",
        r"\bclick\b", r"\bscroll\b"
    ]),
    
    # desktop triggers
    (VoiceTarget.DESKTOP, [
        r"\bfile\b", r"\bfolder\b", r"\bdirectory\b",
        r"\bopen\b.*\.(exe|pdf|doc|txt|py)\b",
        r"\blaunch\b", r"\brun\b.*\bapp\b",
        r"\bexplorer\b", r"\bdesktop\b"
    ]),
]


def route_voice_command(text: str) -> Tuple[VoiceTarget, str]:
    """
    Route a voice command to the appropriate module.
    
    Args:
        text: Transcribed voice command
        
    Returns:
        Tuple of (target module, cleaned command text)
    """
    text_lower = text.lower().strip()
    
    # Check each routing rule
    for target, patterns in ROUTING_RULES:
        for pattern in patterns:
            if re.search(pattern, text_lower):
                # Clean the command by removing the trigger word
                cleaned = re.sub(pattern, "", text_lower, count=1).strip()
                cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace
                return target, cleaned if cleaned else text
    
    # Default to hndl-it (general router)
    return VoiceTarget.HNDL_IT, text


def extract_todo_text(text: str) -> str:
    """
    Extract the actual todo item from a voice command.
    
    Examples:
        "remember to buy milk" -> "buy milk"
        "todo call mom tomorrow" -> "call mom tomorrow"
        "add to my list pick up groceries" -> "pick up groceries"
    """
    # Remove common prefixes
    prefixes = [
        r"^(remember\s*(to)?)\s*",
        r"^(remind\s*me\s*(to)?)\s*",
        r"^(todo\s*)\s*",
        r"^(to.do\s*)\s*",
        r"^(add\s*(to\s*)?(my\s*)?(list\s*)?)\s*",
        r"^(note\s*(that)?)\s*",
        r"^(jot\s*down\s*)\s*",
        r"^(don't\s*forget\s*(to)?)\s*",
        r"^(i\s*need\s*to\s*)\s*",
    ]
    
    cleaned = text.lower().strip()
    for prefix in prefixes:
        cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE)
    
    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    
    return cleaned.strip()


def parse_voice_command(text: str) -> dict:
    """
    Full parsing of a voice command.
    
    Returns:
        dict with:
            - target: VoiceTarget
            - command: cleaned command
            - raw: original text
            - todo_text: extracted todo (if applicable)
    """
    target, command = route_voice_command(text)
    
    result = {
        "target": target,
        "command": command,
        "raw": text,
    }
    
    if target == VoiceTarget.TODO_IT:
        result["todo_text"] = extract_todo_text(text)
    
    return result


# Test
if __name__ == "__main__":
    test_commands = [
        "remember to buy milk",
        "todo call mom tomorrow",
        "read this document out loud",
        "summarize the article",
        "open google.com",
        "go to youtube",
        "open the downloads folder",
        "what's the weather like",  # default to hndl-it
        "add to my list pick up groceries",
        "remind me to take medicine at 9",
    ]
    
    print("Voice Router Test\n" + "="*50)
    for cmd in test_commands:
        result = parse_voice_command(cmd)
        print(f"\nInput: '{cmd}'")
        print(f"  Target: {result['target'].value}")
        print(f"  Command: {result['command']}")
        if "todo_text" in result:
            print(f"  Todo: {result['todo_text']}")
