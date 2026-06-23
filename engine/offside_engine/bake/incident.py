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
        "never overturned. The handball is admitted — the facts are settled. What stays "
        "contested is the acceptable outcome, not what happened."
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


# ── Lampard's ghost goal (Germany v England, 2010) ───────────────────────────
#
# The CONTRAST incident — the proof OFFSIDE is derived, not hard-coded. Its documented
# thesis differs from the Hand of God on the dimension that matters: the Law is clear
# (RULE_AMBIGUITY ABSENT), the fact was always knowable (INDETERMINACY ABSENT), the
# decisive truth was simply unavailable to the officials in the moment with no goal-line
# technology (DECISION_TIME_DEFICIT PRESENT) — but named sources AGREE it was a goal, so
# there is no opposed framing (CULTURAL_PRIOR_BIAS ABSENT). Same engine, same rules, a
# different SPLIT — because the evidence signature differs.

LAMPARD_GHOST_GOAL = IncidentSpec(
    incident_id="lampard-ghost-goal-2010",
    title="Lampard's ghost goal",
    settled_status="ADJUDICATED_CONTESTED",
    settled_statement=(
        "Frank Lampard's shot struck the crossbar and bounced down well behind the goal "
        "line against Germany in the 2010 World Cup. The goal was not given, England lost, "
        "and replays showed the whole ball had clearly crossed the line. That the ball "
        "crossed the line is not in dispute."
    ),
    # Not an admitted offence — the fact (ball over the line) was always settled, so there
    # is no deliberateness residual to resolve. admission_note is empty: INDETERMINACY
    # routes from the absence of an unresolved mental element, not from an admission.
    settled_citation_ids=("lampard-hist-crossed-line",),
    admission_note="",
    lens_queries={
        "REFEREE": "When is a goal scored under the Laws — does the whole ball have to cross the line?",
        "TACTICAL": "How is the disallowed goal represented in the event data?",
        "HISTORICAL": "Could the officials review or clearly see whether the ball crossed the line in 2010?",
        "FRAMING": "How did named figures describe the disallowed goal afterwards?",
    },
    allowed_citation_ids=frozenset(
        {
            # Referee — the Law 10 method-of-scoring clause (whole ball over the line).
            "ifab-law10-goal-scored-p97",
            # Historical — no goal-line tech, obstructed sightline in the moment.
            "lampard-hist-crossed-line",
            "lampard-hist-no-glt-2010",
            "lampard-hist-sightline",
            # Framing — named sources AGREE it was a goal (one-sided, not opposed).
            "lampard-framing-lampard",
            "lampard-framing-merkel-context",
            "lampard-framing-blatter",
        }
    ),
    expected_thesis={
        "RULE_AMBIGUITY": {"ABSENT"},
        # No mental-element evidence bears on Lampard (the fact was always settled), so
        # INDETERMINACY is legitimately NOT_DOCUMENTED rather than actively "ruled out".
        "INDETERMINACY": {"ABSENT", "NOT_DOCUMENTED"},
        "DECISION_TIME_DEFICIT": {"PRESENT"},
        "CULTURAL_PRIOR_BIAS": {"ABSENT"},   # the contrast: agreement, not division
    },
)


# ── Suárez's handball on the line (Uruguay v Ghana, 2010) ────────────────────
#
# The THIRD signature — and the one that completes the lineage. The handball was SEEN and
# CORRECTLY ADJUDICATED in the moment (red card + penalty), so Decision-Time Deficit is
# ABSENT — the clean contrast with both the Hand of God (unseen) and Lampard (unknowable
# without tech). What remains is pure framing: a smart sacrifice versus a cheat. So
# Cultural Prior Bias is the dominant axis, the SAME axis the Hand of God shares — which is
# exactly why the Divergence Lineage groups Hand of God and Suárez together.

