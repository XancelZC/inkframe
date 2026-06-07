"""Novel API routes."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app import storage
from app.models.novel import NovelSummary
from app.models.project import ProjectSummary

router = APIRouter(tags=["novels"])


@router.get("/novels")
def list_novels():
    """Return all novels with chapter info."""
    novels = storage.list_novels()
    result = []
    for novel in novels:
        chapters = storage.list_projects_by_novel(novel.id)
        result.append(
            {
                "id": novel.id,
                "title": novel.title,
                "language": novel.language,
                "pinned": novel.pinned,
                "created_at": novel.created_at,
                "updated_at": novel.updated_at,
                "chapter_count": len(chapters),
                "chapters": [
                    {"id": chapter.id, "title": chapter.title, "created_at": chapter.created_at}
                    for chapter in chapters
                ],
            }
        )
    return result


@router.post("/novels", response_model=NovelSummary, status_code=201)
def create_novel(title: str, language: str = "zh"):
    """Create a new novel."""
    if not title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")
    return storage.create_novel(title=title.strip(), language=language)


@router.get("/novels/{novel_id}")
def get_novel(novel_id: str):
    """Return novel detail with chapter list."""
    novel = storage.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    chapters = storage.list_projects_by_novel(novel_id)

    return {
        "id": novel.id,
        "title": novel.title,
        "language": novel.language,
        "pinned": novel.pinned,
        "created_at": novel.created_at,
        "updated_at": novel.updated_at,
        "chapter_count": len(chapters),
        "chapters": [
            {
                "id": chapter.id,
                "title": chapter.title,
                "source_language": chapter.source_language,
                "created_at": chapter.created_at,
                "updated_at": chapter.updated_at,
            }
            for chapter in chapters
        ],
    }


@router.put("/novels/{novel_id}")
def update_novel(novel_id: str, title: Optional[str] = None, language: Optional[str] = None):
    """Update novel title or language."""
    if not storage.update_novel(novel_id, title=title, language=language):
        raise HTTPException(status_code=404, detail="小说不存在")
    return {"status": "saved"}


@router.put("/novels/{novel_id}/pin")
def set_novel_pinned(novel_id: str, pinned: bool):
    """Pin or unpin a novel in the project list."""
    if not storage.set_novel_pinned(novel_id, pinned=pinned):
        raise HTTPException(status_code=404, detail="小说不存在")
    return {"status": "saved", "pinned": pinned}


@router.delete("/novels/{novel_id}")
def delete_novel(novel_id: str):
    """Delete a novel and all its chapters."""
    if not storage.delete_novel(novel_id):
        raise HTTPException(status_code=404, detail="小说不存在")
    return {"status": "deleted"}


@router.get("/novels/{novel_id}/export")
def export_novel_yaml(novel_id: str):
    """Export all chapters of a novel as a single YAML file."""
    import yaml

    novel = storage.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    chapters = storage.list_projects_by_novel(novel_id)
    if not chapters:
        raise HTTPException(status_code=404, detail="该小说没有章节")

    all_characters = []
    all_acts = []

    for index, chapter in enumerate(chapters):
        project_dir = storage.get_project_dir(chapter.id)

        char_file = project_dir / "03_characters.json"
        if char_file.exists():
            char_data = json.loads(char_file.read_text(encoding="utf-8"))
            for character in char_data.get("characters", []):
                if not any(existing["id"] == character["id"] for existing in all_characters):
                    all_characters.append(character)

        scenes_file = project_dir / "04_scenes.json"
        if scenes_file.exists():
            scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
            all_acts.append(
                {
                    "id": f"act_{index + 1:02d}",
                    "title": chapter.title,
                    "scenes": scenes,
                }
            )

    screenplay = {
        "metadata": {
            "novel_id": novel.id,
            "title": novel.title,
            "language": novel.language,
            "chapter_count": len(chapters),
        },
        "characters": all_characters,
        "acts": all_acts,
    }

    content = yaml.dump(screenplay, allow_unicode=True, default_flow_style=False, sort_keys=False)
    filename = f"{novel.title}_screenplay.yaml"

    return Response(
        content=content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/novels/{novel_id}/chapters", response_model=ProjectSummary, status_code=201)
async def create_chapter(
    novel_id: str,
    title: str = Form(...),
    text: Optional[str] = Form(None),
    source_language: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Create a new chapter in a novel. Supports text paste or file upload."""
    novel = storage.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    if not title.strip():
        raise HTTPException(status_code=400, detail="章节标题不能为空")

    content = None
    if file is not None:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
    elif text is not None:
        content = text

    lang = source_language or novel.language
    if content and not source_language:
        lang = storage.detect_language(content.strip())

    summary = storage.create_project(
        title=title.strip(),
        source_language=lang,
        raw_text=content.strip() if content else None,
        novel_id=novel_id,
    )
    return summary
