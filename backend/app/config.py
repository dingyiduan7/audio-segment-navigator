from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    temp_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("AUDIO_PARSER_TEMP_DIR", Path(tempfile.gettempdir()) / "audio-parser")
        )
    )
    max_upload_bytes: int = int(os.getenv("AUDIO_PARSER_MAX_UPLOAD_MB", "2048")) * 1024 * 1024
    job_ttl_seconds: int = int(os.getenv("AUDIO_PARSER_JOB_TTL_SECONDS", "21600"))
    ffmpeg_binary: str = os.getenv("FFMPEG_BINARY", "ffmpeg")
    ffprobe_binary: str = os.getenv("FFPROBE_BINARY", "ffprobe")
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: _csv_env(
            "AUDIO_PARSER_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        )
    )
    allowed_extensions: tuple[str, ...] = (
        ".mp3",
        ".wav",
        ".flac",
        ".m4a",
        ".aac",
        ".ogg",
        ".opus",
        ".mp4",
        ".mkv",
        ".webm",
        ".mov",
        ".avi",
    )


settings = Settings()
settings.temp_dir.mkdir(parents=True, exist_ok=True)
