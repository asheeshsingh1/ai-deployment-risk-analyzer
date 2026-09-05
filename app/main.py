from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Deployment Risk Analyzer",
    description=(
        "AI-powered deployment risk analysis platform."
    ),
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
    }