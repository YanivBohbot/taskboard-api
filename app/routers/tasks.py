from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.models import Page, Task, TaskCreate, TaskStatus, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@router.post("", status_code=201)
def create_task(project_id: int, data: TaskCreate) -> Task:
    return task_service.create_task(project_id, data)


@router.get("")
def list_tasks(
    project_id: int,
    limit: Limit = 20,
    offset: Offset = 0,
    status: TaskStatus | None = None,
) -> Page[Task]:
    return task_service.list_tasks(project_id, limit, offset, status)


@router.get("/{task_id}")
def get_task(project_id: int, task_id: int) -> Task:
    return task_service.get_task(project_id, task_id)


@router.put("/{task_id}")
def update_task(project_id: int, task_id: int, data: TaskUpdate) -> Task:
    return task_service.update_task(project_id, task_id, data)


@router.delete("/{task_id}", status_code=204)
def delete_task(project_id: int, task_id: int) -> Response:
    task_service.delete_task(project_id, task_id)
    return Response(status_code=204)
