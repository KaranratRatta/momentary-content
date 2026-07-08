import json
from openai import OpenAI
from momentary.config import OPENROUTER_API_KEY, OPENROUTER_MODEL


def _build_system_prompt(num_scenes: int) -> str:
    return f"""You are a YouTube scriptwriter for a cartoon stick-figure educational channel.
The channel uses simple hand-drawn cartoon illustrations with stick figure characters.

Write a script with exactly {num_scenes} scenes about the given topic.
Each scene should have:
- narration: 1-2 sentences of casual, humorous narration (like talking to a friend)
- image_prompt: a detailed visual description for generating a cartoon stick-figure illustration
- duration_hint: estimated seconds for this scene (5-12 seconds based on narration length)

The image_prompt MUST include:
- The cartoon stick figure style (round white head, stick body, simple face)
- The specific scene setting and action
- Lighting and mood details
- Color palette hints

Return ONLY valid JSON in this format:
{{
  "title": "Video Title",
  "scenes": [
    {{
      "narration": "Narration text here",
      "image_prompt": "Detailed image prompt here",
      "duration_hint": 8
    }}
  ]
}}

Do not include any text outside the JSON object."""


def generate_script(topic: str, num_scenes: int = 10) -> dict:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    system_prompt = _build_system_prompt(num_scenes)
    user_prompt = f"Write a cartoon stick-figure educational video script about: {topic}"

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )

    script = json.loads(response.choices[0].message.content)
    return script
