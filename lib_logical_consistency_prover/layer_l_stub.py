"""layer_l_stub — Layer L (LLM) stub implementation.

Provides a deterministic stub for the optional LLM evaluation layer.
Returns verdict="warning", confidence=0.5 without making any LLM calls.

This stub allows the lib to function in environments without LLM access.
To enable actual LLM evaluation, replace this module with a concrete
implementation that calls your LLM provider.

Traces: LIB-NFR-01
Decision Log: #5-3
"""

from __future__ import annotations

from typing import Any, Dict, List


def evaluate(
    spec_logic: List[Dict[str, str]],
    code_contracts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate logical consistency using Layer L (LLM stub).

    This stub implementation does not call any LLM. It returns a conservative
    "warning" verdict indicating that human review is recommended.

    Args:
        spec_logic: List of spec proposition dicts from spec_logic_extractor.
        code_contracts: List of contract dicts from contract_matcher.

    Returns:
        Dict with verdict="warning", confidence=0.5, and explanatory evidence.

    Traces: LIB-NFR-01
    Decision Log: #5-3
    """
    pair_count = min(len(spec_logic), len(code_contracts))

    return {
        "verdict": "warning",
        "confidence": 0.5,
        "evidence": (
            f"Layer L stub: {pair_count} pair(s) evaluated. "
            "LLM evaluation not performed — stub returns advisory warning. "
            "Install and configure an LLM provider for full Layer L evaluation."
        ),
        "fp_candidates": [],
    }
