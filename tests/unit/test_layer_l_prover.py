"""Unit tests for layer_l_prover."""

from __future__ import annotations

from lib_logical_consistency_prover.layer_l_prover import LayerLResult, try_layer_l
from lib_logical_consistency_prover.models import (
    ArtifactId,
    CallGraph,
    CodeContent,
    FunctionNode,
    NormalizedArtifact,
    SpecContent,
    SpecId,
    TraceTag,
)


def _spec(spec_ids: list[str]) -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="spec.md"),
        artifact_type="spec",
        content=SpecContent(spec_ids=[SpecId(spec_id=sid) for sid in spec_ids]),
    )


def _code(trace_refs: list[str]) -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="code.py"),
        artifact_type="code",
        content=CodeContent(
            functions=[
                FunctionNode(
                    node_id="mod.func",
                    kind="function",
                    trace_tags=[TraceTag(tag="Traces", refs=trace_refs)],
                )
            ]
            if trace_refs
            else [],
            call_graph=CallGraph(),
        ),
    )


def test_try_layer_l_returns_result() -> None:
    result = try_layer_l([_spec(["FR-01"])], [_code(["FR-01"])], {})
    assert isinstance(result, LayerLResult)


def test_matching_trace_ref_creates_proved_pair() -> None:
    result = try_layer_l([_spec(["FR-01"])], [_code(["FR-01"])], {})
    assert len(result.proved) == 1
    assert result.proved[0]["spec_id"] == "FR-01"


def test_no_matching_trace_ref_creates_unproved() -> None:
    result = try_layer_l([_spec(["FR-01"])], [_code([])], {})
    assert len(result.unproved) == 1
    assert result.unproved[0]["spec_id"] == "FR-01"


def test_confidence_positive_when_proved() -> None:
    result = try_layer_l([_spec(["FR-01"])], [_code(["FR-01"])], {})
    assert result.confidence > 0.0


def test_confidence_low_when_unproved() -> None:
    result = try_layer_l([_spec(["FR-01"])], [_code([])], {})
    assert result.confidence < 0.5


def test_empty_spec_ids_returns_moderate_confidence() -> None:
    """No spec_ids at all → uses section-based fallback."""
    result = try_layer_l([_spec([])], [_code([])], {})
    # Confidence is 0.35 or 0.5 depending on sections
    assert result.confidence <= 0.5


def test_multiple_spec_ids_all_matched() -> None:
    result = try_layer_l([_spec(["FR-01", "FR-02"])], [_code(["FR-01", "FR-02"])], {})
    assert len(result.proved) == 2


def test_partial_match_confidence_between_zero_and_one() -> None:
    result = try_layer_l([_spec(["FR-01", "FR-02"])], [_code(["FR-01"])], {})
    assert 0.0 < result.confidence < 1.0


def test_method_is_layer_l_trace() -> None:
    result = try_layer_l([_spec(["FR-01"])], [_code(["FR-01"])], {})
    assert result.proved[0]["method"] == "layer_l_trace"
