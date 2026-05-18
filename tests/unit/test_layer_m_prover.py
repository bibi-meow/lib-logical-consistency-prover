"""Unit tests for layer_m_prover."""

from __future__ import annotations

from lib_logical_consistency_prover.code_contract_extractor import CodeContract
from lib_logical_consistency_prover.layer_m_prover import (
    LayerMResult,
    _extract_keywords,
    _rule_based_proof,
    try_layer_m,
)
from lib_logical_consistency_prover.spec_logic_extractor import SpecLogicItem


def _make_spec_item(spec_id: str = "", heading: str = "", content: str = "") -> SpecLogicItem:
    return SpecLogicItem(spec_id=spec_id, heading=heading, content=content, trace_refs=[])


def _make_contract(
    function_id: str = "mod.func",
    trace_refs: list[str] | None = None,
    docstring: str = "",
) -> CodeContract:
    return CodeContract(
        function_id=function_id,
        preconditions=[],
        invariants=[],
        trace_refs=trace_refs or [],
        docstring=docstring,
        kind="function",
    )


def test_try_layer_m_returns_layer_m_result() -> None:
    spec = [_make_spec_item(spec_id="FR-01")]
    code = [_make_contract(trace_refs=["FR-01"])]
    result = try_layer_m(spec, code, use_smt=False)
    assert isinstance(result, LayerMResult)


def test_empty_spec_returns_zero_confidence() -> None:
    result = try_layer_m([], [_make_contract()], use_smt=False)
    assert result.confidence == 0.0


def test_empty_code_returns_zero_confidence() -> None:
    result = try_layer_m([_make_spec_item(spec_id="FR-01")], [], use_smt=False)
    assert result.confidence == 0.0


def test_trace_ref_match_proves_with_high_confidence() -> None:
    spec = [_make_spec_item(spec_id="FR-01")]
    code = [_make_contract(trace_refs=["FR-01"])]
    result = _rule_based_proof(spec, code)
    assert len(result.proved) == 1
    assert result.proved[0]["method"] == "trace_ref"
    assert result.proved[0]["confidence"] >= 0.88


def test_keyword_match_proves_when_no_trace_ref() -> None:
    spec = [_make_spec_item(heading="validate order", content="Order validation.")]
    code = [_make_contract(function_id="service.validate_order", docstring="Validates order.")]
    result = _rule_based_proof(spec, code)
    proved_methods = [p["method"] for p in result.proved]
    assert "keyword_match" in proved_methods


def test_no_match_adds_to_unproved() -> None:
    spec = [_make_spec_item(spec_id="FR-99", heading="Completely unique heading XYZ")]
    code = [_make_contract(function_id="totally.different.func")]
    result = _rule_based_proof(spec, code)
    assert len(result.unproved) >= 1


def test_confidence_zero_on_no_matches() -> None:
    spec = [_make_spec_item(spec_id="FR-99", heading="ZZZZZ")]
    code = [_make_contract(function_id="abc.def")]
    result = _rule_based_proof(spec, code)
    # No proved pairs → confidence 0
    assert result.confidence == 0.0


def test_extract_keywords_removes_stopwords() -> None:
    kws = _extract_keywords("the system shall validate the order")
    assert "the" not in kws
    assert "shall" not in kws
    assert "validate" in kws
    assert "order" in kws


def test_extract_keywords_minimum_length() -> None:
    kws = _extract_keywords("a or by do validate")
    short = [k for k in kws if len(k) < 3]
    assert short == []


def test_multiple_spec_items_all_processed() -> None:
    spec = [
        _make_spec_item(spec_id="FR-01"),
        _make_spec_item(spec_id="FR-02"),
    ]
    code = [
        _make_contract(trace_refs=["FR-01"]),
        _make_contract(function_id="other.func", trace_refs=["FR-02"]),
    ]
    result = _rule_based_proof(spec, code)
    assert len(result.proved) == 2
