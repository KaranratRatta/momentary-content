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
):
    """Generate a complete video from a topic (full pipeline)."""
    check_api_keys()

    num_scenes = calculate_scenes(duration)

    console.print(Panel(f"[bold cyan]{topic}[/bold cyan]", title="Topic", border_style="cyan"))
    console.print(f"  Target duration: [bold]{duration} min[/bold] (~{num_scenes} scenes)")

    console.print("\n[bold][1/4] Generating script...[/bold]")
    script = generate_script(topic, num_scenes)
    title = script.get("title", topic)
    scenes = script["scenes"]
    console.print(f"  Title: [bold]{title}[/bold]")
    console.print(f"  Scenes: {len(scenes)}")

    console.print("\n[bold][2/4] Generating images...[/bold]")
    image_paths = generate_all_images(scenes)
    console.print(f"  Generated {len(image_paths)} images")

    console.print("\n[bold][3/4] Generating voice narration...[/bold]")
    audio_paths = generate_all_voices(scenes)
    console.print(f"  Generated {len(audio_paths)} audio clips")

    console.print("\n[bold][4/4] Assembling video...[/bold]")
    output_path = assemble_video(image_paths, audio_paths, title)

    console.print(Panel(f"[bold green]{output_path}[/bold green]", title="Video Complete!", border_style="green"))


@app.command()
def script(
    topic: str = typer.Argument(help="The topic to generate a script for"),
    duration: float = typer.Option(DEFAULT_DURATION_MINUTES, "--duration", "-d", help="Target duration in minutes"),
    output: Path = typer.Option(None, "--output", "-o", help="Save script to file"),
):
    """Test script generation only."""
    check_api_keys(["openrouter"])

    num_scenes = calculate_scenes(duration)
    console.print(f"[bold]Generating script for:[/bold] {topic} ({num_scenes} scenes, ~{duration} min)")
    result = generate_script(topic, num_scenes)

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
):
    """Test image generation only."""
    check_api_keys(["fal"])

    console.print(f"[bold]Generating image:[/bold] {prompt}")
    path = generate_image(prompt, index)
    console.print(f"[green]Image saved: {path}[/green]")


@app.command()
def voice(
    text: str = typer.Argument(help="Text to convert to speech"),
    index: int = typer.Option(0, "--index", "-i", help="Scene index number"),
):
    """Test voice generation only."""
    check_api_keys(["elevenlabs"])

    console.print(f"[bold]Generating voice:[/bold] {text[:80]}...")
    path = generate_voice(text, index)
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
