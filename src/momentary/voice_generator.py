import base64
import json
import re
from pathlib import Path
from momentary.config import (
    ELEVENLABS_API_KEY, 
    ELEVENLABS_VOICE_ID, 
    ELEVENLABS_MODEL,
    get_audio_dir,
    get_elevenlabs_client,
)


def _match_scenes_to_timestamps(
    scenes: list,
    characters: list,
    start_times: list,
    end_times: list
) -> list:
    """Match scene narrations to character-level timestamps to find boundaries.
    
    Args:
        scenes: List of scene dicts with "narration" key
        characters: List of characters from alignment
        start_times: List of start times for each character
        end_times: List of end times for each character
    
    Returns:
        List of boundary dicts with "scene_index", "start", "end"
    """
    scene_boundaries = []
    char_index = 0
    
    for i, scene in enumerate(scenes):
        narration = scene["narration"]
        scene_start = None
        scene_end = None
        
        narration_chars = list(narration)
        narration_pos = 0
        
        while char_index < len(characters) and narration_pos < len(narration_chars):
            if char_index < len(start_times) and char_index < len(end_times):
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
    
    for i in range(len(scene_boundaries) - 1):
        scene_boundaries[i]["end"] = scene_boundaries[i + 1]["start"]
    
    if scene_boundaries:
        scene_boundaries[-1]["end"] = end_times[-1] if end_times else 10.0
    
    return scene_boundaries


def _create_fallback_boundaries(num_scenes: int) -> list:
    """Create fallback boundaries when alignment data is unavailable."""
    return [
        {
            "scene_index": i,
            "start": i * 5.0,
            "end": (i + 1) * 5.0,
        }
        for i in range(num_scenes)
    ]


def _split_text_into_chunks(text: str, target_words: int = 175) -> list[str]:
    if not text or not text.strip():
        return []
    
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        sentence_word_count = len(sentence.split())
        
        if current_word_count + sentence_word_count > target_words and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = sentence_word_count
        else:
            current_chunk.append(sentence)
            current_word_count += sentence_word_count
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def generate_voice(narration: str, scene_index: int, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None) -> str:
    client = get_elevenlabs_client()

    audio = client.text_to_speech.convert(
        voice_id=voice_id or ELEVENLABS_VOICE_ID,
        text=narration,
        model_id=model or ELEVENLABS_MODEL,
        output_format="mp3_44100_128",
    )

    audio_dir = get_audio_dir(run_dir)

    output_path = audio_dir / f"scene_{scene_index:03d}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return str(output_path)


def generate_all_voices(scenes: list, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None) -> list:
    audio_dir = get_audio_dir(run_dir)

    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_paths = []
    for i, scene in enumerate(scenes):
        print(f"  Generating voice for scene {i + 1}/{len(scenes)}...")
        path = generate_voice(scene["narration"], i, model, voice_id, run_dir)
        audio_paths.append(path)
    return audio_paths


def generate_single_audio(scenes: list, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None) -> tuple[str, dict]:
    client = get_elevenlabs_client()

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

    audio_dir = get_audio_dir(run_dir)

    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / "full_audio.mp3"
    with open(output_path, "wb") as f:
        f.write(audio_data)
    print(f"  Saved full audio to: {output_path}")

    alignment = result.alignment
    scene_boundaries = []

    if alignment and alignment.characters:
        print(f"  Processing {len(alignment.characters)} character timestamps...")
        scene_boundaries = _match_scenes_to_timestamps(
            scenes,
            alignment.characters,
            alignment.character_start_times_seconds,
            alignment.character_end_times_seconds
        )
        print(f"  Created {len(scene_boundaries)} scene boundaries")
    else:
        print(f"  WARNING: No alignment data received, using fallback boundaries")
        scene_boundaries = _create_fallback_boundaries(len(scenes))

    if run_dir:
        boundaries_path = run_dir / "audio" / "boundaries.json"
        with open(boundaries_path, "w") as f:
            json.dump(scene_boundaries, f, indent=2)
        print(f"  Saved boundaries to: {boundaries_path}")

    print(f"  Audio generation complete")
    return str(output_path), {"boundaries": scene_boundaries}


