from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgeGroup(str, Enum):
    PRESCHOOL = "3-5"
    EARLY = "5-7"
    MIDDLE = "7-9"


class GenerationRequest(BaseModel):
    theme: str = Field(..., min_length=3, max_length=300)
    main_character: str = Field(..., min_length=3, max_length=300)
    age_group: AgeGroup = AgeGroup.EARLY
    num_pages: int = Field(4, ge=2, le=8)


class CharacterSheet(BaseModel):
    name: str
    species: str
    appearance: str
    style_anchor: str


class StoryPage(BaseModel):
    page_number: int = Field(..., ge=1)
    narration: str
    scene_prompt: str


class StoryDocument(BaseModel):
    title: str
    character_sheet: CharacterSheet
    pages: list[StoryPage]


class JobStatusEnum(str, Enum):
    QUEUED = "queued"
    STORY_PENDING = "story_pending"
    STORY_DONE = "story_done"
    REFERENCE_PENDING = "reference_pending"
    REFERENCE_DONE = "reference_done"
    ILLUSTRATIONS_PENDING = "illustrations_pending"
    ILLUSTRATIONS_DONE = "illustrations_done"
    PDF_PENDING = "pdf_pending"
    COMPLETE = "complete"
    FAILED = "failed"


class JobStatus(BaseModel):
    run_id: str
    status: JobStatusEnum
    progress: float = Field(0.0, ge=0.0, le=1.0)
    message: str = ""
    error: Optional[str] = None
