<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/status-active-success?style=flat-square">
  <img alt="Status" src="https://img.shields.io/badge/status-active-success?style=flat-square">
</picture>
&nbsp;
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/python-3.9+-blue?style=flat-square">
  <img alt="Python" src="https://img.shields.io/badge/python-3.9+-blue?style=flat-square">
</picture>
&nbsp;
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/license-MIT-yellow?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square">
</picture>

# Script → Image Pipeline

Convert a timestamped YouTube script into a sequence of AI-generated images — one image per timestamp — using [fal.ai](https://fal.ai) Flux models.

Each story gets its own folder. The visual style is fully configurable. Video assembly is ready to plug in when you need it.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your FAL API key
#    Get one at https://fal.ai/dashboard/keys
export FAL_KEY="your-app-id:your-secret"

# 3. Run the pipeline
python pipeline.py --script scripts/input.txt --story puppy-duck --style ms_paint

# 4. Find your images
open output/puppy-duck/images/
```

---

## Example

**Input script** (`scripts/input.txt`):
```
00:00:00 this puppy lost his parents until he
00:00:02 found this duck he was shivering and
00:00:04 didn't know what to do so the duck took
00:00:06 him on her back and comforted him
```

**Run:**
```bash
python pipeline.py --script scripts/input.txt --story puppy-duck --style ms_paint
```

**Output** (`output/puppy-duck/`):
```
output/puppy-duck/
├── segments.json          # Parsed timestamps + text
├── prompts.json           # Full prompts sent to the API
├── manifest.json          # Timestamp → image file mapping
├── images/
│   ├── 000_00-00-00.jpg   # puppy alone, sad
│   ├── 001_00-00-02.jpg   # duck appears, puppy shivering
│   ├── 002_00-00-04.jpg   # duck offers help
│   └── 003_00-00-06.jpg   # puppy on duck's back, comforted
└── video/                 # [Future]
    └── final.mp4
```

---

## How It Works

The pipeline runs in 4 stages:

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. Parse    │ →  │ 2. Build     │ →  │ 3. Generate  │ →  │ 4. Assemble  │
│   script     │    │   prompts    │    │   images     │    │   video      │
│  (timestamps)│    │  (style +    │    │  (FAL API)   │    │  [Future]    │
│              │    │   emotion)   │    │              │    │              │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

| Stage | File | What it does |
|-------|------|-------------|
| 1 | `parser.py` | Extracts timestamps and text from the script |
| 2 | `prompt_builder.py` | Analyzes each segment for emotion + story stage, then builds a tailored prompt using the chosen style template |
| 3 | `generator.py` | Calls `fal-ai/flux/schnell` in parallel for all prompts, downloads the images |
| 4 | `video_assembler.py` | [Not yet implemented] Stitches images + TTS audio into a video |

The prompt builder automatically detects:
- **Emotion** — sad, happy, scared, confused, hopeful, tense, surprised
- **Story stage** — setup, conflict, turning point, resolution

Each prompt is tailored to match what's happening at that exact moment in the story.

---

## Usage

### Basic

```bash
# Every story gets its own folder under output/
python pipeline.py --script scripts/my-script.txt --story my-story
```

### Switch visual styles

```bash
# Stick figure / MS Paint style
python pipeline.py --script scripts/input.txt --story demo --style ms_paint

# Photorealistic
python pipeline.py --script scripts/input.txt --story demo --style realistic

# Anime cel-shaded
python pipeline.py --script scripts/input.txt --story demo --style anime
```

### Multiple stories

```bash
python pipeline.py --script scripts/cat.txt --story cat-adventure --style anime
python pipeline.py --script scripts/dog.txt --story dog-rescue --style ms_paint
python pipeline.py --script scripts/space.txt --story space-odyssey --style realistic

# Output:
# output/cat-adventure/images/
# output/dog-rescue/images/
# output/space-odyssey/images/
```

### Preview prompts without generating

```bash
python pipeline.py --script scripts/input.txt --story demo --skip-generate
# Builds prompts.json so you can review before spending API credits
```

### Control speed

```bash
# Lower concurrency = fewer parallel requests
python pipeline.py --script scripts/input.txt --story demo --concurrency 4
```

---

## Style Templates

Create your own visual style by adding a file to the `styles/` directory.

### Built-in styles

| Style | Description |
|-------|-------------|
| `ms_paint` | Stick figures, thick wobbly black outlines, flat colors, MS Paint amateur look |
| `realistic` | Photorealistic, cinematic lighting, detailed textures, 8K quality |
| `anime` | Cel-shaded 2D anime style, large eyes, vibrant colors |

### Create a custom style

```yaml
# styles/pixel_art.yaml
name: "pixel_art"
description: "8-bit retro video game pixel art"

base_prompt: >
  8-bit pixel art style, retro video game graphics.
  Low resolution pixelated look. Blocky characters.
  Limited color palette. No shading. No anti-aliasing.
  Gameboy-style aesthetic.

character_rules:
  - "Pixel art characters with blocky square proportions"
  - "Limited color palette (max 4 colors per character)"
  - "Simple pixel expressions using 2-3 pixels for eyes"

image_size: "landscape_16_9"
num_inference_steps: 6
```

Then use it:
```bash
python pipeline.py --script scripts/input.txt --story demo --style pixel_art
```

---

## Configuration

All settings in `config.yaml`:

```yaml
pipeline:
  style: "ms_paint"              # Default style
  model: "fal-ai/flux/schnell"   # FAL model
  concurrency: 8                 # Parallel image generations
  output_dir: "./output"         # Base output directory

generator:
  num_inference_steps: 4         # Quality/speed tradeoff
  image_size: "landscape_16_9"   # Aspect ratio
```

---

## Script Format

Your script must have timestamps at the start of each line:

```
HH:MM:SS the text of what's being said at this moment
MM:SS shorter timestamps also work
SS seconds-only format too
```

**Rules:**
- One segment per line
- Timestamp must be at the very beginning of the line
- Every timestamp gets one image

---

## Output Structure

```
output/
└── <story-name>/
    ├── segments.json         # Parsed script data
    ├── prompts.json          # Full prompts sent to the API
    ├── manifest.json         # Timestamp → image mapping
    ├── images/
    │   ├── 000_00-00-00.jpg
    │   ├── 001_00-00-05.jpg
    │   └── ...
    └── video/                # [Future]
        └── final.mp4
```

### manifest.json

The manifest is the glue between stages. It maps every timestamp to its image:

```json
[
  {
    "timestamp_str": "00:00:00",
    "timestamp_seconds": 0.0,
    "text": "this puppy lost his parents until he",
    "image_path": "output/story/images/000_00-00-00.jpg",
    "image_url": "https://..."
  },
  ...
]
```

When you add video assembly, the video assembler reads this file to know which image to show at which time.

---

## Running Individual Stages

```bash
# Stage 1: Parse only
python parser.py scripts/input.txt > output/story/segments.json

# Stage 2: Build prompts from existing segments
python prompt_builder.py output/story/segments.json styles/ms_paint.yaml > output/story/prompts.json

# Stage 3: Generate images from existing prompts
python generator.py output/story/prompts.json

# Stage 4: [Future] Assemble video from manifest
# python video_assembler.py output/story/manifest.json
```

---

## API Key

This tool requires a FAL API key. Get one at [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys).

Set it as an environment variable:

```bash
export FAL_KEY="your-app-id:your-secret"
```

The key format is `app-id:secret` (a UUID, a colon, then another UUID).

---

## Adding Video (Future)

When you're ready to add video assembly:

1. Install MoviePy: `pip install moviepy`
2. Implement `video_assembler.py` — the `manifest.json` already has everything mapped:
   - Which image to show → `image_path`
   - When to show it → `timestamp_seconds`
   - What to say → `text` (for TTS or subtitles)
3. Optionally add TTS (text-to-speech) using OpenAI TTS or edge-tts

The `output/<story>/manifest.json` structure is designed so the video assembler
can be a drop-in module.

---

## Requirements

- Python 3.9+
- `FAL_KEY` environment variable
- `pip install -r requirements.txt`

---

## Project Structure

```
long_form_content/
├── pipeline.py              # Main orchestrator
├── parser.py                # Stage 1: script → segments
├── prompt_builder.py        # Stage 2: segments → prompts
├── generator.py             # Stage 3: prompts → images
├── video_assembler.py       # Stage 4: [Future] video
├── config.yaml              # Main configuration
├── requirements.txt
├── README.md
├── CLAUDE.md                # Claude Code project docs
├── styles/
│   ├── ms_paint.yaml
│   ├── realistic.yaml
│   └── anime.yaml
├── scripts/
│   └── input.txt            # Example script
└── output/
    └── <story-name>/
        ├── segments.json
        ├── prompts.json
        ├── manifest.json
        ├── images/
        └── video/           # [Future]
```