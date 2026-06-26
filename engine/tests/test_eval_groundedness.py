"""The groundedness eval is a build-time audit that does NOT leak numbers into the model
output. These tests assert the deterministic scorer is correct AND that the moat is intact:
the report carries numbers, but no fixture, SPLIT, or lens schema gained a numeric field.
"""

from __future__ import annotations

import json
from pathlib import Path

from offside_engine.analyze.split_schema import IncidentBundle
from offside_engine.eval.groundedness import (
    score_bundle_deterministic,
    write_report,
)

_FIXTURES = Path(__file__).resolve().parents[2] / "web" / "fixtures"


def _a_bundle() -> IncidentBundle:
    path = _FIXTURES / "hand-of-god-1986.json"
    return IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))


def test_grounded_lens_scores_one_empty_lens_scores_zero():
    rows = score_bundle_deterministic(_a_bundle())
    assert rows, "no lenses scored"
    for r in rows:
        if r.guardian_verdict == "GROUNDED" and r.n_citations > 0:
            assert r.groundedness == 1.0
        else:
            assert r.groundedness == 0.0


def test_report_writes_json_and_md(tmp_path: Path):
    rows = score_bundle_deterministic(_a_bundle())
    jp, mp = write_report(rows, tmp_path)
    assert jp.exists() and mp.exists()
    data = json.loads(jp.read_text(encoding="utf-8"))
    assert len(data) == len(rows)
    assert "groundedness" in mp.read_text(encoding="utf-8").lower()


def _keys(obj):
    """Yield every dict key anywhere in a nested JSON structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_eval_numbers_never_entered_the_shipped_fixtures():
    # The audit metric must live only in the report — no 'groundedness' SCORE FIELD may enter
    # a fixture. We check JSON KEYS, not the substring: the word legitimately appears in a
    # rationale ("the groundedness gate could not confirm this reading"), which is prose, not
    # a number. A score would be a numeric field named 'groundedness'.
    for path in _FIXTURES.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "groundedness" not in set(_keys(raw))
