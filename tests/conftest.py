import json
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from src.core.config import settings


class FakeRedis:
    """Lightweight in-memory Redis stub for tests."""

    def __init__(self):
        self.store: Dict[str, Any] = {}
        self.hashes: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        self.store[key] = value
        return True

    def get(self, key: str, deserialize: bool = True) -> Any:
        value = self.store.get(key)
        if deserialize and isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def delete(self, key: str) -> bool:
        self.store.pop(key, None)
        self.hashes.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        return key in self.store or key in self.hashes

    def expire(self, key: str, seconds: int) -> bool:  # pragma: no cover - no-op
        return True

    def increment(self, key: str, amount: int = 1) -> int:
        self.store[key] = int(self.store.get(key, 0)) + amount
        return self.store[key]

    def set_hash(self, name: str, mapping: dict) -> bool:
        self.hashes[name] = mapping
        return True

    def get_hash(self, name: str) -> Dict[str, Any] | None:
        return self.hashes.get(name)

    # Compatibility shim for health checks
    @property
    def client(self):
        return self

    def ping(self):  # pragma: no cover - simple availability check
        return True


@pytest.fixture(scope="session")
def mock_env(tmp_path_factory):
    """Isolate filesystem-dependent settings under a temp directory."""
    base = tmp_path_factory.mktemp("eda_test_data")
    upload = base / "uploads"
    results = base / "results"
    temp = base / "temp"
    for path in (upload, results, temp):
        path.mkdir(parents=True, exist_ok=True)

    original = {
        "upload_dir": settings.file_upload.upload_dir,
        "results_dir": settings.file_upload.results_dir,
        "temp_dir": settings.file_upload.temp_dir,
        "background": settings.performance.background_tasks_enabled,
    }

    settings.file_upload.upload_dir = upload
    settings.file_upload.results_dir = results
    settings.file_upload.temp_dir = temp
    settings.performance.background_tasks_enabled = False

    yield {
        "upload_dir": upload,
        "results_dir": results,
        "temp_dir": temp,
    }

    settings.file_upload.upload_dir = original["upload_dir"]
    settings.file_upload.results_dir = original["results_dir"]
    settings.file_upload.temp_dir = original["temp_dir"]
    settings.performance.background_tasks_enabled = original["background"]


@pytest.fixture()
def fake_redis(monkeypatch):
    """Patch redis_client everywhere with an in-memory stub."""
    mock = FakeRedis()
    monkeypatch.setattr("src.core.redis_client.redis_client", mock, raising=False)
    monkeypatch.setattr("src.api.routes.upload.redis_client", mock, raising=False)
    monkeypatch.setattr("src.api.routes.analysis.redis_client", mock, raising=False)
    monkeypatch.setattr("src.tasks.eda_tasks.redis_client", mock, raising=False)
    return mock


@pytest.fixture()
def test_client(mock_env, fake_redis):
    """FastAPI TestClient with patched environment and Redis."""
    from src.main import app

    return TestClient(app)
