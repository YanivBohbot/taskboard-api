from fastapi import FastAPI

from app.errors import register_error_handlers
from app.rate_limit import FixedWindowRateLimiter, RateLimitMiddleware
from app.routers import health, projects, tasks

rate_limiter = FixedWindowRateLimiter()
app = FastAPI(title="taskboard-api", version="0.1.0")
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)
register_error_handlers(app)
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(tasks.router)
