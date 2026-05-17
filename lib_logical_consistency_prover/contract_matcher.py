"""contract_matcher — extract code contracts and match to spec IDs.

Reads FunctionNode.contracts (ContractInfo) and FunctionNode.trace_tags to build
a list of {"function_id": str, "spec_ids": List[str], "contracts": ContractInfo} dicts.

Traces: LIB-FR-02
Decision Log: #6-1
"""

from __future__ import annotations

from typing import Any, Dict, List

from lib_logical_consistency_prover.models import CodeContent, ContractInfo


def extract_contracts(code: CodeContent) -> List[Dict[str, Any]]:
    """Extract contract information from FunctionNode list.

    For each FunctionNode in code.functions, extracts its ContractInfo and
    resolves spec_ids from trace_tags.

    Args:
        code: The normalized code content.

    Returns:
        List of dicts with keys:
            "function_id" (str): the node_id of the function
            "spec_ids" (List[str]): spec IDs from trace_tags
            "contracts" (ContractInfo): the extracted contract

    Traces: LIB-FR-02
    """
    results: List[Dict[str, Any]] = []

    for fn in code.functions:
        spec_ids = _extract_spec_ids(fn.trace_tags)
        results.append(
            {
                "function_id": fn.node_id,
                "spec_ids": spec_ids,
                "contracts": fn.contracts,
            }
        )

    return results


def _extract_spec_ids(trace_tags: List[Any]) -> List[str]:
    """Extract spec IDs from a list of trace tags.

    Handles TraceTag dataclass objects and plain dicts.

    Args:
        trace_tags: List of TraceTag objects or dicts.

    Returns:
        List of spec ID strings (source_id values from trace tags).
    """
    ids: List[str] = []
    for tag in trace_tags:
        if hasattr(tag, "source_id") and tag.source_id:
            ids.append(tag.source_id)
        elif isinstance(tag, dict) and tag.get("source_id"):
            ids.append(tag["source_id"])
    return ids


def match_pairs(
    spec_logic: List[Dict[str, str]],
    code_contracts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build matched (spec_proposition, code_contract) pairs for SMT verification.

    Matches spec logic entries to code contracts by spec_id.

    Args:
        spec_logic: Output of spec_logic_extractor.extract()
        code_contracts: Output of extract_contracts()

    Returns:
        List of dicts with:
            "spec_proposition" (Dict): the spec logic entry
            "code_contract" (Dict): the matching code contract entry
    """
    pairs: List[Dict[str, Any]] = []

    for prop in spec_logic:
        spec_id = prop.get("spec_id", "")
        for contract in code_contracts:
            if spec_id in contract["spec_ids"]:
                pairs.append(
                    {
                        "spec_proposition": prop,
                        "code_contract": contract,
                    }
                )

    return pairs


def build_empty_contract() -> ContractInfo:
    """Build an empty ContractInfo (utility helper)."""
    return ContractInfo()
