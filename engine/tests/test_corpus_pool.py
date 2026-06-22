"""The evidence pool — assembly from the real committed corpus, and the id contract.

This is the integration check that catches id drift: it builds the pool from the actual
``corpus/`` YAML and asserts the Hand of God incident's allow-list resolves entirely
within it. If a corpus id is renamed without updating the spec (or vice versa), this
goes red before a bake ever fails downstream.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from offside_engine.bake.corpus_pool import assemble_pool
from offside_engine.bake.incident import HAND_OF_GOD
from offside_engine.statsbomb.pull_aggregates import HandOfGodAggregate

_REPO = Path(__file__).resolve().parents[2]
_FRAMING = _REPO / "corpus" / "framing" / "hand-of-god" / "sources.yaml"
_HISTORICAL = _REPO / "corpus" / "historical" / "hand-of-god" / "record.yaml"


def _aggregate() -> HandOfGodAggregate:
    # a frozen, offline aggregate carrying the body-part anomaly
    return HandOfGodAggregate(
        match_id=3750191, scoreline="Argentina 2 - 1 England",
        maradona_total_shots=3, maradona_goals=2,
        hand_of_god_minute=50, hand_of_god_body_part="Other",
        second_goal_minute=54, second_goal_body_part="Left Foot",
        anomaly_present=True, three_sixty_available=False,
    )


def _pool():
    return assemble_pool(framing_yaml=_FRAMING, historical_yaml=_HISTORICAL,
                         aggregate=_aggregate())


@pytest.mark.skipif(not _FRAMING.exists(), reason="corpus not present")
def test_pool_assembles_from_the_real_corpus():
    pool = _pool()
    # every source contributed at least one atom
    kinds = {c.doc_kind for c in pool.values()}
    assert {"IFAB_LAW", "HISTORICAL_REPORT", "FRAMING_SOURCE", "STATSBOMB_EVENT"} <= kinds


@pytest.mark.skipif(not _FRAMING.exists(), reason="corpus not present")
def test_hand_of_god_allow_list_resolves_entirely_in_the_pool():
    pool = _pool()
    missing = sorted(HAND_OF_GOD.allowed_citation_ids - set(pool))
    assert not missing, f"incident allow-list names ids absent from the corpus: {missing}"


@pytest.mark.skipif(not _FRAMING.exists(), reason="corpus not present")
def test_settled_fact_citation_resolves_in_the_pool():
    pool = _pool()
    for cid in HAND_OF_GOD.settled_citation_ids:
        assert cid in pool, f"settled-fact cite '{cid}' is not in the pool"


def test_duplicate_ids_across_sources_are_rejected(tmp_path, monkeypatch):
    # forge a framing loader that collides with a curated IFAB id -> pool must refuse
    import offside_engine.bake.corpus_pool as cp
    from offside_engine.analyze.split_schema import Citation

    clash_id = "ifab-law12-handball-offence-p110"  # a real curated id
    monkeypatch.setattr(
        cp, "load_framing_citations",
        lambda _p: [Citation(id=clash_id, source_doc="framing",
                             doc_kind="FRAMING_SOURCE", extracted_text="x")],
    )
    monkeypatch.setattr(cp, "load_historical_citations", lambda _p: [])
    with pytest.raises(ValueError, match="duplicate citation id"):
        cp.assemble_pool(framing_yaml=tmp_path / "f.yaml",
                         historical_yaml=tmp_path / "h.yaml",
                         aggregate=_aggregate())
