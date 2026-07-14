import json
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from momentary.config import (
    OPENROUTER_API_KEY,
    FAL_KEY,
    ELEVENLABS_API_KEY,
    RUNS_DIR,
    DEFAULT_DURATION_MINUTES,
    DEFAULT_MOTION,
    DEFAULT_AUDIO_MODE,
    DEFAULT_THEME,
    DEFAULT_IMAGE_DENSITY,
    DEFAULT_RESEARCH,
    DEFAULT_STYLE,
    DEFAULT_STOP_AFTER,
    calculate_scenes,
    create_run_directory,
    save_run_config,
    OPENROUTER_MODELS,
    FAL_IMAGE_MODELS,
    ELEVENLABS_MODELS,
    MOTION_EFFECTS,
    AUDIO_MODES,
    NARRATION_THEMES,
    IMAGE_DENSITY,
    STYLE_PROMPTS,
    STOP_AFTER_STAGES,
)
from momentary.script_generator import generate_script, research_topic
from momentary.image_generator import generate_all_images, generate_image, generate_thumbnail
from momentary.voice_generator import generate_all_voices, generate_voice, generate_single_audio, generate_chunked_audio, split_audio_by_boundaries, regenerate_boundaries
from momentary.video_assembler import assemble_video, assemble_video_with_boundaries, get_audio_duration

app = typer.Typer(
    name="momentary",
    help="AI-powered cartoon stick-figure video generation system.",
    add_completion=False,
)
console = Console()


def _is_placeholder(value: str) -> bool:
    return not value or "your-key" in value or "your-key-here" in value


def check_api_keys(required: list[str] | None = None):
    if required is None:
        required = ["openrouter", "fal", "elevenlabs"]
    missing = []
    if "openrouter" in required and _is_placeholder(OPENROUTER_API_KEY):
        missing.append("OPENROUTER_API_KEY")
    if "fal" in required and _is_placeholder(FAL_KEY):
        missing.append("FAL_KEY")
    if "elevenlabs" in required and _is_placeholder(ELEVENLABS_API_KEY):
        missing.append("ELEVENLABS_API_KEY")
    if missing:
        console.print(f"[red]Error: Missing API keys: {', '.join(missing)}[/red]")
        console.print("Copy .env.example to .env and fill in your real keys.")
        raise typer.Exit(1)


