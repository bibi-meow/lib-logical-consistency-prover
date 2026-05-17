"""Tests for LIB-FR-02: code contract extraction.

Gherkin scenario coverage:
  - Scenario: precondition と trace_tag を持つ FunctionNode から contract を抽出する
  - Scenario: contract が空の FunctionNode を処理する

Traces: LIB-FR-02
AT file: tests/test_fr02_contract_matcher.py
"""

from __future__ import annotations

from lib_logical_consistency_prover import contract_matcher
from lib_logical_consistency_prover.models import (
    CodeContent,
    ContractInfo,
    FunctionNode,
    TraceTag,
)


class TestExtractContractsWithPreconditions:
    """Scenario: precondition と trace_tag を持つ FunctionNode から contract を抽出する."""

    def test_basic_extraction(self) -> None:
        """FunctionNode with preconditions and trace_tags → contract entry extracted."""
        fn = FunctionNode(
            node_id="fn_validate",
            kind="function",
            contracts=ContractInfo(preconditions=["x > 0"], invariants=[]),
            trace_tags=[TraceTag(tag_type="spec", source_id="US-23")],
        )
        code = CodeContent(functions=[fn])
        result = contract_matcher.extract_contracts(code)

        assert len(result) == 1
        entry = result[0]
        assert entry["function_id"] == "fn_validate"
        assert "US-23" in entry["spec_ids"]
        assert entry["contracts"].preconditions == ["x > 0"]

    def test_multiple_trace_tags(self) -> None:
        """Multiple trace tags → all spec_ids collected."""
        fn = FunctionNode(
            node_id="fn_multi",
            kind="function",
            contracts=ContractInfo(preconditions=["a != None"]),
            trace_tags=[
                TraceTag(tag_type="spec", source_id="US-23"),
                TraceTag(tag_type="spec", source_id="US-24"),
            ],
        )
        code = CodeContent(functions=[fn])
        result = contract_matcher.extract_contracts(code)

        assert len(result) == 1
        assert "US-23" in result[0]["spec_ids"]
        assert "US-24" in result[0]["spec_ids"]

    def test_invariants_extracted(self) -> None:
        """Invariants are extracted alongside preconditions."""
        fn = FunctionNode(
            node_id="fn_inv",
            kind="function",
            contracts=ContractInfo(
                preconditions=["x > 0"],
                invariants=["result >= 0"],
            ),
            trace_tags=[TraceTag(tag_type="spec", source_id="US-23")],
        )
        code = CodeContent(functions=[fn])
        result = contract_matcher.extract_contracts(code)

        assert result[0]["contracts"].invariants == ["result >= 0"]

    def test_dict_trace_tags(self) -> None:
        """Dict-style trace tags (fallback format) are handled."""
        fn = FunctionNode(
            node_id="fn_dict",
            kind="function",
            contracts=ContractInfo(preconditions=["y > 0"]),
            trace_tags=[{"tag_type": "spec", "source_id": "FR-01"}],
        )
        code = CodeContent(functions=[fn])
        result = contract_matcher.extract_contracts(code)
        assert "FR-01" in result[0]["spec_ids"]


class TestExtractContractsEmpty:
    """Scenario: contract が空の FunctionNode を処理する."""

    def test_empty_contract(self) -> None:
        """FunctionNode with empty ContractInfo → entry with empty contracts."""
        fn = FunctionNode(
            node_id="fn_empty",
            kind="function",
            contracts=ContractInfo(),
            trace_tags=[],
        )
        code = CodeContent(functions=[fn])
        result = contract_matcher.extract_contracts(code)

        assert len(result) == 1
        assert result[0]["spec_ids"] == []
        assert result[0]["contracts"].preconditions == []

    def test_empty_code_content(self) -> None:
        """CodeContent with no functions → empty list."""
        code = CodeContent()
        result = contract_matcher.extract_contracts(code)
        assert result == []

    def test_multiple_functions(self) -> None:
        """Multiple functions → one entry per function."""
        code = CodeContent(
            functions=[
                FunctionNode(
                    node_id="f1",
                    kind="function",
                    contracts=ContractInfo(preconditions=["a > 0"]),
                    trace_tags=[TraceTag(tag_type="spec", source_id="US-23")],
                ),
                FunctionNode(
                    node_id="f2",
                    kind="function",
                    contracts=ContractInfo(),
                    trace_tags=[],
                ),
            ]
        )
        result = contract_matcher.extract_contracts(code)
        assert len(result) == 2
        assert result[0]["function_id"] == "f1"
        assert result[1]["function_id"] == "f2"


class TestMatchPairs:
    """Tests for the match_pairs helper."""

    def test_matching_by_spec_id(self) -> None:
        """Pairs are matched by spec_id."""
        spec_logic = [{"premise": "x > 0", "conclusion": "return positive", "spec_id": "US-23"}]
        code_contracts = [
            {
                "function_id": "fn_pos",
                "spec_ids": ["US-23"],
                "contracts": ContractInfo(preconditions=["x > 0"]),
            }
        ]
        pairs = contract_matcher.match_pairs(spec_logic, code_contracts)
        assert len(pairs) == 1
        assert pairs[0]["spec_proposition"]["spec_id"] == "US-23"

    def test_no_matching_ids(self) -> None:
        """No matching spec_ids → empty pairs list."""
        spec_logic = [{"premise": "", "conclusion": "x", "spec_id": "US-99"}]
        code_contracts = [
            {
                "function_id": "fn_x",
                "spec_ids": ["US-01"],
                "contracts": ContractInfo(),
            }
        ]
        pairs = contract_matcher.match_pairs(spec_logic, code_contracts)
        assert pairs == []
