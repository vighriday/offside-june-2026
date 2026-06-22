"""Full-stack bake — assemble → index → bake → freeze against the REAL corpus.

This is the integration test the Colab notebook stands on: it runs the entire engine
with only the two models mocked (Granite scripted to the golden readings, Guardian to
GROUNDED), real corpus YAML, a real LanceDB index, and the real fixture writer. A pass
means the pipeline is wired correctly end to end; the Colab run only swaps the two mocks
for live Ollama models.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from offside_engine.bake.incident import HAND_OF_GOD
from offside_engine.bake.runner import run_bake
from offside_engine.index.embed import EMBED_DIM
from offside_engine.statsbomb.pull_aggregates import HandOfGodAggregate

# Reuse the scripted models and the offline aggregate from the unit tests.
from tests.test_bake import _ScriptedGranite, _AllGroundedGuardian  # noqa: E402

_REPO = Path(__file__).resolve().parents[2]
_FRAMING = _REPO / "corpus" / "framing" / "hand-of-god" / "sources.yaml"
_HISTORICAL = _REPO / "corpus" / "historical" / "hand-of-god" / "record.yaml"

pytestmark = pytest.mark.skipif(not _FRAMING.exists(), reason="corpus not present")


class _LensKeyedEmbedder:
    """Embeds so each lens's evidence clusters, keyed by words in the real corpus text.

    The runner's retrieval must surface the right ids per lens for the scripted Granite
    to recognise them; this maps obvious lens-specific words onto distinct axes so a
    lens query lands on its own evidence.
    """

    _BASIS = {
        "law": 0, "hand": 0, "offence": 0, "goal": 0,       # referee
        "body": 1, "catch-all": 1, "data": 1, "other": 1,   # tactical
        "review": 2, "video": 2, "officials": 2, "tech": 2,  # historical
        "reported": 3, "said": 3, "called": 3, "described": 3,  # framing
    }

    def _vec(self, text: str):
        axis = 0
        low = text.lower()
        for word, a in self._BASIS.items():
            if word in low:
                axis = a
                break
        v = [0.0] * EMBED_DIM
        v[axis] = 1.0
        return v

    def embed(self, texts):
        return [self._vec(t) for t in texts]

    def embed_one(self, text):
        return self._vec(text)


def _aggregate() -> HandOfGodAggregate:
    return HandOfGodAggregate(
        match_id=3750191, scoreline="Argentina 2 - 1 England",
        maradona_total_shots=3, maradona_goals=2,
        hand_of_god_minute=50, hand_of_god_body_part="Other",
        second_goal_minute=54, second_goal_body_part="Left Foot",
        anomaly_present=True, three_sixty_available=False,
    )


def test_full_stack_bake_writes_the_golden_fixture(tmp_path):
    result = run_bake(
        HAND_OF_GOD,
        framing_yaml=_FRAMING,
        historical_yaml=_HISTORICAL,
        aggregate=_aggregate(),
        db_dir=tmp_path / "lance",
        fixtures_dir=tmp_path / "fixtures",
        corpus_git_sha="abc123",
        embedder=_LensKeyedEmbedder(),
        granite=_ScriptedGranite(),
        guardian=_AllGroundedGuardian(),
    )

    # a fixture was written, named by incident id
    assert result.fixture_path.exists()
    assert result.fixture_path.name == "hand-of-god-1986.json"
    assert result.pool_size >= 4  # laws + historical + framing + statsbomb

    # the documented signature survived the full real-corpus pipeline
    states = {c.axis: c.state for c in result.bundle.split.cells}
    assert states["RULE_AMBIGUITY"] == "ABSENT"
    assert states["INDETERMINACY"] == "ABSENT"
    assert states["DECISION_TIME_DEFICIT"] == "PRESENT"
    assert states["CULTURAL_PRIOR_BIAS"] == "PRESENT"

    # provenance was frozen with the real model + corpus sha
    assert result.bundle.provenance.corpus_git_sha == "abc123"
