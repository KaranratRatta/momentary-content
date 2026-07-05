"""
prompt_builder.py — Stage 2: Build image prompts from segments + style template.

Takes parsed segments and a style config, then generates a tailored prompt
for each segment that captures:
  - What's being said at that moment
  - The emotion / tone
  - The story stage (setup, conflict, turning point, resolution)
  - Character consistency

Uses keyword-based analysis (no external API needed). Can be upgraded to use
an LLM for smarter analysis by setting use_llm: true in config.
"""

from pathlib import Path
from typing import List, Dict, Optional
import yaml


# ─── Emotion/keyword mappings ───────────────────────────────────────────────
EMOTION_KEYWORDS = {
    "sad": ["lost", "alone", "sad", "cry", "tear", "lonely", "abandoned", "gone", "missing"],
    "happy": ["happy", "joy", "excited", "fun", "laugh", "smile", "great", "wonderful", "celebrate"],
    "scared": ["scared", "afraid", "shivering", "cold", "frightened", "panic", "terrified", "danger"],
    "confused": ["confused", "didn't know", "unsure", "what to do", "strange", "weird", "why"],
    "hopeful": ["help", "comfort", "kind", "warm", "safe", "rescue", "save", "together", "friend"],
    "tense": ["wait", "suddenly", "but", "however", "problem", "trouble", "conflict"],
    "surprised": ["surprise", "suddenly", "wow", "unexpected", "amazed", "shocked", "incredible"],
}

STORY_STAGES = {
    "setup": ["once upon", "there was", "lived", "started", "began", "first", "morning", "day"],
    "conflict": ["problem", "but", "however", "unfortunately", "lost", "alone", "didn't know", "scared", "trouble"],
    "turning_point": ["then", "found", "met", "appeared", "came", "arrived", "help", "suddenly", "discovered"],
    "resolution": ["comfort", "together", "safe", "happy", "finally", "saved", "friend", "home", "heart", "love"],
}


def _detect_emotion(text: str) -> str:
    """Return the dominant emotion from the text."""
    text_lower = text.lower()
    scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        scores[emotion] = sum(1 for kw in keywords if kw in text_lower)
    return max(scores, key=scores.get) if any(scores.values()) else "neutral"


def _detect_story_stage(text: str, segment_index: int, total_segments: int) -> str:
    """Detect story stage based on content + position in the sequence."""
    text_lower = text.lower()
    for stage, keywords in STORY_STAGES.items():
        for kw in keywords:
            if kw in text_lower:
                return stage
    # Fallback based on position
    if total_segments <= 1:
        return "setup"
    progress = segment_index / total_segments
    if progress < 0.25:
        return "setup"
    elif progress < 0.5:
        return "conflict"
    elif progress < 0.75:
        return "turning_point"
    else:
        return "resolution"


def _get_character_instructions(style_config: Dict) -> str:
    """Extract character drawing rules from the style config."""
    rules = style_config.get("character_rules", [])
    if isinstance(rules, list):
        return "\n".join(f"- {r}" for r in rules)
    return ""


def build_prompt(
    segment: Dict,
    style_config: Dict,
    segment_index: int,
    total_segments: int,
    previous_characters: Optional[List[str]] = None,
) -> str:
    """
    Build a single image prompt for one segment.

    Args:
        segment: {timestamp_seconds, timestamp_str, text, segment_index}
        style_config: Parsed YAML dict from a style file.
        segment_index: Index in the full sequence.
        total_segments: Total number of segments.
        previous_characters: Characters mentioned in earlier segments (for consistency).

    Returns:
        A complete prompt string ready to send to the image API.
    """
    text = segment["text"]
    emotion = _detect_emotion(text)
    story_stage = _detect_story_stage(text, segment_index, total_segments)
    base = style_config.get("base_prompt", "")
    char_rules = _get_character_instructions(style_config)

    # Build the prompt
    parts = [
        base,
        char_rules,
        f"\nStory stage: {story_stage}. Emotion: {emotion}.",
        f"\nShow this specific moment: {text}",
    ]

    # Add character consistency if we have history
    if previous_characters:
        chars = ", ".join(previous_characters)
        parts.append(f"\nKeep these characters consistent: {chars}")

    # Add emotion-specific visual cues
    emotion_cues = {
        "sad": "Draw a tear or droopy posture. Use simple sad expression.",
        "happy": "Draw a smile. Use simple happy expression with upward curve.",
        "scared": "Show shivering or wide eyes. Tense posture.",
        "confused": "Add a question mark near the character. Confused expression.",
        "hopeful": "Show kind expression. Add a small heart or warm gesture.",
        "tense": "Tense body language. Sweat drops or exclamation marks.",
        "surprised": "Wide eyes, open mouth. Exclamation mark above head.",
        "neutral": "Calm neutral expression.",
    }
    parts.append(f"\nEmotion cue: {emotion_cues.get(emotion, '')}")

    # Aspect ratio instruction
    parts.append("\nWide 16:9 landscape format. Leave empty space around characters.")

    return "\n".join(p for p in parts if p)


def build_all_prompts(
    segments: List[Dict],
    style_config: Dict,
) -> List[Dict]:
    """
    Build prompts for all segments in sequence.

    Returns:
        List of segments with 'prompt' field added.
    """
    total = len(segments)
    characters = []
    results = []

    for i, seg in enumerate(segments):
        prompt = build_prompt(seg, style_config, i, total, characters)
        results.append({**seg, "prompt": prompt})
        # Track mentioned characters for future consistency
        # (simple heuristic: first word of each segment often names the character)
        words = seg["text"].split()
        for w in words[:3]:
            w = w.strip(".,!?")
            if w.lower() not in ("the", "a", "an", "this", "that", "he", "she", "it", "his", "her"):
                if w and w[0].isupper() and w not in characters:
                    characters.append(w)

    return results


# ─── CLI usage ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, sys

    segments_path = sys.argv[1] if len(sys.argv) > 1 else "output/segments.json"
    style_path = sys.argv[2] if len(sys.argv) > 2 else "styles/ms_paint.yaml"

    segments = json.loads(Path(segments_path).read_text())
    style_config = yaml.safe_load(Path(style_path).read_text())

    result = build_all_prompts(segments, style_config)
    print(json.dumps(result, indent=2))