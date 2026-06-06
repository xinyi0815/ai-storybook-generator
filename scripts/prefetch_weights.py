"""Pre-download SDXL + IP-Adapter weights so the first end-to-end run is fast.

Reads model IDs from configs/settings.toml so it stays in sync with what the app actually uses.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore


def main() -> int:
    cfg_path = Path(__file__).resolve().parent.parent / "configs" / "settings.toml"
    if not cfg_path.exists():
        print(f"settings.toml not found at {cfg_path}")
        print("Run: cp configs/settings.example.toml configs/settings.toml")
        return 1

    with cfg_path.open("rb") as f:
        cfg = tomllib.load(f)

    sdxl_id = cfg["diffusion"]["sdxl_model"]
    adapter_repo = cfg["diffusion"]["ip_adapter_repo"]
    adapter_subfolder = cfg["diffusion"].get("ip_adapter_subfolder", "sdxl_models")
    adapter_weight = cfg["diffusion"]["ip_adapter_weight"]

    print(f"Downloading SDXL: {sdxl_id}")
    from diffusers import StableDiffusionXLPipeline
    import torch

    StableDiffusionXLPipeline.from_pretrained(
        sdxl_id,
        torch_dtype=torch.float16,
        variant="fp16",
    )
    print("  SDXL cached.")

    print(f"Downloading IP-Adapter: {adapter_repo}/{adapter_subfolder}/{adapter_weight}")
    from huggingface_hub import hf_hub_download

    hf_hub_download(
        repo_id=adapter_repo,
        subfolder=adapter_subfolder,
        filename=adapter_weight,
    )
    # IP-Adapter also needs the image encoder
    hf_hub_download(
        repo_id=adapter_repo,
        subfolder="models/image_encoder",
        filename="config.json",
    )
    hf_hub_download(
        repo_id=adapter_repo,
        subfolder="models/image_encoder",
        filename="model.safetensors",
    )
    print("  IP-Adapter cached.")

    print("All weights ready. Cache: ~/.cache/huggingface/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
