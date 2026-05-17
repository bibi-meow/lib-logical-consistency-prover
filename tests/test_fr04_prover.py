"""Tests for LIB-FR-04: EvaluationResult generation via prover.prove().

Gherkin scenario coverage:
  - Scenario: 通常モード（advisory_only=False）で全ペア証明済み
  - Scenario: advisory_only=True モードで fail が warning に変換される
  - Scenario: EvaluationResult の全フィールドが揃っている

Traces: LIB-FR-04, LIB-NFR-02
AT file: tests/test_fr04_prover.py
"""

from __future__ import annotations

import pytest

from lib_logical_consistency_prover import prove
from lib_logical_consistency_prover.models import (
    CodeContent,
    ContractInfo,
    EvaluationResult,
    FunctionNode,
    SpecContent,
    SpecId,
    SpecSection,
    StrategyConfig,
    TraceTag,
)


def _make_default_config(**overrides: object) -> StrategyConfig:
    """Create a StrategyConfig with optional param overrides."""
    params = {
        "layer_m_smt_solver": "z3",
        "layer_m_bisimulation": True,
        "layer_l_model": "claude-sonnet-4-6",
        "layer_l_confidence_threshold": 0.75,
        "layer_m_timeout_sec": 10,
        "blocking_mode": "auto",
        "advisory_only": False,
    }
    params.update(overrides)
    return StrategyConfig(params=params)


class TestProveNormalMode:
    """Scenario: 通常モード（advisory_only=False）で全ペア証明済み."""

    def test_empty_spec_code_returns_pass(self) -> None:
        """Empty spec and code → verdict is 'pass' or 'warning', not 'fail'."""
        result = prove(SpecContent(), CodeContent())
        assert isinstance(result, EvaluationResult)
        assert result.verdict in ("pass", "warning")
        assert result.strategy_id == "logical_consistency_v1"

    def test_default_strategy_id(self) -> None:
        """Default StrategyConfig gives strategy_id 'logical_consistency_v1'."""
        result = prove(SpecContent(), CodeContent())
        assert result.strategy_id == "logical_consistency_v1"

    def test_custom_strategy_id(self) -> None:
        """Custom StrategyConfig.strategy_id is preserved in result."""
        config = StrategyConfig(strategy_id="my_custom_v2")
        result = prove(SpecContent(), CodeContent(), config=config)
        assert result.strategy_id == "my_custom_v2"

    def test_consistent_spec_code(self) -> None:
        """Consistent spec/code pair → verdict is 'pass' or 'warning'."""
        spec = SpecContent(
            spec_ids=[SpecId("US-23")],
            sections=[
                SpecSection(
                    title="Auth",
                    content="When authentication succeeds, the system must return status 200.",
                )
            ],
        )
        code = CodeContent(
            functions=[
                FunctionNode(
                    node_id="fn_auth",
                    kind="function",
                    contracts=ContractInfo(
                        preconditions=["authentication succeeds"],
                        invariants=[],
                    ),
                    trace_tags=[TraceTag(tag_type="spec", source_id="US-23")],
                )
            ]
        )
        config = _make_default_config()
        result = prove(spec, code, config=config)
        assert result.verdict in ("pass", "warning")
        assert 0.0 <= result.confidence <= 1.0


class TestAdvisoryOnlyConversion:
    """Scenario: advisory_only=True モードで fail が warning に変換される."""

    def test_advisory_only_converts_fail_to_warning(self) -> None:
        """With advisory_only=True, any fail verdict is converted to warning."""
        from unittest.mock import patch

        from lib_logical_consistency_prover import smt_verifier

        # Force a "fail" from SMT verifier
        fail_result = {
            "verdict": "fail",
            "confidence": 1.0,
            "evidence": "Contradiction detected",
            "fp_candidates": [],
        }

        with patch.object(smt_verifier, "verify", return_value=fail_result):
            config = _make_default_config(advisory_only=True)
            result = prove(SpecContent(), CodeContent(), config=config)

        assert result.verdict == "warning", (
            f"Expected 'warning' (advisory_only=True converts fail), got '{result.verdict}'"
        )

    def test_advisory_only_false_preserves_verdict(self) -> None:
        """With advisory_only=False, verdict is not forcibly converted."""
        config = _make_default_config(advisory_only=False)
        result = prove(SpecContent(), CodeContent(), config=config)
        # Empty spec/code → pass or warning, never fail
        assert result.verdict in ("pass", "warning")

    def test_advisory_only_warning_stays_warning(self) -> None:
        """With advisory_only=True and already-warning verdict → still warning."""
        config = _make_default_config(advisory_only=True)
        result = prove(SpecContent(), CodeContent(), config=config)
        assert result.verdict == "warning" or result.verdict == "pass"
        # Specifically with advisory_only, if it was already pass it stays pass?
        # Per spec: advisory_only converts non-fp_candidate to "warning"
        assert result.verdict == "warning"


class TestEvaluationResultFields:
    """Scenario: EvaluationResult の全フィールドが揃っている."""

    def test_all_fields_present(self) -> None:
        """EvaluationResult has all required fields."""
        result = prove(SpecContent(), CodeContent())
        assert hasattr(result, "strategy_id")
        assert hasattr(result, "verdict")
        assert hasattr(result, "confidence")
        assert hasattr(result, "evidence")
        assert hasattr(result, "fp_candidates")

    def test_confidence_is_float(self) -> None:
        """confidence is a float in [0.0, 1.0]."""
        result = prove(SpecContent(), CodeContent())
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_fp_candidates_is_list(self) -> None:
        """fp_candidates is a list."""
        result = prove(SpecContent(), CodeContent())
        assert isinstance(result.fp_candidates, list)

    def test_evidence_is_string(self) -> None:
        """evidence is a non-empty string."""
        result = prove(SpecContent(), CodeContent())
        assert isinstance(result.evidence, str)
        assert len(result.evidence) > 0

    def test_verdict_is_valid(self) -> None:
        """verdict is one of the valid values."""
        result = prove(SpecContent(), CodeContent())
        assert result.verdict in ("pass", "fail", "warning", "fp_candidate")


class TestProveInputValidation:
    """Input validation tests."""

    def test_none_spec_raises(self) -> None:
        """None spec raises ValueError."""
        with pytest.raises(ValueError, match="spec"):
            prove(None, CodeContent())  # type: ignore[arg-type]

    def test_none_code_raises(self) -> None:
        """None code raises ValueError."""
        with pytest.raises(ValueError, match="code"):
            prove(SpecContent(), None)  # type: ignore[arg-type]

    def test_none_config_uses_defaults(self) -> None:
        """None config → default StrategyConfig used (no error)."""
        result = prove(SpecContent(), CodeContent(), config=None)
        assert result is not None
        assert result.strategy_id == "logical_consistency_v1"
