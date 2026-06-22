"""Curated Historical + Framing loaders — run against the real corpus YAML."""

from __future__ import annotations

from pathlib import Path

from offside_engine.ingest.curated_lenses import (
    load_framing_citations,
    load_historical_citations,
)

_CORPUS = Path(__file__).resolve().parents[2] / "corpus"
_FRAMING = _CORPUS / "framing" / "hand-of-god" / "sources.yaml"
_HISTORICAL = _CORPUS / "historical" / "hand-of-god" / "record.yaml"


def test_framing_loads_named_dated_sources():
    cites = load_framing_citations(_FRAMING)
    assert cites, "expected framing citations"
    for c in cites:
        assert c.doc_kind == "FRAMING_SOURCE"
        assert c.attribution  # every framing names its speaker + source + date
        assert len(c.extracted_text) > 20


def test_framing_includes_both_markets():
    cites = load_framing_citations(_FRAMING)
    text = " ".join(c.extracted_text for c in cites).lower()
    # opposite framings of the same settled fact, from named sources on each side
    assert "maradona" in text
    assert "shilton" in text or "robson" in text


def test_historical_loads_neutral_cited_facts():
    cites = load_historical_citations(_HISTORICAL)
    assert cites
    text = " ".join(c.extracted_text for c in cites).lower()
    # the era-correct grounding the Decision-Time-Deficit axis needs
    assert "no var" in text or "goal-line technology" in text
    for c in cites:
        assert c.doc_kind == "HISTORICAL_REPORT"
        assert c.attribution


def test_curated_citation_ids_are_unique_across_lenses():
    ids = [c.id for c in load_framing_citations(_FRAMING) + load_historical_citations(_HISTORICAL)]
    assert len(ids) == len(set(ids))
