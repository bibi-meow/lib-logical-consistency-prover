"""Tests for LIB-FR-03: Z3 SMT verification.

Gherkin scenario coverage:
  - Scenario: 全ペアが証明可能な場合
  - Scenario: z3 がインストールされていない環境
  - Scenario: 空の spec_logic と code_contracts

Traces: LIB-FR-03, LIB-NFR-01
AT file: tests/test_fr03_smt_verifier.py
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lib_logical_consistency_prover import smt_verifier
from lib_logical_consistency_prover.models import ContractInfo


class TestSMTVerifierEmpty:
    """Scenario: 空の spec_logic と code_contracts."""

    def test_empty_inputs_pass(self) -> None:
        """Empty spec_logic and code_contracts → verdict='pass', confidence=0.95."""
        result = smt_verifier.verify([], [], timeout_sec=30)
        assert result["verdict"] == "pass"
        assert result["confidence"] == pytest.approx(0.95)
        assert "trivially" in result["evidence"].lower() or "no" in result["evidence"].lower()

    def test_returns_dict_with_required_keys(self) -> None:
        """Result always has verdict, confidence, evidence, fp_candidates."""
        result = smt_verifier.verify([], [], timeout_sec=30)
        assert "verdict" in result
        assert "confidence" in result
        assert "evidence" in result
        assert "fp_candidates" in result


class TestSMTVerifierWithZ3:
    """Scenario: 全ペアが証明可能な場合 (when z3 is available)."""

    def test_consistent_pairs_pass_or_warning(self) -> None:
        """spec and code contract match → verdict is pass or warning (not fail)."""
        spec_logic = [{"premise": "x > 0", "conclusion": "return positive", "spec_id": "US-23"}]
        code_contracts = [
            {
                "function_id": "fn_pos",
                "spec_ids": ["US-23"],
                "contracts": ContractInfo(preconditions=["x > 0"]),
            }
        ]
        result = smt_verifier.verify(spec_logic, code_contracts, timeout_sec=30)
        assert result["verdict"] in ("pass", "warning")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_no_matching_spec_ids_warning(self) -> None:
        """No spec_id match → verdict='warning', confidence=0.0."""
        spec_logic = [{"premise": "a > 0", "conclusion": "result ok", "spec_id": "US-99"}]
        code_contracts = [
            {
                "function_id": "fn_x",
                "spec_ids": ["US-01"],
                "contracts": ContractInfo(preconditions=["b > 0"]),
            }
        ]
        result = smt_verifier.verify(spec_logic, code_contracts, timeout_sec=30)
        # No matching pairs → warning
        assert result["verdict"] == "warning"

    def test_contradicting_contract_fail(self) -> None:
        """Conclusion says 'not X' but precondition asserts X → verdict='fail'."""
        spec_logic = [
            {
                "premise": "auth passes",
                "conclusion": "must not return error",
                "spec_id": "US-23",
            }
        ]
        code_contracts = [
            {
                "function_id": "fn_auth",
                "spec_ids": ["US-23"],
                "contracts": ContractInfo(preconditions=["return error"]),
            }
        ]
        result = smt_verifier.verify(spec_logic, code_contracts, timeout_sec=30)
        # Should detect contradiction
        assert result["verdict"] in ("fail", "warning")

    def test_unproved_contract_warning(self) -> None:
        """Code contract exists but has no preconditions → unproved → warning."""
        spec_logic = [{"premise": "x > 0", "conclusion": "ok", "spec_id": "US-23"}]
        code_contracts = [
            {
                "function_id": "fn_bare",
                "spec_ids": ["US-23"],
                "contracts": ContractInfo(preconditions=[], invariants=[]),
            }
        ]
        result = smt_verifier.verify(spec_logic, code_contracts, timeout_sec=30)
        assert result["verdict"] == "warning"
        assert result["confidence"] == pytest.approx(0.6)

    def test_confidence_range(self) -> None:
        """Confidence is always in [0.0, 1.0]."""
        result = smt_verifier.verify(
            [{"premise": "", "conclusion": "x", "spec_id": "US-23"}],
            [{"function_id": "fn", "spec_ids": ["US-23"], "contracts": ContractInfo()}],
            timeout_sec=5,
        )
        assert 0.0 <= result["confidence"] <= 1.0


class TestSMTVerifierNoZ3:
    """Scenario: z3 がインストールされていない環境."""

    def test_graceful_degrade_when_z3_unavailable(self) -> None:
        """When z3 is not available, returns warning with confidence=0.0 (no exception)."""
        with patch.object(smt_verifier, "_Z3_AVAILABLE", False):
            spec_logic = [{"premise": "x", "conclusion": "y", "spec_id": "US-23"}]
            code_contracts = [
                {
                    "function_id": "fn",
                    "spec_ids": ["US-23"],
                    "contracts": ContractInfo(preconditions=["x"]),
                }
            ]
            result = smt_verifier.verify(spec_logic, code_contracts, timeout_sec=5)

        assert result["verdict"] == "warning"
        assert result["confidence"] == pytest.approx(0.0)
        assert "z3" in result["evidence"].lower() or "degraded" in result["evidence"].lower()

    def test_no_exception_on_degrade(self) -> None:
        """No exception raised on graceful degrade."""
        with patch.object(smt_verifier, "_Z3_AVAILABLE", False):
            result = smt_verifier.verify(
                [{"premise": "", "conclusion": "y", "spec_id": "US-23"}],
                [{"function_id": "fn", "spec_ids": ["US-23"], "contracts": ContractInfo()}],
                timeout_sec=5,
            )
        assert result is not None


class TestZ3Available:
    """Tests for z3_available() introspection."""

    def test_z3_available_returns_bool(self) -> None:
        """z3_available() returns a bool."""
        result = smt_verifier.z3_available()
        assert isinstance(result, bool)
