"""Project API routes."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.models.project import ProjectDetail, ProjectSummary
from app.models.character import CharacterTable
from app.pipeline.stage0 import run_stage0
from app.pipeline.stage1 import run_stage1
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


@router.post("/projects/{project_id}/process")
def process_project(project_id: str, from_stage: str = "preprocessing"):
    """Trigger pipeline processing from a specific stage."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        if from_stage == "preprocessing":
            result = run_stage0(project_id)
            return {
                "status": "succeeded",
                "stage": "preprocessing",
                "chapters": len(result.chapters),
                "paragraphs": sum(len(ch.paragraphs) for ch in result.chapters),
                "detected_language": result.detected_language,
            }
        elif from_stage == "character_extraction":
            result = run_stage1(project_id)
            return {
                "status": "succeeded",
                "stage": "character_extraction",
                "characters": len(result.characters),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown stage: {from_stage}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/characters")
def get_characters(project_id: str):
    """Return the character table."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    char_file = storage.get_project_dir(project_id) / "03_characters.json"
    if not char_file.exists():
        raise HTTPException(status_code=404, detail="Characters not extracted yet")

    return json.loads(char_file.read_text(encoding="utf-8"))


@router.put("/projects/{project_id}/characters")
def update_characters(project_id: str, data: dict):
    """Save edited character table."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate it's a valid CharacterTable
    try:
        table = CharacterTable.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid character data: {e}")

    char_file = storage.get_project_dir(project_id) / "03_characters.json"
    char_file.write_text(table.model_dump_json(indent=2), encoding="utf-8")

    return {"status": "saved", "characters": len(table.characters)}


@router.get("/projects/{project_id}/stages/{stage}")
def get_stage_result(project_id: str, stage: str):
    """Return intermediate JSON for a pipeline stage."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    stage_files = {
        "preprocessing": "02_preprocessed.json",
        "character_extraction": "03_characters.json",
        "scene_synthesis": "04_scenes.json",
        "validation": "05_validated.json",
    }

    filename = stage_files.get(stage)
    if not filename:
        raise HTTPException(status_code=400, detail=f"Unknown stage: {stage}")

    file_path = storage.get_project_dir(project_id) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Stage '{stage}' has not been run yet")

    data = json.loads(file_path.read_text(encoding="utf-8"))
    return data
