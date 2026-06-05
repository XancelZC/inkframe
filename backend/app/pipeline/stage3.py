"""Stage 3: Consistency Validation.

Check scene synthesis output for issues: character name consistency,
scene continuity, missing references, low confidence, source integrity.
"""

from __future__ import annotations

import json

from app.models.validation import ValidationLog, ValidationLogEntry, ValidationSeverity
from app.storage import get_project_dir


def run_stage3(project_id: str) -> ValidationLog:
    """Run Stage 3 consistency validation.

    Reads 03_characters.json + 04_scenes.json, writes validation_log.json.
    """
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

    # Check scene continuity
    scene_ids = [s["id"] for s in scenes]
    for i, sid in enumerate(scene_ids):
        expected = f"sc_{i + 1:04d}"
        if sid != expected:
            entries.append(ValidationLogEntry(
                severity=ValidationSeverity.WARNING,
                code="scene_gap",
                message=f"Scene ID {sid} is not sequential (expected {expected})",
                scene_id=sid,
            ))

    # Check each scene's elements
    for scene in scenes:
        scene_id = scene["id"]
        elements = scene.get("elements", [])

        if not elements:
            entries.append(ValidationLogEntry(
                severity=ValidationSeverity.WARNING,
                code="empty_scene",
                message=f"Scene {scene_id} has no elements",
                scene_id=scene_id,
            ))

        for el in elements:
            el_id = el.get("id", "")
            el_type = el.get("type", "")

            # Check character references
            if el_type == "dialogue":
                char_id = el.get("character_id", "")
                if char_id and char_id not in valid_char_ids:
                    entries.append(ValidationLogEntry(
                        severity=ValidationSeverity.ERROR,
                        code="invalid_character_ref",
                        message=f"Element {el_id} references non-existent character {char_id}",
                        scene_id=scene_id,
                        element_id=el_id,
                    ))

            # Check low confidence
            confidence = el.get("confidence", 1.0)
            if confidence < 0.7:
                entries.append(ValidationLogEntry(
                    severity=ValidationSeverity.WARNING,
                    code="low_confidence",
                    message=f"Element {el_id} has low confidence ({confidence:.2f})",
                    scene_id=scene_id,
                    element_id=el_id,
                ))

            # Check inferred without source reference
            if el.get("inferred") and not el.get("source_reference"):
                entries.append(ValidationLogEntry(
                    severity=ValidationSeverity.INFO,
                    code="inferred_no_source",
                    message=f"Inferred element {el_id} has no source reference",
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
                        message=f"Element {el_id} has source reference with empty quote",
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

    return log
