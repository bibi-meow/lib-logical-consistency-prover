"""Extract logical items from spec artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from lib_logical_consistency_prover.models import NormalizedArtifact, SpecContent


@dataclass
class SpecLogicItem:
    spec_id: str
    heading: str
    content: str
    trace_refs: list[str] = field(default_factory=list)


def extract_spec_logic(artifacts: list[NormalizedArtifact]) -> list[SpecLogicItem]:
    """Extract SpecLogicItems from a list of spec artifacts."""
    items: list[SpecLogicItem] = []
    seen_spec_ids: set[str] = set()

    for artifact in artifacts:
        content = artifact.content
        if not isinstance(content, SpecContent):
            continue

        spec_id_set = {s.spec_id for s in content.spec_ids}

        # From sections
        for section in content.sections:
            found_id = _find_spec_id_in_text(section.heading + " " + section.content, spec_id_set)
            item = SpecLogicItem(
                spec_id=found_id,
                heading=section.heading,
                content=section.content,
                trace_refs=[],
            )
            items.append(item)

        # From trace_tags — add refs not already seen as items
        for tag in content.trace_tags:
            for ref in tag.refs:
                if ref not in seen_spec_ids and ref not in {i.spec_id for i in items}:
                    items.append(
                        SpecLogicItem(
                            spec_id=ref,
                            heading=ref,
                            content=tag.tag,
                            trace_refs=list(tag.refs),
                        )
                    )

        # Track all spec IDs from this artifact
        for sid in spec_id_set:
            if sid not in {i.spec_id for i in items}:
                items.append(
                    SpecLogicItem(
                        spec_id=sid,
                        heading=sid,
                        content="",
                        trace_refs=[],
                    )
                )
            seen_spec_ids.add(sid)

    return items


def _find_spec_id_in_text(text: str, known_ids: set[str]) -> str:
    """Return the first known spec ID found in text, or a pattern match."""
    for id_ in known_ids:
        if id_ in text:
            return id_
    m = re.search(r"\b([A-Z]+-\d+|req_\d+)\b", text)
    return m.group(1) if m else ""
