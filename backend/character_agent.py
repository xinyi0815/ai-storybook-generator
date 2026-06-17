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
_ip_adapter_loaded: bool = False


def get_pipeline() -> StableDiffusionXLPipeline:
    """Lazy singleton — load SDXL once and reuse."""
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

    _pipeline = pipe
    return pipe


def ensure_ip_adapter_loaded() -> StableDiffusionXLPipeline:
    """Load IP-Adapter onto the shared pipeline on first call.

    Kept separate from get_pipeline because loading IP-Adapter mutates
    UNet config (encoder_hid_dim_type='ip_image_proj'), making EVERY
    subsequent call require image_embeds. So reference generation
    deliberately runs before this is called.
    """
    global _ip_adapter_loaded
    pipe = get_pipeline()
    if _ip_adapter_loaded:
        return pipe

    cfg = load_settings()["diffusion"]
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
    _ip_adapter_loaded = True
    return pipe


def generate_reference(sheet: CharacterSheet, seed: int = 42) -> Image.Image:
    settings = load_settings()
    cfg = settings["diffusion"]
    image_size = settings["output"]["image_size"]

    pipe = get_pipeline()

    prompt = (
        f"a single {sheet.species} named {sheet.name}, "
        f"{sheet.appearance}, "
        f"full body portrait, standing alone, centered, "
        f"clean simple neutral background, soft even lighting, "
        f"{sheet.style_anchor}"
    )
    negative = (
        "character sheet, model sheet, reference sheet, multiple poses, montage, "
        "multiple characters, duplicate, two characters, group of characters, "
        "blurry, low quality, deformed, ugly, extra limbs, "
        "busy background, text, watermark, signature"
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
