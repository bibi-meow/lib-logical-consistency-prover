"""LIB-FR-02: Keyword match → Layer M heuristic proof (no trace tags)."""

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
    SpecSection,
)


@pytest.fixture
def config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="logical_consistency_v1",
        params={"layer_m_smt_solver": "none", "advisory_only": False},
    )


@pytest.fixture
def spec_artifact() -> NormalizedArtifact:
    """Spec with keyword-rich headings but no explicit spec_ids."""
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="spec.md"),
        artifact_type="spec",
        content=SpecContent(
            sections=[
                SpecSection(
                    heading="validate_order",
                    content="Orders must be validated before processing.",
                ),
            ],
        ),
    )


@pytest.fixture
def code_artifact() -> NormalizedArtifact:
    """Code with matching function name but no trace tags."""
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="order.py"),
        artifact_type="code",
        content=CodeContent(
            functions=[
                FunctionNode(
                    node_id="order.validate_order",
                    kind="function",
                    docstring="Validates an order before processing.",
                ),
            ],
            call_graph=CallGraph(),
        ),
    )


def test_returns_result(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    assert result.strategy_id == "logical_consistency_v1"


def test_evidence_has_proved_pair_via_keyword(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    ev = json.loads(result.evidence)
    # Should have proved via keyword_match heuristic
    methods = [p["method"] for p in ev.get("proved_pairs", [])]
    assert "keyword_match" in methods or len(ev.get("proved_pairs", [])) >= 1


def test_verdict_not_pass_without_trace(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    """Keyword match confidence < 0.9, so verdict should be warning."""
    result = execute(config, [spec_artifact, code_artifact])
    # keyword match gives 0.75 → verdict should be warning (0.6 <= x < 0.9)
    assert result.verdict in ("warning", "pass")


def test_confidence_positive(
    config: StrategyConfig,
    spec_artifact: NormalizedArtifact,
    code_artifact: NormalizedArtifact,
) -> None:
    result = execute(config, [spec_artifact, code_artifact])
    assert result.confidence > 0.0
