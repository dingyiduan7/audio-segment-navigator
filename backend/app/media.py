from __future__ import annotations

import json
import mimetypes
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

from .config import settings
from .models import MediaInfo


class MediaError(RuntimeError):
    pass


def ensure_ffmpeg() -> None:
    missing = [
        binary
        for binary in (settings.ffmpeg_binary, settings.ffprobe_binary)
        if shutil.which(binary) is None
    ]
    if missing:
        raise MediaError(
            "FFmpeg is required but was not found. Install ffmpeg and ensure both "
            f"ffmpeg and ffprobe are on PATH (missing: {', '.join(missing)})."
        )


def probe_media(path: Path, filename: str, content_type: str | None) -> MediaInfo:
    ensure_ffmpeg()
    command = [
        settings.ffprobe_binary,
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise MediaError(result.stderr.strip() or "The uploaded file is not valid media.")

    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MediaError("Could not determine media duration.") from exc

    if duration <= 0:
        raise MediaError("The uploaded media has no playable duration.")

    mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return MediaInfo(
        filename=filename,
        content_type=mime,
        duration=duration,
        has_video=any(stream.get("codec_type") == "video" for stream in data.get("streams", [])),
    )


def extract_analysis_audio(source: Path, destination: Path, sample_rate: int = 22050) -> None:
    ensure_ffmpeg()
    command = [
        settings.ffmpeg_binary,
        "-y",
        "-v",
        "error",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(destination),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=3600)
    if result.returncode:
        raise MediaError(result.stderr.strip() or "FFmpeg could not decode the media.")


def read_wave_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as audio:
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        sample_rate = audio.getframerate()
        frames = audio.readframes(audio.getnframes())

    if sample_width != 2:
        raise MediaError("The extracted analysis audio is not 16-bit PCM.")
    samples = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples, sample_rate
