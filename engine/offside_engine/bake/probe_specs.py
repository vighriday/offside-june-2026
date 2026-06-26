"""Declarative probe specs — the three falsification experiments, per incident.

Kept separate from :mod:`probe` (which runs them) so the experiments are reviewable as
plain data. Each injected atom is a synthesized HISTORICAL passage, clearly id-tagged
``probe-…`` so it can never be confused with committed corpus evidence, and it is added to
the pool only for the duration of its own probe run.

The centerpiece incident is ``offside-margin`` and the targeted axis is INDETERMINACY —
the subtlest of the four and the one whose honesty matters most, since it is the axis the
old engine used to fake. The three probes together prove the axis is *reasoned*:

* FLIP      — say the margin is now perfectly recoverable -> the lens should stop reading
              indeterminacy -> the axis moves off PRESENT.
* NOISE     — say something irrelevant -> the axis must not move.
* OVERREACH — make a wild over-claim the cited text cannot support -> Granite may read it,
              but Granite Guardian flags it UNGROUNDED and the gate demotes it.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import Citation
from offside_engine.bake.probe import ProbeSpec


def _hist_atom(cid: str, text: str) -> Citation:
    """A synthesized HISTORICAL evidence atom for a probe run (never committed corpus)."""
    return Citation(
        id=cid,
        source_doc="probe-injected",
        doc_kind="HISTORICAL_REPORT",
        page=None,
        bbox=None,
        extracted_text=text,
        attribution=None,
    )


# ── offside-margin — the centerpiece, axis INDETERMINACY ─────────────────────

OFFSIDE_MARGIN_PROBES: list[ProbeSpec] = [
    ProbeSpec(
        kind="FLIP",
        axis="INDETERMINACY",
        mode="REPLACE",
        label="Push it the right way",
        plain_question="If the record said the exact line is now perfectly measurable, does "
        "the engine stop calling the truth unknowable?",
        outcome="The engine read the new record and moved the axis off ‘unknowable’. It is "
        "reasoning from what it is shown, not replaying a stored answer.",
        injected_citation=_hist_atom(
            "probe-om-flip-measurable",
            "A chip-in-ball and high-frame-rate skeletal tracking system now fixes the exact "
            "limb position at the instant the ball is played with no frame ambiguity, and the "
            "authorities have removed the tolerance band entirely because the measurement is "
            "now exact and fully reproducible. The position at the margin is completely "
            "recoverable at every margin, and officials confirm the information available is "
            "fully adequate to decide any call.",
        ),
    ),
    ProbeSpec(
        kind="NOISE",
        axis="INDETERMINACY",
        mode="ADD",
        label="Push it with junk",
        plain_question="If we feed it something irrelevant, does it wrongly change its mind?",
        outcome="Irrelevant evidence changed nothing. The engine does not flip at any push — "
        "the negative control held.",
        injected_citation=_hist_atom(
            "probe-om-noise-attendance",
            "The match was played in front of a sell-out crowd and the half-time entertainment "
            "featured a local marching band. Ticket sales for the fixture set a seasonal record.",
        ),
    ),
    ProbeSpec(
        kind="OVERREACH",
        axis="INDETERMINACY",
        mode="REPLACE",  # unused on the OVERREACH path (it audits, it does not re-run the lens)
        label="Lie to it",
        plain_question="If someone over-states what the evidence actually says, does the "
        "second IBM model catch it?",
        outcome="Granite Guardian — the second model — checked this claim against the engine’s "
        "own cited sources and returned UNGROUNDED. It rejects what the evidence does not "
        "support, live. That is the audit that makes the whole thing trustworthy.",
        injected_citation=_hist_atom(
            "probe-om-overreach-suspended",
            "The offside Law has been officially suspended and referees now decide every "
            "marginal call by personal preference, with no measurement of any kind.",
        ),
    ),
]


PROBE_SPECS_BY_INCIDENT: dict[str, list[ProbeSpec]] = {
    "offside-margin": OFFSIDE_MARGIN_PROBES,
}
