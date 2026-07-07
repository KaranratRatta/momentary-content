import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
FAL_IMAGE_MODEL = os.getenv("FAL_IMAGE_MODEL", "fal-ai/flux/schnell")

ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TRANSITION_DURATION = 0.5

NUM_SCENES = 10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
TEMP_IMAGES_DIR = os.path.join(TEMP_DIR, "images")
TEMP_AUDIO_DIR = os.path.join(TEMP_DIR, "audio")

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
