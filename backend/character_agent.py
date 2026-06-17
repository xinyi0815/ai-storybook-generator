from __future__ import annotations

import logging
from typing import Optional

import torch
from diffusers import StableDiffusionXLPipeline
from PIL import Image

from .config import load_settings
from .models import CharacterSheet


logger = logging.getLogger(__name__)


_pipeline: Optional[StableDiffusionXLPipeline] = None


def get_pipeline() -> StableDiffusionXLPipeline:
    """Lazy singleton — load SDXL + IP-Adapter once, reuse for both reference and pages."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    cfg = load_settings()["diffusion"]

    logger.info("Loading SDXL pipeline: %s", cfg["sdxl_model"])
    pipe = StableDiffusionXLPipeline.from_pretrained(
        cfg["sdxl_model"],
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    ).to(cfg["device"])

    logger.info(
        "Loading IP-Adapter: %s/%s/%s",
        cfg["ip_adapter_repo"],
        cfg["ip_adapter_subfolder"],
        cfg["ip_adapter_weight"],
    )
    pipe.load_ip_adapter(
        cfg["ip_adapter_repo"],
        subfolder=cfg["ip_adapter_subfolder"],
        weight_name=cfg["ip_adapter_weight"],
    )
    pipe.set_ip_adapter_scale(0.0)

    _pipeline = pipe
    return pipe


def generate_reference(sheet: CharacterSheet, seed: int = 42) -> Image.Image:
    settings = load_settings()
    cfg = settings["diffusion"]
    image_size = settings["output"]["image_size"]

    pipe = get_pipeline()
    pipe.set_ip_adapter_scale(0.0)

    prompt = (
        f"character reference sheet of {sheet.name} the {sheet.species}, "
        f"{sheet.appearance}, "
        f"full body, centered, plain neutral background, T-pose, "
        f"{sheet.style_anchor}"
    )
    negative = (
        "blurry, low quality, deformed, ugly, extra limbs, multiple characters, "
        "busy background, text, watermark"
    )

    generator = torch.Generator(device=cfg["device"]).manual_seed(seed)
    logger.info("Generating reference image for %s (seed=%d)", sheet.name, seed)
    result = pipe(
        prompt=prompt,
        negative_prompt=negative,
        num_inference_steps=cfg["num_inference_steps"],
        guidance_scale=cfg["guidance_scale"],
        width=image_size,
        height=image_size,
        generator=generator,
    )
    return result.images[0]
