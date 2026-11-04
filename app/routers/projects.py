from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.models import Page, Project, ProjectCreate, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@router.post("", status_code=201)
def create_project(data: ProjectCreate) -> Project:
    return project_service.create_project(data)


@router.get("")
def list_projects(limit: Limit = 20, offset: Offset = 0) -> Page[Project]:
    return project_service.list_projects(limit, offset)


@router.get("/{project_id}")
def get_project(project_id: int) -> Project:
    return project_service.get_project(project_id)


@router.put("/{project_id}")
def update_project(project_id: int, data: ProjectUpdate) -> Project:
    return project_service.update_project(project_id, data)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int) -> Response:
    project_service.delete_project(project_id)
    return Response(status_code=204)
