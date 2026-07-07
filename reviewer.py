"""
reviewer.py — Stage 3.5: Review generated images using a vision LLM.

Evaluates each generated image against its prompt and story context.
Scores images on quality criteria and provides feedback for regeneration.
Works with the pipeline to retry low-scoring images (max retries configurable).
"""

import json
import re
from typing import Dict, List, Optional, Tuple

from llm_client import LLMClient
from generator import generate_single_image
from prompt_builder import refine_scene_prompt


REVIEW_SYSTEM = (
    "You are a quality reviewer for illustrated story video frames (YouTube, 16:9). "
    "You will see a generated image and the prompt that was used to create it.\n\n"
    "Score the image on these criteria (1-5 each):\n"
    "- visual_quality: overall aesthetic, sharpness, color harmony\n"
    "- story_relevance: does the image match the narration/story beat?\n"
    "- character_consistency: do characters look like they belong in the same story?\n"
    "- composition: good framing, balanced layout, appropriate camera angle\n"
    "- engagement: would a viewer find this interesting/enjoyable to look at?\n\n"
    "Then give an overall_score (1-5) and specific actionable feedback.\n\n"
    "Return ONLY valid JSON (no markdown fences):\n"
    "{\n"
    '  "visual_quality": <1-5>,\n'
    '  "story_relevance": <1-5>,\n'
    '  "character_consistency": <1-5>,\n'
    '  "composition": <1-5>,\n'
    '  "engagement": <1-5>,\n'
    '  "overall_score": <1-5>,\n'
    '  "feedback": "specific actionable suggestions for improvement",\n'
    '  "pass": <true if overall_score >= 3, false otherwise>\n'
    "}"
)


def _parse_review(raw: str) -> Dict:
    """Parse the reviewer's JSON response, with fallback."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)
        text = text[1] if len(text) >= 2 else raw
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    score_match = re.search(r'"overall_score"\s*:\s*(\d)', raw)
    score = int(score_match.group(1)) if score_match else 2
    return {
        "overall_score": score,
        "pass": score >= 3,
        "feedback": raw[:500],
    }


def review_image(
    image_url: str,
    prompt: str,
    narration: str,
    llm: LLMClient,
) -> Dict:
    """Review a single generated image."""
    user_text = (
        f"PROMPT USED:\n{prompt}\n\n"
        f"NARRATION FOR THIS SCENE: {narration}\n\n"
        "Review this image. Score it and provide feedback."
    )
    raw = llm.chat_with_image(REVIEW_SYSTEM, user_text, image_url)
    return _parse_review(raw)


def review_and_refine(
    segments: List[Dict],
    bible: Dict,
    style_config: Dict,
    llm: LLMClient,
    model: str = "fal-ai/krea-2/turbo",
    gen_params: Optional[Dict] = None,
    min_score: int = 3,
    max_retries: int = 2,
    output_dir: str = "./output",
) -> List[Dict]:
    """
    Review all generated images. Refine and regenerate those that score below threshold.

    Args:
        segments: Segments with image_path, image_url, and prompt fields.
        bible: The story bible dict.
        style_config: The style template dict.
        llm: LLMClient (must support vision).
        model: FAL model for regeneration.
        gen_params: Generator parameters.
        min_score: Minimum overall score to pass (1-5).
        max_retries: Max regeneration attempts per image.
        output_dir: Output directory for regenerated images.

    Returns:
        Updated segments with potentially new image_path/image_url/prompt.
    """
    gen_params = gen_params or {}

    needs_review = [
        seg for seg in segments
        if seg.get("image_url") and seg["image_url"] != "saved locally"
    ]

    if not needs_review:
        print("   ⚠ No image URLs available for review (images were saved locally without URLs)")
        return segments

    print(f"\n🔍 Reviewing {len(needs_review)} images (min score: {min_score}/5)...")

    review_results = []
    for seg in needs_review:
        idx = seg["segment_index"]
        print(f"   Reviewing [{idx + 1}/{len(segments)}] {seg['timestamp_str']}...")

        try:
            review = review_image(
                image_url=seg["image_url"],
                prompt=seg.get("prompt", ""),
                narration=seg["text"],
                llm=llm,
            )
        except Exception as e:
            print(f"   ⚠ Review failed for segment {idx}: {e}")
            review = {"overall_score": 3, "pass": True, "feedback": "review unavailable"}

        review["segment_index"] = idx
        review_results.append(review)

        score = review.get("overall_score", 0)
        passed = review.get("pass", score >= min_score)
        status = "✓" if passed else "✗"
        print(f"   {status} Score: {score}/5 — {review.get('feedback', '')[:80]}")

    failed = [r for r in review_results if not r.get("pass", False)]

    if not failed:
        print(f"\n✅ All images passed review!")
        _save_review_report(review_results, output_dir)
        return segments

    print(f"\n🔄 Refining {len(failed)} images that scored below {min_score}/5...")

    for retry in range(max_retries):
        if not failed:
            break

        print(f"\n   ── Retry {retry + 1}/{max_retries} ──")
        still_failed = []

        for review in failed:
            idx = review["segment_index"]
            seg = segments[idx]
            feedback = review.get("feedback", "improve quality and composition")

            print(f"   Refining [{idx + 1}] {seg['timestamp_str']}...")

            try:
                new_prompt = refine_scene_prompt(
                    original_prompt=seg.get("prompt", ""),
                    feedback=feedback,
                    bible=bible,
                    style_config=style_config,
                    segment=seg,
                    llm=llm,
                )
            except Exception as e:
                print(f"   ⚠ Prompt refinement failed: {e}")
                still_failed.append(review)
                continue

            seg["prompt"] = new_prompt
            save_path = seg.get("image_path", "")

            success, new_url = generate_single_image(
                prompt=new_prompt,
                save_path=save_path,
                model=model,
                params=gen_params,
            )

            if success and new_url:
                seg["image_url"] = new_url
                print(f"   ✓ Regenerated [{idx + 1}]")

                try:
                    new_review = review_image(
                        image_url=new_url,
                        prompt=new_prompt,
                        narration=seg["text"],
                        llm=llm,
                    )
                    new_review["segment_index"] = idx
                    new_score = new_review.get("overall_score", 0)
                    new_passed = new_review.get("pass", new_score >= min_score)

                    for i, r in enumerate(review_results):
                        if r["segment_index"] == idx:
                            review_results[i] = new_review
                            break

                    status = "✓" if new_passed else "✗"
                    print(f"   {status} New score: {new_score}/5")

                    if not new_passed:
                        still_failed.append(new_review)
                except Exception:
                    print(f"   ✓ Regenerated (re-review skipped)")
            else:
                print(f"   ✗ Regeneration failed [{idx + 1}]")
                still_failed.append(review)

        failed = still_failed

    if failed:
        print(f"\n⚠ {len(failed)} images still below threshold after {max_retries} retries")

    _save_review_report(review_results, output_dir)
    _update_manifest(segments, output_dir)

    return segments


def _save_review_report(reviews: List[Dict], output_dir: str):
    """Save the review results as a JSON report."""
    from pathlib import Path
    report_path = Path(output_dir) / "review_report.json"
    report_path.write_text(json.dumps(reviews, indent=2))
    print(f"📋 Review report saved: {report_path}")


def _update_manifest(segments: List[Dict], output_dir: str):
    """Update the manifest after review/refine cycle."""
    from pathlib import Path
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
