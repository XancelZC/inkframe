"""Project API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.project import ProjectDetail, ProjectSummary
from app import storage

router = APIRouter(tags=["projects"])


class CreateProjectRequest(BaseModel):
    title: str
    source_language: Optional[str] = None


@router.get("/projects", response_model=list[ProjectSummary])
def list_projects():
    """Return all projects."""
    return storage.list_projects()


@router.post("/projects", response_model=ProjectSummary, status_code=201)
def create_project(req: CreateProjectRequest):
    """Create a new project."""
    return storage.create_project(title=req.title, source_language=req.source_language)


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str):
    """Return project detail including raw text."""
    projects = storage.list_projects()
    summary = next((p for p in projects if p.id == project_id), None)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found")

    raw_text = storage.get_raw_text(project_id)
    return ProjectDetail(
        id=summary.id,
        title=summary.title,
        source_language=summary.source_language,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        raw_text=raw_text,
    )
