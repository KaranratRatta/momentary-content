import os
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
FAL_IMAGE_MODEL = os.getenv("FAL_IMAGE_MODEL", "fal-ai/flux/schnell")

ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
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
}

OPENROUTER_MODELS = [
    "deepseek/deepseek-chat",
    "anthropic/claude-sonnet-4",
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

DEFAULT_DURATION_MINUTES = 0.5
AVG_SCENE_DURATION_SECONDS = 8
MIN_SCENES = 3
MAX_SCENES = 30


def calculate_scenes(duration_minutes: float) -> int:
    duration_seconds = duration_minutes * 60
    scenes = int(duration_seconds / AVG_SCENE_DURATION_SECONDS)
    return max(MIN_SCENES, min(MAX_SCENES, scenes))


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = PROJECT_DIR / "runs"


def sanitize_topic(topic: str) -> str:
    sanitized = re.sub(r'[^\w\s-]', '', topic)
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    return sanitized.lower()[:50]


def create_run_directory(topic: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{sanitize_topic(topic)}_{timestamp}"
    run_dir = RUNS_DIR / folder_name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "images").mkdir(exist_ok=True)
    (run_dir / "audio").mkdir(exist_ok=True)
    return run_dir


CARTOON_STYLE_PROMPT = (
    "cartoon stick figure illustration style, "
    "simple hand-drawn sketchy line art, "
    "round white head character with big eyes and simple facial expression, "
    "stick figure body with thin black lines, "
    "flat colors with minimal shading, "
    "earthy muted color palette (browns, dark blues, warm oranges), "
    "cave or historical setting, "
    "dramatic lighting from campfire or torch, "
    "humorous casual tone, "
    "2D animation style, "
    "no photorealism, "
    "no 3D rendering"
)

ANIME_STYLE_PROMPT = (
    "anime illustration style, "
    "detailed anime character design with expressive eyes, "
    "vibrant colors with cel shading, "
    "dynamic composition with dramatic angles, "
    "Japanese animation aesthetic, "
    "clean line art with detailed backgrounds, "
    "emotional lighting and atmosphere"
)

REALISTIC_STYLE_PROMPT = (
    "photorealistic digital art, "
    "highly detailed realistic rendering, "
    "cinematic lighting and composition, "
    "professional photography quality, "
    "natural color palette, "
    "detailed textures and materials, "
    "dramatic mood lighting"
)

STORYBOOK_STYLE_PROMPT = (
    "children's storybook illustration style, "
    "whimsical hand-drawn artwork, "
    "soft pastel color palette, "
    "gentle rounded shapes and friendly characters, "
    "warm cozy atmosphere, "
    "textured paper-like background, "
    "classic fairy tale aesthetic, "
    "inviting and magical mood"
)

STYLE_PROMPTS = {
    "Cartoon Stick Figure": CARTOON_STYLE_PROMPT,
    "Anime": ANIME_STYLE_PROMPT,
    "Realistic": REALISTIC_STYLE_PROMPT,
    "Storybook": STORYBOOK_STYLE_PROMPT,
}

DEFAULT_STYLE = "Cartoon Stick Figure"

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

DEFAULT_MOTION = "Static"
