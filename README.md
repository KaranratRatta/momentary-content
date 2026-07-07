# Momentary Content - AI Video Generation System

Automated video generation system that transforms a topic into a complete cartoon stick-figure educational video.

## Overview

This system generates narrated slideshow videos in the style of cartoon stick-figure educational channels (like "Zenn" on YouTube). Provide a topic, and the system handles script writing, image generation, voice narration, and video assembly automatically.

## Architecture

```
Topic → OpenRouter (Script) → Fal.ai (Images) → ElevenLabs (Voice) → MoviePy (Video) → MP4
```

### Pipeline Steps

1. **Script Generation** (OpenRouter) — Generates a structured JSON script with 10 scenes, each containing narration text and image prompts
2. **Image Generation** (Fal.ai) — Creates cartoon stick-figure illustrations matching the reference video style
3. **Voice Generation** (ElevenLabs) — Converts narration text to speech audio clips
4. **Video Assembly** (MoviePy) — Applies Ken Burns effect to images, syncs with audio, adds crossfade transitions, exports MP4

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
- API keys for OpenRouter, Fal.ai, and ElevenLabs
- FFmpeg (installed automatically with MoviePy)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/momentary-content.git
   cd momentary-content
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Usage

Generate a video from a topic:

```bash
python main.py "What Did Ancient Humans Do at Night?"
```

The video will be saved to `output/` directory.

## Configuration

Edit `config.py` to customize:

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

## Project Structure

```
momentary-content/
├── main.py                 # CLI entry point
── config.py               # Configuration and style prompts
├── script_generator.py     # OpenRouter script generation
├── image_generator.py      # Fal.ai image generation
├── voice_generator.py      # ElevenLabs voice generation
├── video_assembler.py      # MoviePy video assembly
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── output/                 # Generated videos
└── temp/                   # Intermediate files (images, audio)
```

## Cost Estimate

Approximate cost per video (10 scenes):

| Service | Cost |
|---------|------|
| OpenRouter (script) | ~$0.01 |
| Fal.ai (10 images) | ~$0.03 |
| ElevenLabs (~2 min audio) | ~$0.60 |
| **Total** | **~$0.64/video** |

## License

MIT
