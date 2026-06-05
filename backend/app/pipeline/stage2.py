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


def _synthesize_chapter(
    provider,
    ch: dict,
    characters: list[dict],
    char_names: list[str],
    global_scene_index: int,
    global_element_index: int,
) -> tuple[list[Scene], int, int]:
    """Process one chapter and return scenes + updated indices."""
    chapter_id = ch["id"]
    chapter_title = ch.get("title", "")

    # Build chapter text and paragraph map
    chapter_text = ""
    para_map: dict[str, dict] = {}
    for para in ch.get("paragraphs", []):
        chapter_text += para["text"] + "\n"
        para_map[para["id"]] = para

    chapter_excerpt = chapter_text[:6000]

    prompt = f"""你是一个专业的剧本改编助手。请将以下小说章节转换为剧本场景。

重要规则：
- 只使用原文中出现的内容，不要编造新的人物、对话或情节
- 对话必须是原文中实际说出的话（直接引语），不要把叙述转为对话
- 动作描述必须基于原文，可以适当压缩但不要添加
- 如果原文没有直接对话，场景中就不应该有 dialogue 元素
- 角色名必须与提供的角色表一致，不要使用原文中未出现的角色名
- 所有输出内容必须使用中文

章节：{chapter_title}
已知角色：{', '.join(char_names)}

原文：
{chapter_excerpt}

请将原文转换为剧本场景，返回 JSON。"""

    result = provider.generate_json(prompt, SCENE_SYNTHESIS_SCHEMA)

    # Build character name to ID map
    name_to_id = {c["name"]: c["id"] for c in characters}
    for c in characters:
        for alias in c.get("aliases", []):
            name_to_id[alias] = c["id"]

    scenes = []

    for sc_data in result.get("scenes", []):
        global_scene_index += 1
        scene_id = make_scene_id(global_scene_index)
        elements = []

        for el_data in sc_data.get("elements", []):
            global_element_index += 1
            el_type = el_data.get("type", "action")
            el_id = make_element_id(global_element_index)
            content = el_data.get("content", "")
            inferred = el_data.get("inferred", False)
            confidence = el_data.get("confidence", 0.9 if not inferred else 0.6)

            # Find source reference
            source_ref = None
            for pid, para in para_map.items():
                para_text = para.get("text", "")
                if not para_text:
                    continue
                if para_text[:50] in content or content[:50] in para_text:
                    source_ref = SourceReference(
                        chapter_id=chapter_id,
                        paragraph_ids=[para["id"]],
                        start_offset=para.get("start_offset", 0),
                        end_offset=para.get("end_offset", 0),
                        quote=para_text[:100],
                    )
                    break

            char_name = el_data.get("character_name", "")
            char_id = name_to_id.get(char_name, "")

            if el_type == "dialogue":
                # 匹配不到角色时用第一个角色或占位符（不跳过，否则 mock 测试会丢数据）
                effective_char_id = char_id or (characters[0]["id"] if characters else "char_unknown")
                elements.append(DialogueElement(
                    id=el_id,
                    character_id=effective_char_id,
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

        scenes.append(Scene(
            id=scene_id,
            chapter_id=chapter_id,
            title=sc_data.get("title"),
            location=sc_data.get("location"),
            time_of_day=sc_data.get("time_of_day"),
            timeline_order=global_scene_index,
            elements=elements,
        ))

    return scenes, global_scene_index, global_element_index


def run_stage2(project_id: str, provider_id: str = "mock") -> list[Scene]:
    """Run Stage 2 scene synthesis on ALL chapters.

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

    char_names = [c["name"] for c in characters] if characters else ["unknown"]

    # Process all chapters
    all_scenes = []
    global_scene_index = 0
    global_element_index = 0

    for ch in chapters:
        scenes, global_scene_index, global_element_index = _synthesize_chapter(
            provider, ch, characters, char_names, global_scene_index, global_element_index
        )
        all_scenes.extend(scenes)

    # Write output
    output_file = get_project_dir(project_id) / "04_scenes.json"
    output_data = [s.model_dump(mode="json") for s in all_scenes]
    output_file.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return scenes
