"""Canonical ID formats.

All IDs are stable strings with type-specific prefixes.
Format rules from PRD section "Canonical Data Contract".
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer


def _validate_id(value: str, pattern: str) -> str:
    if not re.match(pattern, value):
        raise ValueError(f"ID does not match expected pattern {pattern}: {value!r}")
    return value


def _validate_project_id(v: str) -> str:
    return _validate_id(v, r"^prj_[a-z0-9_]+_\d{8,}$")


def _validate_chapter_id(v: str) -> str:
    return _validate_id(v, r"^ch_\d{4}$")


def _validate_paragraph_id(v: str) -> str:
    return _validate_id(v, r"^p_\d{6}$")


def _validate_character_id(v: str) -> str:
    return _validate_id(v, r"^char_[a-z0-9_]+$")


def _validate_scene_id(v: str) -> str:
    return _validate_id(v, r"^sc_\d{4}$")


def _validate_element_id(v: str) -> str:
    return _validate_id(v, r"^el_\d{6}$")


# Annotated types with validation

ProjectId = Annotated[
    str,
    BeforeValidator(_validate_project_id),
    PlainSerializer(lambda v: v, return_type=str),
]

ChapterId = Annotated[
    str,
    BeforeValidator(_validate_chapter_id),
    PlainSerializer(lambda v: v, return_type=str),
]

ParagraphId = Annotated[
    str,
    BeforeValidator(_validate_paragraph_id),
    PlainSerializer(lambda v: v, return_type=str),
]

CharacterId = Annotated[
    str,
    BeforeValidator(_validate_character_id),
    PlainSerializer(lambda v: v, return_type=str),
]

SceneId = Annotated[
    str,
    BeforeValidator(_validate_scene_id),
    PlainSerializer(lambda v: v, return_type=str),
]

ElementId = Annotated[
    str,
    BeforeValidator(_validate_element_id),
    PlainSerializer(lambda v: v, return_type=str),
]


# ID generators


def _slugify(text: str) -> str:
    """Convert text to a lowercase ASCII slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    return text.strip("_") or "untitled"


def make_project_id(title: str) -> ProjectId:
    """Generate a project ID: prj_<slug>_<timestamp>."""
    slug = _slugify(title)[:20]
    ts = str(int(time.time()))
    project_id = f"prj_{slug}_{ts}"
    _validate_project_id(project_id)
    return project_id


def make_chapter_id(index: int) -> ChapterId:
    """Generate a chapter ID: ch_0001 (1-based, index must be >= 1)."""
    if index < 1:
        raise ValueError(f"Chapter index must be >= 1, got {index}")
    chapter_id = f"ch_{index:04d}"
    _validate_chapter_id(chapter_id)
    return chapter_id


def make_paragraph_id(index: int) -> ParagraphId:
    """Generate a paragraph ID: p_000001 (1-based, index must be >= 1)."""
    if index < 1:
        raise ValueError(f"Paragraph index must be >= 1, got {index}")
    paragraph_id = f"p_{index:06d}"
    _validate_paragraph_id(paragraph_id)
    return paragraph_id


def make_character_id(name: str) -> CharacterId:
    """Generate a character ID: char_<slug>."""
    slug = _slugify(name)[:20]
    character_id = f"char_{slug}"
    _validate_character_id(character_id)
    return character_id


def make_scene_id(index: int) -> SceneId:
    """Generate a scene ID: sc_0001 (1-based, index must be >= 1)."""
    if index < 1:
        raise ValueError(f"Scene index must be >= 1, got {index}")
    scene_id = f"sc_{index:04d}"
    _validate_scene_id(scene_id)
    return scene_id


def make_element_id(index: int) -> ElementId:
    """Generate an element ID: el_000001 (1-based, index must be >= 1)."""
    if index < 1:
        raise ValueError(f"Element index must be >= 1, got {index}")
    element_id = f"el_{index:06d}"
    _validate_element_id(element_id)
    return element_id
