"""spec_logic_extractor — extract logical propositions from SpecContent.

Identifies must/shall/shall not/may not patterns in SpecSection.content
and converts them to {"premise": str, "conclusion": str, "spec_id": str} dicts.

Traces: LIB-FR-01
Decision Log: #5-1, #6-1
"""

from __future__ import annotations

import re
from typing import Dict, List

from lib_logical_consistency_prover.models import SpecContent

# Patterns that signal a logical obligation in spec text.
# Pattern: "When <PREMISE>, the system MUST/SHALL <CONCLUSION>"
# or "If <PREMISE> THEN <CONCLUSION>"
# or standalone "MUST/SHALL <CONCLUSION>"
_WHEN_THEN = re.compile(
    r"[Ww]hen\s+(.+?),\s*(?:the\s+system\s+)?(?:must|shall|should)\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_IF_THEN = re.compile(
    r"[Ii]f\s+(.+?)\s+then\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_SHALL_MUST = re.compile(
    r"(?:the\s+system\s+)?(?:must|shall)\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)


def extract(spec: SpecContent) -> List[Dict[str, str]]:
    """Extract logical propositions from SpecContent sections.

    Scans each SpecSection.content for must/shall/if-then patterns and returns
    a list of {"premise": str, "conclusion": str, "spec_id": str} dicts.

    Args:
        spec: The normalized specification content.

    Returns:
        List of proposition dicts. Empty list if no sections or no patterns found.

    Traces: LIB-FR-01
    """
    results: List[Dict[str, str]] = []

    # Derive a fallback spec_id from spec_ids if available
    default_spec_id = spec.spec_ids[0].id_str if spec.spec_ids else "UNKNOWN"

    for section in spec.sections:
        content = section.content
        spec_id = _find_spec_id(content, spec, default_spec_id)

        # Try "When X, shall/must Y" pattern first (most specific)
        for m in _WHEN_THEN.finditer(content):
            results.append(
                {
                    "premise": m.group(1).strip(),
                    "conclusion": m.group(2).strip(),
                    "spec_id": spec_id,
                }
            )

        # Try "If X then Y"
        for m in _IF_THEN.finditer(content):
            # Only add if not already captured by WHEN_THEN pattern
            premise = m.group(1).strip()
            conclusion = m.group(2).strip()
            if not _already_captured(premise, conclusion, results):
                results.append(
                    {
                        "premise": premise,
                        "conclusion": conclusion,
                        "spec_id": spec_id,
                    }
                )

        # Try standalone "must/shall X" — use empty premise
        for m in _SHALL_MUST.finditer(content):
            conclusion = m.group(1).strip()
            # Skip if the conclusion was already part of a longer match
            if not _already_captured_conclusion(conclusion, results):
                results.append(
                    {
                        "premise": "",
                        "conclusion": conclusion,
                        "spec_id": spec_id,
                    }
                )

    return results


def _find_spec_id(content: str, spec: SpecContent, default: str) -> str:
    """Find the best spec_id for a section by matching trace_tags."""
    for tag in spec.trace_tags:
        if tag.source_id and tag.source_id in content:
            return tag.source_id
    return default


def _already_captured(premise: str, conclusion: str, results: List[Dict[str, str]]) -> bool:
    """Check if this premise/conclusion pair is already in results."""
    for r in results:
        if premise in r["premise"] or r["premise"] in premise:
            if conclusion in r["conclusion"] or r["conclusion"] in conclusion:
                return True
    return False


def _already_captured_conclusion(conclusion: str, results: List[Dict[str, str]]) -> bool:
    """Check if conclusion was already captured as part of a more specific match."""
    for r in results:
        if r["premise"] and (conclusion in r["conclusion"] or r["conclusion"] in conclusion):
            return True
    return False
