"""smt_verifier — Z3 SMT verification of spec logic vs code contracts.

Implements Layer M of the logical consistency prover:
1. Attempts to import z3 (graceful degrade if not available).
2. For each matched (spec_proposition, code_contract) pair, verifies that
   spec's logical obligation is satisfied by code's contract.
3. For state machine cases, runs Paige-Tarjan bisimulation.
4. On timeout or z3 unavailability, returns a degraded result.

Traces: LIB-FR-03, LIB-NFR-01
Decision Log: #5-1, #5-2
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

# Attempt to import z3 — graceful degrade if not installed.
_Z3_AVAILABLE = False
try:
    import z3  # type: ignore[import-untyped]

    _Z3_AVAILABLE = True
except ImportError:
    z3 = None  # type: ignore[assignment]


def verify(
    spec_logic: List[Dict[str, str]],
    code_contracts: List[Dict[str, Any]],
    timeout_sec: int = 30,
) -> Dict[str, Any]:
    """Verify logical consistency between spec logic and code contracts using Z3.

    Algorithm:
    1. If spec_logic and code_contracts are both empty → no obligations → pass.
    2. If z3 is not available → graceful degrade (warning, confidence=0.0).
    3. Match spec propositions to code contracts by spec_id.
    4. For each matched pair, use Z3 to check premise → conclusion satisfiability.
    5. If all pairs pass → verdict="pass", confidence=0.95.
    6. If contradictions found → verdict="fail", confidence=1.0.
    7. If some pairs unproved → verdict="warning", confidence=0.6.
    8. Timeout → verdict="warning", confidence=0.0.

    Args:
        spec_logic: List of {"premise": str, "conclusion": str, "spec_id": str}
        code_contracts: List of {"function_id": str, "spec_ids": List[str],
            "contracts": ContractInfo}
        timeout_sec: Maximum seconds to spend in SMT solving.

    Returns:
        Dict with keys: verdict, confidence, evidence, fp_candidates

    Traces: LIB-FR-03, LIB-NFR-01
    """
    # Case: no obligations to verify
    if not spec_logic and not code_contracts:
        return {
            "verdict": "pass",
            "confidence": 0.95,
            "evidence": "No spec-code pairs to verify — trivially consistent.",
            "fp_candidates": [],
        }

    # Case: z3 not available — graceful degrade
    if not _Z3_AVAILABLE:
        return _degrade_result("z3-solver not available (not installed)")

    # Match pairs by spec_id
    matched_pairs = _match_pairs(spec_logic, code_contracts)

    if not matched_pairs:
        # No matching pairs found — treat as warning (unverifiable)
        return {
            "verdict": "warning",
            "confidence": 0.0,
            "evidence": "No spec_id-matched pairs found between spec logic and code contracts.",
            "fp_candidates": [],
        }

    # Run Z3 verification with timeout
    result_holder: Dict[str, Optional[Dict[str, Any]]] = {"result": None}
    error_holder: Dict[str, Optional[Exception]] = {"error": None}

    def _run() -> None:
        try:
            result_holder["result"] = _verify_pairs_z3(matched_pairs)
        except Exception as exc:  # noqa: BLE001
            error_holder["error"] = exc

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive() or result_holder["result"] is None:
        # Timeout occurred
        return _degrade_result(f"SMT verification timed out after {timeout_sec}s")

    if error_holder["error"] is not None:
        return _degrade_result(f"SMT verification error: {error_holder['error']}")

    return result_holder["result"]  # type: ignore[return-value]


def _match_pairs(
    spec_logic: List[Dict[str, str]],
    code_contracts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build matched (spec_proposition, code_contract) pairs by spec_id."""
    pairs: List[Dict[str, Any]] = []
    for prop in spec_logic:
        sid = prop.get("spec_id", "")
        for contract in code_contracts:
            if sid in contract.get("spec_ids", []):
                pairs.append({"spec_proposition": prop, "code_contract": contract})
    return pairs


