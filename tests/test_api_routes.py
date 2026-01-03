import io
import json

import pandas as pd

from src.models.schemas import AnalysisType, JobStatus


def test_file_upload_and_analysis_flow(test_client, fake_redis, mock_env, monkeypatch):
    # Upload
    data = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "b": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]})
    csv_bytes = data.to_csv(index=False).encode()

    response = test_client.post(
        "/api/v1/upload/",
        files={"file": ("data.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert response.status_code == 201
    file_id = response.json()["file_id"]

    # Trigger analysis synchronously (background disabled via fixture)
    payload = {
        "file_id": file_id,
        "analysis_types": [AnalysisType.ALL.value],
        "generate_insights": False,
        "generate_visualizations": False,
    }
    response = test_client.post("/api/v1/analyze/", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Status
    status_resp = test_client.get(f"/api/v1/analyze/status/{job_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] in {JobStatus.PENDING.value, JobStatus.PROCESSING.value, JobStatus.COMPLETED.value}

    # Force-complete the job in fake redis for predictable result retrieval
    job_key = f"eda:job:{job_id}"
    fake_redis.set_hash(job_key, {"status": JobStatus.COMPLETED.value, "created_at": body["created_at"], "result_available": True})

    # Prepare a small result entry so result endpoint works deterministically
    result_key = f"eda:result:{job_id}"
    fake_redis.set(result_key, {
        "job_id": job_id,
        "file_id": file_id,
        "dataset_schema": {"row_count": 10, "column_count": 2, "columns": [], "total_missing": 0, "memory_usage_mb": 0.01},
        "column_statistics": [],
        "correlation_analysis": None,
        "outlier_analysis": [],
        "distribution_analysis": [],
        "visualizations": [],
        "ai_insights": None,
        "analysis_duration_seconds": 0.1,
        "completed_at": body["created_at"],
    })

    result_resp = test_client.get(f"/api/v1/analyze/result/{job_id}")
    assert result_resp.status_code == 200
    assert result_resp.json()["result"]["job_id"] == job_id


def test_health_endpoint(test_client):
    resp = test_client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] in {"healthy", "degraded"}
