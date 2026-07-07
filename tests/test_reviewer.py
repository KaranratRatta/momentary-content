"""Tests for reviewer.py — image review and refinement loop.

No network calls: uses fake LLM and mocked generator.
"""

import json

import pytest

from reviewer import _parse_review, review_image


GOOD_REVIEW_JSON = json.dumps({
    "visual_quality": 4,
    "story_relevance": 5,
    "character_consistency": 4,
    "composition": 3,
    "engagement": 4,
    "overall_score": 4,
    "feedback": "Good composition, warm lighting works well.",
    "pass": True,
})

BAD_REVIEW_JSON = json.dumps({
    "visual_quality": 2,
    "story_relevance": 2,
    "character_consistency": 1,
    "composition": 2,
    "engagement": 2,
    "overall_score": 2,
    "feedback": "Character is barely visible, composition is off-center.",
    "pass": False,
})


def test_parse_review_valid_json():
    result = _parse_review(GOOD_REVIEW_JSON)
    assert result["overall_score"] == 4
    assert result["pass"] is True
    assert "Good composition" in result["feedback"]


def test_parse_review_fenced_json():
    raw = f'```json\n{BAD_REVIEW_JSON}\n```'
    result = _parse_review(raw)
    assert result["overall_score"] == 2
    assert result["pass"] is False


def test_parse_review_invalid_json_fallback():
    result = _parse_review("this is not json at all")
    assert result["overall_score"] == 2
    assert result["pass"] is False


def test_parse_review_partial_json():
    raw = 'some text "overall_score": 4 more text'
    result = _parse_review(raw)
    assert result["overall_score"] == 4
    assert result["pass"] is True


class FakeVisionLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def is_available(self):
        return True

    def chat_with_image(self, system, user_text, image_url):
        self.calls += 1
        return self.response


def test_review_image_returns_scores():
    llm = FakeVisionLLM(GOOD_REVIEW_JSON)
    result = review_image(
        image_url="https://example.com/image.png",
        prompt="A warm storybook illustration of a puppy.",
        narration="a puppy lost his parents",
        llm=llm,
    )
    assert llm.calls == 1
    assert result["overall_score"] == 4
    assert result["pass"] is True


def test_review_image_bad_score():
    llm = FakeVisionLLM(BAD_REVIEW_JSON)
    result = review_image(
        image_url="https://example.com/bad.png",
        prompt="A scene.",
        narration="something happened",
        llm=llm,
    )
    assert result["overall_score"] == 2
    assert result["pass"] is False
