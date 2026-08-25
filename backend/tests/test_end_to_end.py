import shutil
import time
import wave

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


ffmpeg_available = bool(
    shutil.which(settings.ffmpeg_binary) and shutil.which(settings.ffprobe_binary)
)


@pytest.mark.skipif(not ffmpeg_available, reason="FFmpeg is not installed")
def test_upload_to_detected_segments_pipeline(tmp_path) -> None:
    sample_rate = 4000
    time_axis = np.arange(30 * sample_rate, dtype=np.float32) / sample_rate
    samples = np.concatenate(
        [
            0.25 * np.sin(2 * np.pi * 220 * time_axis),
            np.zeros(int(1.5 * sample_rate), dtype=np.float32),
            0.25 * np.sin(2 * np.pi * 660 * time_axis),
        ]
    )
    media_path = tmp_path / "two-tracks.wav"
    with wave.open(str(media_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes((samples * 32767).astype("<i2").tobytes())

    client = TestClient(app)
    with media_path.open("rb") as media:
        response = client.post(
            "/api/jobs",
            files={"file": (media_path.name, media, "audio/wav")},
        )
    assert response.status_code == 202
    job = response.json()

    deadline = time.monotonic() + 15
    while job["state"] in {"queued", "processing"} and time.monotonic() < deadline:
        time.sleep(0.1)
        job = client.get(f"/api/jobs/{job['id']}").json()

    assert job["state"] == "completed", job.get("error")
    assert len(job["segments"]) == 2
    assert abs(job["segments"][0]["end"] - 30.75) < 1.5
    assert client.get(job["media_url"]).status_code == 200
    assert client.delete(f"/api/jobs/{job['id']}").status_code == 204
