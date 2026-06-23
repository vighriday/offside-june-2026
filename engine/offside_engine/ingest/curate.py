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

from offside_engine.analyze.split_schema import Bbox, Citation

# The cited Law passages, with page anchors confirmed by Docling extraction against the
# IFAB 2025/26 single-pages edition. Verbatim text is filled from the extracted page
# during the bake and human-verified inside the rendered page image before freezing.
CURATED_ANCHORS: list[dict] = [
    {
        "id": "ifab-law11-offside-p103",
        "law": "Law 11",
        "page": 103,
        # bbox confirmed via Docling extraction of the offside-definition page.
        "bbox": {"left": 62.0, "top": 689.0, "right": 373.0, "bottom": 600.0},
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
        # The Referee grounding for the Lampard ghost goal: the goal/no-goal rule is a
        # single clear test (the WHOLE ball must cross the line), so RULE_AMBIGUITY=ABSENT.
        # Real Docling-extracted page + bbox from the born-digital 2025/26 PDF (Law 10, p97).
        "id": "ifab-law10-goal-scored-p97",
        "law": "Law 10",
        "page": 97,
        "bbox": {"left": 62.36, "top": 182.21, "right": 372.96, "bottom": 218.95},
        "topic": "method of scoring — the whole ball must cross the goal line",
        "applies_to_incidents": ["lampard-ghost-goal"],
        "seed_text": (
            "A goal is scored when the whole of the ball passes over the goal line, "
            "between the goalposts and under the crossbar, provided that no offence has "
            "been committed by the team scoring the goal."
        ),
    },
    {
        # F-A: the clause that actually voids a hand-scored goal — the grounding for
        # RULE_AMBIGUITY=ABSENT on the Hand of God. Real Docling page + bbox (p110).
        "id": "ifab-law12-handball-offence-p110",
        "law": "Law 12",
        "page": 110,
        "bbox": {"left": 54.0, "top": 309.0, "right": 373.0, "bottom": 175.0},
        "topic": "handball offence — goal scored from hand/arm is disallowed",
        "applies_to_incidents": ["hand-of-god", "suarez-handball"],
        "seed_text": (
            "It is an offence if a player deliberately touches the ball with their hand/arm, "
            "or scores in the opponents' goal immediately after the ball has touched their "
            "hand/arm, even if accidental. A goal scored in this way does not stand."
        ),
    },
    {
        # Corroboration of the SANCTION only — never the sole RULE_AMBIGUITY anchor (F-A).
        "id": "ifab-law12-dogso-handball-p118",
        "law": "Law 12",
        "page": 118,
        "bbox": {"left": 62.0, "top": 478.0, "right": 372.0, "bottom": 415.0},
        "topic": "denying a goal by deliberate handball (DOGSO sanction)",
        "applies_to_incidents": ["hand-of-god", "suarez-handball"],
        "seed_text": (
            "Where a player denies the opposing team a goal or an obvious goal-scoring "
            "opportunity by committing a deliberate handball offence the player is sent off "
            "whatever the position of the offence."
        ),
    },
]


def build_curated_citations() -> list[Citation]:
    """Build typed Citations from the confirmed anchors (source-doc: IFAB 2025/26).

    Every IFAB anchor carries a real Docling-confirmed bounding box — the bundle
    validator fails the bake on any cited IFAB law citation with a null bbox (F-A/J1).
    """
    return [
        Citation(
            id=a["id"],
            source_doc="ifab-laws-2025-26",
            doc_kind="IFAB_LAW",
            page=a["page"],
            bbox=Bbox(**a["bbox"]) if a.get("bbox") else None,
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