@app.command()
def generate(
    topic: str = typer.Argument(help="The topic for the video"),
    video_idea: str = typer.Option("", "--idea", "-i", help="Optional: specific angle or focus for the video"),
    duration: float = typer.Option(DEFAULT_DURATION_MINUTES, "--duration", "-d", help="Target video duration in minutes"),
    density: str = typer.Option(DEFAULT_IMAGE_DENSITY, "--density", help=f"Image density: {', '.join(IMAGE_DENSITY.keys())}"),
    motion: str = typer.Option(DEFAULT_MOTION, "--motion", "-m", help=f"Motion effect: {', '.join(MOTION_EFFECTS.keys())}"),
    audio_mode: str = typer.Option(DEFAULT_AUDIO_MODE, "--audio-mode", help=f"Audio mode: {', '.join(AUDIO_MODES.keys())}"),
    theme: str = typer.Option(DEFAULT_THEME, "--theme", "-t", help=f"Narration theme: {', '.join(NARRATION_THEMES.keys())}"),
    style: str = typer.Option(DEFAULT_STYLE, "--style", "-s", help=f"Visual style: {', '.join(STYLE_PROMPTS.keys())}"),
    research: bool = typer.Option(DEFAULT_RESEARCH, "--research/--no-research", help="Research topic before writing script"),
    append_style: bool = typer.Option(False, "--append-style/--no-append-style", help="Append style description to image prompts (default: no, LLM incorporates style)"),
    stop_after: str = typer.Option(DEFAULT_STOP_AFTER, "--stop-after", help=f"Stop pipeline after stage: {', '.join(STOP_AFTER_STAGES.keys())}"),
    llm_model: str = typer.Option(None, "--llm-model", help="OpenRouter model (default: from .env)"),
    image_model: str = typer.Option(None, "--image-model", help="Fal.ai image model (default: from .env)"),
    voice_model: str = typer.Option(None, "--voice-model", help="ElevenLabs TTS model (default: from .env)"),
):
    """Generate a complete video from a topic (full pipeline)."""
    check_api_keys()

    num_scenes = calculate_scenes(duration, density)

    console.print(Panel(f"[bold cyan]{topic}[/bold cyan]", title="Topic", border_style="cyan"))
    console.print(f"  Target duration: [bold]{duration} min[/bold] (~{num_scenes} scenes)")
    console.print(f"  Image density: [bold]{density}[/bold]")
    console.print(f"  Theme: [bold]{theme}[/bold]")
    console.print(f"  Style: [bold]{style}[/bold]")
    if video_idea:
        console.print(f"  Video idea: [bold]{video_idea}[/bold]")
    console.print(f"  Motion: [bold]{motion}[/bold]")
    console.print(f"  Audio mode: [bold]{audio_mode}[/bold]")
    console.print(f"  Research: [bold]{'Yes' if research else 'No'}[/bold]")
    console.print(f"  Append style: [bold]{'Yes' if append_style else 'No'}[/bold]")
    if llm_model:
        console.print(f"  LLM Model: [bold]{llm_model}[/bold]")
    if image_model:
        console.print(f"  Image Model: [bold]{image_model}[/bold]")
    if voice_model:
        console.print(f"  Voice Model: [bold]{voice_model}[/bold]")

    run_dir = create_run_directory(topic)
    
    run_config = {
        "topic": topic,
        "video_idea": video_idea,
        "duration": duration,
        "density": density,
        "motion": motion,
        "audio_mode": audio_mode,
        "theme": theme,
        "style": style,
        "research": research,
        "append_style": append_style,
        "stop_after": stop_after,
        "llm_model": llm_model or OPENROUTER_MODEL,
        "image_model": image_model or FAL_IMAGE_MODEL,
        "voice_model": voice_model or ELEVENLABS_MODEL,
    }
    save_run_config(run_dir, run_config)
    
    console.print(f"  Run directory: [bold]{run_dir}[/bold]")
    console.print(f"  Stop after: [bold]{stop_after}[/bold]")

    research_context = ""
    if research:
        console.print("\n[bold][1/5] Researching topic...[/bold]")
        research_context = research_topic(topic, model=llm_model)
        console.print(f"  Research complete ({len(research_context)} chars)")

    console.print(f"\n[bold][{'2' if research else '1'}/5] Generating script...[/bold]")
    target_duration_seconds = duration * 60
    script = generate_script(topic, num_scenes, model=llm_model, theme=theme, research_context=research_context, target_duration_seconds=target_duration_seconds, video_idea=video_idea, style=style, run_dir=run_dir)
    title = script.get("title", topic)
    scenes = script["scenes"]
    console.print(f"  Title: [bold]{title}[/bold]")
    console.print(f"  Scenes: {len(scenes)}")
    total_chars = sum(len(s.get("narration", "")) for s in scenes)
    console.print(f"  Total narration: {total_chars} chars (~{total_chars/15:.0f}s of audio)")

    console.print(f"\n[bold][{'3' if research else '2'}/5] Generating images...[/bold]")
    image_paths = generate_all_images(scenes, model=image_model, style=style, append_style=append_style, run_dir=run_dir)
    console.print(f"  Generated {len(image_paths)} images")

    if "thumbnail_prompt" in script:
        console.print(f"\n[bold]Generating thumbnail...[/bold]")
        thumbnail_path = generate_thumbnail(script["thumbnail_prompt"], thumbnail_text=script.get("thumbnail_text", ""), model=image_model, style=style, append_style=append_style, run_dir=run_dir)
        console.print(f"  Thumbnail: [bold]{thumbnail_path}[/bold]")

    if stop_after == "images":
        console.print(Panel(f"[bold green]Stopped after image generation[/bold green]\nRun directory: [bold]{run_dir}[/bold]", title="Pipeline Stopped", border_style="yellow"))
        return

    console.print(f"\n[bold][{'4' if research else '3'}/5] Generating voice narration...[/bold]")
    try:
        if audio_mode == "Single Audio":
            full_audio_path, timestamp_data = generate_single_audio(scenes, model=voice_model, run_dir=run_dir)
            boundaries = timestamp_data["boundaries"]
            console.print(f"  Generated single audio with {len(boundaries)} scene boundaries")
        elif audio_mode == "Chunked Audio":
            full_audio_path, timestamp_data = generate_chunked_audio(scenes, model=voice_model, run_dir=run_dir)
            boundaries = timestamp_data["boundaries"]
            console.print(f"  Generated chunked audio with {len(boundaries)} scene boundaries")
        else:
            audio_paths = generate_all_voices(scenes, model=voice_model, run_dir=run_dir)
            console.print(f"  Generated {len(audio_paths)} audio clips")
    except Exception as e:
        console.print(f"  [bold red]ERROR:[/bold red] Voice generation failed: {e}")
        raise

    if stop_after == "voice":
        console.print(Panel(f"[bold green]Stopped after voice generation[/bold green]\nRun directory: [bold]{run_dir}[/bold]", title="Pipeline Stopped", border_style="yellow"))
        return

    console.print(f"\n[bold][{'5' if research else '4'}/5] Assembling video...[/bold]")
    if audio_mode in ("Single Audio", "Chunked Audio"):
        output_path = assemble_video_with_boundaries(image_paths, full_audio_path, boundaries, title, motion=motion.lower().replace(" ", "_"), run_dir=run_dir)
    else:
        output_path = assemble_video(image_paths, audio_paths, title, motion=motion.lower().replace(" ", "_"), run_dir=run_dir)

    console.print(Panel(f"[bold green]{output_path}[/bold green]", title="Video Complete!", border_style="green"))


