"""Tests for the canonical schema contract (Issue #1).

Verifies ID formats, source_reference structure, confidence/inferred rules,
element types, status enum, error format, and SSE event structure.
"""

from typing import Optional

import pytest
from pydantic import BaseModel, ValidationError

from app.models.ids import (
    make_project_id,
    make_chapter_id,
    make_paragraph_id,
    make_character_id,
    make_scene_id,
    make_element_id,
    ProjectId,
    ChapterId,
    ParagraphId,
    CharacterId,
    SceneId,
    ElementId,
)
from app.models.character import Character, Relationship, CharacterTable
from app.models.character import Character, Relationship, CharacterTable
from app.models.screenplay import (
    DialogueElement,
    ActionElement,
    TransitionElement,
    NarrationElement,
    SourceReference,
    Scene,
    Act,
    Screenplay,
    ScreenplayMetadata,
    ElementType,
)
from app.models.status import PipelineStatus, PipelineStage, StatusEnum
from app.models.errors import ErrorResponse, ErrorDetail, ErrorCode
from app.models.events import SSEEvent
from app.models.validation import ValidationLogEntry, ValidationLog, ValidationSeverity
from app.models.text import Chapter, Paragraph, PreprocessedText
from app.models.project import ProjectSummary, ProjectIndex, ProjectDetail


# === ID Format Tests ===

# Helper model to trigger Pydantic ValidationError on ID construction


class _IdHolder(BaseModel):
    project_id: Optional[ProjectId] = None
    chapter_id: Optional[ChapterId] = None
    paragraph_id: Optional[ParagraphId] = None
    character_id: Optional[CharacterId] = None
    scene_id: Optional[SceneId] = None
    element_id: Optional[ElementId] = None


class TestIdFormats:
    def test_project_id_format(self):
        pid = make_project_id("My Novel")
        assert pid.startswith("prj_")
        assert "my_novel" in pid

    def test_project_id_rejects_invalid(self):
        with pytest.raises(ValidationError):
            _IdHolder(project_id="invalid_id")

    def test_chapter_id_format(self):
        cid = make_chapter_id(1)
        assert cid == "ch_0001"

    def test_chapter_id_rejects_zero(self):
        with pytest.raises(ValueError, match=">= 1"):
            make_chapter_id(0)

    def test_chapter_id_rejects_invalid(self):
        with pytest.raises(ValidationError):
            _IdHolder(chapter_id="ch_1")  # needs 4 digits

    def test_paragraph_id_format(self):
        pid = make_paragraph_id(1)
        assert pid == "p_000001"

    def test_paragraph_id_rejects_zero(self):
        with pytest.raises(ValueError, match=">= 1"):
            make_paragraph_id(0)

    def test_paragraph_id_rejects_invalid(self):
        with pytest.raises(ValidationError):
            _IdHolder(paragraph_id="p_1")  # needs 6 digits

    def test_character_id_format(self):
        cid = make_character_id("Xiangzi")
        assert cid == "char_xiangzi"

    def test_character_id_rejects_invalid(self):
        with pytest.raises(ValidationError):
            _IdHolder(character_id="xiangzi")  # missing char_ prefix

    def test_scene_id_format(self):
        sid = make_scene_id(1)
        assert sid == "sc_0001"

    def test_scene_id_rejects_zero(self):
        with pytest.raises(ValueError, match=">= 1"):
            make_scene_id(0)

    def test_element_id_format(self):
        eid = make_element_id(1)
        assert eid == "el_000001"

    def test_element_id_rejects_zero(self):
        with pytest.raises(ValueError, match=">= 1"):
            make_element_id(0)


# === Source Reference Tests ===


class TestSourceReference:
    def test_valid_source_reference(self):
        ref = SourceReference(
            chapter_id="ch_0001",
            paragraph_ids=["p_000012"],
            start_offset=120,
            end_offset=168,
            quote="祥子拉着车穿过清晨的街口。",
        )
        assert ref.chapter_id == "ch_0001"
        assert len(ref.paragraph_ids) == 1

    def test_source_reference_requires_quote(self):
        with pytest.raises(ValidationError):
            SourceReference(
                chapter_id="ch_0001",
                paragraph_ids=["p_000012"],
                start_offset=0,
                end_offset=10,
                quote="",  # empty quote
            )

    def test_source_reference_requires_paragraph_ids(self):
        with pytest.raises(ValidationError):
            SourceReference(
                chapter_id="ch_0001",
                paragraph_ids=[],  # empty list
                start_offset=0,
                end_offset=10,
                quote="some text",
            )

    def test_source_reference_end_must_be_gte_start(self):
        with pytest.raises(ValidationError, match="end_offset.*start_offset"):
            SourceReference(
                chapter_id="ch_0001",
                paragraph_ids=["p_000001"],
                start_offset=100,
                end_offset=50,
                quote="text",
            )


# === Confidence and Inferred Tests ===


