import json
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from momentary.config import (
    OPENROUTER_API_KEY,
    FAL_KEY,
    ELEVENLABS_API_KEY,
    TEMP_IMAGES_DIR,
    TEMP_AUDIO_DIR,
    OUTPUT_DIR,
    DEFAULT_DURATION_MINUTES,
    calculate_scenes,
    OPENROUTER_MODELS,
    FAL_IMAGE_MODELS,
    ELEVENLABS_MODELS,
)
from momentary.script_generator import generate_script
from momentary.image_generator import generate_all_images, generate_image
from momentary.voice_generator import generate_all_voices, generate_voice
from momentary.video_assembler import assemble_video, get_audio_duration

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
    duration: float = typer.Option(DEFAULT_DURATION_MINUTES, "--duration", "-d", help="Target video duration in minutes"),
    llm_model: str = typer.Option(None, "--llm-model", help="OpenRouter model (default: from .env)"),
    image_model: str = typer.Option(None, "--image-model", help="Fal.ai image model (default: from .env)"),
    voice_model: str = typer.Option(None, "--voice-model", help="ElevenLabs TTS model (default: from .env)"),
):
    """Generate a complete video from a topic (full pipeline)."""
    check_api_keys()

    num_scenes = calculate_scenes(duration)

    console.print(Panel(f"[bold cyan]{topic}[/bold cyan]", title="Topic", border_style="cyan"))
    console.print(f"  Target duration: [bold]{duration} min[/bold] (~{num_scenes} scenes)")
    if llm_model:
        console.print(f"  LLM Model: [bold]{llm_model}[/bold]")
    if image_model:
        console.print(f"  Image Model: [bold]{image_model}[/bold]")
    if voice_model:
        console.print(f"  Voice Model: [bold]{voice_model}[/bold]")

    console.print("\n[bold][1/4] Generating script...[/bold]")
    script = generate_script(topic, num_scenes, model=llm_model)
    title = script.get("title", topic)
    scenes = script["scenes"]
    console.print(f"  Title: [bold]{title}[/bold]")
    console.print(f"  Scenes: {len(scenes)}")

    console.print("\n[bold][2/4] Generating images...[/bold]")
    image_paths = generate_all_images(scenes, model=image_model)
    console.print(f"  Generated {len(image_paths)} images")

    console.print("\n[bold][3/4] Generating voice narration...[/bold]")
    audio_paths = generate_all_voices(scenes, model=voice_model)
    console.print(f"  Generated {len(audio_paths)} audio clips")

    console.print("\n[bold][4/4] Assembling video...[/bold]")
    output_path = assemble_video(image_paths, audio_paths, title)

    console.print(Panel(f"[bold green]{output_path}[/bold green]", title="Video Complete!", border_style="green"))


@app.command()
def script(
    topic: str = typer.Argument(help="The topic to generate a script for"),
    duration: float = typer.Option(DEFAULT_DURATION_MINUTES, "--duration", "-d", help="Target duration in minutes"),
    model: str = typer.Option(None, "--model", "-m", help="OpenRouter model (default: from .env)"),
    output: Path = typer.Option(None, "--output", "-o", help="Save script to file"),
):
    """Test script generation only."""
    check_api_keys(["openrouter"])

    num_scenes = calculate_scenes(duration)
    console.print(f"[bold]Generating script for:[/bold] {topic} ({num_scenes} scenes, ~{duration} min)")
    if model:
        console.print(f"  Model: [bold]{model}[/bold]")
    result = generate_script(topic, num_scenes, model=model)

    formatted = json.dumps(result, indent=2)
    console.print(Panel(formatted, title="Generated Script", border_style="blue"))

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            f.write(formatted)
        console.print(f"[green]Saved to {output}[/green]")


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
    title: str = typer.Option("Untitled", "--title", "-t", help="Video title for filename"),
):
    """Test video assembly from existing temp/images and temp/audio files."""
    image_files = sorted(TEMP_IMAGES_DIR.glob("scene_*.png"))
    audio_files = sorted(TEMP_AUDIO_DIR.glob("scene_*.mp3"))

    if not image_files:
        console.print("[red]No images found in temp/images/[/red]")
        raise typer.Exit(1)
    if not audio_files:
        console.print("[red]No audio files found in temp/audio/[/red]")
        raise typer.Exit(1)

    if len(image_files) != len(audio_files):
        console.print(f"[yellow]Warning: {len(image_files)} images but {len(audio_files)} audio files[/yellow]")

    image_paths = [str(p) for p in image_files]
    audio_paths = [str(p) for p in audio_files]

    console.print(f"[bold]Assembling video from {len(image_paths)} scenes...[/bold]")
    output_path = assemble_video(image_paths, audio_paths, title)
    console.print(Panel(f"[bold green]{output_path}[/bold green]", title="Video Complete!", border_style="green"))


@app.command()
def status():
    """Check API key configuration and temp files."""
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
    console.print(Panel("Temp Files", border_style="cyan"))

    img_count = len(list(TEMP_IMAGES_DIR.glob("scene_*.png"))) if TEMP_IMAGES_DIR.exists() else 0
    aud_count = len(list(TEMP_AUDIO_DIR.glob("scene_*.mp3"))) if TEMP_AUDIO_DIR.exists() else 0
    out_count = len(list(OUTPUT_DIR.glob("*.mp4"))) if OUTPUT_DIR.exists() else 0

    console.print(f"  Images: {img_count}")
    console.print(f"  Audio:  {aud_count}")
    console.print(f"  Videos: {out_count}")


if __name__ == "__main__":
    app()
