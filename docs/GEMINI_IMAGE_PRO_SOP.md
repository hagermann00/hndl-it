# GEMINI 3 PRO IMAGE (NANO BANANA 3 PRO) - COMPLETE SOP

## Master Reference for the Gemini Ultra Chat Interface ONLY

**Version:** 1.1 | **Date:** January 2026  
**Scope:** Gemini Ultra chat interface ($19.99/mo subscription) - NO API, NO Vertex AI  
**Use Case:** Single images, batches, recurring workflows, and **KDP Publishing**

> [!IMPORTANT]
> This SOP is specifically designed for users operating ONLY through the **Gemini Ultra chat interface** at gemini.google.com. API and Vertex AI methods are mentioned for context but are NOT the focus.

---

## TABLE OF CONTENTS

1. [Quick Reference Card](#quick-reference-card)
2. [Model Identification](#model-identification)
3. [Access Method (Ultra Chat Only)](#access-method-ultra-chat-only)
4. [Core Capabilities](#core-capabilities)
5. [Limitations & Restrictions](#limitations--restrictions)
6. [KDP Publishing Requirements](#kdp-publishing-requirements)
7. [Prompting Best Practices](#prompting-best-practices)
8. [Single Image Workflow](#single-image-workflow)
9. [Batch Processing Workflow](#batch-processing-workflow)
10. [Recurring Request Patterns](#recurring-request-patterns)
11. [Advanced Techniques](#advanced-techniques)
12. [Troubleshooting](#troubleshooting)

---

## QUICK REFERENCE CARD

| Attribute | Value |
|-----------|-------|
| **Official Name** | Gemini 3 Pro Image |
| **Internal Codename** | Nano Banana Pro |
| **Max Resolution** | 4096 x 4096 (4K) |
| **Aspect Ratios** | 1:1, 16:9, 9:16, 21:9, 4:5 |
| **Daily Limit (Free)** | ~100 images/day |
| **Daily Limit (Ultra)** | ~1,000 images/day |
| **Max Input Images** | 14 reference images |
| **Watermark** | SynthID (invisible) + "Created with Gemini" label |
| **Generation Time** | 5-10 seconds typical |

---

## MODEL IDENTIFICATION

### What is "Nano Banana Pro"?

- **Nano Banana** was an internal Google codename discovered during LMArena testing
- **Nano Banana Pro** = **Gemini 3 Pro Image** (production name)
- **Nano Banana** (non-Pro) = **Gemini 2.5 Flash Image** (lighter, faster)

### Model Selection in Gemini Ultra

In the Gemini Ultra chat interface, you do NOT manually select the model. The system automatically routes to:

- **Gemini 3 Pro Image** for complex/high-quality requests
- **Gemini 2.5 Flash Image** for simple/quick requests

---

## ACCESS METHODS

### 1. Gemini Ultra Chat Interface (PRIMARY - This SOP)

**URL:** gemini.google.com  
**Requirement:** Google One AI Ultra subscription ($19.99/mo)

**How to Trigger:**

- Type a prompt describing an image
- Click the camera/image icon
- Say "Generate an image of..."

### 2. Gemini API (Developer)

**Endpoint:** `gemini-3-pro-image-preview`  
**Use Case:** Programmatic/batch generation  
**NOT covered by daily chat limits** - separate quota

### 3. Vertex AI (Enterprise)

**Use Case:** Enterprise-grade, SLA-backed  
**Features:** Batch prediction, 50% cost savings

---

## CORE CAPABILITIES

### ✅ What Nano Banana Pro CAN Do

| Capability | Description |
|------------|-------------|
| **Photorealistic Images** | Sharp detail, accurate lighting, realistic textures |
| **Text Rendering** | Accurate legible text in images (menus, signs, infographics) |
| **Multi-Image Fusion** | Combine up to 14 reference images into one |
| **Subject Consistency** | Maintain character/object across revisions |
| **Conversational Editing** | "Make the sky more dramatic" works mid-conversation |
| **Inpainting** | Add/remove/modify specific areas |
| **Outpainting** | Extend image beyond original borders |
| **Style Transfer** | Apply artistic styles to existing images |
| **4K Resolution** | Generate up to 4096x4096 |
| **Google Grounding** | Access real-world data for accuracy |

### Image Categories Supported

- Product mockups
- Marketing materials
- Infographics with text
- Character design (fictional)
- Landscapes/environments
- Abstract art
- Logos and branding
- Illustrations
- Memes and social content

---

## LIMITATIONS & RESTRICTIONS

### ❌ Hard Blocks (Will Refuse)

| Category | Blocked Content |
|----------|-----------------|
| **Violence** | Gore, torture, sexual violence, harm |
| **Sexual** | Nudity, explicit poses, pornography |
| **Hate** | Racism, discrimination, harassment |
| **Illegal** | Drug use, weapons instructions, underage content |
| **Personal** | Real individuals without consent, addresses, PII |
| **Copyright** | Direct replicas of copyrighted characters/logos |
| **Misinformation** | Election fraud, health misinformation |

### ⚠️ Soft Limitations

| Limitation | Details |
|------------|---------|
| **Daily Quota** | 100 (Free) / 1,000 (Ultra) - resets midnight PT |
| **People Generation** | Temporarily restricted, may refuse some requests |
| **Exact Count** | May not generate exact number requested |
| **Mock-ups with Real Objects** | Brand protection may block modifications |
| **Audio/Video Input** | Not supported for image generation |

### 💰 Tier Comparison

| Feature | Free | AI Pro ($10/mo) | AI Ultra ($20/mo) |
|---------|------|-----------------|-------------------|
| Daily Images | 100 | 500 | 1,000 |
| Max Resolution | 1K | 2K | 4K |
| Priority Access | No | Yes | Yes |
| Batch API | No | Limited | Full |

---

## KDP PUBLISHING REQUIREMENTS

> [!WARNING]
> Gemini Ultra's max native resolution is **4096x4096**. For KDP print covers requiring higher resolution, you may need to upscale using external tools.

### KDP Image Specifications Summary

| Use Case | Min Resolution | Recommended | Format | Color Profile |
|----------|----------------|-------------|--------|---------------|
| **eBook Cover** | 1000 x 1600 px | 1600 x 2560 px | JPEG | RGB |
| **Print Cover** | 300 DPI | 300 DPI | PDF | CMYK |
| **Interior Images** | 300 DPI | 300 DPI | JPEG/TIFF | RGB (eBook) / CMYK (Print) |

### eBook Cover Requirements

| Specification | Requirement | Gemini Ultra Capability |
|---------------|-------------|-------------------------|
| **Ideal Dimensions** | 2560 x 1600 px | ✅ Achievable (request 4K) |
| **Minimum** | 1000 x 625 px | ✅ Easily achievable |
| **Maximum** | 10,000 x 10,000 px | ⚠️ Requires upscaling |
| **Aspect Ratio** | 1.6:1 (height:width) | ✅ Specify in prompt |
| **File Format** | JPEG | ✅ Download as JPEG |
| **File Size** | < 50MB | ✅ Gemini outputs are small |

**Prompt Template for eBook Cover:**

```
Create a professional book cover for "[TITLE]" by [AUTHOR], 
[GENRE] genre, portrait orientation 1600x2560 pixels,
[STYLE] style, [MOOD] atmosphere,
title prominently displayed at top in [FONT STYLE],
author name at bottom, high resolution, KDP-ready
```

### Print Cover Requirements

| Specification | Requirement | Gemini Ultra Capability |
|---------------|-------------|-------------------------|
| **Resolution** | 300 DPI minimum | ⚠️ Must verify after download |
| **Bleed** | 0.125" on all edges | ⚠️ Add manually in post |
| **Color Profile** | CMYK | ❌ Gemini outputs RGB - convert |
| **Spine** | Calculated by page count | ❌ Use KDP Cover Calculator |
| **Safe Zone** | 0.25" from trim | ⚠️ Design with margin |

**KDP Print Cover Workflow (Chat Only):**

1. **Generate Base Cover Art:**

   ```
   Create front cover artwork for a [PAGE_COUNT]-page [GENRE] book,
   title "[TITLE]", [STYLE] design, 4K resolution,
   leave 0.5 inch margin on all edges for bleed
   ```

2. **Download from Gemini** (RGB, ~4096px max)

3. **Post-Processing Required:**
   - Convert RGB → CMYK (use Photoshop, GIMP, or Canva)
   - Add bleed margins (0.125")
   - Calculate spine width: `page_count × 0.002252"` (white paper)
   - Combine front + spine + back into single PDF
   - Use KDP Cover Calculator for exact dimensions

### Interior Image Requirements

| Specification | Requirement | Gemini Ultra Capability |
|---------------|-------------|-------------------------|
| **Resolution** | 300 DPI | ⚠️ Verify after download |
| **Format** | JPEG or TIFF | ✅ JPEG available |
| **Size** | 100% (no enlargement) | ✅ Request exact size |
| **Color** | RGB (eBook) / CMYK (Print) | ⚠️ Convert for print |

**Prompt Template for Interior Illustrations:**

```
Create a [STYLE] illustration for a [GENRE] book interior,
depicting [SCENE DESCRIPTION],
black and white line art OR full color,
300 DPI quality, [WIDTH]x[HEIGHT] pixels,
clean edges, suitable for book printing
```

### KDP-Specific Limitations via Chat Interface

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **Max 4K output** | May not meet large print requirements | Upscale with AI tools (Topaz, Magnific) |
| **RGB only** | Print requires CMYK | Convert in Photoshop/GIMP |
| **No bleed control** | Must add margins manually | Design with extra border |
| **No spine generation** | Can't make full wraparound | Composite in external tool |
| **Watermark** | SynthID embedded | Acceptable for KDP |

### Recommended KDP Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    GEMINI ULTRA CHAT                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Generate cover art at 4K (4096x4096 max)         │    │
│  │ 2. Generate interior illustrations                   │    │
│  │ 3. Download as JPEG                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   POST-PROCESSING                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Upscale if needed (Topaz/Magnific)               │    │
│  │ 2. Convert RGB → CMYK (for print)                   │    │
│  │ 3. Add bleed (0.125")                               │    │
│  │ 4. Use KDP Cover Calculator for dimensions          │    │
│  │ 5. Composite full cover (front + spine + back)      │    │
│  │ 6. Export as PDF (print) or JPEG (eBook)            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      KDP UPLOAD                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PROMPTING BEST PRACTICES

### The SCALES Framework

**S** - Subject: Who/what is in the image  
**C** - Context: Where, when, background  
**A** - Action: What is happening  
**L** - Lighting: Time of day, mood, shadows  
**E** - Emotion/Mood: Feeling to convey  
**S** - Style: Artistic approach, techniques

### Example Prompt Structure

```
[STYLE] [SUBJECT] [ACTION] in [CONTEXT], [LIGHTING], [MOOD], [TECHNICAL SPECS]
```

**Basic:**

```
A robot barista making coffee in a futuristic café
```

**Advanced:**

```
Cinematic photograph of a robot barista with glowing blue optics 
brewing artisan coffee in a neon-lit Tokyo café at night, 
warm tungsten lighting with cyan accent highlights, 
moody cyberpunk atmosphere, shot on 35mm film, shallow depth of field f/1.8
```

### Key Prompt Modifiers

| Category | Examples |
|----------|----------|
| **Style** | photorealistic, watercolor, oil painting, anime, 3D render |
| **Camera** | wide-angle, close-up, macro, drone shot, fisheye |
| **Lighting** | golden hour, studio lighting, dramatic shadows, backlighting |
| **Mood** | serene, dramatic, playful, mysterious, nostalgic |
| **Quality** | HD, 4K, high resolution, ultra-detailed |
| **Aspect** | "16:9 widescreen", "portrait orientation", "square format" |

---

## SINGLE IMAGE WORKFLOW

### Standard Procedure

1. **Open Gemini Ultra** → gemini.google.com
2. **Initiate Request:**
   - Type: "Generate an image of [description]"
   - OR click camera icon → type description
3. **Wait 5-10 seconds** for generation
4. **Review Output**
5. **Iterate if needed:**
   - "Make the lighting warmer"
   - "Add more detail to the background"
   - "Change the color of the dress to blue"
6. **Download** → Click image → Download button

### Quick Commands

| Goal | Command |
|------|---------|
| Generate | "Create an image of..." |
| Edit | "Change the [element] to [new value]" |
| Remove | "Remove the [object] from the image" |
| Add | "Add a [object] to the [location]" |
| Style Change | "Make this look like a [style]" |
| Upscale | "Generate this at 4K resolution" |

---

## BATCH PROCESSING WORKFLOW

### In-Chat Batch (Limited)

The chat interface does NOT support true batch processing. For multiple images:

**Option A: Sequential Generation**

```
Generate 4 variations of a logo for a coffee shop called "Bean Dreams"
- Variation 1: Minimalist
- Variation 2: Vintage
- Variation 3: Modern
- Variation 4: Playful
```

**Option B: Multi-Turn Session**

1. Generate first image
2. "Now create a similar one but with [change]"
3. Continue building collection

### API Batch (Developer)

For true batch processing, use the Gemini API:

```python
import google.generativeai as genai

genai.configure(api_key='your-api-key')

prompts = [
    "A sunset over mountains",
    "A sunrise over ocean",
    "A moonlit forest"
]

for prompt in prompts:
    response = genai.GenerativeModel('gemini-3-pro-image-preview').generate_content(prompt)
    # Save image
```

**Batch API Benefits:**

- Up to 200,000 requests per batch
- 50% cost discount
- Async processing (completes within 24 hours)

---

## RECURRING REQUEST PATTERNS

### Template System

Create reusable prompt templates for consistent output:

**Product Photography Template:**

```
Professional product photograph of [PRODUCT] 
on a [SURFACE] with [BACKGROUND], 
studio lighting with soft shadows, 
e-commerce style, high resolution, 
product centered, clean minimal aesthetic
```

**Social Media Template:**

```
Eye-catching social media graphic in [BRAND_COLORS] 
featuring [SUBJECT] with bold text overlay saying "[TEXT]", 
modern flat design, 1080x1080 square format, 
Instagram-optimized
```

### Character Consistency Workflow

For recurring character across multiple images:

1. **Define Base Character:**

   ```
   A friendly robot named ARIA with silver metallic body, 
   round head, glowing purple eyes, small antenna, 
   approximately 4 feet tall, friendly expression
   ```

2. **Save as Reference:** Download first good generation

3. **Subsequent Requests:**

   ```
   Using the same robot character ARIA from our previous image,
   show her [NEW SCENE/ACTION]
   ```

4. **Use Reference Images:** Upload previous outputs as reference

### Scheduled Content Strategy

**Weekly Content Calendar Workflow:**

| Day | Content Type | Prompt Template |
|-----|--------------|-----------------|
| Mon | Quote Graphic | Inspirational quote with [THEME] background |
| Wed | Product Feature | Product spotlight of [ITEM] |
| Fri | Character Scene | ARIA character in [SETTING] |

---

## ADVANCED TECHNIQUES

### 1. Multi-Image Fusion

Upload 2-14 reference images and combine:

```
Combine the style of [Image 1] with the subject of [Image 2] 
and the color palette of [Image 3]
```

### 2. Thinking Mode (Deep Visual Reasoning)

Trigger planning before rendering:

```
Think carefully about the composition before generating:
Create a complex scene with [detailed requirements]
```

### 3. Reference-Based Generation

Upload existing image + describe changes:

```
[Upload photo]
Recreate this scene in the style of Studio Ghibli anime
```

### 4. Text-in-Image

For accurate text rendering:

```
Create a coffee shop menu board with the following items:
- Espresso $3
- Latte $4
- Cappuccino $4.50
Use rustic chalkboard style with handwritten fonts
```

**Text Tips:**

- Keep phrases under 5 words for best accuracy
- Specify font style explicitly
- Use quotes around exact text needed

### 5. Aspect Ratio Control

```
Generate a cinematic 21:9 ultrawide landscape of...
Create a 9:16 portrait format image for Instagram Stories...
Make a 16:9 widescreen banner showing...
```

---

## TROUBLESHOOTING

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "I can't generate images" | Model confusion | Start new chat, be explicit: "Generate an image" |
| Wrong aspect ratio | Not specified | Add "in 16:9 format" to prompt |
| Text rendering errors | Complex text | Simplify to <5 words, use quotes |
| Quota exceeded | Daily limit | Wait until midnight PT reset |
| Refused generation | Content filter | Rephrase, remove potentially flagged terms |
| Low resolution | Free tier | Upgrade to Ultra for 4K |
| Inconsistent character | No reference | Upload previous images as reference |

### Prompt Debugging

If results are poor:

1. **Simplify:** Remove complex modifiers
2. **Specifiy:** Add explicit style/mood/lighting
3. **Reference:** Upload example of desired output
4. **Iterate:** Use follow-up edits instead of regenerating

---

## APPENDIX: QUICK PROMPT FORMULAS

### For Products

```
Professional [STYLE] product photo of [PRODUCT] on [SURFACE], 
[LIGHTING] lighting, [BACKGROUND], commercial quality, [RESOLUTION]
```

### For Portraits

```
[STYLE] portrait of a [DESCRIPTION] person, 
[EXPRESSION] expression, [LIGHTING], 
shot on [CAMERA/LENS], [MOOD] atmosphere
```

### For Landscapes

```
[STYLE] [TIME_OF_DAY] [LOCATION] landscape, 
[WEATHER] weather, [COLORS] color palette, 
[COMPOSITION] composition, [QUALITY]
```

### For Marketing

```
[PLATFORM]-optimized marketing graphic for [BRAND/PRODUCT],
[BRAND_COLORS] color scheme, featuring [SUBJECT],
bold [FONT_STYLE] text saying "[HEADLINE]",
[STYLE] design, [DIMENSIONS]
```

---

**END OF SOP**

*Document curated from 25+ authoritative sources including Google DevDocs, DeepMind publications, and community research. For NotebookLM curation, upload this document plus linked sources for enhanced RAG capabilities.*
