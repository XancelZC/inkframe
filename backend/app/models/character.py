"""Character extraction structures.

From PRD Stage 1 — Character Extraction output.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.ids import CharacterId


class Relationship(BaseModel):
    """A relationship between two characters."""

    target_character_id: CharacterId
    type: str
    description: Optional[str] = None


class Character(BaseModel):
    """An extracted character."""

    id: CharacterId
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    relationships: list[Relationship] = Field(default_factory=list)


class CharacterTable(BaseModel):
    """Stage 1 output: extracted characters.

    Persisted to 03_characters.json.
    """

    characters: list[Character] = Field(default_factory=list)
