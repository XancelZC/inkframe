"""Novel API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response

from app.models.novel import NovelSummary
from app.models.project import ProjectSummary
from app.api.models import get_active_provider_id, get_provider_type
from app.pipeline.stage0 import run_stage0
from app.pipeline.stage1 import run_stage1
from app.pipeline.stage2 import run_stage2
from app.pipeline.stage3 import run_stage3
from app import storage

router = APIRouter(tags=["novels"])


TEXT_EXTENSIONS = {".txt", ".md"}
SYSTEM_FILE_NAMES = {".ds_store", "thumbs.db"}


def _is_ignored_import_path(path: str) -> bool:
    parts = Path(path.replace("\\", "/")).parts
    for part in parts:
        lower = part.lower()
        if lower in SYSTEM_FILE_NAMES:
            return True
        if part.startswith((".", "~", "._")):
            return True
    return Path(path).suffix.lower() not in TEXT_EXTENSIONS


def _decode_text(raw_bytes: bytes) -> tuple[Optional[str], Optional[str]]:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw_bytes.decode(encoding), None
        except UnicodeDecodeError:
            continue
    return None, "无法按 UTF-8 或 GB18030 解码"


def _title_from_import_path(path: str) -> str:
    return Path(path.replace("\\", "/")).stem.strip()


def _unique_title(title: str, used_titles: set[str]) -> str:
    base = title.strip() or "未命名章节"
    candidate = base
    index = 2
    while candidate in used_titles:
        candidate = f"{base} ({index})"
        index += 1
    used_titles.add(candidate)
    return candidate


def _natural_sort_key(path: str) -> list[object]:
    import re

    normalized = path.replace("\\", "/").lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", normalized)]


def _run_all_stages(project_id: str) -> Optional[str]:
    try:
        active_pid = get_active_provider_id()
        provider_id = get_provider_type(active_pid)
        run_stage0(project_id)
        run_stage1(project_id, provider_id=provider_id)
        run_stage2(project_id, provider_id=provider_id)
        run_stage3(project_id)
        return None
    except Exception as exc:
        return str(exc)


async def _import_chapter_files(
    novel_id: str,
    files: list[UploadFile],
    relative_paths: Optional[list[str]] = None,
    source_language: Optional[str] = None,
    auto_process: bool = False,
) -> dict:
    existing_titles = {p.title for p in storage.list_projects_by_novel(novel_id)}
    file_entries = []

    for index, file in enumerate(files):
        import_path = (
            relative_paths[index]
            if relative_paths and index < len(relative_paths) and relative_paths[index]
            else file.filename or f"chapter-{index + 1}.txt"
        )
        file_entries.append((import_path, file))

    created = []
    failed = []
    ignored = []

    for import_path, file in sorted(file_entries, key=lambda item: _natural_sort_key(item[0])):
        if _is_ignored_import_path(import_path):
            ignored.append({"path": import_path})
            continue

        raw_bytes = await file.read()
        content, decode_error = _decode_text(raw_bytes)
        if decode_error:
            failed.append({"path": import_path, "reason": decode_error})
            continue

        content = (content or "").strip()
        if not content:
            failed.append({"path": import_path, "reason": "文件内容为空"})
            continue

        lang = source_language or storage.detect_language(content)
        title = _unique_title(_title_from_import_path(import_path), existing_titles)
        summary = storage.create_project(
            title=title,
            source_language=lang,
            raw_text=content,
            novel_id=novel_id,
        )

        item = {
            "id": summary.id,
            "title": summary.title,
            "source_language": summary.source_language,
            "path": import_path,
            "process_error": None,
        }
        if auto_process:
            item["process_error"] = _run_all_stages(summary.id)
        created.append(item)

    return {
        "created_chapters": created,
        "failed_files": failed,
        "ignored_files": ignored,
        "created_count": len(created),
        "failed_count": len(failed),
        "ignored_count": len(ignored),
    }


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


@router.post("/novels/import", status_code=201)
async def import_novel(
    title: str = Form(...),
    language: str = Form("zh"),
    auto_process: bool = Form(False),
    files: list[UploadFile] = File(...),
    relative_paths: Optional[list[str]] = Form(None),
):
    """Create a novel and import each text file as one chapter."""
    if not title.strip():
        raise HTTPException(status_code=400, detail="小说标题不能为空")
    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个文本文件")

    novel = storage.create_novel(title=title.strip(), language=language)
    result = await _import_chapter_files(
        novel_id=novel.id,
        files=files,
        relative_paths=relative_paths,
        source_language=None if language == "auto" else language,
        auto_process=auto_process,
    )

    return {"novel": novel.model_dump(mode="json"), **result}


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
        content, decode_error = _decode_text(raw_bytes)
        if decode_error:
            raise HTTPException(status_code=400, detail=decode_error)
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


@router.post("/novels/{novel_id}/chapters/import", status_code=201)
async def import_chapters(
    novel_id: str,
    auto_process: bool = Form(False),
    files: list[UploadFile] = File(...),
    relative_paths: Optional[list[str]] = Form(None),
):
    """Import multiple text files into an existing novel as chapters."""
    novel = storage.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个文本文件")

    result = await _import_chapter_files(
        novel_id=novel_id,
        files=files,
        relative_paths=relative_paths,
        source_language=None,
        auto_process=auto_process,
    )

    return {"novel_id": novel_id, **result}
