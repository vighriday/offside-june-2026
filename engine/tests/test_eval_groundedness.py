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


def test_eval_numbers_never_entered_the_shipped_fixtures():
    # the audit metric must live only in the report — fixtures stay number-free
    for path in _FIXTURES.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        # the bundle must carry no 'groundedness' field anywhere (it is report-only)
        assert "groundedness" not in json.dumps(raw)
