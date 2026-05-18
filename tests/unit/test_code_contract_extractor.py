"""Unit tests for code_contract_extractor."""

from __future__ import annotations

from lib_logical_consistency_prover.code_contract_extractor import (
    CodeContract,
    extract_code_contracts,
)
from lib_logical_consistency_prover.models import (
    ArtifactId,
    CallGraph,
    CodeContent,
    ContractInfo,
    FunctionNode,
    NormalizedArtifact,
    SpecContent,
    TraceTag,
)


def _code_artifact(content: CodeContent) -> NormalizedArtifact:
    return NormalizedArtifact(
        artifact_id=ArtifactId(path="code.py"),
        artifact_type="code",
        content=content,
    )


def test_extract_returns_list_of_contracts() -> None:
    artifact = _code_artifact(
        CodeContent(
            functions=[
                FunctionNode(node_id="mod.func", kind="function"),
            ],
            call_graph=CallGraph(),
        )
    )
    result = extract_code_contracts([artifact])
    assert isinstance(result, list)
    assert all(isinstance(c, CodeContract) for c in result)


def test_function_id_is_node_id() -> None:
    artifact = _code_artifact(
        CodeContent(
            functions=[FunctionNode(node_id="service.do_thing", kind="method")],
            call_graph=CallGraph(),
        )
    )
    result = extract_code_contracts([artifact])
    assert result[0].function_id == "service.do_thing"


def test_trace_refs_extracted_from_trace_tags() -> None:
    artifact = _code_artifact(
        CodeContent(
            functions=[
                FunctionNode(
                    node_id="mod.func",
                    kind="function",
                    trace_tags=[TraceTag(tag="Traces", refs=["FR-01", "US-22"])],
                )
            ],
            call_graph=CallGraph(),
        )
    )
    result = extract_code_contracts([artifact])
    assert "FR-01" in result[0].trace_refs
    assert "US-22" in result[0].trace_refs


def test_preconditions_extracted() -> None:
    artifact = _code_artifact(
        CodeContent(
            functions=[
                FunctionNode(
                    node_id="mod.func",
                    kind="function",
                    contracts=ContractInfo(preconditions=["x > 0", "y is not None"]),
                )
            ],
            call_graph=CallGraph(),
        )
    )
    result = extract_code_contracts([artifact])
    assert result[0].preconditions == ["x > 0", "y is not None"]


def test_empty_code_returns_empty() -> None:
    artifact = _code_artifact(CodeContent())
    result = extract_code_contracts([artifact])
    assert result == []


def test_non_code_artifact_skipped() -> None:
    artifact = NormalizedArtifact(
        artifact_id=ArtifactId(path="spec.md"),
        artifact_type="spec",
        content=SpecContent(),
    )
    result = extract_code_contracts([artifact])
    assert result == []


def test_multiple_functions_extracted() -> None:
    artifact = _code_artifact(
        CodeContent(
            functions=[
                FunctionNode(node_id="mod.func1", kind="function"),
                FunctionNode(node_id="mod.func2", kind="function"),
                FunctionNode(node_id="mod.func3", kind="method"),
            ],
            call_graph=CallGraph(),
        )
    )
    result = extract_code_contracts([artifact])
    assert len(result) == 3


def test_multiple_artifacts_combined() -> None:
    a1 = _code_artifact(
        CodeContent(
            functions=[FunctionNode(node_id="a.func1", kind="function")],
            call_graph=CallGraph(),
        )
    )
    a2 = _code_artifact(
        CodeContent(
            functions=[FunctionNode(node_id="b.func2", kind="function")],
            call_graph=CallGraph(),
        )
    )
    result = extract_code_contracts([a1, a2])
    ids = [c.function_id for c in result]
    assert "a.func1" in ids
    assert "b.func2" in ids
