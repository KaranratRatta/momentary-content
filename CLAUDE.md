# ─── Script-to-Image Pipeline ────────────────────────────────────────────────

## Overview

This pipeline converts a timestamped script into a sequence of images, one per
timestamp, using the FAL API (fal-ai/flux/schnell by default). The visual style
is fully configurable via YAML templates. Each story gets its own folder.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (copy template, fill in FAL_KEY + OPENROUTER_API_KEY)
cp .env.example .env

# Run the full pipeline with the example script
python pipeline.py --script scripts/input.txt --story puppy-duck --style ms_paint

# Output goes to: output/puppy-duck/
```

## Pipeline Stages

```
┌──────────────────────────────────────────────────┐
│  python pipeline.py --script input.txt --story X  │
│                         --style Y                 │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│  1. parser.py                                     │
│     Reads script → extracts timestamps + text     │
│     Output: output/<story>/segments.json          │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│  2. prompt_builder.py                              │
│     LLM writes visual scene depictions             │
│     Story bible + per-scene prompts (parallel)     │
│     Output: output/<story>/prompts.json            │
│            output/<story>/story_bible.json         │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│  3. generator.py                                   │
│     Calls FAL API in parallel for all prompts      │
│     Saves JPEGs + output/<story>/manifest.json     │
└────────────────────┬─────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────┐
│  4. video_assembler.py [FUTURE]                    │
│     Stitches images + TTS audio into video        │
└──────────────────────────────────────────────────┘
```

## Usage

```bash
# Basic usage — story name creates its own folder
python pipeline.py --script scripts/input.txt --story my-story

# With a specific visual style
python pipeline.py --script scripts/input.txt --story my-story --style realistic

# Multiple stories — each gets its own output folder
python pipeline.py --script scripts/cat-story.txt --story cat-adventure --style anime
python pipeline.py --script scripts/dog-story.txt --story dog-rescue --style ms_paint
python pipeline.py --script scripts/space-story.txt --story space-odyssey --style realistic

# Control concurrency (how many images generate at once)
python pipeline.py --script scripts/input.txt --story my-story --concurrency 4

# Prompts only (no API call — preview what would be generated)
python pipeline.py --script scripts/input.txt --story my-story --skip-generate

# Custom base output directory
python pipeline.py --script scripts/input.txt --story my-story --output-dir ./my-projects
```

## Script Format

Timestamps use a colon-separated format — `HH:MM:SS` or `MM:SS`:

```
HH:MM:SS text here...
MM:SS text here...
```

One segment per line, timestamp at the start of the line. (The parser scans
for timestamps anywhere, so a continuous single-line script also works.)

Example (`scripts/input.txt`):
```
00:00:00 this puppy lost his parents until he
00:00:02 found this duck he was shivering and
00:00:04 didn't know what to do so the duck took
00:00:06 him on her back and comforted him
```

## Style Templates

Edit or add templates in `styles/`:

| Style | File | Description |
|-------|------|-------------|
| ms_paint | `styles/ms_paint.yaml` | Stick figures, thick lines, MS Paint look |
| realistic | `styles/realistic.yaml` | Photorealistic cinematic images |
| anime | `styles/anime.yaml` | Anime cel-shaded style |

Create a new style by copying one of these files and customizing the
`base_prompt` and `character_rules`.

## Config

See `config.yaml` for all settings:
- `pipeline.style` — default style name
- `pipeline.model` — FAL model endpoint
- `pipeline.concurrency` — parallel image generation count
- `prompt_builder.model` — OpenRouter model id for scene-prompt generation
- `prompt_builder.concurrency` — parallel LLM calls for scene prompts
- `generator.num_inference_steps` — quality/speed tradeoff
- `generator.image_size` — aspect ratio (landscape_16_9, square_hd, etc.)

## Output Structure

```
output/
└── <story-name>/
    ├── segments.json        # Parsed script segments
    ├── prompts.json         # Final prompts sent to the API
    ├── manifest.json        # Timestamp → image file mapping
    ├── images/
    │   ├── 000_00-00-00.jpg
    │   ├── 001_00-00-02.jpg
    │   └── ...
    └── video/               # [Future]
        └── final.mp4
```

Each story is isolated in its own folder so you can run multiple stories
without files mixing together.

## Running Individual Stages

```bash
# Just parse
python parser.py scripts/input.txt > output/story-name/segments.json

# Parse → build prompts (needs OPENROUTER_API_KEY; add --no-llm for offline fallback)
python prompt_builder.py output/story-name/segments.json styles/ms_paint.yaml > output/story-name/prompts.json

# Just generate images from existing prompts
python generator.py output/story-name/prompts.json

# Future: just assemble video from existing manifest
# python video_assembler.py output/story-name/manifest.json
```

## Adding Video Assembly (Future)

When you're ready to add video, uncomment the `moviepy` dependency in
`requirements.txt` and implement `video_assembler.py`. The
`output/<story>/manifest.json` file already contains all the data needed:
- `timestamp_seconds` — when each segment plays
- `image_path` — the image file to show
- `text` — narration text (for subtitles or TTS)

## API Keys

Keys are loaded from a `.env` file (gitignored; see `.env.example`). Copy the
template and fill it in:

```bash
cp .env.example .env
```

- **FAL_KEY** — image generation. Format: `app-id:secret` (FAL dashboard → API Keys).
- **OPENROUTER_API_KEY** — LLM scene-prompt generation (https://openrouter.ai/keys).
  The model is configured via `prompt_builder.model` in `config.yaml` (any model
  id OpenRouter serves). Without a key, the pipeline falls back to simple
  deterministic prompts so `--skip-generate` previews still work, but scene
  quality will be much lower.

Keys may also be exported as regular environment variables if you prefer.