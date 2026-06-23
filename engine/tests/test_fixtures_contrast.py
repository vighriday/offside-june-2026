"""The generalization proof, as a test over the SHIPPED fixtures.

Spec §2.1: Lampard is the on-camera proof the axes separate — same engine, different
evidence, different SPLIT. This asserts the two committed fixtures agree on three axes and
diverge on exactly one (CULTURAL_PRIOR_BIAS), so the diagnostic is demonstrably derived
from evidence rather than hard-coded. It reads the real JSON the web app renders.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from offside_engine.analyze.split_schema import IncidentBundle

_FIXTURES = Path(__file__).resolve().parents[2] / "web" / "fixtures"
_HOG = _FIXTURES / "hand-of-god-1986.json"
_LAMPARD = _FIXTURES / "lampard-ghost-goal-2010.json"

pytestmark = pytest.mark.skipif(
    not (_HOG.exists() and _LAMPARD.exists()), reason="fixtures not baked"
)


def _states(path: Path) -> dict:
    bundle = IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))
    return {c.axis: c.state for c in bundle.split.cells}


def test_both_fixtures_are_valid_bundles():
    # model_validate runs the click-to-source guard too — a shipped fixture that dead-links
    # an IFAB citation would fail here.
    for p in (_HOG, _LAMPARD):
        IncidentBundle.model_validate_json(p.read_text(encoding="utf-8"))


def test_incidents_diverge_only_on_cultural_prior_bias():
    hog = _states(_HOG)
    lam = _states(_LAMPARD)

    # agree on the law being clear and the moment being deficient
    assert hog["RULE_AMBIGUITY"] == lam["RULE_AMBIGUITY"] == "ABSENT"
    assert hog["DECISION_TIME_DEFICIT"] == lam["DECISION_TIME_DEFICIT"] == "PRESENT"

    # the proof: cultural prior bias is PRESENT for the Hand of God, ruled out for Lampard
    assert hog["CULTURAL_PRIOR_BIAS"] == "PRESENT"
    assert lam["CULTURAL_PRIOR_BIAS"] == "ABSENT"
    assert hog["CULTURAL_PRIOR_BIAS"] != lam["CULTURAL_PRIOR_BIAS"]


def test_every_cited_ifab_law_in_shipped_fixtures_has_page_and_bbox():
    for p in (_HOG, _LAMPARD):
        bundle = IncidentBundle.model_validate_json(p.read_text(encoding="utf-8"))
        cited = set(bundle.settled_fact.citation_ids)
        for sl in bundle.lenses:
            cited.update(sl.output.citation_ids)
        for c in bundle.split.cells:
            cited.update(c.citation_ids)
        for cid in cited:
            cit = bundle.citations.get(cid)
            if cit and cit.doc_kind == "IFAB_LAW":
                assert cit.page is not None and cit.bbox is not None, (
                    f"{p.name}: IFAB citation {cid} missing page/bbox"
                )