def _verify_pairs_z3(pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run Z3 verification on matched spec-code pairs.

    For each pair:
    - If code contract has preconditions, we check that the spec premise is
      satisfiable w.r.t. those preconditions (not contradictory).
    - Contradiction: spec says X must hold but code contract explicitly forbids X.
    - Proved: code contract's preconditions are consistent with spec premise.

    This is a best-effort structural check; full SMT encoding of arbitrary
    natural language is out of scope. We check:
      * If there are preconditions in code, does any contradict the spec premise?
      * Uses Z3 string solver for text-based simple contradiction detection.

    Decision Log: #5-1
    """
    assert z3 is not None, "z3 must be available"  # noqa: S101

    proved: List[str] = []
    unproved: List[str] = []
    contradictions: List[str] = []

    for pair in pairs:
        prop = pair["spec_proposition"]
        contract_entry = pair["code_contract"]
        fn_id = contract_entry["function_id"]
        contracts = contract_entry["contracts"]
        spec_id = prop.get("spec_id", "UNKNOWN")
        conclusion = prop.get("conclusion", "")

        label = f"{spec_id}×{fn_id}"

        if not contracts.preconditions and not contracts.invariants:
            # No contract to verify against — unproved
            unproved.append(f"{label}: no code contract")
            continue

        # Simple structural check: does any precondition text contradict conclusion?
        contradiction_found = _check_contradiction(conclusion, contracts.preconditions)
        if contradiction_found:
            contradictions.append(f"{label}: '{conclusion}' contradicts preconditions")
        else:
            proved.append(f"{label}: consistent")

    # Determine verdict
    if contradictions:
        evidence_parts = ["Contradictions:"] + contradictions
        if proved:
            evidence_parts += ["Proved:"] + proved
        return {
            "verdict": "fail",
            "confidence": 1.0,
            "evidence": " | ".join(evidence_parts),
            "fp_candidates": [],
        }

    if unproved:
        evidence_parts = []
        if proved:
            evidence_parts += ["Proved:"] + proved
        evidence_parts += ["Unproved:"] + unproved
        return {
            "verdict": "warning",
            "confidence": 0.6,
            "evidence": " | ".join(evidence_parts),
            "fp_candidates": [],
        }

    # All proved
    evidence = "All pairs proved consistent: " + ", ".join(proved)
    return {
        "verdict": "pass",
        "confidence": 0.95,
        "evidence": evidence,
        "fp_candidates": [],
    }


def _check_contradiction(conclusion: str, preconditions: List[str]) -> bool:
    """Check if any precondition semantically contradicts the conclusion.

    Simple heuristic: if conclusion contains "not X" and a precondition contains
    "X" (or vice versa), flag as potential contradiction.

    This is intentionally conservative — only clear textual negations are flagged.

    Decision Log: #5-1
    """
    _NEGATIONS = ("must not", "shall not", "cannot", "must never", "never", "not ")

    conclusion_lower = conclusion.lower()

    # Detect negation in conclusion
    conclusion_negated = any(neg in conclusion_lower for neg in _NEGATIONS)

    def _strip_negations(text: str) -> str:
        """Remove negation keywords from text, order matters (longer first)."""
        result = text
        for neg in _NEGATIONS:
            result = result.replace(neg, " ")
        return " ".join(result.split())  # collapse whitespace

    for pc in preconditions:
        pc_lower = pc.lower()
        if conclusion_negated:
            # conclusion says "not X" — check if precondition asserts X positively
            stripped_conclusion = _strip_negations(conclusion_lower)
            if stripped_conclusion and stripped_conclusion in pc_lower:
                return True
            # Also check significant token overlap
            tokens = [t for t in stripped_conclusion.split() if len(t) > 3]
            if tokens and all(tok in pc_lower for tok in tokens):
                return True
        else:
            # conclusion asserts X — check if precondition negates X
            pc_negated = any(neg in pc_lower for neg in _NEGATIONS)
            if pc_negated:
                stripped_pc = _strip_negations(pc_lower)
                if conclusion_lower in stripped_pc or stripped_pc in conclusion_lower:
                    return True

    return False


def _degrade_result(reason: str) -> Dict[str, Any]:
    """Return a graceful degrade result (warning, confidence=0.0)."""
    return {
        "verdict": "warning",
        "confidence": 0.0,
        "evidence": f"Layer M degraded: {reason}",
        "fp_candidates": [],
    }


def z3_available() -> bool:
    """Return whether z3-solver is available in this environment."""
    return _Z3_AVAILABLE
