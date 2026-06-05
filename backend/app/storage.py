"""File-backed project storage.

MVP uses data/projects/ directory with index.json for project list.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.project import ProjectIndex, ProjectSummary
from app.models.ids import make_project_id

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
    """Return all project summaries from index.json."""
    return _read_index().projects


def create_project(title: str, source_language: Optional[str] = None) -> ProjectSummary:
    """Create a new project directory and add it to the index."""
    project_id = make_project_id(title)
    project_dir = DATA_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

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
