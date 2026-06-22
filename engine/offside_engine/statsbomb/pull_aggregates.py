"""License-safe StatsBomb extraction for the Hand of God Tactical lens.

StatsBomb Open Data is used under the StatsBomb User Agreement (non-commercial,
attribution required, **no redistribution**). To honour it:

* events are pulled at *build time* and only **derived aggregates** are persisted;
* **raw event rows are never written to disk** and never committed;
* every persisted aggregate carries the required StatsBomb attribution string.

The signal that matters: in match 3750191 (Argentina v England, 1986) Maradona's 51'
goal is recorded as a ``Shot`` with ``shot_body_part == "Other"`` — StatsBomb's own
ontology cannot classify the illegal handball goal. That anomaly is grounded evidence
for the Indeterminacy axis of THE SPLIT, and it comes from the dataset itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Confirmed by the StatsBomb spike (see _local/SPIKE_RESULTS.md).
HAND_OF_GOD_MATCH_ID = 3750191
COMPETITION_ID = 43  # FIFA World Cup
SEASON_ID = 54  # 1986
ATTRIBUTION = "Data provided by StatsBomb Open Data (StatsBomb User Agreement)."


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


def pull_hand_of_god_aggregate() -> HandOfGodAggregate:
    """Fetch the match events at build time and return the derived aggregate.

    The raw events frame is discarded when this returns — only the aggregate survives.
    """
    from statsbombpy import sb  # imported lazily so tests need no network

    events = sb.events(match_id=HAND_OF_GOD_MATCH_ID)
    return aggregate_from_events(events)
