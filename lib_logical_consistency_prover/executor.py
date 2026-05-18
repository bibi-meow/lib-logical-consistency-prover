"""Main executor: orchestrates Layer M and Layer L proof attempts."""

from __future__ import annotations

from lib_logical_consistency_prover.code_contract_extractor import extract_code_contracts
from lib_logical_consistency_prover.evidence_builder import build_evidence
from lib_logical_consistency_prover.layer_l_prover import try_layer_l
from lib_logical_consistency_prover.layer_m_prover import try_layer_m
from lib_logical_consistency_prover.models import (
    EvaluationResult,
    FPOverride,
    NormalizedArtifact,
    StrategyConfig,
)
from lib_logical_consistency_prover.spec_logic_extractor import extract_spec_logic


def execute(
    config: StrategyConfig,
    artifacts: list[NormalizedArtifact],
    fp_overrides: list[FPOverride] | None = None,
) -> EvaluationResult:
    """Prove logical consistency between spec and code artifacts.

    Strategy:
    1. Attempt Layer M (deterministic/SMT) proof.
    2. If Layer M confidence < 0.9, fall back to Layer L (simulated LLM).
    3. Map confidence → verdict.

    Args:
        config: StrategyConfig with params.
        artifacts: mix of spec and code NormalizedArtifacts.
        fp_overrides: optional false-positive overrides (currently unused).

    Returns:
        EvaluationResult with verdict, confidence, and evidence JSON.
    """
    if not config.enabled:
        return EvaluationResult(
            strategy_id=config.strategy_id,
            verdict="pass",
            confidence=1.0,
            evidence=build_evidence("none", [], [], []),
        )

    spec_artifacts = [a for a in artifacts if a.artifact_type == "spec"]
    code_artifacts = [a for a in artifacts if a.artifact_type == "code"]

    if not spec_artifacts or not code_artifacts:
        return EvaluationResult(
            strategy_id=config.strategy_id,
            verdict="warning",
            confidence=0.0,
            evidence=build_evidence("none", [], []),
        )

    params = config.params
    use_smt = params.get("layer_m_smt_solver", "z3") == "z3"
    advisory_only = bool(params.get("advisory_only", False))

    # Extract intermediate representations
    spec_logic = extract_spec_logic(spec_artifacts)
    code_contracts = extract_code_contracts(code_artifacts)

    # Attempt Layer M
    layer_m_result = try_layer_m(spec_logic, code_contracts, use_smt)

    # Use Layer M result if it fully proved all items (no unproved) OR confidence >= 0.9
    layer_m_sufficient = layer_m_result.confidence >= 0.9 or (
        layer_m_result.proved and not layer_m_result.unproved
    )

    if layer_m_sufficient:
        layer = "M"
        proved = layer_m_result.proved
        unproved = layer_m_result.unproved
        confidence = layer_m_result.confidence
    else:
        # Fall back to Layer L
        layer_l_result = try_layer_l(spec_artifacts, code_artifacts, params)
        layer = "L"
        proved = layer_l_result.proved
        unproved = layer_l_result.unproved
        confidence = layer_l_result.confidence

    # Determine verdict from confidence
    if confidence >= 0.9:
        verdict = "pass"
    elif confidence >= 0.6:
        verdict = "warning"
    else:
        verdict = "warning" if advisory_only else "fail"

    evidence = build_evidence(layer, proved, unproved)

    return EvaluationResult(
        strategy_id=config.strategy_id,
        verdict=verdict,
        confidence=confidence,
        evidence=evidence,
    )
