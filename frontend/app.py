from __future__ import annotations

import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Generator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr

from backend.config import load_settings
from backend.models import AgeGroup, GenerationRequest, JobStatusEnum
from backend.pipeline import get_status, register_job, run_generation


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


AGE_CHOICES = [
    ("3–5 (preschool, very simple language)", AgeGroup.PRESCHOOL.value),
    ("5–7 (early reader, short sentences)", AgeGroup.EARLY.value),
    ("7–9 (middle, richer vocabulary)", AgeGroup.MIDDLE.value),
]


def _outputs_root() -> Path:
    return Path(load_settings()["output"]["dir"])


def generate_storybook(
    theme: str,
    main_character: str,
    age_group_value: str,
    num_pages: int,
    progress: gr.Progress = gr.Progress(),
):
    if not theme or not theme.strip():
        raise gr.Error("Please describe a theme.")
    if not main_character or not main_character.strip():
        raise gr.Error("Please describe the main character.")

    req = GenerationRequest(
        theme=theme.strip(),
        main_character=main_character.strip(),
        age_group=AgeGroup(age_group_value),
        num_pages=int(num_pages),
    )
    run_id = register_job(req)
    logger.info("submitted run %s", run_id)

    thread = threading.Thread(
        target=run_generation, args=(req, run_id), daemon=True
    )
    thread.start()

    last_message = ""
    while thread.is_alive():
        status = get_status(run_id)
        if status is not None:
            if status.message != last_message:
                logger.info("[%s] %s (%.0f%%)", run_id, status.message, status.progress * 100)
                last_message = status.message
            progress(status.progress, desc=status.message)
        time.sleep(0.5)

    status = get_status(run_id)
    if status is None or status.status == JobStatusEnum.FAILED:
        err = status.error if status else "unknown error"
        raise gr.Error(f"Generation failed: {err}")

    out_dir = _outputs_root() / run_id
    story = json.loads((out_dir / "story.json").read_text(encoding="utf-8"))
    title = story["title"]

    gallery_items = []
    for page in story["pages"]:
        img_path = out_dir / f"page_{page['page_number']:02d}.png"
        caption = f"Page {page['page_number']}: {page['narration']}"
        gallery_items.append((str(img_path), caption))

    pdf_path = str(out_dir / "storybook.pdf")
    reference_path = str(out_dir / "reference.png")

    title_md = f"## {title}\n*Featuring {story['character_sheet']['name']} the {story['character_sheet']['species']}*"
    return title_md, gallery_items, reference_path, pdf_path


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="AI Storybook Generator", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# AI Storybook Generator\n"
            "Type a story idea, describe your main character, and the AI will write a short "
            "illustrated storybook with a consistent main character across every page.\n\n"
            "*Powered by Ollama (LLM) + Stable Diffusion XL + IP-Adapter for character consistency.*"
        )

        with gr.Row():
            with gr.Column(scale=1):
                theme = gr.Textbox(
                    label="Theme",
                    placeholder="a brave little turtle who learns to swim in the deep sea",
                    lines=2,
                )
                main_character = gr.Textbox(
                    label="Main character",
                    placeholder="a small green sea turtle named Momo with a bright yellow scarf",
                    lines=2,
                )
                age_group = gr.Radio(
                    choices=AGE_CHOICES,
                    value=AgeGroup.EARLY.value,
                    label="Target age group",
                )
                num_pages = gr.Slider(
                    minimum=2,
                    maximum=8,
                    step=1,
                    value=4,
                    label="Number of pages",
                )
                submit = gr.Button("Generate storybook", variant="primary")

            with gr.Column(scale=2):
                title_out = gr.Markdown()
                gallery = gr.Gallery(
                    label="Pages",
                    show_label=True,
                    columns=2,
                    height=560,
                    object_fit="contain",
                )
                with gr.Row():
                    reference_out = gr.Image(label="Character reference", height=240)
                    pdf_out = gr.File(label="Download PDF")

        gr.Examples(
            examples=[
                [
                    "a brave little turtle who learns to swim in the deep sea",
                    "a small green sea turtle named Momo with a bright yellow scarf",
                    AgeGroup.EARLY.value,
                    4,
                ],
                [
                    "a curious robot who discovers the joy of music",
                    "a small round white robot named Bip with glowing blue eyes and one antenna",
                    AgeGroup.MIDDLE.value,
                    4,
                ],
                [
                    "a shy panda cub who makes their first friend",
                    "a fluffy black-and-white panda cub named Mochi with big round eyes and pink cheeks",
                    AgeGroup.PRESCHOOL.value,
                    4,
                ],
            ],
            inputs=[theme, main_character, age_group, num_pages],
        )

        submit.click(
            fn=generate_storybook,
            inputs=[theme, main_character, age_group, num_pages],
            outputs=[title_out, gallery, reference_out, pdf_out],
            concurrency_limit=1,
        )

    return demo


if __name__ == "__main__":
    settings = load_settings()
    host = settings.get("server", {}).get("host", "0.0.0.0")
    port = int(settings.get("server", {}).get("port", 7860))
    if port == 8000:
        port = 7860
    build_ui().queue(max_size=4).launch(
        server_name=host, server_port=port, share=False, show_error=True
    )
