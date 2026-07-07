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

Convert a timestamped script into a sequence of AI-generated images — one per
timestamp — using [fal.ai](https://fal.ai) Krea 2 Turbo. A vision LLM reviews
every image and automatically refines + regenerates ones that don't meet the
quality bar.

Each story gets its own folder. The visual style is fully configurable.
Video assembly is ready to plug in when you need it.

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
python pipeline.py --script scripts/input.txt --story puppy-duck --style storybook

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
python pipeline.py --script scripts/input.txt --story puppy-duck --style storybook
```

**Output** (`output/puppy-duck/`):
```
output/puppy-duck/
├── segments.json          # Parsed timestamps + text
├── prompts.json           # Full prompts sent to the API
├── story_bible.json       # Character & visual bible
├── manifest.json          # Timestamp → image file mapping
├── review_report.json     # Review scores and feedback
├── images/
│   ├── 000_00-00-00.png   # puppy alone, sad
│   ├── 001_00-00-02.png   # duck appears, puppy shivering
│   ├── 002_00-00-04.png   # duck offers help
│   └── 003_00-00-06.png   # puppy on duck's back, comforted
└── video/                 # [Future]
    └── final.mp4
```

---

## How It Works

The pipeline runs in 4 stages (with a review loop between 3 and 4):

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. Parse    │ →  │ 2. Build     │ →  │ 3. Generate  │ →  │ 3.5 Review   │
│   script     │    │   prompts    │    │   images     │    │   + refine   │
│  (timestamps)│    │  (LLM +      │    │  (FAL API)   │    │  (vision LLM)│
│              │    │   style)     │    │              │    │              │
└─────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                  │
                                   score < threshold              │
                              ┌───────────────────────────────────┘
                              │  refine prompt → regenerate (max 2 retries)
                              ▼
                       ┌──────────────┐
                       │ 4. Assemble  │
                       │   video      │
                       │  [Future]    │
                       └──────────────┘
```

| Stage | File | What it does |
|-------|------|-------------|
| 1 | `parser.py` | Extracts timestamps and text from the script |
| 2 | `prompt_builder.py` | Uses an LLM (via OpenRouter) to write a visual depiction of each scene — a story bible keeps characters consistent, then per-scene prompts are generated in parallel with cinematic direction (composition, camera, mood, lighting) |
| 3 | `generator.py` | Calls `fal-ai/krea-2/turbo` in parallel for all prompts, downloads PNG images |
| 3.5 | `reviewer.py` | Vision LLM scores each image (1-5) on quality, relevance, composition, engagement. Low-scoring images get their prompt refined and are regenerated (up to 2 retries) |
| 4 | `video_assembler.py` | [Not yet implemented] Stitches images + TTS audio into a video |

The prompt builder writes a real **visual depiction** of each moment — camera
angle, composition, mood, lighting, character expression, environment — not just
the narration text. A one-call **story bible** locks each character's appearance
so they stay identical across long videos (~100 scenes). Each prompt bakes in
the chosen visual style.

The **reviewer** uses a vision-capable LLM to actually look at each generated
image and score it on visual quality, story relevance, character consistency,
composition, and engagement. Images below the threshold get their prompt refined
with specific feedback and are regenerated.

> No `OPENROUTER_API_KEY`? The pipeline falls back to simple deterministic
> prompts so `--skip-generate` previews still work — scene quality will be much
> lower without the LLM.

---

## Usage

### Basic

```bash
# Every story gets its own folder under output/
python pipeline.py --script scripts/my-script.txt --story my-story
```

### Switch visual styles

```bash
# Warm watercolor storybook (default)
python pipeline.py --script scripts/input.txt --story demo --style storybook

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
python pipeline.py --script scripts/dog.txt --story dog-rescue --style storybook
python pipeline.py --script scripts/space.txt --story space-odyssey --style realistic

# Output:
# output/cat-adventure/images/
# output/dog-rescue/images/
# output/space-odyssey/images/
```

### Review control

```bash
# Skip the review stage entirely
python pipeline.py --script scripts/input.txt --story demo --skip-review

# Stricter review (higher minimum score, more retries)
python pipeline.py --script scripts/input.txt --story demo --min-score 4 --max-retries 3
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
| `storybook` | Warm watercolor storybook illustrations, soft lighting, cozy atmosphere (default) |
| `ms_paint` | Stick figures, thick wobbly black outlines, flat colors, MS Paint amateur look |
| `realistic` | Photorealistic, cinematic lighting, detailed textures, 8K quality |
| `anime` | Cel-shaded 2D anime style, large eyes, vibrant colors |

### Create a custom style

```yaml
# styles/pixel_art.yaml
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
  style: "storybook"                 # Default style
  model: "fal-ai/krea-2/turbo"       # FAL model
  concurrency: 8                     # Parallel image generations
  output_dir: "./output"             # Base output directory

prompt_builder:                      # LLM scene-prompt generation
  model: "z-ai/glm-5.2"             # any OpenRouter model id
  temperature: 0.8                   # higher = more creative depictions
  concurrency: 8                     # parallel LLM calls for scene prompts
  build_bible: true                  # build a character/visual bible first

generator:
  image_size: "landscape_16_9"       # Aspect ratio (16:9 for YouTube)
  output_format: "png"               # Image format
  enable_prompt_expansion: true      # krea-2/turbo: LLM expands prompts

reviewer:
  min_score: 3                       # Minimum review score to pass (1-5)
  max_retries: 2                     # Max regeneration attempts per image
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
    ├── review_report.json    # Review scores and feedback
    ├── images/
    │   ├── 000_00-00-00.png
    │   ├── 001_00-00-05.png
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
    "image_path": "output/story/images/000_00-00-00.png",
    "image_url": "https://..."
  },
  ...
]
```

When you add video assembly, the video assembler reads this file to know which
image to show at which time.

---

## Running Individual Stages

```bash
# Stage 1: Parse only
python parser.py scripts/input.txt > output/story/segments.json

# Stage 2: Build prompts from existing segments (needs OPENROUTER_API_KEY)
python prompt_builder.py output/story/segments.json styles/storybook.yaml > output/story/prompts.json

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
- **OpenRouter** (`OPENROUTER_API_KEY`) — required for LLM scene prompts and
  the vision reviewer. Without it, the pipeline falls back to simple
  deterministic prompts, so previews still work but scene quality drops.

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
├── generator.py             # Stage 3: prompts → images (FAL API)
├── reviewer.py              # Stage 3.5: vision LLM review + refinement
├── video_assembler.py       # Stage 4: [Future] video
├── config.yaml              # Main configuration
├── requirements.txt
├── .env.example             # API key template (copy to .env)
├── README.md
├── CLAUDE.md                # Claude Code project docs
├── styles/
│   ├── storybook.yaml       # Warm watercolor (default)
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
        ├── review_report.json
        ├── images/
        └── video/           # [Future]
```
