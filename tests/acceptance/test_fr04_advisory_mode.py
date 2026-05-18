"""LIB-FR-04: advisory_only=True → verdict never 'fail'."""

from __future__ import annotations

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
def advisory_config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="logical_consistency_v1",
        params={"advisory_only": True, "layer_m_smt_solver": "none"},
    )


@pytest.fixture
def strict_config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="logical_consistency_v1",
        params={"advisory_only": False, "layer_m_smt_solver": "none"},
    )


@pytest.fixture
def unmatched_artifacts() -> list[NormalizedArtifact]:
    return [
        NormalizedArtifact(
            artifact_id=ArtifactId(path="spec.md"),
            artifact_type="spec",
            content=SpecContent(
                spec_ids=[SpecId(spec_id="COMPLETELY-UNKNOWN-99")],
            ),
        ),
        NormalizedArtifact(
            artifact_id=ArtifactId(path="code.py"),
            artifact_type="code",
            content=CodeContent(),
        ),
    ]


def test_advisory_never_returns_fail(
    advisory_config: StrategyConfig,
    unmatched_artifacts: list[NormalizedArtifact],
) -> None:
    result = execute(advisory_config, unmatched_artifacts)
    assert result.verdict != "fail"


def test_advisory_returns_warning_not_fail(
    advisory_config: StrategyConfig,
    unmatched_artifacts: list[NormalizedArtifact],
) -> None:
    result = execute(advisory_config, unmatched_artifacts)
    assert result.verdict == "warning"


def test_strict_mode_returns_fail_on_no_match(
    strict_config: StrategyConfig,
    unmatched_artifacts: list[NormalizedArtifact],
) -> None:
    """Without advisory_only, low confidence → fail."""
    result = execute(strict_config, unmatched_artifacts)
    assert result.verdict == "fail"


def test_advisory_strategy_id_preserved(
    advisory_config: StrategyConfig,
    unmatched_artifacts: list[NormalizedArtifact],
) -> None:
    result = execute(advisory_config, unmatched_artifacts)
    assert result.strategy_id == "logical_consistency_v1"
