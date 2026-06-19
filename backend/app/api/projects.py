"""Project API routes."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.project import ProjectDetail, ProjectSummary
from app.models.character import CharacterTable
from app.models.status import PipelineStatus
from app.api.models import get_active_provider_id, get_provider_type
from app.pipeline.stage0 import run_stage0
from app.pipeline.stage1 import run_stage1
from app.pipeline.stage2 import run_stage2
from app.pipeline.stage3 import run_stage3
from app.pipeline.progress import ProgressTracker, get_status
from app import storage

router = APIRouter(tags=["projects"])


class CreateProjectRequest(BaseModel):
    title: str
    source_language: Optional[str] = None
    text: Optional[str] = None


class SourceTextUpdateRequest(BaseModel):
    raw_text: str


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


@router.put("/projects/{project_id}")
def update_project(project_id: str, title: Optional[str] = None):
    """Update project title."""
    if title and not storage.update_project_title(project_id, title):
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"status": "saved"}


@router.put("/projects/{project_id}/source", response_model=ProjectDetail)
def update_project_source(project_id: str, data: SourceTextUpdateRequest):
    """Update project source text and invalidate generated pipeline outputs."""
    raw_text = data.raw_text
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No text content provided")

    summary = storage.update_project_raw_text(project_id, raw_text)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectDetail(
        id=summary.id,
        novel_id=summary.novel_id,
        title=summary.title,
        source_language=summary.source_language,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        raw_text=raw_text,
    )


@router.delete("/projects/{project_id}")
def delete_project(project_id: str):
    """Delete a project."""
    if not storage.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted", "id": project_id}


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
        novel_id=summary.novel_id,
        title=summary.title,
        source_language=summary.source_language,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        raw_text=raw_text,
    )


STAGE_ORDER = ["preprocessing", "character_extraction", "scene_synthesis", "validation"]


@router.post("/projects/{project_id}/process")
def process_project(project_id: str, from_stage: str = "preprocessing"):
    """Trigger pipeline processing from a specific stage.

    Validates that all prerequisite stage outputs exist.
    """
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    # Check prerequisites
    if from_stage not in STAGE_ORDER:
        raise HTTPException(status_code=400, detail=f"Unknown stage: {from_stage}")

    stage_idx = STAGE_ORDER.index(from_stage)
    if stage_idx > 0:
        project_dir = storage.get_project_dir(project_id)
        stage_files = {
            "preprocessing": "02_preprocessed.json",
            "character_extraction": "03_characters.json",
            "scene_synthesis": "04_scenes.json",
        }
        for i in range(stage_idx):
            prereq = STAGE_ORDER[i]
            prereq_file = project_dir / stage_files.get(prereq, "")
            if not prereq_file.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot run '{from_stage}': prerequisite '{prereq}' has not been run",
                )

    try:
        # 根据 active 供应商的 type 决定用哪个 LLM provider
        active_pid = get_active_provider_id()
        provider_id = get_provider_type(active_pid)

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
            result = run_stage1(project_id, provider_id=provider_id)
            return {
                "status": "succeeded",
                "stage": "character_extraction",
                "characters": len(result.characters),
            }
        elif from_stage == "scene_synthesis":
            result = run_stage2(project_id, provider_id=provider_id)
            total_elements = sum(len(s.elements) for s in result)
            return {
                "status": "succeeded",
                "stage": "scene_synthesis",
                "scenes": len(result),
                "elements": total_elements,
            }
        elif from_stage == "validation":
            result = run_stage3(project_id)
            return {
                "status": "succeeded",
                "stage": "validation",
                "errors": result.error_count,
                "warnings": result.warning_count,
                "info": result.info_count,
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown stage: {from_stage}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}")


@router.get("/projects/{project_id}/status")
def get_project_status(project_id: str):
    """Return current pipeline status."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")
    return get_status(project_id)


@router.get("/projects/{project_id}/events")
async def project_events(project_id: str):
    """SSE endpoint for pipeline progress events."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    tracker = ProgressTracker(project_id)

    async def generate():
        async for event in tracker.event_stream():
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


@router.get("/projects/{project_id}/screenplay")
def get_screenplay(project_id: str):
    """Return the current screenplay (generated or edited)."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = storage.get_project_dir(project_id)

    # Prefer edited version
    edited = project_dir / "07_screenplay.edited.yaml"
    if edited.exists():
        import yaml
        return yaml.safe_load(edited.read_text(encoding="utf-8"))

    # Fall back to generated
    generated = project_dir / "06_screenplay.generated.yaml"
    if generated.exists():
        import yaml
        return yaml.safe_load(generated.read_text(encoding="utf-8"))

    # Fall back to scenes JSON
    scenes_file = project_dir / "04_scenes.json"
    if scenes_file.exists():
        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
        # Read characters
        char_file = project_dir / "03_characters.json"
        characters = []
        if char_file.exists():
            characters = json.loads(char_file.read_text(encoding="utf-8")).get("characters", [])

        # Get title from project (chapter title)
        project = next((p for p in projects if p.id == project_id), None)
        title = project.title if project else project_id
        source_language = project.source_language if project else "zh"

        return {
            "metadata": {
                "project_id": project_id,
                "title": title,
                "source_language": source_language,
            },
            "characters": characters,
            "acts": [{"id": "act_01", "title": "Act 1", "scenes": scenes}],
        }

    raise HTTPException(status_code=404, detail="Screenplay not generated yet")


@router.put("/projects/{project_id}/screenplay")
def update_screenplay(project_id: str, data: dict):
    """Save edited screenplay."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    import yaml
    project_dir = storage.get_project_dir(project_id)
    edited_file = project_dir / "07_screenplay.edited.yaml"
    edited_file.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )

    return {"status": "saved"}


@router.get("/projects/{project_id}/export")
def export_screenplay(project_id: str):
    """Export screenplay as YAML download."""
    from fastapi.responses import Response
    import yaml

    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    project_dir = storage.get_project_dir(project_id)

    # Prefer edited version
    edited = project_dir / "07_screenplay.edited.yaml"
    generated = project_dir / "06_screenplay.generated.yaml"

    if edited.exists():
        content = edited.read_text(encoding="utf-8")
        filename = f"{project_id}_screenplay_edited.yaml"
    elif generated.exists():
        content = generated.read_text(encoding="utf-8")
        filename = f"{project_id}_screenplay.yaml"
    else:
        # Build from scenes + characters
        scenes_file = project_dir / "04_scenes.json"
        char_file = project_dir / "03_characters.json"
        if not scenes_file.exists():
            raise HTTPException(status_code=404, detail="Screenplay not generated yet")

        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
        characters = json.loads(char_file.read_text(encoding="utf-8")).get("characters", []) if char_file.exists() else []

        # Get title from index
        title = project_id
        for p in storage.list_projects():
            if p.id == project_id:
                title = p.title
                break

        screenplay = {
            "metadata": {"project_id": project_id, "title": title},
            "characters": characters,
            "acts": [{"id": "act_01", "title": "Act 1", "scenes": scenes}],
        }
        content = yaml.dump(screenplay, allow_unicode=True, default_flow_style=False, sort_keys=False)
        filename = f"{project_id}_screenplay.yaml"

    return Response(
        content=content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/validation")
def get_validation_log(project_id: str):
    """Return the validation log."""
    projects = storage.list_projects()
    if not any(p.id == project_id for p in projects):
        raise HTTPException(status_code=404, detail="Project not found")

    log_file = storage.get_project_dir(project_id) / "validation_log.json"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Validation not run yet")

    return json.loads(log_file.read_text(encoding="utf-8"))


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
