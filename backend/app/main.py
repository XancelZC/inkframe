"""InkFrame FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.projects import router as projects_router
from app.api.models import router as models_router
from app.api.novels import router as novels_router

app = FastAPI(title="InkFrame", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(novels_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
