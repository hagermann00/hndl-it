"""
LLM Configuration for hndl-it
Defines the specific models used for different roles in the system.

Strategy: Two-Gear Model (Resident Router + On-Demand Brain)
"""

import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Allow overriding the host via environment variable
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ============================================================================
# MODEL CATALOG
# ============================================================================
MODELS = {
    # Vision
    "moondream": {"size_gb": 1.7, "type": "vision", "notes": "Image understanding"},
    "llava": {"size_gb": 4.0, "type": "vision", "notes": "Better vision, heavier"},
    
    # Fast Routers (1.5-2.5 GB)
    "gemma2:2b": {"size_gb": 1.6, "type": "router", "notes": "Default router, fast"},
    "qwen2.5:3b": {"size_gb": 2.0, "type": "router", "notes": "GPT4 recommended"},
    "llama3.2:3b": {"size_gb": 2.2, "type": "router", "notes": "Perplexity pick"},
    
    # Brain Models (4-8 GB)
    "gemma:7b": {"size_gb": 5.0, "type": "brain", "notes": "Original brain"},
    "qwen2.5:7b": {"size_gb": 4.7, "type": "brain", "notes": "Strong reasoning"},
    "llama3.1:8b": {"size_gb": 4.9, "type": "brain", "notes": "DeepThink pick"},
    "mistral": {"size_gb": 4.1, "type": "brain", "notes": "Balanced"},
}

# ============================================================================
# ACTIVE CONFIGURATION
# ============================================================================
# This is the "Two-Gear" strategy:
# - Router is always resident in VRAM (fast intent classification)
# - Brain is loaded on-demand for complex tasks (then unloaded)

ACTIVE_ROLES = {
    "router": os.getenv("MODEL_ROUTER", "gemma2:2b"),
    "brain": os.getenv("MODEL_BRAIN", "qwen2.5:3b"),
    "vision": os.getenv("MODEL_VISION", "moondream"),
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_ollama_host() -> str:
    """Get the configured Ollama host."""
    return OLLAMA_HOST

def get_model_for_role(role: str) -> str:
    """Get the model name for a specific role."""
    return ACTIVE_ROLES.get(role, "qwen2.5:3b")

def get_model_info(model_name: str) -> dict:
    """Get model metadata."""
    return MODELS.get(model_name, {"size_gb": 0, "type": "unknown", "notes": ""})

def estimate_vram_usage() -> float:
    """Estimate total VRAM if all active models were loaded."""
    total = 0
    for role, model in ACTIVE_ROLES.items():
        info = MODELS.get(model, {})
        total += info.get("size_gb", 0)
    return total

def validate_config():
    """Validate current configuration fits in VRAM budget."""
    VRAM_BUDGET = 10.0  # Leave 2GB headroom on 12GB card
    estimated = estimate_vram_usage()
    
    print(f"🔧 Ollama Host: {OLLAMA_HOST}")

    if estimated > VRAM_BUDGET:
        print(f"⚠️ WARNING: Estimated VRAM ({estimated:.1f}GB) exceeds budget ({VRAM_BUDGET}GB)")
        return False
    else:
        print(f"✅ VRAM OK: {estimated:.1f}GB / {VRAM_BUDGET}GB budget")
        return True


if __name__ == "__main__":
    print("LLM Configuration:")
    print(f"  Router: {ACTIVE_ROLES['router']}")
    print(f"  Brain:  {ACTIVE_ROLES['brain']}")
    print(f"  Vision: {ACTIVE_ROLES['vision']}")
    print()
    validate_config()
