# Agents Configuration

## Available Agents

### `pipeline-agent`
The pipeline agent can run the full script-to-image workflow:
1. Parse a timestamped script
2. Build image prompts with automatic emotion/stage detection
3. Generate images via FAL API
4. (Future) Assemble video

**Invoke:** `python pipeline.py --script <path> --style <name>`

### `style-creator`
Creates new visual style templates for the pipeline. A style template defines:
- `base_prompt` — the core visual description
- `character_rules` — how characters are drawn
- `image_size` — aspect ratio
- `num_inference_steps` — quality/speed tradeoff

**Location:** Create new files in `styles/` directory.

## Configuration Points

| File | Purpose |
|------|---------|
| `config.yaml` | Pipeline settings (model, concurrency, output dir) |
| `styles/*.yaml` | Visual style templates |
| `CLAUDE.md` | Full project documentation |

## Required Environment
- `FAL_KEY` — API key for fal.ai image generation

## Known Models (FAL)
- `fal-ai/flux/schnell` — Fast, good for simple styles
- `fal-ai/flux-dev` — Higher quality, slower
- `fal-ai/flux-realism` — Best for realistic/realistic style