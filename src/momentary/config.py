import os
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-5")
FAL_IMAGE_MODEL = os.getenv("FAL_IMAGE_MODEL", "fal-ai/krea-2/turbo")

ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "ZqvIIuD5aI9JFejebHiH")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

ELEVENLABS_VOICES = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Drew": "29vD33N1CtxCmqQRPOHJ",
    "Clyde": "2EiwWnXFnvU5JabPnv8n",
    "Paul": "5Q0t7uMcjvnagumLfvZi",
    "Domi": "AZnzlk1XvdvUeBnXmlld",
    "Dave": "CYw3kZ02Hs0563khs1Fj",
    "Freya": "D38z5RcWu1voky8WS1ja",
    "Sarah": "EXAVITQu4vr4xnSDxMaL",
    "Antoni": "ErXwobaYiN019PkySvjV",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Josh": "TxGEqnHWrfWFTfGW9XjX",
    "Arnold": "VR6AewLTigWG4xSOukaG",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Sam": "yoZ06aMxZJJ28mfd3POQ",
    "Clara": "Qggl4b0xRMiqOwhPtVWT",
    "Russ": "HKFOb9iktHA85uKXydRT",
    "Mira": "ZqvIIuD5aI9JFejebHiH",
    "Om": "ePiPWpzcHZrcqRzFrgQg",

}

OPENROUTER_MODELS = [
    "deepseek/deepseek-chat",
    "anthropic/claude-sonnet-5",
    "openai/gpt-4o",
    "google/gemini-2.5-pro",
    "meta-llama/llama-3.3-70b-instruct",
]

FAL_IMAGE_MODELS = [
    "fal-ai/krea-2/turbo",
    "fal-ai/flux/schnell",
    "fal-ai/flux-pro",
    "fal-ai/flux-realism",
    "fal-ai/flux-anime",
]

ELEVENLABS_MODELS = [
    "eleven_v3",
    "eleven_multilingual_v2",
    "eleven_multilingual_v1",
    "eleven_english_v2",
    "eleven_english_v1",
]

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TRANSITION_DURATION = 0.5

DEFAULT_RESEARCH = False

DEFAULT_DURATION_MINUTES = 0.5
AVG_SCENE_DURATION_SECONDS = 8
MIN_SCENES = 3
MAX_SCENES = 200

IMAGE_DENSITY = {
    "Fewer": 0.5,
    "Normal": 1.0,
    "More": 2.0,
    "Maximum": 3.0,
}

DEFAULT_IMAGE_DENSITY = "More"


def calculate_scenes(duration_minutes: float, density: str = DEFAULT_IMAGE_DENSITY) -> int:
    multiplier = IMAGE_DENSITY.get(density, 1.0)
    duration_seconds = duration_minutes * 60
    scenes = int((duration_seconds / AVG_SCENE_DURATION_SECONDS) * multiplier)
    return max(MIN_SCENES, min(MAX_SCENES, scenes))


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = PROJECT_DIR / "runs"


def sanitize_topic(topic: str) -> str:
    sanitized = re.sub(r'[^\w\s-]', '', topic)
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    return sanitized.lower()[:50]


def create_run_directory(topic: str) -> Path:
    run_number = get_next_run_number()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{run_number:03d}_{sanitize_topic(topic)}_{timestamp}"
    run_dir = RUNS_DIR / folder_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "images").mkdir(exist_ok=True)
    (run_dir / "audio").mkdir(exist_ok=True)
    return run_dir


def get_next_run_number() -> int:
    counter_file = RUNS_DIR / ".counter"
    
    if counter_file.exists():
        with open(counter_file) as f:
            current = int(f.read().strip())
        next_num = current + 1
    else:
        max_existing = 0
        if RUNS_DIR.exists():
            for folder in RUNS_DIR.iterdir():
                if folder.is_dir():
                    parts = folder.name.split("_")
                    if parts and parts[0].isdigit():
                        max_existing = max(max_existing, int(parts[0]))
        next_num = max_existing + 1
    
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(counter_file, "w") as f:
        f.write(str(next_num))
    
    return next_num


def save_run_config(run_dir: Path, config: dict):
    import json
    config_path = run_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


