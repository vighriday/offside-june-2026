"""StatsBomb aggregate — anomaly detection + license-safe shape, no network.

The synthetic frame mirrors the real spike output: Maradona's 50' goal is body_part
"Other" (the Hand of God), his 54' goal is "Left Foot".
"""

from __future__ import annotations

import re

import pandas as pd
import pytest

from offside_engine.statsbomb.pull_aggregates import (
    ATTRIBUTION,
    HAND_OF_GOD_TACTICAL_CITATION_ID,
    aggregate_from_events,
    to_tactical_citation,
)


def _events():
    return pd.DataFrame(
        [
            {"type": "Shot", "player": "Diego Armando Maradona", "minute": 9,
             "shot_outcome": "Blocked", "shot_body_part": "Left Foot"},
            {"type": "Shot", "player": "Diego Armando Maradona", "minute": 50,
             "shot_outcome": "Goal", "shot_body_part": "Other"},      # Hand of God
            {"type": "Shot", "player": "Diego Armando Maradona", "minute": 54,
             "shot_outcome": "Goal", "shot_body_part": "Left Foot"},  # legit goal
            {"type": "Shot", "player": "Gary Lineker", "minute": 80,
             "shot_outcome": "Goal", "shot_body_part": "Head"},
            {"type": "Pass", "player": "Diego Armando Maradona", "minute": 12,
             "shot_outcome": None, "shot_body_part": None},
        ]
    )


def test_detects_the_hand_of_god_anomaly():
    agg = aggregate_from_events(_events())
    assert agg.anomaly_present is True
    assert agg.hand_of_god_minute == 50
    assert agg.hand_of_god_body_part == "Other"


def test_distinguishes_the_legit_second_goal():
    agg = aggregate_from_events(_events())
    assert agg.second_goal_minute == 54
    assert agg.second_goal_body_part == "Left Foot"


def test_counts_only_maradona_shots_and_goals():
    agg = aggregate_from_events(_events())
    assert agg.maradona_total_shots == 3  # the Pass is excluded
    assert agg.maradona_goals == 2


def test_aggregate_carries_attribution_and_no_raw_rows():
    agg = aggregate_from_events(_events())
    d = agg.to_dict()
    assert d["attribution"] == ATTRIBUTION
    # the aggregate is a flat summary — no nested event rows leak through
    assert all(not isinstance(v, (list, dict)) for v in d.values())
    assert agg.three_sixty_available is False


def test_match_metadata_is_pinned():
    agg = aggregate_from_events(_events())
    assert agg.match_id == 3750191
    assert agg.scoreline == "Argentina 2 - 1 England"


# ── tactical citation bridge ─────────────────────────────────────────────────

def test_tactical_citation_has_stable_id_and_attribution():
    cit = to_tactical_citation(aggregate_from_events(_events()))
    assert cit.id == HAND_OF_GOD_TACTICAL_CITATION_ID
    assert cit.doc_kind == "STATSBOMB_EVENT"
    assert cit.attribution == ATTRIBUTION


def test_tactical_citation_text_carries_the_catch_all_label_and_no_number():
    cit = to_tactical_citation(aggregate_from_events(_events()))
    assert "'Other'" in cit.extracted_text          # the catch-all label, named
    assert "Left Foot" in cit.extracted_text        # the comparison class
    assert "data model only" in cit.extracted_text  # the bounded claim
    # the Tactical lens forbids numbers — the citation text must carry no digit
    assert not re.search(r"\d", cit.extracted_text)


def test_tactical_citation_refuses_when_no_anomaly():
    # a frame with no body_part 'Other' goal -> no anomaly -> no fabricated citation
    df = pd.DataFrame([
        {"type": "Shot", "player": "Diego Armando Maradona", "minute": 54,
         "shot_outcome": "Goal", "shot_body_part": "Left Foot"},
    ])
    with pytest.raises(ValueError, match="no body-part anomaly"):
        to_tactical_citation(aggregate_from_events(df))
