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
    
    # Experimental / Synthesis Recommendations
    "router_qwen": "qwen2.5:3b", # ~2.0 GB - GPT4 Recommended Coordinator
    "router_llama": "llama3.2:3b", # ~2.2 GB - Perplexity Recommended (balanced)
    "brain_qwen": "qwen2.5:7b",  # ~4.7 GB - Strong reasoning alternative to Gemma
    "brain_llama": "llama3.1:8b", # ~4.9 GB - DeepThink recommendation
}

# Active configuration
ACTIVE_ROLES = {
    "vision": MODELS["vision"],   # Moondream (1.7GB)
    "router": "gemma2:2b",        # Keep Gemma 2B (1.6GB) for now (Router)
    "brain": "qwen2.5:3b",        # SWITCH: Use Qwen 3B (2.0GB) instead of Gemma 7B (5.0GB)
}

def get_model_for_role(role: str) -> str:
    return ACTIVE_ROLES.get(role, MODELS["complex"])
