"""Smoke test for the Character Agent (SDXL reference image generation).

Outputs outputs/test_reference.png.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.character_agent import generate_reference
from backend.models import CharacterSheet


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> int:
    sheet = CharacterSheet(
        name="Momo",
        species="turtle",
        appearance=(
            "small green sea turtle with a bright yellow scarf tied around its neck, "
            "big round friendly eyes, smooth shell with subtle hexagon pattern"
        ),
        style_anchor="soft watercolor children's book illustration, warm pastel colors, gentle outlines",
    )
    print(f"Generating reference for {sheet.name} (first call ~60s for SDXL+IP-Adapter load)...")
    img = generate_reference(sheet)
    out = Path("outputs/test_reference.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"Saved: {out.resolve()}")
    print(f"Size: {img.size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
