import streamlit as st
import json
import os
from pathlib import Path

os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parent.parent / "src"))

from momentary.config import (
    OPENROUTER_API_KEY,
    FAL_KEY,
    ELEVENLABS_API_KEY,
    TEMP_IMAGES_DIR,
    TEMP_AUDIO_DIR,
    OUTPUT_DIR,
    NUM_SCENES,
)
from momentary.script_generator import generate_script
from momentary.image_generator import generate_image, generate_all_images
from momentary.voice_generator import generate_voice, generate_all_voices
from momentary.video_assembler import assemble_video, get_audio_duration


st.set_page_config(page_title="Momentary Content", page_icon="", layout="wide")

st.title("Momentary Content")
st.caption("AI-powered cartoon stick-figure video generation")


def check_keys():
    missing = []
    if not OPENROUTER_API_KEY or "your-key" in OPENROUTER_API_KEY:
        missing.append("OpenRouter")
    if not FAL_KEY or "your-key" in FAL_KEY:
        missing.append("Fal.ai")
    if not ELEVENLABS_API_KEY or "your-key" in ELEVENLABS_API_KEY:
        missing.append("ElevenLabs")
    return missing


missing = check_keys()
if missing:
    st.error(f"Missing API keys: {', '.join(missing)}. Set them in `.env`")
    st.stop()


tab_pipeline, tab_script, tab_image, tab_voice, tab_assemble, tab_status = st.tabs(
    ["Full Pipeline", "Test Script", "Test Image", "Test Voice", "Test Assemble", "Status"]
)


with tab_pipeline:
    st.header("Generate Full Video")
    topic = st.text_input("Topic", placeholder="What Did Ancient Humans Do at Night?")

    if st.button("Generate Video", type="primary", disabled=not topic):
        with st.spinner("Generating script..."):
            script = generate_script(topic)
            title = script.get("title", topic)
            scenes = script["scenes"]
            st.success(f"Script: {title} ({len(scenes)} scenes)")

        with st.spinner("Generating images..."):
            image_paths = generate_all_images(scenes)
            st.success(f"Generated {len(image_paths)} images")

        with st.spinner("Generating voice narration..."):
            audio_paths = generate_all_voices(scenes)
            st.success(f"Generated {len(audio_paths)} audio clips")

        with st.spinner("Assembling video..."):
            output_path = assemble_video(image_paths, audio_paths, title)
            st.success(f"Video saved: {output_path}")

            if Path(output_path).exists():
                st.video(output_path)


with tab_script:
    st.header("Test Script Generation")
    topic = st.text_input("Topic", key="script_topic", placeholder="Enter a topic...")

    if st.button("Generate Script", disabled=not topic):
        with st.spinner("Generating..."):
            result = generate_script(topic)
            st.json(result)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download JSON",
                    json.dumps(result, indent=2),
                    file_name="script.json",
                    mime="application/json",
                )
            with col2:
                scenes = result.get("scenes", [])
                st.metric("Scenes", len(scenes))


with tab_image:
    st.header("Test Image Generation")
    prompt = st.text_area("Image Prompt", height=100, placeholder="Describe the scene...")
    index = st.number_input("Scene Index", min_value=0, value=0)

    if st.button("Generate Image", disabled=not prompt):
        with st.spinner("Generating..."):
            path = generate_image(prompt, index)
            st.success(f"Saved: {path}")
            st.image(path, width=720)


with tab_voice:
    st.header("Test Voice Generation")
    text = st.text_area("Narration Text", height=100, placeholder="Enter text to speak...")
    index = st.number_input("Scene Index", min_value=0, value=0, key="voice_index")

    if st.button("Generate Voice", disabled=not text):
        with st.spinner("Generating..."):
            path = generate_voice(text, index)
            duration = get_audio_duration(path)
            st.success(f"Saved: {path} ({duration:.1f}s)")
            st.audio(path)


with tab_assemble:
    st.header("Test Video Assembly")

    img_files = sorted(TEMP_IMAGES_DIR.glob("scene_*.png")) if TEMP_IMAGES_DIR.exists() else []
    aud_files = sorted(TEMP_AUDIO_DIR.glob("scene_*.mp3")) if TEMP_AUDIO_DIR.exists() else []

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Images Available", len(img_files))
    with col2:
        st.metric("Audio Available", len(aud_files))

    if not img_files:
        st.warning("No images in temp/images/. Generate some first.")
    if not aud_files:
        st.warning("No audio in temp/audio/. Generate some first.")

    title = st.text_input("Video Title", value="test_video")

    if st.button("Assemble Video", disabled=not img_files or not aud_files):
        image_paths = [str(p) for p in img_files]
        audio_paths = [str(p) for p in aud_files]

        with st.spinner("Assembling..."):
            output_path = assemble_video(image_paths, audio_paths, title)
            st.success(f"Video saved: {output_path}")
            st.video(output_path)


with tab_status:
    st.header("System Status")

    st.subheader("API Keys")
    keys_status = {
        "OpenRouter": OPENROUTER_API_KEY,
        "Fal.ai": FAL_KEY,
        "ElevenLabs": ELEVENLABS_API_KEY,
    }
    for name, value in keys_status.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"**{name}**")
        with col2:
            if value and "your-key" not in value:
                st.success("Configured")
            else:
                st.error("Missing")

    st.subheader("Files")
    img_count = len(img_files) if TEMP_IMAGES_DIR.exists() else 0
    aud_count = len(aud_files) if TEMP_AUDIO_DIR.exists() else 0
    out_count = len(list(OUTPUT_DIR.glob("*.mp4"))) if OUTPUT_DIR.exists() else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Images", img_count)
    col2.metric("Audio Clips", aud_count)
    col3.metric("Videos", out_count)

    st.subheader("Generated Videos")
    if OUTPUT_DIR.exists():
        videos = list(OUTPUT_DIR.glob("*.mp4"))
        for v in videos:
            st.write(f"- {v.name}")
    else:
        st.info("No videos generated yet.")
