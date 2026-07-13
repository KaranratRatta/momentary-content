import json
from pathlib import Path
from openai import OpenAI
from momentary.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, NARRATION_THEMES, DEFAULT_THEME, RESEARCH_PROMPT, STYLE_PROMPTS, DEFAULT_STYLE


def _build_system_prompt(num_scenes: int, theme: str = "Educational", research_context: str = "", target_duration_seconds: float | None = None, video_idea: str = "", style: str = DEFAULT_STYLE) -> str:
    theme_description = NARRATION_THEMES.get(theme, NARRATION_THEMES[DEFAULT_THEME])
    style_description = STYLE_PROMPTS.get(style, STYLE_PROMPTS[DEFAULT_STYLE])

    research_section = ""
    if research_context:
        research_section = f"""

RESEARCH CONTEXT (use these facts to make your script accurate and interesting):
{research_context}

NOTE: You do NOT need to use all the facts above. Select only the most relevant and interesting ones that fit the target video length. You can also add additional facts or angles not mentioned above if they make the video more engaging."""

    duration_section = ""
    if target_duration_seconds:
        avg_per_scene = target_duration_seconds / num_scenes
        duration_section = f"""

TARGET DURATION: The full video should be approximately {target_duration_seconds} seconds ({target_duration_seconds/60:.1f} minutes).
With {num_scenes} scenes, each scene's narration should be roughly {avg_per_scene:.0f} seconds when spoken aloud.

FLEXIBLE SCENE SPLITTING: You can split narration flexibly across scenes:
- One sentence can span multiple scenes (e.g., 1 sentence across 2-3 images for emphasis)
- Multiple sentences can share a scene (e.g., 4 sentences in 1 image if they're related)
- Adjust the split based on visual interest and pacing, not just sentence boundaries
- Focus on creating visually distinct moments that match the narration flow
- Aim for variety: some quick cuts (short narration per scene), some lingering moments (longer narration per scene)

Write naturally, but keep this pacing in mind. Good narration quality is more important than hitting exact timing."""

    idea_section = ""
    if video_idea:
        idea_section = f"""

VIDEO IDEA / FOCUS (the creator wants to emphasize these aspects):
{video_idea}"""

    duration_phrase = f" and approximately {target_duration_seconds} seconds long" if target_duration_seconds else ""

    return f"""You are a YouTube scriptwriter for an educational channel that uses hand-drawn cartoon illustrations.
The style is casual and engaging, similar to channels like Kurzgesagt, Vsauce, or Zenn.

NARRATION STYLE: {theme_description}

VISUAL STYLE: {style_description}

IMPORTANT: When writing image_prompt and thumbnail_prompt, you MUST incorporate ALL elements of the visual style described above. Include details about line quality, background treatment, character design, lighting, and overall aesthetic in every prompt.

HOOK STRUCTURE: The first 1-5 scenes MUST be a hook that opens a loop. Tease the payoff without giving it away. Create curiosity that makes viewers want to keep watching. Don't reveal the answer or main point yet - just hint at something interesting coming.

SPOKEN ENGLISH: Write like you're talking to others, not writing an essay. Use:
- Contractions
- Casual transitions
- Short, punchy sentences mixed with longer ones
- Conversational tone, not formal academic language
- Rhetorical questions to engage the viewer

Write a script with exactly {num_scenes} scenes{duration_phrase} about the given topic.{research_section}{duration_section}{idea_section}

Each scene should have:
- narration: The portion of narration for this specific image/scene. Can be a fragment, one sentence, or multiple sentences depending on visual pacing.
- image_prompt: a detailed visual description for generating an illustration that fully incorporates the visual style described above
- duration_hint: estimated seconds for this scene based on narration length

IMPORTANT IMAGE PROMPT GUIDELINES:
- Human characters: simple stick figures with round white heads, simple shapes eyes (dots, line, heart, big circles for shock emotion, etc.), no noses
- Objects/environments: more detailed than characters, but still in a hand-drawn cartoon style
- Include specific lighting, mood, and color details
- Describe the composition and what's happening in the scene
- Make prompts specific enough to generate consistent style across scenes
- CRITICAL: Every image_prompt must fully incorporate the visual style described above (line quality, background treatment, character design, lighting, overall aesthetic)
- You may optionally include text within an image to highlight a key topic or concept, but use this sparingly — only when it genuinely adds impact. Do not add text to every image. When you do include text, choose the font style and placement yourself to best fit the scene, don't make it too large.

THUMBNAIL PROMPT: Create a visual description for an eye-catching YouTube thumbnail that fully incorporates the visual style described above. Make it bold, simple, and attention-grabbing. Focus on one key visual element that represents the video's core idea. Include all style details (line quality, background, character design, etc.). IMPORTANT: Include the clickbait text as part of the visual description, describing how it should look in the image (font style, color, position, etc.).

THUMBNAIL TEXT: Create a short, punchy clickbait text (2-5 words) that will be displayed in the thumbnail. Make it curiosity-inducing, dramatic, or surprising. Examples: "YOU WON'T BELIEVE", "THE TRUTH", "SHOCKING", "NEVER DO THIS", "SECRET REVEALED".

DESCRIPTION: Write a YouTube description that:
- Starts with a hook that creates curiosity
- Briefly mentions what viewers will learn
- Includes 3-5 relevant hashtags at the end
- Is 2-4 sentences total, conversational tone

Return ONLY valid JSON in this format:
{{
  "title": "Video Title",
  "description": "YouTube description here",
  "thumbnail_prompt": "Thumbnail visual description here with full style incorporation",
  "thumbnail_text": "Short clickbait text here (2-5 words)",
  "scenes": [
    {{
      "narration": "Natural narration here",
      "image_prompt": "Detailed image prompt here with full style incorporation",
      "duration_hint": 8
    }}
  ]
}}

Do not include any text outside the JSON object."""


def generate_script(
    topic: str,
    num_scenes: int = 10,
    model: str | None = None,
    theme: str = DEFAULT_THEME,
    research_context: str = "",
    target_duration_seconds: float | None = None,
    video_idea: str = "",
    style: str = DEFAULT_STYLE,
    run_dir: Path | None = None,
) -> dict:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    system_prompt = _build_system_prompt(num_scenes, theme, research_context, target_duration_seconds, video_idea, style)
    user_prompt = f"Write a video script about: {topic}"

    response = client.chat.completions.create(
        model=model or OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    script = json.loads(response.choices[0].message.content)

    if run_dir:
        script_path = run_dir / "script.json"
        with open(script_path, "w") as f:
            json.dump(script, f, indent=2)
        
        if "description" in script:
            description_path = run_dir / "description.txt"
            with open(description_path, "w") as f:
                f.write(script["description"])

    return script


def research_topic(topic: str, model: str | None = None) -> str:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    response = client.chat.completions.create(
        model=model or OPENROUTER_MODEL,
        messages=[
            {"role": "user", "content": RESEARCH_PROMPT.format(topic=topic)},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content
