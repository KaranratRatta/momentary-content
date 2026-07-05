"""
generator.py — Stage 3: Generate images from prompts via FAL API.

Takes a list of segments with prompts, calls fal-ai/flux/schnell (or any
FAL model) in parallel, and saves the images to disk.

Outputs:
  - Images saved to output_dir as <segment_index>_<timestamp>.jpg
  - manifest.json mapping timestamp → image_path
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.error


FAL_BASE_URL = "https://fal.run"


def _call_fal_sync(prompt: str, model: str, params: dict) -> Optional[str]:
    """
    Call FAL API synchronously. Returns the image URL or None on failure.
    """
    url = f"{FAL_BASE_URL}/{model}"
    headers = {
        "Authorization": f"Key {os.environ.get('FAL_KEY', '')}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "image_size": params.get("image_size", "landscape_16_9"),
        "num_inference_steps": params.get("num_inference_steps", 4),
    }

    if params.get("sync_mode") == "async":
        # For future: async queue support
        pass

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        images = result.get("images", [])
        if images:
            return images[0]["url"]
        print(f"  ⚠ No images in response: {result.get('detail', 'unknown')}")
        return None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  ✗ HTTP {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def _download_image(url: str, save_path: str) -> bool:
    """Download image from URL to local path. Returns True on success."""
    try:
        urllib.request.urlretrieve(url, save_path)
        return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False


def generate_images(
    segments: List[Dict],
    output_dir: str = "./output",
    model: str = "fal-ai/flux/schnell",
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
        params: Additional FAL parameters (image_size, num_inference_steps, etc.).

    Returns:
        List of segments with 'image_path' and 'image_url' fields added.
    """
    params = params or {}
    img_dir = Path(output_dir) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(segments)
    completed = 0
    failed = 0

    print(f"\n🎨 Generating {total} images with {concurrency} workers...")
    start = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_map = {}

        for seg in segments:
            prompt = seg.get("prompt", seg.get("text", ""))
            idx = seg["segment_index"]
            ts = seg["timestamp_str"].replace(":", "-")
            filename = f"{idx:03d}_{ts}.jpg"

            future = executor.submit(_call_fal_sync, prompt, model, params)
            future_map[future] = (seg, filename)

        for future in as_completed(future_map):
            seg, filename = future_map[future]
            image_url = future.result()

            if image_url:
                save_path = str(img_dir / filename)
                if _download_image(image_url, save_path):
                    seg["image_url"] = image_url
                    seg["image_path"] = save_path
                    completed += 1
                    print(f"  ✓ [{completed}/{total}] {seg['timestamp_str']} — {filename}")
                else:
                    failed += 1
                    print(f"  ✗ [{completed+failed}/{total}] Download failed: {seg['timestamp_str']}")
            else:
                failed += 1
                print(f"  ✗ [{completed+failed}/{total}] Generation failed: {seg['timestamp_str']}")

    elapsed = time.time() - start
    print(f"\n✅ Done: {completed} succeeded, {failed} failed in {elapsed:.1f}s")

    # Write manifest
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

    prompts_path = sys.argv[1] if len(sys.argv) > 1 else "output/prompts.json"
    segments = json.loads(Path(prompts_path).read_text())
    generate_images(segments)