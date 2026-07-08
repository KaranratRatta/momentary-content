from pathlib import Path
from elevenlabs import ElevenLabs
from momentary.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL


def generate_voice(narration: str, scene_index: int, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None) -> str:
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    audio = client.text_to_speech.convert(
        voice_id=voice_id or ELEVENLABS_VOICE_ID,
        text=narration,
        model_id=model or ELEVENLABS_MODEL,
        output_format="mp3_44100_128",
    )

    if run_dir:
        audio_dir = run_dir / "audio"
    else:
        audio_dir = Path("temp/audio")

    output_path = audio_dir / f"scene_{scene_index:03d}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return str(output_path)


def generate_all_voices(scenes: list, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None) -> list:
    if run_dir:
        audio_dir = run_dir / "audio"
    else:
        audio_dir = Path("temp/audio")

    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_paths = []
    for i, scene in enumerate(scenes):
        print(f"  Generating voice for scene {i + 1}/{len(scenes)}...")
        path = generate_voice(scene["narration"], i, model, voice_id, run_dir)
        audio_paths.append(path)
    return audio_paths
