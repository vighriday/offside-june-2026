"""The Guardian gate — demotion of any reading the second model cannot ground.

Guardian is faked to a fixed verdict so these assert the *consequence*: a flagged lens
collapses to INSUFFICIENT_EVIDENCE, a flagged cell to NOT_DOCUMENTED, a confirmed one
passes through unchanged, and a non-assertive state is never sent to the model.
"""

from __future__ import annotations

from offside_engine.analyze.guardian_gate import gate_cell, gate_lens
from offside_engine.analyze.split_schema import Citation, LensOutput, SplitCell


class _FakeGuardian:
    """Returns a fixed verdict and records whether it was called."""

    def __init__(self, verdict: str):
        self.model = "granite-guardian3:2b"
        self._verdict = verdict
        self.called = False

    def check_groundedness(self, *, query, context_passages, response):
        self.called = True
        return self._verdict


def _citations():
    return {
        "ifab-1": Citation(id="ifab-1", source_doc="ifab", doc_kind="IFAB_LAW", page=110,
                           extracted_text="A goal scored directly from the hand does not stand."),
    }


# ── lens gate ────────────────────────────────────────────────────────────────

def _grounded_lens():
    return LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED",
                      citation_ids=["ifab-1"], rationale="The clause voids the goal (ifab-1).")


def test_grounded_lens_survives_with_a_grounded_seal():
    g = _FakeGuardian("GROUNDED")
    res = gate_lens(_grounded_lens(), citations=_citations(), guardian=g)
    assert res.output.state == "GROUNDED"
    assert res.seal.verdict == "GROUNDED"
    assert res.seal.checked_context_citation_ids == ["ifab-1"]
    assert res.seal.guardian_model == "granite-guardian3:2b"
    assert g.called


def test_ungrounded_lens_is_demoted_to_insufficient_evidence():
    g = _FakeGuardian("UNGROUNDED")
    res = gate_lens(_grounded_lens(), citations=_citations(), guardian=g)
    assert res.output.state == "INSUFFICIENT_EVIDENCE"
    assert res.output.stance == "INSUFFICIENT_EVIDENCE"
    assert res.output.citation_ids == []
    assert res.seal.verdict == "UNGROUNDED"


def test_already_insufficient_lens_is_not_sent_to_guardian():
    g = _FakeGuardian("GROUNDED")
    lens = LensOutput(lens="TACTICAL", stance="INSUFFICIENT_EVIDENCE",
                      state="INSUFFICIENT_EVIDENCE", citation_ids=[],
                      rationale="No evidence retrieved.")
    res = gate_lens(lens, citations=_citations(), guardian=g)
    assert res.output.state == "INSUFFICIENT_EVIDENCE"
    assert res.seal.verdict == "UNGROUNDED"
    assert not g.called  # nothing to audit


# ── cell gate ────────────────────────────────────────────────────────────────

def _present_cell():
    return SplitCell(axis="DECISION_TIME_DEFICIT", state="PRESENT",
                     citation_ids=["ifab-1"], rationale="No review tech in the moment (ifab-1).")


def test_present_cell_survives_when_grounded():
    g = _FakeGuardian("GROUNDED")
    res = gate_cell(_present_cell(), citations=_citations(), guardian=g)
    assert res.cell.state == "PRESENT"
    assert res.seal.verdict == "GROUNDED"
    assert g.called


def test_ungrounded_present_cell_is_demoted_to_not_documented():
    g = _FakeGuardian("UNGROUNDED")
    res = gate_cell(_present_cell(), citations=_citations(), guardian=g)
    assert res.cell.state == "NOT_DOCUMENTED"
    assert res.cell.citation_ids == []
    assert res.seal.verdict == "UNGROUNDED"


def test_absent_cell_is_not_audited_and_passes_through():
    g = _FakeGuardian("UNGROUNDED")  # even a flag must not touch an ABSENT finding
    cell = SplitCell(axis="RULE_AMBIGUITY", state="ABSENT", citation_ids=[],
                     rationale="A single clear offence clause, no competing clause.")
    res = gate_cell(cell, citations=_citations(), guardian=g)
    assert res.cell.state == "ABSENT"  # our finding, never demoted by the gate
    assert not g.called


def test_missing_citation_text_still_audits_against_what_resolves():
    # a cited id with no matching citation contributes no passage; the gate still runs
    g = _FakeGuardian("GROUNDED")
    cell = SplitCell(axis="CULTURAL_PRIOR_BIAS", state="PRESENT",
                     citation_ids=["ifab-1", "missing-99"],
                     rationale="Two named sources diverge (ifab-1).")
    res = gate_cell(cell, citations=_citations(), guardian=g)
    assert res.seal.checked_context_citation_ids == ["ifab-1", "missing-99"]
    assert res.cell.state == "PRESENT"
