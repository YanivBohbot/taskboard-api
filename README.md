# taskboard-api

A small in-memory FastAPI service for managing projects and their tasks.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Returns status, package version, uptime, and in-memory project/task counts |
| POST, GET | `/projects` | Create / list (`limit` 1-100, `offset`) |
| GET, PUT, DELETE | `/projects/{project_id}` | Deleting a project deletes its tasks |
| POST, GET | `/projects/{project_id}/tasks` | Create / list (`limit`, `offset`, `status`) |
| GET, PUT, DELETE | `/projects/{project_id}/tasks/{task_id}` | |

Task status is one of `todo`, `in_progress`, `done`. The assignee is an email address.

## Error format (ADR-001)

Errors raised by the app (404, 409, 422) use RFC 7807 `application/problem+json`:

```json
{"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Project 7 not found"}
```

## Development

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Running tests

```bash
uv run pytest -q
```

The known-bug test (`test_create_task_with_empty_assignee_returns_500`) is an expected failure (xfail, strict).

## Layout

- `app/routers/` - HTTP layer
- `app/services/` - business logic
- `app/models.py` - pydantic models
- `app/storage.py` - in-memory storage
- `app/errors.py` - problem+json error handling
