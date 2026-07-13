import streamlit as st
import json
import os
from pathlib import Path

os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parent.parent / "src"))

from momentary.config import (
    OPENROUTER_API_KEY,
    FAL_KEY,
    ELEVENLABS_API_KEY,
    RUNS_DIR,
    DEFAULT_DURATION_MINUTES,
    DEFAULT_MOTION,
    DEFAULT_AUDIO_MODE,
    DEFAULT_THEME,
    DEFAULT_IMAGE_DENSITY,
    DEFAULT_RESEARCH,
    calculate_scenes,
    create_run_directory,
    save_run_config,
    OPENROUTER_MODELS,
    FAL_IMAGE_MODELS,
    ELEVENLABS_MODELS,
    ELEVENLABS_VOICES,
    STYLE_PROMPTS,
    DEFAULT_STYLE,
    MOTION_EFFECTS,
    AUDIO_MODES,
    NARRATION_THEMES,
    IMAGE_DENSITY,
    OPENROUTER_MODEL,
    FAL_IMAGE_MODEL,
    ELEVENLABS_MODEL,
    ELEVENLABS_VOICE_ID,
)
from momentary.script_generator import generate_script, research_topic
from momentary.image_generator import generate_image, generate_all_images, generate_thumbnail
from momentary.voice_generator import generate_voice, generate_all_voices, generate_single_audio, generate_chunked_audio, split_audio_by_boundaries
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
        overflow-y: auto !important;
        padding-bottom: 10rem !important;
    }
    section[data-testid="stSidebar"] .stSelectbox > div > div > div {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 8px;
    }
    [data-baseweb="popover"] {
        max-height: 400px !important;
        overflow-y: auto !important;
    }
    [data-baseweb="popover"] ul[role="listbox"] {
        max-height: 380px !important;
        overflow-y: auto !important;
    }
    [data-baseweb="menu"] {
        max-height: 400px !important;
        overflow-y: auto !important;
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

if "generating" not in st.session_state:
    st.session_state.generating = False
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False
if "generation_step" not in st.session_state:
    st.session_state.generation_step = 0
if "run_dir" not in st.session_state:
    st.session_state.run_dir = None
if "research_context" not in st.session_state:
    st.session_state.research_context = ""
if "script" not in st.session_state:
    st.session_state.script = None
if "title" not in st.session_state:
    st.session_state.title = None
if "scenes" not in st.session_state:
    st.session_state.scenes = None
if "image_paths" not in st.session_state:
    st.session_state.image_paths = None
if "audio_paths" not in st.session_state:
    st.session_state.audio_paths = None
if "output_path" not in st.session_state:
    st.session_state.output_path = None

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

    st.subheader("Narration Theme")
    theme = st.selectbox(
        "Theme",
        options=list(NARRATION_THEMES.keys()),
        index=list(NARRATION_THEMES.keys()).index(DEFAULT_THEME),
    )

    research = st.checkbox("Research topic before script", value=DEFAULT_RESEARCH)

    st.subheader("Image Generation")
    image_model = st.selectbox(
        "Image Model",
        options=FAL_IMAGE_MODELS,
        index=FAL_IMAGE_MODELS.index(FAL_IMAGE_MODEL) if FAL_IMAGE_MODEL in FAL_IMAGE_MODELS else 0,
    )

    st.subheader("Image Density")
    density = st.selectbox(
        "Images per video",
        options=list(IMAGE_DENSITY.keys()),
        index=list(IMAGE_DENSITY.keys()).index(DEFAULT_IMAGE_DENSITY),
    )
    density_descriptions = {
        "Fewer": "Fewer images, each shown longer",
        "Normal": "Standard image count",
        "More": "More images, faster transitions",
        "Maximum": "Maximum images, very dynamic",
    }
    st.caption(density_descriptions.get(density, ""))

    st.subheader("Visual Style")
    style = st.selectbox(
        "Style",
        options=list(STYLE_PROMPTS.keys()),
        index=list(STYLE_PROMPTS.keys()).index(DEFAULT_STYLE),
    )
    
    append_style = st.checkbox(
        "Append style description to image prompts",
        value=False,
        help="If unchecked (default), LLM incorporates style into prompts. If checked, style description is appended to each image prompt."
    )

    st.subheader("Video Motion")
    motion = st.selectbox(
        "Motion Effect",
        options=list(MOTION_EFFECTS.keys()),
        index=list(MOTION_EFFECTS.values()).index(DEFAULT_MOTION),
    )

    st.subheader("Audio Mode")
    audio_mode = st.selectbox(
        "Audio Generation",
        options=list(AUDIO_MODES.keys()),
        index=list(AUDIO_MODES.values()).index(DEFAULT_AUDIO_MODE),
    )
    if audio_mode == "Single Audio":
        st.caption("Generates one continuous audio track, more natural flow")
    elif audio_mode == "Chunked Audio":
        st.caption("Splits narration into ~175 word chunks, more reliable for long videos")
    else:
        st.caption("Generates separate audio per scene")

    st.subheader("Voice Generation")
    voice_model = st.selectbox(
        "TTS Model",
        options=ELEVENLABS_MODELS,
        index=ELEVENLABS_MODELS.index(ELEVENLABS_MODEL) if ELEVENLABS_MODEL in ELEVENLABS_MODELS else 0,
    )

    voice_input_type = st.radio(
        "Voice Selection",
        options=["Preset Voices", "Custom Voice ID"],
        horizontal=True,
    )

    if voice_input_type == "Preset Voices":
        voice_options = list(ELEVENLABS_VOICES.keys())
        default_index = 0
        if ELEVENLABS_VOICE_ID in ELEVENLABS_VOICES.values():
            default_index = list(ELEVENLABS_VOICES.values()).index(ELEVENLABS_VOICE_ID)

        voice_name = st.selectbox(
            "Voice",
            options=voice_options,
            index=default_index,
        )
        voice_id = ELEVENLABS_VOICES[voice_name]
    else:
        voice_id = st.text_input(
            "Voice ID",
            value=ELEVENLABS_VOICE_ID,
            placeholder="Enter ElevenLabs Voice ID",
        )
        voice_name = "Custom"

    st.divider()

    missing = check_keys()
    if missing:
        st.error(f"Missing API keys: {', '.join(missing)}")
    else:
        st.success("All API keys configured")


if missing:
    st.stop()


tab_pipeline, tab_script, tab_image, tab_voice, tab_test_split, tab_assemble, tab_runs, tab_status = st.tabs(
    ["Full Pipeline", "Test Script", "Test Image", "Test Voice", "Test Split", "Test Assemble", "Runs", "Status"]
)


with tab_pipeline:
    st.header("Generate Full Video")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic", placeholder="What Did Ancient Humans Do at Night?")
    with col2:
        duration = st.slider("Duration (min)", min_value=0.5, max_value=10.0, value=DEFAULT_DURATION_MINUTES, step=0.5)

    video_idea = st.text_input("Video Idea (optional)", placeholder="e.g., Focus on layer 2 solutions and scalability", help="Optional: specific angle or focus for the video. Leave empty for general coverage.")

    num_scenes = calculate_scenes(duration, density)
    st.caption(f"~{num_scenes} scenes for {duration} min video")

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    with col1:
        st.caption(f"LLM: {llm_model}")
    with col2:
        st.caption(f"Theme: {theme}")
    with col3:
        st.caption(f"Style: {style}")
    with col4:
        st.caption(f"Density: {density}")
    with col5:
        st.caption(f"Motion: {motion}")
    with col6:
        st.caption(f"Audio: {audio_mode}")
    with col7:
        st.caption(f"Research: {'Yes' if research else 'No'}")
    with col8:
        st.caption(f"Voice: {voice_name}")

    if st.session_state.generating:
        col_stop, col_status = st.columns([1, 4])
        with col_stop:
            if st.button("⏹ Stop", type="secondary"):
                st.session_state.stop_requested = True
                st.warning("Stop requested. Finishing current step...")
        with col_status:
            total_steps = 5 if research else 4
            steps = (["Researching...", "Generating script...", "Generating images...", "Generating voice...", "Assembling video..."]
                     if research else
                     ["Generating script...", "Generating images...", "Generating voice...", "Assembling video..."])
            current = min(st.session_state.generation_step, len(steps) - 1)
            st.info(f"Step {current + 1}/{total_steps}: {steps[current]}")

    if st.button("Generate Video", type="primary", disabled=not topic or st.session_state.generating):
        st.session_state.generating = True
        st.session_state.stop_requested = False
        st.session_state.generation_step = 0
        run_dir = create_run_directory(topic)
        
        run_config = {
            "topic": topic,
            "video_idea": video_idea,
            "duration": duration,
            "density": density,
            "motion": motion,
            "audio_mode": audio_mode,
            "theme": theme,
            "research": research,
            "style": style,
            "append_style": append_style,
            "llm_model": llm_model or OPENROUTER_MODEL,
            "image_model": image_model or FAL_IMAGE_MODEL,
            "voice_model": voice_model or ELEVENLABS_MODEL,
            "voice_id": voice_id or ELEVENLABS_VOICE_ID,
        }
        save_run_config(run_dir, run_config)
        
        st.session_state.run_dir = run_dir
        st.rerun()

    if st.session_state.generating and not st.session_state.stop_requested:
        run_dir = st.session_state.run_dir
        st.info(f"Run directory: `{run_dir}`")

        if research and st.session_state.generation_step == 0:
            st.session_state.generation_step = 1
            with st.spinner("Researching topic..."):
                research_context = research_topic(topic, model=llm_model)
                st.session_state.research_context = research_context
                st.success(f"Research complete ({len(research_context)} chars)")
            st.rerun()

        script_step = 1 if research else 0
        if st.session_state.generation_step == script_step:
            st.session_state.generation_step = script_step + 1
            with st.spinner("Generating script..."):
                research_context = st.session_state.get("research_context", "")
                target_duration_seconds = duration * 60
                script = generate_script(
                    topic,
                    num_scenes,
                    model=llm_model,
                    theme=theme,
                    research_context=research_context,
                    target_duration_seconds=target_duration_seconds,
                    video_idea=video_idea,
                    style=style,
                    run_dir=run_dir,
                )
                title = script.get("title", topic)
                scenes = script["scenes"]
                st.session_state.script = script
                st.session_state.title = title
                st.session_state.scenes = scenes
                st.success(f"Script: {title} ({len(scenes)} scenes)")
            st.rerun()

        image_step = script_step + 1
        if st.session_state.generation_step == image_step:
            st.session_state.generation_step = image_step + 1
            with st.spinner("Generating images..."):
                scenes = st.session_state.scenes
                image_paths = generate_all_images(scenes, model=image_model, style=style, append_style=append_style, run_dir=run_dir)
                st.session_state.image_paths = image_paths
                st.success(f"Generated {len(image_paths)} images")
            st.rerun()

        thumbnail_step = image_step + 1
        if st.session_state.generation_step == thumbnail_step:
            st.session_state.generation_step = thumbnail_step + 1
            script = st.session_state.script
            if "thumbnail_prompt" in script:
                with st.spinner("Generating thumbnail..."):
                    thumbnail_path = generate_thumbnail(script["thumbnail_prompt"], model=image_model, style=style, append_style=append_style, run_dir=run_dir)
                    st.session_state.thumbnail_path = thumbnail_path
                    st.success(f"Thumbnail generated")
            st.rerun()

        voice_step = thumbnail_step + 1
        if st.session_state.generation_step == voice_step:
            st.session_state.generation_step = voice_step + 1
            with st.spinner("Generating voice narration..."):
                try:
                    scenes = st.session_state.scenes
                    if audio_mode == "Single Audio":
                        full_audio_path, timestamp_data = generate_single_audio(scenes, model=voice_model, voice_id=voice_id, run_dir=run_dir)
                        boundaries = timestamp_data["boundaries"]
                        st.info("Splitting audio into scenes...")
                        audio_paths = split_audio_by_boundaries(full_audio_path, boundaries, run_dir=run_dir)
                        st.session_state.audio_paths = audio_paths
                        st.success(f"Generated single audio, split into {len(audio_paths)} clips")
                    elif audio_mode == "Chunked Audio":
                        full_audio_path, timestamp_data = generate_chunked_audio(scenes, model=voice_model, voice_id=voice_id, run_dir=run_dir)
                        boundaries = timestamp_data["boundaries"]
                        st.info("Splitting audio into scenes...")
                        audio_paths = split_audio_by_boundaries(full_audio_path, boundaries, run_dir=run_dir)
                        st.session_state.audio_paths = audio_paths
                        st.success(f"Generated chunked audio, split into {len(audio_paths)} clips")
                    else:
                        audio_paths = generate_all_voices(scenes, model=voice_model, voice_id=voice_id, run_dir=run_dir)
                        st.session_state.audio_paths = audio_paths
                        st.success(f"Generated {len(audio_paths)} audio clips")
                except Exception as e:
                    st.error(f"Voice generation failed: {e}")
                    st.session_state.generating = False
                    st.session_state.generation_step = 0
                    st.stop()
            st.rerun()

        assemble_step = voice_step + 1
        if st.session_state.generation_step == assemble_step:
            st.session_state.generation_step = assemble_step + 1
            with st.spinner("Assembling video... (this may take a minute)"):
                image_paths = st.session_state.image_paths
                audio_paths = st.session_state.audio_paths
                title = st.session_state.title

                if not image_paths or not audio_paths or not title:
                    st.error("Missing required data for video assembly. Please restart the generation.")
                    st.session_state.generating = False
                    st.session_state.generation_step = 0
                    st.rerun()

                try:
                    motion_value = MOTION_EFFECTS[motion]
                    output_path = assemble_video(image_paths, audio_paths, title, motion=motion_value, run_dir=run_dir)
                    st.session_state.output_path = output_path
                    st.session_state.generating = False
                    st.session_state.generation_step = 0
                    st.success(f"Video saved: {output_path}")
                except Exception as e:
                    st.error(f"Video assembly failed: {e}")
                    st.session_state.generating = False
                    st.session_state.generation_step = 0
            st.rerun()

    if "output_path" in st.session_state and st.session_state.output_path:
        if Path(st.session_state.output_path).exists():
            st.video(st.session_state.output_path)

    if st.session_state.stop_requested:
        st.session_state.generating = False
        st.session_state.generation_step = 0
        st.session_state.stop_requested = False
        st.warning("Generation stopped.")


with tab_script:
    st.header("Test Script Generation")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Topic", key="script_topic", placeholder="Enter a topic...")
    with col2:
        duration = st.slider("Duration (min)", min_value=0.5, max_value=10.0, value=DEFAULT_DURATION_MINUTES, step=0.5, key="script_duration")

    video_idea = st.text_input("Video Idea (optional)", key="script_video_idea", placeholder="e.g., Focus on layer 2 solutions", help="Optional: specific angle or focus for the video.")

    num_scenes = calculate_scenes(duration, density)
    st.caption(f"~{num_scenes} scenes | Model: {llm_model} | Density: {density}")

    if st.button("Generate Script", disabled=not topic):
        run_dir = create_run_directory(topic)
        with st.spinner("Generating..."):
            research_context = ""
            if research:
                research_context = research_topic(topic, model=llm_model)
            target_duration_seconds = duration * 60
            result = generate_script(
                topic,
                num_scenes,
                model=llm_model,
                theme=theme,
                research_context=research_context,
                target_duration_seconds=target_duration_seconds,
                video_idea=video_idea,
                run_dir=run_dir,
            )
            st.success(f"Script saved to: `{run_dir / 'script.json'}`")
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

    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Model: {image_model}")
    with col2:
        st.caption(f"Style: {style}")

    if st.button("Generate Image", disabled=not prompt):
        with st.spinner("Generating..."):
            path = generate_image(prompt, index, model=image_model, style=style)
            st.success(f"Saved: {path}")
            st.image(path, width=720)


with tab_voice:
    st.header("Test Voice Generation")
    text = st.text_area("Narration Text", height=100, placeholder="Enter text to speak...")
    index = st.number_input("Scene Index", min_value=0, value=0, key="voice_index")

    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Model: {voice_model}")
    with col2:
        st.caption(f"Voice: {voice_name}")

    if st.button("Generate Voice", disabled=not text):
        with st.spinner("Generating..."):
            path = generate_voice(text, index, model=voice_model, voice_id=voice_id)
            duration = get_audio_duration(path)
            st.success(f"Saved: {path} ({duration:.1f}s)")
            st.audio(path)


with tab_assemble:
    st.header("Test Video Assembly")

    if RUNS_DIR.exists():
        runs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()], reverse=True)
        run_options = [r.name for r in runs]
        selected_run = st.selectbox("Select Run", options=run_options)

        if selected_run:
            run_dir = RUNS_DIR / selected_run
            img_files = sorted((run_dir / "images").glob("scene_*.png"))
            aud_files = sorted((run_dir / "audio").glob("scene_*.mp3"))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Images Available", len(img_files))
            with col2:
                st.metric("Audio Available", len(aud_files))

            motion = st.selectbox(
                "Motion Effect",
                options=list(MOTION_EFFECTS.keys()),
                index=list(MOTION_EFFECTS.values()).index(DEFAULT_MOTION),
            )

            if not img_files:
                st.warning("No images in this run.")
            if not aud_files:
                st.warning("No audio in this run.")

            if st.button("Assemble Video", disabled=not img_files or not aud_files):
                image_paths = [str(p) for p in img_files]
                audio_paths = [str(p) for p in aud_files]

                script_path = run_dir / "script.json"
                title = "Untitled"
                if script_path.exists():
                    with open(script_path) as f:
                        script = json.load(f)
                        title = script.get("title", "Untitled")

                with st.spinner("Assembling..."):
                    motion_value = MOTION_EFFECTS[motion]
                    output_path = assemble_video(image_paths, audio_paths, title, motion=motion_value, run_dir=run_dir)
                    st.success(f"Video saved: {output_path}")
                    st.video(output_path)
    else:
        st.info("No runs available. Generate a video first.")


