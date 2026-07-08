# AGENTS.md - AI Agent Guidelines

This document provides instructions for AI agents working on the momentary-content project.

## Project Overview

Automated video generation system that creates cartoon stick-figure educational videos from a topic.

## Tech Stack

- **Language**: Python 3.10+
- **Package Manager**: uv + pyproject.toml
- **Script Generation**: OpenRouter (OpenAI-compatible API)
- **Image Generation**: Fal.ai (FLUX models)
- **Voice Generation**: ElevenLabs TTS
- **Video Assembly**: MoviePy 2.x + Pillow + NumPy
- **CLI**: Typer + Rich
- **UI**: Streamlit

## Project Structure

```
momentary-content/
├── pyproject.toml          # uv project configuration
├── src/
│   └── momentary/
│       ├── __init__.py
│       ├── cli.py              # CLI with subcommands (typer)
│       ├── config.py           # All configuration, API keys, constants
│       ├── script_generator.py # OpenRouter → JSON script
│       ├── image_generator.py  # Fal.ai → PNG images
│       ├── voice_generator.py  # ElevenLabs → MP3 audio
│       └── video_assembler.py  # MoviePy → MP4 video
├── ui/
│   └── app.py                  # Streamlit web interface
├── .env                        # API keys (gitignored)
├── .env.example                # Template
├── output/                     # Final videos
└── temp/                       # Intermediate files
```

## Code Conventions

### Style
- No comments unless explicitly requested
- Use snake_case for functions and variables
- Use UPPER_CASE for constants
- Keep functions focused and single-purpose
- Import order: standard library → third-party → local

### Package Structure
- All code lives in `src/momentary/`
- Use `from momentary.xxx import yyy` for internal imports
- CLI commands in `cli.py` using Typer decorators

### Error Handling
- Let API errors propagate with clear messages
- Use `Path.mkdir(parents=True, exist_ok=True)` for directory creation
- Validate API keys at startup in CLI commands

### Configuration
- All settings in `config.py`
- API keys loaded from `.env` via `python-dotenv`
- Never hardcode API keys
- Placeholder detection: check for "your-key" in values

## CLI Commands

```bash
# Full pipeline
uv run momentary generate "Topic"

# Component testing
uv run momentary script "Topic"
uv run momentary image "Prompt"
uv run momentary voice "Text"
uv run momentary assemble -t "Title"

# Status check
uv run momentary status
```

## Key Design Decisions

### Image Style
All image prompts automatically append `CARTOON_STYLE_PROMPT` from `config.py` to maintain consistent cartoon stick-figure style across all scenes.

### Ken Burns Effect
Random effect per scene: zoom_in, zoom_out, pan_left, or pan_right. Applied via Pillow + NumPy frame-by-frame rendering in MoviePy.

### Audio-Video Sync
Each scene's video duration matches its audio clip duration exactly. Audio is generated first, then video is created to match.

### Transitions
0.5s crossfade between scenes using MoviePy's `crossfadein`/`crossfadeout`.

## Running the Project

```bash
# Install dependencies
uv sync

# Configure API keys
cp .env.example .env
# Edit .env

# Generate a video
uv run momentary generate "Your Topic Here"

# Launch UI
uv run streamlit run ui/app.py
```

## Adding New Features

### New Image Model
Change `FAL_IMAGE_MODEL` in `.env` or `config.py`. Update `image_generator.py` if the API response format differs.

### New Voice
Change `ELEVENLABS_VOICE_ID` in `.env`. Browse voices at ElevenLabs dashboard.

### New LLM
Change `OPENROUTER_MODEL` in `.env`. Any OpenAI-compatible model on OpenRouter works.

### More/Fewer Scenes
Change `NUM_SCENES` in `config.py`.

## Testing

No formal test suite exists. Manual testing via CLI:

```bash
# Test each component separately
uv run momentary script "Test topic"
uv run momentary image "Test prompt"
uv run momentary voice "Test text"
uv run momentary assemble -t "Test"

# Full pipeline
uv run momentary generate "Test topic"
```

Verify:
1. Script generates valid JSON with correct number of scenes
2. Images are 1920x1080 PNG files
3. Audio clips are valid MP3 files
4. Final video plays correctly with audio synced to images

## Dependencies

| Package | Purpose |
|---------|---------|
| `openai` | OpenRouter API client |
| `fal-client` | Fal.ai API client |
| `elevenlabs` | ElevenLabs TTS client |
| `moviepy` | Video editing and assembly |
| `Pillow` | Image processing for Ken Burns |
| `numpy` | Math for zoom/pan calculations |
| `python-dotenv` | Environment variable loading |
| `requests` | HTTP downloads for images |
| `typer` | CLI framework |
| `rich` | Terminal formatting |
| `streamlit` | Web UI framework |