SUAREZ_HANDBALL = IncidentSpec(
    incident_id="suarez-handball-2010",
    title="Suárez's handball on the line",
    settled_status="ADJUDICATED_CONTESTED",
    settled_statement=(
        "In the last minute against Ghana in the 2010 World Cup, Luis Suárez deliberately "
        "handled a goal-bound ball on the line. He was sent off and a penalty was awarded — "
        "the call was correct. Ghana missed the penalty and Uruguay won the shootout. The "
        "handball, and the red card for it, are not in dispute."
    ),
    settled_citation_ids=("ifab-law12-dogso-handball-p118",),
    admission_note=(
        "The handball was deliberate and is admitted; the act itself is not in dispute."
    ),
    lens_queries={
        "REFEREE": "What is the sanction for denying a goal by deliberate handball?",
        "TACTICAL": "How is the handball represented in the event data?",
        "HISTORICAL": "Could the officials see and correctly rule on the handball in the moment?",
        "FRAMING": "How did named figures describe the handball afterwards?",
    },
    allowed_citation_ids=frozenset(
        {
            # Referee — the DOGSO deliberate-handball sanction clause (sent off).
            "ifab-law12-dogso-handball-p118",
            "ifab-law12-handball-offence-p110",
            # Historical — the call was correctly made in the moment (DTD absent).
            "suarez-hist-on-the-line",
            "suarez-hist-correctly-adjudicated",
            # Framing — Suárez vs Gyan, opposed valence on the same admitted act.
            "suarez-framing-suarez",
            "suarez-framing-gyan",
        }
    ),
    expected_thesis={
        "RULE_AMBIGUITY": {"ABSENT"},
        "INDETERMINACY": {"ABSENT"},
        # The contrast: the officials saw it and ruled correctly, so no decision-time gap.
        "DECISION_TIME_DEFICIT": {"ABSENT", "NOT_DOCUMENTED"},
        "CULTURAL_PRIOR_BIAS": {"PRESENT"},
    },
)


# ══════════════════════════════════════════════════════════════════════════════
# CURRENT, UNSETTLED DISPUTES (2024–2026)
#
# The archive incidents above all resolve with RULE_AMBIGUITY=ABSENT and
# INDETERMINACY=ABSENT — the rule was clear and the fact knowable; only sightlines and
# nationalism remained. The three incidents below are live, unsettled disputes from the
# current Laws and the current season, and they are chosen precisely because they light up
# the axes the archive never did — proving the four-axis framework is load-bearing, not
# decorative. Each is a STRUCTURAL dispute (a class of incident, not a single moment),
# which is what makes OFFSIDE a tool for the people who write and apply the Laws, not a
# quiz about famous goals.
# ══════════════════════════════════════════════════════════════════════════════


# ── The modern handball call (Law 12, 2024/25 rewrite) ───────────────────────
#
# The RULE_AMBIGUITY=PRESENT signature — the first incident where the rulebook ITSELF is
# the source of the dispute. The 2024/25 Law retains three different handball tests
# (deliberate, "unnaturally bigger", accidental-into-goal) with different sanctions, and an
# official must pick one in real time. The fact (hand touched ball) is visible and knowable,
# so Decision-Time Deficit is ABSENT; the framings share one complaint rather than splitting
# by nation, so Cultural Prior Bias is one-sided (ABSENT/WEAK). The Referee lens DISPUTES —
# competing clauses point to different outcomes for the same contact.

HANDBALL_REWRITE = IncidentSpec(
    incident_id="handball-rewrite",
    title="The modern handball call",
    settled_status="ADJUDICATED_CONTESTED",
    settled_statement=(
        "Football's handball Law was rewritten for 2024/25, yet it still asks officials to "
        "choose between several different tests for the same contact — deliberate movement, "
        "an 'unnaturally bigger' body, or an accidental touch that leads to a goal — each "
        "with a different consequence. Whether a given handball is an offence is genuinely "
        "disputed, and the disagreement is about the rule, not about what happened."
    ),
    settled_citation_ids=("ifab-law12-handball-deliberate-p110",),
    admission_note="",
    lens_queries={
        "REFEREE": "Does the Law give one clear test for handball, or several competing tests?",
        "TACTICAL": "Does the event data resolve which handball test applies?",
        "HISTORICAL": "Could officials see the contact, and was the information adequate at the moment?",
        "FRAMING": "How did named figures describe the handball Law afterwards?",
    },
    allowed_citation_ids=frozenset(
        {
            "ifab-law12-handball-deliberate-p110",
            "ifab-law12-handball-offence-p110",
            "hb-hist-three-tests",
            "hb-hist-visible-knowable",
            "hb-hist-inconsistent-application",
            "hb-framing-pundit",
            "hb-framing-coach",
        }
    ),
    expected_thesis={
        "RULE_AMBIGUITY": {"PRESENT"},
        "INDETERMINACY": {"ABSENT", "NOT_DOCUMENTED"},
        "DECISION_TIME_DEFICIT": {"ABSENT"},
        "CULTURAL_PRIOR_BIAS": {"ABSENT", "WEAK"},
    },
)


# ── The millimetre offside line (semi-automated offside, 2024/25) ────────────
#
# The INDETERMINACY=PRESENT signature — the first incident where the truth itself is not
# recoverable. Law 11 fixes the offside line precisely, so the RULE is clear (Rule Ambiguity
# ABSENT). Semi-automated technology can now see the moment, so there is no Decision-Time
# Deficit. But at a millimetre margin the exact position cannot be measured — the
# authorities' own "thicker line" is an admission of it. The Historical lens DISPUTES
# knowability, which the router maps to INDETERMINACY (not Decision-Time Deficit).

