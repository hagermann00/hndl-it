# LLM Browser MCP Registry
# All LLMs accessible via Chrome CDP (no API fees)

LLM_REGISTRY = {
    "gemini": {
        "url": "https://gemini.google.com/app",
        "input_selector": "div[contenteditable='true']",
        "submit": "Enter",
        "response_selector": "message-content",
        "profile": "brihag8"
    },
    "deepseek": {
        "url": "https://chat.deepseek.com/",
        "input_selector": "textarea",
        "submit": "Enter",
        "response_selector": ".markdown-body",
        "profile": "brihag8"
    },
    "grok": {
        "url": "https://grok.x.com/",
        "input_selector": "textarea",
        "submit": "Enter",
        "response_selector": ".message-content",
        "profile": "brihag8"
    },
    "claude": {
        "url": "https://claude.ai/new",
        "input_selector": "div[contenteditable='true']",
        "submit": "Enter",
        "response_selector": ".prose",
        "profile": "brihag8"
    },
    "chatgpt": {
        "url": "https://chatgpt.com/",
        "input_selector": "textarea",
        "submit": "Enter",
        "response_selector": ".markdown",
        "profile": "brihag8"
    },
    "manus": {
        "url": "https://manus.im/",
        "input_selector": "textarea",
        "submit": "Enter",
        "response_selector": ".response",
        "profile": "brihag8"
    },
    "abacus": {
        "url": "https://abacus.ai/",
        "input_selector": "textarea",
        "submit": "Enter",
        "response_selector": ".chat-response",
        "profile": "brihag8"
    }
}