class TestConfidenceInferred:
    def test_confidence_range(self):
        el = ActionElement(
            id="el_000001",
            content="祥子拉着车。",
            confidence=0.86,
            inferred=False,
        )
        assert el.confidence == 0.86

    def test_confidence_cannot_exceed_1(self):
        with pytest.raises(ValidationError):
            ActionElement(id="el_000001", content="text", confidence=1.5)

    def test_confidence_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            ActionElement(id="el_000001", content="text", confidence=-0.1)

    def test_inferred_defaults_false(self):
        el = ActionElement(id="el_000001", content="text")
        assert el.inferred is False

    def test_inferred_set_true(self):
        el = ActionElement(id="el_000001", content="text", inferred=True)
        assert el.inferred is True


# === Element Type Tests ===


class TestElementTypes:
    def test_dialogue_element(self):
        el = DialogueElement(
            id="el_000001",
            character_id="char_xiangzi",
            content="你好。",
            parenthetical="平静地说",
        )
        assert el.type == ElementType.DIALOGUE
        assert el.character_id == "char_xiangzi"
        assert el.parenthetical == "平静地说"

    def test_action_element(self):
        el = ActionElement(
            id="el_000002",
            content="祥子拉着车穿过街口。",
            character_ids=["char_xiangzi"],
        )
        assert el.type == ElementType.ACTION
        assert "char_xiangzi" in el.character_ids

    def test_transition_element(self):
        el = TransitionElement(id="el_000003", content="CUT TO:")
        assert el.type == ElementType.TRANSITION

    def test_narration_element(self):
        el = NarrationElement(id="el_000004", content="他心想，这一切不过是徒劳。")
        assert el.type == ElementType.NARRATION

    def test_dialogue_requires_character_id(self):
        with pytest.raises(ValidationError):
            DialogueElement(id="el_000001", content="text")  # missing character_id

    def test_action_does_not_require_character_ids(self):
        el = ActionElement(id="el_000001", content="门被推开。")
        assert el.character_ids == []


# === Character Tests ===


class TestCharacter:
    def test_character_with_relationships(self):
        char = Character(
            id="char_xiangzi",
            name="祥子",
            aliases=["车夫"],
            description="年轻车夫",
            relationships=[
                Relationship(
                    target_character_id="char_huniu",
                    type="acquaintance",
                    description="原文中存在多次互动",
                )
            ],
        )
        assert len(char.relationships) == 1
        assert char.relationships[0].target_character_id == "char_huniu"

    def test_character_table(self):
        table = CharacterTable(
            characters=[
                Character(id="char_a", name="A"),
                Character(id="char_b", name="B"),
            ]
        )
        assert len(table.characters) == 2


# === Pipeline Status Tests ===


class TestPipelineStatus:
    def test_status_enum_values(self):
        assert StatusEnum.IDLE.value == "idle"
        assert StatusEnum.RUNNING.value == "running"
        assert StatusEnum.FAILED.value == "failed"

    def test_pipeline_stage_values(self):
        assert PipelineStage.PREPROCESSING.value == "preprocessing"
        assert PipelineStage.SCENE_SYNTHESIS.value == "scene_synthesis"

    def test_pipeline_status_model(self):
        status = PipelineStatus(
            project_id="prj_test_20260101",
            current_stage=PipelineStage.PREPROCESSING,
            status=StatusEnum.RUNNING,
            progress=0.5,
        )
        assert status.progress == 0.5

    def test_progress_cannot_exceed_1(self):
        with pytest.raises(ValidationError):
            PipelineStatus(project_id="prj_test", progress=1.5)

    def test_progress_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            PipelineStatus(project_id="prj_test", progress=-0.1)


# === Error Response Tests ===


class TestErrorResponse:
    def test_error_response_format(self):
        resp = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.SCHEMA_VALIDATION_FAILED,
                message="Stage output did not match schema",
                details={"field": "character_id"},
            )
        )
        assert resp.error.code == ErrorCode.SCHEMA_VALIDATION_FAILED
        assert resp.error.details["field"] == "character_id"

    def test_error_codes(self):
        assert ErrorCode.PROVIDER_ERROR.value == "provider_error"
        assert ErrorCode.RATE_LIMITED.value == "rate_limited"
        assert ErrorCode.INVALID_JSON.value == "invalid_json"
        assert ErrorCode.TIMEOUT.value == "timeout"
        assert ErrorCode.NOT_FOUND.value == "not_found"


# === SSE Event Tests ===


class TestSSEEvent:
    def test_sse_event_structure(self):
        event = SSEEvent(
            project_id="prj_demo_20260605",
            stage=PipelineStage.SCENE_SYNTHESIS,
            status=StatusEnum.RUNNING,
            chapter_id="ch_0003",
            progress=0.48,
            message="Generating scenes for chapter 3",
        )
        assert event.stage == PipelineStage.SCENE_SYNTHESIS
        assert event.progress == 0.48
        assert event.chapter_id == "ch_0003"

    def test_sse_event_without_chapter(self):
        event = SSEEvent(
            project_id="prj_demo_20260605",
            stage=PipelineStage.PREPROCESSING,
            status=StatusEnum.SUCCEEDED,
            progress=1.0,
            message="Preprocessing complete",
        )
        assert event.chapter_id is None

    def test_sse_event_progress_cannot_exceed_1(self):
        with pytest.raises(ValidationError):
            SSEEvent(
                project_id="prj_demo_20260605",
                stage=PipelineStage.PREPROCESSING,
                status=StatusEnum.RUNNING,
                progress=1.5,
            )

    def test_sse_event_progress_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            SSEEvent(
                project_id="prj_demo_20260605",
                stage=PipelineStage.PREPROCESSING,
                status=StatusEnum.RUNNING,
                progress=-0.1,
            )


