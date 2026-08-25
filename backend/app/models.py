from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class JobState(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class MediaInfo(BaseModel):
    filename: str
    content_type: str
    duration: float = Field(gt=0)
    has_video: bool = False


class Segment(BaseModel):
    id: int = Field(ge=0)
    label: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    duration: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)


class JobResponse(BaseModel):
    id: str
    state: JobState
    progress: float = Field(ge=0, le=1)
    error: str | None = None
    media: MediaInfo | None = None
    segments: list[Segment] | None = None
    media_url: str | None = None
