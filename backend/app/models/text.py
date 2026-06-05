"""Preprocessed text structures.

From PRD Stage 0 — Text Preprocessing output.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.ids import ChapterId, ParagraphId


class Paragraph(BaseModel):
    """A single paragraph from the source text."""

    id: ParagraphId
    text: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_offsets(self) -> "Paragraph":
        if self.end_offset < self.start_offset:
            raise ValueError(
                f"end_offset ({self.end_offset}) must be >= start_offset ({self.start_offset})"
            )
        return self


class Chapter(BaseModel):
    """A chapter from the source text."""

    id: ChapterId
    title: Optional[str] = None
    paragraphs: list[Paragraph] = Field(default_factory=list)


class PreprocessedText(BaseModel):
    """Stage 0 output: structured text with chapters and paragraphs.

    Persisted to 02_preprocessed.json.
    """

    chapters: list[Chapter] = Field(default_factory=list)
    detected_language: str = Field(pattern=r"^(zh|en)$")
