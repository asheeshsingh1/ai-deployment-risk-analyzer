from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.repositories import router as repositories_router
from app.api.risk import router as risk_router
from app.api.scm import router as scm_router
from app.api.services import router as services_router
from app.api.analysis import router as analysis_router
from app.api.history import router as history_router
from app.config import get_settings
from fastapi.middleware.cors import CORSMiddleware


settings = get_settings()

app = FastAPI(
    title="Deployment Risk Analyzer",
    description=("AI-powered deployment risk analysis platform."),
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(risk_router)
app.include_router(scm_router)
app.include_router(repositories_router)
app.include_router(services_router)
app.include_router(analysis_router)
app.include_router(history_router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": "0.4.0",
        "status": "running",
    }
