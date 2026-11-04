from app import storage
from app.errors import NotFoundError
from app.models import Page, Task, TaskCreate, TaskStatus, TaskUpdate
from app.services.project_service import get_project


def _domain(assignee: str) -> str:
    # Derive the email domain used for grouping/notifications.
    return assignee.split("@")[1]


def create_task(project_id: int, data: TaskCreate) -> Task:
    get_project(project_id)
    task = Task(
        id=storage.next_id("task"),
        project_id=project_id,
        title=data.title,
        assignee=data.assignee,
        assignee_domain=_domain(data.assignee),
        status=data.status,
    )
    storage.tasks[task.id] = task
    return task


def get_task(project_id: int, task_id: int) -> Task:
    get_project(project_id)
    task = storage.tasks.get(task_id)
    if task is None or task.project_id != project_id:
        raise NotFoundError(f"Task {task_id} not found in project {project_id}")
    return task


def list_tasks(
    project_id: int, limit: int, offset: int, status: TaskStatus | None = None
) -> Page[Task]:
    get_project(project_id)
    items = [t for t in storage.tasks.values() if t.project_id == project_id]
    if status is not None:
        items = [t for t in items if t.status == status]
    return Page[Task](
        items=items[offset : offset + limit], total=len(items), limit=limit, offset=offset
    )


def update_task(project_id: int, task_id: int, data: TaskUpdate) -> Task:
    task = get_task(project_id, task_id)
    changes = data.model_dump(exclude_none=True)
    if "assignee" in changes:
        changes["assignee_domain"] = _domain(changes["assignee"])
    updated = task.model_copy(update=changes)
    storage.tasks[task_id] = updated
    return updated


def delete_task(project_id: int, task_id: int) -> None:
    get_task(project_id, task_id)
    del storage.tasks[task_id]
