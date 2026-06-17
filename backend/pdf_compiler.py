from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from .models import StoryDocument


logger = logging.getLogger(__name__)


def compile_pdf(
    story: StoryDocument,
    page_image_paths: Sequence[Path],
    output_path: Path,
) -> Path:
    if len(page_image_paths) != len(story.pages):
        raise ValueError(
            f"page count mismatch: {len(page_image_paths)} images for {len(story.pages)} pages"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A5,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        title=story.title,
        author="AI Storybook Generator",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "StoryTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=28,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=16,
        textColor="grey",
    )
    narration_style = ParagraphStyle(
        "Narration",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=16,
    )
    page_label_style = ParagraphStyle(
        "PageLabel",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor="grey",
    )

    flowables = [
        Spacer(1, 3 * cm),
        Paragraph(story.title, title_style),
        Spacer(1, 0.6 * cm),
        Paragraph(f"<i>Featuring {story.character_sheet.name} the {story.character_sheet.species}</i>", subtitle_style),
        PageBreak(),
    ]

    img_w = img_h = 11 * cm
    for page, img_path in zip(story.pages, page_image_paths):
        img = RLImage(str(img_path), width=img_w, height=img_h)
        block = KeepTogether(
            [
                img,
                Spacer(1, 0.4 * cm),
                Paragraph(page.narration, narration_style),
                Spacer(1, 0.3 * cm),
                Paragraph(f"— page {page.page_number} —", page_label_style),
            ]
        )
        flowables.append(block)
        flowables.append(PageBreak())

    if flowables and isinstance(flowables[-1], PageBreak):
        flowables.pop()

    logger.info("Writing PDF: %s (%d pages)", output_path, len(story.pages))
    doc.build(flowables)
    return output_path
