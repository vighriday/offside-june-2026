"""The Guardian gate — demote any reading the second IBM model cannot ground.

:mod:`guardian` gives a verdict; this module makes that verdict *consequential*. It
takes a Granite reading plus the exact passages it cited, asks Guardian whether the
reading is grounded in those passages, and:

* records a :class:`TrustSeal` (the frozen audit result), and
* **demotes the reading if Guardian flags it** — a lens collapses to
  ``INSUFFICIENT_EVIDENCE``; a SPLIT cell collapses to ``NOT_DOCUMENTED``.

The demotion is the whole point: a claim reaches a fixture only if the first model
asserted it *and* the second model could not refute it against the cited page. A
reading with no citations is never sent to Guardian — there is nothing to audit, so it
is treated as ungrounded by construction (it would already be ``INSUFFICIENT_EVIDENCE``
/ ``ABSENT`` from the schema's cite-or-die rule).
"""

from __future__ import annotations

from dataclasses import dataclass

from offside_engine.analyze.guardian import GuardianClient
from offside_engine.analyze.split_schema import (
    Citation,
    LensOutput,
    SplitCell,
    TrustSeal,
)

# Cell states that make a positive, citation-backed claim and so must be audited.
_ASSERTIVE_CELL_STATES = ("PRESENT", "WEAK")


def _passages_for(citation_ids: list[str], by_id: dict[str, Citation]) -> list[str]:
    """Resolve a reading's cited ids to the source passages Guardian audits against.

    An id with no matching citation contributes nothing — the reading then has fewer
    real passages behind it, which can only make the gate stricter, never looser.
    """
    out: list[str] = []
    for cid in citation_ids:
        cit = by_id.get(cid)
        if cit is not None and cit.extracted_text:
            out.append(cit.extracted_text)
    return out


@dataclass(frozen=True)
class GatedLens:
    """A lens output after the gate, plus the seal recording the audit."""

    output: LensOutput
    seal: TrustSeal


@dataclass(frozen=True)
class GatedCell:
    """A SPLIT cell after the gate, plus the seal recording the audit."""

    cell: SplitCell
    seal: TrustSeal


def _demoted_lens(lens: LensOutput) -> LensOutput:
    """Collapse a flagged lens to the one valid ungrounded answer."""
    return LensOutput(
        lens=lens.lens,
        stance="INSUFFICIENT_EVIDENCE",
        state="INSUFFICIENT_EVIDENCE",
        citation_ids=[],
        rationale="The groundedness gate could not confirm this reading against its cited source.",
    )


def _demoted_cell(cell: SplitCell) -> SplitCell:
    """Collapse a flagged cell to NOT_DOCUMENTED — undocumented, not asserted false."""
    return SplitCell(
        axis=cell.axis,
        state="NOT_DOCUMENTED",
        citation_ids=[],
        rationale="The groundedness gate could not confirm this reading against its cited source.",
    )


def gate_lens(
    lens: LensOutput,
    *,
    citations: dict[str, Citation],
    guardian: GuardianClient,
) -> GatedLens:
    """Audit a lens reading and demote it to INSUFFICIENT_EVIDENCE if Guardian flags it.

    A lens already at ``INSUFFICIENT_EVIDENCE`` carries no claim to audit; it is passed
    through with an UNGROUNDED seal (nothing was grounded) and no model call.
    """
    if lens.state == "INSUFFICIENT_EVIDENCE":
        seal = TrustSeal(
            verdict="UNGROUNDED",
            guardian_model=guardian.model,
            checked_context_citation_ids=[],
        )
        return GatedLens(output=lens, seal=seal)

    passages = _passages_for(lens.citation_ids, citations)
    verdict = guardian.check_groundedness(
        query=f"Is the {lens.lens} lens reading grounded in its cited sources?",
        context_passages=passages,
        response=lens.rationale,
    )
    seal = TrustSeal(
        verdict=verdict,
        guardian_model=guardian.model,
        checked_context_citation_ids=list(lens.citation_ids),
    )
    output = lens if verdict == "GROUNDED" else _demoted_lens(lens)
    return GatedLens(output=output, seal=seal)


def gate_cell(
    cell: SplitCell,
    *,
    citations: dict[str, Citation],
    guardian: GuardianClient,
) -> GatedCell:
    """Audit a SPLIT cell and demote PRESENT/WEAK to NOT_DOCUMENTED if Guardian flags it.

    ABSENT and NOT_DOCUMENTED make no citation-backed claim, so there is nothing to
    audit; they pass through with an UNGROUNDED seal and no model call. (ABSENT is a
    real finding — "ruled out" — but it is *our code's* finding, not a Granite claim
    grounded in a passage, so the groundedness gate does not apply to it.)
    """
    if cell.state not in _ASSERTIVE_CELL_STATES:
        seal = TrustSeal(
            verdict="UNGROUNDED",
            guardian_model=guardian.model,
            checked_context_citation_ids=[],
        )
        return GatedCell(cell=cell, seal=seal)

    passages = _passages_for(cell.citation_ids, citations)
    verdict = guardian.check_groundedness(
        query=f"Is the {cell.axis} reading grounded in its cited sources?",
        context_passages=passages,
        response=cell.rationale,
    )
    seal = TrustSeal(
        verdict=verdict,
        guardian_model=guardian.model,
        checked_context_citation_ids=list(cell.citation_ids),
    )
    out_cell = cell if verdict == "GROUNDED" else _demoted_cell(cell)
    return GatedCell(cell=out_cell, seal=seal)
