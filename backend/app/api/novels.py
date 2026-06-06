"""Novel API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response

from app.models.novel import NovelSummary
from app.models.project import ProjectSummary
from app import storage

router = APIRouter(tags=["novels"])


@router.get("/novels")
def list_novels():
    """Return all novels with chapter info."""
    novels = storage.list_novels()
    result = []
    for n in novels:
        chapters = storage.list_projects_by_novel(n.id)
        result.append({
            "id": n.id,
            "title": n.title,
            "language": n.language,
            "created_at": n.created_at,
            "updated_at": n.updated_at,
            "chapter_count": len(chapters),
            "chapters": [
                {"id": c.id, "title": c.title, "created_at": c.created_at}
                for c in chapters
            ],
        })
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

    # 计算统计
    total_chars = 0
    total_chapters = len(chapters)

    return {
        "id": novel.id,
        "title": novel.title,
        "language": novel.language,
        "created_at": novel.created_at,
        "updated_at": novel.updated_at,
        "chapter_count": total_chapters,
        "chapters": [
            {
                "id": c.id,
                "title": c.title,
                "source_language": c.source_language,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in chapters
        ],
    }


@router.put("/novels/{novel_id}")
def update_novel(novel_id: str, title: Optional[str] = None, language: Optional[str] = None):
    """Update novel title or language."""
    if not storage.update_novel(novel_id, title=title, language=language):
        raise HTTPException(status_code=404, detail="小说不存在")
    return {"status": "saved"}


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

    # 收集所有章节的剧本数据
    all_characters = []
    all_acts = []

    for i, ch in enumerate(chapters):
        project_dir = storage.get_project_dir(ch.id)

        # 读取角色
        char_file = project_dir / "03_characters.json"
        if char_file.exists():
            char_data = json.loads(char_file.read_text(encoding="utf-8"))
            for c in char_data.get("characters", []):
                if not any(existing["id"] == c["id"] for existing in all_characters):
                    all_characters.append(c)

        # 读取场景
        scenes_file = project_dir / "04_scenes.json"
        if scenes_file.exists():
            scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
            all_acts.append({
                "id": f"act_{i + 1:02d}",
                "title": ch.title,
                "scenes": scenes,
            })

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

    # 优先使用上传的文件
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
