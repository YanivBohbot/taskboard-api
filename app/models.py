from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class Project(BaseModel):
    id: int
    name: str
    description: str = ""


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    # Assignee email. No email validation on purpose (see README).
    assignee: str
    status: TaskStatus = TaskStatus.todo


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    assignee: str | None = None
    status: TaskStatus | None = None


class Task(BaseModel):
    id: int
    project_id: int
    title: str
    assignee: str
    assignee_domain: str
    status: TaskStatus
    # Services set persisted task timestamps explicitly; this default keeps
    # direct model construction valid.
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
