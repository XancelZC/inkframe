"""Stage 0: Text Preprocessing.

Split raw text into chapters and paragraphs, detect language,
assign stable IDs. Pure rules, no LLM calls.

Configurable thresholds:
- max_chapter_chars: 60000 (split chapters exceeding this)
- chunk_chars: 4000 (chunk size for long chapters)
- chunk_overlap_paragraphs: 1 (overlap for context continuity)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from app.models.ids import make_chapter_id, make_paragraph_id
from app.models.text import Chapter, Paragraph, PreprocessedText
from app.storage import detect_language, get_project_dir, get_raw_text


DEFAULT_MAX_CHAPTER_CHARS = 60000
DEFAULT_CHUNK_CHARS = 4000
DEFAULT_CHUNK_OVERLAP = 1


def _split_into_chapters(text: str) -> list[tuple[Optional[str], str]]:
    """Split text into chapters. Returns list of (title, content) tuples.

    Heuristics:
    - Lines starting with 'Chapter', 'CHAPTER', '第...章', '第...回' etc.
    - If no chapter markers found, treat entire text as one chapter.
    """
    # Pattern matches common chapter markers
    pattern = re.compile(
        r"^(?:"
        r"(?:Chapter|CHAPTER)\s+\d+.*"  # Chapter 1, Chapter II
        r"|第[一二三四五六七八九十百千\d]+[章回节卷].*"  # 第一章, 第一回
        r"|(?:Part|PART)\s+\d+.*"  # Part 1
        r")$",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(text))

    if not matches:
        return [(None, text)]

    chapters = []
    for i, match in enumerate(matches):
        title = match.group().strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            chapters.append((title, content))

    # If first match doesn't start at 0, add preamble as first chapter
    if matches and matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            chapters.insert(0, (None, preamble))

    return chapters if chapters else [(None, text)]


def _split_into_paragraphs(text: str) -> list[tuple[str, int, int]]:
    """Split text into paragraphs with offsets. Returns (text, start, end)."""
    paragraphs = []
    current_pos = 0

    for match in re.finditer(r"\n\s*\n", text):
        para_text = text[current_pos : match.start()].strip()
        if para_text:
            paragraphs.append((para_text, current_pos, match.start()))
        current_pos = match.end()

    # Last paragraph
    remaining = text[current_pos:].strip()
    if remaining:
        paragraphs.append((remaining, current_pos, len(text)))

    # If no paragraphs found, treat entire text as one paragraph
    if not paragraphs and text.strip():
        paragraphs.append((text.strip(), 0, len(text)))

    return paragraphs


def run_stage0(
    project_id: str,
    max_chapter_chars: int = DEFAULT_MAX_CHAPTER_CHARS,
) -> PreprocessedText:
    """Run Stage 0 preprocessing on a project's raw text.

    Reads 01_raw.txt, writes 02_preprocessed.json.
    """
    raw_text = get_raw_text(project_id)
    if raw_text is None:
        raise FileNotFoundError(f"No raw text found for project {project_id}")

    detected_lang = detect_language(raw_text)
    chapter_splits = _split_into_chapters(raw_text)

    chapters = []
    global_para_index = 1

    for ch_index, (title, ch_content) in enumerate(chapter_splits, start=1):
        chapter_id = make_chapter_id(ch_index)

        # If chapter is too long, chunk it
        if len(ch_content) > max_chapter_chars:
            # Split into paragraphs first, then group into chunks
            all_paragraphs = _split_into_paragraphs(ch_content)
            chunks: list[list[tuple[str, int, int]]] = []
            current_chunk: list[tuple[str, int, int]] = []
            current_size = 0

            for para_text, start, end in all_paragraphs:
                para_size = len(para_text)
                if current_size + para_size > DEFAULT_CHUNK_CHARS and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_size = 0
                current_chunk.append((para_text, start, end))
                current_size += para_size

            if current_chunk:
                chunks.append(current_chunk)

            # Create one chapter per chunk
            for chunk_index, chunk in enumerate(chunks):
                chunk_ch_id = make_chapter_id(ch_index) if chunk_index == 0 else make_chapter_id(ch_index)
                # For multiple chunks of same chapter, use same chapter_id
                paragraphs = []
                for para_text, start, end in chunk:
                    paragraphs.append(
                        Paragraph(
                            id=make_paragraph_id(global_para_index),
                            text=para_text,
                            start_offset=start,
                            end_offset=end,
                        )
                    )
                    global_para_index += 1

                chunk_title = title
                if chunk_index > 0:
                    chunk_title = f"{title} (part {chunk_index + 1})" if title else f"Part {chunk_index + 1}"

                chapters.append(
                    Chapter(
                        id=chunk_ch_id,
                        title=chunk_title,
                        paragraphs=paragraphs,
                    )
                )
        else:
            paras_data = _split_into_paragraphs(ch_content)
            paragraphs = []
            for para_text, start, end in paras_data:
                paragraphs.append(
                    Paragraph(
                        id=make_paragraph_id(global_para_index),
                        text=para_text,
                        start_offset=start,
                        end_offset=end,
                    )
                )
                global_para_index += 1

            chapters.append(
                Chapter(
                    id=chapter_id,
                    title=title,
                    paragraphs=paragraphs,
                )
            )

    result = PreprocessedText(chapters=chapters, detected_language=detected_lang)

    # Write output
    output_dir = get_project_dir(project_id)
    output_file = output_dir / "02_preprocessed.json"
    output_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    return result
