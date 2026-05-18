"""Layer L (simulated LLM) prover: deterministic stub."""

from __future__ import annotations

from dataclasses import dataclass, field

from lib_logical_consistency_prover.models import CodeContent, NormalizedArtifact, SpecContent


@dataclass
class LayerLResult:
    proved: list[dict] = field(default_factory=list)
    unproved: list[dict] = field(default_factory=list)
    confidence: float = 0.0


def try_layer_l(
    spec_artifacts: list[NormalizedArtifact],
    code_artifacts: list[NormalizedArtifact],
    params: dict,
) -> LayerLResult:
    """Layer L: simulated LLM evaluation (deterministic stub).

    Since the actual LLM evaluator lib is not yet implemented, this uses a
    deterministic simulation based on trace tag cross-matching.
    """
    # Collect all function trace refs from code
    all_trace_refs: set[str] = set()
    for artifact in code_artifacts:
        if isinstance(artifact.content, CodeContent):
            for fn in artifact.content.functions:
                for tag in fn.trace_tags:
                    all_trace_refs.update(tag.refs)

    # Collect all spec_ids from spec
    all_spec_ids: set[str] = set()
    for artifact in spec_artifacts:
        if isinstance(artifact.content, SpecContent):
            for sid in artifact.content.spec_ids:
                all_spec_ids.add(sid.spec_id)

    proved: list[dict] = []
    unproved: list[dict] = []

    if not all_spec_ids:
        # No explicit spec IDs — evaluate based on section/heading presence
        has_sections = any(
            isinstance(a.content, SpecContent) and len(a.content.sections) > 0
            for a in spec_artifacts
        )
        confidence = 0.5 if has_sections else 0.35
        return LayerLResult(proved=[], unproved=[], confidence=confidence)

    for spec_id in all_spec_ids:
        if spec_id in all_trace_refs:
            proved.append(
                {
                    "spec_id": spec_id,
                    "function": "via_trace_tag",
                    "method": "layer_l_trace",
                    "confidence": 0.75,
                }
            )
        else:
            unproved.append({"spec_id": spec_id, "reason": "no_trace_ref"})

    total = len(proved) + len(unproved)
    confidence = (len(proved) / total * 0.75) if total > 0 else 0.35

    return LayerLResult(proved=proved, unproved=unproved, confidence=confidence)
