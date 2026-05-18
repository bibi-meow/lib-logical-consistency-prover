"""LIB-FR-06: enabled=False → always returns pass without evaluation."""

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
    CodeContent,
    SpecContent,
    SpecId,
)


@pytest.fixture
def disabled_config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="logical_consistency_v1",
        params={"layer_m_smt_solver": "none"},
        enabled=False,
    )


@pytest.fixture
def any_artifacts() -> list[NormalizedArtifact]:
    return [
        NormalizedArtifact(
            artifact_id=ArtifactId(path="spec.md"),
            artifact_type="spec",
            content=SpecContent(spec_ids=[SpecId(spec_id="UNKNOWN-999")]),
        ),
        NormalizedArtifact(
            artifact_id=ArtifactId(path="code.py"),
            artifact_type="code",
            content=CodeContent(),
        ),
    ]


def test_disabled_returns_pass(
    disabled_config: StrategyConfig, any_artifacts: list[NormalizedArtifact]
) -> None:
    result = execute(disabled_config, any_artifacts)
    assert result.verdict == "pass"


def test_disabled_confidence_is_one(
    disabled_config: StrategyConfig, any_artifacts: list[NormalizedArtifact]
) -> None:
    result = execute(disabled_config, any_artifacts)
    assert result.confidence == 1.0


def test_disabled_strategy_id_preserved(
    disabled_config: StrategyConfig, any_artifacts: list[NormalizedArtifact]
) -> None:
    result = execute(disabled_config, any_artifacts)
    assert result.strategy_id == "logical_consistency_v1"


def test_disabled_evidence_is_valid_json(
    disabled_config: StrategyConfig, any_artifacts: list[NormalizedArtifact]
) -> None:
    result = execute(disabled_config, any_artifacts)
    ev = json.loads(result.evidence)
    assert isinstance(ev, dict)
    assert "layer" in ev
