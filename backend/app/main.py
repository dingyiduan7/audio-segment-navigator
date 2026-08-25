from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import settings
from .jobs import jobs
from .media import ensure_ffmpeg
from .models import JobResponse

app = FastAPI(title="Audio Segment Navigator", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    try:
        ensure_ffmpeg()
        available = True
    except Exception:
        available = False
    return {"status": "ok", "ffmpeg": available}


@app.post("/api/jobs", response_model=JobResponse, status_code=202)
async def create_job(file: UploadFile = File(...)) -> JobResponse:
    filename = Path(file.filename or "media").name
    extension = Path(filename).suffix.lower()
    if extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    upload_dir = settings.temp_dir / str(uuid.uuid4())
    upload_dir.mkdir(parents=True, exist_ok=False)
    destination = upload_dir / f"source{extension}"
    size = 0
    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="The uploaded file is too large.")
                output.write(chunk)
    except Exception:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise
    finally:
        await file.close()

    job = jobs.create(destination, filename, file.content_type or "application/octet-stream")
    return job.response()


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return job.response()


@app.get("/api/jobs/{job_id}/media")
def stream_media(job_id: str) -> FileResponse:
    job = jobs.get(job_id)
    if job is None or not job.source_path.exists():
        raise HTTPException(status_code=404, detail="Media not found.")
    return FileResponse(
        job.source_path,
        media_type=job.content_type,
        filename=job.original_filename,
        content_disposition_type="inline",
    )


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: str) -> None:
    if jobs.delete(job_id) is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
