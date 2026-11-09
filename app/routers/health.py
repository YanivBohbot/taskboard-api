from fastapi import APIRouter

from app.models import HealthStatus
from app.services import health_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> HealthStatus:
    return health_service.get_health()
