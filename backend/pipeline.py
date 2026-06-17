from __future__ import annotations

import logging
import uuid
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from .character_agent import generate_reference
from .config import load_settings
from .illustration_agent import generate_page
from .models import GenerationRequest, JobStatus, JobStatusEnum
from .pdf_compiler import compile_pdf
from .story_agent import generate_story


logger = logging.getLogger(__name__)


_jobs: Dict[str, JobStatus] = {}
_jobs_lock = Lock()


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def register_job(req: GenerationRequest) -> str:
    run_id = new_run_id()
    with _jobs_lock:
        _jobs[run_id] = JobStatus(
            run_id=run_id,
            status=JobStatusEnum.QUEUED,
            progress=0.0,
            message=f"Queued: {req.num_pages}-page story about {req.theme[:40]}",
        )
    return run_id


def get_status(run_id: str) -> Optional[JobStatus]:
    with _jobs_lock:
        return _jobs.get(run_id)


def _update(run_id: str, **fields) -> None:
    with _jobs_lock:
        status = _jobs.get(run_id)
        if status is None:
            return
        for k, v in fields.items():
            setattr(status, k, v)


def run_generation(req: GenerationRequest, run_id: str) -> None:
    """Synchronous pipeline. Caller is responsible for running off the event loop."""
    settings = load_settings()
    out_root = Path(settings["output"]["dir"]) / run_id
    out_root.mkdir(parents=True, exist_ok=True)

    try:
        _update(
            run_id,
            status=JobStatusEnum.STORY_PENDING,
            message="Writing story with LLM...",
            progress=0.05,
        )
        story = generate_story(req)
        (out_root / "story.json").write_text(
            story.model_dump_json(indent=2), encoding="utf-8"
        )
        _update(
            run_id,
            status=JobStatusEnum.STORY_DONE,
            message=f"Story drafted: {story.title!r}",
            progress=0.15,
        )

        seed = abs(hash(run_id)) & 0x7FFFFFFF

        _update(
            run_id,
            status=JobStatusEnum.REFERENCE_PENDING,
            message="Generating character reference image...",
            progress=0.20,
        )
        reference_img = generate_reference(story.character_sheet, seed=seed)
        reference_path = out_root / "reference.png"
        reference_img.save(reference_path)
        _update(
            run_id,
            status=JobStatusEnum.REFERENCE_DONE,
            message="Character reference ready",
            progress=0.30,
        )

        _update(
            run_id,
            status=JobStatusEnum.ILLUSTRATIONS_PENDING,
            message=f"Illustrating {len(story.pages)} pages with IP-Adapter...",
            progress=0.32,
        )
        page_paths = []
        for i, page in enumerate(story.pages):
            page_img = generate_page(
                reference_img, page.scene_prompt, seed=seed + page.page_number
            )
            page_path = out_root / f"page_{page.page_number:02d}.png"
            page_img.save(page_path)
            page_paths.append(page_path)
            progress = 0.32 + 0.55 * (i + 1) / len(story.pages)
            _update(
                run_id,
                progress=progress,
                message=f"Illustrated page {i + 1}/{len(story.pages)}",
            )
        _update(
            run_id,
            status=JobStatusEnum.ILLUSTRATIONS_DONE,
            message="All pages illustrated",
            progress=0.88,
        )

        _update(
            run_id,
            status=JobStatusEnum.PDF_PENDING,
            message="Compiling PDF...",
            progress=0.92,
        )
        pdf_path = out_root / "storybook.pdf"
        compile_pdf(story, page_paths, pdf_path)

        _update(
            run_id,
            status=JobStatusEnum.COMPLETE,
            message=f"Done: {story.title!r}",
            progress=1.0,
        )
        logger.info("run %s complete: %s", run_id, pdf_path)
    except Exception as e:
        logger.exception("run %s failed", run_id)
        _update(run_id, status=JobStatusEnum.FAILED, error=str(e), message=f"Failed: {e}")
