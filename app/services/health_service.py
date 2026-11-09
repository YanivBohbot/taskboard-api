import importlib.metadata
import time

from app import storage
from app.models import HealthStatus

_DISTRIBUTION_NAME = "taskboard-api"
_STARTED_AT = time.monotonic()


def get_health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        version=importlib.metadata.version(_DISTRIBUTION_NAME),
        uptime_seconds=time.monotonic() - _STARTED_AT,
        project_count=len(storage.projects),
        task_count=len(storage.tasks),
    )
