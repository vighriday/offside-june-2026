"""Deterministic SPLIT routing — the code fallback derives the right shape from evidence.

These prove the code router applies the documented rules: the golden Hand of God lens
signatures route to the golden SPLIT (ABSENT, ABSENT, PRESENT, PRESENT), and a different
signature (Lampard-shaped: clear law, knowable fact, decision-time deficit, agreement)
routes to a different SPLIT — so the router is evidence-derived, not hard-coded.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import LensOutput
from offside_engine.bake.synthesize import derive_split


def _lens(lens, stance, ids):
    state = "GROUNDED" if ids else "INSUFFICIENT_EVIDENCE"
    st = stance if ids else "INSUFFICIENT_EVIDENCE"
    return LensOutput(lens=lens, stance=st, state=state, citation_ids=list(ids),
                      rationale="r" if ids else "none")


def _states(split):
    return {c.axis: c.state for c in split.cells}


def test_hand_of_god_signature_routes_to_the_golden_split():
    # REFEREE SUPPORTS (clear law), HISTORICAL SUPPORTS (tech absent + obstructed),
    # FRAMING MIXED (opposed named sources), act admitted.
    lenses = [
        _lens("REFEREE", "SUPPORTS", ["ifab-1"]),
        _lens("TACTICAL", "SUPPORTS", ["sb-1"]),
        _lens("HISTORICAL", "SUPPORTS", ["hist-1"]),
        _lens("FRAMING", "MIXED", ["fr-1", "fr-2"]),
    ]
    split = derive_split(lenses, admitted_act=True)
    states = _states(split)
    assert states["RULE_AMBIGUITY"] == "ABSENT"
    assert states["INDETERMINACY"] == "ABSENT"          # admitted act
    assert states["DECISION_TIME_DEFICIT"] == "PRESENT"
    assert states["CULTURAL_PRIOR_BIAS"] == "PRESENT"


def test_present_cells_cite_their_lens_ids_and_absent_cells_do_not():
    lenses = [
        _lens("REFEREE", "SUPPORTS", ["ifab-1"]),
        _lens("TACTICAL", "SUPPORTS", ["sb-1"]),
        _lens("HISTORICAL", "SUPPORTS", ["hist-1"]),
        _lens("FRAMING", "MIXED", ["fr-1", "fr-2"]),
    ]
    by = {c.axis: c for c in derive_split(lenses, admitted_act=True).cells}
    assert by["DECISION_TIME_DEFICIT"].citation_ids == ["hist-1"]
    assert by["CULTURAL_PRIOR_BIAS"].citation_ids == ["fr-1", "fr-2"]
    assert by["RULE_AMBIGUITY"].citation_ids == []      # ABSENT carries no citation
    assert by["INDETERMINACY"].citation_ids == []


def test_lampard_shaped_signature_routes_differently():
    # Clear law, knowable fact (not admitted but no unresolved mental element), historical
    # decision-time deficit, but framing AGREES (one-sided) -> CULTURAL_PRIOR_BIAS ABSENT.
    lenses = [
        _lens("REFEREE", "SUPPORTS", ["law10-1"]),
        _lens("TACTICAL", "INSUFFICIENT_EVIDENCE", []),
        _lens("HISTORICAL", "SUPPORTS", ["lhist-1"]),
        _lens("FRAMING", "SUPPORTS", ["lfr-1"]),   # everyone agrees it was a goal
    ]
    states = _states(derive_split(lenses, admitted_act=False))
    assert states["RULE_AMBIGUITY"] == "ABSENT"
    assert states["DECISION_TIME_DEFICIT"] == "PRESENT"
    assert states["CULTURAL_PRIOR_BIAS"] == "ABSENT"     # the contrast with Hand of God


def test_missing_lens_evidence_routes_to_not_documented():
    lenses = [
        _lens("REFEREE", "SUPPORTS", []),     # no evidence
        _lens("TACTICAL", "SUPPORTS", []),
        _lens("HISTORICAL", "SUPPORTS", []),
        _lens("FRAMING", "MIXED", []),
    ]
    states = _states(derive_split(lenses, admitted_act=False))
    # with no evidence in any lens, every axis is NOT_DOCUMENTED, never silently ABSENT
    assert states["RULE_AMBIGUITY"] == "NOT_DOCUMENTED"
    assert states["DECISION_TIME_DEFICIT"] == "NOT_DOCUMENTED"
    assert states["CULTURAL_PRIOR_BIAS"] == "NOT_DOCUMENTED"
