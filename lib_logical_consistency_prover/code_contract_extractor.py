"""Extract contracts from code artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from lib_logical_consistency_prover.models import CodeContent, NormalizedArtifact


@dataclass
class CodeContract:
    function_id: str
    preconditions: list[str]
    invariants: list[str]
    trace_refs: list[str]
    docstring: str
    kind: str


def extract_code_contracts(artifacts: list[NormalizedArtifact]) -> list[CodeContract]:
    """Extract CodeContracts from a list of code artifacts."""
    contracts: list[CodeContract] = []

    for artifact in artifacts:
        content = artifact.content
        if not isinstance(content, CodeContent):
            continue

        for fn in content.functions:
            trace_refs: list[str] = []
            for tag in fn.trace_tags:
                trace_refs.extend(tag.refs)

            contracts.append(
                CodeContract(
                    function_id=fn.node_id,
                    preconditions=list(fn.contracts.preconditions),
                    invariants=list(fn.contracts.invariants),
                    trace_refs=trace_refs,
                    docstring=fn.docstring,
                    kind=fn.kind,
                )
            )

    return contracts
