"""
FastAPI entrypoint. Run locally with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.uploads import router as uploads_router
from app.core.config import settings

app = FastAPI(title="Reel Edit AI", debug=settings.DEBUG)

app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(projects_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
