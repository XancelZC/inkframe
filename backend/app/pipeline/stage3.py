"""Stage 3: Consistency Validation.

Check scene synthesis output for issues: character name consistency,
scene continuity, missing references, low confidence, source integrity.
"""

from __future__ import annotations

import json

from app.models.validation import ValidationLog, ValidationLogEntry, ValidationSeverity
from app.storage import get_project_dir


def run_stage3(project_id: str, tracker=None) -> ValidationLog:
    """Run Stage 3 consistency validation.

    Reads 03_characters.json + 04_scenes.json, writes validation_log.json.
    """
    from app.models.status import PipelineStage
    if tracker:
        tracker.start_stage(PipelineStage.VALIDATION, "开始一致性校验")

    project_dir = get_project_dir(project_id)

    # Read characters
    char_file = project_dir / "03_characters.json"
    if not char_file.exists():
        raise FileNotFoundError("Stage 1 must be run before Stage 3")

    char_data = json.loads(char_file.read_text(encoding="utf-8"))
    characters = char_data.get("characters", [])
    valid_char_ids = {c["id"] for c in characters}

    # Read scenes
    scenes_file = project_dir / "04_scenes.json"
    if not scenes_file.exists():
        raise FileNotFoundError("Stage 2 must be run before Stage 3")

    scenes = json.loads(scenes_file.read_text(encoding="utf-8"))

    entries: list[ValidationLogEntry] = []

    # Check scene order (monotonically increasing, not strictly sequential)
    scene_ids = [s["id"] for s in scenes]
    for i in range(1, len(scene_ids)):
        if scene_ids[i] <= scene_ids[i - 1]:
            entries.append(ValidationLogEntry(
                severity=ValidationSeverity.WARNING,
                code="scene_order",
                message=f"场景 {scene_ids[i]} 不在 {scene_ids[i-1]} 之后",
                scene_id=scene_ids[i],
            ))

    # Check each scene's elements
    for scene in scenes:
        scene_id = scene["id"]
        elements = scene.get("elements", [])

        if not elements:
            entries.append(ValidationLogEntry(
                severity=ValidationSeverity.WARNING,
                code="empty_scene",
                message=f"场景 {scene_id} 没有任何剧本元素，请补充动作、对话、旁白或转场。",
                scene_id=scene_id,
            ))

        for el in elements:
            el_id = el.get("id", "")
            el_type = el.get("type", "")

            # Check character references
            if el_type == "dialogue":
                char_id = el.get("character_id", "")
                if not char_id:
                    entries.append(ValidationLogEntry(
                        severity=ValidationSeverity.WARNING,
                        code="missing_character",
                        message=f"对话元素 {el_id} 缺少角色引用",
                        scene_id=scene_id,
                        element_id=el_id,
                    ))
                elif char_id not in valid_char_ids:
                    entries.append(ValidationLogEntry(
                        severity=ValidationSeverity.ERROR,
                        code="invalid_character_ref",
                        message=f"元素 {el_id} 引用了不存在的角色 {char_id}",
                        scene_id=scene_id,
                        element_id=el_id,
                    ))

            # Check low confidence
            confidence = el.get("confidence", 1.0)
            if confidence < 0.7:
                entries.append(ValidationLogEntry(
                    severity=ValidationSeverity.WARNING,
                    code="low_confidence",
                    message=f"元素 {el_id} 的置信度较低（{confidence:.2f}），建议对照原文检查或手动修改。",
                    scene_id=scene_id,
                    element_id=el_id,
                ))

            # Check inferred without source reference
            if el.get("inferred") and not el.get("source_reference"):
                entries.append(ValidationLogEntry(
                    severity=ValidationSeverity.INFO,
                    code="inferred_no_source",
                    message=f"推断生成的元素 {el_id} 缺少原文引用，建议补充来源或确认该内容是否需要保留。",
                    scene_id=scene_id,
                    element_id=el_id,
                ))

            # Check source reference integrity
            source_ref = el.get("source_reference")
            if source_ref:
                if not source_ref.get("quote"):
                    entries.append(ValidationLogEntry(
                        severity=ValidationSeverity.WARNING,
                        code="empty_source_quote",
                        message=f"元素 {el_id} 的原文引用缺少摘录内容，请检查来源段落。",
                        scene_id=scene_id,
                        element_id=el_id,
                    ))

    error_count = sum(1 for e in entries if e.severity == ValidationSeverity.ERROR)
    warning_count = sum(1 for e in entries if e.severity == ValidationSeverity.WARNING)
    info_count = sum(1 for e in entries if e.severity == ValidationSeverity.INFO)

    log = ValidationLog(
        entries=entries,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
    )

    # Write output
    output_file = project_dir / "validation_log.json"
    output_file.write_text(log.model_dump_json(indent=2), encoding="utf-8")

    if tracker:
        tracker.complete_stage(PipelineStage.VALIDATION, f"校验完成，{error_count} 错误 {warning_count} 警告", final=False)

    return log
