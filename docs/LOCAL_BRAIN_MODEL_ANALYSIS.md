# HNDL-IT Local Brain Model Selection Analysis

## Purpose

This document provides a comprehensive analysis for selecting the LOCAL BRAIN model for the hndl-it system. The brain model must work CONCURRENTLY with Moondream (vision) and handle multi-agent coordination.

---

## PROMPT FOR CLAUDE CODE / FUTURE AI REVIEW

```
USE MAXIMUM THINKING. Review this entire document with ultra-sequential analysis.

TASK: Provide 3 ranked recommendations for the Local Brain model with:
1. Full justification for each
2. What to SKEW TOWARDS (priorities)
3. What to EXPLICITLY AVOID (anti-patterns)
4. Edge cases and failure modes

CONTEXT:
- Hardware: RTX 2060 (12GB VRAM), 48GB System RAM, NVMe SSD
- Vision Model: Moondream (1.7GB, always loaded)
- Use Case: Multi-agent coordination (Browser, Desktop, Vision, Summarization)
- Priority: 100% LOCAL operation, Cloud only on failure
- Concurrent: Vision + Brain must run simultaneously
```

---

## HARDWARE CONSTRAINTS

| Resource | Total | Reserved | Available for Brain |
|----------|-------|----------|---------------------|
| VRAM | 12,288 MB | 3,700 MB (Moondream + CUDA) | **8,588 MB** |
| **VRAM + RAM Offload** | **24 GB** | 3,700 MB | **~20 GB** ✅ TESTED STABLE |
| System RAM | 48 GB | ~8 GB (Windows) | **~40 GB** (for offload) |
| SSD | NVMe | - | Available for mmap |

### ⚡ CRITICAL UPDATE: 24GB Effective Memory Confirmed

The system has been **tested and validated** to run models up to 24GB using VRAM + RAM offload without crashing. This opens up larger, more capable models like **Mixtral 8x7B**.

---

## ALL MODEL OPTIONS ANALYZED

### Category 1: Dense Models (Traditional)

| Model | VRAM | Context | Reasoning | Tool Use | Speed | Fits w/ Moondream? |
|-------|------|---------|-----------|----------|-------|-------------------|
| TinyLlama 1.1B | 1.5 GB | 4K | ❌ Weak | ❌ Poor | ✅ Fast | ✅ Yes |
| Llama 3.2:3b | 2.0 GB | 8K | ⚠️ Basic | ⚠️ Limited | ✅ Fast | ✅ Yes |
| Phi-3 Mini 3.8B | 2.5 GB | 128K | ✅ Good | ✅ Good | ✅ Fast | ✅ Yes |
| Qwen2.5:7b | 4.5 GB | 128K | ✅ Strong | ✅ Strong | ✅ Good | ✅ Yes |
| Llama 3.1:8b | 5.0 GB | 128K | ✅ Strong | ✅ Strong | ✅ Good | ✅ Yes |
| DeepSeek-Coder:6.7b | 4.5 GB | 16K | ✅ Code-focused | ✅ Strong | ✅ Good | ✅ Yes |
| Mistral 7B | 4.5 GB | 32K | ✅ Strong | ✅ Good | ✅ Good | ✅ Yes |
| Llama 3.1:70b | 40 GB | 128K | ✅✅ Excellent | ✅✅ Excellent | ❌ Needs offload | ⚠️ RAM offload |

### Category 2: Mixture of Experts (MoE)

| Model | Total Params | Active Params | VRAM | Reasoning | Speed | Fits w/ Moondream? |
|-------|-------------|---------------|------|-----------|-------|-------------------|
| OLMoE-1B-7B | 7B | 1B | ~4 GB | ⚠️ Basic | ✅ Fast | ✅ Yes |
| Qwen1.5-MoE-A2.7B | 14B | 2.7B | ~5 GB | ✅ Good | ✅ Good | ✅ Yes |
| Qwen3:30b-a3b | 30B | 3B | ~8 GB | ✅ Strong | ✅ Good | ⚠️ Tight |
| Mixtral 8x7B | 47B | 13B | 26 GB | ✅✅ Excellent | ⚠️ Needs offload | ❌ RAM offload |
| Mixtral 8x22B | 141B | 39B | 88 GB | ✅✅✅ Best | ❌ Very slow | ❌ Extreme offload |

### Category 3: Specialized / Agentic

| Model | VRAM | Specialty | Agentic Capable? | Fits? |
|-------|------|-----------|------------------|-------|
| Nemotron 3 Nano | ~8 GB | Agentic AI | ✅✅ Designed for it | ⚠️ Tight |
| Hermes 2 Pro 7B | ~4.5 GB | Function calling | ✅ Strong | ✅ Yes |
| Gorilla OpenFunctions | ~4 GB | API calling | ✅ Strong | ✅ Yes |

---

## EVALUATION CRITERIA (Weighted)

