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


def test_historical_disputes_routes_to_indeterminacy_not_decision_time():
    # The offside-margin signature: clear law, but the HISTORICAL lens DISPUTES knowability
    # (the exact truth is unrecoverable even now). The honest router reads that real stance —
    # not any planted citation id — and routes INDETERMINACY PRESENT, DECISION_TIME ABSENT.
    lenses = [
        _lens("REFEREE", "SUPPORTS", ["law11-1"]),
        _lens("TACTICAL", "INSUFFICIENT_EVIDENCE", []),
        _lens("HISTORICAL", "DISPUTES", ["om-hist-1"]),
        _lens("FRAMING", "SUPPORTS", ["om-fr-1"]),   # one-sided framing
    ]
    by = {c.axis: c for c in derive_split(lenses, admitted_act=False).cells}
    assert by["INDETERMINACY"].state == "PRESENT"
    assert by["INDETERMINACY"].citation_ids == ["om-hist-1"]   # cites what Granite cited
    assert by["DECISION_TIME_DEFICIT"].state == "ABSENT"       # tech sees it; not a sightline gap
    assert by["RULE_AMBIGUITY"].state == "ABSENT"


def test_indeterminacy_keys_on_stance_not_any_citation_id():
    # The de-circularization guarantee: the SAME cited ids with a SUPPORTS stance must NOT
    # fire INDETERMINACY. The axis follows the model's reading, never the id string — so
    # renaming a citation can never flip the answer.
    disputes = [
        _lens("REFEREE", "SUPPORTS", ["law-1"]),
        _lens("TACTICAL", "INSUFFICIENT_EVIDENCE", []),
        _lens("HISTORICAL", "DISPUTES", ["same-id"]),
        _lens("FRAMING", "SUPPORTS", ["fr-1"]),
    ]
    supports = [
        _lens("REFEREE", "SUPPORTS", ["law-1"]),
        _lens("TACTICAL", "INSUFFICIENT_EVIDENCE", []),
        _lens("HISTORICAL", "SUPPORTS", ["same-id"]),   # identical id, different reading
        _lens("FRAMING", "SUPPORTS", ["fr-1"]),
    ]
    d = _states(derive_split(disputes, admitted_act=False))
    s = _states(derive_split(supports, admitted_act=False))
    assert d["INDETERMINACY"] == "PRESENT"
    assert s["INDETERMINACY"] == "NOT_DOCUMENTED"      # same id, but SUPPORTS != indeterminacy
    assert s["DECISION_TIME_DEFICIT"] == "PRESENT"     # SUPPORTS is a decision-time gap


def test_historical_mixed_rules_out_both_gaps():
    # suarez / handball / pgmol: the info WAS adequate, fully knowable, no gap of either kind.
    lenses = [
        _lens("REFEREE", "DISPUTES", ["law-1", "law-2"]),
        _lens("TACTICAL", "INSUFFICIENT_EVIDENCE", []),
        _lens("HISTORICAL", "MIXED", ["hist-1"]),
        _lens("FRAMING", "SUPPORTS", ["fr-1"]),
    ]
    states = _states(derive_split(lenses, admitted_act=False))
    assert states["DECISION_TIME_DEFICIT"] == "ABSENT"        # fully knowable, no sightline gap
    assert states["INDETERMINACY"] == "NOT_DOCUMENTED"        # nothing unrecoverable
    assert states["RULE_AMBIGUITY"] == "PRESENT"              # the dispute is the rule


def test_admitted_act_dominates_even_if_historical_disputes():
    # An admitted act resolves the residual; INDETERMINACY must be ABSENT regardless of a
    # DISPUTES historical reading (the precondition gates first).
    lenses = [
        _lens("REFEREE", "SUPPORTS", ["law-1"]),
        _lens("TACTICAL", "INSUFFICIENT_EVIDENCE", []),
        _lens("HISTORICAL", "DISPUTES", ["hist-1"]),
        _lens("FRAMING", "MIXED", ["fr-1", "fr-2"]),
    ]
    states = _states(derive_split(lenses, admitted_act=True))
    assert states["INDETERMINACY"] == "ABSENT"


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
