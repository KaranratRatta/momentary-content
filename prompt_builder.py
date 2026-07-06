"""
prompt_builder.py — Stage 2: Build image prompts from script segments.

Uses an LLM (via OpenRouter) to write real visual *depictions* of each scene,
instead of dumping the narration text into a style template. Two-phase:

  1. Story bible (1 LLM call): a fixed character & visual description for the
     whole story — keeps characters looking the same across distant scenes
     (critical for long videos, ~100 images).
  2. Per-scene prompts (N LLM calls, in parallel): one vivid visual depiction
     per timestamp, using the bible + the segment's narration + the previous
     couple of segments for continuity.

If no OPENROUTER_API_KEY is set (or --no-llm is passed), it falls back to a
deliberately simple deterministic prompt so previews still work offline.

Output shape is unchanged: each segment gains a `prompt` field, so
prompts.json / generator.py / the manifest all keep working.
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from llm_client import LLMClient


# ─── Style helpers ───────────────────────────────────────────────────────────

def _get_character_instructions(style_config: Dict) -> str:
    """Extract character drawing rules from the style config."""
    rules = style_config.get("character_rules", [])
    if isinstance(rules, list):
        return "\n".join(f"- {r}" for r in rules)
    return ""


def _style_block(style_config: Dict) -> str:
    """A compact text rendering of the style template for the LLM."""
    base = (style_config.get("base_prompt") or "").strip()
    rules = _get_character_instructions(style_config)
    parts = [f"STYLE BASE:\n{base}"] if base else []
    if rules:
        parts.append(f"CHARACTER RULES:\n{rules}")
    return "\n\n".join(parts)


# ─── Story bible ─────────────────────────────────────────────────────────────

BIBLE_SYSTEM = (
    "You are a visual director for an illustrated story. Read the full script "
    "and produce a compact CHARACTER & VISUAL BIBLE that will keep every "
    "character looking identical across many scenes. Return ONLY valid JSON, "
    "no prose, no markdown fences. Schema:\n"
    "{\n"
    '  "theme": "one sentence describing the overall visual mood/palette",\n'
    '  "palette": "dominant colors and tone",\n'
    '  "characters": [\n'
    '    {"name": "...", "description": "fixed appearance: species, size, colors, '
    'proportions, distinguishing features", "role": "protagonist | supporting"}\n'
    "  ]\n"
    "}"
)


def _script_for_llm(segments: List[Dict]) -> str:
    """Render the full script with segment numbers + timestamps for the LLM."""
    lines = []
    for s in segments:
        lines.append(f"[{s['segment_index']}] {s['timestamp_str']} {s['text']}")
    return "\n".join(lines)


def _build_story_bible(
    segments: List[Dict],
    style_config: Dict,
    llm: LLMClient,
) -> Dict:
    """Call the LLM once to produce the story bible (or load a cached copy)."""
    user = (
        f"{_style_block(style_config)}\n\n"
        f"FULL SCRIPT:\n{_script_for_llm(segments)}\n\n"
        "Produce the character & visual bible as JSON. List every recurring "
        "character. Descriptions must be specific enough to reproduce the same "
        "character in every scene."
    )
    raw = llm.chat(BIBLE_SYSTEM, user)
    return _parse_bible(raw)


def _parse_bible(raw: str) -> Dict:
    """Best-effort JSON extraction from the LLM response."""
    text = raw.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("```", 2)
        # text[1] is the content between first and second fence
        text = text[1] if len(text) >= 2 else raw
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    # Fallback: keep the raw text so downstream still has something
    return {"theme": "", "palette": "", "characters": [], "raw": raw}


def _bible_block(bible: Dict) -> str:
    """Render the bible as text to embed in each scene prompt request."""
    lines = []
    if bible.get("theme"):
        lines.append(f"THEME: {bible['theme']}")
    if bible.get("palette"):
        lines.append(f"PALETTE: {bible['palette']}")
    chars = bible.get("characters") or []
    if chars:
        lines.append("CHARACTERS (keep these appearances EXACTLY):")
        for c in chars:
            name = c.get("name", "?")
            desc = c.get("description", "")
            lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


# ─── Per-scene prompts ───────────────────────────────────────────────────────

SCENE_SYSTEM = (
    "You write image-generation prompts for a single illustrated scene. "
    "Given a character/visual bible, a style, and one line of narration, "
    "write a vivid, concrete VISUAL DEPICTION of that exact moment — what is "
    "on screen, who is there, what they are doing, body language, expression, "
    "lighting, and setting. Do NOT repeat the narration verbatim; translate "
    "it into imagery. Keep every character's appearance pinned to the bible "
    "so they look identical across scenes. Bake the style in fully. "
    "Output ONLY the prompt text — no labels, no preface, no markdown."
)


def _build_scene_prompt(
    segment: Dict,
    bible: Dict,
    style_config: Dict,
    prev_segments: List[Dict],
    total: int,
    llm: LLMClient,
) -> str:
    """Call the LLM for one segment's image prompt."""
    idx = segment["segment_index"]
    user_parts = [
        _style_block(style_config),
        f"\nBIBLE:\n{_bible_block(bible)}" if _bible_block(bible) else "",
        f"\nSCENE POSITION: segment {idx + 1} of {total}.",
    ]
    if prev_segments:
        prev_lines = [f"- {p['text']}" for p in prev_segments]
        user_parts.append("\nIMMEDIATELY BEFORE THIS SCENE:\n" + "\n".join(prev_lines))
    user_parts.append(
        f"\nTHIS SCENE'S NARRATION: {segment['text']}\n\n"
        "Write the image prompt for THIS scene only."
    )
    user = "\n".join(p for p in user_parts if p)
    return llm.chat(SCENE_SYSTEM, user)


