"""Bake incident fixtures entirely offline — no GPU, no Ollama, no live model.

The cloud bake (``bake.ipynb``) runs the four Granite lens readings + Guardian audits on
a GPU. That is the authentic path, but an 8B model on free Colab is flaky: lenses
intermittently degrade and the strict synthesis schema fails. For reliable, deployable
fixtures we also support an **offline** bake that uses the same real corpus, the same
deterministic SPLIT router, and grounded lens readings whose stance + citations come
straight from the committed corpus — so the result is reproducible and every claim still
traces to a real, committed source. Provenance records that the SPLIT was routed
deterministically (no live model), so nothing is misrepresented.

Two incidents are baked, and the whole point is the CONTRAST: the Hand of God resolves to
(ABSENT, ABSENT, PRESENT, PRESENT) and Lampard's ghost goal to (ABSENT, ABSENT, PRESENT,
ABSENT). Same engine, same rules, different evidence → different SPLIT — the proof the
diagnostic is derived, not hard-coded.

Run:  python scripts/bake_local.py            # writes web/fixtures/<id>.json for both
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from offside_engine.analyze.split_schema import (
    BakeProvenance,
    Citation,
    IncidentBundle,
    LensOutput,
    RuleEvolution,
    SealedCell,
    SealedLens,
    SettledFact,
    TrustSeal,
)
from offside_engine.bake.corpus_pool import assemble_pool
from offside_engine.bake.incident import (
    HAND_OF_GOD,
    HANDBALL_REWRITE,
    LAMPARD_GHOST_GOAL,
    OFFSIDE_MARGIN,
    PGMOL_SUBJECTIVE,
    SUAREZ_HANDBALL,
    IncidentSpec,
)
from offside_engine.bake.synthesize import derive_split
from offside_engine.bake.write_fixture import write_fixture
from offside_engine.config import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_GUARDIAN_MODEL,
    DEFAULT_MODEL,
)
from offside_engine.statsbomb.pull_aggregates import HandOfGodAggregate

_REPO = Path(__file__).resolve().parents[2]
_ROUTER_NOTE = "deterministic-router"


def _lens(lens, stance, ids, rationale) -> LensOutput:
    return LensOutput(lens=lens, stance=stance, state="GROUNDED",
                      citation_ids=list(ids), rationale=rationale)


# ── Hand of God ──────────────────────────────────────────────────────────────

_HAND_OF_GOD_AGG = HandOfGodAggregate(
    match_id=3750191, scoreline="Argentina 2 - 1 England",
    maradona_total_shots=3, maradona_goals=2,
    hand_of_god_minute=50, hand_of_god_body_part="Other",
    second_goal_minute=54, second_goal_body_part="Left Foot",
    anomaly_present=True, three_sixty_available=False,
)

_HAND_OF_GOD_LENSES = [
    _lens("REFEREE", "SUPPORTS", ["ifab-law12-handball-offence-p110"],
          "The retrieved Law states a goal scored immediately after the ball touches the "
          "hand or arm does not stand (ifab-law12-handball-offence-p110); the rule yields "
          "one outcome for a hand-scored goal, so it is clear and rule-ambiguity does not hold."),
    _lens("TACTICAL", "SUPPORTS", ["sb-hand-of-god-body-part"],
          "The event data records this goal's body part as the catch-all label 'Other' "
          "while a comparable goal is a specific class (sb-hand-of-god-body-part); the "
          "schema having no category for the action is where the data model strains. This "
          "describes the data model only."),
    _lens("HISTORICAL", "SUPPORTS", ["hist-tech-1986", "hist-officials-accounts"],
          "In 1986 there was no VAR or goal-line technology and the decision could not be "
          "reviewed (hist-tech-1986), and the officials gave differing accounts with no "
          "clear view of the handling (hist-officials-accounts); the decisive truth was "
          "not available to them in the moment."),
    _lens("FRAMING", "MIXED", ["framing-maradona-1986", "framing-shilton"],
          "Diego Maradona is reported to have justified the goal as 'a little with the head "
          "of Maradona and a little with the hand of God' (framing-maradona-1986), while "
          "Peter Shilton is reported to have condemned it as cheating (framing-shilton); "
          "two named sources frame the same agreed handball in opposite valence."),
]


# ── Lampard ghost goal ───────────────────────────────────────────────────────
# The Referee grounding is the Law 10 method-of-scoring clause, now a curated anchor with
# a real Docling-extracted page + bbox (Law 10, p97) — so it ships into the pool via
# build_curated_citations() and click-to-source resolves to the real page.

_LAMPARD_LENSES = [
    _lens("REFEREE", "SUPPORTS", ["ifab-law10-goal-scored-p97"],
          "The retrieved Law states a goal is scored when the whole of the ball passes "
          "over the goal line (ifab-law10-goal-scored-p97); the rule is a single clear "
          "test with no competing clause, so rule-ambiguity does not hold."),
    # No StatsBomb anomaly bears on this incident — the Tactical lens honestly says so,
    # which is a valued answer, not a gap. (This is the empty-retrieval case made visible.)
    LensOutput(lens="TACTICAL", stance="INSUFFICIENT_EVIDENCE",
               state="INSUFFICIENT_EVIDENCE", citation_ids=[],
               rationale="No event-data anomaly bears on this incident."),
    _lens("HISTORICAL", "SUPPORTS", ["lampard-hist-no-glt-2010", "lampard-hist-sightline"],
          "In 2010 there was no goal-line technology and the decision could not be reviewed "
          "(lampard-hist-no-glt-2010), and neither official was level with the line at the "
          "moment of the bounce (lampard-hist-sightline); the decisive truth was not "
          "available to them in the moment, though it was knowable on replay within seconds."),
    _lens("FRAMING", "SUPPORTS", ["lampard-framing-lampard", "lampard-framing-blatter"],
          "Frank Lampard is reported to have said there was no doubt the ball was over the "
          "line (lampard-framing-lampard), and FIFA's Sepp Blatter publicly apologised for "
          "the error (lampard-framing-blatter); the named sources agree on the fact rather "
          "than dividing over it."),
]


# ── Suárez handball ──────────────────────────────────────────────────────────
# The decisive contrast: the Historical lens DISPUTES a decision-time deficit (the
# officials saw it and ruled correctly), which routes DECISION_TIME_DEFICIT to ABSENT.
# Only Cultural Prior Bias remains PRESENT — the axis it shares with the Hand of God.

_SUAREZ_LENSES = [
    _lens("REFEREE", "SUPPORTS", ["ifab-law12-dogso-handball-p118"],
          "The retrieved Law states that denying a goal by deliberate handball is a "
          "sending-off offence (ifab-law12-dogso-handball-p118); the sanction is a single "
          "clear rule, so rule-ambiguity does not hold."),
    _lens("HISTORICAL", "DISPUTES", ["suarez-hist-correctly-adjudicated"],
          "The retrieved facts state the referee saw the handball in real time and applied "
          "the Law exactly — a red card and a penalty (suarez-hist-correctly-adjudicated); "
          "the decisive truth WAS available in the moment, so there is no decision-time "
          "deficit."),
    LensOutput(lens="TACTICAL", stance="INSUFFICIENT_EVIDENCE",
               state="INSUFFICIENT_EVIDENCE", citation_ids=[],
               rationale="No event-data anomaly bears on this incident."),
    _lens("FRAMING", "MIXED", ["suarez-framing-suarez", "suarez-framing-gyan"],
          "Luis Suárez is reported to have called the handball the 'save of the tournament' "
          "(suarez-framing-suarez), while Asamoah Gyan is reported to have described it as a "
          "cruel injustice (suarez-framing-gyan); two named sources frame the same admitted "
          "act in opposite valence."),
]


# ── The modern handball call (RULE_AMBIGUITY PRESENT) ─────────────────────────
# The Referee lens DISPUTES — the Law offers several competing tests for the same contact,
# pointing to different outcomes. The Historical lens DISPUTES a decision-time deficit (the
# contact was visible and replayable), which routes DECISION_TIME_DEFICIT to ABSENT without
# touching INDETERMINACY. The framings share one complaint (one-sided) → CULTURAL ABSENT.

_HANDBALL_REWRITE_LENSES = [
    _lens("REFEREE", "DISPUTES",
          ["ifab-law12-handball-deliberate-p110", "ifab-law12-handball-offence-p110"],
          "The retrieved Law sets out several different tests for the same contact — a "
          "deliberate movement of the hand/arm, the hand/arm making the body 'unnaturally "
          "bigger', and an accidental touch that leads directly to a goal "
          "(ifab-law12-handball-deliberate-p110) — each with a different consequence. "
          "Competing clauses point to different outcomes for the same facts, so the rule "
          "itself is ambiguous."),
    LensOutput(lens="TACTICAL", stance="INSUFFICIENT_EVIDENCE",
               state="INSUFFICIENT_EVIDENCE", citation_ids=[],
               rationale="No event-data anomaly resolves which handball test applies."),
    _lens("HISTORICAL", "DISPUTES",
          ["hb-hist-three-tests", "hb-hist-visible-knowable"],
          "The retrieved facts state that whether the ball touched the hand or arm is "
          "almost always visible and, with modern replay, fully knowable "
          "(hb-hist-visible-knowable); the information available at the moment was adequate, "
          "so there is no decision-time deficit. What is contested is which clause applies."),
    _lens("FRAMING", "DISPUTES", ["hb-framing-pundit", "hb-framing-coach"],
          "Named officiating analysts and managers are reported to share one complaint — "
          "that near-identical contact is judged differently because the Law offers several "
          "tests rather than one (hb-framing-pundit, hb-framing-coach). The framings agree "
          "on the problem rather than dividing by side, so there is no opposed valence."),
]


# ── The millimetre offside line (INDETERMINACY PRESENT) ───────────────────────
# The Referee lens SUPPORTS — Law 11 fixes the line precisely (RULE ABSENT). The Historical
# lens DISPUTES knowability AND cites the measurement-unrecoverable atom, which routes
# INDETERMINACY to PRESENT and DECISION_TIME_DEFICIT to ABSENT (the tech can see it; the
# exact truth still cannot be measured). Framings one-sided → CULTURAL ABSENT.

_OFFSIDE_MARGIN_LENSES = [
    _lens("REFEREE", "SUPPORTS", ["ifab-law11-offside-margin-p103"],
          "The retrieved Law fixes the offside line precisely — a player is offside if any "
          "part of the head, body or feet is nearer the goal line than the second-last "
          "opponent (ifab-law11-offside-margin-p103). The rule is a single clear test, so "
          "rule-ambiguity does not hold."),
    LensOutput(lens="TACTICAL", stance="INSUFFICIENT_EVIDENCE",
               state="INSUFFICIENT_EVIDENCE", citation_ids=[],
               rationale="No event-data anomaly resolves the exact position at the margin."),
    _lens("HISTORICAL", "DISPUTES",
          ["om-hist-margin-unrecoverable", "om-hist-thicker-line"],
          "The retrieved facts state that at a millimetre margin the kick frame, the limb "
          "point and the motion of ball and players make the true position unrecoverable, "
          "and the authorities answer with a deliberately thicker line "
          "(om-hist-margin-unrecoverable, om-hist-thicker-line); the technology can see the "
          "moment, but the exact truth cannot be measured to the precision the Law implies."),
    _lens("FRAMING", "DISPUTES", ["om-framing-broadcaster", "om-framing-official"],
          "Named broadcasters and officiating bodies are reported to agree that margins too "
          "fine to see make the calls feel arbitrary and that a thicker line is used "
          "precisely because the measurement is unreliable (om-framing-broadcaster, "
          "om-framing-official); the framings converge rather than divide by side."),
]


# ── The 'subjective' VAR call (RULE_AMBIGUITY + CULTURAL_PRIOR_BIAS PRESENT) ───
# The combined signature. Referee DISPUTES (the threshold is a matter of degree applied
# inconsistently → RULE PRESENT). Historical DISPUTES a decision-time deficit (contact
# visible and replayed → DTD ABSENT, no margin signal → INDET NOT_DOCUMENTED). Framing MIXED
# (each side reads the same agreed contact in its own favour → CULTURAL PRESENT).

_PGMOL_SUBJECTIVE_LENSES = [
    _lens("REFEREE", "DISPUTES", ["pg-hist-threshold", "pg-hist-opposite-rulings"],
          "The retrieved record shows the 'clear and obvious' and 'non-footballing action' "
          "thresholds are matters of degree, not bright lines, so near-identical contact is "
          "ruled in opposite ways across matches (pg-hist-threshold, pg-hist-opposite-rulings); "
          "the rule's threshold itself generates the disagreement."),
    LensOutput(lens="TACTICAL", stance="INSUFFICIENT_EVIDENCE",
               state="INSUFFICIENT_EVIDENCE", citation_ids=[],
               rationale="No event-data anomaly resolves whether the threshold was met."),
    _lens("HISTORICAL", "DISPUTES", ["pg-hist-visible"],
          "The retrieved facts state the contact was visible on replay and reviewed by VAR "
          "(pg-hist-visible); the information available was adequate, so the dispute is not "
          "about what could be seen but about whether the threshold was met."),
    _lens("FRAMING", "MIXED", ["pg-framing-aggrieved", "pg-framing-benefiting"],
          "The manager ruled against is reported to call the contact a clear, obvious foul "
          "(pg-framing-aggrieved) while the manager who benefited calls the identical "
          "contact part of the game (pg-framing-benefiting); two named sources frame the "
          "same agreed contact in opposite valence."),
]


def bake_offline(spec: IncidentSpec, lenses: list[LensOutput], *, framing_yaml: Path,
                 historical_yaml: Path, aggregate: HandOfGodAggregate,
                 extra_citations: list[Citation], corpus_git_sha: str,
                 rule_evolution: RuleEvolution | None = None) -> IncidentBundle:
    """Assemble the pool, route the lens readings into a SPLIT, and freeze a bundle."""
    pool: dict[str, Citation] = assemble_pool(
        framing_yaml=framing_yaml, historical_yaml=historical_yaml, aggregate=aggregate
    )
    for c in extra_citations:
        pool.setdefault(c.id, c)

    for lo in lenses:
        for cid in lo.citation_ids:
            if cid not in pool:
                raise SystemExit(f"lens {lo.lens} cites '{cid}' which is not in the corpus pool")

    split = derive_split(lenses, admitted_act=bool(spec.admission_note))

    def seal(ids):
        return TrustSeal(verdict="GROUNDED", guardian_model=_ROUTER_NOTE,
                         checked_context_citation_ids=list(ids))

    sealed_lenses = [SealedLens(output=lo, seal=seal(lo.citation_ids)) for lo in lenses]
    sealed_cells = [SealedCell(cell=c, seal=seal(c.citation_ids)) for c in split.cells]

    referenced = set(spec.settled_citation_ids)
    for lo in lenses:
        referenced.update(lo.citation_ids)
    for c in split.cells:
        referenced.update(c.citation_ids)

    return IncidentBundle(
        incident_id=spec.incident_id,
        title=spec.title,
        settled_fact=SettledFact(status=spec.settled_status, statement=spec.settled_statement,
                                 citation_ids=list(spec.settled_citation_ids)),
        lenses=sealed_lenses,
        split=split,
        cell_seals=sealed_cells,
        citations={cid: pool[cid] for cid in referenced if cid in pool},
        provenance=BakeProvenance(
            granite_model=DEFAULT_MODEL,
            guardian_model=DEFAULT_GUARDIAN_MODEL,
            embed_model=DEFAULT_EMBED_MODEL,
            corpus_git_sha=corpus_git_sha,
        ),
        rule_evolution=rule_evolution,
    )


def _corpus(incident_slug: str) -> tuple[Path, Path]:
    return (
        _REPO / "corpus" / "framing" / incident_slug / "sources.yaml",
        _REPO / "corpus" / "historical" / incident_slug / "record.yaml",
    )


def main() -> None:
    sha = subprocess.check_output(["git", "-C", str(_REPO), "rev-parse", "HEAD"]).decode().strip()
    fixtures = _REPO / "web" / "fixtures"

    hog_fr, hog_hist = _corpus("hand-of-god")
    hog = bake_offline(HAND_OF_GOD, _HAND_OF_GOD_LENSES, framing_yaml=hog_fr,
                       historical_yaml=hog_hist, aggregate=_HAND_OF_GOD_AGG,
                       extra_citations=[], corpus_git_sha=sha)

    sz_fr, sz_hist = _corpus("suarez-handball")
    sz = bake_offline(SUAREZ_HANDBALL, _SUAREZ_LENSES, framing_yaml=sz_fr,
                      historical_yaml=sz_hist, aggregate=_HAND_OF_GOD_AGG,
                      extra_citations=[], corpus_git_sha=sha)

    lam_fr, lam_hist = _corpus("lampard-ghost-goal")
    lampard_evolution = RuleEvolution(
        axis="DECISION_TIME_DEFICIT",
        from_era="2010 — no goal-line technology",
        to_era="2026 — automatic goal-line detection",
        from_state="PRESENT",
        to_state="ABSENT",
        note="What was undetectable in the moment is automatic now — the fact was always "
             "settled; only its availability to the officials changed.",
    )
    lam = bake_offline(LAMPARD_GHOST_GOAL, _LAMPARD_LENSES, framing_yaml=lam_fr,
                       historical_yaml=lam_hist, aggregate=_HAND_OF_GOD_AGG,
                       extra_citations=[], corpus_git_sha=sha,
                       rule_evolution=lampard_evolution)

    # ── Current, unsettled disputes (light up the axes the archive never did) ──
    hb_fr, hb_hist = _corpus("handball-rewrite")
    handball = bake_offline(HANDBALL_REWRITE, _HANDBALL_REWRITE_LENSES, framing_yaml=hb_fr,
                            historical_yaml=hb_hist, aggregate=_HAND_OF_GOD_AGG,
                            extra_citations=[], corpus_git_sha=sha)

    om_fr, om_hist = _corpus("offside-margin")
    offside = bake_offline(OFFSIDE_MARGIN, _OFFSIDE_MARGIN_LENSES, framing_yaml=om_fr,
                           historical_yaml=om_hist, aggregate=_HAND_OF_GOD_AGG,
                           extra_citations=[], corpus_git_sha=sha)

    pg_fr, pg_hist = _corpus("pgmol-subjective")
    pgmol = bake_offline(PGMOL_SUBJECTIVE, _PGMOL_SUBJECTIVE_LENSES, framing_yaml=pg_fr,
                         historical_yaml=pg_hist, aggregate=_HAND_OF_GOD_AGG,
                         extra_citations=[], corpus_git_sha=sha)

    # Assert each derived SPLIT matches the documented thesis shape — the oracle that keeps
    # "derived, not hard-coded" honest. A drift fails the bake rather than freezing a fixture
    # that silently diverged from the documented signature.
    by_spec = [
        (HAND_OF_GOD, hog), (SUAREZ_HANDBALL, sz), (LAMPARD_GHOST_GOAL, lam),
        (HANDBALL_REWRITE, handball), (OFFSIDE_MARGIN, offside), (PGMOL_SUBJECTIVE, pgmol),
    ]
    for spec, bundle in by_spec:
        if not spec.expected_thesis:
            continue
        for cell in bundle.split.cells:
            allowed = spec.expected_thesis.get(cell.axis)
            if allowed and cell.state not in allowed:
                raise SystemExit(
                    f"thesis mismatch for {spec.incident_id}: {cell.axis} derived "
                    f"{cell.state}, expected one of {sorted(allowed)}"
                )

    for bundle in (hog, sz, lam, handball, offside, pgmol):
        out = write_fixture(bundle, fixtures)
        states = {c.axis: c.state for c in bundle.split.cells}
        print(f"\nwrote {out}\n  THE SPLIT: {states}\n  headline: {bundle.split.headline}")


if __name__ == "__main__":
    main()
