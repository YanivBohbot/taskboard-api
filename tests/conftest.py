from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app, rate_limiter


@pytest.fixture(autouse=True)
def _reset_state() -> Generator[None, None, None]:
    storage.reset()
    rate_limiter.reset()
    yield
    storage.reset()
    rate_limiter.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def project(client: TestClient) -> dict[str, Any]:
    return client.post("/projects", json={"name": "Alpha"}).json()
