"""Tests for generator.py — FAL API image generation.

No network calls: _call_fal_sync is not tested directly (needs mocking urllib).
Tests focus on payload building and image saving.
"""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from generator import _build_payload, _save_image, generate_single_image


def test_build_payload_krea_no_steps():
    payload = _build_payload(
        "a cute puppy",
        "fal-ai/krea-2/turbo",
        {"image_size": "landscape_16_9", "output_format": "png"},
    )
    assert payload["prompt"] == "a cute puppy"
    assert payload["image_size"] == "landscape_16_9"
    assert payload["output_format"] == "png"
    assert "num_inference_steps" not in payload


def test_build_payload_krea_with_expansion():
    payload = _build_payload(
        "a cute puppy",
        "fal-ai/krea-2/turbo",
        {"image_size": "landscape_16_9", "enable_prompt_expansion": True},
    )
    assert payload["enable_prompt_expansion"] is True
    assert "num_inference_steps" not in payload


def test_build_payload_flux_schnell_has_steps():
    payload = _build_payload(
        "a cute puppy",
        "fal-ai/flux/schnell",
        {"image_size": "landscape_16_9", "num_inference_steps": 4},
    )
    assert payload["num_inference_steps"] == 4
    assert "enable_prompt_expansion" not in payload


def test_build_payload_flux_dev_has_steps_and_guidance():
    payload = _build_payload(
        "a scene",
        "fal-ai/flux/dev",
        {"num_inference_steps": 28, "guidance_scale": 3.5},
    )
    assert payload["num_inference_steps"] == 28
    assert payload["guidance_scale"] == 3.5


def test_build_payload_defaults():
    payload = _build_payload("test", "fal-ai/flux/schnell", {})
    assert payload["image_size"] == "landscape_16_9"
    assert payload["output_format"] == "png"
    assert payload["num_inference_steps"] == 4


def test_save_image_png(tmp_path):
    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)

    save_path = str(tmp_path / "test.png")
    assert _save_image(buf.read(), save_path, "PNG") is True
    assert Path(save_path).exists()

    loaded = Image.open(save_path)
    assert loaded.size == (100, 100)


def test_save_image_invalid_bytes():
    assert _save_image(b"not an image", "/tmp/bad.png") is False
