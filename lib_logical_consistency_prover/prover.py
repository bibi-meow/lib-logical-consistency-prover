"""prover — main entry point for logical consistency verification.

Orchestrates the full verification pipeline:
  1. Extract spec logic from SpecContent (LIB-FR-01)
  2. Extract code contracts from CodeContent (LIB-FR-02)
  3. Verify with Z3 SMT (Layer M) or fall back to Layer L stub (LIB-FR-03)
  4. Assemble EvaluationResult (LIB-FR-04)
  5. Apply advisory_only conversion (LIB-NFR-02)

Traces: LIB-FR-01, LIB-FR-02, LIB-FR-03, LIB-FR-04, LIB-NFR-01, LIB-NFR-02
Decision Log: #7-1
"""

from __future__ import annotations

from lib_logical_consistency_prover import contract_matcher as _cm
from lib_logical_consistency_prover import layer_l_stub as _layer_l
from lib_logical_consistency_prover import smt_verifier as _smt
from lib_logical_consistency_prover import spec_logic_extractor as _sle
from lib_logical_consistency_prover.models import (
    CodeContent,
    EvaluationResult,
    FPCandidate,
    SpecContent,
    StrategyConfig,
)


def prove(
    spec: SpecContent,
    code: CodeContent,
    config: StrategyConfig | None = None,
) -> EvaluationResult:
    """Prove logical consistency between spec and code.

    Implements the Layer M → Layer L fallback pipeline as defined in
    docs/07-spec.md §Pseudocode.

    Args:
        spec: Normalized specification content.
        code: Normalized code content.
        config: Strategy configuration. If None, uses default StrategyConfig.

    Returns:
        EvaluationResult with verdict, confidence, evidence, and fp_candidates.

    Raises:
        ValueError: If spec or code is None.

    Traces: LIB-FR-01, LIB-FR-02, LIB-FR-03, LIB-FR-04, LIB-NFR-01, LIB-NFR-02
    Decision Log: #7-1
    """
    # Step 1: Input validation
    if spec is None:
        raise ValueError("spec must not be None")
    if code is None:
        raise ValueError("code must not be None")

    # Step 2: Default config
    if config is None:
        config = StrategyConfig()

    params = config.params
    timeout_sec = int(params.get("layer_m_timeout_sec", 30))
    advisory_only = bool(params.get("advisory_only", False))

    # Step 3: Extract spec logic (LIB-FR-01)
    spec_logic = _sle.extract(spec)

    # Step 4: Extract code contracts (LIB-FR-02)
    code_contracts = _cm.extract_contracts(code)

    # Step 5: Layer M — Z3 SMT verification (LIB-FR-03)
    try:
        smt_out = _smt.verify(spec_logic, code_contracts, timeout_sec=timeout_sec)
    except Exception:  # noqa: BLE001
        # Any unexpected error in Layer M → fall back to Layer L
        smt_out = _layer_l.evaluate(spec_logic, code_contracts)

    # If Layer M degraded, use Layer L stub for evidence enhancement
    if smt_out.get("confidence", 0.0) == 0.0 and smt_out.get("verdict") == "warning":
        layer_l_out = _layer_l.evaluate(spec_logic, code_contracts)
        # Merge evidence
        combined_evidence = smt_out["evidence"] + " | " + layer_l_out["evidence"]
        smt_out = {
            "verdict": "warning",
            "confidence": 0.0,
            "evidence": combined_evidence,
            "fp_candidates": smt_out.get("fp_candidates", [])
            + layer_l_out.get("fp_candidates", []),
        }

    # Step 6: Assemble EvaluationResult (LIB-FR-04)
    result = _assemble_result(smt_out, config)

    # Step 7: advisory_only conversion (LIB-NFR-02)
    if advisory_only and result.verdict != "fp_candidate":
        result.verdict = "warning"

    return result


def _assemble_result(smt_out: dict, config: StrategyConfig) -> EvaluationResult:  # type: ignore[type-arg]
    """Assemble an EvaluationResult from SMT output.

    Decision Log: #7-1
    """
    fp_candidates = [
        FPCandidate(
            spec_id=fp.get("spec_id", ""),
            function_id=fp.get("function_id", ""),
            reason=fp.get("reason", ""),
            confidence=fp.get("confidence", 0.5),
        )
        for fp in smt_out.get("fp_candidates", [])
    ]

    return EvaluationResult(
        strategy_id=config.strategy_id,
        verdict=smt_out["verdict"],
        confidence=smt_out["confidence"],
        evidence=smt_out["evidence"],
        fp_candidates=fp_candidates,
    )
