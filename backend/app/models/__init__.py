"""InkFrame data contract models.

All ID formats, source_reference structure, confidence/inferred rules,
element types, status enum, error format, and SSE event structure
are defined here as the single source of truth.
"""

from app.models.ids import (
    ProjectId,
    ChapterId,
    ParagraphId,
    CharacterId,
    SceneId,
    ElementId,
    make_project_id,
    make_chapter_id,
    make_paragraph_id,
    make_character_id,
    make_scene_id,
    make_element_id,
)
from app.models.project import ProjectSummary, ProjectIndex, ProjectDetail
from app.models.text import Chapter, Paragraph, PreprocessedText
from app.models.character import Character, Relationship, CharacterTable
from app.models.screenplay import (
    Screenplay,
    ScreenplayMetadata,
    Act,
    Scene,
    SceneElement,
    DialogueElement,
    ActionElement,
    TransitionElement,
    NarrationElement,
    SourceReference,
    ElementType,
)
from app.models.status import PipelineStatus, PipelineStage, StatusEnum
from app.models.errors import ErrorResponse, ErrorCode, ErrorDetail
from app.models.events import SSEEvent
from app.models.validation import ValidationLogEntry, ValidationLog, ValidationSeverity

__all__ = [
    # ID types
    "ProjectId",
    "ChapterId",
    "ParagraphId",
    "CharacterId",
    "SceneId",
    "ElementId",
    # ID generators
    "make_project_id",
    "make_chapter_id",
    "make_paragraph_id",
    "make_character_id",
    "make_scene_id",
    "make_element_id",
    # Project
    "ProjectSummary",
    "ProjectIndex",
    "ProjectDetail",
    # Text
    "Chapter",
    "Paragraph",
    "PreprocessedText",
    # Character
    "Character",
    "Relationship",
    "CharacterTable",
    # Screenplay
    "Screenplay",
    "ScreenplayMetadata",
    "Act",
    "Scene",
    "SceneElement",
    "DialogueElement",
    "ActionElement",
    "TransitionElement",
    "NarrationElement",
    "SourceReference",
    "ElementType",
    # Status
    "PipelineStatus",
    "PipelineStage",
    "StatusEnum",
    # Errors
    "ErrorResponse",
    "ErrorCode",
    "ErrorDetail",
    # Events
    "SSEEvent",
    # Validation
    "ValidationLogEntry",
    "ValidationLog",
    "ValidationSeverity",
]