@app.command()
def script(
    topic: str = typer.Argument(help="The topic to generate a script for"),
    video_idea: str = typer.Option("", "--idea", "-i", help="Optional: specific angle or focus for the video"),
    duration: float = typer.Option(DEFAULT_DURATION_MINUTES, "--duration", "-d", help="Target duration in minutes"),
    theme: str = typer.Option(DEFAULT_THEME, "--theme", "-t", help=f"Narration theme: {', '.join(NARRATION_THEMES.keys())}"),
    style: str = typer.Option(DEFAULT_STYLE, "--style", "-s", help=f"Visual style: {', '.join(STYLE_PROMPTS.keys())}"),
    research: bool = typer.Option(DEFAULT_RESEARCH, "--research/--no-research", help="Research topic before writing script"),
    model: str = typer.Option(None, "--model", "-m", help="OpenRouter model (default: from .env)"),
    output: Path = typer.Option(None, "--output", "-o", help="Save script to file"),
):
    """Test script generation only."""
    check_api_keys(["openrouter"])

    num_scenes = calculate_scenes(duration)
    console.print(f"[bold]Generating script for:[/bold] {topic} ({num_scenes} scenes, ~{duration} min)")
    console.print(f"  Theme: [bold]{theme}[/bold]")
    console.print(f"  Style: [bold]{style}[/bold]")
    if video_idea:
        console.print(f"  Video idea: [bold]{video_idea}[/bold]")
    console.print(f"  Research: [bold]{'Yes' if research else 'No'}[/bold]")
    if model:
        console.print(f"  Model: [bold]{model}[/bold]")

    run_dir = create_run_directory(topic)

    research_context = ""
    if research:
        console.print("\n[bold]Researching topic...[/bold]")
        research_context = research_topic(topic, model=model)
        console.print(f"  Research complete ({len(research_context)} chars)")

    target_duration_seconds = duration * 60
    result = generate_script(topic, num_scenes, model=model, theme=theme, research_context=research_context, target_duration_seconds=target_duration_seconds, video_idea=video_idea, style=style, run_dir=run_dir)

    formatted = json.dumps(result, indent=2)
    console.print(Panel(formatted, title="Generated Script", border_style="blue"))
    console.print(f"[green]Script saved to: {run_dir / 'script.json'}[/green]")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            f.write(formatted)
        console.print(f"[green]Also saved to {output}[/green]")


@app.command()
def image(
    prompt: str = typer.Argument(help="Image generation prompt"),
    index: int = typer.Option(0, "--index", "-i", help="Scene index number"),
    model: str = typer.Option(None, "--model", "-m", help="Fal.ai image model (default: from .env)"),
):
    """Test image generation only."""
    check_api_keys(["fal"])

    console.print(f"[bold]Generating image:[/bold] {prompt}")
    if model:
        console.print(f"  Model: [bold]{model}[/bold]")
    path = generate_image(prompt, index, model)
    console.print(f"[green]Image saved: {path}[/green]")


@app.command()
def voice(
    text: str = typer.Argument(help="Text to convert to speech"),
    index: int = typer.Option(0, "--index", "-i", help="Scene index number"),
    model: str = typer.Option(None, "--model", "-m", help="ElevenLabs TTS model (default: from .env)"),
):
    """Test voice generation only."""
    check_api_keys(["elevenlabs"])

    console.print(f"[bold]Generating voice:[/bold] {text[:80]}...")
    if model:
        console.print(f"  Model: [bold]{model}[/bold]")
    path = generate_voice(text, index, model)
    duration = get_audio_duration(path)
    console.print(f"[green]Audio saved: {path} ({duration:.1f}s)[/green]")


