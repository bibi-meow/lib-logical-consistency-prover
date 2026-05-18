"""Build evidence JSON for EvaluationResult."""

from __future__ import annotations

import json


def build_evidence(
    layer: str,
    proved: list[dict],
    unproved: list[dict],
    contradictions: list[dict] | None = None,
) -> str:
    """Return a JSON string with proof details.

    Args:
        layer: "M", "L", or "none"
        proved: list of proved pair dicts
        unproved: list of unproved pair dicts
        contradictions: optional list of contradiction dicts

    Returns:
        JSON string conforming to the evidence schema.
    """
    total = len(proved) + len(unproved)
    summary = (
        f"{len(proved)}/{total} spec-code pairs proved via Layer {layer}"
        if layer != "none"
        else "No proof attempted — missing spec or code artifacts"
    )

    payload = {
        "layer": layer,
        "proved_pairs": proved,
        "unproved_pairs": unproved,
        "contradictions": contradictions or [],
        "summary": summary,
    }
    return json.dumps(payload, ensure_ascii=False)
