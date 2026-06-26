"""Tests for BakeProvenance.mode field and stream live-user stamping."""
from offside_engine.analyze.split_schema import BakeProvenance


def test_provenance_defaults_to_frozen():
    p = BakeProvenance(granite_model="g", guardian_model="gu", embed_model="e")
    assert p.mode == "frozen"


def test_provenance_accepts_live_user():
    p = BakeProvenance(granite_model="g", guardian_model="gu", embed_model="e", mode="live-user")
    assert p.mode == "live-user"