@app.command()
def assemble(
    run_dir: Path = typer.Argument(help="Path to run directory"),
):
    """Assemble video from a specific run directory."""
    image_files = sorted((run_dir / "images").glob("scene_*.png"))

    if not image_files:
        console.print(f"[red]No images found in {run_dir / 'images'}[/red]")
        raise typer.Exit(1)

    full_audio_path = run_dir / "audio" / "full_audio.mp3"
    boundaries_path = run_dir / "audio" / "boundaries.json"
    audio_files = sorted((run_dir / "audio").glob("scene_*.mp3"))

    script_path = run_dir / "script.json"
    title = "Untitled"
    if script_path.exists():
        import json
        with open(script_path) as f:
            script = json.load(f)
            title = script.get("title", "Untitled")

    image_paths = [str(p) for p in image_files]

    if full_audio_path.exists() and boundaries_path.exists():
        import json
        with open(boundaries_path) as f:
            boundaries = json.load(f)
        console.print(f"[bold]Assembling {len(image_paths)} scenes with full audio + boundaries...[/bold]")
        output_path = assemble_video_with_boundaries(image_paths, str(full_audio_path), boundaries, title, run_dir=run_dir)
    elif audio_files:
        if len(image_paths) != len(audio_files):
            console.print(f"[yellow]Warning: {len(image_paths)} images but {len(audio_files)} audio files[/yellow]")
        audio_paths = [str(p) for p in audio_files]
        console.print(f"[bold]Assembling video from {len(image_paths)} scenes...[/bold]")
        output_path = assemble_video(image_paths, audio_paths, title, run_dir=run_dir)
    else:
        console.print(f"[red]No audio files found in {run_dir / 'audio'}[/red]")
        raise typer.Exit(1)

    console.print(Panel(f"[bold green]{output_path}[/bold green]", title="Video Complete!", border_style="green"))


@app.command()
def test_split(
    run_dir: Path = typer.Argument(help="Path to run directory with full_audio.mp3"),
    regenerate: bool = typer.Option(False, "--regenerate", help="Regenerate boundaries from audio"),
):
    """Test audio splitting on an existing run."""
    full_audio_path = run_dir / "audio" / "full_audio.mp3"
    
    if not full_audio_path.exists():
        console.print(f"[red]No full_audio.mp3 found in {run_dir / 'audio'}[/red]")
        raise typer.Exit(1)
    
    script_path = run_dir / "script.json"
    if not script_path.exists():
        console.print(f"[red]No script.json found in {run_dir}[/red]")
        raise typer.Exit(1)
    
    import json
    with open(script_path) as f:
        script = json.load(f)
    
    scenes = script.get("scenes", [])
    if not scenes:
        console.print("[red]No scenes found in script.json[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold]Testing audio split for {len(scenes)} scenes...[/bold]")
    console.print(f"  Audio file: {full_audio_path}")
    
    boundaries_path = run_dir / "audio" / "boundaries.json"
    
    if regenerate or not boundaries_path.exists():
        if regenerate:
            console.print(f"[yellow]Regenerating boundaries from audio...[/yellow]")
        else:
            console.print(f"[yellow]No saved boundaries found, regenerating...[/yellow]")
        
        try:
            _, timestamp_data = regenerate_boundaries(run_dir)
            boundaries = timestamp_data["boundaries"]
            console.print(f"[green]Regenerated {len(boundaries)} boundaries[/green]")
        except Exception as e:
            console.print(f"[red]Error regenerating boundaries: {e}[/red]")
            raise typer.Exit(1)
    else:
        with open(boundaries_path) as f:
            boundaries = json.load(f)
        console.print(f"[green]Loaded {len(boundaries)} saved boundaries from boundaries.json[/green]")
    
    try:
        audio_paths = split_audio_by_boundaries(str(full_audio_path), boundaries, run_dir=run_dir)
        console.print(f"[green]Successfully split into {len(audio_paths)} audio clips[/green]")
        for path in audio_paths:
            console.print(f"  - {Path(path).name}")
    except Exception as e:
        console.print(f"[red]Error splitting audio: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check API key configuration and runs."""
    console.print(Panel("API Key Status", border_style="cyan"))

    keys = {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "FAL_KEY": FAL_KEY,
        "ELEVENLABS_API_KEY": ELEVENLABS_API_KEY,
    }
    for name, value in keys.items():
        if _is_placeholder(value):
            status = "[red]Missing / Placeholder[/red]"
        else:
            status = "[green]Set[/green]"
        console.print(f"  {name}: {status}")

    console.print()
    console.print(Panel("Runs", border_style="cyan"))

    if RUNS_DIR.exists():
        runs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()])
        console.print(f"  Total runs: {len(runs)}")
        for run in runs[-5:]:
            script_exists = (run / "script.json").exists()
            img_count = len(list((run / "images").glob("scene_*.png"))) if (run / "images").exists() else 0
            aud_count = len(list((run / "audio").glob("scene_*.mp3"))) if (run / "audio").exists() else 0
            video_exists = (run / "video.mp4").exists()
            console.print(f"  - {run.name}")
            console.print(f"    Script: {'[green]Yes[/green]' if script_exists else '[red]No[/red]'} | Images: {img_count} | Audio: {aud_count} | Video: {'[green]Yes[/green]' if video_exists else '[red]No[/red]'}")
    else:
        console.print("  No runs yet")


if __name__ == "__main__":
    app()
