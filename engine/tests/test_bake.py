"""The bake orchestration — full pipeline with Granite and Guardian mocked.

These assert the *orchestration*, not model behaviour: the eight steps run in order,
the gate demotes flow into the bundle, the thesis oracle fires on a mismatch, and the
assembled bundle is internally consistent. Granite is scripted to return the golden
Hand of God readings; Guardian is scripted to a fixed verdict.
"""

from __future__ import annotations

import pytest

from offside_engine.analyze.split_schema import (
    CANONICAL_AXIS_ORDER,
    Citation,
    LensOutput,
    Split,
    SplitCell,
)
from offside_engine.bake.bake import (
    ThesisMismatch,
    assert_thesis_shape,
    bake_incident,
    render_synthesis_input,
)
from offside_engine.bake.incident import HAND_OF_GOD
from offside_engine.retrieve.lens_retrieve import RetrievedHit


# ── fixtures: the golden Hand of God evidence + scripted models ───────────────

# One citation per lens id the spec allows that the golden readings cite.
_GOLDEN_CITES = {
    "ifab-law12-handball-offence-p110": "A goal scored directly from the hand does not stand.",
    "sb-hand-of-god-body-part": "The body part is recorded as the catch-all label 'Other'.",
    "hist-tech-1986": "No video review existed and the officials' views differed.",
    "framing-maradona-1986": "Maradona is reported to have called it the hand of God.",
    "framing-shilton": "Shilton is reported to have called it cheating.",
}


def _citations():
    return {
        cid: Citation(id=cid, source_doc="x", doc_kind="IFAB_LAW", extracted_text=txt)
        for cid, txt in _GOLDEN_CITES.items()
    }


# The golden gated lens outputs Granite "returns", keyed by lens.
_GOLDEN_LENS = {
    "REFEREE": LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
                          citation_ids=["ifab-law12-handball-offence-p110"],
                          rationale="The Law voids a hand-scored goal (ifab-law12-handball-offence-p110)."),
    "TACTICAL": LensOutput(lens="TACTICAL", stance="SUPPORTS", state="GROUNDED",
                           citation_ids=["sb-hand-of-god-body-part"],
                           rationale="The data falls back to the catch-all label (sb-hand-of-god-body-part)."),
    "HISTORICAL": LensOutput(lens="HISTORICAL", stance="SUPPORTS", state="GROUNDED",
                             citation_ids=["hist-tech-1986"],
                             rationale="No review tech and differing views (hist-tech-1986)."),
    "FRAMING": LensOutput(lens="FRAMING", stance="MIXED", state="GROUNDED",
                          citation_ids=["framing-maradona-1986", "framing-shilton"],
                          rationale="Two named sources frame the same goal in opposite valence."),
}

# The golden SPLIT shape Granite "derives" — the documented Hand of God signature. The
# PRESENT cells' citations are filled at synthesis time from the ids the gated lenses
# actually carried (mirrors real synthesis routing), so the SPLIT never cites an id the
# framing/historical lens did not surface under whichever retriever the test used.
def _golden_split(historical_ids: list[str], framing_ids: list[str]) -> Split:
    return Split(
        cells=[
            SplitCell(axis="RULE_AMBIGUITY", state="ABSENT", citation_ids=[],
                      rationale="A single clear offence clause, no competing clause."),
            SplitCell(axis="INDETERMINACY", state="ABSENT", citation_ids=[],
                      rationale="The act is admitted, so deliberateness is resolved."),
            SplitCell(axis="DECISION_TIME_DEFICIT", state="PRESENT",
                      citation_ids=historical_ids or ["hist-tech-1986"],
                      rationale="No review tech and differing views in the moment."),
            SplitCell(axis="CULTURAL_PRIOR_BIAS", state="PRESENT",
                      citation_ids=framing_ids or ["framing-maradona-1986"],
                      rationale="Named sources frame the same goal in opposite valence."),
        ],
        headline="It never resolved over what could be seen and who was watching, not the Law.",
    )


_GOLDEN_SPLIT = _golden_split(["hist-tech-1986"], ["framing-maradona-1986", "framing-shilton"])


def _ids_for_lens_in(user: str, lens: str) -> list[str]:
    """Read back the citation_ids the gated LENS <lens> block carried in the synthesis input."""
    import re
    m = re.search(rf"LENS {lens}:.*?citation_ids: \[(.*?)\]", user, re.DOTALL)
    if not m or not m.group(1).strip() or m.group(1).strip() == "(none)":
        return []
    return [s.strip() for s in m.group(1).split(",") if s.strip()]


class _ScriptedGranite:
    """Returns a golden LensOutput per lens query, then a golden Split for synthesis.

    Lens calls return the golden output for whichever lens's evidence is in `user`,
    citing only the ids actually shown. The synthesis call reads the gated lens ids back
    out of `user` and routes them onto the PRESENT cells — so the derived SPLIT always
    cites ids the lenses really carried, under any retriever.
    """

    class _Cfg:
        model = "granite3.3:8b"

    def __init__(self):
        self.config = self._Cfg()
        self.options = {"temperature": 0.0, "seed": 42}

    def generate_structured(self, *, schema, system, user):
        if schema is Split:
            return _golden_split(
                historical_ids=_ids_for_lens_in(user, "HISTORICAL"),
                framing_ids=_ids_for_lens_in(user, "FRAMING"),
            )
        for lens, out in _GOLDEN_LENS.items():
            if out.citation_ids[0] in user:
                shown = [cid for cid in out.citation_ids if cid in user]
                if not shown:
                    continue
                return out.model_copy(update={"citation_ids": shown})
        raise AssertionError(f"unexpected lens evidence: {user[:80]}")


