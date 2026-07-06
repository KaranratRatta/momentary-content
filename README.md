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

# 2. Configure API keys
cp .env.example .env
#    then edit .env and fill in FAL_KEY (https://fal.ai/dashboard/keys)
#    and OPENROUTER_API_KEY (https://openrouter.ai/keys)

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
│  (timestamps)│    │  (LLM +      │    │  (FAL API)   │    │  [Future]    │
│              │    │   style)     │    │              │    │              │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

| Stage | File | What it does |
|-------|------|-------------|
| 1 | `parser.py` | Extracts timestamps and text from the script |
| 2 | `prompt_builder.py` | Uses an LLM (via OpenRouter) to write a visual depiction of each scene — a story bible keeps characters consistent across scenes, then per-scene prompts are generated in parallel |
| 3 | `generator.py` | Calls `fal-ai/flux/schnell` in parallel for all prompts, downloads the images |
| 4 | `video_assembler.py` | [Not yet implemented] Stitches images + TTS audio into a video |

The prompt builder writes a real **visual depiction** of each moment (who is on
screen, what they're doing, expression, lighting, setting) — it doesn't just
dump the narration text into a style template. A one-call **story bible** locks
each character's appearance so they stay identical across long videos (~100
scenes). Each prompt bakes in the chosen visual style.

> No `OPENROUTER_API_KEY`? Add `--no-llm` (or run with no key) to use a simple
> offline fallback so `--skip-generate` previews still work — scene quality
> will be much lower.

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

# No OpenRouter key? Use the simple offline fallback:
python pipeline.py --script scripts/input.txt --story demo --skip-generate --no-llm
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

prompt_builder:                  # LLM scene-prompt generation
  model: "anthropic/claude-sonnet-4"   # any OpenRouter model id
  temperature: 0.8               # higher = more creative depictions
  concurrency: 8                 # parallel LLM calls for scene prompts
  build_bible: true              # build a character/visual bible first

generator:
  num_inference_steps: 4         # Quality/speed tradeoff
  image_size: "landscape_16_9"   # Aspect ratio
```

API keys live in `.env` (see `.env.example`), not in `config.yaml`.

---

## Script Format

Your script must have a timestamp at the start of each line, in `HH:MM:SS` or
`MM:SS` format:

```
HH:MM:SS the text of what's being said at this moment
MM:SS shorter timestamps also work
```

**Rules:**
- One segment per line
- Timestamp must be at the very beginning of the line
- Every timestamp gets one image
- The parser scans anywhere, so a continuous single-line script also works

---

## Output Structure

```
output/
└── <story-name>/
    ├── segments.json         # Parsed script data
    ├── prompts.json          # Full prompts sent to the API
    ├── story_bible.json      # Character & visual bible (LLM)
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

# Stage 2: Build prompts from existing segments (needs OPENROUTER_API_KEY;
#           add --no-llm for the offline fallback)
python prompt_builder.py output/story/segments.json styles/ms_paint.yaml > output/story/prompts.json

# Stage 3: Generate images from existing prompts
python generator.py output/story/prompts.json

# Stage 4: [Future] Assemble video from manifest
# python video_assembler.py output/story/manifest.json
```

---

## API Keys

Keys are loaded from a `.env` file (gitignored). Copy the template and fill it in:

```bash
cp .env.example .env
```

```dotenv
# .env
FAL_KEY=your-app-id:your-secret                # image generation — fal.ai/dashboard/keys
OPENROUTER_API_KEY=your-openrouter-key         # LLM prompts — openrouter.ai/keys
```

- **FAL** (`FAL_KEY`, format `app-id:secret`) — required for image generation.
- **OpenRouter** (`OPENROUTER_API_KEY`) — required for LLM scene prompts.
  Without it, the pipeline falls back to simple deterministic prompts
  (`--no-llm`), so previews still work but scene quality drops.

Keys can also be exported as regular environment variables if you prefer.

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
- `FAL_KEY` and `OPENROUTER_API_KEY` (in `.env` — see `.env.example`)
- `pip install -r requirements.txt`

---

## Project Structure

```
long_form_content/
├── pipeline.py              # Main orchestrator
├── parser.py                # Stage 1: script → segments
├── prompt_builder.py        # Stage 2: segments → LLM visual prompts
├── llm_client.py            # OpenRouter (OpenAI-compatible) chat client
├── generator.py             # Stage 3: prompts → images
├── video_assembler.py       # Stage 4: [Future] video
├── config.yaml              # Main configuration
├── requirements.txt
├── .env.example             # API key template (copy to .env)
├── README.md
├── CLAUDE.md                # Claude Code project docs
├── styles/
│   ├── ms_paint.yaml
│   ├── realistic.yaml
│   └── anime.yaml
├── scripts/
│   └── input.txt            # Example script
├── tests/                   # Unit tests (pytest)
└── output/
    └── <story-name>/
        ├── segments.json
        ├── prompts.json
        ├── story_bible.json
        ├── manifest.json
        ├── images/
        └── video/           # [Future]
```