def generate_chunked_audio(scenes: list, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None, chunk_words: int = 175) -> tuple[str, dict]:
    from pydub import AudioSegment
    import io
    
    client = get_elevenlabs_client()
    full_narration = " ".join(scene["narration"] for scene in scenes)
    chunks = _split_text_into_chunks(full_narration, chunk_words)
    
    if not chunks:
        print(f"  WARNING: No narration text to generate audio for")
        return "", {"boundaries": [{"scene_index": i, "start": i * 5.0, "end": (i + 1) * 5.0} for i in range(len(scenes))]}
    
    print(f"  Generating chunked audio: {len(chunks)} chunks (~{chunk_words} words each)")
    print(f"  Total narration length: {len(full_narration)} characters")
    
    audio_dir = get_audio_dir(run_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    chunk_audio_files = []
    all_characters = []
    all_start_times = []
    all_end_times = []
    time_offset = 0.0
    
    for i, chunk in enumerate(chunks):
        print(f"    Processing chunk {i + 1}/{len(chunks)} ({len(chunk.split())} words)...")
        
        try:
            result = client.text_to_speech.convert_with_timestamps(
                voice_id=voice_id or ELEVENLABS_VOICE_ID,
                text=chunk,
                model_id=model or ELEVENLABS_MODEL,
                output_format="mp3_44100_128",
            )
            
            audio_data = base64.b64decode(result.audio_base_64)
            chunk_path = audio_dir / f"chunk_{i:03d}.mp3"
            with open(chunk_path, "wb") as f:
                f.write(audio_data)
            chunk_audio_files.append(chunk_path)
            
            if result.alignment and result.alignment.characters:
                for char, start, end in zip(
                    result.alignment.characters,
                    result.alignment.character_start_times_seconds,
                    result.alignment.character_end_times_seconds
                ):
                    all_characters.append(char)
                    all_start_times.append(start + time_offset)
                    all_end_times.append(end + time_offset)
                
                if result.alignment.character_end_times_seconds:
                    chunk_duration = max(result.alignment.character_end_times_seconds)
                    time_offset += chunk_duration + 0.1
                    print(f"      Chunk duration: {chunk_duration:.2f}s")
            
        except Exception as e:
            print(f"      ERROR on chunk {i + 1}: {e}")
            raise
    
    print(f"  Combining {len(chunk_audio_files)} audio chunks...")
    combined_audio = AudioSegment.empty()
    for chunk_path in chunk_audio_files:
        chunk_segment = AudioSegment.from_file(chunk_path)
        combined_audio += chunk_segment
    
    output_path = audio_dir / "full_audio.mp3"
    combined_audio.export(str(output_path), format="mp3")
    print(f"  Saved combined audio to: {output_path}")
    
    for chunk_path in chunk_audio_files:
        chunk_path.unlink()
    
    scene_boundaries = []
    if all_characters:
        print(f"  Processing {len(all_characters)} character timestamps...")
        scene_boundaries = _match_scenes_to_timestamps(
            scenes,
            all_characters,
            all_start_times,
            all_end_times
        )
        print(f"  Created {len(scene_boundaries)} scene boundaries")
    else:
        print(f"  WARNING: No alignment data received, using fallback boundaries")
        scene_boundaries = _create_fallback_boundaries(len(scenes))
    
    if run_dir:
        boundaries_path = run_dir / "audio" / "boundaries.json"
        with open(boundaries_path, "w") as f:
            json.dump(scene_boundaries, f, indent=2)
        print(f"  Saved boundaries to: {boundaries_path}")

    print(f"  Chunked audio generation complete")
    return str(output_path), {"boundaries": scene_boundaries}


def split_audio_by_boundaries(full_audio_path: str, boundaries: list, run_dir: Path | None = None) -> list:
    from pydub import AudioSegment

    print(f"  Splitting audio by boundaries...")
    print(f"  Loading audio from: {full_audio_path}")
    audio = AudioSegment.from_file(full_audio_path)
    print(f"  Audio loaded: {len(audio)}ms")

    audio_dir = get_audio_dir(run_dir)

    audio_dir.mkdir(parents=True, exist_ok=True)

    split_paths = []
    for boundary in boundaries:
        scene_index = boundary["scene_index"]
        start_ms = int(boundary["start"] * 1000)
        end_ms = int(boundary["end"] * 1000)
        
        start_ms = max(0, min(start_ms, len(audio)))
        end_ms = max(start_ms + 1, min(end_ms, len(audio)))

        segment = audio[start_ms:end_ms]
        output_path = audio_dir / f"scene_{scene_index:03d}.mp3"
        segment.export(str(output_path), format="mp3")
        split_paths.append(str(output_path))
        print(f"    Scene {scene_index}: {start_ms}ms - {end_ms}ms ({end_ms - start_ms}ms)")

    print(f"  Split complete: {len(split_paths)} audio clips")
    return split_paths


def regenerate_boundaries(run_dir: Path, model: str | None = None, voice_id: str | None = None) -> tuple[str, dict]:
    """Regenerate boundaries.json from existing full_audio.mp3 and script.json.
    
    This is useful when boundaries.json is missing or outdated.
    """
    import json
    
    script_path = run_dir / "script.json"
    full_audio_path = run_dir / "audio" / "full_audio.mp3"
    
    if not script_path.exists():
        raise FileNotFoundError(f"No script.json found in {run_dir}")
    if not full_audio_path.exists():
        raise FileNotFoundError(f"No full_audio.mp3 found in {run_dir / 'audio'}")
    
    with open(script_path) as f:
        script = json.load(f)
    
    scenes = script.get("scenes", [])
    if not scenes:
        raise ValueError("No scenes found in script.json")
    
    full_narration = " ".join(scene["narration"] for scene in scenes)
    
    print(f"  Regenerating boundaries for {len(scenes)} scenes...")
    print(f"  Total narration length: {len(full_narration)} characters")
    
    client = get_elevenlabs_client()
    
    try:
        result = client.text_to_speech.convert_with_timestamps(
            voice_id=voice_id or ELEVENLABS_VOICE_ID,
            text=full_narration,
            model_id=model or ELEVENLABS_MODEL,
            output_format="mp3_44100_128",
        )
        print(f"  API call completed, processing alignment data...")
    except Exception as e:
        print(f"  ERROR: ElevenLabs API call failed: {e}")
        raise
    
    alignment = result.alignment
    scene_boundaries = []
    
    if alignment and alignment.characters:
        print(f"  Processing {len(alignment.characters)} character timestamps...")
        scene_boundaries = _match_scenes_to_timestamps(
            scenes,
            alignment.characters,
            alignment.character_start_times_seconds,
            alignment.character_end_times_seconds
        )
        print(f"  Created {len(scene_boundaries)} scene boundaries")
    else:
        print(f"  WARNING: No alignment data received, using fallback boundaries")
        scene_boundaries = _create_fallback_boundaries(len(scenes))
    
    boundaries_path = run_dir / "audio" / "boundaries.json"
    with open(boundaries_path, "w") as f:
        json.dump(scene_boundaries, f, indent=2)
    print(f"  Saved boundaries to: {boundaries_path}")
    
    return str(full_audio_path), {"boundaries": scene_boundaries}
