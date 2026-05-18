"""Unit tests for spec_logic_extractor."""

from __future__ import annotations

from lib_logical_consistency_prover.models import (
    ArtifactId,
    CodeContent,
    NormalizedArtifact,
    SpecContent,
    SpecId,
    SpecSection,
    TraceTag,
)
from lib_logical_consistency_prover.spec_logic_extractor import (
    SpecLogicItem,
    _find_spec_id_in_text,
    extract_spec_logic,
)


def _spec_artifact(content: SpecContent) -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="test.md"),
        artifact_type="spec",
        content=content,
    )


def test_extract_returns_list_of_spec_logic_items() -> None:
    artifact = _spec_artifact(
        SpecContent(
            spec_ids=[SpecId(spec_id="FR-01")],
            sections=[SpecSection(heading="Order", content="The order requirement.")],
        )
    )
    result = extract_spec_logic([artifact])
    assert isinstance(result, list)
    assert all(isinstance(i, SpecLogicItem) for i in result)


def test_extract_section_becomes_item() -> None:
    artifact = _spec_artifact(
        SpecContent(
            sections=[SpecSection(heading="Validate Order", content="Validate on create.")],
        )
    )
    result = extract_spec_logic([artifact])
    headings = [i.heading for i in result]
    assert "Validate Order" in headings


def test_extract_spec_id_found_in_section() -> None:
    artifact = _spec_artifact(
        SpecContent(
            spec_ids=[SpecId(spec_id="FR-01")],
            sections=[SpecSection(heading="FR-01 requirement", content="Something.")],
        )
    )
    result = extract_spec_logic([artifact])
    spec_ids_found = [i.spec_id for i in result if i.spec_id == "FR-01"]
    assert len(spec_ids_found) >= 1


def test_extract_trace_tags_produce_items() -> None:
    artifact = _spec_artifact(
        SpecContent(
            trace_tags=[TraceTag(tag="Traces", refs=["US-10", "US-11"])],
        )
    )
    result = extract_spec_logic([artifact])
    spec_ids = [i.spec_id for i in result]
    assert "US-10" in spec_ids or "US-11" in spec_ids


def test_empty_spec_returns_empty() -> None:
    artifact = _spec_artifact(SpecContent())
    result = extract_spec_logic([artifact])
    assert result == []


def test_non_spec_artifact_is_skipped() -> None:
    artifact = NormalizedArtifact(
        artifact_id=ArtifactId(path="code.py"),
        artifact_type="code",
        content=CodeContent(),
    )
    result = extract_spec_logic([artifact])
    assert result == []


def test_find_spec_id_in_text_known_id() -> None:
    assert _find_spec_id_in_text("FR-01 validation", {"FR-01", "FR-02"}) == "FR-01"


def test_find_spec_id_in_text_no_match() -> None:
    assert _find_spec_id_in_text("generic text", {"FR-01"}) == ""


def test_find_spec_id_in_text_pattern_fallback() -> None:
    result = _find_spec_id_in_text("See US-99 for details", set())
    assert result == "US-99"


def test_multiple_artifacts_merged() -> None:
    a1 = _spec_artifact(SpecContent(sections=[SpecSection(heading="Section A", content="...")]))
    a2 = _spec_artifact(SpecContent(sections=[SpecSection(heading="Section B", content="...")]))
    result = extract_spec_logic([a1, a2])
    headings = [i.heading for i in result]
    assert "Section A" in headings
    assert "Section B" in headings
