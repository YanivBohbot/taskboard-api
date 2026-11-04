import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture(autouse=True)
def _reset_storage():
    storage.reset()
    yield
    storage.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def project(client):
    return client.post("/projects", json={"name": "Alpha"}).json()
