from __future__ import annotations

import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from .config import settings
from .detection import build_segments, detect_boundaries
from .media import extract_analysis_audio, probe_media, read_wave_mono
from .models import JobResponse, JobState, MediaInfo, Segment


@dataclass
class Job:
    id: str
    source_path: Path
    original_filename: str
    content_type: str
    state: JobState = JobState.queued
    progress: float = 0.05
    error: str | None = None
    media: MediaInfo | None = None
    segments: list[Segment] | None = None
    created_at: float = field(default_factory=time.time)

    def response(self) -> JobResponse:
        return JobResponse(
            id=self.id,
            state=self.state,
            progress=self.progress,
            error=self.error,
            media=self.media,
            segments=self.segments,
            media_url=f"/api/jobs/{self.id}/media" if self.source_path.exists() else None,
        )


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="audio-analysis")

    def create(self, source_path: Path, original_filename: str, content_type: str) -> Job:
        self.cleanup()
        job = Job(str(uuid.uuid4()), source_path, original_filename, content_type)
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._process, job.id)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def delete(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job is not None:
            shutil.rmtree(job.source_path.parent, ignore_errors=True)
        return job

    def cleanup(self) -> None:
        cutoff = time.time() - settings.job_ttl_seconds
        with self._lock:
            expired = [
                job_id
                for job_id, job in self._jobs.items()
                if job.created_at < cutoff
                and job.state in (JobState.completed, JobState.failed)
            ]
            for job_id in expired:
                job = self._jobs.pop(job_id)
                shutil.rmtree(job.source_path.parent, ignore_errors=True)

    def _update(self, job_id: str, **values: object) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for key, value in values.items():
                setattr(job, key, value)
            return job

    def _process(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is None:
            return
        analysis_path = job.source_path.parent / "analysis.wav"
        try:
            if self._update(job_id, state=JobState.processing, progress=0.15) is None:
                return
            media = probe_media(job.source_path, job.original_filename, job.content_type)
            if self._update(job_id, media=media, progress=0.3) is None:
                return
            extract_analysis_audio(job.source_path, analysis_path)
            if self._update(job_id, progress=0.7) is None:
                return
            samples, sample_rate = read_wave_mono(analysis_path)
            boundaries = detect_boundaries(samples, sample_rate, media.duration)
            segments = build_segments(media.duration, boundaries)
            self._update(
                job_id,
                segments=segments,
                progress=1.0,
                state=JobState.completed,
            )
        except Exception as exc:
            self._update(job_id, state=JobState.failed, progress=1.0, error=str(exc))
        finally:
            analysis_path.unlink(missing_ok=True)


jobs = JobStore()