OFFSIDE_MARGIN = IncidentSpec(
    incident_id="offside-margin",
    title="The millimetre offside line",
    settled_status="ADJUDICATED_CONTESTED",
    settled_statement=(
        "Semi-automated offside technology draws the offside line to the millimetre and is "
        "faster and more consistent than the old manual lines. Yet at the finest margins the "
        "exact position is not physically recoverable — the authorities themselves apply a "
        "deliberately 'thicker' line. The rule is clear and the technology can see it; what "
        "is disputed is whether a truth measured that finely can be known at all."
    ),
    settled_citation_ids=("ifab-law11-offside-margin-p103",),
    admission_note="",
    lens_queries={
        "REFEREE": "Does Law 11 define the offside line clearly?",
        "TACTICAL": "Does the event data resolve the exact position at a millimetre margin?",
        "HISTORICAL": "Can the exact line be measured to the precision the Law implies?",
        "FRAMING": "How did named figures describe the millimetre offside calls?",
    },
    allowed_citation_ids=frozenset(
        {
            "ifab-law11-offside-margin-p103",
            "ifab-law11-offside-p103",
            "om-hist-line-defined",
            "om-hist-margin-unrecoverable",
            "om-hist-thicker-line",
            "om-framing-broadcaster",
            "om-framing-official",
        }
    ),
    expected_thesis={
        "RULE_AMBIGUITY": {"ABSENT"},
        "INDETERMINACY": {"PRESENT"},
        "DECISION_TIME_DEFICIT": {"ABSENT"},
        "CULTURAL_PRIOR_BIAS": {"ABSENT"},
    },
)


# ── The "subjective" VAR call (PGMOL, 2025/26) ───────────────────────────────
#
# The COMBINED signature — the only incident where two structural axes are live at once.
# The "clear and obvious" / "non-footballing action" thresholds are matters of degree, so
# near-identical contact is ruled in opposite ways across matches (Rule Ambiguity PRESENT,
# Referee lens DISPUTES), AND each club's side reads the same agreed contact in its own
# favour (Cultural Prior Bias PRESENT, opposed framings). The contact is visible and
# replayed, so Decision-Time Deficit is ABSENT.

PGMOL_SUBJECTIVE = IncidentSpec(
    incident_id="pgmol-subjective",
    title="The 'subjective' VAR call",
    settled_status="ADJUDICATED_CONTESTED",
    settled_statement=(
        "Across the current Premier League season, near-identical fouls — holding at a "
        "corner, minimal contact on a goalkeeper — are penalised in one match and waved away "
        "in the next. Many are logged not as errors but as 'subjective decisions'. The "
        "contact is agreed and visible; what splits the room is whether the Law's threshold "
        "was met, and which side you support."
    ),
    settled_citation_ids=("pg-hist-threshold",),
    admission_note="",
    lens_queries={
        "REFEREE": "Is the VAR threshold a bright line, or a matter of degree applied inconsistently?",
        "TACTICAL": "Does the event data resolve whether the threshold was met?",
        "HISTORICAL": "Could officials see the contact, and was the information adequate?",
        "FRAMING": "How did named figures on each side describe the same contact?",
    },
    allowed_citation_ids=frozenset(
        {
            "pg-hist-threshold",
            "pg-hist-opposite-rulings",
            "pg-hist-visible",
            "pg-framing-aggrieved",
            "pg-framing-benefiting",
        }
    ),
    expected_thesis={
        "RULE_AMBIGUITY": {"PRESENT"},
        "INDETERMINACY": {"ABSENT", "NOT_DOCUMENTED"},
        "DECISION_TIME_DEFICIT": {"ABSENT"},
        "CULTURAL_PRIOR_BIAS": {"PRESENT"},
    },
)


INCIDENTS: dict[str, IncidentSpec] = {
    HAND_OF_GOD.incident_id: HAND_OF_GOD,
    SUAREZ_HANDBALL.incident_id: SUAREZ_HANDBALL,
    LAMPARD_GHOST_GOAL.incident_id: LAMPARD_GHOST_GOAL,
    HANDBALL_REWRITE.incident_id: HANDBALL_REWRITE,
    OFFSIDE_MARGIN.incident_id: OFFSIDE_MARGIN,
    PGMOL_SUBJECTIVE.incident_id: PGMOL_SUBJECTIVE,
}
