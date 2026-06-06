from __future__ import annotations

import json
import logging
from typing import Optional

from openai import OpenAI
from pydantic import ValidationError

from .config import load_settings
from .models import GenerationRequest, StoryDocument


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a children's book author who writes vivid, age-appropriate illustrated stories.

You MUST return a single JSON object that exactly matches this schema:

{
  "title": "string",
  "character_sheet": {
    "name": "string — short name of the main character",
    "species": "string — species or type (e.g. 'turtle', 'robot', 'girl')",
    "appearance": "string — detailed visual description used by an image model; include color, clothing, distinguishing features",
    "style_anchor": "string — consistent illustration style descriptor used by an image model (e.g. 'soft watercolor children's book illustration, warm pastel colors, gentle outlines')"
  },
  "pages": [
    {
      "page_number": integer (1-indexed),
      "narration": "string — 1 to 2 sentences in plain language for the target age group",
      "scene_prompt": "string — vivid visual description of what is happening on this page. ALWAYS restate the character's appearance and the style_anchor here, so an image model can render a consistent illustration."
    }
  ]
}

Strict rules:
1. The `pages` array MUST contain exactly the number of pages requested by the user.
2. Every `scene_prompt` MUST include the character's appearance (color, clothing, features) and the style_anchor, restated each time.
3. Narration must be appropriate for the target age group: simple words, short sentences, warm and encouraging tone.
4. Tell a complete story arc across the pages: setup, challenge, turning point, resolution.
5. Output JSON only. No prose, no markdown fences, no explanations."""


def _build_user_prompt(req: GenerationRequest) -> str:
    return (
        f"Write a {req.num_pages}-page illustrated story.\n\n"
        f"Theme: {req.theme}\n"
        f"Main character: {req.main_character}\n"
        f"Target age group: {req.age_group.value} years old\n\n"
        f"Return the JSON object only."
    )


def _call_llm(client: OpenAI, model: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )
    return response.choices[0].message.content or ""


def generate_story(req: GenerationRequest, max_retries: int = 1) -> StoryDocument:
    cfg = load_settings()["llm"]
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    model = cfg["model"]
    user_prompt = _build_user_prompt(req)

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            content = _call_llm(client, model, user_prompt)
            data = json.loads(content)
            story = StoryDocument.model_validate(data)
            if len(story.pages) != req.num_pages:
                raise ValueError(
                    f"LLM returned {len(story.pages)} pages, expected {req.num_pages}"
                )
            return story
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            last_error = e
            logger.warning("story generation attempt %d failed: %s", attempt + 1, e)

    raise RuntimeError(f"story generation failed after {max_retries + 1} attempts: {last_error}")