CARTOON_STYLE_PROMPT = (
    "hand-drawn cartoon illustration, "
    "slightly wobbly imperfect lines like actual hand drawing, "
    "organic textured paper background with subtle grain, "
    "human characters as simple stick figures with round white heads and dot eyes, "
    "warm earthy color palette with slight color bleeding at edges, "
    "visible pencil or ink texture in the linework, "
    "slight asymmetry and natural imperfections, "
    "dramatic lighting with soft shadows, "
    "casual humorous educational YouTube style like Kurzgesagt or Vsauce, "
    "no glossy AI look, no perfect symmetry, no plastic smoothness, "
    "no photorealism, no 3D rendering"
)

ANIME_STYLE_PROMPT = (
    "anime illustration style with hand-drawn feel, "
    "slight line weight variation like actual pen work, "
    "textured background with subtle noise, "
    "expressive character design with detailed eyes, "
    "vibrant colors with slight color bleeding, "
    "dynamic composition with natural imperfections, "
    "emotional atmospheric lighting, "
    "no glossy AI perfection, no plastic smoothness"
)

REALISTIC_STYLE_PROMPT = (
    "cinematic digital painting with photographic quality, "
    "film grain texture overlay, "
    "natural lighting with realistic shadows and highlights, "
    "detailed textures on surfaces and materials, "
    "slight depth of field blur on background elements, "
    "color grading like professional film, "
    "no AI artifacts, no oversharpening, no plastic skin"
)

STORYBOOK_STYLE_PROMPT = (
    "classic children's book illustration, "
    "watercolor and colored pencil texture, "
    "visible brush strokes and paper texture, "
    "soft warm color palette with slight color bleeding, "
    "whimsical hand-drawn characters with personality, "
    "cozy atmospheric lighting, "
    "slight imperfections that show it's hand-made, "
    "no digital perfection, no glossy AI look"
)

LAZY_DOODLE_STYLE_PROMPT = (
    "hand-drawn, sharp lines, "
    "color background for scene requires time of day or mood, else use white background, "
    "human characters as simple stick figures with round white heads, no noses, eyes matching emotion and action,"
    "minimal or no lighting/shadows/depth depends on the scene, "
    "flat colors with no shading or highlights, "
    "no glossy AI look, no smooth rendering, "
    "no photorealism, no 3D, no dramatic lighting"
)

STYLE_PROMPTS = {
    "Lazy Doodle": LAZY_DOODLE_STYLE_PROMPT,
    "Cartoon Stick Figure": CARTOON_STYLE_PROMPT,
    "Anime": ANIME_STYLE_PROMPT,
    "Realistic": REALISTIC_STYLE_PROMPT,
    "Storybook": STORYBOOK_STYLE_PROMPT,
}

DEFAULT_STYLE = "Lazy Doodle"

MOTION_EFFECTS = {
    "Static": "static",
    "Zoom In": "zoom_in",
    "Zoom Out": "zoom_out",
    "Pan Left": "pan_left",
    "Pan Right": "pan_right",
    "Pan Up": "pan_up",
    "Pan Down": "pan_down",
    "Random": "random",
    "Variety": "variety",
}

DEFAULT_MOTION = "static"

AUDIO_MODES = {
    "Per Scene": "per_scene",
    "Single Audio": "single_audio",
    "Chunked Audio": "chunked_audio",
}

DEFAULT_AUDIO_MODE = "chunked_audio"
CHUNK_WORDS = 175

NARRATION_THEMES = {
    "Educational": "educational, informative, clear explanations with interesting facts",
    "Humorous": "humorous, witty, casual conversational tone with jokes and playful observations",
    "Dramatic": "dramatic, intense, cinematic storytelling with suspense and emotional weight",
    "Documentary": "documentary-style, authoritative narrator, serious and factual presentation",
    "Storytelling": "storytelling, narrative-driven, like telling a friend an amazing story",
    "Mysterious": "mysterious, intriguing, building curiosity and wonder about the unknown",
}

DEFAULT_THEME = "Educational"

STOP_AFTER_STAGES = {
    "Full Pipeline": "video",
    "After Images": "images",
    "After Voice": "voice",
}

DEFAULT_STOP_AFTER = "video"

RESEARCH_PROMPT = """You are a research assistant. Given a topic, provide key facts, interesting angles, and notable details that would make a video script more accurate and engaging.

Focus on:
- Surprising or counterintuitive facts
- Historical context and timeline
- Scientific explanations (if applicable)
- Common misconceptions to address
- Specific examples and anecdotes

Keep it concise but informative. Return as a structured list of key points.

Topic: {topic}"""
