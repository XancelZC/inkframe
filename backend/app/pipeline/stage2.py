"""Stage 2: Scene Synthesis.

Generate scenes, dialogue, action, narration, and transitions
from one chapter using the LLM provider.

Mock provider returns deterministic scene data.
"""

from __future__ import annotations

import json
from typing import Any

from app.models.ids import make_element_id, make_scene_id
from app.models.screenplay import (
    ActionElement,
    DialogueElement,
    NarrationElement,
    Scene,
    SourceReference,
    TransitionElement,
)
from app.storage import get_project_dir


SCENE_SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "location": {"type": "string"},
                    "time_of_day": {"type": "string"},
                    "elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["dialogue", "action", "transition", "narration"]},
                                "content": {"type": "string"},
                                "character_name": {"type": "string"},
                                "parenthetical": {"type": "string"},
                                "inferred": {"type": "boolean"},
                                "confidence": {"type": "number"},
                            },
                            "required": ["type", "content"],
                        },
                    },
                },
                "required": ["title", "location", "elements"],
            },
        }
    },
    "required": ["scenes"],
}


def run_stage2(project_id: str, provider_id: str = "mock", chapter_index: int = 0) -> list[Scene]:
    """Run Stage 2 scene synthesis on one chapter.

    Reads 02_preprocessed.json + 03_characters.json, writes 04_scenes.json.
    """
    from app.llm.registry import get_provider

    provider = get_provider(provider_id)
    if provider is None:
        raise ValueError(f"Unknown provider: {provider_id}")

    # Read preprocessed text
    preprocessed_file = get_project_dir(project_id) / "02_preprocessed.json"
    if not preprocessed_file.exists():
        raise FileNotFoundError("Stage 0 must be run before Stage 2")

    preprocessed = json.loads(preprocessed_file.read_text(encoding="utf-8"))
    chapters = preprocessed.get("chapters", [])
    if not chapters:
        raise ValueError("No chapters found in preprocessed text")

    # Read characters
    characters_file = get_project_dir(project_id) / "03_characters.json"
    characters = []
    if characters_file.exists():
        char_data = json.loads(characters_file.read_text(encoding="utf-8"))
        characters = char_data.get("characters", [])

    # Select chapter
    ch = chapters[chapter_index % len(chapters)]
    chapter_id = ch["id"]
    chapter_title = ch.get("title", "")

    # Build chapter text
    chapter_text = ""
    para_map: dict[str, dict] = {}
    for para in ch.get("paragraphs", []):
        chapter_text += para["text"] + "\n"
        para_map[para["text"][:20]] = para

    # Build prompt
    char_names = [c["name"] for c in characters] if characters else ["unknown"]
    prompt = f"""Convert this novel chapter into screenplay scenes.

Chapter: {chapter_title}
Characters: {', '.join(char_names)}

Text:
{chapter_text[:3000]}

Generate scenes with dialogue, action, transitions, and narration.
Mark inferred content with inferred=true.
Return JSON matching this schema: {json.dumps(SCENE_SYNTHESIS_SCHEMA)}"""

    # Call LLM
    result = provider.generate_json(prompt, SCENE_SYNTHESIS_SCHEMA)

    # Build character name to ID map
    name_to_id = {c["name"]: c["id"] for c in characters}
    for c in characters:
        for alias in c.get("aliases", []):
            name_to_id[alias] = c["id"]

    # Convert to Scene objects
    scenes = []
    global_element_index = 1

    for sc_index, sc_data in enumerate(result.get("scenes", []), start=1):
        scene_id = make_scene_id(sc_index)
        elements = []

        for el_data in sc_data.get("elements", []):
            el_type = el_data.get("type", "action")
            el_id = make_element_id(global_element_index)
            content = el_data.get("content", "")
            inferred = el_data.get("inferred", False)
            confidence = el_data.get("confidence", 0.9 if not inferred else 0.6)

            # Find source reference from paragraph map
            source_ref = None
            for key, para in para_map.items():
                if key in content or content[:15] in para.get("text", ""):
                    source_ref = SourceReference(
                        chapter_id=chapter_id,
                        paragraph_ids=[para["id"]],
                        start_offset=para.get("start_offset", 0),
                        end_offset=para.get("end_offset", 0),
                        quote=para["text"][:100],
                    )
                    break

            char_name = el_data.get("character_name", "")
            char_id = name_to_id.get(char_name, "")

            if el_type == "dialogue":
                elements.append(DialogueElement(
                    id=el_id,
                    character_id=char_id or (characters[0]["id"] if characters else "char_unknown"),
                    content=content,
                    parenthetical=el_data.get("parenthetical"),
                    inferred=inferred,
                    confidence=confidence,
                    source_reference=source_ref,
                ))
            elif el_type == "transition":
                elements.append(TransitionElement(
                    id=el_id,
                    content=content,
                    inferred=inferred,
                    confidence=confidence,
                    source_reference=source_ref,
                ))
            elif el_type == "narration":
                elements.append(NarrationElement(
                    id=el_id,
                    content=content,
                    inferred=inferred,
                    confidence=confidence,
                    source_reference=source_ref,
                ))
            else:
                char_ids = [char_id] if char_id else []
                elements.append(ActionElement(
                    id=el_id,
                    content=content,
                    character_ids=char_ids,
                    inferred=inferred,
                    confidence=confidence,
                    source_reference=source_ref,
                ))

            global_element_index += 1

        scenes.append(Scene(
            id=scene_id,
            chapter_id=chapter_id,
            title=sc_data.get("title"),
            location=sc_data.get("location"),
            time_of_day=sc_data.get("time_of_day"),
            timeline_order=sc_index,
            elements=elements,
        ))

    # Write output
    output_file = get_project_dir(project_id) / "04_scenes.json"
    output_data = [s.model_dump(mode="json") for s in scenes]
    output_file.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return scenes
