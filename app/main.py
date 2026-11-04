from fastapi import FastAPI

from app.errors import register_error_handlers
from app.routers import health, projects, tasks

app = FastAPI(title="taskboard-api", version="0.1.0")
register_error_handlers(app)
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(tasks.router)
