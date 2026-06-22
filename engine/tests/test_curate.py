"""Curated evidence — the Layer-3 click-to-source guarantee for the cited Laws."""

from __future__ import annotations

import json

from offside_engine.ingest.curate import (
    CURATED_ANCHORS,
    build_curated_citations,
    save_curated_evidence,
)


def test_anchors_cover_the_hero_incidents():
    incidents = {i for a in CURATED_ANCHORS for i in a["applies_to_incidents"]}
    # Hand of God is the hero; Lampard drives Rule Evolution.
    assert "hand-of-god" in incidents
    assert "lampard-ghost-goal" in incidents


def test_curated_citations_are_well_formed():
    cites = build_curated_citations()
    assert cites, "expected at least one curated citation"
    for c in cites:
        assert c.page is not None and c.page > 0
        assert c.source_doc == "ifab-laws-2025-26"
        assert len(c.extracted_text) > 20  # a real passage, not a stub


def test_every_anchor_id_is_unique():
    ids = [a["id"] for a in CURATED_ANCHORS]
    assert len(ids) == len(set(ids))


def test_save_curated_evidence_round_trips(tmp_path):
    out = save_curated_evidence(tmp_path / "curated.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert set(payload) == {a["id"] for a in CURATED_ANCHORS}
    # records carry the human-facing fields the web viewer needs
    sample = next(iter(payload.values()))
    assert {"page", "extracted_text", "law", "applies_to_incidents"} <= set(sample)
