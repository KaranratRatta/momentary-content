import requests
import fal_client
from pathlib import Path
from momentary.config import FAL_IMAGE_MODEL, STYLE_PROMPTS, DEFAULT_STYLE, VIDEO_WIDTH, VIDEO_HEIGHT, ANIMAL_GUIDANCE


ANIMAL_KEYWORDS = [
    "animal", "dog", "cat", "bird", "fish", "horse", "cow", "pig", "sheep", "goat",
    "chicken", "duck", "rabbit", "mouse", "rat", "lion", "tiger", "bear", "elephant",
    "monkey", "ape", "gorilla", "snake", "lizard", "frog", "turtle", "whale", "dolphin",
    "shark", "octopus", "spider", "insect", "butterfly", "bee", "ant", "pet", "wildlife"
]


def _contains_animals(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in ANIMAL_KEYWORDS)


def generate_image(scene_prompt: str, scene_index: int, model: str | None = None, style: str | None = None, run_dir: Path | None = None) -> str:
    style_name = style or DEFAULT_STYLE
    style_prompt = STYLE_PROMPTS.get(style_name, STYLE_PROMPTS[DEFAULT_STYLE])
    
    full_prompt = f"{scene_prompt}, {style_prompt}"
    
    if _contains_animals(scene_prompt):
        animal_guidance = ANIMAL_GUIDANCE.get(style_name, ANIMAL_GUIDANCE.get(DEFAULT_STYLE))
        if animal_guidance:
            full_prompt = f"{full_prompt}, {animal_guidance}"

    result = fal_client.subscribe(
        model or FAL_IMAGE_MODEL,
        arguments={
            "prompt": full_prompt,
            "image_size": {"width": VIDEO_WIDTH, "height": VIDEO_HEIGHT},
            "num_inference_steps": 8,
            "num_images": 1,
        },
    )

    if "images" in result and len(result["images"]) > 0:
        image_url = result["images"][0]["url"]
    elif "image" in result:
        image_url = result["image"]["url"] if isinstance(result["image"], dict) else result["image"]
    else:
        raise ValueError(f"No image in Fal.ai response: {result}")

    if run_dir:
        images_dir = run_dir / "images"
    else:
        images_dir = Path("temp/images")

    output_path = images_dir / f"scene_{scene_index:03d}.png"
    response = requests.get(image_url)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    return str(output_path)


def generate_all_images(scenes: list, model: str | None = None, style: str | None = None, run_dir: Path | None = None) -> list:
    if run_dir:
        images_dir = run_dir / "images"
    else:
        images_dir = Path("temp/images")

    images_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []
    for i, scene in enumerate(scenes):
        print(f"  Generating image for scene {i + 1}/{len(scenes)}...")
        path = generate_image(scene["image_prompt"], i, model, style, run_dir)
        image_paths.append(path)
    return image_paths
