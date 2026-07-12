"""Tests for script generator prompt construction."""

import pytest
from momentary.script_generator import _build_system_prompt


def test_prompt_without_target_duration():
    """Prompt should not contain 'None' when target_duration_seconds is not provided."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=None,
        video_idea=""
    )
    assert "None" not in prompt, "Prompt contains 'None' literal"
    assert "seconds length" not in prompt, "Prompt mentions seconds when no duration provided"


def test_prompt_with_target_duration():
    """Prompt should include duration info when target_duration_seconds is provided."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "30 seconds" in prompt or "30.0 seconds" in prompt, "Prompt should mention target duration"
    assert "None" not in prompt, "Prompt contains 'None' literal"


def test_prompt_with_research_context():
    """Prompt should include research context and guidance about selective usage."""
    research = "Fact 1: Something interesting. Fact 2: Another fact."
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context=research,
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "Fact 1" in prompt, "Research context should be included"
    assert "Fact 2" in prompt, "Research context should be included"
    assert "do NOT need to use all" in prompt or "select only" in prompt.lower(), "Should guide LLM to be selective with research"


def test_prompt_with_video_idea():
    """Prompt should include video idea when provided."""
    idea = "Focus on layer 2 solutions and scalability"
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=idea
    )
    assert "layer 2" in prompt.lower() or "scalability" in prompt.lower(), "Video idea should be included"


def test_prompt_without_video_idea():
    """Prompt should not contain video idea section when not provided."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "VIDEO IDEA / FOCUS" not in prompt, "Should not include video idea section when empty"


def test_prompt_scene_count():
    """Prompt should mention the correct number of scenes."""
    prompt = _build_system_prompt(
        num_scenes=15,
        theme="Educational",
        research_context="",
        target_duration_seconds=120.0,
        video_idea=""
    )
    assert "15 scenes" in prompt, "Prompt should mention correct scene count"


def test_prompt_theme():
    """Prompt should include the narration theme description."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Humorous",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "humorous" in prompt.lower() or "Humorous" in prompt, "Prompt should include theme"


def test_prompt_image_guidelines():
    """Prompt should always include image prompt guidelines."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=None,
        video_idea=""
    )
    assert "stick figures" in prompt.lower(), "Should mention stick figures"
    assert "Animals" in prompt or "animals" in prompt, "Should mention animals"
    assert "NOT stick figures" in prompt or "not stick figures" in prompt, "Should clarify animals are not stick figures"


def test_prompt_json_format():
    """Prompt should include JSON format example."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert '"title"' in prompt, "Should include title in JSON example"
    assert '"scenes"' in prompt, "Should include scenes in JSON example"
    assert '"narration"' in prompt, "Should include narration in JSON example"
    assert '"image_prompt"' in prompt, "Should include image_prompt in JSON example"
    assert '"duration_hint"' in prompt, "Should include duration_hint in JSON example"
    assert '"description"' in prompt, "Should include description in JSON example"
    assert '"thumbnail_prompt"' in prompt, "Should include thumbnail_prompt in JSON example"


def test_prompt_description_guidelines():
    """Prompt should include guidelines for writing YouTube description."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "DESCRIPTION" in prompt or "description" in prompt.lower(), "Should mention description"
    assert "hook" in prompt.lower() or "curiosity" in prompt.lower(), "Should mention hook/curiosity for description"
    assert "hashtag" in prompt.lower() or "#" in prompt, "Should mention hashtags"


def test_prompt_thumbnail_guidelines():
    """Prompt should include guidelines for creating thumbnail prompt."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "THUMBNAIL" in prompt or "thumbnail" in prompt.lower(), "Should mention thumbnail"
    assert "eye-catching" in prompt.lower() or "attention" in prompt.lower(), "Should mention eye-catching/attention"


def test_prompt_no_none_leakage():
    """Comprehensive test: ensure 'None' never appears in any prompt variation."""
    test_cases = [
        {"num_scenes": 3, "theme": "Educational", "research_context": "", "target_duration_seconds": None, "video_idea": ""},
        {"num_scenes": 3, "theme": "Educational", "research_context": "", "target_duration_seconds": 30.0, "video_idea": ""},
        {"num_scenes": 3, "theme": "Humorous", "research_context": "Some research", "target_duration_seconds": None, "video_idea": ""},
        {"num_scenes": 3, "theme": "Dramatic", "research_context": "Some research", "target_duration_seconds": 60.0, "video_idea": "Focus on X"},
        {"num_scenes": 10, "theme": "Documentary", "research_context": "", "target_duration_seconds": 120.0, "video_idea": ""},
    ]
    for i, kwargs in enumerate(test_cases):
        prompt = _build_system_prompt(**kwargs)
        assert "None" not in prompt, f"Test case {i}: Prompt contains 'None' literal with kwargs={kwargs}"


def test_prompt_duration_calculation():
    """Prompt should calculate correct average seconds per scene."""
    prompt = _build_system_prompt(
        num_scenes=6,
        theme="Educational",
        research_context="",
        target_duration_seconds=60.0,
        video_idea=""
    )
    assert "10 seconds" in prompt or "10.0 seconds" in prompt, "Should calculate 60/6=10 seconds per scene"


def test_prompt_research_selective_guidance():
    """Research section should explicitly tell LLM to be selective."""
    prompt = _build_system_prompt(
        num_scenes=7,
        theme="Educational",
        research_context="Fact A, Fact B, Fact C",
        target_duration_seconds=30.0,
        video_idea=""
    )
    assert "do NOT need to use all" in prompt or "select" in prompt.lower(), "Should guide selective usage of research"
    assert "fit the target video length" in prompt or "video length" in prompt.lower(), "Should mention fitting video length"
