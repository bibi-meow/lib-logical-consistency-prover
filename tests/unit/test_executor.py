"""Unit tests for executor.py."""

from __future__ import annotations

import json

from lib_logical_consistency_prover import execute
from lib_logical_consistency_prover.models import (
    ArtifactId,
    CallGraph,
    CodeContent,
    EvaluationResult,
    FPOverride,
    FunctionNode,
    NormalizedArtifact,
    SpecContent,
    SpecId,
    StrategyConfig,
    TraceTag,
)


def _config(**kwargs) -> StrategyConfig:
    params = {"layer_m_smt_solver": "none", **kwargs.pop("params", {})}
    return StrategyConfig(strategy_id="logical_consistency_v1", params=params, **kwargs)


def _spec(spec_ids: list[str] | None = None, sections: list | None = None) -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="spec.md"),
        artifact_type="spec",
        content=SpecContent(
            spec_ids=[SpecId(spec_id=sid) for sid in (spec_ids or [])],
            sections=sections or [],
        ),
    )


def _code(trace_refs: list[str] | None = None) -> NormalizedArtifact:
    fns = []
    if trace_refs:
        fns.append(
            FunctionNode(
                node_id="mod.func",
                kind="function",
                trace_tags=[TraceTag(tag="Traces", refs=trace_refs)],
            )
        )
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="code.py"),
        artifact_type="code",
        content=CodeContent(functions=fns, call_graph=CallGraph()),
    )


def test_execute_returns_evaluation_result() -> None:
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])])
    assert isinstance(result, EvaluationResult)


def test_strategy_id_preserved() -> None:
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])])
    assert result.strategy_id == "logical_consistency_v1"


def test_verdict_is_valid_value() -> None:
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])])
    assert result.verdict in ("pass", "fail", "warning", "fp_candidate")


def test_evidence_is_valid_json() -> None:
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])])
    ev = json.loads(result.evidence)
    assert isinstance(ev, dict)


def test_evidence_has_required_keys() -> None:
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])])
    ev = json.loads(result.evidence)
    for key in ("layer", "proved_pairs", "unproved_pairs", "summary"):
        assert key in ev, f"Missing key: {key}"


def test_disabled_config_returns_pass() -> None:
    result = execute(_config(enabled=False), [_spec(["UNKNOWN"]), _code([])])
    assert result.verdict == "pass"
    assert result.confidence == 1.0


def test_fp_overrides_accepted() -> None:
    overrides = [FPOverride(rule_id="rule1", reason="known issue")]
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])], fp_overrides=overrides)
    assert isinstance(result, EvaluationResult)


def test_fp_overrides_none_accepted() -> None:
    result = execute(_config(), [_spec(["FR-01"]), _code(["FR-01"])], fp_overrides=None)
    assert isinstance(result, EvaluationResult)


def test_high_confidence_gives_pass() -> None:
    """Multiple trace refs → high confidence → pass."""
    result = execute(
        _config(),
        [
            _spec(["FR-01", "FR-02"]),
            NormalizedArtifact(
                artifact_id=ArtifactId(path="code.py"),
                artifact_type="code",
                content=CodeContent(
                    functions=[
                        FunctionNode(
                            node_id="mod.func1",
                            kind="function",
                            trace_tags=[TraceTag(tag="Traces", refs=["FR-01"])],
                        ),
                        FunctionNode(
                            node_id="mod.func2",
                            kind="function",
                            trace_tags=[TraceTag(tag="Traces", refs=["FR-02"])],
                        ),
                    ],
                    call_graph=CallGraph(),
                ),
            ),
        ],
    )
    assert result.verdict == "pass"
    assert result.confidence >= 0.9
