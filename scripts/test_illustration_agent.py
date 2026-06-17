"""Smoke test for IP-Adapter illustration generation.

Run scripts/test_character_agent.py first to produce outputs/test_reference.png.
Outputs outputs/test_page.png.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from backend.illustration_agent import generate_page


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


SCENE_PROMPT = (
    "Momo the small green sea turtle is swimming deeper into the ocean. "
    "A bright yellow scarf flutters behind its neck. The water turns from light blue to "
    "deep navy as Momo descends, big curious eyes looking ahead. "
    "Soft watercolor children's book illustration, warm pastel colors, gentle outlines."
)


def main() -> int:
    ref_path = Path("outputs/test_reference.png")
    if not ref_path.exists():
        print(f"missing {ref_path}")
        print("run scripts/test_character_agent.py first to produce a reference image")
        return 1

    reference = Image.open(ref_path).convert("RGB")
    print(f"Reference: {ref_path} ({reference.size})")
    print("Generating page with IP-Adapter...")
    img = generate_page(reference, SCENE_PROMPT, seed=42)
    out = Path("outputs/test_page.png")
    img.save(out)
    print(f"Saved: {out.resolve()}")
    print(f"Size: {img.size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
