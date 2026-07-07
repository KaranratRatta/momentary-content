"""
generator.py — Stage 3: Generate images from prompts via FAL API.

Takes a list of segments with prompts, calls a FAL model (default: krea-2/turbo)
in parallel, and saves the images to disk as PNG.

Outputs:
  - Images saved to output_dir as <segment_index>_<timestamp>.png
  - manifest.json mapping timestamp → image_path
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import urllib.request
import urllib.error

from PIL import Image


FAL_BASE_URL = "https://fal.run"

MODELS_WITHOUT_STEPS = {"fal-ai/krea-2/turbo", "fal-ai/krea-2"}


def _build_payload(prompt: str, model: str, params: dict) -> dict:
    """Build the right API payload based on the model's schema."""
    payload = {
        "prompt": prompt,
        "image_size": params.get("image_size", "landscape_16_9"),
        "output_format": params.get("output_format", "png"),
    }

    if model in MODELS_WITHOUT_STEPS:
        if "enable_prompt_expansion" in params:
            payload["enable_prompt_expansion"] = params["enable_prompt_expansion"]
        if "acceleration" in params:
            payload["acceleration"] = params["acceleration"]
    else:
        payload["num_inference_steps"] = params.get("num_inference_steps", 4)
        if "guidance_scale" in params:
            payload["guidance_scale"] = params["guidance_scale"]

    return payload


def _call_fal_sync(prompt: str, model: str, params: dict) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Call FAL API synchronously. Returns (image_bytes, image_url) or (None, None) on failure.
    """
    url = f"{FAL_BASE_URL}/{model}"
    headers = {
        "Authorization": f"Key {os.environ.get('FAL_KEY', '')}",
        "Content-Type": "application/json",
    }

    payload = _build_payload(prompt, model, params)

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        images = result.get("images", [])
        if not images:
            print(f"  ⚠ No images in response: {result.get('detail', 'unknown')}")
            return None, None

        image_url = images[0]["url"]

        img_req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(img_req, timeout=120) as img_resp:
            return img_resp.read(), image_url

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  ✗ HTTP {e.code}: {body[:200]}")
        return None, None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, None


def _save_image(image_bytes: bytes, save_path: str, fmt: str = "PNG") -> bool:
    """Save image bytes to disk. Returns True on success."""
    try:
        img = Image.open(BytesIO(image_bytes))
        img.save(save_path, fmt)
        return True
    except Exception as e:
        print(f"  ✗ Image save failed: {e}")
        return False


def generate_single_image(
    prompt: str,
    save_path: str,
    model: str = "fal-ai/krea-2/turbo",
    params: Optional[Dict] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Generate a single image. Used by the reviewer for retries.

    Returns:
        (success, image_url)
    """
    params = params or {}
    image_bytes, image_url = _call_fal_sync(prompt, model, params)
    if image_bytes and _save_image(image_bytes, save_path):
        return True, image_url
    return False, None


def generate_images(
    segments: List[Dict],
    output_dir: str = "./output",
    model: str = "fal-ai/krea-2/turbo",
    concurrency: int = 8,
    params: Optional[Dict] = None,
) -> List[Dict]:
    """
    Generate images for all segments in parallel.

    Args:
        segments: List of dicts with at least 'prompt', 'timestamp_str', 'segment_index'.
        output_dir: Where to save images and manifest.
        model: FAL model endpoint.
        concurrency: Max parallel requests.
        params: Additional FAL parameters (image_size, output_format, etc.).

    Returns:
        List of segments with 'image_path' and 'image_url' fields added.
    """
    params = params or {}
    img_dir = Path(output_dir) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    total = len(segments)
    completed = 0
    failed = 0

    print(f"\n🎨 Generating {total} images with {concurrency} workers...")
    print(f"   Model: {model}")
    start = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_map = {}

        for seg in segments:
            prompt = seg.get("prompt", seg.get("text", ""))
            idx = seg["segment_index"]
            ts = seg["timestamp_str"].replace(":", "-")
            filename = f"{idx:03d}_{ts}.png"

            future = executor.submit(_call_fal_sync, prompt, model, params)
            future_map[future] = (seg, filename)

        for future in as_completed(future_map):
            seg, filename = future_map[future]
            image_bytes, image_url = future.result()

            if image_bytes:
                save_path = str(img_dir / filename)
                if _save_image(image_bytes, save_path):
                    seg["image_url"] = image_url or "saved locally"
                    seg["image_path"] = save_path
                    completed += 1
                    print(f"  ✓ [{completed}/{total}] {seg['timestamp_str']} — {filename}")
                else:
                    failed += 1
                    print(f"  ✗ [{completed+failed}/{total}] Save failed: {seg['timestamp_str']}")
            else:
                failed += 1
                print(f"  ✗ [{completed+failed}/{total}] Generation failed: {seg['timestamp_str']}")

    elapsed = time.time() - start
    print(f"\n✅ Done: {completed} succeeded, {failed} failed in {elapsed:.1f}s")

    manifest = [
        {
            "timestamp_str": seg["timestamp_str"],
            "timestamp_seconds": seg["timestamp_seconds"],
            "text": seg["text"],
            "image_path": seg.get("image_path", ""),
            "image_url": seg.get("image_url", ""),
            "segment_index": seg["segment_index"],
        }
        for seg in segments
    ]
    manifest_path = Path(output_dir) / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"📄 Manifest written: {manifest_path}")

    return segments


# ─── CLI usage ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    prompts_path = sys.argv[1] if len(sys.argv) > 1 else "output/prompts.json"
    segments = json.loads(Path(prompts_path).read_text())
    generate_images(segments)
