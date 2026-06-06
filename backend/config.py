from __future__ import annotations

from functools import lru_cache
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_settings() -> dict:
    path = PROJECT_ROOT / "configs" / "settings.toml"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy from configs/settings.example.toml."
        )
    with path.open("rb") as f:
        return tomllib.load(f)
