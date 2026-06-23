"""Deterministic code routing of the gated lens evidence onto THE SPLIT.

The SPLIT synthesis is a set of *fixed routing rules* (see ``prompts.SPLIT_SYSTEM``):
each axis reads one lens's evidence signature and maps it to a cell state. Those rules
are deterministic, so they can be applied in code — which is strictly more reliable than
asking an 8B model to emit a four-cell schema-valid JSON object every time.

We still prefer the Granite synthesis at bake time (it keeps the "a model routed the
evidence" story and can phrase a richer rationale), but when Granite cannot produce a
schema-valid SPLIT, this code router produces the same evidence-derived SPLIT from the
same gated lens outputs. It is **not** hard-coded toward any answer: it reads only the
lens signatures, so a different incident (e.g. Lampard) yields a different SPLIT — the
exact property the thesis oracle checks.

Each axis maps from exactly one lens's gated output:

* RULE_AMBIGUITY        ← REFEREE   (SUPPORTS=clear law → ABSENT; DISPUTES=competing
                                     clauses → PRESENT; MIXED=one edge → WEAK)
* INDETERMINACY         ← REFEREE   (admitted act → ABSENT, per the hard precondition)
* DECISION_TIME_DEFICIT ← HISTORICAL(SUPPORTS=tech absent + view obstructed → PRESENT;
                                     MIXED=one of the two → WEAK)
* CULTURAL_PRIOR_BIAS   ← FRAMING   (MIXED=opposed named sources → PRESENT;
                                     SUPPORTS/DISPUTES one-sided → ABSENT)
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import (
    CellState,
    LensOutput,
    Split,
    SplitCell,
)

# Does the SHARED_SETTLED_FACT record the actor admitting the act? Passed in by the bake
# so the INDETERMINACY precondition can fire without re-reading sources.


def _by_lens(lenses: list[LensOutput]) -> dict[str, LensOutput]:
    return {lo.lens: lo for lo in lenses}


def _cell(axis, state: CellState, source: LensOutput | None, rationale: str) -> SplitCell:
    cite = list(source.citation_ids) if (source and state in ("PRESENT", "WEAK")) else []
    return SplitCell(axis=axis, state=state, citation_ids=cite, rationale=rationale)


def _grounded(lo: LensOutput | None) -> bool:
    return bool(lo and lo.state == "GROUNDED" and lo.citation_ids)


def derive_split(lenses: list[LensOutput], *, admitted_act: bool) -> Split:
    """Route the gated lens outputs onto the four-axis SPLIT by the fixed rules."""
    by = _by_lens(lenses)
    ref = by.get("REFEREE")
    hist = by.get("HISTORICAL")
    fram = by.get("FRAMING")

    # RULE_AMBIGUITY ← REFEREE. A clear single offence clause (SUPPORTS) rules it out;
    # genuinely competing clauses (DISPUTES) make it present; a single edge is weak.
    if not _grounded(ref):
        rule = _cell("RULE_AMBIGUITY", "NOT_DOCUMENTED", None,
                     "No referee-law evidence bears on this incident.")
    elif ref.stance == "DISPUTES":
        rule = _cell("RULE_AMBIGUITY", "PRESENT", ref,
                     "Retrieved clauses point to different outcomes for the same facts.")
    elif ref.stance == "MIXED":
        rule = _cell("RULE_AMBIGUITY", "WEAK", ref,
                     "The retrieved law is mostly clear but one edge is underspecified.")
    else:  # SUPPORTS — a clear single offence clause
        rule = _cell("RULE_AMBIGUITY", "ABSENT", None,
                     "A clear single offence clause governs the act, with no competing clause.")

    # INDETERMINACY ← REFEREE intent element, gated by the admission precondition.
    if admitted_act:
        indet = _cell("INDETERMINACY", "ABSENT", None,
                      "The act is admitted, so the deliberateness residual is resolved.")
    elif _grounded(ref) and ref.stance in ("DISPUTES", "MIXED"):
        indet = _cell("INDETERMINACY", "PRESENT", ref,
                      "A load-bearing mental element remains unresolved by the evidence.")
    else:
        indet = _cell("INDETERMINACY", "NOT_DOCUMENTED", None,
                      "No evidence makes an unresolved mental element load-bearing.")

    # DECISION_TIME_DEFICIT ← HISTORICAL. Tech absent AND view obstructed → present.
    if not _grounded(hist):
        dtd = _cell("DECISION_TIME_DEFICIT", "NOT_DOCUMENTED", None,
                    "No historical fact bears on what was available at the moment of the call.")
    elif hist.stance == "SUPPORTS":
        dtd = _cell("DECISION_TIME_DEFICIT", "PRESENT", hist,
                    "Resolving technology was absent and the view was obstructed in the moment.")
    elif hist.stance == "MIXED":
        dtd = _cell("DECISION_TIME_DEFICIT", "WEAK", hist,
                    "Only one of absent technology or an obstructed view holds.")
    else:
        dtd = _cell("DECISION_TIME_DEFICIT", "ABSENT", None,
                    "Review technology existed and the view was clear at the moment of the call.")

    # CULTURAL_PRIOR_BIAS ← FRAMING. Opposed named sources on the same fact → present.
    if not _grounded(fram):
        cult = _cell("CULTURAL_PRIOR_BIAS", "NOT_DOCUMENTED", None,
                     "No named-source quote bears on this incident.")
    elif fram.stance == "MIXED":
        cult = _cell("CULTURAL_PRIOR_BIAS", "PRESENT", fram,
                     "Named sources frame the same settled fact in opposed valence.")
    else:  # SUPPORTS / DISPUTES — one-sided
        cult = _cell("CULTURAL_PRIOR_BIAS", "ABSENT", None,
                     "Named sources agree on the outcome; there is no opposed framing.")

    headline = (
        "It stays contested over "
        + _name_present_axes([rule, indet, dtd, cult])
        + " — not over the dimensions ruled out."
    )
    return Split(cells=[rule, indet, dtd, cult], headline=headline)


_AXIS_PHRASE = {
    "RULE_AMBIGUITY": "whether the Law is clear",
    "INDETERMINACY": "whether the fact is knowable",
    "DECISION_TIME_DEFICIT": "what could be seen in the moment",
    "CULTURAL_PRIOR_BIAS": "how named sources frame the same fact",
}


def _name_present_axes(cells: list[SplitCell]) -> str:
    live = [_AXIS_PHRASE[c.axis] for c in cells if c.state in ("PRESENT", "WEAK")]
    if not live:
        return "no single dimension"
    if len(live) == 1:
        return live[0]
    return ", ".join(live[:-1]) + " and " + live[-1]
