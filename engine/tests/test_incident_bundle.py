"""IncidentBundle — the frozen fixture contract and its internal-consistency guards.

The bundle is the whole thing the web reads. These tests pin the invariants the web
relies on: one panel per lens, cell seals in canonical axis order matching the SPLIT,
and every cited id resolvable in the citation map (so click-to-source never dangles).
"""

from __future__ import annotations

import pytest

from offside_engine.analyze.split_schema import (
    CANONICAL_AXIS_ORDER,
    BakeProvenance,
    Citation,
    IncidentBundle,
    LensOutput,
    SealedCell,
    SealedLens,
    SettledFact,
    Split,
    SplitCell,
    TrustSeal,
)


def _seal(verdict="GROUNDED", ids=()):
    return TrustSeal(verdict=verdict, guardian_model="granite-guardian3:2b",
                     checked_context_citation_ids=list(ids))


def _lens_panel(lens, ids):
    out = LensOutput(lens=lens, stance="SUPPORTS", state="GROUNDED",
                     citation_ids=list(ids), rationale="grounded reading")
    return SealedLens(output=out, seal=_seal(ids=ids))


def _absent_cell(axis):
    return SplitCell(axis=axis, state="ABSENT", citation_ids=[], rationale="ruled out")


def _present_cell(axis, ids):
    return SplitCell(axis=axis, state="PRESENT", citation_ids=list(ids), rationale="present")


def _bundle(**overrides):
    citations = {
        "c-ref": Citation(id="c-ref", source_doc="ifab", doc_kind="IFAB_LAW", page=110,
                          extracted_text="law"),
        "c-frame": Citation(id="c-frame", source_doc="framing", doc_kind="FRAMING_SOURCE",
                            extracted_text="quote"),
    }
    lenses = [
        _lens_panel("REFEREE", ["c-ref"]),
        _lens_panel("TACTICAL", ["c-ref"]),
        _lens_panel("HISTORICAL", ["c-ref"]),
        _lens_panel("FRAMING", ["c-frame"]),
    ]
    cells = [
        _absent_cell("RULE_AMBIGUITY"),
        _absent_cell("INDETERMINACY"),
        _present_cell("DECISION_TIME_DEFICIT", ["c-ref"]),
        _present_cell("CULTURAL_PRIOR_BIAS", ["c-frame"]),
    ]
    split = Split(cells=cells, headline="why it never resolved")
    cell_seals = [SealedCell(cell=c, seal=_seal(ids=c.citation_ids)) for c in cells]
    kwargs = dict(
        incident_id="hand-of-god-1986",
        title="The Hand of God",
        settled_fact=SettledFact(status="ADJUDICATED_CONTESTED",
                                 statement="The goal stood and was never overturned.",
                                 citation_ids=[]),
        lenses=lenses,
        split=split,
        cell_seals=cell_seals,
        citations=citations,
        provenance=BakeProvenance(granite_model="granite3.3:8b",
                                  guardian_model="granite-guardian3:2b",
                                  embed_model="granite-embedding:30m"),
    )
    kwargs.update(overrides)
    return IncidentBundle(**kwargs)


def test_a_well_formed_bundle_validates():
    b = _bundle()
    assert b.incident_id == "hand-of-god-1986"
    assert tuple(c.axis for c in b.split.cells) == CANONICAL_AXIS_ORDER


def test_duplicate_lens_panel_is_rejected():
    dup = [_lens_panel("REFEREE", ["c-ref"])] * 4
    with pytest.raises(ValueError, match="one panel per lens"):
        _bundle(lenses=dup)


def test_cell_seals_out_of_axis_order_is_rejected():
    b = _bundle()
    reversed_seals = list(reversed(b.cell_seals))
    with pytest.raises(ValueError, match="canonical axis order"):
        _bundle(cell_seals=reversed_seals)


def test_cited_id_with_no_citation_is_rejected():
    # a lens cites an id that is absent from the citation map -> click-to-source dangles
    bad = [
        _lens_panel("REFEREE", ["c-missing"]),
        _lens_panel("TACTICAL", ["c-ref"]),
        _lens_panel("HISTORICAL", ["c-ref"]),
        _lens_panel("FRAMING", ["c-frame"]),
    ]
    with pytest.raises(ValueError, match="no citation"):
        _bundle(lenses=bad)


def test_bundle_round_trips_through_json():
    b = _bundle()
    again = IncidentBundle.model_validate_json(b.model_dump_json())
    assert again == b
