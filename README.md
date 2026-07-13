# Momentary Content - AI Video Generation System

Automated video generation system that transforms a topic into a complete cartoon stick-figure educational video with narration, thumbnails, and YouTube descriptions.

## Overview

This system generates narrated slideshow videos in the style of cartoon stick-figure educational channels. Provide a topic, and the system handles script writing (with hooks and spoken English), image generation, voice narration, thumbnail creation, and video assembly automatically.

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
# Full pipeline (default 8 min video)
uv run momentary generate "Your Topic"

# Specify video duration
uv run momentary generate "Your Topic" -d 5        # 5 minute video
uv run momentary generate "Your Topic" -d 0.5      # 30 second video

# Custom narration theme
uv run momentary generate "Your Topic" -t "Humorous"
uv run momentary generate "Your Topic" -t "Dramatic"

# Different audio modes
uv run momentary generate "Your Topic" --audio-mode "Single Audio"  # More natural flow
uv run momentary generate "Your Topic" --audio-mode "Chunked Audio" # Handles long texts
uv run momentary generate "Your Topic" --audio-mode "Per Scene"     # Precise sync

# Image density control
uv run momentary generate "Your Topic" --density "More"      # 2x images
uv run momentary generate "Your Topic" --density "Maximum"   # 3x images
uv run momentary generate "Your Topic" --density "Fewer"     # 0.5x images

# Skip research step
uv run momentary generate "Your Topic" --no-research

# Test script generation only
uv run momentary script "Your Topic"
uv run momentary script "Your Topic" -d 3 -o script.json

# Test image generation only
uv run momentary image "A stick figure in a cave with campfire"

# Test voice generation only
uv run momentary voice "This is a test narration"

# Test audio splitting on existing run
uv run momentary test-split runs/001_your_topic_20260708_221500

# Assemble video from a specific run
uv run momentary assemble runs/001_your_topic_20260708_221500

# Check system status
uv run momentary status
```

### Video Duration

The system calculates the number of scenes based on target duration:
- Average scene: ~8 seconds
- Minimum: 3 scenes (0.5 min)
- Maximum: 30 scenes (5+ min)
- The LLM adjusts narration length to fit the target duration

### Run Directory Structure

Each generation creates a permanent run directory with numbered folders:

```
runs/
├── 001_what_did_ancient_humans_do_at_night_20260708_221500/
│   ├── config.json          # All generation settings
│   ├── script.json          # Generated script
│   ├── description.txt      # YouTube description
│   ├── thumbnail.png        # Video thumbnail
│   ├── images/
│   │   ├── scene_000.png
│   │   └── scene_001.png
│   ├── audio/
│   │   ├── scene_000.mp3
│   │   ├── scene_001.mp3
│   │   └── boundaries.json  # Audio split timestamps
│   └── video.mp4            # Final video
```

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
- **Test Split** - Test audio splitting on existing runs
- **Test Assemble** - Assemble video from a specific run
- **Runs** - Browse all runs with scripts, images, audio, and videos
- **Status** - Check API keys and system status

## Architecture

```
Topic → OpenRouter (Script + Description + Thumbnail) → Fal.ai (Images + Thumbnail) → ElevenLabs (Voice) → MoviePy (Video) → MP4
```

### Pipeline Steps

1. **Script Generation** (OpenRouter) — Generates structured JSON script with hook structure, spoken English narration, YouTube description, and thumbnail prompt
2. **Image Generation** (Fal.ai) — Creates cartoon illustrations in selected style (Lazy Doodle default)
3. **Thumbnail Generation** (Fal.ai) — Creates eye-catching thumbnail using same style
4. **Voice Generation** (ElevenLabs) — Converts narration text to speech (Per Scene, Single Audio, or Chunked Audio)
5. **Video Assembly** (MoviePy) — Ken Burns effect + crossfade transitions → MP4

## Image Styles

Available styles (configurable in config.py):

- **Lazy Doodle** (default) — Wobbly imperfect lines, white background, minimal lighting, intentionally sloppy
- **Cartoon Stick Figure** — Hand-drawn cartoon with textured paper background
- **Anime** — Anime illustration with expressive characters
- **Realistic** — Cinematic digital painting with photographic quality
- **Storybook** — Classic children's book illustration with watercolor texture

All styles maintain consistent visual appearance across scenes and include anti-AI keywords to reduce glossy/perfect appearance.

### Style Handling

By default, the LLM incorporates the full style description into each image prompt during script generation. This creates more cohesive, natural prompts.

If you prefer the old behavior, use `--append-style` to append the style description to each image prompt after generation:

```bash
# Default: LLM incorporates style into prompts
uv run momentary generate "Topic"

# Alternative: Append style to prompts
uv run momentary generate "Topic" --append-style
```

## Script Generation Features

The script generator includes:
- **Hook structure** — First 1-2 scenes tease the payoff without revealing it
- **Spoken English** — Conversational tone with contractions, casual transitions
- **YouTube description** — Generated with hook and hashtags
- **Thumbnail prompt** — Eye-catching thumbnail description in same style

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
├── tests/                      # Pytest test suite
│   ├── test_config.py
│   ├── test_script_generator.py
│   ├── test_image_generator.py
│   ├── test_voice_generator.py
│   └── test_video_assembler.py
├── ui/
│   └── app.py                  # Streamlit web interface
├── runs/                       # Permanent run directories
│   └── {run_number}_{topic}_{timestamp}/
│       ├── config.json
│       ├── script.json
│       ├── description.txt
│       ├── thumbnail.png
│       ├── images/
│       ├── audio/
│       └── video.mp4
├── .env.example                # API key template
```

## Configuration

Edit `.env` or `config.py` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat` | LLM model for script generation |
| `FAL_IMAGE_MODEL` | `fal-ai/flux/schnell` | Image generation model |
| `ELEVENLABS_VOICE_ID` | `21m00Tcm4TlvDq8ikWAM` | ElevenLabs voice ID |
| `DEFAULT_STYLE` | `Lazy Doodle` | Default image style |
| `DEFAULT_AUDIO_MODE` | `Single Audio` | Default audio generation mode |
| `VIDEO_WIDTH` | `1920` | Output video width |
| `VIDEO_HEIGHT` | `1080` | Output video height |
| `FPS` | `30` | Output video frame rate |
| `TRANSITION_DURATION` | `0.5` | Crossfade duration between scenes |

## Cost Estimate

Approximate cost per video (10 scenes):

| Service | Cost |
|---------|------|
| OpenRouter (script) | ~$0.01 |
| Fal.ai (10 images + 1 thumbnail) | ~$0.03 |
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
