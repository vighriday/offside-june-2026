"""Curated evidence — the unconditional click-to-source guarantee (Layer 3).

THE SPLIT only ever cites a small, fixed set of Law passages. Rather than depend on a
full-document Docling pass succeeding for every page, we freeze exactly those cited
passages into a small, human-verified ``curated_evidence.json``. Each record is seeded
from Docling's own provenance (page number + extracted text) on the page range that
contains it, then confirmed by a human against the rendered page image.

The web click handler resolves a cell's ``citation_ids`` to these records and renders
the page image with the passage highlighted — so click-to-source works for the demo
incidents regardless of any full-document extraction quirk.

This module builds and validates the curated set; the actual page numbers and verbatim
text are confirmed during the bake (see ``scripts``/notebook) and frozen to
``data/docling/curated_evidence.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

from offside_engine.analyze.split_schema import Citation

# The cited Law passages, with page anchors confirmed by Docling extraction against the
# IFAB 2025/26 single-pages edition. Verbatim text is filled from the extracted page
# during the bake and human-verified inside the rendered page image before freezing.
CURATED_ANCHORS: list[dict] = [
    {
        "id": "ifab-law11-offside-p103",
        "law": "Law 11",
        "page": 103,
        "topic": "offside position definition",
        "applies_to_incidents": ["lampard-ghost-goal"],
        "seed_text": (
            "A player is in an offside position if: any part of the head, body or feet is "
            "in the opponents' half (excluding the halfway line) and any part of the head, "
            "body or feet is nearer to the opponents' goal line than both the ball and the "
            "second-last opponent."
        ),
    },
    {
        "id": "ifab-law12-dogso-handball-p118",
        "law": "Law 12",
        "page": 118,
        "topic": "denying a goal by deliberate handball (DOGSO)",
        "applies_to_incidents": ["hand-of-god", "suarez-handball"],
        "seed_text": (
            "Where a player denies the opposing team a goal or an obvious goal-scoring "
            "opportunity by committing a deliberate handball offence the player is sent off "
            "whatever the position of the offence."
        ),
    },
]


def build_curated_citations() -> list[Citation]:
    """Build typed Citations from the confirmed anchors (source-doc: IFAB 2025/26)."""
    return [
        Citation(
            id=a["id"],
            source_doc="ifab-laws-2025-26",
            doc_kind="IFAB_LAW",
            page=a["page"],
            extracted_text=a["seed_text"],
        )
        for a in CURATED_ANCHORS
    ]


def save_curated_evidence(out_path: Path) -> Path:
    """Write the curated evidence index (id -> citation + applies_to_incidents)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {}
    for anchor, cite in zip(CURATED_ANCHORS, build_curated_citations()):
        record = cite.model_dump(mode="json")
        record["law"] = anchor["law"]
        record["topic"] = anchor["topic"]
        record["applies_to_incidents"] = anchor["applies_to_incidents"]
        payload[cite.id] = record
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
