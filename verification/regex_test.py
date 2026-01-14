import json
import re
from typing import Dict, Any

def extract_json_new(text: str):
    if not text: return {}
    text_limit = 2000
    safe_text = text[:text_limit]
    try:
        start = safe_text.find('{')
        end = safe_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_candidate = safe_text[start:end+1]
            return json.loads(json_candidate)
    except: pass
    return {"raw": safe_text}

# Pathological test cases
print("Test 1 (Normal):", extract_json_new('Result: {"target": "todo", "action": "add"}'))
print("Test 2 (No JSON):", extract_json_new('Just some text'))
print("Test 3 (Malformed):", extract_json_new('{"target": "todo", "action"'))
print("Test 4 (Large input):", extract_json_new('{' + 'a' * 3000 + '}')) # Should truncate
