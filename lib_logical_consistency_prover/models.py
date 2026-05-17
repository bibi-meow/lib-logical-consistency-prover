"""lib-logical-consistency-prover — data models.

All input/output types for the logical consistency prover.

Traces: LIB-FR-01, LIB-FR-02, LIB-FR-03, LIB-FR-04
Decision Log: #6-1, #7-1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------


@dataclass
class SpecId:
    """A specification identifier."""

    id_str: str


@dataclass
class SpecSection:
    """A section of a specification document."""

    title: str
    content: str
    level: int = 1


@dataclass
class TraceTag:
    """A traceability tag linking artifacts."""

    tag_type: str
    source_id: str
    target_id: str = ""


@dataclass
class ContractInfo:
    """Contract information for a function (preconditions and invariants)."""

    preconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)


@dataclass
class FunctionNode:
    """A function node in the code graph."""

    node_id: str
    kind: str
    contracts: ContractInfo = field(default_factory=ContractInfo)
    docstring: Optional[str] = None
    trace_tags: List[Any] = field(default_factory=list)


@dataclass
class CallGraph:
    """A call graph representing function relationships."""

    nodes: List[str] = field(default_factory=list)
    edges: List[tuple] = field(default_factory=list)


@dataclass
class SpecContent:
    """Normalized specification content."""

    spec_ids: List[SpecId] = field(default_factory=list)
    sections: List[SpecSection] = field(default_factory=list)
    trace_tags: List[TraceTag] = field(default_factory=list)


@dataclass
class CodeContent:
    """Normalized code content."""

    functions: List[FunctionNode] = field(default_factory=list)
    call_graph: CallGraph = field(default_factory=CallGraph)


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------


@dataclass
class FPCandidate:
    """A false-positive candidate — a spec/code pair that may be incorrectly flagged."""

    spec_id: str
    function_id: str
    reason: str
    confidence: float = 0.5


@dataclass
class EvaluationResult:
    """The result of a logical consistency evaluation.

    Attributes:
        strategy_id: Identifier of the strategy that produced this result.
        verdict: One of "pass", "fail", "warning", "fp_candidate".
            - "pass": all pairs proved consistent (confidence >= 0.95)
            - "fail": contradiction detected (confidence = 1.0)
            - "warning": unproved pairs or degraded mode (confidence = 0.0–0.6)
            - "fp_candidate": potential false positive
        confidence: Float in [0.0, 1.0]. Layer M proved: 0.95+; Layer L only: 0.5–0.8;
            unproved: 0.0.
        evidence: Human-readable summary of proved/unproved pairs and contradiction basis.
        fp_candidates: List of potential false-positive pairs.
    """

    strategy_id: str
    verdict: str  # "pass" | "fail" | "warning" | "fp_candidate"
    confidence: float
    evidence: str
    fp_candidates: List[FPCandidate] = field(default_factory=list)


@dataclass
class StrategyConfig:
    """Configuration for the logical consistency prover strategy."""

    strategy_id: str = "logical_consistency_v1"
    input_types: List[str] = field(default_factory=lambda: ["spec", "code"])
    executor_lib: str = "lib_logical_consistency_prover.prover"
    params: Dict[str, Any] = field(
        default_factory=lambda: {
            "layer_m_smt_solver": "z3",
            "layer_m_bisimulation": True,
            "layer_l_model": "claude-sonnet-4-6",
            "layer_l_confidence_threshold": 0.75,
            "layer_m_timeout_sec": 30,
            "blocking_mode": "auto",
            "advisory_only": False,
        }
    )
    enabled: bool = True
