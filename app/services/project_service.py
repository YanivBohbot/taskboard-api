from app import storage
from app.errors import ConflictError, NotFoundError
from app.models import Page, Project, ProjectCreate, ProjectUpdate


def create_project(data: ProjectCreate) -> Project:
    if any(p.name == data.name for p in storage.projects.values()):
        raise ConflictError(f"Project named '{data.name}' already exists")
    project = Project(id=storage.next_id("project"), **data.model_dump())
    storage.projects[project.id] = project
    return project


def get_project(project_id: int) -> Project:
    project = storage.projects.get(project_id)
    if project is None:
        raise NotFoundError(f"Project {project_id} not found")
    return project


def list_projects(limit: int, offset: int) -> Page[Project]:
    items = list(storage.projects.values())
    return Page[Project](
        items=items[offset : offset + limit], total=len(items), limit=limit, offset=offset
    )


def update_project(project_id: int, data: ProjectUpdate) -> Project:
    project = get_project(project_id)
    updated = project.model_copy(update=data.model_dump(exclude_none=True))
    storage.projects[project_id] = updated
    return updated


def delete_project(project_id: int) -> None:
    get_project(project_id)
    del storage.projects[project_id]
    for tid in [t.id for t in storage.tasks.values() if t.project_id == project_id]:
        del storage.tasks[tid]