# ─── Offline fallback (no API key / --no-llm) ───────────────────────────────

def _fallback_prompt(segment: Dict, style_config: Dict) -> str:
    """
    Minimal deterministic prompt when the LLM is unavailable.
    Intentionally simple — NOT a second rule engine. Just enough to preview.
    """
    base = (style_config.get("base_prompt") or "").strip()
    rules = _get_character_instructions(style_config)
    parts = [p for p in (base, rules, f"Scene: {segment['text']}") if p]
    parts.append("Wide 16:9 landscape format.")
    return "\n\n".join(parts)


# ─── Orchestrator ────────────────────────────────────────────────────────────

def build_all_prompts(
    segments: List[Dict],
    style_config: Dict,
    llm: Optional[LLMClient] = None,
    concurrency: int = 8,
    bible_path: Optional[str] = None,
    use_llm: bool = True,
) -> List[Dict]:
    """
    Build prompts for all segments.

    With an LLM: build (or load) a story bible, then generate per-scene
    prompts in parallel. Without one (or use_llm=False): use the simple
    fallback so the pipeline still produces a prompts.json offline.
    """
    total = len(segments)
    results = [dict(seg) for seg in segments]  # copy, preserve order

    # ── Offline / forced fallback path ──────────────────────────────────────
    if not use_llm or llm is None or not llm.is_available():
        if use_llm:
            print("   ⚠ no OPENROUTER_API_KEY — using simple offline fallback prompts.")
        for r in results:
            r["prompt"] = _fallback_prompt(r, style_config)
        return results

    # ── LLM path ────────────────────────────────────────────────────────────
    bible: Dict = {}
    if bible_path and Path(bible_path).exists():
        try:
            bible = json.loads(Path(bible_path).read_text())
            print(f"   ♻  Loaded cached story bible: {bible_path}")
        except (json.JSONDecodeError, OSError):
            bible = {}

    if not bible:
        print(f"   📖 Building story bible (1 LLM call)...")
        bible = _build_story_bible(segments, style_config, llm)
        if bible_path:
            Path(bible_path).parent.mkdir(parents=True, exist_ok=True)
            Path(bible_path).write_text(json.dumps(bible, indent=2))
            print(f"   Saved bible: {bible_path}")

    print(f"   ✏️  Generating {total} scene prompts ({concurrency} in parallel)...")

    def _task(i: int):
        seg = results[i]
        prev = [results[j] for j in range(max(0, i - 2), i)]
        return i, _build_scene_prompt(seg, bible, style_config, prev, total, llm)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(_task, i): i for i in range(total)}
        for future in as_completed(futures):
            i, prompt = future.result()
            results[i]["prompt"] = prompt
            print(f"   ✓ [{i + 1}/{total}] {results[i]['timestamp_str']}")

    return results


# ─── CLI usage ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()  # load OPENROUTER_API_KEY from .env if present

    parser = argparse.ArgumentParser(
        description="Build image prompts from script segments (LLM-powered).",
    )
    parser.add_argument("segments_path", nargs="?", default="output/segments.json",
                        help="Path to segments.json")
    parser.add_argument("style_path", nargs="?", default="styles/ms_paint.yaml",
                        help="Path to style YAML")
    parser.add_argument("--no-llm", action="store_true",
                        help="Use the simple offline fallback (no API key needed)")
    parser.add_argument("--concurrency", type=int, default=8,
                        help="Parallel LLM calls for scene prompts")
    parser.add_argument("--bible-path", default=None,
                        help="Where to load/save the story bible JSON")
    args = parser.parse_args()

    segments = json.loads(Path(args.segments_path).read_text())
    style_config = yaml.safe_load(Path(args.style_path).read_text())

    llm = None if args.no_llm else LLMClient.from_config({})
    result = build_all_prompts(
        segments, style_config,
        llm=llm, concurrency=args.concurrency,
        bible_path=args.bible_path,
        use_llm=not args.no_llm,
    )
    print(json.dumps(result, indent=2))
