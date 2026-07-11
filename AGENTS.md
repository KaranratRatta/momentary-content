# AGENTS.md - AI Agent Guidelines

This document provides instructions for AI agents working on the momentary-content project.

## Important Rules

- **Do NOT push code to git.** The user will push code themselves. Only commit locally if asked.
- **Always update both UI and CLI together.** When adding a new parameter, option, or feature, you MUST update both `src/momentary/cli.py` AND `ui/app.py`. The CLI uses Typer and the UI uses Streamlit — they are separate entry points that call the same underlying functions. Forgetting to update one of them causes bugs where the UI passes `None` for parameters the CLI correctly passes. Always check both files when making changes.

## Project Overview

Automated video generation system that creates educational videos from a topic. Features research-before-writing, multiple narration themes, and improved visual style prompts that reduce AI-generated appearance.

## Tech Stack

- **Language**: Python 3.10+
- **Package Manager**: uv + pyproject.toml
- **Script Generation**: OpenRouter (OpenAI-compatible API)
- **Image Generation**: Fal.ai (FLUX models)
- **Voice Generation**: ElevenLabs TTS (per-scene or single audio with timestamps)
- **Video Assembly**: MoviePy 2.x + Pillow + NumPy
- **Audio Splitting**: pydub + FFmpeg
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
├── runs/                       # Permanent run directories
│   ── topic_timestamp/
│       ├── script.json
│       ├── images/
│       ├── audio/
│       └── video.mp4
├── .env                        # API keys (gitignored)
── .env.example                # Template
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
# Full pipeline (default 2 min, with research)
uv run momentary generate "Topic"

# Custom duration
uv run momentary generate "Topic" -d 5        # 5 minute video
uv run momentary generate "Topic" -d 0.5      # 30 second video

# Narration theme
uv run momentary generate "Topic" -t "Humorous"
uv run momentary generate "Topic" -t "Dramatic"

# Skip research step
uv run momentary generate "Topic" --no-research

# Audio mode (per-scene or single audio)
uv run momentary generate "Topic" --audio-mode "Single Audio"  # More natural flow
uv run momentary generate "Topic" --audio-mode "Per Scene"

# Image density (control number of images)
uv run momentary generate "Topic" --density "More"      # 2x images
uv run momentary generate "Topic" --density "Maximum"   # 3x images
uv run momentary generate "Topic" --density "Fewer"     # 0.5x images

# Component testing
uv run momentary script "Topic" -d 3 -t "Educational"
uv run momentary image "Prompt"
uv run momentary voice "Text"

# Assemble from a specific run
uv run momentary assemble runs/topic_timestamp

# Status check
uv run momentary status
```

### Duration-Based Generation

The system calculates scenes from target duration:
- `scenes = (duration_seconds / 8) * density_multiplier`
- Clamped between 3 and 30 scenes
- LLM adjusts narration to fit target length

### Image Density

Control the number of images generated:
- **Fewer** (0.5x): Half the normal image count, each shown longer
- **Normal** (1.0x): Standard image count
- **More** (2.0x): Double the images, faster transitions
- **Maximum** (3.0x): Triple the images, very dynamic

### Narration Themes

- **Educational** (default): Informative, clear explanations with interesting facts
- **Humorous**: Witty, casual conversational tone with jokes
- **Dramatic**: Intense, cinematic storytelling with suspense
- **Documentary**: Authoritative narrator, serious and factual
- **Storytelling**: Narrative-driven, like telling a friend a story
- **Mysterious**: Intriguing, building curiosity about the unknown

### Research Step

By default, the system researches the topic before writing the script. This provides the LLM with accurate facts and interesting angles. Disable with `--no-research`.

### Audio Modes

- **Per Scene**: Generates separate audio clip for each scene. Precise sync but may sound disjointed.
- **Single Audio** (default): Generates one continuous audio track using ElevenLabs timestamps, then splits at scene boundaries. More natural flow with better voice continuity.

## Key Design Decisions

### Image Style
All image prompts automatically append a style-specific prompt from `config.py` to maintain consistent visual style. Style prompts include:
- Anti-AI keywords to reduce glossy/perfect AI appearance
- Texture and imperfection guidance for hand-drawn feel
- Specific guidance that animals are drawn with detail (not stick figures)
- Human characters remain simple stick figures

Available styles: Cartoon Stick Figure, Anime, Realistic, Storybook

### Ken Burns Effect
Random effect per scene: zoom_in, zoom_out, pan_left, pan_right, pan_up, pan_down, or static. Applied via Pillow + NumPy frame-by-frame rendering in MoviePy.

### Audio-Video Sync
Each scene's video duration matches its audio clip duration exactly. Audio is generated first, then video is created to match.

### Single Audio Mode
Uses ElevenLabs `convert_with_timestamps` API to get character-level timing data. The full narration is generated as one audio file, then split at scene boundaries using the timestamp alignment data.

### Research Step
Before script generation, the system researches the topic to gather facts and interesting angles. This research is passed to the script generator as context, resulting in more accurate and engaging content.

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
uv run momentary assemble runs/test_topic_timestamp

# Full pipeline
uv run momentary generate "Test topic"
```

Verify:
1. Script generates valid JSON with correct number of scenes and saves to `runs/`
2. Images are 1920x1080 PNG files in `runs/{topic}/images/`
3. Audio clips are valid MP3 files in `runs/{topic}/audio/`
4. Final video plays correctly with audio synced to images in `runs/{topic}/video.mp4`

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
| `pydub` | Audio splitting for single audio mode |
