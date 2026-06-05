"""Screenplay structures.

From PRD Stage 2 — Scene Synthesis output, and the canonical YAML schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

from app.models.character import Character
from app.models.ids import CharacterId, ChapterId, ElementId, ParagraphId, ProjectId, SceneId


class ElementType(str, Enum):
    """Scene element types."""

    DIALOGUE = "dialogue"
    ACTION = "action"
    TRANSITION = "transition"
    NARRATION = "narration"


class SourceReference(BaseModel):
    """Traceable reference back to the original novel text.

    Every element that comes from or is derived from source text
    must include this reference.
    """

    chapter_id: ChapterId
    paragraph_ids: list[ParagraphId] = Field(min_length=1)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    quote: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def _check_offsets(self) -> "SourceReference":
        if self.end_offset < self.start_offset:
            raise ValueError(
                f"end_offset ({self.end_offset}) must be >= start_offset ({self.start_offset})"
            )
        return self


class _ElementBase(BaseModel):
    """Common fields for all scene elements."""

    id: ElementId
    inferred: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_reference: Optional[SourceReference] = None


class DialogueElement(_ElementBase):
    """A line of dialogue spoken by a character."""

    type: Literal[ElementType.DIALOGUE] = ElementType.DIALOGUE
    character_id: CharacterId
    content: str
    parenthetical: Optional[str] = None


class ActionElement(_ElementBase):
    """A stage direction or action description."""

    type: Literal[ElementType.ACTION] = ElementType.ACTION
    content: str
    character_ids: list[CharacterId] = Field(default_factory=list)


class TransitionElement(_ElementBase):
    """A scene transition (e.g., CUT TO, FADE OUT)."""

    type: Literal[ElementType.TRANSITION] = ElementType.TRANSITION
    content: str


class NarrationElement(_ElementBase):
    """Voice-over or narration that cannot be visually represented."""

    type: Literal[ElementType.NARRATION] = ElementType.NARRATION
    content: str


SceneElement = Annotated[
    Union[DialogueElement, ActionElement, TransitionElement, NarrationElement],
    Field(discriminator="type"),
]


class Scene(BaseModel):
    """A single scene within an act."""

    id: SceneId
    chapter_id: ChapterId
    title: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    timeline_order: int = Field(default=0, ge=0)
    elements: list[SceneElement] = Field(default_factory=list)


class Act(BaseModel):
    """A dramatic act containing scenes."""

    id: str
    title: Optional[str] = None
    scenes: list[Scene] = Field(default_factory=list)


class ScreenplayMetadata(BaseModel):
    """Metadata for a screenplay."""

    project_id: ProjectId
    title: str
    source_language: str = Field(pattern=r"^(zh|en)$")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model: dict = Field(default_factory=lambda: {"provider": "mock", "name": "mock-screenplay"})


class Screenplay(BaseModel):
    """Complete screenplay structure.

    Persisted to 06_screenplay.generated.yaml or 07_screenplay.edited.yaml.
    """

    metadata: ScreenplayMetadata
    characters: list[Character] = Field(default_factory=list)
    acts: list[Act] = Field(default_factory=list)
