import json
from pathlib import Path
from openai import OpenAI
from momentary.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, NARRATION_THEMES, DEFAULT_THEME, RESEARCH_PROMPT


def _build_system_prompt(num_scenes: int, theme: str = "Educational", research_context: str = "", target_duration_seconds: float | None = None, video_idea: str = "") -> str:
    theme_description = NARRATION_THEMES.get(theme, NARRATION_THEMES[DEFAULT_THEME])

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

Write a script with exactly {num_scenes} scenes{duration_phrase} about the given topic.{research_section}{duration_section}{idea_section}

Each scene should have:
- narration: Natural, engaging narration. Write quality content - don't sacrifice writing quality for brevity. Let the narration flow naturally.
- image_prompt: a detailed visual description for generating an illustration
- duration_hint: estimated seconds for this scene based on narration length

IMPORTANT IMAGE PROMPT GUIDELINES:
- Human characters: simple stick figures with round white heads and dot eyes
- Animals: draw with full detail and personality, NOT stick figures. Show their actual appearance with characteristic features
- Objects/environments: detailed and textured, not stick figures
- Include specific lighting, mood, and color details
- Describe the composition and what's happening in the scene
- Make prompts specific enough to generate consistent style across scenes

Return ONLY valid JSON in this format:
{{
  "title": "Video Title",
  "scenes": [
    {{
      "narration": "Natural narration here",
      "image_prompt": "Detailed image prompt here",
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
    run_dir: Path | None = None,
) -> dict:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    system_prompt = _build_system_prompt(num_scenes, theme, research_context, target_duration_seconds, video_idea)
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
