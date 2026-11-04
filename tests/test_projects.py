def test_create_project(client):
    r = client.post("/projects", json={"name": "Alpha", "description": "First"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Alpha"
    assert body["description"] == "First"
    assert body["id"] == 1


def test_get_project(client, project):
    r = client.get(f"/projects/{project['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Alpha"


def test_get_missing_project_returns_problem_json(client):
    r = client.get("/projects/999")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert set(body) == {"type", "title", "status", "detail"}
    assert body["status"] == 404


def test_update_project(client, project):
    r = client.put(f"/projects/{project['id']}", json={"name": "Beta"})
    assert r.status_code == 200
    assert r.json()["name"] == "Beta"


def test_delete_project(client, project):
    assert client.delete(f"/projects/{project['id']}").status_code == 204
    assert client.get(f"/projects/{project['id']}").status_code == 404


def test_delete_project_removes_its_tasks(client, project):
    client.post(f"/projects/{project['id']}/tasks", json={"title": "t", "assignee": "a@b.io"})
    client.delete(f"/projects/{project['id']}")
    from app import storage

    assert storage.tasks == {}


def test_duplicate_project_name_returns_409(client, project):
    r = client.post("/projects", json={"name": "Alpha"})
    assert r.status_code == 409
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 409


def test_create_project_validation_error_is_problem_json(client):
    r = client.post("/projects", json={"name": ""})
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["status"] == 422


def test_list_projects_pagination(client):
    for i in range(5):
        client.post("/projects", json={"name": f"P{i}"})
    r = client.get("/projects", params={"limit": 2, "offset": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert [p["name"] for p in body["items"]] == ["P1", "P2"]
