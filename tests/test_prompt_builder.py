"""Tests for prompt_builder.py — LLM scene prompts + offline fallback.

No network calls: the LLM path uses a FakeLLM (duck-typed), and the offline
fallback path needs no key at all.
"""

import json
from pathlib import Path

import pytest

import prompt_builder as pb


STYLE = {
    "name": "ms_paint",
    "base_prompt": "MS Paint style. Thick outlines. Flat colors.",
    "character_rules": [
        "Draw stick figures with round heads",
        "Never draw humans unless mentioned",
    ],
}

SEGMENTS = [
    {"timestamp_str": "00:00:00", "timestamp_seconds": 0, "text": "a puppy lost his parents", "segment_index": 0},
    {"timestamp_str": "00:00:02", "timestamp_seconds": 2, "text": "he found a duck", "segment_index": 1},
    {"timestamp_str": "00:00:04", "timestamp_seconds": 4, "text": "the duck comforted him", "segment_index": 2},
]


# ─── Pure helpers ────────────────────────────────────────────────────────────

def test_style_block_has_base_and_rules():
    block = pb._style_block(STYLE)
    assert "MS Paint style" in block
    assert "stick figures" in block
    assert "Never draw humans" in block


def test_script_for_llm_includes_index_and_text():
    out = pb._script_for_llm(SEGMENTS)
    assert "[0] 00:00:00 a puppy lost his parents" in out
    assert "[2] 00:00:04 the duck comforted him" in out


def test_bible_block_renders_characters():
    bible = {
        "theme": "innocent friendship",
        "palette": "brown and yellow",
        "characters": [
            {"name": "Puppy", "description": "small brown", "role": "protagonist"},
            {"name": "Duck", "description": "yellow", "role": "supporting"},
        ],
    }
    block = pb._bible_block(bible)
    assert "THEME: innocent friendship" in block
    assert "PALETTE: brown and yellow" in block
    assert "Puppy: small brown" in block
    assert "Duck: yellow" in block


def test_bible_block_empty():
    assert pb._bible_block({}) == ""


# ─── _parse_bible ─────────────────────────────────────────────────────────────

def test_parse_bible_plain_json():
    raw = '{"theme":"t","palette":"p","characters":[{"name":"X","description":"d","role":"r"}]}'
    bible = pb._parse_bible(raw)
    assert bible["theme"] == "t"
    assert bible["characters"][0]["name"] == "X"


def test_parse_bible_fenced_json():
    raw = '```json\n{"theme":"t","palette":"p","characters":[]}\n```'
    bible = pb._parse_bible(raw)
    assert bible["theme"] == "t"
    assert bible["characters"] == []


def test_parse_bible_invalid_returns_raw():
    bible = pb._parse_bible("not json at all")
    assert "raw" in bible
    assert bible["raw"] == "not json at all"
    assert bible["characters"] == []


# ─── Fallback prompt (no LLM) ─────────────────────────────────────────────────

def test_fallback_prompt_includes_style_and_scene():
    seg = SEGMENTS[1]
    prompt = pb._fallback_prompt(seg, STYLE)
    assert "MS Paint style" in prompt
    assert "he found a duck" in prompt
    assert "16:9" in prompt


def test_build_all_prompts_fallback_no_llm():
    """With no LLM client, every segment gets a fallback prompt."""
    results = pb.build_all_prompts(SEGMENTS, STYLE, llm=None)
    assert len(results) == 3
    for r, seg in zip(results, SEGMENTS):
        assert r["prompt"]  # non-empty
        assert r["text"] == seg["text"]              # original fields preserved
        assert r["segment_index"] == seg["segment_index"]
        assert r["timestamp_str"] == seg["timestamp_str"]


def test_build_all_prompts_use_llm_false_forces_fallback():
    """Even with an LLM, use_llm=False uses the fallback."""
    class BoomLLM:
        def is_available(self):
            return True
        def chat(self, system, user):
            raise AssertionError("LLM should not be called when use_llm=False")
    results = pb.build_all_prompts(SEGMENTS, STYLE, llm=BoomLLM(), use_llm=False)
    assert all(r["prompt"] for r in results)


# ─── LLM path with a fake client (no network) ─────────────────────────────────

class FakeLLM:
    """Duck-typed LLM that returns canned bible JSON + scene text."""

    def __init__(self, allow_bible=True):
        self.allow_bible = allow_bible
        self.calls = 0

    def is_available(self):
        return True

    def chat(self, system, user):
        self.calls += 1
        if "BIBLE" in system:
            if not self.allow_bible:
                raise AssertionError("bible should be loaded from cache, not rebuilt")
            return json.dumps({
                "theme": "t", "palette": "p",
                "characters": [{"name": "Puppy", "description": "small brown", "role": "protagonist"}],
            })
        return "A vivid visual depiction of the scene."


def test_build_all_prompts_llm_path_attaches_prompts(tmp_path):
    bible_path = str(tmp_path / "story_bible.json")
    llm = FakeLLM()
    results = pb.build_all_prompts(SEGMENTS, STYLE, llm=llm, bible_path=bible_path)
    # 1 bible call + 3 scene calls
    assert llm.calls == 4
    assert all(r["prompt"] == "A vivid visual depiction of the scene." for r in results)
    # bible persisted to disk
    saved = json.loads(Path(bible_path).read_text())
    assert saved["characters"][0]["name"] == "Puppy"
    # results keep original order/fields
    assert [r["segment_index"] for r in results] == [0, 1, 2]


def test_build_all_prompts_caches_bible(tmp_path):
    """A second run reuses the cached bible instead of rebuilding it."""
    bible_path = str(tmp_path / "story_bible.json")

    first = FakeLLM(allow_bible=True)
    pb.build_all_prompts(SEGMENTS, STYLE, llm=first, bible_path=bible_path)
    assert first.calls == 4  # 1 bible + 3 scenes

    # Second run: bible is loaded from disk, so the bible chat must NOT happen.
    second = FakeLLM(allow_bible=False)
    pb.build_all_prompts(SEGMENTS, STYLE, llm=second, bible_path=bible_path)
    assert second.calls == 3  # scene calls only — no bible rebuild


def test_build_all_prompts_llm_unavailable_falls_back(tmp_path):
    class NoKeyLLM:
        def is_available(self):
            return False
        def chat(self, *a, **k):
            raise AssertionError("should not call LLM when unavailable")
    results = pb.build_all_prompts(
        SEGMENTS, STYLE, llm=NoKeyLLM(), bible_path=str(tmp_path / "b.json")
    )
    # Falls back to deterministic prompts, not LLM calls.
    assert all("MS Paint style" in r["prompt"] for r in results)
