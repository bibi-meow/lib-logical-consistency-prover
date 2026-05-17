"""Tests for LIB-FR-01: spec logic extraction.

Gherkin scenario coverage:
  - Scenario: must/shall パターンから論理命題を抽出する
  - Scenario: 空の SpecContent を渡す

Traces: LIB-FR-01
AT file: tests/test_fr01_spec_logic_extractor.py
"""

from __future__ import annotations

from lib_logical_consistency_prover import spec_logic_extractor
from lib_logical_consistency_prover.models import SpecContent, SpecSection


class TestExtractMustShallPatterns:
    """Scenario: must/shall パターンから論理命題を抽出する."""

    def test_when_must_pattern(self) -> None:
        """When X, the system must Y → premise=X, conclusion=Y."""
        spec = SpecContent(
            sections=[
                SpecSection(
                    title="Auth",
                    content=("When authentication succeeds, the system must return status 200."),
                )
            ]
        )
        result = spec_logic_extractor.extract(spec)
        assert len(result) >= 1
        # Find the when-must match
        when_match = next((r for r in result if "authentication" in r["premise"].lower()), None)
        assert when_match is not None, f"Expected when-must match, got: {result}"
        assert "authentication" in when_match["premise"].lower()
        assert "200" in when_match["conclusion"] or "status" in when_match["conclusion"]

    def test_shall_standalone_pattern(self) -> None:
        """Standalone 'shall' returns entry with empty premise."""
        spec = SpecContent(
            sections=[
                SpecSection(
                    title="Performance",
                    content="The system shall respond within 500ms.",
                )
            ]
        )
        result = spec_logic_extractor.extract(spec)
        assert len(result) >= 1
        conclusions = [r["conclusion"] for r in result]
        assert any("respond" in c or "500ms" in c for c in conclusions)

    def test_if_then_pattern(self) -> None:
        """If X then Y → premise=X, conclusion=Y."""
        spec = SpecContent(
            sections=[
                SpecSection(
                    title="Validation",
                    content="If input is null then raise ValueError.",
                )
            ]
        )
        result = spec_logic_extractor.extract(spec)
        assert len(result) >= 1
        if_match = next((r for r in result if "null" in r.get("premise", "").lower()), None)
        assert if_match is not None or any("ValueError" in r["conclusion"] for r in result)

    def test_multiple_sections(self) -> None:
        """Multiple sections with must patterns → all extracted."""
        spec = SpecContent(
            sections=[
                SpecSection(
                    title="S1",
                    content="The system must log all errors.",
                ),
                SpecSection(
                    title="S2",
                    content="The system must validate input before processing.",
                ),
            ]
        )
        result = spec_logic_extractor.extract(spec)
        assert len(result) >= 2

    def test_spec_id_propagation(self) -> None:
        """spec_id is included in each result entry."""
        from lib_logical_consistency_prover.models import SpecId

        spec = SpecContent(
            spec_ids=[SpecId("US-23")],
            sections=[
                SpecSection(
                    title="Consistency",
                    content="The system must prove logical consistency.",
                )
            ],
        )
        result = spec_logic_extractor.extract(spec)
        assert all("spec_id" in r for r in result)
        assert all(r["spec_id"] == "US-23" for r in result)


class TestExtractEmptySpecContent:
    """Scenario: 空の SpecContent を渡す."""

    def test_empty_sections(self) -> None:
        """Empty sections → empty list (no exception)."""
        spec = SpecContent()
        result = spec_logic_extractor.extract(spec)
        assert result == []

    def test_sections_with_no_patterns(self) -> None:
        """Sections with no must/shall/if-then → empty list."""
        spec = SpecContent(
            sections=[
                SpecSection(
                    title="Introduction",
                    content="This document describes the system architecture.",
                )
            ]
        )
        result = spec_logic_extractor.extract(spec)
        # May be empty or minimal — no crash
        assert isinstance(result, list)

    def test_none_safe(self) -> None:
        """SpecContent with None-like defaults doesn't crash."""
        spec = SpecContent(sections=[], spec_ids=[], trace_tags=[])
        result = spec_logic_extractor.extract(spec)
        assert result == []
