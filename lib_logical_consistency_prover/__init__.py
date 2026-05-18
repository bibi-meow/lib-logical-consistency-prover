"""lib-logical-consistency-prover: proves logical consistency between specs and code."""

from lib_logical_consistency_prover.executor import execute
from lib_logical_consistency_prover.models import (
    ArtifactId,
    CallEdge,
    CallGraph,
    CodeContent,
    ContractInfo,
    DiagramRef,
    EvaluationResult,
    FPCandidate,
    FPOverride,
    FunctionNode,
    NormalizedArtifact,
    ParamInfo,
    SourceRange,
    SpecContent,
    SpecId,
    SpecSection,
    StrategyConfig,
    TraceTag,
    TypeDep,
)

__all__ = [
    "execute",
    "NormalizedArtifact",
    "StrategyConfig",
    "EvaluationResult",
    "SpecContent",
    "CodeContent",
    "FunctionNode",
    "CallGraph",
    "CallEdge",
    "TypeDep",
    "ArtifactId",
    "FPOverride",
    "FPCandidate",
    "ContractInfo",
    "ParamInfo",
    "SpecId",
    "TraceTag",
    "SpecSection",
    "DiagramRef",
    "SourceRange",
]
__version__ = "0.1.0"
