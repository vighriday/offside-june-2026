"""TS contract export — guard against the TypeScript drifting from the Pydantic models.

The exported TS interfaces are written by hand in export_types.py; this test makes that
safe by asserting every field of every contract model appears in the generated TS. Add a
field to IncidentBundle without mirroring it and this goes red — the web types can never
silently lag the engine contract.
"""

from __future__ import annotations

from offside_engine.analyze.split_schema import (
    BakeProvenance,
    Bbox,
    Citation,
    IncidentBundle,
    LensOutput,
    SealedCell,
    SealedLens,
    SettledFact,
    Split,
    SplitCell,
    TrustSeal,
)
from offside_engine.export_types import build_ts

_CONTRACT_MODELS = (
    Bbox, Citation, TrustSeal, LensOutput, SplitCell, Split,
    SettledFact, SealedLens, SealedCell, BakeProvenance, IncidentBundle,
)


def test_every_contract_model_field_is_present_in_the_ts():
    ts = build_ts()
    missing = []
    for model in _CONTRACT_MODELS:
        for field in model.model_fields:
            # each field name must appear as a TS property key somewhere in the export
            if f"{field}:" not in ts and f"{field}?:" not in ts:
                missing.append(f"{model.__name__}.{field}")
    assert not missing, f"TS contract is missing fields (drift!): {missing}"


def test_enums_render_as_string_literal_unions():
    ts = build_ts()
    assert 'export type CellState = "PRESENT" | "WEAK" | "ABSENT" | "NOT_DOCUMENTED";' in ts
    assert '"RULE_AMBIGUITY"' in ts and '"CULTURAL_PRIOR_BIAS"' in ts
    assert 'export type GuardianVerdict = "GROUNDED" | "UNGROUNDED";' in ts


def test_canonical_axis_order_is_exported_for_the_web():
    ts = build_ts()
    assert "CANONICAL_AXIS_ORDER" in ts
    # the order matters: the SPLIT always renders these four in this sequence
    idx = ts.index("CANONICAL_AXIS_ORDER")
    tail = ts[idx:]
    assert tail.index("RULE_AMBIGUITY") < tail.index("INDETERMINACY") < tail.index(
        "DECISION_TIME_DEFICIT"
    ) < tail.index("CULTURAL_PRIOR_BIAS")