with tab_test_split:
    st.header("Test Audio Splitting")
    st.caption("Test audio splitting on an existing run with full_audio.mp3")

    if RUNS_DIR.exists():
        runs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()], reverse=True)
        run_options = [r.name for r in runs]
        selected_run = st.selectbox("Select Run", options=run_options, key="split_run")

        if selected_run:
            run_dir = RUNS_DIR / selected_run
            full_audio_path = run_dir / "audio" / "full_audio.mp3"
            script_path = run_dir / "script.json"

            if full_audio_path.exists():
                st.success(f"Found: {full_audio_path.name}")
            else:
                st.error("No full_audio.mp3 found in this run")

            if script_path.exists():
                with open(script_path) as f:
                    script = json.load(f)
                scenes = script.get("scenes", [])
                st.metric("Scenes in script", len(scenes))
            else:
                st.error("No script.json found in this run")
                scenes = []

            if st.button("Test Split Audio", disabled=not full_audio_path.exists() or not scenes):
                try:
                    boundaries_path = run_dir / "audio" / "boundaries.json"
                    if boundaries_path.exists():
                        with open(boundaries_path) as f:
                            boundaries = json.load(f)
                        st.info(f"Loaded {len(boundaries)} saved boundaries from boundaries.json")
                    else:
                        st.warning("No saved boundaries found, using dummy 5s intervals")
                        boundaries = []
                        for i, scene in enumerate(scenes):
                            boundaries.append({
                                "scene_index": i,
                                "start": i * 5.0,
                                "end": (i + 1) * 5.0,
                            })

                    with st.spinner("Splitting audio..."):
                        audio_paths = split_audio_by_boundaries(str(full_audio_path), boundaries, run_dir=run_dir)
                        st.success(f"Successfully split into {len(audio_paths)} audio clips")
                        
                        for path in audio_paths:
                            st.write(f"- {Path(path).name}")
                except Exception as e:
                    st.error(f"Error splitting audio: {e}")
    else:
        st.info("No runs available. Generate a video first.")


