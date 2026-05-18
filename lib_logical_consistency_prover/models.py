"""Data models for lib-logical-consistency-prover."""

from __future__ import annotations

from typing import Union

from pydantic import BaseModel


class ArtifactId(BaseModel):
    path: str


class SpecId(BaseModel):
    spec_id: str
    section: str = ""


class TraceTag(BaseModel):
    tag: str
    refs: list[str] = []


class SpecSection(BaseModel):
    heading: str
    content: str
    level: int = 2


class DiagramRef(BaseModel):
    diagram_id: str
    diagram_type: str
    source_format: str
    raw_source: str = ""


class SpecContent(BaseModel):
    spec_ids: list[SpecId] = []
    sections: list[SpecSection] = []
    trace_tags: list[TraceTag] = []
    embedded_diagrams: list[DiagramRef] = []


class ParamInfo(BaseModel):
    name: str
    type_annotation: str = ""


class ContractInfo(BaseModel):
    preconditions: list[str] = []
    invariants: list[str] = []


class SourceRange(BaseModel):
    start_line: int = 0
    end_line: int = 0


class FunctionNode(BaseModel):
    node_id: str
    kind: str
    params: list[ParamInfo] = []
    return_type: str = ""
    contracts: ContractInfo = ContractInfo()
    docstring: str = ""
    trace_tags: list[TraceTag] = []
    source_range: SourceRange = SourceRange()


class CallEdge(BaseModel):
    caller: str
    callee: str


class CallGraph(BaseModel):
    nodes: list[str] = []
    edges: list[CallEdge] = []


class TypeDep(BaseModel):
    source: str
    target: str
    kind: str = "uses"


class CodeContent(BaseModel):
    functions: list[FunctionNode] = []
    call_graph: CallGraph = CallGraph()
    type_deps: list[TypeDep] = []


class NormalizedArtifact(BaseModel):
    artifact_id: ArtifactId
    artifact_type: str
    content: Union[SpecContent, CodeContent]


class StrategyConfig(BaseModel):
    strategy_id: str
    input_types: list[str] = ["spec", "code"]
    executor_lib: str = "lib_logical_consistency_prover"
    params: dict = {}
    enabled: bool = True


class FPOverride(BaseModel):
    rule_id: str
    reason: str = ""


class FPCandidate(BaseModel):
    rule_id: str
    description: str = ""


class EvaluationResult(BaseModel):
    strategy_id: str
    verdict: str  # "pass" | "fail" | "warning" | "fp_candidate"
    confidence: float
    evidence: str  # JSON string
    fp_candidates: list[FPCandidate] = []
