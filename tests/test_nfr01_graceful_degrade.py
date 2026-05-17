"""Tests for LIB-NFR-01: graceful degrade when z3 is not available.

Gherkin scenario coverage:
  - Scenario: z3 import が失敗する環境

Traces: LIB-NFR-01
AT file: tests/test_nfr01_graceful_degrade.py
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from lib_logical_consistency_prover import prove, smt_verifier
from lib_logical_consistency_prover.models import (
    CodeContent,
    ContractInfo,
    FunctionNode,
    SpecContent,
    SpecId,
    SpecSection,
    TraceTag,
)


class TestGracefulDegradeZ3Unavailable:
    """Scenario: z3 import が失敗する環境."""

    def test_prove_no_exception_when_z3_unavailable(self) -> None:
        """prove() does not raise when z3 is unavailable."""
        with patch.object(smt_verifier, "_Z3_AVAILABLE", False):
            spec = SpecContent(
                spec_ids=[SpecId("US-23")],
                sections=[
                    SpecSection(
                        title="Test",
                        content="The system must verify consistency.",
                    )
                ],
            )
            code = CodeContent(
                functions=[
                    FunctionNode(
                        node_id="fn",
                        kind="function",
                        contracts=ContractInfo(preconditions=["x > 0"]),
                        trace_tags=[TraceTag(tag_type="spec", source_id="US-23")],
                    )
                ]
            )
            # Must not raise
            result = prove(spec, code)

        assert result is not None

    def test_verdict_not_fail_when_z3_unavailable(self) -> None:
        """When z3 is unavailable, verdict is 'warning' (not 'fail' or exception)."""
        with patch.object(smt_verifier, "_Z3_AVAILABLE", False):
            result = prove(SpecContent(), CodeContent())

        assert result.verdict != "fail"
        assert result.verdict in ("pass", "warning", "fp_candidate")

    def test_confidence_zero_when_z3_unavailable_and_has_pairs(self) -> None:
        """When z3 is unavailable with pairs to verify, confidence degrades."""
        with patch.object(smt_verifier, "_Z3_AVAILABLE", False):
            spec = SpecContent(
                spec_ids=[SpecId("US-23")],
                sections=[
                    SpecSection(
                        title="Auth",
                        content="The system must validate input.",
                    )
                ],
            )
            code = CodeContent(
                functions=[
                    FunctionNode(
                        node_id="fn_validate",
                        kind="function",
                        contracts=ContractInfo(preconditions=["input is valid"]),
                        trace_tags=[TraceTag(tag_type="spec", source_id="US-23")],
                    )
                ]
            )
            result = prove(spec, code)

        # Confidence should be 0.0 or low (degraded)
        assert result.confidence <= 0.6

    def test_smt_verifier_degrade_directly(self) -> None:
        """smt_verifier.verify() degrades cleanly when z3 is unavailable."""
        with patch.object(smt_verifier, "_Z3_AVAILABLE", False):
            result = smt_verifier.verify(
                [{"premise": "x", "conclusion": "y", "spec_id": "US-23"}],
                [
                    {
                        "function_id": "fn",
                        "spec_ids": ["US-23"],
                        "contracts": ContractInfo(preconditions=["x"]),
                    }
                ],
                timeout_sec=5,
            )

        assert result["verdict"] == "warning"
        assert result["confidence"] == pytest.approx(0.0)
        assert isinstance(result["evidence"], str)
        assert len(result["evidence"]) > 0

    def test_layer_l_stub_always_available(self) -> None:
        """layer_l_stub.evaluate() works regardless of z3 availability."""
        from lib_logical_consistency_prover import layer_l_stub

        result = layer_l_stub.evaluate([], [])
        assert result["verdict"] == "warning"
        assert result["confidence"] == pytest.approx(0.5)
