import base64
import re
from pathlib import Path
from elevenlabs import ElevenLabs
from momentary.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL


def _split_text_into_chunks(text: str, target_words: int = 175) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
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


def generate_chunked_audio(scenes: list, model: str | None = None, voice_id: str | None = None, run_dir: Path | None = None, chunk_words: int = 175) -> tuple[str, dict]:
    from pydub import AudioSegment
    import io
    
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    full_narration = " ".join(scene["narration"] for scene in scenes)
    chunks = _split_text_into_chunks(full_narration, chunk_words)
    
    if not chunks:
        print(f"  WARNING: No narration text to generate audio for")
        return "", {"boundaries": [{"scene_index": i, "start": i * 5.0, "end": (i + 1) * 5.0} for i in range(len(scenes))]}
    
    print(f"  Generating chunked audio: {len(chunks)} chunks (~{chunk_words} words each)")
    print(f"  Total narration length: {len(full_narration)} characters")
    
    if run_dir:
        audio_dir = run_dir / "audio"
    else:
        audio_dir = Path("temp/audio")
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
        full_narration_chars = list(full_narration)
        char_index = 0
        
        for i, scene in enumerate(scenes):
            narration = scene["narration"]
            scene_start = None
            scene_end = None
            
            narration_chars = list(narration)
            narration_pos = 0
            
            while char_index < len(all_characters) and narration_pos < len(narration_chars):
                if all_characters[char_index].lower() == narration_chars[narration_pos].lower():
                    if scene_start is None:
                        scene_start = all_start_times[char_index]
                    narration_pos += 1
                    if narration_pos >= len(narration_chars):
                        scene_end = all_end_times[char_index]
                char_index += 1
            
            if scene_start is None:
                scene_start = all_start_times[0] if all_start_times else 0.0
            if scene_end is None:
                if i + 1 < len(scenes):
                    scene_end = scene_boundaries[i + 1]["start"] if scene_boundaries else all_end_times[-1] if all_end_times else 10.0
                else:
                    scene_end = all_end_times[-1] if all_end_times else 10.0
            
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
    
    print(f"  Chunked audio generation complete")
    return str(output_path), {"boundaries": scene_boundaries}


def split_audio_by_boundaries(full_audio_path: str, boundaries: list, run_dir: Path | None = None) -> list:
    from pydub import AudioSegment

    print(f"  Splitting audio by boundaries...")
    print(f"  Loading audio from: {full_audio_path}")
    audio = AudioSegment.from_file(full_audio_path)
    print(f"  Audio loaded: {len(audio)}ms")

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
        
        start_ms = max(0, min(start_ms, len(audio)))
        end_ms = max(start_ms + 1, min(end_ms, len(audio)))

        segment = audio[start_ms:end_ms]
        output_path = audio_dir / f"scene_{scene_index:03d}.mp3"
        segment.export(str(output_path), format="mp3")
        split_paths.append(str(output_path))
        print(f"    Scene {scene_index}: {start_ms}ms - {end_ms}ms ({end_ms - start_ms}ms)")

    print(f"  Split complete: {len(split_paths)} audio clips")
    return split_paths
