"""In-memory storage. Process-local; data is lost on restart."""

from app.models import Project, Task

projects: dict[int, Project] = {}
tasks: dict[int, Task] = {}
_counters = {"project": 0, "task": 0}


def next_id(kind: str) -> int:
    _counters[kind] += 1
    return _counters[kind]


def reset() -> None:
    projects.clear()
    tasks.clear()
    for k in _counters:
        _counters[k] = 0