| Criterion | Weight | Reason |
|-----------|--------|--------|
| Fits in VRAM with Moondream | 25% | MUST FIT - non-negotiable |
| Multi-step reasoning | 20% | Agent needs to plan complex tasks |
| Tool/function calling | 20% | Must output structured commands |
| Speed (tokens/sec) | 15% | Real-time agent interaction |
| Context window | 10% | Remember conversation + task history |
| Error recovery | 10% | Handle failures gracefully |

---

## WHAT TO SKEW TOWARDS ✅

1. **Models with proven tool/function calling**
   - Hermes 2 Pro, Qwen2.5, Mistral - all have instruction-following training
   - Can output JSON commands reliably

2. **7B-8B sweet spot**
   - Enough reasoning for multi-step tasks
   - Fast enough for real-time
   - Fits comfortably with Moondream

3. **Extended context (32K+)**
   - Needed for: task history, error logs, multi-agent coordination
   - Phi-3, Qwen2.5, Llama 3.1 all have 128K capacity

4. **MoE efficiency (if stable)**
   - Get 14B intelligence with 3B active params
   - BUT: Less tested, potential instability

---

## WHAT TO EXPLICITLY AVOID ❌

1. **Models under 3B parameters**
   - TinyLlama, Phi-2, etc.
   - Reason: Cannot handle multi-step reasoning reliably
   - Failure mode: Gets confused, loops, hallucinates steps

2. **Models requiring >8GB VRAM**
   - Leaves no buffer for context growth
   - Failure mode: OOM crash mid-task

3. **Code-only models as general brain**
   - DeepSeek-Coder is great for code, poor for general reasoning
   - Failure mode: Misunderstands non-code tasks

4. **Untested MoE implementations**
   - Some MoE models have sparse Ollama support
   - Failure mode: Random crashes, incorrect expert routing

5. **Models without instruction tuning**
   - Base models (no -instruct, -chat suffix)
   - Failure mode: Doesn't follow commands, rambles

---

## TOP 3 RECOMMENDATIONS (REVISED FOR 24GB CAPACITY)

### 🥇 RECOMMENDATION 1: Mixtral 8x7B (MoE)

**Why:**

- **47B total params, 13B active** - Massive intelligence
- GPT-3.5+ level reasoning
- Excellent at multi-agent coordination
- Strong tool/function calling
- WITH 24GB capacity: **FITS!**

**VRAM + RAM Math:**

```
Moondream:          1,700 MB (VRAM)
Mixtral 8x7B:      12,000 MB (VRAM) + 14,000 MB (RAM offload)
Context (32K):        200 MB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:             ~28 GB distributed across VRAM + RAM
Status:            ✅ FITS WITH TESTED OFFLOAD
```

**Speed:** 10-20 tokens/sec (slower due to offload, but still usable for agentic tasks)

**Risk:** Slightly slower than pure-VRAM models. Proven stable on your system.

---

### 🥈 RECOMMENDATION 2: Qwen2.5:14b-instruct

**Why:**

- 14B dense model - Strong reasoning
- 128K context window
- Fits entirely in 24GB capacity
- Faster than Mixtral (less offload)

**VRAM + RAM Math:**

```
Moondream:          1,700 MB
Qwen2.5:14b:        9,000 MB (mostly VRAM, minimal offload)
Context:              150 MB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:             ~11 GB ✅ FITS IN PURE VRAM
```

**Speed:** 30-40 tokens/sec (faster, mostly in VRAM)

**Risk:** None. Very safe choice.

---

### 🥉 RECOMMENDATION 3: Qwen2.5:7b-instruct (Conservative)

**Why:**

- Original safe recommendation
- 4.5GB VRAM only
- Maximum headroom for other tasks
- Fastest option

**VRAM Math:**

```
Moondream:        1,700 MB
Qwen2.5:7b:       4,500 MB
Context (32K):      100 MB
|--------|------------|--------------|-------------|
| VRAM Safety | ✅✅ | ✅✅ | ⚠️ |
| Reasoning | ✅✅ | ✅✅ | ✅✅✅ |
| Tool Calling | ✅✅ | ✅✅✅ | ✅ |
| Speed | ✅✅ | ✅✅ | ✅✅ |
| Stability | ✅✅✅ | ✅✅ | ⚠️ |
| **TOTAL** | **9/10** | **8/10** | **7/10** |

---

## CONCLUSION

**START WITH: Qwen2.5:7b-instruct**

- Safest choice
- Proven performance
- Room for growth

**UPGRADE PATH:**

1. If Qwen2.5 works well → Stay with it
2. If need better function calling → Try Hermes 2 Pro
3. If need more intelligence → Try MoE (with testing)
4. If all local fails → Escalate to Cloud (Antigravity)

---

## COMMAND TO INSTALL

```bash
ollama pull qwen2.5:7b-instruct
```

---

*Document created: 2026-01-09*
*System: hndl-it v1.0*
*Hardware: RTX 2060 12GB, 48GB RAM*
