import csv
from datetime import UTC, datetime
from io import StringIO

import pytest

from app.models import Task, TaskStatus
from app.services import task_service


def _create(client, project_id, **kw):
    payload = {"title": "Write docs", "assignee": "dev@example.com"}
    payload.update(kw)
    return client.post(f"/projects/{project_id}/tasks", json=payload)


def _read_csv(text):
    return list(csv.reader(StringIO(text)))


def _parse_iso8601_with_timezone(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() is not None
    return parsed


def test_create_task_defaults_to_todo(client, project):
    r = _create(client, project["id"])
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "todo"
    assert body["project_id"] == project["id"]
    assert body["assignee"] == "dev@example.com"


def test_task_model_supplies_created_at_default_for_direct_construction():
    task = Task(
        id=1,
        project_id=1,
        title="Direct",
        assignee="dev@example.com",
        assignee_domain="example.com",
        status=TaskStatus.todo,
    )

    assert task.created_at.tzinfo is not None


def test_create_task_uses_current_timezone_aware_timestamp(client, project, monkeypatch):
    fixed_now = datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)
    monkeypatch.setattr(task_service, "_now_utc", lambda: fixed_now)

    r = _create(client, project["id"])

    assert r.status_code == 201
    created_at = _parse_iso8601_with_timezone(r.json()["created_at"])
    assert created_at == fixed_now


def test_create_task_in_missing_project_returns_404(client):
    r = _create(client, 42)
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")


def test_create_task_invalid_status_returns_422(client, project):
    r = _create(client, project["id"], status="blocked")
    assert r.status_code == 422
    assert r.json()["status"] == 422


def test_get_task(client, project):
    task = _create(client, project["id"]).json()
    r = client.get(f"/projects/{project['id']}/tasks/{task['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Write docs"


def test_get_missing_task_returns_404(client, project):
    r = client.get(f"/projects/{project['id']}/tasks/99")
    assert r.status_code == 404
    assert r.json()["status"] == 404


def test_task_not_visible_from_other_project(client, project):
    other = client.post("/projects", json={"name": "Other"}).json()
    task = _create(client, project["id"]).json()
    assert client.get(f"/projects/{other['id']}/tasks/{task['id']}").status_code == 404


def test_update_task_status(client, project):
    task = _create(client, project["id"]).json()
    r = client.put(
        f"/projects/{project['id']}/tasks/{task['id']}",
        json={"status": "in_progress"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"
    assert r.json()["title"] == "Write docs"


def test_delete_task(client, project):
    task = _create(client, project["id"]).json()
    assert client.delete(f"/projects/{project['id']}/tasks/{task['id']}").status_code == 204
    assert client.get(f"/projects/{project['id']}/tasks/{task['id']}").status_code == 404


def test_list_tasks_pagination(client, project):
    for i in range(5):
        _create(client, project["id"], title=f"T{i}")
    r = client.get(f"/projects/{project['id']}/tasks", params={"limit": 2, "offset": 3})
    body = r.json()
    assert body["total"] == 5
    assert [t["title"] for t in body["items"]] == ["T3", "T4"]


def test_list_tasks_filter_by_status(client, project):
    _create(client, project["id"], title="a")
    _create(client, project["id"], title="b", status="done")
    r = client.get(f"/projects/{project['id']}/tasks", params={"status": "done"})
    assert [t["title"] for t in r.json()["items"]] == ["b"]


def test_ac1_export_tasks_csv_includes_only_specified_columns_in_order(client, project):
    task = _create(client, project["id"], title="Only columns").json()

    r = client.get(f"/projects/{project['id']}/tasks/export.csv")

    rows = _read_csv(r.text)
    assert rows[0] == ["id", "title", "status", "assignee", "created_at"]
    assert len(rows[1]) == 5
    assert rows[1][:4] == [
        str(task["id"]),
        "Only columns",
        task["status"],
        task["assignee"],
    ]
    _parse_iso8601_with_timezone(rows[1][4])


def test_ac2_export_tasks_csv_content_type(client, project):
    r = client.get(f"/projects/{project['id']}/tasks/export.csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")


def test_ac3_export_tasks_csv_has_one_ordered_row_per_project_task(client, project):
    _create(client, project["id"], title="first")
    other = client.post("/projects", json={"name": "Other"}).json()
    _create(client, other["id"], title="not exported")
    _create(client, project["id"], title="second")

    r = client.get(f"/projects/{project['id']}/tasks/export.csv")

    rows = _read_csv(r.text)
    assert [row[0] for row in rows[1:]] == ["1", "3"]
    assert [row[1] for row in rows[1:]] == ["first", "second"]


def test_ac4_export_tasks_csv_quotes_rfc4180_values(client, project):
    _create(
        client,
        project["id"],
        title='Needs "quotes", comma\nand newline',
        assignee='dev,"ops"@example.com',
    )

    r = client.get(f"/projects/{project['id']}/tasks/export.csv")

    assert '"Needs ""quotes"", comma\nand newline"' in r.text
    assert '"dev,""ops""@example.com"' in r.text
    assert _read_csv(r.text)[1][1:4] == [
        'Needs "quotes", comma\nand newline',
        "todo",
        'dev,"ops"@example.com',
    ]


def test_ac5_export_tasks_csv_empty_project_returns_header_only(client, project):
    r = client.get(f"/projects/{project['id']}/tasks/export.csv")
    assert r.status_code == 200
    assert _read_csv(r.text) == [["id", "title", "status", "assignee", "created_at"]]


def test_ac6_export_tasks_csv_missing_project_returns_problem_json(client):
    r = client.get("/projects/999/tasks/export.csv")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert set(body) == {"type", "title", "status", "detail"}
    assert body["title"] == "Not Found"
    assert body["status"] == 404
    assert body["detail"] == "Project 999 not found"


@pytest.mark.parametrize("limit", [0, 101])
def test_pagination_limit_out_of_range_returns_422(client, limit):
    r = client.get("/projects", params={"limit": limit})
    assert r.status_code == 422


@pytest.mark.xfail(strict=True, reason="SHIP bug demo")
def test_create_task_with_empty_assignee_returns_500():
    """Documents the deliberate bug: an empty assignee crashes the service (500).

    Expected behaviour once fixed: a 422 problem+json. The assertion below
    states the *desired* behaviour, so the test fails (xfail) today.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app, raise_server_exceptions=False)
    pid = c.post("/projects", json={"name": "Bug"}).json()["id"]
    r = c.post(f"/projects/{pid}/tasks", json={"title": "x", "assignee": ""})
    assert r.status_code == 422
