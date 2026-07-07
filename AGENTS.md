# AGENTS.md - AI Agent Guidelines

This document provides instructions for AI agents working on the momentary-content project.

## Project Overview

Automated video generation system that creates cartoon stick-figure educational videos from a topic.

## Tech Stack

- **Language**: Python 3.12+
- **Script Generation**: OpenRouter (OpenAI-compatible API)
- **Image Generation**: Fal.ai (FLUX models)
- **Voice Generation**: ElevenLabs TTS
- **Video Assembly**: MoviePy + Pillow + NumPy
- **Package Management**: pip + requirements.txt

## Project Structure

```
momentary-content/
├── main.py                 # CLI entry point (argparse)
├── config.py               # All configuration, API keys, constants
├── script_generator.py     # OpenRouter → JSON script
├── image_generator.py      # Fal.ai → PNG images
├── voice_generator.py      # ElevenLabs → MP3 audio
── video_assembler.py      # MoviePy → MP4 video
├── requirements.txt        # Dependencies
├── .env                    # API keys (gitignored)
├── .env.example            # Template
├── output/                 # Final videos
└── temp/                   # Intermediate files
```

## Code Conventions

### Style
- No comments unless explicitly requested
- Use snake_case for functions and variables
- Use UPPER_CASE for constants
- Keep functions focused and single-purpose
- Import order: standard library → third-party → local

### Error Handling
- Let API errors propagate with clear messages
- Use `os.makedirs(..., exist_ok=True)` for directory creation
- Validate API keys at startup in `main.py`

### Configuration
- All settings in `config.py`
- API keys loaded from `.env` via `python-dotenv`
- Never hardcode API keys

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
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env

# Generate a video
python main.py "Your Topic Here"
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

No formal test suite exists. Manual testing:

```bash
python main.py "Test topic"
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
