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


# 常见非人名的两字词，用于过滤 fallback 正则的误匹配
_ZH_STOPWORDS = {
    "他们", "她们", "我们", "你们", "自己", "什么", "怎么", "这里", "那里",
    "一个", "这个", "那个", "可以", "不是", "没有", "知道", "已经", "因为",
    "所以", "但是", "如果", "只是", "还是", "就是", "不过", "而且", "虽然",
    "然后", "现在", "时候", "出来", "起来", "开始", "觉得", "发现", "可能",
    "应该", "这样", "那样", "一些", "一下", "一切", "为了", "之间", "以后",
    "以前", "这些", "那些", "许多", "大家", "别人", "不要", "不会", "不能",
}


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
            # Fallback: regex for Chinese names (2-3 characters), filter stopwords
            for match in re.finditer(r"[一-鿿]{2,3}", text):
                word = match.group()
                if word not in _ZH_STOPWORDS:
                    candidates.add(word)
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


def run_stage1(project_id: str, provider_id: str = "mock", tracker=None) -> CharacterTable:
    """Run Stage 1 character extraction.

    Reads 02_preprocessed.json, writes 03_characters.json.
    """
    from app.llm.registry import get_provider
    from app.models.status import PipelineStage
    if tracker:
        tracker.start_stage(PipelineStage.CHARACTER_EXTRACTION, "开始角色提取")

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

    # Build prompt — 必须包含原文，否则 LLM 会编造角色
    text_excerpt = all_text[:8000]  # 限制长度避免超 token

    prompt = f"""你是一个专业的剧本分析助手。请从以下小说原文中提取所有出现过的角色。

重要规则：
- 只提取原文中明确出现的人物，不要编造
- 如果原文中没有明确的人物，返回空数组
- 角色名必须与原文一致

候选人物名（仅供参考，可能不准确）：{', '.join(candidates) if candidates else '无'}

原文：
{text_excerpt}

请提取角色信息，返回 JSON。"""

    # Call LLM
    if tracker:
        tracker.update_progress(PipelineStage.CHARACTER_EXTRACTION, 0.3, message="正在调用 LLM 提取角色")
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

            # Find target character ID — 只做精确匹配，不瞎连
            target_id = name_to_id.get(target_name)
            if not target_id:
                # 尝试模糊匹配：包含关系
                for other in characters:
                    if other.name == target_name or target_name in other.aliases:
                        target_id = other.id
                        break

            # 如果还是匹配不到，跳过这条关系（不默认连到其他角色）
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

    if tracker:
        tracker.complete_stage(PipelineStage.CHARACTER_EXTRACTION, f"角色提取完成，共 {len(characters)} 个角色", final=False)

    return table
