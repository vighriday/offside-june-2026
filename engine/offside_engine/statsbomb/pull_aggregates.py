"""License-safe StatsBomb extraction for the Hand of God Tactical lens.

StatsBomb Open Data is used under the StatsBomb User Agreement (non-commercial,
attribution required, **no redistribution**). To honour it:

* events are pulled at *build time* and only **derived aggregates** are persisted;
* **raw event rows are never written to disk** and never committed;
* every persisted aggregate carries the required StatsBomb attribution string.

The signal that matters: in match 3750191 (Argentina v England, 1986) Maradona's 51'
goal is recorded as a ``Shot`` with ``shot_body_part == "Other"``. This is a statement
about the *data model only*: StatsBomb's shot ontology has no category for a
hand-scored goal, so the event falls back to the catch-all ``Other``. It is a
corroborating exhibit of the incident's oddness — **not** evidence of intent, of the
original officiating call, or that the fact is unknowable. It is cited by the Tactical
lens as a captioned aside and never feeds the Decision-Time-Deficit axis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from offside_engine.analyze.split_schema import Citation

# Confirmed by the StatsBomb spike (see _local/SPIKE_RESULTS.md).
HAND_OF_GOD_MATCH_ID = 3750191
COMPETITION_ID = 43  # FIFA World Cup
SEASON_ID = 54  # 1986
ATTRIBUTION = "Data provided by StatsBomb Open Data (StatsBomb User Agreement)."

# The stable id the Tactical lens cites for the Hand of God body-part anomaly.
HAND_OF_GOD_TACTICAL_CITATION_ID = "sb-hand-of-god-body-part"

# The feed's catch-all body-part label — a string, never a number. The Tactical lens
# reports that a goal fell back to this label, not any stat value.
_CATCH_ALL_LABEL = "Other"


@dataclass(frozen=True)
class HandOfGodAggregate:
    """The derived, license-safe summary persisted for the Tactical lens."""

    match_id: int
    scoreline: str
    maradona_total_shots: int
    maradona_goals: int
    hand_of_god_minute: int | None
    hand_of_god_body_part: str | None
    second_goal_minute: int | None
    second_goal_body_part: str | None
    anomaly_present: bool  # a goal classified as body_part "Other"
    three_sixty_available: bool
    attribution: str = ATTRIBUTION

    def to_dict(self) -> dict:
        return asdict(self)


def aggregate_from_events(events) -> HandOfGodAggregate:
    """Compute the derived aggregate from a StatsBomb events DataFrame.

    Takes the events frame as an argument (rather than fetching) so this is unit-
    testable without network and so the raw frame stays in memory only — it is never
    returned or written.
    """
    shots = events[events["type"] == "Shot"]
    mara = shots[shots["player"].str.contains("Maradona", case=False, na=False)]
    goals = mara[mara["shot_outcome"] == "Goal"].sort_values("minute")

    def _at(idx: int, col: str):
        return None if idx >= len(goals) else goals.iloc[idx][col]

    hog_min = _at(0, "minute")
    hog_bp = _at(0, "shot_body_part")
    g2_min = _at(1, "minute")
    g2_bp = _at(1, "shot_body_part")

    return HandOfGodAggregate(
        match_id=HAND_OF_GOD_MATCH_ID,
        scoreline="Argentina 2 - 1 England",
        maradona_total_shots=int(len(mara)),
        maradona_goals=int(len(goals)),
        hand_of_god_minute=None if hog_min is None else int(hog_min),
        hand_of_god_body_part=None if hog_bp is None else str(hog_bp),
        second_goal_minute=None if g2_min is None else int(g2_min),
        second_goal_body_part=None if g2_bp is None else str(g2_bp),
        anomaly_present=bool((goals["shot_body_part"] == "Other").any()),
        three_sixty_available=False,  # confirmed 404 for 1986 in the spike
    )


def to_tactical_citation(agg: HandOfGodAggregate) -> Citation:
    """Render the aggregate as the single license-safe Citation the Tactical lens cites.

    The text is a statement about the *data model only*: the hand-scored goal fell back
    to the feed's catch-all body-part label while a comparable goal carries a real
    body-part class. It contains **no number and no raw event row** — only the catch-all
    label name and the comparison — so it honours both the StatsBomb no-redistribution
    rule and the lens's no-numbers rule. Built only when the anomaly is actually present.
    """
    if not agg.anomaly_present:
        raise ValueError(
            "no body-part anomaly in the aggregate — refusing to fabricate a Tactical citation"
        )
    comparison = (
        f"a comparable goal by the same player is recorded with a specific body-part class "
        f"('{agg.second_goal_body_part}')"
        if agg.second_goal_body_part and agg.second_goal_body_part != _CATCH_ALL_LABEL
        else "a comparable goal by the same player is recorded with a specific body-part class"
    )
    text = (
        f"In the event data this goal's body part is recorded as the catch-all label "
        f"'{_CATCH_ALL_LABEL}', while {comparison}. The shot ontology has no category "
        f"for a hand-scored goal, so the event falls back to '{_CATCH_ALL_LABEL}'. This "
        f"describes the data model only — not officiating, intent, or knowability."
    )
    return Citation(
        id=HAND_OF_GOD_TACTICAL_CITATION_ID,
        source_doc="statsbomb-open-data",
        doc_kind="STATSBOMB_EVENT",
        page=None,
        extracted_text=text,
        attribution=agg.attribution,
    )


def pull_hand_of_god_aggregate() -> HandOfGodAggregate:
    """Fetch the match events at build time and return the derived aggregate.

    The raw events frame is discarded when this returns — only the aggregate survives.
    """
    from statsbombpy import sb  # imported lazily so tests need no network

    events = sb.events(match_id=HAND_OF_GOD_MATCH_ID)
    return aggregate_from_events(events)
