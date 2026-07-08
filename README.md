# Momentary Content - AI Video Generation System

Automated video generation system that transforms a topic into a complete cartoon stick-figure educational video.

## Overview

This system generates narrated slideshow videos in the style of cartoon stick-figure educational channels. Provide a topic, and the system handles script writing, image generation, voice narration, and video assembly automatically.

## Quick Start

```bash
# Install dependencies with uv
uv sync

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Generate a video
uv run momentary generate "What Did Ancient Humans Do at Night?"

# Or launch the web UI
uv run streamlit run ui/app.py
```

## CLI Commands

The `momentary` CLI supports individual component testing:

```bash
# Full pipeline (default 2 min video)
uv run momentary generate "Your Topic"

# Specify video duration
uv run momentary generate "Your Topic" -d 5        # 5 minute video
uv run momentary generate "Your Topic" -d 0.5      # 30 second video

# Test script generation only
uv run momentary script "Your Topic"
uv run momentary script "Your Topic" -d 3 -o script.json

# Test image generation only
uv run momentary image "A stick figure in a cave with campfire"

# Test voice generation only
uv run momentary voice "This is a test narration"

# Assemble video from existing temp files
uv run momentary assemble -t "My Video"

# Check system status
uv run momentary status
```

### Video Duration

The system calculates the number of scenes based on target duration:
- Average scene: ~8 seconds
- Minimum: 3 scenes (0.5 min)
- Maximum: 30 scenes (5+ min)
- The LLM adjusts narration length to fit the target duration

## Web UI

Launch the Streamlit interface:

```bash
uv run streamlit run ui/app.py
```

The UI provides tabs for:
- **Full Pipeline** - Generate complete video from topic with duration slider
- **Test Script** - Test OpenRouter script generation
- **Test Image** - Test Fal.ai image generation
- **Test Voice** - Test ElevenLabs voice generation
- **Test Assemble** - Assemble video from existing temp files
- **Status** - Check API keys and generated files

## Architecture

```
Topic → OpenRouter (Script) → Fal.ai (Images) → ElevenLabs (Voice) → MoviePy (Video) → MP4
```

### Pipeline Steps

1. **Script Generation** (OpenRouter) — Generates a structured JSON script with 10 scenes
2. **Image Generation** (Fal.ai) — Creates cartoon stick-figure illustrations
3. **Voice Generation** (ElevenLabs) — Converts narration text to speech
4. **Video Assembly** (MoviePy) — Ken Burns effect + crossfade transitions → MP4

## Image Style

All generated images follow the cartoon stick-figure illustration style:
- Round white head character with big eyes and simple facial expression
- Stick figure body with thin black lines
- Hand-drawn sketchy line art
- Flat colors with minimal shading
- Earthy muted color palette (browns, dark blues, warm oranges)
- Cave or historical settings with dramatic campfire/torch lighting
- 2D animation style, no photorealism

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- API keys for OpenRouter, Fal.ai, and ElevenLabs
- FFmpeg (installed automatically with MoviePy)

## Project Structure

```
momentary-content/
├── pyproject.toml          # uv project configuration
├── src/
│   └── momentary/
│       ├── __init__.py
│       ├── cli.py              # CLI with subcommands
│       ├── config.py           # Configuration and style prompts
│       ├── script_generator.py # OpenRouter script generation
│       ├── image_generator.py  # Fal.ai image generation
│       ├── voice_generator.py  # ElevenLabs voice generation
│       └── video_assembler.py  # MoviePy video assembly
├── ui/
│   └── app.py                  # Streamlit web interface
├── .env.example                # API key template
├── output/                     # Generated videos
└── temp/                       # Intermediate files (images, audio)
```

## Configuration

Edit `.env` or `config.py` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat` | LLM model for script generation |
| `FAL_IMAGE_MODEL` | `fal-ai/flux/schnell` | Image generation model |
| `ELEVENLABS_VOICE_ID` | `21m00Tcm4TlvDq8ikWAM` | ElevenLabs voice ID |
| `NUM_SCENES` | `10` | Number of scenes per video |
| `VIDEO_WIDTH` | `1920` | Output video width |
| `VIDEO_HEIGHT` | `1080` | Output video height |
| `FPS` | `30` | Output video frame rate |
| `TRANSITION_DURATION` | `0.5` | Crossfade duration between scenes |

## Cost Estimate

Approximate cost per video (10 scenes):

| Service | Cost |
|---------|------|
| OpenRouter (script) | ~$0.01 |
| Fal.ai (10 images) | ~$0.03 |
| ElevenLabs (~2 min audio) | ~$0.60 |
| **Total** | **~$0.64/video** |

## Development

```bash
# Run tests
uv run pytest

# Lint code
uv run ruff check src/

# Format code
uv run ruff format src/
```

## License

MIT
