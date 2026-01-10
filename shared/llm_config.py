"""
LLM Configuration for hndl-it
Defines the specific models used for different roles in the system.

VRAM Budget: ~10GB on 12GB RTX 2060
Strategy: Two-Gear Model (Resident Router + On-Demand Brain)
"""

# ============================================================================
# MODEL CATALOG
# ============================================================================
MODELS = {
    # Vision
    "moondream": {"size_gb": 1.7, "type": "vision", "notes": "Image understanding"},
    
    # Fast Routers (1.5-2.5 GB)
    "gemma2:2b": {"size_gb": 1.6, "type": "router", "notes": "Default router, fast"},
    "qwen2.5:3b": {"size_gb": 2.0, "type": "router", "notes": "GPT4 recommended"},
    "llama3.2:3b": {"size_gb": 2.2, "type": "router", "notes": "Perplexity pick"},
    
    # Brain Models (4-8 GB)
    "gemma:7b": {"size_gb": 5.0, "type": "brain", "notes": "Original brain"},
    "qwen2.5:7b": {"size_gb": 4.7, "type": "brain", "notes": "Strong reasoning"},
    "llama3.1:8b": {"size_gb": 4.9, "type": "brain", "notes": "DeepThink pick"},
}

# ============================================================================
# ACTIVE CONFIGURATION
# ============================================================================
# This is the "Two-Gear" strategy:
# - Router is always resident in VRAM (fast intent classification)
# - Brain is loaded on-demand for complex tasks (then unloaded)
# - Vision is loaded on-demand for image tasks

ACTIVE_ROLES = {
    "router": "gemma2:2b",     # Always resident (~1.6 GB)
    "brain": "qwen2.5:3b",     # On-demand (~2.0 GB) - Using smaller model for VRAM safety
    "vision": "moondream",     # On-demand (~1.7 GB)
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_model_for_role(role: str) -> str:
    """Get the model name for a specific role."""
    return ACTIVE_ROLES.get(role, "gemma:7b")  # Default to gemma:7b

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

def get_available_models_by_type(model_type: str) -> list:
    """Get all models of a specific type."""
    return [name for name, info in MODELS.items() if info.get("type") == model_type]

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_config():
    """Validate current configuration fits in VRAM budget."""
    VRAM_BUDGET = 10.0  # Leave 2GB headroom on 12GB card
    estimated = estimate_vram_usage()
    
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
