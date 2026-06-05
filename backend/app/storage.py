"""File-backed project storage.

MVP uses data/projects/ directory with index.json for project list.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.project import ProjectIndex, ProjectSummary
from app.models.ids import make_project_id


def detect_language(text: str) -> str:
    """Detect language as 'zh' or 'en'. Defaults to 'zh' if uncertain."""
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    total_chars = len(text.strip())
    if total_chars == 0:
        return "zh"
    return "zh" if chinese_chars / total_chars > 0.3 else "en"

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "projects"
INDEX_FILE = DATA_DIR / "index.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_index() -> ProjectIndex:
    _ensure_data_dir()
    if not INDEX_FILE.exists():
        return ProjectIndex()
    data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return ProjectIndex.model_validate(data)


def _write_index(index: ProjectIndex) -> None:
    _ensure_data_dir()
    INDEX_FILE.write_text(
        index.model_dump_json(indent=2),
        encoding="utf-8",
    )


def list_projects() -> list[ProjectSummary]:
    """Return all project summaries from index.json, sorted by newest first."""
    projects = _read_index().projects
    projects.sort(key=lambda p: p.created_at, reverse=True)
    return projects


def delete_project(project_id: str) -> bool:
    """Delete a project and its directory. Returns True if deleted."""
    import shutil

    index = _read_index()
    original_len = len(index.projects)
    index.projects = [p for p in index.projects if p.id != project_id]

    if len(index.projects) == original_len:
        return False

    _write_index(index)

    project_dir = DATA_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)

    return True


def create_project(
    title: str,
    source_language: Optional[str] = None,
    raw_text: Optional[str] = None,
) -> ProjectSummary:
    """Create a new project directory and add it to the index."""
    project_id = make_project_id(title)
    project_dir = DATA_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    if raw_text:
        raw_file = project_dir / "01_raw.txt"
        raw_file.write_text(raw_text, encoding="utf-8")

    now = datetime.now(timezone.utc)
    summary = ProjectSummary(
        id=project_id,
        title=title,
        source_language=source_language,
        created_at=now,
        updated_at=now,
    )

    index = _read_index()
    index.projects.append(summary)
    _write_index(index)

    return summary


def get_project_dir(project_id: str) -> Path:
    """Return the project directory path."""
    return DATA_DIR / project_id


def get_raw_text(project_id: str) -> Optional[str]:
    """Return raw text for a project, or None if not found."""
    raw_file = DATA_DIR / project_id / "01_raw.txt"
    if not raw_file.exists():
        return None
    return raw_file.read_text(encoding="utf-8")
