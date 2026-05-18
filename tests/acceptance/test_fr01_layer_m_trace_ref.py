"""LIB-FR-01: Direct trace tag reference → Layer M proof."""

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
    ContractInfo,
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
        params={
            "layer_m_smt_solver": "none",  # skip z3 for tests
            "advisory_only": False,
        },
    )


@pytest.fixture
def spec_artifact() -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="spec.md"),
        artifact_type="spec",
        content=SpecContent(
            spec_ids=[SpecId(spec_id="FR-01"), SpecId(spec_id="US-22")],
            sections=[
                SpecSection(
                    heading="Order Creation",
                    content="The system shall create orders with validated items.",
                ),
            ],
        ),
    )


@pytest.fixture
def code_artifact() -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="order_service.py"),
        artifact_type="code",
        content=CodeContent(
            functions=[
                FunctionNode(
                    node_id="order_service.OrderService.create_order",
                    kind="method",
                    trace_tags=[TraceTag(tag="Traces", refs=["FR-01", "US-22"])],
                    contracts=ContractInfo(preconditions=["validate_items"]),
                    docstring="Create a new order. Traces: FR-01, US-22",
                ),
            ],
            call_graph=CallGraph(),
        ),
    )


def test_returns_evaluation_result(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    assert result.strategy_id == "logical_consistency_v1"
    assert result.verdict in ("pass", "warning", "fail", "fp_candidate")


def test_verdict_is_pass_when_trace_refs_match(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    assert result.verdict == "pass"


def test_confidence_is_high(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    assert result.confidence >= 0.7


def test_evidence_has_proved_pairs(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    ev = json.loads(result.evidence)
    assert len(ev["proved_pairs"]) >= 1


def test_evidence_layer_is_m(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    ev = json.loads(result.evidence)
    assert ev["layer"] == "M"


def test_evidence_has_summary(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    ev = json.loads(result.evidence)
    assert "summary" in ev
    assert len(ev["summary"]) > 0


def test_fp_candidates_empty_by_default(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    assert result.fp_candidates == []
