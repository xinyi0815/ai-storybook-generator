from __future__ import annotations

import logging

import torch
from PIL import Image

from .character_agent import get_pipeline
from .config import load_settings


logger = logging.getLogger(__name__)


def generate_page(
    reference: Image.Image,
    scene_prompt: str,
    seed: int = 0,
    ip_adapter_scale: float | None = None,
) -> Image.Image:
    settings = load_settings()
    cfg = settings["diffusion"]
    image_size = settings["output"]["image_size"]

    pipe = get_pipeline()
    scale = ip_adapter_scale if ip_adapter_scale is not None else cfg["ip_adapter_scale"]
    pipe.set_ip_adapter_scale(scale)

    negative = (
        "blurry, low quality, deformed, ugly, text, watermark, signature, "
        "multiple characters, duplicate character, inconsistent character"
    )

    generator = torch.Generator(device=cfg["device"]).manual_seed(seed)
    logger.info(
        "Generating page (seed=%d, ip_adapter_scale=%.2f): %s",
        seed,
        scale,
        scene_prompt[:80] + ("..." if len(scene_prompt) > 80 else ""),
    )
    result = pipe(
        prompt=scene_prompt,
        negative_prompt=negative,
        ip_adapter_image=reference,
        num_inference_steps=cfg["num_inference_steps"],
        guidance_scale=cfg["guidance_scale"],
        width=image_size,
        height=image_size,
        generator=generator,
    )
    return result.images[0]
