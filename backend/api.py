from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import load_settings
from .models import GenerationRequest, JobStatus, JobStatusEnum
from .pipeline import get_status, register_job, run_generation


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(title="AI Storybook Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateResponse(BaseModel):
    run_id: str


class ResultResponse(BaseModel):
    run_id: str
    files: List[str]
    pdf: str
    story_json: str
    reference: str
    pages: List[str]


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def submit_generation(req: GenerationRequest) -> GenerateResponse:
    run_id = register_job(req)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, run_generation, req, run_id)
    logger.info("submitted run %s for theme: %s", run_id, req.theme[:60])
    return GenerateResponse(run_id=run_id)


@app.get("/api/status/{run_id}", response_model=JobStatus)
async def status_endpoint(run_id: str) -> JobStatus:
    status = get_status(run_id)
    if status is None:
        raise HTTPException(404, f"run_id {run_id} not found")
    return status


def _output_dir(run_id: str) -> Path:
    return Path(load_settings()["output"]["dir"]) / run_id


@app.get("/api/result/{run_id}", response_model=ResultResponse)
async def result_endpoint(run_id: str) -> ResultResponse:
    status = get_status(run_id)
    if status is None:
        raise HTTPException(404, f"run_id {run_id} not found")
    if status.status != JobStatusEnum.COMPLETE:
        raise HTTPException(409, f"run {run_id} is {status.status.value}, not complete")

    out_dir = _output_dir(run_id)
    if not out_dir.exists():
        raise HTTPException(500, f"output directory missing for {run_id}")

    files = sorted(p.name for p in out_dir.iterdir() if p.is_file())
    pages = sorted(f for f in files if f.startswith("page_") and f.endswith(".png"))
    return ResultResponse(
        run_id=run_id,
        files=files,
        pdf="storybook.pdf",
        story_json="story.json",
        reference="reference.png",
        pages=pages,
    )


@app.get("/api/file/{run_id}/{filename}")
async def file_endpoint(run_id: str, filename: str) -> FileResponse:
    out_dir = _output_dir(run_id).resolve()
    file_path = (out_dir / filename).resolve()
    if out_dir not in file_path.parents and file_path != out_dir:
        raise HTTPException(403, "path traversal blocked")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, f"file {filename} not found in run {run_id}")
    return FileResponse(file_path)
