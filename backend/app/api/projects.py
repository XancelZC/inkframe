"""Project API routes."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.models.project import ProjectDetail, ProjectSummary
from app import storage

router = APIRouter(tags=["projects"])


class CreateProjectRequest(BaseModel):
    title: str
    source_language: Optional[str] = None
    text: Optional[str] = None


@router.get("/projects", response_model=list[ProjectSummary])
def list_projects():
    """Return all projects."""
    return storage.list_projects()


@router.post("/projects", response_model=ProjectSummary, status_code=201)
async def create_project(
    title: str = Form(...),
    source_language: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Create a new project from pasted text or uploaded file."""
    content = None

    if file is not None:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
    elif text is not None:
        content = text

    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="No text content provided")

    content = content.strip()
    if source_language is None:
        source_language = storage.detect_language(content)

    summary = storage.create_project(
        title=title,
        source_language=source_language,
        raw_text=content,
    )
    return summary


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