class _AllGroundedGuardian:
    model = "granite-guardian3:2b"

    def check_groundedness(self, *, query, context_passages, response):
        return "GROUNDED"


class _GoldenRetriever:
    """Returns the allowed hits for each lens so run_lens renders real evidence."""

    _BY_LENS = {
        "REFEREE": [("ifab-law12-handball-offence-p110", _GOLDEN_CITES["ifab-law12-handball-offence-p110"])],
        "TACTICAL": [("sb-hand-of-god-body-part", _GOLDEN_CITES["sb-hand-of-god-body-part"])],
        "HISTORICAL": [("hist-tech-1986", _GOLDEN_CITES["hist-tech-1986"])],
        "FRAMING": [("framing-maradona-1986", _GOLDEN_CITES["framing-maradona-1986"]),
                    ("framing-shilton", _GOLDEN_CITES["framing-shilton"])],
    }

    def retrieve(self, *, lens, query, k=3, allowed_citation_ids=None):
        hits = []
        for cid, txt in self._BY_LENS[lens]:
            if allowed_citation_ids is None or cid in allowed_citation_ids:
                hits.append(RetrievedHit(citation_id=cid, lens=lens, page=None, text=txt, score=0.1))
        return hits


# ── render + oracle ──────────────────────────────────────────────────────────

def test_synthesis_input_carries_settled_fact_and_lens_blocks():
    text = render_synthesis_input(list(_GOLDEN_LENS.values()), shared_settled_fact="the act is admitted")
    assert "SHARED_SETTLED_FACT" in text
    assert "the act is admitted" in text
    assert "LENS REFEREE" in text and "LENS FRAMING" in text
    # it must not leak a number into the synthesis input
    assert "73" not in text


def test_thesis_oracle_passes_on_the_documented_shape():
    assert_thesis_shape(_GOLDEN_SPLIT, HAND_OF_GOD.expected_thesis)  # no raise


def test_thesis_oracle_fails_when_a_cell_drifts():
    drifted = Split(
        cells=[
            SplitCell(axis="RULE_AMBIGUITY", state="PRESENT", citation_ids=["hist-tech-1986"],
                      rationale="(wrong) the law conflicts (hist-tech-1986)."),
            *(_GOLDEN_SPLIT.cells[1:]),
        ],
        headline="drifted",
    )
    with pytest.raises(ThesisMismatch, match="RULE_AMBIGUITY"):
        assert_thesis_shape(drifted, HAND_OF_GOD.expected_thesis)


# ── full bake ────────────────────────────────────────────────────────────────

def test_full_bake_produces_the_golden_bundle():
    bundle = bake_incident(
        HAND_OF_GOD,
        retriever=_GoldenRetriever(),
        granite=_ScriptedGranite(),
        guardian=_AllGroundedGuardian(),
        citations=_citations(),
        corpus_git_sha="deadbeef",
    )
    assert bundle.incident_id == "hand-of-god-1986"
    assert bundle.settled_fact.status == "ADJUDICATED_CONTESTED"
    # the documented signature survived end to end
    states = {c.axis: c.state for c in bundle.split.cells}
    assert states["RULE_AMBIGUITY"] == "ABSENT"
    assert states["INDETERMINACY"] == "ABSENT"
    assert states["DECISION_TIME_DEFICIT"] == "PRESENT"
    assert states["CULTURAL_PRIOR_BIAS"] == "PRESENT"
    # four sealed lenses, four sealed cells in canonical order
    assert len(bundle.lenses) == 4
    assert tuple(sc.cell.axis for sc in bundle.cell_seals) == CANONICAL_AXIS_ORDER
    # provenance frozen
    assert bundle.provenance.corpus_git_sha == "deadbeef"
    assert bundle.provenance.guardian_model == "granite-guardian3:2b"


def test_ungrounded_lens_is_demoted_in_the_bundle():
    class _RefereeUngrounded:
        model = "granite-guardian3:2b"

        def check_groundedness(self, *, query, context_passages, response):
            # flag only the referee reading; ground everything else
            return "UNGROUNDED" if "voids a hand-scored goal" in response else "GROUNDED"

    bundle = bake_incident(
        HAND_OF_GOD,
        retriever=_GoldenRetriever(),
        granite=_ScriptedGranite(),
        guardian=_RefereeUngrounded(),
        citations=_citations(),
    )
    referee = next(sl for sl in bundle.lenses if sl.output.lens == "REFEREE")
    assert referee.output.state == "INSUFFICIENT_EVIDENCE"
    assert referee.seal.verdict == "UNGROUNDED"
