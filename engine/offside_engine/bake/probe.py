"""The falsification engine — make a baked incident try to break its own answer, live.

A frozen SPLIT is easy to mistake for a lookup table: maybe the engine just *replays* a
stored answer. The honest way to disprove that is to ATTACK the engine and watch what it
does, through the same real Granite + Granite Guardian pipeline that produced the fixture:

* ``FLIP``      — feed it a grounded counter-passage that *should* change one lens's
                  reading. A reasoning engine MOVES the axis. A lookup table would not.
* ``NOISE``     — feed it an irrelevant passage. A reasoning engine does NOT move. This is
                  the negative control that rules out "it flips at any push".
* ``OVERREACH`` — feed it a passage whose claim outruns what it supports. Granite may read
                  it, but **Granite Guardian — the second IBM model — flags it UNGROUNDED**
                  and the gate demotes it. The audit overrules the reading, on camera.

Each probe runs the REAL pipeline (retrieve → Granite → Guardian → route) against a copy of
the incident's evidence with one extra passage injected, and records the genuine outcome:
the axis state before, the axis state after, and the actual Guardian verdict token. Nothing
here is hand-authored — the :mod:`offside_engine.bake.integrity` lock fails the build if a
probe's verdict did not come from a real ``granite*`` model, so a fabricated overrule can
never ship.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from offside_engine.analyze.granite_client import GraniteClient
from offside_engine.analyze.guardian import GuardianClient
from offside_engine.analyze.guardian_gate import gate_lens
from offside_engine.analyze.lens_runner import run_lens
from offside_engine.analyze.split_schema import (
    Citation,
    LensKind,
    Probe,
    ProbeKind,
    SplitAxis,
)
from offside_engine.bake.incident import IncidentSpec
from offside_engine.bake.synthesize import derive_split
from offside_engine.index.build_lance import build_index
from offside_engine.retrieve.lens_retrieve import LensRetriever, RetrievedHit

# How a probe presents its injected evidence to the target lens:
#   REPLACE — the lens sees ONLY the injected atom(s): a clean counterfactual ("if the record
#             said THIS instead, what would the engine read?"). Used by FLIP and OVERREACH,
#             where the point is a decisive change in what the evidence says.
#   ADD     — the lens sees its real evidence PLUS the injected atom: used by NOISE, the
#             negative control, where irrelevant evidence must not disturb the real reading.
ProbeMode = Literal["REPLACE", "ADD"]

# Which lens carries each axis — the lens a probe must perturb to move that axis.
_AXIS_LENS: dict[SplitAxis, LensKind] = {
    "RULE_AMBIGUITY": "REFEREE",
    "INDETERMINACY": "HISTORICAL",
    "DECISION_TIME_DEFICIT": "HISTORICAL",
    "CULTURAL_PRIOR_BIAS": "FRAMING",
}


@dataclass(frozen=True)
class ProbeSpec:
    """The declarative input for one probe — what to inject and what to watch.

    ``injected_citation`` is a synthesized evidence atom added to the pool and the incident
    allow-list before the real pipeline runs. It is clearly marked in its id (``probe-…``)
    so it can never be mistaken for committed corpus evidence. ``label`` / ``plain_question``
    / ``outcome`` are the judge-facing copy; the states and verdict are filled in live.
    """

    kind: ProbeKind
    axis: SplitAxis
    mode: ProbeMode
    label: str
    plain_question: str
    outcome: str
    injected_citation: Citation


def _axis_state(lenses: list, *, admitted_act: bool, axis: SplitAxis) -> str:
    split = derive_split(lenses, admitted_act=admitted_act)
    return next(c.state for c in split.cells if c.axis == axis)


def _real_cited_passages(base_gated: list, lens: LensKind, pool: dict[str, Citation]) -> list[str]:
    """The exact source passages the baseline lens reading cited — what Guardian audits against."""
    target = next((lo for lo in base_gated if lo.lens == lens), None)
    if target is None:
        return []
    return [pool[c].extracted_text for c in target.citation_ids if c in pool and pool[c].extracted_text]


def _run_overreach(
    pspec: ProbeSpec,
    spec: IncidentSpec,
    *,
    base_citations: dict[str, Citation],
    base_gated: list,
    guardian: GuardianClient,
) -> Probe:
    """The honest audit demo: submit a deliberately OVER-STATED claim to the real Granite
    Guardian, audited against the engine's OWN real cited evidence, and capture the genuine
    UNGROUNDED token.

    This does not pretend the engine made the over-claim — it tests the *auditor*. The
    engine's real answer is unchanged (state_before == state_after); the point is that the
    second IBM model rejects a claim the cited sources do not support, live and for real. The
    integrity lock requires this to be a true ``granite*`` UNGROUNDED, so it cannot be faked.
    """
    target_lens = _AXIS_LENS[pspec.axis]
    admitted = bool(spec.admission_note)
    state = _axis_state(base_gated, admitted_act=admitted, axis=pspec.axis)

    passages = _real_cited_passages(base_gated, target_lens, base_citations)
    verdict = guardian.check_groundedness(
        query=spec.lens_queries[target_lens],
        context_passages=passages,
        response=pspec.injected_citation.extracted_text,  # the over-claim
    )
    return Probe(
        kind=pspec.kind,
        axis=pspec.axis,
        label=pspec.label,
        plain_question=pspec.plain_question,
        injected_text=pspec.injected_citation.extracted_text,
        state_before=state,
        state_after=state,  # the engine's answer does not move; the auditor rejects the claim
        guardian_verdict=verdict,
        guardian_model=guardian.model,
        outcome=pspec.outcome,
    )


def run_probe(
    pspec: ProbeSpec,
    spec: IncidentSpec,
    *,
    base_citations: dict[str, Citation],
    base_gated: list,
    granite: GraniteClient,
    guardian: GuardianClient,
) -> Probe:
    """Run one probe through the real pipeline and capture its genuine outcome.

    ``base_gated`` is the incident's already-gated lens outputs (the untouched bake), so the
    *before* state is read from the real baseline, not recomputed.

    FLIP / NOISE inject an atom and re-run the target lens through Granite + Guardian, then
    read the *after* state. OVERREACH instead submits an over-stated claim to the real
    Guardian against the engine's own cited evidence and captures the genuine UNGROUNDED —
    the auditor demo. The Guardian verdict recorded is always a real captured token.
    """
    if pspec.kind == "OVERREACH":
        return _run_overreach(
            pspec, spec, base_citations=base_citations, base_gated=base_gated, guardian=guardian,
        )

    target_lens = _AXIS_LENS[pspec.axis]
    admitted = bool(spec.admission_note)

    # before: the target axis state in the untouched, already-baked lens set.
    state_before = _axis_state(base_gated, admitted_act=admitted, axis=pspec.axis)

    # Build the perturbed pool and allow-list per the probe's mode:
    #   REPLACE — the lens may surface ONLY the injected atom (the counterfactual world);
    #   ADD     — the lens keeps its real allow-list AND the injected atom (the noise control).
    inj = pspec.injected_citation
    pool = dict(base_citations)
    pool[inj.id] = inj
    if pspec.mode == "REPLACE":
        allow = {inj.id}
    else:
        allow = set(spec.allowed_citation_ids) | {inj.id}

    # Force the injected atom into the lens's evidence block (it must actually be SEEN; we
    # are testing what the lens does WITH it, not whether retrieval ranks it). It stays
    # citable and is audited by Guardian exactly like any retrieved passage.
    forced = (
        RetrievedHit(
            citation_id=inj.id, lens=target_lens, page=inj.page,
            text=inj.extracted_text, score=0.0,
        ),
    )

    with tempfile.TemporaryDirectory() as tmp:
        db_dir = Path(tmp) / "lance"
        build_index(list(pool.values()), db_dir)
        retriever = LensRetriever(db_dir)

        run = run_lens(
            lens=target_lens,
            query=spec.lens_queries[target_lens],
            retriever=retriever,
            granite=granite,
            allowed_citation_ids=allow,
            extra_hits=forced,
        )
        gated = gate_lens(run.output, citations=pool, guardian=guardian)

    # Splice the re-read target lens back into the baseline lens set, preserving order.
    perturbed = [gated.output if lo.lens == target_lens else lo for lo in base_gated]
    state_after = _axis_state(perturbed, admitted_act=admitted, axis=pspec.axis)

    return Probe(
        kind=pspec.kind,
        axis=pspec.axis,
        label=pspec.label,
        plain_question=pspec.plain_question,
        injected_text=pspec.injected_citation.extracted_text,
        state_before=state_before,
        state_after=state_after,
        guardian_verdict=gated.seal.verdict,
        guardian_model=gated.seal.guardian_model,
        outcome=pspec.outcome,
    )
