"""
LLM Configuration for hndl-it
Defines the specific models used for different roles in the system.
Targeting ~10GB VRAM usage on 12GB card.
"""

# Model definitions
MODELS = {
    "vision": "moondream",       # ~1.7 GB
    "router": "gemma2:2b",       # ~1.6 GB - Fast decision making
    "complex": "gemma:7b",       # ~5.0 GB - Deep reasoning/Task execution
    "editor": "qwen2.5:7b-instruct", # ~4.7 GB - (Optional fallback)
}

# Active configuration
ACTIVE_ROLES = {
    "vision": MODELS["vision"],
    "router": MODELS["router"],
    "brain": MODELS["complex"],  # Main thinker
}

def get_model_for_role(role: str) -> str:
    return ACTIVE_ROLES.get(role, MODELS["complex"])
