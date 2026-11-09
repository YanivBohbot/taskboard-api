import importlib.metadata
from types import SimpleNamespace

from app import storage
from app.services import health_service


class NoScanDict(dict):
    def __iter__(self):
        raise AssertionError("health endpoint must not iterate storage")

    def items(self):
        raise AssertionError("health endpoint must not scan storage items")

    def keys(self):
        raise AssertionError("health endpoint must not scan storage keys")

    def values(self):
        raise AssertionError("health endpoint must not scan storage values")


def test_ac1_health_response_has_detailed_ok_shape(client):
    r = client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "status",
        "version",
        "uptime_seconds",
        "project_count",
        "task_count",
    }
    assert body["status"] == "ok"


def test_ac2_version_comes_from_installed_package_metadata(client, monkeypatch):
    expected = importlib.metadata.version("taskboard-api")
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["version"] == expected

    def fake_version(distribution_name: str) -> str:
        assert distribution_name == "taskboard-api"
        return "2030.4"

    monkeypatch.setattr(health_service.importlib.metadata, "version", fake_version)
    r = client.get("/health")

    assert r.status_code == 200
    assert r.json()["version"] == "2030.4"


def test_ac3_uptime_is_non_negative_number_from_monotonic_start(client, monkeypatch):
    ticks = iter([100.25, 101.5])
    monkeypatch.setattr(health_service, "_STARTED_AT", 100.0)
    monkeypatch.setattr(
        health_service,
        "time",
        SimpleNamespace(monotonic=lambda: next(ticks)),
    )

    first = client.get("/health").json()["uptime_seconds"]
    second = client.get("/health").json()["uptime_seconds"]

    assert isinstance(first, int | float)
    assert first >= 0
    assert second > first


def test_ac4_counts_reflect_current_in_memory_storage(client):
    first_project = client.post("/projects", json={"name": "Alpha"}).json()
    second_project = client.post("/projects", json={"name": "Beta"}).json()
    client.post(
        f"/projects/{first_project['id']}/tasks",
        json={"title": "One", "assignee": "one@example.com"},
    )
    client.post(
        f"/projects/{first_project['id']}/tasks",
        json={"title": "Two", "assignee": "two@example.com"},
    )
    client.post(
        f"/projects/{second_project['id']}/tasks",
        json={"title": "Three", "assignee": "three@example.com"},
    )

    r = client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert body["project_count"] == 2
    assert body["task_count"] == 3


def test_ac5_health_is_unauthenticated_empty_safe_and_uses_len_only(client, monkeypatch):
    monkeypatch.setattr(storage, "projects", NoScanDict())
    monkeypatch.setattr(storage, "tasks", NoScanDict())

    r = client.get("/health")

    assert r.status_code == 200
    body = r.json()
    assert body["project_count"] == 0
    assert body["task_count"] == 0
