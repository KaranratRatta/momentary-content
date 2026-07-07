import os
from elevenlabs import ElevenLabs
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, TEMP_AUDIO_DIR


def generate_voice(narration: str, scene_index: int) -> str:
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    audio = client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        text=narration,
        model_id="eleven_monolingual_v1",
        output_format="mp3_44100_128",
    )

    output_path = os.path.join(TEMP_AUDIO_DIR, f"scene_{scene_index:03d}.mp3")
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return output_path


def generate_all_voices(scenes: list) -> list:
    os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
    audio_paths = []
    for i, scene in enumerate(scenes):
        print(f"  Generating voice for scene {i + 1}/{len(scenes)}...")
        path = generate_voice(scene["narration"], i)
        audio_paths.append(path)
    return audio_paths