with tab_runs:
    st.header("All Runs")

    if RUNS_DIR.exists():
        runs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()], reverse=True)
        st.metric("Total Runs", len(runs))

        for run in runs:
            with st.expander(run.name):
                script_path = run / "script.json"
                img_count = len(list((run / "images").glob("scene_*.png"))) if (run / "images").exists() else 0
                aud_count = len(list((run / "audio").glob("scene_*.mp3"))) if (run / "audio").exists() else 0
                video_exists = (run / "video.mp4").exists()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Script", "Yes" if script_path.exists() else "No")
                col2.metric("Images", img_count)
                col3.metric("Audio", aud_count)
                col4.metric("Video", "Yes" if video_exists else "No")

                if script_path.exists():
                    with open(script_path) as f:
                        script = json.load(f)
                    st.subheader("Script")
                    st.json(script)

                if video_exists:
                    st.subheader("Video")
                    st.video(str(run / "video.mp4"))
    else:
        st.info("No runs yet. Generate a video to get started.")


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
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("LLM", llm_model)
    with col2:
        st.metric("Image", image_model)
    with col3:
        st.metric("Style", style)
    with col4:
        st.metric("Motion", motion)
    with col5:
        if voice_name == "Custom":
            st.metric("Voice", f"Custom ({voice_id[:8]}...)")
        else:
            st.metric("Voice", voice_name)

    st.subheader("Runs")
    if RUNS_DIR.exists():
        runs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()])
        st.metric("Total Runs", len(runs))

        if runs:
            st.subheader("Recent Runs")
            for run in runs[-5:]:
                script_exists = (run / "script.json").exists()
                img_count = len(list((run / "images").glob("scene_*.png"))) if (run / "images").exists() else 0
                aud_count = len(list((run / "audio").glob("scene_*.mp3"))) if (run / "audio").exists() else 0
                video_exists = (run / "video.mp4").exists()
                st.write(f"- **{run.name}**")
                st.caption(f"Script: {'Yes' if script_exists else 'No'} | Images: {img_count} | Audio: {aud_count} | Video: {'Yes' if video_exists else 'No'}")
    else:
        st.metric("Total Runs", 0)
        st.info("No runs yet.")
