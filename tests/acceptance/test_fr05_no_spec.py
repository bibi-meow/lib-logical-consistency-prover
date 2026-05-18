"""LIB-FR-05: Missing spec or code artifacts → warning with confidence 0.0."""

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
)


@pytest.fixture
def config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="logical_consistency_v1",
        params={"layer_m_smt_solver": "none"},
    )


@pytest.fixture
def code_only() -> list[NormalizedArtifact]:
    return [
        NormalizedArtifact(
            artifact_id=ArtifactId(path="code.py"),
            artifact_type="code",
            content=CodeContent(
                functions=[FunctionNode(node_id="some.func", kind="function")],
                call_graph=CallGraph(),
            ),
        )
    ]


@pytest.fixture
def spec_only() -> list[NormalizedArtifact]:
    return [
        NormalizedArtifact(
            artifact_id=ArtifactId(path="spec.md"),
            artifact_type="spec",
            content=SpecContent(spec_ids=[SpecId(spec_id="FR-01")]),
        )
    ]


@pytest.fixture
def empty_artifacts() -> list[NormalizedArtifact]:
    return []


def test_no_spec_returns_warning(
    config: StrategyConfig, code_only: list[NormalizedArtifact]
) -> None:
    result = execute(config, code_only)
    assert result.verdict == "warning"


def test_no_code_returns_warning(
    config: StrategyConfig, spec_only: list[NormalizedArtifact]
) -> None:
    result = execute(config, spec_only)
    assert result.verdict == "warning"


def test_empty_artifacts_returns_warning(
    config: StrategyConfig, empty_artifacts: list[NormalizedArtifact]
) -> None:
    result = execute(config, empty_artifacts)
    assert result.verdict == "warning"


def test_no_spec_confidence_is_zero(
    config: StrategyConfig, code_only: list[NormalizedArtifact]
) -> None:
    result = execute(config, code_only)
    assert result.confidence == 0.0


def test_no_spec_evidence_layer_is_none(
    config: StrategyConfig, code_only: list[NormalizedArtifact]
) -> None:
    result = execute(config, code_only)
    ev = json.loads(result.evidence)
    assert ev["layer"] == "none"


def test_strategy_id_preserved_on_missing_artifacts(
    config: StrategyConfig, empty_artifacts: list[NormalizedArtifact]
) -> None:
    result = execute(config, empty_artifacts)
    assert result.strategy_id == "logical_consistency_v1"