# === Validation Log Tests ===


class TestValidationLog:
    def test_validation_log_entry(self):
        entry = ValidationLogEntry(
            severity=ValidationSeverity.WARNING,
            code="low_confidence",
            message="Element has confidence below 0.7",
            scene_id="sc_0001",
            element_id="el_000005",
        )
        assert entry.severity == ValidationSeverity.WARNING

    def test_validation_log_entry_rejects_invalid_scene_id(self):
        with pytest.raises(ValidationError):
            ValidationLogEntry(
                severity=ValidationSeverity.WARNING,
                code="test",
                message="test",
                scene_id="invalid_id",
            )

    def test_validation_log_counts(self):
        log = ValidationLog(
            entries=[
                ValidationLogEntry(severity=ValidationSeverity.ERROR, code="e1", message="err"),
                ValidationLogEntry(severity=ValidationSeverity.WARNING, code="w1", message="warn"),
                ValidationLogEntry(severity=ValidationSeverity.INFO, code="i1", message="info"),
            ],
            error_count=1,
            warning_count=1,
            info_count=1,
        )
        assert log.error_count == 1


# === Text Preprocessing Tests ===


class TestPreprocessedText:
    def test_chapter_and_paragraph(self):
        text = PreprocessedText(
            chapters=[
                Chapter(
                    id="ch_0001",
                    title="第一章",
                    paragraphs=[
                        Paragraph(
                            id="p_000001",
                            text="祥子拉着车穿过清晨的街口。",
                            start_offset=0,
                            end_offset=14,
                        )
                    ],
                )
            ],
            detected_language="zh",
        )
        assert text.chapters[0].paragraphs[0].id == "p_000001"

    def test_language_must_be_zh_or_en(self):
        with pytest.raises(ValidationError):
            PreprocessedText(chapters=[], detected_language="fr")

    def test_paragraph_end_must_be_gte_start(self):
        with pytest.raises(ValidationError, match="end_offset.*start_offset"):
            PreprocessedText(
                chapters=[
                    Chapter(
                        id="ch_0001",
                        paragraphs=[
                            Paragraph(
                                id="p_000001",
                                text="text",
                                start_offset=100,
                                end_offset=50,
                            )
                        ],
                    )
                ],
                detected_language="zh",
            )


# === Project Tests ===


class TestProject:
    def test_project_summary(self):
        proj = ProjectSummary(
            id="prj_demo_20260605",
            title="Demo Novel",
            source_language="zh",
        )
        assert proj.id == "prj_demo_20260605"

    def test_project_index(self):
        idx = ProjectIndex(
            projects=[
                ProjectSummary(id="prj_alpha_1000000000", title="A"),
                ProjectSummary(id="prj_beta_2000000000", title="B"),
            ]
        )
        assert len(idx.projects) == 2

    def test_project_detail(self):
        detail = ProjectDetail(
            id="prj_demo_20260605",
            title="Demo",
            raw_text="祥子拉着车...",
        )
        assert detail.raw_text is not None


# === Full Screenplay Integration Test ===


class TestFullScreenplay:
    def test_full_screenplay_from_prd_example(self):
        """Reconstruct the YAML example from the PRD as a Pydantic model."""
        screenplay = Screenplay(
            metadata=ScreenplayMetadata(
                project_id="prj_demo_20260605",
                title="Demo Novel",
                source_language="zh",
            ),
            characters=[
                Character(
                    id="char_xiangzi",
                    name="祥子",
                    aliases=["车夫"],
                    description="年轻车夫",
                )
            ],
            acts=[
                Act(
                    id="act_01",
                    title="第一幕",
                    scenes=[
                        Scene(
                            id="sc_0001",
                            chapter_id="ch_0001",
                            title="街口初遇",
                            location="北平街口",
                            time_of_day="morning",
                            timeline_order=1,
                            elements=[
                                ActionElement(
                                    id="el_000001",
                                    content="祥子拉着车穿过清晨的街口。",
                                    character_ids=["char_xiangzi"],
                                    inferred=False,
                                    confidence=0.86,
                                    source_reference=SourceReference(
                                        chapter_id="ch_0001",
                                        paragraph_ids=["p_000012"],
                                        start_offset=120,
                                        end_offset=168,
                                        quote="祥子拉着车...",
                                    ),
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        assert len(screenplay.acts) == 1
        assert screenplay.acts[0].scenes[0].elements[0].type == ElementType.ACTION
