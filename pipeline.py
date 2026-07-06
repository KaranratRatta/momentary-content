"""
pipeline.py — Main orchestrator for the Script → Images → (Future) Video pipeline.

Runs the full pipeline:
  1. Parse script → segments
  2. Build prompts from segments + style template
  3. Generate images via FAL API
  4. [Future] Assemble video

Usage:
    python pipeline.py --script scripts/input.txt --style ms_paint
    python pipeline.py --script scripts/input.txt --story my-story --style realistic
    python pipeline.py --script scripts/input.txt --story my-story --style anime --concurrency 4
    python pipeline.py --script scripts/input.txt --style anime --skip-generate  # prompts only
"""

import argparse
import json
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from parser import parse_script
from prompt_builder import build_all_prompts
from llm_client import LLMClient
from generator import generate_images
from video_assembler import assemble_video

# Load API keys from .env (FAL_KEY, OPENROUTER_API_KEY) if present.
load_dotenv()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load YAML config file."""
    return yaml.safe_load(Path(config_path).read_text())


def load_style(style_name: str, config: dict) -> dict:
    """Load a style template by name."""
    style_path = Path(config.get("pipeline", {}).get("style_dir", "styles")) / f"{style_name}.yaml"
    if not style_path.exists():
        # Check if it's in the current directory
        style_path = Path(f"styles/{style_name}.yaml")
    return yaml.safe_load(style_path.read_text())


def run_pipeline(
    script_path: str,
    story_name: str = "untitled",
    style_name: str = "ms_paint",
    concurrency: Optional[int] = None,
    output_dir: Optional[str] = None,
    skip_generate: bool = False,
    skip_video: bool = True,
    config_path: str = "config.yaml",
) -> dict:
    """Run the full pipeline end-to-end."""

    config = load_config(config_path)
    pipeline_cfg = config.get("pipeline", {})
    parser_cfg = config.get("parser", {})
    prompt_cfg = config.get("prompt_builder", {})
    generator_cfg = config.get("generator", {})
    video_cfg = config.get("video", {})

    style_config = load_style(style_name, config)
    base_output = output_dir or pipeline_cfg.get("output_dir", "./output")
    output_dir = str(Path(base_output) / story_name)
    concurrency = concurrency or pipeline_cfg.get("concurrency", 8)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║   Script → Image Pipeline                        ║")
    print(f"║   Story: {story_name:<33} ║")
    print(f"║   Style: {style_name:<34} ║")
    print(f"║   Script: {Path(script_path).name:<33} ║")
    print(f"╚══════════════════════════════════════════════════╝")

    # ── Stage 1: Parse ─────────────────────────────────────────────────────
    print(f"\n📖 Stage 1: Parsing script...")
    segments = parse_script(script_path, timestamp_pattern=parser_cfg.get("timestamp_pattern", r"(\d{1,2}:\d{2}(?::\d{2})?)"))
    if not segments:
        print("✗ No timestamps found in the script. Check the format.")
        return {"segments": [], "status": "error: no timestamps"}

    print(f"   Found {len(segments)} timestamped segments")

    # Save intermediate
    seg_path = Path(output_dir) / "segments.json"
    seg_path.write_text(json.dumps([{k: v for k, v in s.items() if k != "prompt"} for s in segments], indent=2))
    print(f"   Saved: {seg_path}")

    # ── Stage 2: Build prompts ─────────────────────────────────────────────
    print(f"\n✏️  Stage 2: Building prompts...")
    llm = LLMClient.from_config(prompt_cfg)
    if llm.is_available():
        print(f"   🤖 LLM: OpenRouter / {prompt_cfg.get('model', 'default')}")

    bible_path = str(Path(output_dir) / "story_bible.json")
    segments = build_all_prompts(
        segments,
        style_config,
        llm=llm,
        concurrency=prompt_cfg.get("concurrency", 8),
        bible_path=bible_path if prompt_cfg.get("build_bible", True) else None,
    )

    prompts_path = Path(output_dir) / "prompts.json"
    prompts_path.write_text(json.dumps(segments, indent=2))
    print(f"   Saved: {prompts_path}")

    if skip_generate:
        print(f"\n⏭  Skipping image generation (--skip-generate)")
        return {"segments": segments, "status": "prompts_only"}

    # ── Stage 3: Generate images ───────────────────────────────────────────
    print(f"\n🎨 Stage 3: Generating images...")
    gen_params = {
        "image_size": style_config.get("image_size", generator_cfg.get("image_size", "landscape_16_9")),
        "num_inference_steps": style_config.get("num_inference_steps", generator_cfg.get("num_inference_steps", 4)),
        "sync_mode": generator_cfg.get("sync_mode", "sync"),
    }

    segments = generate_images(
        segments=segments,
        output_dir=output_dir,
        model=pipeline_cfg.get("model", "fal-ai/flux/schnell"),
        concurrency=concurrency,
        params=gen_params,
    )

    # ── Stage 4: Video [Future] ────────────────────────────────────────────
    if not skip_video:
        print(f"\n🎬 Stage 4: Assembling video...")
        manifest_path = Path(output_dir) / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            assemble_video(
                manifest=manifest,
                output_path=str(Path(output_dir) / "video" / "final.mp4"),
                fps=video_cfg.get("fps", 30),
                transition=video_cfg.get("transition", "fade"),
                transition_duration=video_cfg.get("transition_duration", 0.3),
            )
        else:
            print("   ⚠ No manifest found. Skipping video assembly.")
    else:
        print(f"\n⏭  Stage 4: Video assembly skipped (not yet implemented)")

    print(f"\n🎉 Pipeline complete! Output in: {output_dir}/")
    return {"segments": segments, "status": "complete"}


# ─── CLI entry point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script → Image → Video pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py --script scripts/input.txt
  python pipeline.py --script scripts/input.txt --style realistic
  python pipeline.py --script scripts/input.txt --style ms_paint --concurrency 4
  python pipeline.py --script scripts/input.txt --style anime --skip-generate
        """,
    )
    parser.add_argument("--script", required=True, help="Path to script file with timestamps")
    parser.add_argument("--story", default="untitled", help="Story name (creates output/<story>/ folder)")
    parser.add_argument("--style", default="ms_paint", help="Style template name (ms_paint, realistic, anime)")
    parser.add_argument("--concurrency", type=int, default=None, help="Parallel image generations")
    parser.add_argument("--output-dir", default=None, help="Base output directory (default: ./output)")
    parser.add_argument("--skip-generate", action="store_true", help="Only build prompts, skip image gen")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")

    args = parser.parse_args()
    run_pipeline(
        script_path=args.script,
        story_name=args.story,
        style_name=args.style,
        concurrency=args.concurrency,
        output_dir=args.output_dir,
        skip_generate=args.skip_generate,
        config_path=args.config,
    )