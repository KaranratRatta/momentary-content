import requests
import fal_client
from pathlib import Path
from momentary.config import FAL_IMAGE_MODEL, TEMP_IMAGES_DIR, CARTOON_STYLE_PROMPT, VIDEO_WIDTH, VIDEO_HEIGHT


def generate_image(scene_prompt: str, scene_index: int) -> str:
    full_prompt = f"{scene_prompt}, {CARTOON_STYLE_PROMPT}"

    result = fal_client.subscribe(
        FAL_IMAGE_MODEL,
        arguments={
            "prompt": full_prompt,
            "image_size": {"width": VIDEO_WIDTH, "height": VIDEO_HEIGHT},
            "num_inference_steps": 4,
            "num_images": 1,
        },
    )

    if "images" in result and len(result["images"]) > 0:
        image_url = result["images"][0]["url"]
    elif "image" in result:
        image_url = result["image"]["url"] if isinstance(result["image"], dict) else result["image"]
    else:
        raise ValueError(f"No image in Fal.ai response: {result}")

    output_path = TEMP_IMAGES_DIR / f"scene_{scene_index:03d}.png"
    response = requests.get(image_url)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    return str(output_path)


def generate_all_images(scenes: list) -> list:
    TEMP_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_paths = []
    for i, scene in enumerate(scenes):
        print(f"  Generating image for scene {i + 1}/{len(scenes)}...")
        path = generate_image(scene["image_prompt"], i)
        image_paths.append(path)
    return image_paths
