"""Stage 1: Character Extraction.

Extract characters, aliases, descriptions, and relationships from
preprocessed text using the LLM provider.

Uses jieba for Chinese candidate names, spaCy for English.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.models.character import Character, CharacterTable, Relationship
from app.models.ids import make_character_id
from app.storage import get_project_dir


def _extract_candidate_names(text: str, language: str) -> list[str]:
    """Extract candidate character names using NLP heuristics."""
    candidates = set()

    if language == "zh":
        try:
            import jieba
            import jieba.posseg as pseg

            words = pseg.cut(text)
            for word, flag in words:
                if flag in ("nr", "nrt") and len(word) >= 2:
                    candidates.add(word)
        except ImportError:
            # Fallback: regex for Chinese names (2-3 characters)
            for match in re.finditer(r"[一-鿿]{2,3}", text):
                candidates.add(match.group())
    else:
        # English: capitalized words that appear multiple times
        words = re.findall(r"\b[A-Z][a-z]+\b", text)
        word_counts: dict[str, int] = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1
        for word, count in word_counts.items():
            if count >= 2 and word not in {"The", "This", "That", "Chapter", "Part"}:
                candidates.add(word)

    return sorted(candidates)[:20]  # Limit to top 20


CHARACTER_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target_name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["name"],
            },
        }
    },
    "required": ["characters"],
}


def run_stage1(project_id: str, provider_id: str = "mock") -> CharacterTable:
    """Run Stage 1 character extraction.

    Reads 02_preprocessed.json, writes 03_characters.json.
    """
    from app.llm.registry import get_provider

    provider = get_provider(provider_id)
    if provider is None:
        raise ValueError(f"Unknown provider: {provider_id}")

    # Read preprocessed text
    preprocessed_file = get_project_dir(project_id) / "02_preprocessed.json"
    if not preprocessed_file.exists():
        raise FileNotFoundError("Stage 0 must be run before Stage 1")

    preprocessed = json.loads(preprocessed_file.read_text(encoding="utf-8"))
    language = preprocessed.get("detected_language", "zh")

    # Combine all chapter text for candidate extraction
    all_text = ""
    for chapter in preprocessed.get("chapters", []):
        for para in chapter.get("paragraphs", []):
            all_text += para.get("text", "") + "\n"

    # Extract candidate names
    candidates = _extract_candidate_names(all_text, language)

    # Build prompt
    prompt = f"""Extract all characters from this novel text.
Candidate names found: {', '.join(candidates) if candidates else 'none detected'}

For each character, provide:
- name: the character's primary name
- aliases: other names or titles used for this character
- description: a brief description of who they are
- relationships: connections to other characters

Return JSON matching this schema: {json.dumps(CHARACTER_EXTRACTION_SCHEMA)}"""

    # Call LLM
    result = provider.generate_json(prompt, CHARACTER_EXTRACTION_SCHEMA)

    # Convert to Character objects
    characters = []
    name_to_id: dict[str, str] = {}

    for i, char_data in enumerate(result.get("characters", []), start=1):
        name = char_data.get("name", f"Character_{i}")
        char_id = make_character_id(name)
        name_to_id[name] = char_id

        characters.append(
            Character(
                id=char_id,
                name=name,
                aliases=char_data.get("aliases", []),
                description=char_data.get("description"),
            )
        )

    # Build relationships after all characters have IDs
    for i, char_data in enumerate(result.get("characters", [])):
        relationships = []
        for rel in char_data.get("relationships", []):
            target_name = rel.get("target_name", "")
            if not target_name:
                continue

            # Find target character ID
            target_id = name_to_id.get(target_name)
            if not target_id:
                # Try fuzzy match
                for other in characters:
                    if other.name == target_name or target_name in other.aliases:
                        target_id = other.id
                        break
            if not target_id and len(characters) > 1:
                # Default to first other character
                target_id = next(c.id for c in characters if c.id != characters[i].id)

            if target_id:
                relationships.append(
                    Relationship(
                        target_character_id=target_id,
                        type=rel.get("type", "unknown"),
                        description=rel.get("description"),
                    )
                )

        characters[i].relationships = relationships

    table = CharacterTable(characters=characters)

    # Write output
    output_file = get_project_dir(project_id) / "03_characters.json"
    output_file.write_text(table.model_dump_json(indent=2), encoding="utf-8")

    return table
