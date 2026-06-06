"""Smoke test for the LLM Story Agent. Run from project root with venv active.

Usage:
    python scripts/test_story_agent.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.models import AgeGroup, GenerationRequest
from backend.story_agent import generate_story


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> int:
    req = GenerationRequest(
        theme="a brave little turtle who learns to swim in the deep sea",
        main_character="a small green sea turtle named Momo with a bright yellow scarf",
        age_group=AgeGroup.EARLY,
        num_pages=4,
    )
    print(f"Theme: {req.theme}")
    print(f"Character: {req.main_character}")
    print(f"Pages: {req.num_pages}")
    print("-" * 60)
    print("Calling Ollama...")
    story = generate_story(req)
    print("-" * 60)
    print(json.dumps(story.model_dump(), indent=2, ensure_ascii=False))
    print("-" * 60)
    print(f"OK: generated {len(story.pages)} pages, title: {story.title!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
