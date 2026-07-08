import os
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

OPENROUTER_MODELS = [
    "deepseek/deepseek-chat",
    "anthropic/claude-sonnet-4",
    "openai/gpt-4o",
    "google/gemini-2.5-pro",
    "meta-llama/llama-3.3-70b-instruct",
]

FAL_IMAGE_MODELS = [
    "fal-ai/flux/schnell",
    "fal-ai/flux-pro",
    "fal-ai/flux-realism",
    "fal-ai/flux-anime",
]

ELEVENLABS_MODELS = [
    "eleven_multilingual_v2",
    "eleven_multilingual_v1",
    "eleven_english_v2",
    "eleven_english_v1",
]

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TRANSITION_DURATION = 0.5

DEFAULT_DURATION_MINUTES = 8.0
AVG_SCENE_DURATION_SECONDS = 8
MIN_SCENES = 3
MAX_SCENES = 30


def calculate_scenes(duration_minutes: float) -> int:
    duration_seconds = duration_minutes * 60
    scenes = int(duration_seconds / AVG_SCENE_DURATION_SECONDS)
    return max(MIN_SCENES, min(MAX_SCENES, scenes))

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
TEMP_DIR = PROJECT_DIR / "temp"
TEMP_IMAGES_DIR = TEMP_DIR / "images"
TEMP_AUDIO_DIR = TEMP_DIR / "audio"

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
