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
    DEFAULT_DURATION_MINUTES,
    calculate_scenes,
    OPENROUTER_MODELS,
    FAL_IMAGE_MODELS,
    ELEVENLABS_MODELS,
    OPENROUTER_MODEL,
    FAL_IMAGE_MODEL,
    ELEVENLABS_MODEL,
)
from momentary.script_generator import generate_script
from momentary.image_generator import generate_image, generate_all_images
from momentary.voice_generator import generate_voice, generate_all_voices
from momentary.video_assembler import assemble_video, get_audio_duration


st.set_page_config(page_title="Momentary Content", page_icon="", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    .stApp > header {
        background: transparent;
    }
    .stTitle {
        color: #e0e0ff;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
    }
    .stCaption {
        color: #8888aa;
        text-align: center;
        font-size: 1.1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        color: #8888aa;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.3);
        color: #e0e0ff;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    .stButton > button:disabled {
        background: #444;
        color: #888;
        box-shadow: none;
        transform: none;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        color: #e0e0ff;
        padding: 12px 16px;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    .stSelectbox > div > div > div {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        color: #e0e0ff;
    }
    .stSlider > div > div > div > div {
        background: #6366f1;
    }
    .stSlider > div > div > div > div > div {
        background: #6366f1;
    }
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px;
        color: #e0e0ff;
    }
    .stMetric {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stMetricValue"] {
        color: #e0e0ff;
        font-size: 1.5rem;
    }
    [data-testid="stMetricLabel"] {
        color: #8888aa;
    }
    .stAlert {
        border-radius: 12px;
        border: none;
    }
    .stSpinner > div {
        border-color: rgba(99, 102, 241, 0.3);
        border-top-color: #6366f1;
    }
    header {
        visibility: hidden;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stDownloadButton > button {
        background: rgba(99, 102, 241, 0.2);
        border: 1px solid #6366f1;
        color: #e0e0ff;
        border-radius: 10px;
        padding: 10px 20px;
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 26, 0.95);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    section[data-testid="stSidebar"] .stSelectbox > div > div > div {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] h3 {
        color: #e0e0ff;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    section[data-testid="stSidebar"] label {
        color: #8888aa;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

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


with st.sidebar:
    st.header("Model Settings")

    st.subheader("Script Generation")
    llm_model = st.selectbox(
        "LLM Model",
        options=OPENROUTER_MODELS,
        index=OPENROUTER_MODELS.index(OPENROUTER_MODEL) if OPENROUTER_MODEL in OPENROUTER_MODELS else 0,
    )

    st.subheader("Image Generation")
    image_model = st.selectbox(
        "Image Model",
        options=FAL_IMAGE_MODELS,
        index=FAL_IMAGE_MODELS.index(FAL_IMAGE_MODEL) if FAL_IMAGE_MODEL in FAL_IMAGE_MODELS else 0,
    )

    st.subheader("Voice Generation")
    voice_model = st.selectbox(
        "TTS Model",
        options=ELEVENLABS_MODELS,
        index=ELEVENLABS_MODELS.index(ELEVENLABS_MODEL) if ELEVENLABS_MODEL in ELEVENLABS_MODELS else 0,
    )

    st.divider()

    missing = check_keys()
    if missing:
        st.error(f"Missing API keys: {', '.join(missing)}")
    else:
        st.success("All API keys configured")


if missing:
    st.stop()


tab_pipeline, tab_script, tab_image, tab_voice, tab_assemble, tab_status = st.tabs(
    ["Full Pipeline", "Test Script", "Test Image", "Test Voice", "Test Assemble", "Status"]
)


with tab_pipeline:
    st.header("Generate Full Video")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic", placeholder="What Did Ancient Humans Do at Night?")
    with col2:
        duration = st.slider("Duration (min)", min_value=0.5, max_value=10.0, value=DEFAULT_DURATION_MINUTES, step=0.5)

    num_scenes = calculate_scenes(duration)
    st.caption(f"~{num_scenes} scenes for {duration} min video")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"LLM: {llm_model}")
    with col2:
        st.caption(f"Image: {image_model}")
    with col3:
        st.caption(f"Voice: {voice_model}")

    if st.button("Generate Video", type="primary", disabled=not topic):
        with st.spinner("Generating script..."):
            script = generate_script(topic, num_scenes, model=llm_model)
            title = script.get("title", topic)
            scenes = script["scenes"]
            st.success(f"Script: {title} ({len(scenes)} scenes)")

        with st.spinner("Generating images..."):
            image_paths = generate_all_images(scenes, model=image_model)
            st.success(f"Generated {len(image_paths)} images")

        with st.spinner("Generating voice narration..."):
            audio_paths = generate_all_voices(scenes, model=voice_model)
            st.success(f"Generated {len(audio_paths)} audio clips")

        with st.spinner("Assembling video..."):
            output_path = assemble_video(image_paths, audio_paths, title)
            st.success(f"Video saved: {output_path}")

            if Path(output_path).exists():
                st.video(output_path)


with tab_script:
    st.header("Test Script Generation")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic", key="script_topic", placeholder="Enter a topic...")
    with col2:
        duration = st.slider("Duration (min)", min_value=0.5, max_value=10.0, value=DEFAULT_DURATION_MINUTES, step=0.5, key="script_duration")

    num_scenes = calculate_scenes(duration)
    st.caption(f"~{num_scenes} scenes | Model: {llm_model}")

    if st.button("Generate Script", disabled=not topic):
        with st.spinner("Generating..."):
            result = generate_script(topic, num_scenes, model=llm_model)
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

    st.caption(f"Model: {image_model}")

    if st.button("Generate Image", disabled=not prompt):
        with st.spinner("Generating..."):
            path = generate_image(prompt, index, model=image_model)
            st.success(f"Saved: {path}")
            st.image(path, width=720)


with tab_voice:
    st.header("Test Voice Generation")
    text = st.text_area("Narration Text", height=100, placeholder="Enter text to speak...")
    index = st.number_input("Scene Index", min_value=0, value=0, key="voice_index")

    st.caption(f"Model: {voice_model}")

    if st.button("Generate Voice", disabled=not text):
        with st.spinner("Generating..."):
            path = generate_voice(text, index, model=voice_model)
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

    st.subheader("Current Models")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("LLM", llm_model)
    with col2:
        st.metric("Image", image_model)
    with col3:
        st.metric("Voice", voice_model)

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
