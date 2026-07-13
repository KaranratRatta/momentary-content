import requests
import fal_client
from pathlib import Path
from momentary.config import FAL_IMAGE_MODEL, STYLE_PROMPTS, DEFAULT_STYLE, VIDEO_WIDTH, VIDEO_HEIGHT


def generate_image(scene_prompt: str, scene_index: int, model: str | None = None, style: str | None = None, append_style: bool = False, run_dir: Path | None = None) -> str:
    if append_style:
        style_name = style or DEFAULT_STYLE
        style_prompt = STYLE_PROMPTS.get(style_name, STYLE_PROMPTS[DEFAULT_STYLE])
        full_prompt = f"{scene_prompt}, {style_prompt}"
    else:
        full_prompt = scene_prompt

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


def generate_all_images(scenes: list, model: str | None = None, style: str | None = None, append_style: bool = False, run_dir: Path | None = None) -> list:
    if run_dir:
        images_dir = run_dir / "images"
    else:
        images_dir = Path("temp/images")

    images_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []
    for i, scene in enumerate(scenes):
        print(f"  Generating image for scene {i + 1}/{len(scenes)}...")
        path = generate_image(scene["image_prompt"], i, model, style, append_style, run_dir)
        image_paths.append(path)
    return image_paths


def generate_thumbnail(thumbnail_prompt: str, model: str | None = None, style: str | None = None, append_style: bool = False, thumbnail_text: str = "", run_dir: Path | None = None) -> str:
    if append_style:
        style_name = style or DEFAULT_STYLE
        style_prompt = STYLE_PROMPTS.get(style_name, STYLE_PROMPTS[DEFAULT_STYLE])
        full_prompt = f"{thumbnail_prompt}, {style_prompt}"
    else:
        full_prompt = thumbnail_prompt
    
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
        output_path = run_dir / "thumbnail.png"
    else:
        output_path = Path("temp") / "thumbnail.png"

    response = requests.get(image_url)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    img = Image.open(io.BytesIO(response.content))
    
    if thumbnail_text:
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), thumbnail_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (img.width - text_width) // 2
        y = img.height - text_height - 100
        
        for offset_x in range(-5, 6):
            for offset_y in range(-5, 6):
                draw.text((x + offset_x, y + offset_y), thumbnail_text, font=font, fill="black")
        
        draw.text((x, y), thumbnail_text, font=font, fill="yellow")
    
    img.save(output_path)

    return str(output_path)
