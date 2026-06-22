"""Behavioral tests for THE SPLIT contract — the validators do what they claim."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from offside_engine.analyze.split_schema import (
    CANONICAL_AXIS_ORDER,
    LensOutput,
    Split,
    SplitCell,
)


def _cell(axis, state="PRESENT", citations=("c1",), rationale="grounded reading"):
    return SplitCell(axis=axis, state=state, citation_ids=list(citations), rationale=rationale)


def _valid_split():
    return Split(
        cells=[
            _cell("RULE_AMBIGUITY", "WEAK"),
            _cell("INDETERMINACY", "ABSENT", citations=()),
            _cell("DECISION_TIME_DEFICIT", "PRESENT"),
            _cell("CULTURAL_PRIOR_BIAS", "PRESENT"),
        ],
        headline="Settled by the rules; never by the world.",
    )


# ── LensOutput ───────────────────────────────────────────────────────────────


def test_grounded_lens_requires_a_citation():
    with pytest.raises(ValidationError):
        LensOutput(lens="REFEREE", stance="SUPPORTS", state="GROUNDED", citation_ids=[], rationale="x")


def test_insufficient_evidence_lens_must_be_empty_and_consistent():
    ok = LensOutput(
        lens="TACTICAL",
        stance="INSUFFICIENT_EVIDENCE",
        state="INSUFFICIENT_EVIDENCE",
        citation_ids=[],
        rationale="no spatial data for this era",
    )
    assert ok.state == "INSUFFICIENT_EVIDENCE"

    with pytest.raises(ValidationError):  # carrying a citation while claiming no evidence
        LensOutput(
            lens="TACTICAL",
            stance="INSUFFICIENT_EVIDENCE",
            state="INSUFFICIENT_EVIDENCE",
            citation_ids=["c1"],
            rationale="contradiction",
        )


# ── SplitCell ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("state", ["PRESENT", "WEAK"])
def test_present_and_weak_cells_require_citations(state):
    with pytest.raises(ValidationError):
        _cell("RULE_AMBIGUITY", state, citations=())


@pytest.mark.parametrize("state", ["ABSENT", "NOT_DOCUMENTED"])
def test_absent_and_not_documented_cells_need_no_citation(state):
    cell = _cell("INDETERMINACY", state, citations=())
    assert cell.state == state


# ── Split ────────────────────────────────────────────────────────────────────


def test_valid_split_round_trips():
    s = _valid_split()
    assert [c.axis for c in s.cells] == list(CANONICAL_AXIS_ORDER)


def test_split_requires_exactly_four_cells():
    with pytest.raises(ValidationError):
        Split(cells=[_cell("RULE_AMBIGUITY")], headline="too few")


def test_split_rejects_wrong_axis_order():
    with pytest.raises(ValidationError):
        Split(
            cells=[
                _cell("INDETERMINACY"),
                _cell("RULE_AMBIGUITY"),
                _cell("DECISION_TIME_DEFICIT"),
                _cell("CULTURAL_PRIOR_BIAS"),
            ],
            headline="out of order",
        )


def test_split_rejects_duplicate_axes():
    with pytest.raises(ValidationError):
        Split(
            cells=[
                _cell("RULE_AMBIGUITY"),
                _cell("RULE_AMBIGUITY"),
                _cell("DECISION_TIME_DEFICIT"),
                _cell("CULTURAL_PRIOR_BIAS"),
            ],
            headline="dupes",
        )
