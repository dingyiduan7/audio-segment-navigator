from app.jobs import JobStore


def test_update_is_safe_after_job_is_deleted() -> None:
    store = JobStore()

    assert store._update("missing-job", progress=1.0) is None
