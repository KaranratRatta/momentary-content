import base64
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


def generate_single_audio(scenes: list, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None) -> tuple[str, dict]:
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    full_narration = " ".join(scene["narration"] for scene in scenes)

    print(f"  Generating single audio for {len(scenes)} scenes...")
    print(f"  Total narration length: {len(full_narration)} characters")
    
    try:
        result = client.text_to_speech.convert_with_timestamps(
            voice_id=voice_id or ELEVENLABS_VOICE_ID,
            text=full_narration,
            model_id=model or ELEVENLABS_MODEL,
            output_format="mp3_44100_128",
        )
        print(f"  API call completed, processing audio data...")
    except Exception as e:
        print(f"  ERROR: ElevenLabs API call failed: {e}")
        raise

    try:
        audio_data = base64.b64decode(result.audio_base_64)
        print(f"  Audio data decoded: {len(audio_data)} bytes")
    except Exception as e:
        print(f"  ERROR: Failed to decode audio data: {e}")
        raise

    if run_dir:
        audio_dir = run_dir / "audio"
    else:
        audio_dir = Path("temp/audio")

    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / "full_audio.mp3"
    with open(output_path, "wb") as f:
        f.write(audio_data)
    print(f"  Saved full audio to: {output_path}")

    alignment = result.alignment
    scene_boundaries = []

    if alignment and alignment.characters:
        print(f"  Processing {len(alignment.characters)} character timestamps...")
        characters = alignment.characters
        start_times = alignment.character_start_times_seconds
        end_times = alignment.character_end_times_seconds

        full_narration_chars = list(full_narration)
        char_index = 0

        for i, scene in enumerate(scenes):
            narration = scene["narration"]
            scene_start = None
            scene_end = None

            narration_chars = list(narration)
            narration_pos = 0

            while char_index < len(characters) and narration_pos < len(narration_chars):
                if characters[char_index].lower() == narration_chars[narration_pos].lower():
                    if scene_start is None:
                        scene_start = start_times[char_index]
                    narration_pos += 1
                    if narration_pos >= len(narration_chars):
                        scene_end = end_times[char_index]
                char_index += 1

            if scene_start is None:
                scene_start = start_times[0] if start_times else 0.0
            if scene_end is None:
                if i + 1 < len(scenes):
                    scene_end = scene_boundaries[i + 1]["start"] if scene_boundaries else end_times[-1] if end_times else 10.0
                else:
                    scene_end = end_times[-1] if end_times else 10.0

            scene_boundaries.append({
                "scene_index": i,
                "start": scene_start,
                "end": scene_end,
            })
        print(f"  Created {len(scene_boundaries)} scene boundaries")
    else:
        print(f"  WARNING: No alignment data received, using fallback boundaries")
        for i in range(len(scenes)):
            scene_boundaries.append({
                "scene_index": i,
                "start": i * 5.0,
                "end": (i + 1) * 5.0,
            })

    print(f"  Audio generation complete")
    return str(output_path), {"boundaries": scene_boundaries}


def split_audio_by_boundaries(full_audio_path: str, boundaries: list, run_dir: Path | None = None) -> list:
    from pydub import AudioSegment

    audio = AudioSegment.from_file(full_audio_path)

    if run_dir:
        audio_dir = run_dir / "audio"
    else:
        audio_dir = Path("temp/audio")

    audio_dir.mkdir(parents=True, exist_ok=True)

    split_paths = []
    for boundary in boundaries:
        scene_index = boundary["scene_index"]
        start_ms = int(boundary["start"] * 1000)
        end_ms = int(boundary["end"] * 1000)

        segment = audio[start_ms:end_ms]
        output_path = audio_dir / f"scene_{scene_index:03d}.mp3"
        segment.export(str(output_path), format="mp3")
        split_paths.append(str(output_path))

    return split_paths
