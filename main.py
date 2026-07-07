import sys
import argparse
from script_generator import generate_script
from image_generator import generate_all_images
from voice_generator import generate_all_voices
from video_assembler import assemble_video
from config import OPENROUTER_API_KEY, FAL_KEY, ELEVENLABS_API_KEY


def check_api_keys():
    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not FAL_KEY:
        missing.append("FAL_KEY")
    if not ELEVENLABS_API_KEY:
        missing.append("ELEVENLABS_API_KEY")
    if missing:
        print(f"Error: Missing API keys in .env: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a cartoon stick-figure educational video from a topic."
    )
    parser.add_argument("topic", help="The topic for the video (e.g., 'What Did Ancient Humans Do at Night?')")
    args = parser.parse_args()

    topic = args.topic

    check_api_keys()

    print(f"\n{'='*60}")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    print("[1/4] Generating script with OpenRouter...")
    script = generate_script(topic)
    title = script.get("title", topic)
    scenes = script["scenes"]
    print(f"  Title: {title}")
    print(f"  Scenes: {len(scenes)}\n")

    print("[2/4] Generating images with Fal.ai...")
    image_paths = generate_all_images(scenes)
    print(f"  Generated {len(image_paths)} images\n")

    print("[3/4] Generating voice narration with ElevenLabs...")
    audio_paths = generate_all_voices(scenes)
    print(f"  Generated {len(audio_paths)} audio clips\n")

    print("[4/4] Assembling video with MoviePy...")
    output_path = assemble_video(image_paths, audio_paths, title)

    print(f"\n{'='*60}")
    print(f"  Video complete!")
    print(f"  Output: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
