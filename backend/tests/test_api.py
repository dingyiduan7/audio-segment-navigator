from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_reports_service_state() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert isinstance(response.json()["ffmpeg"], bool)


def test_rejects_unsupported_upload() -> None:
    response = client.post(
        "/api/jobs",
        files={"file": ("notes.txt", b"not media", "text/plain")},
    )

    assert response.status_code == 415
