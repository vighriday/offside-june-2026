"""Incident specifications — the declarative input to a bake.

An :class:`IncidentSpec` is everything the bake needs to turn a real football moment
into an :class:`~offside_engine.analyze.split_schema.IncidentBundle`: the settled fact
to state first, the per-lens retrieval query, the per-incident citation allow-list (so a
lens can never cite evidence from another incident), and the *expected thesis shape*.

The thesis shape is NOT how the answer is produced — Granite + the synthesis rules
derive each cell state from evidence with no knowledge of the expected answer. The shape
is an **assertion the bake checks afterwards**: if the derived SPLIT does not match the
documented thesis for a known incident, the bake fails loudly rather than freeze a
fixture that silently drifted. That is what keeps "derived, not hard-coded" honest — the
shape is a test oracle, never an input to generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from offside_engine.analyze.split_schema import (
    CANONICAL_AXIS_ORDER,
    CellState,
    LensKind,
    ResolutionStatus,
    SplitAxis,
)

# Per-axis allowed states for a thesis assertion. A set lets a thesis say "ABSENT or
# WEAK" where the documented record tolerates either without being satisfied by PRESENT.
ThesisShape = dict[SplitAxis, set[CellState]]


@dataclass(frozen=True)
class IncidentSpec:
    """The declarative spec for one incident, consumed by the bake."""

    incident_id: str
    title: str
    settled_status: ResolutionStatus
    settled_statement: str
    settled_citation_ids: tuple[str, ...]
    # The actor's own admission, injected into the synthesis SHARED_SETTLED_FACT so the
    # INDETERMINACY precondition can fire ("admitted act -> deliberateness resolved").
    admission_note: str
    lens_queries: dict[LensKind, str]
    # The only citation ids any lens may surface for this incident (the allow-list).
    allowed_citation_ids: frozenset[str]
    expected_thesis: ThesisShape = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.expected_thesis:
            unknown = set(self.expected_thesis) - set(CANONICAL_AXIS_ORDER)
            if unknown:
                raise ValueError(f"expected_thesis names unknown axes: {sorted(unknown)}")


# ── The Hand of God (Argentina v England, 1986) ──────────────────────────────
#
# The golden incident. Its documented thesis: the Law is CLEAR (a hand-scored goal does
# not stand — RULE_AMBIGUITY ABSENT/WEAK); the deliberateness is RESOLVED because the
# actor later admitted the act (INDETERMINACY ABSENT); what the referee could see in the
# moment was deficient (DECISION_TIME_DEFICIT PRESENT); and named sources frame the same
# agreed handball in opposite valence (CULTURAL_PRIOR_BIAS PRESENT). The moment stays
# debated not because the law is unclear, but because of what could be seen and which
# nation is watching.

HAND_OF_GOD = IncidentSpec(
    incident_id="hand-of-god-1986",
    title="The Hand of God",
    settled_status="ADJUDICATED_CONTESTED",
    settled_statement=(
        "Diego Maradona scored with his hand against England in the 1986 World Cup "
        "quarter-final. The referee allowed the goal, Argentina won, and the result was "
        "never overturned. The handball itself is not in dispute."
    ),
    settled_citation_ids=("ifab-law12-handball-offence-p110",),
    admission_note=(
        "The scorer later acknowledged the ball was played by his hand; the act itself "
        "is admitted and not in dispute."
    ),
    lens_queries={
        "REFEREE": "Is a goal scored directly from the hand or arm an offence under the Laws?",
        "TACTICAL": "How is a hand-scored goal recorded in the shot event data model?",
        "HISTORICAL": "Could the officials review or clearly see the handball at the moment of the decision?",
        "FRAMING": "How did named figures describe the goal afterwards?",
    },
    allowed_citation_ids=frozenset(
        {
            # Referee — the real goal-voiding clause (F-A) + sanction corroboration.
            "ifab-law12-handball-offence-p110",
            "ifab-law12-dogso-handball-p118",
            # Tactical — the StatsBomb body-part 'Other' anomaly aggregate.
            "sb-hand-of-god-body-part",
            # Historical — curated facts on review tech and sightlines in 1986.
            # NOTE: hist-context-malvinas is deliberately excluded (F-F): it bears on
            # CONTEXT, not CULTURAL_PRIOR_BIAS, and must not feed any lens as bias evidence.
            "hist-tech-1986",
            "hist-officials-accounts",
            "hist-never-overturned",
            # Framing — named-source quotes (Maradona / Shilton / Robson), real ids.
            "framing-maradona-1986",
            "framing-maradona-2000",
            "framing-shilton",
            "framing-robson",
        }
    ),
    expected_thesis={
        "RULE_AMBIGUITY": {"ABSENT", "WEAK"},
        "INDETERMINACY": {"ABSENT"},
        "DECISION_TIME_DEFICIT": {"PRESENT"},
        "CULTURAL_PRIOR_BIAS": {"PRESENT"},
    },
)


INCIDENTS: dict[str, IncidentSpec] = {HAND_OF_GOD.incident_id: HAND_OF_GOD}
