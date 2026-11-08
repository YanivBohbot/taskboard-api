import pytest


def _create(client, project_id, **kw):
    payload = {"title": "Write docs", "assignee": "dev@example.com"}
    payload.update(kw)
    return client.post(f"/projects/{project_id}/tasks", json=payload)


def test_create_task_defaults_to_todo(client, project):
    r = _create(client, project["id"])
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "todo"
    assert body["project_id"] == project["id"]
    assert body["assignee"] == "dev@example.com"


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


@pytest.mark.parametrize("limit", [0, 101])
def test_pagination_limit_out_of_range_returns_422(client, limit):
    r = client.get("/projects", params={"limit": limit})
    assert r.status_code == 422


def test_ac1_empty_assignee_returns_422_problem(client, project):
    r = client.post(
        f"/projects/{project['id']}/tasks",
        json={"title": "Write docs", "assignee": ""},
    )

    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert set(body) == {"type", "title", "status", "detail"}
    assert body["type"] == "about:blank"
    assert body["title"] == "Unprocessable Entity"
    assert body["status"] == 422
    assert "assignee" in body["detail"]
