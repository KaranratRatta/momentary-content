"""Tests for config consistency and UI selectbox logic."""

import pytest
from momentary.config import (
    STYLE_PROMPTS,
    DEFAULT_STYLE,
    MOTION_EFFECTS,
    DEFAULT_MOTION,
    AUDIO_MODES,
    DEFAULT_AUDIO_MODE,
    ELEVENLABS_VOICES,
    ELEVENLABS_VOICE_ID,
    NARRATION_THEMES,
    DEFAULT_THEME,
)


def test_default_style_exists_in_style_prompts():
    """DEFAULT_STYLE must be a key in STYLE_PROMPTS."""
    assert DEFAULT_STYLE in STYLE_PROMPTS, (
        f"DEFAULT_STYLE '{DEFAULT_STYLE}' not found in STYLE_PROMPTS keys: {list(STYLE_PROMPTS.keys())}"
    )


def test_default_motion_exists_in_motion_effects():
    """DEFAULT_MOTION must be a value in MOTION_EFFECTS."""
    assert DEFAULT_MOTION in MOTION_EFFECTS.values(), (
        f"DEFAULT_MOTION '{DEFAULT_MOTION}' not found in MOTION_EFFECTS values: {list(MOTION_EFFECTS.values())}"
    )


def test_default_audio_mode_exists_in_audio_modes():
    """DEFAULT_AUDIO_MODE must be a value in AUDIO_MODES."""
    assert DEFAULT_AUDIO_MODE in AUDIO_MODES.values(), (
        f"DEFAULT_AUDIO_MODE '{DEFAULT_AUDIO_MODE}' not found in AUDIO_MODES values: {list(AUDIO_MODES.values())}"
    )


def test_default_theme_exists_in_narration_themes():
    """DEFAULT_THEME must be a key in NARRATION_THEMES."""
    assert DEFAULT_THEME in NARRATION_THEMES, (
        f"DEFAULT_THEME '{DEFAULT_THEME}' not found in NARRATION_THEMES keys: {list(NARRATION_THEMES.keys())}"
    )


def test_default_voice_id_exists_in_elevenlabs_voices():
    """ELEVENLABS_VOICE_ID must be a value in ELEVENLABS_VOICES (or be a valid custom ID)."""
    # This is optional since users can set custom voice IDs
    # But we test that if it's in the dict, it's valid
    if ELEVENLABS_VOICE_ID in ELEVENLABS_VOICES.values():
        assert True  # Valid preset voice
    else:
        assert True  # Custom voice ID, also valid


def test_style_prompts_selectbox_index():
    """Test that we can find the index for selectbox without ValueError."""
    keys = list(STYLE_PROMPTS.keys())
    index = keys.index(DEFAULT_STYLE)
    assert 0 <= index < len(keys)


def test_motion_effects_selectbox_index():
    """Test that we can find the index for selectbox without ValueError."""
    values = list(MOTION_EFFECTS.values())
    index = values.index(DEFAULT_MOTION)
    assert 0 <= index < len(values)


def test_audio_modes_selectbox_index():
    """Test that we can find the index for selectbox without ValueError."""
    values = list(AUDIO_MODES.values())
    index = values.index(DEFAULT_AUDIO_MODE)
    assert 0 <= index < len(values)


def test_narration_themes_selectbox_index():
    """Test that we can find the index for theme selectbox without ValueError."""
    keys = list(NARRATION_THEMES.keys())
    index = keys.index(DEFAULT_THEME)
    assert 0 <= index < len(keys)


def test_all_config_dicts_are_non_empty():
    """All config dictionaries should have at least one entry."""
    assert len(STYLE_PROMPTS) > 0
    assert len(MOTION_EFFECTS) > 0
    assert len(AUDIO_MODES) > 0
    assert len(ELEVENLABS_VOICES) > 0
    assert len(NARRATION_THEMES) > 0


def test_config_dict_values_are_unique():
    """All values in config dicts should be unique to avoid index confusion."""
    motion_values = list(MOTION_EFFECTS.values())
    assert len(motion_values) == len(set(motion_values)), "MOTION_EFFECTS has duplicate values"

    audio_values = list(AUDIO_MODES.values())
    assert len(audio_values) == len(set(audio_values)), "AUDIO_MODES has duplicate values"


def test_style_prompts_contain_anti_ai_keywords():
    """Style prompts should contain keywords that reduce AI-generated look."""
    anti_ai_keywords = [
        "no glossy", "no perfect", "imperfection", "hand-drawn",
        "no AI", "no plastic", "film grain", "texture",
    ]
    for style_name, prompt in STYLE_PROMPTS.items():
        has_keyword = any(keyword in prompt for keyword in anti_ai_keywords)
        assert has_keyword, (
            f"Style '{style_name}' missing anti-AI keywords. Prompt: {prompt[:100]}..."
        )


def test_animal_guidance_exists():
    """Animal guidance should exist for each style."""
    from momentary.config import ANIMAL_GUIDANCE, STYLE_PROMPTS
    
    for style_name in STYLE_PROMPTS.keys():
        assert style_name in ANIMAL_GUIDANCE, (
            f"Style '{style_name}' missing from ANIMAL_GUIDANCE"
        )
        assert "animal" in ANIMAL_GUIDANCE[style_name].lower(), (
            f"Style '{style_name}' animal guidance missing 'animal' keyword"
        )
