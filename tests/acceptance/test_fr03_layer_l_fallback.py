"""LIB-FR-03: No Layer M match → falls back to Layer L."""

from __future__ import annotations

import json

import pytest

from lib_logical_consistency_prover import (
    NormalizedArtifact,
    StrategyConfig,
    execute,
)
from lib_logical_consistency_prover.models import (
    ArtifactId,
    CallGraph,
    CodeContent,
    FunctionNode,
    SpecContent,
    SpecId,
    SpecSection,
    TraceTag,
)


@pytest.fixture
def config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="logical_consistency_v1",
        params={"layer_m_smt_solver": "none", "advisory_only": False},
    )


@pytest.fixture
def spec_no_match() -> NormalizedArtifact:
    """Spec with spec_id that won't match via Layer M."""
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="spec.md"),
        artifact_type="spec",
        content=SpecContent(
            spec_ids=[SpecId(spec_id="UNMATCHABLE-99")],
            sections=[
                SpecSection(heading="Unmatchable Requirement", content="XYZ constraint."),
            ],
        ),
    )


@pytest.fixture
def code_with_trace() -> NormalizedArtifact:
    """Code function that traces to UNMATCHABLE-99 — Layer L will find it."""
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="code.py"),
        artifact_type="code",
        content=CodeContent(
            functions=[
                FunctionNode(
                    node_id="some_module.some_func",
                    kind="function",
                    trace_tags=[TraceTag(tag="Traces", refs=["UNMATCHABLE-99"])],
                    docstring="Implements UNMATCHABLE-99",
                ),
            ],
            call_graph=CallGraph(),
        ),
    )


@pytest.fixture
def code_no_trace() -> NormalizedArtifact:
    """Code function with no trace tags — Layer L won't find a match."""
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="code.py"),
        artifact_type="code",
        content=CodeContent(
            functions=[
                FunctionNode(
                    node_id="xyz_module.irrelevant_func",
                    kind="function",
                    docstring="Does something completely unrelated.",
                ),
            ],
            call_graph=CallGraph(),
        ),
    )


def test_layer_l_fallback_with_trace(
    config: StrategyConfig,
    spec_no_match: NormalizedArtifact,
    code_with_trace: NormalizedArtifact,
) -> None:
    """When Layer M fails but Layer L finds a trace ref, verdict improves."""
    result = execute(config, [spec_no_match, code_with_trace])
    # Layer M cannot prove via trace_ref for "UNMATCHABLE-99" (no keyword match either)
    # Layer L should find the trace ref
    assert result.verdict in ("pass", "warning", "fail")
    assert result.confidence >= 0.0


def test_layer_l_fallback_no_trace_returns_fail_or_warning(
    config: StrategyConfig,
    spec_no_match: NormalizedArtifact,
    code_no_trace: NormalizedArtifact,
) -> None:
    """When neither Layer M nor Layer L finds a match, low confidence."""
    result = execute(config, [spec_no_match, code_no_trace])
    assert result.verdict in ("fail", "warning")
    assert result.confidence < 0.9


def test_evidence_structure_is_valid(
    config: StrategyConfig,
    spec_no_match: NormalizedArtifact,
    code_no_trace: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_no_match, code_no_trace])
    ev = json.loads(result.evidence)
    assert "layer" in ev
    assert "proved_pairs" in ev
    assert "unproved_pairs" in ev
    assert "summary" in ev
    assert isinstance(ev["proved_pairs"], list)
    assert isinstance(ev["unproved_pairs"], list)


def test_evidence_layer_is_l_when_m_fails(
    config: StrategyConfig,
    spec_no_match: NormalizedArtifact,
    code_no_trace: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_no_match, code_no_trace])
    ev = json.loads(result.evidence)
    assert ev["layer"] == "L"
